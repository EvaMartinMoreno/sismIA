import pandas as pd
import numpy as np
import random
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# === 📥 Cargar datos reales de Elche
ruta_real = Path("data/clean/dataset_modelo.csv")
df_real = pd.read_csv(ruta_real, parse_dates=["FECHA_EVENTO"])
df_real_elche = df_real[df_real["COMUNIDAD"].str.upper() == "ELCHE"].copy()

# === 📊 Calcular promedios y rangos para simular
easistencia_media = df_real_elche["NUM_ASISTENCIAS"].mean()
precio_medio = df_real_elche["PRECIO_MEDIO"].mean()
coste_unitario = df_real_elche["COSTE_UNITARIO"].mean()

# Rango de fechas futuras
fecha_inicio = df_real_elche["FECHA_EVENTO"].max() + timedelta(days=7)
fechas_simuladas = pd.date_range(start=fecha_inicio, periods=10, freq="7D")

# === 🛠️ Generar eventos simulados
np.random.seed(42)
simulaciones = []

for fecha in fechas_simuladas:
    simulaciones.append({
        "FECHA_EVENTO": fecha,
        "NOMBRE_EVENTO": f"Evento Simulado {fecha.strftime('%Y-%m-%d')}",
        "COMUNIDAD": "ELCHE",
        "TIPO_EVENTO": "pago",
        "COSTE_UNITARIO": round(np.random.normal(coste_unitario, 1.5), 2),
        "PRECIO_MEDIO": round(np.random.normal(precio_medio, 1.5), 2),
        "COLABORACION": np.random.choice([0, 1], p=[0.5, 0.5]),
        "TIPO_ACTIVIDAD": np.random.choice(["almuerzo", "charla", "entrenamiento"]),
        "MES": fecha.month,
        "DIA_SEMANA_NUM": fecha.weekday(),
        "DIA_MES": fecha.day,
        "SEMANA_MES": (fecha.day - 1) // 7 + 1,
        "TEMPORADA": "verano" if fecha.month in [6, 7, 8] else "no_verano"
    })

# === 💾 Guardar CSV
simulado_df = pd.DataFrame(simulaciones)
salida = Path("stats/datasets/simulacion_datos_elche.csv")
simulado_df.to_csv(salida, index=False)
print(f"✅ Datos simulados guardados en: {salida.resolve()}")

# Pintamos puntos por separado para evitar líneas feas
plt.figure(figsize=(12, 6))
sns.scatterplot(data=df_sim, x="FECHA_EVENTO", y="NUM_ASISTENCIAS", label="simulado", color="royalblue", s=50)
sns.scatterplot(data=df_real, x="FECHA_EVENTO", y="NUM_ASISTENCIAS", label="real", color="orangered", s=50)

# Opcional: línea de tendencia sólo para lo simulado (porque es regular)
sns.lineplot(data=df_sim, x="FECHA_EVENTO", y="NUM_ASISTENCIAS", label="Tendencia simulada", color="royalblue", lw=1.5)

plt.title("📍 Asistentes por evento en Girona (simulado vs real)")
plt.xlabel("Fecha del evento")
plt.ylabel("Número de asistentes por evento")
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.show()
