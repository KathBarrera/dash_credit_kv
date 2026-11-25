# -*- coding: utf-8 -*-
"""Íconos SVG propios (sin dependencias ni emojis; toman el color del texto)."""

from dash import html
from urllib.parse import quote

from tablero.config import tx

ICONS = {
    "play": '<rect x="2" y="5" width="20" height="14" rx="3"/><path d="M10 9.5v5l4.5-2.5z"/>',
    "flag": '<path d="M5 21V4"/><path d="M5 4h11l-2 4 2 4H5"/>',
    "panel": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M6.3 17.7l-1.4 1.4M19.1 4.9l-1.4 1.4"/>',
    "moon": '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9z"/>',
    "home": '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M10 21v-6h4v6"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    "book": '<path d="M2 4h6a4 4 0 0 1 4 4v13a3 3 0 0 0-3-3H2z"/><path d="M22 4h-6a4 4 0 0 0-4 4v13a3 3 0 0 1 3-3h7z"/>',
    "bars": '<path d="M3 3v18h18"/><path d="M8 17v-5M13 17V8M18 17v-9"/>',
    "scatter": '<circle cx="7" cy="16" r="2"/><circle cx="12" cy="8" r="2"/><circle cx="18" cy="14" r="2"/><path d="M8.4 14.3l2.3-4.5M13.5 9.4l3.3 3.2"/>',
    "link": '<path d="M10 13a5 5 0 0 0 7.07 0l3-3a5 5 0 0 0-7.07-7.07l-1.5 1.5"/><path d="M14 11a5 5 0 0 0-7.07 0l-3 3a5 5 0 0 0 7.07 7.07l1.5-1.5"/>',
    "github": '<path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.4 5.4 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/><path d="M9 18c-4.51 2-5-2-7-2"/>',
    "notebook": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h8M8 9h2"/>',
    "external": '<path d="M15 3h6v6M10 14 21 3M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    "database": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "alert": '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
    "calendar": '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    "columns": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M9 4v16M15 4v16"/>',
    "coin": '<circle cx="12" cy="12" r="9"/><path d="M14.5 9a2.5 2.5 0 0 0-2.5-1.5c-1.4 0-2.5.9-2.5 2s1.1 1.7 2.5 2 2.5.9 2.5 2-1.1 2-2.5 2a2.5 2.5 0 0 1-2.5-1.5M12 6v1.5M12 16.5V18"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "mail": '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-10 5L2 7"/>',
    "linkedin": '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-4 0v7h-4v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/>',
    "flip": '<path d="M3 12a9 9 0 0 1 15.5-6.2L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-15.5 6.2L3 16"/><path d="M3 21v-5h5"/>',
    # --- nuevos: detalles de tarjeta de crédito ---
    "card": '<rect x="2" y="5" width="20" height="14" rx="2.5"/><path d="M2 10h20M6 15h4"/>',
    "chip": '<rect x="4" y="5" width="16" height="14" rx="3"/><path d="M4 10h16M4 14h16M10 5v14M14 5v14"/>',
    "contactless": '<path d="M8.5 8.5a5 5 0 0 1 0 7M12 6a9 9 0 0 1 0 12M15.5 3.5a13 13 0 0 1 0 17"/>',
    # íconos financieros para el pipeline (datafono, recibo, billetera, tarjeta con pago)
    "pos": '<rect x="5" y="2" width="14" height="20" rx="2.5"/><rect x="7.5" y="4.5" width="9" height="5" rx="1"/>'
           '<path d="M8.5 13h.01M12 13h.01M15.5 13h.01M8.5 16h.01M12 16h.01M15.5 16h.01M8.5 19h.01M12 19h.01M15.5 19h.01"/>',
    "receipt": '<path d="M6 2.5h12v19l-2-1.4-2 1.4-2-1.4-2 1.4-2-1.4-2 1.4z"/><path d="M9 7h6M9 11h6M9 15h3.5"/>',
    "wallet": '<path d="M4 7.5V18a2 2 0 0 0 2 2h13a1 1 0 0 0 1-1v-3M4 7.5A2 2 0 0 1 6 5.5h11V8"/>'
              '<path d="M4 7.5A1.5 1.5 0 0 0 5.5 9H20v4"/><path d="M21 13h-4a1.5 1.5 0 0 0 0 3h4z"/>',
    "cardpay": '<rect x="2" y="4" width="16" height="11" rx="2"/><path d="M2 8h16M5 12h3"/>'
               '<circle cx="18" cy="17" r="4"/><path d="M16.4 17l1.1 1.1 2.1-2.2"/>',
    "safe": '<rect x="3" y="3" width="18" height="16" rx="2"/><circle cx="12" cy="11" r="3.5"/>'
            '<path d="M12 7.5v1M12 13.5v1M8.5 11h1M14.5 11h1M6 19v2M18 19v2"/>',
    # --- página Modelos ---
    "layers": '<path d="m12 2 10 5-10 5L2 7z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>',
    "trophy": '<path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0z"/><path d="M17 5h3v2a3 3 0 0 1-3 3M7 5H4v2a3 3 0 0 0 3 3"/>',
    "chevron": '<path d="m9 6 6 6-6 6"/>',
    "gauge": '<path d="M3.5 18a9.5 9.5 0 1 1 17 0"/><path d="m12 13 4.5-4.5"/><circle cx="12" cy="13" r="1.4"/>',
    "male": '<circle cx="10" cy="14" r="6"/><path d="M14.5 9.5 20 4M15 4h5v5"/>',
    "female": '<circle cx="12" cy="9" r="6"/><path d="M12 15v7M9 19h6"/>',
    "gender": '<circle cx="11" cy="12" r="5"/><path d="M14.5 8.5 19 4M15 4h4v4M11 17v5M8.5 19.5h5"/>',
    "cap": '<path d="m2 9 10-5 10 5-10 5z"/><path d="M6 11v5c3 2 9 2 12 0v-5M22 9v6"/>',
    "pencil": '<path d="M17 3l4 4L8 20H4v-4z"/><path d="m14 6 4 4"/>',
    "dots": '<circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/>',
    "rings": '<circle cx="9" cy="14" r="5.5"/><circle cx="15" cy="14" r="5.5"/><path d="m10 5 2-2 2 2-2 2z"/>',
    "person": '<circle cx="12" cy="7" r="4"/><path d="M5 21a7 7 0 0 1 14 0"/>',
    "tree": '<path d="M12 22v-5"/><path d="M12 17H6l3-4H7l3-4H8.5L12 3l3.5 6H14l3 4h-2l3 4z"/>',
    "save": '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><path d="M17 21v-8H7v8M7 3v5h8"/>',
    # --- asistente Kyo ---
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "filter": '<path d="M3 4h18l-7 8.5V20l-4-2v-5.5z"/>',
    "expand": '<path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7"/>',
    "send": '<path d="M22 2 11 13"/><path d="M22 2 15 22l-4-9-9-4z"/>',
    "reset": '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/>',
}


def _icon_css():
    out = []
    for name, body in ICONS.items():
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="black" '
               'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + body + '</svg>')
        out.append(f'.ico-{name}{{--ico:url("data:image/svg+xml,{quote(svg)}");}}')
    return "\n".join(out)


def icon(name, cls=""):
    """Ícono decorativo: <span class="ico ico-nombre">, coloreado con el color del texto."""
    return html.Span(className=f"ico ico-{name} {cls}".strip(), **{"aria-hidden": "true"})


PAGE_ICONS = {"Introducción": "info", "Problema y Objetivos": "target", "Marco Teórico": "book",
              "EDA Univariado": "bars", "EDA Multivariado": "scatter", "Modelos": "layers", "Modelo original": "tree", "Predecir": "gauge",
              "Enlaces": "link", "Equipo": "users", "Conclusiones": "flag",
              "Introduction": "info", "Problem and Objectives": "target", "Theoretical Framework": "book",
              "Univariate EDA": "bars", "Multivariate EDA": "scatter", "Models": "layers", "Original model": "tree", "Predict": "gauge",
              "Links": "link", "Team": "users", "Conclusions": "flag"}


def zoom_btn():
    """Botón de «ampliar» de la esquina superior derecha. assets/card_focus.js lo cambia por «cerrar» al ampliar."""
    abrir, cerrar = tx("Ampliar tarjeta", "Enlarge card"), tx("Cerrar (Esc)", "Close (Esc)")
    return html.Button([icon("expand", "zb-open"), icon("close", "zb-close")], type="button", className="card-zoom",
                       title=abrir, **{"aria-label": abrir, "aria-expanded": "false",
                                       "data-label-open": abrir, "data-label-close": cerrar})
