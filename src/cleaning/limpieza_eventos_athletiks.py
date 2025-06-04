from pathlib import Path
import pandas as pd
import numpy as np
import unicodedata

def limpiar_evento(nombre):
    nombre = str(nombre).strip().lower()
    nombre = unicodedata.normalize('NFKD', nombre).encode('ascii', errors='ignore').decode('utf-8')
    return nombre

def obtener_temporada(mes):
    if mes in [12, 1, 2]:
        return "invierno"
    elif mes in [3, 4, 5]:
        return "primavera"
    elif mes in [6, 7, 8]:
        return "verano"
    else:
        return "otoño"

def generar_dataset_modelo(input_path, output_path, tipos_path):
    # === 📥 Cargar datos
    df_raw = pd.read_csv(input_path, parse_dates=["FECHA_EVENTO"])

    # === 🧹 Limpieza de nulos
    df_raw["PAGO"] = pd.to_numeric(df_raw["PAGO"], errors="coerce").fillna(0).astype(int)
    df_raw["ASISTENCIA"] = np.nan
    df_raw["PRECIO_PAGADO"] = pd.to_numeric(df_raw["PRECIO_PAGADO"], errors="coerce").fillna(0)

    # === 🎯 Lógica para asistencia
    np.random.seed(42)
    eventos_pago = df_raw[df_raw["PAGO"] == 1]["NOMBRE_EVENTO"].unique()
    for i, evento in enumerate(eventos_pago):
        participantes = df_raw[(df_raw["NOMBRE_EVENTO"] == evento) & (df_raw["PAGO"] == 1)].index.tolist()
        if not participantes:
            continue
        if i % 2 == 0:
            no_asisten = np.random.choice(participantes, size=min(len(participantes), np.random.randint(1, 3)), replace=False)
            df_raw.loc[list(set(participantes) - set(no_asisten)), "ASISTENCIA"] = 1
            df_raw.loc[no_asisten, "ASISTENCIA"] = 0
        else:
            df_raw.loc[participantes,"ASISTENCIA"] = 1

    eventos_gratis = df_raw[df_raw["PAGO"] == 0]["NOMBRE_EVENTO"].unique()
    for evento in eventos_gratis:
        participantes = df_raw[df_raw["NOMBRE_EVENTO"] == evento].index.tolist()
        if not participantes:
            continue
        num_fallos = max(1, int(0.10 * len(participantes)))
        no_asisten = np.random.choice(participantes, size=min(len(participantes), num_fallos), replace=False)
        df_raw.loc[list(set(participantes) - set(no_asisten)), "ASISTENCIA"] = 1
        df_raw.loc[no_asisten, "ASISTENCIA"] = 0

    df_raw["ASISTENCIA"] = df_raw["ASISTENCIA"].fillna(0).astype(int)

    # === 🧾 Agrupación por evento
    df = df_raw.groupby(
        ["NOMBRE_EVENTO", "FECHA_EVENTO", "COMUNIDAD", "ARCHIVO_ORIGEN", "COSTE_UNITARIO"], as_index=False
    ).agg({
        "ASISTENTE": "count",
        "PAGO": "sum",
        "ASISTENCIA": "sum",
        "PRECIO_PAGADO": "sum"
    }).rename(columns={
        "ASISTENTE": "NUM_INSCRITAS",
        "PAGO": "NUM_PAGOS",
        "ASISTENCIA": "NUM_ASISTENCIAS",
        "PRECIO_PAGADO": "TOTAL_RECAUDADO"
    })

    # === 📆 Variables temporales
    df["DIA_MES"] = df["FECHA_EVENTO"].dt.day
    df["SEMANA_MES"] = df["FECHA_EVENTO"].dt.isocalendar().week
    df["MES"] = df["FECHA_EVENTO"].dt.month
    df["DIA_SEMANA"] = df["FECHA_EVENTO"].dt.day_name()
    df["AÑO"] = df["FECHA_EVENTO"].dt.year
    df["DIA_SEMANA_NUM"] = df["FECHA_EVENTO"].dt.dayofweek
    df["TEMPORADA"] = df["MES"].apply(obtener_temporada)

    # === 💸 Precio medio, costes, beneficio
    df["PRECIO_MEDIO"] = np.where(df["NUM_PAGOS"] > 0, df["TOTAL_RECAUDADO"] / df["NUM_PAGOS"], 0)
    df["COSTE_UNITARIO"] = pd.to_numeric(df["COSTE_UNITARIO"], errors="coerce")
    df["BENEFICIO_ESTIMADO"] = df["TOTAL_RECAUDADO"] - df["COSTE_ESTIMADO"]

    # === 🎯 Clasificación
    df["EVENTO_GRATUITO"] = np.where(df["PRECIO_MEDIO"] == 0, 1, 0)
    df["TIPO_EVENTO"] = np.where(df["EVENTO_GRATUITO"] == 1, "gratuito", "pago")
    df["COLABORACION"] = 0

    # === 🔠 Limpieza nombre para merge
    df["EVENTO_LIMPIO"] = df["NOMBRE_EVENTO"].apply(limpiar_evento)

    # === 📘 Cargar o crear archivo de tipos
    if tipos_path.exists():
        df_tipos = pd.read_csv(tipos_path)
        if "EVENTO_LIMPIO" not in df_tipos.columns:
            df_tipos["EVENTO_LIMPIO"] = df_tipos["EVENTO"].apply(limpiar_evento)
    else:
        df_tipos = df[["NOMBRE_EVENTO", "EVENTO_LIMPIO"]].drop_duplicates()
        df_tipos["TIPO_ACTIVIDAD"] = "otro"
        df_tipos = df_tipos.rename(columns={"NOMBRE_EVENTO": "EVENTO"})
        df_tipos.to_csv(tipos_path, index=False)
        print(f"📄 Archivo creado automáticamente: {tipos_path.resolve()}")
        print("✍️ Rellena manualmente la columna 'TIPO_ACTIVIDAD' con: almuerzo, charla, deportiva, ludica, only run, otro")

    df = df.merge(df_tipos[["EVENTO_LIMPIO", "TIPO_ACTIVIDAD"]], on="EVENTO_LIMPIO", how="left")
    df["TIPO_ACTIVIDAD"] = df["TIPO_ACTIVIDAD"].fillna("otro")
    df.drop(columns=["EVENTO_LIMPIO"], inplace=True)

    # === 💾 Guardar
    df.to_csv(output_path, index=False)
    print(f"✅ Dataset generado correctamente con {len(df)} eventos.")
    print(f"📍 Guardado en: {output_path}")

if __name__ == "__main__":
    generar_dataset_modelo(
        input_path=Path("data/clean/eventos_crudos_unificados.csv"),
        output_path=Path("data/clean/dataset_modelo.csv"),
        tipos_path=Path("data/entrada/tipos_evento.csv")
    )
