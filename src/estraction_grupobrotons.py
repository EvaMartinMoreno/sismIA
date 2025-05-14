import os
import time
import csv
import pytesseract
import requests
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# === CONFIGURACIÓN ===
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
BASE_URL = "https://grupobrotons.com/events/"
output_folder = os.path.join("sismia","data", "raw", "races")
os.makedirs(output_folder, exist_ok=True)
csv_filename = os.path.join(output_folder, "carreras_grupobrotons.csv")

# === FUNCIONES AUXILIARES ===
def get_event_links():
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.content, 'html.parser')
    links = []

    for a in soup.select('a[href*="/event/"]'):
        href = a.get('href')
        if href and href not in links:
            links.append(href)

    return links

def extract_event_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    try:
        nombre = soup.select_one('h1.tribe-events-single-event-title').text.strip()
    except:
        nombre = "No disponible"

    try:
        fecha = soup.select_one('abbr.tribe-events-start-date').text.strip()
    except:
        fecha = "No disponible"

    try:
        imagen_url = soup.select_one('div.tribe-events-single-event-description img')['src']
    except:
        imagen_url = "No disponible"

    # === OCR desde imagen ===
    texto_imagen = "No disponible"
    if imagen_url != "No disponible":
        try:
            img_response = requests.get(imagen_url)
            img = Image.open(BytesIO(img_response.content))
            texto_imagen = pytesseract.image_to_string(img).strip()
        except Exception as ocr_error:
            print(f"⚠️ Error OCR en {url}: {ocr_error}")
            texto_imagen = "Error OCR"

    return {
        "Nombre": nombre,
        "Fecha": fecha,
        "Imagen URL": imagen_url,
        "Texto Imagen": texto_imagen
    }

# === PROCESO PRINCIPAL ===
event_links = get_event_links()
print(f"🔗 Se encontraron {len(event_links)} eventos.")

event_data = []
for link in event_links:
    print(f"📥 Procesando: {link}")
    data = extract_event_data(link)
    event_data.append(data)

# === GUARDAR CSV ===
with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=["Nombre", "Fecha", "Imagen URL", "Texto Imagen"])
    writer.writeheader()
    writer.writerows(event_data)

print(f"\n✅ Datos guardados en: {csv_filename}")
