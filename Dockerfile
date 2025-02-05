# 1. Schlankes Python-Image verwenden
FROM python:3.9-slim

# 2. Default-Werte für Env Vars (können beim "docker run" überschrieben werden)
#ENV SELENIUM_URL="http://vienna:4444/wd/hub"
ENV SELENIUM_URL="<selenium_url>"
ENV INTERVAL=15
ENV DISCORD_WEBHOOK_URL="<webhook>"

# Debug: verhindert das Puffern von Python-Ausgaben
ENV PYTHONUNBUFFERED=1

# 3. Arbeitsverzeichnis
WORKDIR /app

# 4. requirements installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Eigentlichen Code kopieren
COPY script.py /app/

# 6. Standard-Kommando (Einstiegspunkt)
#    Wir setzen hier INTERVAL als Env Var ein, damit script.py ihn parsen kann.
CMD ["sh", "-c", "python script.py --interval ${INTERVAL}"]
