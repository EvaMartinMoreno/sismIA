import pandas as pd
import numpy as np
import random
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# === SEMILLA PARA REPRODUCIBILIDAD
random.seed(42)
np.random.seed(42)

# === DISTRIBUCIONES REALES DE EVENTOS DE PAGO EN GIRONA
PESOS_DIA_SEMANA = {4: 0.16666666666666666, 6: 0.8333333333333334}  # viernes, domingo
PESOS_SEMANA_MES = {1: 0.16666666666666666, 2: 0.5, 3: 0.3333333333333333}

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
    return np.random.choice([1, 0], p=[0.3, 0.7])

def generar_tipo_actividad():
    return np.random.choice(["almuerzo", "ludico", "deportiva"], p=[0.5, 0.3, 0.2])

def calcular_crecimiento_con_ruido_refinado(edad_meses: int, mes: int, colaboracion: int) -> int:
    estacionalidad = {
        1: -5, 2: -3, 3: 1, 4: 2, 5: 3, 6: 1,
        7: -1, 8: -3, 9: 2, 10: 4, 11: 3, 12: -4
    }
    if edad_meses < 35:
        tendencia = 22 + edad_meses * 0.4
    elif 35 <= edad_meses <= 45:
        tendencia = 55 - (edad_meses - 35) * 4.5
    else:
        tendencia = 15 + (edad_meses - 45) * 5.2

    ajuste_estacional = estacionalidad.get(mes, 0)
    ruido = np.random.normal(0, 3)
    base = tendencia + ajuste_estacional + ruido

    if colaboracion:
        base *= 0.6  # menor asistencia por exclusividad

    return max(5, int(round(base)))

def ajustar_fecha_con_pesos(fecha_base: pd.Timestamp) -> pd.Timestamp:
    dia_semana_num = np.random.choice(list(PESOS_DIA_SEMANA.keys()), p=list(PESOS_DIA_SEMANA.values()))
    dias_hasta_dia = (dia_semana_num - fecha_base.weekday()) % 7
    return fecha_base + pd.Timedelta(days=dias_hasta_dia)

def generar_datos_simulados(comunidad: str, inicio: str, meses_totales: int = 61,
                             eventos_pago_por_mes: int = 1, eventos_gratuito_por_mes: int = 4) -> pd.DataFrame:
    eventos = []
    contador_eventos = 1
    inicio_dt = pd.Timestamp(inicio)
    inicio_global = datetime(2018, 4, 1)

    for mes_offset in range(meses_totales):
        fecha_mes = inicio_global + pd.DateOffset(months=mes_offset)
        edad_meses = max(0, (fecha_mes.year - inicio_dt.year) * 12 + (fecha_mes.month - inicio_dt.month))
        mes = fecha_mes.month
        año = fecha_mes.year
        temporada = obtener_temporada(mes)

        for _ in range(eventos_gratuito_por_mes):
            asistentes = max(1, int(np.random.normal(loc=20, scale=3)))
            inscritas = asistentes + random.randint(1, 5)
            coste = round(random.uniform(50, 150), 2)
            dia_mes = random.randint(1, 28)
            fecha_evento = pd.Timestamp(year=año, month=mes, day=dia_mes)
            semana_dentro_mes = (fecha_evento.day - 1) // 7 + 1

            eventos.append({
                "NOMBRE_EVENTO": f"Sisterhood Free {contador_eventos}",
                "FECHA_EVENTO": fecha_evento,
                "COMUNIDAD": comunidad,
                "DIA_SEMANA": fecha_evento.strftime("%A"),
                "DIA_SEMANA_NUM": fecha_evento.weekday(),
                "DIA_MES": fecha_evento.day,
                "SEMANA_DENTRO_DEL_MES": semana_dentro_mes,
                "MES": mes,
                "AÑO": año,
                "TEMPORADA": temporada,
                "NUM_INSCRITAS": inscritas,
                "NUM_PAGOS": 0,
                "NUM_ASISTENCIAS": asistentes,
                "TOTAL_RECAUDADO": 0.0,
                "EVENTO_GRATUITO": 1,
                "TIPO_EVENTO": "gratuito",
                "COSTE_UNITARIO": 0,
                "COSTE_ESTIMADO": 0,
                "BENEFICIO_ESTIMADO": 0,
                "PRECIO_MEDIO": 0.0,
                "COLABORACION": 0,
                "TIPO_ACTIVIDAD": "only run"
            })
            contador_eventos += 1

        for _ in range(eventos_pago_por_mes):
            colaboracion = generar_colaboracion()
            precio = round(np.random.uniform(12, 18) if colaboracion else np.random.uniform(9, 14), 2)
            asistentes = calcular_crecimiento_con_ruido_refinado(edad_meses, mes, colaboracion)
            inscritas = asistentes + random.randint(2, 8)
            ingresos = asistentes * precio
            coste = round(np.random.uniform(130, 250) if colaboracion else np.random.uniform(80, 180), 2)

            semana_simulada = np.random.choice(list(PESOS_SEMANA_MES.keys()), p=list(PESOS_SEMANA_MES.values()))
            dia_base = 1 + (semana_simulada - 1) * 7
            fecha_base = pd.Timestamp(year=año, month=mes, day=min(dia_base, 28))
            fecha_evento_pago = ajustar_fecha_con_pesos(fecha_base)

            eventos.append({
                "NOMBRE_EVENTO": f"Sisterhood Premium {contador_eventos}",
                "FECHA_EVENTO": fecha_evento_pago,
                "COMUNIDAD": comunidad,
                "DIA_SEMANA": fecha_evento_pago.strftime("%A"),
                "DIA_SEMANA_NUM": fecha_evento_pago.weekday(),
                "DIA_MES": fecha_evento_pago.day,
                "SEMANA_DENTRO_DEL_MES": semana_simulada,
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
                "BENEFICIO_ESTIMADO": ingresos - coste,
                "PRECIO_MEDIO": precio,
                "COLABORACION": colaboracion,
                "TIPO_ACTIVIDAD": generar_tipo_actividad()
            })
            contador_eventos += 1

    return pd.DataFrame(eventos)

# === EJECUCIÓN DIRECTA DEL SCRIPT
if __name__ == "__main__":
    df_simulado = generar_datos_simulados("GIRONA", "2018-04-01")
    output_path = Path("data/raw/simulacion_datos_girona_v2.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_simulado.to_csv(output_path, index=False)
    print(f"✅ Dataset simulado generado con {len(df_simulado)} eventos.")
    print(f"📍 Guardado en: {output_path.resolve()}")

def simular_datos_Girona():
    df_simulado = generar_datos_simulados("GIRONA", "2018-04-01")
    output_path = Path("data/raw/simulacion_datos_girona_v2.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_simulado.to_csv(output_path, index=False)
    print(f"✅ Dataset simulado generado con {len(df_simulado)} eventos.")
    print(f"📍 Guardado en: {output_path.resolve()}")
