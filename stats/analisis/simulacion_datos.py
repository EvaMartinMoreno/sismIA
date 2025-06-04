import pandas as pd
import numpy as np
import random
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# === SEMILLA
random.seed(42)
np.random.seed(42)

# === FUNCIONES DE APOYO
def obtener_temporada(mes):
    if mes in [12, 1, 2]:
        return "invierno"
    elif mes in [3, 4, 5]:
        return "primavera"
    elif mes in [6, 7, 8]:
        return "verano"
    else:
        return "otoño"

def generar_colaboracion():
    return np.random.choice([1, 0], p=[0.1667, 0.8333])

def generar_tipo_actividad():
    return np.random.choice(["almuerzo", "ludico", "deportiva"], p=[0.5, 0.3333, 0.1667])

# === NUEVA FUNCIÓN DE CRECIMIENTO REALISTA
def calcular_crecimiento_con_ruido_refinado(edad_meses: int, mes: int) -> int:
    estacionalidad = {
        1: -5, 2: -3, 3: 1, 4: 2, 5: 3, 6: 1,
        7: -1, 8: -3, 9: 2, 10: 4, 11: 3, 12: -4
    }

    # V descendente entre edad 35-45 (~marzo 2024 - enero 2025) y rebote fuerte
    if edad_meses < 35:
        tendencia = 22 + edad_meses * 0.4
    elif 35 <= edad_meses <= 45:
        tendencia = 55 - (edad_meses - 35) * 4.5
    else:
        tendencia = 15 + (edad_meses - 45) * 5.2

    ruido = np.random.normal(0, 4 if edad_meses > 45 else 2.5)
    ajuste_estacional = estacionalidad.get(mes, 0)
    total = tendencia + ajuste_estacional + ruido
    return max(5, int(round(total)))

# === GENERADOR DE DATOS SIMULADOS
def generar_datos_simulados(comunidad: str, inicio: str, meses_totales: int = 60,
                             eventos_pago_por_mes: int = 1, eventos_gratuito_por_mes: int = 4) -> pd.DataFrame:
    eventos = []
    contador_eventos = 1
    inicio_dt = pd.Timestamp(inicio)
    inicio_global = datetime(2021, 1, 1)

    for mes_offset in range(meses_totales):
        fecha_evento = inicio_global + pd.DateOffset(months=mes_offset)
        edad_meses = max(0, (fecha_evento.year - inicio_dt.year) * 12 + (fecha_evento.month - inicio_dt.month))
        mes = fecha_evento.month
        semana = int(fecha_evento.strftime("%U"))
        dia_semana = fecha_evento.strftime("%A")
        año = fecha_evento.year
        dia_mes = fecha_evento.day
        temporada = obtener_temporada(mes)

        # GRATUITOS
        for _ in range(eventos_gratuito_por_mes):
            asistentes = int(np.random.normal(loc=20, scale=3))
            asistentes = max(1, asistentes)
            inscritas = asistentes + random.randint(1, 5)
            coste = round(random.uniform(50, 150), 2)
            beneficio = 0 - coste
            eventos.append({
                "NOMBRE_EVENTO": f"Sisterhood Free {contador_eventos}",
                "FECHA_EVENTO": fecha_evento,
                "COMUNIDAD": comunidad,
                "DIA_SEMANA": dia_semana,
                "DIA_SEMANA_NUM": fecha_evento.weekday(),
                "DIA_MES": dia_mes,
                "SEMANA_MES": semana,
                "MES": mes,
                "AÑO": año,
                "TEMPORADA": temporada,
                "NUM_INSCRITAS": inscritas,
                "NUM_PAGOS": 0,
                "NUM_ASISTENCIAS": asistentes,
                "TOTAL_RECAUDADO": 0.0,
                "EVENTO_GRATUITO": 1,
                "TIPO_EVENTO": "gratuito",
                "COSTE_UNITARIO": coste / inscritas,
                "COSTE_ESTIMADO": coste,
                "BENEFICIO_ESTIMADO": beneficio,
                "PRECIO_MEDIO": 0.0,
                "COLABORACION": generar_colaboracion(),
                "TIPO_ACTIVIDAD": generar_tipo_actividad()
            })
            contador_eventos += 1

        # DE PAGO
        for _ in range(eventos_pago_por_mes):
            asistentes = calcular_crecimiento_con_ruido_refinado(edad_meses, mes)
            inscritas = asistentes + random.randint(2, 8)
            precio = round(random.uniform(10, 20), 2)
            ingresos = asistentes * precio
            coste = round(random.uniform(100, 250), 2)
            beneficio = ingresos - coste
            eventos.append({
                "NOMBRE_EVENTO": f"Sisterhood Premium {contador_eventos}",
                "FECHA_EVENTO": fecha_evento,
                "COMUNIDAD": comunidad,
                "DIA_SEMANA": dia_semana,
                "DIA_SEMANA_NUM": fecha_evento.weekday(),
                "DIA_MES": dia_mes,
                "SEMANA_MES": semana,
                "MES": mes,
                "AÑO": año,
                "TEMPORADA": temporada,
                "NUM_INSCRITAS": inscritas,
                "NUM_PAGOS": asistentes,
                "NUM_ASISTENCIAS": asistentes,
                "TOTAL_RECAUDADO": ingresos,
                "EVENTO_GRATUITO": 0,
                "TIPO_EVENTO": "pago",
                "COSTE_UNITARIO": coste / inscritas,
                "COSTE_ESTIMADO": coste,
                "BENEFICIO_ESTIMADO": beneficio,
                "PRECIO_MEDIO": precio,
                "COLABORACION": generar_colaboracion(),
                "TIPO_ACTIVIDAD": generar_tipo_actividad()
            })
            contador_eventos += 1

    return pd.DataFrame(eventos)

# === GENERACIÓN Y GUARDADO
df_simulado = generar_datos_simulados("GIRONA", "2024-01-01")
output_path = Path("stats") / "datasets" / "simulacion_datos_girona.csv"
output_path.parent.mkdir(parents=True, exist_ok=True)
df_simulado.to_csv(output_path, index=False)
print(f"✅ Dataset simulado generado con {len(df_simulado)} eventos.")
print(f"📍 Guardado en: {output_path}")

# === VISUALIZACIÓN COMPARATIVA POR EVENTO
df_real = pd.read_csv("data/clean/dataset_modelo.csv", parse_dates=["FECHA_EVENTO"])
df_real = df_real[(df_real["COMUNIDAD"] == "GIRONA") & (df_real["TIPO_EVENTO"] == "pago")]

# Eliminar outliers en ambos
lim_sup_sim = df_simulado["NUM_ASISTENCIAS"].quantile(0.95)
lim_sup_real = df_real["NUM_ASISTENCIAS"].quantile(0.95)

df_sim = df_simulado[(df_simulado["TIPO_EVENTO"] == "pago") & (df_simulado["NUM_ASISTENCIAS"] < lim_sup_sim)].copy()
df_real = df_real[df_real["NUM_ASISTENCIAS"] < lim_sup_real].copy()

df_sim["TIPO"] = "simulado"
df_real["TIPO"] = "real"

df_plot = pd.concat([df_sim, df_real], ignore_index=True)

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
