# 📦 Librerías
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns

# 📁 Rutas
PATH_REAL = Path("data/clean/dataset_modelo.csv")
PATH_SIM = Path("stats/datasets/simulacion_datos_girona.csv")
MODEL_PATH = Path("src/models/prediccion_reglineal_asistencias_girona.pkl")

# 📥 Cargar y limpiar datos
df_real = pd.read_csv(PATH_REAL, parse_dates=["FECHA_EVENTO"])
df_sim = pd.read_csv(PATH_SIM, parse_dates=["FECHA_EVENTO"])

# Filtrar solo eventos de pago en Girona
df_real = df_real[(df_real["COMUNIDAD"].str.upper() == "GIRONA") & (df_real["TIPO_EVENTO"] == "pago")]
df_sim = df_sim[(df_sim["COMUNIDAD"].str.upper() == "GIRONA") & (df_sim["TIPO_EVENTO"] == "pago")]

# 🚨 Validación de costes solo para los filtrados
if "COSTE_UNITARIO_VALIDADO" not in df_real.columns or not df_real["COSTE_UNITARIO_VALIDADO"].all():
    # Mostrar eventos no validados después del filtro
    eventos_no_validados = df_real[df_real["COSTE_UNITARIO_VALIDADO"] != True]
    print("\n🔍 Eventos de pago en Girona SIN validación de coste:")
    print(eventos_no_validados[["NOMBRE_EVENTO", "FECHA_EVENTO", "COSTE_UNITARIO", "COSTE_UNITARIO_VALIDADO"]])
    print(f"\n❌ Hay {len(eventos_no_validados)} eventos sin validar.")
    raise ValueError("⛔ Hay eventos sin COSTE_UNITARIO validado. Revisa antes de entrenar.")

# 🔢 Features
features = ["MES", "DIA_SEMANA_NUM", "DIA_MES", "SEMANA_MES", "TEMPORADA",
            "COSTE_UNITARIO", "PRECIO_MEDIO", "COLABORACION", "TIPO_ACTIVIDAD"]
X = pd.get_dummies(df_total[features], columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)
y = df_total["NUM_ASISTENCIAS"]

# 🔍 Análisis exploratorio previo al entrenamiento
print("\n📊 Análisis de correlaciones y relevancia de variables...")

# Selección de variables numéricas originales (sin dummies)
variables_interes = [
    "NUM_ASISTENCIAS", "NUM_INSCRITAS", "NUM_PAGOS", "PRECIO_MEDIO",
    "COSTE_UNITARIO", "BENEFICIO_ESTIMADO", "INGRESO_POR_ASISTENTE",
    "DIA_MES", "SEMANA_MES", "MES", "DIA_SEMANA_NUM", "COLABORACION"
]

df_corr = df_total[variables_interes].dropna().copy()

# Correlaciones
plt.figure(figsize=(12, 8))
sns.heatmap(df_corr.corr(), annot=True, cmap="coolwarm", fmt=".2f")
plt.title("🔍 Matriz de correlaciones - Eventos de pago Girona")
plt.tight_layout()
plt.show()

# Importancia con regresión lineal
X_corr = df_corr.drop(columns=["NUM_ASISTENCIAS"])
y_corr = df_corr["NUM_ASISTENCIAS"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_corr)

modelo_exploratorio = LinearRegression()
modelo_exploratorio.fit(X_scaled, y_corr)

importancia = pd.Series(modelo_exploratorio.coef_, index=X_corr.columns).sort_values(ascending=False)
print("\n📈 Importancia de variables (modelo exploratorio):\n")
print(importancia)

# 🔮 Entrenamiento
modelo = LinearRegression()
modelo.fit(X, y)
joblib.dump(modelo, MODEL_PATH)
print(f"\n✅ Modelo guardado en: {MODEL_PATH.resolve()}")

# 📊 Evaluación
mae = mean_absolute_error(y, modelo.predict(X))
rmse = np.sqrt(mean_squared_error(y, modelo.predict(X)))
r2 = r2_score(y, modelo.predict(X))

print(f"📊 MAE: {mae:.2f}")
print(f"📊 RMSE: {rmse:.2f}")
print(f"📊 R²: {r2:.2f}")
