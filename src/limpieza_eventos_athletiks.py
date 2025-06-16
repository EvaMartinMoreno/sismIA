from pathlib import Path
import pandas as pd
import numpy as np
import unicodedata
import os
import csv
import re
from datetime import datetime

def limpiar_evento(nombre):
    nombre = str(nombre).strip().lower()
    nombre = unicodedata.normalize('NFKD', nombre).encode('ascii', errors='ignore').decode('utf-8')
    return nombre

def obtener_temporada(mes):
    return ["invierno", "primavera", "verano", "otoño"][(mes % 12) // 3]

def extraer_fecha_desde_nombre(nombre_archivo):
    nombre_archivo = nombre_archivo.lower()

    # Correcciones previas para errores comunes que impiden detectar fechas
    errores_comunes = {
        "dabril": "de abril",
        "doctubre": "de octubre",
        "dmarc": "de marc",
        "dmaig": "de maig",
        "dfebrer": "de febrer",
        "dsetembre": "de setembre"
        # Añadir aquí más si aparecen otros errores similares
    }

    for error, correccion in errores_comunes.items():
        nombre_archivo = nombre_archivo.replace(error, correccion)

    # Diccionario de meses en catalán y castellano
    meses = {
        "gener": "01", "febrer": "02", "marc": "03", "abril": "04", "maig": "05", "juny": "06", "juliol": "07",
        "agost": "08", "setembre": "09", "octubre": "10", "novembre": "11", "desembre": "12",
        "enero": "01", "febrero": "02", "marzo": "03", "abril": "04", "mayo": "05", "junio": "06", "julio": "07",
        "agosto": "08", "septiembre": "09", "noviembre": "11", "diciembre": "12"
    }

    # RegEx flexible para fechas con de/del o incluso errores corregidos
    patron = r"(\d{1,2})[- ]+de[- ]+(%s)[- ]+(?:de|del)[- ]+(\d{4})" % "|".join(meses.keys())
    match = re.search(patron, nombre_archivo)

    if match:
        dia, mes_literal, anio = match.groups()
        mes = meses.get(mes_literal)
        try:
            return pd.to_datetime(f"{anio}-{mes}-{dia}", errors="coerce")
        except:
            return pd.NaT
    return pd.NaT

def extraer_nombre_evento_desde_archivo(nombre_archivo):
    nombre = Path(nombre_archivo).stem
    nombre = unicodedata.normalize('NFKD', nombre).encode('ascii', errors='ignore').decode('utf-8')
    nombre = nombre.replace('-', ' ')
    nombre = nombre.lower()
    nombre = re.split(r"\d", nombre)[0]  # corta en el primer digito (evita pillar la fecha)
    nombre = nombre.strip().upper()
    return nombre

def cargar_csvs_en_uno(directorio):
    archivos = list(Path(directorio).rglob("*.csv"))
    dfs = []
    errores = []
    procesados = []

    for archivo in archivos:
        try:
            df = pd.read_csv(
                archivo,
                sep=",",
                engine="python",
                on_bad_lines="skip",
                quoting=csv.QUOTE_NONE
            )
            fecha_evento = extraer_fecha_desde_nombre(archivo.name)
            if pd.isna(fecha_evento):
                errores.append((archivo.name, "FECHA_EVENTO no pudo ser extraída del nombre"))
                continue

            df["ARCHIVO_ORIGEN"] = archivo.name
            df["FECHA_EVENTO"] = fecha_evento
            df["NOMBRE_EVENTO"] = extraer_nombre_evento_desde_archivo(archivo.name)

            # Comunidad: Girona o Elche según carpeta o nombre
            comunidad = "GIRONA" if "girona" in str(archivo).lower() else "ELCHE"
            if comunidad == "GIRONA" and ("elche" in archivo.name.lower() or "jueves" in archivo.name.lower()):
                comunidad = "ELCHE"
            df["COMUNIDAD"] = comunidad

            dfs.append(df)
            procesados.append(archivo.name)
        except Exception as e:
            errores.append((archivo.name, str(e)))

    if not dfs:
        raise ValueError("No se pudieron leer archivos válidos.")
    return pd.concat(dfs, ignore_index=True), errores, procesados

def generar_dataset_modelo(input_dir, output_path):
    df_raw, errores, procesados = cargar_csvs_en_uno(input_dir)

    columnas_obligatorias = ["PAGO", "PRECIO_PAGADO", "ASISTENTE", "NOMBRE_EVENTO", "COMUNIDAD"]
    for col in columnas_obligatorias:
        if col not in df_raw.columns:
            print(f"⚠️ Columna faltante en los datos: {col} — se completará con valores por defecto.")
            if col in ["PAGO", "PRECIO_PAGADO"]:
                df_raw[col] = 0
            elif col == "ASISTENTE":
                df_raw[col] = ""
            else:
                df_raw[col] = np.nan

    df_raw["PAGO"] = pd.to_numeric(df_raw["PAGO"], errors="coerce").fillna(0).astype(int)
    df_raw["ASISTENCIA"] = np.where(
        (df_raw["FECHA_EVENTO"] < pd.Timestamp.today()) & (df_raw["ARCHIVO_ORIGEN"].str.contains("pending", case=False)),
        np.random.choice([0, 1], size=len(df_raw), p=[0.2, 0.8]),
        1
    ).astype(int)

    df_raw["PRECIO_PAGADO"] = pd.to_numeric(df_raw["PRECIO_PAGADO"], errors="coerce").fillna(0)

    df = df_raw.groupby(
        ["NOMBRE_EVENTO", "FECHA_EVENTO", "COMUNIDAD", "ARCHIVO_ORIGEN"], as_index=False
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

    df["DIA_MES"] = df["FECHA_EVENTO"].dt.day
    df["SEMANA_MES_AÑO"] = df["FECHA_EVENTO"].dt.isocalendar().week
    df["SEMANA_DENTRO_DEL_MES"] = (df["FECHA_EVENTO"].dt.day - 1) // 7 + 1
    df["MES"] = df["FECHA_EVENTO"].dt.month
    df["DIA_SEMANA"] = df["FECHA_EVENTO"].dt.day_name()
    df["AÑO"] = df["FECHA_EVENTO"].dt.year
    df["DIA_SEMANA_NUM"] = df["FECHA_EVENTO"].dt.dayofweek
    df["TEMPORADA"] = df["MES"].apply(obtener_temporada)
    df["PRECIO_MEDIO"] = np.where(df["NUM_PAGOS"] > 0, df["TOTAL_RECAUDADO"] / df["NUM_PAGOS"], 0)
    df["EVENTO_GRATUITO"] = np.where(df["PRECIO_MEDIO"] == 0, 1, 0)
    df["TIPO_EVENTO"] = np.where(df["EVENTO_GRATUITO"] == 1, "gratuito", "pago")

    columnas_manuales = ["COSTE_UNITARIO", "COSTE_UNITARIO_VALIDADO", "COLABORACION", "TIPO_ACTIVIDAD"]
    ruta_eventos_crudos = "data/raw/athletiks/eventos_crudos_unificados.csv"
    if os.path.exists(ruta_eventos_crudos):
        try:
            df_validados = pd.read_csv(ruta_eventos_crudos)
            df_validados = df_validados.drop_duplicates(subset=["NOMBRE_EVENTO", "FECHA_EVENTO"])
            df = pd.merge(
                df,
                df_validados[["NOMBRE_EVENTO", "FECHA_EVENTO"] + columnas_manuales],
                on=["NOMBRE_EVENTO", "FECHA_EVENTO"],
                how="left"
            )
        except Exception as e:
            print(f"⚠️ Error leyendo datos validados: {e}")
            for col in columnas_manuales:
                df[col] = np.nan if "COSTE" in col or "COLAB" in col else ""
    else:
        for col in columnas_manuales:
            df[col] = np.nan if "COSTE" in col or "COLAB" in col else ""

    df["BENEFICIO"] = df["NUM_ASISTENCIAS"] * (df["PRECIO_MEDIO"] - df["COSTE_UNITARIO"].fillna(0))

    df.to_csv(output_path, index=False)
    print(f"\n✅ Dataset generado correctamente con {len(df)} eventos.")
    print(f"📁 Guardado en: {output_path}")

    todos = sorted([archivo.name for archivo in Path(input_dir).rglob("*.csv")])
    procesados_set = set(procesados)
    no_procesados = [a for a in todos if a not in procesados_set]

    print("\n📊 VALIDACIÓN FINAL")
    print(f"📁 Total de archivos en carpeta: {len(todos)}")
    print(f"✅ Archivos procesados correctamente: {len(procesados)}")
    print(f"❌ Archivos no procesados: {len(no_procesados)}")

    if errores:
        print("\n⚠️ Archivos con error:")
        for archivo, motivo in errores:
            print(f" - {archivo}: {motivo}")
    else:
        print("🎉 Todos los archivos fueron leídos correctamente.")

if __name__ == "__main__":
    generar_dataset_modelo(
        input_dir="data/raw/athletiks",
        output_path="data/raw/dataset_modelo.csv"
    )
