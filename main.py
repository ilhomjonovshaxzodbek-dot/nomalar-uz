"""
Nomalar.uz — BARCHA KOD BITTA FAYLDA.

Bu faylda:
- Backend (FastAPI) — ma'lumotlarni saqlash, link yaratish
- Frontend (HTML + CSS + JS) — hammasi shu faylning ichida, string sifatida

GitHub'ga yuklaganda sizga faqat 2 ta fayl kerak:
  1. main.py (shu fayl)
  2. requirements.txt

SQLite baza fayli (nomalar.db) birinchi ishga tushganda avtomatik yaratiladi.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlite3
import os
import re
import json
import random
import string

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nomalar.db")

app = FastAPI(title="Nomalar.uz")


# ============================================================
#  BAZA (DATABASE)
# ============================================================

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            is_verified INTEGER DEFAULT 0,
            verify_code TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text or "noma"


def unique_slug(base_slug: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    slug = base_slug
    while True:
        cur.execute("SELECT 1 FROM pages WHERE slug = ?", (slug,))
        if not cur.fetchone():
            conn.close()
            return slug
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
        slug = f"{base_slug}-{suffix}"


# ============================================================
#  UMUMIY DIZAYN QISMLARI — IKONKALAR, NAVBAR, SAHIFA QOBIG'I
#  (marketing sahifalari: bosh sahifa, noma turlari, qanday
#   ishlaydi, afzalliklar — barchasi shu qismlardan foydalanadi)
# ============================================================

ICON_SVG = {
    "heart": '<path d="M12 21s-7-4.35-9.5-9A5.5 5.5 0 0 1 12 6a5.5 5.5 0 0 1 9.5 6C19 16.65 12 21 12 21Z"/>',
    "cake": '<path d="M4 21v-7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v7M4 21h16M8 12V8m4 4V8m4 4V8M8 6a1 1 0 1 0 0-2 1 1 0 0 0 0 2Zm4 0a1 1 0 1 0 0-2 1 1 0 0 0 0 2Zm4 0a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z"/>',
    "document": '<path d="M7 3h7l5 5v13H7V3Z"/><path d="M14 3v5h5M9 12h6M9 16h6"/>',
    "moon": '<path d="M20 14.5A8.5 8.5 0 1 1 9.5 4a7 7 0 0 0 10.5 10.5Z"/>',
    "graduation": '<path d="M2 9 12 4l10 5-10 5-10-5Z"/><path d="M6 11v5c0 1.5 3 3 6 3s6-1.5 6-3v-5"/>',
    "building": '<path d="M4 21V7l8-4 8 4v14M4 21h16M9 21v-6h6v6"/>',
    "shield": '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6l-8-3Z"/><path d="m9 12 2 2 4-4"/>',
    "envelope": '<path d="M3 6h18v12H3V6Z"/><path d="m3 7 9 6 9-6"/>',
    "idcard": '<rect x="3" y="5" width="18" height="14" rx="2"/><circle cx="8.5" cy="12" r="2"/><path d="M13 10h6M13 14h4"/>',
    "briefcase": '<rect x="3" y="7" width="18" height="12" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>',
    "bolt": '<path d="M13 2 3 14h7l-1 8 11-14h-7l0-6Z"/>',
    "sparkle": '<path d="M12 2v6M12 16v6M2 12h6M16 12h6M5 5l4 4M15 15l4 4M19 5l-4 4M9 15l-4 4"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18Z"/>',
    "coin": '<circle cx="12" cy="12" r="9"/><path d="M12 7v10M9 9.5c0-1.4 1.3-2.5 3-2.5s3 1.1 3 2.5-1.3 2-3 2.5c-1.7.5-3 1.1-3 2.5s1.3 2.5 3 2.5 3-1.1 3-2.5"/>',
}


def icon_badge(icon_key: str, size: int = 22, bg: str = "rgba(47,111,237,0.1)", color: str = "var(--accent1)") -> str:
    svg_inner = ICON_SVG.get(icon_key, ICON_SVG["sparkle"])
    return (
        f'<span class="icon-badge" style="background:{bg};color:{color};">'
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{svg_inner}</svg></span>'
    )


TEMPLATE_META = [
    {"key": "toy", "name": "To'y taklifnomasi", "icon": "heart", "desc": "Kuyov-kelin, sana va manzil bilan chiroyli to'y taklifnomasi."},
    {"key": "tugilgan-kun", "name": "Tug'ilgan kun", "icon": "cake", "desc": "Tug'ilgan kun kechasi uchun taklifnoma, sana va manzil bilan."},
    {"key": "beshik", "name": "Beshik to'yi", "icon": "moon", "desc": "Chaqaloq va ota-ona ismi bilan beshik to'yi taklifnomasi."},
    {"key": "bitiruv", "name": "Bitiruv marosimi", "icon": "graduation", "desc": "Maktab yoki universitet bitiruv marosimi uchun taklifnoma."},
    {"key": "rasmiy", "name": "Rasmiy tadbir", "icon": "building", "desc": "Konferensiya, yig'ilish va boshqa rasmiy tadbirlar uchun."},
    {"key": "sevishganlar", "name": "Sevishganlar xati", "icon": "envelope", "desc": "Yurak gaplaringizni chiroyli xat shaklida yetkazing."},
    {"key": "kafolat", "name": "Kafolat xati", "icon": "shield", "desc": "Mahsulot yoki xizmat uchun rasmiy kafolat xati."},
    {"key": "ota-ona-kafolat", "name": "Ota-ona kafolat xati", "icon": "shield", "desc": "O'quvchi uchun ota-ona tomonidan kafolat xati."},
    {"key": "tugilgan-kun-tabrik", "name": "Tug'ilgan kun tabrigi", "icon": "cake", "desc": "Yaqiningizga tug'ilgan kun tabrigini yuboring."},
    {"key": "tushuntirish", "name": "Tushuntirish xati", "icon": "document", "desc": "Rasmiy tushuntirish xati — maktab, ish joyi uchun."},
    {"key": "eslatma", "name": "Eslatma xati", "icon": "document", "desc": "Muddat va topshiriqlar haqida rasmiy eslatma."},
    {"key": "minnatdorchilik", "name": "Minnatdorchilik xati", "icon": "document", "desc": "Hamkor yoki jamoa a'zosiga minnatdorchilik bildiring."},
    {"key": "vizitka", "name": "Vizitka", "icon": "idcard", "desc": "Ism, lavozim va aloqa ma'lumotlari bilan raqamli vizitka."},
    {"key": "rezyume", "name": "Rezyume / CV", "icon": "briefcase", "desc": "Ish tajribasi va ko'nikmalar bilan raqamli rezyume."},
]

SITE_STYLE = r"""
:root {
  --bg1: #EAF2FF; --bg2: #F3F8FF; --bg3: #FFFFFF;
  --ink: #16233B; --ink-dim: #64748B;
  --glass: rgba(255,255,255,0.72); --glass-strong: rgba(255,255,255,0.9); --glass-border: rgba(219,231,249,0.9);
  --accent1: #2F6FED; --accent2: #4A8CFF; --accent3: #7DB2FF;
  --accent-grad: linear-gradient(135deg, var(--accent1) 0%, var(--accent2) 100%);
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: linear-gradient(160deg, var(--bg1) 0%, var(--bg2) 45%, var(--bg3) 100%); color: var(--ink); font-family: 'Inter', sans-serif; min-height: 100vh; }
.eyebrow { font-size: 12px; letter-spacing: 0.16em; text-transform: uppercase; color: var(--accent1); font-weight: 600; margin: 0 0 12px; }
.navbar { position: sticky; top: 0; left: 0; right: 0; z-index: 20; display: flex; align-items: center; justify-content: space-between; padding: 16px 5vw; background: rgba(255,255,255,0.9); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); border-bottom: 1px solid var(--glass-border); }
.nav-logo { font-family: 'Sora', sans-serif; font-weight: 800; font-size: 19px; color: var(--ink); text-decoration: none; display: flex; align-items: center; gap: 8px; }
.nav-logo .dot { color: var(--accent1); }
.nav-links { display: flex; gap: 28px; list-style: none; margin: 0; padding: 0; }
.nav-links a { color: var(--ink-dim); text-decoration: none; font-size: 14px; font-weight: 500; }
.nav-links a:hover, .nav-links a.active { color: var(--accent1); }
.nav-right { display: flex; align-items: center; gap: 14px; }
.btn-login, .btn-primary { font-family: 'Inter', sans-serif; font-size: 13.5px; font-weight: 600; background: var(--accent-grad); color: #fff; border: none; border-radius: 999px; padding: 11px 24px; cursor: pointer; text-decoration: none; display: inline-block; box-shadow: 0 8px 22px rgba(47,111,237,0.28); }
.btn-login:hover, .btn-primary:hover { box-shadow: 0 10px 28px rgba(47,111,237,0.38); }
.btn-outline { font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 600; background: #fff; color: var(--accent1); border: 1px solid var(--glass-border); border-radius: 999px; padding: 13px 28px; cursor: pointer; text-decoration: none; display: inline-block; }
@media (max-width: 780px) { .nav-links { display: none; } }
.page-wrap { width: 100%; max-width: 1080px; margin: 0 auto; padding: 44px 20px 80px; }
.page-header { text-align: center; margin-bottom: 40px; }
.section-title { font-family: 'Sora', sans-serif; font-weight: 700; font-size: clamp(24px,3.6vw,34px); margin: 0 0 12px; color: var(--ink); }
.section-sub { color: var(--ink-dim); font-size: 15px; max-width: 560px; margin: 0 auto; line-height: 1.6; }
.icon-badge { display: inline-flex; align-items: center; justify-content: center; width: 46px; height: 46px; border-radius: 14px; flex-shrink: 0; }
.hero { text-align: center; padding: 40px 20px 10px; }
.hero h1 { font-family: 'Sora', sans-serif; font-weight: 800; font-size: clamp(28px,4.5vw,46px); line-height: 1.15; color: var(--ink); margin: 0 0 16px; }
.hero h1 span { background: var(--accent-grad); -webkit-background-clip: text; background-clip: text; color: transparent; }
.hero p.hero-sub { color: var(--ink-dim); font-size: 15.5px; max-width: 520px; margin: 0 auto 28px; line-height: 1.6; }
.hero-actions { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
.tpl-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr)); gap: 16px; }
.tpl-page-card { background: #fff; border: 1px solid var(--glass-border); border-radius: 18px; padding: 22px; display: flex; flex-direction: column; gap: 12px; text-align: left; box-shadow: 0 4px 16px rgba(47,111,237,0.07); }
.tpl-page-card .tpl-name { font-family: 'Sora', sans-serif; font-weight: 700; font-size: 15.5px; color: var(--ink); }
.tpl-page-card p { font-size: 13px; color: var(--ink-dim); margin: 0; line-height: 1.5; }
.tpl-page-card a.btn-outline { margin-top: 6px; padding: 9px 18px; font-size: 13px; align-self: flex-start; }
.benefit-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr)); gap: 18px; }
.benefit-card { background: #fff; border: 1px solid var(--glass-border); border-radius: 18px; padding: 28px 24px; text-align: left; box-shadow: 0 4px 16px rgba(47,111,237,0.07); }
.benefit-card .icon-badge { margin-bottom: 14px; }
.benefit-card h3 { font-family: 'Sora', sans-serif; font-size: 16px; margin: 0 0 8px; color: var(--ink); }
.benefit-card p { font-size: 13.5px; color: var(--ink-dim); margin: 0; line-height: 1.6; }
.step-list { display: flex; flex-direction: column; gap: 18px; max-width: 720px; margin: 0 auto; }
.step-card { background: #fff; border: 1px solid var(--glass-border); border-radius: 20px; padding: 26px 28px; display: flex; gap: 20px; align-items: flex-start; text-align: left; box-shadow: 0 4px 16px rgba(47,111,237,0.07); }
.step-num { font-family: 'Sora', sans-serif; font-weight: 800; font-size: 22px; color: var(--accent1); background: rgba(47,111,237,0.1); width: 44px; height: 44px; border-radius: 14px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.step-card h3 { font-family: 'Sora', sans-serif; font-size: 17px; margin: 2px 0 8px; color: var(--ink); }
.step-card p { font-size: 14px; color: var(--ink-dim); line-height: 1.65; margin: 0 0 8px; }
.step-card ul { margin: 8px 0 0; padding-left: 18px; color: var(--ink-dim); font-size: 13.5px; line-height: 1.7; }
.site-footer-static { text-align: center; font-size: 12px; color: var(--ink-dim); opacity: 0.75; padding: 20px 20px 36px; }
"""


def nav_html(active: str = "") -> str:
    def cls(name):
        return "active" if name == active else ""

    return f"""<nav class="navbar">
  <a href="/" class="nav-logo">Nomalar<span class="dot">.</span>uz</a>
  <ul class="nav-links">
    <li><a href="/" class="{cls('home')}">Bosh sahifa</a></li>
    <li><a href="/turlar" class="{cls('turlar')}">Noma turlari</a></li>
    <li><a href="/qanday-ishlaydi" class="{cls('qanday')}">Qanday ishlaydi?</a></li>
    <li><a href="/afzalliklar" class="{cls('afzallik')}">Afzalliklar</a></li>
  </ul>
  <div class="nav-right">
    <a class="btn-login" href="/yaratish">Noma yaratish</a>
  </div>
</nav>"""


def page_shell(title: str, active: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>{SITE_STYLE}</style>
</head>
<body>
{nav_html(active)}
{body}
<p class="site-footer-static">Yaratuvchi: Ilhomjonov Shahzodbek</p>
</body>
</html>"""


@app.get("/turlar", response_class=HTMLResponse)
def turlar_page():
    cards = ""
    for t in TEMPLATE_META:
        cards += f"""<div class="tpl-page-card">
  {icon_badge(t['icon'])}
  <span class="tpl-name">{t['name']}</span>
  <p>{t['desc']}</p>
  <a class="btn-outline" href="/yaratish">Yaratish &rarr;</a>
</div>
"""
    body = f"""<div class="page-wrap">
  <div class="page-header">
    <p class="eyebrow">14 xil shablon</p>
    <h1 class="section-title">Noma turlarini tanlang</h1>
    <p class="section-sub">Turli hayotiy voqealar uchun eng mos tanlangan uslublar — har biri o'ziga xos dizaynda.</p>
  </div>
  <div class="tpl-grid">
    {cards}
  </div>
</div>"""
    return page_shell("Noma turlari — Nomalar.uz", "turlar", body)


@app.get("/qanday-ishlaydi", response_class=HTMLResponse)
def qanday_ishlaydi_page():
    body = f"""<div class="page-wrap">
  <div class="page-header">
    <p class="eyebrow">3 oddiy qadam</p>
    <h1 class="section-title">Qanday ishlaydi?</h1>
    <p class="section-sub">Nomalar.uz orqali chiroyli raqamli noma yaratish — ro'yxatdan o'tishsiz, to'lovsiz, atigi bir necha daqiqada.</p>
  </div>
  <div class="step-list">
    <div class="step-card">
      <span class="step-num">1</span>
      <div>
        <h3>Noma turini tanlaysiz</h3>
        <p>To'y, tug'ilgan kun, beshik to'yi, bitiruv marosimi, rasmiy tadbir va yana 9 xil noma turidan biriga bosasiz. Har bir tur o'ziga xos rang va uslubda tayyorlangan — mavzuga mos chiqadi.</p>
        <ul>
          <li>14 xil tayyor shablon, hech biri bir-birini takrorlamaydi</li>
          <li>Har birida o'z rangi, shrifti va joylashuvi bor</li>
        </ul>
      </div>
    </div>
    <div class="step-card">
      <span class="step-num">2</span>
      <div>
        <h3>Ma'lumotlarni kiritasiz</h3>
        <p>Ism, sana, vaqt va manzil kabi asosiy ma'lumotlarni oddiy formaga yozasiz. Xohlasangiz manzilni xaritadan belgilashingiz, rasm yoki fon musiqasi qo'shishingiz, hatto asosiy rangni o'zgartirishingiz mumkin — bularning barchasi ixtiyoriy.</p>
        <ul>
          <li>Xaritadan aniq manzil tanlash (Toshkent va butun O'zbekiston bo'ylab)</li>
          <li>Rasm, fon musiqasi va rangni moslashtirish ixtiyoriy</li>
        </ul>
      </div>
    </div>
    <div class="step-card">
      <span class="step-num">3</span>
      <div>
        <h3>Havolani olib, ulashasiz</h3>
        <p>Bir necha soniyada shaxsiy havolangiz tayyor bo'ladi. Uni Telegram, Instagram yoki istalgan ilova orqali mehmonlaringizga yuborasiz. Sahifada chop etish, rasm sifatida yuklab olish va QR kod orqali ulashish imkoniyatlari ham bor.</p>
        <ul>
          <li>Havola doimiy — istalgan vaqt qayta ochiladi</li>
          <li>Chop etish, yuklab olish va QR kod — bittasi bilan</li>
        </ul>
      </div>
    </div>
  </div>
  <div style="text-align:center;margin-top:44px;">
    <a class="btn-login" href="/yaratish">Hoziroq boshlash &rarr;</a>
  </div>
</div>"""
    return page_shell("Qanday ishlaydi? — Nomalar.uz", "qanday", body)


@app.get("/afzalliklar", response_class=HTMLResponse)
def afzalliklar_page():
    items = [
        ("sparkle", "Zamonaviy dizayn", "Har bir shablon alohida ishlab chiqilgan, o'ziga xos rang va uslubda — andoza his qilinmaydi."),
        ("coin", "100% bepul", "Hech qanday to'lov, obuna yoki yashirin cheklov yo'q — barcha shablonlar hammaga ochiq."),
        ("bolt", "Tezkor", "Formani to'ldirib, bir necha soniyada tayyor havola olasiz — kutish yo'q."),
        ("globe", "Istalgan joydan ochiladi", "Havola Telegram, Instagram, brauzer — qayerda ulashmang, mukammal ochiladi."),
        ("shield", "Ishonchli va barqaror", "Yaratilgan sahifangiz doimiy havolada saqlanadi, istalgan vaqt qayta ochiladi."),
        ("idcard", "Shaxsiylashtirish", "Rasm, fon musiqasi va asosiy rangni o'zingizga moslab o'zgartirishingiz mumkin."),
    ]
    cards = ""
    for icon, title, desc in items:
        cards += f"""<div class="benefit-card">
  {icon_badge(icon, size=24)}
  <h3>{title}</h3>
  <p>{desc}</p>
</div>
"""
    body = f"""<div class="page-wrap">
  <div class="page-header">
    <p class="eyebrow">Nega Nomalar.uz?</p>
    <h1 class="section-title">Afzalliklar</h1>
    <p class="section-sub">Nomalar.uz'ni tanlashning bir nechta sababi.</p>
  </div>
  <div class="benefit-grid">
    {cards}
  </div>
</div>"""
    return page_shell("Afzalliklar — Nomalar.uz", "afzallik", body)


@app.get("/", response_class=HTMLResponse)
def landing_home():
    mini_cards = ""
    for t in TEMPLATE_META[:8]:
        mini_cards += f"""<div class="tpl-page-card" style="text-align:center;align-items:center;">
  {icon_badge(t['icon'])}
  <span class="tpl-name">{t['name']}</span>
</div>
"""
    body = f"""<div class="page-wrap" style="padding-top:10px;">
  <section class="hero">
    <p class="eyebrow">raqamli noma</p>
    <h1>Har qanday vaziyat uchun <span>noma yarating</span></h1>
    <p class="hero-sub">Nomalar.uz — to'y, tug'ilgan kun, bitiruv va boshqa muhim kunlaringiz uchun chiroyli raqamli nomalarni bir necha daqiqada, mutlaqo bepul yarating.</p>
    <div class="hero-actions">
      <a class="btn-login" href="/yaratish">Noma yaratish &rarr;</a>
      <a class="btn-outline" href="/qanday-ishlaydi">Qanday ishlaydi?</a>
    </div>
  </section>

  <div class="page-header" style="margin-top:60px;">
    <p class="eyebrow">14 xil shablon</p>
    <h2 class="section-title">Noma turlarini tanlang</h2>
    <p class="section-sub">Turli hayotiy voqealar uchun eng mos tanlangan uslublar.</p>
  </div>
  <div class="tpl-grid">
    {mini_cards}
  </div>
  <div style="text-align:center;margin-top:22px;">
    <a class="btn-outline" href="/turlar">Barcha turlarni ko'rish &rarr;</a>
  </div>
</div>"""
    return page_shell("Nomalar.uz — muhim daqiqalaringiz uchun noma", "home", body)


# ============================================================
#  NOMA YARATISH OQIMI (HTML + CSS + JS — HAMMASI SHU YERDA)
# ============================================================

HOME_PAGE = r"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Nomalar.uz — muhim daqiqalaringiz uchun noma</title>
<meta name="description" content="To'y, tug'ilgan kun, eslatma va boshqa tadbirlaringiz uchun raqamli noma yarating.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<style>
:root {
  --bg1: #EAF2FF; --bg2: #F3F8FF; --bg3: #FFFFFF;
  --ink: #16233B; --ink-dim: #64748B;
  --glass: rgba(255,255,255,0.72); --glass-strong: rgba(255,255,255,0.9); --glass-border: rgba(219,231,249,0.9);
  --accent1: #2F6FED; --accent2: #4A8CFF; --accent3: #7DB2FF;
  --accent-grad: linear-gradient(135deg, var(--accent1) 0%, var(--accent2) 100%);
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: linear-gradient(160deg, var(--bg1) 0%, var(--bg2) 50%, var(--bg3) 100%); color: var(--ink); font-family: 'Inter', sans-serif; overflow-x: hidden; min-height: 100vh; }
.eyebrow { font-family: 'Inter', sans-serif; font-size: 12px; letter-spacing: 0.16em; text-transform: uppercase; color: var(--accent1); font-weight: 600; margin: 0 0 12px; }
.seal { position: fixed; top: 24px; left: 50%; transform: translateX(-50%); width: 34px; height: 34px; opacity: 0.9; z-index: 10; }
.seal svg { width: 100%; height: 100%; }
.seal circle { fill: url(#seal-grad); }
.seal path { fill: #fff; }
.screen { display: none; min-height: 100vh; align-items: center; justify-content: center; padding: 100px 24px 48px; position: relative; z-index: 1; perspective: 1400px; }
.bg-decor { position: fixed; inset: 0; z-index: 0; overflow: hidden; pointer-events: none; perspective: 1200px; }
.bg-orb { position: absolute; border-radius: 50%; filter: blur(26px); opacity: 0.72; will-change: transform; }
.bg-orb.o1 { width: 380px; height: 380px; background: radial-gradient(circle at 32% 26%, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0) 24%), radial-gradient(circle at 62% 68%, rgba(30,10,60,0.28) 0%, transparent 55%), radial-gradient(circle at 42% 40%, var(--accent1) 0%, transparent 72%); top: -120px; left: -110px; animation: drift1 20s ease-in-out infinite; }
.bg-orb.o2 { width: 340px; height: 340px; background: radial-gradient(circle at 32% 26%, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0) 24%), radial-gradient(circle at 62% 68%, rgba(70,10,40,0.25) 0%, transparent 55%), radial-gradient(circle at 42% 40%, var(--accent3) 0%, transparent 72%); bottom: -140px; right: -90px; animation: drift2 24s ease-in-out infinite; }
.bg-orb.o3 { width: 280px; height: 280px; background: radial-gradient(circle at 32% 26%, rgba(255,255,255,0.95) 0%, rgba(255,255,255,0) 24%), radial-gradient(circle at 62% 68%, rgba(50,10,60,0.25) 0%, transparent 55%), radial-gradient(circle at 42% 40%, var(--accent2) 0%, transparent 72%); top: 40%; left: 58%; animation: drift3 28s ease-in-out infinite; }
.bg-grid { position: absolute; inset: -10%; background-image: radial-gradient(rgba(109,93,246,0.10) 1px, transparent 1px); background-size: 30px 30px; mask-image: radial-gradient(ellipse 70% 60% at 50% 40%, black 0%, transparent 75%); -webkit-mask-image: radial-gradient(ellipse 70% 60% at 50% 40%, black 0%, transparent 75%); animation: gridshift 60s linear infinite; }
@keyframes drift1 { 0%,100% { transform: translate(0,0) scale(1); } 50% { transform: translate(50px,70px) scale(1.12); } }
@keyframes drift2 { 0%,100% { transform: translate(0,0) scale(1); } 50% { transform: translate(-60px,-50px) scale(1.15); } }
@keyframes drift3 { 0%,100% { transform: translate(0,0) scale(1); } 50% { transform: translate(-40px,40px) scale(0.9); } }
@keyframes gridshift { 0% { background-position: 0 0; } 100% { background-position: 60px 60px; } }
@media (max-width: 600px) {
  .bg-orb { filter: blur(18px); opacity: 0.55; }
  .bg-orb.o1 { width: 220px; height: 220px; }
  .bg-orb.o2 { width: 200px; height: 200px; }
  .bg-orb.o3 { width: 170px; height: 170px; }
}
@media (prefers-reduced-motion: reduce) {
  .bg-orb, .bg-grid { animation: none; }
}
.screen.active { display: flex; }
#screen-intro.screen.active { display: block; padding-top: 0; }
.intro-wrap { text-align: center; width: min(92vw, 440px); animation: rise 0.8s ease both; background: var(--glass); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px); border: 1px solid var(--glass-border); border-radius: 32px; padding: 52px 40px; box-shadow: 0 24px 70px rgba(109,93,246,0.22), 0 2px 8px rgba(109,93,246,0.08), inset 0 1px 0 rgba(255,255,255,0.7); }
.brand-title { font-family: 'Sora', sans-serif; font-weight: 800; font-size: 48px; margin: 0 0 12px; background: var(--accent-grad); background-size: 220% 100%; -webkit-background-clip: text; background-clip: text; color: transparent; animation: shimmer 5s ease-in-out infinite; letter-spacing: -0.01em; }
.brand-title .dot { -webkit-text-fill-color: var(--accent3); }
@keyframes shimmer { 0% { background-position: 0% 0; } 50% { background-position: 100% 0; } 100% { background-position: 0% 0; } }
.intro-sub { color: var(--ink-dim); font-size: 15px; margin: 0 0 32px; }
.intro-actions { display: flex; align-items: center; justify-content: center; gap: 10px; }
.navbar { position: fixed; top: 0; left: 0; right: 0; z-index: 20; display: flex; align-items: center; justify-content: space-between; padding: 16px 5vw; background: rgba(255,255,255,0.85); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); border-bottom: 1px solid var(--glass-border); }
.nav-logo { font-family: 'Sora', sans-serif; font-weight: 800; font-size: 19px; color: var(--ink); display: flex; align-items: center; gap: 8px; }
.nav-logo .dot { color: var(--accent1); }
.nav-links { display: flex; gap: 28px; list-style: none; margin: 0; padding: 0; }
.nav-links a { color: var(--ink-dim); text-decoration: none; font-size: 14px; font-weight: 500; }
.nav-links a:hover { color: var(--accent1); }
.nav-right { display: flex; align-items: center; gap: 14px; }
.btn-login { font-family: 'Inter', sans-serif; font-size: 13.5px; font-weight: 600; background: var(--accent-grad); color: #fff; border: none; border-radius: 999px; padding: 10px 22px; cursor: pointer; }
@media (max-width: 780px) { .nav-links { display: none; } }
.landing-wrap { width: 100%; max-width: 1080px; margin: 0 auto; padding-top: 30px; }
.hero { text-align: center; padding: 30px 20px 10px; }
.hero h1 { font-family: 'Sora', sans-serif; font-weight: 800; font-size: clamp(28px,4.5vw,46px); line-height: 1.15; color: var(--ink); margin: 0 0 16px; }
.hero h1 span { background: var(--accent-grad); -webkit-background-clip: text; background-clip: text; color: transparent; }
.hero p.hero-sub { color: var(--ink-dim); font-size: 15.5px; max-width: 520px; margin: 0 auto 28px; line-height: 1.6; }
.hero-actions { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
.btn-outline { font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 600; background: #fff; color: var(--accent1); border: 1px solid var(--glass-border); border-radius: 999px; padding: 14px 30px; cursor: pointer; }
.landing-section { padding: 54px 20px 10px; text-align: center; }
.landing-section .section-title { text-align: center; }
.landing-section .section-sub { color: var(--ink-dim); font-size: 14px; margin: -16px 0 30px; }
.mini-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px,1fr)); gap: 12px; max-width: 900px; margin: 0 auto; }
.mini-tpl { background: #fff; border: 1px solid var(--glass-border); border-radius: 16px; padding: 18px 10px; display: flex; flex-direction: column; align-items: center; gap: 8px; box-shadow: 0 4px 14px rgba(47,111,237,0.06); }
.mini-tpl .ic { font-size: 22px; }
.mini-tpl span.mini-name { font-size: 12.5px; font-weight: 600; color: var(--ink); }
.benefit-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px,1fr)); gap: 16px; max-width: 900px; margin: 0 auto; }
.benefit-card { background: #fff; border: 1px solid var(--glass-border); border-radius: 18px; padding: 26px 20px; text-align: left; box-shadow: 0 4px 16px rgba(47,111,237,0.06); }
.benefit-card .ic { font-size: 22px; margin-bottom: 10px; }
.benefit-card h3 { font-family: 'Sora', sans-serif; font-size: 15px; margin: 0 0 6px; color: var(--ink); }
.benefit-card p { font-size: 13px; color: var(--ink-dim); margin: 0; line-height: 1.5; }
.btn-primary { font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 600; letter-spacing: 0.01em; background: var(--accent-grad); color: #fff; border: none; border-radius: 999px; padding: 14px 38px; cursor: pointer; transition: transform 0.15s ease, box-shadow 0.3s ease; box-shadow: 0 8px 24px rgba(109,93,246,0.35); }
.btn-primary:hover { box-shadow: 0 10px 32px rgba(109,93,246,0.48); transform: translateY(-2px); }
.btn-primary:active { transform: scale(0.98); }
.btn-primary:focus-visible { outline: 2px solid var(--accent1); outline-offset: 3px; }
.explain-wrap { width: min(92vw, 440px); text-align: center; background: var(--glass); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px); border: 1px solid var(--glass-border); border-radius: 32px; padding: 48px 36px; box-shadow: 0 24px 70px rgba(109,93,246,0.22), 0 2px 8px rgba(109,93,246,0.08), inset 0 1px 0 rgba(255,255,255,0.7); }
.explain-slide { display: none; animation: rise 0.5s ease both; }
.explain-slide.active { display: block; }
.explain-num { font-family: 'Sora', sans-serif; font-weight: 700; font-size: 14px; color: var(--accent1); letter-spacing: 0.1em; }
.explain-slide h2 { font-family: 'Sora', sans-serif; font-weight: 700; font-size: 27px; margin: 8px 0 12px; color: var(--ink); }
.explain-slide p { color: var(--ink-dim); font-size: 15px; line-height: 1.6; margin: 0 0 32px; }
.explain-dots { display: flex; justify-content: center; gap: 8px; margin-bottom: 28px; }
.dot-i { width: 6px; height: 6px; border-radius: 50%; background: var(--ink-dim); opacity: 0.3; transition: opacity 0.2s ease, background 0.2s ease; }
.dot-i.active { opacity: 1; background: var(--accent2); }
.templates-wrap { max-width: 480px; width: 100%; text-align: center; }
.intro-wrap, .explain-wrap, .form-wrap, .result-wrap, .tpl-card { transition: transform 0.35s cubic-bezier(0.22,1,0.36,1), box-shadow 0.35s ease, border-color 0.2s ease, background 0.2s ease; will-change: transform; }
.section-title { font-family: 'Sora', sans-serif; font-weight: 700; font-size: 28px; margin: 0 0 28px; color: var(--ink); }
.template-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.tpl-card { font-family: 'Inter', sans-serif; background: var(--glass); backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); border: 1px solid var(--glass-border); border-radius: 16px; padding: 20px 16px; color: var(--ink); cursor: pointer; text-align: left; transition: border-color 0.2s ease, background 0.2s ease, transform 0.15s ease, box-shadow 0.2s ease; display: flex; flex-direction: column; gap: 10px; box-shadow: 0 4px 18px rgba(109,93,246,0.08); }
.tpl-card:hover { border-color: var(--accent2); background: var(--glass-strong); transform: translateY(-2px); box-shadow: 0 10px 26px rgba(109,93,246,0.18); }
.tpl-card.selected { border-color: var(--accent1); background: var(--glass-strong); box-shadow: 0 10px 30px rgba(109,93,246,0.25); }
.tpl-mark { font-family: 'Sora', sans-serif; font-weight: 700; font-size: 17px; background: var(--accent-grad); -webkit-background-clip: text; background-clip: text; color: transparent; }
.tpl-name { font-size: 13.5px; font-weight: 600; }
.next-note { margin-top: 26px; font-size: 13px; color: var(--ink-dim); }
.form-wrap { width: min(92vw, 440px); background: var(--glass); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px); border: 1px solid var(--glass-border); border-radius: 32px; padding: 44px 36px; box-shadow: 0 24px 70px rgba(109,93,246,0.22), 0 2px 8px rgba(109,93,246,0.08), inset 0 1px 0 rgba(255,255,255,0.7); }
.form-wrap .section-title { text-align: center; }
.app-form { display: flex; flex-direction: column; gap: 16px; }
.app-form label { display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: var(--ink-dim); font-weight: 500; }
.app-form input, .app-form textarea { font-family: 'Inter', sans-serif; font-size: 14px; background: rgba(255,255,255,0.75); border: 1px solid rgba(109,93,246,0.14); border-radius: 14px; padding: 12px 14px; color: var(--ink); transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease; box-shadow: inset 0 1px 2px rgba(109,93,246,0.04); }
.app-form input:hover, .app-form textarea:hover { background: rgba(255,255,255,0.9); }
.app-form input:focus, .app-form textarea:focus { outline: none; border-color: var(--accent1); background: #fff; box-shadow: 0 0 0 4px rgba(109,93,246,0.14); }
.app-form textarea { font-family: inherit; resize: vertical; }
.row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-error { color: #E1477A; font-size: 13px; min-height: 18px; margin: 0; }
.result-wrap { width: min(92vw, 440px); text-align: center; background: var(--glass); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px); border: 1px solid var(--glass-border); border-radius: 32px; padding: 44px 36px; box-shadow: 0 24px 70px rgba(109,93,246,0.22), 0 2px 8px rgba(109,93,246,0.08), inset 0 1px 0 rgba(255,255,255,0.7); }
.result-sub { color: var(--ink-dim); font-size: 14px; margin: 0 0 20px; }
.result-link-box { display: flex; gap: 8px; margin-bottom: 20px; }
.result-link-box input { flex: 1; font-family: 'Inter', sans-serif; font-size: 13px; background: rgba(255,255,255,0.7); border: 1px solid rgba(109,93,246,0.18); border-radius: 10px; padding: 11px 12px; color: var(--ink); }
.btn-view-link { display: inline-block; color: var(--accent1); font-weight: 600; font-size: 14px; text-decoration: none; }
.btn-view-link:hover { text-decoration: underline; }
.map-field { display: flex; flex-direction: column; gap: 6px; }
.map-field-label { font-size: 13px; color: var(--ink-dim); font-weight: 500; }
.btn-map-pick { align-self: flex-start; font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 600; background: rgba(109,93,246,0.1); border: 1px solid var(--accent1); color: var(--accent1); border-radius: 999px; padding: 9px 16px; cursor: pointer; }
.btn-map-pick:hover { background: rgba(109,93,246,0.18); }
.map-preview { font-size: 12px; color: var(--ink-dim); margin: 0; }
.photo-field { display: flex; flex-direction: column; gap: 6px; }
.photo-field input[type="file"] { font-family: 'Inter', sans-serif; font-size: 12.5px; color: var(--ink-dim); }
.photo-field input[type="file"]::file-selector-button { font-family: 'Inter', sans-serif; font-size: 12.5px; font-weight: 600; background: rgba(109,93,246,0.1); border: 1px solid var(--accent1); color: var(--accent1); border-radius: 999px; padding: 7px 14px; cursor: pointer; margin-right: 8px; }
.photo-field input[type="url"] { font-family: 'Inter', sans-serif; font-size: 13px; background: rgba(255,255,255,0.7); border: 1px solid rgba(109,93,246,0.18); border-radius: 10px; padding: 9px 12px; color: var(--ink); }
.photo-preview-note { font-size: 12px; color: var(--accent2); font-weight: 500; margin: 0; min-height: 14px; }
.color-field { display: flex; flex-direction: column; gap: 8px; }
.color-field input[type="color"] { width: 52px; height: 36px; padding: 2px; border: 1px solid rgba(109,93,246,0.18); border-radius: 8px; background: transparent; cursor: pointer; }
.map-modal { display: none; position: fixed; inset: 0; background: rgba(32,31,51,0.45); backdrop-filter: blur(4px); z-index: 100; align-items: center; justify-content: center; padding: 20px; }
.map-modal.active { display: flex; }
.map-modal-inner { background: #fff; border-radius: 18px; padding: 18px; max-width: 480px; width: 100%; box-shadow: 0 24px 60px rgba(32,31,51,0.25); }
#map-picker { height: 320px; border-radius: 12px; }
.map-modal-actions { display: flex; justify-content: space-between; gap: 10px; margin-top: 14px; }
.map-modal-actions .btn-primary { flex: 1; }
.map-modal-hint { font-family: 'Inter', sans-serif; font-size: 12px; color: var(--ink-dim); margin: 0 0 10px; }
.site-footer { position: fixed; bottom: 14px; left: 50%; transform: translateX(-50%); font-size: 11px; color: var(--ink-dim); opacity: 0.7; z-index: 5; }
.btn-back { position: absolute; top: 24px; left: 24px; background: var(--glass); backdrop-filter: blur(10px); border: 1px solid var(--glass-border); color: var(--ink-dim); font-family: 'Inter', sans-serif; font-size: 13px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 6px; padding: 8px 14px; border-radius: 999px; z-index: 2; }
.btn-back:hover { color: var(--accent1); border-color: var(--accent1); }
@keyframes rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
@media (prefers-reduced-motion: reduce) { .intro-wrap, .explain-slide { animation: none; } }
</style>
</head>
<body>

<div class="bg-decor" aria-hidden="true">
  <div class="bg-grid"></div>
  <div class="bg-orb o1"></div>
  <div class="bg-orb o2"></div>
  <div class="bg-orb o3"></div>
</div>

<div class="seal" aria-hidden="true">
  <svg viewBox="0 0 100 100">
    <defs>
      <linearGradient id="seal-grad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#6D5DF6"/>
        <stop offset="55%" stop-color="#C86DD7"/>
        <stop offset="100%" stop-color="#FF8AAE"/>
      </linearGradient>
    </defs>
    <circle cx="50" cy="50" r="46"/>
    <path d="M50 20 L58 42 L82 42 L62 56 L70 78 L50 64 L30 78 L38 56 L18 42 L42 42 Z"/>
  </svg>
</div>

<section id="screen-explain" class="screen active">
  <a class="btn-back" href="/" style="text-decoration:none;">&larr; Bosh sahifa</a>
  <div class="explain-wrap">
    <div class="explain-slide" data-index="0">
      <span class="explain-num">01</span>
      <h2>Turini tanlaysiz</h2>
      <p>To'y, tug'ilgan kun, eslatma va yana boshqa 7 xil noma turidan birini tanlaysiz.</p>
    </div>
    <div class="explain-slide" data-index="1">
      <span class="explain-num">02</span>
      <h2>Ma'lumot kiritasiz</h2>
      <p>Ism, sana, manzil kabi kerakli ma'lumotlarni oddiy formaga yozasiz.</p>
    </div>
    <div class="explain-slide" data-index="2">
      <span class="explain-num">03</span>
      <h2>Link olasiz</h2>
      <p>Tayyor chiroyli sahifangiz uchun link yaratiladi — uni istalgan joyga yuborasiz.</p>
    </div>
    <div class="explain-dots">
      <span class="dot-i active" data-i="0"></span>
      <span class="dot-i" data-i="1"></span>
      <span class="dot-i" data-i="2"></span>
    </div>
    <button class="btn-primary" id="btn-continue">Davom etish</button>
  </div>
</section>

<section id="screen-templates" class="screen">
  <button class="btn-back" data-back="screen-explain">&larr; Orqaga</button>
  <div class="templates-wrap">
    <p class="eyebrow">1-qadam</p>
    <h2 class="section-title">Qanday noma kerak?</h2>
    <div class="template-grid">
      <button class="tpl-card" data-tpl="toy"><span class="tpl-mark">01</span><span class="tpl-name">To'y taklifnomasi</span></button>
      <button class="tpl-card" data-tpl="tugilgan-kun"><span class="tpl-mark">02</span><span class="tpl-name">Tug'ilgan kun</span></button>
      <button class="tpl-card" data-tpl="tushuntirish"><span class="tpl-mark">03</span><span class="tpl-name">Tushuntirish xati</span></button>
      <button class="tpl-card" data-tpl="eslatma"><span class="tpl-mark">04</span><span class="tpl-name">Eslatma xati</span></button>
      <button class="tpl-card" data-tpl="beshik"><span class="tpl-mark">05</span><span class="tpl-name">Beshik to'yi</span></button>
      <button class="tpl-card" data-tpl="bitiruv"><span class="tpl-mark">06</span><span class="tpl-name">Bitiruv marosimi</span></button>
      <button class="tpl-card" data-tpl="rasmiy"><span class="tpl-mark">07</span><span class="tpl-name">Rasmiy tadbir</span></button>
      <button class="tpl-card" data-tpl="kafolat"><span class="tpl-mark">08</span><span class="tpl-name">Kafolat xati</span></button>
      <button class="tpl-card" data-tpl="ota-ona-kafolat"><span class="tpl-mark">09</span><span class="tpl-name">Ota-ona kafolat xati</span></button>
      <button class="tpl-card" data-tpl="tugilgan-kun-tabrik"><span class="tpl-mark">10</span><span class="tpl-name">Tug'ilgan kun tabrigi</span></button>
      <button class="tpl-card" data-tpl="sevishganlar"><span class="tpl-mark">11</span><span class="tpl-name">Sevishganlar xati</span></button>
      <button class="tpl-card" data-tpl="vizitka"><span class="tpl-mark">12</span><span class="tpl-name">Vizitka</span></button>
      <button class="tpl-card" data-tpl="rezyume"><span class="tpl-mark">13</span><span class="tpl-name">Rezyume / CV</span></button>
      <button class="tpl-card" data-tpl="minnatdorchilik"><span class="tpl-mark">14</span><span class="tpl-name">Minnatdorchilik xati</span></button>
    </div>
    <p class="next-note" id="next-note">Tanlang — keyingi bosqichda forma ochiladi.</p>
  </div>
</section>

<section id="screen-form-toy" class="screen">
  <button class="btn-back" data-back="screen-templates">&larr; Orqaga</button>
  <div class="form-wrap">
    <p class="eyebrow">2-qadam</p>
    <h2 class="section-title">To'y ma'lumotlari</h2>
    <form id="form-toy" class="app-form">
      <label>Kuyov ismi<input type="text" name="kuyov" placeholder="Farhod" required></label>
      <label>Kelin ismi<input type="text" name="kelin" placeholder="Shirin" required></label>
      <div class="row-2">
        <label>Sana<input type="date" name="sana" required></label>
        <label>Vaqt<input type="time" name="vaqt" required></label>
      </div>
      <label>Manzil<input type="text" name="manzil" placeholder="Toshkent, Navoiy ko'chasi 23" required></label>
      <div class="map-field">
        <span class="map-field-label">Manzil xaritada (ixtiyoriy)</span>
        <input type="hidden" name="xarita_link" id="xarita-toy">
        <button type="button" class="btn-map-pick" id="xarita-toy-btn" data-target="xarita-toy">📍 Xaritadan joy tanlash</button>
        <p class="map-preview" id="xarita-toy-preview"></p>
      </div>
      <button type="submit" class="btn-primary" style="width:100%;margin-top:8px;">Noma yaratish</button>
      <p class="form-error" id="form-toy-error"></p>
    </form>
  </div>
</section>

<section id="screen-form-tugilgan-kun" class="screen">
  <button class="btn-back" data-back="screen-templates">&larr; Orqaga</button>
  <div class="form-wrap">
    <p class="eyebrow">2-qadam</p>
    <h2 class="section-title">Tug'ilgan kun ma'lumotlari</h2>
    <form id="form-tugilgan-kun" class="app-form">
      <label>Kimning tug'ilgan kuni?<input type="text" name="ism" placeholder="Malika" required></label>
      <label>Necha yosh to'ladi (ixtiyoriy)<input type="number" name="yosh" placeholder="18" min="0"></label>
      <div class="row-2">
        <label>Sana<input type="date" name="sana" required></label>
        <label>Vaqt<input type="time" name="vaqt" required></label>
      </div>
      <label>Manzil<input type="text" name="manzil" placeholder="Toshkent, restoran nomi" required></label>
      <div class="map-field">
        <span class="map-field-label">Manzil xaritada (ixtiyoriy)</span>
        <input type="hidden" name="xarita_link" id="xarita-tugilgan-kun">
        <button type="button" class="btn-map-pick" id="xarita-tugilgan-kun-btn" data-target="xarita-tugilgan-kun">📍 Xaritadan joy tanlash</button>
        <p class="map-preview" id="xarita-tugilgan-kun-preview"></p>
      </div>
      <label>Tabrik matni (ixtiyoriy)<input type="text" name="xabar" placeholder="Kelib, quvonchimizga sherik bo'ling!"></label>
      <button type="submit" class="btn-primary" style="width:100%;margin-top:8px;">Noma yaratish</button>
      <p class="form-error" id="form-tugilgan-kun-error"></p>
    </form>
  </div>
</section>

<section id="screen-form-tushuntirish" class="screen">
  <button class="btn-back" data-back="screen-templates">&larr; Orqaga</button>
  <div class="form-wrap">
    <p class="eyebrow">2-qadam</p>
    <h2 class="section-title">Tushuntirish xati</h2>
    <form id="form-tushuntirish" class="app-form">
      <label>Sarlavha<input type="text" name="sarlavha" placeholder="Tushuntirish xati" required></label>
      <label>Kimga<input type="text" name="kimga" placeholder="Maktab direktoriga / Bo'lim boshlig'iga" required></label>
      <label>Matn<textarea name="matn" rows="6" placeholder="Xat matnini shu yerga yozing..." required></textarea></label>
      <label>Kimdan (imzo)<input type="text" name="kimdan" placeholder="Ism Familiya" required></label>
      <label>Sana<input type="date" name="sana" required></label>
      <button type="submit" class="btn-primary" style="width:100%;margin-top:8px;">Noma yaratish</button>
      <p class="form-error" id="form-tushuntirish-error"></p>
    </form>
  </div>
</section>


<section id="screen-form-eslatma" class="screen">
  <button class="btn-back" data-back="screen-templates">&larr; Orqaga</button>
  <div class="form-wrap">
    <p class="eyebrow">2-qadam</p>
    <h2 class="section-title">Eslatma xati</h2>
    <form id="form-eslatma" class="app-form">
      <label>Sarlavha<input type="text" name="sarlavha" placeholder="Muddat yaqinlashmoqda" required></label>
      <label>Kimga<input type="text" name="kimga" placeholder="Hamma xodimlarga" required></label>
      <label>Eslatma matni<textarea name="matn" rows="5" placeholder="Nimani eslatmoqchisiz?" required></textarea></label>
      <label>Muddat (sana)<input type="date" name="muddat" required></label>
      <label>Kimdan<input type="text" name="kimdan" placeholder="Ism Familiya" required></label>
      <button type="submit" class="btn-primary" style="width:100%;margin-top:8px;">Noma yaratish</button>
      <p class="form-error" id="form-eslatma-error"></p>
    </form>
  </div>
</section>


<section id="screen-form-kafolat" class="screen">
  <button class="btn-back" data-back="screen-templates">&larr; Orqaga</button>
  <div class="form-wrap">
    <p class="eyebrow">2-qadam</p>
    <h2 class="section-title">Kafolat xati</h2>
    <form id="form-kafolat" class="app-form">
      <label>Mahsulot yoki xizmat nomi<input type="text" name="mahsulot" placeholder="Noutbuk ta'mirlash xizmati" required></label>
      <label>Mijoz ismi<input type="text" name="mijoz" placeholder="Ism Familiya" required></label>
      <div class="row-2">
        <label>Kafolat muddati<input type="text" name="muddat" placeholder="12 oy" required></label>
        <label>Berilgan sana<input type="date" name="sana" required></label>
      </div>
      <label>Shartlar (ixtiyoriy)<textarea name="shartlar" rows="4" placeholder="Kafolat qanday hollarda amal qiladi..."></textarea></label>
      <label>Beruvchi tashkilot/shaxs<input type="text" name="beruvchi" placeholder="Kompaniya yoki ism" required></label>
      <button type="submit" class="btn-primary" style="width:100%;margin-top:8px;">Noma yaratish</button>
      <p class="form-error" id="form-kafolat-error"></p>
    </form>
  </div>
</section>


<section id="screen-form-ota-ona-kafolat" class="screen">
  <button class="btn-back" data-back="screen-templates">&larr; Orqaga</button>
  <div class="form-wrap">
    <p class="eyebrow">2-qadam</p>
    <h2 class="section-title">Ota-ona kafolat xati</h2>
    <form id="form-ota-ona-kafolat" class="app-form">
      <label>O'quvchi ismi<input type="text" name="oquvchi" placeholder="Ism Familiya" required></label>
      <label>Sinf/guruh<input type="text" name="sinf" placeholder="9-A sinf" required></label>
      <label>Maktab/muassasa nomi<input type="text" name="maktab" placeholder="12-maktab" required></label>
      <label>Ota-ona ismi<input type="text" name="otaona" placeholder="Ism Familiya" required></label>
      <label>Va'da matni<textarea name="vada" rows="4" placeholder="Farzandim intizomga rioya qilishiga, darslarga muntazam qatnashishiga va'da beraman..." required></textarea></label>
      <label>Sana<input type="date" name="sana" required></label>
      <button type="submit" class="btn-primary" style="width:100%;margin-top:8px;">Noma yaratish</button>
      <p class="form-error" id="form-ota-ona-kafolat-error"></p>
    </form>
  </div>
</section>


<section id="screen-form-tugilgan-kun-tabrik" class="screen">
  <button class="btn-back" data-back="screen-templates">&larr; Orqaga</button>
  <div class="form-wrap">
    <p class="eyebrow">2-qadam</p>
    <h2 class="section-title">Tug'ilgan kun tabrigi</h2>
    <form id="form-tugilgan-kun-tabrik" class="app-form">
      <label>Kimga (ism)<input type="text" name="kimga" placeholder="Malika" required></label>
      <label>Tabrik matni<textarea name="tabrik" rows="5" placeholder="Tug'ilgan kuning bilan! Baxtli, sog'lom va orzularing amalga oshadigan yil bo'lsin!" required></textarea></label>
      <label>Kimdan<input type="text" name="kimdan" placeholder="Ism Familiya" required></label>
      <button type="submit" class="btn-primary" style="width:100%;margin-top:8px;">Noma yaratish</button>
      <p class="form-error" id="form-tugilgan-kun-tabrik-error"></p>
    </form>
  </div>
</section>


<section id="screen-form-beshik" class="screen">
  <button class="btn-back" data-back="screen-templates">&larr; Orqaga</button>
  <div class="form-wrap">
    <p class="eyebrow">2-qadam</p>
    <h2 class="section-title">Beshik to'yi</h2>
    <form id="form-beshik" class="app-form">
      <label>Chaqaloq ismi<input type="text" name="chaqaloq" placeholder="Sardor" required></label>
      <label>Ota-ona ismi<input type="text" name="otaona" placeholder="Aziz va Nilufar" required></label>
      <div class="row-2">
        <label>Marosim sanasi<input type="date" name="sana" required></label>
        <label>Vaqt<input type="time" name="vaqt" required></label>
      </div>
      <label>Manzil<input type="text" name="manzil" placeholder="Toshkent, uy manzili" required></label>
      <div class="map-field">
        <span class="map-field-label">Manzil xaritada (ixtiyoriy)</span>
        <input type="hidden" name="xarita_link" id="xarita-beshik">
        <button type="button" class="btn-map-pick" id="xarita-beshik-btn" data-target="xarita-beshik">📍 Xaritadan joy tanlash</button>
        <p class="map-preview" id="xarita-beshik-preview"></p>
      </div>
      <button type="submit" class="btn-primary" style="width:100%;margin-top:8px;">Noma yaratish</button>
      <p class="form-error" id="form-beshik-error"></p>
    </form>
  </div>
</section>


<section id="screen-form-bitiruv" class="screen">
  <button class="btn-back" data-back="screen-templates">&larr; Orqaga</button>
  <div class="form-wrap">
    <p class="eyebrow">2-qadam</p>
    <h2 class="section-title">Bitiruv marosimi</h2>
    <form id="form-bitiruv" class="app-form">
      <label>Bitiruvchi ismi<input type="text" name="ism" placeholder="Sardor Aliyev" required></label>
      <label>Ta'lim muassasasi<input type="text" name="muassasa" placeholder="21-maktab / TATU" required></label>
      <div class="row-2">
        <label>Marosim sanasi<input type="date" name="sana" required></label>
        <label>Vaqt<input type="time" name="vaqt" required></label>
      </div>
      <label>Manzil<input type="text" name="manzil" placeholder="Aktlar zali, manzil" required></label>
      <div class="map-field">
        <span class="map-field-label">Manzil xaritada (ixtiyoriy)</span>
        <input type="hidden" name="xarita_link" id="xarita-bitiruv">
        <button type="button" class="btn-map-pick" id="xarita-bitiruv-btn" data-target="xarita-bitiruv">📍 Xaritadan joy tanlash</button>
        <p class="map-preview" id="xarita-bitiruv-preview"></p>
      </div>
      <button type="submit" class="btn-primary" style="width:100%;margin-top:8px;">Noma yaratish</button>
      <p class="form-error" id="form-bitiruv-error"></p>
    </form>
  </div>
</section>


<section id="screen-form-rasmiy" class="screen">
  <button class="btn-back" data-back="screen-templates">&larr; Orqaga</button>
  <div class="form-wrap">
    <p class="eyebrow">2-qadam</p>
    <h2 class="section-title">Rasmiy tadbir</h2>
    <form id="form-rasmiy" class="app-form">
      <label>Tadbir nomi<input type="text" name="tadbir" placeholder="Yillik konferensiya" required></label>
      <label>Tashkilotchi<input type="text" name="tashkilotchi" placeholder="Kompaniya nomi" required></label>
      <div class="row-2">
        <label>Sana<input type="date" name="sana" required></label>
        <label>Vaqt<input type="time" name="vaqt" required></label>
      </div>
      <label>Manzil<input type="text" name="manzil" placeholder="Konferensiya zali, manzil" required></label>
      <div class="map-field">
        <span class="map-field-label">Manzil xaritada (ixtiyoriy)</span>
        <input type="hidden" name="xarita_link" id="xarita-rasmiy">
        <button type="button" class="btn-map-pick" id="xarita-rasmiy-btn" data-target="xarita-rasmiy">📍 Xaritadan joy tanlash</button>
        <p class="map-preview" id="xarita-rasmiy-preview"></p>
      </div>
      <label>Qisqa tavsif (ixtiyoriy)<textarea name="tavsif" rows="3" placeholder="Tadbir haqida qisqacha..."></textarea></label>
      <button type="submit" class="btn-primary" style="width:100%;margin-top:8px;">Noma yaratish</button>
      <p class="form-error" id="form-rasmiy-error"></p>
    </form>
  </div>
</section>


<section id="screen-form-sevishganlar" class="screen">
  <button class="btn-back" data-back="screen-templates">&larr; Orqaga</button>
  <div class="form-wrap">
    <p class="eyebrow">2-qadam</p>
    <h2 class="section-title">Sevishganlar xati</h2>
    <form id="form-sevishganlar" class="app-form">
      <label>Kimga (sevgilingiz ismi)<input type="text" name="kimga" placeholder="Zarina" required></label>
      <label>Xat matni<textarea name="matn" rows="6" placeholder="Yuragimdagi gaplarni shu yerga yozing..." required></textarea></label>
      <label>Kimdan<input type="text" name="kimdan" placeholder="Ism" required></label>
      <button type="submit" class="btn-primary" style="width:100%;margin-top:8px;">Noma yaratish</button>
      <p class="form-error" id="form-sevishganlar-error"></p>
    </form>
  </div>
</section>


<section id="screen-form-vizitka" class="screen">
  <button class="btn-back" data-back="screen-templates">&larr; Orqaga</button>
  <div class="form-wrap">
    <p class="eyebrow">2-qadam</p>
    <h2 class="section-title">Vizitka ma'lumotlari</h2>
    <form id="form-vizitka" class="app-form">
      <label>Ism Familiya<input type="text" name="ism" placeholder="Sardor Aliyev" required></label>
      <label>Lavozim / kasb<input type="text" name="lavozim" placeholder="Veb-dasturchi" required></label>
      <label>Telefon<input type="text" name="telefon" placeholder="+998 90 123 45 67" required></label>
      <label>Email (ixtiyoriy)<input type="email" name="email" placeholder="sardor@mail.com"></label>
      <label>Ijtimoiy tarmoq / sayt (ixtiyoriy)<input type="text" name="tarmoq" placeholder="t.me/username yoki instagram"></label>
      <label>Qisqa tavsif (ixtiyoriy)<input type="text" name="tavsif" placeholder="Frontend va backend bo'yicha mutaxassis"></label>
      <button type="submit" class="btn-primary" style="width:100%;margin-top:8px;">Noma yaratish</button>
      <p class="form-error" id="form-vizitka-error"></p>
    </form>
  </div>
</section>


<section id="screen-form-rezyume" class="screen">
  <button class="btn-back" data-back="screen-templates">&larr; Orqaga</button>
  <div class="form-wrap">
    <p class="eyebrow">2-qadam</p>
    <h2 class="section-title">Rezyume / CV</h2>
    <form id="form-rezyume" class="app-form">
      <label>Ism Familiya<input type="text" name="ism" placeholder="Sardor Aliyev" required></label>
      <label>Lavozim / maqsad<input type="text" name="lavozim" placeholder="Backend dasturchi" required></label>
      <div class="row-2">
        <label>Telefon<input type="text" name="telefon" placeholder="+998 90 123 45 67" required></label>
        <label>Email<input type="email" name="email" placeholder="sardor@mail.com"></label>
      </div>
      <label>Ish tajribasi<textarea name="tajriba" rows="4" placeholder="2023-2026: ABC kompaniyasida backend dasturchi..." required></textarea></label>
      <label>Ko'nikmalar (ixtiyoriy)<textarea name="konikmalar" rows="3" placeholder="Python, FastAPI, SQL, Git..."></textarea></label>
      <button type="submit" class="btn-primary" style="width:100%;margin-top:8px;">Noma yaratish</button>
      <p class="form-error" id="form-rezyume-error"></p>
    </form>
  </div>
</section>


<section id="screen-form-minnatdorchilik" class="screen">
  <button class="btn-back" data-back="screen-templates">&larr; Orqaga</button>
  <div class="form-wrap">
    <p class="eyebrow">2-qadam</p>
    <h2 class="section-title">Minnatdorchilik xati</h2>
    <form id="form-minnatdorchilik" class="app-form">
      <label>Kimga<input type="text" name="kimga" placeholder="Jamoa a'zosi yoki hamkor ismi" required></label>
      <label>Xat matni<textarea name="matn" rows="5" placeholder="Sizning mehnatingiz va sadoqatingiz uchun minnatdormiz..." required></textarea></label>
      <label>Kimdan<input type="text" name="kimdan" placeholder="Ism Familiya yoki kompaniya" required></label>
      <label>Sana<input type="date" name="sana" required></label>
      <button type="submit" class="btn-primary" style="width:100%;margin-top:8px;">Noma yaratish</button>
      <p class="form-error" id="form-minnatdorchilik-error"></p>
    </form>
  </div>
</section>


<section id="screen-result" class="screen">
  <div class="result-wrap">
    <p class="eyebrow">Tayyor</p>

    <h2 class="section-title">Noma yaratildi</h2>
    <p class="result-sub">Havolani mehmonlaringizga yuboring:</p>
    <div class="result-link-box">
      <input type="text" id="result-link" readonly>
      <button id="btn-copy" class="btn-primary">Nusxalash</button>
    </div>
    <a id="btn-view" href="#" target="_blank" class="btn-view-link">Sahifani ko'rish &rarr;</a>
    <p style="margin-top:20px;"><button class="btn-back" data-back="screen-templates" style="position:static;">&larr; Yana noma yaratish</button></p>
  </div>
</section>

<p class="site-footer">Yaratuvchi: Ilhomjonov Shahzodbek</p>

<div id="map-modal" class="map-modal">
  <div class="map-modal-inner">
    <p class="map-modal-hint">Xaritada manzilni bosib belgilang</p>
    <div id="map-picker"></div>
    <div class="map-modal-actions">
      <button type="button" id="map-cancel" class="btn-primary" style="background:transparent;border:1px solid var(--ink);color:var(--ink);box-shadow:none;">Bekor qilish</button>
      <button type="button" id="map-confirm" class="btn-primary">Tanlash</button>
    </div>
  </div>
</div>

<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

// --- Orqaga tugmalari ---
document.querySelectorAll('.btn-back[data-back]').forEach(btn => {
  btn.addEventListener('click', () => showScreen(btn.dataset.back));
});

const slides = document.querySelectorAll('.explain-slide');
const dots = document.querySelectorAll('.dot-i');
let currentSlide = 0;

function setSlide(i) {
  slides.forEach(s => s.classList.remove('active'));
  dots.forEach(d => d.classList.remove('active'));
  slides[i].classList.add('active');
  dots[i].classList.add('active');
  currentSlide = i;
}
setSlide(0);

document.getElementById('btn-continue').addEventListener('click', () => {
  if (currentSlide < slides.length - 1) { setSlide(currentSlide + 1); }
  else { showScreen('screen-templates'); }
});

const tplCards = document.querySelectorAll('.tpl-card');
const nextNote = document.getElementById('next-note');

tplCards.forEach(card => {
  card.addEventListener('click', () => {
    tplCards.forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    const tplName = card.querySelector('.tpl-name').textContent;
    const tpl = card.dataset.tpl;
    if (tpl === 'toy') { showScreen('screen-form-toy'); }
    else if (tpl === 'tugilgan-kun') { showScreen('screen-form-tugilgan-kun'); }
    else if (tpl === 'tushuntirish') { showScreen('screen-form-tushuntirish'); }
    else if (tpl === 'eslatma') { showScreen('screen-form-eslatma'); }
    else if (tpl === 'kafolat') { showScreen('screen-form-kafolat'); }
    else if (tpl === 'ota-ona-kafolat') { showScreen('screen-form-ota-ona-kafolat'); }
    else if (tpl === 'tugilgan-kun-tabrik') { showScreen('screen-form-tugilgan-kun-tabrik'); }
    else if (tpl === 'beshik') { showScreen('screen-form-beshik'); }
    else if (tpl === 'bitiruv') { showScreen('screen-form-bitiruv'); }
    else if (tpl === 'rasmiy') { showScreen('screen-form-rasmiy'); }
    else if (tpl === 'sevishganlar') { showScreen('screen-form-sevishganlar'); }
    else if (tpl === 'vizitka') { showScreen('screen-form-vizitka'); }
    else if (tpl === 'rezyume') { showScreen('screen-form-rezyume'); }
    else if (tpl === 'minnatdorchilik') { showScreen('screen-form-minnatdorchilik'); }
    else { nextNote.textContent = `"${tplName}" formasi tez orada qo'shiladi.`; }
  });
});

// --- Har bir formaga "Fon musiqasi", "Rasm" va "Rang" maydonlarini avtomatik qo'shish ---
const defaultAccentColors = {
  'form-toy': '#5C7A5E',
  'form-tugilgan-kun': '#E8724C',
  'form-tushuntirish': '#2B3A55',
  'form-eslatma': '#92702A',
  'form-kafolat': '#C9A84C',
  'form-ota-ona-kafolat': '#2C4A73',
  'form-tugilgan-kun-tabrik': '#B0459A',
  'form-beshik': '#8E7CC3',
  'form-bitiruv': '#D4AF37',
  'form-rasmiy': '#2455A4',
  'form-sevishganlar': '#B0475F',
  'form-vizitka': '#4A9B8E',
  'form-rezyume': '#2C4A6B',
  'form-minnatdorchilik': '#B9862F'
};

document.querySelectorAll('.app-form').forEach(form => {
  const submitBtn = form.querySelector('button[type="submit"]');
  if (!submitBtn) return;

  if (!form.querySelector('[name="rang"]')) {
    const defaultColor = defaultAccentColors[form.id] || '#B8905A';
    const colorWrap = document.createElement('label');
    colorWrap.className = 'color-field';
    colorWrap.innerHTML =
      'Asosiy rang (ixtiyoriy)' +
      '<input type="color" name="rang" value="' + defaultColor + '">';
    form.insertBefore(colorWrap, submitBtn);
  }

  if (!form.querySelector('[name="musiqa"]')) {
    const musicWrap = document.createElement('div');
    musicWrap.className = 'photo-field';
    musicWrap.innerHTML =
      '<span class="map-field-label">Fon musiqasi (ixtiyoriy)</span>' +
      '<input type="hidden" name="musiqa">' +
      '<input type="file" class="music-file-input" accept="audio/*">' +
      '<input type="url" class="music-url-input" placeholder="yoki musiqa havolasi (URL)">' +
      '<p class="photo-preview-note"></p>';
    form.insertBefore(musicWrap, submitBtn);

    const musicHidden = musicWrap.querySelector('[name="musiqa"]');
    const musicFileInput = musicWrap.querySelector('.music-file-input');
    const musicUrlInput = musicWrap.querySelector('.music-url-input');
    const musicNote = musicWrap.querySelector('.photo-preview-note');

    musicFileInput.addEventListener('change', () => {
      const file = musicFileInput.files && musicFileInput.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        musicHidden.value = reader.result;
        musicUrlInput.value = '';
        musicNote.textContent = "Musiqa tanlandi: " + file.name;
      };
      reader.readAsDataURL(file);
    });

    musicUrlInput.addEventListener('input', () => {
      if (musicUrlInput.value.trim()) {
        musicHidden.value = musicUrlInput.value.trim();
        musicFileInput.value = '';
        musicNote.textContent = 'Havola orqali musiqa qo\u2019shiladi.';
      } else if (!musicFileInput.files.length) {
        musicHidden.value = '';
        musicNote.textContent = '';
      }
    });
  }

  if (!form.querySelector('[name="rasm"]')) {
    const wrap = document.createElement('div');
    wrap.className = 'photo-field';
    wrap.innerHTML =
      '<span class="map-field-label">Rasm (ixtiyoriy)</span>' +
      '<input type="hidden" name="rasm">' +
      '<input type="file" class="photo-file-input" accept="image/*">' +
      '<input type="url" class="photo-url-input" placeholder="yoki rasm havolasi (URL)">' +
      '<p class="photo-preview-note"></p>';
    form.insertBefore(wrap, submitBtn);

    const hiddenInput = wrap.querySelector('[name="rasm"]');
    const fileInput = wrap.querySelector('.photo-file-input');
    const urlInput = wrap.querySelector('.photo-url-input');
    const note = wrap.querySelector('.photo-preview-note');

    fileInput.addEventListener('change', () => {
      const file = fileInput.files && fileInput.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = () => {
        hiddenInput.value = reader.result;
        urlInput.value = '';
        note.textContent = "Rasm tanlandi: " + file.name;
      };
      reader.readAsDataURL(file);
    });

    urlInput.addEventListener('input', () => {
      if (urlInput.value.trim()) {
        hiddenInput.value = urlInput.value.trim();
        fileInput.value = '';
        note.textContent = 'Havola orqali rasm qo\u2019shiladi.';
      } else if (!fileInput.files.length) {
        hiddenInput.value = '';
        note.textContent = '';
      }
    });
  }
});

function setupForm(formId, errorId, apiPath) {
  const form = document.getElementById(formId);
  const errorEl = document.getElementById(errorId);

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorEl.textContent = '';
    const data = Object.fromEntries(new FormData(form).entries());
    try {
      const res = await fetch(apiPath, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) {
        const err = await res.json();
        errorEl.textContent = err.detail || "Xatolik yuz berdi, qayta urinib ko'ring.";
        return;
      }
      const result = await res.json();
      const fullUrl = window.location.origin + result.url;
      document.getElementById('result-link').value = fullUrl;
      document.getElementById('btn-view').href = fullUrl;
      showScreen('screen-result');
    } catch (err) {
      errorEl.textContent = "Internet aloqasida muammo, qayta urinib ko'ring.";
    }
  });
}

setupForm('form-toy', 'form-toy-error', '/api/create/toy');
setupForm('form-tugilgan-kun', 'form-tugilgan-kun-error', '/api/create/tugilgan-kun');
setupForm('form-tushuntirish', 'form-tushuntirish-error', '/api/create/tushuntirish');
setupForm('form-eslatma', 'form-eslatma-error', '/api/create/eslatma');
setupForm('form-kafolat', 'form-kafolat-error', '/api/create/kafolat');
setupForm('form-ota-ona-kafolat', 'form-ota-ona-kafolat-error', '/api/create/ota-ona-kafolat');
setupForm('form-tugilgan-kun-tabrik', 'form-tugilgan-kun-tabrik-error', '/api/create/tugilgan-kun-tabrik');
setupForm('form-beshik', 'form-beshik-error', '/api/create/beshik');
setupForm('form-bitiruv', 'form-bitiruv-error', '/api/create/bitiruv');
setupForm('form-rasmiy', 'form-rasmiy-error', '/api/create/rasmiy');
setupForm('form-sevishganlar', 'form-sevishganlar-error', '/api/create/sevishganlar');
setupForm('form-vizitka', 'form-vizitka-error', '/api/create/vizitka');
setupForm('form-rezyume', 'form-rezyume-error', '/api/create/rezyume');
setupForm('form-minnatdorchilik', 'form-minnatdorchilik-error', '/api/create/minnatdorchilik');

// --- Xaritadan joy tanlash ---
let mapInstance = null;
let mapMarker = null;
let currentMapTarget = null;

function ensureMapInitialized() {
  if (mapInstance) return;
  mapInstance = L.map('map-picker').setView([41.311081, 69.240562], 12);
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    attribution: 'Tiles &copy; Esri'
  }).addTo(mapInstance);
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
  }).addTo(mapInstance);
  mapInstance.on('click', function (e) {
    if (mapMarker) { mapInstance.removeLayer(mapMarker); }
    mapMarker = L.marker(e.latlng).addTo(mapInstance);
  });
}

document.querySelectorAll('.btn-map-pick').forEach(btn => {
  btn.addEventListener('click', () => {
    currentMapTarget = btn.dataset.target;
    document.getElementById('map-modal').classList.add('active');
    ensureMapInitialized();
    setTimeout(() => mapInstance.invalidateSize(), 150);
  });
});

document.getElementById('map-cancel').addEventListener('click', () => {
  document.getElementById('map-modal').classList.remove('active');
});

document.getElementById('map-confirm').addEventListener('click', () => {
  if (!mapMarker) {
    alert('Iltimos, avval xaritada joyni bosib belgilang.');
    return;
  }
  const latlng = mapMarker.getLatLng();
  const link = `https://www.google.com/maps?q=${latlng.lat.toFixed(6)},${latlng.lng.toFixed(6)}`;
  document.getElementById(currentMapTarget).value = link;
  document.getElementById(currentMapTarget + '-preview').textContent = `Tanlandi: ${latlng.lat.toFixed(5)}, ${latlng.lng.toFixed(5)}`;
  document.getElementById(currentMapTarget + '-btn').textContent = "📍 Joyni o'zgartirish";
  document.getElementById('map-modal').classList.remove('active');
});

document.getElementById('btn-copy').addEventListener('click', () => {
  const input = document.getElementById('result-link');
  input.select();
  navigator.clipboard.writeText(input.value);
  const btn = document.getElementById('btn-copy');
  const original = btn.textContent;
  btn.textContent = 'Nusxalandi ✓';
  setTimeout(() => { btn.textContent = original; }, 1500);
});
</script>
</body>
</html>"""


@app.get("/yaratish", response_class=HTMLResponse)
def home():
    return HOME_PAGE


# ============================================================
#  TO'Y TAKLIFNOMASI — FORMA VA NATIJA
# ============================================================

class ToyForm(BaseModel):
    kuyov: str
    kelin: str
    sana: str
    vaqt: str
    manzil: str
    xarita_link: str = ""
    musiqa: str = ""
    rasm: str = ""
    rang: str = ""


@app.post("/api/create/toy")
def create_toy(form: ToyForm):
    if not form.kuyov.strip() or not form.kelin.strip() or not form.sana or not form.manzil.strip():
        raise HTTPException(status_code=400, detail="Kerakli maydonlar to'ldirilmagan")

    base = slugify(f"{form.kuyov}-{form.kelin}")
    slug = unique_slug(base)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pages (template_type, slug, data) VALUES (?, ?, ?)",
        ("toy", slug, json.dumps(form.dict(), ensure_ascii=False)),
    )
    conn.commit()
    conn.close()

    return {"slug": slug, "url": f"/n/{slug}"}


# ============================================================
#  TUG'ILGAN KUN — FORMA VA NATIJA
# ============================================================

class BirthdayForm(BaseModel):
    ism: str
    yosh: str = ""
    sana: str
    vaqt: str
    manzil: str
    xarita_link: str = ""
    xabar: str = ""
    musiqa: str = ""
    rasm: str = ""
    rang: str = ""


@app.post("/api/create/tugilgan-kun")
def create_birthday(form: BirthdayForm):
    if not form.ism.strip() or not form.sana or not form.manzil.strip():
        raise HTTPException(status_code=400, detail="Kerakli maydonlar to'ldirilmagan")

    base = slugify(f"{form.ism}-tugilgan-kun")
    slug = unique_slug(base)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pages (template_type, slug, data) VALUES (?, ?, ?)",
        ("tugilgan-kun", slug, json.dumps(form.dict(), ensure_ascii=False)),
    )
    conn.commit()
    conn.close()

    return {"slug": slug, "url": f"/n/{slug}"}


# ============================================================
#  TUSHUNTIRISH XATI — FORMA VA NATIJA
# ============================================================

class ExplanationForm(BaseModel):
    sarlavha: str
    kimga: str
    matn: str
    kimdan: str
    sana: str
    musiqa: str = ""
    rasm: str = ""
    rang: str = ""


@app.post("/api/create/tushuntirish")
def create_explanation(form: ExplanationForm):
    if not form.sarlavha.strip() or not form.kimga.strip() or not form.matn.strip() or not form.kimdan.strip():
        raise HTTPException(status_code=400, detail="Kerakli maydonlar to'ldirilmagan")

    base = slugify(f"{form.kimdan}-xati")
    slug = unique_slug(base)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pages (template_type, slug, data) VALUES (?, ?, ?)",
        ("tushuntirish", slug, json.dumps(form.dict(), ensure_ascii=False)),
    )
    conn.commit()
    conn.close()

    return {"slug": slug, "url": f"/n/{slug}"}


# ============================================================
#  ESLATMA XATI — FORMA VA NATIJA
# ============================================================

class ReminderForm(BaseModel):
    sarlavha: str
    kimga: str
    matn: str
    muddat: str
    kimdan: str
    musiqa: str = ""
    rasm: str = ""
    rang: str = ""


@app.post("/api/create/eslatma")
def create_reminder(form: ReminderForm):
    if not form.sarlavha.strip() or not form.kimga.strip() or not form.matn.strip() or not form.muddat or not form.kimdan.strip():
        raise HTTPException(status_code=400, detail="Kerakli maydonlar to'ldirilmagan")

    base = slugify(f"{form.kimdan}-eslatma")
    slug = unique_slug(base)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pages (template_type, slug, data) VALUES (?, ?, ?)",
        ("eslatma", slug, json.dumps(form.dict(), ensure_ascii=False)),
    )
    conn.commit()
    conn.close()

    return {"slug": slug, "url": f"/n/{slug}"}


# ============================================================
#  KAFOLAT XATI — FORMA VA NATIJA
# ============================================================

class GuaranteeForm(BaseModel):
    mahsulot: str
    mijoz: str
    muddat: str
    sana: str
    shartlar: str = ""
    beruvchi: str
    musiqa: str = ""
    rasm: str = ""
    rang: str = ""


@app.post("/api/create/kafolat")
def create_guarantee(form: GuaranteeForm):
    if not form.mahsulot.strip() or not form.mijoz.strip() or not form.muddat.strip() or not form.sana or not form.beruvchi.strip():
        raise HTTPException(status_code=400, detail="Kerakli maydonlar to'ldirilmagan")

    base = slugify(f"{form.beruvchi}-kafolat")
    slug = unique_slug(base)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pages (template_type, slug, data) VALUES (?, ?, ?)",
        ("kafolat", slug, json.dumps(form.dict(), ensure_ascii=False)),
    )
    conn.commit()
    conn.close()

    return {"slug": slug, "url": f"/n/{slug}"}


# ============================================================
#  OTA-ONA KAFOLAT XATI — FORMA VA NATIJA
# ============================================================

class ParentGuaranteeForm(BaseModel):
    oquvchi: str
    sinf: str
    maktab: str
    otaona: str
    vada: str
    sana: str
    musiqa: str = ""
    rasm: str = ""
    rang: str = ""


@app.post("/api/create/ota-ona-kafolat")
def create_parent_guarantee(form: ParentGuaranteeForm):
    if not form.oquvchi.strip() or not form.maktab.strip() or not form.otaona.strip() or not form.vada.strip() or not form.sana:
        raise HTTPException(status_code=400, detail="Kerakli maydonlar to'ldirilmagan")

    base = slugify(f"{form.oquvchi}-kafolat")
    slug = unique_slug(base)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pages (template_type, slug, data) VALUES (?, ?, ?)",
        ("ota-ona-kafolat", slug, json.dumps(form.dict(), ensure_ascii=False)),
    )
    conn.commit()
    conn.close()

    return {"slug": slug, "url": f"/n/{slug}"}


# ============================================================
#  TUG'ILGAN KUN TABRIGI — FORMA VA NATIJA
# ============================================================

class BirthdayGreetingForm(BaseModel):
    kimga: str
    tabrik: str
    kimdan: str
    musiqa: str = ""
    rasm: str = ""
    rang: str = ""


@app.post("/api/create/tugilgan-kun-tabrik")
def create_birthday_greeting(form: BirthdayGreetingForm):
    if not form.kimga.strip() or not form.tabrik.strip() or not form.kimdan.strip():
        raise HTTPException(status_code=400, detail="Kerakli maydonlar to'ldirilmagan")

    base = slugify(f"{form.kimga}-tabrik")
    slug = unique_slug(base)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pages (template_type, slug, data) VALUES (?, ?, ?)",
        ("tugilgan-kun-tabrik", slug, json.dumps(form.dict(), ensure_ascii=False)),
    )
    conn.commit()
    conn.close()

    return {"slug": slug, "url": f"/n/{slug}"}


# ============================================================
#  BESHIK TO'YI — FORMA VA NATIJA
# ============================================================

class CradleForm(BaseModel):
    chaqaloq: str
    otaona: str
    sana: str
    vaqt: str
    manzil: str
    xarita_link: str = ""
    musiqa: str = ""
    rasm: str = ""
    rang: str = ""


@app.post("/api/create/beshik")
def create_cradle(form: CradleForm):
    if not form.chaqaloq.strip() or not form.otaona.strip() or not form.sana or not form.manzil.strip():
        raise HTTPException(status_code=400, detail="Kerakli maydonlar to'ldirilmagan")

    base = slugify(f"{form.chaqaloq}-beshik-toyi")
    slug = unique_slug(base)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pages (template_type, slug, data) VALUES (?, ?, ?)",
        ("beshik", slug, json.dumps(form.dict(), ensure_ascii=False)),
    )
    conn.commit()
    conn.close()

    return {"slug": slug, "url": f"/n/{slug}"}


# ============================================================
#  BITIRUV MAROSIMI — FORMA VA NATIJA
# ============================================================

class GraduationForm(BaseModel):
    ism: str
    muassasa: str
    sana: str
    vaqt: str
    manzil: str
    xarita_link: str = ""
    musiqa: str = ""
    rasm: str = ""
    rang: str = ""


@app.post("/api/create/bitiruv")
def create_graduation(form: GraduationForm):
    if not form.ism.strip() or not form.muassasa.strip() or not form.sana or not form.manzil.strip():
        raise HTTPException(status_code=400, detail="Kerakli maydonlar to'ldirilmagan")

    base = slugify(f"{form.ism}-bitiruv")
    slug = unique_slug(base)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pages (template_type, slug, data) VALUES (?, ?, ?)",
        ("bitiruv", slug, json.dumps(form.dict(), ensure_ascii=False)),
    )
    conn.commit()
    conn.close()

    return {"slug": slug, "url": f"/n/{slug}"}


# ============================================================
#  RASMIY TADBIR — FORMA VA NATIJA
# ============================================================

class OfficialEventForm(BaseModel):
    tadbir: str
    tashkilotchi: str
    sana: str
    vaqt: str
    manzil: str
    xarita_link: str = ""
    tavsif: str = ""
    musiqa: str = ""
    rasm: str = ""
    rang: str = ""


@app.post("/api/create/rasmiy")
def create_official_event(form: OfficialEventForm):
    if not form.tadbir.strip() or not form.tashkilotchi.strip() or not form.sana or not form.manzil.strip():
        raise HTTPException(status_code=400, detail="Kerakli maydonlar to'ldirilmagan")

    base = slugify(f"{form.tadbir}")
    slug = unique_slug(base)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pages (template_type, slug, data) VALUES (?, ?, ?)",
        ("rasmiy", slug, json.dumps(form.dict(), ensure_ascii=False)),
    )
    conn.commit()
    conn.close()

    return {"slug": slug, "url": f"/n/{slug}"}


# ============================================================
#  SEVISHGANLAR XATI — FORMA VA NATIJA
# ============================================================

class LoveLetterForm(BaseModel):
    kimga: str
    matn: str
    kimdan: str
    musiqa: str = ""
    rasm: str = ""
    rang: str = ""


@app.post("/api/create/sevishganlar")
def create_love_letter(form: LoveLetterForm):
    if not form.kimga.strip() or not form.matn.strip() or not form.kimdan.strip():
        raise HTTPException(status_code=400, detail="Kerakli maydonlar to'ldirilmagan")

    base = slugify(f"{form.kimdan}-{form.kimga}-xat")
    slug = unique_slug(base)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pages (template_type, slug, data) VALUES (?, ?, ?)",
        ("sevishganlar", slug, json.dumps(form.dict(), ensure_ascii=False)),
    )
    conn.commit()
    conn.close()

    return {"slug": slug, "url": f"/n/{slug}"}


# ============================================================
#  VIZITKA — FORMA VA NATIJA
# ============================================================

class VizitkaForm(BaseModel):
    ism: str
    lavozim: str
    telefon: str
    email: str = ""
    tarmoq: str = ""
    tavsif: str = ""
    musiqa: str = ""
    rasm: str = ""
    rang: str = ""


@app.post("/api/create/vizitka")
def create_vizitka(form: VizitkaForm):
    if not form.ism.strip() or not form.lavozim.strip() or not form.telefon.strip():
        raise HTTPException(status_code=400, detail="Kerakli maydonlar to'ldirilmagan")

    base = slugify(f"{form.ism}-vizitka")
    slug = unique_slug(base)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pages (template_type, slug, data) VALUES (?, ?, ?)",
        ("vizitka", slug, json.dumps(form.dict(), ensure_ascii=False)),
    )
    conn.commit()
    conn.close()

    return {"slug": slug, "url": f"/n/{slug}"}


# ============================================================
#  REZYUME / CV — FORMA VA NATIJA
# ============================================================

class ResumeForm(BaseModel):
    ism: str
    lavozim: str
    telefon: str
    email: str = ""
    tajriba: str
    konikmalar: str = ""
    musiqa: str = ""
    rasm: str = ""
    rang: str = ""


@app.post("/api/create/rezyume")
def create_resume(form: ResumeForm):
    if not form.ism.strip() or not form.lavozim.strip() or not form.telefon.strip() or not form.tajriba.strip():
        raise HTTPException(status_code=400, detail="Kerakli maydonlar to'ldirilmagan")

    base = slugify(f"{form.ism}-rezyume")
    slug = unique_slug(base)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pages (template_type, slug, data) VALUES (?, ?, ?)",
        ("rezyume", slug, json.dumps(form.dict(), ensure_ascii=False)),
    )
    conn.commit()
    conn.close()

    return {"slug": slug, "url": f"/n/{slug}"}


# ============================================================
#  MINNATDORCHILIK XATI — FORMA VA NATIJA
# ============================================================

class ThanksForm(BaseModel):
    kimga: str
    matn: str
    kimdan: str
    sana: str
    musiqa: str = ""
    rasm: str = ""
    rang: str = ""


@app.post("/api/create/minnatdorchilik")
def create_thanks(form: ThanksForm):
    if not form.kimga.strip() or not form.matn.strip() or not form.kimdan.strip() or not form.sana:
        raise HTTPException(status_code=400, detail="Kerakli maydonlar to'ldirilmagan")

    base = slugify(f"{form.kimdan}-minnatdorchilik")
    slug = unique_slug(base)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pages (template_type, slug, data) VALUES (?, ?, ?)",
        ("minnatdorchilik", slug, json.dumps(form.dict(), ensure_ascii=False)),
    )
    conn.commit()
    conn.close()

    return {"slug": slug, "url": f"/n/{slug}"}


@app.get("/n/{slug}", response_class=HTMLResponse)
def view_page(slug: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT template_type, data FROM pages WHERE slug = ?", (slug,))
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Bunday noma topilmadi")

    template_type, data_json = row
    data = json.loads(data_json)

    if template_type == "toy":
        html = render_toy_page(data)
    elif template_type == "tugilgan-kun":
        html = render_birthday_page(data)
    elif template_type == "tushuntirish":
        html = render_explanation_page(data)
    elif template_type == "eslatma":
        html = render_reminder_page(data)
    elif template_type == "kafolat":
        html = render_guarantee_page(data)
    elif template_type == "ota-ona-kafolat":
        html = render_parent_guarantee_page(data)
    elif template_type == "tugilgan-kun-tabrik":
        html = render_birthday_greeting_page(data)
    elif template_type == "beshik":
        html = render_cradle_page(data)
    elif template_type == "bitiruv":
        html = render_graduation_page(data)
    elif template_type == "rasmiy":
        html = render_official_event_page(data)
    elif template_type == "sevishganlar":
        html = render_love_letter_page(data)
    elif template_type == "vizitka":
        html = render_vizitka_page(data)
    elif template_type == "rezyume":
        html = render_resume_page(data)
    elif template_type == "minnatdorchilik":
        html = render_thanks_page(data)
    else:
        raise HTTPException(status_code=404, detail="Noma turi topilmadi")

    html = inject_photo(html, data)
    html = inject_music_player(html, data)
    return inject_action_bar(html)


def inject_photo(html: str, data: dict) -> str:
    rasm = (data.get("rasm") or "").strip()
    if not rasm:
        return html

    safe_src = rasm.replace('"', "&quot;")
    photo_css = (
        '<style>.pg-photo{width:112px;height:112px;border-radius:50%;'
        "object-fit:cover;display:block;margin:0 auto 22px;"
        "box-shadow:0 10px 28px rgba(0,0,0,0.22);"
        'border:3px solid rgba(255,255,255,0.85);}</style>'
    )
    if "</head>" in html:
        html = html.replace("</head>", photo_css + "</head>", 1)
    else:
        html = photo_css + html

    photo_html = f'<img src="{safe_src}" alt="rasm" class="pg-photo">'
    body_idx = html.find("<body>")
    if body_idx == -1:
        return html
    div_idx = html.find("<div", body_idx)
    if div_idx == -1:
        return html
    tag_end = html.find(">", div_idx)
    if tag_end == -1:
        return html
    insertion_point = tag_end + 1
    return html[:insertion_point] + photo_html + html[insertion_point:]


def inject_music_player(html: str, data: dict) -> str:
    musiqa = (data.get("musiqa") or "").strip()
    if not musiqa:
        return html

    safe_url = musiqa.replace('"', "&quot;")
    player = f"""
<audio id="pg-bg-audio" src="{safe_url}" loop preload="auto"></audio>
<button class="pg-music-btn" id="pg-music-toggle" type="button" aria-label="Musiqa">
  <svg id="pg-music-icon" viewBox="0 0 24 24" fill="none"><path d="M9 18V5l12-2v13" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/><circle cx="6" cy="18" r="3" stroke="currentColor" stroke-width="1.6"/><circle cx="18" cy="16" r="3" stroke="currentColor" stroke-width="1.6"/></svg>
</button>
<style>
  .pg-music-btn {{
    position: fixed; top: 18px; right: 18px; z-index: 70;
    width: 42px; height: 42px; border-radius: 50%; border: none; cursor: pointer;
    background: rgba(15,17,22,0.85); color: rgba(255,255,255,0.85);
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 6px 18px rgba(0,0,0,0.25); backdrop-filter: blur(8px);
    transition: background 0.15s ease;
  }}
  .pg-music-btn:hover {{ background: rgba(30,33,40,0.95); }}
  .pg-music-btn svg {{ width: 18px; height: 18px; }}
  .pg-music-btn.muted {{ opacity: 0.55; }}
  @keyframes pg-pulse {{ 0%,100% {{ transform: scale(1); }} 50% {{ transform: scale(1.08); }} }}
  .pg-music-btn.playing {{ animation: pg-pulse 1.6s ease-in-out infinite; }}
  @media print {{ .pg-music-btn {{ display: none !important; }} }}
</style>
<script>
(function () {{
  var audio = document.getElementById('pg-bg-audio');
  var btn = document.getElementById('pg-music-toggle');
  var playing = false;

  function tryAutoplay() {{
    audio.volume = 0.55;
    audio.play().then(function () {{
      playing = true;
      btn.classList.add('playing');
      btn.classList.remove('muted');
    }}).catch(function () {{
      playing = false;
      btn.classList.add('muted');
    }});
  }}

  btn.addEventListener('click', function () {{
    if (playing) {{
      audio.pause();
      playing = false;
      btn.classList.remove('playing');
      btn.classList.add('muted');
    }} else {{
      audio.play().then(function () {{
        playing = true;
        btn.classList.add('playing');
        btn.classList.remove('muted');
      }}).catch(function () {{}});
    }}
  }});

  tryAutoplay();
  document.addEventListener('click', function onceUnlock() {{
    if (!playing) {{ tryAutoplay(); }}
    document.removeEventListener('click', onceUnlock);
  }}, {{ once: true }});
}})();
</script>
"""
    if "</body>" in html:
        return html.replace("</body>", player + "</body>", 1)
    return html + player


ACTION_BAR_BLOCK = r"""
<div class="pg-action-bar" id="pg-action-bar">
  <button class="pg-btn" id="pg-print-btn" type="button" aria-label="Chop etish">
    <svg viewBox="0 0 24 24" fill="none"><path d="M6 9V3h12v6M6 18H4a1 1 0 0 1-1-1v-6a1 1 0 0 1 1-1h16a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1h-2M6 14h12v7H6v-7Z" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
    <span>Chop etish</span>
  </button>
  <button class="pg-btn" id="pg-download-btn" type="button" aria-label="Yuklab olish">
    <svg viewBox="0 0 24 24" fill="none"><path d="M12 3v12m0 0 4.5-4.5M12 15l-4.5-4.5M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>
    <span>Yuklab olish</span>
  </button>
  <button class="pg-btn" id="pg-share-btn" type="button" aria-label="Ulashish">
    <svg viewBox="0 0 24 24" fill="none"><circle cx="18" cy="5" r="2.4" stroke="currentColor" stroke-width="1.6"/><circle cx="6" cy="12" r="2.4" stroke="currentColor" stroke-width="1.6"/><circle cx="18" cy="19" r="2.4" stroke="currentColor" stroke-width="1.6"/><path d="M8.1 10.7 15.9 6.3M8.1 13.3l7.8 4.4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg>
    <span>Ulashish</span>
  </button>
  <button class="pg-btn" id="pg-qr-btn" type="button" aria-label="QR kod">
    <svg viewBox="0 0 24 24" fill="none"><rect x="3.5" y="3.5" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.6"/><rect x="14.5" y="3.5" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.6"/><rect x="3.5" y="14.5" width="6" height="6" rx="1" stroke="currentColor" stroke-width="1.6"/><path d="M14.5 14.5h2.6v2.6h-2.6zM19.5 14.5H21v2h-1.5zM14.5 19.5h2v1.5h-2zM19.5 19.3h1.5v1.7h-1.5z" fill="currentColor"/></svg>
    <span>QR kod</span>
  </button>
</div>

<div class="pg-qr-modal" id="pg-qr-modal">
  <div class="pg-qr-inner">
    <img id="pg-qr-img" alt="QR kod" width="200" height="200">
    <p>Havolani telefon kamerasi bilan skanerlang</p>
    <button class="pg-btn pg-qr-close" id="pg-qr-close" type="button"><span>Yopish</span></button>
  </div>
</div>

<style>
  .pg-action-bar {
    position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%);
    display: flex; gap: 6px; flex-wrap: wrap; justify-content: center;
    background: rgba(15,17,22,0.92); padding: 8px; border-radius: 18px;
    z-index: 60; backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
    max-width: 94vw; box-shadow: 0 8px 28px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
  }
  .pg-btn {
    font-family: 'Inter', sans-serif; font-size: 12.5px; font-weight: 500;
    background: transparent; color: rgba(255,255,255,0.88); border: none;
    border-radius: 12px; padding: 9px 13px; cursor: pointer; white-space: nowrap;
    transition: background 0.15s ease, color 0.15s ease;
    display: inline-flex; align-items: center; gap: 7px;
  }
  .pg-btn svg { width: 16px; height: 16px; flex-shrink: 0; color: rgba(255,255,255,0.7); transition: color 0.15s ease; }
  .pg-btn:hover { background: rgba(255,255,255,0.1); color: #fff; }
  .pg-btn:hover svg { color: #fff; }
  .pg-btn span { line-height: 1; }
  @media (max-width: 420px) {
    .pg-btn span { display: none; }
    .pg-btn { padding: 11px; border-radius: 50%; }
  }
  .pg-qr-modal {
    display: none; position: fixed; inset: 0; background: rgba(10,12,16,0.75);
    z-index: 100; align-items: center; justify-content: center; padding: 20px;
    backdrop-filter: blur(3px);
  }
  .pg-qr-modal.active { display: flex; }
  .pg-qr-inner {
    background: #fff; border-radius: 18px; padding: 28px 26px 22px; text-align: center;
    max-width: 280px; width: 100%; box-shadow: 0 24px 60px rgba(0,0,0,0.35);
  }
  .pg-qr-inner img { border-radius: 8px; border: 1px solid #EEE; padding: 6px; }
  .pg-qr-inner p {
    font-family: 'Inter', sans-serif; font-size: 12.5px; color: #5A5F6B;
    margin: 16px 0 18px; line-height: 1.5;
  }
  .pg-qr-close { background: #1B2430 !important; color: #fff !important; justify-content: center; width: 100%; padding: 11px !important; }
  .pg-qr-close:hover { background: #2A3648 !important; }
  @media print {
    .pg-action-bar, .pg-qr-modal { display: none !important; }
  }
</style>

<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script>
(function () {
  var pageUrl = window.location.href;

  var printBtn = document.getElementById('pg-print-btn');
  if (printBtn) {
    printBtn.addEventListener('click', function () { window.print(); });
  }

  var qrBtn = document.getElementById('pg-qr-btn');
  var qrModal = document.getElementById('pg-qr-modal');
  var qrImg = document.getElementById('pg-qr-img');
  var qrClose = document.getElementById('pg-qr-close');
  if (qrBtn) {
    qrBtn.addEventListener('click', function () {
      qrImg.src = 'https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=' + encodeURIComponent(pageUrl);
      qrModal.classList.add('active');
    });
  }
  if (qrClose) {
    qrClose.addEventListener('click', function () { qrModal.classList.remove('active'); });
  }
  if (qrModal) {
    qrModal.addEventListener('click', function (e) {
      if (e.target === qrModal) { qrModal.classList.remove('active'); }
    });
  }

  var shareBtn = document.getElementById('pg-share-btn');
  if (shareBtn) {
    shareBtn.addEventListener('click', function () {
      if (navigator.share) {
        navigator.share({ url: pageUrl }).catch(function () {});
      } else {
        var tgUrl = 'https://t.me/share/url?url=' + encodeURIComponent(pageUrl);
        window.open(tgUrl, '_blank');
      }
    });
  }

  var downloadBtn = document.getElementById('pg-download-btn');
  if (downloadBtn) {
    downloadBtn.addEventListener('click', function () {
      var bar = document.getElementById('pg-action-bar');
      var originalDisplay = bar.style.display;
      var originalOpacity = downloadBtn.style.opacity;
      bar.style.display = 'none';
      downloadBtn.style.opacity = '0.5';
      html2canvas(document.body, { backgroundColor: null, scale: 2, useCORS: true }).then(function (canvas) {
        bar.style.display = originalDisplay;
        downloadBtn.style.opacity = originalOpacity;
        var link = document.createElement('a');
        var slugPart = (window.location.pathname.split('/').filter(Boolean).pop() || 'noma');
        link.download = slugPart + '.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
      }).catch(function () {
        bar.style.display = originalDisplay;
        downloadBtn.style.opacity = originalOpacity;
      });
    });
  }
})();
</script>
"""


def inject_action_bar(html: str) -> str:
    if "</body>" in html:
        return html.replace("</body>", ACTION_BAR_BLOCK + "</body>", 1)
    return html + ACTION_BAR_BLOCK


def render_toy_page(data: dict) -> str:
    kuyov = data["kuyov"]
    kelin = data["kelin"]
    sana = data["sana"]
    vaqt = data["vaqt"]
    manzil = data["manzil"]
    xarita_link = data.get("xarita_link") or ""
    accent = data.get("rang") or "#5C7A5E"

    map_html = ""
    if xarita_link:
        map_html = f'<a class="map-link" href="{xarita_link}" target="_blank" rel="noopener">Manzilni xaritada ko\'rish</a>'

    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{kuyov} & {kelin} — to'y taklifnomasi</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;1,500&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; min-height: 100vh; background: #F6EFE4; color: #3B2E22; font-family: 'Inter', sans-serif; display: flex; align-items: center; justify-content: center; padding: 60px 20px; }}
  .card {{ max-width: 420px; text-align: center; }}
  .eyebrow {{ font-size: 12px; letter-spacing: 0.18em; text-transform: uppercase; color: #B98A5A; margin-bottom: 18px; }}
  .names {{ font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 44px; color: {accent}; margin: 0; }}
  .amp {{ font-size: 20px; color: #C97A6D; margin: 10px 0; }}
  .tagline {{ font-size: 14px; color: #7A6A56; margin: 24px 0 40px; }}
  .details {{ border-top: 1px solid #D9C9AE; padding-top: 28px; }}
  .details p {{ margin: 6px 0; font-size: 15px; }}
  .details .label {{ font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; color: #B98A5A; }}
  .countdown {{ display: flex; gap: 10px; justify-content: center; margin: 32px 0; }}
  .countdown div {{ background: #FFFDF8; border: 1px solid #E4D6BC; border-radius: 8px; padding: 12px 14px; min-width: 60px; }}
  .countdown span {{ display: block; font-family: 'Cormorant Garamond', serif; font-size: 24px; color: #C97A6D; }}
  .countdown small {{ font-size: 10px; letter-spacing: 0.08em; color: #7A6A56; text-transform: uppercase; }}
  .map-link {{ display: inline-block; margin-top: 24px; font-size: 13px; color: {accent}; text-decoration: underline; }}
</style>
</head>
<body>
<div class="card">
  <p class="eyebrow">Nikoh to'yi tantanasi</p>
  <p class="names">{kuyov}</p>
  <p class="amp">&#10084;</p>
  <p class="names">{kelin}</p>
  <p class="tagline">Ikki qalbning birikishi — eng buyuk baxt</p>
  <div class="countdown" id="countdown">
    <div><span id="cd-days">00</span><small>kun</small></div>
    <div><span id="cd-hours">00</span><small>soat</small></div>
    <div><span id="cd-mins">00</span><small>daqiqa</small></div>
    <div><span id="cd-secs">00</span><small>soniya</small></div>
  </div>
  <div class="details">
    <p class="label">Sana va vaqt</p>
    <p>{sana} &middot; {vaqt}</p>
    <p class="label" style="margin-top:16px;">Manzil</p>
    <p>{manzil}</p>
    {map_html}
  </div>
</div>
<script>
  const target = new Date("{sana}T{vaqt}:00");
  function tick() {{
    const now = new Date();
    let diff = Math.max(0, target - now);
    const days = Math.floor(diff / (1000*60*60*24));
    const hours = Math.floor((diff / (1000*60*60)) % 24);
    const mins = Math.floor((diff / (1000*60)) % 60);
    const secs = Math.floor((diff / 1000) % 60);
    document.getElementById('cd-days').textContent = String(days).padStart(2,'0');
    document.getElementById('cd-hours').textContent = String(hours).padStart(2,'0');
    document.getElementById('cd-mins').textContent = String(mins).padStart(2,'0');
    document.getElementById('cd-secs').textContent = String(secs).padStart(2,'0');
  }}
  tick();
  setInterval(tick, 1000);
</script>
</body>
</html>"""


def render_birthday_page(data: dict) -> str:
    accent = data.get("rang") or "#E8724C"
    ism = data["ism"]
    yosh = data.get("yosh") or ""
    sana = data["sana"]
    vaqt = data["vaqt"]
    manzil = data["manzil"]
    xarita_link = data.get("xarita_link") or ""
    xabar = data.get("xabar") or "Kelib, quvonchimizga sherik bo'ling!"

    yosh_html = f'<p class="yosh">{yosh} yosh</p>' if yosh else ""
    map_html = ""
    if xarita_link:
        map_html = f'<a class="map-link" href="{xarita_link}" target="_blank" rel="noopener">Manzilni xaritada ko\'rish</a>'

    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{ism} — tug'ilgan kun taklifnomasi</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh;
    background: radial-gradient(circle at 20% 15%, #FFE3A3 0%, #FFB84D 35%, #FF8C6B 70%, #F2694C 100%);
    color: #4A2A1F;
    font-family: 'Inter', sans-serif;
    display: flex; align-items: center; justify-content: center;
    padding: 60px 20px;
  }}
  .card {{
    max-width: 420px; width: 100%; text-align: center;
    background: rgba(255,255,255,0.88);
    border-radius: 24px;
    padding: 40px 28px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.12);
  }}
  .balloons {{ font-size: 32px; margin-bottom: 8px; }}
  .eyebrow {{ font-size: 12px; letter-spacing: 0.16em; text-transform: uppercase; color: {accent}; margin-bottom: 10px; font-weight: 500; }}
  .name {{ font-family: 'Baloo 2', sans-serif; font-weight: 700; font-size: 38px; color: {accent}; margin: 0; }}
  .yosh {{ font-family: 'Baloo 2', sans-serif; font-weight: 600; font-size: 18px; color: #F2A65A; margin: 6px 0 0; }}
  .xabar {{ font-size: 14px; color: #6B4A3A; margin: 20px 0 30px; line-height: 1.6; }}
  .details {{ border-top: 2px dashed #F2C79E; padding-top: 24px; }}
  .details p {{ margin: 6px 0; font-size: 15px; }}
  .details .label {{ font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: {accent}; font-weight: 500; }}
  .map-link {{ display: inline-block; margin-top: 20px; font-size: 13px; color: {accent}; font-weight: 500; text-decoration: underline; }}
</style>
</head>
<body>
<div class="card">
  <div class="balloons">🎈🎉🎂</div>
  <p class="eyebrow">Tug'ilgan kun taklifnomasi</p>
  <p class="name">{ism}</p>
  {yosh_html}
  <p class="xabar">{xabar}</p>
  <div class="details">
    <p class="label">Sana va vaqt</p>
    <p>{sana} &middot; {vaqt}</p>
    <p class="label" style="margin-top:14px;">Manzil</p>
    <p>{manzil}</p>
    {map_html}
  </div>
</div>
</body>
</html>"""


def escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_explanation_page(data: dict) -> str:
    accent = data.get("rang") or "#2B3A55"
    sarlavha = escape_html(data["sarlavha"])
    kimga = escape_html(data["kimga"])
    matn = escape_html(data["matn"]).replace("\n", "<br>")
    kimdan = escape_html(data["kimdan"])
    sana = data["sana"]

    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{sarlavha}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,wght@0,400;0,600;1,400&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh;
    background: #EAECEF;
    color: #1F2937;
    font-family: 'Source Serif 4', serif;
    display: flex; align-items: flex-start; justify-content: center;
    padding: 48px 20px;
  }}
  .paper {{
    max-width: 560px; width: 100%;
    background: #FFFFFF;
    padding: 48px 44px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    border-top: 4px solid {accent};
  }}
  .letterhead {{ font-family: 'Inter', sans-serif; font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: #6B7686; margin: 0 0 32px; }}
  .title {{ font-size: 26px; font-weight: 600; margin: 0 0 28px; color: {accent}; }}
  .addressee {{ font-family: 'Inter', sans-serif; font-size: 13px; color: #6B7686; margin: 0 0 24px; }}
  .body-text {{ font-size: 16px; line-height: 1.75; color: #2B3340; margin: 0 0 40px; }}
  .signoff {{ font-family: 'Inter', sans-serif; font-size: 13px; color: #6B7686; text-align: right; border-top: 1px solid #E4E7EC; padding-top: 20px; }}
  .signoff strong {{ display: block; font-family: 'Source Serif 4', serif; font-size: 16px; color: {accent}; margin-bottom: 2px; }}
</style>
</head>
<body>
<div class="paper">
  <p class="letterhead">Nomalar.uz &middot; Rasmiy xat</p>
  <h1 class="title">{sarlavha}</h1>
  <p class="addressee">Kimga: {kimga}</p>
  <p class="body-text">{matn}</p>
  <div class="signoff">
    <strong>{kimdan}</strong>
    {sana}
  </div>
</div>
</body>
</html>"""


def render_reminder_page(data: dict) -> str:
    accent = data.get("rang") or "#92702A"
    sarlavha = escape_html(data["sarlavha"])
    kimga = escape_html(data["kimga"])
    matn = escape_html(data["matn"]).replace("\n", "<br>")
    muddat = data["muddat"]
    kimdan = escape_html(data["kimdan"])

    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{sarlavha}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Kalam:wght@400;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh;
    background: #E7E2D6;
    color: #3A3324;
    font-family: 'Inter', sans-serif;
    display: flex; align-items: center; justify-content: center;
    padding: 60px 20px;
  }}
  .note {{
    max-width: 380px; width: 100%;
    background: #FDE68A;
    padding: 40px 32px 34px;
    transform: rotate(-1.2deg);
    box-shadow: 0 14px 30px rgba(0,0,0,0.15);
    position: relative;
  }}
  .pin {{ position: absolute; top: -14px; left: 50%; transform: translateX(-50%); font-size: 28px; }}
  .eyebrow {{ font-family: 'Inter', sans-serif; font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: {accent}; margin: 6px 0 14px; }}
  .title {{ font-family: 'Kalam', cursive; font-weight: 700; font-size: 26px; color: #4A3B14; margin: 0 0 18px; }}
  .addressee {{ font-size: 13px; color: #6B5A2E; margin: 0 0 18px; }}
  .body-text {{ font-family: 'Kalam', cursive; font-size: 17px; line-height: 1.6; color: #3A3324; margin: 0 0 26px; }}
  .muddat-box {{ background: rgba(255,255,255,0.5); border-radius: 8px; padding: 12px 14px; margin-bottom: 18px; }}
  .muddat-box .label {{ font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: {accent}; }}
  .muddat-box p {{ margin: 4px 0 0; font-weight: 500; }}
  .kimdan {{ font-size: 13px; color: #6B5A2E; text-align: right; }}
</style>
</head>
<body>
<div class="note">
  <div class="pin">📌</div>
  <p class="eyebrow">Eslatma xati</p>
  <h1 class="title">{sarlavha}</h1>
  <p class="addressee">Kimga: {kimga}</p>
  <p class="body-text">{matn}</p>
  <div class="muddat-box">
    <p class="label">Muddat</p>
    <p>{muddat}</p>
  </div>
  <p class="kimdan">— {kimdan}</p>
</div>
</body>
</html>"""


def render_guarantee_page(data: dict) -> str:
    accent = data.get("rang") or "#C9A84C"
    mahsulot = escape_html(data["mahsulot"])
    mijoz = escape_html(data["mijoz"])
    muddat = escape_html(data["muddat"])
    sana = data["sana"]
    shartlar = escape_html(data.get("shartlar") or "").replace("\n", "<br>")
    beruvchi = escape_html(data["beruvchi"])

    shartlar_html = ""
    if shartlar:
        shartlar_html = f'<p class="label" style="margin-top:20px;">Shartlar</p><p class="shartlar-text">{shartlar}</p>'

    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kafolat xati — {mahsulot}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh;
    background: #101820;
    color: #E9E4D6;
    font-family: 'Inter', sans-serif;
    display: flex; align-items: center; justify-content: center;
    padding: 48px 20px;
  }}
  .cert {{
    max-width: 460px; width: 100%;
    background: #16202B;
    border: 1px solid {accent};
    padding: 44px 36px;
    text-align: center;
    position: relative;
  }}
  .cert::before {{
    content: "";
    position: absolute; inset: 8px;
    border: 1px solid rgba(201,168,76,0.35);
    pointer-events: none;
  }}
  .badge {{ font-size: 30px; margin-bottom: 10px; }}
  .eyebrow {{ font-size: 11px; letter-spacing: 0.2em; text-transform: uppercase; color: {accent}; margin: 0 0 18px; }}
  .title {{ font-family: 'Cormorant Garamond', serif; font-weight: 600; font-size: 28px; margin: 0 0 6px; color: #F3ECD9; }}
  .mijoz {{ font-size: 13px; color: #9FA8B0; margin: 0 0 30px; }}
  .row {{ display: flex; justify-content: space-between; border-top: 1px solid rgba(201,168,76,0.25); padding: 14px 0; text-align: left; }}
  .row .label {{ font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: {accent}; }}
  .row .value {{ font-size: 14px; color: #E9E4D6; }}
  .shartlar-text {{ font-size: 13px; color: #B7BEC5; line-height: 1.6; text-align: left; margin-top: 6px; }}
  .beruvchi {{ margin-top: 28px; font-family: 'Cormorant Garamond', serif; font-size: 17px; color: {accent}; }}
</style>
</head>
<body>
<div class="cert">
  <div class="badge">🛡️</div>
  <p class="eyebrow">Kafolat xati</p>
  <h1 class="title">{mahsulot}</h1>
  <p class="mijoz">Mijoz: {mijoz}</p>

  <div class="row"><span class="label">Kafolat muddati</span><span class="value">{muddat}</span></div>
  <div class="row"><span class="label">Berilgan sana</span><span class="value">{sana}</span></div>

  {shartlar_html}

  <p class="beruvchi">{beruvchi}</p>
</div>
</body>
</html>"""


def render_parent_guarantee_page(data: dict) -> str:
    accent = data.get("rang") or "#2C4A73"
    oquvchi = escape_html(data["oquvchi"])
    sinf = escape_html(data["sinf"])
    maktab = escape_html(data["maktab"])
    otaona = escape_html(data["otaona"])
    vada = escape_html(data["vada"]).replace("\n", "<br>")
    sana = data["sana"]

    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Kafolat xati — {oquvchi}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@600&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh;
    background: #E9EEF3;
    font-family: 'Inter', sans-serif;
    display: flex; align-items: center; justify-content: center;
    padding: 48px 20px;
  }}
  .sheet {{
    max-width: 460px; width: 100%;
    background:
      linear-gradient(#FDFEFF 0px, #FDFEFF 27px, #CFE0F0 28px);
    background-size: 100% 28px;
    background-color: #FDFEFF;
    padding: 40px 40px 40px 56px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    position: relative;
    border-left: 3px solid #E8746B;
  }}
  .eyebrow {{ font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: #4A6FA5; margin: 0 0 20px; }}
  .title {{ font-family: 'Caveat', cursive; font-weight: 600; font-size: 32px; color: {accent}; margin: 0 0 24px; }}
  .info {{ font-size: 14px; color: #2E3B4E; margin: 4px 0; }}
  .info b {{ color: {accent}; }}
  .vada {{ font-family: 'Caveat', cursive; font-size: 20px; color: #2E3B4E; line-height: 1.5; margin: 20px 0; }}
  .footer {{ font-size: 13px; color: #4A6FA5; margin-top: 20px; text-align: right; }}
</style>
</head>
<body>
<div class="sheet">
  <p class="eyebrow">Ota-ona kafolat xati</p>
  <h1 class="title">{maktab}</h1>
  <p class="info"><b>O'quvchi:</b> {oquvchi} ({sinf})</p>
  <p class="info"><b>Ota-ona:</b> {otaona}</p>
  <p class="vada">{vada}</p>
  <p class="footer">{otaona} &middot; {sana}</p>
</div>
</body>
</html>"""


def render_birthday_greeting_page(data: dict) -> str:
    accent = data.get("rang") or "#B0459A"
    kimga = escape_html(data["kimga"])
    tabrik = escape_html(data["tabrik"]).replace("\n", "<br>")
    kimdan = escape_html(data["kimdan"])

    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{kimga} — tug'ilgan kun tabrigi</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fredoka:wght@600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh;
    background: linear-gradient(160deg, #FBC7E0 0%, #C8B6F2 50%, #A6D8F0 100%);
    color: #3A2E4A;
    font-family: 'Inter', sans-serif;
    display: flex; align-items: center; justify-content: center;
    padding: 60px 20px;
  }}
  .card {{
    max-width: 400px; width: 100%; text-align: center;
    background: rgba(255,255,255,0.82);
    border-radius: 28px;
    padding: 44px 30px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.12);
  }}
  .confetti {{ font-size: 30px; margin-bottom: 10px; letter-spacing: 6px; }}
  .headline {{ font-family: 'Fredoka', sans-serif; font-weight: 700; font-size: 30px; color: {accent}; margin: 0 0 6px; }}
  .kimga {{ font-family: 'Fredoka', sans-serif; font-weight: 600; font-size: 22px; color: #5B4B8A; margin: 0 0 22px; }}
  .tabrik {{ font-size: 15px; line-height: 1.7; color: #4A3D5C; margin: 0 0 26px; }}
  .kimdan {{ font-size: 13px; color: #7A6A8F; }}
</style>
</head>
<body>
<div class="card">
  <div class="confetti">🎉🎈🎁</div>
  <p class="headline">Tabriklaymiz!</p>
  <p class="kimga">{kimga}</p>
  <p class="tabrik">{tabrik}</p>
  <p class="kimdan">— {kimdan}</p>
</div>
</body>
</html>"""


def render_cradle_page(data: dict) -> str:
    accent = data.get("rang") or "#8E7CC3"
    chaqaloq = escape_html(data["chaqaloq"])
    otaona = escape_html(data["otaona"])
    sana = data["sana"]
    vaqt = data["vaqt"]
    manzil = escape_html(data["manzil"])
    xarita_link = data.get("xarita_link") or ""

    map_html = ""
    if xarita_link:
        map_html = f'<a class="map-link" href="{xarita_link}" target="_blank" rel="noopener">Manzilni xaritada ko\'rish</a>'

    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{chaqaloq} — beshik to'yi</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@500;600&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh;
    background: linear-gradient(180deg, #DCEEFB 0%, #F3E6F5 100%);
    color: #4A4560;
    font-family: 'Inter', sans-serif;
    display: flex; align-items: center; justify-content: center;
    padding: 60px 20px;
  }}
  .card {{
    max-width: 400px; width: 100%; text-align: center;
    background: rgba(255,255,255,0.85);
    border-radius: 26px;
    padding: 42px 30px;
    box-shadow: 0 16px 40px rgba(100,100,160,0.14);
  }}
  .icon {{ font-size: 28px; margin-bottom: 12px; }}
  .eyebrow {{ font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase; color: {accent}; margin: 0 0 14px; }}
  .name {{ font-family: 'Quicksand', sans-serif; font-weight: 600; font-size: 30px; color: #6E5A9E; margin: 0 0 6px; }}
  .parents {{ font-size: 14px; color: #7A7291; margin: 0 0 28px; }}
  .details {{ border-top: 1px dashed #D6C9E8; padding-top: 24px; }}
  .details p {{ margin: 6px 0; font-size: 15px; }}
  .details .label {{ font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: {accent}; }}
  .map-link {{ display: inline-block; margin-top: 18px; font-size: 13px; color: #6E5A9E; text-decoration: underline; }}
</style>
</head>
<body>
<div class="card">
  <div class="icon">🌙✨</div>
  <p class="eyebrow">Beshik to'yi</p>
  <p class="name">{chaqaloq}</p>
  <p class="parents">{otaona} oilasidan</p>
  <div class="details">
    <p class="label">Sana va vaqt</p>
    <p>{sana} &middot; {vaqt}</p>
    <p class="label" style="margin-top:14px;">Manzil</p>
    <p>{manzil}</p>
    {map_html}
  </div>
</div>
</body>
</html>"""


def render_graduation_page(data: dict) -> str:
    accent = data.get("rang") or "#D4AF37"
    ism = escape_html(data["ism"])
    muassasa = escape_html(data["muassasa"])
    sana = data["sana"]
    vaqt = data["vaqt"]
    manzil = escape_html(data["manzil"])
    xarita_link = data.get("xarita_link") or ""

    map_html = ""
    if xarita_link:
        map_html = f'<a class="map-link" href="{xarita_link}" target="_blank" rel="noopener">Manzilni xaritada ko\'rish</a>'

    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{ism} — bitiruv marosimi</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh;
    background: #0F1B3C;
    color: #E7E9F2;
    font-family: 'Inter', sans-serif;
    display: flex; align-items: center; justify-content: center;
    padding: 60px 20px;
  }}
  .card {{
    max-width: 420px; width: 100%; text-align: center;
    border: 1px solid {accent};
    padding: 42px 32px;
  }}
  .icon {{ font-size: 30px; margin-bottom: 12px; }}
  .eyebrow {{ font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: {accent}; margin: 0 0 16px; }}
  .name {{ font-family: 'Playfair Display', serif; font-weight: 700; font-size: 30px; color: #FFFFFF; margin: 0 0 8px; }}
  .muassasa {{ font-size: 14px; color: #A9B0C6; margin: 0 0 28px; }}
  .details {{ border-top: 1px solid rgba(212,175,55,0.3); padding-top: 24px; }}
  .details p {{ margin: 6px 0; font-size: 15px; }}
  .details .label {{ font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: {accent}; }}
  .map-link {{ display: inline-block; margin-top: 18px; font-size: 13px; color: {accent}; text-decoration: underline; }}
</style>
</head>
<body>
<div class="card">
  <div class="icon">🎓</div>
  <p class="eyebrow">Bitiruv marosimi</p>
  <p class="name">{ism}</p>
  <p class="muassasa">{muassasa}</p>
  <div class="details">
    <p class="label">Sana va vaqt</p>
    <p>{sana} &middot; {vaqt}</p>
    <p class="label" style="margin-top:14px;">Manzil</p>
    <p>{manzil}</p>
    {map_html}
  </div>
</div>
</body>
</html>"""


def render_official_event_page(data: dict) -> str:
    accent = data.get("rang") or "#2455A4"
    tadbir = escape_html(data["tadbir"])
    tashkilotchi = escape_html(data["tashkilotchi"])
    sana = data["sana"]
    vaqt = data["vaqt"]
    manzil = escape_html(data["manzil"])
    xarita_link = data.get("xarita_link") or ""
    tavsif = escape_html(data.get("tavsif") or "").replace("\n", "<br>")

    map_html = ""
    if xarita_link:
        map_html = f'<a class="map-link" href="{xarita_link}" target="_blank" rel="noopener">Manzilni xaritada ko\'rish</a>'

    tavsif_html = f'<p class="tavsif">{tavsif}</p>' if tavsif else ""

    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{tadbir}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh;
    background: #F4F5F7;
    color: #1F2733;
    font-family: 'Inter', sans-serif;
    display: flex; align-items: center; justify-content: center;
    padding: 60px 20px;
  }}
  .card {{
    max-width: 460px; width: 100%;
    background: #FFFFFF;
    border-radius: 4px;
    border-left: 5px solid {accent};
    padding: 40px 36px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.06);
  }}
  .eyebrow {{ font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: {accent}; margin: 0 0 12px; font-weight: 600; }}
  .title {{ font-size: 24px; font-weight: 700; margin: 0 0 8px; color: #1F2733; }}
  .tashkilotchi {{ font-size: 13px; color: #6B7686; margin: 0 0 28px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; border-top: 1px solid #E4E7EC; padding-top: 22px; margin-bottom: 18px; }}
  .grid .label {{ font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: #6B7686; margin: 0 0 4px; }}
  .grid .value {{ font-size: 14px; font-weight: 500; margin: 0; }}
  .tavsif {{ font-size: 14px; line-height: 1.6; color: #3A4353; margin: 10px 0 6px; }}
  .map-link {{ display: inline-block; margin-top: 8px; font-size: 13px; color: {accent}; text-decoration: underline; }}
</style>
</head>
<body>
<div class="card">
  <p class="eyebrow">Rasmiy tadbir</p>
  <h1 class="title">{tadbir}</h1>
  <p class="tashkilotchi">Tashkilotchi: {tashkilotchi}</p>
  <div class="grid">
    <div><p class="label">Sana</p><p class="value">{sana}</p></div>
    <div><p class="label">Vaqt</p><p class="value">{vaqt}</p></div>
  </div>
  <p class="grid label" style="margin-bottom:2px;">Manzil</p>
  <p class="value">{manzil}</p>
  {map_html}
  {tavsif_html}
</div>
</body>
</html>"""


def render_love_letter_page(data: dict) -> str:
    accent = data.get("rang") or "#B0475F"
    kimga = escape_html(data["kimga"])
    matn = escape_html(data["matn"]).replace("\n", "<br>")
    kimdan = escape_html(data["kimdan"])

    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{kimga} uchun xat</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@1,500;1,600&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh;
    background: linear-gradient(160deg, #F7D9DE 0%, #E8B7C4 55%, #D693A8 100%);
    color: #5C2A3A;
    font-family: 'Inter', sans-serif;
    display: flex; align-items: center; justify-content: center;
    padding: 60px 20px;
  }}
  .card {{
    max-width: 420px; width: 100%; text-align: center;
    background: rgba(255,255,255,0.85);
    border-radius: 6px;
    padding: 46px 34px;
    box-shadow: 0 18px 45px rgba(120,40,60,0.18);
  }}
  .heart {{ font-size: 26px; margin-bottom: 10px; }}
  .eyebrow {{ font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase; color: {accent}; margin: 0 0 16px; }}
  .kimga {{ font-family: 'Cormorant Garamond', serif; font-style: italic; font-weight: 600; font-size: 34px; color: #A03A54; margin: 0 0 26px; }}
  .matn {{ font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 19px; line-height: 1.7; color: #5C2A3A; margin: 0 0 30px; }}
  .kimdan {{ font-size: 14px; color: #8A5062; }}
</style>
</head>
<body>
<div class="card">
  <div class="heart">💌</div>
  <p class="eyebrow">Sevishganlar xati</p>
  <p class="kimga">{kimga}</p>
  <p class="matn">{matn}</p>
  <p class="kimdan">— {kimdan}</p>
</div>
</body>
</html>"""


def render_vizitka_page(data: dict) -> str:
    ism = escape_html(data["ism"])
    lavozim = escape_html(data["lavozim"])
    telefon = escape_html(data["telefon"])
    email = escape_html(data.get("email") or "")
    tarmoq = escape_html(data.get("tarmoq") or "")
    tavsif = escape_html(data.get("tavsif") or "")
    accent = data.get("rang") or "#4A9B8E"

    email_html = f'<p class="contact-row"><span class="ic">✉</span> {email}</p>' if email else ""
    tarmoq_html = f'<p class="contact-row"><span class="ic">🔗</span> {tarmoq}</p>' if tarmoq else ""
    tavsif_html = f'<p class="tavsif">{tavsif}</p>' if tavsif else ""

    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{ism} — vizitka</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh;
    background: #14181C;
    color: #E7EBEE;
    font-family: 'Inter', sans-serif;
    display: flex; align-items: center; justify-content: center;
    padding: 60px 20px;
  }}
  .card {{
    max-width: 400px; width: 100%;
    background: #1C2126;
    border-radius: 18px;
    padding: 40px 34px;
    border-top: 3px solid {accent};
    box-shadow: 0 20px 50px rgba(0,0,0,0.35);
  }}
  .eyebrow {{ font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: {accent}; margin: 0 0 18px; font-weight: 500; }}
  .name {{ font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 30px; color: #FFFFFF; margin: 0 0 4px; }}
  .lavozim {{ font-size: 14px; color: #9AA4AC; margin: 0 0 28px; }}
  .contacts {{ border-top: 1px solid rgba(255,255,255,0.08); padding-top: 22px; }}
  .contact-row {{ font-size: 14px; margin: 8px 0; display: flex; align-items: center; gap: 10px; }}
  .contact-row .ic {{ color: {accent}; font-size: 15px; width: 18px; text-align: center; }}
  .tavsif {{ font-size: 13px; color: #B7BEC5; line-height: 1.6; margin-top: 22px; padding-top: 18px; border-top: 1px solid rgba(255,255,255,0.08); }}
</style>
</head>
<body>
<div class="card">
  <p class="eyebrow">Vizitka</p>
  <p class="name">{ism}</p>
  <p class="lavozim">{lavozim}</p>
  <div class="contacts">
    <p class="contact-row"><span class="ic">☎</span> {telefon}</p>
    {email_html}
    {tarmoq_html}
  </div>
  {tavsif_html}
</div>
</body>
</html>"""


def render_resume_page(data: dict) -> str:
    ism = escape_html(data["ism"])
    lavozim = escape_html(data["lavozim"])
    telefon = escape_html(data["telefon"])
    email = escape_html(data.get("email") or "")
    tajriba = escape_html(data["tajriba"]).replace("\n", "<br>")
    konikmalar = escape_html(data.get("konikmalar") or "").replace("\n", "<br>")
    accent = data.get("rang") or "#2C4A6B"

    email_html = f' &middot; {email}' if email else ""
    konikmalar_html = ""
    if konikmalar:
        konikmalar_html = f"""
  <div class="section">
    <p class="section-title">Ko'nikmalar</p>
    <p class="section-body">{konikmalar}</p>
  </div>"""

    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{ism} — rezyume</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@500;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh;
    background: #F0F2F4;
    color: #232A32;
    font-family: 'Inter', sans-serif;
    display: flex; align-items: flex-start; justify-content: center;
    padding: 48px 20px;
  }}
  .sheet {{
    max-width: 560px; width: 100%;
    background: #FFFFFF;
    padding: 46px 44px;
    box-shadow: 0 6px 28px rgba(0,0,0,0.08);
    border-radius: 4px;
  }}
  .header {{ border-bottom: 3px solid {accent}; padding-bottom: 22px; margin-bottom: 26px; }}
  .name {{ font-family: 'Libre Franklin', sans-serif; font-weight: 700; font-size: 30px; color: #1B222B; margin: 0 0 4px; }}
  .lavozim {{ font-size: 15px; color: {accent}; font-weight: 600; margin: 0 0 12px; }}
  .contact-line {{ font-size: 13px; color: #6B7686; }}
  .section {{ margin-bottom: 24px; }}
  .section-title {{ font-family: 'Libre Franklin', sans-serif; font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; color: {accent}; font-weight: 700; margin: 0 0 10px; }}
  .section-body {{ font-size: 14.5px; line-height: 1.7; color: #333B44; margin: 0; }}
</style>
</head>
<body>
<div class="sheet">
  <div class="header">
    <p class="name">{ism}</p>
    <p class="lavozim">{lavozim}</p>
    <p class="contact-line">{telefon}{email_html}</p>
  </div>
  <div class="section">
    <p class="section-title">Ish tajribasi</p>
    <p class="section-body">{tajriba}</p>
  </div>
  {konikmalar_html}
</div>
</body>
</html>"""


def render_thanks_page(data: dict) -> str:
    kimga = escape_html(data["kimga"])
    matn = escape_html(data["matn"]).replace("\n", "<br>")
    kimdan = escape_html(data["kimdan"])
    sana = data["sana"]
    accent = data.get("rang") or "#B9862F"

    return f"""<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Minnatdorchilik xati — {kimga}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;1,500&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh;
    background: #FBF6EC;
    color: #3E3421;
    font-family: 'Inter', sans-serif;
    display: flex; align-items: center; justify-content: center;
    padding: 48px 20px;
  }}
  .card {{
    max-width: 460px; width: 100%;
    background: #FFFFFF;
    padding: 46px 40px;
    text-align: center;
    border: 1px solid #EAD9AE;
    position: relative;
  }}
  .card::before {{
    content: "";
    position: absolute; inset: 10px;
    border: 1px solid {accent}55;
    pointer-events: none;
  }}
  .icon {{ font-size: 28px; margin-bottom: 8px; }}
  .eyebrow {{ font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: {accent}; margin: 0 0 18px; font-weight: 600; }}
  .kimga {{ font-family: 'Cormorant Garamond', serif; font-style: italic; font-weight: 600; font-size: 28px; color: #2E2712; margin: 0 0 22px; }}
  .matn {{ font-size: 15px; line-height: 1.75; color: #4A4028; margin: 0 0 28px; }}
  .signoff {{ border-top: 1px solid #EAD9AE; padding-top: 18px; font-size: 13px; color: #7A6A42; }}
  .signoff strong {{ display: block; font-family: 'Cormorant Garamond', serif; font-size: 17px; color: {accent}; margin-bottom: 2px; }}
</style>
</head>
<body>
<div class="card">
  <div class="icon">🙏</div>
  <p class="eyebrow">Minnatdorchilik xati</p>
  <p class="kimga">{kimga}</p>
  <p class="matn">{matn}</p>
  <div class="signoff">
    <strong>{kimdan}</strong>
    {sana}
  </div>
</div>
</body>
</html>"""
