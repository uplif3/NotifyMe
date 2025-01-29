import argparse
import time
import json
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def parse_args():
    parser = argparse.ArgumentParser(description="Check product availability in intervals.")
    parser.add_argument(
        "--interval",
        type=int,
        default=15,
        help="Abstand in Minuten zwischen den Checks (Standard: 15)"
    )
    return parser.parse_args()

chrome_options = Options()
#chrome_options.add_argument("--headless")  # optionaler Headless-Modus
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 \
    (KHTML, like Gecko) Chrome/109.0.5414.74 Safari/537.36"
)
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

url = "https://marketplace.nvidia.com/de-at/consumer/graphics-cards/"
discord_webhook_url = "<DISCORD-HOOK>"

def send_discord_notification(message: str):
    """Kleiner Helper, um eine Nachricht an Discord zu senden."""
    if not discord_webhook_url:
        print("Kein Discord-Webhook konfiguriert.")
        return
    payload = {"content": message}
    try:
        response = requests.post(discord_webhook_url, json=payload)
        if response.status_code == 204:
            print("Nachricht an Discord gesendet:", message)
        else:
            print(f"Fehler beim Senden an Discord: {response.text}")
    except Exception as e:
        print(f"Exception beim Senden an Discord: {e}")


def check_all_products():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    try:
        driver.get(url)

        # Warte, bis Elemente gerendert sind (z.B. Warte auf #resultsDiv)
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.ID, "resultsDiv")))

        # Finde alle <div> mit style="display: none; visibility: hidden;" und ID
        hidden_divs = driver.find_elements(
            By.CSS_SELECTOR,
            "div[style*='display: none'][style*='visibility: hidden'][id]"
        )

        print(f"Gefundene versteckte DIVs: {len(hidden_divs)}")

        for div in hidden_divs:
            product_id = div.get_attribute("id")  # z.B. "270775"
            inner_html = div.get_attribute("innerHTML").strip()

            # Falls das DIV leer ist, überspringen
            if not inner_html:
                continue

            # Debug: Direkt den JSON-String ausgeben
            print(f"\n==> Produkt-ID: {product_id} | RAW JSON:\n{inner_html}\n")

            try:
                product_info_list = json.loads(inner_html)
                if not product_info_list:
                    continue

                # Debug: Parsed JSON anzeigen
                print(f"Parsed JSON (als Python-Liste): {product_info_list}")

                # In der Regel nur 1 Objekt in der Liste
                product_info = product_info_list[0]
                title = product_info.get("productTitle", "")
                price = product_info.get("salePrice", "")
                is_available = product_info.get("isAvailable", False)
                purchase_link = product_info.get("directPurchaseLink", "")

                print(f"Produkt-ID: {product_id} | Titel: {title} | Verfügbar: {is_available} | Preis: {price}")

                # Beispiel-Logik: Wenn verfügbar und nicht "RTX 40" im Titel
                if is_available:
                    if "RTX 40" in title.upper():
                        print(f"SKIP: {title} ist verfügbar, aber wird nicht gemeldet (Ausschluss).")
                        continue

                    message = f"**{title}** ist JETZT verfügbar für {price}!\nLink: {purchase_link}"
                    send_discord_notification(message)

            except json.JSONDecodeError:
                print(f"Konnte JSON für Produkt-ID {product_id} nicht parsen.")

            # kleiner Sleep zwischen den Iterationen
            time.sleep(1)

    finally:
        driver.quit()


def main():
    args = parse_args()
    interval_minutes = args.interval

    print(f"Starte Checks alle {interval_minutes} Minuten.")
    try:
        while True:
            check_all_products()
            print(f"Nächster Check in {interval_minutes} Minuten.")
            time.sleep(interval_minutes * 60)
    except KeyboardInterrupt:
        print("Skript wurde manuell beendet.")


if __name__ == "__main__":
    main()
