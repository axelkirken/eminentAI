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
    "https://www.google.com/maps/place/Vattenverket+Kottlasj%C3%B6n/@59.3503456,18.1903447,17z/data=!4m8!3m7!1s0x465f82fed5580315:0x9fe04566ea4ebf89!8m2!3d59.3503429!4d18.1929196!9m1!1b1!16s%2Fg%2F11dyzcrbqj?entry=ttu"
)
time.sleep(3)
button_result = driver.find_element(
    by=By.XPATH,
    value='//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/div[1]/form[2]',
)
if button_result:
    print("Found button")
driver.execute_script("arguments[0].click();", button_result)
time.sleep(5)
# Find the total number of reviews
total_number_of_reviews = driver.find_element(
    by=By.XPATH,
    value='//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/div[1]/form[2]/div',
).text.split(" ")[0]
total_number_of_reviews = (
    int(total_number_of_reviews.replace(",", ""))
    if "," in total_number_of_reviews
    else int(total_number_of_reviews)
)
# Find scroll layout
scrollable_div = driver.find_element_by_xpath(
    '//*[@id="pane"]/div/div[1]/div/div/div[2]'
)
# Scroll as many times as necessary to load all reviews
for i in range(0, (round(total_number_of_reviews / 10 - 1))):
    driver.execute_script(
        "arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div
    )
    time.sleep(1)
