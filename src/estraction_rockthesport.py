import os
import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === CONFIGURACIÓN ===
output_folder = os.path.join("sismia","data", "raw", "races")
os.makedirs(output_folder, exist_ok=True)
csv_filename = os.path.join(output_folder, "carreras_alicante_rockthesport.csv")

# === INICIALIZAR NAVEGADOR ===
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)

try:
    # === ABRIR PÁGINA DE CALENDARIO ===
    driver.get("https://web.rockthesport.com/es/es/master/calendario")
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "form-eventsCustom")))
    time.sleep(2)

    # === SELECCIONAR FILTRO "Running/Atletismo" ===
    deporte_btn = driver.find_element(By.XPATH, "//app-ddlmultiple[@name='parameters.common.text.sport']//button")
    deporte_btn.click()
    time.sleep(1)
    running_chk = driver.find_element(By.XPATH, "//app-ddlmultiple[@name='parameters.common.text.sport']//li[contains(., 'Running/Atletismo')]//input")
    driver.execute_script("arguments[0].click();", running_chk)
    time.sleep(1)

    # === CERRAR DESPLEGABLE DE DEPORTE ===
    driver.execute_script("document.body.click();")
    time.sleep(1)

    # === SELECCIONAR FILTRO "Alicante/Alacant" ===
    provincia_btn = driver.find_element(By.XPATH, "//app-ddlmultiple[@name='Provincias']//button")
    provincia_btn.click()
    time.sleep(1)
    alicante_chk = driver.find_element(By.XPATH, "//app-ddlmultiple[@name='Provincias']//li[contains(., 'Alicante/Alacant')]//input")
    driver.execute_script("arguments[0].click();", alicante_chk)
    time.sleep(1)

    # === CERRAR DESPLEGABLE DE PROVINCIA ===
    driver.execute_script("document.body.click();")
    time.sleep(3)  # espera extra por si tarda en actualizar

    # === EXTRAER EVENTOS ===
    eventos = driver.find_elements(By.CLASS_NAME, "panel-evento")
    data = []

    for e in eventos:
        try:
            nombre = e.find_element(By.CLASS_NAME, "event-title").text.strip()
            fecha = e.find_elements(By.TAG_NAME, "p")[0].text.strip().split('\n')[0]
            lugar = e.find_elements(By.TAG_NAME, "p")[0].text.strip().split('\n')[-1]
            tipologia = e.find_element(By.CLASS_NAME, "categoria").text.strip()

            # Extraer el link del botón "Ver"
            try:
                ver_btn = e.find_element(By.XPATH, ".//a[contains(text(),'Ver')]")
                link = ver_btn.get_attribute("href")
            except:
                link = "No disponible"

            data.append({
                "Nombre": nombre,
                "Fecha": fecha,
                "Ubicación": lugar,
                "Tipología": tipologia,
            })

        except Exception as err:
            print(f"⚠️ Error en evento: {err}")
            continue


    # === GUARDAR CSV ===
    with open(csv_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["Nombre", "Fecha", "Ubicación", "Tipología"])
        writer.writeheader()
        for row in data:
            writer.writerow(row)

    print(f"✅ Datos guardados en: {csv_filename}")

finally:
    driver.quit()
    print("\n🏁 Proceso terminado.")
