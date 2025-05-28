
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# === CONFIGURACIÓN INICIAL ===
sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)

# === CARGA DE DATOS ===
ruta_csv = Path(__file__).parent / "dataset_modelo.csv"
df = pd.read_csv(ruta_csv)
df["FECHA_EVENTO"] = pd.to_datetime(df["FECHA_EVENTO"], errors="coerce")

# === NUEVAS VARIABLES CALCULADAS ===
df["TASA_ASISTENCIA"] = (df["NUM_ASISTENCIAS"] / df["NUM_INSCRITAS"]).fillna(0).clip(0, 1)
df["INGRESO_POR_ASISTENTE"] = (df["TOTAL_RECAUDADO"] / df["NUM_ASISTENCIAS"]).replace([np.inf, -np.inf], 0).fillna(0)

# === ANÁLISIS ESTADÍSTICO ===
eventos_por_mes = df.groupby(["COMUNIDAD", "TIPO_EVENTO", "MES"]).size().reset_index(name="NUM_EVENTOS")
mes_mas_eventos = eventos_por_mes.sort_values("NUM_EVENTOS", ascending=False).groupby(["COMUNIDAD", "TIPO_EVENTO"]).first().reset_index()
estadisticas = df.groupby(["COMUNIDAD", "TIPO_EVENTO"]).agg({
    "NUM_ASISTENCIAS": "mean",
    "BENEFICIO_ESTIMADO": "mean",
    "NUM_INSCRITAS": "mean",
    "NUM_PAGOS": "mean",
    "TOTAL_RECAUDADO": "mean"
}).reset_index()
eventos_totales = df.groupby(["COMUNIDAD", "TIPO_EVENTO"]).size().reset_index(name="TOTAL_EVENTOS")
eventos_por_dia = df.groupby(["COMUNIDAD", "TIPO_EVENTO", "DIA_SEMANA"]).size().reset_index(name="NUM_EVENTOS")
evento_max_asistencia = df.loc[df["NUM_ASISTENCIAS"].idxmax()][["NOMBRE_EVENTO", "COMUNIDAD", "TIPO_EVENTO", "NUM_ASISTENCIAS"]]
eventos_deficitarios = df[df["BENEFICIO_ESTIMADO"] <= 0]
eventos_baja_asistencia = df[df["TASA_ASISTENCIA"] < 0.5]
eventos_cero_asistencia = df[df["NUM_ASISTENCIAS"] == 0]

# === RESULTADOS POR TERMINAL ===
print("\nEventos por mes:\n", eventos_por_mes)
print("\nMes con más eventos por grupo:\n", mes_mas_eventos)
print("\nEstadísticas medias:\n", estadisticas)
print("\nTotal de eventos por grupo:\n", eventos_totales)
print("\nEventos por día de la semana:\n", eventos_por_dia)
print("\nEvento con más asistentes:\n", evento_max_asistencia.to_string())
print("\nEventos deficitarios (primeros 10):\n", eventos_deficitarios.head(10))
print("\nEventos con baja asistencia (<50%) (primeros 10):\n", eventos_baja_asistencia.head(10))
print("\nEventos con 0 asistentes (primeros 10):\n", eventos_cero_asistencia.head(10))

# === GRÁFICOS ===
# 1. Eventos por mes
plt.figure()
sns.countplot(data=df, x="MES", hue="COMUNIDAD")
plt.title("Número de eventos por mes y comunidad")
plt.tight_layout()
plt.show()

# 2. Asistencias por tipo de evento
plt.figure()
sns.boxplot(data=df, x="TIPO_EVENTO", y="NUM_ASISTENCIAS", hue="COMUNIDAD")
plt.title("Distribución de asistentes por tipo de evento")
plt.tight_layout()
plt.show()

# 3. Beneficio vs asistentes
plt.figure()
sns.scatterplot(data=df, x="NUM_ASISTENCIAS", y="BENEFICIO_ESTIMADO", hue="COMUNIDAD", style="TIPO_EVENTO")
plt.title("Relación entre asistentes y beneficio")
plt.tight_layout()
plt.show()

# 4. Tasa de asistencia por comunidad
plt.figure()
sns.boxplot(data=df, x="COMUNIDAD", y="TASA_ASISTENCIA", hue="TIPO_EVENTO")
plt.title("Tasa de asistencia por comunidad y tipo")
plt.tight_layout()
plt.show()

# 5. Ingreso por asistente
plt.figure()
sns.histplot(data=df[df["INGRESO_POR_ASISTENTE"] > 0], x="INGRESO_POR_ASISTENTE", bins=30, kde=True)
plt.title("Distribución de ingreso por asistente")
plt.tight_layout()
plt.show()
