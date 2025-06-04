import os
import time
import csv
import pytesseract
import requests
import pandas as pd
from PIL import Image
from io import BytesIO
from bs4 import BeautifulSoup

# === CONFIG GENERAL ===
pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
BASE_DIR = os.path.join("sismia", "data", "raw", "races")
os.makedirs(BASE_DIR, exist_ok=True)

# === GRUPO BROTONS ===
def scrape_grupo_brotons():
    BASE_URL = "https://grupobrotons.com/events/"
    def get_links():
        res = requests.get(BASE_URL)
        soup = BeautifulSoup(res.content, 'html.parser')
        return list({a['href'] for a in soup.select('a[href*="/event/"]')})

    def extract_event(url):
        res = requests.get(url)
        soup = BeautifulSoup(res.content, 'html.parser')
        nombre = soup.select_one('h1.tribe-events-single-event-title')
        fecha = soup.select_one('abbr.tribe-events-start-date')
        imagen_tag = soup.select_one('div.tribe-events-single-event-description img')

        nombre = nombre.text.strip() if nombre else "No disponible"
        fecha = fecha.text.strip() if fecha else "No disponible"
        imagen_url = imagen_tag['src'] if imagen_tag else "No disponible"

        texto_imagen = "No disponible"
        if imagen_url != "No disponible":
            try:
                img_data = requests.get(imagen_url).content
                img = Image.open(BytesIO(img_data))
                texto_imagen = pytesseract.image_to_string(img).strip()
            except:
                texto_imagen = "Error OCR"

        return {
            "Nombre": nombre,
            "Fecha": fecha,
            "Imagen URL": imagen_url,
            "Texto Imagen": texto_imagen
        }

    links = get_links()
    print(f"🔗 [Grupo Brotons] {len(links)} eventos encontrados")
    eventos = [extract_event(link) for link in links]

    path = os.path.join(BASE_DIR, "carreras_grupobrotons.csv")
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=eventos[0].keys())
        writer.writeheader()
        writer.writerows(eventos)
    print(f"✅ Guardado: {path}")

# === RUNEDIA ===
def scrape_runedia(province="valencia", year=2025):
    def get_html(province, date, page):
        url = f"https://runedia.mundodeportivo.com/calendario-carreras/espana/{province}/provincia/tipo/distancia/{date}/0/0/{page}/"
        headers = {"User-Agent": "Mozilla/5.0"}
        return requests.get(url, headers=headers).text

    def parse_box(div):
        try:
            dia = div.find("span", class_="dia").text.strip()
            mes = div.find("span", class_="mes").text.strip()
            titulo = div.find("a", class_="nom-cursa").text.strip()
            enlace = div.find("a", class_="nom-cursa")["href"]
            localidad = div.find("span", class_="lloc").text.strip()
            spans = div.find_all("span")
            tipo = spans[-2].text.strip() if len(spans) >= 2 else None
            distancia = spans[-1].text.strip() if len(spans) >= 1 else None
            return {
                "dia": dia, "mes": mes, "titulo": titulo,
                "enlace": f"https://runedia.mundodeportivo.com{enlace}",
                "localidad": localidad, "tipo": tipo, "distancia": distancia,
                "provincia": province, "año": year
            }
        except:
            return {}

    races, page, date = [], 1, f"{year}-01"
    while True:
        print(f"🔄 Runedia - {province} {year} página {page}")
        soup = BeautifulSoup(get_html(province, date, page), "html.parser")
        boxes = soup.find_all("div", class_="item-cursa")
        if not boxes:
            break
        races += [parse_box(box) for box in boxes]
        page += 1
        time.sleep(1)

    df = pd.DataFrame(races)
    path = os.path.join(BASE_DIR, f"carreras_runedia_{province}_{year}.csv")
    df.to_csv(path, index=False)
    print(f"✅ Guardado: {path}")

# === ROCKTHESPORT ===
def scrape_rockthesport():
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)

    url = "https://web.rockthesport.com/es/es/master/calendario"
    driver.get(url)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "form-eventsCustom")))
    time.sleep(2)

    deporte_btn = driver.find_element(By.XPATH, "//app-ddlmultiple[@name='parameters.common.text.sport']//button")
    deporte_btn.click()
    time.sleep(1)
    running_chk = driver.find_element(By.XPATH, "//app-ddlmultiple[@name='parameters.common.text.sport']//li[contains(., 'Running/Atletismo')]//input")
    driver.execute_script("arguments[0].click();", running_chk)
    driver.execute_script("document.body.click();")
    time.sleep(1)

    provincia_btn = driver.find_element(By.XPATH, "//app-ddlmultiple[@name='Provincias']//button")
    provincia_btn.click()
    time.sleep(1)
    alicante_chk = driver.find_element(By.XPATH, "//app-ddlmultiple[@name='Provincias']//li[contains(., 'Alicante/Alacant')]//input")
    driver.execute_script("arguments[0].click();", alicante_chk)
    driver.execute_script("document.body.click();")
    time.sleep(3)

    eventos = driver.find_elements(By.CLASS_NAME, "panel-evento")
    data = []
    for e in eventos:
        try:
            nombre = e.find_element(By.CLASS_NAME, "event-title").text.strip()
            fecha_lugar = e.find_elements(By.TAG_NAME, "p")[0].text.strip().split('\n')
            fecha = fecha_lugar[0] if fecha_lugar else ""
            lugar = fecha_lugar[-1] if fecha_lugar else ""
            tipo = e.find_element(By.CLASS_NAME, "categoria").text.strip()
            try:
                link = e.find_element(By.XPATH, ".//a[contains(text(),'Ver')]").get_attribute("href")
            except:
                link = "No disponible"
            data.append({"Nombre": nombre, "Fecha": fecha, "Ubicación": lugar, "Tipología": tipo, "Link": link})
        except Exception as err:
            print(f"⚠️ Error evento: {err}")
            continue

    path = os.path.join(BASE_DIR, "carreras_alicante_rockthesport.csv")
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"✅ Guardado: {path}")
    driver.quit()

# === EJECUCIÓN CENTRAL ===
def ejecutar_todos():
    scrape_grupo_brotons()
    scrape_runedia("valencia", 2025)
    scrape_rockthesport()

if __name__ == "__main__":
    ejecutar_todos()  # O llama scrape_grupo_brotons() etc. si quieres ejecutarlos individualmente
