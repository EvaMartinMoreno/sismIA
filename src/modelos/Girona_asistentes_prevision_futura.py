import pandas as pd
import joblib
from pathlib import Path

# === 📥 Cargar modelo y simulación
modelo = joblib.load("src/models/modelo_lineal_unificado_girona.pkl")
df_sim = pd.read_csv("stats/datasets/simulacion_datos_girona.csv", parse_dates=["FECHA_EVENTO"])

# === 🧽 Filtrar eventos simulados futuros (por ejemplo a partir de hoy)
hoy = pd.Timestamp.today().normalize()
df_futuro = df_sim[(df_sim["TIPO_EVENTO"] == "pago") & (df_sim["FECHA_EVENTO"] >= hoy)].copy()

# === 🔢 Features y encoding
features = ["MES", "DIA_SEMANA_NUM", "DIA_MES", "SEMANA_MES", "TEMPORADA", 
            "COSTE_UNITARIO", "PRECIO_MEDIO", "COLABORACION", "TIPO_ACTIVIDAD"]

X_futuro = pd.get_dummies(df_futuro[features], columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)

# Alinear columnas con las del modelo original
X_train_columns = modelo.feature_names_in_
X_futuro = X_futuro.reindex(columns=X_train_columns, fill_value=0)

# === 🔮 Predicción
df_futuro["PREDICCION_ASISTENCIA"] = modelo.predict(X_futuro)

# === 💾 Exportar resultados
df_futuro[["FECHA_EVENTO", "NOMBRE_EVENTO", "PREDICCION_ASISTENCIA"]].to_csv("stats//datasets/Girona_prediccion_asistentes_futuros.csv", index=False)
print("✅ Predicciones guardadas en stats//datasets/Girona_prediccion_asistentes_futuros.csv")
