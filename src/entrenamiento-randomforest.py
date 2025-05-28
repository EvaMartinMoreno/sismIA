
import pandas as pd
import numpy as np
import random
from datetime import datetime
from pathlib import Path

# Semilla para reproducibilidad
random.seed(42)
np.random.seed(42)

# Configuración
meses_totales = 60  # Generamos 5 años para cubrir desde antes de la creación hasta madurez
inicio_global = datetime(2021, 1, 1)

# Inicio real de cada comunidad
inicio_comunidad = {
    "GIRONA": pd.Timestamp("2024-01-01"),
    "ELCHE": pd.Timestamp("2025-01-01")
}

# Parámetros de eventos por mes
eventos_pago_por_mes = 1
eventos_gratuito_por_mes = 4

# Lógica de crecimiento basada en edad
def calcular_crecimiento(edad_meses):
    if edad_meses < 6:
        return 1 + 0.25
    anios = edad_meses // 12
    return 1 + 0.25 + anios * 0.005

# Generar eventos
eventos = []
contador_eventos = 1

for mes_offset in range(meses_totales):
    fecha_evento = inicio_global + pd.DateOffset(months=mes_offset)
    anio = fecha_evento.year
    mes = fecha_evento.month
    semana = int(fecha_evento.strftime("%U"))
    dia_semana = fecha_evento.strftime("%A")

    for comunidad in ["GIRONA", "ELCHE"]:
        edad_meses = (fecha_evento.year - inicio_comunidad[comunidad].year) * 12 + (fecha_evento.month - inicio_comunidad[comunidad].month)
        edad_meses = max(0, edad_meses)
        crecimiento = calcular_crecimiento(edad_meses)

        # Eventos gratuitos
        for _ in range(eventos_gratuito_por_mes):
            asistentes = int(np.random.normal(loc=20 * crecimiento, scale=3))
            asistentes = max(1, asistentes)
            inscritas = asistentes + random.randint(1, 5)
            nombre = f"Sisterhood Free {contador_eventos}"
            eventos.append({
                "NOMBRE_EVENTO": nombre,
                "FECHA_EVENTO": fecha_evento,
                "COMUNIDAD": comunidad,
                "DIA_SEMANA": dia_semana,
                "MES": mes,
                "SEMANA": semana,
                "NUM_INSCRITAS": inscritas,
                "NUM_PAGOS": 0,
                "NUM_ASISTENCIAS": asistentes,
                "TOTAL_RECAUDADO": 0.0,
                "EVENTO_GRATUITO": True,
                "TIPO_EVENTO": "gratuito",
                "COSTE_ESTIMADO": 0.0,
                "BENEFICIO_ESTIMADO": 0.0
            })
            contador_eventos += 1

        # Evento de pago
        asistentes = int(np.random.normal(loc=40 * crecimiento, scale=5))
        asistentes = max(5, asistentes)
        inscritas = asistentes + random.randint(2, 8)
        precio = round(random.uniform(10, 20), 2)
        ingresos = asistentes * precio
        coste = round(random.uniform(100, 250), 2)
        beneficio = ingresos - coste
        nombre = f"Sisterhood Premium {contador_eventos}"
        eventos.append({
            "NOMBRE_EVENTO": nombre,
            "FECHA_EVENTO": fecha_evento,
            "COMUNIDAD": comunidad,
            "DIA_SEMANA": dia_semana,
            "MES": mes,
            "SEMANA": semana,
            "NUM_INSCRITAS": inscritas,
            "NUM_PAGOS": asistentes,
            "NUM_ASISTENCIAS": asistentes,
            "TOTAL_RECAUDADO": ingresos,
            "EVENTO_GRATUITO": False,
            "TIPO_EVENTO": "pago",
            "COSTE_ESTIMADO": coste,
            "BENEFICIO_ESTIMADO": beneficio
        })
        contador_eventos += 1

# Crear DataFrame y guardar
df = pd.DataFrame(eventos)
output_path = Path(__file__).parent / "eventos_simulados_sisterhood.csv"
df.to_csv(output_path, index=False)
print(f"✅ CSV generado en: {output_path}")

# Resumen estadístico por comunidad
print("\n📊 RESUMEN ESTADÍSTICO POR COMUNIDAD")
for comunidad in df["COMUNIDAD"].unique():
    df_com = df[df["COMUNIDAD"] == comunidad]
    print(f"\n🔹 Comunidad: {comunidad}")
    print("- Total de eventos:", len(df_com))
    print("- Eventos por tipo:")
    print(df_com["TIPO_EVENTO"].value_counts())
    print("- Media de asistentes por tipo:")
    print(df_com.groupby("TIPO_EVENTO")["NUM_ASISTENCIAS"].mean())
    print("- Media de beneficio por tipo:")
    print(df_com.groupby("TIPO_EVENTO")["BENEFICIO_ESTIMADO"].mean())
    print("- Beneficio total estimado:", round(df_com["BENEFICIO_ESTIMADO"].sum(), 2))
