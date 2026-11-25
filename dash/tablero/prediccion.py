# -*- coding: utf-8 -*-
"""Predecir: carga los modelos serializados con joblib (modelo/modelo_xgboost.pkl y modelo_cs_fof.pkl)
y calcula puntajes, árboles que empujan el riesgo, historial, aporte por grupo y «¿Qué pasaría si…?».
"""

import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sys
from dash import html
from plotly.subplots import make_subplots

from tablero.config import (
    BASE_DIR, GOLD_DARK, GOLD_MID, GREY_BLUE, L, NAVY, PALE_GOLD, WARM_GOLD, WHITE, tx)
from tablero.datos import (BILL_COLS, CAT_COLS, DF, MONTH_ORDER, PAYAMT_COLS, PAY_COLS, month_lbl)
from tablero.utilidades import style_fig

# El .pkl lo genera `python -m modelo.entrenar_extra xgboost` (ver modelo/entrenar_extra.py).
# Es un Pipeline completo: transforma las 23 variables originales, aplica one-hot y
# predice con XGBoost con pesos de clase (scale_pos_weight), el mejor modelo de
# referencia del proyecto. Aquí solo se CARGA y se usa.
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))   # para que joblib encuentre modelo.features
MODEL_FILE = BASE_DIR / "modelo" / "modelo_xgboost.pkl"
MODEL_META_FILE = BASE_DIR / "modelo" / "modelo_xgboost.json"
try:
    import joblib
    from modelo.features import INPUT_COLS
    MODELO = joblib.load(MODEL_FILE)
    MODELO_META = json.loads(MODEL_META_FILE.read_text(encoding="utf-8"))
    MODELO_ERROR = None
except Exception as _e:   # el tablero sigue funcionando aunque falte el modelo
    MODELO, MODELO_META, MODELO_ERROR = None, {}, f"{type(_e).__name__}: {_e}"
    INPUT_COLS = (["LIMIT_BAL", "SEX", "EDUCATION", "MARRIAGE", "AGE"] + PAY_COLS + BILL_COLS + PAYAMT_COLS)
    print(f"[modelo] no se pudo cargar {MODEL_FILE.name}: {MODELO_ERROR}")

# Selector de «Predecir»: XGBoost (el mejor modelo de referencia) y CS-FOF (original).
# El segundo lo genera `python -m modelo.entrenar_extra cs_fof`; si falta, el selector solo ofrece XGBoost.
MODELOS = {}
if MODELO is not None:
    MODELOS["xgboost"] = (MODELO, MODELO_META)
for _k in ("cs_fof",):
    try:
        MODELOS[_k] = (joblib.load(BASE_DIR / "modelo" / f"modelo_{_k}.pkl"),
                       json.loads((BASE_DIR / "modelo" / f"modelo_{_k}.json").read_text(encoding="utf-8")))
    except Exception as _e:
        print(f"[modelo] no se pudo cargar modelo_{_k}.pkl: {type(_e).__name__}: {_e}")
MODEL_LABELS = {"xgboost": ("XGBoost", "XGBoost"),
                "cs_fof": ("CS-FOF (modelo original)", "CS-FOF (original model)")}


def _mk(key):
    return key if key in MODELOS else "xgboost"


def _meta(key):
    return MODELOS[_mk(key)][1]


# Columnas del formulario en orden cronológico (Abr ... Sep)
PAY_CHRONO = MONTH_ORDER                                         # PAY_6 ... PAY_0
BILL_CHRONO = [f"BILL_AMT{i}" for i in range(6, 0, -1)]          # BILL_AMT6 = abril
PAYAMT_CHRONO = [f"PAY_AMT{i}" for i in range(6, 0, -1)]


def _profile_typical():
    """Cliente «típico»: mediana de las numéricas y moda de las categóricas."""
    out = {c: int(DF[c].mode()[0]) for c in CAT_COLS + PAY_COLS}
    out.update({c: int(round(DF[c].median(), -2)) for c in BILL_COLS + PAYAMT_COLS})
    out["LIMIT_BAL"] = int(round(DF["LIMIT_BAL"].median(), -4))
    out["AGE"] = int(DF["AGE"].median())
    return out


PROFILES = {
    "tipico": (("Cliente típico", "Typical client"), _profile_typical()),
    "al-dia": (("Al día, cupo alto", "Up to date, high limit"), {
        "LIMIT_BAL": 360000, "SEX": 2, "EDUCATION": 1, "MARRIAGE": 2, "AGE": 36,
        **{c: -1 for c in PAY_COLS},
        **dict(zip(BILL_COLS, [18500, 21000, 15800, 19200, 12400, 16900])),
        **dict(zip(PAYAMT_COLS, [21000, 15800, 19200, 12400, 16900, 14000]))}),
    "atrasos": (("Atrasos recientes", "Recent delays"), {
        "LIMIT_BAL": 50000, "SEX": 1, "EDUCATION": 3, "MARRIAGE": 1, "AGE": 47,
        **dict(zip(PAY_COLS, [2, 2, 2, 0, 0, 0])),
        **dict(zip(BILL_COLS, [49200, 48100, 46800, 45100, 44300, 43000])),
        **dict(zip(PAYAMT_COLS, [0, 0, 1500, 1600, 1700, 1800]))}),
}


SEX_OTHER = 3   # «Otro»: el dataset solo registra 1 = hombre y 2 = mujer
# Grupos de variables para «¿Qué empuja su riesgo?»
DRIVER_GROUPS = [(("Historial de pagos", "Payment history"), PAY_COLS),
                 (("Montos pagados", "Amounts paid"), PAYAMT_COLS),
                 (("Facturación", "Billing"), BILL_COLS),
                 (("Cupo de crédito", "Credit limit"), ["LIMIT_BAL"]),
                 (("Perfil demográfico", "Demographic profile"), ["AGE", "SEX", "EDUCATION", "MARRIAGE"])]
# Variables del simulador «¿Qué pasaría si…?»: (etiqueta corta, valores, título del eje)
WHATIF = {
    "PAY_0": (("Atraso en septiembre", "September delay"), list(range(-2, 9)),
              ("Estado de pago en septiembre", "September repayment status")),
    "LIMIT_BAL": (("Cupo", "Limit"), list(range(10000, 1000001, 30000)), ("Cupo de crédito (NT$)", "Credit limit (NT$)")),
    "PAY_AMT1": (("Pago de septiembre", "September payment"),
                 [0] + sorted({int(round(v, -2)) for v in np.geomspace(500, 200000, 22)}),
                 ("Monto pagado en septiembre (NT$)", "Amount paid in September (NT$)")),
    "AGE": (("Edad", "Age"), list(range(21, 76, 2)), ("Edad (años)", "Age (years)")),
}
_PAY_SHORT = {-2: ("Sin uso", "No use"), -1: ("Al día", "Paid"), 0: ("Mínimo", "Minimum")}


def _pay_short(v):
    return L(_PAY_SHORT[v]) if v in _PAY_SHORT else tx(f"{v} m atraso", f"{v} m late")


def predict_scores(rows, key="xgboost"):
    """Lista de dicts con las 23 variables -> puntajes (0-1) del modelo serializado.

    Para SEX = 3 («Otro») promedia las predicciones como hombre y como mujer, porque el
    modelo solo aprendió esas dos categorías.
    """
    d = pd.DataFrame([[r[c] for c in INPUT_COLS] for r in rows], columns=INPUT_COLS)
    other = (d["SEX"] == SEX_OTHER).to_numpy()
    d.loc[other, "SEX"] = 1
    modelo = MODELOS[_mk(key)][0]
    p = modelo.predict_proba(d)[:, 1]
    if other.any():
        d2 = d[other].copy()
        d2["SEX"] = 2
        p[other] = (p[other] + modelo.predict_proba(d2)[:, 1]) / 2
    return p


def predict_risk(values, key="xgboost"):
    return float(predict_scores([values], key)[0])


_XGB_LEAVES = {}


def _xgb_leaf_values(clf):
    """Valor de cada hoja de cada árbol de XGBoost: {árbol: {nodo: valor}} (se calcula una vez)."""
    if id(clf) not in _XGB_LEAVES:
        t = clf.get_booster().trees_to_dataframe()
        t = t[t["Feature"] == "Leaf"]
        _XGB_LEAVES[id(clf)] = {k: dict(zip(g["Node"], g["Gain"])) for k, g in t.groupby("Tree")}
    return _XGB_LEAVES[id(clf)]


def tree_votes(values, key="xgboost"):
    """Cuántos árboles empujan hacia «incumple».

    En CS-FOF (un bosque) es la proporción de árboles con probabilidad ≥ 0.5. En XGBoost los árboles se suman en
    cadena: cuenta los que llevan al cliente a una hoja de valor positivo, es decir, que suben su puntaje."""
    rows = [values] if values["SEX"] != SEX_OTHER else [{**values, "SEX": 1}, {**values, "SEX": 2}]
    X = pd.DataFrame([[r[c] for c in INPUT_COLS] for r in rows], columns=INPUT_COLS)
    modelo = MODELOS[_mk(key)][0]
    Xt = modelo[:-1].transform(X)
    if _mk(key) == "cs_fof":
        bosque = modelo[-1]
        Z = (np.asarray(Xt, dtype=float) - bosque.media_) / bosque.escala_
        trees = bosque.arboles_
        yes = np.mean([np.mean(a.proba1(Z) >= 0.5) for a in trees]) * len(trees)
    else:
        clf = modelo[-1]
        hojas, valores = clf.apply(np.asarray(Xt, dtype=float)), _xgb_leaf_values(clf)
        trees = range(hojas.shape[1])
        yes = np.mean([[valores[j][int(h[j])] > 0 for j in trees] for h in hojas]) * len(trees)
    return int(round(yes)), len(trees)


def fig_client_history(values):
    """Facturado vs. pagado por mes y estado de pago (eje derecho)."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    ml = month_lbl()
    fig.add_trace(go.Bar(x=ml, y=[values[c] or 0 for c in BILL_CHRONO], name=tx("Facturado", "Billed"),
                         marker_color=NAVY,
                         hovertemplate="%{x} · " + tx("facturado", "billed") + ": NT$ %{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Bar(x=ml, y=[values[c] or 0 for c in PAYAMT_CHRONO], name=tx("Pagado", "Paid"),
                         marker_color=PALE_GOLD,
                         hovertemplate="%{x} · " + tx("pagado", "paid") + ": NT$ %{y:,.0f}<extra></extra>"))
    st = [values[c] for c in PAY_CHRONO]
    fig.add_trace(go.Scatter(
        x=ml, y=st, name=tx("Estado de pago", "Repayment status"), mode="lines+markers",
        customdata=[_pay_short(v) for v in st],
        line=dict(color=WARM_GOLD, width=2.5),
        marker=dict(size=12, color=[WARM_GOLD if v >= 1 else GREY_BLUE for v in st], line=dict(width=1.5, color=WHITE)),
        hovertemplate="%{x} · " + tx("estado", "status") + ": %{customdata}<extra></extra>"), secondary_y=True)
    style_fig(fig, 340)
    fig.update_layout(barmode="group", bargap=.28, margin=dict(l=60, r=55, t=40, b=36))
    fig.update_yaxes(title_text="NT$", secondary_y=False, tickformat="~s")
    fig.update_yaxes(title_text=tx("Estado de pago", "Repayment status"), secondary_y=True, range=[-2.8, 9.2],
                     showgrid=False, tickvals=[-2, -1, 0, 2, 4, 6, 8],
                     ticktext=[_pay_short(-2), _pay_short(-1), _pay_short(0), "2 m", "4 m", "6 m", "8 m"])
    return fig


# Fondo para SHAP: 40 clientes reales al azar (semilla fija). Se elige una sola vez al iniciar.
_SHAP_BG = None


def _shap_background():
    global _SHAP_BG
    if _SHAP_BG is None:
        _SHAP_BG = DF[INPUT_COLS].sample(40, random_state=42).to_dict("records")
    return _SHAP_BG


def shap_groups(values, key="xgboost"):
    """Valores de Shapley exactos (SHAP intervencional) por grupo de variables.

    Con 5 grupos hay 2^5 = 32 coaliciones. Para cada coalición S, v(S) es el puntaje medio cuando el
    cliente conserva sus valores en los grupos de S y toma los de cada cliente del fondo en el resto.
    phi_g = sum_S |S|!(5-|S|-1)!/5! [v(S + g) - v(S)]. Por construcción, base + sum(phi) = puntaje.
    """
    from itertools import combinations
    from math import factorial
    bg = _shap_background(); G = len(DRIVER_GROUPS)
    coal = [frozenset(c) for r in range(G + 1) for c in combinations(range(G), r)]
    rows = []
    for S in coal:
        keep = [c for g in S for c in DRIVER_GROUPS[g][1]]
        rows += [{**b, **{c: values[c] for c in keep}} for b in bg]
    p = predict_scores(rows, key).reshape(len(coal), len(bg)).mean(1)
    v = dict(zip(coal, p))
    phi = []
    for g in range(G):
        tot = 0.0
        for S in coal:
            if g in S:
                continue
            w = factorial(len(S)) * factorial(G - len(S) - 1) / factorial(G)
            tot += w * (v[S | {g}] - v[S])
        phi.append(tot)
    return v[frozenset()], np.array(phi), v[frozenset(range(G))]


def fig_drivers(values, score, key="xgboost"):
    """Barras SHAP por grupo de variables (puntos de riesgo frente al puntaje medio del fondo)."""
    base, phi, full = shap_groups(values, key)
    d = pd.DataFrame({"grupo": [L(g) for g, _ in DRIVER_GROUPS], "aporte": phi * 100})
    d = d.reindex(d["aporte"].abs().sort_values().index)
    fig = go.Figure(go.Bar(
        x=d["aporte"], y=d["grupo"], orientation="h",
        marker_color=[WARM_GOLD if v > 0 else NAVY for v in d["aporte"]],
        text=[f"{v:+.1f} pts" for v in d["aporte"]], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}: %{x:+.1f} " + tx("puntos (valor SHAP)", "points (SHAP value)") + "<extra></extra>"))
    lim = max(5, d["aporte"].abs().max() * 1.6)
    fig.add_vline(x=0, line_color=GREY_BLUE, line_width=1)
    style_fig(fig, 340, legend_top=False)
    fig.update_layout(margin=dict(l=150, r=30, t=34, b=46), showlegend=False,
                      title=dict(text=tx(f"Puntaje medio {base * 100:.1f} + aportes = {full * 100:.1f}",
                                         f"Average score {base * 100:.1f} + contributions = {full * 100:.1f}"),
                                 font=dict(size=13), x=0.5),
                      xaxis_title=tx("Puntos de riesgo que suma (+) o resta (−)", "Risk points added (+) or removed (−)"))
    fig.update_xaxes(range=[-lim, lim], zeroline=False)
    return fig


def conformal_block(score, key="xgboost"):
    """Conjunto de predicción conforme (90 %) a partir de los umbrales guardados en el .json del modelo."""
    cf = _meta(key).get("conformal")
    if not cf:
        return ""
    no, si = score <= cf["q0"], 1 - score <= cf["q1"]
    etiquetas = ([tx("no incumple", "no default")] if no else []) + ([tx("incumple", "default")] if si else [])
    txt = (tx("El modelo no puede decidir con 90 % de confianza.", "The model cannot decide with 90% confidence.")
           if len(etiquetas) == 2 else tx("Conjunto vacío (caso atípico).", "Empty set (unusual case).") if not etiquetas else "")
    return html.Div([
        html.B(tx("Conjunto de predicción (90 %): ", "Prediction set (90%): ")),
        html.Span("{" + ", ".join(etiquetas) + "}"), *([html.Br(), html.Span(txt)] if txt else []), html.Br(),
        html.Small(tx(f"Predicción conforme. Cobertura real {cf['cobertura_empirica']:.1%} en {cf['n_verificacion']:,} clientes de prueba. "
                      f"Bajo {cf['solo_no_incumple_si_p_menor_que']:.0%}: «no incumple»; sobre {cf['solo_incumple_si_p_mayor_que']:.0%}: "
                      f"«incumple»; entre ambos, las dos.",
                      f"Conformal prediction. Actual coverage {cf['cobertura_empirica']:.1%} on {cf['n_verificacion']:,} test clients. "
                      f"Below {cf['solo_no_incumple_si_p_menor_que']:.0%}: “no default”; above {cf['solo_incumple_si_p_mayor_que']:.0%}: "
                      f"“default”; in between, both."),
                   className="muted")], className="callout pf-conformal")


def fig_whatif(values, var, score, key="xgboost", thr=None):
    """Puntaje del cliente si solo cambiara una variable."""
    lbl, grid, xtitle = WHATIF[var]
    lbl, xtitle = L(lbl), L(xtitle)
    p = predict_scores([{**values, var: x} for x in grid], key) * 100
    thr = (_meta(key).get("umbral", 0.5) if thr is None else thr) * 100
    cur = values[var]
    is_pay = var == "PAY_0"
    xs = [_pay_short(x) if is_pay else x for x in grid]
    fig = go.Figure()
    fig.add_hrect(y0=thr, y1=100, fillcolor="rgba(184,143,61,0.10)", line_width=0)
    fig.add_trace(go.Scatter(x=xs, y=p, mode="lines+markers", line=dict(color=NAVY, width=3, shape="spline" if not is_pay else "linear"),
                             marker=dict(size=7, color=NAVY), name=lbl,
                             hovertemplate=f"{xtitle}: %{{x}}<br>{tx('Puntaje', 'Score')}: %{{y:.0f}}%<extra></extra>"))
    fig.add_trace(go.Scatter(x=[_pay_short(cur) if is_pay else cur], y=[score * 100], mode="markers+text",
                             marker=dict(symbol="star", size=20, color=PALE_GOLD, line=dict(width=1.5, color=GOLD_DARK)),
                             text=[tx("Este cliente", "This client")], textposition="top center",
                             textfont=dict(color=GOLD_DARK), name=tx("Este cliente", "This client"),
                             hovertemplate=tx("Este cliente", "This client") + ": %{y:.0f}%<extra></extra>"))
    fig.add_hline(y=thr, line_dash="dash", line_color=WARM_GOLD, line_width=1.5,
                  annotation_text=tx(f"Umbral {thr:.0f}%: por encima, «riesgo alto»",
                                     f"Threshold {thr:.0f}%: above it, “high risk”"), annotation_position="top left",
                  annotation_font_color=GOLD_MID)
    style_fig(fig, 360, legend_top=False)
    fig.update_layout(margin=dict(l=60, r=24, t=24, b=50), showlegend=False,
                      xaxis_title=xtitle, yaxis_title=tx("Puntaje de riesgo (%)", "Risk score (%)"))
    fig.update_yaxes(range=[0, 100], ticksuffix="%")
    if is_pay:
        fig.update_xaxes(type="category")
    elif var != "AGE":
        fig.update_xaxes(tickformat="~s")
    return fig


def _rec_thr(key):
    return _meta(key).get("umbral_ajustable", {}).get("recomendado", 0.5)
