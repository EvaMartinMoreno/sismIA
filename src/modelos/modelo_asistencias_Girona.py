# 📦 Librerías
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# 📁 Rutas
PATH_REAL = Path("data/clean/dataset_modelo.csv")
PATH_SIM = Path("data/clean/simulacion_datos_girona.csv")
MODEL_PATH = Path("models/reglineal_asistencias_girona.pkl")

def entrenar_modelo_asistencias():
    # 📥 Cargar datos
    df_real = pd.read_csv(PATH_REAL)
    df_sim = pd.read_csv(PATH_SIM)

    # Identificador de origen
    df_real["ES_REAL"] = 1
    df_sim["ES_REAL"] = 0

    # Unir y filtrar
    df_combined = pd.concat([df_real, df_sim], ignore_index=True)
    df_combined = df_combined[
        (df_combined["TIPO_EVENTO"] == "pago") &
        (df_combined["TEMPERATURA"].notnull())
    ].copy()

    # 🧼 Normalizar texto y eliminar outliers
    df_combined["TIPO_ACTIVIDAD"] = df_combined["TIPO_ACTIVIDAD"].str.strip().str.lower()
    df_combined["TIPO_ACTIVIDAD"] = df_combined["TIPO_ACTIVIDAD"].replace({"ludica": "ludico"})

    filtro_outliers = (
        (df_combined["COSTE_ESTIMADO"] <= 1000) &
        (df_combined["BENEFICIO_ESTIMADO"] >= -1000) &
        (df_combined["PRECIO_MEDIO"] <= 30)
    )
    df_combined = df_combined[filtro_outliers].copy()

    # 🔢 Features y target
    features = [
        "COSTE_ESTIMADO", "PRECIO_MEDIO", "DIA_SEMANA_NUM", "MES",
        "SEMANA_DENTRO_DEL_MES", "COLABORACION", "TEMPORADA",
        "TIPO_ACTIVIDAD", "TEMPERATURA"
    ]
    target = "NUM_ASISTENCIAS"

    df_model = df_combined[features + [target]].copy()
    df_model = pd.get_dummies(df_model, columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)

    X = df_model.drop(columns=[target])
    y = df_model[target]

    # Split y escalado
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 🤖 Entrenamiento
    modelo = LinearRegression()
    modelo.fit(X_train_scaled, y_train)
    joblib.dump(modelo, MODEL_PATH)

    # 📏 Métricas
    y_pred = modelo.predict(X_test_scaled)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print("✅ Modelo de asistencias entrenado y guardado")
    print(f"📊 MAE: {mae:.2f} | RMSE: {rmse:.2f} | R²: {r2:.2f}")
