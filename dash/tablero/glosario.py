# -*- coding: utf-8 -*-
"""Glosario de símbolos de las ecuaciones (CS-FOF y HIB).

Cada símbolo tiene un nombre y una explicación en español e inglés. Con ese glosario, assets/ecuaciones.js:
  - reconoce los símbolos dentro de las ecuaciones que dibuja MathJax (por su forma, p. ej. «S_w» o «n_0»),
  - muestra una burbuja con el significado al pasar el cursor (o tocar) un símbolo, y
  - ilumina todos los lugares donde se usa: las demás ecuaciones, los textos y los identificadores del código.

Un símbolo del texto se escribe con V("S_w", "csfof"); uno del código se declara en CODIGO.
Una ecuación va envuelta con fx(tex, scope) para que sepa a qué glosario pertenece.
"""

import json
import re

from dash import dcc, html

from tablero.config import tx
from tablero.iconos import icon

# Los dos glosarios («ámbitos»): un mismo símbolo puede significar otra cosa en cada uno (p. ej. t, w).
CSFOF, HIB = "csfof", "hib"

H = "̂"   # acento circunflejo combinado: p̂

# token: (símbolo para mostrar, (nombre ES, explicación ES), (nombre EN, explicación EN))
GLOSARIO = {
    CSFOF: {
        "w_i": ("wᵢ", ("Peso de costo del cliente i", "Vale c si el cliente incumple y 1 si paga. Hace que no detectar a un moroso cueste más que una falsa alarma."),
                ("Cost weight of client i", "It is c if the client defaults and 1 if they pay, so missing a defaulter costs more than a false alarm.")),
        "y_i": ("yᵢ", ("Etiqueta del cliente i", "1 = incumple el pago del mes siguiente; 0 = paga."),
                ("Label of client i", "1 = defaults next month; 0 = pays.")),
        "c": ("c", ("Costo de no detectar un moroso", "c = n₀/n₁ (≈ 3.5 con 22 % de morosos): iguala el peso total de las dos clases."),
              ("Cost of missing a defaulter", "c = n₀/n₁ (≈ 3.5 with 22% defaulters): it equalizes the total weight of the two classes.")),
        "n_0": ("n₀", ("Clientes que pagan", "Cuántos clientes del entrenamiento pagan (y = 0)."),
                ("Clients who pay", "How many training clients pay (y = 0).")),
        "n_1": ("n₁", ("Clientes que incumplen", "Cuántos clientes del entrenamiento incumplen (y = 1)."),
                ("Clients who default", "How many training clients default (y = 1).")),
        "\U0001D7D9": ("𝟙{·}", ("Función indicadora", "Vale 1 si la condición entre llaves se cumple y 0 si no."),
                       ("Indicator function", "It is 1 if the condition in braces holds and 0 otherwise.")),
        "G": ("G(L, R)", ("Impureza de Gini ponderada", "Qué tan mezclados quedan pagadores y morosos después del corte; menor G = mejor corte."),
              ("Weighted Gini impurity", "How mixed payers and defaulters are after the cut; lower G = better cut.")),
        "L": ("L", ("Hijo izquierdo", "Clientes que caen a la izquierda del corte."), ("Left child", "Clients that fall to the left of the cut.")),
        "R": ("R", ("Hijo derecho", "Clientes que caen a la derecha del corte."), ("Right child", "Clients that fall to the right of the cut.")),
        "A": ("A", ("Un lado del corte", "A es L (izquierda) o R (derecha)."), ("One side of the cut", "A is L (left) or R (right).")),
        "W_L": ("W_L", ("Peso de la izquierda", "Suma de los pesos wᵢ de los clientes que caen a la izquierda."),
                ("Weight on the left", "Sum of the weights wᵢ of the clients that fall to the left.")),
        "W_R": ("W_R", ("Peso de la derecha", "Suma de los pesos wᵢ de los clientes que caen a la derecha."),
                ("Weight on the right", "Sum of the weights wᵢ of the clients that fall to the right.")),
        "p_L": ("p_L", ("Morosos a la izquierda", "Proporción ponderada de morosos entre los clientes de la izquierda."),
                ("Defaulters on the left", "Weighted share of defaulters among the clients on the left.")),
        "p_R": ("p_R", ("Morosos a la derecha", "Proporción ponderada de morosos entre los clientes de la derecha."),
                ("Defaulters on the right", "Weighted share of defaulters among the clients on the right.")),
        "p_A": ("p_A", ("Morosos en el lado A", "Proporción ponderada de morosos: Σ wᵢ yᵢ / Σ wᵢ sobre los clientes del lado A."),
                ("Defaulters on side A", "Weighted share of defaulters: Σ wᵢ yᵢ / Σ wᵢ over the clients on side A.")),
        "x_i,F": ("x_{i,F}", ("Cliente i con q variables", "El cliente i descrito solo con las q variables que se sortearon en este nodo (el conjunto F)."),
                  ("Client i with q variables", "Client i described only by the q variables drawn at this node (the set F).")),
        "x": ("x", ("Un cliente", "Vector con las variables del cliente cuya probabilidad se quiere predecir."),
              ("A client", "Vector of variables of the client whose probability is being predicted.")),
        "μ_y_i": ("μ_{yᵢ}", ("Media de la clase del cliente i", "Media ponderada de las variables de la clase (paga o incumple) a la que pertenece el cliente i."),
                       ("Mean of client i's class", "Weighted mean of the variables of the class (pays or defaults) the client belongs to.")),
        "μ_0": ("μ₀", ("Media de los que pagan", "Media ponderada por costo de las variables de los clientes que pagan, dentro del nodo."),
                     ("Mean of payers", "Cost-weighted mean of the variables of the clients who pay, inside the node.")),
        "μ_1": ("μ₁", ("Media de los que incumplen", "Media ponderada por costo de las variables de los clientes que incumplen, dentro del nodo."),
                     ("Mean of defaulters", "Cost-weighted mean of the variables of the clients who default, inside the node.")),
        "S_w": ("S_w", ("Dispersión intra-clase", "Matriz q×q: qué tanto se dispersan los clientes alrededor de la media de su clase, ponderada por costo y regularizada con ε."),
                ("Within-class scatter", "q×q matrix: how much clients spread around their class mean, cost-weighted and regularized with ε.")),
        "S": ("S", ("Dispersión sin regularizar", "La dispersión intra-clase antes de sumarle ε·tr(S)/q a la diagonal."),
              ("Unregularized scatter", "The within-class scatter before adding ε·tr(S)/q to the diagonal.")),
        "ε": ("ε", ("Regularización", "Evita que S_w sea casi singular (los montos facturados son casi colineales). Modelo final: ε = 0.324."),
                   ("Regularization", "Keeps S_w from being nearly singular (billed amounts are nearly collinear). Final model: ε = 0.324.")),
        "tr": ("tr(S)", ("Traza", "Suma de la diagonal de S; tr(S)/q es la varianza media por variable."),
               ("Trace", "Sum of the diagonal of S; tr(S)/q is the mean variance per variable.")),
        "q": ("q", ("Variables sorteadas por nodo", "Cuántas variables se eligen al azar en cada nodo (max_features = log2 en el modelo final)."),
              ("Variables drawn per node", "How many variables are drawn at random at each node (max_features = log2 in the final model).")),
        "I_q": ("I_q", ("Matriz identidad", "Matriz q×q con unos en la diagonal."), ("Identity matrix", "q×q matrix with ones on the diagonal.")),
        "v": ("v", ("Dirección de Fisher", "Vector unitario que mejor separa a las dos clases en el nodo (Proposición 2). El corte oblicuo es un umbral sobre vᵀx."),
              ("Fisher direction", "Unit vector that best separates the two classes at the node (Proposition 2). The oblique cut is a threshold on vᵀx.")),
        "S_w^-1": ("S_w⁻¹", ("Inversa de S_w", "En el código no se invierte: se resuelve el sistema S_w v = μ₁ − μ₀."),
                   ("Inverse of S_w", "In the code it is not inverted: the system S_w v = μ₁ − μ₀ is solved.")),
        "z_i": ("zᵢ", ("Proyección del cliente i", "Posición del cliente i sobre la dirección v: zᵢ = vᵀx_{i,F}. El corte oblicuo es un umbral sobre z."),
                ("Projection of client i", "Position of client i along the direction v: zᵢ = vᵀx_{i,F}. The oblique cut is a threshold on z.")),
        "f": ("f(x)", ("Probabilidad del bosque", "Probabilidad de incumplimiento que da el bosque: el promedio de sus T árboles."),
              ("Forest probability", "Default probability given by the forest: the average of its T trees.")),
        "T": ("T", ("Número de árboles", "Cuántos árboles tiene el bosque (359 en el modelo final)."),
              ("Number of trees", "How many trees the forest has (359 in the final model).")),
        "p" + H + "_t": ("p̂_t(x)", ("Probabilidad del árbol t", "La probabilidad que da la hoja a la que llega el cliente en el árbol t."),
                         ("Probability of tree t", "The probability given by the leaf the client reaches in tree t.")),
        "p" + H + "_hoja": ("p̂_hoja", ("Probabilidad de una hoja", "Proporción ponderada de morosos entre los clientes de entrenamiento que llegaron a esa hoja."),
                            ("Probability of a leaf", "Weighted share of defaulters among the training clients that reached that leaf.")),
        "t": ("t", ("Umbral del corte", "Valor que separa izquierda y derecha; se elige el que minimiza G."),
              ("Cut threshold", "Value that splits left from right; the one that minimizes G is chosen.")),
        "j": ("j", ("Variable candidata", "Una de las q variables sorteadas en el nodo."), ("Candidate variable", "One of the q variables drawn at the node.")),
        "F": ("F", ("Variables sorteadas", "El conjunto de las q variables que se eligieron al azar en este nodo."),
              ("Drawn variables", "The set of the q variables drawn at random at this node.")),
    },
    HIB: {
        "Z": ("Z", ("Logits de los miembros", "Matriz n×M: la puntuación (logit) fuera de muestra que da cada uno de los M modelos a cada cliente, con 3 pliegues internos."),
              ("Members' logits", "n×M matrix: the out-of-sample score (logit) each of the M models gives each client, with 3 inner folds.")),
        "w": ("w", ("Pesos de los modelos", "Cuánto cuenta cada modelo en el ensamble. Son positivos y suman 1; con λ quedan casi iguales (0.10–0.14)."),
              ("Model weights", "How much each model counts in the ensemble. They are positive and sum to 1; with λ they end up almost equal (0.10–0.14).")),
        "θ": ("θ", ("Parámetros libres", "Los números que se optimizan; w = softmax(θ) los convierte en pesos que suman 1."),
                   ("Free parameters", "The numbers that get optimized; w = softmax(θ) turns them into weights that sum to 1.")),
        "s": ("s", ("Puntaje combinado", "s = Zw: la puntuación del ensamble para cada cliente (promedio ponderado de los logits)."),
              ("Combined score", "s = Zw: the ensemble's score for each client (weighted average of the logits).")),
        "s_i": ("sᵢ", ("Puntaje del cliente i", "La puntuación combinada del cliente i."), ("Score of client i", "The combined score of client i.")),
        "q_i": ("qᵢ", ("Marca suave del cliente i", "Una versión suave y derivable de «marcar como default»: cerca de 1 si sᵢ supera el umbral t, cerca de 0 si no."),
                ("Soft flag of client i", "A smooth, differentiable version of “flag as default”: near 1 if sᵢ is above the threshold t, near 0 if not.")),
        "σ": ("σ", ("Sigmoide", "σ(u) = 1/(1 + e⁻ᵘ): convierte una distancia al umbral en un número entre 0 y 1."),
                   ("Sigmoid", "σ(u) = 1/(1 + e⁻ᵘ): turns a distance to the threshold into a number between 0 and 1.")),
        "t": ("t", ("Umbral", "Puntaje a partir del cual se marca a un cliente como default. Se aprende junto con los pesos; el umbral final se reelige maximizando el F1 duro."),
              ("Threshold", "Score above which a client is flagged as default. It is learned together with the weights; the final threshold is re-chosen by maximizing the hard F1.")),
        "τ": ("τ", ("Temperatura", "Qué tan abrupta es la marca suave. Con τ = 0.3 la curva se parece a un escalón pero sigue siendo derivable."),
                   ("Temperature", "How sharp the soft flag is. With τ = 0.3 the curve looks like a step but stays differentiable.")),
        "y_i": ("yᵢ", ("Etiqueta del cliente i", "1 = incumple el pago del mes siguiente; 0 = paga."), ("Label of client i", "1 = defaults next month; 0 = pays.")),
        "λ": ("λ", ("Fuerza de la penalización", "Empuja los pesos hacia el promedio uniforme 1/M. Con λ = 0.05 el ensamble casi no se aleja del promedio simple."),
                   ("Penalty strength", "Pushes the weights toward the uniform average 1/M. With λ = 0.05 the ensemble hardly departs from the simple average.")),
        "M": ("M", ("Número de miembros", "M = 8: CS-FOF, XGBoost, CatBoost, LightGBM, Random Forest, Extra Trees, HistGradientBoosting y regresión logística."),
              ("Number of members", "M = 8: CS-FOF, XGBoost, CatBoost, LightGBM, Random Forest, Extra Trees, HistGradientBoosting and logistic regression.")),
        "1": ("1", ("Vector de unos", "1/M es el peso de cada modelo en el promedio uniforme."), ("Vector of ones", "1/M is each model's weight in the uniform average.")),
    },
}

# identificador del código → símbolo del glosario (el código que se muestra junto a las ecuaciones)
CODIGO = {
    CSFOF: {"n0": "n_0", "n1": "n_1", "w": "w_i", "WL": "W_L", "WR": "W_R", "pL": "p_L", "pR": "p_R", "Sw": "S_w",
            "eps": "ε", "mu0": "μ_0", "mu1": "μ_1", "V": "v", "z": "z_i"},
    HIB: {"Z": "Z", "Zt": "Z", "w": "w", "q": "q_i", "tau": "τ", "lam": "λ", "m": "M"},
}


def glossary_json():
    """El glosario como JSON, para que lo lea assets/ecuaciones.js."""
    gl = {sc: {tok: {"sym": s, "es": list(es), "en": list(en)} for tok, (s, es, en) in d.items()}
          for sc, d in GLOSARIO.items()}
    return json.dumps({"g": gl, "code": CODIGO}, ensure_ascii=False)


def glossary_script():
    return "<script>window.EQ_GLOSS=" + glossary_json().replace("</", "<\\/") + ";</script>"


_TOK = re.compile(r"^(?P<base>[^_^]+)(?:_(?P<sub>[^^]+))?(?:\^(?P<sup>.+))?$")


def V(token, scope=CSFOF, label=None):
    """Un símbolo dentro de un texto (con subíndice si lo lleva) que se ilumina y explica igual que en la ecuación."""
    if label is None:
        m = _TOK.match(token)
        parts = [m["base"]]
        if m and m["sub"]:
            parts.append(html.Sub(m["sub"]))
        if m and m["sup"]:
            parts.append(html.Sup(m["sup"]))
        label = parts
    return html.Span(label, className="eqv", **{"data-eqv": token, "data-gs": scope})


def fx(tex, scope=CSFOF, display=True):
    """Ecuación LaTeX (MathJax) que pertenece al glosario `scope`: sus símbolos se explican y se iluminan."""
    body = f"$${tex}$$" if display else f"${tex}$"
    return html.Div(dcc.Markdown(body, mathjax=True, className="formula"), className="eqw", **{"data-gscope": scope})


def eqv_hint():
    """Una línea que explica cómo usar los símbolos de las ecuaciones."""
    return html.P([icon("info"), tx("Pasa el cursor (o toca) cualquier símbolo de una ecuación, de un texto o del código: "
                                    "una burbuja dice qué significa e ilumina todos los lugares donde se usa.",
                                    "Hover over (or tap) any symbol in an equation, a text or the code: a bubble says what it "
                                    "means and highlights every place where it is used.")], className="eqv-hint")
