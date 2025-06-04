# 📦 Librerías
import pandas as pd
import joblib
from pathlib import Path

# 📁 Rutas
MODEL_PATH = Path("src/models/modelo_beneficio_girona.pkl")
PATH_SIM = Path("stats/datasets/simulacion_datos_girona.csv")
OUTPUT_PRED = Path("stats/datasets/Girona_prediccion_beneficio_eventos_futuros.csv")

# 📥 Cargar modelo y datos
modelo = joblib.load(MODEL_PATH)
df_sim = pd.read_csv(PATH_SIM, parse_dates=["FECHA_EVENTO"])

# 🧽 Filtrar eventos futuros y de pago
hoy = pd.Timestamp.today().normalize()
df_futuro = df_sim[(df_sim["TIPO_EVENTO"] == "pago") & (df_sim["FECHA_EVENTO"] >= hoy)].copy()

# 🔢 Features
features = [
    "NUM_ASISTENCIAS", "COSTE_UNITARIO", "PRECIO_MEDIO",
    "MES", "DIA_SEMANA_NUM", "DIA_MES", "SEMANA_MES",
    "TEMPORADA", "COLABORACION", "TIPO_ACTIVIDAD"
]
X_futuro = pd.get_dummies(df_futuro[features], columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)
X_futuro = X_futuro.reindex(columns=modelo.feature_names_in_, fill_value=0)

# 🔮 Predicción
df_futuro["BENEFICIO_PREDICHO"] = modelo.predict(X_futuro).round(2)

# 💾 Guardar resultados
OUTPUT_PRED.parent.mkdir(parents=True, exist_ok=True)
df_futuro.to_csv(OUTPUT_PRED, index=False)

print("✅ Predicción de beneficios guardada")
print(df_futuro[["FECHA_EVENTO", "NOMBRE_EVENTO", "NUM_ASISTENCIAS", "BENEFICIO_PREDICHO"]].sort_values("FECHA_EVENTO").head())
