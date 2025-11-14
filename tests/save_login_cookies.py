# tests/save_login_cookies.py
import time
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions

# where to store cookies
COOKIES_FILE = "cookies.json"

def open_browser_for_manual_login():
    options = ChromeOptions()
    # keep browser window visible for manual interaction
    options.add_argument("--start-maximized")
    # Optional: disable automation flags (helps reduce detection)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Optional: use a named user-data-dir to persist across runs
    # options.add_argument(r"--user-data-dir=C:\temp\selenium_profile")

    driver = webdriver.Chrome(options=options)
    return driver

def main():
    driver = open_browser_for_manual_login()
    try:
        driver.get("https://signin.ebay.com/")
        print("Please login manually in the opened browser window. Solve any CAPTCHA if shown.")
        print("After you finish login, press ENTER here to continue and save cookies.")
        input("Press ENTER after login is completed in browser...")

        # quick wait to ensure cookies populated
        time.sleep(2)

        cookies = driver.get_cookies()
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2)
        print(f"Saved {len(cookies)} cookies to {COOKIES_FILE}")
    finally:
        # keep browser open or close? we close to not leave processes
        try:
            driver.quit()
        except Exception:
            pass

if __name__ == "__main__":
    main()
