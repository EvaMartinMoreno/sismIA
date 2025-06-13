# 📦 Librerías
import pandas as pd
import joblib
from pathlib import Path
from datetime import date, timedelta
import random

# 📁 Rutas
PATH_REALES = Path("data/clean/dataset_modelo.csv")
OUTPUT_PATH = Path("data/predicciones/simulaciones_futuras.csv")
MODEL_PATH_ASIST = Path("src/modelos/modelo_asistencias_girona.pkl")
MODEL_PATH_BENEF = Path("src/modelos/modelo_beneficio_girona.pkl")

def generar_fecha_evento(prob_dias, prob_semanas, fecha_inicio):
    for _ in range(10):  # intentar varias combinaciones
        mes = random.randint(1, 12)
        año = fecha_inicio.year + 1 if mes < fecha_inicio.month else fecha_inicio.year
        dia_semana = random.choices(list(prob_dias.keys()), weights=prob_dias.values())[0]
        semana_mes = random.choices(list(prob_semanas.keys()), weights=prob_semanas.values())[0]
        base_dia = (semana_mes - 1) * 7 + 1

        for offset in range(7):
            dia_candidato = base_dia + offset
            try:
                fecha = date(año, mes, dia_candidato)
                if fecha.weekday() == dia_semana and fecha > fecha_inicio:
                    return fecha
            except:
                continue
    return fecha_inicio + timedelta(days=30)  # fallback

def predecir_eventos_girona():
    # === Cargar dataset real
    df_real = pd.read_csv(PATH_REALES)
    df_real["FECHA_EVENTO"] = pd.to_datetime(df_real["FECHA_EVENTO"], errors="coerce")
    df_real = df_real[df_real["TIPO_EVENTO"] == "pago"]
    df_real = df_real[df_real["TIPO_ACTIVIDAD"].str.lower().str.strip() != "only run"]

    # === Probabilidades reales de fechas
    df_real["DIA_SEMANA_NUM"] = df_real["FECHA_EVENTO"].dt.weekday
    df_real["SEMANA_DENTRO_DEL_MES"] = (df_real["FECHA_EVENTO"].dt.day - 1) // 7 + 1
    prob_dias = df_real["DIA_SEMANA_NUM"].value_counts(normalize=True).to_dict()
    prob_semanas = df_real["SEMANA_DENTRO_DEL_MES"].value_counts(normalize=True).to_dict()

    # === Punto de partida de fechas
    fecha_inicio = df_real["FECHA_EVENTO"].max().date()

    # === Valores promedio y top categorías
    promedio_coste = df_real["COSTE_ESTIMADO"].mean()
    promedio_precio = df_real["PRECIO_MEDIO"].mean()
    promedio_temp = df_real["TEMPERATURA"].mean()
    top_tipos = df_real["TIPO_ACTIVIDAD"].value_counts().head(3).index.tolist()
    top_colab = df_real["COLABORACION"].value_counts().head(2).index.tolist()
    top_temp = df_real["TEMPORADA"].value_counts().head(3).index.tolist()

    # === Generar eventos futuros
    eventos_futuros = []
    for _ in range(6):
        fecha = generar_fecha_evento(prob_dias, prob_semanas, fecha_inicio)
        evento = {
            "FECHA_EVENTO": fecha,
            "COSTE_ESTIMADO": promedio_coste,
            "PRECIO_MEDIO": promedio_precio,
            "DIA_SEMANA_NUM": fecha.weekday(),
            "MES": fecha.month,
            "DIA_MES": fecha.day,
            "SEMANA_DENTRO_DEL_MES": (fecha.day - 1) // 7 + 1,
            "COLABORACION": random.choice(top_colab),
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
    df["ASISTENCIAS_PREDICHAS"] = modelo_asist.predict(df_asist)

    # === Predicción de beneficio
    modelo_benef, cols_benef = joblib.load(MODEL_PATH_BENEF)
    df["NUM_ASISTENCIAS"] = df["ASISTENCIAS_PREDICHAS"]
    df_benef = pd.get_dummies(df, columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)
    for col in cols_benef:
        if col not in df_benef.columns:
            df_benef[col] = 0
    df_benef = df_benef.reindex(columns=cols_benef, fill_value=0)
    df["BENEFICIO_ESTIMADO"] = modelo_benef.predict(df_benef).round(2)

    # === Guardar CSV final
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Simulaciones futuras guardadas con beneficio en: {OUTPUT_PATH.resolve()}")

if __name__ == "__main__":
    predecir_eventos_girona()
