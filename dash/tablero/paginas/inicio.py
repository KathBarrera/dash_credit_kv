# -*- coding: utf-8 -*-
"""Portada: tarjeta que gira, vistazo rápido, video y accesos."""

import plotly.graph_objects as go
import re
from dash import dcc, html

from tablero.componentes import card
from tablero.config import (
    AUTHORS, INSTITUTION, L, LINKS, MONO, PROJECT_TITLE, PROJECT_VIDEO_URL, WARM_GOLD, tx)
from tablero.datos import DF, TARGET
from tablero.iconos import icon
from tablero.utilidades import GLOBAL_RATE, style_fig


# ---------------------------------------------------------------- Portada y vistazo rápido
def fig_home():
    """Tasa de default según el estado de pago de septiembre (el hallazgo más claro del EDA)."""
    g = DF.groupby("PAY_0")[TARGET].agg(["mean", "size"])
    g = g[g["size"] >= 100]
    fig = go.Figure(go.Bar(
        x=[str(int(i)) for i in g.index], y=g["mean"] * 100, marker_color=MONO, customdata=g["size"],
        hovertemplate="PAY_0 = %{x}<br>Default: %{y:.1f}%<br>" + tx("Clientes", "Clients")
                      + ": %{customdata:,}<extra></extra>"))
    fig.add_hline(y=GLOBAL_RATE * 100, line_dash="dash", line_color=WARM_GOLD, line_width=1.6,
                  annotation_text=tx(f"Tasa global {GLOBAL_RATE:.1%}", f"Overall rate {GLOBAL_RATE:.1%}"),
                  annotation_position="top left", annotation_font_color=WARM_GOLD)
    style_fig(fig, 310, legend_top=False)
    fig.update_layout(margin=dict(l=55, r=20, t=24, b=55), showlegend=False,
                      xaxis_title=tx("Estado de pago en septiembre (PAY_0)", "September repayment status (PAY_0)"),
                      yaxis_title=tx("% que incumple el mes siguiente", "% defaulting the next month"))
    fig.update_xaxes(type="category")
    return fig


def youtube_id(url):
    """Identificador de un video de YouTube a partir de cualquier forma de enlace (o None)."""
    m = re.search(r"(?:youtu\.be/|[?&]v=|/(?:embed|shorts|live)/)([A-Za-z0-9_-]{11})", url or "")
    return m.group(1) if m else None


def video_card():
    """Video del proyecto: reproductor de YouTube embebido o, sin enlace, un espacio reservado."""
    vid = youtube_id(PROJECT_VIDEO_URL)
    if vid:
        body = html.Div(html.Iframe(
            src=f"https://www.youtube-nocookie.com/embed/{vid}?rel=0", title=tx("Video del proyecto", "Project video"),
            allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen",
            referrerPolicy="strict-origin-when-cross-origin"), className="video-wrap")
        extra = html.A([icon("external"), tx("Ver en YouTube", "Watch on YouTube")],
                       href=f"https://www.youtube.com/watch?v={vid}", target="_blank", rel="noopener noreferrer",
                       className="video-link")
    else:
        body = html.Div([icon("play", "video-ico"), html.B(tx("Video próximamente", "Video coming soon")),
                         html.Span(tx("Aquí se verá el video del proyecto.", "The project video will appear here."))],
                        className="video-wrap video-empty")
        extra = None
    return card(tx("Video del proyecto", "Project video"), [body, extra] if extra else [body])


def link_cards(compact=False):
    items = []
    for lk in LINKS:
        title = L(lk["title"])
        body = [html.Div([html.Span(icon(lk["icon"]), className="lc-ico"), icon("external", "lc-ext")],
                         className="lc-top"),
                html.Div(title, className="lc-title")]
        if not compact:
            body.append(html.P(L(lk["desc"])))
        items.append(html.A(body, href=lk["url"], target="_blank", rel="noopener noreferrer",
                            className="link-card", title=f"{tx('Abrir', 'Open')}: {title}"))
    return html.Div(items, className="link-grid")


def quick_look():
    """Gráfica de PAY_0 (antes en la portada), ahora al inicio de Introducción."""
    r_late = DF.loc[DF["PAY_0"] >= 2, TARGET].mean()
    r_ok = DF.loc[DF["PAY_0"] <= 0, TARGET].mean()
    return card(tx("Vistazo rápido: el atraso de septiembre anticipa el incumplimiento",
                   "Quick look: September's delay anticipates default"),
                [dcc.Graph(id="home-graph", figure=fig_home(),
                           config={"displaylogo": False, "displayModeBar": False}),
                 html.P(tx(f"Entre quienes tenían 2 o más meses de atraso en septiembre, {r_late:.0%} incumplió el mes "
                           f"siguiente; entre quienes iban al día o pagaban el mínimo, {r_ok:.0%}.",
                           f"Among those 2 or more months late in September, {r_late:.0%} defaulted the following "
                           f"month; among those up to date or paying the minimum, {r_ok:.0%}."), className="muted")])


def _stat(label, value):
    return html.Div([html.Span(label), html.B(value)], className="sig-stat")


def page_home():
    """Portada a pantalla completa: una tarjeta de crédito interactiva (inclina con el mouse, se voltea)."""
    front = html.Div([
        html.Div(className="cc-gloss"),
        html.Div([html.Span(tx("Riesgo de crédito", "Credit risk"), className="cc-brand"), icon("contactless", "cc-nfc")],
                 className="cc-top"),
        html.Div(className="cc-chip"),
        html.Div("•••• •••• •••• 2005", className="cc-number"),
        html.Div([
            html.Div([html.Span(tx("Titulares", "Cardholders"), className="cc-lbl"),
                      *[html.Div(a["name"], className="cc-name") for a in AUTHORS]]),
            html.Div([html.Span(tx("Periodo de datos", "Data period"), className="cc-lbl"),
                      html.Div(tx("ABR 2005 A SEP 2005", "APR 2005 to SEP 2005"), className="cc-name")],
                     className="cc-valid"),
        ], className="cc-bottom"),
    ], className="cc-face cc-front")
    back = html.Div([
        html.Div(className="cc-gloss"),
        html.Div(className="cc-mag"),
        html.Div([_stat(tx("Clientes", "Clients"), f"{len(DF):,}"), _stat("Default", f"{GLOBAL_RATE:.1%}"),
                  _stat(tx("Periodo", "Period"), tx("Abr a Sep 2005", "Apr to Sep 2005"))], className="cc-sig"),
        html.P(tx("Datos: UCI · Banco de Taiwán · Yeh & Lien (2009)", "Data: UCI · Taiwanese bank · Yeh & Lien (2009)"),
               className="cc-fine"),
    ], className="cc-face cc-back")
    card3d = html.Div(html.Div([front, back], className="cc-inner"), id="cc", tabIndex=0, className="cc",
                      **{"aria-label": tx("Tarjeta del proyecto. Púlsala para voltearla",
                                          "Project card. Press it to flip it")})
    return html.Div([
        html.Div(className="bill-bg"),
        html.Div([
            html.Div(html.Div(card3d, className="cc-settle"), className="cc-scene"),
            html.Div([
                html.Div([icon("card"), tx("Proyecto EDA", "EDA Project")], className="cover-tag"),
                html.H1(L(PROJECT_TITLE)),
                html.P(tx(f"Quién deja de pagar el mes siguiente y qué señales lo anticipan: {len(DF):,} clientes de "
                          "tarjeta de crédito de un banco de Taiwán, de abril a septiembre de 2005.",
                          f"Who stops paying the following month and which signals anticipate it: {len(DF):,} credit "
                          "card clients of a Taiwanese bank, from April to September 2005."), className="hero-lead"),
                dcc.Link([tx("Iniciar recorrido", "Start the tour"), icon("arrow")], href="/introduccion",
                         className="btn primary big"),
                html.Div([html.Span(tx("Haz clic o toca la tarjeta para voltearla.", "Click or tap the card to flip it.")),
                          html.Span(L(INSTITUTION))],
                         className="cover-hint"),
            ], className="cover-copy"),
        ], className="cover-hero"),
    ], className="cover")
