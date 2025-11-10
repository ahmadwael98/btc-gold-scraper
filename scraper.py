import pandas as pd
from bs4 import BeautifulSoup
import requests
import datetime as dt
import os
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
import gspread
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from urllib.error import HTTPError
from requests.exceptions import ConnectionError
import json
from google.oauth2.service_account import Credentials
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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

def get_gspread_client():
    service_account_info = json.loads(os.environ["GSPREAD_JSON"])
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    return gspread.authorize(creds)




def main():
    print("test first in main")
    driver = get_driver()
    spread_api = get_gspread_client()
    spread_sheet = spread_api.open("BTC and Dollars")
    print("spread done")

    # =========================
    # Dollar Price
    # =========================
    try:
        # --- BS4 first ---
        print("NBE (BS4)")
        nbe_response = requests.get("https://www.nbe.com.eg/NBE/E/#/EN/ExchangeRatesAndCurrencyConverter", timeout=15).content
        nbe_soup = BeautifulSoup(nbe_response, "html.parser")
        table_cells = nbe_soup.find_all("td", {"class": "marker"})
        us = [i.get_text(strip=True) for i in table_cells]

        spliting = us[3].split("\n")
        Dollar_price = (spliting[0].split(" "))[1]
        print("NBE (BS4)")
    except:
        try:
            # --- Selenium fallback ---
            print("NBE (Selenium)")
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
                print("Google")
                driver.get("https://www.google.com")
                search = driver.find_element(By.XPATH, "//input[@class='gLFyf']")
                search.send_keys("dollar to egp")
                search.send_keys(Keys.ENTER)
                Dollar_price = driver.find_element(
                    By.XPATH, "//span[@class='DFlfde SwHCTb']"
                ).text
                print("Google")
            except:
                Dollar_price = "Closed or Unreachable"
                print("Dollar Closed")

    print(Dollar_price)

    # =========================
    # Gold Prices
    # =========================
    try:
        # --- BS4 first ---
        print("Gold (BS4)")
        kerat_21_response = requests.get("https://market.isagha.com/prices", timeout=15).content
        kerat_21_soup = BeautifulSoup(kerat_21_response, "html.parser")
        kerat_21_span = kerat_21_soup.find_all("div", class_="value")

        kerat = [i.text for i in kerat_21_span]

        kerat_24_buy = kerat[0].split()[0]
        kerat_24_sell = kerat[1].split()[0]

        kerat_21_buy = kerat[6].split()[0]
        kerat_21_sell = kerat[7].split()[0]

        kerat_18_buy = kerat[9].split()[0]
        kerat_18_sell = kerat[10].split()[0]
        ounce_dollar = kerat[24].split()[0]

        coin_price = (float(kerat_21_buy) + 54) * 8
        Dollar_to_egp = float(kerat_24_buy) / (float(ounce_dollar) / 31.1)
        Dollar_to_egp = round(Dollar_to_egp, 2)
        coin_price = round(coin_price)
        ounce_dollar = round(float(ounce_dollar))
        print("Gold (BS4)")

    except:
        try:
            # --- Selenium fallback ---
            print("Gold (Selenium)")
            driver.get("https://market.isagha.com/prices")
            search = driver.find_elements(By.XPATH, "//div[@class='value']")
            kerat_price = [i.text for i in search]

            kerat_24_buy = kerat_price[0].split()[0]
            kerat_24_sell = kerat_price[1].split()[0]
            kerat_21_buy = kerat_price[6].split()[0]
            kerat_21_sell = kerat_price[7].split()[0]
            kerat_18_buy = kerat_price[9].split()[0]
            kerat_18_sell = kerat_price[10].split()[0]
            ounce_dollar = kerat_price[24].split()[0]

            coin_price = (float(kerat_21_buy) + 54) * 8
            Dollar_to_egp = float(kerat_24_buy) / (float(ounce_dollar) / 31.1)
            Dollar_to_egp = round(Dollar_to_egp, 2)
            coin_price = round(coin_price)
            ounce_dollar = round(float(ounce_dollar))
            print("Gold (Selenium)")

        except:
            kerat_18_sell = kerat_21_sell = kerat_24_sell = "Closed or Unreachable"
            kerat_18_buy = kerat_21_buy = kerat_24_buy = "Closed or Unreachable"
            coin_price = "Closed or Unreachable"
            Dollar_to_egp = "Closed or Unreachable"
            ounce_dollar = "Closed or Unreachable"
            print("Gold Closed")

    # =========================
    # Black Market
    # =========================
    try:
        # --- BS4 first ---
        print("Black Market (BS4)")
        black_response = requests.get("https://sarf-today.com/currency/us_dollar/market",timeout=15).content
        black_soup = BeautifulSoup(black_response, "html.parser")
        price_block = black_soup.find("div", class_="col-md-8 cur-info-container")
        price_list = price_block.get_text("\n", strip=True)
        blackmarket = price_list.split("\n")
        avgblackmarket = (float(blackmarket[3]) + float(blackmarket[5])) / 2
        print("Black Market (BS4)")
    except:
        try:
            print("Black Market (Selenium)")
            # --- Selenium fallback ---
            driver.get("https://sarf-today.com/currency/us_dollar/market")
            price_list = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@class='col-md-8 cur-info-container']")
                )
            ).text
            blackmarket = price_list.split("\n")
            avgblackmarket = (float(blackmarket[3]) + float(blackmarket[5])) / 2
            print("Black Market (Selenium)")
        except:
            avgblackmarket = "Closed or Unreachable"
            print("Black Market Closed")

    # =========================
    # Save to Sheets
    # =========================
    current_time = dt.datetime.now()
    data = [
        current_time.strftime("%Y-%m-%d"),
        current_time.strftime("%H:%M:%S"),
        str(coin_price) + " EGP",
        Dollar_price,
        kerat_18_buy,
        kerat_21_buy,
        kerat_24_buy,
        kerat_18_sell,
        kerat_21_sell,
        kerat_24_sell,
        ounce_dollar,
        Dollar_to_egp,
        avgblackmarket,
        "GitHub",
    ]

    wks1 = spread_sheet.worksheet("Sheet1")
    wks1.insert_row(values=data, index=2, value_input_option="RAW")

    print(data)
    wks2 = spread_sheet.worksheet("Sheet2")
    wks2.update("A2:N2", [data])

    driver.quit()


if __name__ == "__main__":
    main()
