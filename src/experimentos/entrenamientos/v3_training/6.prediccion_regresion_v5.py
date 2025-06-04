import pandas as pd
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import os

# === CARGA DE DATOS ===
df = pd.read_csv("stats/dataset_modelo_clusterizado.csv", parse_dates=["FECHA_EVENTO"])

# === VARIABLES ===
features = [
    "COSTE_ESTIMADO", "SEMANA", "DIA_SEMANA", "MES", "TIPO_EVENTO", 
    "COMUNIDAD", "CLUSTER_EVENTO"
]
target = "NUM_ASISTENCIAS"

df_model = df[features + [target]].copy()
df_model = pd.get_dummies(df_model, columns=["DIA_SEMANA", "MES", "TIPO_EVENTO", "COMUNIDAD"], drop_first=True)

X = df_model.drop(columns=[target])
y = df_model[target]

# === SPLIT ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === ENTRENAMIENTO ===
modelo_lr = LinearRegression()
modelo_rf = RandomForestRegressor(n_estimators=100, random_state=42)

modelo_lr.fit(X_train, y_train)
modelo_rf.fit(X_train, y_train)

# === GUARDADO DE MODELOS ===
os.makedirs("modelos", exist_ok=True)
joblib.dump(modelo_lr, "src/modelos/modelo_regresion_lineal.pkl")
joblib.dump(modelo_rf, "src/modelos/modelo_random_forest.pkl")

print("\n✅ Modelos de regresión guardados correctamente en la carpeta 'modelos/'")

# === MÉTRICAS OPCIONALES ===
y_pred_lr = modelo_lr.predict(X_test)
y_pred_rf = modelo_rf.predict(X_test)

print("\n📊 Evaluación:")
print(f"Lineal - MAE: {mean_absolute_error(y_test, y_pred_lr):.2f} | R2: {r2_score(y_test, y_pred_lr):.2f}")
print(f"RF     - MAE: {mean_absolute_error(y_test, y_pred_rf):.2f} | R2: {r2_score(y_test, y_pred_rf):.2f}")
