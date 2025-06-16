import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Rutas de entrada y salida
PATH_REAL = Path("data/raw/dataset_modelo_validado.csv")
PATH_SIM = Path("data/raw/simulacion_datos_girona.csv")
MODEL_PATH = Path("src/modelos/modelo_beneficio_girona.pkl")
VERSION_PATH = Path("src/modelos/beneficio_version.txt")
CSV_FUTURO = Path("data/predicciones/simulaciones_futuras.csv")

def entrenar_modelo_beneficio():
    """
    Entrena un modelo de regresión lineal para predecir el beneficio estimado de eventos.
    Utiliza datos reales y simulados, realiza limpieza, codifica variables categóricas,
    entrena el modelo, lo guarda, y muestra métricas.
    """

    # Carga y filtrado de datos
    df_real = pd.read_csv(PATH_REAL, parse_dates=["FECHA_EVENTO"])
    df_sim = pd.read_csv(PATH_SIM, parse_dates=["FECHA_EVENTO"])

    # Filtrar únicamente eventos de Girona de tipo "pago"
    df_real = df_real[(df_real["COMUNIDAD"].str.upper() == "GIRONA") & (df_real["TIPO_EVENTO"] == "pago")]
    df_sim = df_sim[(df_sim["COMUNIDAD"].str.upper() == "GIRONA") & (df_sim["TIPO_EVENTO"] == "pago")]

    # Eliminar simulaciones en fechas ya existentes en los datos reales
    fechas_reales = df_real["FECHA_EVENTO"].dt.normalize()
    df_sim = df_sim[~df_sim["FECHA_EVENTO"].dt.normalize().isin(fechas_reales)]

    # Combinar datasets
    df_total = pd.concat([df_real, df_sim], ignore_index=True)

    # Definición de features (variables categóricas) y target 
    features = [
        "NUM_ASISTENCIAS", "COSTE_UNITARIO", "PRECIO_MEDIO",
        "MES", "DIA_SEMANA_NUM", "DIA_MES", "SEMANA_DENTRO_DEL_MES",
        "TEMPORADA", "COLABORACION", "TIPO_ACTIVIDAD", "TEMPERATURA"
    ]
    target = "BENEFICIO_ESTIMADO"

    # Eliminar registros con valores nulos en variables necesarias
    df_total = df_total.dropna(subset=features + [target])

    # Homogeneizar valores categóricos
    df_total["TIPO_ACTIVIDAD"] = df_total["TIPO_ACTIVIDAD"].str.strip().str.lower().replace({"ludica": "ludico"})

    # Codificación one-hot de variables categóricas
    df_model = pd.get_dummies(df_total[features + [target]], columns=["TEMPORADA", "TIPO_ACTIVIDAD"], drop_first=True)

    # Entrenamiento del modelo
    X = df_model.drop(columns=[target])
    y = df_model[target]
    final_features = X.columns.tolist()

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    modelo = LinearRegression()
    modelo.fit(X_train, y_train)

    # Guardar el modelo y la versión
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump((modelo, final_features), MODEL_PATH)

    num_eventos_actual = df_total.shape[0]
    with open(VERSION_PATH, "w") as f:
        f.write(str(num_eventos_actual))

    # Evaluación del modelo
    y_pred = modelo.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print("\n✅ Modelo de beneficio entrenado y guardado")
    print(f"📊 MAE: {mae:.2f} | RMSE: {rmse:.2f} | R²: {r2:.2f}")

# Ejecución directa
if __name__ == "__main__":
    entrenar_modelo_beneficio()
