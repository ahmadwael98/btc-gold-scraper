import json
from bs4 import BeautifulSoup
import requests
import datetime as dt
import gspread
from selenium import webdriver
from selenium.webdriver.common.by import By
from google.oauth2.service_account import Credentials
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

def wait_for(driver, by, value, timeout=5):  # reduced timeout
    """Wait until element is visible in Selenium."""
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, value))
    )

def get_soup_with_wait(url, selector=None, retries=2, delay=2):  # reduced retries/delay
    """Try fetching page until selector found or max retries reached."""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.content, "html.parser")
            if not selector or soup.select_one(selector):
                return soup
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
        time.sleep(delay)
    raise Exception(f"Failed to load {url} after {retries} retries.")

def main():
    print("Starting scraper")
    driver = get_driver()

    print("Getting Dollar price")
    Dollar_price = getDollar_price(driver)
    print("Dollar price:", Dollar_price)

    print("Getting Gold prices")
    gold_data = getGold_prices(driver)
    print("Gold data:", gold_data)

    print("Getting Black Market")
    avgblackmarket = getBlack_market(driver)
    print("Black Market:", avgblackmarket)

    # Save to Sheets (optional for debugging)
    try:
        print("Saving to Google Sheets")
        current_time = dt.datetime.now()
        data = [
            current_time.strftime("%Y-%m-%d"),
            current_time.strftime("%H:%M:%S"),
            str(gold_data[8]) + " EGP",
            Dollar_price,
            gold_data[0],
            gold_data[1],
            gold_data[2],
            gold_data[3],
            gold_data[4],
            gold_data[5],
            gold_data[6],
            gold_data[7],
            avgblackmarket,
            "GitHub",
        ]
       
    except Exception as e:
        print("Skipping Google Sheets due to error:", e)

    driver.quit()
    print("Scraper finished")

def get_driver():
    chrome_path = os.getenv("CHROME_BIN", "/usr/bin/google-chrome")
    driver_path = os.getenv("CHROMEDRIVER_BIN", None)

    options = Options()
    options.binary_location = chrome_path
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-infobars")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    if driver_path:
        service = Service(driver_path)
        return webdriver.Chrome(service=service, options=options)
    else:
        return webdriver.Chrome(options=options)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def getDollar_price(driver):
    print("getdollar")
    try:
            # --- Selenium fallback ---
            driver.get(
                "https://www.nbe.com.eg/NBE/E/#/EN/ExchangeRatesAndCurrencyConverter"
            )
            search = WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.XPATH, "//td[@class='marker']"))
            )
            us = [i.text for i in search]
            spliting = us[3].split("\n")
            Dollar_price = (spliting[0].split(" "))[1]
            print("NBE (Selenium)")
    except:
        try:
            driver.get("https://www.cibeg.com/en/currency-converter")
            usd_row = wait_for(driver, By.XPATH, "//td[text()='USD']/parent::tr", timeout=5)
            cols = usd_row.find_elements(By.TAG_NAME, "td")
            Dollar_price = cols[1].text
            print(f"Buy: {Dollar_price} CIB Selenium") 
        except:
            Dollar_price = 'Closed or Unreachable'
            print('Dollar Closed')
    return Dollar_price

def getGold_prices(driver):
    try:
        soup = get_soup_with_wait("https://market.isagha.com/prices", "div.value")
        kerat_21_span = soup.find_all("div", class_="value")
        kerat = [i.text for i in kerat_21_span]

        kerat_24_buy = kerat[0].split()[0]
        kerat_24_sell = kerat[1].split()[0]
        kerat_21_buy = kerat[6].split()[0]
        kerat_21_sell = kerat[7].split()[0]
        kerat_18_buy = kerat[9].split()[0]
        kerat_18_sell = kerat[10].split()[0]
        ounce_dollar = kerat[24].split()[0]

        coin_price = (float(kerat_21_buy) + 75) * 8
        Dollar_to_egp = float(kerat_24_buy) / (float(ounce_dollar) / 31.1)
        Dollar_to_egp = round(Dollar_to_egp, 2)
        coin_price = round(coin_price)
        ounce_dollar = round(float(ounce_dollar))
        print("Gold (BS4)")
    except:
        # fallback Selenium methods remain same
        try:
            driver.get("https://market.isagha.com/prices")
            wait_for(driver, By.XPATH, "//div[@class='value']", timeout=5)
            kerat_price = [i.text for i in driver.find_elements(By.XPATH, "//div[@class='value']")]
            kerat_24_buy = kerat_price[0].split()[0]
            kerat_24_sell = kerat_price[1].split()[0]
            kerat_21_buy = kerat_price[6].split()[0]
            kerat_21_sell = kerat_price[7].split()[0]
            kerat_18_buy = kerat_price[9].split()[0]
            kerat_18_sell = kerat_price[10].split()[0]
            ounce_dollar = kerat_price[24].split()[0]

            coin_price = (float(kerat_21_buy) + 75) * 8
            Dollar_to_egp = float(kerat_24_buy) / (float(ounce_dollar) / 31.1)
            Dollar_to_egp = round(Dollar_to_egp, 2)
            coin_price = round(coin_price)
            ounce_dollar = round(float(ounce_dollar))
            print("Gold (Selenium)")
        except:
            kerat_18_sell = kerat_21_sell = kerat_24_sell = "Closed or Unreachable"
            kerat_18_buy = kerat_21_buy = kerat_24_buy = "Closed or Unreachable"
            coin_price = Dollar_to_egp = ounce_dollar = "Closed or Unreachable"
            print("Gold Closed")
    return (
        kerat_18_buy,
        kerat_21_buy,
        kerat_24_buy,
        kerat_18_sell,
        kerat_21_sell,
        kerat_24_sell,
        ounce_dollar,
        Dollar_to_egp,
        coin_price,
    )

def getBlack_market(driver):
    try:
        soup = get_soup_with_wait("https://sarf-today.com/currency/us_dollar/market", "div.col-md-8.cur-info-container")
        price_block = soup.find("div", class_="col-md-8 cur-info-container")
        price_list = price_block.get_text("\n", strip=True)
        blackmarket = price_list.split("\n")
        avgblackmarket = (float(blackmarket[3]) + float(blackmarket[5])) / 2
        print("Black Market (BS4)")
    except:
        try:
            driver.get("https://sarf-today.com/currency/us_dollar/market")
            price_list = wait_for(driver, By.XPATH, "//div[@class='col-md-8 cur-info-container']", timeout=5).text
            blackmarket = price_list.split("\n")
            avgblackmarket = (float(blackmarket[3]) + float(blackmarket[5])) / 2
            print("Black Market (Selenium)")
        except:
            avgblackmarket = "Closed or Unreachable"
            print("Black Market Closed")
    return avgblackmarket

if __name__ == "__main__":
    main()
