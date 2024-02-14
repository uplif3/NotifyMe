from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import traceback
import requests
import datetime
import time


chrome_options = Options()
#chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--verbose")
chrome_options.add_argument("--log-path=chrome.log")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
chrome_options.add_argument("--window-size=1920,1080")


chromedriver_path = 'PATH TO THE CHROMEDRIVER'
discord_webhook_url = 'YOUR DISCORD WEBHOOK LINK'

# The ID from the Classes of the Buy Button
id4080 = "326781"
id4060 = "269544"

# Initialisiere den WebDriver
service = Service(chromedriver_path)

# Link to your Nvidia Store Page
url = 'https://store.nvidia.com/de-at/geforce/store/?page=1&limit=9&locale=de-at'


def check_product_availability(element_id):
    print("Start next Check")
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print("Seite geladen:", url)
        print("Suche nach: ", element_id)
        access_denied_header = driver.find_element(By.TAG_NAME, "h1")
        if "Access Denied" in access_denied_header.text:
            print("Zugriff verweigert")
        else:
            wait = WebDriverWait(driver, 20)
            element = wait.until(EC.presence_of_element_located((By.ID, element_id)))
            print("Element:")
            print(element)
            time.sleep(10)
            print("Element Outer HTML:")
            print(element.get_attribute('outerHTML'))

            data = element.get_attribute("innerHTML").strip()
            if data and data != "[]":
                print("Element Inner HTML:")
                print(data)
                try:
                    product_info = json.loads(data)

                    if product_info[0]['isAvailable']:
                        direct_purchase_link = product_info[0]['directPurchaseLink']
                        print("Produkt ist verfügbar - DirectPurchaseLink:", direct_purchase_link)

                        message = {
                            "content": f"Produkt ist verfügbar - DirectPurchaseLink: {direct_purchase_link}"
                        }
                        response = requests.post(discord_webhook_url, json=message)
                        if response.status_code == 204:
                            print("Nachricht wurde an Discord gesendet.")
                        else:
                            print("Fehler beim Senden der Nachricht an Discord.")
                    else:
                        print("Produkt ist nicht verfügbar.")
                except json.JSONDecodeError:
                    print("Fehler beim Parsen von JSON-Daten.")
            else:
                print("Keine Daten gefunden im Element Inner HTML.")
    except NoSuchElementException:
        print("Das gesuchte Element wurde nicht gefunden.")
    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
        traceback.print_exc()
    finally:
        driver.quit()
        pass

def main():
    message_sent_today = False
    try:
        while True:
            now = datetime.datetime.now()
            next_run = now + datetime.timedelta(minutes=15)
            if now.hour == 13 and now.minute < 10 and not message_sent_today:
                message = {
                    "content": f"Still Alive!"
                }
                response = requests.post(discord_webhook_url, json=message)

                message_sent_today = True
            elif now.hour != 13:
                message_sent_today = False

            check_product_availability(id4080) #set the id from the class here
            
            time_to_next_run = (next_run - datetime.datetime.now()).total_seconds()
            time.sleep(max(0, time_to_next_run))
    except KeyboardInterrupt:
        print("Skript wurde manuell beendet.")


main()