# -*- coding: utf-8 -*-
"""Pestaña «5 · Del CS-FOF al HIB» del Modelo original: cómo, a partir del modelo original, se combinó con
XGBoost, CatBoost, LightGBM, Random Forest, Extra Trees, HistGradientBoosting y regresión logística para mejorar el F1.

Fuentes: Tabla_combinaciones.xlsx y el informe de HIB (rama claude/wonderful-planck-tq6tc2 del proyecto:
entregables_profesor/ y protocolo_confirmatorio_v2/), siempre con 25 pliegues (5 repeticiones × 5 pliegues).
Las redes neuronales (TabM, TabM-Fisher, TabPFN) se reportan solo en el paper, por indicación del profesor.
El «stacking con regresión logística» como combinador no se usa en el proyecto y no se muestra.
"""

import numpy as np
import plotly.graph_objects as go
from dash import dcc, html

from tablero.componentes import _tbl, card, interp_block, kpi
from tablero.config import BASE_DIR, DEEP_NAVY, DEEP_RGBA, GREY_BLUE, L, NAVY, WARM_GOLD, WHITE, tx
from tablero.glosario import HIB, V, eqv_hint, fx
from tablero.iconos import icon
from tablero.pipeline import pipeline_btn
from tablero.utilidades import style_fig

HIB_SRC = (BASE_DIR / "modelo" / "hib" / "hib_regla.txt").read_text(encoding="utf-8")
HIB_COMMIT = "https://github.com/valeriaflorezs/Credit_Card_Project/blob/claude/wonderful-planck-tq6tc2/entregables_profesor/protocolo_confirmatorio_v2/hib.py"

# Diferencia = candidato − XGBoost de su propia corrida; IC 95 % de la t corregida de Nadeau-Bengio.
# (etiqueta es, etiqueta en, F1, diferencia, IC inf, IC sup, gana en, p Nadeau-Bengio, p Wilcoxon, p Wilcoxon-Holm, grupo)
# Fase A = exploración inicial; fase B = los 13 candidatos congelados, validados con semillas nuevas (se omiten los que usan
# stacking con regresión logística); HIB = prueba pre-registrada (v1: semillas 5000-5004; v2: 7100-7104).
BEYOND_ROWS = [
    ("HIB, confirmación v2", "HIB, v2 confirmation", 0.5505, 0.0037, 0.0000, 0.0074, "21/25", 0.049, 2.7e-05, 5.3e-05, "hib"),
    ("HIB, primera corrida v1", "HIB, first run v1", 0.5502, 0.0039, -0.0018, 0.0096, "19/25", 0.17, None, 0.0016, "hib"),
    ("Promedio: CS-FOF + XGBoost(4) + CatBoost ×2 + HistGB", "Average: CS-FOF + XGBoost(4) + CatBoost ×2 + HistGB",
     0.5499, 0.0038, -0.0020, 0.0096, "19/25", 0.190, 0.0018, 0.0127, "ens"),
    ("Logit ponderado: CatBoost + HistGB", "Weighted logit: CatBoost + HistGB",
     0.5495, 0.0034, -0.0032, 0.0100, "18/25", 0.295, 0.0088, 0.0295, "ens"),
    ("Promedio: XGBoost(4) + CatBoost ×2 + LightGBM + HistGB", "Average: XGBoost(4) + CatBoost ×2 + LightGBM + HistGB",
     0.5494, 0.0032, -0.0028, 0.0092, "19/25", 0.279, 0.0074, 0.0295, "ens"),
    ("Logit ponderado: XGBoost(4) + CatBoost + HistGB", "Weighted logit: XGBoost(4) + CatBoost + HistGB",
     0.5492, 0.0031, -0.0029, 0.0091, "17/25", 0.298, 0.0088, 0.0295, "ens"),
    ("FWLS por PAY_0: XGBoost(4) + CatBoost", "FWLS by PAY_0: XGBoost(4) + CatBoost",
     0.5491, 0.0030, -0.0030, 0.0090, "16/25", 0.309, 0.0255, 0.0295, "ens"),
    ("Logit ponderado: CatBoost ×2 + LightGBM + HistGB", "Weighted logit: CatBoost ×2 + LightGBM + HistGB",
     0.5491, 0.0030, -0.0022, 0.0082, "19/25", 0.247, 0.0023, 0.0135, "ens"),
    ("Caruana, 10 modelos (con CS-FOF)", "Caruana, 10 models (with CS-FOF)",
     0.5491, 0.0030, -0.0014, 0.0074, "20/25", 0.175, 0.0015, 0.0117, "ens"),
    ("FWLS por PAY_0, 10 modelos (con CS-FOF)", "FWLS by PAY_0, 10 models (with CS-FOF)",
     0.5491, 0.0030, -0.0017, 0.0078, "15/25", 0.203, 0.0042, 0.0209, "ens"),
    ("CatBoost solo (referencia)", "CatBoost alone (reference)",
     0.5494, 0.0037, -0.0015, 0.0089, "21/25", 0.158, 0.00049, 0.0093, "base"),
    ("CS-FOF solo, umbral interno (referencia)", "CS-FOF alone, inner threshold (reference)",
     0.5473, 0.0016, -0.0018, 0.0049, "19/25", 0.352, 0.0125, 0.1247, "csfof"),
    ("Rotation Forest propio (referencia)", "Own Rotation Forest (reference)",
     0.5421, -0.0036, -0.0087, 0.0015, "5/25", 0.156, 0.00019, 0.0038, "base"),
]
# F1 medio de cada modelo en las corridas (meseta)
BEYOND_PLATEAU = [  # (modelo, F1 medio, grupo)
    ("Regresión logística|Logistic regression", 0.5230, "base"), ("Rotation Forest", 0.5421, "base"),
    ("XGBoost", 0.5457, "base"), ("Random Forest", 0.5461, "base"), ("LightGBM", 0.5467, "base"),
    ("CS-FOF", 0.5473, "csfof"), ("CatBoost", 0.5494, "base"),
    ("Promedio CS-FOF + 4 boosting|CS-FOF + 4 boosting average", 0.5499, "ens"), ("HIB v2", 0.5505, "hib"),
]
BEYOND_COLORS = {"ens": NAVY, "hib": WARM_GOLD, "base": GREY_BLUE, "csfof": DEEP_NAVY}
BEYOND_SYMBOLS = {"ens": "circle", "hib": "diamond", "base": "circle-open", "csfof": "square"}

SIG = 0.05


def _beyond_group(g):
    return {"ens": tx("Ensambles de la fase B (25 pliegues)", "Phase B ensembles (25 folds)"),
            "hib": tx("HIB (25 pliegues)", "HIB (25 folds)"),
            "base": tx("Modelos individuales (referencia)", "Single models (reference)"),
            "csfof": tx("CS-FOF (modelo original)", "CS-FOF (original model)")}[g]


def fig_beyond_diff():
    """Diferencia de F1 frente a XGBoost con su IC 95 %, con la región de equivalencia práctica (±0.01)."""
    rows = list(reversed(BEYOND_ROWS))
    fig = go.Figure()
    fig.add_vrect(x0=-0.01, x1=0.01, fillcolor=f"{DEEP_RGBA}0.06)", line_width=0, layer="below")
    fig.add_vline(x=0, line_color=DEEP_NAVY, line_width=1.2)
    vistos = set()
    for es, en, f1, d, lo, hi, gana, pnb, pw, pwh, g in rows:
        y = tx(es, en)
        fig.add_trace(go.Scatter(
            x=[d], y=[y], mode="markers",
            marker=dict(size=11, color=BEYOND_COLORS[g], symbol=BEYOND_SYMBOLS[g], line=dict(width=1.8, color=BEYOND_COLORS[g] if "open" in BEYOND_SYMBOLS[g] else WHITE)),
            error_x=dict(type="data", symmetric=False, array=[hi - d], arrayminus=[d - lo], color=BEYOND_COLORS[g], thickness=2.4, width=0),
            name=_beyond_group(g), legendgroup=g, showlegend=g not in vistos,
            hovertemplate=(f"<b>{y}</b><br>F1: {f1:.4f}<br>" + tx("Dif. F1", "F1 diff.") + f": {d:+.4f}<br>IC 95 %: [{lo:+.4f}, {hi:+.4f}]"
                           f"<br>p Nadeau-Bengio: {pnb:.3f}<br>p Wilcoxon-Holm: {pwh:.4f}<extra></extra>")))
        vistos.add(g)
    fig.add_annotation(x=0.0098, y=1.0, yref="paper", text=tx("Equivalencia práctica ±0.01", "Practical equivalence ±0.01"),
                       showarrow=False, xanchor="right", yanchor="bottom", font=dict(size=11, color=GREY_BLUE))
    style_fig(fig, h=640, title=tx("Diferencia de F1 frente a XGBoost (IC 95 %)", "F1 difference vs XGBoost (95% CI)"),
              xaxis=dict(title=tx("F1 del modelo − F1 de XGBoost", "Model F1 − XGBoost F1"), range=[-0.0125, 0.0125], tickformat="+.3f"),
              yaxis=dict(automargin=True))
    fig.update_layout(margin=dict(l=20, r=30, t=80, b=130),
                      legend=dict(orientation="h", yanchor="top", y=-0.13, xanchor="center", x=0.5))
    return fig


def fig_wilcoxon():
    """−log10 del p de Wilcoxon (con Holm) de cada candidato frente a XGBoost, con la línea de p = 0.05."""
    rows = sorted([r for r in BEYOND_ROWS if r[9] is not None and r[3] > 0], key=lambda r: -np.log10(r[9]))   # solo los que superan a XGBoost
    fig = go.Figure()
    for es, en, f1, d, lo, hi, gana, pnb, pw, pwh, g in rows:
        y = tx(es, en)
        fig.add_trace(go.Bar(
            y=[y], x=[-np.log10(pwh)], orientation="h", marker=dict(color=BEYOND_COLORS[g] if pwh < SIG else "rgba(120,130,150,.45)"),
            showlegend=False, text=[f"p = {pwh:.4f}" if pwh >= 1e-4 else "p < 0.0001"], textposition="outside", cliponaxis=False,
            textfont=dict(size=11, color=DEEP_NAVY),
            hovertemplate=f"<b>{y}</b><br>Wilcoxon-Holm p = {pwh:.5f}<br>" + tx("Dif. F1", "F1 diff.") + f": {d:+.4f}<extra></extra>"))
    fig.add_vline(x=-np.log10(SIG), line_color=WARM_GOLD, line_width=2, line_dash="dash")
    fig.add_annotation(x=-np.log10(SIG), y=1.0, yref="paper", text="p = 0.05", showarrow=False, xanchor="left", yanchor="bottom",
                       font=dict(size=11, color=WARM_GOLD))
    style_fig(fig, h=560, title=tx("Wilcoxon con Holm frente a XGBoost", "Wilcoxon with Holm vs XGBoost"),
              xaxis=dict(title=tx("−log₁₀ del p ajustado (más a la derecha = más significativo)", "−log₁₀ of the adjusted p (further right = more significant)"),
                         range=[0, 5.4]),
              yaxis=dict(automargin=True))
    fig.update_layout(margin=dict(l=20, r=70, t=80, b=70), bargap=.35)
    return fig


def fig_beyond_plateau():
    """F1 medio de cada modelo: la «meseta» en la que quedan casi todos."""
    rows = sorted(BEYOND_PLATEAU, key=lambda r: r[1])
    nombre = lambda s: tx(*s.split("|")) if "|" in s else s
    fig = go.Figure()
    fig.add_vrect(x0=0.5457, x1=0.5505, fillcolor=f"{DEEP_RGBA}0.06)", line_width=0, layer="below")
    vistos = set()
    for s, v, g in rows:
        fig.add_trace(go.Scatter(
            x=[v], y=[nombre(s)], mode="markers+text", text=[f"{v:.4f}"], textposition="middle right",
            textfont=dict(size=11, color=DEEP_NAVY),
            marker=dict(size=12, color=BEYOND_COLORS[g], symbol=BEYOND_SYMBOLS[g], line=dict(width=1.8, color=BEYOND_COLORS[g] if "open" in BEYOND_SYMBOLS[g] else WHITE)),
            name=_beyond_group(g), legendgroup=g, showlegend=g not in vistos,
            hovertemplate=f"<b>{nombre(s)}</b><br>F1: {v:.4f}<extra></extra>"))
        vistos.add(g)
    fig.add_annotation(x=0.5481, y=1.0, yref="paper", showarrow=False, yanchor="bottom", font=dict(size=11, color=GREY_BLUE),
                       text=tx("7 de 9 modelos en 0.0048 de F1", "7 of 9 models within 0.0048 of F1"))
    style_fig(fig, h=520, title=tx("La meseta del F1", "The F1 plateau"),
              xaxis=dict(title=tx("F1 medio de la clase default", "Mean F1 of the default class"), range=[0.52, 0.558]),
              yaxis=dict(automargin=True))
    fig.update_layout(margin=dict(l=20, r=30, t=80, b=130),
                      legend=dict(orientation="h", yanchor="top", y=-0.13, xanchor="center", x=0.5))
    return fig


# (nombre, tipo, explicación básica, explicación técnica)
BEYOND_MODELS = [
    ("Promedio de probabilidades", "Probability average", ("Combinador", "Combiner"),
     ("Es como preguntarle a varios expertos y quedarse con el promedio de sus opiniones. Si cada uno se equivoca en "
      "clientes distintos, los errores se compensan.",
      "It is like asking several experts and keeping the average of their opinions. If each one makes mistakes on "
      "different clients, the errors cancel out."),
     ("p̂ = (1/M) Σₘ pₘ, sin parámetros que aprender. Reduce la varianza en la medida en que los errores de los miembros "
      "no estén correlacionados. La variante en logit (promedio de log-odds) equivale a una media geométrica de las "
      "odds. Es la referencia contra la que debe ganar cualquier regla de pesos.",
      "p̂ = (1/M) Σₘ pₘ, with no parameters to learn. It reduces variance to the extent that the members' errors are not "
      "correlated. The logit variant (average of log-odds) is a geometric mean of the odds. It is the baseline any "
      "weighting rule must beat.")),
    ("FWLS por PAY_0", "FWLS by PAY_0", ("Combinador", "Combiner"),
     ("El jefe cambia de criterio según el cliente: confía en unos expertos para quien va al día y en otros para "
      "quien tiene atraso.",
      "The boss changes criteria by client: it trusts some experts for clients who are up to date and others for "
      "clients who are behind."),
     ("Feature-weighted linear stacking (Sill et al., 2009): los pesos dependen de una meta-variable. Aquí "
      "z = Σₘ (aₘ + bₘ·g)·logit pₘ con g = 1{PAY_0 > 0}, ajustado con regresión logística sobre predicciones fuera de "
      "pliegue. Busca aprovechar que XGBoost acierta más entre los clientes al día.",
      "Feature-weighted linear stacking (Sill et al., 2009): the weights depend on a meta-feature. Here "
      "z = Σₘ (aₘ + bₘ·g)·logit pₘ with g = 1{PAY_0 > 0}, fitted with logistic regression on out-of-fold predictions. "
      "It tries to exploit that XGBoost does better among clients who are up to date.")),
    ("Selección de Caruana", "Caruana selection", ("Combinador", "Combiner"),
     ("Se arma el equipo de a un experto: en cada paso entra el que más mejora el resultado, y se puede repetir al "
      "mismo experto para darle más peso.",
      "The team is built one expert at a time: at each step the one that most improves the result joins, and the same "
      "expert can be added again to give it more weight."),
     ("Selección hacia adelante con reemplazo sobre las predicciones fuera de pliegue (Caruana et al., 2004). El "
      "peso de cada modelo es la fracción de veces que fue elegido. Es la regla que usan AutoGluon y TabArena.",
      "Forward selection with replacement on the out-of-fold predictions (Caruana et al., 2004). Each model's weight "
      "is the fraction of times it was chosen. It is the rule used by AutoGluon and TabArena.")),
    ("HIB (ensamble híbrido)", "HIB (hybrid ensemble)", ("Propuesto", "Proposed"),
     ("Un equipo de 8 modelos (CS-FOF, XGBoost, CatBoost, LightGBM, Random Forest, Extra Trees, HistGradientBoosting y "
      "regresión logística) cuyos votos se ajustan para lograr el mejor F1, sin alejarse demasiado de un voto parejo.",
      "A team of 8 models (CS-FOF, XGBoost, CatBoost, LightGBM, Random Forest, Extra Trees, HistGradientBoosting and "
      "logistic regression) whose votes are tuned to get the best F1, without straying too far from an equal vote."),
     ("w = softmax(θ), s = Zw, qᵢ = σ((sᵢ − t)/τ). Se maximiza el F1 suave 2Σqᵢyᵢ / (Σqᵢ + Σyᵢ) − λM‖w − 1/M‖² "
      "con L-BFGS-B (60 iteraciones, τ = 0.3, λ = 0.05) sobre los logits fuera de muestra Z (3 pliegues internos). "
      "El umbral final maximiza el F1 duro. Los pesos aprendidos quedaron casi uniformes (0.10 a 0.14).",
      "w = softmax(θ), s = Zw, qᵢ = σ((sᵢ − t)/τ). It maximizes the soft F1 2Σqᵢyᵢ / (Σqᵢ + Σyᵢ) − λM‖w − 1/M‖² "
      "with L-BFGS-B (60 iterations, τ = 0.3, λ = 0.05) on the out-of-sample logits Z (3 inner folds). The final "
      "threshold maximizes the hard F1. The learned weights ended up almost uniform (0.10 to 0.14).")),
    ("CatBoost", "CatBoost", ("Modelo base", "Base model"),
     ("Árboles en fila: cada uno corrige los errores de los anteriores, con un truco para no «hacer trampa» al "
      "aprender de los mismos datos con los que se evalúa.",
      "Trees in a row: each one fixes the errors of the previous ones, with a trick to avoid «cheating» by learning "
      "from the same data it is evaluated on."),
     ("Gradient boosting con árboles simétricos (oblivious trees) y ordered boosting, que calcula los gradientes de "
      "cada fila con modelos que no la vieron y así reduce el sesgo de predicción (prediction shift). Prokhorenkova "
      "et al., 2018.",
      "Gradient boosting with symmetric (oblivious) trees and ordered boosting, which computes each row's gradients "
      "with models that did not see it, reducing prediction shift. Prokhorenkova et al., 2018.")),
    ("LightGBM", "LightGBM", ("Modelo base", "Base model"),
     ("Otro boosting de árboles, muy rápido: hace crecer cada árbol por la hoja que más ayuda.",
      "Another tree boosting method, very fast: it grows each tree from the leaf that helps the most."),
     ("GBDT con histogramas, crecimiento por hoja (leaf-wise), muestreo por gradiente (GOSS) y agrupación de "
      "variables exclusivas (EFB). Ke et al., 2017.",
      "Histogram-based GBDT with leaf-wise growth, gradient-based sampling (GOSS) and exclusive feature bundling "
      "(EFB). Ke et al., 2017.")),
    ("Extra Trees", "Extra Trees", ("Modelo base", "Base model"),
     ("Un bosque cuyos cortes se eligen al azar: los árboles salen más distintos entre sí, y eso reduce el "
      "sobreajuste.",
      "A forest whose splits are chosen at random: the trees end up more different from each other, which reduces "
      "overfitting."),
     ("Extremely randomized trees (Geurts et al., 2006): en cada nodo se sortea un umbral por variable candidata y se "
      "elige el mejor de esos cortes aleatorios. Menos varianza que Random Forest a cambio de algo más de sesgo.",
      "Extremely randomized trees (Geurts et al., 2006): at each node one threshold is drawn per candidate feature and "
      "the best of those random splits is chosen. Less variance than Random Forest at the cost of some extra bias.")),
    ("HistGradientBoosting", "HistGradientBoosting", ("Modelo base", "Base model"),
     ("La versión de boosting por histogramas que trae scikit-learn.",
      "The histogram-based boosting that comes with scikit-learn."),
     ("Agrupa cada variable en hasta 255 intervalos por cuantiles y busca los cortes sobre esos intervalos, al estilo "
      "de LightGBM. Maneja valores faltantes de forma nativa.",
      "It bins each feature into up to 255 quantile intervals and searches splits over those bins, LightGBM-style. "
      "It handles missing values natively.")),
    ("Rotation Forest", "Rotation Forest", ("Modelo base", "Base model"),
     ("Antes de cada árbol «gira» los ejes de los datos para que los cortes puedan ser diagonales. Es primo de "
      "CS-FOF.",
      "Before each tree it «rotates» the data axes so the splits can be diagonal. It is a cousin of CS-FOF."),
     ("Rodríguez et al. (2006): por árbol, se parte el conjunto de variables en subconjuntos aleatorios, se aplica PCA "
      "a cada uno y el árbol se entrena sobre las componentes. Aquí quedó por debajo de XGBoost (−0.0036).",
      "Rodríguez et al. (2006): for each tree the features are split into random subsets, PCA is applied to each and "
      "the tree is trained on the components. Here it fell below XGBoost (−0.0036).")),
]



def _beyond_model_card(es, en, tag, basic, tech):
    return html.Div([
        html.Div([html.B(tx(es, en)), html.Span(L(tag), className="tag")], className="beyond-head"),
        html.P(L(basic), className="muted"),
        html.Details([html.Summary([icon("info"), tx("Ver explicación técnica", "Show technical explanation"),
                                    icon("chevron", "interp-chev")], className="interp-btn"),
                      html.Div(html.Div([html.B(tx("Técnica", "Technical")), html.P(L(tech))], className="interp tech"),
                               className="interp-body")], className="interp-wrap"),
    ], className="beyond-model")


def _h(tok, label=None):
    """Símbolo del glosario de HIB dentro de un texto."""
    return V(tok, HIB, label)


def _eq_hib(n, tex, why, donde=None):
    """Ecuación de HIB con su número, su razón de ser y, si la hay, la parte del código que la implementa."""
    cuerpo = [fx(tex, HIB), html.P([html.B(tx("Por qué: ", "Why: ")), *(why if isinstance(why, list) else [why])], className="cs-eq-why")]
    if donde:
        cuerpo.append(html.P([html.B(tx("En el código: ", "In the code: ")), donde], className="cs-eq-why"))
    return html.Div([html.Div(f"({n})", className="cs-eq-n"), html.Div(cuerpo, className="cs-eq-body")], className="cs-eq")


def _members():
    """CS-FOF en el centro de la historia: se combina con los 7 modelos hasta llegar a HIB."""
    miembros = ["XGBoost", "CatBoost", "LightGBM", "Random Forest", "Extra Trees", "HistGradientBoosting",
                tx("Regresión logística", "Logistic regression")]
    return html.Div([
        html.Div([html.Span("CS-FOF", className="hib-chip hib-orig"), html.Small(tx("modelo original", "original model"))],
                 className="hib-col"),
        html.Span("+", className="hib-op"),
        html.Div([html.Span(m, className="hib-chip") for m in miembros], className="hib-col hib-mem"),
        html.Span("→", className="hib-op"),
        html.Div([html.Span("HIB", className="hib-chip hib-main"),
                  html.Small(tx("pesos w aprendidos para un F1 suave", "weights w learned for a soft F1"))], className="hib-col"),
        html.Span("→", className="hib-op"),
        html.Div([html.Span("F1 0.5505", className="hib-chip hib-res"),
                  html.Small(tx("+0.0037 sobre XGBoost", "+0.0037 over XGBoost"))], className="hib-col"),
    ], className="hib-flow")


def csfof_beyond():
    from tablero.paginas.modelo_original import py_code   # import tardío: modelo_original importa este módulo
    gcfg = {"displaylogo": False}
    sig = lambda s: html.B(s)
    cand = [r for r in BEYOND_ROWS if r[10] == "ens"]
    n_sig = sum(r[9] < SIG for r in cand)
    cand_rows = [(tx(r[0], r[1]), f"{r[2]:.4f}", f"{r[3]:+.4f} [{r[4]:+.4f}, {r[5]:+.4f}]", r[6], f"{r[7]:.2f}",
                  (sig if r[9] < SIG else (lambda s: s))(f"{r[9]:.4f}")) for r in cand]
    return [
        card(tx("De CS-FOF a HIB: mejorar el F1 combinando modelos", "From CS-FOF to HIB: raising F1 by combining models"), [
            html.P(tx("CS-FOF obtuvo el mayor F1 medio de los 8 modelos (0.5479), pero empató con XGBoost (0.5466). Para mejorar el F1, "
                      "se partió del modelo original y se hizo un ensamble (stacking) con XGBoost, CatBoost, LightGBM, Random Forest, "
                      "Extra Trees, HistGradientBoosting y regresión logística. Primero se exploraron 2 582 formas de combinarlos, se "
                      "congelaron los 13 mejores candidatos y, con semillas nuevas, se probó el ensamble final: HIB.",
                      "CS-FOF got the highest mean F1 of the 8 models (0.5479) but tied with XGBoost (0.5466). To raise F1, the work "
                      "started from the original model and built an ensemble (stacking) with XGBoost, CatBoost, LightGBM, Random Forest, "
                      "Extra Trees, HistGradientBoosting and logistic regression. First 2,582 ways of combining them were explored, the "
                      "13 best candidates were frozen and, with new seeds, the final ensemble was tested: HIB.")),
            _members(),
            html.Div([
                kpi("HIB · F1", "0.5505", tx("+0.0037 sobre XGBoost; gana en 21 de 25 pliegues", "+0.0037 over XGBoost; wins 21 of 25 folds"), "trophy"),
                kpi(tx("Wilcoxon con Holm", "Wilcoxon with Holm"), "p = 0.0001",
                    tx("HIB frente a XGBoost; gana a los 7 modelos base", "HIB vs XGBoost; it beats all 7 baseline models"), "target"),
                kpi(tx("Miembros", "Members"), "8", tx("CS-FOF + 7 modelos de librería", "CS-FOF + 7 library models"), "layers"),
                kpi(tx("Combinaciones probadas", "Combinations tried"), "2 582",
                    tx("13 candidatos congelados, confirmados con semillas nuevas → HIB", "13 frozen candidates, confirmed with new seeds → HIB"), "bars"),
            ], className="kpi-row k4"),
            html.Div(pipeline_btn("hib", label=tx("Ver el código del pipeline de esta mejora", "See this improvement's pipeline code")),
                     className="hib-pipe"),
        ]),
        card(tx("Las ecuaciones de HIB", "HIB's equations"), [
            html.P(tx("HIB toma las puntuaciones fuera de muestra de los 8 modelos y aprende cuánto pesa cada uno para que el F1 sea el mejor posible. "
                      "Como el F1 «duro» no se puede derivar, usa una versión suave (qᵢ) y una penalización que acerca los pesos al promedio uniforme.",
                      "HIB takes the out-of-sample scores of the 8 models and learns how much each one weighs so that F1 is as high as possible. "
                      "Since the “hard” F1 cannot be differentiated, it uses a soft version (qᵢ) and a penalty that pulls the weights toward the uniform average."),
                   className="muted"),
            eqv_hint(),
            _eq_hib("H1", r"w=\operatorname{softmax}(\theta),\qquad s=Zw",
                    tx(["cada modelo da una puntuación (logit) a cada cliente y esas columnas forman ", _h("Z"), ". ", _h("w"), " = softmax(", _h("θ"),
                        ") mantiene los pesos positivos y con suma 1; ", _h("s"), " es el promedio ponderado de los logits."],
                       ["each model gives each client a score (logit) and those columns form ", _h("Z"), ". ", _h("w"), " = softmax(", _h("θ"),
                        ") keeps the weights positive and summing to 1; ", _h("s"), " is the weighted average of the logits."]),
                    tx("líneas 8 y 10 de hib_regla (softmax de p[:m] y Z @ w)", "lines 8 and 10 of hib_regla (softmax of p[:m] and Z @ w)")),
            _eq_hib("H2", r"q_i=\sigma\!\left(\frac{s_i-t}{\tau}\right)",
                    tx(["marcar o no a un cliente como default es un escalón y no se puede derivar. ", _h("q_i"), " es la versión suave: cerca de 1 si ",
                        _h("s_i"), " supera el umbral ", _h("t"), " y cerca de 0 si no; ", _h("τ"), " = 0.3 controla qué tan abrupta es."],
                       ["flagging or not a client as default is a step and cannot be differentiated. ", _h("q_i"), " is the soft version: near 1 if ",
                        _h("s_i"), " is above the threshold ", _h("t"), " and near 0 if not; ", _h("τ"), " = 0.3 sets how sharp it is."]),
                    tx("línea 8 de hib_regla (q = 1/(1+np.exp(-(Z @ w-p[m])/tau)))", "line 8 of hib_regla (q = 1/(1+np.exp(-(Z @ w-p[m])/tau)))")),
            _eq_hib("H3", r"\max_{\theta,\,t}\ \frac{2\sum_i q_i y_i}{\sum_i q_i+\sum_i y_i}\;-\;\lambda M\,\lVert w-\mathbf{1}/M\rVert^{2}",
                    tx(["el primer término es el F1 suave (con ", _h("q_i"), " en lugar de las marcas duras) y se maximiza con L-BFGS-B (60 iteraciones). "
                        "El segundo, con ", _h("λ"), " = 0.05, empuja los ", _h("M"), " = 8 pesos hacia el promedio uniforme 1/", _h("M"),
                        ": por eso los pesos aprendidos quedan casi iguales (0.10 a 0.14)."],
                       ["the first term is the soft F1 (with ", _h("q_i"), " instead of the hard flags) and is maximized with L-BFGS-B (60 iterations). "
                        "The second, with ", _h("λ"), " = 0.05, pushes the ", _h("M"), " = 8 weights toward the uniform average 1/", _h("M"),
                        ": that is why the learned weights end up almost equal (0.10 to 0.14)."]),
                    tx("líneas 7 a 9 de hib_regla (la función f que minimiza L-BFGS-B)", "lines 7 to 9 of hib_regla (the function f minimized by L-BFGS-B)")),
            html.Div(tx("El umbral final no es el t aprendido: se elige el que maximiza el F1 duro sobre las puntuaciones fuera de muestra "
                        "(entre 5 % y 60 % de positivos predichos), igual que para todos los modelos.",
                        "The final threshold is not the learned t: it is the one that maximizes the hard F1 on the out-of-sample scores "
                        "(between 5% and 60% of predicted positives), as for every model."), className="callout"),
        ]),
        card(tx("HIB en el código", "HIB in the code"), [
            html.P([tx("Copia fiel de la regla del protocolo congelado (", "Faithful copy of the frozen protocol's rule ("),
                    html.A("hib.py", href=HIB_COMMIT, target="_blank", rel="noopener noreferrer"),
                    tx("). Los miembros vienen de librería; la regla de pesos está en numpy y scipy. Los identificadores iluminan sus símbolos.",
                       "). The members come from libraries; the weight rule is in numpy and scipy. Identifiers light up their symbols.")],
                   className="muted"),
            py_code(HIB_SRC, scope=HIB),
        ]),
        card(tx("Cómo se llegó a HIB", "How HIB came about"), [
            html.P(tx("Cada tarjeta da la idea en palabras sencillas; el botón abre la explicación técnica.",
                      "Each card gives the idea in plain words; the button opens the technical explanation."), className="muted"),
            html.H4(tx("Formas de combinar modelos (ensamble / stacking)", "Ways to combine models (ensemble / stacking)"), className="beyond-sub"),
            html.Div([_beyond_model_card(*m[:3], *m[3:]) for m in BEYOND_MODELS[:4]], className="grid g2"),
            html.H4(tx("Los modelos que se combinan", "The models being combined"), className="beyond-sub"),
            html.Div([_beyond_model_card(*m[:3], *m[3:]) for m in BEYOND_MODELS[4:]], className="grid g3"),
        ]),
        card(tx("Los candidatos congelados (fase B)", "The frozen candidates (phase B)"), [
            html.P(tx("De las 2 582 combinaciones se congelaron los 13 mejores candidatos antes de probarlos con semillas nuevas (25 pliegues). Aquí se "
                      f"muestran los {len(cand)} que no usan stacking con regresión logística como combinador. Diferencia = candidato − XGBoost.",
                      "Of the 2,582 combinations, the 13 best candidates were frozen before testing them with new seeds (25 folds). Shown here are "
                      f"the {len(cand)} that do not use logistic regression stacking as the combiner. Difference = candidate − XGBoost."), className="muted"),
            _tbl([tx("Candidato", "Candidate"), "F1", tx("Dif. F1 [IC 95 %]", "F1 diff. [95% CI]"), tx("Gana en", "Wins in"),
                  "p N-B", tx("p Wilcoxon-Holm", "Wilcoxon-Holm p")], cand_rows),
            html.Div(tx(f"Los {n_sig} de {len(cand)} candidatos superan a XGBoost con Wilcoxon-Holm (p < 0.05), pero ninguno con Nadeau-Bengio. "
                        "Por eso se diseñó HIB y se confirmó con un protocolo pre-registrado.",
                        f"{n_sig} of {len(cand)} candidates beat XGBoost with Wilcoxon-Holm (p < 0.05), but none with Nadeau-Bengio. "
                        "That is why HIB was designed and confirmed with a pre-registered protocol."), className="callout"),
        ]),
        card(tx("Wilcoxon con Holm: el ensamble supera a XGBoost", "Wilcoxon with Holm: the ensemble beats XGBoost"), [
            dcc.Graph(id="cs-beyond-wilcoxon", figure=fig_wilcoxon(), config=gcfg),
            interp_block(
                tx("Cada barra es qué tan seguros estamos de que el modelo le gana a XGBoost según Wilcoxon: pasada la línea dorada, la ventaja es "
                   "estadísticamente significativa. HIB es la que pasa más lejos. También pasa CatBoost solo: Wilcoxon es una prueba permisiva.",
                   "Each bar shows how sure we are that the model beats XGBoost according to Wilcoxon: past the golden line, the advantage is "
                   "statistically significant. HIB goes furthest. CatBoost alone also passes: Wilcoxon is a permissive test."),
                tx("Wilcoxon de rangos con signo sobre las 25 diferencias de F1 por pliegue, con Holm. Es la prueba pareada que aceptó el "
                   "profesor, pero trata los pliegues como independientes aunque comparten datos; por eso es optimista. Nadeau-Bengio, que sí "
                   "lo corrige, no rechaza para ningún candidato (p ≥ 0.17), y HIB queda en p = 0.049 sin ajustar.",
                   "Wilcoxon signed-rank on the 25 per-fold F1 differences, with Holm. It is the paired test the professor accepted, but it "
                   "treats folds as independent even though they share data, so it is optimistic. Nadeau-Bengio, which does correct for that, "
                   "does not reject for any candidate (p ≥ 0.17), and HIB is at p = 0.049 unadjusted.")),
        ]),
        card(tx("HIB: confirmación v2 (semillas nuevas, 25 pliegues)", "HIB: v2 confirmation (new seeds, 25 folds)"), [
            html.P(tx("Diferencia = HIB − modelo; p ajustados por Holm sobre 7 contrastes. En negrita, p < 0.05.",
                      "Difference = HIB − model; p adjusted by Holm over 7 contrasts. In bold, p < 0.05."), className="muted"),
            _tbl([tx("Modelo", "Model"), "F1", tx("Dif. F1", "F1 diff."), tx("Gana HIB", "HIB wins"), tx("δ de Cliff", "Cliff's δ"),
                  "Wilcoxon", "DeLong", "McNemar"],
                 [(html.B("HIB"), html.B("0.5505"), "—", "—", "—", "—", "—", "—"),
                  ("Random Forest", "0.5477", "+0.0028", "17/25", "0.24", sig("0.015"), sig("< 0.001"), sig("0.001")),
                  ("XGBoost", "0.5468", "+0.0037", "21/25", "0.29", sig("< 0.001"), sig("< 0.001"), sig("< 0.001")),
                  ("SVM", "0.5411", "+0.0094", "25/25", "0.62", sig("< 0.001"), sig("< 0.001"), sig("< 0.001")),
                  (tx("Árbol de decisión", "Decision tree"), "0.5326", "+0.0179", "25/25", "0.84", sig("< 0.001"), sig("< 0.001"), sig("0.001")),
                  (tx("Regresión logística", "Logistic regression"), "0.5266", "+0.0239", "25/25", "0.97", sig("< 0.001"), sig("< 0.001"), sig("< 0.001")),
                  ("KNN", "0.5233", "+0.0271", "25/25", "0.98", sig("< 0.001"), sig("< 0.001"), sig("< 0.001")),
                  ("Naive Bayes", "0.5106", "+0.0399", "25/25", "1.00", sig("< 0.001"), sig("< 0.001"), sig("< 0.001"))]),
            interp_block(
                tx("Con las pruebas que aceptó el profesor, HIB le gana a los 7 modelos base, también a XGBoost y Random "
                   "Forest, aunque por muy poco frente a estos dos (menos de 0.004 de F1). La primera corrida (semillas 5000 a 5004) "
                   "da lo mismo: HIB 0.5502 contra XGBoost 0.5463, Wilcoxon-Holm 0.0016.",
                   "With the tests the professor accepted, HIB beats the 7 baseline models, including XGBoost and Random "
                   "Forest, although by very little against these two (under 0.004 of F1). The first run (seeds 5000 to 5004) "
                   "gives the same: HIB 0.5502 vs XGBoost 0.5463, Wilcoxon-Holm 0.0016."),
                tx("Friedman global p ≈ 10⁻³⁰; rango medio de HIB 1.48 (Random Forest 2.28, XGBoost 2.52). No rechazan "
                   "frente a XGBoost y Random Forest: Nadeau-Bengio (p sin ajustar 0.049 y 0.31) y Nemenyi (0.81 y 0.94). "
                   "Wilcoxon trata los pliegues como independientes y DeLong y McNemar usan predicciones agrupadas: las "
                   "tres dan p optimistas con validación repetida.",
                   "Global Friedman p ≈ 10⁻³⁰; HIB mean rank 1.48 (Random Forest 2.28, XGBoost 2.52). Not rejecting "
                   "against XGBoost and Random Forest: Nadeau-Bengio (unadjusted p 0.049 and 0.31) and Nemenyi (0.81 and "
                   "0.94). Wilcoxon treats folds as independent and DeLong and McNemar use pooled predictions: all three "
                   "give optimistic p-values with repeated validation.")),
        ]),
        card(tx("Diferencia frente a XGBoost", "Difference vs XGBoost"), [
            dcc.Graph(id="cs-beyond-diff", figure=fig_beyond_diff(), config=gcfg),
            interp_block(
                tx("Cada punto es cuánto mejor (a la derecha) o peor (a la izquierda) es un modelo que XGBoost, y la línea "
                   "es el margen de duda. Los ensambles quedan a la derecha del cero, pero todas las líneas tocan o cruzan el cero y quedan "
                   "dentro de la franja de «prácticamente iguales»: la ventaja es real con Wilcoxon, pero pequeña.",
                   "Each dot is how much better (right) or worse (left) a model is than XGBoost, and the line is the "
                   "margin of doubt. The ensembles sit to the right of zero, but every line touches or crosses zero and stays inside the "
                   "«practically equal» band: the advantage is real with Wilcoxon, but small."),
                tx("IC 95 % de la t corregida de Nadeau-Bengio, que multiplica la varianza por 1/J + n_prueba/n_entrenamiento "
                   "porque los pliegues comparten datos. Cada modelo se compara con el XGBoost de su propia corrida "
                   "(particiones distintas). Los IC de HIB se reconstruyeron desde la diferencia y el p sin ajustar. "
                   "Franja gris: ROPE de ±0.01.",
                   "95% CI of the Nadeau-Bengio corrected t, which multiplies the variance by 1/J + n_test/n_train because "
                   "folds share data. Each model is compared with the XGBoost of its own run (different partitions). "
                   "HIB's CIs were rebuilt from the difference and the unadjusted p. Grey band: ROPE of ±0.01.")),
        ]),
        card(tx("La meseta del F1", "The F1 plateau"), [
            dcc.Graph(id="cs-beyond-plateau", figure=fig_beyond_plateau(), config=gcfg),
            interp_block(
                tx("Bosques, boosting, nuestro bosque oblicuo y los ensambles terminan casi en el mismo F1. Cuando "
                   "modelos tan distintos chocan con el mismo techo, el límite está en la información de los datos, no "
                   "en el modelo.",
                   "Forests, boosting, our oblique forest and the ensembles end up at almost the same F1. When such "
                   "different models hit the same ceiling, the limit is in the information in the data, not in the model."),
                tx("F1 medio con el umbral elegido en el entrenamiento. Excepto la regresión logística y Rotation Forest, "
                   "los otros 7 modelos caen en 0.0048 de F1, cuando el F1 de un mismo modelo varía unos 0.01 entre pliegues. "
                   "La literatura sobre este conjunto reporta el mismo techo (F1 ≈ 0.55, AUC ≈ 0.78).",
                   "Mean F1 with the threshold chosen on training data. Except logistic regression and Rotation Forest, "
                   "the other 7 models fall within 0.0048 of F1, while a single model's F1 varies about 0.01 across folds. "
                   "The literature on this dataset reports the same ceiling (F1 ≈ 0.55, AUC ≈ 0.78).")),
        ]),
        card(tx("¿De dónde sale la ventaja de HIB?", "Where does HIB's advantage come from?"), [
            html.P(tx("La regla de HIB frente a reglas estándar con los mismos 8 modelos (comparación exploratoria).",
                      "HIB's rule vs standard rules with the same 8 models (exploratory comparison)."), className="muted"),
            _tbl([tx("Regla", "Rule"), "F1", tx("HIB − regla", "HIB − rule"), tx("Gana HIB", "HIB wins"), "Wilcoxon"],
                 [(html.B(tx("HIB (F1 suave)", "HIB (soft F1)")), html.B("0.5505"), "—", "—", "—"),
                  (tx("Promedio uniforme de logits", "Uniform logit average"), "0.5501", "+0.0004", "15/25", "0.33"),
                  (tx("Promedio de probabilidades", "Probability average"), "0.5501", "+0.0004", "16/25", "0.30"),
                  (tx("Selección de Caruana", "Caruana selection"), "0.5494", "+0.0011", "14/25", "0.12")]),
            html.Div(tx("La ventaja viene de combinar 8 modelos, no de la regla de pesos: un promedio simple logra lo mismo. "
                        "Quitar CS-FOF tampoco cambia nada (0.5505 sin él, 0.5502 con él).",
                        "The advantage comes from combining 8 models, not from the weighting rule: a plain average does "
                        "the same. Removing CS-FOF does not change anything either (0.5505 without it, 0.5502 with it)."),
                     className="callout"),
        ]),
        card(tx("¿Por qué no mejora más el score?", "Why doesn't the score improve more?"), [
            html.Ul([
                html.Li([html.B(tx("Las diferencias son del tamaño del ruido. ", "The differences are noise-sized. ")),
                         tx("El F1 de un mismo modelo varía unos 0.01 entre pliegues; las ventajas observadas son de 0.002 a "
                            "0.004, y para ser claras necesitarían 0.005 a 0.007.",
                            "A single model's F1 varies about 0.01 across folds; the observed gains are 0.002 to 0.004, and "
                            "to be clear they would need 0.005 to 0.007.")]),
                html.Li([html.B(tx("El límite está en los datos. ", "The limit is in the data. ")),
                         tx("La señal dominante es el atraso reciente (PAY_0, PAY_2) y todos los modelos la capturan igual; "
                            "en los clientes al día (77 % de la cartera) ninguno pasa de F1 0.29.",
                            "The dominant signal is recent delay (PAY_0, PAY_2) and every model captures it equally; among "
                            "clients who are up to date (77% of the portfolio) none goes above F1 0.29.")]),
                html.Li([html.B(tx("Los modelos se equivocan en los mismos clientes. ", "The models miss the same clients. ")),
                         tx("Por eso combinarlos suma poco y quitar CS-FOF no cambia nada.",
                            "That is why combining them adds little and removing CS-FOF changes nothing.")]),
                html.Li([html.B(tx("Ordenar mejor no es clasificar mejor. ", "Ranking better is not classifying better. ")),
                         tx("Balancear o combinar modelos cambia sobre todo el orden de los clientes (AUC); una mejora "
                            "del orden reordena pocos clientes cerca del umbral, así que el F1 casi no cambia.",
                            "Balancing or combining models mostly changes the ranking of clients (AUC); a better ranking "
                            "reorders few clients near the threshold, so F1 barely changes.")]),
            ], className="beyond-list"),
            html.Div(tx("Con estos datos, una mejora sustancial del score es muy improbable: la única vía realista sería "
                        "agregar información nueva (otras variables u otros periodos), no cambiar de modelo.",
                        "With this data, a substantial score improvement is very unlikely: the only realistic path would be "
                        "adding new information (other features or periods), not changing the model."), className="callout"),
        ]),
        card(tx("Lo que hay que decir con honestidad", "What must be said honestly"), [
            html.Ul([
                html.Li(tx("La ventaja de HIB (+0.0037 de F1, ≈ 0.7 % relativo) es pequeña: Nadeau-Bengio, que corrige la dependencia entre "
                           "pliegues, no rechaza frente a XGBoost (p = 0.049 sin ajustar, no sobrevive a Holm).",
                           "HIB's advantage (+0.0037 F1, ≈ 0.7% relative) is small: Nadeau-Bengio, which corrects for dependence between "
                           "folds, does not reject against XGBoost (p = 0.049 unadjusted, it does not survive Holm).")),
                html.Li(tx("La ventaja viene de combinar 8 modelos: un promedio simple de los mismos modelos logra +0.0004 menos (p = 0.33). "
                           "La regla de pesos y CS-FOF no cambian el resultado de forma medible.",
                           "The advantage comes from combining 8 models: a plain average of the same models is only 0.0004 lower (p = 0.33). "
                           "The weighting rule and CS-FOF do not change the result measurably.")),
                html.Li(tx("Se evaluaron más de 2 600 diseños antes de HIB; las semillas nuevas en cada etapa lo mitigan, pero la ventaja observada "
                           "del mejor de muchos tiende a estar inflada.",
                           "More than 2,600 designs were evaluated before HIB; new seeds at each stage mitigate this, but the observed "
                           "advantage of the best of many tends to be inflated.")),
                html.Li(tx("Solo se evaluó en Taiwán (2005), con particiones distintas para cada corrida: cada una se compara con el XGBoost de su propia corrida.",
                           "It was evaluated only on Taiwan (2005), with different partitions for each run: each is compared with the XGBoost of its own run.")),
            ], className="beyond-list"),
        ]),
    ]
