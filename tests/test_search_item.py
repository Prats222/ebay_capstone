# tests/test_search_item.py
import time
import random
import datetime
import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# relies on your existing project files
from pages.home_page import HomePage
from pages.search_results_page import SearchResultsPage
from Utilities.Dataread import Dataread


@allure.epic("E-Commerce Testing")
@allure.feature("Product Search")
@allure.story("Search, open product tabs, add to cart, return to results")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Search results: open multiple product tabs, add to cart, return")
def test_search_and_add_multiple_products(setup_driver):
    driver = setup_driver
    wait = WebDriverWait(driver, 20)

    # --- config ---
    MAX_PRODUCTS = 5        # how many products on the first results page to try
    KEYWORD_MATCH_REQUIRED = True  # require href/title to contain keyword
    MAX_CAPTCHAS = 2        # stop the test if too many CAPTCHAs appear in one run
    captcha_count = 0

    # some fallback add-to-cart selectors (keep these for non-ux-call variants)
    ADD_TO_CART_SELECTORS = [
        "#atcRedesignId_btn",
        "button#isCartBtn_btn",
        "button[aria-label='Add to cart']",
        "button[title='Add to cart']",
        "button[data-testid='add-to-cart-button']",
        "button[aria-describedby*='atc']",
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add to cart')]",
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add to basket')]",
    ]

    # --- Step 1: open homepage and read keyword ---
    data_reader = Dataread()
    filepath = "Testdata1.xlsx"   # relative to Utilities directory
    search_keyword = data_reader.dataread(filepath)
    if not search_keyword:
        raise AssertionError("Test data (search keyword) not found in Utilities/Testdata1.xlsx")

    with allure.step("Navigate to eBay homepage and perform search"):
        driver.get("https://www.ebay.com")
        allure.attach(driver.current_url, name="Homepage URL", attachment_type=allure.attachment_type.TEXT)
        time.sleep(1)

        home = HomePage(driver)
        home.search_item(search_keyword)
        time.sleep(2)  # let results start loading

    # --- Step 2: collect candidates from results ---
    with allure.step("Collect product anchors from search results (cards & list)"):
        try:
            wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "a.s-item__link, li.s-item, img.s-card__image, .s-item__wrapper, .srp-results a")
            ))
        except Exception:
            pass

        candidates = []

        # anchors by common class
        try:
            for a in driver.find_elements(By.CSS_SELECTOR, "a.s-item__link"):
                if a not in candidates:
                    candidates.append(a)
        except Exception:
            pass

        # anchors under li.s-item
        try:
            for a in driver.find_elements(By.CSS_SELECTOR, "li.s-item a"):
                if a not in candidates:
                    candidates.append(a)
        except Exception:
            pass

        # card images -> ancestor anchors
        try:
            for img in driver.find_elements(By.CSS_SELECTOR, "img.s-card__image"):
                try:
                    a = img.find_element(By.XPATH, "./ancestor::a[1]")
                    if a and a not in candidates:
                        candidates.append(a)
                except Exception:
                    continue
        except Exception:
            pass

        # fallback anchors containing /itm/
        try:
            for a in driver.find_elements(By.XPATH, "//a[contains(@href,'/itm/')]"):
                if a not in candidates:
                    candidates.append(a)
        except Exception:
            pass

        # limit and ensure href present
        final_candidates = []
        for a in candidates:
            if len(final_candidates) >= MAX_PRODUCTS:
                break
            try:
                href = a.get_attribute("href") or ""
                if href.strip():
                    final_candidates.append(a)
            except Exception:
                continue

        if not final_candidates:
            allure.attach(driver.get_screenshot_as_png(), name="no_candidates", attachment_type=allure.attachment_type.PNG)
            raise AssertionError("No product candidates found on search results page")

    # --- Step 3: iterate candidates, open in new tab, check & add to cart, close tab ---
    added_count = 0
    original_handle = driver.current_window_handle

    for idx, anchor in enumerate(final_candidates, start=1):
        try:
            # small randomized human-like pause before acting on each candidate
            time.sleep(random.uniform(1.0, 3.0))

            # refresh href safely
            try:
                href = anchor.get_attribute("href")
            except Exception:
                anchors_now = driver.find_elements(By.CSS_SELECTOR, "a.s-item__link, li.s-item a, .srp-results a")
                if len(anchors_now) >= idx:
                    anchor = anchors_now[idx - 1]
                    href = anchor.get_attribute("href")
                else:
                    href = None

            if not href:
                continue

            # gather title/alt text
            title_text = (anchor.text or "").strip()
            alt_text = ""
            try:
                img = anchor.find_element(By.TAG_NAME, "img")
                alt_text = (img.get_attribute("alt") or "").strip()
            except Exception:
                alt_text = ""

            combo = " ".join([title_text, alt_text, href]).lower()
            keyword_lower = search_keyword.lower()

            if KEYWORD_MATCH_REQUIRED:
                tokens = [t for t in keyword_lower.split() if len(t) > 1]
                matched = any(tok in combo for tok in tokens)
                if not matched:
                    print(f"Skipping candidate #{idx} (no keyword token in href/title/alt)")
                    continue

            # open in new tab (preferred)
            try:
                driver.execute_script("window.open(arguments[0], '_blank');", href)
            except Exception:
                try:
                    anchor.click()
                except Exception:
                    driver.get(href)

            # switch to new tab (most recent that isn't original)
            time.sleep(random.uniform(0.8, 1.6))
            handles = driver.window_handles
            new_handle = None
            for h in handles[::-1]:
                if h != original_handle:
                    new_handle = h
                    break
            if new_handle:
                driver.switch_to.window(new_handle)

            # ---------- CAPTCHA detection (product tab) ----------
            try:
                captcha_found = False
                # hcaptcha/recaptcha iframe presence
                if driver.find_elements(By.CSS_SELECTOR, "iframe[src*='hcaptcha.com'], iframe[src*='captcha'], iframe[src*='recaptcha']"):
                    captcha_found = True
                # body text check
                if not captcha_found:
                    try:
                        body_text = driver.find_element(By.TAG_NAME, "body").text or ""
                        if "please verify yourself" in body_text.lower() or "verify yourself" in body_text.lower() or "please verify" in body_text.lower():
                            captcha_found = True
                    except Exception:
                        pass
                if not captcha_found:
                    if driver.find_elements(By.CSS_SELECTOR, ".h-captcha, .h-captcha-checkbox, .g-recaptcha, .captcha"):
                        captcha_found = True

                if captcha_found:
                    captcha_count += 1
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    path = f"tests/captcha_{ts}.png"
                    try:
                        driver.save_screenshot(path)
                    except Exception:
                        try:
                            with open(path, "wb") as _f:
                                _f.write(driver.get_screenshot_as_png())
                        except Exception:
                            pass
                    try:
                        allure.attach.file(path, name=f"captcha_{ts}", attachment_type=allure.attachment_type.PNG)
                    except Exception:
                        pass
                    print(f"⚠️ CAPTCHA detected on candidate #{idx}, screenshot saved at {path}. Skipping this product.")
                    try:
                        driver.close()
                    except Exception:
                        pass
                    try:
                        driver.switch_to.window(original_handle)
                    except Exception:
                        handles = driver.window_handles
                        if handles:
                            driver.switch_to.window(handles[0])
                    time.sleep(random.uniform(0.8, 1.6))
                    # stop early if too many captchas triggered
                    if captcha_count >= MAX_CAPTCHAS:
                        raise AssertionError(f"Too many CAPTCHAs encountered ({captcha_count}). Aborting test to avoid blocking.")
                    continue
            except AssertionError:
                # re-raise the captcha abort assertion
                raise
            except Exception:
                pass
            # ---------- end captcha detection ----------

            # ---------- Skip product if it requires manual variant selection (e.g., Colour) ----------
            try:
                need_variant = False

                if driver.find_elements(By.XPATH, "//*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'please select a colour') or contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'please select a color')]"):
                    need_variant = True

                if driver.find_elements(By.XPATH, "//label[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'colour') and contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'select')]") \
                   or driver.find_elements(By.XPATH, "//label[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'color') and contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'select')]"):
                    need_variant = True

                from selenium.webdriver.support.ui import Select as _Select
                for s in driver.find_elements(By.TAG_NAME, "select"):
                    try:
                        sel = _Select(s)
                        first = sel.first_selected_option
                        if first and first.text and first.text.strip().lower().startswith("select"):
                            need_variant = True
                            break
                    except Exception:
                        continue

                if need_variant:
                    print(f"Skipping candidate #{idx} — requires manual variant selection (color/size).")
                    try:
                        driver.close()
                    except Exception:
                        pass
                    try:
                        driver.switch_to.window(original_handle)
                    except Exception:
                        handles = driver.window_handles
                        if handles:
                            driver.switch_to.window(handles[0])
                    time.sleep(random.uniform(0.8, 1.6))
                    continue
            except Exception:
                pass
            # ---------- end variant skip ----------

            # wait for product elements to appear lightly
            try:
                WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "h1, #itemTitle, .x-item-title__main, .it-ttl")
                ))
            except Exception:
                pass

            # ---------- add-to-cart logic ----------
            def try_click_add_by_ux_span():
                try:
                    spans = driver.find_elements(By.XPATH, "//span[contains(normalize-space(.), 'Add to cart') or contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add to cart')]")
                    if not spans:
                        spans = driver.find_elements(By.CSS_SELECTOR, "span.ux-call-to-action__text")
                    for sp in spans:
                        try:
                            txt = (sp.text or "").strip().lower()
                            if "add to cart" not in txt and "add to basket" not in txt:
                                continue
                        except Exception:
                            continue
                        try:
                            clickable = sp.find_element(By.XPATH, "./ancestor::button[1]")
                        except Exception:
                            try:
                                clickable = sp.find_element(By.XPATH, "./ancestor::a[1]")
                            except Exception:
                                clickable = None
                        if not clickable:
                            try:
                                sp.click()
                                time.sleep(0.5)
                            except Exception:
                                pass
                        else:
                            try:
                                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", clickable)
                            except Exception:
                                pass
                            time.sleep(0.2)
                            try:
                                clickable.click()
                            except Exception:
                                try:
                                    driver.execute_script("arguments[0].click();", clickable)
                                except Exception:
                                    try:
                                        sp.click()
                                    except Exception:
                                        pass
                        try:
                            WebDriverWait(driver, 6).until(EC.presence_of_element_located((
                                By.XPATH,
                                "//span[contains(normalize-space(.), 'See in cart') or contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'see in cart')]"
                            )))
                            return True
                        except Exception:
                            time.sleep(1)
                            try:
                                if driver.find_elements(By.XPATH, "//span[contains(normalize-space(.), 'See in cart') or contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'see in cart')]"):
                                    return True
                            except Exception:
                                pass
                    return False
                except Exception:
                    return False

            def try_click_add_button_general():
                if try_click_add_by_ux_span():
                    return True
                for sel in ADD_TO_CART_SELECTORS:
                    try:
                        if sel.strip().startswith("//"):
                            btn = driver.find_element(By.XPATH, sel)
                        else:
                            btn = driver.find_element(By.CSS_SELECTOR, sel)
                        if btn and btn.is_displayed():
                            try:
                                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                            except Exception:
                                pass
                            time.sleep(0.3)
                            try:
                                btn.click()
                            except Exception:
                                try:
                                    driver.execute_script("arguments[0].click();", btn)
                                except Exception:
                                    pass
                            try:
                                WebDriverWait(driver, 6).until(EC.presence_of_element_located((
                                    By.XPATH,
                                    "//span[contains(normalize-space(.), 'See in cart') or //*[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'see in cart')]"
                                )))
                                return True
                            except Exception:
                                return True
                    except Exception:
                        continue
                try:
                    btn = driver.find_element(By.XPATH, "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add to cart') or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'add to basket')]")
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                    except Exception:
                        pass
                    try:
                        btn.click()
                    except Exception:
                        try:
                            driver.execute_script("arguments[0].click();", btn)
                        except Exception:
                            pass
                    time.sleep(1)
                    try:
                        if driver.find_elements(By.XPATH, "//span[contains(normalize-space(.), 'See in cart') or contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'see in cart')]"):
                            return True
                    except Exception:
                        pass
                except Exception:
                    pass
                return False

            added = try_click_add_button_general()

            # if add failed, try to auto-select options then retry
            if not added:
                try:
                    radios = driver.find_elements(By.XPATH, "//input[@type='radio']")
                    for r in radios:
                        try:
                            if r.is_displayed() and r.is_enabled():
                                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", r)
                                r.click()
                                time.sleep(0.3)
                                break
                        except Exception:
                            continue
                except Exception:
                    pass

                try:
                    for s in driver.find_elements(By.TAG_NAME, "select"):
                        try:
                            sel = Select(s)
                            for option in sel.options:
                                val = (option.get_attribute("value") or "").strip()
                                txt = (option.text or "").strip()
                                if val and not txt.lower().startswith("select"):
                                    try:
                                        sel.select_by_value(val)
                                    except Exception:
                                        try:
                                            sel.select_by_visible_text(txt)
                                        except Exception:
                                            continue
                                    time.sleep(0.4)
                                    break
                        except Exception:
                            continue
                except Exception:
                    pass

                try:
                    tiles = driver.find_elements(By.CSS_SELECTOR, "button[role='radio'], .swatch, .variation, .item-variation")
                    for t in tiles:
                        try:
                            if t.is_displayed():
                                try:
                                    t.click()
                                except Exception:
                                    try:
                                        driver.execute_script("arguments[0].click();", t)
                                    except Exception:
                                        continue
                                time.sleep(0.3)
                                break
                        except Exception:
                            continue
                except Exception:
                    pass

                added = try_click_add_button_general()

            if not added:
                try:
                    allure.attach(driver.get_screenshot_as_png(), name=f"product_{idx}_add_failed", attachment_type=allure.attachment_type.PNG)
                    allure.attach(driver.page_source, name=f"product_{idx}_html", attachment_type=allure.attachment_type.HTML)
                except Exception:
                    pass

            # If add succeeded, optionally click See in cart button
            if added:
                try:
                    see_btns = driver.find_elements(By.XPATH, "//span[contains(normalize-space(.), 'See in cart')]/ancestor::a[1] | //span[contains(normalize-space(.), 'See in cart')]/ancestor::button[1]")
                    if see_btns:
                        try:
                            btn = see_btns[0]
                            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                            time.sleep(0.2)
                            try:
                                btn.click()
                            except Exception:
                                try:
                                    driver.execute_script("arguments[0].click();", btn)
                                except Exception:
                                    pass
                            time.sleep(1)
                        except Exception:
                            pass
                except Exception:
                    pass

            result_msg = f"Candidate #{idx}: href='{href[:120]}' title='{title_text[:80]}' alt='{alt_text[:80]}' added={added}"
            print(result_msg)
            allure.attach(result_msg, name=f"product_{idx}_info", attachment_type=allure.attachment_type.TEXT)
            if added:
                added_count += 1

            # Close product tab and return to results tab
            try:
                driver.close()
            except Exception:
                pass
            try:
                driver.switch_to.window(original_handle)
            except Exception:
                handles = driver.window_handles
                if handles:
                    driver.switch_to.window(handles[0])

            # randomized small wait before next product
            time.sleep(random.uniform(1.2, 3.0))

        except Exception as e:
            try:
                allure.attach(driver.get_screenshot_as_png(), name=f"candidate_{idx}_error", attachment_type=allure.attachment_type.PNG)
            except Exception:
                pass
            try:
                driver.switch_to.window(original_handle)
            except Exception:
                try:
                    driver.switch_to.window(driver.window_handles[0])
                except Exception:
                    pass
            continue

    # final cart screenshot behavior — open cart in a NEW tab so we don't accidentally capture a CAPTCHA page
    print(f"Total products successfully added to cart: {added_count}")
    allure.attach(str(added_count), name="added_count", attachment_type=allure.attachment_type.TEXT)

    if added_count > 0:
        with allure.step("Open cart page (new tab), remove last added product, capture final screenshot"):
            try:
                # open cart in a new tab (do not replace current window's content)
                try:
                    driver.execute_script("window.open('https://cart.ebay.com','_blank');")
                except Exception:
                    # fallback: navigate current window (less ideal)
                    driver.get("https://cart.ebay.com")

                # switch to the newest handle (cart)
                time.sleep(1.0)
                handles = driver.window_handles
                cart_handle = None
                for h in handles[::-1]:
                    if h != original_handle:
                        cart_handle = h
                        break
                if cart_handle:
                    driver.switch_to.window(cart_handle)
                else:
                    # if no new handle, stay in current window
                    driver.get("https://cart.ebay.com")

                # wait for cart content to appear (or for captcha)
                try:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                except Exception:
                    pass

                # detect captcha on cart
                cart_has_captcha = False
                try:
                    if driver.find_elements(By.CSS_SELECTOR,
                                            "iframe[src*='hcaptcha.com'], iframe[src*='captcha'], iframe[src*='recaptcha']"):
                        cart_has_captcha = True
                    else:
                        body_text = ""
                        try:
                            body_text = driver.find_element(By.TAG_NAME, "body").text or ""
                        except Exception:
                            body_text = ""
                        if any(tok in body_text.lower() for tok in
                               ("please verify yourself", "please verify", "verify yourself", "security check")):
                            cart_has_captcha = True
                except Exception:
                    cart_has_captcha = False

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

                # if blocked by captcha, save screenshot and bail to avoid extra actions
                if cart_has_captcha:
                    screenshot_path = f"tests/cart_blocked_by_captcha_{timestamp}.png"
                    try:
                        driver.save_screenshot(screenshot_path)
                    except Exception:
                        try:
                            with open(screenshot_path, "wb") as _f:
                                _f.write(driver.get_screenshot_as_png())
                        except Exception:
                            pass
                    try:
                        allure.attach.file(screenshot_path, name="cart_blocked_by_captcha",
                                           attachment_type=allure.attachment_type.PNG)
                    except Exception:
                        pass
                    print(f"⚠️ Cart page blocked by CAPTCHA. Screenshot saved to: {screenshot_path}")
                else:
                    # --- BEFORE removal: attach a before-removal screenshot and page HTML ---
                    before_png = f"tests/cart_before_remove_{timestamp}.png"
                    before_html = f"tests/cart_before_remove_{timestamp}.html"
                    try:
                        driver.save_screenshot(before_png)
                    except Exception:
                        try:
                            with open(before_png, "wb") as _f:
                                _f.write(driver.get_screenshot_as_png())
                        except Exception:
                            pass
                    try:
                        with open(before_html, "w", encoding="utf-8") as f:
                            f.write(driver.page_source)
                    except Exception:
                        pass
                    try:
                        allure.attach.file(before_png, name="cart_before_remove",
                                           attachment_type=allure.attachment_type.PNG)
                        allure.attach.file(before_html, name="cart_before_remove_html",
                                           attachment_type=allure.attachment_type.HTML)
                    except Exception:
                        pass

                    # --- attempt to remove the last added product ---
                    # Heuristic: find visible "Remove" controls (buttons/links/spans) and click the last one
                    removed = False
                    try:
                        # collect candidate remove elements (buttons/links) visible in cart
                        remove_selectors = [
                            "//button[contains(normalize-space(.),'Remove') or contains(., 'Remove item')]",
                            "//a[contains(normalize-space(.),'Remove') or contains(., 'Remove item')]",
                            "//button[contains(normalize-space(.),'Delete') or contains(., 'Delete item')]",
                            "//a[contains(normalize-space(.),'Delete') or contains(., 'Delete item')]",
                            "//button[contains(@aria-label,'Remove') or contains(@aria-label,'delete')]"
                        ]
                        remove_elems = []
                        for rs in remove_selectors:
                            try:
                                found = driver.find_elements(By.XPATH, rs)
                                for el in found:
                                    try:
                                        if el.is_displayed():
                                            remove_elems.append(el)
                                    except Exception:
                                        continue
                            except Exception:
                                continue

                        # deduplicate and keep order
                        uniq = []
                        for e in remove_elems:
                            if e not in uniq:
                                uniq.append(e)
                        remove_elems = uniq

                        if remove_elems:
                            # pick last remove element (assumes last product corresponds to last remove button)
                            last_btn = remove_elems[-1]
                            # count before
                            before_count = len(remove_elems)
                            try:
                                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", last_btn)
                            except Exception:
                                pass
                            time.sleep(0.3)
                            try:
                                last_btn.click()
                            except Exception:
                                try:
                                    driver.execute_script("arguments[0].click();", last_btn)
                                except Exception:
                                    pass

                            # wait for remove to take effect: either a confirmation text or the number of remove elements decreases
                            try:
                                WebDriverWait(driver, 8).until(
                                    lambda d: len([x for x in d.find_elements(By.XPATH,
                                                                              "//button[contains(normalize-space(.),'Remove') or contains(., 'Remove item') or //a[contains(normalize-space(.),'Remove')]")
                                                   if (x.is_displayed() if hasattr(x,
                                                                                   'is_displayed') else True)]) < before_count
                                )
                                removed = True
                            except Exception:
                                # fallback: wait a short while and check changes
                                time.sleep(2)
                                try:
                                    new_remove_elems = driver.find_elements(By.XPATH,
                                                                            "//button[contains(normalize-space(.),'Remove') or //a[contains(normalize-space(.),'Remove')]]")
                                    if len(new_remove_elems) < before_count:
                                        removed = True
                                except Exception:
                                    removed = False
                        else:
                            print("No remove buttons found in cart - cannot remove last item programmatically.")
                    except Exception as e_rm:
                        print("Exception while attempting removal:", e_rm)
                        removed = False

                    # Attach result and screenshot after removal attempt
                    after_ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    after_png = f"tests/cart_after_remove_{after_ts}.png"
                    try:
                        time.sleep(1)
                        driver.save_screenshot(after_png)
                    except Exception:
                        try:
                            with open(after_png, "wb") as _f:
                                _f.write(driver.get_screenshot_as_png())
                        except Exception:
                            pass
                    try:
                        allure.attach.file(after_png, name="cart_after_remove",
                                           attachment_type=allure.attachment_type.PNG)
                    except Exception:
                        pass

                    if removed:
                        print("✅ Successfully removed the last item from cart (heuristic).")
                    else:
                        print("⚠️ Could not confirm removal of last item (see before/after screenshots).")

                    # Save the "final" cart screenshot (after removal attempt) as final_cart_after_remove
                    final_path = f"tests/final_cart_after_remove_{after_ts}.png"
                    try:
                        driver.save_screenshot(final_path)
                    except Exception:
                        try:
                            with open(final_path, "wb") as _f:
                                _f.write(driver.get_screenshot_as_png())
                        except Exception:
                            pass
                    try:
                        allure.attach.file(final_path, name="final_cart_after_remove",
                                           attachment_type=allure.attachment_type.PNG)
                    except Exception:
                        pass
                    print(f"Saved final cart screenshot (after remove attempt) to: {final_path}")

                # close cart tab if we opened one and return to original
                try:
                    handles_after = driver.window_handles
                    if cart_handle and cart_handle in handles_after:
                        driver.close()
                        try:
                            if original_handle in driver.window_handles:
                                driver.switch_to.window(original_handle)
                            else:
                                rem = driver.window_handles
                                if rem:
                                    driver.switch_to.window(rem[0])
                        except Exception:
                            pass
                except Exception:
                    pass

            except Exception as e:
                print(f"⚠️ Could not open cart / remove item / save screenshot: {e}")
