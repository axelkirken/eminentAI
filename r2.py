import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


def extract_google_reviews(driver, query):
    driver.get("https://www.google.com/?hl=en")
    driver.find_element_by_name("q").send_keys(query)
    WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.NAME, "btnK"))
    ).click()

    reviews_header = driver.find_element_by_css_selector("div.kp-header")
    reviews_link = reviews_header.find_element_by_partial_link_text("Google reviews")
    number_of_reviews = int(reviews_link.text.split()[0])
    reviews_link.click()

    all_reviews = WebDriverWait(driver, 3).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "div.gws-localreviews__google-review")
        )
    )
    while len(all_reviews) < number_of_reviews:
        driver.execute_script("arguments[0].scrollIntoView(true);", all_reviews[-1])
        WebDriverWait(driver, 5, 0.25).until_not(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div[class$="activityIndicator"]')
            )
        )
        all_reviews = driver.find_elements_by_css_selector(
            "div.gws-localreviews__google-review"
        )

    reviews = []
    for review in all_reviews:
        try:
            full_text_element = review.find_element_by_css_selector(
                "span.review-full-text"
            )
        except NoSuchElementException:
            full_text_element = review.find_element_by_css_selector('span[class^="r-"]')
        reviews.append(full_text_element.get_attribute("textContent"))

    return reviews


if __name__ == "__main__":
    try:
        driver = webdriver.Chrome()
        reviews = extract_google_reviews(
            driver, "STANLEY BRIDGE CYCLES AND SPORTS LIMITED"
        )
    finally:
        driver.quit()

    print(reviews)
