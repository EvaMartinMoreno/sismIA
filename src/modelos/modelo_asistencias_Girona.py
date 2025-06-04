# 📦 Librerías
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns

# 📁 Rutas
PATH_REAL = Path("data/clean/dataset_modelo.csv")
PATH_SIM = Path("stats/datasets/simulacion_datos_girona.csv")
MODEL_PATH = Path("src/models/prediccion_reglineal_asistencias_girona.pkl")

# 📥 Cargar y limpiar datos
df_real = pd.read_csv(PATH_REAL, parse_dates=["FECHA_EVENTO"])
df_sim = pd.read_csv(PATH_SIM, parse_dates=["FECHA_EVENTO"])

df_real = df_real[(df_real["COMUNIDAD"].str.upper() == "GIRONA") & (df_real["TIPO_EVENTO"] == "pago")]
df_sim = df_sim[(df_sim["COMUNIDAD"].str.upper() == "GIRONA") & (df_sim["TIPO_EVENTO"] == "pago")]

fechas_reales = df_real["FECHA_EVENTO"].dt.normalize()
df_sim = df_sim[~df_sim["FECHA_EVENTO"].dt.normalize().isin(fechas_reales)]

df_total = pd.concat([df_real, df_sim], ignore_index=True)

# 🔢 Features
features = ["MES", "DIA_SEMANA_NUM", "DIA_MES", "SEMANA_MES", "TEMPORADA",
            "COSTE_UNITARIO", "PRECIO_MEDIO", "COLABORACION", "TIPO_ACTIVIDAD"]
X = pd.get_dummies(df_total[features], columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)
y = df_total["NUM_ASISTENCIAS"]

# 🔮 Entrenamiento
modelo = LinearRegression()
modelo.fit(X, y)
joblib.dump(modelo, MODEL_PATH)
print(f"✅ Modelo guardado en: {MODEL_PATH.resolve()}")

# 📊 Evaluación
mae = mean_absolute_error(y, modelo.predict(X))
rmse = np.sqrt(mean_squared_error(y, modelo.predict(X)))
r2 = r2_score(y, modelo.predict(X))

print(f"📊 MAE: {mae:.2f}")
print(f"📊 RMSE: {rmse:.2f}")
print(f"📊 R²: {r2:.2f}")

# 📈 Visualización
# (Gráficos y coeficientes: opcional pero útil)
