# 📦 Librerías
import os
import sys
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from src.limpieza_eventos_athletiks import generar_dataset_modelo
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
sys.path.append(str(Path(__file__).resolve().parent.parent))

# 📁 Configuración
load_dotenv()
USUARIO_GIRONA = os.getenv("USUARIO_GIRONA")
PASSWORD_GIRONA = os.getenv("PASSWORD_GIRONA")
USUARIO_ELCHE = os.getenv("USUARIO_ELCHE")
PASSWORD_ELCHE = os.getenv("PASSWORD_ELCHE")
REAL_OUTPUT = Path("data/raw/dataset_modelo.csv")
VALIDADO_OUTPUT = Path("data/raw/dataset_modelo_validado.csv")
SIM_OUTPUT = Path("data/raw/simulacion_datos_girona.csv")

# 🔄 Fase 1: scraping y limpieza
def main_primera_fase():
    scrappear_eventos(USUARIO_GIRONA, PASSWORD_GIRONA, comunidad="GIRONA")
    scrappear_eventos(USUARIO_ELCHE, PASSWORD_ELCHE, comunidad="ELCHE")
    input_path = Path("data/raw/athletiks")
    generar_dataset_modelo(input_path, REAL_OUTPUT)
    print("✅ Datos reales limpios y guardados. Ahora ve a la app y valida los costes.")

# 🔄 Fase 2: simulación y modelos
def main_segunda_fase():
    df_real = pd.read_csv(VALIDADO_OUTPUT)
    if not df_real["COSTE_UNITARIO_VALIDADO"].any():
        raise ValueError("❌ No hay eventos con COSTE_UNITARIO_VALIDADO == True. No se puede simular.")
    
    df_simulado = generar_datos_simulados("GIRONA", "2024-01-01")
    df_simulado.to_csv("data/raw/simulacion_datos_girona.csv", index=False)

    if necesita_temperatura(VALIDADO_OUTPUT):
        añadir_temperatura_a_csv(VALIDADO_OUTPUT, punto_estacion, "Reales")
    if necesita_temperatura(SIM_OUTPUT):
        añadir_temperatura_a_csv(SIM_OUTPUT, punto_estacion, "Simulados")

    entrenar_modelo_asistencias()
    entrenar_modelo_beneficio()
    predecir_eventos_girona()

    print("✅ Simulación, modelos y predicciones completadas.")
