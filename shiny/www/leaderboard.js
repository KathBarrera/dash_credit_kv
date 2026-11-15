// Tabla de líderes de «Modelos»: clic (o Enter) en un encabezado ordena; el buscador filtra las filas.
// Un único listener delegado en document, porque la página se vuelve a crear al navegar.
(function () {
  'use strict';
  function val(td, num) {
    var s = (td.getAttribute('data-v') || td.textContent).trim();
    if (!num) return s.toLowerCase();
    var x = parseFloat(s.replace(/,/g, ''));
    return isNaN(x) ? null : x;
  }
  function sortBy(th) {
    var table = th.closest('table'), tb = table.tBodies[0];
    var k = +th.getAttribute('data-k'), num = th.getAttribute('data-t') === 'num';
    var dir = th.getAttribute('aria-sort') === 'ascending' ? -1 : 1;
    table.querySelectorAll('th.lb-sort').forEach(function (h) { h.removeAttribute('aria-sort'); });
    th.setAttribute('aria-sort', dir === 1 ? 'ascending' : 'descending');
    var rows = Array.prototype.slice.call(tb.rows);
    rows.sort(function (a, b) {
      var x = val(a.cells[k], num), y = val(b.cells[k], num);
      if (x === null && y === null) return 0;
      if (x === null) return 1;            // vacíos siempre al final
      if (y === null) return -1;
      return (x < y ? -1 : x > y ? 1 : 0) * dir;
    });
    rows.forEach(function (r) { tb.appendChild(r); });
  }
  function filter(inp) {
    var box = inp.closest('.lb'), q = inp.value.trim().toLowerCase(), n = 0;
    var rows = box.querySelectorAll('tbody tr');
    rows.forEach(function (r) {
      var ok = !q || r.textContent.toLowerCase().indexOf(q) >= 0;
      r.style.display = ok ? '' : 'none'; if (ok) n++;
    });
    var c = box.querySelector('.lb-count');
    if (c) c.textContent = c.getAttribute('data-tpl').replace('{n}', n).replace('{t}', rows.length);
  }
  document.addEventListener('click', function (e) {
    var th = e.target.closest && e.target.closest('th.lb-sort');
    if (th) sortBy(th);
  });
  document.addEventListener('keydown', function (e) {
    var th = e.target.closest && e.target.closest('th.lb-sort');
    if (th && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); sortBy(th); }
  });
  document.addEventListener('input', function (e) {
    if (e.target.classList && e.target.classList.contains('lb-search')) filter(e.target);
  });
})();
