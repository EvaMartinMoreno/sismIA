import requests
import time
import pandas as pd
import os
from datetime import datetime

# Reemplaza con tu token válido (¡esto caduca! puedes usar dotenv luego)
ACCESS_TOKEN = "EAAJg1EXrT80BO9zZBtaBazG4jmt3jIA551zZCs8qTTNHUbxMqinXctSMbqopfRE0nmQ2cJThlFyls62ZB89qAhXYU910cpGupsbNL90dAnSDIUfXDnD6Ow1volYZBRnZCkrpkwhNhuxrZBNrPWxStUU5VXWLo96XnDrZBiZCQVODEm5EMieAhNs8c8DybSkDouzIHfa6UFudYZAASSPAZD"
IG_USER_ID = "17841458252704780"  # Instagram Business Account ID
API_VERSION = "v22.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

DATA_DIR = "data"
USER_CSV = os.path.join(DATA_DIR, "user_insights.csv")
MEDIA_CSV = os.path.join(DATA_DIR, "media_insights.csv")

USER_METRICS = ["profile_views", "accounts_engaged", "total_interactions"]

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def get_follower_count():
    url = f"{BASE_URL}/{IG_USER_ID}"
    params = {"fields": "followers_count", "access_token": ACCESS_TOKEN}
    res = requests.get(url, params=params)
    if res.status_code == 200:
        return {
            "timestamp": datetime.now().isoformat(),
            "metric": "followers_count",
            "dimension": "total",
            "value": res.json().get("followers_count")
        }
    else:
        print("❌ Error en followers_count:", res.status_code, res.text)
        return None

def get_user_insights():
    url = f"{BASE_URL}/{IG_USER_ID}/insights"
    params = {
        "metric": ",".join(USER_METRICS),
        "period": "day",
        "metric_type": "total_value",
        "access_token": ACCESS_TOKEN
    }
    res = requests.get(url, params=params)
    if res.status_code == 200:
        return res.json().get("data", [])
    else:
        print("❌ Error en user insights:", res.status_code, res.text)
        return []

def save_user_insights(followers_record, insights_data):
    rows = []
    if followers_record:
        rows.append(followers_record)

    for metric in insights_data:
        for value in metric.get("values", []):
            rows.append({
                "timestamp": datetime.now().isoformat(),
                "metric": metric["name"],
                "dimension": "total",
                "value": value["value"]
            })

    df_new = pd.DataFrame(rows)

    if os.path.exists(USER_CSV) and os.path.getsize(USER_CSV) > 0:
        df_old = pd.read_csv(USER_CSV)
        df = pd.concat([df_old, df_new]).drop_duplicates()
    else:
        df = df_new

    df.to_csv(USER_CSV, index=False)
    print(f"✅ Guardado en {USER_CSV} ({len(df_new)} nuevas filas)")

def get_recent_media(limit=10):
    url = f"{BASE_URL}/{IG_USER_ID}/media"
    params = {
        "fields": "id,caption,timestamp,media_type,permalink",
        "access_token": ACCESS_TOKEN,
        "limit": limit
    }
    res = requests.get(url, params=params)
    if res.status_code == 200:
        return res.json().get("data", [])
    else:
        print("❌ Error en media:", res.status_code, res.text)
        return []

def save_media_insights(media_records):
    if not media_records:
        print("⚠ No hay datos de publicaciones para guardar.")
        return

    df_new = pd.DataFrame(media_records)

    # Evitar error por archivo vacío o sin columnas
    if os.path.exists(MEDIA_CSV) and os.path.getsize(MEDIA_CSV) > 0:
        try:
            df_old = pd.read_csv(MEDIA_CSV)
            df = pd.concat([df_old, df_new]).drop_duplicates()
        except pd.errors.EmptyDataError:
            print("⚠ Archivo existente pero vacío. Se sobrescribirá.")
            df = df_new
    else:
        df = df_new

    df.to_csv(MEDIA_CSV, index=False)
    print(f"✅ Guardado en {MEDIA_CSV} ({len(df_new)} nuevas filas)")

def run_combined_tracker():
    while True:
        print(f"\n🚀 Ejecutando ciclo: {datetime.now().isoformat()}")
        ensure_data_dir()

        print("📊 Métricas del perfil...")
        followers = get_follower_count()
        user_insights = get_user_insights()
        save_user_insights(followers, user_insights)

        print("📸 Métricas de publicaciones...")
        media = get_recent_media(limit=10)
        media_rows = []

        for item in media:
            media_id = item["id"]
            media_type = item["media_type"]

            # Selección de métricas válidas por tipo
            if media_type == "IMAGE":
                valid_metrics = ["reach", "saved", "likes", "comments", "shares", "views", "total_interactions"]
            elif media_type == "VIDEO":
                valid_metrics = ["reach", "saved", "likes", "comments", "shares", "video_views", "views", "total_interactions"]
            elif media_type == "CAROUSEL_ALBUM":
                valid_metrics = ["reach", "saved", "likes", "comments", "shares", "total_interactions"]
            else:
                print(f"⚠ Tipo de media no soportado: {media_type}")
                continue

            url = f"{BASE_URL}/{media_id}/insights"
            params = {
                "metric": ",".join(valid_metrics),
                "access_token": ACCESS_TOKEN
            }

            res = requests.get(url, params=params)
            if res.status_code != 200:
                print(f"❌ Error en media {media_id}: {res.status_code} {res.text}")
                continue

            insights = res.json().get("data", [])
            for metric in insights:
                media_rows.append({
                    "media_id": media_id,
                    "timestamp": item["timestamp"],
                    "media_type": media_type,
                    "permalink": item["permalink"],
                    "metric": metric["name"],
                    "value": metric["values"][0]["value"],
                    "collected_at": datetime.now().isoformat()
                })

        save_media_insights(media_rows)

        print("⏳ Esperando 12 horas...\n")
        time.sleep(12 * 60 * 60)

if __name__ == "__main__":
    run_combined_tracker()