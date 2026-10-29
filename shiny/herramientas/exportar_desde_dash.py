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
# Ajustes para la versión Shiny: el modelo se guarda con saveRDS (no joblib) y la app es de R.
REEMPLAZOS = [
    (r"joblib\.dump", "saveRDS"), (r"joblib\.load", "readRDS"), (r"\bjoblib\b", "saveRDS/readRDS"),
    (r"modelo_credito\.pkl", "modelo_credito.rds"), (r"\.pkl\b", ".rds"),
    (r"predict_proba", "predict()"), (r"modelo/entrenar\.py", "modelo/entrenar_modelo.R"),
    (r"python -m modelo\.entrenar", "Rscript modelo/entrenar_modelo.R"),
    (r"scikit-learn", "ranger (R)"), (r"\bapp\.py\b", "app.R"), (r"python app\.R", "shiny::runApp()"),
    (r"http://127\.0\.0\.1:8050", "http://127.0.0.1:8060"),
    (r"`pip install -r requirements\.txt`", "`install.packages()`"),
]
EXTRA_EJEMPLOS = {   # preguntas propias de la versión R
    "serializacion": ["qué es saveRDS", "qué es el archivo rds", "modelo_credito.rds", "qué es readRDS",
                      "what is saveRDS", "what is the rds file", "what is readRDS"],
}


def ajustar(s):
    if not s:
        return s
    for a, b in REEMPLAZOS:
        s = re.sub(a, b, s)
    return s


def intencion(it):
    return {"id": it.id, "titulo": it.titulo, "ejemplos": list(it.ejemplos) + EXTRA_EJEMPLOS.get(it.id, []),
            "texto": ajustar(it.texto),
            "tecnico": ajustar(it.tecnico), "pagina": it.pagina, "sug": list(it.sug), "mood": it.mood}


salida = {}
for lg in ("es", "en"):
    intenciones, paginas, de_pagina, sug = construir_conocimiento(A, lg)
    salida[lg] = {"intenciones": [intencion(i) for i in intenciones], "paginas": paginas,
                  "intencion_de_pagina": de_pagina, "sug_de_pagina": sug, "textos": TEXTOS[lg]}
(SHINY / "kyo" / "conocimiento.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")

pruebas = {"es": [list(x) for x in evaluar.PRUEBA], "en": [list(x) for x in evaluar.PRUEBA_EN],
           "fuera": list(evaluar.FUERA)}
(SHINY / "kyo" / "pruebas.json").write_text(json.dumps(pruebas, ensure_ascii=False, indent=1), encoding="utf-8")
print("Listo:", ", ".join(str(p.relative_to(RAIZ)) for p in [SHINY / "www" / "estilos.css", SHINY / "kyo"]))
