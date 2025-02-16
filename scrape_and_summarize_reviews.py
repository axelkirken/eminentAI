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
import random
from transformers import pipeline
import json
from openai import OpenAI
import os
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

client = OpenAI(api_key=os.getenv("EMINENT_API_KEY"))


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


def randomSleep(baseline=0, variable=500):
    variable = random.random() * variable
    time.sleep((baseline + variable) / 1000)


def getReviews(driver):
    driver.get(
        "https://www.google.com/maps/place/Vattenverket+Kottlasj%C3%B6n/@59.3503429,18.1903447,17z/data=!4m8!3m7!1s0x465f82fed5580315:0x9fe04566ea4ebf89!8m2!3d59.3503429!4d18.1929196!9m1!1b1!16s%2Fg%2F11dyzcrbqj?entry=ttu"
    )
    time.sleep(2)
    # Cookies
    button_result = driver.find_element(
        by=By.XPATH,
        value='//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/div[1]/form[2]/div/div/button/div[3]',
    )
    driver.execute_script("arguments[0].click();", button_result)
    time.sleep(2)

    for i in range(10):
        elements = driver.find_elements(
            by=By.XPATH, value='//*[@class="jftiEf fontBodyMedium "]'
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", elements[-1])
        randomSleep(500)
    print(len(elements))

    showMoreButtons = driver.find_elements(
        by=By.XPATH, value='//*[@class="w8nwRe kyuRq"]'
    )
    for button in showMoreButtons:
        driver.execute_script("arguments[0].click();", button)
        randomSleep(100)

    reviews = driver.find_elements(by=By.XPATH, value='//*[@class="wiI7pd"]')
    review_list = []
    for review in reviews:
        review_list.append(review.text)
    # with open("reviews.json", "w") as outfile:
    #     json.dump(review_list, outfile)
    return review_list


def getSentiment(reviews):
    reviews = [review[:1000] for review in reviews]
    classifier = pipeline(
        task="text-classification", model="SamLowe/roberta-base-go_emotions", top_k=None
    )

    model_outputs = classifier(reviews)
    with open("sentiment.json", "w") as outfile:
        json.dump(model_outputs, outfile)

    reactions = {}
    for output in model_outputs:
        for element in output:
            label = element["label"]
            score = element["score"]
            reactions[label] = reactions.get(label, 0) + score

    print(reactions)
    labels = list(reactions.keys())
    scores = list(reactions.values())

    return labels, scores


def getSummary(reviews):
    all_reviews = "\n".join(reviews)
    messages = [
        {
            "role": "system",
            "content": """You are a helpful assistant to summarize reviews written about a company""",
        },
        {
            "role": "user",
            "content": f"""
            Summarize the following reviews into about 10 bullet points that can be useful for the company to improve it's business. Include at least 3 improvement areas.  The reviews: 
            {all_reviews}
            """,
        },
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo", temperature=0, messages=messages, timeout=40
    )
    print("\n", response.usage)
    summary = response.choices[0].message.content.strip()
    print(summary)
    return summary


def getThemes(reviews):
    classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
    candidate_labels = [
        "food",
        "service",
        "location",
        "lunch",
        "dinner",
        "expensive",
        "cheap",
        "atmosphere",
        "ambience",
        "staff",
        "wait",
        "time",
        "menu",
        "dish",
        "drink",
        "dessert",
        "price",
    ]
    results = {}
    for review in reviews[:10]:
        sequence_to_classify = review[:1000]
        output = classifier(sequence_to_classify, candidate_labels, multi_label=True)
        for label, score in zip(output["labels"], output["scores"]):
            results[label] = results.get(label, 0) + score
    labels = list(results.keys())
    scores = list(results.values())
    return labels, scores


static = True
if static:
    driver = initDriver()
    driver.maximize_window()
    getReviews(driver)
    with open("reviews.json", "r") as f:
        reviews = json.load(f)
else:
    driver = initDriver()
    driver.maximize_window()
    reviews = getReviews(driver)

labels, scores = getSentiment(reviews)
labels2, scores2 = getThemes(reviews)

if static:
    with open("summary.txt", "r") as f:
        summary = f.read()
else:
    summary = getSummary(reviews[:10])

plt.figure(figsize=(20, 10))
gs = gridspec.GridSpec(2, 2, width_ratios=[1, 1])

# Plotting area
ax1 = plt.subplot(gs[:, 0])
ax1.barh(labels, scores, color="skyblue")
ax1.set_xlabel("Scores")
ax1.set_ylabel("Emotions")
ax1.set_title("Emotion Scores")
ax1.invert_yaxis()

# Text area
ax2 = plt.subplot(gs[0, 1])
paragraph = f"""
Summary

{summary}"""
ax2.text(0.0, 1.05, paragraph, fontsize=12, va="top", ha="left", wrap=True)

ax2.set_xticks([])
ax2.set_yticks([])
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)
ax2.spines["bottom"].set_visible(False)
ax2.spines["left"].set_visible(False)


ax3 = plt.subplot(gs[1, 1])
ax3.barh(labels2, scores2, color="skyblue")
ax3.set_xlabel("Scores")
ax3.set_ylabel("Themes")
ax3.invert_yaxis()
ax3.set_title("Themes")

plt.get_current_fig_manager().full_screen_toggle()
plt.tight_layout()
plt.show()
