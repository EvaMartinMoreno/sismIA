import os
import time
import shutil
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# === CONFIGURACIÓN ===
ATHLETIKS_EMAIL = "sisterhoodrunningclub@gmail.com"
ATHLETIKS_PASSWORD = "SHcarlota23"
DOWNLOAD_FOLDER = os.path.join("sismia", "sismia", "data", "raw")
DESCARGAS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# === INICIAR DRIVER ===
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
prefs = {"download.default_directory": os.path.abspath(DESCARGAS_DIR)}
options.add_experimental_option("prefs", prefs)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# === LOGIN ===
driver.get("https://athletiks.io/es/signin?redirectTo=/es")
time.sleep(3)
driver.find_element(By.NAME, "email").send_keys(ATHLETIKS_EMAIL)
driver.find_element(By.NAME, "password").send_keys(ATHLETIKS_PASSWORD)
driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
time.sleep(5)

# === IR AL PERFIL Y EMPEZAR PROCESO ===
driver.get("https://athletiks.io/es/profile")
time.sleep(5)

# === CANTIDAD DE EVENTOS ===
event_articles = driver.find_elements(By.TAG_NAME, "article")
total_eventos = len(event_articles)
print(f"🔵 Eventos encontrados: {total_eventos}")

for index in range(total_eventos):
    try:
        print(f"\n➡️ Procesando evento {index + 1} de {total_eventos}...")

        # Volver al perfil y refrescar la lista de eventos
        driver.get("https://athletiks.io/es/profile")
        time.sleep(4)
        event_articles = driver.find_elements(By.TAG_NAME, "article")

        if index >= len(event_articles):
            print("⚠️ El índice ya no existe. Saltando evento.")
            continue

        article = event_articles[index]

        # Abrir evento
        driver.execute_script("arguments[0].scrollIntoView(true);", article)
        time.sleep(1)
        article.click()
        time.sleep(4)

        # Ir a /attendees
        current_url = driver.current_url
        if not current_url.endswith("/"):
            current_url += "/"
        attendees_url = urljoin(current_url, "attendees")
        driver.get(attendees_url)
        print(f"➡️ Página de asistentes: {attendees_url}")
        time.sleep(4)

        # Clic en botón "asistentes"
        try:
            download_button = driver.find_element(By.XPATH, "//button[.//span[contains(translate(text(),'ASISTENTES','asistentes'),'asistentes')]]")
            download_button.click()
            print("📥 Botón de descarga clicado")
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ No se pudo clicar botón de descarga. Error: {e}")
            continue

        # Mover archivo a carpeta
        try:
            files = [f for f in os.listdir(DESCARGAS_DIR) if f.endswith(".csv")]
            if not files:
                print("⚠️ No se encontró ningún CSV en la carpeta de descargas.")
            else:
                latest_file = max(
                    [os.path.join(DESCARGAS_DIR, f) for f in files],
                    key=os.path.getctime
                )
                target_path = os.path.join(DOWNLOAD_FOLDER, os.path.basename(latest_file))
                shutil.move(latest_file, target_path)
                print(f"✅ CSV movido a: {target_path}")
        except Exception as e:
            print(f"❌ Error moviendo archivo: {e}")

    except Exception as e:
        print(f"❌ Error inesperado en evento {index + 1}: {e}")

# === CERRAR ===
driver.quit()
print("\n🏁 Proceso terminado.")
