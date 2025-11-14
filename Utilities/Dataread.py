import allure
import time
from openpyxl import load_workbook
import os

class Dataread:
    @allure.step("Load data from Excel file: {file_path}")
    def dataread(self, file_path="Testdata1.xlsx"):
        """
        Read the search keyword from the given Excel file located in the Utilities folder.
        - file_path: name of the file relative to the Utilities directory (default: Testdata1.xlsx)
        Returns the keyword string (e.g., "outdoor toys")
        """
        # build full path to the Excel file inside the Utilities folder
        full_path = os.path.join(os.path.dirname(__file__), file_path)

        # Open the workbook and read A1
        wb = load_workbook(filename=full_path)
        sheet = wb.active

        # small pause (could be removed later)
        time.sleep(1)

        search_keyword = sheet["A1"].value
        return search_keyword
