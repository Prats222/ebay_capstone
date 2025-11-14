# tests/test_login.py
import os
import time
import datetime
import pytest
import allure
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementNotInteractableException, TimeoutException

load_dotenv()  # loads EBAY_EMAIL & EBAY_PASSWORD from project root .env

# Config
CAPTCHA_WAIT_TIMEOUT_SECONDS = 180   # how long to wait for manual CAPTCHA (adjust as needed)
CAPTCHA_POLL_INTERVAL = 3            # poll interval while waiting
EMAIL_RETRY_ON_OOPS = True
VERIFY_LOGIN_TIMEOUT = 20            # strict verification wait for account UI


def _has_captcha(driver):
    """Heuristic detection of captcha / verification step"""
    try:
        if driver.find_elements(By.CSS_SELECTOR, "iframe[src*='hcaptcha'], iframe[src*='recaptcha']"):
            return True
        body = ""
        try:
            body = (driver.find_element(By.TAG_NAME, "body").text or "").lower()
        except Exception:
            body = ""
        if any(token in body for token in ("please verify yourself", "please verify", "verify yourself", "security check", "select the images", "i am not a robot")):
            return True
        if driver.find_elements(By.CSS_SELECTOR, ".h-captcha, .h-captcha-checkbox, .g-recaptcha, .captcha"):
            return True
    except Exception:
        return False
    return False


def _email_oops_present(driver):
    try:
        el = driver.find_elements(By.XPATH, "//*[contains(., \"Oops, that's not a match\") or contains(., \"Oops, that isn't a match\") or contains(., 'not a match')]")
        return bool(el)
    except Exception:
        return False


def _verify_logged_in_strict(driver, timeout=VERIFY_LOGIN_TIMEOUT):
    """
    Strict verification that the user is logged in:
      - Must find a visible account element (Account button, My eBay) within timeout
      - And current URL should not contain 'signin'
    Returns True only if confident.
    """
    try:
        wait = WebDriverWait(driver, timeout)
        # Wait for any of the account UI elements to be visible
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "button[aria-label*='Account'], a[title*='My eBay'], #gh-ug")))
        # also ensure url moved away from signin
        time.sleep(0.5)
        cur = ""
        try:
            cur = driver.current_url.lower()
        except Exception:
            cur = ""
        if "signin" in cur:
            return False
        return True
    except Exception:
        return False


def _save_debug(driver, prefix="login"):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    png = f"tests/{prefix}_screenshot_{ts}.png"
    html = f"tests/{prefix}_page_{ts}.html"
    try:
        driver.save_screenshot(png)
    except Exception:
        try:
            with open(png, "wb") as f:
                f.write(driver.get_screenshot_as_png())
        except Exception:
            pass
    try:
        with open(html, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    except Exception:
        pass
    return png, html


# ---------- ROBUST pre-email wait + enter_email replacement ----------
def _wait_for_userid_clickable(driver, timeout=20):
    """Wait until the userid field is present and looks interactable (displayed + enabled).
       Returns the WebElement or raises TimeoutException.
    """
    end = time.time() + timeout
    while time.time() < end:
        try:
            els = driver.find_elements(By.ID, "userid")
            if not els:
                time.sleep(0.4)
                continue
            el = els[0]
            # element must be displayed & enabled
            try:
                if not (el.is_displayed() and el.is_enabled()):
                    time.sleep(0.4)
                    continue
            except Exception:
                time.sleep(0.4)
                continue

            # Try to ensure it's not covered by some overlay: check elementFromPoint at element's center
            try:
                rect = driver.execute_script(
                    "const r = arguments[0].getBoundingClientRect(); return {x: Math.floor(r.left + r.width/2), y: Math.floor(r.top + r.height/2)};",
                    el
                )
                if rect and isinstance(rect, dict):
                    x, y = rect.get("x"), rect.get("y")
                    # scroll into view
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                    top_el = None
                    try:
                        top_el = driver.execute_script("return document.elementFromPoint(arguments[0], arguments[1]);", x, y)
                    except Exception:
                        top_el = None
                    if top_el:
                        # If elementFromPoint is the same element or a descendant, assume not covered
                        is_child = driver.execute_script(
                            "let t = arguments[0]; let el = arguments[1]; while(t){ if(t === el) return true; t = t.parentElement;} return false;",
                            top_el, el
                        )
                        if not is_child:
                            # covered by overlay, wait and retry
                            time.sleep(0.6)
                            continue
            except Exception:
                # if this check fails for any reason, ignore and proceed
                pass

            return el
        except Exception:
            time.sleep(0.4)
            continue
    raise TimeoutException("userid element not clickable/visible within timeout")


def _robust_set_input_value(driver, el, value):
    """Try send_keys, then JS fallback that sets value, removes readonly/disabled and dispatches events."""
    try:
        el.clear()
    except Exception:
        pass
    try:
        el.send_keys(value)
        return True
    except Exception:
        # fallback: use JS to set value and dispatch events
        try:
            js = """
            const el = arguments[0];
            const v = arguments[1];
            try { el.removeAttribute('readonly'); } catch(e) {}
            try { el.removeAttribute('disabled'); } catch(e) {}
            el.focus();
            el.value = v;
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
            return true;
            """
            driver.execute_script(js, el, value)
            time.sleep(0.3)
            return True
        except Exception:
            return False


def _pre_email_wait_and_enter(driver, EMAIL):
    """
    Wait until either email/password field appears or captcha appears.
    If captcha appears first, wait for manual solve.
    Then robustly enter email (with retries) and submit.
    """
    start = time.time()
    found = False
    PRE_EMAIL_TIMEOUT = CAPTCHA_WAIT_TIMEOUT_SECONDS
    while time.time() - start < PRE_EMAIL_TIMEOUT:
        try:
            # If password field present already (rare), proceed
            if driver.find_elements(By.ID, "pass"):
                found = True
                break

            # Quick check: if userid is present and visible, consider found (detailed check before typing)
            try:
                els = driver.find_elements(By.ID, "userid")
                if els and els[0].is_displayed() and els[0].is_enabled():
                    found = True
                    break
            except Exception:
                pass

            # If captcha present, screenshot and wait for manual solve
            if _has_captcha(driver):
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                path = f"tests/login_pre_captcha_{ts}.png"
                try:
                    driver.save_screenshot(path)
                except Exception:
                    try:
                        with open(path, "wb") as f:
                            f.write(driver.get_screenshot_as_png())
                    except Exception:
                        pass
                try:
                    allure.attach.file(path, name="pre_captcha_screenshot", attachment_type=allure.attachment_type.PNG)
                except Exception:
                    pass

                print("⚠️ CAPTCHA detected BEFORE email step. Please solve it manually in the opened browser.")
                # poll captcha disappearance
                captcha_start = time.time()
                while time.time() - captcha_start < PRE_EMAIL_TIMEOUT:
                    if not _has_captcha(driver):
                        time.sleep(1.0)
                        break
                    time.sleep(CAPTCHA_POLL_INTERVAL)
            else:
                time.sleep(0.8)
        except Exception:
            time.sleep(0.8)
            continue

    if not found:
        png, html = _save_debug(driver, prefix="login_pre_open_timeout")
        try:
            allure.attach.file(png, name="pre_open_timeout_screenshot", attachment_type=allure.attachment_type.PNG)
            allure.attach.file(html, name="pre_open_timeout_html", attachment_type=allure.attachment_type.HTML)
        except Exception:
            pass
        pytest.fail("Timeout: neither email nor password field appeared and/or pre-email CAPTCHA wasn't solved in time.")

    # robust enter_email that retries if page reloads / field not interactable
    def enter_email(max_attempts=4):
        attempt = 0
        last_exc = None
        while attempt < max_attempts:
            attempt += 1
            try:
                el = _wait_for_userid_clickable(driver, timeout=10)
                # fresh reference in case of reload
                el = driver.find_element(By.ID, "userid")
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                except Exception:
                    pass

                ok = _robust_set_input_value(driver, el, EMAIL)
                if not ok:
                    last_exc = Exception("Could not set email into userid via send_keys or JS fallback")
                    time.sleep(0.8)
                    continue

                # click continue
                try:
                    btn = driver.find_element(By.ID, "signin-continue-btn")
                    try:
                        btn.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", btn)
                except Exception:
                    try:
                        el.submit()
                    except Exception:
                        pass

                # small pause to let page react
                time.sleep(1.2)
                return True
            except TimeoutException as te:
                last_exc = te
                time.sleep(0.6)
                continue
            except Exception as e:
                last_exc = e
                time.sleep(0.6)
                continue

        # exhausted attempts -> fail with evidence
        png, html = _save_debug(driver, prefix="login_enter_email_failed")
        try:
            allure.attach.file(png, name="enter_email_failed_screenshot", attachment_type=allure.attachment_type.PNG)
            allure.attach.file(html, name="enter_email_failed_html", attachment_type=allure.attachment_type.HTML)
        except Exception:
            pass
        pytest.fail(f"Could not interact with email input after {max_attempts} attempts. Last error: {last_exc}")

    # run the enter_email helper
    return enter_email()


# ---------- END of robust replacement ----------


@allure.epic("E-Commerce Testing")
@allure.feature("User Login")
@allure.story("Login functionality verification (strict)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify user login on eBay (strict — fail on CAPTCHA/loop)")
def test_user_login(setup_driver):
    """
    Strict login test:
      - reads credentials from .env
      - attempts login, handles captcha by waiting (manual) up to CAPTCHA_WAIT_TIMEOUT_SECONDS
      - verifies success strictly; if not successful -> fail with screenshot + page html
    """
    driver = setup_driver
    wait = WebDriverWait(driver, 15)

    EMAIL = os.getenv("EBAY_EMAIL")
    PASSWORD = os.getenv("EBAY_PASSWORD")

    if not EMAIL or not PASSWORD:
        pytest.skip("⚠️ Please set EBAY_EMAIL and EBAY_PASSWORD in your .env file.")

    # navigate to signin
    try:
        driver.get("https://signin.ebay.com/")
    except Exception:
        pytest.fail("Could not open eBay signin URL.")

    # Use the robust pre-email wait & enter helper (handles pre-captcha, reloads and retries)
    _pre_email_wait_and_enter(driver, EMAIL)

    # If captcha/verification occurs after entering email — wait for manual solve (strict)
    if _has_captcha(driver):
        print("⚠️ CAPTCHA detected after entering email. Please solve it manually in the opened browser.")
        start = time.time()
        solved = False
        while time.time() - start < CAPTCHA_WAIT_TIMEOUT_SECONDS:
            if not _has_captcha(driver):
                # sometimes after solving captcha, the signin page may reload — break to re-evaluate
                solved = True
                break
            time.sleep(CAPTCHA_POLL_INTERVAL)
        if not solved:
            png, html = _save_debug(driver, prefix="login_captcha")
            try:
                allure.attach.file(png, name="captcha_screenshot", attachment_type=allure.attachment_type.PNG)
                allure.attach.file(html, name="captcha_page", attachment_type=allure.attachment_type.HTML)
            except Exception:
                pass
            pytest.fail(f"CAPTCHA detected and not solved within {CAPTCHA_WAIT_TIMEOUT_SECONDS} seconds. Saved {png} and {html} as evidence.")

    # If "Oops" banner present — optionally retry email once slowly
    if _email_oops_present(driver) and EMAIL_RETRY_ON_OOPS:
        print("🔁 Email error banner seen — retrying email once slowly.")
        time.sleep(1)
        _pre_email_wait_and_enter(driver, EMAIL)
        time.sleep(1)

    # Wait for password field (if not present, fail)
    try:
        wait.until(EC.presence_of_element_located((By.ID, "pass")))
    except Exception:
        # If there's no password field, bail and capture evidence
        png, html = _save_debug(driver, prefix="login_no_pass")
        try:
            allure.attach.file(png, name="no_pass_screenshot", attachment_type=allure.attachment_type.PNG)
            allure.attach.file(html, name="no_pass_page", attachment_type=allure.attachment_type.HTML)
        except Exception:
            pass
        pytest.fail("Password step not visible after email entry. See saved screenshot and page HTML.")

    # Enter password (robust) and submit
    try:
        pw = driver.find_element(By.ID, "pass")
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", pw)
        except Exception:
            pass
        try:
            pw.clear()
            pw.send_keys(PASSWORD)
        except ElementNotInteractableException:
            # fallback JS setter
            driver.execute_script("""
                const el = arguments[0]; const v = arguments[1];
                el.value = v;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            """, pw, PASSWORD)
    except Exception:
        png, html = _save_debug(driver, prefix="login_pw_find_failed")
        try:
            allure.attach.file(png, name="pw_find_failed", attachment_type=allure.attachment_type.PNG)
            allure.attach.file(html, name="pw_find_failed_html", attachment_type=allure.attachment_type.HTML)
        except Exception:
            pass
        pytest.fail("Could not find or populate password field.")

    # Click sign in button reliably
    try:
        try:
            sign_in_btn = driver.find_element(By.ID, "sgnBt")
        except Exception:
            sign_in_btn = driver.find_element(By.XPATH, "//button[@type='submit' or contains(., 'Sign in')]")
        try:
            sign_in_btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", sign_in_btn)
    except Exception:
        png, html = _save_debug(driver, prefix="login_click_failed")
        try:
            allure.attach.file(png, name="login_click_failed", attachment_type=allure.attachment_type.PNG)
            allure.attach.file(html, name="login_click_failed_html", attachment_type=allure.attachment_type.HTML)
        except Exception:
            pass
        pytest.fail("Could not click Sign in button.")

    # Now strictly verify logged in
    if _verify_logged_in_strict(driver, timeout=VERIFY_LOGIN_TIMEOUT):
        # success: save screenshot for proof
        try:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            s = f"tests/login_success_{ts}.png"
            driver.save_screenshot(s)
            try:
                allure.attach.file(s, name="login_success", attachment_type=allure.attachment_type.PNG)
            except Exception:
                pass
            print("✅ Login successful — saved screenshot:", s)
        except Exception:
            pass
        assert True
    else:
        png, html = _save_debug(driver, prefix="login_failed_final")
        try:
            allure.attach.file(png, name="login_failed_final_screenshot", attachment_type=allure.attachment_type.PNG)
            allure.attach.file(html, name="login_failed_final_html", attachment_type=allure.attachment_type.HTML)
        except Exception:
            pass
        pytest.fail("Login failed — account UI not detected after sign-in attempt. See saved screenshot + HTML for evidence.")
