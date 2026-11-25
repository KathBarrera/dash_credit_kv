# -*- coding: utf-8 -*-
"""Pestaña «5 · ¿Se puede mejorar?» del Modelo original: ensambles, HIB y redes neuronales frente a XGBoost."""

import plotly.graph_objects as go
from dash import dcc, html

from tablero.componentes import _tbl, card, interp_block, kpi
from tablero.config import BROWN, DEEP_NAVY, DEEP_RGBA, GREY_BLUE, L, NAVY, WARM_GOLD, WHITE, tx
from tablero.iconos import icon
from tablero.utilidades import style_fig


# --- Pestaña 5: ¿se puede mejorar? (ensambles, HIB y redes neuronales) -----------------------
# Fuentes: Tabla_combinaciones.xlsx y el documento de HIB (corridas de ensambles, 25 pliegues) y
# results/redes_repeated/metricas.csv del repositorio del proyecto (redes neuronales, 50 pliegues).
# Diferencia = modelo − XGBoost de su propia corrida; IC 95 % de la t corregida de Nadeau-Bengio.
# Los IC de HIB se reconstruyeron a partir de la diferencia y del p sin ajustar reportados.
BEYOND_DIFF = [  # (etiqueta es, etiqueta en, diferencia, IC inf, IC sup, p NB, grupo)
    ("HIB, confirmación v2", "HIB, confirmation v2", 0.0037, 0.0000, 0.0074, 0.049, "hib"),
    ("HIB, primera corrida v1", "HIB, first run v1", 0.0039, -0.0018, 0.0096, 0.17, "hib"),
    ("Stacking LR: XGBoost(4) + CatBoost + Extra Trees", "LR stacking: XGBoost(4) + CatBoost + Extra Trees", 0.0040, -0.0014, 0.0093, 0.14, "ens"),
    ("Promedio: CS-FOF + 4 boosting", "Average: CS-FOF + 4 boosting", 0.0038, -0.0020, 0.0096, 0.19, "ens"),
    ("CatBoost", "CatBoost", 0.0037, -0.0015, 0.0089, 0.16, "ens"),
    ("Selección de Caruana, 10 modelos", "Caruana selection, 10 models", 0.0030, -0.0014, 0.0074, 0.17, "ens"),
    ("FWLS por PAY_0 con CS-FOF", "FWLS by PAY_0 with CS-FOF", 0.0024, -0.0011, 0.0060, 0.17, "ens"),
    ("FWLS por PAY_0 sin CS-FOF", "FWLS by PAY_0 without CS-FOF", 0.0024, -0.0011, 0.0059, 0.17, "ens"),
    ("CS-FOF (umbral interno)", "CS-FOF (inner threshold)", 0.0016, -0.0018, 0.0049, 0.35, "ens"),
    ("Rotation Forest propio", "Own Rotation Forest", -0.0036, -0.0087, 0.0015, 0.16, "ens"),
    ("TabPFN v2.5", "TabPFN v2.5", 0.0023, -0.0023, 0.0070, 0.32, "red"),
    ("TabM", "TabM", -0.0025, -0.0088, 0.0038, 0.43, "red"),
    ("TabM-Fisher", "TabM-Fisher", -0.0025, -0.0095, 0.0044, 0.47, "red"),
]
BEYOND_PLATEAU = [  # (modelo, F1 medio, grupo)
    ("Regresión logística|Logistic regression", 0.5230, "ens"), ("Rotation Forest", 0.5421, "ens"),
    ("TabM-Fisher", 0.5439, "red"), ("TabM", 0.5439, "red"), ("XGBoost (ensambles)|XGBoost (ensembles)", 0.5457, "ens"),
    ("Random Forest", 0.5461, "ens"), ("XGBoost (redes)|XGBoost (networks)", 0.5464, "red"), ("LightGBM", 0.5467, "ens"),
    ("CS-FOF", 0.5473, "ens"), ("TabPFN v2.5", 0.5487, "red"), ("CatBoost", 0.5494, "ens"),
    ("Mejor stacking (fase B)|Best stacking (phase B)", 0.5501, "ens"), ("HIB v2", 0.5505, "hib"),
]
BEYOND_COLORS = {"ens": NAVY, "hib": WARM_GOLD, "red": BROWN}
BEYOND_SYMBOLS = {"ens": "circle", "hib": "diamond", "red": "square"}


def _beyond_group(g):
    return {"ens": tx("Ensambles y modelos base (25 pliegues)", "Ensembles and base models (25 folds)"),
            "hib": tx("HIB, ensamble propuesto (25 pliegues)", "HIB, proposed ensemble (25 folds)"),
            "red": tx("Redes neuronales (50 pliegues)", "Neural networks (50 folds)")}[g]


def fig_beyond_diff():
    """Diferencia de F1 frente a XGBoost con su IC 95 %, con la región de equivalencia práctica (±0.01)."""
    rows = list(reversed(BEYOND_DIFF))
    fig = go.Figure()
    fig.add_vrect(x0=-0.01, x1=0.01, fillcolor=f"{DEEP_RGBA}0.06)", line_width=0, layer="below")
    fig.add_vline(x=0, line_color=DEEP_NAVY, line_width=1.2)
    vistos = set()
    for es, en, d, lo, hi, p, g in rows:
        y = tx(es, en)
        fig.add_trace(go.Scatter(
            x=[d], y=[y], mode="markers", marker=dict(size=11, color=BEYOND_COLORS[g], symbol=BEYOND_SYMBOLS[g], line=dict(width=1.5, color=WHITE)),
            error_x=dict(type="data", symmetric=False, array=[hi - d], arrayminus=[d - lo], color=BEYOND_COLORS[g],
                         thickness=2.4, width=0),
            name=_beyond_group(g), legendgroup=g, showlegend=g not in vistos,
            hovertemplate=(f"<b>{y}</b><br>" + tx("Dif. F1", "F1 diff.") + f": {d:+.4f}<br>IC 95 %: [{lo:+.4f}, {hi:+.4f}]"
                           f"<br>p Nadeau-Bengio: {p:.3f}<extra></extra>")))
        vistos.add(g)
    fig.add_annotation(x=0.0098, y=1.0, yref="paper", text=tx("Equivalencia práctica ±0.01", "Practical equivalence ±0.01"),
                       showarrow=False, xanchor="right", yanchor="bottom", font=dict(size=11, color=GREY_BLUE))
    style_fig(fig, h=560, title=tx("Diferencia de F1 frente a XGBoost (IC 95 %)", "F1 difference vs XGBoost (95% CI)"),
              xaxis=dict(title=tx("F1 del modelo − F1 de XGBoost", "Model F1 − XGBoost F1"), range=[-0.0125, 0.0125],
                         tickformat="+.3f"),
              yaxis=dict(automargin=True))
    fig.update_layout(margin=dict(l=20, r=30, t=80, b=120),
                      legend=dict(orientation="h", yanchor="top", y=-0.14, xanchor="center", x=0.5))
    return fig


def fig_beyond_plateau():
    """F1 medio de cada modelo: la «meseta» en la que quedan casi todos."""
    rows = sorted(BEYOND_PLATEAU, key=lambda r: r[1])
    nombre = lambda s: tx(*s.split("|")) if "|" in s else s
    fig = go.Figure()
    fig.add_vrect(x0=0.5439, x1=0.5505, fillcolor=f"{DEEP_RGBA}0.06)", line_width=0, layer="below")
    vistos = set()
    for s, v, g in rows:
        fig.add_trace(go.Scatter(
            x=[v], y=[nombre(s)], mode="markers+text", text=[f"{v:.4f}"], textposition="middle right",
            textfont=dict(size=11, color=DEEP_NAVY),
            marker=dict(size=12, color=BEYOND_COLORS[g], symbol=BEYOND_SYMBOLS[g], line=dict(width=1.5, color=WHITE)),
            name=_beyond_group(g), legendgroup=g, showlegend=g not in vistos,
            hovertemplate=f"<b>{nombre(s)}</b><br>F1: {v:.4f}<extra></extra>"))
        vistos.add(g)
    fig.add_annotation(x=0.5472, y=1.0, yref="paper", showarrow=False, yanchor="bottom", font=dict(size=11, color=GREY_BLUE),
                       text=tx("11 de 13 modelos en 0.0066 de F1", "11 of 13 models within 0.0066 of F1"))
    style_fig(fig, h=520, title=tx("La meseta del F1", "The F1 plateau"),
              xaxis=dict(title=tx("F1 medio de la clase default", "Mean F1 of the default class"), range=[0.52, 0.558]),
              yaxis=dict(automargin=True))
    fig.update_layout(margin=dict(l=20, r=30, t=80, b=120),
                      legend=dict(orientation="h", yanchor="top", y=-0.14, xanchor="center", x=0.5))
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
    ("Stacking con regresión logística", "Logistic regression stacking", ("Combinador", "Combiner"),
     ("Un «jefe» aprende cuánto confiar en cada experto, mirando cómo les fue con clientes que no habían visto.",
      "A «boss» learns how much to trust each expert, looking at how they did with clients they had not seen."),
     ("Meta-modelo logístico sobre los logits fuera de pliegue (out-of-fold) de los modelos base, calculados con "
      "validación cruzada interna para evitar fuga de información. Los coeficientes son los pesos; el umbral se elige "
      "después para maximizar el F1.",
      "Logistic meta-model on the base models' out-of-fold logits, computed with inner cross-validation to avoid "
      "leakage. The coefficients are the weights; the threshold is then chosen to maximize F1.")),
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
    ("TabM", "TabM", ("Red neuronal", "Neural network"),
     ("Una red neuronal que en realidad son 32 redes pequeñas que comparten casi todo su «cerebro» y votan juntas.",
      "A neural network that is really 32 small networks sharing almost all of their «brain» and voting together."),
     ("Gorishniy et al. (ICLR 2025): MLP con BatchEnsemble, k = 32 miembros que comparten los pesos y solo difieren en "
      "adaptadores multiplicativos. Cada miembro se entrena con su propia pérdida y la predicción promedia los k. Aquí: "
      "entropía cruzada ponderada por el costo del moroso, AdamW y parada temprana.",
      "Gorishniy et al. (ICLR 2025): MLP with BatchEnsemble, k = 32 members that share the weights and differ only in "
      "multiplicative adapters. Each member is trained with its own loss and the prediction averages the k. Here: "
      "cross-entropy weighted by the cost of a defaulter, AdamW and early stopping.")),
    ("TabM-Fisher", "TabM-Fisher", ("Red neuronal propia", "Own neural network"),
     ("TabM al que le damos como pista las «líneas diagonales» que ya encontró CS-FOF, para que se concentre en lo "
      "que CS-FOF no ve.",
      "TabM given, as a hint, the «diagonal lines» that CS-FOF already found, so it can focus on what CS-FOF misses."),
     ("Dentro de cada entrenamiento se ajusta un CS-FOF auxiliar (50 árboles, cortes de profundidad ≤ 2). Sus 16 "
      "cortes oblicuos (v, t) se convierten en variables vᵀx − t (distancia con signo a cada frontera) y se agregan a "
      "las 20 variables. La ablación contra TabM mide si esas variables aportan.",
      "Inside each training set an auxiliary CS-FOF is fitted (50 trees, splits of depth ≤ 2). Its 16 oblique splits "
      "(v, t) become features vᵀx − t (signed distance to each boundary) added to the 20 features. The ablation "
      "against TabM measures whether those features help.")),
    ("TabPFN v2.5", "TabPFN v2.5", ("Red preentrenada", "Pretrained network"),
     ("Un modelo que ya «vio» millones de problemas inventados y resuelve el nuestro sin entrenarse: mira nuestros "
      "clientes como ejemplos y predice.",
      "A model that has already «seen» millions of made-up problems and solves ours without training: it looks at our "
      "clients as examples and predicts."),
     ("Transformer preentrenado sobre tablas sintéticas generadas desde un prior bayesiano (Grinsztajn et al., 2025). "
      "Hace aprendizaje en contexto: aproxima la distribución predictiva posterior en una sola pasada, sin búsqueda "
      "de hiperparámetros. Al ser preentrenado, no cuenta como modelo original en el curso.",
      "Transformer pretrained on synthetic tables generated from a Bayesian prior (Grinsztajn et al., 2025). It does "
      "in-context learning: it approximates the posterior predictive distribution in one pass, with no "
      "hyperparameter search. Being pretrained, it does not count as an original model in the course.")),
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


def csfof_beyond():
    gcfg = {"displaylogo": False}
    sig = lambda s: html.B(s)
    return [
        card(tx("¿Se puede superar a XGBoost?", "Can XGBoost be beaten?"), [
            html.P(tx("Como CS-FOF empató con XGBoost, el equipo probó dos caminos más: combinar modelos (ensambles, "
                      "stacking y un ensamble propio, HIB) y redes neuronales (TabM, TabM-Fisher y TabPFN). Esta pestaña "
                      "resume qué se probó, cómo funciona cada modelo y qué se encontró.",
                      "Since CS-FOF tied with XGBoost, the team tried two more paths: combining models (ensembles, "
                      "stacking and an own ensemble, HIB) and neural networks (TabM, TabM-Fisher and TabPFN). This tab "
                      "summarizes what was tried, how each model works and what was found."), className="muted"),
            html.Div([
                kpi("HIB", "+0.0037", tx("F1 sobre XGBoost; gana en 21 de 25 pliegues", "F1 over XGBoost; wins 21 of 25 folds"), "trophy"),
                kpi(tx("HIB frente al promedio simple", "HIB vs plain average"), "+0.0004",
                    tx("p = 0.33: la regla de pesos no aporta", "p = 0.33: the weighting rule adds nothing"), "layers"),
                kpi("TabM-Fisher", "−0.0025", tx("F1 frente a XGBoost; p = 0.47", "F1 vs XGBoost; p = 0.47"), "bars"),
                kpi(tx("Techo del dato", "Data ceiling"), "0.54–0.55",
                    tx("F1 de casi todos los modelos, sin importar la familia", "F1 of almost every model, whatever the family"), "target"),
            ], className="kpi-row k4"),
        ]),
        card(tx("Los modelos que se probaron", "The models that were tried"), [
            html.P(tx("Cada tarjeta da la idea en palabras sencillas; el botón abre la explicación técnica.",
                      "Each card gives the idea in plain words; the button opens the technical explanation."), className="muted"),
            html.H4(tx("Formas de combinar modelos", "Ways to combine models"), className="beyond-sub"),
            html.Div([_beyond_model_card(*m[:3], *m[3:]) for m in BEYOND_MODELS[:5]], className="grid g3"),
            html.H4(tx("Modelos base añadidos", "Added base models"), className="beyond-sub"),
            html.Div([_beyond_model_card(*m[:3], *m[3:]) for m in BEYOND_MODELS[5:10]], className="grid g3"),
            html.H4(tx("Redes neuronales", "Neural networks"), className="beyond-sub"),
            html.Div([_beyond_model_card(*m[:3], *m[3:]) for m in BEYOND_MODELS[10:]], className="grid g3"),
        ]),
        card(tx("Diferencia frente a XGBoost", "Difference vs XGBoost"), [
            dcc.Graph(id="cs-beyond-diff", figure=fig_beyond_diff(), config=gcfg),
            interp_block(
                tx("Cada punto es cuánto mejor (a la derecha) o peor (a la izquierda) es un modelo que XGBoost, y la línea "
                   "es el margen de duda. Todas las líneas tocan o cruzan el cero y quedan dentro de la franja de "
                   "«prácticamente iguales»: ningún modelo le saca una ventaja clara.",
                   "Each dot is how much better (right) or worse (left) a model is than XGBoost, and the line is the "
                   "margin of doubt. Every line touches or crosses zero and stays inside the «practically equal» band: "
                   "no model gets a clear lead."),
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
                tx("Bosques, boosting, ensambles, redes y un modelo preentrenado terminan casi en el mismo F1. Cuando "
                   "modelos tan distintos chocan con el mismo techo, el límite está en la información de los datos, no "
                   "en el modelo.",
                   "Forests, boosting, ensembles, networks and a pretrained model end up at almost the same F1. When such "
                   "different models hit the same ceiling, the limit is in the information in the data, not in the model."),
                tx("F1 medio con el umbral elegido en el entrenamiento. Excepto la regresión logística y Rotation Forest, "
                   "los otros 11 modelos caen en 0.0066 de F1, cuando el F1 de un mismo modelo varía unos 0.01 entre pliegues. "
                   "La literatura sobre este conjunto reporta el mismo techo (F1 ≈ 0.55, AUC ≈ 0.78).",
                   "Mean F1 with the threshold chosen on training data. Except logistic regression and Rotation Forest, "
                   "the other 11 models fall within 0.0066 of F1, while a single model's F1 varies about 0.01 across folds. "
                   "The literature on this dataset reports the same ceiling (F1 ≈ 0.55, AUC ≈ 0.78).")),
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
                   "Forest, aunque por muy poco frente a estos dos (menos de 0.004 de F1).",
                   "With the tests the professor accepted, HIB beats the 7 base models, including XGBoost and Random "
                   "Forest, although by very little against these two (under 0.004 of F1)."),
                tx("Friedman global p ≈ 10⁻³⁰; rango medio de HIB 1.48 (Random Forest 2.28, XGBoost 2.52). No rechazan "
                   "frente a XGBoost y Random Forest: Nadeau-Bengio (p sin ajustar 0.049 y 0.31) y Nemenyi (0.81 y 0.94). "
                   "Wilcoxon trata los pliegues como independientes y DeLong y McNemar usan predicciones agrupadas: las "
                   "tres dan p optimistas con validación repetida.",
                   "Global Friedman p ≈ 10⁻³⁰; HIB mean rank 1.48 (Random Forest 2.28, XGBoost 2.52). Not rejecting "
                   "against XGBoost and Random Forest: Nadeau-Bengio (unadjusted p 0.049 and 0.31) and Nemenyi (0.81 and "
                   "0.94). Wilcoxon treats folds as independent and DeLong and McNemar use pooled predictions: all three "
                   "give optimistic p-values with repeated validation.")),
        ]),
        card(tx("¿De dónde sale la ventaja de HIB?", "Where does HIB's advantage come from?"), [
            html.P(tx("La regla de HIB frente a reglas estándar con los mismos 8 modelos (comparación exploratoria).",
                      "HIB's rule vs standard rules with the same 8 models (exploratory comparison)."), className="muted"),
            _tbl([tx("Regla", "Rule"), "F1", tx("HIB − regla", "HIB − rule"), tx("Gana HIB", "HIB wins"), "Wilcoxon"],
                 [(html.B(tx("HIB (F1 suave)", "HIB (soft F1)")), html.B("0.5505"), "—", "—", "—"),
                  (tx("Promedio uniforme de logits", "Uniform logit average"), "0.5501", "+0.0004", "15/25", "0.33"),
                  (tx("Promedio de probabilidades", "Probability average"), "0.5501", "+0.0004", "16/25", "0.30"),
                  (tx("Stacking con regresión logística", "Logistic regression stacking"), "0.5497", "+0.0008", "17/25", "0.12"),
                  (tx("Selección de Caruana", "Caruana selection"), "0.5494", "+0.0011", "14/25", "0.12")]),
            html.Div(tx("La ventaja viene de combinar 8 modelos, no de la regla de pesos: un promedio simple logra lo mismo. "
                        "Quitar CS-FOF tampoco cambia nada (0.5505 sin él, 0.5502 con él).",
                        "The advantage comes from combining 8 models, not from the weighting rule: a plain average does "
                        "the same. Removing CS-FOF does not change anything either (0.5505 without it, 0.5502 with it)."),
                     className="callout"),
        ]),
        card(tx("Redes neuronales (50 pliegues)", "Neural networks (50 folds)"), [
            html.P(tx("10 repeticiones × 5 pliegues con las mismas particiones para los cuatro modelos, en GPU.",
                      "10 repetitions × 5 folds with the same partitions for the four models, on GPU."), className="muted"),
            _tbl([tx("Modelo", "Model"), "F1", tx("Dif. F1 [IC 95 %]", "F1 diff. [95% CI]"), "p Nadeau-Bengio",
                  tx("Gana en", "Wins in"), "AUC-ROC"],
                 [("TabPFN v2.5", "0.5487", "+0.0023 [−0.0023, 0.0070]", "0.32", "38/50", html.B("0.7894")),
                  ("XGBoost", "0.5464", "—", "—", "—", "0.7850"),
                  ("TabM", "0.5439", "−0.0025 [−0.0088, 0.0038]", "0.43", "17/50", "0.7826"),
                  (html.B("TabM-Fisher"), "0.5439", "−0.0025 [−0.0095, 0.0044]", "0.47", "18/50", "0.7824")]),
            interp_block(
                tx("Ninguna red le gana a XGBoost en F1, y darle a TabM las «líneas» de CS-FOF no cambia nada. TabPFN "
                   "ordena mejor a los clientes por riesgo, pero eso no se traduce en más aciertos.",
                   "No network beats XGBoost in F1, and giving TabM the «lines» from CS-FOF changes nothing. TabPFN ranks "
                   "clients by risk better, but that does not turn into more hits."),
                tx("Prueba bayesiana con ROPE ±0.01: 98 a 100 % de probabilidad de equivalencia práctica en F1. Ablación "
                   "TabM-Fisher − TabM: 0.0000 [−0.0043, 0.0043], p = 0.99. TabPFN supera a XGBoost en AUC-ROC (+0.0045, "
                   "p = 0.0001, 49/50 pliegues) y AUC-PR (+0.0083, p = 0.003): mejora el orden global, pero casi no "
                   "mueve clientes cerca del umbral.",
                   "Bayesian test with ROPE ±0.01: 98 to 100% probability of practical equivalence in F1. TabM-Fisher − "
                   "TabM ablation: 0.0000 [−0.0043, 0.0043], p = 0.99. TabPFN beats XGBoost in ROC-AUC (+0.0045, "
                   "p = 0.0001, 49/50 folds) and PR-AUC (+0.0083, p = 0.003): it improves the overall ranking but barely "
                   "moves clients near the threshold.")),
        ]),
        card(tx("¿Por qué no mejora el score?", "Why doesn't the score improve?"), [
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
                         tx("Una mejora del AUC reordena pocos clientes cerca del umbral, así que el F1 casi no cambia.",
                            "An AUC gain reorders few clients near the threshold, so F1 barely changes.")]),
            ], className="beyond-list"),
            html.Div(tx("Con estos datos, una mejora sustancial del score es muy improbable: la única vía realista sería "
                        "agregar información nueva (otras variables u otros periodos), no cambiar de modelo.",
                        "With this data, a substantial score improvement is very unlikely: the only realistic path would be "
                        "adding new information (other features or periods), not changing the model."), className="callout"),
        ]),
    ]
