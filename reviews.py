from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import re
import time


def initDriver(timeout=30):
    print("initDriver: Initializing driver")
    driver = getDriver()
    driver.set_page_load_timeout(timeout)
    driver.implicitly_wait(timeout)
    driver.set_script_timeout(timeout)
    return driver


def getDriver():
    options = webdriver.ChromeOptions()
    options.add_argument("--lang=en")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("window-size=1920x1080")
    driver = webdriver.Chrome(
        options=options,
        service=Service(),
    )
    return driver


driver = initDriver()
driver.get(
    "https://www.google.com/search?q=vattenverket+liding%C3%B6&rlz=1C5CHFA_enSE1077SE1077&oq=vattenverket+liding%C3%B6&gs_lcrp=EgZjaHJvbWUyCQgAEEUYORiABDIHCAEQABiABDIHCAIQABiABDIHCAMQABiABDIHCAQQABiABDIHCAUQABiABDIHCAYQABiABDIKCAcQABgPGBYYHjIICAgQABgWGB4yCAgJEAAYFhgeqAIAsAIA&sourceid=chrome&ie=UTF-8#lrd=0x465f82fed5580315:0x9fe04566ea4ebf89,1,,,,"
)
time.sleep(3)
button_result = driver.find_element(
    by=By.XPATH,
    value="//button[@id='L2AGLb']",
)
if button_result:
    print("Found button")
driver.execute_script("arguments[0].click();", button_result)

old = -1
elements = []
while len(elements) != old:
    old = len(elements)
    elements = driver.find_elements(
        by=By.XPATH,
        value="//div[@class='WMbnJf vY6njf gws-localreviews__google-review']",
    )

    print(len(elements))
    scrollable_div = driver.find_element(
        By.XPATH,
        '//*[@id="reviewSort"]/div',
    )
    driver.execute_script(
        "arguments[0].scrollBottom = arguments[0].scrollHeight", scrollable_div
    )
    last_review = driver.find_element(
        By.CSS_SELECTOR, "div.gws-localreviews__google-review:last-of-type"
    )
    last_review.find_element()
    driver.execute_script("arguments[0].scrollIntoView(true);", last_review)

time.sleep(50)
