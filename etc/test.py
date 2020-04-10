#!/usr/bin/env python3

# Runs end-to-end tests on a jupyterhub instance

import sys
import time
import argparse
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

MAX_LOAD_COUNT = 10

NOTEBOOK_CODE = """
import python_pachyderm
client = python_pachyderm.Client.new_in_cluster()
client.who_am_i()
"""

def retry(f, attempts=10, sleep=1.0):
    count = 0
    while count < attempts:
        try:
            return f()
        except AssertionError:
            count += 1
            if count >= attempts:
                raise
            time.sleep(sleep)

def login(driver, url, username, password):
    print("login")

    # get the jupyterhub login page
    driver.get(url)

    # fill out username/password fields
    username_field = driver.find_element_by_id("username_input")
    username_field.send_keys(username)
    password_field = driver.find_element_by_id("password_input")
    password_field.send_keys(password)
    driver.find_element_by_id("login_submit").click()

    # Repeatedly check for the title on the jupyter user homepage. We
    # repeatedly check over a period of 30s because, on the first login,
    # jupyterhub shows a loading page while the user pod is spun up. We want
    # to ensure it successfully clears this loading page and gets to the
    # homepage.
    def check_title():
        assert driver.title == "Home Page - Select or create a notebook", "not in the user homepage"
    retry(check_title, attempts=30)

def get_token(driver, url):
    print("token")

    driver.get(urljoin(url, "/hub/token"))

    def get_token():
        driver.find_element_by_class_name("btn-jupyter").click()
        token = driver.find_element_by_id("token-result").get_attribute("innerHTML")
        assert token, "token not ready yet"
        return token
    return retry(get_token)

def test_pachctl(url, token):
    print("pachctl")

    

def main(url, username, password, webdriver_path, headless, debug):
    opts = Options()
    opts.headless = headless

    # create a selenium driver
    if webdriver_path:
        driver = webdriver.Firefox(executable_path=webdriver_path, options=opts)
    else:
        driver = webdriver.Firefox(options=opts)
    
    login(driver, url, username, password)
    token = get_token(driver, url)
    test_pachctl(url, token)

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
    args = parser.parse_args()

    main(args.url, args.username, args.password, args.webdriver, args.headless, args.debug)
