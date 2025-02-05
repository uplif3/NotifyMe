import argparse
import time
import json
import requests
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

def parse_args():
    """
    Lies die Interval-Minuten aus CLI-Argumenten,
    fallback auf die Environment Variable INTERVAL oder 15.
    """
    parser = argparse.ArgumentParser(description="Check product availability in intervals.")
    parser.add_argument(
        "--interval",
        type=int,
        default=int(os.getenv("INTERVAL", "15")),
        help="Abstand in Minuten zwischen den Checks (Standard: 15)"
    )
    args = parser.parse_args()
    print(f"[DEBUG] parse_args() -> interval = {args.interval}")
    return args

# Environment-Variablen lesen
discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")
selenium_url = os.getenv("SELENIUM_URL", "http://localhost:4444/wd/hub")

# Chrome-Options vorbereiten
chrome_options = Options()
# chrome_options.add_argument("--headless")  # Falls ohne sichtbares Browserfenster erwünscht
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument(
    "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/109.0.5414.74 Safari/537.36"
)

chrome_options.set_capability("browserName", "chrome")
chrome_options.set_capability("platformName", "ANY")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option("useAutomationExtension", False)

# URL, die geprüft wird
url = "https://marketplace.nvidia.com/de-at/consumer/graphics-cards/"

def send_discord_notification(message: str):
    """Kleiner Helper, um eine Nachricht an Discord zu senden."""
    print(f"[DEBUG] send_discord_notification() -> Nachricht: {message}")
    if not discord_webhook_url:
        print("[DEBUG] Kein Discord-Webhook konfiguriert, breche ab.")
        return
    payload = {"content": message}
    try:
        response = requests.post(discord_webhook_url, json=payload)
        if response.status_code == 204:
            print("[DEBUG] Nachricht erfolgreich an Discord gesendet.")
        else:
            print(f"[DEBUG] Fehler beim Senden an Discord: {response.text}")
    except Exception as e:
        print(f"[DEBUG] Exception beim Senden an Discord: {e}")

def get_remote_driver(chrome_opts, selenium_url, max_retries=5, delay=5):
    """
    Mehrfach versuchen, eine Verbindung zum Remote-WebDriver herzustellen.
    """
    print("[DEBUG] get_remote_driver() aufgerufen.")
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[DEBUG] Versuche Verbindung zu Selenium (Attempt {attempt}/{max_retries})")
            driver = webdriver.Remote(
                command_executor=selenium_url,
                options=chrome_opts
            )
            print("[DEBUG] get_remote_driver() -> Verbindung zu Selenium hergestellt!")
            return driver
        except WebDriverException as e:
            print(f"[DEBUG] Verbindung fehlgeschlagen: {e}")
            if attempt < max_retries:
                print(f"[DEBUG] Warte {delay} Sekunden und versuche es erneut...")
                time.sleep(delay)
            else:
                print("[DEBUG] Alle Versuche gescheitert, werfe Exception weiter.")
                raise

def check_all_products():
    """
    Verbindet sich via Remote WebDriver mit dem Selenium-Container
    und durchsucht die Seite nach den versteckten JSON-Blobs.
    """
    print("[DEBUG] check_all_products() aufgerufen.")
    print(f"[DEBUG] Verwende Selenium-URL: {selenium_url}")

    driver = get_remote_driver(chrome_options, selenium_url)

    try:
        print(f"[DEBUG] Rufe URL auf: {url}")
        driver.get(url)
        print("[DEBUG] Seite geladen. Warte auf #resultsDiv...")

        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.ID, "resultsDiv")))
        print("[DEBUG] #resultsDiv gefunden.")

        # Finde alle <div> mit style="display: none; visibility: hidden;" und ID
        hidden_divs = driver.find_elements(
            By.CSS_SELECTOR,
            "div[style*='display: none'][style*='visibility: hidden'][id]"
        )

        print(f"[DEBUG] Anzahl gefundener versteckter DIVs: {len(hidden_divs)}")

        for div in hidden_divs:
            product_id = div.get_attribute("id")
            inner_html = div.get_attribute("innerHTML").strip()

            if not inner_html:
                print(f"[DEBUG] DIV mit ID {product_id} ist leer, überspringe.")
                continue

            print(f"[DEBUG] Produkt-ID: {product_id} | RAW JSON: {inner_html[:200]}...")

            try:
                product_info_list = json.loads(inner_html)
                if not product_info_list:
                    print("[DEBUG] Produkt-Info-Liste leer, überspringe.")
                    continue

                print(f"[DEBUG] Parsed JSON (als Python-Liste): {product_info_list}")

                # Normalerweise nur 1 Objekt in der Liste
                product_info = product_info_list[0]
                title = product_info.get("productTitle", "")
                price = product_info.get("salePrice", "")
                is_available = product_info.get("isAvailable", False)
                direct_purchase_link = product_info.get("directPurchaseLink", "")
                purchase_link = product_info.get("purchaseLink", "")

                print(f"[DEBUG] Produkt-ID: {product_id} | Titel: {title} | Verfügbar: {is_available} | Preis: {price}")

                # Produkte ignorieren, wenn `directPurchaseLink` und `purchaseLink` gleich sind
                if is_available and direct_purchase_link == purchase_link:
                    print(f"[DEBUG] SKIP: {title} hat identische Links für Kauf → Keine Meldung an Discord.")
                    continue

                # Beispiel: Nur melden, wenn verfügbar und NICHT "RTX 40" im Titel
                if is_available:
                    if "RTX 40" in title.upper():
                        print(f"[DEBUG] SKIP: {title} ({product_id}) ist verfügbar, aber wird nicht gemeldet (Ausschluss).")
                        continue

                    message = (
                        f"**{title}** ist JETZT verfügbar für {price}!\nLink: {direct_purchase_link}"
                    )
                    send_discord_notification(message)

            except json.JSONDecodeError:
                print(f"[DEBUG] Konnte JSON für Produkt-ID {product_id} nicht parsen.")

            # Kleiner Sleep zwischen den Iterationen
            time.sleep(1)

    finally:
        print("[DEBUG] Fahre Driver herunter...")
        driver.quit()

def main():
    print("[DEBUG] main() gestartet.")
    args = parse_args()
    interval_minutes = args.interval
    print(f"[DEBUG] Intervall-Minuten (aus Args): {interval_minutes}")

    # Einmalige Discord-Nachricht zum Start
    send_discord_notification(
        f"Container gestartet! Interval = {interval_minutes} Min, "
        f"SELENIUM_URL = {selenium_url}"
    )

    print(f"Starte Checks alle {interval_minutes} Minuten.")
    try:
        while True:
            print("[DEBUG] Rufe check_all_products() auf...")
            check_all_products()
            print(f"Nächster Check in {interval_minutes} Minuten.")
            print("[DEBUG] Warte jetzt in der Hauptschleife...")
            time.sleep(interval_minutes * 60)
    except KeyboardInterrupt:
        print("Skript wurde manuell beendet.")
        print("[DEBUG] KeyboardInterrupt gefangen, beende das Skript.")

if __name__ == "__main__":
    main()
