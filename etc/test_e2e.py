#!/usr/bin/env python3

# Runs end-to-end tests on a jupyterhub instance

import re
import sys
import json
import time
import asyncio
import argparse
from urllib.parse import urljoin, quote as urlquote, urlparse, unquote as urlunquote

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import requests
import websockets

MAX_LOAD_COUNT = 10

PACHCTL_WHOAMI_PATTERN = re.compile(r'You are ".+"\nsession expires: .+\nYou are an administrator of this Pachyderm cluster\n', re.MULTILINE)
PYTHON_WHOAMI_PATTERN = re.compile(r'username: \".+\"')
PACHCTL_VERSION_PATTERN = re.compile(r'COMPONENT +VERSION +\npachctl', re.MULTILINE)
PYTHON_VERSION_PATTERN = re.compile(r'major: (\d+)\nminor: (\d+)', re.MULTILINE)
HOMEPAGE_PATH_PATTERN = re.compile(r'/user/([^/]+)/')

def retry(f, attempts=10, sleep=1.0):
    """
    Repeatedly retries an operation, ignore exceptions, n times with a given
    sleep between runs.
    """
    count = 0
    while count < attempts:
        try:
            return f()
        except:
            count += 1
            if count >= attempts:
                raise
            time.sleep(sleep)

async def run_command(ws, cmd, timeout=1.0):
    """
    Runs a command in a terminal session available on a websocket connection
    """

    await ws.send(json.dumps(["stdin", "{}\r\n".format(cmd)]))
    await ws.recv() # ignore command being echoed back

    start_time = time.time()
    lines = []

    while time.time() - start_time < timeout:
        try:
            line = await asyncio.wait_for(ws.recv(), timeout=timeout)
        except asyncio.TimeoutError:
            pass
        else:
            lines.append(json.loads(line))

    # seems to always be true, even when stderr is printed to instead
    assert all(stdio == "stdout" for (stdio, _) in lines)

    return "".join(l.replace("\r\n", "\n") for (_, l) in lines)

def check_stdout(pattern, lines):
    """
    Verifies terminal stdout against a given regex
    """
    assert pattern.search(lines) is not None, \
        "unexpected terminal output:\n{}".format(lines)

def login(driver, url, login_username, login_password):
    """
    Tests for successful login using selenium
    """
    print("login")

    # get the jupyterhub login page
    driver.get(url)

    # fill out username/password fields
    if login_username:
        username_field = driver.find_element_by_id("username_input")
        username_field.send_keys(login_username)
    password_field = driver.find_element_by_id("password_input")
    password_field.send_keys(login_password)
    driver.find_element_by_id("login_submit").click()

    # Repeatedly check for the title on the jupyter user homepage. We check
    # over a period of 30s because, on the first login, jupyterhub shows a
    # loading page while the user pod is spun up. We want to ensure it
    # successfully clears this loading page and gets to the homepage.
    def check_title():
        assert driver.title == "Home Page - Select or create a notebook", "unexpected page title: {}".format(driver.title)
    retry(check_title, attempts=30)

    # Get the logged in username
    homepage_url = urlparse(driver.current_url)
    return urlunquote(HOMEPAGE_PATH_PATTERN.match(homepage_url.path).groups()[0])

def get_token(driver, url):
    """
    Using selenium, this extracts an API token
    """
    print("token")

    driver.get(urljoin(url, "/hub/token"))

    def get_token():
        driver.find_element_by_class_name("btn-jupyter").click()
        token = driver.find_element_by_id("token-result").get_attribute("innerHTML")
        assert token, "token not ready yet"
        return token
    return retry(get_token)

async def test_terminal(url, token, username, no_auth_check):
    """
    Tests that it's possible to start a Jupyter terminal session, and that
    expected dependencies are installed
    """

    print("terminal init")

    # Start a terminal session
    res = requests.request("POST", urljoin(url, "/user/{}/api/terminals".format(urlquote(username))), data=dict(token=token))
    res.raise_for_status()
    term_name = res.json()["name"]

    # Use Jupyter's undocumented API for interacting with the terminal
    # session.
    # 1) Determine the websocket URL for the terminal session
    ws_url = urljoin(url, "/user/{}/terminals/websocket/{}?token={}".format(urlquote(username), urlquote(term_name), urlquote(token)))
    ws_url = ws_url.replace("http://", "ws://")
    ws_url = ws_url.replace("https://", "wss://")

    # 2) Connect with websockets
    async with websockets.connect(ws_url) as ws:
        # 3) Ignore the setup message
        await ws.recv()

        # 4) Check that `pachctl` is installed
        print("pachctl version")
        lines = await run_command(ws, "pachctl version")
        check_stdout(PACHCTL_VERSION_PATTERN, lines)

        # 5) Check that python_pachyderm is installed
        print("python_pachyderm version")
        lines = await run_command(ws, "python3 -c 'import python_pachyderm; c = python_pachyderm.Client.new_in_cluster(); print(c.get_remote_version())'")
        check_stdout(PYTHON_VERSION_PATTERN, lines)
        
        if not no_auth_check:
            # 6) Check that we're authenticated in `pachctl`
            print("pachctl whoami")
            lines = await run_command(ws, "pachctl auth whoami")
            check_stdout(PACHCTL_WHOAMI_PATTERN, lines)

            # 7) Check that we're authenticated in python_pachyderm
            print("python_pachyderm whoami")
            lines = await run_command(ws, "python3 -c 'import python_pachyderm; c = python_pachyderm.Client.new_in_cluster(); print(c.who_am_i())'")
            check_stdout(PYTHON_WHOAMI_PATTERN, lines)

def main(url, login_username, login_password, webdriver_path, headless, debug, no_auth_check):
    opts = Options()
    opts.headless = headless

    # create a selenium driver
    if webdriver_path:
        driver = webdriver.Firefox(executable_path=webdriver_path, options=opts)
    else:
        driver = webdriver.Firefox(options=opts)
    
    # run tests
    resolved_username = login(driver, url, login_username, login_password)
    token = get_token(driver, url)
    asyncio.run(test_terminal(url, token, resolved_username, no_auth_check))

    if not debug:
        driver.quit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="JupyterHub login url")
    parser.add_argument("username", help="JupyterHub login username")
    parser.add_argument("password", help="JupyterHub login password")
    parser.add_argument("--webdriver", help="path to webdriver executable")
    parser.add_argument("--headless", action="store_true", help="headless mode")
    parser.add_argument("--debug", action="store_true", help="debug mode")
    parser.add_argument("--no-auth-check", action="store_true", help="Disable auth-related tests")
    args = parser.parse_args()

    main(args.url, args.username, args.password, args.webdriver, args.headless, args.debug, args.no_auth_check)
