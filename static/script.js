// --- Ekranlar orasida o'tish ---
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

document.getElementById('btn-start').addEventListener('click', () => {
  showScreen('screen-explain');
});

// --- Tushuntirish slaydlari ---
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
  if (currentSlide < slides.length - 1) {
    setSlide(currentSlide + 1);
  } else {
    showScreen('screen-templates');
  }
});

// --- Shablon tanlash ---
const tplCards = document.querySelectorAll('.tpl-card');
const nextNote = document.getElementById('next-note');

tplCards.forEach(card => {
  card.addEventListener('click', () => {
    tplCards.forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    const tplName = card.querySelector('.tpl-name').textContent;
    nextNote.textContent = `"${tplName}" tanlandi — forma tez orada shu yerda ochiladi.`;
    // Keyingi bosqichda: shu yerdan forma sahifasiga o'tkaziladi
    // window.location.href = `/create/${card.dataset.tpl}`;
  });
});
