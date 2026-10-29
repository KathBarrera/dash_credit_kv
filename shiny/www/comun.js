// Copiado del tablero Dash (dash/app.py: COVER_JS + BOT_JS)

(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  function cc() { return document.getElementById('cc'); }
  function setRole() { var c = cc(); if (c && !c.getAttribute('role')) c.setAttribute('role', 'button'); }
  function reset(c) { ['--rx', '--ry', '--mx', '--my'].forEach(function (k) { c.style.removeProperty(k); }); }
  document.addEventListener('mousemove', function (e) {
    var c = cc(); if (!c) return; setRole();
    if (reduce || !fine) return;
    var r = c.getBoundingClientRect();
    var x = Math.min(1.3, Math.max(-0.3, (e.clientX - r.left) / r.width));
    var y = Math.min(1.3, Math.max(-0.3, (e.clientY - r.top) / r.height));
    c.style.setProperty('--rx', ((0.5 - y) * 14).toFixed(2) + 'deg');
    c.style.setProperty('--ry', ((x - 0.5) * 18).toFixed(2) + 'deg');
    c.style.setProperty('--mx', (x * 100).toFixed(1) + '%');
    c.style.setProperty('--my', (y * 100).toFixed(1) + '%');
  });
  document.documentElement.addEventListener('mouseleave', function () { var c = cc(); if (c) reset(c); });
  function flip() { var c = cc(); if (!c) return; c.classList.toggle('flipped');
    c.setAttribute('aria-pressed', c.classList.contains('flipped') ? 'true' : 'false'); }
  document.addEventListener('click', function (e) { if (e.target.closest && e.target.closest('#cc')) flip(); });
  document.addEventListener('keydown', function (e) {
    var a = document.activeElement;
    if ((e.key === 'Enter' || e.key === ' ') && a && a.id === 'cc') { e.preventDefault(); flip(); }
  });
})();

// ---------- Equipo: tarjetas verticales (.tc) — inclinación, brillo y volteo ----------
(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
  function clear(c) { ['--rx', '--ry', '--mx', '--my'].forEach(function (k) { c.style.removeProperty(k); }); }
  document.addEventListener('mousemove', function (e) {
    if (reduce || !fine) return;
    var hit = e.target.closest ? e.target.closest('.tc') : null;
    document.querySelectorAll('.tc').forEach(function (c) {
      if (c !== hit) { clear(c); return; }
      var r = c.getBoundingClientRect();
      var x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      c.style.setProperty('--rx', ((0.5 - y) * 10).toFixed(2) + 'deg');
      c.style.setProperty('--ry', ((x - 0.5) * 12).toFixed(2) + 'deg');
      c.style.setProperty('--mx', (x * 100).toFixed(1) + '%');
      c.style.setProperty('--my', (y * 100).toFixed(1) + '%');
    });
  });
  function copyEmail(btn) {
    var email = btn.getAttribute('data-email');
    function done() { btn.classList.add('copied'); clearTimeout(btn._t);
      btn._t = setTimeout(function () { btn.classList.remove('copied'); }, 1800); }
    function fallback() { var t = document.createElement('textarea'); t.value = email;
      t.style.position = 'fixed'; t.style.opacity = '0'; document.body.appendChild(t); t.select();
      try { document.execCommand('copy'); done(); } catch (err) { window.prompt('Copia el correo:', email); }
      document.body.removeChild(t); }
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(email).then(done, fallback);
    else fallback();
  }
  function flip(c) { c.classList.toggle('flipped');
    c.setAttribute('aria-pressed', c.classList.contains('flipped') ? 'true' : 'false'); }
  document.addEventListener('click', function (e) {
    if (!e.target.closest) return;
    var cp = e.target.closest('.tc-copy');
    if (cp) { copyEmail(cp); return; }
    if (e.target.closest('a, button')) return;   // los enlaces funcionan sin voltear
    var c = e.target.closest('.tc'); if (c) flip(c);
  });
  document.addEventListener('keydown', function (e) {
    var a = document.activeElement;
    if ((e.key === 'Enter' || e.key === ' ') && a && a.classList && a.classList.contains('tc')) {
      e.preventDefault(); flip(a); }
  });
})();

// ---------- Modelos: carrusel deslizable (flechas, puntos y tarjeta activa) ----------
(function () {
  function slides(t) { return t.querySelectorAll('.mc-slide'); }
  var PAD = 10;                    // = padding lateral de .mc-track
  function current(t) {           // primera tarjeta visible (alineada al inicio)
    var x = t.scrollLeft + PAD, best = 0, d = Infinity;
    slides(t).forEach(function (s, i) {
      var dd = Math.abs(s.offsetLeft - x); if (dd < d) { d = dd; best = i; } });
    return best;
  }
  function visible(t, i) {         // cuántas tarjetas caben a la vez
    var s = slides(t)[i]; if (!s) return 1;
    return Math.max(1, Math.round((t.clientWidth - 2 * PAD + 20) / (s.offsetWidth + 20)));
  }
  function go(t, i) {
    var all = slides(t), n = all.length;
    i = Math.max(0, Math.min(i, n - 1));
    t.scrollTo({ left: all[i].offsetLeft - PAD, behavior: 'smooth' });
  }
  function sync(t) {
    var w = t.closest('.mc-wrap'); if (!w) return;
    var i = current(t), n = slides(t).length, v = visible(t, i);
    var end = t.scrollLeft + t.clientWidth >= t.scrollWidth - 4;
    if (end) i = Math.max(0, n - v);
    slides(t).forEach(function (s, k) { s.classList.toggle('is-active', k >= i && k < i + v); });
    w.querySelectorAll('.mc-dot').forEach(function (d, k) {
      var on = k >= i && k < i + v;
      d.classList.toggle('on', on);
      if (on) d.setAttribute('aria-current', 'true'); else d.removeAttribute('aria-current'); });
    var p = w.querySelector('.mc-prev'), nx = w.querySelector('.mc-next');
    if (p) p.disabled = i <= 0 && t.scrollLeft < 4;
    if (nx) nx.disabled = end;
  }
  document.addEventListener('click', function (e) {
    if (!e.target.closest) return;
    var b = e.target.closest('.mc-prev, .mc-next, .mc-dot'); if (!b) return;
    var w = b.closest('.mc-wrap'), t = w && w.querySelector('.mc-track'); if (!t) return;
    if (b.classList.contains('mc-dot')) go(t, +b.getAttribute('data-i'));
    else go(t, current(t) + (b.classList.contains('mc-next') ? 1 : -1));
  });
  document.addEventListener('keydown', function (e) {
    var t = document.activeElement;
    if (!t || !t.classList || !t.classList.contains('mc-track')) return;
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      e.preventDefault(); go(t, current(t) + (e.key === 'ArrowRight' ? 1 : -1)); }
  });
  var raf = 0;
  document.addEventListener('scroll', function (e) {
    var t = e.target;
    if (!t.classList || !t.classList.contains('mc-track')) return;
    cancelAnimationFrame(raf); raf = requestAnimationFrame(function () { sync(t); });
  }, true);
  // Predecir: al mover cualquier control, la tarjeta "late" al menos 0,9 s (y mientras Dash recalcula)
  var busyT = 0;
  function busy(e) {
    if (!e.target.closest || !e.target.closest('.pf-form')) return;
    var v = document.getElementById('pf-verdict'); if (!v) return;
    v.classList.add('pf-busy'); clearTimeout(busyT);
    busyT = setTimeout(function () { v.classList.remove('pf-busy'); }, 900);
  }
  document.addEventListener('input', busy, true);
  document.addEventListener('change', busy, true);
  document.addEventListener('pointerup', busy, true);
  // Dash dibuja la página después de cargar: sincroniza cuando aparece un carrusel nuevo
  function scan() {
    document.querySelectorAll('.mc-track:not([data-ready])').forEach(function (t) {
      t.setAttribute('data-ready', '1'); t.scrollLeft = 0; sync(t); });
  }
  new MutationObserver(scan).observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener('resize', function () {
    document.querySelectorAll('.mc-track').forEach(function (t) { sync(t); }); });
})();


// ---------- Kyo: abrir y cerrar el panel (Kyo se queda fijo en la esquina inferior derecha) ----------
(function () {
  var root = document.documentElement;
  function walker() { return document.getElementById('kyo-walker'); }
  function relayout() { setTimeout(function () { window.dispatchEvent(new Event('resize')); }, 330); }
  function openBot() {
    if (root.classList.contains('bot-open')) return;
    var w = walker(); if (w) w.classList.remove('talk');
    root.classList.add('bot-open'); relayout();
    setTimeout(function () { var i = document.getElementById('bot-input'); if (i) i.focus(); }, 340);
  }
  function closeBot() {
    if (!root.classList.contains('bot-open')) return;
    root.classList.remove('bot-open'); relayout();
    var w = walker(); if (w) w.focus({ preventScroll: true });
  }
  window.kyo = { open: openBot, close: closeBot };
  document.addEventListener('click', function (e) {
    if (!e.target.closest) return;
    if (e.target.closest('#kyo-walker')) { openBot(); return; }
    if (e.target.closest('#bot-close')) closeBot();
  });
  document.addEventListener('keydown', function (e) {
    var a = document.activeElement;
    if ((e.key === 'Enter' || e.key === ' ') && a && a.id === 'kyo-walker') { e.preventDefault(); openBot(); }
    if (e.key === 'Escape' && root.classList.contains('bot-open')) closeBot();
  });
  // Al entrar, Kyo saluda unos segundos con su globo y luego solo lo muestra al pasar el mouse
  setTimeout(function () {
    var w = walker(); if (!w || root.classList.contains('bot-open')) return;
    w.classList.add('talk'); setTimeout(function () { w.classList.remove('talk'); }, 5000);
  }, 1500);
  // Desplaza el chat al último mensaje cuando llega una respuesta
  new MutationObserver(function () {
    var m = document.getElementById('bot-msgs');
    if (m && m.dataset.n !== String(m.children.length)) { m.dataset.n = m.children.length; m.scrollTop = m.scrollHeight; }
  }).observe(document.documentElement, { childList: true, subtree: true });
})();
