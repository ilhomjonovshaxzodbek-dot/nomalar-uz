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
#  BOSH SAHIFA (HTML + CSS + JS — HAMMASI SHU YERDA)
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
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {
  --ink: #1B2430; --ink-deep: #131A24; --parchment: #F3ECD9; --parchment-dim: #E4DABF;
  --brass: #B8905A; --brass-light: #D8B888; --text-on-ink: #EFE8D6; --text-on-ink-dim: #9AA4B2;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: var(--ink); color: var(--text-on-ink); font-family: 'Inter', sans-serif; overflow-x: hidden; min-height: 100vh; }
.eyebrow { font-family: 'Inter', sans-serif; font-size: 12px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--brass-light); margin: 0 0 12px; }
.seal { position: fixed; top: 24px; left: 50%; transform: translateX(-50%); width: 34px; height: 34px; opacity: 0.9; z-index: 10; }
.seal svg { width: 100%; height: 100%; }
.seal circle { fill: var(--brass); }
.seal path { fill: var(--ink); }
.screen { display: none; min-height: 100vh; align-items: center; justify-content: center; padding: 100px 24px 48px; position: relative; }
.screen.active { display: flex; }
.intro-wrap { text-align: center; max-width: 420px; animation: rise 0.8s ease both; }
.brand-title { font-family: 'Cormorant Garamond', serif; font-weight: 600; font-size: 56px; margin: 0 0 12px; color: var(--parchment); }
.brand-title .dot { color: var(--brass); }
.intro-sub { color: var(--text-on-ink-dim); font-size: 15px; margin: 0 0 40px; }
.btn-primary { font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 500; letter-spacing: 0.02em; background: var(--brass); color: var(--ink-deep); border: none; border-radius: 2px; padding: 14px 36px; cursor: pointer; transition: background 0.2s ease, transform 0.15s ease; }
.btn-primary:hover { background: var(--brass-light); }
.btn-primary:active { transform: scale(0.98); }
.btn-primary:focus-visible { outline: 2px solid var(--parchment); outline-offset: 3px; }
.explain-wrap { max-width: 420px; width: 100%; text-align: center; }
.explain-slide { display: none; animation: rise 0.5s ease both; }
.explain-slide.active { display: block; }
.explain-num { font-family: 'Cormorant Garamond', serif; font-size: 15px; color: var(--brass-light); letter-spacing: 0.1em; }
.explain-slide h2 { font-family: 'Cormorant Garamond', serif; font-weight: 600; font-size: 30px; margin: 8px 0 12px; color: var(--parchment); }
.explain-slide p { color: var(--text-on-ink-dim); font-size: 15px; line-height: 1.6; margin: 0 0 32px; }
.explain-dots { display: flex; justify-content: center; gap: 8px; margin-bottom: 32px; }
.dot-i { width: 6px; height: 6px; border-radius: 50%; background: var(--text-on-ink-dim); opacity: 0.4; transition: opacity 0.2s ease, background 0.2s ease; }
.dot-i.active { opacity: 1; background: var(--brass); }
.templates-wrap { max-width: 460px; width: 100%; text-align: center; }
.section-title { font-family: 'Cormorant Garamond', serif; font-weight: 600; font-size: 32px; margin: 0 0 32px; color: var(--parchment); }
.template-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.tpl-card { font-family: 'Inter', sans-serif; background: transparent; border: 1px solid rgba(239, 232, 214, 0.16); border-radius: 3px; padding: 22px 14px; color: var(--text-on-ink); cursor: pointer; text-align: left; transition: border-color 0.2s ease, background 0.2s ease; display: flex; flex-direction: column; gap: 10px; }
.tpl-card:hover { border-color: var(--brass); background: rgba(184, 144, 90, 0.08); }
.tpl-card.selected { border-color: var(--brass); background: rgba(184, 144, 90, 0.14); }
.tpl-mark { font-family: 'Cormorant Garamond', serif; font-size: 20px; color: var(--brass-light); }
.tpl-name { font-size: 14px; font-weight: 500; }
.next-note { margin-top: 28px; font-size: 13px; color: var(--text-on-ink-dim); }
.form-wrap { max-width: 380px; width: 100%; }
.form-wrap .section-title { text-align: center; }
.app-form { display: flex; flex-direction: column; gap: 16px; }
.app-form label { display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: var(--text-on-ink-dim); }
.app-form input, .app-form textarea { font-family: 'Inter', sans-serif; font-size: 14px; background: rgba(239, 232, 214, 0.05); border: 1px solid rgba(239, 232, 214, 0.16); border-radius: 3px; padding: 11px 12px; color: var(--text-on-ink); }
.app-form input:focus, .app-form textarea:focus { outline: none; border-color: var(--brass); }
.app-form textarea { font-family: inherit; resize: vertical; }
.row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-error { color: #D97757; font-size: 13px; min-height: 18px; margin: 0; }
.result-wrap { max-width: 380px; width: 100%; text-align: center; }
.result-sub { color: var(--text-on-ink-dim); font-size: 14px; margin: 0 0 20px; }
.result-link-box { display: flex; gap: 8px; margin-bottom: 20px; }
.result-link-box input { flex: 1; font-family: 'Inter', sans-serif; font-size: 13px; background: rgba(239, 232, 214, 0.05); border: 1px solid rgba(239, 232, 214, 0.16); border-radius: 3px; padding: 11px 12px; color: var(--text-on-ink); }
.btn-view-link { display: inline-block; color: var(--brass-light); font-size: 14px; text-decoration: none; }
.btn-view-link:hover { text-decoration: underline; }
.site-footer { position: fixed; bottom: 14px; left: 50%; transform: translateX(-50%); font-size: 11px; color: var(--text-on-ink-dim); opacity: 0.6; z-index: 5; }
.btn-back { position: absolute; top: 24px; left: 24px; background: none; border: none; color: var(--text-on-ink-dim); font-family: 'Inter', sans-serif; font-size: 13px; cursor: pointer; display: flex; align-items: center; gap: 6px; padding: 8px; }
.btn-back:hover { color: var(--parchment); }
@keyframes rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
@media (prefers-reduced-motion: reduce) { .intro-wrap, .explain-slide { animation: none; } }
</style>
</head>
<body>

<div class="seal" aria-hidden="true">
  <svg viewBox="0 0 100 100">
    <circle cx="50" cy="50" r="46"/>
    <path d="M50 20 L58 42 L82 42 L62 56 L70 78 L50 64 L30 78 L38 56 L18 42 L42 42 Z"/>
  </svg>
</div>

<section id="screen-intro" class="screen active">
  <div class="intro-wrap">
    <p class="eyebrow">raqamli noma</p>
    <h1 class="brand-title">Nomalar<span class="dot">.</span>uz</h1>
    <p class="intro-sub">Muhim daqiqalaringiz uchun — bir necha daqiqada.</p>
    <button class="btn-primary" id="btn-start">Boshlash</button>
  </div>
</section>

<section id="screen-explain" class="screen">
  <button class="btn-back" id="btn-back-explain">&larr; Orqaga</button>
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
      <label>Xarita havolasi (ixtiyoriy)<input type="url" name="xarita_link" placeholder="https://maps.google.com/..."></label>
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
      <label>Xarita havolasi (ixtiyoriy)<input type="url" name="xarita_link" placeholder="https://maps.google.com/..."></label>
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
      <label>Xarita havolasi (ixtiyoriy)<input type="url" name="xarita_link" placeholder="https://maps.google.com/..."></label>
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
      <label>Xarita havolasi (ixtiyoriy)<input type="url" name="xarita_link" placeholder="https://maps.google.com/..."></label>
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
      <label>Xarita havolasi (ixtiyoriy)<input type="url" name="xarita_link" placeholder="https://maps.google.com/..."></label>
      <label>Qisqa tavsif (ixtiyoriy)<textarea name="tavsif" rows="3" placeholder="Tadbir haqida qisqacha..."></textarea></label>
      <button type="submit" class="btn-primary" style="width:100%;margin-top:8px;">Noma yaratish</button>
      <p class="form-error" id="form-rasmiy-error"></p>
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

<script>
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

document.getElementById('btn-start').addEventListener('click', () => showScreen('screen-explain'));

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

document.getElementById('btn-back-explain').addEventListener('click', () => {
  if (currentSlide > 0) { setSlide(currentSlide - 1); }
  else { showScreen('screen-intro'); }
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
    else { nextNote.textContent = `"${tplName}" formasi tez orada qo'shiladi.`; }
  });
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


@app.get("/", response_class=HTMLResponse)
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
        return render_toy_page(data)
    if template_type == "tugilgan-kun":
        return render_birthday_page(data)
    if template_type == "tushuntirish":
        return render_explanation_page(data)
    if template_type == "eslatma":
        return render_reminder_page(data)
    if template_type == "kafolat":
        return render_guarantee_page(data)
    if template_type == "ota-ona-kafolat":
        return render_parent_guarantee_page(data)
    if template_type == "tugilgan-kun-tabrik":
        return render_birthday_greeting_page(data)
    if template_type == "beshik":
        return render_cradle_page(data)
    if template_type == "bitiruv":
        return render_graduation_page(data)
    if template_type == "rasmiy":
        return render_official_event_page(data)

    raise HTTPException(status_code=404, detail="Noma turi topilmadi")


def render_toy_page(data: dict) -> str:
    kuyov = data["kuyov"]
    kelin = data["kelin"]
    sana = data["sana"]
    vaqt = data["vaqt"]
    manzil = data["manzil"]
    xarita_link = data.get("xarita_link") or ""

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
  .names {{ font-family: 'Cormorant Garamond', serif; font-style: italic; font-size: 44px; color: #5C7A5E; margin: 0; }}
  .amp {{ font-size: 20px; color: #C97A6D; margin: 10px 0; }}
  .tagline {{ font-size: 14px; color: #7A6A56; margin: 24px 0 40px; }}
  .details {{ border-top: 1px solid #D9C9AE; padding-top: 28px; }}
  .details p {{ margin: 6px 0; font-size: 15px; }}
  .details .label {{ font-size: 11px; letter-spacing: 0.12em; text-transform: uppercase; color: #B98A5A; }}
  .countdown {{ display: flex; gap: 10px; justify-content: center; margin: 32px 0; }}
  .countdown div {{ background: #FFFDF8; border: 1px solid #E4D6BC; border-radius: 8px; padding: 12px 14px; min-width: 60px; }}
  .countdown span {{ display: block; font-family: 'Cormorant Garamond', serif; font-size: 24px; color: #C97A6D; }}
  .countdown small {{ font-size: 10px; letter-spacing: 0.08em; color: #7A6A56; text-transform: uppercase; }}
  .map-link {{ display: inline-block; margin-top: 24px; font-size: 13px; color: #5C7A5E; text-decoration: underline; }}
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
  .eyebrow {{ font-size: 12px; letter-spacing: 0.16em; text-transform: uppercase; color: #E8724C; margin-bottom: 10px; font-weight: 500; }}
  .name {{ font-family: 'Baloo 2', sans-serif; font-weight: 700; font-size: 38px; color: #E8724C; margin: 0; }}
  .yosh {{ font-family: 'Baloo 2', sans-serif; font-weight: 600; font-size: 18px; color: #F2A65A; margin: 6px 0 0; }}
  .xabar {{ font-size: 14px; color: #6B4A3A; margin: 20px 0 30px; line-height: 1.6; }}
  .details {{ border-top: 2px dashed #F2C79E; padding-top: 24px; }}
  .details p {{ margin: 6px 0; font-size: 15px; }}
  .details .label {{ font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: #E8724C; font-weight: 500; }}
  .map-link {{ display: inline-block; margin-top: 20px; font-size: 13px; color: #E8724C; font-weight: 500; text-decoration: underline; }}
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
    border-top: 4px solid #2B3A55;
  }}
  .letterhead {{ font-family: 'Inter', sans-serif; font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: #6B7686; margin: 0 0 32px; }}
  .title {{ font-size: 26px; font-weight: 600; margin: 0 0 28px; color: #2B3A55; }}
  .addressee {{ font-family: 'Inter', sans-serif; font-size: 13px; color: #6B7686; margin: 0 0 24px; }}
  .body-text {{ font-size: 16px; line-height: 1.75; color: #2B3340; margin: 0 0 40px; }}
  .signoff {{ font-family: 'Inter', sans-serif; font-size: 13px; color: #6B7686; text-align: right; border-top: 1px solid #E4E7EC; padding-top: 20px; }}
  .signoff strong {{ display: block; font-family: 'Source Serif 4', serif; font-size: 16px; color: #2B3A55; margin-bottom: 2px; }}
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
  .eyebrow {{ font-family: 'Inter', sans-serif; font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: #92702A; margin: 6px 0 14px; }}
  .title {{ font-family: 'Kalam', cursive; font-weight: 700; font-size: 26px; color: #4A3B14; margin: 0 0 18px; }}
  .addressee {{ font-size: 13px; color: #6B5A2E; margin: 0 0 18px; }}
  .body-text {{ font-family: 'Kalam', cursive; font-size: 17px; line-height: 1.6; color: #3A3324; margin: 0 0 26px; }}
  .muddat-box {{ background: rgba(255,255,255,0.5); border-radius: 8px; padding: 12px 14px; margin-bottom: 18px; }}
  .muddat-box .label {{ font-size: 10px; letter-spacing: 0.1em; text-transform: uppercase; color: #92702A; }}
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
    border: 1px solid #C9A84C;
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
  .eyebrow {{ font-size: 11px; letter-spacing: 0.2em; text-transform: uppercase; color: #C9A84C; margin: 0 0 18px; }}
  .title {{ font-family: 'Cormorant Garamond', serif; font-weight: 600; font-size: 28px; margin: 0 0 6px; color: #F3ECD9; }}
  .mijoz {{ font-size: 13px; color: #9FA8B0; margin: 0 0 30px; }}
  .row {{ display: flex; justify-content: space-between; border-top: 1px solid rgba(201,168,76,0.25); padding: 14px 0; text-align: left; }}
  .row .label {{ font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: #C9A84C; }}
  .row .value {{ font-size: 14px; color: #E9E4D6; }}
  .shartlar-text {{ font-size: 13px; color: #B7BEC5; line-height: 1.6; text-align: left; margin-top: 6px; }}
  .beruvchi {{ margin-top: 28px; font-family: 'Cormorant Garamond', serif; font-size: 17px; color: #C9A84C; }}
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
  .title {{ font-family: 'Caveat', cursive; font-weight: 600; font-size: 32px; color: #2C4A73; margin: 0 0 24px; }}
  .info {{ font-size: 14px; color: #2E3B4E; margin: 4px 0; }}
  .info b {{ color: #2C4A73; }}
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
  .headline {{ font-family: 'Fredoka', sans-serif; font-weight: 700; font-size: 30px; color: #B0459A; margin: 0 0 6px; }}
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
  .eyebrow {{ font-size: 11px; letter-spacing: 0.16em; text-transform: uppercase; color: #8E7CC3; margin: 0 0 14px; }}
  .name {{ font-family: 'Quicksand', sans-serif; font-weight: 600; font-size: 30px; color: #6E5A9E; margin: 0 0 6px; }}
  .parents {{ font-size: 14px; color: #7A7291; margin: 0 0 28px; }}
  .details {{ border-top: 1px dashed #D6C9E8; padding-top: 24px; }}
  .details p {{ margin: 6px 0; font-size: 15px; }}
  .details .label {{ font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: #8E7CC3; }}
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
    border: 1px solid #D4AF37;
    padding: 42px 32px;
  }}
  .icon {{ font-size: 30px; margin-bottom: 12px; }}
  .eyebrow {{ font-size: 11px; letter-spacing: 0.18em; text-transform: uppercase; color: #D4AF37; margin: 0 0 16px; }}
  .name {{ font-family: 'Playfair Display', serif; font-weight: 700; font-size: 30px; color: #FFFFFF; margin: 0 0 8px; }}
  .muassasa {{ font-size: 14px; color: #A9B0C6; margin: 0 0 28px; }}
  .details {{ border-top: 1px solid rgba(212,175,55,0.3); padding-top: 24px; }}
  .details p {{ margin: 6px 0; font-size: 15px; }}
  .details .label {{ font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; color: #D4AF37; }}
  .map-link {{ display: inline-block; margin-top: 18px; font-size: 13px; color: #D4AF37; text-decoration: underline; }}
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
    border-left: 5px solid #2455A4;
    padding: 40px 36px;
    box-shadow: 0 6px 24px rgba(0,0,0,0.06);
  }}
  .eyebrow {{ font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase; color: #2455A4; margin: 0 0 12px; font-weight: 600; }}
  .title {{ font-size: 24px; font-weight: 700; margin: 0 0 8px; color: #1F2733; }}
  .tashkilotchi {{ font-size: 13px; color: #6B7686; margin: 0 0 28px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; border-top: 1px solid #E4E7EC; padding-top: 22px; margin-bottom: 18px; }}
  .grid .label {{ font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: #6B7686; margin: 0 0 4px; }}
  .grid .value {{ font-size: 14px; font-weight: 500; margin: 0; }}
  .tavsif {{ font-size: 14px; line-height: 1.6; color: #3A4353; margin: 10px 0 6px; }}
  .map-link {{ display: inline-block; margin-top: 8px; font-size: 13px; color: #2455A4; text-decoration: underline; }}
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
