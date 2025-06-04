import os
import pickle
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# === CONFIGURACIÓN ===
USUARIO = "emjemj9"
PASSWORD = "MuchoElche25"
CUENTAS = [
    "thegingerclub_", "hybnrun", "ramones_running", "narinant.socialrun",
    "kilometrouno_", "madeforsocialrunclub", "madrunnerss", "revel.club",
    "vibesnclub", "estesorunners", "voltarunclub", "b3tterrunclubb",
    "clanrunning", "unofficialrunclub", "socialrunclubvlc", "runninggirlscanarias",
    "goforthrunners", "coolgirlsrun.co"
]
COOKIES_PATH = "cookies"
COOKIES_FILE = os.path.join(COOKIES_PATH, "cookies.pkl")

# === Preparar navegador ===
options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# === Intentar cargar cookies ===
driver.get("https://www.instagram.com/")
time.sleep(5)
cookies_cargadas = False

if os.path.exists(COOKIES_FILE):
    try:
        with open(COOKIES_FILE, "rb") as f:
            cookies = pickle.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
        driver.refresh()
        time.sleep(5)
        if "login" not in driver.current_url:
            print("✅ Sesión restaurada desde cookies.")
            cookies_cargadas = True
    except Exception as e:
        print("⚠️ Error cargando cookies:", e)

# === Login manual si no había cookies ===
if not cookies_cargadas:
    driver.get("https://www.instagram.com/accounts/login/")
    time.sleep(5)
    username_input = driver.find_element(By.NAME, "username")
    password_input = driver.find_element(By.NAME, "password")
    username_input.send_keys(USUARIO)
    password_input.send_keys(PASSWORD)
    password_input.send_keys(Keys.RETURN)
    time.sleep(8)

    if "login" in driver.current_url:
        print("❌ Login fallido.")
        driver.quit()
        exit()

    os.makedirs(COOKIES_PATH, exist_ok=True)
    with open(COOKIES_FILE, "wb") as f:
        pickle.dump(driver.get_cookies(), f)
    print("✅ Login exitoso. Cookies guardadas.")

# === Scraping para cada cuenta ===
for CUENTA in CUENTAS:
    print(f"\n🔍 Procesando cuenta: {CUENTA}")
    URL = f"https://www.instagram.com/{CUENTA}/"
    driver.get(URL)
    time.sleep(5)

    # Scroll para cargar posts
    for _ in range(2):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    post_links = list({a.get_attribute("href") for a in driver.find_elements(By.TAG_NAME, "a") if "/p/" in a.get_attribute("href")})
    post_links = post_links[:10]

    data = []

    for link in post_links:
        try:
            driver.get(link)
            time.sleep(6)  # Espera extra para asegurar carga completa

            # === Fecha
            fecha = None
            try:
                fecha_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "time"))
                )
                fecha = fecha_element.get_attribute("datetime")
            except:
                pass

            # === Texto y hashtags del caption
            texto = ""
            hashtags = []

            try:
                # Espera un poco extra para asegurarse de que carga todo
                time.sleep(2)

                spans = driver.find_elements(By.XPATH, '//div[@data-testid="post-comment-root"]//span')
                for s in spans:
                    posible_texto = s.text.strip()
                    if posible_texto:
                        texto = posible_texto
                        break

                hashtags = [word for word in texto.split() if word.startswith("#")]

                if not texto:
                    print("⚠️ Post sin texto visible (caption vacío o no cargado aún)")

            except Exception as e:
                print(f"⚠️ Error extrayendo el caption: {e}")


            # === Tipo de post
            tipo = "carrusel" if driver.find_elements(By.XPATH, '//div[@role="button"][@aria-label="Siguiente"]') else "imagen"
            if driver.find_elements(By.TAG_NAME, "video"):
                tipo = "video"

            # === Likes
            likes = None
            try:
                like_text = driver.execute_script("""
                    const spans = document.querySelectorAll('span');
                    for (const span of spans) {
                        if (span.textContent.includes('Me gusta') || span.textContent.includes('likes')) {
                            const number = span.querySelector('span');
                            if (number && !isNaN(parseInt(number.textContent.replace('.', '')))) {
                                return number.textContent;
                            }
                        }
                    }
                    return null;
                """)
                likes = like_text.replace('.', '') if like_text else None
            except:
                likes = None

            # === Comentarios
            comentarios = 0
            try:
                comment_count = driver.execute_script("return document.querySelectorAll('ul ul').length;")
                comentarios = int(comment_count)
            except:
                comentarios = 0

            print(f"✅ Post: {link} | Likes: {likes} | Comentarios: {comentarios}")

            data.append({
                "cuenta": CUENTA,
                "url": link,
                "fecha": fecha,
                "tipo": tipo,
                "texto": texto,
                "hashtags": ", ".join(hashtags),
                "likes": likes,
                "comentarios": comentarios
            })

        except Exception as e:
            print(f"⚠️ Error procesando {link}: {e}")

    # Guardar CSV
    df = pd.DataFrame(data)
    os.makedirs("data/raw/externos", exist_ok=True)
    nombre_csv = f"data/raw/externos/instagram_{CUENTA}.csv"
    df.to_csv(nombre_csv, index=False, encoding="utf-8")
    print(f"📁 CSV guardado: {nombre_csv}")

driver.quit()
