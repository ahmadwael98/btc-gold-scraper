
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



def wait_for(driver, by, value, timeout=10):
    """Wait until element is visible in Selenium."""
    return WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, value))
    )

def get_soup_with_wait(url, selector=None, retries=3, delay=3):
    """Try fetching page until selector found or max retries reached."""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            if not selector or soup.select_one(selector):
                return soup
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
        time.sleep(delay)
    raise Exception(f"Failed to load {url} after {retries} retries.")


def main():
    driver = get_driver()

    # =========================
    # Dollar Price
    # =========================
    Dollar_price = getDollar_price(driver)

    # =========================
    # Gold Prices
    # =========================
    (
        kerat_18_buy,
        kerat_21_buy,
        kerat_24_buy,
        kerat_18_sell,
        kerat_21_sell,
        kerat_24_sell,
        ounce_dollar,
        Dollar_to_egp,
        coin_price,
    ) = getGold_prices(driver)

    # =========================
    # Black Market
    # =========================
    avgblackmarket = getBlack_market(driver)

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

    get_gspread(data)
    print(data)
    driver.quit()


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


def get_gspread(data):

    service_account_info = json.loads(os.environ["GSPREAD_JSON"])
    creds = Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
    spread_api = gspread.authorize(creds)
    spread_sheet = spread_api.open("BTC and Dollars")
    wks1 = spread_sheet.worksheet("Sheet1")
    wks1.insert_row(values=data, index=2, value_input_option="RAW")
    print(data)
    wks2 = spread_sheet.worksheet("Sheet2")
    wks2.update("A2:N2", [data])


def getDollar_price(driver):
    try:
        driver.get('https://www.nbe.com.eg/NBE/E/#/EN/ExchangeRatesAndCurrencyConverter')
        wait_for(driver, By.XPATH, "//td[@class='marker']")
        us = [i.text for i in driver.find_elements(By.XPATH, "//td[@class='marker']")]
        spliting = us[3].split('\n')
        Dollar_price = (spliting[0].split(' '))[1]
        print("NBE Selenium")
        return Dollar_price        

    except:
        try:
            driver.get("https://www.cibeg.com/en/currency-converter")
            usd_row = wait_for(driver, By.XPATH, "//td[text()='USD']/parent::tr")
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
        try:
            driver.get("https://market.isagha.com/prices")
            wait_for(driver, By.XPATH, "//div[@class='value']")
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
            try:
                driver.get("https://goldbullioneg.com/%d8%a3%d8%b3%d8%b9%d8%a7%d8%b1-%d8%a7%d9%84%d8%b0%d9%87%d8%a8/")
                wait_for(driver, By.CSS_SELECTOR, "tbody tr")
                rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")

                for row in rows[1:]:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 3:
                        name = cells[0].text.strip()
                        buy = cells[1].get_attribute("data-val")
                        sell = cells[2].get_attribute("data-val")
                        print(f"{name}: Buy={buy}, Sell={sell}")
                        if rows.index(row) == 1:
                            kerat_24_buy = buy
                            kerat_24_sell = sell
                        if rows.index(row) == 3:
                            kerat_21_buy = buy
                            kerat_21_sell = sell
                        if rows.index(row) == 4:
                            kerat_18_buy = buy
                            kerat_18_sell = sell
                        if rows.index(row) == 7:
                            ounce_dollar = buy
                coin_price = (float(kerat_21_buy) + 75) * 8
                Dollar_to_egp = float(kerat_24_buy) / (float(ounce_dollar) / 31.1)
                Dollar_to_egp = round(Dollar_to_egp, 2)
                coin_price = round(coin_price)
                ounce_dollar = round(float(ounce_dollar))
                print("Gold (goldbullioneg Selenium)")
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
            price_list = wait_for(driver, By.XPATH, "//div[@class='col-md-8 cur-info-container']").text
            blackmarket = price_list.split("\n")
            avgblackmarket = (float(blackmarket[3]) + float(blackmarket[5])) / 2
            print("Black Market (Selenium)")
        except:
            try:
                driver.get('https://egcurrency.com/en/currency/usd-to-egp/blackmarket')
                big_price = wait_for(driver, By.CSS_SELECTOR, "b.d-block.text-danger").text.strip()
                sell_price = wait_for(driver, By.XPATH, "//p[contains(., 'Sell Price')]/b").text.strip()
                buy = float(big_price)
                sell = float(sell_price)
                avg = round((buy + sell) / 2, 2)
                print(f"Buy: {buy} | Sell: {sell} | Average: {avg}")
                print("Black Market (egcurrency Selenium)")
                avgblackmarket = avg
            except:
                avgblackmarket = "Closed or Unreachable"
                print("Black Market Closed")
    return avgblackmarket


if __name__ == "__main__":
    main()
