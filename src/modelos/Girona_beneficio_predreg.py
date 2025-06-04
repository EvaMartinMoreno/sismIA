import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from pathlib import Path

# === 📥 Cargar datasets
path_real = Path("data/clean/dataset_modelo.csv")
path_sim = Path("stats/datasets/simulacion_datos_girona.csv")

# === Leer archivos
df_real = pd.read_csv(path_real, parse_dates=["FECHA_EVENTO"])
df_sim = pd.read_csv(path_sim, parse_dates=["FECHA_EVENTO"])

# === Filtrar solo Girona y eventos de pago
real = df_real[(df_real["COMUNIDAD"].str.upper() == "GIRONA") & (df_real["TIPO_EVENTO"] == "pago")].copy()
sim = df_sim[(df_sim["COMUNIDAD"].str.upper() == "GIRONA") & (df_sim["TIPO_EVENTO"] == "pago")].copy()

# === Quitar duplicados por fecha en simulación
fechas_reales = real["FECHA_EVENTO"].dt.normalize()
sim = sim[~sim["FECHA_EVENTO"].dt.normalize().isin(fechas_reales)]

# === Unir real + simulado
full = pd.concat([real, sim], ignore_index=True)

# === Objetivo: predecir beneficio
X = full[[
    "NUM_ASISTENCIAS", "COSTE_UNITARIO", "PRECIO_MEDIO",
    "MES", "DIA_SEMANA_NUM", "DIA_MES", "SEMANA_MES",
    "TEMPORADA", "COLABORACION", "TIPO_ACTIVIDAD"
]].copy()

X = pd.get_dummies(X, columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)
y = full["BENEFICIO_ESTIMADO"]

# === Entrenamiento modelo
modelo = LinearRegression()
modelo.fit(X, y)
y_pred = modelo.predict(X)

# === Evaluación
mae = mean_absolute_error(y, y_pred)
rmse = np.sqrt(mean_squared_error(y, y_pred))
r2 = r2_score(y, y_pred)

print("\n✅ Modelo de regresión entrenado para predecir el BENEFICIO en Girona")
print(f"📊 MAE: {mae:.2f}")
print(f"📊 RMSE: {rmse:.2f}")
print(f"📊 R²: {r2:.2f}")

# === Guardar modelo
output_path = Path("src/models/modelo_beneficio_girona.pkl")
joblib.dump(modelo, output_path)
print(f"💾 Modelo guardado en: {output_path.resolve()}")

# === Visualizaciones
sns.set(style="whitegrid")
plt.figure(figsize=(12, 5))

# --- Real vs Predicción
plt.subplot(1, 2, 1)
sns.scatterplot(x=y, y=y_pred)
plt.plot([y.min(), y.max()], [y.min(), y.max()], '--', color='gray')
plt.xlabel("Beneficio real")
plt.ylabel("Beneficio predicho")
plt.title("Beneficio real vs. predicho")

# --- Errores residuales
plt.subplot(1, 2, 2)
residuals = y - y_pred
sns.histplot(residuals, kde=True)
plt.title("Distribución de errores residuales")
plt.xlabel("Error")

plt.tight_layout()
plt.show()
