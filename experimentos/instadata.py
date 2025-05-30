import pandas as pd
import os

def cargar_métricas_instagram():
    ruta = os.path.join(os.path.dirname(__file__), "..", "data", "user_insights.csv")
    
    if not os.path.exists(ruta):
        return {"seguidores": "—", "nuevos": "—"}

    df = pd.read_csv(ruta)
    df_followers = df[df["metric"] == "followers_count"].sort_values("timestamp", ascending=False)

    if df_followers.shape[0] < 2:
        return {
            "seguidores": df_followers["value"].iloc[0] if not df_followers.empty else "—",
            "nuevos": "—"
        }

    seguidores_hoy = df_followers["value"].iloc[0]
    seguidores_ayer = df_followers["value"].iloc[1]
    nuevos = seguidores_hoy - seguidores_ayer

    return {
        "seguidores": seguidores_hoy,
        "nuevos": f"{nuevos:+}"
    }
