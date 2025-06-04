
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

# === CARGA DE DATOS CON CLUSTERS ===
df = pd.read_csv("stats/dataset_modelo_clusterizado_v2.csv", parse_dates=["FECHA_EVENTO"])

# === VARIABLES ===
y = df["NUM_ASISTENCIAS"]
X = df.drop(columns=["NUM_ASISTENCIAS", "FECHA_EVENTO"])

# Convertir columnas categóricas a dummies (por si CLUSTER_EVENTO no lo está)
X = pd.get_dummies(X, drop_first=True)
X.columns = X.columns.astype(str)

# === SPLIT ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === MODELO LINEAL ===
modelo_lr = LinearRegression()
modelo_lr.fit(X_train, y_train)
y_pred_lr = modelo_lr.predict(X_test)

# === RANDOM FOREST ===
modelo_rf = RandomForestRegressor(n_estimators=100, random_state=42)
modelo_rf.fit(X_train, y_train)
y_pred_rf = modelo_rf.predict(X_test)

# === EVALUACIÓN ===
def evaluar(y_test, y_pred, nombre):
    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred) ** 0.5
    r2 = r2_score(y_test, y_pred)
    return {"Modelo": nombre, "MAE": mae, "RMSE": rmse, "R2": r2}

resultados = []
resultados.append(evaluar(y_test, y_pred_lr, "Regresión Lineal"))
resultados.append(evaluar(y_test, y_pred_rf, "Random Forest"))

df_resultados = pd.DataFrame(resultados)
print("\n📊 Comparativa de Modelos:")
print(df_resultados)

# === GRAFICAR RESULTADOS ===
fig, ax = plt.subplots(figsize=(10, 5))
df_resultados.set_index("Modelo")[["MAE", "RMSE"]].plot(kind="barh", ax=ax)
plt.title("Comparativa de errores de modelos de regresión")
plt.xlabel("Error")
plt.tight_layout()
plt.grid(True)
plt.show()
