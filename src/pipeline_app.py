# 📦 Librerías
import os
import sys
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.cleaning.limpieza_eventos_athletiks import generar_dataset_modelo
from src.scraping.scraper_athletiks import scrappear_eventos
from src.scraping.scraper_temperatura import (
    añadir_temperatura_a_csv,
    necesita_temperatura,
    punto_estacion,
)
from src.modelos.modelo_beneficio_Girona import entrenar_modelo_beneficio
from src.modelos.modelo_asistencias_Girona import entrenar_modelo_asistencias
from src.simulacion_datos import generar_datos_simulados
from src.modelos.eventos_futuros_Girona import predecir_eventos_girona

# --------------------------------------------------------------------
# 📁 Configuración
# --------------------------------------------------------------------
load_dotenv()
USUARIO_GIRONA = os.getenv("USUARIO_GIRONA")
PASSWORD_GIRONA = os.getenv("PASSWORD_GIRONA")
USUARIO_ELCHE = os.getenv("USUARIO_ELCHE")
PASSWORD_ELCHE = os.getenv("PASSWORD_ELCHE")

# --------------------------------------------------------------------
# 1. Scraping
# --------------------------------------------------------------------
def actualizar_datos_girona():
    scrappear_eventos(
        usuario=USUARIO_GIRONA,
        password=PASSWORD_GIRONA,
        comunidad="GIRONA"
    )

def actualizar_datos_elche():
    scrappear_eventos(
        usuario=USUARIO_ELCHE,
        password=PASSWORD_ELCHE,
        comunidad="ELCHE"
    )

# --------------------------------------------------------------------
# 2. Limpieza de eventos
# --------------------------------------------------------------------
# --------------------------------------------------------------------
# 2. Limpieza de eventos (ahora exporta a RAW)
# --------------------------------------------------------------------
REAL_PATH = Path("data/raw/eventos_crudos_unificados.csv")
SIM_PATH = Path("data/raw/simulacion_datos_girona.csv")
REAL_OUTPUT = Path("data/raw/dataset_modelo.csv")     
SIM_OUTPUT = Path("data/clean/simulacion_datos_girona.csv")

def ejecutar_limpieza():
    input_path = Path("data/raw/athletiks")
    output_path = Path("data/raw/dataset_modelo.csv")
    generar_dataset_modelo(input_path, output_path)
    print("✅ Dataset limpio guardado en RAW. Ahora debes introducir los datos manualmente desde la app.")
    
# --------------------------------------------------------------------
# 3. Añadir variable TEMPERATURA a datasets (solo si falta)
# --------------------------------------------------------------------
def enriquecer_con_temperatura():
    if necesita_temperatura(REAL_OUTPUT):
        print("🌡️ Añadiendo temperatura a datos REALES...")
        añadir_temperatura_a_csv(REAL_OUTPUT, punto_estacion, "Reales")
    else:
        print("✅ Datos REALES ya tienen temperatura.")

    if necesita_temperatura(SIM_OUTPUT):
        print("🌡️ Añadiendo temperatura a datos SIMULADOS...")
        añadir_temperatura_a_csv(SIM_OUTPUT, punto_estacion, "Simulados")
    else:
        print("✅ Datos SIMULADOS ya tienen temperatura.")

# --------------------------------------------------------------------
# 4. Simulación de eventos futuros
# --------------------------------------------------------------------
def simular_eventos_Girona():
    df_simulado = generar_datos_simulados("GIRONA", "2024-01-01")
    output_path = Path("data/raw/simulacion_datos_girona.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_simulado.to_csv(output_path, index=False)
    print(f"✅ Dataset simulado generado con {len(df_simulado)} eventos.")
    print(f"📁 Guardado en: {output_path.resolve()}")

# --------------------------------------------------------------------
# 5. Entrenamiento de modelos
# --------------------------------------------------------------------
def entrenar_modelos():
    entrenar_modelo_asistencias()
    entrenar_modelo_beneficio()

# --------------------------------------------------------------------
# 6. Predicción de eventos futuros
# --------------------------------------------------------------------
def generar_predicciones():
    predecir_eventos_girona()

# --------------------------------------------------------------------
# 🔁 MAIN PIPELINE
# --------------------------------------------------------------------
def main():
    actualizar_datos_girona()
    actualizar_datos_elche()
    ejecutar_limpieza()
    simular_eventos_Girona()
    enriquecer_con_temperatura()
    entrenar_modelos()
    generar_predicciones()
    print("✅ Pipeline ejecutado correctamente.")

if __name__ == "__main__":
    main()
