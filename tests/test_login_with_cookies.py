# tests/test_login_with_cookies.py
import os
import json
import time
import allure
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

COOKIES_FILE = "cookies.json"

def _open_driver():
    options = ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # options.add_argument(r"--user-data-dir=C:\temp\selenium_profile")  # optional
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    return driver

@allure.epic("E-Commerce Testing")
@allure.feature("User Login")
@allure.severity(allure.severity_level.CRITICAL)
def test_login_using_saved_cookies():
    """
    Load cookies saved earlier, open ebay and assert account UI visible.
    Make sure you ran tests/save_login_cookies.py once before running this.
    """
    if not os.path.exists(COOKIES_FILE):
        pytest.skip("cookies.json not found — run tests/save_login_cookies.py first (manual login).")

    driver = _open_driver()
    wait = WebDriverWait(driver, 20)
    try:
        # navigate to ebay root first to set domain
        driver.get("https://www.ebay.com")
        time.sleep(1)
        # load cookies
        with open(COOKIES_FILE, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        added = 0
        for c in cookies:
            # sanitize cookie fields for Selenium (no 'sameSite' -> older drivers may complain)
            cookie = {k: c[k] for k in c if k in ("name", "value", "path", "domain", "secure", "httpOnly", "expiry")}
            try:
                driver.add_cookie(cookie)
                added += 1
            except Exception:
                # ignore cookie errors (domain mismatch, expiry)
                continue

        print(f"Added {added} cookies from {COOKIES_FILE}")
        driver.get("https://www.ebay.com")  # reload as logged-in user
        time.sleep(2)

        # check heuristics: account menu / my ebay
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[aria-label*='Account'], a[title*='My eBay'], #gh-ug")))
            # Save screenshot
            path = "tests/login_using_cookies.png"
            driver.save_screenshot(path)
            allure.attach.file(path, name="login_using_cookies", attachment_type=allure.attachment_type.PNG)
            print("Login via cookies succeeded.")
        except Exception:
            path = "tests/login_using_cookies_failed.png"
            driver.save_screenshot(path)
            allure.attach.file(path, name="login_using_cookies_failed", attachment_type=allure.attachment_type.PNG)
            pytest.fail("Login via cookies did not detect account UI — cookies may be invalid/expired.")
    finally:
        try:
            driver.quit()
        except Exception:
            pass
