// Modo «foco»: amplía una tarjeta (.card o .kpi) al centro de la pantalla con el resto de la página oscurecido.
//  - Un único listener delegado en document: las tarjetas se crean y destruyen al navegar (Dash/React).
//  - La tarjeta NO se mueve del DOM: se le añade la clase .card-zoomed (position:fixed) y la capa oscura es
//    un elemento aparte (#focus-overlay) colgado de <body>.
(function () {
  'use strict';
  var ZOOMED = 'card-zoomed';
  var CARD = '.card:not(.no-zoom), .kpi:not(.no-zoom)';   // .no-zoom: tarjetas que no se amplían (filtros globales)
  // Elementos sobre los que un clic NO debe ampliar la tarjeta (el botón de ampliar es el camino seguro).
  var INTERACTIVE = [
    'a', 'button', 'input', 'select', 'textarea', 'label', 'summary', 'option',
    '[role="button"]', '[role="tab"]', '[role="slider"]', '[role="combobox"]', '[role="listbox"]', '[role="option"]',
    '[role="checkbox"]', '[role="radio"]', '[role="switch"]', '[role="link"]', '[contenteditable="true"]',
    '[class*="slider"]', '[class*="dropdown"]', '[class*="Select"]',
    '.js-plotly-plot', '.modebar', '.dash-table-container', '.dash-spreadsheet-container', 'table',
    '[tabindex]:not([tabindex="-1"])'
  ].join(',');

  var overlay = null, zoomed = null, opener = null, path0 = '', scrollY0 = 0, frozen = null, lifted = [];

  function ensureOverlay() {
    if (overlay && overlay.isConnected) return overlay;
    overlay = document.createElement('div');
    overlay.id = 'focus-overlay';
    overlay.className = 'focus-overlay';
    overlay.setAttribute('aria-hidden', 'true');
    document.body.appendChild(overlay);
    return overlay;
  }

  function lang() { return document.documentElement.getAttribute('data-lang') === 'en' ? 'en' : 'es'; }

  // Redibuja los gráficos de Plotly de la tarjeta al nuevo tamaño (y avisa a la ventana)
  function resizePlots(card) {
    function go() {
      if (window.Plotly && card && card.isConnected) {
        card.querySelectorAll('.js-plotly-plot').forEach(function (g) {
          try { window.Plotly.Plots.resize(g); } catch (e) { /* gráfico aún sin dibujar */ }
        });
      }
      window.dispatchEvent(new Event('resize'));
    }
    requestAnimationFrame(function () { requestAnimationFrame(go); });
    setTimeout(go, 260);
  }

  function btnOf(card) {
    for (var i = 0; i < card.children.length; i++) {
      if (card.children[i].classList && card.children[i].classList.contains('card-zoom')) return card.children[i];
    }
    return null;
  }

  function setBtn(card, isOpen) {
    var b = btnOf(card); if (!b) return;
    var label = b.getAttribute(isOpen ? 'data-label-close' : 'data-label-open');
    if (label) { b.setAttribute('aria-label', label); b.setAttribute('title', label); }
    b.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  }

  // Un ancestro con position:sticky (o con z-index) crea su propio contexto de apilamiento y dejaría la tarjeta
  // ampliada por debajo de la capa oscura: se le sube el z-index mientras dure el modo foco.
  function lift(card) {
    for (var e = card.parentElement; e && e !== document.body; e = e.parentElement) {
      var cs = getComputedStyle(e);
      if (cs.position !== 'static' && (cs.position === 'sticky' || cs.position === 'fixed' || cs.zIndex !== 'auto')) {
        lifted.push({ el: e, z: e.style.zIndex });
        e.style.zIndex = '10010';
      }
    }
  }
  function unlift() {
    lifted.forEach(function (l) { l.el.style.zIndex = l.z; });
    lifted = [];
  }

  function open(card, from) {
    if (zoomed) close();
    zoomed = card; opener = from || btnOf(card);
    path0 = location.pathname; scrollY0 = window.scrollY;
    // La tarjeta sale del flujo (position:fixed): se fija la altura de su contenedor para que la página no salte.
    var par = card.parentElement;
    if (par) {
      frozen = { el: par, minHeight: par.style.minHeight };
      par.style.minHeight = par.offsetHeight + 'px';
    }
    lift(card);
    var title = card.querySelector('.card-title, .kpi-label');
    card.classList.add(ZOOMED);
    card.setAttribute('role', 'dialog');
    card.setAttribute('aria-modal', 'true');
    if (title) card.setAttribute('aria-label', title.textContent.trim());
    card.setAttribute('tabindex', '-1');
    setBtn(card, true);
    ensureOverlay().classList.add('on');
    document.documentElement.classList.add('focus-open');
    try { card.focus({ preventScroll: true }); } catch (e) { card.focus(); }
    resizePlots(card);
  }

  function close() {
    var card = zoomed; if (!card) return;
    zoomed = null;
    card.classList.remove(ZOOMED);
    card.removeAttribute('role'); card.removeAttribute('aria-modal');
    card.removeAttribute('aria-label'); card.removeAttribute('tabindex');
    card.scrollTop = 0;
    setBtn(card, false);
    if (frozen) { frozen.el.style.minHeight = frozen.minHeight; frozen = null; }
    unlift();
    if (overlay) overlay.classList.remove('on');
    document.documentElement.classList.remove('focus-open');
    if (Math.abs(window.scrollY - scrollY0) > 1) window.scrollTo(0, scrollY0);
    var back = opener; opener = null;
    if (back && back.isConnected) { try { back.focus({ preventScroll: true }); } catch (e) { back.focus(); } }
    resizePlots(card);
  }

  document.addEventListener('click', function (e) {
    var t = e.target;
    if (!t || !t.closest || e.button !== 0) return;
    // clic en la capa oscura
    if (t.id === 'focus-overlay') { if (zoomed) close(); return; }
    // botón de ampliar / cerrar de la esquina
    var btn = t.closest('.card-zoom');
    if (btn) {
      var c = btn.closest(CARD);
      if (!c) return;
      e.preventDefault();
      if (c === zoomed) close(); else open(c, btn);
      return;
    }
    if (zoomed) return;             // ya ampliada: sus controles funcionan con normalidad
    if (e.defaultPrevented) return;
    var card = t.closest(CARD);
    if (!card || t.closest(INTERACTIVE)) return;
    var sel = window.getSelection && window.getSelection();
    if (sel && String(sel).length > 0) return;   // el usuario estaba seleccionando texto
    open(card, btnOf(card));
  });

  // Escape cierra el modo foco (antes que el panel de Kyo o cualquier otro manejador de Escape),
  // salvo que haya un menú desplegable abierto: ese Escape es para el menú.
  document.addEventListener('keydown', function (e) {
    if (!zoomed) return;
    if (e.key === 'Escape') {
      if (document.querySelector('[aria-expanded="true"]:not(.card-zoom), [data-radix-popper-content-wrapper]')) return;
      e.stopPropagation(); e.preventDefault(); close();
    } else if (e.key === 'Tab') {
      var f = Array.prototype.filter.call(zoomed.querySelectorAll(
        'a[href],button:not([disabled]),input:not([disabled]),select,textarea,summary,[tabindex]:not([tabindex="-1"])'),
        function (n) { return n.offsetParent !== null || n.classList.contains('card-zoom'); });
      if (!f.length) { e.preventDefault(); return; }
      var a = document.activeElement;
      if (e.shiftKey && (a === f[0] || a === zoomed)) { e.preventDefault(); f[f.length - 1].focus(); }
      else if (!e.shiftKey && a === f[f.length - 1]) { e.preventDefault(); f[0].focus(); }
    }
  }, true);

  // Cambio de página (o la tarjeta desaparece del DOM): se cierra el modo foco y se quita la capa oscura.
  function check() {
    if (!zoomed) return;
    if (!zoomed.isConnected || location.pathname !== path0) {
      var card = zoomed; zoomed = null; frozen = null; opener = null; lifted = [];
      card.classList.remove(ZOOMED);
      if (overlay) overlay.classList.remove('on');
      document.documentElement.classList.remove('focus-open');
    }
  }
  new MutationObserver(check).observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener('popstate', check);
})();
