import pandas as pd
import numpy as np
import joblib
from pathlib import Path

# === 📥 Cargar modelo entrenado
modelo_path = Path("src/models/modelo_beneficio_girona.pkl")
modelo = joblib.load(modelo_path)

# === 📥 Cargar eventos futuros simulados
df_sim = pd.read_csv("stats/datasets/simulacion_datos_girona.csv", parse_dates=["FECHA_EVENTO"])
hoy = pd.Timestamp.today().normalize()
df_futuro = df_sim[(df_sim["TIPO_EVENTO"] == "pago") & (df_sim["FECHA_EVENTO"] >= hoy)].copy()

# === 🔢 Features necesarios para la predicción
features = [
    "NUM_ASISTENCIAS", "COSTE_UNITARIO", "PRECIO_MEDIO",
    "MES", "DIA_SEMANA_NUM", "DIA_MES", "SEMANA_MES",
    "TEMPORADA", "COLABORACION", "TIPO_ACTIVIDAD"
]

# === Preparar X con las columnas dummy
X = df_futuro[features].copy()
X = pd.get_dummies(X, columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)

# === Alinear columnas del modelo
X = X.reindex(columns=modelo.feature_names_in_, fill_value=0)

# === 🔮 Predicción de beneficio
predicciones = modelo.predict(X)
df_futuro["BENEFICIO_PREDICHO"] = predicciones.round(2)

# === 💾 Guardar resultados
output_path = Path("stats/datasets/Girona_prediccion_beneficio_eventos_futuros.csv")
output_path.parent.mkdir(parents=True, exist_ok=True)
df_futuro.to_csv(output_path, index=False)

print("✅ Predicción de beneficios completada")
print(f"📍 Resultados guardados en: {output_path.resolve()}")
print(df_futuro[["FECHA_EVENTO", "NOMBRE_EVENTO", "NUM_ASISTENCIAS", "BENEFICIO_PREDICHO"]].sort_values("FECHA_EVENTO").head())
