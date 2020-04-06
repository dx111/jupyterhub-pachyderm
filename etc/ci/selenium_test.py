#!/usr/bin/env python3

import sys
import time

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

MAX_LOAD_COUNT = 10

def main(webdriver_path, url, username, password):
    opts = Options()
    opts.headless = True
    driver = webdriver.Firefox(executable_path=webdriver_path, options=opts)

    # Login
    driver.get(url)
    username_field = driver.find_element_by_id("username_input")
    username_field.send_keys(username)
    password_field = driver.find_element_by_id("password_input")
    password_field.send_keys(password)
    driver.find_element_by_id("login_submit").click()

    # See if we're on the loading page
    load_count = 0
    while driver.title == "JupyterHub":
        load_count += 1
        assert load_count < MAX_LOAD_COUNT, "waited too long for JupyterHub user homepage to load"
        time.sleep(3.0)

    # Verify we're logged in
    assert driver.title == "Home Page - Select or create a notebook", "not in the user homepage"

    driver.quit()

if __name__ == '__main__':
    webdriver_path = sys.argv[1]
    url = sys.argv[2]
    username = sys.argv[3]
    password = sys.argv[4]
    main(webdriver_path, url, username, password)
