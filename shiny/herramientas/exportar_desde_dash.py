# -*- coding: utf-8 -*-
"""Copia a la app Shiny lo que comparte con el tablero Dash, para que ambos se vean y respondan igual.

Uso (desde la raíz del repositorio):
    python shiny/herramientas/exportar_desde_dash.py

Genera:
    shiny/www/estilos.css         el mismo CSS del Dash (paleta, tarjetas, íconos SVG, Kyo)
    shiny/www/comun.js            el mismo JavaScript de interacción (portada, carrusel, equipo, Kyo)
    shiny/www/kyo/<ánimo>.svg      la mascota Kyo en sus cinco expresiones
    shiny/kyo/walker.html          Kyo fijo en la esquina (SVG animable con CSS)
    shiny/kyo/conocimiento.json    base de conocimiento de Kyo (intenciones, ejemplos y respuestas, es/en)
    shiny/kyo/pruebas.json         preguntas de prueba de asistente/evaluar.py

El motor de Kyo (TF-IDF + regresión logística) se vuelve a entrenar en R (shiny/R/09_kyo.R).
Solo hay que correr este script cuando cambie el diseño o el contenido de Kyo en el Dash.
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DASH, SHINY = RAIZ / "dash", RAIZ / "shiny"
sys.path.insert(0, str(DASH))

import app as A                                    # noqa: E402  (carga datos, modelo y Kyo)
from asistente import evaluar                       # noqa: E402
from asistente.conocimiento import construir_conocimiento  # noqa: E402
from asistente.mascota import mascota_svg           # noqa: E402
from asistente.motor import TEXTOS                  # noqa: E402

# --- 1. CSS (mismo diseño) ---------------------------------------------------
css = A.CSS
(SHINY / "www" / "estilos.css").write_text(css, encoding="utf-8")

# --- 1b. JavaScript de interacción (portada, tarjetas del equipo, carrusel, Predecir y panel de Kyo) ---
(SHINY / "www" / "comun.js").write_text("// Copiado del tablero Dash (dash/app.py: COVER_JS + BOT_JS)\n" + A.COVER_JS + "\n" + A.BOT_JS,
                                         encoding="utf-8")

# --- 2. Kyo: SVG por ánimo y el Kyo fijo de la esquina ------------------------
for m in ("happy", "thinking", "explaining", "proud", "alert"):
    (SHINY / "www" / "kyo" / f"{m}.svg").write_text(mascota_svg(m, uid=m), encoding="utf-8")
(SHINY / "kyo" / "walker.html").write_text(A.WALKER_HTML, encoding="utf-8")

# --- 3. Conocimiento de Kyo ---------------------------------------------------
# Ajustes para la versión Shiny. Los dos modelos de Predecir (XGBoost y CS-FOF) se entrenan en Python en el
# Dash y se exportan a R (herramientas/exportar_xgboost.py y exportar_cs_fof.py); Kyo de Shiny es una regresión
# logística programada en R (R/09_kyo.R). Los reemplazos son puntuales: scikit-learn se sigue usando en el
# proyecto (por ejemplo, para reajustar SVM en CPU), así que no se reemplaza en general.
REEMPLAZOS = [
    (r"\*\*regresión logística\*\* de scikit-learn", "**regresión logística** programada en R"),
    (r"a scikit-learn \*\*logistic regression\*\*", "a **logistic regression** programmed in R"),
    (r"\*\*Cómo se serializó el modelo\*\* \(joblib\)", "**Cómo se exportó el modelo a R**"),
    (r"\*\*How the model was serialized\*\* \(joblib\)", "**How the model was exported to R**"),
    (r"\bapp\.py\b", "app.R"), (r"python app\.R", "shiny::runApp()"),
    (r"http://127\.0\.0\.1:8050", "http://127.0.0.1:8060"),
    (r"`pip install -r requirements\.txt`", "`install.packages()`"),
]
EXTRA_EJEMPLOS = {   # preguntas propias de la versión R
    "serializacion": ["cómo se exportó el modelo a R", "qué es xgboost_arboles", "cómo funciona XGBoost en R",
                      "por qué no se reentrenó en R", "how was the model exported to R", "how does XGBoost run in R"],
}


def textos_shiny(lg):
    """Textos de la intención «serializacion» para Shiny: el modelo se exporta del Dash, no se reentrena."""
    m = json.loads((SHINY / "modelo" / "xgboost_meta.json").read_text(encoding="utf-8"))
    pr, hp = m["prueba"], m["hiperparametros"]
    n = len(m["nodos_por_arbol"])
    hps = ", ".join(f"{k} = {round(v, 4) if isinstance(v, float) else v}" for k, v in hp.items())
    if lg == "es":
        return (f"Los dos modelos de **Predecir** se entrenaron en Python (tablero Dash) y se **exportaron** a R, en "
                f"lugar de reentrenarlos con otro algoritmo:\n\n"
                f"1. **Entrenar** en Python (`dash/modelo/entrenar_extra.py`) y guardar con `joblib`.\n"
                f"2. **Exportar** los árboles: `herramientas/exportar_xgboost.py` escribe los {n} árboles de XGBoost "
                f"(umbrales float32 exactos) en `modelo/xgboost_arboles.bin.gz`; `exportar_cs_fof.py` hace lo mismo con CS-FOF.\n"
                f"3. **Cargar** en R al arrancar la app (`R/06c_xgboost.R` y `R/06b_cs_fof.R`).\n"
                f"4. **Predecir**: R recorre los árboles igual que XGBoost y da la misma probabilidad que Python "
                f"(diferencia menor que 10⁻⁶ en 300 clientes de prueba).\n\n"
                f"XGBoost en prueba (20 %): F1 {pr['f1']:.3f}, recall {pr['recall']:.3f}, precisión {pr['precision']:.3f}, "
                f"ROC-AUC {pr['roc_auc']:.3f}.",
                f"Hiperparámetros de XGBoost (los finales de la validación anidada 5 × 5 del proyecto): {hps}. "
                f"Entrenado con {m['n_entrenamiento']:,} clientes. Cada nodo envía al cliente a la izquierda si "
                f"x < umbral (en float32) y el puntaje es la sigmoide de la suma de las {n} hojas.")
    return (f"Both **Predict** models were trained in Python (Dash dashboard) and **exported** to R, instead of "
            f"retraining them with another algorithm:\n\n"
            f"1. **Train** in Python (`dash/modelo/entrenar_extra.py`) and save with `joblib`.\n"
            f"2. **Export** the trees: `herramientas/exportar_xgboost.py` writes the {n} XGBoost trees (exact float32 "
            f"thresholds) to `modelo/xgboost_arboles.bin.gz`; `exportar_cs_fof.py` does the same for CS-FOF.\n"
            f"3. **Load** them in R when the app starts (`R/06c_xgboost.R` and `R/06b_cs_fof.R`).\n"
            f"4. **Predict**: R traverses the trees like XGBoost and gives the same probability as Python "
            f"(difference below 10⁻⁶ on 300 test clients).\n\n"
            f"XGBoost on the test set (20%): F1 {pr['f1']:.3f}, recall {pr['recall']:.3f}, precision {pr['precision']:.3f}, "
            f"ROC-AUC {pr['roc_auc']:.3f}.",
            f"XGBoost hyperparameters (the final ones from the project's 5 × 5 nested validation): {hps}. "
            f"Trained on {m['n_entrenamiento']:,} clients. Each node sends the client left if x < threshold "
            f"(in float32) and the score is the sigmoid of the sum of the {n} leaves.")


def ajustar(s):
    if not s:
        return s
    for a, b in REEMPLAZOS:
        s = re.sub(a, b, s)
    return s


def intencion(it, lg):
    texto, tecnico = textos_shiny(lg) if it.id == "serializacion" else (ajustar(it.texto), ajustar(it.tecnico))
    titulo = (("Cómo se exportó el modelo a R" if lg == "es" else "How the model was exported to R")
              if it.id == "serializacion" else it.titulo)
    return {"id": it.id, "titulo": titulo, "ejemplos": list(it.ejemplos) + EXTRA_EJEMPLOS.get(it.id, []),
            "texto": texto, "tecnico": tecnico, "pagina": it.pagina, "sug": list(it.sug), "mood": it.mood}


salida = {}
for lg in ("es", "en"):
    intenciones, paginas, de_pagina, sug = construir_conocimiento(A, lg)
    salida[lg] = {"intenciones": [intencion(i, lg) for i in intenciones], "paginas": paginas,
                  "intencion_de_pagina": de_pagina, "sug_de_pagina": sug, "textos": TEXTOS[lg]}
(SHINY / "kyo" / "conocimiento.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")

pruebas = {"es": [list(x) for x in evaluar.PRUEBA], "en": [list(x) for x in evaluar.PRUEBA_EN],
           "fuera": list(evaluar.FUERA)}
(SHINY / "kyo" / "pruebas.json").write_text(json.dumps(pruebas, ensure_ascii=False, indent=1), encoding="utf-8")
print("Listo:", ", ".join(str(p.relative_to(RAIZ)) for p in [SHINY / "www" / "estilos.css", SHINY / "kyo"]))
