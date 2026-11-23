# -*- coding: utf-8 -*-
"""Callbacks del asistente Kyo: preguntas, sugerencias y panel."""

from dash import ALL, Input, Output, State, ctx, html, no_update

from tablero.config import LANG, set_lang, tx
from tablero.iconos import icon
from tablero.kyo import BOT, _bot_msg, _bot_path
from tablero.servidor import app


# ---------- Callbacks: Asistente Kyo -------------------------------------------
@app.callback(Output("bot-store", "data"), Output("bot-input", "value"),
              Input("bot-send", "n_clicks"), Input("bot-input", "n_submit"),
              Input({"type": "bot-sug", "index": ALL}, "n_clicks"), Input("bot-reset", "n_clicks"),
              State("bot-input", "value"), State("url", "pathname"), State("bot-store", "data"), State("lang", "data"),
              prevent_initial_call=True)
def cb_bot(_send, _enter, _sugs, _reset, text, path, hist, lang):
    trig = ctx.triggered_id
    if trig == "bot-reset":
        return [], ""
    if isinstance(trig, dict):   # una sugerencia: su texto viaja en el id
        # (ctx.triggered pierde el valor cuando el id tiene tildes; se busca en la lista de entradas)
        clicked = any(i["id"] == trig and i.get("value") for i in ctx.inputs_list[2])
        if not clicked:          # los botones recién dibujados también disparan el callback
            return no_update, no_update
        text = trig["index"]
    text = (text or "").strip()[:300]
    if not text:
        return no_update, no_update
    hist = list(hist or [])[-38:]
    last = next((m.get("i") for m in reversed(hist) if m["r"] == "b" and m.get("i")), None)
    hist += [{"r": "u", "t": text}, {"r": "b", **BOT.responder(text, _bot_path(path), last, lang)}]
    return hist, ""


@app.callback(Output("bot-msgs", "children"), Output("bot-sugs", "children"), Output("bot-where", "children"),
              Input("bot-store", "data"), Input("url", "pathname"), Input("lang", "data"))
def cb_bot_render(hist, path, lang):
    set_lang(lang)
    lang = LANG.get()
    path = _bot_path(path)
    hist = hist or []
    msgs = [BOT.bienvenida(path, lang) | {"r": "b"}] + hist
    sugs = msgs[-1].get("s", []) if not hist else (hist[-1].get("s") or BOT.sug_de_pagina[lang].get(path, []))
    where = [icon("info"), tx("Estás en ", "You are on "), html.B(BOT.nombre_pagina(path, lang))]
    return ([_bot_msg(m, path) for m in msgs],
            [html.Button(s, id={"type": "bot-sug", "index": s}, n_clicks=0, className="bot-sug", type="button")
             for s in sugs],
            where)
