import instaloader
import pandas as pd

# Crea una instancia de Instaloader
L = instaloader.Instaloader()

# Nombre del perfil de ejemplo 
PROFILE = "thegingerclub_"  # cámbialo por cualquier cuenta pública

# Descarga los metadatos del perfil (sin fotos)
L.download_profile(PROFILE, profile_pic=False, fast_update=True, download_stories=False, download_posts=False)


PROFILE = "thegingerclub_"  # cambia por la cuenta que quieras analizar

L = instaloader.Instaloader()
posts = instaloader.Profile.from_username(L.context, PROFILE).get_posts()

data = []
for post in posts:
    data.append({
        "fecha": post.date_utc,
        "tipo": post.typename,
        "likes": post.likes,
        "comentarios": post.comments,
        "hashtags": post.caption_hashtags,
        "texto": post.caption[:100],  # primer fragmento del texto
    })
    if len(data) >= 50:  # solo los últimos 50 posts
        break

df = pd.DataFrame(data)
df.to_csv(f"data/raw/instagram_{PROFILE}.csv", index=False, encoding='utf-8')
print(f"✅ CSV generado para {PROFILE}")
