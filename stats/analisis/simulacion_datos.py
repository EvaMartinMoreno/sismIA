# src/simulacion/simular_eventos_girona.py

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

def calcular_crecimiento_con_ruido_refinado(edad_meses: int, mes: int) -> int:
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
    ruido = np.random.normal(0, 4 if edad_meses > 45 else 2.5)
    ajuste_estacional = estacionalidad.get(mes, 0)
    total = tendencia + ajuste_estacional + ruido
    return max(5, int(round(total)))

def ajustar_fecha_a_findesemana(fecha_base: pd.Timestamp) -> pd.Timestamp:
    """Ajusta la fecha al siguiente viernes/sábado/domingo con preferencia por sábado y domingo."""
    fecha = fecha_base
    while fecha.weekday() not in [4, 5, 6]:  # 4=viernes, 5=sábado, 6=domingo
        fecha += pd.Timedelta(days=1)
    if fecha.weekday() == 4 and random.random() < 0.5:
        fecha += pd.Timedelta(days=random.choice([1, 2]))  # pásalo a sábado o domingo
    return fecha

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
        año = fecha_evento.year
        temporada = obtener_temporada(mes)

        # Eventos gratuitos
        for _ in range(eventos_gratuito_por_mes):
            asistentes = max(1, int(np.random.normal(loc=20, scale=3)))
            inscritas = asistentes + random.randint(1, 5)
            coste = round(random.uniform(50, 150), 2)
            eventos.append({
                "NOMBRE_EVENTO": f"Sisterhood Free {contador_eventos}",
                "FECHA_EVENTO": fecha_evento,
                "COMUNIDAD": comunidad,
                "DIA_SEMANA": fecha_evento.strftime("%A"),
                "DIA_SEMANA_NUM": fecha_evento.weekday(),
                "DIA_MES": fecha_evento.day,
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
                "BENEFICIO_ESTIMADO": -coste,
                "PRECIO_MEDIO": 0.0,
                "COLABORACION": generar_colaboracion(),
                "TIPO_ACTIVIDAD": generar_tipo_actividad()
            })
            contador_eventos += 1

        # Eventos de pago
        for _ in range(eventos_pago_por_mes):
            asistentes = calcular_crecimiento_con_ruido_refinado(edad_meses, mes)
            inscritas = asistentes + random.randint(2, 8)
            precio = round(random.uniform(10, 20), 2)
            ingresos = asistentes * precio
            coste = round(random.uniform(100, 250), 2)

            # Ajustar la fecha al siguiente finde
            fecha_evento_pago = ajustar_fecha_a_findesemana(fecha_evento)
            eventos.append({
                "NOMBRE_EVENTO": f"Sisterhood Premium {contador_eventos}",
                "FECHA_EVENTO": fecha_evento_pago,
                "COMUNIDAD": comunidad,
                "DIA_SEMANA": fecha_evento_pago.strftime("%A"),
                "DIA_SEMANA_NUM": fecha_evento_pago.weekday(),
                "DIA_MES": fecha_evento_pago.day,
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
                "BENEFICIO_ESTIMADO": ingresos - coste,
                "PRECIO_MEDIO": precio,
                "COLABORACION": generar_colaboracion(),
                "TIPO_ACTIVIDAD": generar_tipo_actividad()
            })
            contador_eventos += 1

    return pd.DataFrame(eventos)

# === EJECUCIÓN DIRECTA DEL SCRIPT
if __name__ == "__main__":
    df_simulado = generar_datos_simulados("GIRONA", "2024-01-01")
    output_path = Path("stats/datasets/simulacion_datos_girona.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_simulado.to_csv(output_path, index=False)
    print(f"✅ Dataset simulado generado con {len(df_simulado)} eventos.")
    print(f"📍 Guardado en: {output_path.resolve()}")
