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
.screen { display: none; min-height: 100vh; align-items: center; justify-content: center; padding: 100px 24px 48px; }
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
#form-toy { display: flex; flex-direction: column; gap: 16px; }
#form-toy label { display: flex; flex-direction: column; gap: 6px; font-size: 13px; color: var(--text-on-ink-dim); }
#form-toy input { font-family: 'Inter', sans-serif; font-size: 14px; background: rgba(239, 232, 214, 0.05); border: 1px solid rgba(239, 232, 214, 0.16); border-radius: 3px; padding: 11px 12px; color: var(--text-on-ink); }
#form-toy input:focus { outline: none; border-color: var(--brass); }
.row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-error { color: #D97757; font-size: 13px; min-height: 18px; margin: 0; }
.result-wrap { max-width: 380px; width: 100%; text-align: center; }
.result-sub { color: var(--text-on-ink-dim); font-size: 14px; margin: 0 0 20px; }
.result-link-box { display: flex; gap: 8px; margin-bottom: 20px; }
.result-link-box input { flex: 1; font-family: 'Inter', sans-serif; font-size: 13px; background: rgba(239, 232, 214, 0.05); border: 1px solid rgba(239, 232, 214, 0.16); border-radius: 3px; padding: 11px 12px; color: var(--text-on-ink); }
.btn-view-link { display: inline-block; color: var(--brass-light); font-size: 14px; text-decoration: none; }
.btn-view-link:hover { text-decoration: underline; }
.site-footer { position: fixed; bottom: 14px; left: 50%; transform: translateX(-50%); font-size: 11px; color: var(--text-on-ink-dim); opacity: 0.6; z-index: 5; }
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
    </div>
    <p class="next-note" id="next-note">Tanlang — keyingi bosqichda forma ochiladi.</p>
  </div>
</section>

<section id="screen-form-toy" class="screen">
  <div class="form-wrap">
    <p class="eyebrow">2-qadam</p>
    <h2 class="section-title">To'y ma'lumotlari</h2>
    <form id="form-toy">
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
  <div class="form-wrap">
    <p class="eyebrow">2-qadam</p>
    <h2 class="section-title">Tug'ilgan kun ma'lumotlari</h2>
    <form id="form-tugilgan-kun">
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
  </div>
</section>

<p class="site-footer">Yaratuvchi: Ilhomjonov Shahzodbek</p>

<script>
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

document.getElementById('btn-start').addEventListener('click', () => showScreen('screen-explain'));

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
