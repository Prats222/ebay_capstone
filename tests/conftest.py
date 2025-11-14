# # conftest.py
# import pytest
# import allure
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options as ChromeOptions
# from selenium.webdriver.firefox.options import Options as FirefoxOptions
# from selenium.webdriver.edge.options import Options as EdgeOptions
# import time
# import os
#
# def pytest_addoption(parser):
#     """Add custom CLI option: --browser"""
#     parser.addoption(
#         "--browser",
#         action="store",
#         default="chrome",
#         help="Browser to run tests: chrome | firefox | edge",
#     )
#
#
# @pytest.fixture(scope="function")
# def setup_driver(request):
#     browser = request.config.getoption("--browser").lower()
#
#     # inside setup_driver fixture in conftest.py, replace chrome branch with:
#
#     if browser == "chrome":
#         from selenium.webdriver.chrome.options import Options as ChromeOptions
#         options = ChromeOptions()
#
#         # IMPORTANT: point these to your local chrome profile location + profile directory (the name exactly as it appears)
#         user_data_dir = r"C:\Users\prateek.mishra\AppData\Local\Google\Chrome\User Data"
#         profile_dir = "ebay_profile"  # <- your profile name
#
#         # use your profile (do NOT have Chrome open with this profile while test starts)
#         options.add_argument(f"--user-data-dir={user_data_dir}")
#         options.add_argument(f"--profile-directory={profile_dir}")
#
#         # keep other helpful options
#         options.add_argument("--disable-blink-features=AutomationControlled")
#         options.add_experimental_option("excludeSwitches", ["enable-automation"])
#         options.add_experimental_option("useAutomationExtension", False)
#         options.add_argument(
#             "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#             "AppleWebKit/537.36 (KHTML, like Gecko) "
#             "Chrome/120.0.0.0 Safari/537.36"
#         )
#
#         driver = webdriver.Chrome(options=options)
#
#
#     elif browser == "firefox":
#         options = FirefoxOptions()
#         options.set_preference("dom.webdriver.enabled", False)
#         options.set_preference("useAutomationExtension", False)
#         driver = webdriver.Firefox(options=options)
#
#     elif browser == "edge":
#         options = EdgeOptions()
#         options.add_argument("start-maximized")
#         driver = webdriver.Edge(options=options)
#
#     else:
#         raise ValueError(f"Browser '{browser}' is not supported. Use chrome | firefox | edge.")
#
#     driver.maximize_window()
#     yield driver
#
#     # Attach screenshot on failure, but don't die if the session is gone
#     try:
#         if getattr(request.node, "rep_call", None) and request.node.rep_call.failed:
#             try:
#                 png = None
#                 try:
#                     png = driver.get_screenshot_as_png()
#                 except Exception:
#                     png = None
#                 if png:
#                     allure.attach(png, name="screenshot_on_failure", attachment_type=allure.attachment_type.PNG)
#             except Exception as e:
#                 print("teardown screenshot skipped:", e)
#     except Exception:
#         pass
#
#     try:
#         driver.quit()
#     except Exception:
#         pass
#
#
# @pytest.hookimpl(tryfirst=True, hookwrapper=True)
# def pytest_runtest_makereport(item, call):
#     """Hook to capture test result for screenshot on failure"""
#     outcome = yield
#     rep = outcome.get_result()
#     setattr(item, "rep_" + rep.when, rep)


############### Till here cookie wala code ###############


# conftest.py
# import pytest
# import allure
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options as ChromeOptions
# from selenium.webdriver.firefox.options import Options as FirefoxOptions
# from selenium.webdriver.edge.options import Options as EdgeOptions
# import time
#
#
# def pytest_addoption(parser):
#     """Add custom CLI option: --browser"""
#     parser.addoption(
#         "--browser",
#         action="store",
#         default="chrome",
#         help="Browser to run tests: chrome | firefox | edge",
#     )
#
#
# @pytest.fixture(scope="function")
# def setup_driver(request):
#     browser = request.config.getoption("--browser").lower()
#
#     if browser == "chrome":
#         options = ChromeOptions()
#         # keep some anti-detection flags you used previously (optional)
#         options.add_argument("--disable-blink-features=AutomationControlled")
#         options.add_experimental_option("excludeSwitches", ["enable-automation"])
#         options.add_experimental_option("useAutomationExtension", False)
#         options.add_argument(
#             "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#             "AppleWebKit/537.36 (KHTML, like Gecko) "
#             "Chrome/120.0.0.0 Safari/537.36"
#         )
#         # uncomment if you want browser visible but not headless (we want visible for manual captcha)
#         # options.add_argument("--start-maximized")
#
#         driver = webdriver.Chrome(options=options)
#
#     elif browser == "firefox":
#         options = FirefoxOptions()
#         # keep settings that reduce webdriver footprint
#         options.set_preference("dom.webdriver.enabled", False)
#         options.set_preference("useAutomationExtension", False)
#         driver = webdriver.Firefox(options=options)
#
#     elif browser == "edge":
#         options = EdgeOptions()
#         options.add_argument("start-maximized")
#         driver = webdriver.Edge(options=options)
#
#     else:
#         raise ValueError(f"Browser '{browser}' is not supported. Use chrome | firefox | edge.")
#
#     # make comfortable for manual interaction
#     try:
#         driver.maximize_window()
#     except Exception:
#         pass
#
#     yield driver
#
#     # TEARDOWN: attach screenshot on failure (but be robust if session is gone)
#     try:
#         if getattr(request.node, "rep_call", None) and request.node.rep_call.failed:
#             try:
#                 png = None
#                 try:
#                     png = driver.get_screenshot_as_png()
#                 except Exception:
#                     png = None
#                 if png:
#                     allure.attach(png, name="screenshot_on_failure", attachment_type=allure.attachment_type.PNG)
#             except Exception as e:
#                 print("teardown: could not attach screenshot:", e)
#     except Exception:
#         pass
#
#     # always try to quit the driver
#     try:
#         driver.quit()
#     except Exception:
#         pass
#
#
# @pytest.hookimpl(tryfirst=True, hookwrapper=True)
# def pytest_runtest_makereport(item, call):
#     """Hook to capture test result for screenshot on failure - stores rep on item"""
#     outcome = yield
#     rep = outcome.get_result()
#     setattr(item, "rep_" + rep.when, rep)

############ idhar se fresh code for github ####
# conftest.py
import os
import time
import pytest
import allure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions

# local manager (used only outside CI)
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

def pytest_addoption(parser):
    parser.addoption(
        "--browser",
        action="store",
        default="chrome",
        help="Browser to run tests: chrome | firefox | edge",
    )

def _is_ci():
    return bool(os.getenv("CI") or os.getenv("GITHUB_ACTIONS"))

@pytest.fixture(scope="function")
def setup_driver(request):
    browser = request.config.getoption("--browser").lower()

    # ---------- CHROME ----------
    if browser == "chrome":
        options = ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

        if _is_ci():
            # CI: use system-installed chromium & chromedriver
            # Try to set binary_location sensibly for ubuntu runners
            if os.path.exists("/usr/bin/chromium-browser"):
                options.binary_location = "/usr/bin/chromium-browser"
            elif os.path.exists("/usr/bin/chromium"):
                options.binary_location = "/usr/bin/chromium"
            # headless & CI-friendly flags
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            # Use system chromedriver path (installed on the runner)
            service = ChromeService(executable_path="/usr/bin/chromedriver")
        else:
            # Local dev: allow using local Chrome profile, webdriver-manager for chromedriver
            ud = os.getenv("CHROME_USER_DATA")
            pd = os.getenv("CHROME_PROFILE_DIR")
            if ud:
                options.add_argument(f"--user-data-dir={ud}")
            if pd:
                options.add_argument(f"--profile-directory={pd}")
            # do not start headless locally so you can manually solve captchas
            service = ChromeService(ChromeDriverManager().install())

        driver = webdriver.Chrome(service=service, options=options)

    # ---------- FIREFOX ----------
    elif browser == "firefox":
        options = FirefoxOptions()
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        if _is_ci():
            options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)

    # ---------- EDGE ----------
    elif browser == "edge":
        options = EdgeOptions()
        if _is_ci():
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
        else:
            options.add_argument("start-maximized")
        driver = webdriver.Edge(options=options)

    else:
        raise ValueError(f"Browser '{browser}' is not supported. Use chrome | firefox | edge.")

    try:
        driver.maximize_window()
    except Exception:
        pass

    yield driver

    # TEARDOWN: attach screenshot if the test failed (best-effort)
    try:
        if getattr(request.node, "rep_call", None) and request.node.rep_call.failed:
            try:
                png = None
                try:
                    png = driver.get_screenshot_as_png()
                except Exception:
                    png = None
                if png:
                    allure.attach(png, name="screenshot_on_failure", attachment_type=allure.attachment_type.PNG)
            except Exception:
                pass
    except Exception:
        pass

    try:
        driver.quit()
    except Exception:
        pass

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


