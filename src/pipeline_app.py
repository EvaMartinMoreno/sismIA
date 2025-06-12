# 📦 Librerías
import os
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from src.cleaning.limpieza_eventos_athletiks import generar_dataset_modelo
from src.scraping.scraper_athletiks import scrappear_eventos
from src.scraping.scraper_temperatura import añadir_temperatura, punto_estacion
import joblib
from datetime import timedelta
from selenium import webdriver
from src.modelos.modelo_beneficio_Girona import entrenar_modelo_beneficio
from src.modelos.modelo_asistencias_Girona import entrenar_modelo_asistencias
from src.simulacion_datos import generar_datos_simulados
from src.modelos.eventos_futuros_Girona import predecir_eventos_girona

# ------------------------------------------------------------------------------
# 📁 Configuración
# ------------------------------------------------------------------------------
load_dotenv()
USUARIO_GIRONA = os.getenv("USUARIO_GIRONA")
PASSWORD_GIRONA = os.getenv("PASSWORD_GIRONA")
USUARIO_ELCHE = os.getenv("USUARIO_ELCHE")
PASSWORD_ELCHE = os.getenv("PASSWORD_ELCHE")

# ------------------------------------------------------------------------------
# 1. Scraping
# ------------------------------------------------------------------------------
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
        comunidad="ELCHE",
    )

# ------------------------------------------------------------------------------
# 2. Limpieza de eventos
# ------------------------------------------------------------------------------
def ejecutar_limpieza():
    input_path = Path("data/raw/athletiks/eventos_crudos_unificados.csv")
    output_path = Path("data/clean/dataset_modelo.csv")
    tipos_path = Path("data/raw/selector/tipos_evento.csv")

    generar_dataset_modelo(input_path, output_path, tipos_path)

    df = pd.read_csv(output_path)
    eventos_sin_tipo = df[df["TIPO_ACTIVIDAD"] == "otro"]["NOMBRE_EVENTO"].unique()

    if len(eventos_sin_tipo) > 0:
        print(f" Hay {len(eventos_sin_tipo)} eventos sin categorizar.")
        df[["NOMBRE_EVENTO", "FECHA_EVENTO"]].to_csv("data/entrada/eventos_sin_tipo.csv", index=False)
        raise Exception(" STOP: Hay eventos sin categorizar. Corrige antes de seguir.")
    else:
        print("odos los eventos están correctamente categorizados.")

# ------------------------------------------------------------------------------
# 3. Añadir variable TEMPERATURA a datasets
# ------------------------------------------------------------------------------
def enriquecer_con_temperatura():
    from scraping.scraper_temperatura import REAL_PATH, SIM_PATH, REAL_OUTPUT, SIM_OUTPUT
    df_real = pd.read_csv(REAL_PATH)
    df_sim = pd.read_csv(SIM_PATH)

    df_real = añadir_temperatura(df_real, punto_estacion, "Reales")
    df_sim = añadir_temperatura(df_sim, punto_estacion, "Simulados")

    df_real.to_csv(REAL_OUTPUT, index=False)
    df_sim.to_csv(SIM_OUTPUT, index=False)

# ------------------------------------------------------------------------------
# 4 Simulación de eventos futuros
# ------------------------------------------------------------------------------
def simular_eventos_Girona():
    df_simulado = generar_datos_simulados("GIRONA", "2024-01-01")
    output_path = Path("data/raw/simulacion_datos_girona.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_simulado.to_csv(output_path, index=False)
    print(f"Dataset simulado generado con {len(df_simulado)} eventos.")
    print(f"Guardado en: {output_path.resolve()}")

# ------------------------------------------------------------------------------
# 5. Entrenamiento de modelos
# ------------------------------------------------------------------------------
def entrenar_modelos():
    entrenar_modelo_asistencias()
    entrenar_modelo_beneficio()

# ------------------------------------------------------------------------------
# 6. Generación de predicciones futuras
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# 7. Sugerencia de próxima fecha
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# 🔁 MAIN PIPELINE
# ------------------------------------------------------------------------------
def main():
    actualizar_datos_girona()
    actualizar_datos_elche()
    ejecutar_limpieza()
    simular_eventos_Girona()
    enriquecer_con_temperatura()
    entrenar_modelos()
    predecir_eventos_girona()
    entrenar_modelo_asistencias()
    entrenar_modelo_beneficio()
    print("Pipeline ejecutado correctamente.")

if __name__ == "__main__":
    main()
