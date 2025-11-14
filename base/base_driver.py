# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
#
# class BaseDriver:
#     def __init__(self, driver):
#         self.driver = driver
#
#     def wait_for_element(self, locator, timeout=30):
#         return WebDriverWait(self.driver, timeout).until(
#             EC.presence_of_element_located(locator)
#         )
#
#     def wait_for_elements(self, locator, timeout=30):
#         return WebDriverWait(self.driver, timeout).until(
#             EC.presence_of_all_elements_located(locator)
#         )

import allure
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BaseDriver:
    def __init__(self, driver):
        self.driver = driver

    @allure.step("Waiting for element: {locator}")
    def wait_for_element(self, locator, timeout=30):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )

    @allure.step("Waiting for elements: {locator}")
    def wait_for_elements(self, locator, timeout=30):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_all_elements_located(locator)
        )
