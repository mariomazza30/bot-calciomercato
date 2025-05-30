from flask import Flask
import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# === CONFIG ===
SPREADSHEET_NAME = 'Calciomercato Serie A'
SHEET_NAME = 'Notizie'
CRED_FILE = 'credenziali.json'

# === Google Sheets Setup ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(CRED_FILE, scope)
client = gspread.authorize(creds)
sheet = client.open(SPREADSHEET_NAME).worksheet(SHEET_NAME)

def è_ufficiale(testo):
    testo = testo.lower()
    return any(kw in testo for kw in ["ufficiale", "ha firmato", "nuovo giocatore", "passa al", "è della", "ha annunciato", "accolto"])

def esegui_scraping():
    url = 'https://sport.sky.it/calciomercato'
    res = requests.get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    articoli = soup.find_all('div', class_='news-list__item')

    righe_attuali = sheet.get_all_values()
    titoli_esistenti = [riga[0] for riga in righe_attuali]

    aggiunti = 0

    for articolo in articoli:
        titolo_tag = articolo.find('h3')
        if not titolo_tag:
            continue
        titolo = titolo_tag.get_text(strip=True)

        if not è_ufficiale(titolo) or titolo in titoli_esistenti:
            continue

        link_tag = articolo.find('a')
        if not link_tag or not link_tag.get('href'):
            continue

        link = "https://sport.sky.it" + link_tag['href']
        oggi = datetime.now().strftime('%d/%m/%Y')
        squadra = titolo.split()[-1] if titolo.split()[-1].istitle() else "?"
        operazione = "Acquisto" if "acquisto" in titolo.lower() or "firma" in titolo.lower() else "?"

        sheet.append_row([titolo, link, oggi, squadra, operazione, "", "", ""])
        aggiunti += 1

    return aggiunti

@app.route('/')
def ping():
    aggiunte = esegui_scraping()
    return f'✅ Bot attivo – Notizie ufficiali aggiunte: {aggiunte}'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)