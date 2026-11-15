// Conserva el estado plegado/desplegado de «Filtros globales» al pasar de una página del EDA a la otra.
// Las tarjetas se recrean al navegar, así que se guarda en sessionStorage y se restaura al aparecer.
(function () {
  var KEY = 'ef-fold-open';
  function read() { try { return sessionStorage.getItem(KEY) === '1'; } catch (e) { return false; } }
  function write(v) { try { sessionStorage.setItem(KEY, v ? '1' : '0'); } catch (e) {} }
  // «toggle» no burbujea: se escucha en captura
  document.addEventListener('toggle', function (e) {
    var d = e.target;
    if (d && d.id === 'ef-fold') write(d.open);
  }, true);
  function restore() {
    var d = document.getElementById('ef-fold');
    if (d && !d.dataset.efRestored) {
      d.dataset.efRestored = '1';
      if (read() && !d.open) d.open = true;
    }
  }
  new MutationObserver(restore).observe(document.documentElement, { childList: true, subtree: true });
  restore();
})();
