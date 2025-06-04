import pandas as pd
import joblib
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# === Cargar modelo de Girona
modelo = joblib.load("src/models/modelo_lineal_unificado_girona.pkl")

# === Cargar dataset real y filtrar ELCHE
df = pd.read_csv("data/clean/dataset_modelo.csv", parse_dates=["FECHA_EVENTO"])
df_elche = df[(df["COMUNIDAD"].str.upper() == "ELCHE") & (df["TIPO_EVENTO"] == "pago")].copy()

# === Preparar features
features = ["MES", "DIA_SEMANA_NUM", "DIA_MES", "SEMANA_MES", "TEMPORADA",
            "COSTE_UNITARIO", "PRECIO_MEDIO", "COLABORACION", "TIPO_ACTIVIDAD"]

X = pd.get_dummies(df_elche[features], columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)
X = X.reindex(columns=modelo.feature_names_in_, fill_value=0)

# === Predicción
y_real = df_elche["NUM_ASISTENCIAS"]
y_pred = modelo.predict(X)

# === Métricas
mae = mean_absolute_error(y_real, y_pred)
rmse = np.sqrt(mean_squared_error(y_real, y_pred))
r2 = r2_score(y_real, y_pred)

print("📍 Evaluación del modelo de Girona sobre eventos reales de Elche:")
print(f"🔸 MAE: {mae:.2f}")
print(f"🔸 RMSE: {rmse:.2f}")
print(f"🔸 R²: {r2:.2f}")

# === Visualizaciones
plt.figure(figsize=(12, 5))

# 1. Real vs Predicción
plt.subplot(1, 2, 1)
sns.scatterplot(x=y_real, y=y_pred)
plt.plot([y_real.min(), y_real.max()], [y_real.min(), y_real.max()], '--', color='gray')
plt.xlabel("Asistencias reales")
plt.ylabel("Predicción")
plt.title("🎯 Real vs Predicción - Elche")

# 2. Errores
plt.subplot(1, 2, 2)
residuos = y_real - y_pred
sns.histplot(residuos, kde=True)
plt.title("📉 Errores residuales (real - predicción)")
plt.xlabel("Error")
plt.tight_layout()
plt.show()
