# -*- coding: utf-8 -*-
"""Evalúa a Kyo con preguntas que NO están en su entrenamiento.

Uso (desde la carpeta dash/):
    python -m asistente.evaluar

Reporta:
    1. Validación cruzada estratificada sobre las preguntas de ejemplo.
    2. Exactitud sobre un conjunto de prueba de preguntas parafraseadas (escritas aparte).
    3. Que rechace preguntas fuera del tablero en vez de inventar.
    4. Que cada sugerencia (los botones del chat) lleve a la respuesta prevista.
"""
import sys
from collections import Counter

import numpy as np
from sklearn.base import clone
from sklearn.model_selection import StratifiedKFold

# (pregunta nueva, intención esperada, página abierta)
PRUEBA = [
    ("hola, ¿quién eres tú?", "quien_eres", "/"),
    ("¿con qué algoritmo te entrenaron?", "quien_eres", "/"),
    ("¿qué cosas te puedo preguntar?", "ayuda", "/"),
    ("explicame q hay en esta pantalla", "esta_pagina", "/modelos"),
    ("no entiendo esta sección, ¿me ayudas?", "esta_pagina", "/multivariado"),
    ("explícamelo de forma más técnica", "mas_tecnico", "/multivariado"),
    ("¿cómo pongo el tema oscuro?", "navegacion", "/"),
    ("dame un resumen de las conclusiones del estudio", "resumen", "/"),
    ("¿para qué sirve la tarjeta que gira en la portada?", "p_inicio", "/"),
    ("¿qué tiene la sección de introducción?", "p_intro", "/introduccion"),
    ("¿qué dice la gráfica de barras de PAY_0 en la intro?", "intro_vistazo", "/introduccion"),
    ("¿eliminaron registros repetidos?", "intro_limpieza", "/univariado"),
    ("¿de qué banco y de qué país son los clientes?", "dataset", "/"),
    ("¿por qué es un problema para el banco?", "p_problema", "/problema"),
    ("¿qué hipótesis se plantean?", "hipotesis", "/problema"),
    ("¿cuál es el objetivo general del análisis?", "objetivos", "/problema"),
    ("¿los resultados son causales?", "limitaciones", "/problema"),
    ("¿qué significa PD, LGD y EAD?", "perdida_esperada", "/marco"),
    ("¿para qué sirve un score de crédito?", "scoring", "/marco"),
    ("¿qué es un análisis exploratorio?", "eda_concepto", "/marco"),
    ("¿cómo se detectan los outliers?", "atipicos", "/marco"),
    ("¿por qué la accuracy no sirve aquí?", "desbalance", "/marco"),
    ("¿por qué escogieron Spearman en vez de Pearson?", "spearman", "/marco"),
    ("¿cómo se mide el tamaño del efecto entre categóricas?", "cramer", "/marco"),
    ("¿qué prueba compara dos grupos sin normalidad?", "pruebas_grupos", "/marco"),
    ("¿qué significa cada columna del dataset?", "diccionario", "/marco"),
    ("¿qué representa limit bal?", "v_limit", "/univariado"),
    ("¿qué edad tienen en promedio?", "v_age", "/univariado"),
    ("¿hay más mujeres que hombres?", "v_sex", "/univariado"),
    ("¿qué nivel educativo predomina?", "v_edu", "/univariado"),
    ("¿qué significa un valor de -1 en pay_0?", "v_pay", "/univariado"),
    ("¿por qué algunas facturas son negativas?", "v_bill", "/univariado"),
    ("¿cuánto pagan al mes los clientes?", "v_payamt", "/univariado"),
    ("¿qué porcentaje de clientes cae en mora?", "v_target", "/univariado"),
    ("¿qué hay en la página univariada?", "p_uni", "/univariado"),
    ("¿qué son los puntos sueltos del boxplot del explorador?", "uni_explorador", "/univariado"),
    ("¿qué diferencia hay entre histograma y densidad?", "uni_cuant", "/univariado"),
    ("¿qué secciones tiene el multivariado?", "p_multi", "/multivariado"),
    ("¿qué significa el color dorado en la matriz de correlaciones?", "corr", "/multivariado"),
    ("¿la educación cambia la tasa de incumplimiento?", "rates", "/multivariado"),
    ("¿los que no pagan tienen cupos más bajos?", "limit_box", "/multivariado"),
    ("¿los clientes jóvenes se atrasan más?", "age", "/multivariado"),
    ("¿cómo funciona el módulo para cruzar variables?", "cross", "/multivariado"),
    ("¿qué es la scatter matrix con puntos de colores?", "splom", "/multivariado"),
    ("¿qué conclusiones saca el análisis multivariado?", "hallazgos", "/multivariado"),
    ("¿cuántas combinaciones de modelos evaluaron?", "p_modelos", "/modelos"),
    ("¿qué algoritmo funcionó mejor?", "mejor_modelo", "/modelos"),
    ("¿cómo se leen las tarjetas que se deslizan?", "carrusel", "/modelos"),
    ("¿balancear las clases mejora el F1?", "heat_modelos", "/modelos"),
    ("¿por qué los puntos sin balanceo quedan abajo en la dispersión?", "scatter_modelos", "/modelos"),
    ("¿cuántos falsos negativos tiene el mejor modelo?", "cm", "/modelos"),
    ("¿cuál es la variable más importante según SHAP?", "shap", "/modelos"),
    ("¿hay diferencias significativas entre los primeros modelos?", "como_leer", "/modelos"),
    ("¿qué diferencia hay entre recall y precisión?", "metricas", "/modelos"),
    ("¿cómo funciona SMOTE?", "balanceo", "/modelos"),
    ("¿qué es la búsqueda bayesiana con Optuna?", "optimizacion", "/modelos"),
    ("¿qué son los folds internos?", "validacion", "/modelos"),
    ("¿qué tal le fue a xgboost?", "m_xgboost", "/modelos"),
    ("¿en qué puesto quedó naive bayes?", "m_naive_bayes", "/modelos"),
    ("¿cómo funciona knn?", "m_knn", "/modelos"),
    ("¿qué tan buena fue la regresión logística?", "m_logistic_regression", "/modelos"),
    ("¿cómo calculo el riesgo de un cliente nuevo?", "p_predecir", "/predecir"),
    ("¿qué cargan los botones de ejemplo?", "formulario", "/predecir"),
    ("¿desde qué puntaje se considera riesgo alto?", "gauge", "/predecir"),
    ("¿qué significan los cuadritos de los árboles?", "votos", "/predecir"),
    ("¿qué muestra la gráfica de facturado contra pagado?", "historial", "/predecir"),
    ("¿por qué este cliente tiene riesgo alto?", "drivers", "/predecir"),
    ("¿qué pasa con el riesgo si cambio la edad?", "whatif", "/predecir"),
    ("¿para qué sirve joblib?", "serializacion", "/predecir"),
    ("¿qué acciones debería tomar la entidad con estos resultados?", "p_conclusiones", "/conclusiones"),
    ("¿dónde encuentro el código en github?", "p_enlaces", "/enlaces"),
    ("¿qué hace cada notebook?", "notebooks", "/enlaces"),
    ("¿quiénes son las autoras del tablero?", "p_equipo", "/equipo"),
    ("muchas gracias kyo", "gracias", "/"),
    # con errores de escritura
    ("esplicame la matris de correlasion", "corr", "/multivariado"),
    ("q es el recal", "metricas", "/modelos"),
    ("cual es el mejor modlo", "mejor_modelo", "/modelos"),
    ("q signifca pay0", "v_pay", "/univariado"),
]

PRUEBA_EN = [
    ("hey, who are you?", "quien_eres", "/"),
    ("what kind of questions can I ask?", "ayuda", "/"),
    ("explain what is on this screen", "esta_pagina", "/modelos"),
    ("make it more technical", "mas_tecnico", "/multivariado"),
    ("how can I turn on dark mode?", "navegacion", "/"),
    ("give me a summary of the study's conclusions", "resumen", "/"),
    ("what is the spinning card on the cover for?", "p_inicio", "/"),
    ("did they delete repeated records?", "intro_limpieza", "/univariado"),
    ("which country and bank are the clients from?", "dataset", "/"),
    ("which hypotheses are proposed?", "hipotesis", "/problema"),
    ("are the results causal?", "limitaciones", "/problema"),
    ("what do PD, LGD and EAD mean?", "perdida_esperada", "/marco"),
    ("why did they pick Spearman instead of Pearson?", "spearman", "/marco"),
    ("how is effect size measured between categorical variables?", "cramer", "/marco"),
    ("what does limit bal represent?", "v_limit", "/univariado"),
    ("what does a value of -1 in pay_0 mean?", "v_pay", "/univariado"),
    ("why are some bills negative?", "v_bill", "/univariado"),
    ("what percentage of clients default?", "v_target", "/univariado"),
    ("what does the gold color mean in the correlation matrix?", "corr", "/multivariado"),
    ("does education change the default rate?", "rates", "/multivariado"),
    ("do young clients fall behind more?", "age", "/multivariado"),
    ("which algorithm performed best?", "mejor_modelo", "/modelos"),
    ("how many false negatives does the best model have?", "cm", "/modelos"),
    ("what is the difference between recall and precision?", "metricas", "/modelos"),
    ("how does SMOTE work?", "balanceo", "/modelos"),
    ("how did xgboost perform?", "m_xgboost", "/modelos"),
    ("from what score is a client high risk?", "gauge", "/predecir"),
    ("why is the credit card cracked?", "gauge", "/predecir"),
    ("what happens to the risk if I change the age?", "whatif", "/predecir"),
    ("what is joblib used for?", "serializacion", "/predecir"),
    ("who are the authors of the dashboard?", "p_equipo", "/equipo"),
    ("how do I switch the language to spanish?", "navegacion", "/"),
    ("thanks a lot kyo", "gracias", "/"),
    ("explian the corelation matrix", "corr", "/multivariado"),
]

FUERA = [
    "¿cuál es la capital de Francia?", "dame una receta de arepas", "¿quién ganó el mundial de fútbol?",
    "¿qué hora es?", "cuéntame un chiste", "¿cómo está el clima mañana?", "¿cuánto es 2 más 2?",
    "escríbeme un poema", "¿cuál es el precio del dólar hoy?", "recomiéndame una película",
    "what is the capital of France?", "give me a pizza recipe", "who won the world cup?", "what time is it?",
    "tell me a joke", "write me a poem", "recommend me a movie",
]


def _probar(bot, casos):
    fallos = []
    for q, esperado, pag in casos:
        cid, prob, sim, cob, _sc = bot.clasificar(q, pag)
        aceptada, _ = bot.entiende(q, pag)
        if cid != esperado or aceptada is None:
            fallos.append((q, esperado, cid, prob, sim, aceptada is None))
    return fallos


def main():
    import app as A   # carga datos, modelo y entrena a Kyo
    bot = A.BOT
    print(f"Kyo · {bot.n_temas} intenciones · {bot.n_ejemplos} preguntas de entrenamiento (es + en)\n")

    # 1) validación cruzada sobre los ejemplos
    X, y = bot.M, bot.y
    cnt = Counter(y)
    ok = np.array([cnt[c] >= 3 for c in y])
    skf = StratifiedKFold(n_splits=3, shuffle=True, random_state=0)
    accs = []
    for tr, te in skf.split(X[ok], y[ok]):
        m = clone(bot.clf).fit(X[ok][tr], y[ok][tr])
        accs.append((m.predict(X[ok][te]) == y[ok][te]).mean())
    print(f"1) Validación cruzada (3 folds) sobre los ejemplos: {np.mean(accs):.1%} ± {np.std(accs):.1%}\n"
          "   (prueba exigente: cada tema pierde un tercio de sus pocos ejemplos al entrenar)")

    # 2) preguntas nuevas en cada idioma
    total_ok = True
    for nombre, casos in (("español", PRUEBA), ("inglés", PRUEBA_EN)):
        fallos = _probar(bot, casos)
        acc = 1 - len(fallos) / len(casos)
        total_ok &= acc >= 0.9
        print(f"2) Preguntas nuevas en {nombre}: {acc:.1%} ({len(casos) - len(fallos)}/{len(casos)})")
        for q, e, c, p, s, r in fallos:
            print(f"   ✗ «{q}» esperaba {e}, dio {c} (p={p:.2f}, sim={s:.2f}{', rechazada' if r else ''})")

    # 3) fuera del tablero
    mal = []
    for q in FUERA:
        r = bot.responder(q, "/")
        if r["i"] is not None:
            mal.append((q, r["i"]))
    print(f"3) Preguntas fuera del tablero rechazadas: {len(FUERA) - len(mal)}/{len(FUERA)}")
    for q, c in mal:
        print(f"   ✗ «{q}» respondió {c}")

    # 4) sugerencias: cada botón debe llevar al mismo tema en español y en inglés
    pares = set()
    for iid, it in bot.I["es"].items():
        pares.update(zip(it.sug, bot.I["en"][iid].sug))
    for ruta, lst in bot.sug_de_pagina["es"].items():
        pares.update(zip(lst, bot.sug_de_pagina["en"][ruta]))
    malas = []
    for es, en in sorted(pares):
        a, _ = bot.entiende(es, "/")
        b, _ = bot.entiende(en, "/")
        if a is None or b is None or a != b:
            malas.append((es, en, a, b))
    print(f"4) Sugerencias que llevan al mismo tema en ambos idiomas: {len(pares) - len(malas)}/{len(pares)}")
    for es, en, a, b in malas:
        print(f"   ✗ «{es}» → {a} | «{en}» → {b}")
    return 0 if total_ok and not mal and not malas else 1


if __name__ == "__main__":
    sys.exit(main())
