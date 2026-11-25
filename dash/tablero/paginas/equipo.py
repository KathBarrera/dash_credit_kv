# -*- coding: utf-8 -*-
"""Página Equipo: tarjetas que se voltean con la bio y los enlaces."""

from dash import html

from tablero.componentes import page_title
from tablero.config import (INSTITUTION, L, TEAM, tx)
from tablero.iconos import icon
from tablero.servidor import app


# ---------------------------------------------------------------- Equipo
def _team_link(ic, label, href):
    ext = {} if href.startswith("mailto:") else {"target": "_blank", "rel": "noopener noreferrer"}
    return html.A([icon(ic), html.Span(label)], href=href, className="tc-link", title=label, **ext)


def _copy_email(email):
    """Botón que copia el correo al portapapeles (ver TEAM_JS) y avisa con «¡Correo copiado!»."""
    return html.Button([icon("mail"), html.Span(email, className="tc-copy-txt"),
                        html.Span(tx("¡Correo copiado!", "Email copied!"), className="tc-copy-ok",
                                  **{"aria-live": "polite"})],
                       className="tc-link tc-copy", title=f"{tx('Copiar', 'Copy')} {email}", n_clicks=0,
                       **{"data-email": email, "type": "button"})


def team_card(m, i):
    """Tarjeta de crédito vertical: frente con foto y rol; reverso con bio y enlaces (se voltea)."""
    front = html.Div([
        html.Div(className="cc-gloss"),
        html.Div([html.Span(tx("Equipo · Uninorte", "Team · Uninorte"), className="cc-brand"),
                  icon("contactless", "cc-nfc")], className="cc-top"),
        html.Div(html.Img(src=app.get_asset_url(m["photo"]), alt=tx(f"Foto de {m['name']}", f"Photo of {m['name']}")),
                 className="tc-photo"),
        html.Div([html.Div(className="cc-chip tc-chip"),
                  html.Div(f"•••• •••• •••• {m['card_no']}", className="tc-number")], className="tc-mid"),
        html.Div([html.Span(tx("Titular", "Cardholder"), className="cc-lbl"), html.Div(m["name"], className="tc-name"),
                  html.Div(L(m["role"]), className="tc-role")]),
        html.Div([icon("flip"), tx("Toca para ver contacto", "Tap to see contact")], className="tc-hint"),
    ], className="cc-face tc-front")
    back = html.Div([
        html.Div(className="cc-gloss"),
        html.Div(className="cc-mag tc-mag"),
        html.Div([html.Span(tx("Firma autorizada", "Authorized signature"), className="tc-sig-lbl"),
                  html.Div(m["short"], className="tc-sig-name")], className="tc-sig"),
        html.P(L(m["bio"]), className="tc-bio"),
        html.Div([_team_link("github", "GitHub", m["github"]),
                  _team_link("linkedin", "LinkedIn", m["linkedin"]),
                  _copy_email(m["email"])], className="tc-links"),
        html.P(L(INSTITUTION), className="cc-fine tc-fine"),
    ], className="cc-face tc-back")
    return html.Div(html.Div([front, back], className="tc-inner"), className="tc", tabIndex=0,
                    **{"role": "button", "aria-pressed": "false",
                       "aria-label": tx(f"Tarjeta de {m['name']}. Púlsala para ver su contacto",
                                        f"{m['name']}'s card. Press it to see their contact")})


def page_team():
    return html.Div([
        page_title(tx("Equipo", "Team"), ""),
        html.Div([html.Div(team_card(m, i), className="tc-scene") for i, m in enumerate(TEAM)],
                 className="team-grid"),
        html.P(tx("Haz clic o toca una tarjeta para voltearla y ver la bio y los enlaces.",
                  "Click or tap a card to flip it and see the bio and links."), className="muted team-hint"),
    ])
