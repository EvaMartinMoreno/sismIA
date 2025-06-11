from __future__ import annotations
import os
import time
import tempfile
import datetime as dt
from pathlib import Path
from typing import List, Dict, Any
import requests
import pandas as pd
from dotenv import load_dotenv
from PIL import Image
import pytesseract
import instaloader

# ---------------------------------------------------------------------------
# 0. Configuración
# ---------------------------------------------------------------------------
load_dotenv()

ACCESS_TOKEN: str | None = os.getenv("IG_ACCESS_TOKEN")
IG_USER_ID: str | None = os.getenv("IG_USER_ID")
IG_USERNAME: str | None = os.getenv("IG_USERNAME")
IG_PASSWORD: str | None = os.getenv("IG_PASSWORD")
TARGET_PROFILE: str = os.getenv("TARGET_PROFILE") or (IG_USERNAME or "")

if not all([ACCESS_TOKEN, IG_USER_ID, IG_USERNAME, IG_PASSWORD]):
    raise SystemExit("❌ Faltan variables en .env (IG_ACCESS_TOKEN, IG_USER_ID, IG_USERNAME, IG_PASSWORD)")

API_VERSION = "v22.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

DATA_DIR = Path("data/raw/instagram")
DATA_DIR.mkdir(parents=True, exist_ok=True)
USER_CSV = DATA_DIR / "user_insights.csv"
MEDIA_CSV = DATA_DIR / "media_insights.csv"
POST_CSV = DATA_DIR / "insta_posts.csv"

USER_METRICS: List[str] = ["profile_views", "accounts_engaged", "total_interactions"]
POST_METRICS: List[str] = ["reach", "saved", "likes", "comments", "shares", "total_interactions"]

# ---------------------------------------------------------------------------
# 1. Utilidades básicas
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc).isoformat()


def _request_json(url: str, params: Dict[str, Any], label: str) -> Dict[str, Any] | None:
    """Wrapper sencillo con manejo de errores y timeout."""
    try:
        res = requests.get(url, params=params, timeout=30)
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ {label}: {e}")
        return None


def _append_csv(path: Path, df_new: pd.DataFrame, subset: List[str]) -> None:
    """Concatena df_new a path evitando duplicados por subset."""
    if path.exists() and path.stat().st_size > 0:
        try:
            df_old = pd.read_csv(path)
            df = pd.concat([df_old, df_new]).drop_duplicates(subset=subset, keep="last")
        except pd.errors.EmptyDataError:
            df = df_new
    else:
        df = df_new
    df.to_csv(path, index=False)
    print(f"✅ Guardado {len(df_new)} filas en {path}")

# ---------------------------------------------------------------------------
# 2. Graph API helpers
# ---------------------------------------------------------------------------

def get_follower_count() -> dict | None:
    url = f"{BASE_URL}/{IG_USER_ID}"
    data = _request_json(url, {"fields": "followers_count", "access_token": ACCESS_TOKEN}, "followers_count")
    if data and "followers_count" in data:
        return {
            "timestamp": _now_iso(),
            "metric": "followers_count",
            "dimension": "total",
            "value": data["followers_count"],
        }
    return None


def get_user_insights() -> List[dict]:
    url = f"{BASE_URL}/{IG_USER_ID}/insights"
    params = {
        "metric": ",".join(USER_METRICS),
        "period": "day",
        "metric_type": "total_value",
        "access_token": ACCESS_TOKEN,
    }
    data = _request_json(url, params, "user_insights")
    return data.get("data", []) if data else []


def get_recent_media(limit: int = 20) -> List[dict]:
    """Devuelve posts más recientes que los ya guardados en MEDIA_CSV."""
    last_ts: dt.datetime | None = None
    if MEDIA_CSV.exists():
        try:
            last_ts = pd.to_datetime(pd.read_csv(MEDIA_CSV)["timestamp"]).max()
        except Exception:
            pass

    url = f"{BASE_URL}/{IG_USER_ID}/media"
    params = {
        "fields": "id,caption,timestamp,media_type,permalink,media_url",
        "access_token": ACCESS_TOKEN,
        "limit": limit,
    }
    data = _request_json(url, params, "media")
    if not data:
        return []

    posts = []
    for p in data.get("data", []):
        ts = pd.to_datetime(p["timestamp"])
        if last_ts is None or ts > last_ts:
            posts.append(p)
    return posts


def collect_media_insights(posts: List[dict]) -> List[dict]:
    results = []
    for item in posts:
        media_id = item["id"]
        url = f"{BASE_URL}/{media_id}/insights"
        params = {"metric": ",".join(POST_METRICS), "access_token": ACCESS_TOKEN}
        time.sleep(0.3)  # throttle
        data = _request_json(url, params, f"media {media_id}")
        if not data:
            continue
        for metric in data.get("data", []):
            results.append({
                "media_id": media_id,
                "timestamp": item["timestamp"],
                "media_type": item["media_type"],
                "media_url": item.get("media_url", ""),
                "permalink": item["permalink"],
                "metric": metric["name"],
                "value": metric["values"][0]["value"],
                "collected_at": _now_iso(),
            })
    return results

# ---------------------------------------------------------------------------
# 3. Instaloader + OCR
# ---------------------------------------------------------------------------

def _init_instaloader() -> instaloader.Instaloader:
    L = instaloader.Instaloader(
        download_pictures=True,
        download_video_thumbnails=False,
        save_metadata=False,
        quiet=True,
    )
    L.login(IG_USERNAME, IG_PASSWORD)
    return L


def collect_post_text(limit: int | None = None) -> List[dict]:
    """Descarga caption, alt‑text y OCR del TARGET_PROFILE."""
    L = _init_instaloader()
    profile = instaloader.Profile.from_username(L.context, TARGET_PROFILE.lstrip("@"))
    now_utc = dt.datetime.utcnow()
    records: List[dict] = []

    for idx, post in enumerate(profile.get_posts()):
        if limit and idx >= limit:
            break
        caption = post.caption or ""
        alt_text = post.accessibility_caption or ""
        age_days = (now_utc - post.date_utc.replace(tzinfo=None)).days

        # OCR solo 1ª imagen para no freír cuota
        with tempfile.TemporaryDirectory() as tmp:
            fname = L.download_pic(
                filename=os.path.join(tmp, post.shortcode),
                url=post.url,
                mtime=post.date_utc,
            )
            try:
                ocr_text = pytesseract.image_to_string(Image.open(fname)).strip()
            except Exception:
                ocr_text = ""

        records.append({
            "shortcode": post.shortcode,
            "caption": caption,
            "alt_text": alt_text,
            "ocr_text": ocr_text,
            "age_days": age_days,
            "likes": post.likes,
            "comments": post.comments,
            "collected_at": _now_iso(),
        })
    return records

# ---------------------------------------------------------------------------
# 4. Main workflow
# ---------------------------------------------------------------------------

def run_once():
    # 4.1 Perfil
    print("\n📊 Perfil…")
    followers = get_follower_count()
    insights = get_user_insights()

    rows_user: List[dict] = []
    if followers:
        rows_user.append(followers)
    for m in insights:
        if "values" in m:
            for v in m["values"]:
                rows_user.append({
                    "timestamp": _now_iso(),
                    "metric": m["name"],
                    "dimension": "total",
                    "value": v["value"],
                })
    _append_csv(USER_CSV, pd.DataFrame(rows_user), ["timestamp", "metric"])

    # 4.2 Posts (Graph metrics)
    print("\n📸 Publicaciones… (métricas)")
    new_posts = get_recent_media(limit=20)
    media_rows = collect_media_insights(new_posts)
    _append_csv(MEDIA_CSV, pd.DataFrame(media_rows), ["media_id", "metric", "collected_at"])

    # 4.3 Posts (caption/alt/OCR)
    print("\n📝 Texto + OCR…")
    text_records = collect_post_text(limit=100)  # cambia límite si quieres
    _append_csv(POST_CSV, pd.DataFrame(text_records), ["shortcode", "collected_at"])

    print("\n✅ Sincronización completada.")


if __name__ == "__main__":
    run_once()
