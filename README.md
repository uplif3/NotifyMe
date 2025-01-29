# NotifyMe – NVIDIA GPU Restock Notifier

Dieses Skript prüft in regelmäßigen Abständen den Bestand an Founders-Edition-Grafikkarten auf der **NVIDIA Marketplace**-Seite. Sobald eine Karte als verfügbar gemeldet wird, sendet das Skript eine Nachricht mit einem Direktlink per Discord-Webhook.

## Features

- **Automatisierter Browser** über [Selenium](https://www.selenium.dev/).  
- **Benachrichtigung** via [Discord Webhook](https://support.discord.com/hc/de/articles/228383668-Intro-to-Webhooks).  
- **Individuelles Intervall** per Kommandozeilen-Parameter (`--interval` in Minuten).  
- **Flexibel anpassbar** für andere NVIDIA-Store-Regionen (z. B. `de-at`, `de-de`, `en-us` etc.).  

---

## Voraussetzungen

1. **Python 3** (empfohlen ab Version 3.8 oder höher).
2. **Google Chrome** (installiert auf deinem System).
3. **Passender ChromeDriver**:
   - Entweder manuell herunterladen (siehe [ChromeDriver Downloads](https://chromedriver.chromium.org/downloads)) und den Pfad hinterlegen.
   - Oder das Python-Paket [webdriver_manager](https://pypi.org/project/webdriver-manager/) nutzen, das den Download automatisch verwaltet.
4. **Discord Webhook URL**  
   - Erstelle einen Webhook in deinem Discord-Server und kopiere die URL.

---

## Installation

1. **Python-Abhängigkeiten installieren**:
   ```bash
   pip install --upgrade selenium webdriver_manager requests
   ```
2. (Optional) Falls du den ChromeDriver manuell laden willst, setze den Pfad im Skript oder in der Umgebungsvariable:
   ```python
   service = Service("/pfad/zu/chromedriver")
   driver = webdriver.Chrome(service=service, options=chrome_options)
   ```
   Standardmäßig nutzt das Skript `webdriver_manager`.

3. **Discord Webhook** in der Variable `discord_webhook_url` im Skript eintragen.

---

## Konfiguration

- **URL** anpassen:  
  Standardmäßig ist `https://marketplace.nvidia.com/de-at/consumer/graphics-cards/` hinterlegt.  
  Möchtest du eine andere Region, passe die Variable `url` im Skript an, z. B.:
  ```python
  url = "https://marketplace.nvidia.com/de-de/consumer/graphics-cards/"
  ```
- **Filtern von Produkten**:  
  Im Skript wird jedes Produkt geparst, das in den JSON-Daten auftaucht. Du kannst im Code Logik anpassen (z. B. bestimmte RTX-Modelle ausschließen).
- **Prüfintervall**:  
  Per `--interval` (in Minuten) festlegen. Standard sind 15 Minuten.  

---

## Nutzung

1. **Skript ausführen** (Standardintervall: 15 Minuten):
   ```bash
   python main.py
   ```
2. **Skript mit benutzerdefiniertem Intervall**:
   ```bash
   python main.py --interval 5
   ```
   (Wiederholt den Check alle 5 Minuten.)

Während der Ausführung:

- Öffnet sich ein Chrome-Browser (sofern du **nicht** den Headless-Modus aktivierst).
- Das Skript lädt die Seite, findet alle JSON-Blöcke, in denen Informationen über die GPUs stehen, und wertet das `isAvailable`-Feld aus.  
- Wenn eine Karte verfügbar ist, wird automatisch eine Nachricht an deinen konfigurierten Discord-Webhook geschickt.

---

## Tipps & Hinweise

1. **Shadowban-Risiko**  
   Wenn du das Intervall zu kurz einstellst (z. B. unter 1 Minute), kann die Webseite dich blockieren oder „Access Denied“ senden. 15 Minuten sind erfahrungsgemäß sicherer.  
2. **User-Agent & Anti-Bot**  
   Sollte die Seite abweichende Daten liefern, kannst du mit dem User-Agent in `chrome_options.add_argument(...)` experimentieren, um wie ein normaler Browser aufzutreten.  
3. **Session/Cookies**  
   Manchmal erhält man erst bei Login oder bestimmten Cookies die korrekten Daten. Bei Bedarf kannst du Cookies importieren (z. B. `driver.add_cookie`).  
4. **Discord-Webhook-Sicherheit**  
   Teile die Webhook-URL nicht öffentlich. Sonst könnten Fremde Nachrichten in deinen Channel senden.

---

## Wie funktioniert’s?

1. **Aufruf**: Das Skript startet einen automatisierten Chrome-Browser via Selenium.  
2. **Seite laden**: Es ruft die URL des NVIDIA Marketplace auf, wartet bis `#resultsDiv` sichtbar ist.  
3. **JSON auslesen**: Alle `<div>`-Container mit Produktdaten werden im Hintergrund (CSS `display: none` + `visibility: hidden`) gefunden und der darin enthaltene JSON-Text wird geparst.  
4. **Prüfung**:  
   - Für jedes Produkt wird `isAvailable` sowie `directPurchaseLink` geprüft.  
   - Wenn verfügbar, wird sofort eine Discord-Nachricht geschickt – inklusive Kauf-Link.  
5. **Pause & Wiederholung**: Das Skript schläft für das angegebene Intervall (`--interval`) und wiederholt dann den Vorgang.

---

## Beispiel für eine erfolgreiche Benachrichtigung

Du erhältst auf Discord z. B.:

```
**NVIDIA GeForce RTX 4080 SUPER** ist JETZT verfügbar für 1129.0!
Link: https://marketplace.nvidia.com/de-at/consumer/graphics-cards/nvidia-geforce-rtx-4080-super/
```

Danach kannst du direkt auf den Link klicken und die Karte kaufen.

---

## Bekannte Probleme

- **„Access Denied“ oder leere Ergebnisse**:  
  Meistens zu hohes Abfrageintervall. Ggf. Intervall verlängern oder Proxy wechseln.  
- **Unterschiedliche Daten in Browser vs. Bot**:  
  Oft haben Shops A/B-Tests, Regionseinstellungen oder setzen Cookies, die du im Bot nicht hast. Ggf. den User-Agent anpassen oder Cookies übertragen.
- **Fehler beim JSON-Parsing**:  
  Wenn NVIDIA das Layout ändert, muss ggf. der Selektor im Code aktualisiert werden.
- **Headless**:
  Der Headless Modus funktioniert nicht, verwende diesen nicht!

---

## Autor & Lizenz

- Das Skript wurde ursprünglich von [@uplif3](https://github.com/uplif3) erstellt und angepasst für die neue NVIDIA Marketplace-Struktur.  
- Du kannst es nach Belieben verändern und teilen. Bitte teile Verbesserungen gerne zurück!  

---

### Viel Erfolg und Spaß beim automatisierten GPU-Shopping!  

Falls du Fragen hast oder Hilfe beim Anpassen benötigst, erstelle ein Issue oder melde dich bei [@uplif3](https://github.com/uplif3). 
