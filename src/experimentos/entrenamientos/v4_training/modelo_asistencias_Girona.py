import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt

# === CARGAR DATOS ===
df = pd.read_csv("stats/datasets/simulacion_datos_girona.csv", parse_dates=["FECHA_EVENTO"])

# === LIMPIEZA BÁSICA ===
df["COMUNIDAD"] = df["COMUNIDAD"].str.upper().str.strip()
df["TIPO_EVENTO"] = df["TIPO_EVENTO"].str.lower().str.strip()

# === FILTRO: GIRONA + EVENTOS DE PAGO (REALOIDES Y SIMULADOS) ===
df = df[(df["COMUNIDAD"] == "GIRONA") & (df["TIPO_EVENTO"] == "pago")]

# === DEFINIR VARIABLES ===
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

# === PREPROCESADO ===
df_model = df[features + [target]].copy()
df_model = pd.get_dummies(df_model, columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)

X = df_model.drop(columns=[target])
y = df_model[target]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# === ENTRENAMIENTO ===
modelo = LinearRegression()
modelo.fit(X_train_scaled, y_train)

# === PREDICCIÓN Y MÉTRICAS ===
y_pred = modelo.predict(X_test_scaled)

mae = mean_absolute_error(y_test, y_pred)
rmse = mean_squared_error(y_test, y_pred) ** 0.5
r2 = r2_score(y_test, y_pred)   

print("\n✅ Modelo con datos reales + simulados")
print(f"MAE: {mae:.2f}")
print(f"RMSE: {rmse:.2f}")
print(f"R2: {r2:.2f}")

# === VISUALIZACIÓN ===
plt.figure(figsize=(7, 5))
plt.scatter(y_test, y_pred, alpha=0.7)
plt.plot([y.min(), y.max()], [y.min(), y.max()], '--r')
plt.xlabel("Asistencias reales")
plt.ylabel("Asistencias predichas")
plt.title("Regresión lineal: Reales vs Predichas (datos mixtos)")
plt.tight_layout()
plt.show()
