# NotifyMe – NVIDIA GPU Restock Notifier

Dieses Skript prüft in regelmäßigen Abständen den Bestand an Founders-Edition-Grafikkarten auf der **NVIDIA Marketplace**-Seite. Sobald eine Karte als verfügbar gemeldet wird, sendet das Skript eine Nachricht mit einem Direktlink per Discord-Webhook.

---

## Features

- **Automatisierter Browser** über [Selenium](https://www.selenium.dev/) in einem **externen Docker-Container** (z. B. `selenium/standalone-chrome`).  
- **Benachrichtigung** via [Discord Webhook](https://support.discord.com/hc/de/articles/228383668-Intro-to-Webhooks).  
- **Individuelles Intervall** per Kommandozeilen-Parameter (`--interval` in Minuten) oder Umgebungsvariable `INTERVAL`.  
- **Anpassbare Region** (z. B. `de-at`, `de-de`, `en-us`, etc.).

---

## Voraussetzungen

1. **Docker** installiert.  
2. **Docker-Image mit Selenium** (z. B. `selenium/standalone-chrome` oder ein Selenium Grid):  
   - Beispiel für einfachen Start:
     ```bash
     docker run -d --name selenium_chrome -p 4444:4444 selenium/standalone-chrome
     ```
   - Danach ist Selenium erreichbar unter `http://localhost:4444/wd/hub` (oder IP/Port anpassen).  
3. Dein eigener Docker-Container (oder lokales Python) für das **NotifyMe**-Skript:
   - Du **benötigst keinen** lokal installierten Chrome/ChromeDriver mehr, da der Zugriff remote auf den Selenium-Container erfolgt.  
4. **Discord Webhook URL**:
   - In deinem Discord-Server einen Webhook erstellen und die URL bereithalten.

---

## Installation (Docker-Variante mit externem Selenium)

### 1. Docker-Image für das Skript erstellen

Erstelle einen Ordner, der dein Skript enthält, z. B. `my_notifyme/`.  
Dort hinein legst du:

- `script.py` (das eigentliche Python-Skript)  
- `requirements.txt` (Abhängigkeiten)  
- `Dockerfile` (Baut dein Skript-Image)

**`requirements.txt`** (Beispiel):
```
selenium
requests
```

**`Dockerfile`** (Beispiel):
```dockerfile
FROM python:3.9-slim

# Environment-Variablen (können via Docker-Run überschrieben werden)
ENV SELENIUM_URL="http://localhost:4444/wd/hub"
ENV INTERVAL=15
ENV DISCORD_WEBHOOK_URL=""

# Python-Ausgabe nicht puffern
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY script.py /app/

CMD ["sh", "-c", "python script.py --interval ${INTERVAL}"]
```

In diesem Beispiel:
- `SELENIUM_URL` zeigt standardmäßig auf `http://localhost:4444/wd/hub`, kann aber überschrieben werden.  
- `INTERVAL` ist das Standard-Intervall (15 Minuten).  
- `DISCORD_WEBHOOK_URL` wird hier leer gelassen, du kannst es später beim `docker run -e DISCORD_WEBHOOK_URL=...` belegen.

Baue das Docker-Image:

```bash
cd my_notifyme
docker build -t notifyme .
```

### 2. Selenium-Container starten

Falls noch nicht geschehen, starte den **Selenium-Standalone-Chrome**-Container:

```bash
docker run -d --name selenium_chrome -p 4444:4444 selenium/standalone-chrome
```

Damit läuft Selenium auf `http://localhost:4444/wd/hub`.

### 3. NotifyMe-Container starten

Starte nun dein Docker-Image. Übergebe **Selenium-URL**, **Interval** und **Discord-Webhook** (falls gewünscht) als Umgebungsvariablen:

```bash
docker run --rm \
  -e SELENIUM_URL="http://<DEINE-SELENIUM-IP>:4444/wd/hub" \
  -e INTERVAL=10 \
  -e DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/DEIN_WEBHOOK" \
  notifyme
```

- `SELENIUM_URL` zeigt auf den Selenium-Container (lokal `localhost`, in einem Docker-Netzwerk ggf. `selenium_chrome:4444/wd/hub`).  
- `INTERVAL=10` → Prüft alle 10 Minuten (statt 15).  
- `DISCORD_WEBHOOK_URL` = deine echte Webhook-URL.  

Wenn alles klappt, siehst du Log-Ausgaben:
- `[DEBUG] main() gestartet.`
- `[DEBUG] Rufe check_all_products() auf...`
- usw.

Das Skript schickt einmalig beim Start eine Meldung an Discord und dann bei jedem Fund einer verfügbaren GPU ebenfalls eine Nachricht.

---

## Konfiguration / Code-Anpassung

### 1. URL (Region) ändern

Im `script.py` findest du eine Variable:

```python
url = "https://marketplace.nvidia.com/de-at/consumer/graphics-cards/"
```

Passe hier die Region an, z. B.:

```python
url = "https://marketplace.nvidia.com/de-de/consumer/graphics-cards/"
```

### 2. Produkte filtern

Im Code siehst du, wie JSON geparst wird und wie das Skript Verfügbarkeit (`isAvailable`) prüft.  
Du kannst selbst festlegen, ob manche Produkte oder bestimmte Modelle ignoriert werden sollen (z. B. eine `if "RTX 40" in title.upper(): continue`-Bedingung).

### 3. Headless-Modus (optional)

In `script.py` findest du:
```python
# chrome_options.add_argument("--headless")
```
Wenn du das entkommentierst, läuft Selenium ohne sichtbaren Browser. Für Docker-Umgebungen ist Headless oft sinnvoll, sollte aber mit `selenium/standalone-chrome` meistens auch standardmäßig so funktionieren. Bei Problemen kannst du `--headless` aktivieren.

---

## Nutzung außerhalb von Docker (lokal)

Möchtest du das Skript **lokal** ausführen (z. B. mit einer lokalen Chrome-Installation oder lokalem Selenium-Container), kannst du:

1. Python-Abhängigkeiten installieren:
   ```bash
   pip install selenium requests
   ```
2. **Selenium-Server (Standalone)** starten oder eine lokale Chrome-Installation + ChromeDriver einrichten.  
3. Skript ausführen:
   ```bash
   python script.py --interval 15
   ```
   (oder Umgebungsvariablen wie `SELENIUM_URL` entsprechend setzen).

---

## Tipps & Hinweise

1. **Selenium-URL (Docker-Netzwerk)**  
   Wenn du `selenium_chrome` und `notifyme` im selben Docker-Netzwerk laufen lässt, kannst du anstelle von `http://localhost:4444/wd/hub` z. B. `http://selenium_chrome:4444/wd/hub` verwenden. Stelle nur sicher, dass beide Container im selben Netzwerk sind.  

2. **Access Denied / Shadowban**  
   Wenn du den Shop zu oft anfragst (z. B. Intervall < 1 Minute), kann der Seitenbetreiber dich blockieren oder die Seite reagiert mit „Access Denied“. Ein Intervall von 10-15 Minuten ist oft sicherer.  

3. **Debugging**  
   Achte auf die `[DEBUG]`-Ausgaben im Container-Log. Wenn du nichts bekommst, prüfe, ob das Skript ordnungsgemäß gestartet ist (z. B. `docker logs <container-id>`).  

4. **Discord Webhook Sicherheit**  
   Teile deine Webhook-URL nicht öffentlich. Sonst könnten Unbefugte deinen Discord-Channel zuspammen.

---

## Funktionsweise (Kurzfassung)

1. **Script startet** und verbindet sich über `webdriver.Remote(command_executor=<SELENIUM_URL>)` zum Selenium-Container.  
2. **Seite laden**: Das Skript lädt `marketplace.nvidia.com/...`.  
3. **Produkt-Daten**: Alle versteckten `<div>`-Container mit JSON werden geparst.  
4. **Verfügbarkeit prüfen**: Ist `isAvailable == True`, wird ein Discord-Webhook ausgelöst, inkl. Link zum Kauf.  
5. **Schleife**: Danach schläft das Skript für das gewählte Intervall (z. B. 10 oder 15 Minuten) und wiederholt den Vorgang.

---

## Beispiel für eine erfolgreiche Benachrichtigung

```
**NVIDIA GeForce RTX 4070 Ti Founders Edition** ist JETZT verfügbar für 899.0!
Link: https://marketplace.nvidia.com/de-at/consumer/graphics-cards/nvidia-geforce-rtx-4070ti-fe/
```

Klicke direkt auf den Link, um (sofern vorrätig) zu kaufen.

---

## Autor & Lizenz

- Das Skript wurde ursprünglich von [@uplif3](https://github.com/uplif3) erstellt und für die neue NVIDIA Marketplace-Struktur sowie Docker + externem Selenium angepasst.  
- Du kannst es gerne weiterverbreiten und anpassen.  
- Falls du Änderungen oder Verbesserungen hast, freuen wir uns über einen Pull Request oder Issue!

### Viel Erfolg beim GPU-Jagen per Docker-Skript!
