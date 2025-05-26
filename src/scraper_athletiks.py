import os
import time
import shutil
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def scrappear_eventos(usuario, password, comunidad):
    BASE_DIR = os.path.join("data", "raw", "athletiks", comunidad.upper())
    DESCARGAS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
    os.makedirs(BASE_DIR, exist_ok=True)

    # === INICIAR DRIVER ===
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

    # Verificar si sigue en login (login fallido)
    if "signin" in driver.current_url or "login" in driver.current_url:
        print("❌ Error: Credenciales inválidas")
        driver.quit()
        return False

    # === IR AL PERFIL Y EMPEZAR PROCESO ===
    driver.get("https://athletiks.io/es/profile")
    time.sleep(5)

    # === CANTIDAD DE EVENTOS ===
    event_articles = driver.find_elements(By.TAG_NAME, "article")
    total_eventos = len(event_articles)
    print(f"🔵 [{comunidad}] Eventos encontrados: {total_eventos}")

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

            # Obtener slug del evento desde la URL para usar como nombre de archivo
            parsed_url = urlparse(attendees_url)
            slug = parsed_url.path.strip("/").split("/")[-2]  # nombre-evento-fecha-codigo
            nombre_archivo = f"{slug}.csv"
            ruta_archivo = os.path.join(BASE_DIR, nombre_archivo)

            # Clic en botón "asistentes"
            try:
                download_button = driver.find_element(By.XPATH, "//button[.//span[contains(translate(text(),'ASISTENTES','asistentes'),'asistentes')]]")
                download_button.click()
                print("📥 Botón de descarga clicado")
                time.sleep(5)
            except Exception as e:
                print(f"⚠️ No se pudo clicar botón de descarga. Error: {e}")
                continue

            # Mover archivo a carpeta final
            try:
                files = [f for f in os.listdir(DESCARGAS_DIR) if f.endswith(".csv")]
                if not files:
                    print("⚠️ No se encontró ningún CSV en la carpeta de descargas.")
                else:
                    latest_file = max(
                        [os.path.join(DESCARGAS_DIR, f) for f in files],
                        key=os.path.getctime
                    )
                    shutil.move(latest_file, ruta_archivo)
                    print(f"✅ CSV guardado como: {ruta_archivo}")
            except Exception as e:
                print(f"❌ Error moviendo archivo: {e}")

        except Exception as e:
            print(f"❌ Error inesperado en evento {index + 1}: {e}")

    # === CERRAR ===
    driver.quit()
    print(f"🏁 Scraping finalizado para {comunidad}.")
    return True

