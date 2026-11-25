# -*- coding: utf-8 -*-
"""Página Predecir: formulario, tarjeta de riesgo que se rompe según el puntaje y veredicto."""

from dash import dcc, html
from urllib.parse import quote

from tablero.componentes import (EDU_TILES, KEEP, MAR_TILES, SEX_TILES, _tbl, card, interp_block, page_title)
from tablero.config import L, tx
from tablero.datos import (BILL_COLS, DF, PAYAMT_COLS, month_lbl, pretty)
from tablero.iconos import icon
from tablero.prediccion import (
    BILL_CHRONO, MODELO, MODELOS, MODELO_ERROR, MODELO_META, MODEL_LABELS, PAYAMT_CHRONO, PAY_CHRONO,
    PROFILES, WHATIF, _meta, _mk, _rec_thr, conformal_block, tree_votes)


def _pf_field(label, comp, hint=None, cls=""):
    return html.Div([html.Label(label, htmlFor=getattr(comp, "id", None), className="ctl-label"), comp,
                     html.Div(hint, className="pf-hint") if hint else None], className=f"pf-field {cls}".strip())


def _num(id_, value, step="any", min_=None):
    return dcc.Input(id=f"pf-{id_}", type="number", value=value, step=step, min=min_, debounce=True,
                     className="pf-input", placeholder=pretty(id_), **KEEP)


def _tiles(id_, options, value):
    """Opciones como tarjetas con ícono (RadioItems con estilo)."""
    return dcc.RadioItems(
        id=f"pf-{id_}", value=value, className="pf-tiles", inputClassName="pf-tile-in", labelClassName="pf-tile",
        options=[{"label": html.Span([icon(ic, "pf-tile-ico"), html.Span(L(txt), className="pf-tile-txt")]), "value": v}
                 for v, txt, ic in options], **KEEP)


def _pay_slider(col, value):
    return dcc.Slider(id=f"pf-{col}", min=-2, max=8, step=1, value=value, included=False,
                      marks={i: {"label": str(i)} for i in range(-2, 9)}, className="pf-pay-slider",
                      allow_direct_input=False, **KEEP)


SERIALIZE_CODE = ("""import joblib

# 1) Entrenar y guardar (modelo/entrenar_extra.py)
modelo = pipeline("xgboost", spw).fit(X_tr, y_tr)  # Pipeline: variables + one-hot + XGBoost
joblib.dump(modelo, "modelo/modelo_xgboost.pkl", compress=3)

# 2) Cargar en el tablero (tablero/prediccion.py), una sola vez al arrancar
modelo = joblib.load("modelo/modelo_xgboost.pkl")

# 3) Predecir con los datos del formulario
cliente = pd.DataFrame([valores], columns=INPUT_COLS)
riesgo = modelo.predict_proba(cliente)[0, 1]  # puntaje de 0 a 1""",
                  """import joblib

# 1) Train and save (modelo/entrenar_extra.py)
modelo = pipeline("xgboost", spw).fit(X_tr, y_tr)  # Pipeline: features + one-hot + XGBoost
joblib.dump(modelo, "modelo/modelo_xgboost.pkl", compress=3)

# 2) Load in the dashboard (tablero/prediccion.py), once at startup
modelo = joblib.load("modelo/modelo_xgboost.pkl")

# 3) Predict with the form data
cliente = pd.DataFrame([valores], columns=INPUT_COLS)
riesgo = modelo.predict_proba(cliente)[0, 1]  # score from 0 to 1""")


def model_info_card():
    m = MODELO_META
    pr = m.get("prueba", {})
    hp = m.get("hiperparametros", {})
    ver = m.get("versiones", {})
    rows = [(tx("Modelo", "Model"), f"{m.get('modelo', '—')} · {m.get('balanceo', '')}"),
            (tx("Búsqueda", "Search"), m.get("busqueda", "—")),
            (tx("Hiperparámetros", "Hyperparameters"), ", ".join(f"{k} = {v}" for k, v in hp.items()) or "—"),
            (tx("Prueba (20 %)", "Test (20%)"),
             f"F1 {pr.get('f1', 0):.3f} · recall {pr.get('recall', 0):.3f} · {tx('precisión', 'precision')} "
             f"{pr.get('precision', 0):.3f} · ROC-AUC {pr.get('roc_auc', 0):.3f}" if pr else "—"),
            (tx("Entrenado", "Trained"), f"{m.get('n_entrenamiento', 0):,} {tx('clientes', 'clients')} · {m.get('fecha', '—')}"),
            (tx("Versiones", "Versions"), f"xgboost {ver.get('xgboost', '—')} · scikit-learn {ver.get('scikit-learn', '—')} · "
                                         f"joblib {ver.get('joblib', '—')}")]
    steps = [(tx("Entrenar", "Train"), tx("Se ajusta XGBoost con los datos históricos (modelo/entrenar_extra.py).",
                                          "XGBoost is fitted on the historical data (modelo/entrenar_extra.py)."), "tree"),
             (tx("Guardar", "Save"), tx("joblib.dump escribe el modelo en un archivo .pkl.",
                                        "joblib.dump writes the model to a .pkl file."), "save"),
             (tx("Cargar", "Load"), tx("El tablero lo lee con joblib.load al arrancar, sin reentrenar.",
                                       "The dashboard reads it with joblib.load at startup, without retraining."), "notebook"),
             (tx("Predecir", "Predict"), tx("Cada cambio del formulario llama a predict_proba.",
                                            "Every form change calls predict_proba."), "gauge")]
    return card(tx("Cómo se serializó el modelo", "How the model was serialized"), [
        html.P(tx("Serializar es guardar un modelo ya entrenado en un archivo para usarlo después sin volver a "
                  "entrenarlo. Así funciona esta sección:",
                  "Serializing means saving an already trained model to a file to use it later without retraining "
                  "it. This is how this section works:")),
        html.Div([html.Div([html.Span(f"{i + 1}", className="pf-step-n"), icon(ic, "pf-step-ico"),
                            html.B(t), html.P(d)], className="pf-step") for i, (t, d, ic) in enumerate(steps)],
                 className="pf-steps"),
        html.Details([html.Summary(tx("Ver el código", "Show the code")),
                      html.Pre(html.Code(L(SERIALIZE_CODE)), className="pf-code")], className="pf-details"),
        html.Div(_tbl([tx("Detalle", "Detail"), tx("Valor", "Value")], rows), className="table-wrap"),
    ])


def _flow():
    n = MODELO[-1].n_estimators if MODELO is not None else 0
    items = [("users", tx("1. Datos del cliente", "1. Client data"),
              tx("Perfil, pagos y montos de abril a septiembre.", "Profile, payments and amounts from April to September.")),
             ("layers", tx("2. Se transforman", "2. They are transformed"),
              tx("Logaritmos y resumen de las facturas, igual que en el proyecto.",
                 "Logarithms and bill summary, just as in the project.")),
             ("tree", tx(f"3. {n} árboles en cadena", f"3. {n} trees in a chain"),
              tx("XGBoost: cada árbol corrige los errores de los anteriores.",
                 "XGBoost: each tree corrects the errors of the previous ones.")),
             ("gauge", tx("4. Puntaje y decisión", "4. Score and decision"),
              tx("Se suman sus aportes; desde el umbral elegido es «riesgo alto».",
                 "Their contributions are added; from the chosen threshold it is “high risk”."))]
    out = []
    for i, (ic, t, d) in enumerate(items):
        out.append(html.Div([html.Span(icon(ic), className="pf-flow-ico"), html.Div([html.B(t), html.P(d)])],
                            className="pf-flow-item"))
        if i < len(items) - 1:
            out.append(html.Span(icon("chevron"), className="pf-flow-arrow"))
    return html.Div(out, className="pf-flow")


def page_predict():
    head = page_title(tx("Predecir", "Predict"), "")
    if MODELO is None:
        return html.Div([head, card(tx("El modelo no está disponible", "The model is not available"), [
            html.P([tx("No se encontró ", "Could not find "), html.Code("modelo/modelo_xgboost.pkl"),
                    tx(" o no se pudo cargar.", " or it could not be loaded.")]),
            html.P([tx("Para generarlo, desde la carpeta ", "To generate it, from the "), html.Code("dash/"),
                    tx(" ejecuta ", " folder run "), html.Code("python -m modelo.entrenar_extra xgboost"), "."]),
            html.P(MODELO_ERROR, className="muted")])])
    base = PROFILES["tipico"][1]
    gcfg = {"displaylogo": False, "displayModeBar": False}
    ml = month_lbl()
    k = tx("mil", "k")
    form = card(tx("Datos del cliente", "Client data"), [
        html.Div([html.Span(tx("Prueba un ejemplo:", "Try an example:"), className="pf-hint"),
                  *[html.Button([icon(ic), L(lbl)], id=f"pf-prof-{key}", n_clicks=0, className="btn ghost pf-prof",
                                type="button")
                    for (key, (lbl, _v)), ic in zip(PROFILES.items(), ["users", "target", "alert"])]],
                 className="pf-profiles"),
        html.H4([icon("users"), tx("Perfil", "Profile")], className="pf-h"),
        html.Div([
            _pf_field(tx("Cupo de crédito", "Credit limit"), dcc.Slider(
                id="pf-LIMIT_BAL", min=10000, max=1000000, step=10000, value=base["LIMIT_BAL"],
                marks={10000: f"10 {k}", 250000: f"250 {k}", 500000: f"500 {k}", 750000: f"750 {k}", 1000000: "1 M"},
                tooltip={"placement": "top", "always_visible": True, "template": "NT$ {value}"},
                className="pf-slider", allow_direct_input=False, **KEEP)),
            _pf_field(tx("Edad", "Age"), dcc.Slider(
                id="pf-AGE", min=21, max=79, step=1, value=base["AGE"],
                marks={i: str(i) for i in range(30, 80, 10)},
                tooltip={"placement": "top", "always_visible": True, "template": "{value} " + tx("años", "years")},
                className="pf-slider", allow_direct_input=False, **KEEP)),
        ], className="pf-grid pf-g2"),
        _pf_field(tx("Sexo", "Sex"), _tiles("SEX", SEX_TILES, base["SEX"])),
        html.P(tx("El dataset solo registra hombre y mujer; con «Otro» el modelo promedia ambas predicciones.",
                  "The dataset only records male and female; with “Other” the model averages both predictions."),
               className="pf-hint pf-note"),
        _pf_field(tx("Educación", "Education"), _tiles("EDUCATION", EDU_TILES, base["EDUCATION"]), cls="pf-row"),
        _pf_field(tx("Estado civil", "Marital status"), _tiles("MARRIAGE", MAR_TILES, base["MARRIAGE"]), cls="pf-row"),
        html.H4([icon("calendar"), tx("Estado de pago por mes (2005)", "Repayment status by month (2005)")],
                className="pf-h"),
        html.Div([html.Span(tx("−2 sin consumo", "−2 no use"), className="pf-key k-ok"),
                  html.Span(tx("−1 pagó todo", "−1 paid in full"), className="pf-key k-ok"),
                  html.Span(tx("0 pago mínimo", "0 minimum payment"), className="pf-key k-mid"),
                  html.Span(tx("1 a 8: meses de atraso", "1 to 8: months late"), className="pf-key k-late")],
                 className="pf-keys"),
        html.Div([html.Div([html.Span(m, className="pf-pay-m"), _pay_slider(c, base[c])], className="pf-pay-row")
                  for m, c in zip(ml, PAY_CHRONO)], className="pf-pay"),
        html.H4([icon("coin"), tx("Montos por mes (NT$)", "Amounts by month (NT$)")], className="pf-h"),
        html.Div(html.Div([
            html.Span(), *[html.Span(m, className="pf-mh") for m in ml],
            html.Span(tx("Facturado", "Billed"), className="pf-rh"), *[_num(c, base[c]) for c in BILL_CHRONO],
            html.Span(tx("Pagado", "Paid"), className="pf-rh"), *[_num(c, base[c], min_=0) for c in PAYAMT_CHRONO],
        ], className="pf-amounts"), className="table-wrap"),
    ], cls="pf-form")
    result = card(tx("Resultado", "Result"), [
        html.Div(id="pf-verdict"),
        html.Div(id="pf-trees"),
    ], cls="pf-result")
    selector = card(tx("Modelo", "Model"), [
        dcc.RadioItems(id="pf-model", value="xgboost", className="pf-tiles pf-seg", inputClassName="pf-tile-in",
                       labelClassName="pf-tile", options=[{"label": L(MODEL_LABELS[k]), "value": k} for k in MODELOS],
                       **KEEP),
        html.Div(id="pf-model-info", className="muted"),
        # Plegable: arranca cerrado y el resumen muestra el umbral elegido. El deslizador y las cifras siguen en el
        # DOM aunque esté cerrado (los oculta <details>), porque los callbacks de Predecir los usan.
        html.Details([
            html.Summary([icon("target"), html.Span(tx("Umbral de decisión", "Decision threshold"), className="thr-tt"),
                          html.Span(id="pf-thr-sum", className="thr-sum"),
                          html.Span(icon("chevron", "thr-chev"), className="ef-toggle", **{"aria-hidden": "true"})],
                         className="pf-h thr-summary"),
            dcc.Slider(id="pf-thr", min=0.05, max=0.95, step=0.01, value=_rec_thr("xgboost"),
                       marks={v: f"{v:.0%}" for v in (0.05, 0.25, 0.5, 0.75, 0.95)},
                       tooltip={"placement": "top", "always_visible": True, "transform": "pctFormat"},
                       className="pf-slider", **KEEP),
            html.Div(id="pf-thr-info", className="pf-thr-info"),
        ], id="pf-thr-fold", className="thr-fold"),
    ])
    return html.Div([
        head,
        _flow(),
        selector,
        html.Div([form, html.Div(result, className="pf-side")], className="pf-layout"),
        html.Div([
            card(tx("Historial del cliente", "Client history"), [
                dcc.Graph(id="pf-history", config=gcfg),
                interp_block(
                    tx("Las barras comparan lo que le facturaron con lo que pagó cada mes; la línea dorada muestra su "
                       "estado de pago. Cuando la línea sube por encima de 0 hay atraso, y cuando las barras doradas "
                       "son mucho más bajas que las azules, el cliente está pagando poco de su deuda.",
                       "The bars compare what was billed with what was paid each month; the gold line shows the "
                       "repayment status. When the line rises above 0 there is a delay, and when the gold bars are "
                       "much lower than the blue ones, the client is paying little of their debt."),
                    tx("El modelo no usa las seis facturas por separado: las resume en nivel medio (log con signo), "
                       "tendencia mensual y número de meses con saldo a favor, como en el proyecto. Los estados de "
                       "pago (PAY_0 … PAY_6) sí entran uno por uno y son las variables más importantes según SHAP.",
                       "The model does not use the six bills separately: it summarizes them as average level (signed "
                       "log), monthly trend and number of months with a credit balance, as in the project. The "
                       "repayment statuses (PAY_0 … PAY_6) do enter one by one and are the most important variables "
                       "according to SHAP.")),
            ]),
            card(tx("¿Qué empuja su riesgo? (SHAP)", "What drives their risk? (SHAP)"), [
                dcc.Graph(id="pf-drivers", config=gcfg),
                interp_block(
                    tx("Cada barra es el valor SHAP de un grupo de variables: cuántos puntos de riesgo suma (dorado) o "
                       "resta (azul) frente al puntaje medio de 40 clientes reales. El título muestra que el puntaje medio "
                       "más todos los aportes da exactamente el puntaje del cliente.",
                       "Each bar is the SHAP value of a group of variables: how many risk points it adds (gold) or "
                       "removes (blue) compared with the average score of 40 real clients. The title shows that the "
                       "average score plus all contributions gives exactly the client's score."),
                    tx("Valores de Shapley exactos por grupo (SHAP intervencional): con 5 grupos se evalúan las 32 "
                       "coaliciones posibles, cada una promediada sobre los 40 clientes de fondo (1,280 predicciones). "
                       "Se agrupa por tema porque las variables de un mismo grupo (por ejemplo, los seis estados de pago) "
                       "están muy correlacionadas, y repartir el aporte entre ellas una por una sería inestable.",
                       "Exact Shapley values by group (interventional SHAP): with 5 groups the 32 possible coalitions "
                       "are evaluated, each averaged over the 40 background clients (1,280 predictions). Variables are "
                       "grouped by topic because those in the same group (for example, the six repayment statuses) are "
                       "highly correlated, and splitting the contribution among them one by one would be unstable.")),
            ]),
        ], className="grid g2"),
        card(tx("¿Qué pasaría si…?", "What if…?"), [
            dcc.RadioItems(id="pf-whatif-var", value="PAY_0", className="pf-tiles pf-seg", inputClassName="pf-tile-in",
                           labelClassName="pf-tile", options=[{"label": L(v[0]), "value": key} for key, v in WHATIF.items()],
                           **KEEP),
            dcc.Graph(id="pf-whatif", config=gcfg),
            interp_block(
                tx("La línea muestra el puntaje que tendría este mismo cliente si solo cambiara la variable elegida; "
                   "la estrella es su situación actual. Por ejemplo, con «Atraso en septiembre» se ve cuánto sube el "
                   "riesgo con cada mes de atraso.",
                   "The line shows the score this same client would have if only the chosen variable changed; the "
                   "star is their current situation. For example, with “September delay” you can see how much the "
                   "risk rises with each month of delay."),
                tx("Es una curva de dependencia individual (ICE): se fija el resto de variables y se recorre una sola. "
                   "En los modelos de árboles la curva tiene escalones porque cada árbol corta la variable en umbrales; no implica "
                   "causalidad, solo describe cómo responde el modelo.",
                   "It is an individual conditional expectation (ICE) curve: the other variables are fixed and only one "
                   "is varied. In tree models the curve has steps because each tree splits the variable at thresholds; "
                   "it does not imply causality, it only describes how the model responds.")),
        ]),
        model_info_card(),
    ])


def trees_block(values, key="xgboost"):
    yes, n = tree_votes(values, key)
    bosque = _mk(key) == "cs_fof"
    share = yes / n if n else 0
    cells = int(round(share * 100))
    return html.Div([
        html.Div([icon("tree"), html.B(tx(f"{yes} de {n} árboles votan «incumple»",
                                          f"{yes} of {n} trees vote “default”") if bosque else
                                       tx(f"{yes} de {n} árboles empujan hacia «incumple»",
                                          f"{yes} of {n} trees push toward “default”"))], className="pf-trees-h"),
        html.Div([html.Span(className="pf-cell" + (" on" if i < cells else "")) for i in range(100)],
                 className="pf-waffle", title=tx(f"{share:.0%} de los árboles", f"{share:.0%} of the trees")),
        html.P(tx("Cada cuadro es 1 % del bosque. El puntaje promedia las probabilidades de todos los árboles, "
                  "por eso puede diferir un poco de esta proporción.",
                  "Each square is 1% of the forest. The score averages the probabilities of all the trees, so it "
                  "may differ slightly from this proportion.") if bosque else
               tx("Cada cuadro es 1 % de los árboles. En XGBoost los árboles trabajan en cadena: cada uno corrige a "
                  "los anteriores y suma o resta un poco al puntaje. Como no todos pesan lo mismo, el puntaje puede "
                  "diferir de esta proporción.",
                  "Each square is 1% of the trees. In XGBoost the trees work in a chain: each one corrects the "
                  "previous ones and adds or subtracts a little from the score. Since they do not all weigh the same, "
                  "the score may differ from this proportion."), className="muted"),
    ], className="pf-trees")


# ---------- Tarjeta de riesgo: una tarjeta de crédito que se rompe por la mitad según el puntaje ----------
# Coordenadas en un lienzo de 160 x 100 (proporción de una tarjeta). Una sola fractura, de arriba abajo:
#   < 30 %  intacta · 30–50 %  la fractura crece desde el centro · 50–92 %  la tarjeta se abre por ella.
RC_SPLIT = [(98.7, 0.0), (101.9, 14.0), (101.9, 29.0), (104.0, 44.0), (107.2, 58.0), (108.9, 72.0),
            (111.5, 86.0), (110.7, 100.0)]
RC_CENTER_Y = 44.0                 # desde aquí crece la fractura, hacia arriba y hacia abajo
RC_CRACK_FROM = 0.30               # aparece la fractura
RC_SPLIT_FROM = 0.50               # (umbral) la tarjeta empieza a abrirse
RC_SPLIT_FULL = 0.92               # abierta del todo (el 1 % más riesgoso del dataset)


def _rc_path(pts):
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)


def _rc_x_at(y):
    """x de la fractura a la altura y (interpolación entre sus puntos)."""
    for (x0, y0), (x1, y1) in zip(RC_SPLIT, RC_SPLIT[1:]):
        if y0 <= y <= y1:
            return x0 + (x1 - x0) * (y - y0) / (y1 - y0)
    return RC_SPLIT[-1][0]


def _rc_svg(score, thr=RC_SPLIT_FROM):
    """SVG (data URI) con la parte visible de la fractura para este puntaje."""
    crack_from = max(thr - (RC_SPLIT_FROM - RC_CRACK_FROM), 0.01)
    t = min(max((score - crack_from) / (thr - crack_from), 0), 1)
    if t <= 0:
        return "none"
    top, bot = RC_CENTER_Y * (1 - t), RC_CENTER_Y + (100 - RC_CENTER_Y) * t
    pts = [(_rc_x_at(top), top)] + [(x, y) for x, y in RC_SPLIT if top < y < bot] + [(_rc_x_at(bot), bot)]
    d = _rc_path(pts)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 100" preserveAspectRatio="none">'
           f'<path d="{d}" fill="none" stroke="rgba(5,8,20,.6)" stroke-width="1.4" '
           'stroke-linecap="round" stroke-linejoin="round"/>'
           f'<path d="{d}" fill="none" stroke="rgba(255,255,255,.8)" stroke-width=".6" '
           'stroke-linecap="round" stroke-linejoin="round"/></svg>')
    return f'url("data:image/svg+xml,{quote(svg)}")'


def _rc_clip(side):
    """clip-path de cada pedazo, siguiendo la fractura principal."""
    line = [f"{x / 1.6:.1f}% {y:.1f}%" for x, y in RC_SPLIT]
    if side == "l":
        return "polygon(0% 0%, " + ", ".join(line) + ", 0% 100%)"
    return "polygon(100% 0%, " + ", ".join(line) + ", 100% 100%)"


def risk_card(score, thr):
    """Veredicto como tarjeta de crédito: intacta con riesgo bajo; con riesgo alto se rompe y se abre."""
    high = score >= thr
    full = max(RC_SPLIT_FULL, min(thr + 0.05, 1.0))
    k = min(max((score - thr) / (full - thr), 0), 1)   # cuánto se separan los pedazos (desde el umbral)
    title = (tx("Riesgo alto: probable incumplimiento", "High risk: likely default") if high
             else tx("Riesgo bajo: probable pago", "Low risk: likely to pay"))
    cracks = _rc_svg(score, thr)

    def face(clip, hidden=False):
        return html.Div([
            html.Div(className="cc-gloss"),
            html.Div([html.Span(tx("Riesgo de crédito", "Credit risk"), className="cc-brand"),
                      icon("contactless", "cc-nfc")], className="cc-top"),
            html.Div([html.Div(className="cc-chip rc-chip"),
                      html.Div([html.Span(tx("Puntaje de riesgo", "Risk score"), className="cc-lbl"),
                                html.Div(f"{score:.0%}", className="rc-score")])], className="rc-mid"),
            html.Div([html.Div([html.Span(tx("Veredicto", "Verdict"), className="cc-lbl"),
                                html.Div(title, className="rc-verdict")]),
                      html.Div([html.Span(tx("Umbral", "Threshold"), className="cc-lbl"),
                                html.Div(f"{thr:.0%}", className="cc-name")],
                               className="cc-valid")], className="cc-bottom"),
            html.Div(className="rc-cracks", style={"backgroundImage": cracks}),
        ], className="cc-face rc-face", style={"clipPath": clip}, **({"aria-hidden": "true"} if hidden else {}))

    # el recorte va en la cara y la sombra en el pedazo, así la sombra sigue la forma rota
    left_style = {"transform": f"translate({-12 * k:.1f}px, {5 * k:.1f}px) rotate({-3.5 * k:.2f}deg)"}
    right_style = {"visibility": "visible" if k > 0 else "hidden",
                   "transform": f"translate({12 * k:.1f}px, {-3 * k:.1f}px) rotate({4.5 * k:.2f}deg)"}
    heat = min(max((score - 0.3) / 0.6, 0), 1)
    return html.Div([
        html.Div(face(_rc_clip("l") if k > 0 else "none"), className="rc-piece", style=left_style),
        html.Div(face(_rc_clip("r"), hidden=True), className="rc-piece", style=right_style),
    ], className="rc " + ("hi" if high else "lo") + (" split" if k > 0 else ""),
        style={"--heat": f"{heat:.3f}"}, role="img",
        **{"aria-label": tx(f"{title}. Puntaje {score:.0%}, umbral {thr:.0%}.",
                            f"{title}. Score {score:.0%}, threshold {thr:.0%}.")})


def threshold_stats(key, thr):
    """Recall, precisión y falsas alarmas del umbral elegido, medidos en la mitad de verificación de la prueba."""
    curva = _meta(key).get("umbral_ajustable", {}).get("curva", [])
    return min(curva, key=lambda c: abs(c["umbral"] - thr)) if curva else {}


def predict_verdict(values, score, key="xgboost", thr=None):
    thr = _meta(key).get("umbral", 0.5) if thr is None else thr
    pr = threshold_stats(key, thr)
    late = [m for m, c in zip(month_lbl(), PAY_CHRONO) if (values.get(c) or 0) >= 1]
    signals = []
    if (values.get("PAY_0") or 0) >= 1:
        n = values["PAY_0"]
        signals.append(("alert", tx(f"{n} {'mes' if n == 1 else 'meses'} de atraso en septiembre: la señal que más "
                                    "pesa en el modelo.",
                                    f"{n} {'month' if n == 1 else 'months'} late in September: the signal that "
                                    "weighs most in the model.")))
    elif late:
        signals.append(("calendar", tx(f"Tuvo atrasos en {', '.join(late)}, aunque en septiembre está al día.",
                                       f"Was late in {', '.join(late)}, although up to date in September.")))
    else:
        signals.append(("target", tx("Sin atrasos en los seis meses.", "No delays in the six months.")))
    bills = sum(values.get(c) or 0 for c in BILL_COLS)
    paid = sum(values.get(c) or 0 for c in PAYAMT_COLS)
    if bills > 0:
        signals.append(("coin", tx(f"Pagó el {min(paid / bills, 9.99):.0%} de lo facturado en el periodo.",
                                   f"Paid {min(paid / bills, 9.99):.0%} of the amount billed in the period.")))
    q = (DF["LIMIT_BAL"] < (values.get("LIMIT_BAL") or 0)).mean()
    signals.append(("card", tx(f"Su cupo supera al de {q:.0%} de los clientes.",
                               f"Their limit is higher than that of {q:.0%} of clients.")))
    return html.Div([
        html.Div(risk_card(score, thr), className="rc-wrap"),
        html.Ul([html.Li([icon(ic), html.Span(s)]) for ic, s in signals], className="pf-signals"),
        conformal_block(score, key),
        html.Details([html.Summary(tx("¿Cómo leer el puntaje?", "How to read the score?")), html.P(
            (tx(f"Con el umbral de {thr:.0%} el modelo detecta {pr.get('recall', 0):.0%} de quienes incumplen y acierta en "
                f"{pr.get('precision', 0):.0%} de los clientes que marca como riesgosos (datos de prueba). ",
                f"With the {thr:.0%} threshold the model detects {pr.get('recall', 0):.0%} of defaulters and is right about "
                f"{pr.get('precision', 0):.0%} of the clients it flags as risky (test data). ") if pr else "")
            + tx("No es una probabilidad calibrada: el modelo se entrenó con pesos de clase, que lo hacen sobrestimar "
                 "el riesgo frente a la tasa real (22 %). Sirve para ordenar y clasificar clientes.",
                 "It is not a calibrated probability: the model was trained with class weights, which make it "
                 "overestimate the risk compared with the real rate (22%). It is useful to rank and classify clients."))],
            className="pf-details"),
    ])
