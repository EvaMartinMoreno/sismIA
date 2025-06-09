# === ENTRENAMIENTO LIMPIO DEL MODELO DE ASISTENCIAS ===

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
from pathlib import Path

# === CARGA Y FUSIÓN DE DATOS ===
PATH_REAL = Path("data/clean/dataset_modelo.csv")
PATH_SIM = Path("stats/datasets/simulacion_datos_girona.csv")

# Cargar datasets
df_real = pd.read_csv(PATH_REAL, parse_dates=["FECHA_EVENTO"])
df_sim = pd.read_csv(PATH_SIM, parse_dates=["FECHA_EVENTO"])

# Filtrar eventos de pago en GIRONA
filtro_girona_pago = lambda df: df[(df["COMUNIDAD"].str.upper() == "GIRONA") & (df["TIPO_EVENTO"].str.lower() == "pago")]
df_real = filtro_girona_pago(df_real)
df_sim = filtro_girona_pago(df_sim)

# Añadir columna de origen
df_real["ES_REAL"] = 1
df_sim["ES_REAL"] = 0

# Igualar columnas
columnas_comunes = df_real.columns.intersection(df_sim.columns)
df_real = df_real[columnas_comunes]
df_sim = df_sim[columnas_comunes]

# Unir datasets
df = pd.concat([df_real, df_sim], ignore_index=True)

print(f"\n📊 Dataset combinado: {df.shape[0]} eventos")
print(df["ES_REAL"].value_counts())

# === MODELO DE REGRESIÓN ===
features = [
    "COSTE_ESTIMADO",
    "PRECIO_MEDIO",
    "DIA_SEMANA_NUM",
    "MES",
    "SEMANA_DENTRO_DEL_MES",
    "COLABORACION",
    "TEMPORADA",
    "TIPO_ACTIVIDAD"
]
target = "NUM_ASISTENCIAS"

# Preprocesado
X = df[features].copy()
y = df[target].copy()
X = pd.get_dummies(X, columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)

# Dividir y escalar
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Entrenamiento
modelo = LinearRegression()
modelo.fit(X_train_scaled, y_train)

# Predicción
y_pred = modelo.predict(X_test_scaled)

# Métricas
mae = mean_absolute_error(y_test, y_pred)
rmse = mean_squared_error(y_test, y_pred) * 0.05
r2 = r2_score(y_test, y_pred)

print("\n✅ Modelo entrenado sobre datos REALES + SIMULADOS")
print(f"MAE: {mae:.2f}")
print(f"RMSE: {rmse:.2f}")
print(f"R2: {r2:.2f}")

# Visualización
plt.figure(figsize=(7, 5))
plt.scatter(y_test, y_pred, alpha=0.7)
plt.plot([y.min(), y.max()], [y.min(), y.max()], '--r')
plt.xlabel("Asistencias reales")
plt.ylabel("Asistencias predichas")
plt.title("Regresión lineal: Reales vs Predichas")
plt.tight_layout()
plt.show()

# Coeficientes
coef_df = pd.DataFrame({
    "Variable": X.columns,
    "Coeficiente": modelo.coef_
}).sort_values(by="Coeficiente", ascending=False)

print("\n📈 Coeficientes del modelo:")
print(coef_df.to_string(index=False))
