// Símbolos de las ecuaciones: burbuja con su significado e iluminación de todos los lugares donde se usan.
//
//  - El glosario (window.EQ_GLOSS) lo genera tablero/glosario.py y lo inserta en la página.
//  - MathJax dibuja cada ecuación como un SVG con <g data-mml-node="mi|msub|…">. Aquí se reconoce cada símbolo
//    por su forma («S_w», «n_0», «p̂_t»…) y, si está en el glosario de su ámbito, se marca con data-eqv.
//    Un ámbito es el glosario al que pertenece la ecuación: lo da el ancestro con data-gscope.
//  - Los símbolos de los textos ya vienen marcados (<span class="eqv" data-eqv data-gs>) y los identificadores del
//    código (<pre data-scope>) se envuelven aquí según window.EQ_GLOSS.code.
//  - Al pasar el cursor (o tocar) un símbolo se ilumina todo lo que tenga el mismo data-eqv y data-gs, y la burbuja
//    dice en qué ecuaciones, líneas de código y textos aparece.
(function () {
  'use strict';
  var G = window.EQ_GLOSS || { g: {}, code: {} };
  var tip = null, cur = null, lit = [], sticky = false, timer = null;

  function lang() { return document.documentElement.getAttribute('data-lang') === 'en' ? 'en' : 'es'; }

  // ---------- reconocer símbolos en el SVG de MathJax ----------
  function norm(s) {
    return s.normalize('NFKC').replace(/−/g, '-').replace(/ϵ/g, 'ε').replace(/ϕ/g, 'φ')
            .replace(/ϑ/g, 'θ').replace(/ϖ/g, 'π');
  }
  function kids(g) {
    return Array.prototype.filter.call(g.children, function (c) { return c.tagName === 'g' && c.hasAttribute('data-mml-node'); });
  }
  function leaf(g) {
    var out = '';
    Array.prototype.forEach.call(g.children, function (c) {
      if (c.tagName === 'use' && c.hasAttribute('data-c')) {
        var cp = parseInt(c.getAttribute('data-c'), 16);
        out += (cp >= 0x1D7D8 && cp <= 0x1D7E1) ? String.fromCodePoint(cp) : norm(String.fromCodePoint(cp));
      } else if (c.tagName === 'text') {
        var s = c.textContent || '';
        out += /^[\u{1D7D8}-\u{1D7E1}]$/u.test(s) ? s : norm(s);
      }
    });
    return out;
  }
  function tok(g) {
    var t = g.getAttribute('data-mml-node'), k = kids(g);
    switch (t) {
      case 'mi': case 'mn': case 'mo': case 'mtext': return leaf(g);
      case 'msub': return k.length > 1 ? tok(k[0]) + '_' + tok(k[1]) : null;
      case 'msup': return k.length > 1 ? tok(k[0]) + '^' + tok(k[1]) : null;
      case 'msubsup': return k.length > 2 ? tok(k[0]) + '_' + tok(k[1]) + '^' + tok(k[2]) : null;
      case 'mover':
        if (k.length > 1) { var a = tok(k[1]); return tok(k[0]) + (a === '^' ? '̂' : a === '~' ? '̃' : ''); }
        return null;
      case 'mrow': case 'TeXAtom': case 'mstyle': case 'math':
        return k.map(function (c) { return tok(c) || ''; }).join('');
      default: return '';
    }
  }
  var LABELLED = { mi: 1, mn: 1, msub: 1, msup: 1, msubsup: 1, mover: 1 };
  function visit(g, scope, dict) {
    var t = g.getAttribute('data-mml-node');
    if (LABELLED[t]) {
      var tk = tok(g);
      if (tk && dict[tk]) {
        g.setAttribute('data-eqv', tk); g.setAttribute('data-gs', scope); g.classList.add('eqv');
        return;
      }
    }
    kids(g).forEach(function (c) { visit(c, scope, dict); });
  }
  function labelMath(c) {
    c.setAttribute('data-eqv-done', '1');
    var box = c.closest('[data-gscope]');
    if (!box) return;
    var scope = box.getAttribute('data-gscope'), dict = G.g[scope];
    if (!dict) return;
    var root = c.querySelector('g[data-mml-node="math"]');
    if (root) visit(root, scope, dict);
    // zona de contacto: un rectángulo transparente del tamaño del símbolo (los huecos de un símbolo no reciben el cursor)
    Array.prototype.forEach.call(c.querySelectorAll('g.eqv'), function (g) {
      try {
        var b = g.getBBox();
        if (!b.width || !b.height) return;
        var r = document.createElementNS('http://www.w3.org/2000/svg', 'rect'), pad = 40;
        r.setAttribute('x', b.x - pad); r.setAttribute('y', b.y - pad);
        r.setAttribute('width', b.width + 2 * pad); r.setAttribute('height', b.height + 2 * pad);
        r.setAttribute('fill', 'none'); r.setAttribute('stroke', 'none'); r.setAttribute('pointer-events', 'all');
        g.insertBefore(r, g.firstChild);
      } catch (e) { /* aún sin dibujar */ }
    });
  }

  // ---------- identificadores del código ----------
  function wrapCode(pre) {
    pre.setAttribute('data-eqv-done', '1');
    var scope = pre.getAttribute('data-scope'), map = (G.code || {})[scope];
    if (!map || !G.g[scope]) return;
    var names = Object.keys(map).sort(function (a, b) { return b.length - a.length; });
    if (!names.length) return;
    var re = new RegExp('(^|[^A-Za-z0-9_])(' + names.join('|') + ')(?![A-Za-z0-9_])', 'g');
    var w = document.createTreeWalker(pre, NodeFilter.SHOW_TEXT, null), nodes = [], n;
    while ((n = w.nextNode())) nodes.push(n);
    nodes.forEach(function (node) {
      var txt = node.nodeValue;
      if (!txt || node.parentNode.closest('.hl-com, .hl-str')) return;
      re.lastIndex = 0;
      if (!re.test(txt)) return;
      re.lastIndex = 0;
      var frag = document.createDocumentFragment(), last = 0, m;
      while ((m = re.exec(txt))) {
        var start = m.index + m[1].length;
        frag.appendChild(document.createTextNode(txt.slice(last, start)));
        var sp = document.createElement('span');
        sp.className = 'eqv eqv-code'; sp.textContent = m[2];
        sp.setAttribute('data-eqv', map[m[2]]); sp.setAttribute('data-gs', scope);
        frag.appendChild(sp);
        last = start + m[2].length;
      }
      frag.appendChild(document.createTextNode(txt.slice(last)));
      node.parentNode.replaceChild(frag, node);
    });
  }

  function scan() {
    Array.prototype.forEach.call(document.querySelectorAll('mjx-container:not([data-eqv-done])'), labelMath);
    Array.prototype.forEach.call(document.querySelectorAll('pre[data-scope]:not([data-eqv-done])'), wrapCode);
  }
  function later() { clearTimeout(timer); timer = setTimeout(scan, 120); }
  new MutationObserver(later).observe(document.documentElement, { childList: true, subtree: true });
  later();

  // ---------- burbuja e iluminación ----------
  function esc(s) { return s.replace(/\\/g, '\\\\').replace(/"/g, '\\"'); }
  function same(el) {
    return document.querySelectorAll('[data-gs="' + esc(el.getAttribute('data-gs')) + '"][data-eqv="' + esc(el.getAttribute('data-eqv')) + '"]');
  }
  function ensureTip() {
    if (tip && tip.isConnected) return tip;
    tip = document.createElement('div');
    tip.id = 'eqv-tip'; tip.setAttribute('role', 'tooltip');
    document.body.appendChild(tip);
    return tip;
  }
  function where(list) {
    var en = lang() === 'en', eqs = [], code = 0, text = 0;
    Array.prototype.forEach.call(list, function (e) {
      var eq = e.closest('.cs-eq'), n = eq && eq.querySelector('.cs-eq-n');
      if (e.classList.contains('eqv-code')) code++;
      else if (e.namespaceURI && e.namespaceURI.indexOf('svg') >= 0 || e.closest('mjx-container')) {
        var lbl = n ? n.textContent.trim() : (en ? 'equation' : 'ecuación');
        if (eqs.indexOf(lbl) < 0) eqs.push(lbl);
      } else text++;
    });
    var out = [];
    if (eqs.length) out.push((en ? 'equations ' : 'ecuaciones ') + eqs.join(', '));
    if (code) out.push((en ? 'code ×' : 'código ×') + code);
    if (text) out.push((en ? 'text ×' : 'texto ×') + text);
    return out.join(' · ');
  }
  function show(el) {
    var info = (G.g[el.getAttribute('data-gs')] || {})[el.getAttribute('data-eqv')];
    cur = el;
    lit = Array.prototype.slice.call(same(el));
    lit.forEach(function (e) { e.classList.add('eqv-on'); });
    if (!info) return;
    var l = lang(), d = info[l] || info.es, t = ensureTip();
    t.innerHTML = '';
    var h = document.createElement('div'); h.className = 'eqv-h';
    var s = document.createElement('b'); s.textContent = info.sym;
    var nm = document.createElement('span'); nm.textContent = d[0];
    h.appendChild(s); h.appendChild(nm);
    var p = document.createElement('div'); p.className = 'eqv-d'; p.textContent = d[1];
    var w = document.createElement('div'); w.className = 'eqv-w';
    w.textContent = (l === 'en' ? 'Appears in: ' : 'Aparece en: ') + where(lit);
    t.appendChild(h); t.appendChild(p); t.appendChild(w);
    t.classList.add('on');
    var r = el.getBoundingClientRect(), tw = t.offsetWidth, th = t.offsetHeight;
    var x = Math.max(8, Math.min(window.innerWidth - tw - 8, r.left + r.width / 2 - tw / 2));
    var y = r.top - th - 10; if (y < 8) y = r.bottom + 10;
    t.style.left = x + 'px'; t.style.top = y + 'px';
  }
  function clear() {
    lit.forEach(function (e) { e.classList.remove('eqv-on'); });
    lit = []; cur = null; sticky = false;
    if (tip) tip.classList.remove('on');
  }
  document.addEventListener('mouseover', function (e) {
    if (sticky) return;
    var el = e.target.closest ? e.target.closest('[data-eqv]') : null;
    if (el === cur) return;
    clear();
    if (el) show(el);
  });
  document.addEventListener('click', function (e) {
    var el = e.target.closest ? e.target.closest('[data-eqv]') : null;
    if (el && (window.matchMedia && window.matchMedia('(hover: none)').matches)) {   // pantallas táctiles: tocar fija la burbuja
      if (sticky && el === cur) { clear(); return; }
      clear(); show(el); sticky = true; return;
    }
    if (sticky) clear();
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') clear(); });
  window.addEventListener('scroll', function () { if (cur && !sticky) clear(); }, true);
})();
