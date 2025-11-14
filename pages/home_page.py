# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from base.base_driver import BaseDriver
#
# class HomePage(BaseDriver):
#     SEARCH_BOX = (By.ID, "gh-ac")
#
#     def __init__(self, driver):
#         super().__init__(driver)
#
#     def search_item(self, item_name):
#         search_box = self.wait_for_element(self.SEARCH_BOX)
#         search_box.clear()
#         search_box.send_keys(item_name)
#         search_box.send_keys(Keys.RETURN)
import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from base.base_driver import BaseDriver


class HomePage(BaseDriver):
    SEARCH_BOX = (By.ID, "gh-ac")

    def __init__(self, driver):
        super().__init__(driver)

    @allure.step("Searching for item: {item_name}")
    def search_item(self, item_name):
        search_box = self.wait_for_element(self.SEARCH_BOX)
        search_box.clear()
        search_box.send_keys(item_name)
        search_box.send_keys(Keys.RETURN)
        allure.attach(item_name, name="Search Term", attachment_type=allure.attachment_type.TEXT)
