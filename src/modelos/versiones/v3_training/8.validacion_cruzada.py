import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib

from sklearn.model_selection import cross_val_predict, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

# === CARGA DE DATOS ===
df = pd.read_csv("stats/dataset_modelo_clusterizado.csv", parse_dates=["FECHA_EVENTO"])

# === VARIABLES ===
features = [
    "COSTE_ESTIMADO", "SEMANA", "DIA_SEMANA", "MES",
    "TIPO_EVENTO", "COMUNIDAD", "CLUSTER_EVENTO"
]
target = "NUM_ASISTENCIAS"

df_model = df[features + [target]].copy()
df_model = pd.get_dummies(df_model, columns=["DIA_SEMANA", "MES", "TIPO_EVENTO", "COMUNIDAD"], drop_first=True)

X = df_model.drop(columns=[target])
y = df_model[target]

# === MODELOS ===
modelo_lr = LinearRegression()
modelo_rf = RandomForestRegressor(n_estimators=100, random_state=42)

# === VALIDACIÓN CRUZADA ===
cv = KFold(n_splits=5, shuffle=True, random_state=42)

def evaluar_cv(modelo, X, y, nombre):
    y_pred = cross_val_predict(modelo, X, y, cv=cv)
    mae = mean_absolute_error(y, y_pred)
    rmse = mean_squared_error(y, y_pred) ** 0.5  # compatible con versiones antiguas
    r2 = r2_score(y, y_pred)
    print(f"\n📊 Resultados para {nombre}:")
    print(f"MAE  = {mae:.2f}")
    print(f"RMSE = {rmse:.2f}")
    print(f"R²   = {r2:.2f}")
    return {"Modelo": nombre, "MAE": mae, "RMSE": rmse, "R2": r2}

# === EVALUAR LOS MODELOS ===
resultados = [
    evaluar_cv(modelo_lr, X, y, "Regresión Lineal"),
    evaluar_cv(modelo_rf, X, y, "Random Forest")
]

df_resultados = pd.DataFrame(resultados)

# === GRÁFICO DE COMPARACIÓN ===
plt.figure(figsize=(8, 5))
plt.bar(df_resultados["Modelo"], df_resultados["R2"], color=["skyblue", "orange"])
plt.title("📊 R² con Validación Cruzada")
plt.ylabel("R²")
plt.ylim(-2, 1)
for i, r2 in enumerate(df_resultados["R2"]):
    plt.text(i, r2 + 0.05, f"{r2:.2f}", ha="center")
plt.tight_layout()
plt.grid(True)
plt.show()
