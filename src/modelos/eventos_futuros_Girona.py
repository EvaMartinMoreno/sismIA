# 📦 Librerías
import pandas as pd
import joblib
import numpy as np
from pathlib import Path
from datetime import date, timedelta
from sklearn.preprocessing import StandardScaler
import random

# 📁 Rutas
PATH_REALES = Path("data/raw/dataset_modelo_validado.csv")
PATH_SIM = Path("data/raw/simulacion_datos_girona.csv")
OUTPUT_PATH = Path("data/predicciones/simulaciones_futuras.csv")
MODEL_PATH_ASIST = Path("src/modelos/modelo_asistencias_girona.pkl")
MODEL_PATH_BENEF = Path("src/modelos/modelo_beneficio_girona.pkl")

def generar_fecha_evento(prob_dias, prob_semanas):
    hoy = date.today()
    mes_siguiente = hoy.month + 1 if hoy.month < 12 else 1
    año = hoy.year if mes_siguiente != 1 else hoy.year + 1

    for _ in range(10):
        dia_semana = random.choices(list(prob_dias.keys()), weights=prob_dias.values())[0]
        semana_mes = random.choices(list(prob_semanas.keys()), weights=prob_semanas.values())[0]
        base_dia = (semana_mes - 1) * 7 + 1
        for offset in range(7):
            dia_candidato = base_dia + offset
            try:
                fecha = date(año, mes_siguiente, dia_candidato)
                if fecha.weekday() == dia_semana:
                    return fecha
            except:
                continue
    return date(año, mes_siguiente, 15)

def predecir_eventos_girona():
    # === Cargar datasets reales + simulados
    df_real = pd.read_csv(PATH_REALES)
    df_sim = pd.read_csv(PATH_SIM)

    df_real = df_real[df_real["TIPO_EVENTO"] == "pago"]
    df_sim = df_sim[df_sim["TIPO_EVENTO"] == "pago"]
    df_total = pd.concat([df_real, df_sim], ignore_index=True)

    df_total["FECHA_EVENTO"] = pd.to_datetime(df_total["FECHA_EVENTO"], errors="coerce")
    df_total["TIPO_ACTIVIDAD"] = df_total["TIPO_ACTIVIDAD"].astype(str)
    df_total = df_total[df_total["TIPO_ACTIVIDAD"].str.lower().str.strip() != "only run"]

    if df_total.empty:
        print("⛔ No hay datos suficientes para generar eventos futuros.")
        return

    # === Probabilidades para fechas futuras
    df_total["DIA_SEMANA_NUM"] = df_total["FECHA_EVENTO"].dt.weekday
    df_total["SEMANA_DENTRO_DEL_MES"] = (df_total["FECHA_EVENTO"].dt.day - 1) // 7 + 1
    prob_dias = df_total["DIA_SEMANA_NUM"].value_counts(normalize=True).to_dict()
    prob_semanas = df_total["SEMANA_DENTRO_DEL_MES"].value_counts(normalize=True).to_dict()
    fecha_inicio = df_total["FECHA_EVENTO"].max().date()

    # === Promedios y distribuciones
    df_total["COSTE_UNITARIO"] = pd.to_numeric(df_total["COSTE_UNITARIO"], errors="coerce")
    df_total["NUM_INSCRITAS"] = pd.to_numeric(df_total["NUM_INSCRITAS"], errors="coerce")
    promedio_coste = (df_total["COSTE_UNITARIO"] * df_total["NUM_INSCRITAS"]).dropna().mean()
    promedio_precio = df_total["PRECIO_MEDIO"].dropna().mean()
    promedio_temp = df_total["TEMPERATURA"].dropna().mean()

    top_tipos = df_total["TIPO_ACTIVIDAD"].dropna().value_counts().head(3).index.tolist() or ["ludico"]
    top_temp = df_total["TEMPORADA"].dropna().value_counts().head(3).index.tolist() or ["primavera"]
    p_colab = df_total["COLABORACION"].mean() if "COLABORACION" in df_total.columns else 0.5

    # === Generar nuevos eventos simulados
    eventos_futuros = []
    for _ in range(6):
        fecha = generar_fecha_evento(prob_dias, prob_semanas)
        evento = {
            "FECHA_EVENTO": fecha,
            "COSTE_ESTIMADO": promedio_coste,
            "PRECIO_MEDIO": promedio_precio,
            "DIA_SEMANA_NUM": fecha.weekday(),
            "MES": fecha.month,
            "DIA_MES": fecha.day,
            "SEMANA_DENTRO_DEL_MES": (fecha.day - 1) // 7 + 1,
            "COLABORACION": int(random.random() < p_colab),
            "TEMPORADA": random.choice(top_temp),
            "TIPO_ACTIVIDAD": random.choice(top_tipos),
            "TEMPERATURA": promedio_temp,
            "TIPO_EVENTO": "pago"
        }
        eventos_futuros.append(evento)

    df = pd.DataFrame(eventos_futuros)
    df["TIPO_ACTIVIDAD"] = df["TIPO_ACTIVIDAD"].str.strip().str.lower().replace({"ludica": "ludico"})

    # === Predicción de asistentes
    modelo_asist, cols_asist = joblib.load(MODEL_PATH_ASIST)
    df_asist = pd.get_dummies(df, columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)
    for col in cols_asist:
        if col not in df_asist.columns:
            df_asist[col] = 0
    df_asist = df_asist.reindex(columns=cols_asist, fill_value=0)
    df_asist = df_asist.dropna()
    df = df.loc[df_asist.index]

    scaler_asist = StandardScaler()
    df_asist_scaled = scaler_asist.fit_transform(df_asist)

    if df_asist.empty:
        print("❌ No se han podido generar eventos futuros válidos para predecir asistencias.")
        return

    df["ASISTENCIAS_PREDICHAS"] = np.maximum(0, modelo_asist.predict(df_asist_scaled).round())
    df["NUM_ASISTENCIAS"] = df["ASISTENCIAS_PREDICHAS"]

    # === Predicción de beneficio
    modelo_benef, cols_benef = joblib.load(MODEL_PATH_BENEF)
    df_benef = pd.get_dummies(df, columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)
    for col in cols_benef:
        if col not in df_benef.columns:
            df_benef[col] = 0
    df_benef = df_benef.reindex(columns=cols_benef, fill_value=0)
    df_benef = df_benef.dropna()
    df = df.loc[df_benef.index]

    if df_benef.empty:
        print("❌ No se han podido calcular beneficios simulados válidos.")
        return

    df["BENEFICIO_ESTIMADO"] = modelo_benef.predict(df_benef).round(2)

    # === Guardar
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Simulaciones futuras guardadas con beneficio en: {OUTPUT_PATH.resolve()}")

if __name__ == "__main__":
    predecir_eventos_girona()
