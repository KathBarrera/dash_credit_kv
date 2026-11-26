// Ventana del pipeline del proyecto: se abre con cualquier botón [data-pipe-open], resalta la etapa pedida
// (data-stage) y se cierra con la X, el fondo, Esc o al seguir un enlace del tablero.
(function () {
  'use strict';
  var opener = null;
  function modal() { return document.getElementById('pipe-modal'); }
  function open(stage) {
    var m = modal();
    if (!m) return;
    m.classList.add('on');
    document.documentElement.classList.add('pipe-open');
    var stages = m.querySelectorAll('.pipe-stage'), hit = null;
    Array.prototype.forEach.call(stages, function (s) {
      var on = !!stage && s.getAttribute('data-stage') === stage;
      s.classList.toggle('pipe-hl', on);
      if (on) hit = s;
    });
    var body = m.querySelector('.pipe-body');
    if (body) body.scrollTop = 0;
    if (hit) setTimeout(function () { hit.scrollIntoView({ block: 'center', behavior: 'smooth' }); }, 60);
    var x = m.querySelector('#pipe-close');
    if (x) x.focus();
  }
  function close() {
    var m = modal();
    if (!m || !m.classList.contains('on')) return;
    m.classList.remove('on');
    document.documentElement.classList.remove('pipe-open');
    if (opener && opener.isConnected) opener.focus();
    opener = null;
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest ? e.target.closest('[data-pipe-open]') : null;
    if (b) { opener = b; open(b.getAttribute('data-pipe-open') || ''); return; }
    if (e.target.closest && (e.target.closest('[data-pipe-close]') || e.target.closest('.pipe-link'))) close();
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
})();
