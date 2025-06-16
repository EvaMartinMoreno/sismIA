import os
import sys
from pathlib import Path
import streamlit as st
import pandas as pd
ROOT = Path(__file__).resolve().parent.parent
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

# Credenciales y rutas 
USUARIO_GIRONA = st.secrets["USUARIO_GIRONA"]
PASSWORD_GIRONA = st.secrets["PASSWORD_GIRONA"]
USUARIO_ELCHE = st.secrets["USUARIO_ELCHE"]
PASSWORD_ELCHE = st.secrets["PASSWORD_ELCHE"]
REAL_OUTPUT = Path("data/raw/dataset_modelo.csv")
VALIDADO_OUTPUT = Path("data/raw/dataset_modelo_validado.csv")
SIM_OUTPUT = Path("data/raw/simulacion_datos_girona.csv")

# Fase 1: scraping y limpieza
def main_primera_fase():
    scrappear_eventos(USUARIO_GIRONA, PASSWORD_GIRONA, comunidad="GIRONA")
    scrappear_eventos(USUARIO_ELCHE, PASSWORD_ELCHE, comunidad="ELCHE")
    input_path = Path("data/raw/athletiks")
    generar_dataset_modelo(input_path, REAL_OUTPUT)
    
    # Aquí se fusionan los datos nuevos con los validados previos
    fusionar_datasets_validado_y_nuevos()

    print("✅ Datos reales limpios y guardados. Ahora ve a la app y valida los costes.")

# Fusionar validados con nuevos eventos sin perder validaciones anteriores
def fusionar_datasets_validado_y_nuevos():
    if not REAL_OUTPUT.exists():
        print("❌ No existe dataset_modelo.csv para fusionar.")
        return

    df_nuevo = pd.read_csv(REAL_OUTPUT)
    if VALIDADO_OUTPUT.exists():
        df_validado = pd.read_csv(VALIDADO_OUTPUT)
        df_merged = pd.concat([df_validado, df_nuevo], ignore_index=True)
        df_merged = df_merged.drop_duplicates(subset=["ID_EVENTO"], keep="first")
    else:
        df_merged = df_nuevo

    df_merged.to_csv(VALIDADO_OUTPUT, index=False)
    print("Fusión completada: dataset_modelo_validado.csv actualizado con nuevos eventos sin perder los validados.")

# Fase 2: simulación y modelos
def main_segunda_fase():
    df_real = pd.read_csv(VALIDADO_OUTPUT)
    if not df_real["COSTE_UNITARIO_VALIDADO"].any():
        raise ValueError("❌ No hay eventos con COSTE_UNITARIO_VALIDADO == True. No se puede simular.")

    if not SIM_OUTPUT.exists():
        df_simulado = generar_datos_simulados("GIRONA", "2024-01-01")
        df_simulado.to_csv(SIM_OUTPUT, index=False)
        print("✅ Simulación de datos creada.")
    else:
        print("ℹ️ Simulación ya existe. No se sobrescribe.")

    if necesita_temperatura(VALIDADO_OUTPUT):
        añadir_temperatura_a_csv(VALIDADO_OUTPUT, punto_estacion, "Reales")
    else:
        print("✅ Datos reales ya tienen temperatura.")

    if necesita_temperatura(SIM_OUTPUT):
        añadir_temperatura_a_csv(SIM_OUTPUT, punto_estacion, "Simulados")
    else:
        print("✅ Datos simulados ya tienen temperatura.")

    entrenar_modelo_asistencias()
    entrenar_modelo_beneficio()
    predecir_eventos_girona()
    print("✅ Simulación, modelos y predicciones completadas.")
 
# Ejecución directa
if __name__ == "__main__":
    main_primera_fase()
    main_segunda_fase()
