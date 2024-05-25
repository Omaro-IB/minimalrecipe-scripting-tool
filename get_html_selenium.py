from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
import requests
from selenium.common.exceptions import WebDriverException


def get_html_selenium(url):
    print("Issue with website response, trying again with FireFox driver (should take ~30-60 seconds)...")

    options = Options()
    options.add_argument("--headless")

    driver = webdriver.Firefox(options=options)
    driver.get(url)
    html = driver.page_source

    if "yummly" in url:  # yummly has a "continue to directions" button that must be clicked
        try:
            try:
                button = WebDriverWait(driver, 30).until(
                    ec.presence_of_element_located((
                        By.XPATH, "/html/body/div[1]/div[1]/div[4]/div/div[6]/div[2]/div[3]/div[2]/div[3]/a"))
                )
                new_url = button.get_attribute("href")
            finally:
                driver.quit()

            new_url = new_url[:new_url.find("?")]  # remove any ?options
            print(f"Yummly URL detected, found new URL {new_url}")
            r = requests.get(new_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0'})
            return r.text
        except WebDriverException:  # most likely no button present - recipe on page
            return html

    return html

