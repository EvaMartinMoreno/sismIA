import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import matplotlib.pyplot as plt
from pipeline_entrenamiento_v2 import pipeline_dataset

# === CARGA DE DATOS ORIGINALES ===
df_real = pd.read_csv("stats/dataset_modelo.csv", parse_dates=["FECHA_EVENTO"])
df_fake = pd.read_csv("stats/eventos_simulados_girona.csv", parse_dates=["FECHA_EVENTO"])

# === APLICAR PIPELINE Y OBTENER DF LIMPIO ===
df_limpio = pipeline_dataset(df_real, df_fake)

# === FILTRAR SOLO VARIABLES DISPONIBLES ANTES DEL EVENTO ===
y = df_limpio["NUM_ASISTENCIAS"]

# Lista explícita de columnas válidas
columnas_previas = [col for col in df_limpio.columns if (
    "NUM_PAGOS" not in col and
    "TOTAL_RECAUDADO" not in col and
    "BENEFICIO_ESTIMADO" not in col and
    col != "NUM_ASISTENCIAS" and
    col != "FECHA_EVENTO"
)]

X = df_limpio[columnas_previas]
X.columns = X.columns.astype(str)

# === SPLIT TRAIN/TEST ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === MODELO LINEAL ===
modelo_lr = LinearRegression()
modelo_lr.fit(X_train, y_train)
y_pred_lr = modelo_lr.predict(X_test)

print("\n📊 Evaluación del Modelo Lineal (solo con datos previos):")
print(f"MAE  (Error absoluto medio): {mean_absolute_error(y_test, y_pred_lr):.2f}")
print(f"RMSE (Raíz del error cuadrático medio): {mean_squared_error(y_test, y_pred_lr) ** 0.5:.2f}")
print(f"R²   (Coeficiente de determinación): {r2_score(y_test, y_pred_lr):.2f}")

# === RANDOM FOREST ===
modelo_rf = RandomForestRegressor(n_estimators=100, random_state=42)
modelo_rf.fit(X_train, y_train)
y_pred_rf = modelo_rf.predict(X_test)

print("\n🌲 Evaluación del Random Forest (solo con datos previos):")
print(f"MAE  (Error absoluto medio): {mean_absolute_error(y_test, y_pred_rf):.2f}")
print(f"RMSE (Raíz del error cuadrático medio): {mean_squared_error(y_test, y_pred_rf) ** 0.5:.2f}")
print(f"R²   (Coeficiente de determinación): {r2_score(y_test, y_pred_rf):.2f}")

# === IMPORTANCIA DE VARIABLES ===
importances = modelo_rf.feature_importances_
feature_importance = pd.Series(importances, index=X.columns).sort_values(ascending=False)

print("\n🔍 Top 10 variables más importantes (modelo previo):")
print(feature_importance.head(10))

# === GRAFICAR ===
plt.figure(figsize=(10, 6))
feature_importance.head(10).plot(kind='barh')
plt.title("🎯 Variables más importantes para predecir NUM_ASISTENCIAS (antes del evento)")
plt.xlabel("Importancia (de 0 a 1)")
plt.gca().invert_yaxis()
plt.grid(True)
plt.tight_layout()
plt.show()
