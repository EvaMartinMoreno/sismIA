# ========== 1. Scraping Web Athletiks ==========
import json
import pandas as pd
import joblib
import os
from pathlib import Path
from cleaning.limpieza_eventos_athletiks import generar_dataset_modelo
from scraping.scraper_athletiks import scrappear_eventos
from pathlib import Path
from datetime import timedelta
from selenium import webdriver
from dotenv import load_dotenv

load_dotenv()
USUARIO_GIRONA = os.getenv("USUARIO_GIRONA")
PASSWORD_GIRONA = os.getenv("PASSWORD_GIRONA")
USUARIO_ELCHE = os.getenv("USUARIO_ELCHE")
PASSWORD_ELCHE = os.getenv("PASSWORD_ELCHE")
ESTADO_PATH = Path("data/raw/athletiks/estado_scraping.json")

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

# ========== 2. Limpieza y generación del dataset modelo ==========
def ejecutar_limpieza():

    input_path = Path("data/clean/eventos_crudos_unificados.csv")
    output_path = Path("data/clean/dataset_modelo.csv")
    tipos_path = Path("data/entrada/tipos_evento.csv")

    generar_dataset_modelo(input_path, output_path, tipos_path)

    # 🚨 Verificar si hay eventos sin categorizar
    df = pd.read_csv(output_path)
    eventos_sin_tipo = df[df["TIPO_ACTIVIDAD"] == "otro"]["NOMBRE_EVENTO"].unique()

    if len(eventos_sin_tipo) > 0:
        print(f"⚠️ Hay {len(eventos_sin_tipo)} eventos sin categorizar.")
        print("📝 Rellena el archivo 'data/entrada/tipos_evento.csv' para continuar.")
        df[["NOMBRE_EVENTO", "FECHA_EVENTO"]].to_csv("data/entrada/eventos_sin_tipo.csv", index=False)
        raise Exception("⛔ STOP: Hay eventos sin categorizar. Corrige antes de seguir.")
    else:
        print("✅ Todos los eventos están correctamente categorizados.")


# ========== 3. Generación de datos simulados ==========
def generar_predicciones():

    # === 📍 Rutas
    PATH_SIM = Path("stats/datasets/simulacion_datos_girona.csv")
    OUTPUT_ASISTENCIA = Path("stats/datasets/Girona_prediccion_asistentes_futuros.csv")
    OUTPUT_BENEFICIO = Path("stats/datasets/Girona_prediccion_beneficio_eventos_futuros.csv")
    MODEL_ASISTENCIA = Path("src/models/modelo_asistencias_Girona.pkl")
    MODEL_BENEFICIO = Path("src/models/modelo_beneficio_Girona.pkl")

    # === ✅ Verificar existencia de modelos
    if not MODEL_ASISTENCIA.exists():
        raise FileNotFoundError(f"⛔ Falta el modelo de asistencia: {MODEL_ASISTENCIA.resolve()}")
    if not MODEL_BENEFICIO.exists():
        raise FileNotFoundError(f"⛔ Falta el modelo de beneficio: {MODEL_BENEFICIO.resolve()}")

    # === 📥 Cargar datos simulados futuros
    df_sim = pd.read_csv(PATH_SIM, parse_dates=["FECHA_EVENTO"])
    hoy = pd.Timestamp.today().normalize()
    df_futuro = df_sim[(df_sim["TIPO_EVENTO"] == "pago") & (df_sim["FECHA_EVENTO"] >= hoy)].copy()

    if df_futuro.empty:
        print("⚠️ No hay eventos futuros para predecir.")
        return

    # === 🔮 Predicción Asistencia
    print("▶️ Prediciendo asistencia futura...")
    modelo_asistencia = joblib.load(MODEL_ASISTENCIA)
    features_asist = ["MES", "DIA_SEMANA_NUM", "DIA_MES", "SEMANA_MES", "TEMPORADA",
                      "COSTE_UNITARIO", "PRECIO_MEDIO", "COLABORACION", "TIPO_ACTIVIDAD"]

    X_asist = pd.get_dummies(df_futuro[features_asist], columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)
    X_asist = X_asist.reindex(columns=modelo_asistencia.feature_names_in_, fill_value=0)

    df_futuro["ASISTENCIA_PREVISTA"] = modelo_asistencia.predict(X_asist).round().astype(int)

    # === 💾 Guardar predicciones de asistencia
    df_futuro.to_csv(OUTPUT_ASISTENCIA, index=False)
    print(f"✅ Predicción asistencia guardada en: {OUTPUT_ASISTENCIA.resolve()}")

    # === 🔮 Predicción Beneficio
    print("▶️ Prediciendo beneficio futuro...")
    modelo_beneficio = joblib.load(MODEL_BENEFICIO)
    features_benef = ["ASISTENCIA_PREVISTA", "COSTE_UNITARIO", "PRECIO_MEDIO",
                      "MES", "DIA_SEMANA_NUM", "DIA_MES", "SEMANA_MES",
                      "TEMPORADA", "COLABORACION", "TIPO_ACTIVIDAD"]

    X_benef = pd.get_dummies(df_futuro[features_benef], columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)
    X_benef = X_benef.reindex(columns=modelo_beneficio.feature_names_in_, fill_value=0)

    df_futuro["BENEFICIO_PREDICHO"] = modelo_beneficio.predict(X_benef).round(2)

    # === 💾 Guardar predicciones finales (app las consume aquí)
    columnas_finales = [
        "NOMBRE_EVENTO", "FECHA_EVENTO", "COMUNIDAD", "TIPO_EVENTO", "TIPO_ACTIVIDAD",
        "COSTE_UNITARIO", "PRECIO_MEDIO", "COLABORACION",
        "ASISTENCIA_PREVISTA", "BENEFICIO_PREDICHO"
    ]
    df_futuro[columnas_finales].to_csv(OUTPUT_BENEFICIO, index=False)
    print(f"✅ Predicción beneficio guardada en: {OUTPUT_BENEFICIO.resolve()}")

# ============= 4. Sugerencia de próximas fechas de eventos ==========
def sugerir_fecha_evento():

    PATH_EVENTOS = Path("data/clean/dataset_modelo.csv")
    PATH_FECHA_SUGERIDA = Path("stats/datasets/proxima_fecha_sugerida.csv")

    def sugerir_proxima_fecha(ultima_fecha, fechas_existentes, dias_entre_eventos=30):
        fecha = ultima_fecha + timedelta(days=dias_entre_eventos)
        while fecha.weekday() != 6:  # 6 = Domingo
            fecha += timedelta(days=1)
        fechas_existentes_set = set([f.date() for f in fechas_existentes])
        while fecha.date() in fechas_existentes_set:
            fecha += timedelta(weeks=1)
        return fecha

    # === 📥 Cargar eventos reales (solo pagos de Girona)
    df = pd.read_csv(PATH_EVENTOS, parse_dates=["FECHA_EVENTO"])
    df = df[(df["COMUNIDAD"].str.upper() == "GIRONA") & (df["TIPO_EVENTO"] == "pago")]

    if df.empty:
        print("⚠️ No hay eventos suficientes para sugerir una fecha.")
        return

    fechas = df["FECHA_EVENTO"].sort_values().tolist()
    ultima_fecha = fechas[-1]
    sugerida = sugerir_proxima_fecha(ultima_fecha, fechas)

    # === 💾 Guardar resultado
    Path(PATH_FECHA_SUGERIDA.parent).mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{"FECHA_SUGERIDA": sugerida}]).to_csv(PATH_FECHA_SUGERIDA, index=False)

# ========== 5. Pipeline principal ==========
def main():
    actualizar_datos_girona()
    actualizar_datos_elche()
    ejecutar_limpieza()
    generar_predicciones()
    sugerir_fecha_evento()

if __name__ == "__main__":
    main()