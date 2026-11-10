// =============================================================================
// Shiny: navegación por #/ruta, idioma, tema claro/oscuro, menú plegable y Kyo
// (el resto de la interacción —portada, carrusel, equipo, Predecir— está en comun.js)
// =============================================================================
(function () {
  var root = document.documentElement;
  function guardar(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function leer(k, d) { try { return localStorage.getItem(k) || d; } catch (e) { return d; } }

  var lang = leer('lang', 'es') === 'en' ? 'en' : 'es';
  var theme = leer('theme', 'light') === 'dark' ? 'dark' : 'light';
  var collapsed = false;

  function ruta() {
    var h = (location.hash || '').replace(/^#/, '');
    if (!h || h.charAt(0) !== '/') h = '/';
    if (h.length > 1 && h.slice(-1) === '/') h = h.slice(0, -1);
    return h;
  }
  function aplicar() {
    root.setAttribute('data-theme', theme);
    root.setAttribute('lang', lang); root.setAttribute('data-lang', lang);
    document.title = lang === 'en' ? 'EDA · Credit Risk' : 'EDA · Riesgo Crediticio';
    var shell = document.getElementById('shell');
    if (shell) shell.className = ruta() === '/' ? 'app cover' : (collapsed ? 'app collapsed' : 'app');
    document.querySelectorAll('.theme-toggle').forEach(function (b) {
      b.title = theme === 'dark' ? (lang === 'en' ? 'Switch to light mode' : 'Cambiar a modo claro')
                                 : (lang === 'en' ? 'Switch to dark mode' : 'Cambiar a modo oscuro'); });
    var bi = document.getElementById('bot-input');
    if (bi) bi.placeholder = lang === 'en' ? 'Ask me about any part of the dashboard…' : 'Pregúntame por cualquier parte del tablero…';
    document.querySelectorAll('.lang-switch').forEach(function (b) {
      b.title = lang === 'en' ? 'Cambiar a español' : 'Switch to English'; });
  }
  function enviar() {
    if (!window.Shiny || !Shiny.setInputValue) return;
    Shiny.setInputValue('route', ruta());
    Shiny.setInputValue('lang', lang);
    Shiny.setInputValue('theme', theme);
  }
  aplicar();

  document.addEventListener('click', function (e) {
    if (!e.target.closest) return;
    if (e.target.closest('.lang-switch')) {
      lang = lang === 'en' ? 'es' : 'en'; guardar('lang', lang); aplicar(); enviar(); return; }
    if (e.target.closest('.theme-toggle')) {
      theme = theme === 'dark' ? 'light' : 'dark'; guardar('theme', theme); aplicar(); enviar(); return; }
    if (e.target.closest('#sb-btn')) {
      collapsed = !collapsed; aplicar();
      setTimeout(function () { window.dispatchEvent(new Event('resize')); }, 350); return; }
  });
  window.addEventListener('hashchange', function () {
    aplicar(); enviar();
    window.scrollTo(0, 0);
    var sb = document.querySelector('.sidebar'); if (sb && window.innerWidth <= 900) sb.scrollTop = 0;
  });
  $(document).on('shiny:connected', function () { enviar(); });

  // Fórmulas: MathJax vuelve a dibujar cuando cambia el contenido (páginas y chat de Kyo)
  var mjT = 0;
  function typeset() {
    clearTimeout(mjT);
    mjT = setTimeout(function () {
      // si MathJax aún no terminó de cargar (abre directo en una página con fórmulas), reintenta
      if (!(window.MathJax && MathJax.typesetPromise)) { mjT = setTimeout(typeset, 300); return; }
      MathJax.typesetPromise().catch(function () {});
    }, 60);
  }
  $(document).on('shiny:value', function (e) {
    if (e.name === 'page' || e.name === 'bot-msgs') typeset();
    if (e.name === 'page') setTimeout(function () { window.dispatchEvent(new Event('resize')); }, 80);
  });

  // Kyo: Enter envía; las sugerencias viajan con su texto
  document.addEventListener('keydown', function (e) {
    var a = document.activeElement;
    if (e.key === 'Enter' && a && a.id === 'bot-input') {
      e.preventDefault();
      Shiny.setInputValue('bot_send', { t: a.value, n: Date.now() }, { priority: 'event' });
      a.value = '';
    }
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest) return;
    var b = e.target.closest('#bot-send');
    if (b) { var i = document.getElementById('bot-input');
      Shiny.setInputValue('bot_send', { t: i.value, n: Date.now() }, { priority: 'event' }); i.value = ''; return; }
    var s = e.target.closest('.bot-sug');
    if (s) { Shiny.setInputValue('bot_send', { t: s.getAttribute('data-q'), n: Date.now() }, { priority: 'event' }); return; }
    if (e.target.closest('#bot-reset')) Shiny.setInputValue('bot_reset', Date.now(), { priority: 'event' });
  });

  // Correo del equipo: el botón no debe voltear la tarjeta (comun.js lo maneja)

  // Modelo original: pestañas Teoría / Metodología / Código / Resultados.
  // Shiny pausa las gráficas ocultas; al mostrar una pestaña se avisa con 'shown' y un resize.
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('.cs-tab'); if (!b) return;
    var v = b.getAttribute('data-tab');
    document.querySelectorAll('.cs-tab').forEach(function (x) { x.classList.toggle('cs-tab--on', x === b); });
    document.querySelectorAll('.cs-pane').forEach(function (p) {
      var on = p.getAttribute('data-pane') === v;
      p.style.display = on ? '' : 'none';
      if (on) $(p).trigger('shown');
    });
    setTimeout(function () { window.dispatchEvent(new Event('resize')); typeset(); resaltar(); }, 60);
  });
  // Código de CS-FOF con colores de sintaxis (highlight.js)
  function resaltar() {
    if (!window.hljs) return;
    document.querySelectorAll('pre.cs-code code:not(.hljs)').forEach(function (c) { hljs.highlightElement(c); });
  }
  $(document).on('shiny:value', function (e) { if (e.name === 'page') setTimeout(resaltar, 80); });
})();
