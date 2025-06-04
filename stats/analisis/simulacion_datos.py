import pandas as pd
import numpy as np
import random
from datetime import datetime
from pathlib import Path

# Semilla
random.seed(42)
np.random.seed(42)

# === FUNCIONES DE CRECIMIENTO ===
def calcular_crecimiento_generico(edad_meses):
    return max(1, 1 + 0.25 + (edad_meses // 12) * 0.005)

def calcular_crecimiento_con_ruido(edad_meses: int) -> int:
    if edad_meses < 3:
        pendiente = 1.1; intercepto = 18.0; ruido = 2.3
    elif 3 <= edad_meses < 6:
        pendiente = 1.3; intercepto = 17.5; ruido = 3.0
    elif 10 <= edad_meses <= 11:
        pendiente = 0.9; intercepto = 17.0; ruido = 3.0
    elif 11 < edad_meses <= 13:
        pendiente = 0.7; intercepto = 14.0; ruido = 3.5
    else:
        pendiente = 1.7; intercepto = 14.5; ruido = 5.5

    valor_base = intercepto + pendiente * edad_meses
    valor = np.random.normal(loc=valor_base, scale=ruido)
    return max(5, int(round(valor)))

# === TEMPORADA
def obtener_temporada(mes):
    if mes in [12, 1, 2]:
        return "invierno"
    elif mes in [3, 4, 5]:
        return "primavera"
    elif mes in [6, 7, 8]:
        return "verano"
    else:
        return "otoño"

# === GENERADOR DE DATOS
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
            crecimiento = calcular_crecimiento_generico(edad_meses)
            asistentes = int(np.random.normal(loc=20 * crecimiento, scale=3))
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
                "COLABORACION": 0,
                "TIPO_ACTIVIDAD": "deportiva"
            })
            contador_eventos += 1

        # DE PAGO
        for _ in range(eventos_pago_por_mes):
            if comunidad.upper() == "GIRONA":
                asistentes = calcular_crecimiento_con_ruido(edad_meses)
            else:
                crecimiento = calcular_crecimiento_generico(edad_meses)
                asistentes = int(np.random.normal(loc=40 * crecimiento, scale=5))

            asistentes = max(5, asistentes)
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
                "COLABORACION": 0,
                "TIPO_ACTIVIDAD": "deportiva"
            })
            contador_eventos += 1

    return pd.DataFrame(eventos)

# === GENERACIÓN FINAL
df_simulado = generar_datos_simulados("GIRONA", "2024-01-01")

output_path = Path("stats") / "datasets" / "simulacion_datos_girona.csv"
output_path.parent.mkdir(parents=True, exist_ok=True)
df_simulado.to_csv(output_path, index=False)
print(f"✅ Dataset simulado generado con {len(df_simulado)} eventos.")
print(f"📍 Guardado en: {output_path}")
