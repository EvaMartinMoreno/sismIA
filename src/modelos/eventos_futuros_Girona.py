# 📦 Librerías
import pandas as pd
import joblib
from pathlib import Path
from datetime import timedelta, date
from sklearn.preprocessing import StandardScaler
import random

# 📁 Rutas
PATH_REALES = Path("data/clean/dataset_modelo.csv")
OUTPUT_PATH = Path("data/predicciones/predicciones_futuras.csv")
MODEL_PATH = Path("src/modelos/modelo_asistencias_girona.pkl")

def primer_domingo_del_mes(year, month):
    for day in range(1, 8):
        if date(year, month, day).weekday() == 6:  # 6 = domingo
            return date(year, month, day)

def predecir_eventos_girona():
    # === Cargar dataset real
    df_real = pd.read_csv(PATH_REALES)
    df_real["FECHA_EVENTO"] = pd.to_datetime(df_real["FECHA_EVENTO"], errors="coerce")

    # === Filtrar solo eventos de pago
    df_real = df_real[df_real["TIPO_EVENTO"] == "pago"]

    # === Excluir tipo de actividad "only run"
    df_real = df_real[df_real["TIPO_ACTIVIDAD"].str.lower().str.strip() != "only run"]

    # === Detectar última fecha real
    fecha_inicio = df_real["FECHA_EVENTO"].max().date()
    primer_mes = fecha_inicio.month + 1 if fecha_inicio.day > 7 else fecha_inicio.month
    primer_año = fecha_inicio.year

    # === Calcular valores representativos
    promedio_coste = df_real["COSTE_ESTIMADO"].mean()
    promedio_precio = df_real["PRECIO_MEDIO"].mean()
    promedio_temp = df_real["TEMPERATURA"].mean()

    # Muestreo aleatorio entre los más comunes
    top_tipos = df_real["TIPO_ACTIVIDAD"].value_counts().head(3).index.tolist()
    top_colab = df_real["COLABORACION"].value_counts().head(2).index.tolist()
    top_temp = df_real["TEMPORADA"].value_counts().head(3).index.tolist()

    # === Generar eventos futuros (uno al mes)
    eventos_futuros = []
    for i in range(6):
        month = (primer_mes + i - 1) % 12 + 1
        year = primer_año + ((primer_mes + i - 1) // 12)
        fecha = primer_domingo_del_mes(year, month)

        evento = {
            "FECHA_EVENTO": fecha,
            "COSTE_ESTIMADO": promedio_coste,
            "PRECIO_MEDIO": promedio_precio,
            "DIA_SEMANA_NUM": fecha.weekday(),
            "MES": fecha.month,
            "SEMANA_DENTRO_DEL_MES": (fecha.day - 1) // 7 + 1,
            "COLABORACION": random.choice(top_colab),
            "TEMPORADA": random.choice(top_temp),
            "TIPO_ACTIVIDAD": random.choice(top_tipos),
            "TEMPERATURA": promedio_temp,
            "TIPO_EVENTO": "pago"
        }
        eventos_futuros.append(evento)

    df = pd.DataFrame(eventos_futuros)

    # === Normalizar texto
    df["TIPO_ACTIVIDAD"] = df["TIPO_ACTIVIDAD"].str.strip().str.lower()
    df["TIPO_ACTIVIDAD"] = df["TIPO_ACTIVIDAD"].replace({"ludica": "ludico"})

    # === Cargar modelo y columnas esperadas
    modelo, columnas_esperadas = joblib.load(MODEL_PATH)

    # === Validación de NaNs
    features_basicos = [
        "COSTE_ESTIMADO", "PRECIO_MEDIO", "DIA_SEMANA_NUM", "MES",
        "SEMANA_DENTRO_DEL_MES", "COLABORACION", "TEMPORADA", "TIPO_ACTIVIDAD", "TEMPERATURA"
    ]
    df = df.dropna(subset=features_basicos)

    # === Dummies
    df_dummies = pd.get_dummies(df, columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)

    # === Añadir columnas faltantes y reordenar
    for col in columnas_esperadas:
        if col not in df_dummies.columns:
            df_dummies[col] = 0
    df_dummies = df_dummies.reindex(columns=columnas_esperadas, fill_value=0)

    # === Escalado
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df_dummies)

    # === Predicción
    predicciones = modelo.predict(X_scaled)
    df["ASISTENCIAS_PREDICHAS"] = predicciones

    # === Guardado
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"✅ Predicciones futuras guardadas en: {OUTPUT_PATH.resolve()}")

if __name__ == "__main__":
    predecir_eventos_girona()
