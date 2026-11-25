# -*- coding: utf-8 -*-
"""Asistente Kyo: se entrena al arrancar con las cifras del tablero y arma su panel y sus mensajes.
Su lógica (motor, conocimiento y mascota) está en asistente/.
"""

import re
from types import SimpleNamespace
from asistente import Asistente, construir_conocimiento, mascota_uri
from dash import dcc, html

from tablero import config, datos, eda_multi, eda_uni, prediccion, resultados, utilidades
from tablero.config import tx
from tablero.iconos import icon

# ---------- Asistente Kyo: entrenamiento y panel ------------------------------------
# Se entrena una sola vez al arrancar (menos de un segundo) con las mismas cifras e interpretaciones que
# dibujan las gráficas: construir_conocimiento() lee los datos, figuras y resultados de estos módulos.
CONTENIDO = SimpleNamespace(**{k: v for m in (config, datos, utilidades, eda_uni, eda_multi, resultados, prediccion)
                          for k, v in vars(m).items()})
BOT = Asistente({"es": construir_conocimiento(CONTENIDO, "es"), "en": construir_conocimiento(CONTENIDO, "en")})
print(f"[kyo] entrenado con {BOT.n_ejemplos} preguntas (español e inglés) de {BOT.n_temas} temas del tablero")
BOT_AV = {m: mascota_uri(m) for m in ("happy", "thinking", "explaining", "proud", "alert")}


def bot_panel():
    return html.Aside([
        html.Div([
            html.Img(src=BOT_AV["happy"], className="bot-av", alt=""),
            html.Div([html.Div(["Kyo", html.Span(className="bot-dot")], className="bot-name"),
                      html.Div(id="bot-sub", className="bot-sub")],
                     className="bot-id"),
            html.Button(icon("reset"), id="bot-reset", n_clicks=0, className="icon-btn", type="button"),
            html.Button(icon("close"), id="bot-close", n_clicks=0, className="icon-btn", type="button"),
        ], className="bot-head"),
        html.Div(id="bot-where", className="bot-where"),
        html.Div(id="bot-msgs", className="bot-msgs", role="log", **{"aria-live": "polite"}),
        html.Div(id="bot-sugs", className="bot-sugs"),
        html.Div([
            dcc.Input(id="bot-input", type="text", n_submit=0, autoComplete="off", className="bot-input",
                      maxLength=300),
            html.Button(icon("send"), id="bot-send", n_clicks=0, className="bot-send", type="button"),
        ], className="bot-form"),
        html.P(id="bot-foot", className="bot-foot"),
    ], id="bot-panel", className="bot-panel", **{"aria-label": "Kyo"})


def _bot_path(path):
    return (path or "/").rstrip("/") or "/"


def _bot_msg(m, path):
    if m["r"] == "u":
        return html.Div(html.Div(m["t"], className="bm-bubble"), className="bm user")
    # MathJax para que las fórmulas de Kyo ($$…$$) se vean como fórmulas; "NT$" se escapa para no abrir una fórmula
    txt = re.sub(r"\$\$(.+?)\$\$", r"$$\\displaystyle \1$$", m["t"].replace("NT$", "NT&#36;"), flags=re.S)
    body = [dcc.Markdown(txt, link_target="_blank", mathjax=True)]
    if m.get("p") and m["p"] != path:
        body.append(dcc.Link([f"{tx('Ir a', 'Go to')} {m.get('n') or tx('la sección', 'the section')}", icon("arrow")],
                             href=m["p"], className="bot-go"))
    return html.Div([html.Img(src=BOT_AV.get(m.get("m"), BOT_AV["happy"]), className="bm-av", alt=""),
                     html.Div(body, className="bm-bubble")], className="bm bot")
