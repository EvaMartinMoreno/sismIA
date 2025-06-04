import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np
import os

# === CARGA DEL DATASET ===
df = pd.read_csv("stats/dataset_modelo_clusterizado.csv", parse_dates=["FECHA_EVENTO"])

# === DEFINIR VARIABLES ===
features = [
    "COSTE_ESTIMADO", "SEMANA", "DIA_SEMANA", "MES", "TIPO_EVENTO", 
    "COMUNIDAD", "CLUSTER_EVENTO"
]
target = "NUM_ASISTENCIAS"

# === DUMMIES Y TRANSFORMACIÓN ===
df_model = df[features + [target]].copy()
df_model = pd.get_dummies(df_model, columns=["DIA_SEMANA", "MES", "TIPO_EVENTO", "COMUNIDAD"], drop_first=True)

X = df_model.drop(columns=[target])
y = df_model[target]

# === CARGAR MODELOS ENTRENADOS ===
modelo_lr = joblib.load("modelos/modelo_regresion_lineal.pkl")
modelo_rf = joblib.load("modelos/modelo_random_forest.pkl")

# === PREDICCIONES ===
y_pred_lr = modelo_lr.predict(X)
y_pred_rf = modelo_rf.predict(X)

# === MÉTRICAS ===
def calcular_metricas(nombre, y_real, y_pred):
    return {
        "Modelo": nombre,
        "MAE": mean_absolute_error(y_real, y_pred),
        "RMSE": mean_squared_error(y_real, y_pred, squared=False),
        "R2": r2_score(y_real, y_pred)
    }

resultados = [
    calcular_metricas("Regresión Lineal", y, y_pred_lr),
    calcular_metricas("Random Forest", y, y_pred_rf)
]
df_resultados = pd.DataFrame(resultados)

# === MOSTRAR MÉTRICAS ===
print("\n📊 Comparativa de Modelos:")
print(df_resultados)

# === GRAFICAR ===
plt.figure(figsize=(8, 5))
plt.bar(df_resultados["Modelo"], df_resultados["R2"], color=["skyblue", "orange"])
plt.title("📊 Comparativa de R² entre modelos")
plt.ylabel("R²")
plt.ylim(0, 1)
for i, r2 in enumerate(df_resultados["R2"]):
    plt.text(i, r2 + 0.02, f"{r2:.2f}", ha="center")
plt.tight_layout()
plt.show()
