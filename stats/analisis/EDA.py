import pandas as pd

def analizar_distribuciones_eventos_real(csv_path = r"C:\Users\eva\Documents\TU_RUTA_COMPLETA_HASTA\dataset_modelo.csv"
) -> dict:
    """
    Analiza la distribución real de eventos de pago en Girona.
    Devuelve los diccionarios con pesos para DIA_SEMANA_NUM y SEMANA_MES,
    que pueden usarse luego para generar eventos simulados realistas.
    """

    # === Cargar datos
    df = pd.read_csv(csv_path)

    # === Normalización básica
    df["COMUNIDAD"] = df["COMUNIDAD"].str.strip().str.upper()
    df["TIPO_EVENTO"] = df["TIPO_EVENTO"].str.strip().str.lower()

    # === Filtrar solo eventos REALES, DE PAGO, en GIRONA
    df_reales = df[
        (df["COMUNIDAD"] == "GIRONA") &
        (df["TIPO_EVENTO"] == "pago") &
        (df["ES_REAL"] == 1)
    ].copy()

    if df_reales.empty:
        print("⚠️ No se encontraron eventos reales de pago en Girona.")
        return {}

    # === Distribución real de días de la semana
    dias_semana = df_reales["DIA_SEMANA_NUM"].value_counts(normalize=True).sort_index()
    pesos_dia_semana = dias_semana.to_dict()

    # === Distribución real de número de semana del mes
    semanas_mes = df_reales["SEMANA_MES"].value_counts(normalize=True).sort_index()
    pesos_semana_mes = semanas_mes.to_dict()

    # === Mostrar resultados
    print("📅 Distribución real de DIA_SEMANA_NUM (%):")
    print(dias_semana)

    print("\n📅 Distribución real de SEMANA_MES (%):")
    print(semanas_mes)

    print("\n🎯 Diccionario para simulación - DIA_SEMANA_NUM:")
    print(pesos_dia_semana)

    print("\n🎯 Diccionario para simulación - SEMANA_MES:")
    print(pesos_semana_mes)

    return {
        "pesos_dia_semana": pesos_dia_semana,
        "pesos_semana_mes": pesos_semana_mes
    }

# === EJECUCIÓN DIRECTA DEL SCRIPT
if __name__ == "__main__":
    pesos = analizar_distribuciones_eventos_real("dataset_modelo.csv")
