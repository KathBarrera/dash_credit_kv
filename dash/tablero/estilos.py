# -*- coding: utf-8 -*-
"""CSS y JavaScript del tablero (portada, Kyo y paso a paso), con la paleta de config.py."""

from asistente import mascota_svg

from tablero.config import (CREAM, DEEP_NAVY, NAVY, PALE_GOLD, WARM_GOLD)
from tablero.iconos import _icon_css

CSS = """
:root {
  --deep:%%DEEP%%; --navy:%%NAVY%%; --pale:%%PALE%%; --gold:%%GOLD%%; --cream:%%CREAM%%;
  --bg:%%CREAM%%; --surface:#FFFFFF; --surface-2:#F8F6F0;
  --text:%%DEEP%%; --muted:#5D667F; --line:rgba(26,35,61,.10); --line-strong:rgba(26,35,61,.24);
  --accent:%%NAVY%%; --on-accent:#FFFFFF; --accent-2:%%GOLD%%;
  --side-bg:%%DEEP%%; --side-text:#D3D8E5; --side-muted:#9AA3BA; --side-line:rgba(255,255,255,.10);
  --note-bg:#F6F0E1; --note-line:%%GOLD%%; --tech-bg:#ECEEF4; --tech-line:%%NAVY%%;
  --code-bg:#EBE5D5; --th-bg:%%DEEP%%; --zebra:#FAF8F3; --focus:%%GOLD%%;
}
[data-theme="dark"] {
  color-scheme: dark;
  --bg:#141A2B; --surface:#1B2338; --surface-2:#222B43;
  --text:#E8E4DA; --muted:#A7B0C6; --line:rgba(232,228,218,.10); --line-strong:rgba(232,228,218,.26);
  --accent:%%PALE%%; --on-accent:#1A233D; --accent-2:%%PALE%%;
  --side-bg:#10162A; --side-text:#D3D8E5; --side-muted:#98A1B8; --side-line:rgba(255,255,255,.08);
  --note-bg:rgba(210,187,137,.12); --note-line:%%PALE%%; --tech-bg:rgba(142,156,198,.14); --tech-line:#8E9CC6;
  --code-bg:rgba(210,187,137,.16); --th-bg:#2A3552; --zebra:rgba(255,255,255,.03); --focus:%%PALE%%;
}
* { box-sizing:border-box; }
html { scroll-behavior:smooth; }
html, body { margin:0; padding:0; background:var(--bg); color:var(--text);
  font-family:Inter,'Segoe UI',Roboto,Helvetica,Arial,sans-serif; font-size:15px; line-height:1.55; }
a { color:inherit; }
:focus-visible { outline:2px solid var(--focus); outline-offset:2px; border-radius:6px; }

/* ---------- Íconos ---------- */
.ico { display:inline-block; flex:none; width:1.2em; height:1.2em; background-color:currentColor;
  -webkit-mask:var(--ico) center/contain no-repeat; mask:var(--ico) center/contain no-repeat; }

/* ---------- Barra lateral ---------- */
.sidebar { position:fixed; top:0; left:0; bottom:0; width:272px; background:var(--side-bg); color:var(--side-text);
  padding:24px 18px; display:flex; flex-direction:column; border-right:1px solid var(--side-line); overflow-y:auto;
  z-index:50; transition:transform .3s ease; }
.brand { display:block; color:inherit; text-decoration:none; padding:0 6px 18px; }
.brand-tag { color:var(--pale); font-size:12px; font-weight:600; }
.brand-title { font-size:20px; line-height:1.25; font-weight:700; margin:6px 0 4px; color:#fff; }
.brand-sub { color:var(--side-muted); font-size:12.5px; margin:0; }
.nav { border-top:1px solid var(--side-line); padding-top:12px; }
.nav a { display:flex; align-items:center; gap:11px; padding:9px 12px; margin:2px 0; border-radius:8px; color:var(--side-text);
  text-decoration:none; font-weight:500; position:relative; transition:background .15s, color .15s; }
.nav a .ico { opacity:.8; }
.nav a:hover { background:rgba(255,255,255,.07); color:#fff; }
.nav a.active { background:rgba(255,255,255,.10); color:#fff; font-weight:600; }
.nav a.active::before { content:''; position:absolute; left:0; top:8px; bottom:8px; width:3px; border-radius:3px; background:var(--pale); }
.nav a.active .ico { opacity:1; color:var(--pale); }
.authors { margin-top:auto; padding:16px 6px 0; border-top:1px solid var(--side-line); }
.authors h4 { margin:0 0 10px; color:var(--pale); font-size:12.5px; font-weight:600; }
.author { margin-bottom:10px; }
.author .nm { font-weight:600; font-size:13.5px; color:#fff; }
.author .em { font-size:12px; color:var(--side-muted); word-break:break-all; }
.inst { font-size:11.5px; color:var(--side-muted); margin-top:8px; }
.app.collapsed .sidebar { transform:translateX(-100%); }
.app.collapsed .main { margin-left:0; }

/* ---------- Estructura y barra superior ---------- */
.main { margin-left:272px; min-height:100vh; display:flex; flex-direction:column; transition:margin-left .3s ease; }
.topbar { background:var(--surface); color:var(--text); padding:12px 32px; border-bottom:1px solid var(--line);
  display:flex; justify-content:space-between; align-items:center; gap:16px; position:sticky; top:0; z-index:40; }
.tb-left, .tb-right { display:flex; align-items:center; gap:12px; }
.topbar .t1 { font-weight:700; font-size:16px; }
.topbar .t2 { color:var(--muted); font-size:12.5px; }
.badge { color:var(--muted); font-size:12.5px; font-weight:500; padding:5px 12px; border-radius:999px;
  border:1px solid var(--line-strong); white-space:nowrap; }
.icon-btn { display:inline-flex; align-items:center; justify-content:center; width:36px; height:36px; padding:0;
  background:transparent; border:1px solid var(--line-strong); border-radius:8px; color:var(--text); cursor:pointer;
  text-decoration:none; font-family:inherit; transition:background .15s, border-color .15s, color .15s; }
.icon-btn .ico { width:18px; height:18px; }
.icon-btn:hover { background:var(--surface-2); border-color:var(--accent-2); color:var(--accent-2); }
.theme-toggle { position:relative; display:inline-flex; align-items:center; width:62px; height:32px; padding:3px;
  border-radius:999px; border:1px solid var(--line-strong); background:var(--surface-2); cursor:pointer; }
.theme-toggle::before { content:''; position:absolute; top:3px; left:3px; width:24px; height:24px; border-radius:50%;
  background:var(--accent); transition:transform .2s ease; }
[data-theme="dark"] .theme-toggle::before { transform:translateX(30px); }
.theme-toggle .ico { position:relative; z-index:1; width:24px; height:24px; -webkit-mask-size:14px; mask-size:14px; }
.theme-toggle .t-sun { color:var(--on-accent); } .theme-toggle .t-moon { color:var(--muted); margin-left:6px; }
[data-theme="dark"] .theme-toggle .t-sun { color:var(--muted); }
[data-theme="dark"] .theme-toggle .t-moon { color:var(--on-accent); }
.content { padding:28px 32px 10px; flex:1; }

/* ---------- Títulos ---------- */
.page-title h2 { margin:0; font-size:27px; font-weight:700; letter-spacing:-.01em; display:flex; align-items:center; gap:12px; }
.page-title .pt-ico { width:26px; height:26px; color:var(--accent-2); }
.page-title { margin-bottom:22px; } .page-title p { margin:6px 0 22px; color:var(--muted); }
.section-h { font-size:18px; font-weight:700; margin:30px 0 12px; }

/* ---------- Tarjetas y KPI ---------- */
.video-wrap { position:relative; width:100%; max-width:960px; margin:0 auto; aspect-ratio:16/9; border-radius:10px; overflow:hidden; background:#000; }
.video-wrap iframe { position:absolute; inset:0; width:100%; height:100%; border:0; }
.video-empty { display:flex; flex-direction:column; align-items:center; justify-content:center; gap:6px; text-align:center;
  background:var(--surface-2); border:2px dashed var(--line-strong); color:var(--muted); padding:16px;
  aspect-ratio:auto; min-height:220px; }
.video-empty b { color:var(--text); font-size:17px; }
.video-ico { width:46px; height:46px; color:var(--accent-2); }
.video-link { display:inline-flex; align-items:center; gap:6px; margin-top:10px; font-weight:600; }
.video-link svg { width:16px; height:16px; }
.card { background:var(--surface); border-radius:10px; padding:20px 22px; margin-bottom:20px; border:1px solid var(--line); min-width:0; }
.card-title { margin:0 0 4px; font-size:17px; font-weight:700; }
.card-sub { margin:0 0 12px; color:var(--muted); font-size:13px; }
.card p { margin:8px 0; }
.card ul { margin:6px 0 6px 20px; padding:0; } .card li { margin:4px 0; }
.card ol { margin:6px 0 6px 22px; padding:0; }
.muted { color:var(--muted); font-size:13.5px; }
.refs li { font-size:13.5px; }
.refs.ieee { display:grid; gap:8px; }
.target-strip { margin:4px 0 14px; }
.ts-head { display:flex; justify-content:space-between; font-size:13px; color:var(--muted); margin-bottom:6px; }
.ts-ratio b { color:var(--text); }
.ts-bar { display:flex; height:30px; border-radius:8px; overflow:hidden; font-size:12.5px; font-weight:700; }
.ts-seg { display:flex; align-items:center; padding:0 10px; white-space:nowrap; overflow:hidden; }
.ts-0 { background:var(--accent); color:var(--on-accent); }
.ts-1 { background:#B88F3D; color:#fff; justify-content:flex-end; }
.obj-label { font-weight:700; font-size:13px; letter-spacing:.04em; text-transform:uppercase; color:var(--muted); margin:2px 0 8px; }
.callout + .obj-label { margin-top:18px; }
.obj-list { columns:2; column-gap:40px; margin:0; padding-left:22px; }
.obj-list li { break-inside:avoid; margin-bottom:8px; }
@media (max-width:900px) { .obj-list { columns:1; } }
.ref-item p { margin:0; font-size:13.5px; line-height:1.55; padding-left:2.4em; text-indent:-2.4em; overflow-wrap:anywhere; }
/* Mosaico (masonry) de tarjetas: sin huecos cuando las alturas son distintas */
.masonry { column-count:2; column-gap:20px; }
.masonry > .card { break-inside:avoid; display:inline-block; width:100%; }
@media (max-width:900px) { .masonry { column-count:1; } }
.grid { display:grid; gap:20px; } .g2 { grid-template-columns:repeat(2,minmax(0,1fr)); }
.g3 { grid-template-columns:repeat(3,minmax(0,1fr)); } .g4 { grid-template-columns:repeat(4,minmax(0,1fr)); }
.span-2 { grid-column:span 2; }
.kpi-row { display:grid; gap:16px; margin-bottom:20px; } .k4 { grid-template-columns:repeat(4,minmax(0,1fr)); }
.k3 { grid-template-columns:repeat(3,minmax(0,1fr)); margin:12px 0; }
.k2 { grid-template-columns:repeat(2,minmax(0,1fr)); margin:10px 0 14px; }
.kpi-money .kpi-value { white-space:nowrap; font-size:clamp(20px, 2vw, 26px); }
.kpi-usd { font-weight:700; color:var(--accent-2); font-size:14px; margin:2px 0 4px; white-space:nowrap; }
.kpi-fx { font-size:12.5px; margin-top:-6px; }
.kpi-compact .kpi-value { font-size:24px; }
.kpi { background:var(--surface); border:1px solid var(--line); border-left:3px solid var(--accent-2); border-radius:10px; padding:14px 16px; }
.kpi-head { display:flex; align-items:center; gap:8px; color:var(--muted); }
.kpi-head .ico { color:var(--accent-2); width:17px; height:17px; }
.kpi-label { font-size:12.5px; font-weight:600; }
.kpi-value { font-size:26px; font-weight:700; margin:6px 0 2px; letter-spacing:-.01em; }
.kpi-note { font-size:12px; color:var(--muted); }

/* ---------- Controles ---------- */
.controls { display:flex; flex-wrap:wrap; gap:18px; margin:6px 0 12px; align-items:flex-end; }
.control { min-width:220px; flex:1; }
.ctl-label { display:block; font-size:12.5px; font-weight:600; color:var(--muted); margin-bottom:5px; }
.radio label, .check label { display:inline-flex; align-items:center; gap:5px; margin-right:16px; cursor:pointer; font-size:14px; }
.radio input, .check input { accent-color:var(--accent); }
.radio label, .check label { color:var(--text) !important; }   /* Dash 4 fija un azul oscuro que no se lee en modo oscuro */

/* ---------- Interpretaciones ---------- */
.interp-wrap { margin-top:12px; }
.interp-btn { display:inline-flex; align-items:center; gap:8px; cursor:pointer; list-style:none; user-select:none;
  padding:7px 14px; border-radius:999px; border:1px solid var(--line-strong); font-weight:600; font-size:13px;
  color:var(--text); background:var(--surface-2); transition:border-color .15s, color .15s; }
.interp-btn::-webkit-details-marker { display:none; }
.interp-btn:hover { border-color:var(--accent-2); color:var(--accent-2); }
.interp-btn .ico { width:15px; height:15px; }
.interp-chev { transition:transform .2s ease; }
.interp-wrap[open] .interp-chev { transform:rotate(90deg); }
.interp-wrap[open] .interp-btn { border-color:var(--accent-2); }
.interp-body { margin-top:10px; display:grid; gap:10px; }
.interp { border-radius:8px; padding:10px 14px; }
.interp b { font-size:13px; }
.interp p { margin:6px 0 2px !important; font-size:14px; }
.interp.basic { background:var(--note-bg); border-left:3px solid var(--note-line); }
.interp.tech { background:var(--tech-bg); border-left:3px solid var(--tech-line); }
/* desplegable tipo tarjeta (Referencias del Marco Teórico) */
details.fold > summary { cursor:pointer; list-style:none; display:flex; align-items:center; gap:10px;
  font-weight:700; font-size:16px; }
details.fold > summary::-webkit-details-marker { display:none; }
details.fold > summary::after { content:'+'; margin-left:auto; font-size:20px; font-weight:400; color:var(--accent-2); }
details.fold[open] > summary::after { content:'−'; }
details.fold > summary .ico { color:var(--accent-2); }
details.fold[open] > summary { margin-bottom:10px; }
/* fórmulas LaTeX (MathJax) */
.formula.dash-markdown, .formula > div { overflow-x:auto; overflow-y:hidden; }
.formula { text-align:center; overflow-y:hidden; }
.formula mjx-container { margin:0 !important; padding:4px 0; font-size:112% !important; max-width:100%; }
.formula mjx-container[display="true"] { overflow:visible; }
.formula p { margin:0; }

/* ---------- Contenido de texto ---------- */
.callout { background:var(--note-bg); border-left:3px solid var(--note-line); border-radius:8px; padding:14px 18px; font-size:15.5px; font-weight:600; }
.formula { background:var(--tech-bg); border-left:3px solid var(--tech-line); border-radius:8px; padding:9px 14px; margin:8px 0;
  font-family:Consolas,'Courier New',monospace; font-size:13.5px; overflow-x:auto; }
.tag { display:inline-block; background:var(--accent); color:var(--on-accent); border-radius:999px; font-size:11.5px;
  font-weight:600; padding:2px 10px; margin-left:8px; white-space:nowrap; }
code { background:var(--code-bg); color:var(--text); padding:2px 6px; border-radius:6px; font-size:13px; }
.table-wrap { overflow-x:auto; }
.tag.verdict { margin-left:0; }
.vtable { border-collapse:collapse; width:100%; font-size:14px; }
.vtable th { background:var(--th-bg); color:#fff; text-align:left; padding:10px 12px; font-weight:600; }
.vtable th:first-child { border-top-left-radius:8px; } .vtable th:last-child { border-top-right-radius:8px; }
.vtable td { padding:9px 12px; border-bottom:1px solid var(--line); vertical-align:top; }
.vtable tr:nth-child(even) td { background:var(--zebra); }
.finding { background:var(--surface); border:1px solid var(--line); border-left:3px solid var(--accent-2); border-radius:10px; padding:14px 16px; }
.find-title { font-weight:700; margin-bottom:4px; } .finding p { margin:4px 0; font-size:14px; }

/* ---------- Portada (texto) ---------- */
.hero-lead { font-size:17px; color:var(--muted); max-width:52ch; margin:0 0 24px; }
.btn { display:inline-flex; align-items:center; gap:9px; padding:10px 16px; border-radius:8px; font-weight:600; font-size:14.5px;
  text-decoration:none; border:1px solid transparent; transition:background .15s, border-color .15s, transform .15s; }
.btn .ico { width:17px; height:17px; }
.btn.primary { background:var(--accent); color:var(--on-accent); }
.btn.primary:hover { filter:brightness(1.12); } .btn.primary:hover .ico { transform:translateX(3px); }
.btn.primary .ico { transition:transform .15s; }
.btn.ghost { border-color:var(--line-strong); color:var(--text); }
.btn.ghost:hover { background:var(--surface-2); border-color:var(--accent-2); }
.link-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:14px; margin-bottom:20px; }
.link-card { display:flex; flex-direction:column; gap:8px; padding:16px; background:var(--surface); border:1px solid var(--line);
  border-radius:10px; text-decoration:none; color:var(--text); transition:border-color .15s, background .15s; }
.link-card:hover { border-color:var(--accent-2); background:var(--surface-2); }
.lc-top { display:flex; justify-content:space-between; align-items:center; }
.lc-ico { display:inline-flex; align-items:center; justify-content:center; width:34px; height:34px; border-radius:8px;
  background:var(--surface-2); border:1px solid var(--line); color:var(--accent-2); }
.lc-ext { width:16px; height:16px; color:var(--muted); transition:color .15s; }
.link-card:hover .lc-ext { color:var(--accent-2); }
.lc-title { font-weight:700; }
.link-card p { margin:0; color:var(--muted); font-size:13.5px; }
.lc-url { color:var(--muted); font-size:12px; word-break:break-all; margin-top:auto; }

/* ---------- Pie ---------- */
.footer { background:var(--surface); color:var(--muted); padding:16px 32px; border-top:1px solid var(--line); font-size:12.5px;
  display:flex; flex-wrap:wrap; gap:8px 24px; justify-content:space-between; align-items:center; margin-top:24px; }
.footer b { color:var(--text); }
.footer-links { display:flex; flex-wrap:wrap; gap:6px 18px; }
.footer-links a { display:inline-flex; align-items:center; gap:6px; color:var(--muted); text-decoration:none; }
.footer-links a:hover { color:var(--accent-2); }
.footer-links .ico { width:15px; height:15px; }

/* ---------- Menús desplegables (Dash) en modo oscuro ---------- */
[data-theme="dark"] .Select-control, [data-theme="dark"] .Select-menu-outer, [data-theme="dark"] .Select-menu,
[data-theme="dark"] .VirtualizedSelectOption, [data-theme="dark"] .dash-dropdown,
[data-theme="dark"] .dash-dropdown-content { background:var(--surface-2) !important; color:var(--text) !important;
  border-color:var(--line-strong) !important; }
[data-theme="dark"] .Select-value-label, [data-theme="dark"] .Select-placeholder,
[data-theme="dark"] .Select--single > .Select-control .Select-value, [data-theme="dark"] .Select-input > input,
[data-theme="dark"] .dash-dropdown * { color:var(--text) !important; }
[data-theme="dark"] .VirtualizedSelectFocusedOption, [data-theme="dark"] .Select-option.is-focused { background:var(--th-bg) !important; }
[data-theme="dark"] .Select-value { background:transparent !important; }
[data-theme="dark"] .Select-arrow { border-top-color:var(--text) !important; }

/* ---------- Adaptación a pantallas pequeñas ---------- */
@media (max-width:1100px) { .g3,.g4,.k4 { grid-template-columns:repeat(2,minmax(0,1fr)); } .span-2 { grid-column:span 2; } }
@media (max-width:900px) {
  .sidebar { position:static; width:100%; } .main { margin-left:0; } .app.collapsed .sidebar { display:none; }
  .g2,.g3,.g4,.k4,.k3 { grid-template-columns:1fr; } .span-2 { grid-column:auto; }
  .topbar { position:static; flex-wrap:wrap; padding:12px 16px; } .content { padding:20px 16px; } .footer { padding:16px; } }
@media (prefers-reduced-motion:reduce) { * { transition:none !important; scroll-behavior:auto !important; } }
"""
for _tok, _val in {"%%DEEP%%": DEEP_NAVY, "%%NAVY%%": NAVY, "%%PALE%%": PALE_GOLD,
                   "%%GOLD%%": WARM_GOLD, "%%CREAM%%": CREAM}.items():
    CSS = CSS.replace(_tok, _val)

# ---------- CSS nuevo: detalles de tarjeta, portada, Anterior/Siguiente, pipeline ----------
NEW_CSS = """
/* ---- detalles sobrios de tarjeta ---- */
.kpi-value { font-variant-numeric:tabular-nums; letter-spacing:.04em; }
.brand-tag { display:flex; align-items:center; gap:7px; }
.badge { display:inline-flex; align-items:center; gap:7px; }
.brand-tag .ico { width:15px; height:15px; color:var(--pale); }
.badge .ico { width:15px; height:15px; color:var(--accent-2); }

/* ---- portada: sin menú, barra superior ni pie ---- */
.app.cover .sidebar, .app.cover .topbar, .app.cover .footer { display:none; }
.app.cover .main { margin-left:0; } .app.cover .content { padding:0; }
.cover-toggle { display:none; }
.app.cover .cover-toggle { display:inline-flex; align-items:center; gap:8px; position:fixed; top:18px; right:22px; z-index:60; }
/* ---- botón de idioma ES | EN ---- */
.lang-switch { display:inline-flex; align-items:center; gap:2px; height:32px; padding:3px; border-radius:999px;
  border:1px solid var(--line-strong); background:var(--surface-2); cursor:pointer; font-family:inherit; }
.lang-switch span { padding:5px 8px; border-radius:999px; font-size:11.5px; font-weight:700; letter-spacing:.04em;
  line-height:1; color:var(--muted); transition:background .2s ease, color .2s ease; }
:root:not([data-lang="en"]) .lang-switch .ls-es, :root[data-lang="en"] .lang-switch .ls-en {
  background:var(--accent); color:var(--on-accent); }
.lang-switch:hover { border-color:var(--accent-2); }
/* textos fijos fuera de Dash (globo de Kyo): se muestra el del idioma activo */
:root[data-lang="en"] .l-es, :root:not([data-lang="en"]) .l-en { display:none; }
.cover { position:relative; min-height:100vh; display:flex; align-items:center; overflow:hidden; }
.bill-bg { position:absolute; inset:0; opacity:.7; pointer-events:none;
  background:repeating-linear-gradient(115deg, var(--line) 0 1px, transparent 1px 13px),
             repeating-linear-gradient(35deg, var(--line) 0 1px, transparent 1px 17px);
  -webkit-mask-image:radial-gradient(ellipse at 30% 50%, #000 20%, transparent 80%);
  mask-image:radial-gradient(ellipse at 30% 50%, #000 20%, transparent 80%); }
.cover-hero { position:relative; width:100%; display:grid; grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);
  gap:56px; align-items:center; padding:56px 7vw; }
.cover-tag { display:inline-flex; align-items:center; gap:8px; color:var(--accent-2); font-weight:700; font-size:14px; margin-bottom:14px; }
.cover-copy h1 { font-size:clamp(32px,4.2vw,50px); line-height:1.1; letter-spacing:-.02em; margin:0 0 16px; }
.btn.big { padding:14px 24px; font-size:16px; }
.cover-hint { display:flex; flex-direction:column; gap:3px; margin-top:22px; font-size:12.5px; color:var(--muted); }

/* ---- tarjeta ---- */
.cc-scene { perspective:1200px; display:flex; justify-content:center; }
.cc-settle, .cc, .cc-inner { transform-style:preserve-3d; }
.cc-settle { width:min(540px,88vw); animation:cc-settle .9s cubic-bezier(.2,.8,.2,1) both; }
.cc { position:relative; aspect-ratio:1.586; border-radius:22px; cursor:pointer; outline:none;
  transition:transform .18s ease-out; transform:rotateX(var(--rx,0deg)) rotateY(var(--ry,0deg)); }
.cc:focus-visible { box-shadow:0 0 0 3px var(--focus); }
.cc-inner { position:absolute; inset:0; transition:transform .8s cubic-bezier(.3,.7,.2,1); }
.cc.flipped .cc-inner { transform:rotateY(180deg); }
.cc-face { position:absolute; inset:0; border-radius:22px; overflow:hidden; color:#F3EFE7; padding:6.5% 7%;
  backface-visibility:hidden; -webkit-backface-visibility:hidden; border:1px solid rgba(210,187,137,.38);
  background:repeating-radial-gradient(circle at 88% 12%, rgba(210,187,137,.08) 0 1px, transparent 1px 8px),
             linear-gradient(135deg, #2A3860 0%, #1A233D 60%, #141B30 100%);
  box-shadow:0 34px 60px -24px rgba(8,12,30,.6), inset 0 1px 0 rgba(255,255,255,.08); }
.cc-front { display:flex; flex-direction:column; justify-content:space-between; }
.cc-back { transform:rotateY(180deg); padding:0; display:flex; flex-direction:column; }
.cc-gloss { position:absolute; inset:0; pointer-events:none; mix-blend-mode:soft-light; opacity:.9;
  background:radial-gradient(circle at var(--mx,28%) var(--my,18%), rgba(255,255,255,.5), transparent 46%); }
.cc-top { display:flex; justify-content:space-between; align-items:center; }
.cc-brand { font-size:clamp(11px,1.5vw,13px); font-weight:700; letter-spacing:.14em; color:#D2BB89; }
.cc-nfc { width:26px; height:26px; color:#D2BB89; }
.cc-chip { position:relative; width:17%; aspect-ratio:1.25; border-radius:9px;
  background:linear-gradient(135deg, #E6D3A3, #B88F3D 60%, #D2BB89); }
.cc-chip::before { content:''; position:absolute; left:0; right:0; top:50%; height:1px; background:rgba(26,35,61,.45);
  box-shadow:0 -9px 0 rgba(26,35,61,.35), 0 9px 0 rgba(26,35,61,.35); }
.cc-chip::after { content:''; position:absolute; top:0; bottom:0; left:50%; width:1px; background:rgba(26,35,61,.45); }
.cc-number { font-family:Consolas,'Courier New',monospace; font-size:clamp(17px,3.3vw,27px); letter-spacing:.14em;
  font-variant-numeric:tabular-nums; text-shadow:0 1px 0 rgba(0,0,0,.45), 0 -1px 0 rgba(255,255,255,.14); }
.cc-bottom { display:flex; justify-content:space-between; align-items:flex-end; gap:12px; }
.cc-lbl { display:block; font-size:10px; letter-spacing:.1em; color:#9AA3BA; margin-bottom:2px; }
.cc-name { font-size:clamp(11px,1.7vw,14px); font-weight:600; letter-spacing:.1em; text-transform:uppercase; }
.cc-valid { text-align:right; }
.cc-mag { height:17%; margin-top:8%; background:#0B1020; }
.cc-sig { margin:7% 7% 0; padding:3.5% 4%; border-radius:6px; display:grid; grid-template-columns:repeat(3,1fr); gap:8px;
  background:repeating-linear-gradient(135deg, #F3EFE7 0 6px, #E9E3D3 6px 12px); color:#1A233D; }
.sig-stat { display:flex; flex-direction:column; }
.sig-stat span { font-size:10px; letter-spacing:.06em; color:#5D667F; }
.sig-stat b { font-size:clamp(12px,2.2vw,17px); font-variant-numeric:tabular-nums; }
.cc-fine { margin:auto 7% 6%; font-size:10.5px; color:#9AA3BA; }
@keyframes cc-settle { from { opacity:0; transform:translateY(-26px) rotate(-3deg) scale(.96); } to { opacity:1; transform:none; } }

/* ---- Anterior / Siguiente ---- */
.pn-row { display:flex; justify-content:space-between; gap:16px; margin:8px 0 18px; }
.pn { display:inline-flex; align-items:center; gap:12px; padding:12px 18px; border:1px solid var(--line-strong); border-radius:10px;
  background:var(--surface); color:var(--text); text-decoration:none; transition:border-color .15s, background .15s; }
.pn:hover { border-color:var(--accent-2); background:var(--surface-2); }
.pn small { display:block; font-size:11.5px; color:var(--muted); } .pn b { font-size:14.5px; }
.pn .ico { color:var(--accent-2); } .pn .flip { transform:scaleX(-1); }
.pn.next { text-align:right; margin-left:auto; }

/* ---- Pipeline completo ---- */
.nb-list { display:grid; gap:10px; }
.nb-row { display:flex; align-items:center; gap:14px; padding:12px 14px; border:1px solid var(--line); border-radius:10px;
  background:var(--surface); color:var(--text); text-decoration:none; transition:border-color .15s, background .15s; }
.nb-row:hover { border-color:var(--accent-2); background:var(--surface-2); }
.nb-num { position:relative; flex:none; width:42px; height:42px; display:inline-flex; align-items:center; justify-content:center;
  border-radius:11px; color:#F1E1B6; background:linear-gradient(145deg, #36456D 0%, #1A233D 100%);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.12), 0 6px 14px -8px rgba(8,12,30,.6); }
.nb-num .ico { width:22px; height:22px; }
.nb-n { position:absolute; right:-6px; bottom:-6px; min-width:20px; height:18px; padding:0 4px; border-radius:99px;
  display:inline-flex; align-items:center; justify-content:center; font-size:10px; font-weight:800; line-height:1;
  background:#D9AE4E; color:#1A233D; border:2px solid var(--surface); font-variant-numeric:tabular-nums; }
.nb-row:hover .nb-num { color:#FFE7A8; }
.nb-body { flex:1; min-width:0; } .nb-t { font-weight:700; } .nb-body p { margin:2px 0 0; color:var(--muted); font-size:13.5px; }
.nb-ext { width:16px; height:16px; color:var(--muted); } .nb-row:hover .nb-ext { color:var(--accent-2); }

@media (max-width:900px) { .cover-hero { grid-template-columns:1fr; gap:32px; padding:72px 6vw 40px; } .cc-scene { order:-1; } }
@media (prefers-reduced-motion:reduce) { .cc-settle { animation:none; } }

/* ---- Equipo: tarjetas de crédito verticales ---- */
.team-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,330px)); justify-content:center;
  gap:clamp(24px,4vw,56px); margin:8px 0 6px; }
.tc-scene { perspective:1200px; animation:cc-settle .8s cubic-bezier(.2,.8,.2,1) both; animation-delay:var(--d,0s); }
.tc-scene:nth-child(2) { animation-delay:.12s; }
.tc, .tc-inner { transform-style:preserve-3d; }
.tc { position:relative; aspect-ratio:0.63; border-radius:22px; cursor:pointer; outline:none;
  transition:transform .18s ease-out; transform:rotateX(var(--rx,0deg)) rotateY(var(--ry,0deg)); }
.tc:focus-visible { box-shadow:0 0 0 3px var(--focus); }
.tc-inner { position:absolute; inset:0; transition:transform .8s cubic-bezier(.3,.7,.2,1); }
.tc.flipped .tc-inner, .tc:has(.tc-link:focus-visible) .tc-inner { transform:rotateY(180deg); }
.tc .cc-face { padding:8% 8.5%; display:flex; flex-direction:column; }
.tc-front { gap:4.5%; }
.tc-front .cc-top, .tc-front .tc-photo, .tc-front .tc-mid { position:relative; }
.tc-photo { flex:1; min-height:0; border-radius:14px; overflow:hidden; border:1px solid rgba(210,187,137,.45);
  box-shadow:inset 0 0 0 1px rgba(0,0,0,.2); background:#141B30; }
.tc-photo img { width:100%; height:100%; object-fit:cover; object-position:50% 22%; display:block;
  filter:saturate(.92) contrast(1.03); }
.tc-mid { display:flex; align-items:center; gap:12px; }
.tc-chip { width:44px; flex:none; border-radius:7px; }
.tc-chip::before { box-shadow:0 -6px 0 rgba(26,35,61,.35), 0 6px 0 rgba(26,35,61,.35); }
.tc-number { font-family:Consolas,'Courier New',monospace; font-size:clamp(13px,1.35vw,15.5px); letter-spacing:.12em;
  white-space:nowrap; text-shadow:0 1px 0 rgba(0,0,0,.45), 0 -1px 0 rgba(255,255,255,.14); }
.tc-name { font-size:15px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; line-height:1.25; }
.tc-role { margin-top:4px; font-size:12.5px; color:#D2BB89; line-height:1.4; }
.tc-hint { display:inline-flex; align-items:center; gap:6px; font-size:11px; color:#9AA3BA; letter-spacing:.04em; }
.tc-hint .ico { width:13px; height:13px; }
.tc-back { transform:rotateY(180deg); padding:0 !important; }
.tc-mag { height:auto; aspect-ratio:5.2; margin-top:12%; flex:none; }
.tc-sig { margin:7% 8.5% 0; padding:9px 12px; border-radius:6px; color:#1A233D;
  background:repeating-linear-gradient(135deg, #F3EFE7 0 6px, #E9E3D3 6px 12px); }
.tc-sig-lbl { display:block; font-size:9.5px; letter-spacing:.08em; color:#5D667F; text-transform:uppercase; }
.tc-sig-name { font-family:'Brush Script MT','Segoe Script',cursive; font-size:24px; line-height:1.15; }
.tc-bio { position:relative; margin:7% 8.5% 0; font-size:13.5px; line-height:1.55; color:#E3DED3; }
.tc-links { position:relative; display:grid; gap:8px; margin:auto 8.5% 0; }
.tc-link { display:flex; align-items:center; gap:10px; padding:9px 12px; border-radius:10px; min-width:0;
  border:1px solid rgba(210,187,137,.32); background:rgba(255,255,255,.04); color:#F3EFE7; text-decoration:none;
  font-size:13px; transition:background .15s, border-color .15s; }
.tc-link span { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.tc-link .ico { color:#D2BB89; }
.tc-link:hover, .tc-link:focus-visible { background:rgba(210,187,137,.14); border-color:#D2BB89; }
button.tc-link { width:100%; font:inherit; font-size:13px; text-align:left; cursor:pointer; }
.tc-copy { position:relative; }
.tc-copy-ok { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; gap:6px;
  border-radius:10px; background:#D2BB89; color:#1A233D; font-weight:700; opacity:0; transform:scale(.96);
  transition:opacity .2s, transform .2s; pointer-events:none; }
.tc-copy.copied .tc-copy-ok { opacity:1; transform:none; }
.tc-fine { position:relative; margin:5% 8.5% 7% !important; }
.team-hint { text-align:center; font-size:13px; margin:18px 0 8px; }
@media (max-width:600px) { .team-grid { grid-template-columns:minmax(0,320px); } }
@media (prefers-reduced-motion:reduce) { .tc-scene { animation:none; } .tc-inner { transition:none; } }

/* ---- Modelos: carrusel deslizable de tarjetas ---- */
@property --mc-ang { syntax:'<angle>'; initial-value:0deg; inherits:false; }
/* Carrusel: tantas tarjetas como quepan (3 / 2 / 1 según el ancho del contenedor), alineadas al inicio,
   sin márgenes vacíos a los lados. */
.mc-stage { position:relative; padding:0 30px; container-type:inline-size; }
.mc-track { --mc-gap:20px; --mc-w:88%; position:relative; display:flex; gap:var(--mc-gap); overflow-x:auto;
  overscroll-behavior-x:contain; scroll-snap-type:x mandatory; scroll-behavior:smooth; scrollbar-width:none;
  padding:26px 10px 30px; scroll-padding-inline:10px; outline:none; border-radius:14px; }
@container (min-width:620px) { .mc-track { --mc-w:calc((100% - var(--mc-gap)) / 2); } }
@container (min-width:1000px) { .mc-track { --mc-w:calc((100% - 2 * var(--mc-gap)) / 3); } }
.mc-track::-webkit-scrollbar { display:none; }
.mc-track:focus-visible { box-shadow:inset 0 0 0 2px var(--focus); }
.mc-slide { position:relative; flex:0 0 var(--mc-w); scroll-snap-align:start; display:flex; flex-direction:column;
  gap:12px; padding:20px 22px 18px; border-radius:20px; overflow:hidden; color:#F3EFE7;
  border:1px solid rgba(210,187,137,.30);
  background:repeating-radial-gradient(circle at 88% 12%, rgba(210,187,137,.07) 0 1px, transparent 1px 8px),
             linear-gradient(150deg, #2A3860 0%, #1A233D 58%, #141B30 100%);
  box-shadow:0 26px 46px -26px rgba(8,12,30,.65), inset 0 1px 0 rgba(255,255,255,.07);
  transition:transform .3s ease, box-shadow .3s ease; }
.mc-slide:hover { transform:translateY(-3px); }
.mc-slide .cc-gloss { opacity:.45; }
.mc-slide > *:not(.cc-gloss) { position:relative; }
/* el mejor: borde con luz dorada que recorre el contorno + halo suave */
.mc-slide.best { border-color:transparent; animation:mc-glow 3.4s ease-in-out infinite; }
.mc-slide.best::after { content:''; position:absolute; inset:0; border-radius:inherit; padding:2px; pointer-events:none;
  background:conic-gradient(from var(--mc-ang), rgba(210,187,137,.35) 0deg, rgba(210,187,137,.35) 200deg,
             #B88F3D 250deg, #F6E7C1 290deg, #D2BB89 315deg, rgba(210,187,137,.35) 350deg);
  -webkit-mask:linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite:xor; mask-composite:exclude; animation:mc-spin 5s linear infinite; }
@keyframes mc-spin { to { --mc-ang:360deg; } }
/* Modelo original: pestañas Teoría / Resultados */
.cs-tabs-wrap { margin:18px 0 4px; }
.cs-tabs { display:flex; gap:6px; padding:4px; border-radius:999px; background:var(--surface-2);
  border:1px solid var(--line); width:fit-content; max-width:100%; }
.cs-tabs .cs-tab { width:auto !important; flex:none !important; border:0 !important; background:transparent !important; color:var(--muted) !important;
  padding:8px 18px !important; border-radius:999px; font-weight:600; cursor:pointer; white-space:nowrap; }
.cs-tabs .cs-tab--on { background:var(--accent) !important; color:var(--on-accent) !important; }
.cs-pane { padding-top:14px; display:flex; flex-direction:column; gap:18px; }
.cs-pane > .card { margin:0; }
.cs-pane > .grid > .card { margin:0; }
.cs-tabs { flex-wrap:wrap; border-radius:22px !important; }
.cs-flow { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; counter-reset:paso; }
.cs-flow-item { position:relative; padding:12px 14px; border-radius:12px; background:var(--surface-2); border:1px solid var(--line); }
.cs-flow-item b { display:block; margin:6px 0 2px; } .cs-flow-item p { margin:0; font-size:12.8px; color:var(--muted); }
.cs-flow-item:nth-child(3) { border-color:var(--accent-2); box-shadow:0 0 0 1px var(--accent-2) inset; }
.cs-eq { display:flex; gap:12px; align-items:flex-start; margin:6px 0 12px; }
.cs-eq-n { flex:none; width:34px; padding-top:16px; font-weight:700; color:var(--accent-2); text-align:right; }
.cs-eq-body { flex:1; min-width:0; } .cs-eq-why { margin:2px 0 0; font-size:13.5px; color:var(--muted); }
.cs-pseudo { font-size:12.8px; line-height:1.7; white-space:pre; }
.cs-props li { margin:0 0 8px; font-size:14px; }
.cs-checklist { list-style:none; padding:0; margin:0 0 8px; display:grid; gap:8px; }
.cs-checklist li { display:flex; gap:10px; align-items:flex-start; font-size:14px; }
.cs-chk { flex:none; display:inline-grid; place-items:center; width:22px; height:22px; border-radius:50%; font-size:15px; line-height:1; font-weight:800; }
.cs-chk.ok { background:var(--accent-2); color:#1A233D; } .cs-chk.mid { border:2px solid var(--accent-2); color:var(--accent-2); }
.cs-links { display:flex; flex-wrap:wrap; gap:10px; margin-top:4px; }
.cs-link { display:inline-flex; align-items:center; gap:8px; padding:8px 14px; border-radius:999px; border:1px solid var(--line-strong);
  color:var(--text); text-decoration:none; font-weight:600; font-size:13.5px; }
.cs-link:hover { border-color:var(--accent-2); color:var(--accent-2); }
.cs-code { max-height:520px; overflow:auto; font-size:12.6px; line-height:1.55; }
.cs-code-sub { margin:16px 0 6px; font-size:14px; } .cs-code-sub .muted { font-weight:500; }
.cs-code-eqs { border:1px solid var(--line); border-radius:10px; overflow:hidden; }
.cs-code-rows { background:var(--tech-bg); }
.cs-code-rows .pf-code { margin:0; border-radius:0; border-left:none; padding:2px 16px; max-height:none;
  overflow-x:auto; background:transparent; font-size:13px; line-height:1.6; }
.cs-code-rows.hl { background:var(--note-bg); box-shadow:inset 3px 0 0 var(--accent-2); }
.cs-eqc { margin:0; padding:6px 12px 8px 4px; background:var(--surface); border-top:1px solid var(--line); border-bottom:1px solid var(--line); }
.cs-sum { cursor:pointer; font-weight:600; margin:4px 0 8px; }
.hl-kw { color:#8A3FA0; font-weight:600; } .hl-def { color:#1F5FA8; font-weight:700; } .hl-str { color:#2E7D4F; }
.hl-com { color:#7A8094; font-style:italic; } .hl-num { color:#B5591E; } .hl-bi { color:#9A7A33; }
[data-theme="dark"] .hl-kw { color:#D49BE8; } [data-theme="dark"] .hl-def { color:#8EC1FF; } [data-theme="dark"] .hl-str { color:#9AD7A8; }
[data-theme="dark"] .hl-com { color:#9AA3BA; } [data-theme="dark"] .hl-num { color:#F2B37A; } [data-theme="dark"] .hl-bi { color:#D2BB89; }
@media (max-width:1100px) { .cs-flow { grid-template-columns:repeat(2,minmax(0,1fr)); } }
.beyond-sub { margin:18px 0 10px; font-size:15px; color:var(--accent-2); }
.beyond-model { border:1px solid var(--line-strong); border-radius:10px; padding:14px 16px; background:var(--surface-2); }
.beyond-head { display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:6px; }
.beyond-head .tag { margin-left:0; white-space:nowrap; }
.beyond-model .muted { margin:0 0 6px; }
.beyond-list { margin:4px 0 14px; padding-left:20px; line-height:1.6; } .beyond-list li { margin-bottom:6px; }
@media (max-width:600px) { .cs-flow { grid-template-columns:1fr; } .cs-eq-n { width:26px; } }
.cs-h { margin:22px 0 6px; font-size:15px; color:var(--text); }
.cs-fig-t { font-weight:600; font-size:13px; color:var(--muted); margin:6px 0 2px; }
.cs-fig-t.on { color:var(--accent-2); }
.cs-steps { display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:14px; }
.cs-step { position:relative; background:var(--surface-2); border:1px solid var(--line); border-radius:14px;
  padding:16px 16px 10px 16px; }
.cs-step h4 { margin:6px 0 4px; font-size:14px; }
.cs-step p { margin:0 0 6px; font-size:13.5px; color:var(--muted); }
.cs-num { display:inline-grid; place-items:center; width:26px; height:26px; border-radius:50%;
  background:var(--accent-2); color:var(--on-accent); font-weight:700; font-size:13px; }
[data-theme="dark"] .cs-num { color:#1A233D; }
@media (max-width:600px) { .cs-tabs .cs-tab { padding:7px 12px !important; } }
@keyframes mc-glow {
  0%,100% { box-shadow:0 0 0 1px rgba(210,187,137,.45), 0 0 22px 0 rgba(210,187,137,.35), 0 26px 46px -26px rgba(8,12,30,.65); }
  50%     { box-shadow:0 0 0 1px rgba(210,187,137,.75), 0 0 38px 4px rgba(210,187,137,.55), 0 26px 46px -26px rgba(8,12,30,.65); } }
.mc-top { display:flex; justify-content:space-between; align-items:center; gap:10px; }
.mc-rank { font-family:Consolas,'Courier New',monospace; font-weight:700; font-size:14px; letter-spacing:.12em; color:#D2BB89; }
.mc-fam-top { font-size:10.5px; letter-spacing:.12em; text-transform:uppercase; color:#9AA3BA; text-align:right; }
.mc-badge { display:inline-flex; align-items:center; gap:6px; padding:4px 11px; border-radius:999px; font-size:11.5px;
  font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:#1A233D;
  background:linear-gradient(135deg, #F1E1B6, #D2BB89 55%, #B88F3D); box-shadow:0 0 14px rgba(210,187,137,.55); }
.mc-badge .ico { width:14px; height:14px; }
.mc-name { margin:2px 0 0; font-size:23px; font-weight:800; letter-spacing:-.01em; color:#fff; }
.mc-family { margin-top:-8px; font-size:12.5px; color:#D2BB89; }
.mc-score { display:flex; align-items:center; gap:14px; padding:10px 0 2px; }
.mc-chip { width:46px; flex:none; border-radius:8px; }
.mc-chip::before { box-shadow:0 -7px 0 rgba(26,35,61,.35), 0 7px 0 rgba(26,35,61,.35); }
.mc-f1 { font-family:Consolas,'Courier New',monospace; font-size:36px; font-weight:700; letter-spacing:.06em;
  font-variant-numeric:tabular-nums; text-shadow:0 1px 0 rgba(0,0,0,.45), 0 -1px 0 rgba(255,255,255,.14); }
.mc-slide.best .mc-f1 { color:#F1E1B6; }
.mc-std { margin-left:8px; white-space:nowrap; font-size:12.5px; color:#9AA3BA; font-variant-numeric:tabular-nums; }
.mc-config { display:flex; flex-wrap:wrap; gap:6px; }
.mc-pill { font-size:12px; font-weight:600; padding:3px 10px; border-radius:999px; color:#F3EFE7;
  border:1px solid rgba(210,187,137,.38); background:rgba(255,255,255,.05); }
.mc-metrics { display:grid; gap:7px; padding-top:10px; border-top:1px solid rgba(255,255,255,.08); }
.mc-metric { display:grid; grid-template-columns:92px 1fr 44px; align-items:center; gap:10px; font-size:12.5px; color:#D3D8E5; }
.mc-tech .mc-metric { grid-template-columns:104px 1fr 44px; }
.mc-metric b { text-align:right; font-variant-numeric:tabular-nums; color:#F3EFE7; font-weight:600; }
.mc-bar { height:7px; border-radius:99px; background:rgba(255,255,255,.08); overflow:hidden; }
.mc-bar > span { display:block; height:100%; border-radius:inherit; background:linear-gradient(90deg, #66749C, #AEB8D6); }
.mc-bar.na { background:repeating-linear-gradient(135deg, rgba(255,255,255,.08) 0 4px, transparent 4px 8px); }
.mc-tech .mc-bar > span { background:linear-gradient(90deg, #4A5679, #8089A0); }
.mc-tech .mc-metric.on { color:#F1E1B6; font-weight:600; }
.mc-tech .mc-metric.on .mc-bar > span { background:linear-gradient(90deg, #B88F3D, #F1E1B6); }
.mc-desc { margin:2px 0 0 !important; font-size:13px; line-height:1.5; color:#E3DED3; }
.mc-note { margin:0 !important; font-size:12.5px; line-height:1.5; color:#B9C1D6; padding-left:10px;
  border-left:2px solid rgba(210,187,137,.55); }
.mc-foot { margin-top:auto; padding-top:8px; font-size:11px; letter-spacing:.06em; color:#9AA3BA;
  font-variant-numeric:tabular-nums; }
.mc-nav { position:absolute; top:50%; z-index:2; width:38px; height:38px; margin-top:-19px; display:inline-flex;
  align-items:center; justify-content:center; padding:0; border-radius:50%; cursor:pointer; color:var(--text);
  background:var(--surface); border:1px solid var(--line-strong); box-shadow:0 6px 18px -8px rgba(8,12,30,.45);
  transition:background .15s, border-color .15s, color .15s, opacity .15s; }
.mc-nav:hover { border-color:var(--accent-2); color:var(--accent-2); }
.mc-nav .ico { width:20px; height:20px; }
.mc-prev { left:-6px; } .mc-prev .ico { transform:scaleX(-1); } .mc-next { right:-6px; }
.mc-nav[disabled] { opacity:.35; cursor:default; }
.mc-dots { display:flex; justify-content:center; gap:8px; margin-top:2px; }
.mc-dot { width:9px; height:9px; padding:0; border-radius:99px; cursor:pointer; border:0; background:var(--line-strong);
  transition:width .25s ease, background .25s ease; }
.mc-dot.on { width:26px; background:var(--accent-2); }
.mc-dot:first-child { box-shadow:0 0 0 2px rgba(210,187,137,.45); }
.mc-hint { text-align:center; font-size:12.5px; margin:10px 0 0; }
@media (max-width:600px) { .mc-stage { padding:0; } .mc-nav { display:none; } .mc-track { --mc-gap:14px; }
  .mc-slide { padding:18px 16px 16px; } .mc-f1 { font-size:30px; } .mc-chip { width:38px; }
  .mc-metric, .mc-tech .mc-metric { grid-template-columns:84px 1fr 40px; gap:8px; } }
@media (prefers-reduced-motion:reduce) {
  .mc-slide.best, .mc-slide.best::after { animation:none; }
  .mc-slide.best { box-shadow:0 0 0 1px rgba(210,187,137,.7), 0 0 30px 2px rgba(210,187,137,.45); }
  .mc-track { scroll-behavior:auto; } }

/* ---- Predecir: flujo, formulario visual y resultado ---- */
.pf-flow { display:flex; align-items:stretch; gap:10px; margin:0 0 20px; }
.pf-flow-item { flex:1; display:flex; gap:12px; align-items:flex-start; padding:14px 16px; border-radius:12px;
  background:var(--surface); border:1px solid var(--line); animation:pf-in .5s ease both; }
.pf-flow-item:nth-child(3) { animation-delay:.08s; } .pf-flow-item:nth-child(5) { animation-delay:.16s; }
.pf-flow-item:nth-child(7) { animation-delay:.24s; }
.pf-flow-item b { display:block; font-size:14px; } .pf-flow-item p { margin:2px 0 0; font-size:12.5px; color:var(--muted); }
.pf-flow-ico { flex:none; width:38px; height:38px; border-radius:10px; display:inline-flex; align-items:center;
  justify-content:center; background:var(--accent); color:var(--on-accent); }
.pf-flow-ico .ico { width:20px; height:20px; }
.pf-flow-arrow { align-self:center; color:var(--accent-2); } .pf-flow-arrow .ico { width:18px; height:18px; }
@keyframes pf-in { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:none; } }
.pf-layout { display:grid; grid-template-columns:minmax(0,1.55fr) minmax(310px,1fr); gap:20px; align-items:start; }
.pf-side { position:sticky; top:84px; }
.pf-profiles { display:flex; flex-wrap:wrap; align-items:center; gap:8px; margin:4px 0 6px; }
.pf-prof { padding:6px 12px; font-size:13px; cursor:pointer; background:transparent; font-family:inherit; }
.pf-prof .ico { width:15px; height:15px; color:var(--accent-2); }
.pf-h { margin:20px 0 12px; font-size:13px; font-weight:700; letter-spacing:.06em; text-transform:uppercase;
  color:var(--accent-2); display:flex; align-items:center; gap:8px; }
.pf-h .ico { width:16px; height:16px; }
.pf-h::after { content:''; flex:1; height:1px; background:var(--line); }
.pf-grid { display:grid; gap:14px 22px; margin-bottom:12px; }
.pf-g2 { grid-template-columns:repeat(2,minmax(0,1fr)); }
.pf-field { min-width:0; } .pf-field .ctl-label { margin-bottom:8px; }
.pf-hint { font-size:12.5px; color:var(--muted); } .pf-note { margin:6px 0 12px; } .pf-row { margin-bottom:14px; }
.pf-slider { padding-top:34px; }
.pf-thr-info { margin-top:10px; }
/* ---------- Modo foco: una tarjeta ampliada al centro (assets/card_focus.js) ---------- */
.card, .kpi { position:relative; }
.card-zoom { position:absolute; top:10px; right:10px; z-index:2; width:30px; height:30px; padding:0; display:inline-flex;
  align-items:center; justify-content:center; background:var(--surface); color:var(--muted); cursor:pointer;
  border:1px solid var(--line-strong); border-radius:8px; opacity:.75; transition:opacity .15s, color .15s, border-color .15s; }
.card-zoom .ico { width:16px; height:16px; }
.card-zoom .zb-close { display:none; }
.card:hover > .card-zoom, .kpi:hover > .card-zoom, .card-zoom:focus-visible { opacity:1; }
.card-zoom:hover { color:var(--accent-2); border-color:var(--accent-2); opacity:1; }
.card > .card-title { padding-right:38px; }
.kpi > .card-zoom { top:6px; right:6px; width:24px; height:24px; border-radius:6px; }
.kpi > .card-zoom .ico { width:13px; height:13px; }
.kpi > .kpi-head { padding-right:26px; }
.ef-card > .card-zoom { top:16px; right:14px; }
.ef-summary { padding-right:58px; }

.focus-overlay { position:fixed; inset:0; z-index:10005; background:rgba(8,12,24,.72); opacity:0; visibility:hidden;
  transition:opacity .18s ease, visibility 0s linear .18s; }
.focus-overlay.on { opacity:1; visibility:visible; transition:opacity .18s ease, visibility 0s; }
html.focus-open, html.focus-open body { overflow:hidden; }
.card-zoomed { --fz:1.3; position:fixed !important; z-index:10010; zoom:var(--fz); margin:0 !important;
  top:calc(5vh / var(--fz)) !important; left:calc(5vw / var(--fz)) !important;
  width:calc(90vw / var(--fz)) !important; height:calc(90vh / var(--fz)) !important; max-width:none !important; overflow-y:auto; overflow-x:hidden; overscroll-behavior:contain; padding-top:20px;
  box-shadow:0 24px 80px rgba(0,0,0,.55); border-color:var(--line-strong); outline:none; }
.card-zoomed.ef-card { padding-top:0; }
.kpi.card-zoomed { --fz:2.6; display:flex; flex-direction:column; justify-content:center; padding:24px 40px;
  border-left-width:6px; border-left-color:var(--accent-2); }
.card-zoomed > .card-zoom { position:fixed; top:calc((5vh + 12px) / var(--fz)); right:calc((5vw + 12px) / var(--fz));
  width:calc(52px / var(--fz)); height:calc(52px / var(--fz)); z-index:3; opacity:1; color:var(--text);
  background:var(--surface-2); border-color:var(--accent-2); }
.card-zoomed > .card-zoom .ico { width:calc(28px / var(--fz)); height:calc(28px / var(--fz)); }
.card-zoomed > .card-zoom .zb-open { display:none; } .card-zoomed > .card-zoom .zb-close { display:inline-block; }
.card-zoomed > .card-title { padding-right:56px; }
/* los menús desplegables de Dash viven fuera de la tarjeta: deben quedar por encima de la capa */
.dash-dropdown-content, [data-radix-popper-content-wrapper], .dash-tooltip { z-index:10030 !important; }
/* el menú se posiciona en píxeles de pantalla; dentro de la tarjeta con zoom hay que deshacer el zoom */
.card-zoomed [data-radix-popper-content-wrapper] { zoom:calc(1 / var(--fz)); }
@media (prefers-reduced-motion:reduce) { .focus-overlay, .focus-overlay.on { transition:none; } }
.ef-card { padding:0; }
.ef-summary { display:flex; align-items:center; gap:12px; padding:14px 22px; cursor:pointer; list-style:none; }
.ef-summary::-webkit-details-marker { display:none; }
.ef-summary .ef-ico { width:20px; height:20px; color:var(--accent-2); }
.ef-summary .card-title { margin:0; flex:none; }
.ef-summary .ef-info { flex:1; min-width:0; font-weight:600; color:var(--text); font-size:14px; }
.ef-toggle { flex:none; display:inline-flex; align-items:center; justify-content:center; width:32px; height:32px;
  border:1px solid var(--line-strong); border-radius:8px; color:var(--text); }
.ef-summary:hover .ef-toggle { border-color:var(--accent-2); color:var(--accent-2); }
.ef-toggle .ico { transition:transform .2s; transform:rotate(90deg); }
.ef-fold[open] .ef-toggle .ico { transform:rotate(-90deg); }
.ef-body { padding:0 22px 16px; border-top:1px solid var(--line); }
/* íconos de los filtros globales */
.ctl-label-ico { display:flex; align-items:center; gap:6px; }
.ctl-label-ico .ico { width:15px; height:15px; color:var(--accent-2); }
.opt-ico { display:inline-flex; align-items:center; gap:5px; }
.opt-ico .ico { width:15px; height:15px; color:var(--muted); }
/* umbral plegable en Predecir */
.thr-summary { cursor:pointer; list-style:none; }
.thr-summary::-webkit-details-marker { display:none; }
.thr-summary .thr-sum { font-size:14px; color:var(--accent-2); letter-spacing:0; text-transform:none; }
.thr-summary .ef-toggle { order:3; width:28px; height:28px; }
.thr-summary::after { order:2; }
.thr-summary:hover .ef-toggle { border-color:var(--accent-2); color:var(--accent-2); }
.thr-fold .thr-chev { transition:transform .2s; transform:rotate(90deg); }
.thr-fold[open] .thr-chev { transform:rotate(-90deg); }
.ef-bar { display:flex; align-items:center; justify-content:space-between; gap:12px; margin:10px 0 4px; flex-wrap:wrap; }
.pf-thr-kpis { display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:10px; margin-bottom:8px; }
.pf-thr-k { border:1px solid var(--line); border-radius:12px; padding:8px 12px; display:flex; flex-direction:column; }
.pf-thr-k b { font-size:22px; color:var(--accent-2, #B88F3D); line-height:1.2; }
.pf-thr-k small { color:var(--muted); font-size:12px; }
.pf-form { --Dash-Fill-Interactive-Strong:var(--accent-2); --Dash-Fill-Inverse-Strong:var(--surface);
  --Dash-Text-Strong:var(--text); --Dash-Fill-Disabled:var(--line-strong); --Dash-Text-Primary:var(--muted); }
.pf-form .dash-slider-tooltip { color:var(--text); font-weight:700; font-variant-numeric:tabular-nums;
  white-space:nowrap; padding:6px 9px; }
.pf-form .dash-slider-mark { color:var(--muted); font-size:11.5px; }
.pf-form .dash-slider-thumb { width:18px; height:18px; }
/* tarjetas con ícono */
.pf-tiles { display:flex !important; flex-direction:row; flex-wrap:wrap; gap:8px; }
.pf-tiles .dash-options-list-option { flex:1 1 0; min-width:84px; position:relative; display:flex; padding:0;
  margin:0; background:transparent; align-items:stretch; }
.pf-tiles .dash-options-list-option-wrapper { position:absolute; width:1px; height:1px; overflow:hidden; opacity:0; }
.pf-tile { flex:1; display:flex; }
.pf-tile > span { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:6px;
  padding:12px 8px 10px; border-radius:12px; border:1.5px solid var(--line-strong); background:var(--surface);
  color:var(--muted); font-size:13px; font-weight:600; text-align:center;
  transition:border-color .15s, background .15s, color .15s, transform .15s, box-shadow .15s; }
.dash-options-list-option:hover .pf-tile > span { border-color:var(--accent-2); color:var(--text); transform:translateY(-2px); }
.pf-tile-ico { width:28px; height:28px; }
.dash-options-list-option.selected .pf-tile > span { border-color:var(--accent-2); color:var(--text);
  background:linear-gradient(180deg, rgba(210,187,137,.20), rgba(210,187,137,.06));
  box-shadow:0 0 0 3px rgba(210,187,137,.25), 0 8px 18px -12px rgba(184,143,61,.8); }
.dash-options-list-option.selected .pf-tile-ico { color:var(--accent-2); }
.dash-options-list-option:has(input:focus-visible) .pf-tile > span { outline:2px solid var(--focus); outline-offset:2px; }
.pf-seg { margin-bottom:6px; } .pf-seg .pf-tile > span { padding:9px 10px; flex-direction:row; }
/* estado de pago */
.pf-keys { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:8px; }
.pf-key { font-size:11.5px; font-weight:600; padding:3px 9px; border-radius:999px; border:1px solid var(--line-strong); }
.pf-key.k-ok { background:var(--tech-bg); } .pf-key.k-mid { background:var(--surface-2); }
.pf-key.k-late { background:rgba(184,143,61,.16); border-color:rgba(184,143,61,.5); }
.pf-pay { display:grid; gap:2px; }
.pf-pay-row { display:grid; grid-template-columns:44px 1fr; align-items:center; gap:10px; }
.pf-pay-m { font-size:13px; font-weight:700; color:var(--muted); }
.pf-pay-slider { padding:6px 0 0; }
/* montos */
.pf-input { width:100%; height:36px; padding:6px 8px; border-radius:6px; border:1px solid var(--line-strong);
  background:var(--surface); color:var(--text); font:inherit; font-size:13px; font-variant-numeric:tabular-nums; }
.pf-input:focus { outline:none; border-color:var(--accent-2); box-shadow:0 0 0 3px rgba(184,143,61,.18); }
.pf-amounts { display:grid; grid-template-columns:78px repeat(6,minmax(0,1fr)); gap:8px; align-items:center; }
.pf-mh { font-size:12.5px; font-weight:600; color:var(--muted); text-align:center; }
.pf-rh { font-size:12.5px; font-weight:600; color:var(--muted); }
/* resultado */
.pf-result { border-top:3px solid var(--accent-2); }
/* ---- tarjeta de riesgo: se agrieta con el puntaje y se parte con riesgo muy alto ---- */
.rc { position:relative; width:100%; max-width:440px; margin:4px auto 16px; aspect-ratio:1.6; --heat:0; }
.rc-piece { position:absolute; inset:0; transition:transform .6s cubic-bezier(.3,.7,.2,1);
  filter:drop-shadow(0 18px 22px rgba(8,12,30,.35)); }
.rc .rc-face { display:flex; flex-direction:column; justify-content:space-between; padding:6% 7%;
  box-shadow:none; transition:background .5s ease, border-color .5s ease;
  background:repeating-radial-gradient(circle at 88% 12%, rgba(210,187,137,.08) 0 1px, transparent 1px 8px),
    linear-gradient(135deg,
      color-mix(in srgb, #2A3860, #7A2E1F calc(var(--heat) * 70%)) 0%,
      color-mix(in srgb, #1A233D, #4A1A14 calc(var(--heat) * 70%)) 60%,
      color-mix(in srgb, #141B30, #2B0F0C calc(var(--heat) * 70%)) 100%); }
.rc.hi .rc-face { border-color:rgba(232,120,90,.55); }
/* mientras predict_proba recalcula: la tarjeta "late" con un halo dorado y un brillo que la recorre */
#pf-verdict.pf-busy .rc, #pf-verdict[data-dash-is-loading="true"] .rc { animation:rc-pulse 1.1s ease-in-out infinite; }
#pf-verdict.pf-busy .rc-piece, #pf-verdict[data-dash-is-loading="true"] .rc-piece { filter:drop-shadow(0 18px 22px rgba(8,12,30,.35))
  drop-shadow(0 0 14px rgba(242,193,78,.55)); }
#pf-verdict.pf-busy .rc.hi .rc-piece, #pf-verdict[data-dash-is-loading="true"] .rc.hi .rc-piece {
  filter:drop-shadow(0 18px 22px rgba(8,12,30,.35)) drop-shadow(0 0 14px rgba(235,64,52,.55)); }   /* riesgo alto: halo rojo */
#pf-verdict.pf-busy .rc::after, #pf-verdict[data-dash-is-loading="true"] .rc::after { content:''; position:absolute; inset:0; border-radius:22px;
  pointer-events:none; z-index:3; background:linear-gradient(110deg, transparent 30%, rgba(255,240,200,.28) 50%, transparent 70%);
  background-size:220% 100%; animation:rc-shine 1.1s linear infinite; }
#pf-verdict[data-dash-is-loading="true"] .rc-score { opacity:.55; transition:opacity .2s; }
@keyframes rc-pulse { 0%,100% { transform:scale(1) translateY(0); } 50% { transform:scale(1.025) translateY(-3px); } }
@keyframes rc-shine { from { background-position:120% 0; } to { background-position:-120% 0; } }
@media (prefers-reduced-motion:reduce) {
  #pf-verdict[data-dash-is-loading="true"] .rc, #pf-verdict.pf-busy .rc::after, #pf-verdict[data-dash-is-loading="true"] .rc::after { animation:none; } }
.rc-mid { display:flex; align-items:center; gap:7%; }
.rc-chip { width:19%; }
.rc-score { font-family:Consolas,'Courier New',monospace; font-size:clamp(30px,4.6vw,44px); font-weight:700;
  letter-spacing:.06em; line-height:1; font-variant-numeric:tabular-nums;
  text-shadow:0 1px 0 rgba(0,0,0,.45), 0 -1px 0 rgba(255,255,255,.14); }
.rc.hi .rc-score { color:#F2C27A; }
.rc-verdict { font-size:clamp(11.5px,1.5vw,13.5px); font-weight:700; letter-spacing:.02em; }
.rc-cracks { position:absolute; inset:0; z-index:0; pointer-events:none; background:center/100% 100% no-repeat; }
.rc-face > :not(.rc-cracks):not(.cc-gloss) { position:relative; z-index:1; }   /* el texto queda sobre las grietas */
.rc.split .rc-piece:first-child { animation:rc-crack .45s ease-out; }
/* brillo de 2 s al cambiar el puntaje: dorado si es riesgo bajo, rojo si es riesgo alto */
.rc-wrap.glow-good { animation:rc-glow-good 2s ease-in-out; }
.rc-wrap.glow-bad { animation:rc-glow-bad 2s ease-in-out; }
@keyframes rc-glow-good {
  0%, 100% { filter:drop-shadow(0 0 0 rgba(246,196,69,0)); }
  15%, 55% { filter:drop-shadow(0 0 10px rgba(255,214,102,1)) drop-shadow(0 0 26px rgba(246,196,69,.95)) drop-shadow(0 0 48px rgba(246,196,69,.6)); } }
@keyframes rc-glow-bad {
  0%, 100% { filter:drop-shadow(0 0 0 rgba(235,64,52,0)); }
  15%, 55% { filter:drop-shadow(0 0 10px rgba(255,90,80,1)) drop-shadow(0 0 26px rgba(235,64,52,.95)) drop-shadow(0 0 48px rgba(235,64,52,.6)); } }
@media (prefers-reduced-motion:reduce) { .rc-wrap.glow-good, .rc-wrap.glow-bad { animation-duration:.01s; } }
@keyframes rc-crack { 0% { translate:0 0; } 25% { translate:-3px 1px; } 50% { translate:3px -1px; } 75% { translate:-1px 0; } 100% { translate:0 0; } }
@media (prefers-reduced-motion:reduce) { .rc-piece { transition:none; } .rc.split .rc-piece:first-child { animation:none; } }
.pf-badge { display:flex; align-items:center; gap:12px; padding:12px 14px; border-radius:10px; margin:0 0 10px;
  animation:pf-in .35s ease both; }
.pf-badge .ico { width:26px; height:26px; flex:none; }
.pf-badge b { display:block; font-size:15px; } .pf-badge span { font-size:12.5px; color:var(--muted); }
.pf-badge.hi { background:rgba(184,143,61,.14); border:1px solid rgba(184,143,61,.55); }
.pf-badge.hi .ico { color:var(--accent-2); }
.pf-badge.lo { background:var(--tech-bg); border:1px solid var(--line-strong); }
.pf-badge.lo .ico { color:var(--tech-line); }
.pf-signals { list-style:none; margin:0 0 8px; padding:0; display:grid; gap:7px; }
.card .pf-signals li { display:flex; gap:9px; align-items:flex-start; margin:0; font-size:13.5px; }
.pf-signals .ico { width:17px; height:17px; margin-top:2px; color:var(--accent-2); }
.pf-details { margin:8px 0; font-size:13.5px; } .pf-details summary { cursor:pointer; font-weight:700; color:var(--accent); }
.pf-details p { color:var(--muted); }
.pf-trees { margin-top:12px; padding-top:12px; border-top:1px solid var(--line); }
.pf-trees-h { display:flex; align-items:center; gap:8px; margin-bottom:8px; font-size:14px; }
.pf-trees-h .ico { width:20px; height:20px; color:var(--accent-2); }
.pf-waffle { display:grid; grid-template-columns:repeat(20,1fr); gap:3px; max-width:340px; }
.pf-cell { aspect-ratio:1; border-radius:3px; background:var(--line-strong); transition:background .4s ease; }
.pf-cell.on { background:var(--accent-2); }
/* serialización */
.pf-steps { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:12px; margin:12px 0; }
.pf-step { position:relative; padding:14px 14px 12px; border-radius:12px; background:var(--surface-2); border:1px solid var(--line); }
.pf-step-n { position:absolute; top:10px; right:12px; font-size:22px; font-weight:800; color:var(--line-strong); }
.pf-step-ico { width:24px; height:24px; color:var(--accent-2); }
.pf-step b { display:block; margin-top:6px; } .card .pf-step p { margin:4px 0 0; font-size:12.5px; color:var(--muted); }
.pf-code { text-align:left; white-space:pre; tab-size:4; line-height:1.6; margin:10px 0; padding:14px 18px;
  background:var(--tech-bg); border-left:3px solid var(--tech-line); border-radius:8px; overflow-x:auto;
  font-family:Consolas,'Courier New',monospace; font-size:13px; }
.pf-code code { background:none; padding:0; font-size:inherit; white-space:pre; display:block; }
@media (max-width:1250px) { .pf-layout { grid-template-columns:1fr; } .pf-side { position:static; }
  .pf-flow { flex-wrap:wrap; } .pf-flow-item { flex:1 1 40%; } .pf-flow-arrow { display:none; } }
@media (max-width:700px) { .pf-g2, .pf-steps { grid-template-columns:1fr; } .pf-flow-item { flex-basis:100%; }
  .pf-amounts { min-width:600px; }
  .pf-tiles .dash-options-list-option { min-width:64px; } .pf-tile > span { font-size:12px; padding:10px 4px 8px; } }
@media (prefers-reduced-motion:reduce) { .pf-flow-item, .pf-badge { animation:none; } }
"""

# ---------- JS de la portada: inclinación con el mouse, brillo y volteo ----------
COVER_JS = """
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
  // Predecir: brillo de 2 s cuando la tarjeta cambia de puntaje (dorado = riesgo bajo, rojo = riesgo alto)
  var rcLast = null;
  function rcGlow() {
    var w = document.querySelector('#pf-verdict .rc-wrap:not([data-seen])'); if (!w) return;
    w.setAttribute('data-seen', '1');
    var s = w.querySelector('.rc-score'), rc = w.querySelector('.rc');
    var score = s ? s.textContent.trim() : null;
    if (rcLast !== null && score !== null && score !== rcLast) {
      w.classList.add(rc && rc.classList.contains('hi') ? 'glow-bad' : 'glow-good');
      setTimeout(function () { w.classList.remove('glow-good', 'glow-bad'); }, 2100);
    }
    rcLast = score;
  }
  new MutationObserver(rcGlow).observe(document.documentElement, { childList: true, subtree: true });
  // Dash dibuja la página después de cargar: sincroniza cuando aparece un carrusel nuevo
  function scan() {
    document.querySelectorAll('.mc-track:not([data-ready])').forEach(function (t) {
      t.setAttribute('data-ready', '1'); t.scrollLeft = 0; sync(t); });
  }
  new MutationObserver(scan).observe(document.documentElement, { childList: true, subtree: true });
  window.addEventListener('resize', function () {
    document.querySelectorAll('.mc-track').forEach(function (t) { sync(t); }); });
})();
"""
CSS += NEW_CSS

# ---------- CSS: símbolos de las ecuaciones (burbuja + iluminación) y ventana del pipeline ----------
EQ_PIPE_CSS = """
:root { --eqv-hl:#9A6700; --eqv-bg:rgba(212,170,70,.34); --eqv-glow:rgba(212,170,70,.85); }
[data-theme="dark"] { --eqv-hl:#F6DC96; --eqv-bg:rgba(246,220,150,.26); --eqv-glow:rgba(246,220,150,.8); }
.eqw { max-width:100%; }
/* símbolos en textos y código */
.eqv { cursor:help; border-radius:3px; transition:background .12s, box-shadow .12s; }
span.eqv { border-bottom:1px dotted var(--accent-2); }
span.eqv-on { background:var(--eqv-bg); box-shadow:0 0 0 2px var(--eqv-bg); border-bottom-color:transparent; }
.eqv-code { border-bottom:1px dotted var(--accent-2); }
/* símbolos dentro de las ecuaciones (SVG de MathJax) */
g.eqv { transition:fill .12s; }
g.eqv:hover, g.eqv.eqv-on { fill:var(--eqv-hl); stroke:var(--eqv-hl); filter:drop-shadow(0 0 3px var(--eqv-glow)); }
.hib-flow { display:flex; align-items:center; justify-content:center; gap:12px; flex-wrap:wrap; margin:14px 0 18px; padding:16px;
  border:1px solid var(--line-strong); border-radius:12px; background:var(--surface-2); }
.hib-col { display:flex; flex-direction:column; align-items:center; gap:6px; text-align:center; } .hib-col small { color:var(--muted); font-size:12px; max-width:160px; }
.hib-mem { flex-direction:row; flex-wrap:wrap; justify-content:center; max-width:430px; }
.hib-chip { display:inline-block; padding:6px 12px; border-radius:999px; font-size:13px; font-weight:600; border:1px solid var(--line-strong); background:var(--surface); }
.hib-orig { background:var(--deep); color:#fff; border-color:var(--deep); } [data-theme="dark"] .hib-orig { background:var(--pale); color:#1A233D; border-color:var(--pale); }
.hib-main { background:var(--accent-2); color:#1A233D; border-color:var(--accent-2); font-size:15px; }
.hib-res { border-color:var(--accent-2); color:var(--accent-2); font-size:15px; }
.hib-op { font-size:22px; font-weight:700; color:var(--accent-2); }
.hib-pipe { margin-top:14px; }
.eqv-hint { display:flex; align-items:center; gap:8px; margin:0 0 6px; font-size:13px; color:var(--muted); }
.eqv-hint .ico { width:15px; height:15px; color:var(--accent-2); }
#eqv-tip { position:fixed; z-index:10040; max-width:340px; padding:10px 13px; border-radius:10px; pointer-events:none;
  background:var(--surface); color:var(--text); border:1px solid var(--accent-2); box-shadow:0 10px 30px rgba(8,12,24,.28);
  font-size:13.5px; line-height:1.45; opacity:0; visibility:hidden; transition:opacity .12s; }
#eqv-tip.on { opacity:1; visibility:visible; }
#eqv-tip .eqv-h { display:flex; align-items:baseline; gap:8px; margin-bottom:4px; }
#eqv-tip .eqv-h b { font-size:16px; color:var(--accent-2); font-family:'Cambria Math','STIX Two Math',Georgia,serif; white-space:nowrap; }
#eqv-tip .eqv-h span { font-weight:700; }
#eqv-tip .eqv-w { margin-top:6px; padding-top:6px; border-top:1px solid var(--line); font-size:12px; color:var(--muted); }
/* botón y ventana del pipeline */
.page-title.pt-row { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
.pipe-btn { white-space:nowrap; }
.pipe-btn.compact { padding:6px 12px; font-size:13px; gap:7px; } .pipe-btn.compact .ico { width:15px; height:15px; }
.pipe-btn:hover { border-color:var(--accent-2); }
.pipe-modal { position:fixed; inset:0; z-index:10020; display:none; align-items:center; justify-content:center; padding:16px; }
.pipe-modal.on { display:flex; }
.pipe-bg { position:absolute; inset:0; background:rgba(8,12,24,.72); }
.pipe-dialog { position:relative; width:min(1040px,100%); max-height:92vh; display:flex; flex-direction:column; background:var(--surface);
  color:var(--text); border-radius:14px; border:1px solid var(--line-strong); box-shadow:0 24px 70px rgba(0,0,0,.45); }
.pipe-head { display:flex; align-items:center; justify-content:space-between; gap:12px; padding:14px 20px; border-bottom:1px solid var(--line); }
.pipe-head h3 { margin:0; font-size:19px; }
.pipe-body { overflow:auto; padding:6px 20px 22px; }
.pipe-intro { margin:12px 0 4px; }
.pipe-phase { margin:18px 0 10px; padding:6px 12px; border-radius:8px; font-size:13.5px; font-weight:700; letter-spacing:.02em;
  background:var(--th-bg); color:#fff; display:inline-block; }
.pipe-phase-mejora { background:var(--accent-2); color:#1A233D; }
.pipe-flow { display:grid; gap:14px; position:relative; }
.pipe-stage { position:relative; padding:12px 16px 12px 16px; border:1px solid var(--line-strong); border-radius:10px; background:var(--surface-2);
  transition:box-shadow .2s, border-color .2s, background .2s; }
.pipe-stage + .pipe-stage::before { content:"↓"; position:absolute; top:-15px; left:26px; font-size:15px; line-height:14px; color:var(--accent-2); font-weight:700; }
.pipe-stage p { margin:6px 0 8px; font-size:14px; }
.pipe-st-head { display:flex; align-items:center; gap:10px; }
.pipe-st-head h4 { margin:0; font-size:15.5px; }
.pipe-num { flex:none; width:26px; height:26px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center;
  background:var(--accent); color:var(--on-accent); font-size:13px; font-weight:700; }
.pipe-chips { display:flex; flex-wrap:wrap; gap:6px; }
.pipe-chip { font-size:12px; padding:2px 9px; border-radius:999px; border:1px solid var(--line-strong); color:var(--muted); background:var(--surface); }
.pipe-link { display:inline-flex; align-items:center; gap:6px; margin-top:8px; font-size:13.5px; font-weight:600; color:var(--accent); text-decoration:none; }
.pipe-link .ico { width:14px; height:14px; } .pipe-link:hover { color:var(--accent-2); }
.pipe-body > .pipe-stage { margin-top:18px; } .pipe-body .pipe-stage .pf-code { margin:8px 0 0; max-height:430px; overflow:auto; }
.pipe-stage.pipe-hl { border-color:var(--accent-2); background:var(--note-bg); box-shadow:0 0 0 3px rgba(184,143,61,.38); }
html.pipe-open { overflow:hidden; }
@media (min-width:900px) { .pipe-group:not(:first-of-type) .pipe-flow { grid-template-columns:1fr 1fr; } .pipe-group:not(:first-of-type) .pipe-stage::before { display:none; } }
@media (max-width:700px) { .pipe-btn.compact .pipe-btn-txt { display:none; } .pipe-btn.compact { padding:6px 9px; } }
@media (prefers-reduced-motion:reduce) { #eqv-tip, .pipe-stage, g.eqv { transition:none; } }
"""
CSS += EQ_PIPE_CSS
CSS += _icon_css()

BOT_W = 400   # ancho del panel en px
BOT_CSS = """
/* ---- panel del asistente: se abre a la derecha y empuja el contenido ---- */
.bot-panel { position:fixed; top:0; right:0; bottom:0; width:%%W%%px; max-width:100vw; z-index:10002;
  display:flex; flex-direction:column; background:var(--surface); color:var(--text);
  border-left:1px solid var(--line-strong); box-shadow:-12px 0 32px rgba(10,14,30,.14);
  transform:translateX(100%); visibility:hidden; transition:transform .3s ease, visibility 0s linear .3s; }
.bot-open .bot-panel { transform:none; visibility:visible; transition:transform .3s ease, visibility 0s; }
.main { transition:margin-left .3s ease, margin-right .3s ease; }
@media (min-width:1101px) { .bot-open .main { margin-right:%%W%%px; } }
.bot-head { display:flex; align-items:center; gap:10px; padding:12px 14px; border-bottom:1px solid var(--line); }
.bot-av { width:40px; height:48px; flex:none; }
.bot-id { flex:1; min-width:0; }
.bot-name { font-weight:700; font-size:15px; display:flex; align-items:center; gap:8px; }
.bot-dot { width:8px; height:8px; border-radius:50%; background:#3FB27F; box-shadow:0 0 0 3px rgba(63,178,127,.18); }
.bot-sub { color:var(--muted); font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.bot-head .icon-btn { width:32px; height:32px; }
.bot-where { padding:8px 16px; font-size:12px; color:var(--muted); border-bottom:1px solid var(--line);
  background:var(--surface-2); display:flex; align-items:center; gap:6px; }
.bot-where b { color:var(--text); font-weight:600; }
.bot-where .ico { width:14px; height:14px; color:var(--accent-2); }
.bot-msgs { flex:1; overflow-y:auto; padding:16px 14px 6px; display:flex; flex-direction:column; gap:14px;
  scroll-behavior:smooth; }
.bm { display:flex; gap:8px; align-items:flex-start; animation:bot-in .25s ease both; }
.bm.user { justify-content:flex-end; }
.bm-av { width:30px; height:36px; flex:none; margin-top:2px; }
.bm-bubble { max-width:86%; padding:10px 13px; border-radius:14px; font-size:13.5px; line-height:1.5;
  overflow-wrap:anywhere; }
.bm.bot .bm-bubble { background:var(--surface-2); border:1px solid var(--line); border-top-left-radius:4px; }
.bm.user .bm-bubble { background:var(--accent); color:var(--on-accent); border-top-right-radius:4px; }
.bm-bubble p { margin:0 0 7px; } .bm-bubble p:last-child { margin-bottom:0; }
.bm-bubble ul, .bm-bubble ol { margin:4px 0 7px; padding-left:18px; } .bm-bubble li { margin:2px 0; }
.bm-bubble code { background:var(--code-bg); padding:1px 5px; border-radius:4px; font-size:12px; }
.bm-bubble > div > *:last-child { margin-bottom:0; }
.bm-bubble p:has(> mjx-container:only-child) { overflow-x:auto; overflow-y:hidden; padding:6px 10px; border-radius:8px;
  background:var(--tech-bg); border-left:3px solid var(--tech-line); text-align:center; }
.bm-bubble mjx-container[display="true"] { display:block; margin:6px 0 !important; padding:6px 8px; overflow-x:auto; overflow-y:hidden;
  max-width:100%; border-radius:8px; background:var(--tech-bg); border-left:3px solid var(--tech-line); }
.bot-go { display:inline-flex; align-items:center; gap:6px; margin-top:8px; padding:5px 10px; border-radius:999px;
  font-size:12.5px; font-weight:600; text-decoration:none; color:var(--accent-2); border:1px solid var(--accent-2); }
.bot-go .ico { width:14px; height:14px; }
.bot-go:hover { background:var(--accent-2); color:var(--on-accent); }
.bot-sugs { display:flex; flex-wrap:wrap; gap:6px; padding:8px 14px 4px; }
.bot-sug { font:inherit; font-size:12.5px; text-align:left; padding:6px 11px; border-radius:999px; cursor:pointer;
  color:var(--text); background:transparent; border:1px solid var(--line-strong); transition:background .15s, border-color .15s; }
.bot-sug:hover { border-color:var(--accent-2); background:var(--surface-2); }
.bot-form { display:flex; gap:8px; padding:10px 14px 6px; }
.bot-input { flex:1; min-width:0; font:inherit; font-size:14px; padding:10px 12px; border-radius:10px;
  border:1px solid var(--line-strong); background:var(--surface-2); color:var(--text); }
.bot-input:focus { outline:none; border-color:var(--accent-2); box-shadow:0 0 0 3px rgba(184,143,61,.18); }
.bot-send { width:42px; flex:none; border:0; border-radius:10px; cursor:pointer; background:var(--accent);
  color:var(--on-accent); display:inline-flex; align-items:center; justify-content:center; }
.bot-send .ico { width:18px; height:18px; }
.bot-foot { margin:0; padding:2px 16px 12px; font-size:11px; color:var(--muted); }
@keyframes bot-in { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:none; } }

/* ---- Kyo, fijo en la esquina inferior derecha ---- */
/* z-index por encima de la barra de depuración de Dash (10000), que solo aparece con python app.py */
.kyo-walker { position:fixed; right:22px; bottom:4px; width:68px; height:82px; z-index:10001; cursor:pointer;
  transition:opacity .25s ease; -webkit-tap-highlight-color:transparent; }
.kyo-walker:focus-visible { outline:2px solid var(--focus); outline-offset:4px; border-radius:12px; }
.bot-open .kyo-walker { opacity:0; pointer-events:none; }
.kyo-flip { width:100%; height:100%; transition:transform .25s ease; }
.kyo-svg { width:100%; height:100%; overflow:visible; display:block; filter:drop-shadow(0 4px 6px rgba(20,16,43,.22)) drop-shadow(0 0 10px rgba(246,200,90,.55));
  transition:transform .2s ease; }
.kyo-walker:hover .kyo-svg { transform:translateY(-4px) scale(1.06); }
.kyo-svg .a-eyes { transform-box:fill-box; transform-origin:center; animation:kyo-blink 4.6s infinite; }
.kyo-svg .a-leg, .kyo-svg .a-arm { transform-box:fill-box; transform-origin:50% 0; }
.kyo-svg .a-spark { transform-box:fill-box; transform-origin:center; animation:kyo-twinkle 2.4s ease-in-out infinite; }
.kyo-bubble { position:absolute; right:58px; bottom:64px; width:max-content; max-width:210px; padding:7px 11px;
  border-radius:12px 12px 2px 12px; background:var(--surface); color:var(--text); border:1px solid var(--line-strong);
  box-shadow:0 6px 18px rgba(10,14,30,.16); font-size:12.5px; font-weight:600; line-height:1.35;
  opacity:0; transform:translateY(6px); pointer-events:none; transition:opacity .25s ease, transform .25s ease; }
.kyo-walker.talk .kyo-bubble, .kyo-walker:hover .kyo-bubble { opacity:1; transform:none; }
@keyframes kyo-blink { 0%,92%,100% { transform:scaleY(1); } 95% { transform:scaleY(.12); } }
@keyframes kyo-twinkle { 0%,100% { transform:scale(1); opacity:1; } 50% { transform:scale(.7); opacity:.6; } }
@media (max-width:900px) {
  .bot-panel { width:100%; }
  .tb-right { flex-wrap:wrap; }   /* la barra superior ya no desborda la pantalla del celular */
  .kyo-walker { width:56px; height:68px; right:12px; }
  .kyo-bubble { right:46px; bottom:52px; } }
@media (prefers-reduced-motion:reduce) {
  .kyo-svg .a-eyes, .kyo-svg .a-spark { animation:none !important; }
  .bm { animation:none; } }
""".replace("%%W%%", str(BOT_W))
CSS += BOT_CSS

# Mascota fija en la página (fuera de Dash), en la esquina inferior derecha
WALKER_HTML = (
    '<div id="kyo-walker" class="kyo-walker" role="button" tabindex="0" '
    'aria-label="Kyo: abrir el asistente / open the assistant" title="Kyo">'
    '<div class="kyo-bubble"><span class="l-es">¿Te explico el tablero? ¡Tócame!</span>'
    '<span class="l-en">Want me to explain the dashboard? Tap me!</span></div>'
    f'<div class="kyo-flip">{mascota_svg("happy", cls="kyo-svg", uid="walker")}</div></div>')

BOT_JS = """
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
"""
