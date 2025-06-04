# 📦 Librerías
import pandas as pd
import joblib
from pathlib import Path

# 📁 Rutas
MODEL_PATH = Path("src/models/modelo_lineal_unificado_girona.pkl")
DATA_PATH = Path("stats/datasets/simulacion_datos_girona.csv")
OUTPUT_PRED = Path("stats/datasets/Girona_prediccion_asistentes_futuros.csv")

# 📥 Cargar modelo y datos
modelo = joblib.load(MODEL_PATH)
df_sim = pd.read_csv(DATA_PATH, parse_dates=["FECHA_EVENTO"])

# 📆 Filtrar eventos futuros y de pago
hoy = pd.Timestamp.today().normalize()
df_futuro = df_sim[(df_sim["TIPO_EVENTO"] == "pago") & (df_sim["FECHA_EVENTO"] >= hoy)].copy()

# 🔢 Features
features = ["MES", "DIA_SEMANA_NUM", "DIA_MES", "SEMANA_MES", "TEMPORADA",
            "COSTE_UNITARIO", "PRECIO_MEDIO", "COLABORACION", "TIPO_ACTIVIDAD"]
X = pd.get_dummies(df_futuro[features], columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)
X = X.reindex(columns=modelo.feature_names_in_, fill_value=0)

# 🔮 Predicción
df_futuro["ASISTENCIA_PREVISTA"] = modelo.predict(X)

# 💾 Guardar
df_futuro.to_csv(OUTPUT_PRED, index=False)
print(f"✅ Predicciones guardadas en: {OUTPUT_PRED.resolve()}")
