# pages/search_results_page.py
import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


class SearchResultsPage:
    def __init__(self, driver):
        self.driver = driver

    def _dismiss_common_overlays(self):
        """
        Try to close common overlays like cookie banners or modals that block clicks.
        It's safe to call this; if nothing is present it just continues.
        """
        try:
            # common accept/close buttons — we try a few selectors
            candidates = [
                "button[aria-label='Close']",
                "button[aria-label='Accept']",
                "button[aria-label='I accept']",
                "button#gdpr-banner-accept",
                "button.privacy-accept",     # generic
                "button.btn--primary",       # generic
            ]
            for sel in candidates:
                try:
                    el = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if el and el.is_displayed():
                        el.click()
                        time.sleep(0.5)
                        return
                except Exception:
                    continue
        except Exception:
            pass

    @allure.step("Clicking item containing keyword: {keyword}")
    def click_item_with_keyword(self, keyword):
        """
        Robust eBay search result clicker.
        Handles:
         - card layout (img.s-card__image inside anchor)
         - classic list layout (a.s-item__link or li.s-item)
         - fallback anchors that contain '/itm/' in href
        Returns True if clicked something, False otherwise.
        """
        try:
            self._dismiss_common_overlays()

            wait = WebDriverWait(self.driver, 30)

            # Wait for any of the likely patterns to appear on the page
            wait.until(EC.presence_of_all_elements_located((
                By.CSS_SELECTOR,
                "a.s-item__link, li.s-item, .srp-results a, img.s-card__image, .s-item__wrapper"
            )))

            keyword_lower = keyword.lower() if isinstance(keyword, str) else str(keyword).lower()
            candidates = []

            # 1) Preferred: anchors with class s-item__link
            try:
                anchors = self.driver.find_elements(By.CSS_SELECTOR, "a.s-item__link")
                for a in anchors:
                    candidates.append(a)
            except Exception:
                pass

            # 2) Anchors under li.s-item
            try:
                anchors2 = self.driver.find_elements(By.CSS_SELECTOR, "li.s-item a")
                for a in anchors2:
                    if a not in candidates:
                        candidates.append(a)
            except Exception:
                pass

            # 3) Anchors in srp-results or s-item__wrapper
            try:
                anchors3 = self.driver.find_elements(By.CSS_SELECTOR, ".srp-results a, .s-item__wrapper a, .s-list .s-item a")
                for a in anchors3:
                    if a not in candidates:
                        candidates.append(a)
            except Exception:
                pass

            # 4) Cards: find images and resolve to ancestor anchor (newer layout)
            try:
                imgs = self.driver.find_elements(By.CSS_SELECTOR, "img.s-card__image")
                for img in imgs:
                    try:
                        a = img.find_element(By.XPATH, "./ancestor::a[1]")
                        if a and a not in candidates:
                            candidates.append(a)
                    except Exception:
                        continue
            except Exception:
                pass

            # 5) Fallback: any anchors that look like product links (/itm/)
            try:
                all_anchors = self.driver.find_elements(By.XPATH, "//a[contains(@href,'/itm/')]")
                for a in all_anchors:
                    if a not in candidates:
                        candidates.append(a)
            except Exception:
                pass

            # Try each candidate: check its visible text, child image alt, or href
            for idx, a in enumerate(candidates):
                try:
                    href = a.get_attribute("href") or ""
                    text = (a.text or "").strip()
                    alt_text = ""
                    try:
                        img = a.find_element(By.TAG_NAME, "img")
                        alt_text = (img.get_attribute("alt") or "").strip()
                    except Exception:
                        alt_text = ""

                    combined = " ".join([text, alt_text, href]).lower()

                    # match keyword or prefer explicit product links
                    if keyword_lower in combined or "/itm/" in href:
                        print(f"Clicking candidate #{idx+1}: text='{text[:60]}', alt='{alt_text[:60]}', href='{href[:80]}'")
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", a)
                        except Exception:
                            pass
                        time.sleep(0.4)
                        try:
                            a.click()
                        except Exception:
                            # try javascript click as fallback
                            try:
                                self.driver.execute_script("arguments[0].click();", a)
                            except Exception:
                                pass
                        time.sleep(2)
                        return True
                except Exception:
                    # if a candidate fails (stale element, click intercepted), continue to next
                    continue

            # Nothing matched
            print(f"No item link with '{keyword}' found in this search.")
            return False

        except Exception as e:
            # attach screenshot and source for debugging
            try:
                allure.attach(self.driver.get_screenshot_as_png(), name="search_results_screenshot", attachment_type=allure.attachment_type.PNG)
                allure.attach(self.driver.page_source, name="search_results_page_source", attachment_type=allure.attachment_type.HTML)
            except Exception:
                pass
            # re-raise so pytest shows the error trace
            raise
