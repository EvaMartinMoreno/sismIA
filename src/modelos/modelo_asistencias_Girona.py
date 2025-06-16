import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Rutas de entrada y salida
PATH_REAL = Path("data/raw/dataset_modelo_validado.csv")
PATH_SIM = Path("data/raw/simulacion_datos_girona.csv")
MODEL_PATH = Path("src/modelos/modelo_asistencias_girona.pkl")
VERSION_PATH = Path("src/modelos/asistencias_version.txt")

def entrenar_modelo_asistencias():
    # Cargar datos
    df_real = pd.read_csv(PATH_REAL)
    df_sim = pd.read_csv(PATH_SIM)

    # Identificador de origen
    df_real["ES_REAL"] = 1
    df_sim["ES_REAL"] = 0

    # Filtrar los datos reales por la comunidad de Girona, eventos de pago y sin nulos
    df_real = df_real[
        (df_real["COMUNIDAD"] == "GIRONA") &
        (df_real["TIPO_EVENTO"] == "pago") &
        (df_real["TEMPERATURA"].notnull())
    ]

    # Filtrar simulados (Girona y de pago)
    df_sim = df_sim[
        (df_sim["TIPO_EVENTO"] == "pago") &
        (df_sim["TEMPERATURA"].notnull())
    ]

    # Unir ambos
    df_combined = pd.concat([df_real, df_sim], ignore_index=True)

    # Normalizar texto y eliminar outliers
    df_combined["TIPO_ACTIVIDAD"] = df_combined["TIPO_ACTIVIDAD"].str.strip().str.lower()
    df_combined["TIPO_ACTIVIDAD"] = df_combined["TIPO_ACTIVIDAD"].replace({"ludica": "ludico"})

    filtro_outliers = (
        (df_combined["COSTE_ESTIMADO"] <= 1000) &
        (df_combined["BENEFICIO_ESTIMADO"] >= -1000) &
        (df_combined["PRECIO_MEDIO"] <= 30)
    )
    df_combined = df_combined[filtro_outliers].copy()

    # Validar si hay nuevos eventos
    num_eventos_actual = df_combined.shape[0]
    if VERSION_PATH.exists():
        with open(VERSION_PATH, "r") as f:
            num_eventos_previo = int(f.read().strip())
    else:
        num_eventos_previo = -1

    if num_eventos_actual == num_eventos_previo:
        print("⏩ No hay nuevos eventos. Se omite el reentrenamiento.")
        return

    # Definición de features (variables categóricas) y target 
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

    # Guardar las columnas reales
    final_features = X.columns.tolist()  

    # Split y escalado
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Entrenamiento
    modelo = LinearRegression()
    modelo.fit(X_train_scaled, y_train)

    # Guardar modelo + features
    joblib.dump((modelo, final_features), MODEL_PATH)  

    # Guardar nueva versión
    with open(VERSION_PATH, "w") as f:
        f.write(str(num_eventos_actual))

    # Métricas
    y_pred = modelo.predict(X_test_scaled)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print("odelo de asistencias entrenado y guardado")
    print(f"MAE: {mae:.2f} | RMSE: {rmse:.2f} | R²: {r2:.2f}")

# Ejecución directa
if __name__ == "__main__":
    entrenar_modelo_asistencias()
