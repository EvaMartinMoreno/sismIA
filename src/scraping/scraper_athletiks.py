
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import shutil
import os
import csv
from urllib.parse import urljoin, urlparse
import pandas as pd


def scrappear_eventos(usuario, password, comunidad):
    BASE_DIR = os.path.join("data", "raw", "athletiks", comunidad.upper())
    DESCARGAS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
    os.makedirs(BASE_DIR, exist_ok=True)

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    prefs = {"download.default_directory": os.path.abspath(DESCARGAS_DIR)}
    options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # === LOGIN ===
    driver.get("https://athletiks.io/es/signin?redirectTo=/es")
    time.sleep(3)
    driver.find_element(By.NAME, "email").send_keys(usuario)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
    time.sleep(5)

    if "signin" in driver.current_url or "login" in driver.current_url:
        print("❌ Error: Credenciales inválidas")
        driver.quit()
        return

    print(f"📌 [{comunidad}] Buscando eventos con inscripción abierta...")

    index = 0
    while True:
        driver.get("https://athletiks.io/es/profile")
        time.sleep(3)

        event_articles = driver.find_elements(By.TAG_NAME, "article")
        total_eventos = len(event_articles)
        if index == 0:
            print(f"🔍 Se han detectado {total_eventos} eventos en la página de perfil.")

        if index >= total_eventos:
            break

        try:
            article = event_articles[index]
            driver.execute_script("arguments[0].scrollIntoView(true);", article)
            time.sleep(1)
            article.click()
            time.sleep(3)

            current_url = driver.current_url
            if not current_url.endswith("/"):
                current_url += "/"
            attendees_url = urljoin(current_url, "attendees")
            driver.get(attendees_url)
            time.sleep(2)

            parsed_url = urlparse(attendees_url)
            slug = parsed_url.path.strip("/").split("/")[-2]
            nombre_archivo = f"{slug}.csv"
            ruta_archivo = os.path.join(BASE_DIR, nombre_archivo)

            if os.path.exists(ruta_archivo):
                print(f"✅ Ya existe: {nombre_archivo}. Saltando.")
                index += 1
                continue

            try:
                download_button = driver.find_element(By.XPATH, "//button[.//span[contains(translate(text(),'ASISTENTES','asistentes'),'asistentes')]]")
                download_button.click()
                print("📥 Botón de descarga clicado")
                time.sleep(5)
            except Exception:
                print("🚫 Evento sin inscripción abierta o sin botón de descarga. Saltando.")
                index += 1
                continue

            try:
                files = [f for f in os.listdir(DESCARGAS_DIR) if f.endswith(".csv")]
                if not files:
                    print("❌ No se encontró ningún CSV en la carpeta de descargas.")
                else:
                    latest_file = max(
                        [os.path.join(DESCARGAS_DIR, f) for f in files],
                        key=os.path.getctime
                    )

                    # Leer y reparar delimitador si es necesario
                    with open(latest_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Comprobamos si hay solo una columna mal separada
                    if content.count(";") > 5 and "," not in content:
                        with open(latest_file, "w", encoding="utf-8", newline="") as f:
                            f.write(content)

                    shutil.move(latest_file, ruta_archivo)
                    print(f"✅ CSV guardado como: {ruta_archivo}")
            except Exception as e:
                print(f"❌ Error moviendo archivo: {e}")

        except Exception as e:
            print(f"⚠️ Error inesperado: {e}")

        index += 1

    driver.quit()
    print(f"🚀 Scraping finalizado para {comunidad}.")


if __name__ == "__main__":
    import getpass

    print("🟣 Scraper de Athletiks")
    comunidad = input("Comunidad (ej. Girona, Elche): ").strip()
    usuario = input("Email: ").strip()
    password = getpass.getpass("Contraseña: ")

    scrappear_eventos(usuario, password, comunidad)
