# 📦 Librerías
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# 📁 Rutas
PATH_REAL = Path("data/clean/dataset_modelo.csv")
PATH_SIM = Path("stats/datasets/simulacion_datos_girona.csv")
MODEL_PATH = Path("src/models/modelo_beneficio_girona.pkl")

# 📥 Cargar datos
df_real = pd.read_csv(PATH_REAL, parse_dates=["FECHA_EVENTO"])
df_sim = pd.read_csv(PATH_SIM, parse_dates=["FECHA_EVENTO"])

# 🚨 Validación de costes
if "COSTE_UNITARIO_VALIDADO" not in df_real.columns or not df_real["COSTE_UNITARIO_VALIDADO"].all():
    raise ValueError("⛔ Hay eventos sin COSTE_UNITARIO validado. Revisa antes de entrenar.") 

# 🧽 Filtrar Girona y eventos de pago
df_real = df_real[(df_real["COMUNIDAD"].str.upper() == "GIRONA") & (df_real["TIPO_EVENTO"] == "pago")]
df_sim = df_sim[(df_sim["COMUNIDAD"].str.upper() == "GIRONA") & (df_sim["TIPO_EVENTO"] == "pago")]

# 🚫 Quitar fechas duplicadas
fechas_reales = df_real["FECHA_EVENTO"].dt.normalize()
df_sim = df_sim[~df_sim["FECHA_EVENTO"].dt.normalize().isin(fechas_reales)]

# 🔀 Unir
df_total = pd.concat([df_real, df_sim], ignore_index=True)

# 🔢 Features y target
features = [
    "NUM_ASISTENCIAS", "COSTE_UNITARIO", "PRECIO_MEDIO",
    "MES", "DIA_SEMANA_NUM", "DIA_MES", "SEMANA_MES",
    "TEMPORADA", "COLABORACION", "TIPO_ACTIVIDAD"
]
X = pd.get_dummies(df_total[features], columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)
y = df_total["BENEFICIO_ESTIMADO"]

# 🤖 Entrenamiento
modelo = LinearRegression()
modelo.fit(X, y)
joblib.dump(modelo, MODEL_PATH)
print(f"✅ Modelo guardado en: {MODEL_PATH.resolve()}")

# 📏 Métricas
mae = mean_absolute_error(y, modelo.predict(X))
rmse = np.sqrt(mean_squared_error(y, modelo.predict(X)))
r2 = r2_score(y, modelo.predict(X))

print(f"📊 MAE: {mae:.2f}")
print(f"📊 RMSE: {rmse:.2f}")
print(f"📊 R²: {r2:.2f}")

# 📈 Visualización
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
sns.scatterplot(x=y, y=modelo.predict(X), alpha=0.6)
plt.plot([y.min(), y.max()], [y.min(), y.max()], '--', color='gray')
plt.xlabel("Beneficio real")
plt.ylabel("Beneficio predicho")
plt.title("Real vs. Predicción")

plt.subplot(1, 2, 2)
sns.histplot(y - modelo.predict(X), kde=True)
plt.title("Errores residuales")
plt.xlabel("Error")
plt.tight_layout()
plt.show()
