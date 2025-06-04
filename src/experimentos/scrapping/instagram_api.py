import requests
import time
import pandas as pd
import os
from datetime import datetime

# Reemplaza con tu token válido
ACCESS_TOKEN = "EAAJg1EXrT80BO42KgisKKLP5gqsKmtn6VUsL7PZCnra3uZCDtlMfTTvW4Lsxlq0PWNlyz1hMpL2rZB2k3QZCkpNSJVe3UATadn7725xc4w869ZCqQ4Uj20mqjjb4fWR81i9LrAxmkvzQqgdvW0oAcjwmSZC9b53s7jHxPQ4vSUujRgBeYOXgZDZD"
IG_USER_ID = "17841458252704780"
API_VERSION = "v22.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

DATA_DIR = "data"
USER_CSV = os.path.join(DATA_DIR, "user_insights.csv")
MEDIA_CSV = os.path.join(DATA_DIR, "media_insights.csv")

USER_METRICS = ["profile_views", "accounts_engaged", "total_interactions"]

def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

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

if __name__ == "__main__":
    print("📊 Probar consulta directa de métricas...")
    data = get_user_insights()
    for item in data:
        print(f"\n🔍 MÉTRICA: {item.get('name')}")
        print("🔧 DATOS COMPLETOS:", item)

def save_user_insights(followers_record, insights_data):
    rows = []
    if followers_record:
        rows.append(followers_record)

    for metric in insights_data:
        if "values" in metric:
            for value in metric.get("values", []):
                rows.append({
                    "timestamp": datetime.now().isoformat(),
                    "metric": metric["name"],
                    "dimension": "total",
                    "value": value["value"]
                })
        elif "total_value" in metric:
            rows.append({
                "timestamp": datetime.now().isoformat(),
                "metric": metric["name"],
                "dimension": "total",
                "value": metric["total_value"]["value"]
            })

    df_new = pd.DataFrame(rows)

    try:
        if os.path.exists(USER_CSV) and os.path.getsize(USER_CSV) > 0:
            df_old = pd.read_csv(USER_CSV)
            df = pd.concat([df_old, df_new]).drop_duplicates(subset=["timestamp", "metric"], keep="last")
        else:
            df = df_new
    except pd.errors.EmptyDataError:
        print("⚠ Archivo user_insights.csv está vacío. Se sobrescribirá.")
        df = df_new
    df.to_csv(USER_CSV, index=False)
    print(f"✅ Guardado en {USER_CSV} ({len(df_new)} nuevas filas)")

def get_recent_media(limit=20):
    last_timestamp = None
    if os.path.exists(MEDIA_CSV):
        try:
            df_old = pd.read_csv(MEDIA_CSV)
            last_timestamp = pd.to_datetime(df_old["timestamp"]).max()
        except:
            pass

    url = f"{BASE_URL}/{IG_USER_ID}/media"
    params = {
        "fields": "id,caption,timestamp,media_type,permalink,media_url",
        "access_token": ACCESS_TOKEN,
        "limit": limit
    }
    res = requests.get(url, params=params)

    if res.status_code != 200:
        print("❌ Error en media:", res.status_code, res.text)
        return []

    data = res.json().get("data", [])

    new_posts = []
    for post in data:
        post_time = pd.to_datetime(post["timestamp"])
        if last_timestamp is None or post_time > last_timestamp:
            new_posts.append(post)  # mantenemos todos los campos como media_url, etc.

    return new_posts

def save_media_insights(media_records):
    if not media_records:
        print("⚠ No hay datos de publicaciones para guardar.")
        return

    df_new = pd.DataFrame(media_records)

    if os.path.exists(MEDIA_CSV) and os.path.getsize(MEDIA_CSV) > 0:
        try:
            df_old = pd.read_csv(MEDIA_CSV)
            df = pd.concat([df_old, df_new]).drop_duplicates(subset=["media_id", "metric", "collected_at"], keep="last")
        except pd.errors.EmptyDataError:
            print("⚠ Archivo existente pero vacío. Se sobrescribirá.")
            df = df_new
    else:
        df = df_new

    df.to_csv(MEDIA_CSV, index=False)
    print(f"✅ Guardado en {MEDIA_CSV} ({len(df_new)} nuevas filas)")

def run_actualizacion_unica():
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

        if media_type not in ["IMAGE", "VIDEO", "CAROUSEL_ALBUM"]:
            print(f"⚠ Tipo de media no soportado: {media_type}")
            continue

        valid_metrics = ["reach", "saved", "likes", "comments", "shares", "total_interactions"]

        url = f"{BASE_URL}/{media_id}/insights"
        params = {
            "metric": ",".join(valid_metrics),
            "access_token": ACCESS_TOKEN
        }

        try:
            time.sleep(0.3)
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
                    "media_url": item.get("media_url", ""),  
                    "permalink": item["permalink"],
                    "metric": metric["name"],
                    "value": metric["values"][0]["value"],
                    "collected_at": datetime.now().isoformat()
                })

        except requests.exceptions.ConnectionError as e:
            print(f"❌ Conexión abortada para media {media_id}: {e}")
            continue

    save_media_insights(media_rows)

if __name__ == "__main__":
    run_actualizacion_unica()
