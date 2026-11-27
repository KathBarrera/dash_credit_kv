# -*- coding: utf-8 -*-
"""Página Modelo original (CS-FOF): teoría visual, comparación con su rival, metodología y código."""

import numpy as np
import plotly.graph_objects as go
from dash import dcc, html

from tablero.componentes import (_tbl, card, control, interp_block, kpi, page_title)
from tablero.config import (
    BASE_DIR, CREAM, DEEP_NAVY, DEEP_RGBA, GREY_BLUE, L, PALE_GOLD, REPO_PROJECT, WARM_GOLD, WHITE, tx)
from tablero.datos import DF, TARGET
from tablero.eda_multi import CORR
from tablero.glosario import CSFOF, HIB, V, eqv_hint, fx
from tablero.iconos import icon, zoom_btn
from tablero.paginas.mejoras import csfof_beyond
from tablero.resultados import CSFOF_CM, minfo
from tablero.utilidades import GLOBAL_RATE, style_fig


# ----- Modelo original CS-FOF (experiments/comparacion_final del proyecto) -----
# Pruebas de CS-FOF frente a la mejor combinación de cada modelo de referencia (5 folds externos; Holm sobre 7
# comparaciones; experiments/paper/pruebas_cs_fof.csv y comparacion_final/ del proyecto)
CSFOF_TESTS = [  # (rival, diferencia F1, folds ganados, p Nadeau-Bengio Holm, delta de Cliff, p DeLong, McNemar)
    ("xgboost", 0.0014, 4, 0.627, 0.36, "0.561", "434 / 827"),
    ("random_forest", 0.0027, 4, 0.619, 0.36, "0.171", "313 / 615"),
    ("svm", 0.0092, 5, 0.010, 0.76, "—", "—"),
    ("knn", 0.0216, 5, 0.034, 0.92, "—", "—"),
    ("decision_tree", 0.0225, 5, 0.003, 1.00, "—", "—"),
    ("logistic_regression", 0.0297, 5, 0.010, 1.00, "—", "—"),
    ("naive_bayes", 0.0493, 5, 0.0002, 1.00, "—", "—"),
]
# F1 de la mejor configuración en Taiwán y en los tres conjuntos adicionales (pesos de clase, búsqueda aleatoria)
CROSS_DATA = [  # (modelo, taiwan, german, australian, polish, rango medio entre los 8 modelos)
    ("xgboost", 0.547, 0.599, 0.880, 0.682, 2.00), ("random_forest", 0.545, 0.600, 0.874, 0.446, 3.00),
    ("cs_fof", 0.548, 0.589, 0.874, 0.430, 3.25),
]


# ----- Teoría visual de CS-FOF: corte recto frente a corte oblicuo con clientes reales -----
# Dos variables de este conjunto (límite de crédito y monto pagado en septiembre, en log10). Se compara
# el mejor corte recto (una variable), un árbol clásico de 3 niveles (hasta 7 cortes rectos) y un solo
# corte en la dirección de Fisher ponderada por costo, que es lo que CS-FOF evalúa en cada nodo.
def _csfof_toy():
    from sklearn.tree import DecisionTreeClassifier
    a = np.log10(DF["LIMIT_BAL"].to_numpy(float))
    b = np.log10(DF["PAY_AMT1"].clip(lower=0).to_numpy(float) + 1)
    y = DF[TARGET].to_numpy(int)
    X = np.column_stack([a, b])
    c = (y == 0).sum() / (y == 1).sum()                 # costo del moroso, como en CS-FOF
    w = np.where(y == 1, c, 1.0)

    def gini(wt, pw):                                   # Gini ponderado
        p = pw / wt
        return 2 * p * (1 - p)

    W, P = w.sum(), (w * y).sum()
    g0 = gini(W, P)

    def mejor_corte(z):
        o = np.argsort(z, kind="stable"); zs, cw, cp = z[o], np.cumsum(w[o]), np.cumsum((w * y)[o])
        best, thr = 0.0, None
        for q in np.unique(np.quantile(zs, np.linspace(.02, .98, 97))):
            i = np.searchsorted(zs, q, side="right")
            if i < 50 or i > len(zs) - 50:
                continue
            wl, pl = cw[i - 1], cp[i - 1]
            g = g0 - wl / W * gini(wl, pl) - (W - wl) / W * gini(W - wl, P - pl)
            if g > best:
                best, thr = g, q
        return best, thr

    g_axis = max(mejor_corte(a)[0], mejor_corte(b)[0])
    mu, sd = X.mean(0), X.std(0)
    Z = (X - mu) / sd
    m1 = np.average(Z[y == 1], axis=0, weights=w[y == 1]); m0 = Z[y == 0].mean(0)
    Sw = np.cov(Z[y == 1].T) + np.cov(Z[y == 0].T) + 0.1 * np.eye(2)
    v = np.linalg.solve(Sw, m1 - m0)                    # dirección de Fisher
    g_obl, t_obl = mejor_corte(Z @ v)

    def fisher_en(idx):                                 # corte de Fisher dentro de un nodo (para 3 cortes)
        yy, ww, zz = y[idx], w[idx], Z[idx]
        mm1 = np.average(zz[yy == 1], axis=0, weights=ww[yy == 1])
        vv = np.linalg.solve(np.cov(zz[yy == 1].T) + np.cov(zz[yy == 0].T) + 0.1 * np.eye(2), mm1 - zz[yy == 0].mean(0))
        s = zz @ vv; Wn, Pn = ww.sum(), (ww * yy).sum(); best, th = 0.0, np.inf
        for q in np.unique(np.quantile(s, np.linspace(.02, .98, 97))):
            L_ = s <= q
            if L_.sum() < 200 or (~L_).sum() < 200:
                continue
            g = (gini(Wn, Pn) - ww[L_].sum() / Wn * gini(ww[L_].sum(), (ww * yy)[L_].sum())
                 - ww[~L_].sum() / Wn * gini(ww[~L_].sum(), (ww * yy)[~L_].sum()))
            if g > best:
                best, th = g, q
        return s <= th

    def ganancia(leaf):
        return g0 - sum(w[leaf == L_].sum() / W * gini(w[leaf == L_].sum(), (w * y)[leaf == L_].sum())
                        for L_ in np.unique(leaf))

    hojas = np.zeros(len(y), int); izq = fisher_en(np.arange(len(y))); hojas[~izq] = 1
    for k in (0, 1):
        s_ = np.flatnonzero(hojas == k); hojas[s_[~fisher_en(s_)]] = 10 + k
    g_obl3 = ganancia(hojas)
    g_axis3 = ganancia(DecisionTreeClassifier(max_depth=2, min_samples_leaf=200, class_weight={0: 1.0, 1: c},
                                              random_state=42).fit(X, y).apply(X))
    tree = DecisionTreeClassifier(max_depth=3, min_samples_leaf=200, class_weight={0: 1.0, 1: c},
                                  random_state=42).fit(X, y)
    leaf = tree.apply(X)
    g_tree = ganancia(leaf)
    n_cuts = int((tree.tree_.children_left != -1).sum())
    # segmentos de cada corte recto del árbol, dentro de la región de su nodo (la «escalera»)
    tr, segs = tree.tree_, []

    def recorrer(n, x0, x1, y0, y1):
        if tr.children_left[n] == -1:
            return
        f, th = tr.feature[n], tr.threshold[n]
        if f == 0:
            segs.append(((th, th), (y0, y1))); recorrer(tr.children_left[n], x0, th, y0, y1)
            recorrer(tr.children_right[n], th, x1, y0, y1)
        else:
            segs.append(((x0, x1), (th, th))); recorrer(tr.children_left[n], x0, x1, y0, th)
            recorrer(tr.children_right[n], x0, x1, th, y1)
    recorrer(0, a.min(), a.max(), 0.0, b.max())
    gx = np.linspace(a.min(), a.max(), 220); gy = np.linspace(0, b.max(), 220)
    GX, GY = np.meshgrid(gx, gy)
    G = np.column_stack([GX.ravel(), GY.ravel()])
    reg_tree = tree.predict(G).reshape(GX.shape)
    reg_obl = ((((G - mu) / sd) @ v) > t_obl).astype(int).reshape(GX.shape)
    rng = np.random.default_rng(42)
    idx = np.concatenate([rng.choice(np.flatnonzero(y == k), 1300, replace=False) for k in (0, 1)])
    jit = rng.normal(0, 0.03, (len(idx), 2))
    return dict(a=a[idx] + jit[:, 0], b=b[idx] + jit[:, 1], y=y[idx], gx=gx, gy=gy, reg_tree=reg_tree,
                reg_obl=reg_obl, segs=segs, g_axis=g_axis, g_tree=g_tree, g_obl=g_obl, g_axis3=g_axis3, g_obl3=g_obl3, n_cuts=n_cuts, c=c,
                v=v / np.abs(v).max())


CS_TOY = _csfof_toy()


def fig_csfof_toy(kind):
    """Clientes reales; región sombreada = donde el corte predice «incumple»."""
    T = CS_TOY
    reg = T["reg_tree"] if kind == "tree" else T["reg_obl"]
    fig = go.Figure(go.Heatmap(x=T["gx"], y=T["gy"], z=reg, showscale=False, hoverinfo="skip", zsmooth=False,
                               colorscale=[[0, "rgba(0,0,0,0)"], [1, f"{DEEP_RGBA}0.13)"]]))
    for k, col, name in ((0, GREY_BLUE, tx("Paga", "Pays")), (1, WARM_GOLD, tx("Incumple", "Defaults"))):
        m = T["y"] == k
        fig.add_trace(go.Scattergl(x=T["a"][m], y=T["b"][m], mode="markers", name=name,
                                   marker=dict(size=4, color=col, opacity=.55 if k == 0 else .75),
                                   hoverinfo="skip"))
    if kind == "tree":   # cada corte recto del árbol como un segmento
        for sx, sy in T["segs"]:
            fig.add_trace(go.Scatter(x=list(sx), y=list(sy), mode="lines", showlegend=False, hoverinfo="skip",
                                     line=dict(color=DEEP_NAVY, width=2.2)))
    else:
        fig.add_trace(go.Contour(x=T["gx"], y=T["gy"], z=reg, showscale=False, hoverinfo="skip",
                                 contours=dict(start=.5, end=.5, size=1, coloring="none"),
                                 line=dict(color=DEEP_NAVY, width=2.4), showlegend=False))
    style_fig(fig, 360)
    fig.update_layout(margin=dict(l=70, r=16, t=40, b=55))
    fig.update_xaxes(title=tx("Límite de crédito (NT$)", "Credit limit (NT$)"),
                     tickvals=[4, np.log10(3e4), 5, np.log10(3e5), 6], ticktext=["10k", "30k", "100k", "300k", "1M"])
    fig.update_yaxes(title=tx("Pagó en septiembre (NT$)", "Paid in September (NT$)"),
                     tickvals=[0, 2, 3, 4, 5, 6], ticktext=["0", "100", "1k", "10k", "100k", "1M"])
    return fig


def _cs_step(n, title, body, formula=None):
    return html.Div([html.Span(str(n), className="cs-num"), html.H4(title), html.P(body),
                     fx(formula) if formula else None],
                    className="cs-step")


def csfof_theory():
    T = CS_TOY
    rho_pay = CORR.loc["PAY_0", "PAY_2"]
    bill = [f"BILL_AMT{i}" for i in range(1, 7)]
    bmin = DF[bill].corr(method="spearman").values[np.triu_indices(6, 1)].min()
    gcfg = {"displaylogo": False, "displayModeBar": False}
    mejora = T["g_obl"] / T["g_axis"] - 1
    return [card(tx("La idea en una imagen", "The idea in one picture"), [
        html.P(tx("Cada punto es un cliente real. Un árbol clásico solo puede cortar en línea recta sobre una variable "
                  "a la vez, así que para separar a quienes incumplen arma una escalera de cortes. Pero el riesgo no "
                  "depende del límite o del pago por separado, sino de la combinación de ambos: es una frontera en "
                  "diagonal. CS-FOF puede trazarla con un solo corte.",
                  "Each point is a real client. A classic tree can only cut in a straight line on one variable at a "
                  "time, so to separate defaulters it builds a staircase of cuts. But risk does not depend on the limit "
                  "or the payment separately; it depends on their combination: a diagonal boundary. CS-FOF can draw it "
                  "with a single cut.")),
        html.Div([
            html.Div([html.Div(tx(f"Árbol clásico: {T['n_cuts']} cortes rectos", f"Classic tree: {T['n_cuts']} straight cuts"),
                              className="cs-fig-t"),
                      dcc.Graph(id="cs-toy-tree", figure=fig_csfof_toy("tree"), config=gcfg)]),
            html.Div([html.Div(tx("CS-FOF: 1 corte oblicuo", "CS-FOF: 1 oblique cut"), className="cs-fig-t on"),
                      dcc.Graph(id="cs-toy-obl", figure=fig_csfof_toy("oblique"), config=gcfg)]),
        ], className="grid g2"),
        html.P(tx("¿Cuánto separa cada opción? Reducción de impureza (Gini ponderado) con el mismo número de cortes:",
                  "How much does each option separate? Impurity reduction (weighted Gini) with the same number of cuts:"),
               className="muted"),
        html.Div([
            kpi(tx("Con 1 corte", "With 1 cut"), f"+{mejora:.0%}",
                tx(f"oblicuo {T['g_obl']:.4f} frente a recto {T['g_axis']:.4f}",
                   f"oblique {T['g_obl']:.4f} vs straight {T['g_axis']:.4f}"), "target"),
            kpi(tx("Con 3 cortes", "With 3 cuts"), f"+{T['g_obl3'] / T['g_axis3'] - 1:.0%}",
                tx(f"oblicuos {T['g_obl3']:.4f} frente a rectos {T['g_axis3']:.4f}",
                   f"oblique {T['g_obl3']:.4f} vs straight {T['g_axis3']:.4f}"), "layers"),
            kpi(tx(f"{T['n_cuts']} cortes rectos", f"{T['n_cuts']} straight cuts"), f"{T['g_tree']:.4f}",
                tx("la escalera ya alcanza a la diagonal", "the staircase catches up with the diagonal"), "bars"),
        ], className="kpi-row k3"),
        html.Div(tx("La ventaja del corte oblicuo es grande cuando hay pocos cortes y se achica a medida que la escalera "
                    "de cortes rectos se acerca a la diagonal. Un bosque completo tiene miles de cortes; por eso, en los "
                    "resultados, CS-FOF empata con los mejores modelos en vez de superarlos con amplitud.",
                    "The oblique cut's advantage is large when there are few cuts and shrinks as the staircase of "
                    "straight cuts approaches the diagonal. A full forest has thousands of cuts; that is why, in the "
                    "results, CS-FOF ties with the best models instead of clearly beating them."), className="callout"),
        interp_block(
            tx("La zona sombreada es donde cada modelo diría «incumple». El árbol necesita varios escalones para "
               "seguir la diagonal; el corte oblicuo la sigue de una vez: menos límite y menos pago, más riesgo.",
               "The shaded area is where each model would say “defaults”. The tree needs several steps to follow the "
               "diagonal; the oblique cut follows it at once: lower limit and lower payment, higher risk."),
            tx(f"Variables en log10, 29 965 clientes; se muestran 2 600 al azar (mitad de cada clase). Dirección de "
               f"Fisher (estandarizada) ∝ ({T['v'][0]:+.2f}, {T['v'][1]:+.2f}). Pesos de costo c = n₀/n₁ = {T['c']:.2f}. "
               "El árbol clásico es CART con profundidad 3, hoja mínima 200 y los mismos pesos. Es una ilustración "
               "en 2 variables; en el modelo real cada nodo usa √p variables al azar.",
               f"Variables in log10, 29,965 clients; 2,600 shown at random (half of each class). Fisher direction "
               f"(standardized) ∝ ({T['v'][0]:+.2f}, {T['v'][1]:+.2f}). Cost weights c = n₀/n₁ = {T['c']:.2f}. The "
               "classic tree is CART with depth 3, minimum leaf 200 and the same weights. It is a 2-variable "
               "illustration; in the real model each node uses √p random variables.")),
    ]), card(tx("Cómo decide cada nodo", "How each node decides"), [
        html.Div([
            _cs_step(1, tx("Cortes rectos", "Straight cuts"),
                     tx("Como en Random Forest, prueba umbrales sobre √p variables elegidas al azar.",
                        "As in Random Forest, it tries thresholds on √p randomly chosen variables.")),
            _cs_step(2, tx("Dirección de Fisher con costo", "Cost-weighted Fisher direction"),
                     tx("Con los clientes de ese nodo calcula la combinación de variables que mejor separa a las dos "
                        "clases, pesando más a quienes incumplen.",
                        "With the clients in that node it computes the combination of variables that best separates "
                        "the two classes, giving more weight to defaulters."),
                     r"\mathbf{v}=S_w^{-1}(\mu_1-\mu_0)"),
            _cs_step(3, tx("Se queda con el mejor", "Keeps the best one"),
                     tx("Compara todos los cortes con el Gini ponderado y elige el que más lo reduce. Por eso el corte "
                        "elegido nunca es peor que el mejor corte recto (Proposición 1).",
                        "It compares all cuts with the weighted Gini and picks the one that reduces it most. That is "
                        "why the chosen cut is never worse than the best straight cut (Proposition 1)."),
                     r"\Delta G(\text{elegido})\ \ge\ \max_j \Delta G(\text{recto}_j)"),
        ], className="cs-steps"),
    ]), card(tx("Por qué encaja con estos datos", "Why it fits this data"), [
        html.Div([
            kpi(tx("Atrasos correlacionados", "Correlated delays"), f"ρ = {rho_pay:.2f}",
                tx("PAY_0 con PAY_2: el riesgo vive en combinaciones", "PAY_0 with PAY_2: risk lives in combinations"), "layers"),
            kpi(tx("Montos redundantes", "Redundant amounts"), f"ρ ≥ {bmin:.2f}",
                tx("entre BILL_AMT1 a BILL_AMT6 (VIF > 20)", "among BILL_AMT1 to BILL_AMT6 (VIF > 20)"), "columns"),
            kpi(tx("Desbalance", "Imbalance"), f"{GLOBAL_RATE:.1%}",
                tx(f"incumple; cada moroso pesa {T['c']:.1f} veces más", f"default; each defaulter weighs {T['c']:.1f}× more"), "alert"),
            kpi(tx("Cortes oblicuos usados", "Oblique cuts used"), "71 %",
                tx("de los nodos del modelo final; quitarlos baja el F1", "of the final model's nodes; removing them lowers F1"), "target"),
        ], className="kpi-row k4"),
        html.Div(tx("Lo que la teoría no garantiza: la Proposición 1 asegura que cada corte es al menos tan bueno como "
                    "el mejor corte recto en los datos de entrenamiento, no que el bosque completo prediga mejor en "
                    "clientes nuevos que métodos como XGBoost. Eso solo lo dicen las pruebas estadísticas "
                    "(pestaña 4).",
                    "What the theory does not guarantee: Proposition 1 ensures each cut is at least as good as the best "
                    "straight cut on the training data, not that the whole forest predicts new clients better than "
                    "methods like XGBoost. Only the statistical tests can say that (tab 4)."),
                 className="callout"),
    ])]


# ----- CS-FOF frente al rival que se elija (Random Forest es su versión sin cortes oblicuos ni costo por nodo) -----
# Pliegues: validación anidada 5 x 5, mejor combinación de cada modelo (experiments/comparacion_final/mejor_por_modelo.csv).
# Datos y ruido: experiments/robustez/ del proyecto (exploratorio; hiperparámetros fijos por pliegue).
CS_RIVALS = ["random_forest", "xgboost"]
CS_VS = {
    "folds": dict(x=["1", "2", "3", "4", "5"], v={
        "cs_fof": ([0.5484, 0.5447, 0.5441, 0.5572, 0.5453], None),
        "random_forest": ([0.5510, 0.5404, 0.5375, 0.5556, 0.5417], None),
        "xgboost": ([0.5478, 0.5428, 0.5403, 0.5619, 0.5399], None)}),
    "size": dict(x=["10 %", "25 %", "50 %", "100 %"], v={
        "cs_fof": ([0.5356, 0.5429, 0.5473, 0.5483], [0.0073, 0.0065, 0.0073, 0.0078]),
        "random_forest": ([0.5375, 0.5415, 0.5405, 0.5434], [0.0091, 0.0084, 0.0093, 0.0076]),
        "xgboost": ([0.5244, 0.5370, 0.5392, 0.5448], [0.0088, 0.0089, 0.0076, 0.0087])}),
    "noise": dict(x=["0 %", "5 %", "10 %", "20 %"], v={
        "cs_fof": ([0.5483, 0.5455, 0.5455, 0.5336], [0.0078, 0.0081, 0.0085, 0.0147]),
        "random_forest": ([0.5434, 0.5423, 0.5414, 0.5303], [0.0076, 0.0085, 0.0109, 0.0148]),
        "xgboost": ([0.5448, 0.5430, 0.5401, 0.5252], [0.0087, 0.0065, 0.0090, 0.0111])}),
}
_CSRF_X = {"folds": ("Pliegue externo", "Outer fold"), "size": ("Datos de entrenamiento usados", "Training data used"),
           "noise": ("Etiquetas de entrenamiento invertidas", "Training labels flipped")}
_RIVAL_DESC = {
    "random_forest": ("Random Forest es el modelo básico más parecido: CS-FOF es un Random Forest al que se le agregó el "
                      "corte oblicuo con costo, así que esta comparación aísla lo que aporta la idea nueva.",
                      "Random Forest is the most similar basic model: CS-FOF is a Random Forest with the cost-sensitive "
                      "oblique cut added, so this comparison isolates what the new idea contributes."),
    "xgboost": ("XGBoost es la mejor de las 112 combinaciones del diseño factorial del Entregable 2: es el rival más exigente.",
                "XGBoost is the best of the 112 combinations of the Deliverable 2 factorial design: it is the toughest rival."),
}


def _rival(r):
    return r if r in CS_RIVALS else "random_forest"


def fig_cs_vs_rf(scn, rival="random_forest"):
    """Líneas que se dibujan punto por punto (botón de reproducir) con la diferencia en cada paso."""
    rival = _rival(rival)
    D = CS_VS[scn]
    n, xs = len(D["x"]), D["x"]
    cs, cs_sd = D["v"]["cs_fof"]
    rv, rv_sd = D["v"][rival]
    rname = minfo(rival, "label")
    allv = cs + rv
    pad = 0.012 if cs_sd else 0.006
    yr = [min(allv) - pad, max(allv) + pad]
    series = [("CS-FOF", cs, cs_sd, WARM_GOLD, "diamond"), (rname, rv, rv_sd, DEEP_NAVY, "circle")]

    # etiqueta arriba para el que va ganando en ese punto y abajo para el otro (no se enciman)
    arriba = [a >= b for a, b in zip(cs, rv)]
    pos = {"CS-FOF": ["top center" if u else "bottom center" for u in arriba],
           rname: ["bottom center" if u else "top center" for u in arriba]}

    def trazas(k):
        out = []
        for name, v, sd, col, sym in series:
            out.append(go.Scatter(
                x=xs[:k], y=v[:k], mode="lines+markers+text", name=name,
                text=[f"{z:.3f}" for z in v[:k]], textposition=pos[name][:k],
                textfont=dict(size=11, color=col),
                line=dict(color=col, width=3), marker=dict(size=12, symbol=sym, color=col, line=dict(width=1.5, color=WHITE)),
                error_y=dict(type="data", array=sd[:k], color=col, thickness=1.2, width=4, visible=True) if sd else None,
                hovertemplate=f"<b>{name}</b><br>%{{x}}<br>F1: %{{y:.4f}}<extra></extra>"))
        return out

    def nota(k):
        d = cs[k - 1] - rv[k - 1]
        if abs(d) < 5e-5:
            txt = tx(f"<b>{xs[k - 1]}</b>: empate", f"<b>{xs[k - 1]}</b>: tie")
        else:
            quien = "CS-FOF" if d > 0 else rname
            txt = tx(f"<b>{xs[k - 1]}</b>: gana {quien} por {abs(d):.4f}", f"<b>{xs[k - 1]}</b>: {quien} wins by {abs(d):.4f}")
        return [dict(xref="paper", yref="paper", x=0.0, y=1.22, showarrow=False, xanchor="left", yanchor="bottom",
                     font=dict(size=13, color=WARM_GOLD if d > 0 else DEEP_NAVY), text=txt)]

    # nombres únicos por escenario y rival: así una animación en curso no se mezcla con la nueva
    tag = f"{scn}-{rival}"
    frames = [go.Frame(data=trazas(k), name=f"{tag}-{k}", layout=go.Layout(annotations=nota(k))) for k in range(1, n + 1)]
    fig = go.Figure(data=trazas(n), frames=frames)
    style_fig(fig, 400)
    play = dict(label=tx("▶ Reproducir", "▶ Play"), method="animate",
                args=[None, dict(frame=dict(duration=900, redraw=True), transition=dict(duration=450, easing="cubic-in-out"),
                                 fromcurrent=False, mode="immediate")])
    fig.update_layout(
        annotations=nota(n), margin=dict(l=60, r=20, t=100, b=95), uirevision=tag,
        xaxis=dict(title=L(_CSRF_X[scn]), type="category", categoryorder="array", categoryarray=xs, range=[-0.4, n - 0.6]),
        yaxis=dict(title=tx("F1 de la clase default", "F1 of the default class"), range=yr),
        updatemenus=[dict(type="buttons", showactive=False, x=0, y=-0.22, xanchor="left", yanchor="top",
                          bgcolor=CREAM, bordercolor=PALE_GOLD, font=dict(color=DEEP_NAVY), buttons=[play])],
        sliders=[dict(active=n - 1, x=0.2, len=0.8, y=-0.17, yanchor="top", pad=dict(t=0),
                      currentvalue=dict(visible=False), font=dict(color=GREY_BLUE),
                      steps=[dict(label=xs[k - 1], method="animate",
                                  args=[[f"{tag}-{k}"], dict(mode="immediate", frame=dict(duration=0, redraw=True),
                                                       transition=dict(duration=300))]) for k in range(1, n + 1)])])
    return fig


def cs_vs_rf_interp(scn, rival="random_forest"):
    rival = _rival(rival)
    D = CS_VS[scn]
    cs, _ = D["v"]["cs_fof"]
    rv, _ = D["v"][rival]
    rname = minfo(rival, "label")
    xs = D["x"]
    gana = sum(a > b for a, b in zip(cs, rv))
    dif = float(np.mean(np.array(cs) - np.array(rv)))
    lead = L(_RIVAL_DESC[rival]) + " "
    if scn == "folds":
        if dif >= 0:
            basic = tx(f"CS-FOF le gana a {rname} en {gana} de 5 pliegues, con {dif:.4f} de F1 más en promedio: menos "
                       "que lo que cambia el F1 de un pliegue a otro.",
                       f"CS-FOF beats {rname} in {gana} of 5 folds, with {dif:.4f} more F1 on average: less than F1 "
                       "changes from one fold to another.")
        else:
            basic = tx(f"CS-FOF le gana a {rname} solo en {gana} de 5 pliegues y queda {abs(dif):.4f} de F1 por debajo en "
                       "promedio: en la práctica, un empate.",
                       f"CS-FOF beats {rname} in only {gana} of 5 folds and is {abs(dif):.4f} of F1 below on average: "
                       "in practice, a tie.")
        t = next(row for row in CSFOF_TESTS if row[0] == rival)
        tech = tx(f"Validación anidada 5 × 5, mejor combinación de cada uno. Nadeau-Bengio con Holm p = {t[3]:.3f}; "
                  f"δ de Cliff = {t[4]:+.2f}; DeLong p = {t[5]}; McNemar (errores exclusivos CS-FOF / {rname}): {t[6]}. "
                  "Ninguna prueba de superioridad es significativa.",
                  f"Nested 5 × 5 validation, best combination of each. Nadeau-Bengio with Holm p = {t[3]:.3f}; "
                  f"Cliff's δ = {t[4]:+.2f}; DeLong p = {t[5]}; McNemar (exclusive errors CS-FOF / {rname}): {t[6]}. "
                  "No superiority test is significant.")
    elif scn == "size":
        donde = ", ".join(x for x, a, b in zip(xs, cs, rv) if a > b) or tx("ninguno", "none")
        basic = tx(f"CS-FOF queda arriba de {rname} en {gana} de 4 tamaños ({donde}). Con 10 % de los datos pierde "
                   f"{cs[-1] - cs[0]:.3f} de F1 frente a {rv[-1] - rv[0]:.3f} de {rname}: calcular la dirección de Fisher "
                   "en cada nodo necesita suficientes clientes.",
                   f"CS-FOF is above {rname} in {gana} of 4 sizes ({donde}). With 10% of the data it loses "
                   f"{cs[-1] - cs[0]:.3f} of F1 versus {rv[-1] - rv[0]:.3f} for {rname}: computing the Fisher direction "
                   "at each node needs enough clients.")
        tech = tx("Exploratorio: fracción estratificada del entrenamiento de cada pliegue, prueba completa, "
                  "hiperparámetros elegidos en la validación anidada (sin búsqueda nueva). Barras: ± 1 desviación "
                  "estándar entre los 5 pliegues. Sin pruebas de hipótesis.",
                  "Exploratory: stratified fraction of each fold's training set, full test set, hyperparameters chosen "
                  "in the nested validation (no new search). Bars: ± 1 standard deviation across the 5 folds. No "
                  "hypothesis tests.")
    else:
        basic = tx(f"Al ensuciar las etiquetas de entrenamiento, CS-FOF queda arriba de {rname} en {gana} de 4 niveles. "
                   f"Con 20 % de ruido pierde {cs[0] - cs[-1]:.3f} de F1 y {rname} {rv[0] - rv[-1]:.3f}.",
                   f"When the training labels are corrupted, CS-FOF is above {rname} at {gana} of 4 levels. With 20% "
                   f"noise it loses {cs[0] - cs[-1]:.3f} of F1 and {rname} {rv[0] - rv[-1]:.3f}.")
        tech = tx("Exploratorio: se invierte al azar una fracción de las etiquetas de entrenamiento (la misma para todos "
                  "los modelos); la prueba es limpia. Barras: ± 1 desviación estándar entre pliegues; si se solapan, la "
                  "diferencia no es concluyente.",
                  "Exploratory: a random fraction of training labels is flipped (the same for all models); the test set "
                  "is clean. Bars: ± 1 standard deviation across folds; if they overlap, the difference is not "
                  "conclusive.")
    return interp_block(lead + basic, tech)


# ----- Metodología y código de CS-FOF (estructura de la «Guía de redacción metodológica» del curso) -----
CSFOF_DIR = BASE_DIR / "modelo" / "cs_fof"
CSFOF_SRC = (CSFOF_DIR / "original_model.py").read_text(encoding="utf-8")
CSFOF_TESTS_SRC = (CSFOF_DIR / "test_original_model.py").read_text(encoding="utf-8")
CSFOF_URL = REPO_PROJECT + "/blob/main/src/original_model.py"
CSFOF_TESTS_URL = REPO_PROJECT + "/blob/main/tests/test_original_model.py"


def _py_seg(src, name):
    """Código fuente de una función o clase de nivel superior (se lee del archivo real)."""
    import ast
    for node in ast.parse(src).body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name:
            return ast.get_source_segment(src, node)
    raise KeyError(name)


def _py_between(src, start, end):
    """Líneas desde la que contiene `start` hasta antes de la que contiene `end`, sin sangría común."""
    import textwrap
    lines = src.splitlines()
    i = next(k for k, ln in enumerate(lines) if start in ln)
    j = next(k for k in range(i + 1, len(lines)) if end in lines[k])
    return textwrap.dedent("\n".join(lines[i:j])).rstrip()


def py_code(src, scope=None):
    """Bloque de código Python con colores de sintaxis (tokenize de la librería estándar, sin dependencias)."""
    import io, keyword, tokenize
    lines = src.splitlines(keepends=True)
    offs = [0]
    for ln in lines:
        offs.append(offs[-1] + len(ln))
    out, pos, prev = [], 0, None
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return html.Pre(html.Code(src), className="pf-code cs-code", **({"data-scope": scope} if scope else {}))
    for tk in toks:
        if tk.type in (tokenize.ENDMARKER,):
            continue
        a = offs[tk.start[0] - 1] + tk.start[1]
        b = offs[tk.end[0] - 1] + tk.end[1]
        if a > pos:
            out.append(src[pos:a])
        s = src[a:b]
        cls = None
        if tk.type == tokenize.COMMENT:
            cls = "hl-com"
        elif tk.type == tokenize.STRING:
            cls = "hl-str"
        elif tk.type == tokenize.NUMBER:
            cls = "hl-num"
        elif tk.type == tokenize.NAME:
            if keyword.iskeyword(s):
                cls = "hl-kw"
            elif prev in ("def", "class"):
                cls = "hl-def"
            elif s in ("np", "self", "True", "False", "None"):
                cls = "hl-bi"
        out.append(html.Span(s, className=cls) if cls else s)
        if tk.type == tokenize.NAME:
            prev = s
        elif tk.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT):
            prev = None
        pos = b
    out.append(src[pos:])
    return html.Pre(html.Code(out), className="pf-code cs-code", **({"data-scope": scope} if scope else {}))


# ----- Ecuaciones en el código: cada ecuación se muestra justo antes de las líneas que la implementan -----
CSFOF_LINES = CSFOF_SRC.splitlines()


def _linea(patron, desde=1):
    """Número de línea (desde 1) de la primera línea del archivo, a partir de `desde`, que contiene `patron`."""
    for k in range(desde - 1, len(CSFOF_LINES)):
        if patron in CSFOF_LINES[k]:
            return k + 1
    raise KeyError(patron)


def _gh(a, b=None):
    """Enlace a esas líneas de original_model.py en GitHub."""
    return CSFOF_URL + f"#L{a}" + (f"-L{b}" if b and b != a else "")


def _rango(a, b):
    return f"{a}" if a == b else f"{a}–{b}"


def _hl_line(linea):
    """Una línea con colores de sintaxis; un fragmento suelto (docstring, línea de continuación) queda sin colores."""
    sangria = linea[:len(linea) - len(linea.lstrip())]
    resto = py_code(linea.lstrip()).children.children
    return [sangria] + (resto if isinstance(resto, list) else [resto])


def _code_rows(a, b, hl=False):
    """Líneas a..b del archivo; hl resalta las que implementan la ecuación."""
    partes = []
    for k, ln in enumerate(CSFOF_LINES[a - 1:b]):
        partes += (["\n"] if k else []) + _hl_line(ln)
    return html.Div(html.Pre(html.Code(partes), className="pf-code cs-code", **{"data-scope": CSFOF}),
                    className="cs-code-rows" + (" hl" if hl else ""))


def _eq_en_codigo(num, tex, que, a, b):
    """La ecuación, lo que hace esa parte del código y el enlace a sus líneas."""
    return html.Div([
        html.Div(f"({num})", className="cs-eq-n"),
        html.Div([fx(tex),
                  html.P([html.B(tx(f"Líneas {_rango(a, b)}: ", f"Lines {_rango(a, b)}: ")), que, " · ",
                          html.A(tx("ver en GitHub", "see on GitHub"), href=_gh(a, b), target="_blank",
                                 rel="noopener noreferrer")], className="cs-eq-why")], className="cs-eq-body"),
    ], className="cs-eq cs-eqc")


def _card_eq_codigo(titulo, nota, segmentos):
    """Tarjeta con el código de original_model.py y cada ecuación insertada justo antes de su línea.

    segmentos: [(subtítulo o None, línea inicial, línea final, [(patrón, n_líneas, número, tex, qué hace), ...])].
    """
    hijos = [html.P(nota, className="muted")]
    for sub, a, b, marcas in segmentos:
        if sub:
            hijos.append(html.H4([sub, html.Span(tx(f" · líneas {_rango(a, b)}", f" · lines {_rango(a, b)}"),
                                                 className="muted")], className="cs-code-sub"))
        bloque, pos = [], a
        for patron, n, num, tex, que in marcas:
            l = _linea(patron, pos)
            if l > pos:
                bloque.append(_code_rows(pos, l - 1))
            bloque.append(_eq_en_codigo(num, tex, que, l, l + n - 1))
            bloque.append(_code_rows(l, l + n - 1, hl=True))
            pos = l + n
        if pos <= b:
            bloque.append(_code_rows(pos, b))
        hijos.append(html.Div(bloque, className="cs-code-eqs"))
    return card(titulo, hijos)


def _lineas_eq():
    """Dónde está cada ecuación de la metodología en original_model.py: {número: (línea inicial, línea final)}."""
    return {
        1: (_linea("n1 = max(int(y.sum()), 1)"), _linea("return np.where(y == 1, n0 / n1, 1.0)")),
        2: (_linea("pL = np.where(WL > 0"), _linea("return WL * 2 * pL * (1 - pL)")),
        3: (_linea("D = Xs - np.where(y[:, None] == 1"), _linea("Sw += (eps * traza")),
        4: (_linea("V = np.linalg.solve(Sw"), _linea("V /= np.linalg.norm(V")),
        5: (_linea("valor[ids_nivel[k]] = W1[k] / W[k]"), _linea("p1 = np.mean([a.proba1(Z)")),
    }


def _eq(n, tex, why):
    """Ecuación numerada con la razón de ser del componente y las líneas del código que la implementan."""
    a, b = _lineas_eq()[n]
    donde = (tx(f"líneas {a} y {b} de original_model.py", f"lines {a} and {b} of original_model.py") if n == 5
             else tx(f"líneas {_rango(a, b)} de original_model.py", f"lines {_rango(a, b)} of original_model.py"))
    return html.Div([
        zoom_btn(),   # modo foco de cada ecuación (assets/card_focus.js)
        html.Div(f"({n})", className="cs-eq-n"),
        html.Div([fx(tex),
                  html.P([html.B(tx("Por qué: ", "Why: ")), *(why if isinstance(why, list) else [why])], className="cs-eq-why"),
                  html.P([html.B(tx("En el código: ", "In the code: ")), donde, " (",
                          tx("pestaña 3 · Código", "tab 3 · Code"), " · ",
                          html.A("GitHub", href=_gh(a, b) if n != 5 else _gh(a), target="_blank",
                                 rel="noopener noreferrer"), ")"], className="cs-eq-why")], className="cs-eq-body"),
    ], className="cs-eq eq-zoom")


METH_FLOW = [  # (título, texto) — los 8 pasos de la guía, aplicados a este proyecto
    (("Formulación", "Formulation"), ("Clasificación binaria f: ℝ²⁰ → {0, 1}; 1 = incumple el pago del mes siguiente.",
                                      "Binary classification f: ℝ²⁰ → {0, 1}; 1 = defaults next month.")),
    (("Datos", "Data"), ("UCI Taiwán: 29 965 clientes, 20 variables, 22.1 % de incumplimiento. Preprocesamiento dentro de cada pliegue.",
                         "UCI Taiwan: 29,965 clients, 20 variables, 22.1% default. Preprocessing inside each fold.")),
    (("Modelo propuesto", "Proposed model"), ("Bosque con cortes oblicuos de Fisher ponderados por costo (ecuaciones 1 a 5).",
                                              "Forest with cost-weighted Fisher oblique cuts (equations 1 to 5).")),
    (("Entrenamiento", "Training"), ("4 búsquedas de hiperparámetros (malla, aleatoria, Optuna, genético); semilla 42.",
                                     "4 hyperparameter searches (grid, random, Optuna, genetic); seed 42.")),
    (("Baselines", "Baselines"), ("Los 7 modelos de referencia exigidos, con el mismo presupuesto de búsqueda.",
                                  "The 7 required baseline models, with the same search budget.")),
    (("Evaluación", "Evaluation"), ("Validación anidada 5 × 5; F1, AUC-ROC, AUC-PR, MCC; Friedman, Nadeau-Bengio, Wilcoxon, DeLong.",
                                    "Nested 5 × 5 validation; F1, ROC-AUC, PR-AUC, MCC; Friedman, Nadeau-Bengio, Wilcoxon, DeLong.")),
    (("Ablación", "Ablation"), ("Mismo bosque sin corte oblicuo y variantes del corte, con todo lo demás fijo.",
                                "Same forest without the oblique cut and variants of the cut, all else fixed.")),
    (("Reproducibilidad", "Reproducibility"), ("Código en GitHub (MIT), 14 pruebas en GitHub Actions, datos de UCI.",
                                               "Code on GitHub (MIT), 14 tests on GitHub Actions, UCI data.")),
]

PSEUDO = """Entrada: D = {(xᵢ, yᵢ)}, T árboles, profundidad d, hoja mínima h, q variables, ε
1  wᵢ ← c·1{yᵢ = 1} + 1{yᵢ = 0},  c = n₀ / n₁                      ▷ ec. (1)
2  para t = 1, …, T:
3      tomar una muestra bootstrap y crecer el árbol por niveles
4      para cada nodo con ≥ 2h clientes, sin ser puro y con profundidad < d:
5          F ← q variables al azar
6          mejor ← el corte recto sobre F de menor G                ▷ ec. (2)
7          v ← dirección de Fisher con los clientes del nodo        ▷ ec. (3) y (4)
8          si el mejor umbral sobre vᵀx tiene menor G: mejor ← oblicuo
9          si mejor deja ≥ h clientes por lado: dividir; si no: hoja
10 f(x) ← promedio de las probabilidades de hoja de los T árboles  ▷ ec. (5)"""

ABLATION = [  # ablación en los 5 pliegues externos (experiments/paper/ablacion_pruebas.csv del proyecto)
    (("CS-FOF completo", "Full CS-FOF"), "0.5483 ± 0.0078", ("Referencia", "Reference")),
    (("Sin corte oblicuo", "Without oblique cut"), "0.5460 ± 0.0082",
     ("−0.0024, peor en 4 de 5 pliegues; p ajustado 0.40: no significativo",
      "−0.0024, worse in 4 of 5 folds; adjusted p 0.40: not significant")),
    (("Dirección con todas las variables (q = p)", "Direction with all variables (q = p)"), "0.5443 ± 0.0104",
     ("−0.0040, peor en 4 de 5 pliegues; p ajustado 0.27: no significativo",
      "−0.0040, worse in 4 of 5 folds; adjusted p 0.27: not significant")),
    (("Sin costo (c = 1)", "Without cost (c = 1)"), "0.4773 ± 0.0124",
     ("−0.071 en los 5 pliegues; p ajustado 0.001: el costo es clave para el F1",
      "−0.071 in all 5 folds; adjusted p 0.001: the cost is key for F1")),
]

CHECKLIST = [  # lista de verificación de la guía; estado honesto
    ("ok", ("La tarea, la pérdida y la notación están definidas formalmente.", "Task, loss and notation are formally defined.")),
    ("ok", ("Particiones antes de cualquier ajuste; imputación, escalado y SMOTE dentro de cada pliegue (sin fuga).",
            "Splits before any fitting; imputation, scaling and SMOTE inside each fold (no leakage).")),
    ("ok", ("El modelo tiene diagrama, ecuaciones, pseudocódigo y complejidad.", "The model has a diagram, equations, pseudocode and complexity.")),
    ("ok", ("Modelos de referencia con el mismo presupuesto de búsqueda.",
            "Baseline models with the same search budget.")),
    ("ok", ("Media y desviación estándar sobre 5 pliegues externos.", "Mean and standard deviation over 5 outer folds.")),
    ("ok", ("Pruebas estadísticas: Friedman-Nemenyi, Nadeau-Bengio, Wilcoxon con Holm, DeLong y McNemar.",
            "Statistical tests: Friedman-Nemenyi, Nadeau-Bengio, Wilcoxon with Holm, DeLong and McNemar.")),
    ("mid", ("Ablación por componente en los 5 pliegues externos, con 3 de las 4 variantes previstas (falta «solo cortes oblicuos»).",
             "Ablation per component on the 5 outer folds, with 3 of the 4 planned variants (“oblique cuts only” is missing).")),
    ("ok", ("Código, datos y versiones disponibles (GitHub, UCI, requirements.txt); DOI de Zenodo pendiente.",
            "Code, data and versions available (GitHub, UCI, requirements.txt); Zenodo DOI pending.")),
    ("ok", ("Figuras del artículo en PDF vectorial, en inglés, desde un solo script.", "Paper figures in vector PDF, in English, from one script.")),
]


def csfof_method():
    flow = html.Div([html.Div([html.Span(str(i + 1), className="cs-num"), html.B(L(tt)), html.P(L(dd))],
                              className="cs-flow-item") for i, (tt, dd) in enumerate(METH_FLOW)], className="cs-flow")
    eqs = [
        _eq(1, r"w_i = c\,\mathbb{1}\{y_i=1\}+\mathbb{1}\{y_i=0\},\quad c=\frac{n_0}{n_1}",
            tx(["con 22 % de morosos, no detectar a uno cuesta más que una falsa alarma; ", V("c"), " ≈ 3.5 iguala el peso total de las dos clases."],
               ["with 22% defaulters, missing one costs more than a false alarm; ", V("c"), " ≈ 3.5 equalizes the total weight of both classes."])),
        _eq(2, r"G(L,R)=W_L\,2p_L(1-p_L)+W_R\,2p_R(1-p_R),\quad p_A=\frac{\sum_{i\in A}w_iy_i}{\sum_{i\in A}w_i}",
            tx(["un solo criterio (", V("G"), "), con los mismos pesos ", V("w_i"), ", para comparar con justicia cortes rectos y oblicuos."],
               ["a single criterion (", V("G"), "), with the same weights ", V("w_i"), ", to compare straight and oblique cuts fairly."])),
        _eq(3, r"S_w=\frac{1}{\sum_i w_i}\sum_i w_i(\mathbf{x}_{i,F}-\mu_{y_i})(\mathbf{x}_{i,F}-\mu_{y_i})^\top+\varepsilon\,\frac{\operatorname{tr}S}{q}\,I_q",
            tx(["los montos facturados son casi colineales y los nodos profundos tienen pocos clientes: ", V("ε"), " evita que ", V("S_w"), " sea casi singular."],
               ["billed amounts are nearly collinear and deep nodes have few clients: ", V("ε"), " keeps ", V("S_w"), " from being nearly singular."])),
        _eq(4, r"\mathbf{v}=\frac{S_w^{-1}(\mu_1-\mu_0)}{\lVert S_w^{-1}(\mu_1-\mu_0)\rVert}",
            tx([V("v"), " es la dirección que mejor separa a las dos clases en el nodo (Proposición 2), calculada solo con sus clientes."],
               [V("v"), " is the direction that best separates the two classes in the node (Proposition 2), computed only with its clients."])),
        _eq(5, r"f(\mathbf{x})=\frac1T\sum_{t=1}^{T}\hat p_t(\mathbf{x}),\quad \hat p_{\text{hoja}}=\frac{\sum_{i\in\text{hoja}}w_iy_i}{\sum_{i\in\text{hoja}}w_i}",
            tx(["promediar los ", V("T"), " árboles, entrenados con muestras bootstrap distintas, reduce la varianza, como en Random Forest."],
               ["averaging the ", V("T"), " trees, trained on different bootstrap samples, reduces variance, as in Random Forest."])),
    ]
    hp = _tbl([tx("Hiperparámetro", "Hyperparameter"), tx("Rango buscado", "Search range"), tx("Modelo final", "Final model")],
              [("n_estimators (T)", "100-500", "359"), ("max_depth (d)", "6-14", "11"),
               ("min_samples_leaf (h)", "10-60", "51"), ("max_features (q)", "sqrt, log2", "log2"),
               ("eps (ε)", tx("0.01 a 1 (escala log)", "0.01 to 1 (log scale)"), "0.324")])
    nuevo = _tbl([tx("Se reutiliza", "Reused"), tx("Es nuevo en CS-FOF", "New in CS-FOF")], [
        (tx("Bosque aleatorio: bootstrap, q variables al azar por nodo y promedio de árboles (Breiman, 2001).",
            "Random forest: bootstrap, q random variables per node and averaging of trees (Breiman, 2001)."),
         tx("La regla de partición: una dirección de Fisher local, ponderada por costo, que compite con los cortes rectos.",
            "The split rule: a local, cost-weighted Fisher direction that competes with straight cuts.")),
        (tx("La idea de cortes oblicuos (Murthy et al., 1994; Menze et al., 2011).",
            "The idea of oblique cuts (Murthy et al., 1994; Menze et al., 2011)."),
         tx("Ambos tipos de corte se evalúan con el mismo Gini ponderado por costo, así el corte oblicuo nunca empeora un nodo.",
            "Both cut types are scored with the same cost-weighted Gini, so the oblique cut never worsens a node.")),
        (tx("El discriminante lineal de Fisher (1936).", "Fisher's linear discriminant (1936)."),
         tx("Su aplicación a la predicción de incumplimiento en tarjetas de crédito (sin antecedentes en Web of Science ni Scopus).",
            "Its application to credit card default prediction (no precedent in Web of Science or Scopus).")),
    ])
    abl = _tbl([tx("Variante", "Variant"), tx("F1 (5 pliegues)", "F1 (5 folds)"), tx("Lectura", "Reading")],
               [(L(a), (html.B(f) if i == 0 else f), L(r)) for i, (a, f, r) in enumerate(ABLATION)])
    check = html.Ul([html.Li([html.Span("✓" if s == "ok" else "◐", className=f"cs-chk {s}"), html.Span(L(txt))])
                     for s, txt in CHECKLIST], className="cs-checklist")
    return [
        card(tx("Flujo de la metodología", "Methodology flow"), [
            html.P(tx("Sigue los ocho pasos de la guía de redacción metodológica del curso, aplicados a este proyecto.",
                      "It follows the eight steps of the course's methodology writing guide, applied to this project."),
                   className="muted"),
            flow]),
        card(tx("Modelo propuesto: ecuaciones", "Proposed model: equations"), [
            html.P(tx("Datos D = {(xᵢ, yᵢ)}, i = 1…n, con xᵢ ∈ ℝᵖ y yᵢ ∈ {0, 1}. Cada componente lleva su justificación.",
                      "Data D = {(xᵢ, yᵢ)}, i = 1…n, with xᵢ ∈ ℝᵖ and yᵢ ∈ {0, 1}. Each component comes with its justification."),
                   className="muted"),
            eqv_hint(),
            *eqs]),
        card(tx("Pseudocódigo", "Pseudocode"), [html.Pre(PSEUDO, className="pf-code cs-pseudo")]),
        html.Div([
            card(tx("Propiedades y complejidad", "Properties and complexity"), [html.Ul([
                html.Li([html.B(tx("Proposición 1. ", "Proposition 1. ")),
                         tx("El corte elegido nunca tiene más impureza que el mejor corte recto sobre las mismas variables.",
                            "The chosen cut never has more impurity than the best straight cut on the same variables.")]),
                html.Li([html.B(tx("Proposición 2. ", "Proposition 2. ")),
                         tx("Con ε = 0, v maximiza el criterio de Fisher J(u) = (uᵀ(μ₁ − μ₀))² / uᵀS_w u (Cauchy-Schwarz).",
                            "With ε = 0, v maximizes Fisher's criterion J(u) = (uᵀ(μ₁ − μ₀))² / uᵀS_w u (Cauchy-Schwarz).")]),
                html.Li([html.B(tx("Proposición 3. ", "Proposition 3. ")),
                         tx("Cada árbol termina y tiene a lo sumo ⌊n/h⌋ hojas.", "Each tree terminates and has at most ⌊n/h⌋ leaves.")]),
                html.Li([html.B(tx("Tiempo. ", "Time. ")),
                         tx("Entrenar un árbol cuesta O(d·n(q log n + q²)); predecir un cliente, O(T·d·p).",
                            "Training one tree costs O(d·n(q log n + q²)); predicting one client, O(T·d·p).")]),
                html.Li([html.B(tx("Memoria. ", "Memory. ")),
                         tx("Cada nodo guarda q coeficientes y un umbral; el modelo final pesa 5 MB.",
                            "Each node stores q coefficients and a threshold; the final model weighs 5 MB.")]),
                html.Li([html.B(tx("Verificación. ", "Verification. ")),
                         tx("Las tres proposiciones se comprueban con pruebas unitarias (pestaña Código).",
                            "The three propositions are checked with unit tests (Code tab).")]),
            ], className="cs-props")]),
            card(tx("Entrenamiento y optimización", "Training and optimization"), [
                html.P(tx("Los 5 hiperparámetros se buscan con los mismos 4 métodos y presupuesto que los demás modelos "
                          "(malla de 32, 25 aleatorias, 30 de Optuna y genético 16 × 10), dentro de la validación anidada.",
                          "The 5 hyperparameters are searched with the same 4 methods and budget as the other models "
                          "(grid of 32, 25 random, 30 Optuna and genetic 16 × 10), inside the nested validation."),
                       className="muted"), hp]),
        ], className="grid g2"),
        card(tx("Qué es nuevo y qué se reutiliza", "What is new and what is reused"), [nuevo]),
        card(tx("Diseño del estudio de ablación", "Ablation study design"), [
            html.P(tx("Cada variante cambia un solo componente y mantiene todo lo demás fijo. Se evaluó en los 5 pliegues "
                      "externos de la validación anidada 5 × 5, con los hiperparámetros de CS-FOF de cada pliegue; F1 como "
                      "media ± desviación y t corregida de Nadeau–Bengio con Holm. Antes, en la etapa de diseño, 14 pruebas "
                      "con el entrenamiento del pliegue 1 solo sirvieron para fijar los rangos de búsqueda.",
                      "Each variant changes a single component and keeps everything else fixed. It was evaluated on the 5 "
                      "outer folds of the 5 × 5 nested validation, with CS-FOF's hyperparameters of each fold; F1 as mean ± "
                      "standard deviation and Nadeau–Bengio corrected t with Holm. Earlier, at the design stage, 14 tests on "
                      "the training set of fold 1 only served to set the search ranges."),
                   className="muted"), abl]),
        card(tx("Lista de verificación de la guía", "Guide checklist"), [
            check,
            html.Div(tx("✓ cumplido · ◐ parcial. Los puntos parciales se declaran como desviaciones en el protocolo del proyecto.",
                        "✓ done · ◐ partial. Partial items are declared as deviations in the project protocol."), className="muted")]),
    ]


def csfof_code():
    n_lines = len(CSFOF_SRC.splitlines())
    L1 = _linea
    eq1 = r"w_i = c\,\mathbb{1}\{y_i=1\}+\mathbb{1}\{y_i=0\},\quad c=\frac{n_0}{n_1}"
    tarjetas = [
        _card_eq_codigo(tx("Ecuación (1): pesos de costo", "Equation (1): cost weights"),
                        tx("El moroso pesa c = n₀/n₁ cuando class_weight = «balanced»; el peso se calcula una vez en fit.",
                           "A defaulter weighs c = n₀/n₁ when class_weight = “balanced”; the weight is computed once in fit."), [
            (tx("Función _pesos_de_clase", "Function _pesos_de_clase"), L1("def _pesos_de_clase"),
             L1('raise ValueError(f"class_weight no válido'), [
                ("n1 = max(int(y.sum()), 1)", 3, 1, eq1,
                 tx("cuenta morosos (n₁) y no morosos (n₀) y da peso n₀/n₁ a cada moroso y 1 a los demás.",
                    "counts defaulters (n₁) and non-defaulters (n₀) and gives weight n₀/n₁ to each defaulter and 1 to the rest."))]),
            (tx("Dónde se usa: CSFisherObliqueForest.fit", "Where it is used: CSFisherObliqueForest.fit"),
             L1("w = _pesos_de_clase(y01"), L1("w = w * np.asarray(sample_weight"), [
                ("w = _pesos_de_clase(y01", 1, 1, r"\mathbf{w}=(w_1,\dots,w_n)",
                 tx("el vector de pesos que usan el Gini (2), la dirección de Fisher (3)–(4) y las hojas (5).",
                    "the weight vector used by the Gini (2), the Fisher direction (3)–(4) and the leaves (5)."))]),
        ]),
        _card_eq_codigo(tx("Ecuación (2): Gini ponderado", "Equation (2): weighted Gini"),
                        tx("El mismo criterio para los dos tipos de corte.", "The same criterion for both cut types."), [
            (tx("Función _gini_ponderado", "Function _gini_ponderado"), L1("def _gini_ponderado"),
             L1("return WL * 2 * pL * (1 - pL)"), [
                ("pL = np.where(WL > 0", 2, 2, r"p_A=\frac{\sum_{i\in A}w_iy_i}{\sum_{i\in A}w_i},\quad A\in\{L,R\}",
                 tx("proporción ponderada de morosos a cada lado del corte (W1L / WL y W1R / WR).",
                    "weighted share of defaulters on each side of the cut (W1L / WL and W1R / WR).")),
                ("return WL * 2 * pL * (1 - pL)", 1, 2, r"G(L,R)=W_L\,2p_L(1-p_L)+W_R\,2p_R(1-p_R)",
                 tx("impureza de Gini ponderada del corte; el nodo elige el corte de menor G.",
                    "weighted Gini impurity of the cut; the node picks the cut with the lowest G."))]),
        ]),
        _card_eq_codigo(tx("Ecuaciones (3) y (4): dirección de Fisher por nodo", "Equations (3) and (4): Fisher direction per node"),
                        tx("Vectorizada: calcula a la vez la dirección de todos los nodos de un nivel con np.bincount.",
                           "Vectorized: it computes the direction of every node in a level at once with np.bincount."), [
            (tx("Función direccion_fisher_por_nodo", "Function direccion_fisher_por_nodo"),
             L1("def direccion_fisher_por_nodo"), L1("return V, valido"), [
                ("mu1 = np.stack(", 2, 3, r"\mu_k=\frac{\sum_{i:\,y_i=k}w_i\,\mathbf{x}_{i,F}}{\sum_{i:\,y_i=k}w_i},\quad k\in\{0,1\}",
                 tx("medias ponderadas por costo de los que pagan (μ₀) y de los que incumplen (μ₁) en cada nodo.",
                    "cost-weighted means of payers (μ₀) and defaulters (μ₁) in each node.")),
                ("D = Xs - np.where(y[:, None] == 1", 10, 3,
                 r"S=\frac{1}{\sum_i w_i}\sum_i w_i(\mathbf{x}_{i,F}-\mu_{y_i})(\mathbf{x}_{i,F}-\mu_{y_i})^\top",
                 tx("dispersión intra-clase ponderada: D son las desviaciones a la media de su clase y Sw se arma por pares de variables.",
                    "weighted within-class scatter: D are deviations from the class mean and Sw is built pair by pair.")),
                ("traza = np.trace(Sw", 2, 3, r"S_w=S+\varepsilon\,\frac{\operatorname{tr}S}{q}\,I_q",
                 tx("regularización: suma ε veces la traza media a la diagonal para que S_w sea invertible.",
                    "regularization: adds ε times the mean trace to the diagonal so S_w is invertible.")),
                ("V = np.linalg.solve(Sw", 2, 4, r"\mathbf{v}=\frac{S_w^{-1}(\mu_1-\mu_0)}{\lVert S_w^{-1}(\mu_1-\mu_0)\rVert}",
                 tx("resuelve S_w v = μ₁ − μ₀ (sin invertir la matriz) y normaliza la dirección.",
                    "solves S_w v = μ₁ − μ₀ (without inverting the matrix) and normalizes the direction."))]),
        ]),
        _card_eq_codigo(tx("El corazón del modelo: los cortes compiten", "The heart of the model: cuts compete"),
                        tx("En cada nivel del árbol: primero el mejor corte recto; luego el oblicuo lo reemplaza solo si tiene menor G.",
                           "At each tree level: first the best straight cut; then the oblique one replaces it only if it has a lower G."), [
            (tx("Método _ArbolCSFOF.fit", "Method _ArbolCSFOF.fit"), L1("# --- candidatos por ejes"),
             L1("# --- aplicar cortes") - 2, [
                ("G, b = _mejor_umbral_por_histograma(nodo_de, Zb", 1, 2, r"\min_{j\in F,\;t}\;G(L,R)",
                 tx("mejor corte recto sobre las q variables sorteadas, con umbrales en 64 cuantiles.",
                    "best straight cut over the q drawn variables, with thresholds on 64 quantiles.")),
                ("V, valido = direccion_fisher_por_nodo", 1, 4, r"\mathbf{v}=\frac{S_w^{-1}(\mu_1-\mu_0)}{\lVert S_w^{-1}(\mu_1-\mu_0)\rVert}",
                 tx("dirección de Fisher de cada nodo, con las ecuaciones (3) y (4).",
                    "Fisher direction of each node, with equations (3) and (4).")),
                ('z = np.einsum("ij,ij->i", Xs, V[nodo_de])', 1, 4, r"z_i=\mathbf{v}^\top\mathbf{x}_{i,F}",
                 tx("proyecta cada cliente sobre la dirección: el corte oblicuo es un umbral sobre z.",
                    "projects each client onto the direction: the oblique cut is a threshold on z.")),
                ("G, b = _mejor_umbral_por_histograma(nodo_de, bz", 1, 2, r"\min_{t}\;G(L,R)\ \text{con}\ L=\{i:\,z_i\le t\}",
                 tx("mejor umbral sobre la proyección, con el mismo Gini ponderado.",
                    "best threshold on the projection, with the same weighted Gini.")),
                ("m = np.flatnonzero(G < mejor_G)", 1, "P1", r"G_{\text{oblicuo}}<G_{\text{recto}}\ \Rightarrow\ \text{gana el corte oblicuo}",
                 tx("la competencia: el oblicuo reemplaza al recto solo si tiene menor impureza (Proposición 1).",
                    "the competition: the oblique cut replaces the straight one only if its impurity is lower (Proposition 1)."))]),
        ]),
        _card_eq_codigo(tx("Ecuación (5): hojas y predicción del bosque", "Equation (5): leaves and forest prediction"),
                        tx("Cada hoja guarda la proporción ponderada de morosos; el bosque promedia las hojas de sus T árboles.",
                           "Each leaf stores the weighted share of defaulters; the forest averages the leaves of its T trees."), [
            (tx("Valor de cada hoja (_ArbolCSFOF.fit)", "Value of each leaf (_ArbolCSFOF.fit)"), L1("ww, wy = wf * cf"),
             L1("puede = (C >= 2 * min_leaf)") - 1, [
                ("valor[ids_nivel[k]] = W1[k] / W[k]", 1, 5,
                 r"\hat p_{\text{hoja}}=\frac{\sum_{i\in\text{hoja}}w_iy_i}{\sum_{i\in\text{hoja}}w_i}",
                 tx("W1 es el peso de los morosos del nodo y W su peso total.", "W1 is the weight of the node's defaulters and W its total weight."))]),
            (tx("Predicción (CSFisherObliqueForest.predict_proba)", "Prediction (CSFisherObliqueForest.predict_proba)"),
             L1("def predict_proba"), L1("def predict(self") - 2, [
                ("p1 = np.mean([a.proba1(Z)", 1, 5, r"f(\mathbf{x})=\frac1T\sum_{t=1}^{T}\hat p_t(\mathbf{x})",
                 tx("promedio de las probabilidades de hoja de los T árboles.", "average of the leaf probabilities of the T trees."))]),
        ]),
    ]
    uso = """from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from src.original_model import CSFisherObliqueForest

modelo = make_pipeline(StandardScaler(), CSFisherObliqueForest(
    n_estimators=359, max_depth=11, min_samples_leaf=51, max_features="log2",
    eps=0.324, class_weight="balanced", random_state=42, n_jobs=8))
modelo.fit(X_train, y_train)
riesgo = modelo.predict_proba(X_test)[:, 1]          # puntaje de incumplimiento
print(modelo[-1].fraccion_cortes_oblicuos())        # 0.71 en el modelo final"""
    pruebas = "\n\n\n".join(_py_seg(CSFOF_TESTS_SRC, n) for n in
                            ("test_frontera_diagonal_la_capta_un_solo_corte_oblicuo", "test_prop1_corte_oblicuo_nunca_peor_que_ejes"))
    links = html.Div([
        html.A([icon("github"), tx("Ver original_model.py en GitHub", "See original_model.py on GitHub")], href=CSFOF_URL,
               target="_blank", rel="noopener noreferrer", className="cs-link"),
        html.A([icon("github"), tx("Ver las 14 pruebas", "See the 14 tests")], href=CSFOF_TESTS_URL,
               target="_blank", rel="noopener noreferrer", className="cs-link"),
    ], className="cs-links")
    return [
        card(tx("Implementación propia", "Own implementation"), [
            html.P(tx(f"CS-FOF está escrito desde cero en un solo archivo de {n_lines} líneas. Solo usa numpy para el cálculo; "
                      "de scikit-learn hereda únicamente la interfaz fit / predict, para poder compararlo con los demás modelos "
                      "en los mismos pipelines. No usa redes neuronales ni importa ningún modelo de árboles.",
                      f"CS-FOF is written from scratch in a single {n_lines}-line file. It only uses numpy for computation; "
                      "from scikit-learn it inherits just the fit / predict interface, so it can be compared with the other "
                      "models in the same pipelines. It uses no neural networks and imports no tree model."),
                   className="muted"),
            html.Div([
                kpi(tx("Líneas de código", "Lines of code"), f"{n_lines}", tx("un solo archivo, numpy", "one file, numpy"), "columns"),
                kpi(tx("Pruebas unitarias", "Unit tests"), "14", tx("en GitHub Actions en cada push", "on GitHub Actions on every push"), "target"),
                kpi(tx("Ajuste de un bosque", "Fitting one forest"), "≈ 13 s", tx("29 965 clientes, 4 procesos", "29,965 clients, 4 processes"), "clock"),
                kpi(tx("Modelo serializado", "Serialized model"), "5 MB", tx("artifacts/cs_fof.joblib", "artifacts/cs_fof.joblib"), "save"),
            ], className="kpi-row k4"),
            eqv_hint(), links]),
        *tarjetas,
        card(tx("Cómo se usa", "How to use it"), [
                html.P(tx("Igual que cualquier modelo de scikit-learn, con los hiperparámetros del modelo final.",
                          "Like any scikit-learn model, with the final model's hyperparameters."), className="muted"),
                py_code(uso)]),
        card(tx("Pruebas de las propiedades", "Tests of the properties"), [
                html.P(tx("Dos de las 14 pruebas: un solo corte oblicuo capta una frontera diagonal, y la Proposición 1.",
                          "Two of the 14 tests: a single oblique cut captures a diagonal boundary, and Proposition 1."),
                       className="muted"),
                py_code(pruebas)]),
        card(tx(f"Archivo completo ({n_lines} líneas)", f"Full file ({n_lines} lines)"), [
            html.Details([html.Summary(tx("Mostrar original_model.py", "Show original_model.py"), className="cs-sum"),
                          py_code(CSFOF_SRC)])]),
    ]


def _csfof_results():
    sig = lambda p: html.B("< 0.001" if p < 0.001 else f"{p:.3f}") if p < 0.05 else f"{p:.3f}"
    tests = _tbl([tx("Rival", "Rival"), tx("Dif. F1", "F1 diff."), tx("Gana en", "Wins in"),
                  "p Nadeau-Bengio (Holm)", tx("δ de Cliff", "Cliff's δ"), "p DeLong",
                  tx("Errores exclusivos (CS-FOF / rival)", "Exclusive errors (CS-FOF / rival)")],
                 [(minfo(m, "label"), f"{d:+.4f}", f"{g}/5", sig(p), f"{dc:+.2f}", dl, mc)
                  for m, d, g, p, dc, dl, mc in CSFOF_TESTS])
    cross = _tbl([tx("Modelo", "Model"), tx("Taiwán", "Taiwan"), "German", "Australian", tx("Polish (año 1)", "Polish (year 1)"),
                  tx("Rango medio", "Mean rank")],
                 [((html.B if m == "cs_fof" else str)(minfo(m, "label")), f"{a:.3f}", f"{b:.3f}", f"{cc:.3f}", f"{d:.3f}", f"{r:.2f}")
                  for m, a, b, cc, d, r in CROSS_DATA])
    return [
        card(tx("CS-FOF frente a otro modelo", "CS-FOF vs another model"), [
        html.P(tx("Elige contra qué modelo comparar a CS-FOF y en qué escenario, y presiona Reproducir.",
                  "Choose which model to compare CS-FOF against and in which scenario, and press Play."), className="muted"),
        html.Div([control(tx("Comparar con", "Compare with"), dcc.RadioItems(
            id="csrf-rival", value="random_forest", className="radio",
            options=[{"label": minfo(m, "label"), "value": m} for m in CS_RIVALS])),
            control(tx("Escenario", "Scenario"), dcc.RadioItems(
            id="csrf-scn", value="folds", className="radio",
            options=[{"label": tx("Los 5 pliegues", "The 5 folds"), "value": "folds"},
                     {"label": tx("Menos datos", "Less data"), "value": "size"},
                     {"label": tx("Más ruido", "More noise"), "value": "noise"}]))], className="controls"),
        html.Div(id="csrf-box"),
        ]),
        card(tx("Pruebas frente a cada modelo (Taiwán)", "Tests against each model (Taiwan)"), [
            html.P(tx("Validación cruzada anidada 5 × 5 con los mismos folds, preprocesamiento y presupuesto de "
                      "búsqueda para los 8 modelos. Métrica principal: F1 de la clase default. En negrita, p < 0.05.",
                      "Nested 5 × 5 cross-validation with the same folds, preprocessing and search budget for the 8 "
                      "models. Main metric: F1 of the default class. In bold, p < 0.05."), className="muted"),
            tests]),
        card(tx("Consistencia en otros conjuntos de crédito (F1)", "Consistency on other credit datasets (F1)"), [
            html.P(tx("Los 8 modelos con pesos de clase y búsqueda aleatoria en tres conjuntos públicos de UCI.",
                      "The 8 models with class weights and random search on three public UCI datasets."),
                   className="muted"),
            cross]),
        card(tx("Métricas fuera de pliegue que pide la guía", "Out-of-fold metrics required by the guide"), [
            html.P(tx("Predicciones fuera de pliegue de los 29 965 clientes (reajuste con los hiperparámetros de cada "
                      "pliegue), umbral 0.5. Descriptivas: solo el AUC-ROC tiene prueba (DeLong).",
                      "Out-of-fold predictions for the 29,965 clients (refit with each fold's hyperparameters), "
                      "threshold 0.5. Descriptive: only ROC-AUC has a test (DeLong)."), className="muted"),
            _tbl([tx("Modelo", "Model"), "MCC", "AUC-PR", tx("Brier (menor es mejor)", "Brier (lower is better)"), "F1"],
                 [(html.B("CS-FOF (original)"), html.B("0.411"), html.B("0.560"), html.B("0.168"), html.B("0.548")),
                  ("XGBoost", "0.401", "0.555", "0.175", "0.545"),
                  ("Random Forest", "0.400", "0.558", "0.173", "0.543")]),
        ]),
        card(tx("Veredicto", "Verdict"), [
        html.Div(tx("CS-FOF obtiene el mayor F1 medio en el problema principal, pero no es superior de forma "
                    "significativa a XGBoost ni a Random Forest, y en los conjuntos adicionales queda por detrás de XGBoost.",
                    "CS-FOF has the highest mean F1 on the main problem, but it is not significantly superior to "
                    "XGBoost or Random Forest, and on the additional datasets it falls behind XGBoost."), className="callout"),
        interp_block(
            tx("En el problema principal CS-FOF acierta tanto como los mejores modelos y es el más estable. Comete "
               "menos errores que solo él cometa, pero eso se debe a que marca menos clientes como riesgosos, no a "
               "que ordene mejor. En el conjunto polaco, con muy pocas quiebras (4 %), XGBoost le "
               "saca mucha ventaja.",
               "On the main problem CS-FOF is as accurate as the best models and is the most stable. It makes fewer "
               "errors that only it makes, but that is because it flags fewer clients as risky, not because it ranks "
               "them better. On the Polish dataset, with very few bankruptcies (4%), XGBoost is far ahead."),
            tx("Friedman sobre los 8 modelos: χ² = 32.9, p = 2.7·10⁻⁵; rangos medios CS-FOF 1.4 y XGBoost 2.2; "
               "diferencia crítica de Nemenyi 4.70. Wilcoxon con 5 folds no puede bajar de p = 0.0625. DeLong y "
               "McNemar usan predicciones fuera de pliegue de los 29 965 clientes. Entre los 4 "
               "conjuntos, Iman-Davenport F = 3.22, p = 0.018; XGBoost tiene el mejor rango medio (2.0) y CS-FOF el tercero (3.25).",
               "Friedman over the 8 models: χ² = 32.9, p = 2.7·10⁻⁵; mean ranks CS-FOF 1.4 and XGBoost 2.2; "
               "Nemenyi critical difference 4.70. Wilcoxon with 5 folds cannot go below p = 0.0625. DeLong and "
               "McNemar use out-of-fold predictions for the 29,965 clients. Across the 4 datasets, "
               "Iman-Davenport F = 3.22, p = 0.018; XGBoost has the best mean rank (2.0) and CS-FOF the third (3.25).")),
        ]),
    ]


def page_original():
    """Página del modelo original CS-FOF: presentación, pestaña de teoría y pestaña de resultados."""
    c = CSFOF_CM
    pos = c["tp"] + c["fn"]
    tab = lambda lbl, val, kids: dcc.Tab(label=lbl, value=val, children=html.Div(kids, className="cs-pane"),
                                         className="cs-tab", selected_className="cs-tab--on")
    return html.Div([
        page_title(tx("Modelo original", "Original model"), "", stage="csfof"),
        card(tx("CS-FOF y HIB: el modelo original y su mejora", "CS-FOF and HIB: the original model and its improvement"), [
            html.P(tx("CS-FOF (Cost-Sensitive Fisher Oblique Forest) es el modelo propuesto en este proyecto: un bosque aleatorio programado "
                      "desde cero, sin redes neuronales, cuyos árboles pueden cortar en diagonal combinando varias variables, en la dirección "
                      "de Fisher ponderada por el costo de no detectar a quien incumple. Obtuvo el mayor F1 medio, pero empató con XGBoost. "
                      "Para mejorar el F1, a partir de CS-FOF se hizo un ensamble (stacking) con XGBoost, CatBoost, LightGBM, Random Forest, "
                      "Extra Trees, HistGradientBoosting y regresión logística: HIB. Las pestañas siguen el orden de una presentación: la idea "
                      "(Teoría), cómo se construyó y evaluó (Metodología), el código, cómo le fue (Resultados) y cómo se mejoró (Del CS-FOF al HIB).",
                      "CS-FOF (Cost-Sensitive Fisher Oblique Forest) is the model proposed in this project: a random forest programmed "
                      "from scratch, without neural networks, whose trees can cut diagonally by combining several variables, along the Fisher "
                      "direction weighted by the cost of missing a defaulter. It got the highest mean F1 but tied with XGBoost. To raise F1, "
                      "an ensemble (stacking) was built from CS-FOF with XGBoost, CatBoost, LightGBM, Random Forest, Extra Trees, "
                      "HistGradientBoosting and logistic regression: HIB. The tabs follow the order of a presentation: the idea (Theory), "
                      "how it was built and evaluated (Methodology), the code, how it performed (Results) and how it was improved (From CS-FOF to HIB).")),
            html.Div([
                kpi("CS-FOF · F1", "0.548 ± 0.005", tx("el mayor de los 8 modelos; sin diferencia significativa con XGBoost",
                                                        "the highest of the 8 models; no significant difference with XGBoost"), "trophy"),
                kpi("CS-FOF · ROC-AUC", "0.785", tx("el mayor de los 8 modelos", "the highest of the 8 models"), "target"),
                kpi("HIB · F1", "0.5505", tx("ensamble que parte de CS-FOF: +0.0037 sobre XGBoost; gana a los 7 modelos base con Wilcoxon-Holm",
                                             "ensemble built from CS-FOF: +0.0037 over XGBoost; beats the 7 baseline models with Wilcoxon-Holm"), "layers"),
                kpi(tx("CS-FOF · cortes oblicuos", "CS-FOF · oblique splits"), "71 %",
                    tx("de los nodos del modelo final", "of the final model's nodes"), "tree"),
            ], className="kpi-row k4"),
        ]),
        dcc.Tabs(value="teoria", className="cs-tabs", parent_className="cs-tabs-wrap", mobile_breakpoint=0, children=[
            tab(tx("1 · Teoría", "1 · Theory"), "teoria", csfof_theory()),
            tab(tx("2 · Metodología", "2 · Methodology"), "metodologia", csfof_method()),
            tab(tx("3 · Código", "3 · Code"), "codigo", csfof_code()),
            tab(tx("4 · Resultados", "4 · Results"), "resultados", _csfof_results()),
            tab(tx("5 · Del CS-FOF al HIB", "5 · From CS-FOF to HIB"), "mejorar", csfof_beyond()),
        ]),
    ])
