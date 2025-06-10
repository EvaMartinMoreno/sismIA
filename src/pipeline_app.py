# 📦 Librerías
import os
import json
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from cleaning.limpieza_eventos_athletiks import generar_dataset_modelo
from scraping.scraper_athletiks import scrappear_eventos
from scraping.scraper_temperatura import añadir_temperatura, punto_estacion
import joblib
from datetime import timedelta
from selenium import webdriver
from modelos.modelo_beneficio_Girona import entrenar_modelo_beneficio
from modelos.modelo_asistencias_Girona import entrenar_modelo_asistencias

# ------------------------------------------------------------------------------
# 📁 Configuración
# ------------------------------------------------------------------------------
load_dotenv()
USUARIO_GIRONA = os.getenv("USUARIO_GIRONA")
PASSWORD_GIRONA = os.getenv("PASSWORD_GIRONA")
USUARIO_ELCHE = os.getenv("USUARIO_ELCHE")
PASSWORD_ELCHE = os.getenv("PASSWORD_ELCHE")
ESTADO_PATH = Path("data/raw/athletiks/estado_scraping.json")

# ------------------------------------------------------------------------------
# 1. Scraping
# ------------------------------------------------------------------------------
def cargar_estado():
    if ESTADO_PATH.exists():
        with open(ESTADO_PATH, "r") as f:
            return json.load(f)
    return {}

def guardar_estado(estado):
    with open(ESTADO_PATH, "w") as f:
        json.dump(estado, f, indent=2)

def actualizar_datos_girona():
    estado = cargar_estado()
    estado_actualizado = scrappear_eventos(
        usuario=USUARIO_GIRONA,
        password=PASSWORD_GIRONA,
        comunidad="GIRONA",
        estado_scraping=estado,
        status="dev"
    )
    guardar_estado(estado_actualizado)

def actualizar_datos_elche():
    estado = cargar_estado()
    estado_actualizado = scrappear_eventos(
        usuario=USUARIO_ELCHE,
        password=PASSWORD_ELCHE,
        comunidad="ELCHE",
        estado_scraping=estado
    )
    guardar_estado(estado_actualizado)

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
        print(f"⚠️ Hay {len(eventos_sin_tipo)} eventos sin categorizar.")
        df[["NOMBRE_EVENTO", "FECHA_EVENTO"]].to_csv("data/entrada/eventos_sin_tipo.csv", index=False)
        raise Exception("⛔ STOP: Hay eventos sin categorizar. Corrige antes de seguir.")
    else:
        print("✅ Todos los eventos están correctamente categorizados.")

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
# 4. Entrenamiento de modelos
# ------------------------------------------------------------------------------
def entrenar_modelos():
    entrenar_modelo_asistencias()
    entrenar_modelo_beneficio()

# ------------------------------------------------------------------------------
# 5. Generación de predicciones futuras
# ------------------------------------------------------------------------------
def generar_predicciones():
    from pathlib import Path
    import pandas as pd

    PATH_SIM = Path("data/raw/simulacion_datos_girona.csv")
    OUTPUT_ASISTENCIA = Path("stats/datasets/Girona_prediccion_asistentes_futuros.csv")
    OUTPUT_BENEFICIO = Path("stats/datasets/Girona_prediccion_beneficio_eventos_futuros.csv")
    MODEL_ASISTENCIA = Path("models/reglineal_asistencias_girona.pkl")
    MODEL_BENEFICIO = Path("src/models/modelo_beneficio_Girona.pkl")

    if not MODEL_ASISTENCIA.exists() or not MODEL_BENEFICIO.exists():
        print("⚠️ No se encuentran modelos entrenados. Aborta generación de predicciones.")
        return

    df_sim = pd.read_csv(PATH_SIM, parse_dates=["FECHA_EVENTO"])
    hoy = pd.Timestamp.today().normalize()
    df_futuro = df_sim[(df_sim["TIPO_EVENTO"] == "pago") & (df_sim["FECHA_EVENTO"] >= hoy)].copy()

    if df_futuro.empty:
        print("No hay eventos futuros para predecir.")
        return

    # === Asistencia
    modelo_asistencia = joblib.load(MODEL_ASISTENCIA)
    features_asist = modelo_asistencia.feature_names_in_
    X_asist = pd.get_dummies(df_futuro, columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)
    X_asist = X_asist.reindex(columns=features_asist, fill_value=0)
    df_futuro["ASISTENCIA_PREVISTA"] = modelo_asistencia.predict(X_asist).round().astype(int)

    # === Beneficio
    modelo_beneficio = joblib.load(MODEL_BENEFICIO)
    features_benef = modelo_beneficio.feature_names_in_
    X_benef = pd.get_dummies(df_futuro, columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)
    X_benef = X_benef.reindex(columns=features_benef, fill_value=0)
    df_futuro["BENEFICIO_PREDICHO"] = modelo_beneficio.predict(X_benef).round(2)

    columnas_finales = [
        "NOMBRE_EVENTO", "FECHA_EVENTO", "COMUNIDAD", "TIPO_EVENTO", "TIPO_ACTIVIDAD",
        "COSTE_UNITARIO", "PRECIO_MEDIO", "COLABORACION",
        "ASISTENCIA_PREVISTA", "BENEFICIO_PREDICHO"
    ]
    df_futuro[columnas_finales].to_csv(OUTPUT_BENEFICIO, index=False)
    print(f"✅ Predicción beneficio guardada en: {OUTPUT_BENEFICIO.resolve()}")

# ------------------------------------------------------------------------------
# 6. Sugerencia de próxima fecha
# ------------------------------------------------------------------------------
def sugerir_fecha_evento():
    PATH_EVENTOS = Path("data/clean/dataset_modelo.csv")
    PATH_FECHA_SUGERIDA = Path("stats/datasets/proxima_fecha_sugerida.csv")

    def sugerir_proxima_fecha(ultima_fecha, fechas_existentes, dias_entre_eventos=30):
        fecha = ultima_fecha + timedelta(days=dias_entre_eventos)
        while fecha.weekday() != 6:
            fecha += timedelta(days=1)
        fechas_existentes_set = set([f.date() for f in fechas_existentes])
        while fecha.date() in fechas_existentes_set:
            fecha += timedelta(weeks=1)
        return fecha

    df = pd.read_csv(PATH_EVENTOS, parse_dates=["FECHA_EVENTO"])
    df = df[(df["COMUNIDAD"].str.upper() == "GIRONA") & (df["TIPO_EVENTO"] == "pago")]

    if df.empty:
        print("⚠️ No hay eventos suficientes para sugerir una fecha.")
        return

    fechas = df["FECHA_EVENTO"].sort_values().tolist()
    ultima_fecha = fechas[-1]
    sugerida = sugerir_proxima_fecha(ultima_fecha, fechas)

    Path(PATH_FECHA_SUGERIDA.parent).mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{"FECHA_SUGERIDA": sugerida}]).to_csv(PATH_FECHA_SUGERIDA, index=False)

# ------------------------------------------------------------------------------
# 🔁 MAIN PIPELINE
# ------------------------------------------------------------------------------
def main():
    actualizar_datos_girona()
    actualizar_datos_elche()
    ejecutar_limpieza()
    enriquecer_con_temperatura()
    entrenar_modelos()
    generar_predicciones()
    sugerir_fecha_evento()
    print("✅ Pipeline ejecutado correctamente.")

if __name__ == "__main__":
    main()
