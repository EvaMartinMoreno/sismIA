import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, timedelta

# ---------- FUNCIONES AUXILIARES ----------
def cargar_datos():
    df = pd.read_csv("data/proceed/carreras_unificadas.csv", parse_dates=["fecha_datetime"])
    return df

def obtener_eventos_mes(df, year, month):
    return df[(df["fecha_datetime"].dt.year == year) & (df["fecha_datetime"].dt.month == month)]

def generar_tabla_calendario(df_mes, year, month):
    cal = calendar.Calendar(firstweekday=0)
    semanas = cal.monthdatescalendar(year, month)

    tabla = ""  # Usamos HTML dentro del markdown
    tabla += "<table style='width: 100%; border-collapse: collapse;'>"
    tabla += "<tr>" + "".join(f"<th style='border: 1px solid #ccc; padding: 6px;'>{dia}</th>" for dia in ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]) + "</tr>"

    for semana in semanas:
        tabla += "<tr>"
        for dia in semana:
            if dia.month != month:
                tabla += "<td style='border: 1px solid #ccc; background-color: #f0f0f0; padding: 6px; vertical-align: top;'></td>"
                continue
            eventos = df_mes[df_mes["fecha_datetime"].dt.date == dia]
            eventos_html = "".join(f"<li style='font-size: 0.75rem;'>{row['nombre_evento'][:25]}</li>" for _, row in eventos.iterrows())
            tabla += f"<td style='border: 1px solid #ccc; padding: 6px; vertical-align: top;'><strong>{dia.day}</strong><ul>{eventos_html}</ul></td>"
        tabla += "</tr>"
    tabla += "</table>"
    return tabla

# ---------- INTERFAZ STREAMLIT ----------
st.set_page_config(page_title="Calendario de Carreras", layout="wide")
st.title("🏃‍♀️ Calendario de Carreras")

# Estado para mes y año si no existe aún
if "mes_actual" not in st.session_state:
    hoy = datetime.today()
    st.session_state.mes_actual = hoy.month
    st.session_state.año_actual = hoy.year

# Controles para cambiar de mes
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("⬅️ Mes anterior"):
        st.session_state.mes_actual -= 1
        if st.session_state.mes_actual < 1:
            st.session_state.mes_actual = 12
            st.session_state.año_actual -= 1

with col3:
    if st.button("Mes siguiente ➡️"):
        st.session_state.mes_actual += 1
        if st.session_state.mes_actual > 12:
            st.session_state.mes_actual = 1
            st.session_state.año_actual += 1

mes = st.session_state.mes_actual
año = st.session_state.año_actual

st.subheader(f"📅 {calendar.month_name[mes]} {año}")

# Carga de datos
df = cargar_datos()
df_mes = obtener_eventos_mes(df, año, mes)

# Calendario HTML
calendario_html = generar_tabla_calendario(df_mes, año, mes)
st.markdown(calendario_html, unsafe_allow_html=True)

# Mostrar eventos detallados opcionalmente
with st.expander("📋 Ver lista completa de carreras del mes"):
    st.dataframe(df_mes[["fecha_datetime", "nombre_evento", "localidad", "tipo", "distancia_km", "fuente"]].sort_values("fecha_datetime"))