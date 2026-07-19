"""
Nomalar.uz — asosiy backend fayl.

Hozircha bu fayl:
- Frontend statik fayllarini ko'rsatadi (index.html, style.css, script.js)
- Kelajakda qo'shiladigan API yo'llari uchun joy tayyorlab qo'yilgan
  (masalan: /api/register, /api/verify-email, /api/create/{turi})

SQLite baza fayli shu papkada avtomatik yaratiladi: nomalar.db
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nomalar.db")

app = FastAPI(title="Nomalar.uz")


def init_db():
    """Baza va jadvallarni birinchi ishga tushirishda tayyorlaydi."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Foydalanuvchilar (faqat email orqali, parolsiz)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            is_verified INTEGER DEFAULT 0,
            verify_code TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Yaratilgan noma/taklifnomalar
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            template_type TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            data TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)

    conn.commit()
    conn.close()


init_db()

# Frontend fayllarini ko'rsatish
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")


@app.get("/")
def home():
    return FileResponse(os.path.join(BASE_DIR, "static", "index.html"))


# --- Keyingi bosqichda qo'shiladigan yo'llar (hozircha bo'sh) ---
# @app.post("/api/register")       -> email qabul qilish + tasdiqlash kodi yuborish
# @app.post("/api/verify")         -> kodni tekshirish
# @app.post("/api/create/{turi}")  -> forma ma'lumotini saqlash, link yaratish
# @app.get("/n/{slug}")            -> yaratilgan noma sahifasini ko'rsatish
