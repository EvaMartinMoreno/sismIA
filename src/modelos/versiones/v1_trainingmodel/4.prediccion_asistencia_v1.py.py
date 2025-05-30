import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# === CARGA DE DATOS ===
df = pd.read_csv("stats/dataset_entrenamiento_pago.csv", parse_dates=["FECHA_EVENTO"])

# === VARIABLES DISPONIBLES ANTES DE LANZAR EL EVENTO ===
# (Excluimos: NUM_PAGOS, TOTAL_RECAUDADO, BENEFICIO_ESTIMADO, NUM_INSCRITAS)
features = [
    col for col in df.columns
    if col not in ['FECHA_EVENTO', 'NUM_ASISTENCIAS', 'NUM_PAGOS', 'TOTAL_RECAUDADO', 'BENEFICIO_ESTIMADO']
]

X = df[features]
y = df["NUM_ASISTENCIAS"]

# === SPLIT TRAIN/TEST ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === ENTRENAMIENTO DEL MODELO ===
modelo = LinearRegression()
modelo.fit(X_train, y_train)

# === PREDICCIONES ===
y_pred = modelo.predict(X_test)

# === EVALUACIÓN DEL MODELO ===
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
rmse = mse ** 0.5
r2 = r2_score(y_test, y_pred)

print("📊 Evaluación del Modelo (predicción previa al evento):")
print(f"MAE  (Error absoluto medio): {mae:.2f}")
print(f"RMSE (Raíz del error cuadrático medio): {rmse:.2f}")
print(f"R²   (Coeficiente de determinación): {r2:.2f}")

#
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# === CARGA DE DATOS ===
df = pd.read_csv("stats/dataset_entrenamiento_pago.csv", parse_dates=["FECHA_EVENTO"])

# === VARIABLES DISPONIBLES ANTES DEL EVENTO ===
features = [
    col for col in df.columns
    if col not in ['FECHA_EVENTO', 'NUM_ASISTENCIAS', 'NUM_PAGOS', 'TOTAL_RECAUDADO', 'BENEFICIO_ESTIMADO']
]

X = df[features]
y = df["NUM_ASISTENCIAS"]

# === SPLIT TRAIN/TEST ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === ENTRENAMIENTO DEL RANDOM FOREST ===
modelo_rf = RandomForestRegressor(n_estimators=100, random_state=42)
modelo_rf.fit(X_train, y_train)

# === PREDICCIÓN Y EVALUACIÓN ===
y_pred = modelo_rf.predict(X_test)

mae = mean_absolute_error(y_test, y_pred)
rmse = mean_squared_error(y_test, y_pred) ** 0.5
r2 = r2_score(y_test, y_pred)

print("🌲 Evaluación del Random Forest:")
print(f"MAE  (Error absoluto medio): {mae:.2f}")
print(f"RMSE (Raíz del error cuadrático medio): {rmse:.2f}")
print(f"R²   (Coeficiente de determinación): {r2:.2f}")

# === IMPORTAR Y CALCULAR IMPORTANCIA DE VARIABLES ===
import pandas as pd

importances = modelo_rf.feature_importances_
feature_importance = pd.Series(importances, index=X.columns).sort_values(ascending=False)

# === MOSTRAR TOP 10 VARIABLES ===
print("🔍 Top 10 variables más importantes en el modelo:")
print(feature_importance.head(10))

# === OPCIONAL: GRAFICAR ===
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
feature_importance.head(10).plot(kind='barh')
plt.title("🎯 Variables más importantes para predecir NUM_ASISTENCIAS")
plt.xlabel("Importancia (de 0 a 1)")
plt.gca().invert_yaxis()
plt.grid(True)
plt.tight_layout()
plt.show()


# Modelo 2:
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# === CARGA DE DATOS ===
df = pd.read_csv("stats/dataset_entrenamiento_pago.csv", parse_dates=["FECHA_EVENTO"])

# === SELECCIÓN DE VARIABLES PARA EL MODELO DE SEGUIMIENTO ===
features = [
    col for col in df.columns
    if col not in ['FECHA_EVENTO', 'NUM_ASISTENCIAS']  # esta es la que queremos predecir
]

X = df[features]
y = df["NUM_ASISTENCIAS"]

# === SPLIT TRAIN/TEST ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === ENTRENAMIENTO DEL RANDOM FOREST ===
modelo_seguimiento = RandomForestRegressor(n_estimators=100, random_state=42)
modelo_seguimiento.fit(X_train, y_train)

# === PREDICCIONES ===
y_pred = modelo_seguimiento.predict(X_test)

# === EVALUACIÓN ===
mae = mean_absolute_error(y_test, y_pred)
rmse = mean_squared_error(y_test, y_pred) ** 0.5
r2 = r2_score(y_test, y_pred)

print("📈 Evaluación del Modelo de Seguimiento:")
print(f"MAE  (Error absoluto medio): {mae:.2f}")
print(f"RMSE (Raíz del error cuadrático medio): {rmse:.2f}")
print(f"R²   (Coeficiente de determinación): {r2:.2f}")

importances = modelo_seguimiento.feature_importances_
feature_importance = pd.Series(importances, index=X.columns).sort_values(ascending=False)

print("🔍 Top variables en el modelo de seguimiento:")
print(feature_importance.head(10))

# Opcional: gráfica
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
feature_importance.head(10).plot(kind='barh')
plt.title("🔍 Variables más importantes - Modelo de seguimiento")
plt.xlabel("Importancia")
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()
