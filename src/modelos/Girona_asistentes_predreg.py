import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

# === 📥 Cargar datasets
path_modelo = Path("data/clean/dataset_modelo.csv")
path_simulado = Path("stats/datasets/simulacion_datos_girona.csv")

df_real = pd.read_csv(path_modelo, parse_dates=["FECHA_EVENTO"])
df_sim = pd.read_csv(path_simulado, parse_dates=["FECHA_EVENTO"])

# === 🧽 Filtro
df_real = df_real[(df_real["COMUNIDAD"].str.upper() == "GIRONA") & (df_real["TIPO_EVENTO"] == "pago")]
df_sim = df_sim[(df_sim["COMUNIDAD"].str.upper() == "GIRONA") & (df_sim["TIPO_EVENTO"] == "pago")]

# === 📆 Unificar
fechas_reales = df_real["FECHA_EVENTO"].dt.normalize()
df_sim = df_sim[~df_sim["FECHA_EVENTO"].dt.normalize().isin(fechas_reales)]
df_total = pd.concat([df_real, df_sim], ignore_index=True)

# === 🔢 Selección de variables
features = ["MES", "DIA_SEMANA_NUM", "DIA_MES", "SEMANA_MES", "TEMPORADA","COSTE_UNITARIO","PRECIO_MEDIO", "COLABORACION", "TIPO_ACTIVIDAD"]
X = df_total[features].copy()
X = pd.get_dummies(X, columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)
y = df_total["NUM_ASISTENCIAS"]

# === 💡 Entrenamiento
modelo = LinearRegression()
modelo.fit(X, y)
y_pred = modelo.predict(X)

# === 📏 Métricas
mae = mean_absolute_error(y, y_pred)
rmse = np.sqrt(mean_squared_error(y, y_pred))
r2 = r2_score(y, y_pred)

print("✅ Modelo entrenado con datos reales + simulados (sin duplicar fechas).")
print(f"📊 MAE: {mae:.2f}")
print(f"📊 RMSE: {rmse:.2f}")
print(f"📊 R²: {r2:.2f}")

# === 💾 Guardar modelo
modelo_path = Path("src/models/modelo_lineal_unificado_girona.pkl")
joblib.dump(modelo, modelo_path)
print(f"💾 Modelo guardado en: {modelo_path.resolve()}")

# === 📈 Visualización
plt.figure(figsize=(12, 5))

# --- 1. Comparación real vs predicción
plt.subplot(1, 2, 1)
sns.scatterplot(x=y, y=y_pred, alpha=0.7)
plt.plot([y.min(), y.max()], [y.min(), y.max()], '--', color='gray')
plt.xlabel("Real")
plt.ylabel("Predicción")
plt.title("Real vs Predicción")

# --- 2. Errores residuales
plt.subplot(1, 2, 2)
residuals = y - y_pred
sns.histplot(residuals, kde=True)
plt.title("Distribución de errores residuales")
plt.xlabel("Error (real - predicción)")

plt.tight_layout()
plt.show()

# === 📎 Mostrar coeficientes
coeficientes = pd.Series(modelo.coef_, index=X.columns).sort_values(ascending=False)
print("\n📌 Pesos de cada variable en la regresión:")
print(coeficientes)

# Visual opcional
plt.figure(figsize=(10, 6))
coeficientes.plot(kind="barh")
plt.title("📉 Peso de cada variable en la predicción de asistencia")
plt.xlabel("Impacto en asistentes")
plt.tight_layout()
plt.show()
