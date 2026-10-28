# -*- coding: utf-8 -*-
"""Base de conocimiento de Kyo: qué sabe del tablero y con qué preguntas se entrena (español e inglés).

`construir_conocimiento(A, lang)` recibe el módulo de la aplicación (app.py ya cargado) y arma las
intenciones en el idioma pedido, con las cifras reales del tablero: las interpretaciones de cada
gráfica salen de las mismas funciones que usa la página (interp_corr, interp_rates, ...), así el bot
nunca contradice lo que se ve en pantalla.

Cada intención usa t(español, inglés) para sus textos y sus preguntas de ejemplo. El bot se entrena
con las preguntas de los dos idiomas y responde en el idioma elegido en el tablero.

Para enseñarle algo nuevo: agrega un Intencion(...) con varias preguntas de ejemplo en cada idioma
(cuantas más formas distintas de preguntar, mejor) y su respuesta. Se reentrena al arrancar.
"""
import numpy as np

from .motor import Intencion


def construir_conocimiento(A, lang="es"):
    """Devuelve (intenciones, paginas, intencion_de_pagina, sug_de_pagina) en el idioma `lang`."""
    A.set_lang(lang)
    try:
        return _construir(A, lang == "en")
    finally:
        A.set_lang("es")


def _construir(A, EN):
    t = (lambda es, en: en) if EN else (lambda es, en: es)
    df, T = A.df, A.TARGET
    n, n_def, rate = len(df), int(df[T].sum()), A.GLOBAL_RATE
    DI = A.DATA_INFO
    nt = A.nt
    pct = lambda x: f"{x:.1%}"
    B, BL = A.BEST, A.BASELINE
    best_lbl = A.minfo(B["model"], "label")
    tech_b, meth_b = A.tech_lbl(B["technique"]).lower(), A.method_lbl(B["method"]).lower()
    cm = A.BEST_CM
    pos, flagged = cm["tp"] + cm["fn"], cm["tp"] + cm["fp"]
    meta = A.MODELO_META or {}
    prueba = meta.get("prueba", {})
    n_trees = len(A.MODELO[-1].estimators_) if getattr(A, "MODELO", None) is not None else 0
    r_late = df.loc[df["PAY_0"] >= 2, T].mean()
    r_ok = df.loc[df["PAY_0"] <= 0, T].mean()
    exposure = df.loc[df[T] == 1, "LIMIT_BAL"].sum()
    bill_def = df.loc[df[T] == 1, "BILL_AMT1"].clip(lower=0).sum()
    findings = A.key_findings()
    lim1 = df.loc[df[T] == 1, "LIMIT_BAL"].median()
    lim0 = df.loc[df[T] == 0, "LIMIT_BAL"].median()
    _iu = np.triu_indices(6, 1)
    bill_rho = A.CORR.loc[A.BILL_COLS, A.BILL_COLS].values[_iu]

    I = []
    add = I.append

    # =====================================================================
    # Conversación general
    # =====================================================================
    add(Intencion(
        "saludo", t("Saludo", "Greeting"),
        t(["hola", "buenas", "buenos días", "buenas tardes", "hey kyo", "hola kyo", "qué tal", "holi",
           "hola cómo estás", "buenas noches"],
          ["hello", "hi", "hey", "good morning", "good afternoon", "hey kyo", "hi kyo", "how are you",
           "hello there", "good evening"]),
        t("¡Hola! Soy **Kyo**. Puedo explicarte cualquier página, gráfica, variable o modelo de este tablero. "
          "Si quieres, empiezo por la página en la que estás.",
          "Hi! I'm **Kyo**. I can explain any page, chart, variable or model of this dashboard. "
          "If you like, I'll start with the page you're on."),
        sug=t(["Explícame esta página", "¿Qué puedo preguntarte?", "¿Cuál es el hallazgo principal?"],
              ["Explain this page", "What can I ask you?", "What is the main finding?"]), mood="happy"))
    add(Intencion(
        "quien_eres", t("Quién es Kyo", "Who Kyo is"),
        t(["quién eres", "qué eres", "hola quién eres", "y tú quién eres", "cómo funcionas", "cómo te entrenaron",
           "eres una inteligencia artificial", "cómo aprendiste", "con qué te entrenaron",
           "qué modelo usas para responder", "eres un bot", "cómo sabes las respuestas",
           "de dónde sacas la información"],
          ["who are you", "what are you", "hi who are you", "hey who are you", "and you who are you",
           "how do you work", "how were you trained",
           "are you an artificial intelligence", "how did you learn", "what were you trained on",
           "what model do you use to answer", "are you a bot", "how do you know the answers",
           "where do you get your information"]),
        t("Soy **Kyo**, un bot entrenado con el contenido de este tablero:\n\n"
          "- Cada página, gráfica, variable y modelo es una *intención* con varias preguntas de ejemplo.\n"
          "- Las preguntas se convierten en vectores **TF-IDF** (palabras y fragmentos de letras, así tolero "
          "errores de escritura) y con ellos se entrena una **regresión logística** de scikit-learn.\n"
          "- Cuando preguntas, calculo la intención más probable. Si no me parezco a nada de lo aprendido, "
          "te lo digo en vez de inventar.\n"
          "- Las cifras salen de las mismas funciones que dibujan el tablero, así que coinciden con lo que ves.\n\n"
          "No me conecto a servicios externos: todo corre dentro de la app. Entiendo español e inglés.",
          "I'm **Kyo**, a bot trained on the content of this dashboard:\n\n"
          "- Each page, chart, variable and model is an *intent* with several example questions.\n"
          "- Questions are turned into **TF-IDF** vectors (words and character fragments, so I tolerate "
          "typos) and a scikit-learn **logistic regression** is trained on them.\n"
          "- When you ask, I compute the most likely intent. If your question doesn't look like anything I "
          "learned, I tell you instead of making things up.\n"
          "- The figures come from the same functions that draw the dashboard, so they match what you see.\n\n"
          "I don't connect to external services: everything runs inside the app. I understand Spanish and English."),
        sug=t(["¿Qué puedo preguntarte?", "Explícame esta página"], ["What can I ask you?", "Explain this page"]),
        mood="proud"))
    add(Intencion(
        "ayuda", t("Qué puedo preguntar", "What I can ask"),
        t(["qué puedo preguntarte", "ayuda", "en qué me ayudas", "qué sabes hacer", "qué sabes",
           "dame ideas de preguntas", "qué temas conoces", "help", "no sé qué preguntar", "opciones"],
          ["what can I ask you", "help", "what can you help me with", "what can you do", "what do you know",
           "give me question ideas", "what topics do you know", "I don't know what to ask", "options"]),
        t("Puedo explicarte:\n\n"
          "- **Cualquier página**: escribe «explícame esta página» o el nombre de la sección.\n"
          "- **Cada gráfica**: la matriz de correlación, las tasas por perfil, el boxplot del límite, la edad, "
          "el cruce de variables, el carrusel de modelos, la matriz de confusión, el puntaje de riesgo…\n"
          "- **Variables**: PAY_0, LIMIT_BAL, BILL_AMT, PAY_AMT, EDUCATION…\n"
          "- **Conceptos**: Spearman, V de Cramér, F1, recall, SMOTE, SHAP, validación cruzada…\n\n"
          "Después de cada respuesta puedes pedir **la explicación técnica**.",
          "I can explain:\n\n"
          "- **Any page**: type “explain this page” or the name of the section.\n"
          "- **Each chart**: the correlation matrix, the rates by profile, the limit boxplot, age, the variable "
          "cross, the model carousel, the confusion matrix, the risk score…\n"
          "- **Variables**: PAY_0, LIMIT_BAL, BILL_AMT, PAY_AMT, EDUCATION…\n"
          "- **Concepts**: Spearman, Cramér's V, F1, recall, SMOTE, SHAP, cross-validation…\n\n"
          "After each answer you can ask for **the technical explanation**."),
        sug=t(["Explícame esta página", "¿Qué es PAY_0?", "¿Cuál es el mejor modelo?", "¿Qué es el F1?"],
              ["Explain this page", "What is PAY_0?", "Which is the best model?", "What is F1?"]),
        mood="happy"))
    add(Intencion(
        "gracias", t("Agradecimiento", "Thanks"),
        t(["gracias", "muchas gracias", "perfecto gracias", "genial", "listo", "ok gracias", "chévere", "excelente",
           "súper", "entendido", "vale gracias", "adiós", "chao", "hasta luego"],
          ["thanks", "thank you", "thank you very much", "great", "perfect thanks", "ok thanks", "awesome",
           "got it", "understood", "bye", "goodbye", "see you"]),
        t("¡Con gusto! Cuando quieras, tócame de nuevo: estoy en la esquina inferior derecha de la pantalla.",
          "You're welcome! Tap me again whenever you like: I'm in the bottom-right corner of the screen."),
        sug=t(["Explícame esta página", "¿Cuál es el hallazgo principal?"],
              ["Explain this page", "What is the main finding?"]), mood="happy"))
    add(Intencion(
        "esta_pagina", t("Esta página", "This page"),
        t(["explícame esta página", "qué hay en esta página", "qué estoy viendo", "de qué trata esta sección",
           "explica esto", "qué es esto", "qué muestra esta página", "resúmeme esta página", "dónde estoy",
           "qué significa lo que estoy viendo", "explícame lo que hay aquí", "qué hay aquí",
           "explica la página actual", "explícame esta parte", "qué contiene esta sección",
           "no entiendo esta página", "ayúdame a entender esta sección", "no entiendo lo que veo"],
          ["explain this page", "what is on this page", "what am I looking at", "what is this section about",
           "explain this", "what is this", "what does this page show", "summarize this page", "where am I",
           "explain what is here", "what is here", "explain the current page", "explain this part",
           "I don't understand this page", "help me understand this section"]),
        "", mood="explaining"))
    add(Intencion(
        "mas_tecnico", t("Versión técnica", "Technical version"),
        t(["dame la explicación técnica", "explicación técnica", "más técnico", "explícalo técnicamente",
           "dame más detalle", "con estadísticos", "versión técnica", "quiero más detalle técnico",
           "profundiza", "detalles técnicos", "explícalo con más rigor", "interpretación técnica"],
          ["give me the technical explanation", "technical explanation", "more technical", "explain it technically",
           "give me more detail", "with statistics", "technical version", "I want more technical detail",
           "go deeper", "technical details", "technical interpretation"]),
        "", mood="explaining"))
    add(Intencion(
        "navegacion", t("Cómo usar el tablero", "How to use the dashboard"),
        t(["cómo uso el tablero", "cómo navego", "cómo cambio a modo oscuro", "cómo oculto el menú",
           "para qué sirve el botón de sol y luna", "cómo voy a la siguiente página", "cómo me muevo por el dash",
           "dónde está el menú", "modo oscuro", "botones anterior y siguiente", "cómo se usa el dashboard",
           "cambiar el tema", "tema oscuro", "modo claro", "cómo cambio el idioma", "poner en inglés",
           "botón ES EN", "cambiar idioma"],
          ["how do I use the dashboard", "how do I navigate", "how do I switch to dark mode", "how do I hide the menu",
           "what is the sun and moon button for", "how do I go to the next page", "where is the menu", "dark mode",
           "previous and next buttons", "change the theme", "light mode", "how do I change the language",
           "switch to spanish", "ES EN button", "change language"]),
        t("Así te mueves por el tablero:\n\n"
          "- **Menú lateral** (izquierda): las diez secciones en orden. El botón de panel de la barra superior "
          "lo oculta o lo muestra.\n"
          "- **ES | EN**: cambia el idioma de todo el tablero (y el mío).\n"
          "- **Sol y luna**: cambia entre modo claro y oscuro (se recuerda en tu navegador).\n"
          "- **Anterior / Siguiente**: al final de cada página te llevan por el tablero en orden.\n"
          "- **Interpretaciones**: bajo cada gráfica, el botón **Ver interpretación** despliega la explicación "
          "básica y la técnica.\n"
          "- **Yo**: estoy en la esquina inferior derecha; tócame para abrir este panel y la **X** para cerrarlo.",
          "This is how you move around the dashboard:\n\n"
          "- **Side menu** (left): the ten sections in order. The panel button in the top bar hides or shows it.\n"
          "- **ES | EN**: changes the language of the whole dashboard (and mine).\n"
          "- **Sun and moon**: switches between light and dark mode (remembered in your browser).\n"
          "- **Previous / Next**: at the end of each page they take you through the dashboard in order.\n"
          "- **Interpretations**: under each chart, the **Show interpretation** button reveals the basic and "
          "technical explanation.\n"
          "- **Me**: I'm in the bottom-right corner; tap me to open this panel and the **X** to close it."),
        sug=t(["Explícame esta página", "¿Qué puedo preguntarte?"], ["Explain this page", "What can I ask you?"]),
        mood="happy"))
    add(Intencion(
        "resumen", t("Resumen del proyecto", "Project summary"),
        t(["de qué trata el proyecto", "resumen del tablero", "resume todo el dashboard", "cuál es el hallazgo principal",
           "conclusiones", "qué encontraron", "cuáles son las conclusiones del análisis",
           "en pocas palabras qué dice el dash", "qué aprendieron", "hallazgos principales",
           "qué es lo más importante del análisis"],
          ["what is the project about", "dashboard summary", "summarize the whole dashboard", "what is the main finding",
           "conclusions", "what did they find", "what are the conclusions of the analysis",
           "in a nutshell what does the dashboard say", "main findings", "what is the most important result"]),
        t(f"El tablero estudia **{n:,} clientes** de tarjeta de crédito de un banco de Taiwán (abril–septiembre "
          f"2005) para entender quién deja de pagar el mes siguiente ({pct(rate)} lo hizo). Lo más importante:\n\n"
          f"1. **El historial de pagos domina.** {findings[0][1]}\n"
          f"2. **Menor cupo, más riesgo.** {findings[2][1]}\n"
          f"3. **Lo demográfico pesa poco.** {findings[3][1]}\n"
          f"4. **Las facturas son redundantes.** {findings[1][1]}\n"
          f"5. **Modelos:** el mejor es {best_lbl} con {tech_b} "
          f"(F1 {B['f1_mean']:.3f} frente a {BL:.3f} de la línea base); balancear las clases es lo que más ayuda.",
          f"The dashboard studies **{n:,} credit card clients** of a Taiwanese bank (April–September 2005) to "
          f"understand who stops paying the following month ({pct(rate)} did). The key points:\n\n"
          f"1. **Payment history dominates.** {findings[0][1]}\n"
          f"2. **Lower limit, higher risk.** {findings[2][1]}\n"
          f"3. **Demographics matter little.** {findings[3][1]}\n"
          f"4. **Bills are redundant.** {findings[1][1]}\n"
          f"5. **Models:** the best is {best_lbl} with {tech_b} "
          f"(F1 {B['f1_mean']:.3f} vs. {BL:.3f} for the baseline); balancing the classes helps the most."),
        sug=t(["¿Qué es PAY_0?", "¿Cuál es el mejor modelo?", "Explícame la matriz de correlación"],
              ["What is PAY_0?", "Which is the best model?", "Explain the correlation matrix"]), mood="proud"))

    # =====================================================================
    # Portada
    # =====================================================================
    add(Intencion(
        "p_inicio", t("Inicio (portada)", "Home (cover)"),
        t(["portada", "página de inicio", "inicio", "qué es la tarjeta de la portada", "por qué hay una tarjeta de crédito",
           "la tarjeta que se voltea", "qué dice la tarjeta", "pantalla principal", "home"],
          ["cover page", "home page", "home", "what is the card on the cover", "why is there a credit card",
           "the card that flips", "what does the card say", "main screen"]),
        t("La **portada** presenta el proyecto con una tarjeta de crédito interactiva:\n\n"
          "- **Frente:** los titulares (las autoras) y el periodo de los datos (abril–septiembre 2005).\n"
          f"- **Reverso** (haz clic para voltearla): {n:,} clientes, {pct(rate)} de default y el periodo.\n"
          "- **Iniciar recorrido** te lleva a la Introducción; desde ahí el menú lateral muestra todas las secciones.",
          "The **cover** presents the project with an interactive credit card:\n\n"
          "- **Front:** the cardholders (the authors) and the data period (April–September 2005).\n"
          f"- **Back** (click to flip it): {n:,} clients, {pct(rate)} default and the period.\n"
          "- **Start the tour** takes you to the Introduction; from there the side menu shows all sections."),
        pagina="/", sug=t(["¿De qué trata el proyecto?", "Explícame la introducción", "¿Cómo uso el tablero?"],
                          ["What is the project about?", "Explain the introduction", "How do I use the dashboard?"]),
        mood="happy"))

    # =====================================================================
    # Introducción
    # =====================================================================
    add(Intencion(
        "p_intro", t("Introducción", "Introduction"),
        t(["explícame la introducción", "qué hay en la introducción", "página de introducción", "contexto del proyecto",
           "para qué es este tablero", "cuál es el contexto"],
          ["explain the introduction", "what is in the introduction", "introduction page", "project context",
           "what is this dashboard for", "what is the context"]),
        t("La **Introducción** da el contexto:\n\n"
          "- **Vistazo rápido:** una gráfica que muestra que el atraso de septiembre anticipa el incumplimiento.\n"
          f"- **KPIs:** {n:,} clientes, 24 variables (23 predictoras + 1 objetivo), {pct(rate)} de default y el "
          "periodo abril–septiembre 2005.\n"
          "- **Fuente y alcance:** datos de Yeh & Lien (2009) en UCI; montos en NT$; el análisis es descriptivo.\n"
          "- **Preparación de los datos:** qué limpieza se hizo.\n"
          "- **Cómo recorrer el tablero:** qué hay en cada sección.",
          "The **Introduction** gives the context:\n\n"
          "- **Quick look:** a chart showing that September's delay anticipates default.\n"
          f"- **KPIs:** {n:,} clients, 24 variables (23 predictors + 1 target), {pct(rate)} default and the "
          "April–September 2005 period.\n"
          "- **Source and scope:** Yeh & Lien (2009) data on UCI; amounts in NT$; the analysis is descriptive.\n"
          "- **Data preparation:** what cleaning was done.\n"
          "- **How to navigate the dashboard:** what each section contains."),
        pagina="/introduccion", sug=t(["Explícame el vistazo rápido", "¿Cómo se limpiaron los datos?",
                                       "¿De dónde salen los datos?"],
                                      ["Explain the quick look", "How was the data cleaned?",
                                       "Where does the data come from?"])))
    add(Intencion(
        "intro_vistazo", t("Vistazo rápido (PAY_0)", "Quick look (PAY_0)"),
        t(["explícame el vistazo rápido", "gráfica del vistazo rápido", "la gráfica de barras de la introducción",
           "el atraso de septiembre anticipa el incumplimiento", "tasa de default según PAY_0",
           "qué muestra la primera gráfica", "barras por estado de pago de septiembre"],
          ["explain the quick look", "quick look chart", "the bar chart in the introduction",
           "September delay anticipates default", "default rate by PAY_0", "what does the first chart show",
           "bars by September repayment status"]),
        t(f"Cada barra es la tasa de default para un valor de **PAY_0** (estado de pago de septiembre). "
          f"Entre quienes tenían 2 o más meses de atraso, **{r_late:.0%}** incumplió el mes siguiente; entre "
          f"quienes iban al día o pagaban el mínimo, **{r_ok:.0%}**. La línea punteada es la tasa global "
          f"({pct(rate)}). Solo se muestran valores con al menos 100 clientes.",
          f"Each bar is the default rate for a value of **PAY_0** (September repayment status). "
          f"Among those 2 or more months late, **{r_late:.0%}** defaulted the following month; among those up to "
          f"date or paying the minimum, **{r_ok:.0%}**. The dashed line is the overall rate ({pct(rate)}). Only "
          "values with at least 100 clients are shown."),
        tecnico=t("Se agrupa por PAY_0 y se calcula la media de la variable objetivo en cada grupo (grupos con n ≥ 100). "
                  "La tasa salta de forma no lineal al pasar de 0 (pago mínimo) a 1–2 meses de atraso, por eso PAY_0 "
                  "conviene tratarla como ordinal o categórica (dummies) y no como una variable lineal. Es la variable "
                  "con mayor ρ de Spearman con el default y la primera en importancia SHAP del mejor modelo.",
                  "Clients are grouped by PAY_0 and the mean of the target is computed in each group (groups with "
                  "n ≥ 100). The rate jumps non-linearly from 0 (minimum payment) to 1–2 months late, so PAY_0 should "
                  "be treated as ordinal or categorical (dummies) rather than linear. It is the variable with the "
                  "highest Spearman ρ with default and the first in SHAP importance for the best model."),
        pagina="/introduccion", sug=t(["¿Qué es PAY_0?", "¿Qué variables pesan más en el modelo?"],
                                      ["What is PAY_0?", "Which variables matter most in the model?"])))
    add(Intencion(
        "intro_limpieza", t("Preparación de los datos", "Data preparation"),
        t(["cómo se limpiaron los datos", "qué limpieza hicieron", "preparación de los datos", "duplicados",
           "qué pasó con los códigos no documentados", "saldos negativos", "por qué no hay PAY_1",
           "calidad de los datos", "transformaciones aplicadas a los datos", "cuántos duplicados había",
           "borraron filas", "quitaron registros duplicados", "limpieza del dataset", "filas eliminadas"],
          ["how was the data cleaned", "what cleaning was done", "data preparation", "duplicates",
           "what happened to the undocumented codes", "negative balances", "why is there no PAY_1", "data quality",
           "how many duplicates were there", "were rows removed", "dataset cleaning", "removed rows",
           "deleted duplicated rows", "repeated rows removed", "were duplicated records dropped"]),
        t(f"La preparación de los datos (Introducción):\n\n"
          f"- Se eliminaron **{DI['duplicados']}** filas duplicadas exactas (de {DI['filas_originales']:,} a {n:,}).\n"
          f"- **{DI['edu_reagrupadas']}** registros con EDUCATION = 0, 5 o 6 (códigos sin documentar) pasaron a «Otros».\n"
          f"- **{DI['mar_reagrupadas']}** registros con MARRIAGE = 0 pasaron a «Otros».\n"
          f"- Se conservaron **{DI['bill_neg_clientes']:,}** clientes con saldo facturado negativo: es saldo a favor "
          "y es válido.\n"
          "- El estado de pago de septiembre se llama PAY_0: el dataset no trae PAY_1.",
          f"Data preparation (Introduction):\n\n"
          f"- **{DI['duplicados']}** exact duplicate rows were removed (from {DI['filas_originales']:,} to {n:,}).\n"
          f"- **{DI['edu_reagrupadas']}** records with EDUCATION = 0, 5 or 6 (undocumented codes) were moved to “Others”.\n"
          f"- **{DI['mar_reagrupadas']}** records with MARRIAGE = 0 were moved to “Others”.\n"
          f"- **{DI['bill_neg_clientes']:,}** clients with a negative bill amount were kept: it is a credit balance "
          "and it is valid.\n"
          "- September's repayment status is called PAY_0: the dataset has no PAY_1."),
        pagina="/introduccion", sug=t(["¿De dónde salen los datos?", "¿Qué es EDUCATION?", "¿Qué es BILL_AMT?"],
                                      ["Where does the data come from?", "What is EDUCATION?", "What is BILL_AMT?"])))
    add(Intencion(
        "dataset", t("Fuente de los datos", "Data source"),
        t(["de dónde salen los datos", "qué dataset usaron", "fuente de los datos", "UCI", "Yeh y Lien",
           "cuántos clientes hay", "de qué banco son los datos", "de qué año son los datos", "en qué moneda están",
           "cuántas variables tiene el dataset", "default of credit card clients", "qué periodo cubren los datos"],
          ["where does the data come from", "which dataset did they use", "data source", "UCI", "Yeh and Lien",
           "how many clients are there", "which bank is the data from", "what year is the data from",
           "what currency are the amounts in", "how many variables does the dataset have",
           "what period does the data cover"]),
        t(f"Los datos son **Default of Credit Card Clients** (UCI Machine Learning Repository), publicados por "
          f"Yeh & Lien (2009). Son {DI['filas_originales']:,} clientes de un banco de **Taiwán** observados de "
          f"**abril a septiembre de 2005** ({n:,} tras quitar duplicados), con 24 variables: cupo, datos "
          "demográficos, estado de pago de seis meses, montos facturados y montos pagados, y si incumplió en "
          "octubre (variable objetivo). Los montos están en **dólares taiwaneses (NT$)**.",
          f"The data is **Default of Credit Card Clients** (UCI Machine Learning Repository), published by "
          f"Yeh & Lien (2009). It has {DI['filas_originales']:,} clients of a **Taiwanese** bank observed from "
          f"**April to September 2005** ({n:,} after removing duplicates), with 24 variables: limit, demographics, "
          "six months of repayment status, billed amounts and paid amounts, and whether they defaulted in October "
          "(target variable). Amounts are in **New Taiwan dollars (NT$)**."),
        pagina="/introduccion", sug=t(["¿Qué variables tiene?", "¿Qué es la variable objetivo?",
                                       "¿Cómo se limpiaron los datos?"],
                                      ["What variables does it have?", "What is the target variable?",
                                       "How was the data cleaned?"])))

    # =====================================================================
    # Problema y objetivos
    # =====================================================================
    add(Intencion(
        "p_problema", t("Problema y Objetivos", "Problem and Objectives"),
        t(["explícame problema y objetivos", "cuál es el problema", "planteamiento del problema", "página del problema",
           "por qué es importante este análisis", "qué problema resuelven", "justificación del proyecto"],
          ["explain problem and objectives", "what is the problem", "problem statement", "problem page",
           "why is this analysis important", "what problem do they solve", "project rationale"]),
        t("**Problema y Objetivos** explica por qué importa el análisis:\n\n"
          "- **Planteamiento:** el banco presta sin saber quién pagará; si se equivoca pierde capital o, si "
          f"restringe de más, pierde ingresos. Aquí {pct(rate)} ({n_def:,} clientes) no pagó.\n"
          f"- **KPIs:** clientes en default, límite expuesto (NT${exposure / 1e6:,.0f} M) y saldo facturado de "
          f"septiembre de quienes incumplen (NT${bill_def / 1e6:,.0f} M).\n"
          "- **Pregunta de investigación**, **justificación**, **alcance y limitaciones**.\n"
          "- **Cinco hipótesis** (H1–H5) y los **objetivos** general y específicos.",
          "**Problem and Objectives** explains why the analysis matters:\n\n"
          "- **Statement:** the bank lends without knowing who will pay; if it gets it wrong it loses capital or, "
          f"if it restricts too much, it loses income. Here {pct(rate)} ({n_def:,} clients) did not pay.\n"
          f"- **KPIs:** clients in default, exposed limit (NT${exposure / 1e6:,.0f} M) and September billed balance "
          f"of defaulters (NT${bill_def / 1e6:,.0f} M).\n"
          "- **Research question**, **rationale**, **scope and limitations**.\n"
          "- **Five hypotheses** (H1–H5) and the general and specific **objectives**."),
        tecnico=t("Los errores no son simétricos: un falso negativo (no detectar a quien incumplirá) suele costar más "
                  "que un falso positivo. Por eso más adelante se privilegian F1 y recall de la clase default sobre "
                  "la exactitud (accuracy).",
                  "Errors are not symmetric: a false negative (missing someone who will default) usually costs more "
                  "than a false positive. That is why F1 and default-class recall are later preferred over accuracy."),
        pagina="/problema", sug=t(["¿Cuáles son las hipótesis?", "¿Cuál es la pregunta de investigación?",
                                   "¿Cuáles son los objetivos?"],
                                  ["What are the hypotheses?", "What is the research question?",
                                   "What are the objectives?"])))
    add(Intencion(
        "pregunta", t("Pregunta de investigación", "Research question"),
        t(["cuál es la pregunta de investigación", "qué pregunta responde el análisis", "preguntas específicas",
           "qué se quiere responder"],
          ["what is the research question", "what question does the analysis answer", "specific questions",
           "what do they want to answer"]),
        t("**Pregunta de investigación:** ¿qué características del cliente, de su línea de crédito y de su historial "
          "reciente de pagos se asocian con el incumplimiento del mes siguiente, y con qué intensidad?\n\n"
          "Preguntas específicas: cómo se distribuyen las variables y qué problemas de calidad tienen, qué tan "
          "desbalanceada está la variable objetivo, qué variables separan mejor a quienes incumplen y si hay "
          "redundancia entre predictoras.",
          "**Research question:** which characteristics of the client, their credit line and their recent payment "
          "history are associated with default the following month, and how strongly?\n\n"
          "Specific questions: how the variables are distributed and what quality issues they have, how imbalanced "
          "the target is, which variables best separate defaulters and whether there is redundancy among predictors."),
        pagina="/problema", sug=t(["¿Cuáles son las hipótesis?", "¿Cuáles son los objetivos?"],
                                  ["What are the hypotheses?", "What are the objectives?"])))
    add(Intencion(
        "hipotesis", t("Hipótesis", "Hypotheses"),
        t(["cuáles son las hipótesis", "hipótesis exploratorias", "H1", "qué hipótesis plantearon",
           "se cumplieron las hipótesis", "tabla de hipótesis", "H2 H3 H4 H5"],
          ["what are the hypotheses", "exploratory hypotheses", "H1", "which hypotheses did they propose",
           "were the hypotheses supported", "hypotheses table", "H2 H3 H4 H5"]),
        t("Las **cinco hipótesis** y lo que muestra el tablero:\n\n"
          "- **H1** El historial de pagos (PAY_0…PAY_6) es el factor más asociado al default → **se apoya**: PAY_0 "
          "tiene la mayor correlación y domina en SHAP.\n"
          f"- **H2** Menor límite de crédito, más default → **se apoya**: mediana {nt(lim1)} (default) vs. {nt(lim0)}.\n"
          "- **H3** Lo demográfico se asocia, pero con efecto pequeño → **se apoya**: V de Cramér < 0.1.\n"
          f"- **H4** Las BILL_AMT están muy correlacionadas → **se apoya**: ρ entre {bill_rho.min():.2f} y "
          f"{bill_rho.max():.2f}.\n"
          f"- **H5** La clase default es minoritaria → **se apoya**: {pct(rate)} frente a {pct(1 - rate)}.",
          "The **five hypotheses** and what the dashboard shows:\n\n"
          "- **H1** Payment history (PAY_0…PAY_6) is the factor most associated with default → **supported**: PAY_0 "
          "has the highest correlation and dominates in SHAP.\n"
          f"- **H2** Lower credit limit, more default → **supported**: median {nt(lim1)} (default) vs. {nt(lim0)}.\n"
          "- **H3** Demographics are associated, but with a small effect → **supported**: Cramér's V < 0.1.\n"
          f"- **H4** The BILL_AMT are highly correlated → **supported**: ρ between {bill_rho.min():.2f} and "
          f"{bill_rho.max():.2f}.\n"
          f"- **H5** The default class is the minority → **supported**: {pct(rate)} vs. {pct(1 - rate)}."),
        pagina="/problema", sug=t(["Explícame la matriz de correlación", "¿Qué es la V de Cramér?",
                                   "¿Qué es el desbalance de clases?"],
                                  ["Explain the correlation matrix", "What is Cramér's V?", "What is class imbalance?"])))
    add(Intencion(
        "objetivos", t("Objetivos", "Objectives"),
        t(["cuáles son los objetivos", "objetivo general", "objetivos específicos", "qué buscan con el análisis",
           "metas del análisis"],
          ["what are the objectives", "general objective", "specific objectives", "what is the goal of the analysis",
           "goals of the analysis"]),
        t("**Objetivo general:** analizar los factores que se asocian con el incumplimiento de pago de los clientes "
          "de tarjeta de crédito mediante un EDA univariado y multivariado.\n\n"
          "**Específicos:** documentar la calidad y la limpieza de los datos (Introducción); caracterizar cada "
          "variable y cuantificar el desbalance (Univariado); comparar clientes con y sin default y detectar "
          "multicolinealidad (Multivariado); y definir lineamientos de preprocesamiento para el modelado "
          "(Hallazgos clave).",
          "**General objective:** analyze the factors associated with payment default among credit card clients "
          "through a univariate and multivariate EDA.\n\n"
          "**Specific:** document data quality and cleaning (Introduction); characterize each variable and "
          "quantify the imbalance (Univariate); compare clients with and without default and detect "
          "multicollinearity (Multivariate); and define preprocessing guidelines for modeling (Key findings)."),
        pagina="/problema", sug=t(["¿Cuáles son las hipótesis?", "¿Cuáles son los hallazgos clave?"],
                                  ["What are the hypotheses?", "What are the key findings?"])))
    add(Intencion(
        "limitaciones", t("Alcance y limitaciones", "Scope and limitations"),
        t(["limitaciones", "alcance del análisis", "qué limitaciones tiene", "se puede generalizar",
           "correlación implica causalidad", "es causal el análisis", "causalidad", "los hallazgos son causa y efecto",
           "sirve para otros países", "por qué no se puede generalizar"],
          ["limitations", "scope of the analysis", "what limitations does it have", "can it be generalized",
           "does correlation imply causation", "is the analysis causal", "causality", "are the findings cause and effect",
           "does it apply to other countries"]),
        t("**Alcance y limitaciones:**\n\n"
          "- Datos de un solo banco de Taiwán y un periodo corto (abril–septiembre 2005): no se generalizan sin cautela.\n"
          "- El análisis es **asociativo**: una correlación no implica causalidad.\n"
          "- El EDA no construye modelos; los modelos se entrenaron en el repositorio del proyecto y se resumen en "
          "la sección Modelos.\n"
          "- Los códigos −2 y 0 de PAY_x no están documentados con precisión; se conservan sin recodificar.",
          "**Scope and limitations:**\n\n"
          "- Data from a single Taiwanese bank and a short period (April–September 2005): it should not be "
          "generalized without caution.\n"
          "- The analysis is **associative**: correlation does not imply causation.\n"
          "- The EDA does not build models; the models were trained in the project repository and are summarized "
          "in the Models section.\n"
          "- Codes −2 and 0 of PAY_x are not precisely documented; they are kept without recoding."),
        pagina="/problema", sug=t(["¿Qué es PAY_0?", "¿De dónde salen los datos?"],
                                  ["What is PAY_0?", "Where does the data come from?"])))
    add(Intencion(
        "kpis_problema", t("Límite expuesto y saldo facturado", "Exposed limit and billed balance"),
        t(["qué es el límite expuesto", "saldo facturado de septiembre", "KPIs del problema",
           "cuánto dinero está en riesgo", "cuánto suman los cupos de quienes incumplen"],
          ["what is the exposed limit", "September billed balance", "problem KPIs", "how much money is at risk",
           "sum of the limits of defaulters"]),
        t(f"En Problema y Objetivos hay tres cifras de negocio:\n\n"
          f"- **Clientes en default:** {n_def:,} ({pct(rate)}).\n"
          f"- **Límite expuesto:** NT${exposure / 1e6:,.0f} millones, la suma de los cupos (LIMIT_BAL) de quienes "
          "incumplen.\n"
          f"- **Saldo facturado (Sep):** NT${bill_def / 1e6:,.0f} millones, la suma de BILL_AMT1 positivo de quienes "
          "incumplen.\n\nDan una idea del tamaño del problema para el banco.",
          f"Problem and Objectives shows three business figures:\n\n"
          f"- **Clients in default:** {n_def:,} ({pct(rate)}).\n"
          f"- **Exposed limit:** NT${exposure / 1e6:,.0f} million, the sum of the limits (LIMIT_BAL) of defaulters.\n"
          f"- **Billed balance (Sep):** NT${bill_def / 1e6:,.0f} million, the sum of positive BILL_AMT1 of defaulters.\n\n"
          "They give an idea of the size of the problem for the bank."),
        pagina="/problema", sug=t(["¿Qué es LIMIT_BAL?", "¿Qué es la pérdida esperada?"],
                                  ["What is LIMIT_BAL?", "What is expected loss?"])))

    # =====================================================================
    # Marco teórico
    # =====================================================================
    add(Intencion(
        "p_marco", t("Marco Teórico", "Theoretical Framework"),
        t(["explícame el marco teórico", "qué hay en el marco teórico", "página del marco teórico",
           "qué conceptos usan", "fundamentos teóricos", "teoría del proyecto"],
          ["explain the theoretical framework", "what is in the theoretical framework", "theoretical framework page",
           "what concepts do they use", "theoretical foundations", "theory of the project"]),
        t("El **Marco Teórico** reúne los conceptos que sustentan el análisis, en ocho tarjetas:\n\n"
          "1. Riesgo de crédito y default (EL = PD × LGD × EAD)\n2. Scoring crediticio\n3. EDA (Tukey)\n"
          "4. Estadística descriptiva y atípicos\n5. Desbalance de clases\n6. Spearman y multicolinealidad (VIF)\n"
          "7. χ² y V de Cramér\n8. Mann-Whitney, Kruskal-Wallis y t de Welch\n\n"
          "Además: antecedentes (Yeh & Lien, 2009), el **diccionario de variables** y las referencias (desplegable).",
          "The **Theoretical Framework** gathers the concepts behind the analysis, in eight cards:\n\n"
          "1. Credit risk and default (EL = PD × LGD × EAD)\n2. Credit scoring\n3. EDA (Tukey)\n"
          "4. Descriptive statistics and outliers\n5. Class imbalance\n6. Spearman and multicollinearity (VIF)\n"
          "7. χ² and Cramér's V\n8. Mann-Whitney, Kruskal-Wallis and Welch's t\n\n"
          "Plus: background (Yeh & Lien, 2009), the **variable dictionary** and the references (collapsible)."),
        pagina="/marco", sug=t(["¿Qué es la pérdida esperada?", "¿Qué es Spearman?", "Muéstrame el diccionario de variables"],
                               ["What is expected loss?", "What is Spearman?", "Show me the variable dictionary"])))
    add(Intencion(
        "perdida_esperada", t("Riesgo de crédito y pérdida esperada", "Credit risk and expected loss"),
        t(["qué es la pérdida esperada", "EL = PD x LGD x EAD", "qué es PD", "qué es LGD", "qué es EAD",
           "qué es el riesgo de crédito", "qué es default", "qué significa default", "Basilea"],
          ["what is expected loss", "EL = PD x LGD x EAD", "what is PD", "what is LGD", "what is EAD",
           "what is credit risk", "what is default", "what does default mean", "Basel"]),
        t("El **riesgo de crédito** es la posibilidad de perder dinero porque un deudor no paga. En Basilea II la "
          "pérdida esperada es **EL = PD × LGD × EAD**:\n\n"
          "- **PD:** probabilidad de incumplimiento (lo que estudian estos datos).\n"
          "- **LGD:** porcentaje que se pierde si hay incumplimiento.\n"
          "- **EAD:** monto expuesto en ese momento.\n\n"
          "Aquí **default** es la variable binaria que indica si el cliente no pagó el mes siguiente.",
          "**Credit risk** is the possibility of losing money because a debtor does not pay. In Basel II expected "
          "loss is **EL = PD × LGD × EAD**:\n\n"
          "- **PD:** probability of default (what this data studies).\n"
          "- **LGD:** percentage lost if there is a default.\n"
          "- **EAD:** amount exposed at that moment.\n\n"
          "Here **default** is the binary variable indicating whether the client did not pay the following month."),
        pagina="/marco", sug=t(["¿Qué es el scoring crediticio?", "¿Qué es la variable objetivo?"],
                               ["What is credit scoring?", "What is the target variable?"])))
    add(Intencion(
        "scoring", t("Scoring crediticio", "Credit scoring"),
        t(["qué es el scoring crediticio", "qué es un modelo de scoring", "para qué sirve el scoring",
           "puntaje crediticio", "score crediticio", "para qué sirve un score", "qué es un score de riesgo"],
          ["what is credit scoring", "what is a scoring model", "what is scoring for", "credit score",
           "what is a risk score used for"]),
        t("Un **modelo de scoring** estima la probabilidad de incumplimiento (PD) con datos del cliente: "
          "comportamiento de pago, límite, deuda y perfil. Sirve para aprobar o rechazar solicitudes, fijar cupos y "
          "priorizar la cobranza. Antes de modelar, el EDA revela la calidad de los datos, las variables más "
          "informativas y los problemas (colinealidad, desbalance, atípicos). La sección **Predecir** es un ejemplo "
          "de scoring con el mejor modelo.",
          "A **scoring model** estimates the probability of default (PD) from client data: payment behavior, limit, "
          "debt and profile. It is used to approve or reject applications, set limits and prioritize collections. "
          "Before modeling, the EDA reveals data quality, the most informative variables and the issues "
          "(collinearity, imbalance, outliers). The **Predict** section is an example of scoring with the best model."),
        pagina="/marco", sug=t(["Explícame la página Predecir", "¿Qué es el EDA?"],
                               ["Explain the Predict page", "What is EDA?"])))
    add(Intencion(
        "eda_concepto", t("Qué es el EDA", "What EDA is"),
        t(["qué es el EDA", "qué es análisis exploratorio de datos", "qué significa EDA", "Tukey",
           "diferencia entre univariado y multivariado", "qué es univariado", "qué es multivariado"],
          ["what is EDA", "what is exploratory data analysis", "what does EDA mean", "Tukey",
           "difference between univariate and multivariate", "what is univariate", "what is multivariate"]),
        t("El **análisis exploratorio de datos (EDA)**, propuesto por John W. Tukey (1977), explora los datos con "
          "resúmenes y gráficos antes de ajustar modelos, para descubrir patrones, anomalías y supuestos.\n\n"
          "- **Univariado:** una variable a la vez (frecuencias, histograma, boxplot) → página EDA Univariado.\n"
          "- **Multivariado:** relaciones entre variables (correlaciones, cruces, comparaciones por grupo) → "
          "página EDA Multivariado.",
          "**Exploratory data analysis (EDA)**, proposed by John W. Tukey (1977), explores the data with summaries "
          "and charts before fitting models, to discover patterns, anomalies and assumptions.\n\n"
          "- **Univariate:** one variable at a time (frequencies, histogram, boxplot) → Univariate EDA page.\n"
          "- **Multivariate:** relationships between variables (correlations, crosses, group comparisons) → "
          "Multivariate EDA page."),
        pagina="/marco", sug=t(["Explícame el EDA univariado", "Explícame el EDA multivariado"],
                               ["Explain the univariate EDA", "Explain the multivariate EDA"])))
    add(Intencion(
        "atipicos", t("Asimetría, atípicos y winsorización", "Skewness, outliers and winsorization"),
        t(["qué es un valor atípico", "qué son los outliers", "regla de Tukey", "qué es la asimetría",
           "qué es la curtosis", "qué es winsorizar", "qué es la winsorización", "qué es el IQR",
           "transformación logarítmica", "qué es skewness", "qué es el recorte P99", "qué es el percentil 99"],
          ["what is an outlier", "what are outliers", "Tukey rule", "what is skewness", "what is kurtosis",
           "what is winsorizing", "what is winsorization", "what is the IQR", "log transformation",
           "what is the P99 trim", "what is the 99th percentile"]),
        t("- **Asimetría (skewness):** hacia dónde se alarga la cola; los montos de dinero suelen tener una cola "
          "larga a la derecha.\n- **Curtosis:** qué tan pesadas son las colas.\n"
          "- **Atípico de Tukey:** x < Q1 − 1.5·IQR o x > Q3 + 1.5·IQR, con IQR = Q3 − Q1.\n"
          "- **Winsorizar:** recortar los extremos a percentiles (p. ej. P1–P99) sin eliminar clientes.\n"
          "- **Recorte P99 en las gráficas:** solo cambia la *vista*, para que unos pocos montos enormes no aplasten "
          "el gráfico; los datos no se modifican.\n"
          "- **Log con signo:** suaviza colas largas cuando hay ceros o negativos.",
          "- **Skewness:** which way the tail stretches; money amounts usually have a long right tail.\n"
          "- **Kurtosis:** how heavy the tails are.\n"
          "- **Tukey outlier:** x < Q1 − 1.5·IQR or x > Q3 + 1.5·IQR, with IQR = Q3 − Q1.\n"
          "- **Winsorizing:** capping the extremes at percentiles (e.g. P1–P99) without removing clients.\n"
          "- **P99 trim in the charts:** only changes the *view*, so that a few huge amounts don't squash the "
          "chart; the data is not modified.\n"
          "- **Signed log:** smooths long tails when there are zeros or negatives."),
        pagina="/marco", sug=t(["Explícame el explorador univariado", "¿Qué es BILL_AMT?"],
                               ["Explain the univariate explorer", "What is BILL_AMT?"])))
    add(Intencion(
        "desbalance", t("Desbalance de clases", "Class imbalance"),
        t(["qué es el desbalance de clases", "por qué las clases están desbalanceadas", "clases desbalanceadas",
           "por qué no usar accuracy", "qué tan desbalanceada está la variable objetivo", "clase minoritaria"],
          ["what is class imbalance", "why are the classes imbalanced", "imbalanced classes",
           "why not use accuracy", "how imbalanced is the target variable", "minority class"]),
        t(f"Hay **desbalance de clases** cuando una clase es mucho menos frecuente. Aquí solo {pct(rate)} incumple "
          f"(razón ≈ {(1 - rate) / rate:.1f}:1), así que un modelo que diga «todos pagan» acertaría {pct(1 - rate)} "
          "de las veces sin servir para nada. Por eso:\n\n"
          "- se ponderan las clases (**class_weight**) o se sobremuestrea la minoritaria (**SMOTE**, **ADASYN**);\n"
          "- se ajusta el umbral de decisión;\n"
          "- se evalúa con **F1, recall y AUC** en lugar de accuracy.",
          f"There is **class imbalance** when one class is much less frequent. Here only {pct(rate)} default "
          f"(ratio ≈ {(1 - rate) / rate:.1f}:1), so a model that says “everyone pays” would be right {pct(1 - rate)} "
          "of the time while being useless. That is why:\n\n"
          "- classes are weighted (**class_weight**) or the minority is oversampled (**SMOTE**, **ADASYN**);\n"
          "- the decision threshold is adjusted;\n"
          "- evaluation uses **F1, recall and AUC** instead of accuracy."),
        pagina="/marco", sug=t(["¿Qué técnicas de balanceo usaron?", "¿Qué es el F1?", "Explícame la variable objetivo"],
                               ["Which balancing techniques were used?", "What is F1?", "Explain the target variable"])))
    add(Intencion(
        "spearman", t("Correlación de Spearman y VIF", "Spearman correlation and VIF"),
        t(["qué es Spearman", "qué es la correlación de Spearman", "por qué Spearman y no Pearson", "qué es rho",
           "qué es el VIF", "qué es la multicolinealidad", "factor de inflación de la varianza", "qué es ρ"],
          ["what is Spearman", "what is Spearman correlation", "why Spearman and not Pearson", "what is rho",
           "what is VIF", "what is multicollinearity", "variance inflation factor", "what is ρ"]),
        t("**Spearman** (ρ) es la correlación de Pearson calculada sobre los *rangos* de los datos. Mide asociación "
          "monótona, no exige linealidad ni normalidad y resiste valores extremos. Se eligió sobre Pearson porque los "
          "montos son muy asimétricos, PAY_x es ordinal y la variable objetivo es binaria.\n\n"
          "**Multicolinealidad:** predictoras casi redundantes que inflan la varianza de los coeficientes. Se mide "
          "con el **VIF = 1 / (1 − R²)**; un VIF > 10 (o > 5) es alerta. En este dataset las BILL_AMT superan 20.",
          "**Spearman** (ρ) is the Pearson correlation computed on the *ranks* of the data. It measures monotonic "
          "association, requires neither linearity nor normality and is robust to extreme values. It was chosen "
          "over Pearson because the amounts are highly skewed, PAY_x is ordinal and the target is binary.\n\n"
          "**Multicollinearity:** nearly redundant predictors that inflate the variance of the coefficients. It is "
          "measured with **VIF = 1 / (1 − R²)**; a VIF > 10 (or > 5) is a warning. In this dataset the BILL_AMT "
          "exceed 20."),
        pagina="/marco", sug=t(["Explícame la matriz de correlación", "¿Qué es BILL_AMT?"],
                               ["Explain the correlation matrix", "What is BILL_AMT?"])))
    add(Intencion(
        "cramer", t("χ² y V de Cramér", "χ² and Cramér's V"),
        t(["qué es la V de Cramér", "qué es chi cuadrado", "prueba chi cuadrado", "qué es χ²",
           "tamaño del efecto categórico", "asociación entre variables categóricas", "chi2"],
          ["what is Cramér's V", "what is Cramer's V", "what is chi square", "chi square test", "what is χ²",
           "categorical effect size", "association between categorical variables", "chi2"]),
        t("La prueba **χ² de independencia** contrasta si dos variables categóricas están asociadas. Su tamaño de "
          "efecto es la **V de Cramér** = √(χ² / (n · min(r−1, c−1))), de 0 a 1: V < 0.1 es pequeño y V ≈ 0.3 "
          "moderado. En el tablero, educación, estado civil y sexo dan V < 0.1: hay diferencias, pero pequeñas.",
          "The **χ² test of independence** checks whether two categorical variables are associated. Its effect "
          "size is **Cramér's V** = √(χ² / (n · min(r−1, c−1))), from 0 to 1: V < 0.1 is small and V ≈ 0.3 "
          "moderate. In the dashboard, education, marital status and sex give V < 0.1: there are differences, "
          "but they are small."),
        pagina="/marco", sug=t(["Explícame las tasas por educación, estado civil y sexo", "¿Qué es el p-value?"],
                               ["Explain the rates by education, marital status and sex", "What is the p-value?"])))
    add(Intencion(
        "pruebas_grupos", t("Mann-Whitney, Kruskal-Wallis y t de Welch", "Mann-Whitney, Kruskal-Wallis and Welch's t"),
        t(["qué es Mann-Whitney", "qué es Kruskal-Wallis", "qué es la t de Welch", "pruebas no paramétricas",
           "comparación de grupos", "qué es el p-value", "qué significa p<0.001", "qué es significancia estadística",
           "tamaño del efecto"],
          ["what is Mann-Whitney", "what is Kruskal-Wallis", "what is Welch's t", "non-parametric tests",
           "group comparison", "what is the p-value", "what does p<0.001 mean", "what is statistical significance",
           "effect size"]),
        t("- **Mann-Whitney U:** compara dos grupos sin suponer normalidad (usa rangos).\n"
          "- **Kruskal-Wallis H:** lo mismo para tres o más grupos.\n"
          "- **t de Welch:** compara medias con varianzas distintas.\n\n"
          f"Ojo con el **p-value**: con n ≈ {n:,} casi cualquier diferencia sale «significativa» (p < 0.05). Por eso el "
          "tablero reporta también el **tamaño del efecto** y la relevancia práctica.",
          "- **Mann-Whitney U:** compares two groups without assuming normality (uses ranks).\n"
          "- **Kruskal-Wallis H:** the same for three or more groups.\n"
          "- **Welch's t:** compares means with unequal variances.\n\n"
          f"Careful with the **p-value**: with n ≈ {n:,} almost any difference is “significant” (p < 0.05). That is "
          "why the dashboard also reports the **effect size** and practical relevance."),
        pagina="/marco", sug=t(["Explícame el boxplot del límite de crédito", "¿Qué es la V de Cramér?"],
                               ["Explain the credit limit boxplot", "What is Cramér's V?"])))
    add(Intencion(
        "antecedentes", t("Antecedentes y referencias", "Background and references"),
        t(["antecedentes", "referencias", "bibliografía", "qué hicieron Yeh y Lien", "estudios previos",
           "sorting smoothing method"],
          ["background", "references", "bibliography", "what did Yeh and Lien do", "previous studies",
           "sorting smoothing method"]),
        t("**Antecedentes:** Yeh y Lien (2009) compararon seis técnicas (regresión logística, análisis discriminante, "
          "k vecinos, Naive Bayes, redes neuronales y árboles) con estos mismos datos y propusieron el *Sorting "
          "Smoothing Method* para estimar la probabilidad real de incumplimiento. La sección **Modelos** retoma esa "
          "comparación con 7 clasificadores, 4 técnicas de balanceo y 4 métodos de optimización.\n\n"
          "Las **referencias** (desplegable al final del Marco Teórico) incluyen Basilea II, Chawla et al. (SMOTE), "
          "Cramér, Kruskal-Wallis, Mann-Whitney, Spearman, Tukey y Yeh & Lien.",
          "**Background:** Yeh and Lien (2009) compared six techniques (logistic regression, discriminant analysis, "
          "k-nearest neighbors, Naive Bayes, neural networks and trees) on this same data and proposed the *Sorting "
          "Smoothing Method* to estimate the real probability of default. The **Models** section revisits that "
          "comparison with 7 classifiers, 4 balancing techniques and 4 optimization methods.\n\n"
          "The **references** (collapsible at the end of the Theoretical Framework) include Basel II, Chawla et al. "
          "(SMOTE), Cramér, Kruskal-Wallis, Mann-Whitney, Spearman, Tukey and Yeh & Lien."),
        pagina="/marco", sug=t(["Explícame la página de modelos", "¿Qué es SMOTE?"],
                               ["Explain the models page", "What is SMOTE?"])))
    add(Intencion(
        "diccionario", t("Diccionario de variables", "Variable dictionary"),
        t(["muéstrame el diccionario de variables", "qué variables tiene", "lista de variables", "diccionario de datos",
           "qué significa cada variable", "qué columnas hay", "variables del dataset"],
          ["show me the variable dictionary", "what variables does it have", "list of variables", "data dictionary",
           "what does each variable mean", "what columns are there", "dataset variables"]),
        t("**Diccionario de variables** (Marco Teórico):\n\n"
          "- **LIMIT_BAL:** cupo de crédito en NT$.\n- **SEX:** 1 hombre, 2 mujer.\n"
          "- **EDUCATION:** 1 posgrado, 2 universidad, 3 secundaria, 4 otros.\n"
          "- **MARRIAGE:** 1 casado, 2 soltero, 3 otros.\n- **AGE:** edad en años.\n"
          "- **PAY_0, PAY_2…PAY_6:** estado de pago de septiembre a abril (−2/−1/0 sin atraso; 1…8 meses de atraso).\n"
          "- **BILL_AMT1–6:** monto facturado de septiembre (1) a abril (6).\n"
          "- **PAY_AMT1–6:** monto pagado de septiembre (1) a abril (6).\n"
          "- **default_payment_next_month:** 1 si incumple en octubre de 2005.",
          "**Variable dictionary** (Theoretical Framework):\n\n"
          "- **LIMIT_BAL:** credit limit in NT$.\n- **SEX:** 1 male, 2 female.\n"
          "- **EDUCATION:** 1 graduate school, 2 university, 3 high school, 4 others.\n"
          "- **MARRIAGE:** 1 married, 2 single, 3 others.\n- **AGE:** age in years.\n"
          "- **PAY_0, PAY_2…PAY_6:** repayment status from September to April (−2/−1/0 no delay; 1…8 months late).\n"
          "- **BILL_AMT1–6:** bill amount from September (1) to April (6).\n"
          "- **PAY_AMT1–6:** amount paid from September (1) to April (6).\n"
          "- **default_payment_next_month:** 1 if the client defaults in October 2005."),
        pagina="/marco", sug=t(["¿Qué es PAY_0?", "¿Qué es LIMIT_BAL?", "¿Qué es la variable objetivo?"],
                               ["What is PAY_0?", "What is LIMIT_BAL?", "What is the target variable?"])))

    # =====================================================================
    # Variables
    # =====================================================================
    b, tt = A.interp_uni("LIMIT_BAL")
    add(Intencion(
        "v_limit", t("LIMIT_BAL (cupo de crédito)", "LIMIT_BAL (credit limit)"),
        t(["qué es LIMIT_BAL", "limit_bal", "límite de crédito", "qué es el cupo", "cuánto cupo tienen los clientes",
           "distribución del límite de crédito"],
          ["what is LIMIT_BAL", "limit_bal", "credit limit", "what is the limit", "how much credit do clients have",
           "credit limit distribution"]),
        t(f"**LIMIT_BAL** es el cupo de crédito (individual + familiar) en NT$. {b}",
          f"**LIMIT_BAL** is the credit limit (individual + family) in NT$. {b}"),
        tecnico=tt, pagina="/univariado",
        sug=t(["Explícame el boxplot del límite de crédito", "¿Qué es PAY_0?"],
              ["Explain the credit limit boxplot", "What is PAY_0?"])))
    b, tt = A.interp_uni("AGE")
    add(Intencion(
        "v_age", t("AGE (edad)", "AGE (age)"),
        t(["qué es AGE", "edad de los clientes", "cuántos años tienen los clientes", "distribución de la edad",
           "edad promedio"],
          ["what is AGE", "age of the clients", "how old are the clients", "age distribution", "average age"]),
        t(f"**AGE** es la edad en años. {b}", f"**AGE** is the age in years. {b}"),
        tecnico=tt, pagina="/univariado",
        sug=t(["Explícame la gráfica de edad y atrasos", "¿Influye la edad en el default?"],
              ["Explain the age and delays chart", "Does age affect default?"])))
    rates_basic = A.interp_rates()[0]
    sex_rates = rates_basic.split(t(". Por", ". By"))[0]
    add(Intencion(
        "v_sex", t("SEX (sexo)", "SEX (sex)"),
        t(["qué es SEX", "variable sexo", "hombres y mujeres", "género", "incumplen más los hombres o las mujeres",
           "diferencia por sexo"],
          ["what is SEX", "sex variable", "men and women", "gender", "do men or women default more",
           "difference by sex"]),
        t(f"**SEX** es el sexo registrado: 1 = hombre, 2 = mujer (el dataset solo trae esas dos categorías). "
          f"{A.interp_uni('SEX')[0]} En la tasa de default: {sex_rates}.",
          f"**SEX** is the recorded sex: 1 = male, 2 = female (the dataset only has those two categories). "
          f"{A.interp_uni('SEX')[0]} In the default rate: {sex_rates}."),
        tecnico=A.interp_uni("SEX")[1], pagina="/univariado",
        sug=t(["Explícame las tasas por educación, estado civil y sexo", "¿Qué es la V de Cramér?"],
              ["Explain the rates by education, marital status and sex", "What is Cramér's V?"])))
    add(Intencion(
        "v_edu", t("EDUCATION (educación)", "EDUCATION (education)"),
        t(["qué es EDUCATION", "nivel educativo", "educación de los clientes", "variable educación",
           "influye la educación", "categoría otros en educación"],
          ["what is EDUCATION", "education level", "clients' education", "education variable",
           "does education matter", "others category in education"]),
        t(f"**EDUCATION**: 1 = posgrado, 2 = universidad, 3 = secundaria, 4 = otros (los códigos 0, 5 y 6 sin "
          f"documentar se agruparon en «Otros»). {A.interp_uni('EDUCATION')[0]}",
          f"**EDUCATION**: 1 = graduate school, 2 = university, 3 = high school, 4 = others (undocumented codes "
          f"0, 5 and 6 were grouped into “Others”). {A.interp_uni('EDUCATION')[0]}"),
        tecnico=A.interp_uni("EDUCATION")[1], pagina="/univariado",
        sug=t(["Explícame las tasas por educación, estado civil y sexo", "¿Cómo se limpiaron los datos?"],
              ["Explain the rates by education, marital status and sex", "How was the data cleaned?"])))
    add(Intencion(
        "v_mar", t("MARRIAGE (estado civil)", "MARRIAGE (marital status)"),
        t(["qué es MARRIAGE", "estado civil", "casados y solteros", "variable estado civil"],
          ["what is MARRIAGE", "marital status", "married and single", "marital status variable"]),
        t(f"**MARRIAGE**: 1 = casado, 2 = soltero, 3 = otros (el código 0 pasó a «Otros»). {A.interp_uni('MARRIAGE')[0]}",
          f"**MARRIAGE**: 1 = married, 2 = single, 3 = others (code 0 was moved to “Others”). "
          f"{A.interp_uni('MARRIAGE')[0]}"),
        tecnico=A.interp_uni("MARRIAGE")[1], pagina="/univariado",
        sug=t(["Explícame las tasas por educación, estado civil y sexo"],
              ["Explain the rates by education, marital status and sex"])))
    b, tt = A.interp_uni("PAY_0")
    add(Intencion(
        "v_pay", t("PAY_0 … PAY_6 (estado de pago)", "PAY_0 … PAY_6 (repayment status)"),
        t(["qué es PAY_0", "pay_0", "qué significa PAY", "estado de pago", "qué significa -2 -1 0 en PAY",
           "historial de pagos", "PAY_2", "PAY_6", "meses de atraso", "qué es el atraso", "por qué no existe PAY_1",
           "qué significa pago mínimo en PAY"],
          ["what is PAY_0", "pay_0", "what does PAY mean", "repayment status", "what do -2 -1 0 mean in PAY",
           "payment history", "PAY_2", "PAY_6", "months late", "what is the delay", "why is there no PAY_1",
           "what does minimum payment mean in PAY"]),
        t("**PAY_0, PAY_2 … PAY_6** son el estado de pago mensual: PAY_0 es septiembre y PAY_6 abril.\n\n"
          "- **−2:** sin consumo · **−1:** pagó todo · **0:** pago mínimo (crédito rotativo)\n"
          "- **1 a 8:** meses de atraso\n\n"
          f"{b} Es **la variable más importante** del análisis: {findings[0][1]}",
          "**PAY_0, PAY_2 … PAY_6** are the monthly repayment status: PAY_0 is September and PAY_6 April.\n\n"
          "- **−2:** no use · **−1:** paid in full · **0:** minimum payment (revolving credit)\n"
          "- **1 to 8:** months late\n\n"
          f"{b} It is **the most important variable** in the analysis: {findings[0][1]}"),
        tecnico=tt, pagina="/univariado",
        sug=t(["Explícame el vistazo rápido", "¿Qué variables pesan más en el modelo?", "¿Qué es BILL_AMT?"],
              ["Explain the quick look", "Which variables matter most in the model?", "What is BILL_AMT?"])))
    b, tt = A.interp_quant("BILL_AMT")
    add(Intencion(
        "v_bill", t("BILL_AMT1–6 (facturación)", "BILL_AMT1–6 (billing)"),
        t(["qué es BILL_AMT", "bill_amt", "monto facturado", "facturas mensuales", "qué es la facturación",
           "por qué hay facturas negativas", "saldo a favor", "BILL_AMT1"],
          ["what is BILL_AMT", "bill_amt", "bill amount", "monthly bills", "what is billing",
           "why are there negative bills", "credit balance", "BILL_AMT1"]),
        t(f"**BILL_AMT1–6** es el monto facturado en el estado de cuenta, de septiembre (1) a abril (6), en NT$. {b}",
          f"**BILL_AMT1–6** is the amount on the bill statement, from September (1) to April (6), in NT$. {b}"),
        tecnico=tt, pagina="/univariado",
        sug=t(["¿Qué es PAY_AMT?", "¿Qué es la multicolinealidad?", "Explícame la matriz de correlación"],
              ["What is PAY_AMT?", "What is multicollinearity?", "Explain the correlation matrix"])))
    b, tt = A.interp_quant("PAY_AMT")
    add(Intencion(
        "v_payamt", t("PAY_AMT1–6 (montos pagados)", "PAY_AMT1–6 (amounts paid)"),
        t(["qué es PAY_AMT", "pay_amt", "montos pagados", "cuánto pagan los clientes", "pagos mensuales",
           "diferencia entre PAY y PAY_AMT", "PAY_AMT1"],
          ["what is PAY_AMT", "pay_amt", "amounts paid", "how much do clients pay", "monthly payments",
           "difference between PAY and PAY_AMT", "PAY_AMT1"]),
        t(f"**PAY_AMT1–6** es lo que el cliente pagó, de septiembre (1) a abril (6), en NT$. No confundir con "
          f"PAY_x, que es el *estado* de pago. {b}",
          f"**PAY_AMT1–6** is what the client paid, from September (1) to April (6), in NT$. Not to be confused "
          f"with PAY_x, which is the repayment *status*. {b}"),
        tecnico=tt, pagina="/univariado", sug=t(["¿Qué es BILL_AMT?", "¿Qué es PAY_0?"],
                                               ["What is BILL_AMT?", "What is PAY_0?"])))
    b, tt = A.interp_target()
    add(Intencion(
        "v_target", t("Variable objetivo (default)", "Target variable (default)"),
        t(["qué es la variable objetivo", "default_payment_next_month", "explícame la variable objetivo",
           "cuántos clientes incumplen", "tasa de default", "qué porcentaje no paga", "gráfica default vs no default",
           "qué es target", "cuál es la tasa global de default"],
          ["what is the target variable", "default_payment_next_month", "explain the target variable",
           "how many clients default", "default rate", "what percentage does not pay", "default vs no default chart",
           "what is the target", "what is the overall default rate"]),
        t(f"La **variable objetivo** (default_payment_next_month) vale 1 si el cliente no pagó en octubre de 2005. {b}",
          f"The **target variable** (default_payment_next_month) is 1 if the client did not pay in October 2005. {b}"),
        tecnico=tt, pagina="/univariado",
        sug=t(["¿Qué es el desbalance de clases?", "¿Qué técnicas de balanceo usaron?"],
              ["What is class imbalance?", "Which balancing techniques were used?"]), mood="alert"))

    # =====================================================================
    # EDA univariado
    # =====================================================================
    add(Intencion(
        "p_uni", t("EDA Univariado", "Univariate EDA"),
        t(["explícame el EDA univariado", "qué hay en el EDA univariado", "página univariada", "análisis univariado",
           "qué muestra el univariado"],
          ["explain the univariate EDA", "what is in the univariate EDA", "univariate page", "univariate analysis",
           "what does the univariate page show"]),
        t("El **EDA Univariado** mira cada variable por separado:\n\n"
          f"- **KPIs:** {n:,} registros, tasa de default {pct(rate)}, límite promedio {nt(df['LIMIT_BAL'].mean())} "
          f"y edad promedio {df['AGE'].mean():.1f} años.\n"
          "- **Variable objetivo:** barras con cuántos pagan y cuántos no (desbalance).\n"
          "- **Explorador univariado:** eliges una variable y ves su histograma + boxplot o sus barras.\n"
          "- **Distribuciones cuantitativas:** LIMIT_BAL, AGE y los seis meses de BILL_AMT y PAY_AMT en "
          "histograma, boxplot o densidad.",
          "The **Univariate EDA** looks at each variable separately:\n\n"
          f"- **KPIs:** {n:,} records, default rate {pct(rate)}, average limit {nt(df['LIMIT_BAL'].mean())} "
          f"and average age {df['AGE'].mean():.1f} years.\n"
          "- **Target variable:** bars with how many pay and how many don't (imbalance).\n"
          "- **Univariate explorer:** you choose a variable and see its histogram + boxplot or its bars.\n"
          "- **Quantitative distributions:** LIMIT_BAL, AGE and the six months of BILL_AMT and PAY_AMT as a "
          "histogram, boxplot or density."),
        pagina="/univariado",
        sug=t(["Explícame la variable objetivo", "Explícame el explorador univariado",
               "Explícame las distribuciones cuantitativas"],
              ["Explain the target variable", "Explain the univariate explorer",
               "Explain the quantitative distributions"])))
    add(Intencion(
        "uni_explorador", t("Explorador univariado", "Univariate explorer"),
        t(["explícame el explorador univariado", "cómo uso el explorador univariado", "histograma con boxplot",
           "qué significa la línea de la mediana", "qué es recortar cola superior", "el selector de variable",
           "para qué sirve el checkbox de P99"],
          ["explain the univariate explorer", "how do I use the univariate explorer", "histogram with boxplot",
           "what does the median line mean", "what is trimming the upper tail", "the variable selector",
           "what is the P99 checkbox for"]),
        t("En el **Explorador univariado** eliges cualquier variable:\n\n"
          "- **Numéricas:** histograma arriba y boxplot abajo; la línea dorada punteada es la **mediana** y en el "
          "boxplot la línea punteada es la media.\n"
          "- **Categóricas** (SEX, EDUCATION, PAY_x…): barras con el porcentaje de cada categoría.\n"
          "- **Recortar cola superior (P99):** oculta el 1 % de valores más altos *solo en la vista*, para que se "
          "vea la forma de la distribución.\n\n"
          "En **Ver interpretación**, la explicación se actualiza sola con la variable que elijas.",
          "In the **Univariate explorer** you choose any variable:\n\n"
          "- **Numeric:** histogram on top and boxplot below; the dashed gold line is the **median** and in the "
          "boxplot the dashed line is the mean.\n"
          "- **Categorical** (SEX, EDUCATION, PAY_x…): bars with the percentage of each category.\n"
          "- **Trim the upper tail (P99):** hides the top 1% of values *only in the view*, so the shape of the "
          "distribution can be seen.\n\n"
          "In **Show interpretation**, the explanation updates automatically with the variable you choose."),
        tecnico=t("La interpretación técnica reporta n, media, mediana, σ, IQR, asimetría, curtosis y % de atípicos de "
                  "Tukey. Si |asimetría| > 2 sugiere transformación logarítmica con signo. Para PAY_x informa la moda y "
                  "el % con atraso ≥ 1 mes, y recomienda tratarla como ordinal/categórica.",
                  "The technical interpretation reports n, mean, median, σ, IQR, skewness, kurtosis and % of Tukey "
                  "outliers. If |skewness| > 2 it suggests a signed log transformation. For PAY_x it reports the mode "
                  "and the % with a delay ≥ 1 month, and recommends treating it as ordinal/categorical."),
        pagina="/univariado", sug=t(["¿Qué es un valor atípico?", "¿Qué es LIMIT_BAL?", "¿Qué es PAY_0?"],
                                    ["What is an outlier?", "What is LIMIT_BAL?", "What is PAY_0?"])))
    b, tt = A.interp_quant("BILL_AMT")
    add(Intencion(
        "uni_cuant", t("Distribuciones de variables cuantitativas", "Distributions of quantitative variables"),
        t(["explícame las distribuciones cuantitativas", "histograma boxplot densidad", "qué es la densidad",
           "qué es un boxplot", "qué es un histograma", "comparar los seis meses de BILL_AMT",
           "familia de variables", "gráfica de densidad"],
          ["explain the quantitative distributions", "histogram boxplot density", "what is density",
           "what is a boxplot", "what is a histogram", "compare the six months of BILL_AMT", "variable family",
           "density chart"]),
        t("La tarjeta **Distribuciones de variables cuantitativas** compara LIMIT_BAL, AGE y las familias BILL_AMT y "
          "PAY_AMT (un color por mes). Puedes verla como:\n\n"
          "- **Histograma:** cuántos clientes caen en cada rango.\n"
          "- **Boxplot:** la caja va del 25 % al 75 % de los datos, la línea es la mediana y los bigotes los "
          "valores típicos.\n- **Densidad:** una curva suavizada de la forma de la distribución.\n\n"
          f"La vista se limita al rango P1–P99. Por ejemplo, para BILL_AMT: {b}",
          "The **Distributions of quantitative variables** card compares LIMIT_BAL, AGE and the BILL_AMT and "
          "PAY_AMT families (one color per month). You can view it as:\n\n"
          "- **Histogram:** how many clients fall in each range.\n"
          "- **Boxplot:** the box goes from 25% to 75% of the data, the line is the median and the whiskers the "
          "typical values.\n- **Density:** a smoothed curve of the shape of the distribution.\n\n"
          f"The view is limited to the P1–P99 range. For example, for BILL_AMT: {b}"),
        tecnico=tt, pagina="/univariado", sug=t(["¿Qué es PAY_AMT?", "¿Qué es un valor atípico?"],
                                               ["What is PAY_AMT?", "What is an outlier?"])))

    # =====================================================================
    # EDA multivariado
    # =====================================================================
    add(Intencion(
        "p_multi", t("EDA Multivariado", "Multivariate EDA"),
        t(["explícame el EDA multivariado", "qué hay en el multivariado", "página multivariada", "análisis multivariado",
           "qué muestra el multivariado"],
          ["explain the multivariate EDA", "what is in the multivariate page", "multivariate page",
           "multivariate analysis", "what does the multivariate page show"]),
        t("El **EDA Multivariado** estudia relaciones entre variables y con el default:\n\n"
          "1. **Matriz de correlación de Spearman**\n2. **Incumplimiento por educación, estado civil y sexo**\n"
          "3. **Límite de crédito según default** (boxplots)\n4. **Edad y patrones de atraso** (tres vistas)\n"
          "5. **Módulo interactivo de cruce de variables**\n6. **Matriz de dispersión**\n"
          "7. **Hallazgos multivariados clave**",
          "The **Multivariate EDA** studies relationships between variables and with default:\n\n"
          "1. **Spearman correlation matrix**\n2. **Default by education, marital status and sex**\n"
          "3. **Credit limit by default** (boxplots)\n4. **Age and delay patterns** (three views)\n"
          "5. **Interactive variable cross module**\n6. **Scatter matrix**\n"
          "7. **Key multivariate findings**"),
        pagina="/multivariado",
        sug=t(["Explícame la matriz de correlación", "Explícame las tasas por educación, estado civil y sexo",
               "¿Cuáles son los hallazgos clave?"],
              ["Explain the correlation matrix", "Explain the rates by education, marital status and sex",
               "What are the key findings?"])))
    b, tt = A.interp_corr()
    add(Intencion(
        "corr", t("Matriz de correlación de Spearman", "Spearman correlation matrix"),
        t(["explícame la matriz de correlación", "mapa de calor de correlación", "qué significan los colores de la matriz",
           "correlaciones entre variables", "heatmap de correlación", "qué variable se relaciona más con el default",
           "bloque dorado de la matriz", "matriz de Spearman"],
          ["explain the correlation matrix", "correlation heatmap", "what do the colors of the matrix mean",
           "correlations between variables", "which variable is most related to default",
           "gold block in the matrix", "Spearman matrix"]),
        t(f"Cada celda es la correlación de Spearman entre dos variables: **dorado** = relación directa, **azul** = "
          f"inversa, crema = casi nada. {b}",
          f"Each cell is the Spearman correlation between two variables: **gold** = direct relationship, **blue** = "
          f"inverse, cream = almost none. {b}"),
        tecnico=tt, pagina="/multivariado",
        sug=t(["¿Qué es Spearman?", "¿Qué es la multicolinealidad?", "¿Qué es PAY_0?"],
              ["What is Spearman?", "What is multicollinearity?", "What is PAY_0?"])))
    b, tt = A.interp_rates()
    add(Intencion(
        "rates", t("Default por educación, estado civil y sexo", "Default by education, marital status and sex"),
        t(["explícame las tasas por educación, estado civil y sexo", "tasa de default por perfil demográfico",
           "barras doradas y azules", "incumplimiento por educación", "default por estado civil",
           "quién incumple más", "perfil demográfico", "influye el sexo en el default"],
          ["explain the rates by education, marital status and sex", "default rate by demographic profile",
           "gold and blue bars", "default by education", "default by marital status", "who defaults more",
           "demographic profile", "does sex affect default"]),
        t(f"Cada barra es la tasa de default de un grupo; la línea punteada es la tasa global ({pct(rate)}). Las "
          f"barras **doradas** están por encima del promedio y las **azules** por debajo. {b}",
          f"Each bar is the default rate of a group; the dashed line is the overall rate ({pct(rate)}). "
          f"**Gold** bars are above average and **blue** ones below. {b}"),
        tecnico=tt, pagina="/multivariado", sug=t(["¿Qué es la V de Cramér?", "¿Qué es EDUCATION?"],
                                                 ["What is Cramér's V?", "What is EDUCATION?"])))
    b, tt = A.interp_limit()
    add(Intencion(
        "limit_box", t("Límite de crédito según default", "Credit limit by default"),
        t(["explícame el boxplot del límite de crédito", "límite de crédito según default", "LIMIT_BAL por default",
           "tienen menos cupo los que incumplen", "escala logarítmica del boxplot", "boxplot de LIMIT_BAL",
           "cómo leo el boxplot", "cupo de quienes no pagan frente a quienes pagan",
           "límite de los morosos vs los cumplidos", "los que incumplen tienen un límite menor",
           "mediana del límite por default"],
          ["explain the credit limit boxplot", "credit limit by default", "LIMIT_BAL by default",
           "do defaulters have a lower limit", "log scale of the boxplot", "LIMIT_BAL boxplot", "how do I read the boxplot",
           "limit of those who don't pay vs those who pay", "median limit by default"]),
        t(f"Son dos cajas: **azul** = clientes que pagaron, **dorada** = los que incumplieron. La línea dentro de "
          f"la caja es la mediana. {b} Puedes cambiar a escala **logarítmica** para ver mejor los valores bajos.",
          f"There are two boxes: **blue** = clients who paid, **gold** = those who defaulted. The line inside the box "
          f"is the median. {b} You can switch to a **logarithmic** scale to see low values better."),
        tecnico=tt, pagina="/multivariado", sug=t(["¿Qué es Mann-Whitney?", "¿Qué es LIMIT_BAL?"],
                                                 ["What is Mann-Whitney?", "What is LIMIT_BAL?"])))
    bl, tl = A.interp_age("lines")
    bh, th = A.interp_age("heat")
    br, tr = A.interp_age("rate")
    add(Intencion(
        "age", t("Edad y patrones de atraso", "Age and delay patterns"),
        t(["explícame la gráfica de edad y atrasos", "influye la edad en el default", "edad y patrones de atraso",
           "atraso promedio por mes y grupo de edad", "porcentaje con atraso por edad", "tasa de default por edad",
           "los jóvenes incumplen más", "mapa de calor de edad"],
          ["explain the age and delays chart", "does age affect default", "age and delay patterns",
           "average delay by month and age group", "percentage late by age", "default rate by age",
           "do young people default more", "age heatmap", "do older clients fall behind on payments",
           "falling behind by age group", "late payments by age"]),
        t("La tarjeta **Edad y patrones de atraso** tiene tres vistas:\n\n"
          f"- **Atraso promedio por mes:** {bl}\n- **% con atraso ≥ 1 mes:** {bh}\n- **Tasa de default por edad:** {br}",
          "The **Age and delay patterns** card has three views:\n\n"
          f"- **Average delay by month:** {bl}\n- **% with delay ≥ 1 month:** {bh}\n- **Default rate by age:** {br}"),
        tecnico=f"{tl} {th} {tr}", pagina="/multivariado", sug=t(["¿Qué es AGE?", "¿Qué es PAY_0?"],
                                                                 ["What is AGE?", "What is PAY_0?"])))
    add(Intencion(
        "cross", t("Módulo interactivo de cruce de variables", "Interactive variable cross module"),
        t(["explícame el cruce de variables", "módulo interactivo", "cómo uso el cruce de variables",
           "variable X variable Y color", "qué gráfico sale en el cruce", "ejes ajustados al percentil 99",
           "cruzar dos variables"],
          ["explain the variable cross", "interactive module", "how do I use the variable cross",
           "X variable Y variable color", "which chart appears in the cross", "axes fitted to the 99th percentile",
           "cross two variables"]),
        t("En el **cruce de variables** eliges **X**, **Y** y, si quieres, una tercera como **color/grupo**. El "
          "tipo de gráfico se ajusta solo:\n\n"
          "- numérica × numérica → **dispersión** con línea de tendencia;\n"
          "- categórica × numérica → **boxplots** por grupo;\n"
          "- categórica × default → **barras de tasa**;\n"
          "- categórica × categórica → **mapa de calor**.\n\n"
          "«Ejes ajustados al percentil 99» corta la vista donde está el 99 % de los clientes. La interpretación "
          "(botón **Ver interpretación**) cambia con tu elección.",
          "In the **variable cross** you choose **X**, **Y** and, optionally, a third one as **color/group**. The "
          "chart type adjusts automatically:\n\n"
          "- numeric × numeric → **scatter** with a trend line;\n"
          "- categorical × numeric → **boxplots** by group;\n"
          "- categorical × default → **rate bars**;\n"
          "- categorical × categorical → **heatmap**.\n\n"
          "“Axes fitted to the 99th percentile” cuts the view where 99% of clients are. The interpretation "
          "(**Show interpretation** button) changes with your choice."),
        tecnico=t("Según el tipo de par se reportan Spearman, Mann-Whitney / Kruskal-Wallis o χ² con V de Cramér. "
                  "Con n ≈ 30 000 el p-value casi siempre es significativo, por eso conviene mirar el tamaño del efecto.",
                  "Depending on the type of pair, Spearman, Mann-Whitney / Kruskal-Wallis or χ² with Cramér's V are "
                  "reported. With n ≈ 30,000 the p-value is almost always significant, so the effect size matters."),
        pagina="/multivariado", sug=t(["¿Qué es Kruskal-Wallis?", "¿Qué es la V de Cramér?"],
                                      ["What is Kruskal-Wallis?", "What is Cramér's V?"])))
    add(Intencion(
        "splom", t("Matriz de dispersión", "Scatter matrix"),
        t(["explícame la matriz de dispersión", "scatter matrix", "splom", "puntos azules y dorados",
           "cruzar varias variables a la vez", "matriz de dispersión de 2 a 6 variables"],
          ["explain the scatter matrix", "scatter matrix", "splom", "blue and gold points",
           "cross several variables at once", "scatter matrix of 2 to 6 variables"]),
        t("La **matriz de dispersión** cruza entre 2 y 6 variables numéricas a la vez sobre una muestra de 1,500 "
          "clientes. Cada punto es un cliente: **azul** = pagó, **dorado** = incumplió. Si los puntos dorados se "
          "concentran en una zona, esa combinación separa a los clientes de riesgo. La interpretación indica qué "
          "par de variables se parece más.",
          "The **scatter matrix** crosses 2 to 6 numeric variables at once on a sample of 1,500 clients. Each point "
          "is a client: **blue** = paid, **gold** = defaulted. If the gold points cluster in one area, that "
          "combination separates risky clients. The interpretation shows which pair of variables is most similar."),
        tecnico=t("Se reportan los pares con mayor |ρ| de Spearman; sirve para detectar colinealidad entre predictoras "
                  "y regiones donde se concentra la clase 1.",
                  "The pairs with the highest Spearman |ρ| are reported; useful to detect collinearity between "
                  "predictors and regions where class 1 concentrates."),
        pagina="/multivariado", sug=t(["Explícame la matriz de correlación", "Explícame el cruce de variables"],
                                      ["Explain the correlation matrix", "Explain the variable cross"])))
    add(Intencion(
        "hallazgos", t("Hallazgos multivariados clave", "Key multivariate findings"),
        t(["cuáles son los hallazgos clave", "hallazgos multivariados", "tarjetas de hallazgos",
           "qué concluye el multivariado", "resumen del multivariado", "conclusiones del EDA multivariado",
           "hallazgos de las relaciones entre variables", "tarjetas finales del multivariado",
           "qué conclusiones hay en esta página multivariada"],
          ["what are the key findings", "multivariate findings", "findings cards", "what does the multivariate conclude",
           "multivariate summary", "conclusions of the multivariate EDA", "findings on relationships between variables"]),
        t("**Hallazgos multivariados clave:**\n\n", "**Key multivariate findings:**\n\n") +
        "\n".join(f"- **{ti}.** {tx_}" for ti, tx_ in findings),
        pagina="/multivariado", sug=t(["¿Cuál es el mejor modelo?", "¿Qué es PAY_0?"],
                                      ["Which is the best model?", "What is PAY_0?"]), mood="proud"))

    # =====================================================================
    # Modelos
    # =====================================================================
    add(Intencion(
        "p_modelos", t("Modelos", "Models"),
        t(["explícame la página de modelos", "qué hay en modelos", "sección de modelos", "qué modelos usaron",
           "cuántos modelos compararon", "qué clasificadores probaron", "112 combinaciones"],
          ["explain the models page", "what is in models", "models section", "which models did they use",
           "how many models did they compare", "which classifiers did they try", "112 combinations"]),
        t(f"**Modelos** resume {len(A.MR)} combinaciones: **7 clasificadores × 4 técnicas de balanceo × 4 métodos de "
          "optimización**, con validación cruzada anidada.\n\n"
          f"- **KPIs:** mejor F1 {B['f1_mean']:.3f} ({best_lbl}), mejora de +{B['f1_mean'] - BL:.3f} sobre la línea "
          f"base y {B['recall_mean']:.0%} de incumplimientos detectados.\n"
          "- **Carrusel:** la mejor combinación de cada modelo.\n"
          "- **F1 por modelo y técnica** (mapa de calor) y **F1 vs. ROC-AUC** (dispersión).\n"
          "- **Matriz de confusión** del mejor modelo y **resumen SHAP**.",
          f"**Models** summarizes {len(A.MR)} combinations: **7 classifiers × 4 balancing techniques × 4 optimization "
          "methods**, with nested cross-validation.\n\n"
          f"- **KPIs:** best F1 {B['f1_mean']:.3f} ({best_lbl}), +{B['f1_mean'] - BL:.3f} over the baseline and "
          f"{B['recall_mean']:.0%} of defaults detected.\n"
          "- **Carousel:** the best combination of each model.\n"
          "- **F1 by model and technique** (heatmap) and **F1 vs. ROC-AUC** (scatter).\n"
          "- **Confusion matrix** of the best model and **SHAP summary**."),
        pagina="/modelos", sug=t(["¿Cuál es el mejor modelo?", "Explícame el carrusel de modelos",
                                  "¿Qué técnicas de balanceo usaron?"],
                                 ["Which is the best model?", "Explain the model carousel",
                                  "Which balancing techniques were used?"])))
    add(Intencion(
        "mejor_modelo", t("Mejor modelo", "Best model"),
        t(["cuál es el mejor modelo", "mejor modelo del ranking", "modelo campeón", "cuál fue el mejor F1",
           "qué modelo eligieron", "cuánto mejoró sobre la línea base", "qué tan bueno es el modelo",
           "qué modelo funcionó mejor", "cuál dio mejores resultados", "el modelo ganador"],
          ["which is the best model", "what is the best model", "top model in the ranking", "champion model",
           "what was the best F1", "which model was chosen", "how much did it improve over the baseline",
           "how good is the model", "which model worked best", "the winning model"]),
        t(f"El mejor es **{best_lbl}** con **{tech_b}** y optimización **{meth_b}**:\n\n"
          f"- **F1:** {B['f1_mean']:.3f} ± {B['f1_std']:.3f} (línea base: {BL:.3f}, +{B['f1_mean'] - BL:.3f})\n"
          f"- **Recall:** {B['recall_mean']:.1%} · **Precisión:** {B['precision_mean']:.1%}\n"
          f"- **ROC-AUC:** {B['roc_auc_mean']:.3f} · **PR-AUC:** {B['pr_auc_mean']:.3f}\n\n"
          "Ojo: está prácticamente **empatado** con XGBoost y SVM; la diferencia es menor que la variación entre folds.",
          f"The best is **{best_lbl}** with **{tech_b}** and **{meth_b}** optimization:\n\n"
          f"- **F1:** {B['f1_mean']:.3f} ± {B['f1_std']:.3f} (baseline: {BL:.3f}, +{B['f1_mean'] - BL:.3f})\n"
          f"- **Recall:** {B['recall_mean']:.1%} · **Precision:** {B['precision_mean']:.1%}\n"
          f"- **ROC-AUC:** {B['roc_auc_mean']:.3f} · **PR-AUC:** {B['pr_auc_mean']:.3f}\n\n"
          "Note: it is practically **tied** with XGBoost and SVM; the difference is smaller than the variation "
          "between folds."),
        tecnico=t("Validación cruzada anidada 3×3; la prueba de Nemenyi no separa a Random Forest, XGBoost y SVM "
                  "(p ≥ 0.88), aunque Random Forest sí supera al árbol de decisión (p = 0.018). 15 de las 112 "
                  "combinaciones quedan a menos de una desviación estándar del mejor F1.",
                  "Nested 3×3 cross-validation; the Nemenyi test does not separate Random Forest, XGBoost and SVM "
                  "(p ≥ 0.88), although Random Forest does beat the decision tree (p = 0.018). 15 of the 112 "
                  "combinations are within one standard deviation of the best F1."),
        pagina="/modelos", sug=t(["Explícame la matriz de confusión", "¿Qué es el F1?", "¿Cómo le fue a XGBoost?"],
                                 ["Explain the confusion matrix", "What is F1?", "How did XGBoost do?"]),
        mood="proud"))
    ranking = ", ".join(f"{i + 1}. {A.minfo(r['model'], 'label')} ({r['f1_mean']:.3f})"
                        for i, r in A.BEST_BY_MODEL.iterrows())
    add(Intencion(
        "carrusel", t("Carrusel de modelos", "Model carousel"),
        t(["explícame el carrusel de modelos", "cómo leo las tarjetas de los modelos", "qué significan las barras del carrusel",
           "tarjetas deslizables de modelos", "qué es el borde dorado", "comparación de modelos", "ranking de modelos"],
          ["explain the model carousel", "how do I read the model cards", "what do the carousel bars mean",
           "sliding model cards", "what is the gold border", "model comparison", "model ranking"]),
        t("El **carrusel** muestra una tarjeta por modelo, con su **mejor combinación**, ordenadas por F1:\n\n"
          "- puesto, familia del modelo y F1 ± desviación estándar;\n"
          "- la técnica de balanceo y el método de optimización que lo lograron;\n"
          "- barras de precisión, recall, ROC-AUC y PR-AUC;\n"
          "- su mejor F1 con cada técnica de balanceo;\n- una descripción y una nota.\n\n"
          f"El **borde dorado** marca el mejor. Ranking: {ranking}.",
          "The **carousel** shows one card per model, with its **best combination**, ordered by F1:\n\n"
          "- rank, model family and F1 ± standard deviation;\n"
          "- the balancing technique and optimization method that achieved it;\n"
          "- precision, recall, ROC-AUC and PR-AUC bars;\n"
          "- its best F1 with each balancing technique;\n- a description and a note.\n\n"
          f"The **gold border** marks the best. Ranking: {ranking}."),
        pagina="/modelos", sug=t(["¿Cuál es el mejor modelo?", "¿Qué es el F1?", "¿Qué es el PR-AUC?"],
                                 ["Which is the best model?", "What is F1?", "What is PR-AUC?"])))
    add(Intencion(
        "heat_modelos", t("F1 por modelo y técnica de balanceo", "F1 by model and balancing technique"),
        t(["explícame el mapa de calor de F1", "F1 por modelo y técnica de balanceo", "qué técnica de balanceo es mejor",
           "sirve balancear", "sin balanceo vs pesos de clase", "heatmap de modelos"],
          ["explain the F1 heatmap", "F1 by model and balancing technique", "which balancing technique is best",
           "does balancing help", "no balancing vs class weights", "models heatmap"]),
        t("Cada celda es el **mejor F1** de un modelo con una técnica de balanceo. Sin balanceo todos rinden peor "
          "porque casi no detectan a quienes incumplen; con **pesos de clase**, Random Forest y XGBoost llegan a 0.55.",
          "Each cell is a model's **best F1** with a balancing technique. Without balancing all of them perform "
          "worse because they barely detect defaulters; with **class weights**, Random Forest and XGBoost reach 0.55."),
        tecnico=t("Friedman (28 bloques modelo × método): χ² = 59.8, p ≈ 7·10⁻¹³. F1 medio: 0.453 sin balanceo, 0.526 "
                  "pesos de clase, 0.519 SMOTE y 0.513 ADASYN. «Sin balanceo» es peor que las tres (Nemenyi p ≤ 10⁻⁴); "
                  "pesos de clase supera a ADASYN (p = 0.020) y empata con SMOTE (p = 0.67). Naive Bayes casi no cambia.",
                  "Friedman (28 model × method blocks): χ² = 59.8, p ≈ 7·10⁻¹³. Mean F1: 0.453 no balancing, 0.526 "
                  "class weights, 0.519 SMOTE and 0.513 ADASYN. “No balancing” is worse than all three (Nemenyi "
                  "p ≤ 10⁻⁴); class weights beat ADASYN (p = 0.020) and tie with SMOTE (p = 0.67). Naive Bayes barely "
                  "changes."),
        pagina="/modelos", sug=t(["¿Qué técnicas de balanceo usaron?", "Explícame la gráfica de F1 vs ROC-AUC"],
                                 ["Which balancing techniques were used?", "Explain the F1 vs ROC-AUC chart"])))
    add(Intencion(
        "scatter_modelos", t("F1 vs. ROC-AUC", "F1 vs. ROC-AUC"),
        t(["explícame la gráfica de F1 vs ROC-AUC", "balancear mueve el umbral", "dispersión de las 112 combinaciones",
           "por qué los puntos grises están abajo", "qué es la estrella en la dispersión de modelos",
           "balancear mueve el umbral no la capacidad de ordenar"],
          ["explain the F1 vs ROC-AUC chart", "balancing moves the threshold", "scatter of the 112 combinations",
           "why are the grey points at the bottom", "what is the star in the models scatter",
           "balancing moves the threshold not the ranking ability"]),
        t("Cada punto es una de las 112 combinaciones (color = técnica de balanceo; la **estrella** es la mejor). Las "
          "que no balancean (**gris**) quedan abajo: aciertan poco con quienes incumplen. Pero **no** quedan más a la "
          "izquierda: ordenan a los clientes casi igual de bien. Lo que cambia es dónde se pone el corte entre "
          "«paga» e «incumple».",
          "Each point is one of the 112 combinations (color = balancing technique; the **star** is the best). Those "
          "without balancing (**grey**) sit at the bottom: they rarely get defaulters right. But they are **not** "
          "further left: they rank clients almost equally well. What changes is where the cut between “pays” and "
          "“defaults” is placed."),
        tecnico=t("ROC-AUC medio: 0.758 sin balanceo, 0.761 pesos de clase, 0.754 SMOTE y 0.749 ADASYN. Con umbral 0.5 "
                  "el recall pasa de 0.377 a 0.610 y la precisión baja de 0.618 a 0.460: la ganancia de F1 "
                  "(0.456 → 0.523) viene sobre todo del umbral y no de un modelo que discrimine mejor.",
                  "Mean ROC-AUC: 0.758 no balancing, 0.761 class weights, 0.754 SMOTE and 0.749 ADASYN. At a 0.5 "
                  "threshold recall goes from 0.377 to 0.610 and precision drops from 0.618 to 0.460: the F1 gain "
                  "(0.456 → 0.523) comes mostly from the threshold, not from a model that discriminates better."),
        pagina="/modelos", sug=t(["¿Qué es el ROC-AUC?", "¿Qué es el umbral de decisión?"],
                                 ["What is ROC-AUC?", "What is the decision threshold?"])))
    add(Intencion(
        "cm", t("Matriz de confusión del mejor modelo", "Confusion matrix of the best model"),
        t(["explícame la matriz de confusión", "qué es una matriz de confusión", "falsas alarmas", "no detectados",
           "cuántos falsos negativos hay", "cuántos morosos no detecta",
           "falsos positivos y falsos negativos", "cuántos morosos detecta el modelo", "verdaderos positivos"],
          ["explain the confusion matrix", "what is a confusion matrix", "false alarms", "missed defaulters",
           "how many false negatives", "how many defaulters are missed",
           "false positives and false negatives", "how many defaulters does the model detect", "true positives"]),
        t(f"La **matriz de confusión** cruza lo real con lo que predijo {best_lbl} (umbral 0.5) sobre "
          f"{sum(cm.values()):,} clientes:\n\n"
          f"- **Detectados:** {cm['tp']:,} de {pos:,} que incumplieron ({cm['tp'] / pos:.0%}).\n"
          f"- **No detectados** (falsos negativos): {cm['fn']:,}.\n"
          f"- **Falsas alarmas** (falsos positivos): {cm['fp']:,}.\n"
          f"- **Bien clasificados que pagan:** {cm['tn']:,}.\n\n"
          f"De los {flagged:,} que marca como riesgosos, {cm['tp'] / flagged:.0%} sí incumple.",
          f"The **confusion matrix** crosses reality with what {best_lbl} predicted (threshold 0.5) on "
          f"{sum(cm.values()):,} clients:\n\n"
          f"- **Detected:** {cm['tp']:,} of {pos:,} who defaulted ({cm['tp'] / pos:.0%}).\n"
          f"- **Missed** (false negatives): {cm['fn']:,}.\n"
          f"- **False alarms** (false positives): {cm['fp']:,}.\n"
          f"- **Correctly classified payers:** {cm['tn']:,}.\n\n"
          f"Of the {flagged:,} it flags as risky, {cm['tp'] / flagged:.0%} actually default."),
        tecnico=t("Predicciones out-of-fold de los tres modelos de los folds externos (AUC agrupado 0.781). Las "
                  "probabilidades no están calibradas (ECE = 0.196) porque el balanceo infla la clase positiva; una "
                  "recalibración isotónica la baja a 0.017 en un fold. Ajustar el umbral según el costo de cada "
                  "error es el siguiente paso.",
                  "Out-of-fold predictions from the three outer-fold models (pooled AUC 0.781). The probabilities are "
                  "not calibrated (ECE = 0.196) because balancing inflates the positive class; isotonic recalibration "
                  "lowers it to 0.017 on one fold. Tuning the threshold to the cost of each error is the next step."),
        pagina="/modelos", sug=t(["¿Qué es el recall?", "¿Qué es el umbral de decisión?"],
                                 ["What is recall?", "What is the decision threshold?"])))
    add(Intencion(
        "shap", t("SHAP: variables que más pesan", "SHAP: most important variables"),
        t(["qué variables pesan más en el modelo", "qué es SHAP", "importancia de variables", "interpretabilidad",
           "qué variable es más importante para el modelo", "explícame el resumen SHAP", "LIME"],
          ["which variables matter most in the model", "what is SHAP", "feature importance", "interpretability",
           "which variable is most important for the model", "explain the SHAP summary", "LIME"]),
        t("**SHAP** reparte la predicción de un modelo entre las variables para ver cuánto aporta cada una. En el "
          "mejor modelo:\n\n"
          "- **PAY_0 domina:** más meses de atraso en septiembre empujan hacia el default.\n"
          "- Le siguen **PAY_2 y PAY_3**, luego PAY_4 a PAY_6.\n"
          "- **Mayor LIMIT_BAL, menor riesgo.**\n"
          "- **Montos pagados y facturados:** efecto pequeño.\n\n"
          "Coincide con el EDA: el historial de pagos es la señal más fuerte y lo demográfico pesa poco.",
          "**SHAP** splits a model's prediction among the variables to see how much each one contributes. In the "
          "best model:\n\n"
          "- **PAY_0 dominates:** more months late in September push toward default.\n"
          "- **PAY_2 and PAY_3** follow, then PAY_4 to PAY_6.\n"
          "- **Higher LIMIT_BAL, lower risk.**\n"
          "- **Paid and billed amounts:** small effect.\n\n"
          "It matches the EDA: payment history is the strongest signal and demographics matter little."),
        tecnico=t("SHAP del Random Forest sobre 100 clientes de un fold (notebook 06_interpretability). Con variables "
                  "correlacionadas SHAP reparte la importancia entre ellas, así que el orden exacto entre PAY_2…PAY_6 "
                  "es aproximado.",
                  "Random Forest SHAP on 100 clients from one fold (notebook 06_interpretability). With correlated "
                  "variables SHAP splits importance among them, so the exact order among PAY_2…PAY_6 is approximate."),
        pagina="/modelos", sug=t(["¿Qué es PAY_0?", "Explícame «¿Qué empuja su riesgo?»"],
                                 ["What is PAY_0?", "Explain “What drives their risk?”"])))
    add(Intencion(
        "como_leer", t("Qué tan distintos son los modelos", "How different the models are"),
        t(["cómo leer los resultados de los modelos", "están empatados los modelos", "qué es Nemenyi",
           "qué es la prueba de Friedman", "importa el método de optimización", "son comparables los resultados de SVM",
           "diferencia significativa entre modelos"],
          ["how to read the model results", "are the models tied", "what is Nemenyi", "what is the Friedman test",
           "does the optimization method matter", "are the SVM results comparable",
           "significant difference between models"]),
        t("**Qué tan distintos son los modelos:**\n\n"
          "- Los primeros lugares están **prácticamente empatados**: 15 de 112 combinaciones quedan a menos de una "
          "desviación del mejor F1 y Nemenyi no separa ningún par.\n"
          "- Lo que sí importa es **balancear**. El método de optimización casi no cambia el F1 (0.5022 a 0.5032): "
          "conviene elegirlo por su costo.\n"
          "- SVM se corrió en Colab con GPU y no es estrictamente comparable; KNN y Naive Bayes con pesos de clase "
          "usan ajustes propios.\n"
          "- Validación cruzada anidada 3×3: con 3 folds las pruebas tienen poca potencia.",
          "**How different the models are:**\n\n"
          "- The top places are **practically tied**: 15 of 112 combinations are within one deviation of the best F1 "
          "and Nemenyi separates no pair.\n"
          "- What does matter is **balancing**. The optimization method barely changes F1 (0.5022 to 0.5032): it "
          "should be chosen by its cost.\n"
          "- SVM was run on Colab with a GPU and is not strictly comparable; KNN and Naive Bayes with class weights "
          "use project-specific adjustments.\n"
          "- Nested 3×3 cross-validation: with 3 folds the tests have low power."),
        tecnico=t("Friedman + Nemenyi: diferencia crítica 115.4 frente a 107.7 de diferencia máxima de rangos. La "
                  "desviación del F1 usa ddof = 1.",
                  "Friedman + Nemenyi: critical difference 115.4 versus a maximum rank difference of 107.7. The F1 "
                  "deviation uses ddof = 1."),
        pagina="/modelos", sug=t(["¿Qué es la validación cruzada anidada?", "¿Qué métodos de optimización usaron?"],
                                 ["What is nested cross-validation?", "Which optimization methods were used?"])))
    add(Intencion(
        "metricas", t("Métricas: F1, precisión, recall, ROC-AUC, PR-AUC", "Metrics: F1, precision, recall, ROC-AUC, PR-AUC"),
        t(["qué es el F1", "qué es el recall", "qué es la precisión", "qué es el ROC-AUC", "qué es el PR-AUC",
           "qué métricas usaron", "diferencia entre precisión y recall", "qué es AUC", "qué es sensibilidad",
           "por qué usan F1"],
          ["what is F1", "what is the F1 score", "what is recall", "what is precision", "what is ROC-AUC",
           "what is PR-AUC", "which metrics did they use", "difference between precision and recall", "what is AUC",
           "what is sensitivity", "why use F1"]),
        t("Métricas de la clase **default**:\n\n"
          "- **Recall:** de quienes incumplen, qué parte detecta el modelo.\n"
          "- **Precisión:** de quienes marca como riesgosos, qué parte sí incumple.\n"
          "- **F1:** equilibrio entre ambas (media armónica). Es la métrica principal.\n"
          "- **ROC-AUC:** qué tan bien *ordena* a los clientes de más a menos riesgo (0.5 = azar, 1 = perfecto).\n"
          "- **PR-AUC:** como el AUC pero centrado en la clase minoritaria.\n\n"
          "No se usa accuracy porque, con 78 % de clientes que pagan, engaña.",
          "Metrics for the **default** class:\n\n"
          "- **Recall:** of those who default, what share the model detects.\n"
          "- **Precision:** of those it flags as risky, what share actually defaults.\n"
          "- **F1:** balance between both (harmonic mean). It is the main metric.\n"
          "- **ROC-AUC:** how well it *ranks* clients from most to least risky (0.5 = chance, 1 = perfect).\n"
          "- **PR-AUC:** like AUC but focused on the minority class.\n\n"
          "Accuracy is not used because, with 78% of clients paying, it is misleading."),
        pagina="/modelos", sug=t(["¿Cuál es el mejor modelo?", "¿Qué es el desbalance de clases?"],
                                 ["Which is the best model?", "What is class imbalance?"])))
    add(Intencion(
        "balanceo", t("Técnicas de balanceo", "Balancing techniques"),
        t(["qué técnicas de balanceo usaron", "qué es SMOTE", "qué es ADASYN", "qué es class weight",
           "qué son pesos de clase", "class_weight balanced", "sobremuestreo", "cómo balancearon las clases"],
          ["which balancing techniques were used", "what is SMOTE", "what is ADASYN", "what is class weight",
           "what are class weights", "class_weight balanced", "oversampling", "how were the classes balanced"]),
        t("Las 4 opciones de **balanceo** comparadas:\n\n"
          "- **Sin balanceo:** los datos tal cual (línea base).\n"
          "- **Pesos de clase** (class_weight): equivocarse con un cliente que incumple «cuesta» más al entrenar. "
          "Fue la mejor.\n"
          "- **SMOTE:** crea clientes sintéticos de la clase minoritaria interpolando entre vecinos.\n"
          "- **ADASYN:** como SMOTE, pero genera más ejemplos donde la clase es más difícil de aprender.",
          "The 4 **balancing** options compared:\n\n"
          "- **No balancing:** the data as is (baseline).\n"
          "- **Class weights** (class_weight): getting a defaulter wrong “costs” more during training. It was the best.\n"
          "- **SMOTE:** creates synthetic minority-class clients by interpolating between neighbors.\n"
          "- **ADASYN:** like SMOTE, but generates more examples where the class is harder to learn."),
        pagina="/modelos", sug=t(["Explícame el mapa de calor de F1", "¿Qué métodos de optimización usaron?"],
                                 ["Explain the F1 heatmap", "Which optimization methods were used?"])))
    add(Intencion(
        "optimizacion", t("Métodos de optimización", "Optimization methods"),
        t(["qué métodos de optimización usaron", "qué es grid search", "qué es random search", "optimización bayesiana",
           "qué es Optuna", "algoritmo genético", "qué es DEAP", "hiperparámetros", "cómo optimizaron los hiperparámetros"],
          ["which optimization methods were used", "what is grid search", "what is random search",
           "bayesian optimization", "what is Optuna", "genetic algorithm", "what is DEAP", "hyperparameters",
           "how were the hyperparameters tuned"]),
        t("Los **4 métodos de optimización** de hiperparámetros:\n\n"
          "- **Grid search:** prueba todas las combinaciones de una rejilla.\n"
          "- **Random search:** prueba combinaciones al azar.\n"
          "- **Bayesiana (Optuna):** usa los resultados previos para elegir la siguiente prueba.\n"
          "- **Genética (DEAP):** «evoluciona» una población de configuraciones.\n\n"
          "Casi no cambian el F1 (0.5022 a 0.5032 en promedio), así que conviene elegir por costo computacional.",
          "The **4 hyperparameter optimization methods**:\n\n"
          "- **Grid search:** tries every combination in a grid.\n"
          "- **Random search:** tries random combinations.\n"
          "- **Bayesian (Optuna):** uses previous results to choose the next trial.\n"
          "- **Genetic (DEAP):** “evolves” a population of configurations.\n\n"
          "They barely change F1 (0.5022 to 0.5032 on average), so it is best to choose by computational cost."),
        pagina="/modelos", sug=t(["¿Qué es la validación cruzada anidada?", "¿Qué técnicas de balanceo usaron?"],
                                 ["What is nested cross-validation?", "Which balancing techniques were used?"])))
    add(Intencion(
        "validacion", t("Validación cruzada anidada", "Nested cross-validation"),
        t(["qué es la validación cruzada anidada", "validación cruzada", "folds", "cómo validaron los modelos",
           "qué son los folds externos e internos", "cross validation", "nested cv"],
          ["what is nested cross-validation", "cross-validation", "folds", "how were the models validated",
           "what are the outer and inner folds", "cross validation", "nested cv"]),
        t("En la **validación cruzada anidada** hay dos niveles: los **3 folds internos** eligen los hiperparámetros y "
          "los **3 folds externos** miden el rendimiento con datos que el ajuste nunca vio. Así el F1 reportado no "
          "está inflado por la búsqueda de hiperparámetros. El «±» del F1 es la desviación entre los folds externos.",
          "In **nested cross-validation** there are two levels: the **3 inner folds** choose the hyperparameters and "
          "the **3 outer folds** measure performance on data the tuning never saw. That way the reported F1 is not "
          "inflated by the hyperparameter search. The “±” of F1 is the deviation across the outer folds."),
        pagina="/modelos", sug=t(["¿Están empatados los modelos?", "¿Qué es el F1?"],
                                 ["Are the models tied?", "What is F1?"])))
    for idx, r in A.BEST_BY_MODEL.iterrows():
        m = r["model"]
        lbl = A.minfo(m, "label")
        rank = int(idx) + 1
        alias = {"random_forest": (["bosque aleatorio", "random forest"], ["random forest"]),
                 "xgboost": (["xgboost", "xgb", "gradient boosting"], ["xgboost", "xgb", "gradient boosting"]),
                 "svm": (["svm", "máquina de vectores de soporte", "support vector machine"],
                         ["svm", "support vector machine"]),
                 "knn": (["knn", "k vecinos", "vecinos más cercanos"], ["knn", "k nearest neighbors", "nearest neighbors"]),
                 "decision_tree": (["árbol de decisión", "decision tree", "árbol"], ["decision tree", "tree"]),
                 "logistic_regression": (["regresión logística", "línea base", "logistic regression"],
                                         ["logistic regression", "baseline"]),
                 "naive_bayes": (["naive bayes", "bayes ingenuo"], ["naive bayes"])}[m]
        al = t(*alias)
        if EN:
            ej = [q for a in al for q in (f"what is {a}", f"how did {a} do", f"{a} results", f"explain {a}")]
            ej += [f"what rank did {al[0]} get", f"F1 of {al[0]}"]
        else:
            ej = [q for a in al for q in (f"qué es {a}", f"cómo le fue a {a}", f"resultados de {a}", f"explícame {a}")]
            ej += [f"en qué puesto quedó {al[0]}", f"F1 de {al[0]}"]
        tech_m, meth_m = A.tech_lbl(r["technique"]).lower(), A.method_lbl(r["method"]).lower()
        add(Intencion(
            f"m_{m}", lbl, ej,
            t(f"**{lbl}** · {A.minfo(m, 'family')} · puesto **#{rank}** de 7.\n\n{A.minfo(m, 'desc')}\n\n"
              f"Mejor combinación: {tech_m} + {meth_m} → **F1 {r['f1_mean']:.3f}** ± {r['f1_std']:.3f}, recall "
              f"{r['recall_mean']:.3f}, precisión {r['precision_mean']:.3f}, ROC-AUC {r['roc_auc_mean']:.3f}.\n\n"
              f"{A.minfo(m, 'note')}",
              f"**{lbl}** · {A.minfo(m, 'family')} · rank **#{rank}** of 7.\n\n{A.minfo(m, 'desc')}\n\n"
              f"Best combination: {tech_m} + {meth_m} → **F1 {r['f1_mean']:.3f}** ± {r['f1_std']:.3f}, recall "
              f"{r['recall_mean']:.3f}, precision {r['precision_mean']:.3f}, ROC-AUC {r['roc_auc_mean']:.3f}.\n\n"
              f"{A.minfo(m, 'note')}"),
            pagina="/modelos", sug=t(["¿Cuál es el mejor modelo?", "Explícame el carrusel de modelos"],
                                     ["Which is the best model?", "Explain the model carousel"]),
            mood="proud" if rank == 1 else "explaining"))

    # =====================================================================
    # Predecir
    # =====================================================================
    add(Intencion(
        "p_predecir", t("Predecir", "Predict"),
        t(["explícame la página Predecir", "cómo funciona Predecir", "cómo predigo el riesgo de un cliente",
           "qué hace la sección predecir", "simulador de riesgo", "cómo evalúo un cliente",
           "calcular el riesgo de un cliente", "predecir si un cliente nuevo va a pagar", "probar el modelo con un cliente"],
          ["explain the Predict page", "how does Predict work", "how do I predict a client's risk",
           "what does the predict section do", "risk simulator", "how do I evaluate a client",
           "calculate a client's risk", "predict whether a new client will pay", "test the model with a client"]),
        t("En **Predecir** llenas los datos de un cliente y el modelo serializado calcula su riesgo **en vivo**:\n\n"
          f"1. **Flujo:** datos → transformaciones → {n_trees} árboles opinan → puntaje y decisión.\n"
          "2. **Formulario:** perfil (cupo, edad, sexo, educación, estado civil), estado de pago por mes y montos.\n"
          "3. **Resultado:** una tarjeta de crédito con el puntaje y el veredicto, señales y votos de los árboles.\n"
          "4. **Historial del cliente**, **¿Qué empuja su riesgo?** y **¿Qué pasaría si…?**\n"
          "5. **Cómo se serializó el modelo** (joblib).",
          "In **Predict** you fill in a client's data and the serialized model computes their risk **live**:\n\n"
          f"1. **Flow:** data → transformations → {n_trees} trees give their opinion → score and decision.\n"
          "2. **Form:** profile (limit, age, sex, education, marital status), repayment status by month and amounts.\n"
          "3. **Result:** a credit card with the score and the verdict, signals and the trees' votes.\n"
          "4. **Client history**, **What drives their risk?** and **What if…?**\n"
          "5. **How the model was serialized** (joblib)."),
        pagina="/predecir",
        sug=t(["¿Cómo lleno el formulario?", "¿Cómo leo el puntaje de riesgo?", "Explícame «¿Qué pasaría si…?»"],
              ["How do I fill in the form?", "How do I read the risk score?", "Explain “What if…?”"])))
    add(Intencion(
        "formulario", t("Formulario del cliente", "Client form"),
        t(["cómo lleno el formulario", "qué son los perfiles de ejemplo", "cliente típico", "atrasos recientes",
           "al día cupo alto", "deslizadores de estado de pago", "qué pongo en facturado y pagado",
           "qué significa Otro en sexo", "botones prueba un ejemplo"],
          ["how do I fill in the form", "what are the example profiles", "typical client", "recent delays",
           "up to date high limit", "repayment status sliders", "what do I put in billed and paid",
           "what does Other mean in sex", "try an example buttons"]),
        t("El **formulario** tiene tres bloques:\n\n"
          "- **Perfil:** cupo y edad con deslizadores; sexo, educación y estado civil con tarjetas.\n"
          "- **Estado de pago por mes** (abril → septiembre): −2 sin consumo, −1 pagó todo, 0 pago mínimo, "
          "1–8 meses de atraso.\n"
          "- **Montos por mes:** lo facturado y lo pagado en NT$.\n\n"
          "Los botones **Prueba un ejemplo** cargan tres perfiles: *cliente típico* (mediana y moda), *al día, cupo "
          "alto* y *atrasos recientes*. Con sexo «Otro» el modelo promedia las predicciones como hombre y mujer, "
          "porque el dataset solo registra esas dos.",
          "The **form** has three blocks:\n\n"
          "- **Profile:** limit and age with sliders; sex, education and marital status with cards.\n"
          "- **Repayment status by month** (April → September): −2 no use, −1 paid in full, 0 minimum payment, "
          "1–8 months late.\n"
          "- **Amounts by month:** what was billed and what was paid in NT$.\n\n"
          "The **Try an example** buttons load three profiles: *typical client* (median and mode), *up to date, high "
          "limit* and *recent delays*. With sex “Other” the model averages the predictions as male and female, "
          "because the dataset only records those two."),
        pagina="/predecir", sug=t(["¿Cómo leo el puntaje de riesgo?", "¿Qué son los votos de los árboles?"],
                                  ["How do I read the risk score?", "What are the trees' votes?"])))
    thr = meta.get("umbral", 0.5)
    add(Intencion(
        "gauge", t("Puntaje de riesgo y veredicto", "Risk score and verdict"),
        t(["cómo leo el puntaje de riesgo", "qué significa el porcentaje de la tarjeta", "qué es el umbral de decisión",
           "riesgo alto o bajo", "por qué 50 por ciento", "es una probabilidad el puntaje", "qué significa el veredicto",
           "el puntaje de la tarjeta", "qué son las señales del resultado", "a partir de qué puntaje es riesgo alto",
           "cuándo se considera riesgo alto", "por qué la tarjeta está rota", "qué significa la grieta de la tarjeta",
           "por qué se parte la tarjeta", "la tarjeta de crédito del resultado"],
          ["how do I read the risk score", "what does the card percentage mean", "what is the decision threshold",
           "high or low risk", "why 50 percent", "is the score a probability", "what does the verdict mean",
           "the score on the card", "what are the result signals", "from what score is it high risk",
           "why is the card broken", "what does the crack in the card mean", "why does the card split",
           "the credit card in the result", "what score counts as high risk", "high risk threshold",
           "cracked credit card", "the card is broken in the result", "split card in predict",
           "when is a client considered high risk", "which score means high risk"]),
        t(f"La **tarjeta de crédito** del resultado muestra el puntaje de 0 a 100 %. Desde el **umbral de {thr:.0%}** el "
          "veredicto es «riesgo alto: probable incumplimiento» (dorado); por debajo, «riesgo bajo» (azul).\n\n"
          "Además se rompe según el riesgo: está intacta con riesgo bajo; **desde 30 %** aparece una fractura por la "
          "mitad que crece hasta cruzarla, y **desde el umbral (50 %)** la tarjeta se abre por ahí, más cuanto más "
          "alto es el puntaje.\n\nDebajo aparecen "
          "**señales** en lenguaje simple: atrasos, qué parte de lo facturado pagó y cómo es su cupo frente a los demás.\n\n"
          + (f"Con ese umbral el modelo detecta {prueba.get('recall', 0):.0%} de quienes incumplen y acierta en "
             f"{prueba.get('precision', 0):.0%} de los que marca (datos de prueba). " if prueba else "")
          + "No es una probabilidad calibrada: sirve para **ordenar y clasificar** clientes.",
          f"The result's **credit card** shows the score from 0 to 100%. From the **{thr:.0%} threshold** the verdict "
          "is “high risk: likely default” (gold); below it, “low risk” (blue).\n\n"
          "It also breaks according to the risk: it is intact with low risk; **from 30%** a crack appears in the "
          "middle and grows until it crosses the card, and **from the threshold (50%)** the card splits open there, "
          "more the higher the score.\n\nBelow it there are **signals** in plain language: delays, what share of the "
          "bill was paid and how their limit compares with others.\n\n"
          + (f"With that threshold the model detects {prueba.get('recall', 0):.0%} of defaulters and is right about "
             f"{prueba.get('precision', 0):.0%} of those it flags (test data). " if prueba else "")
          + "It is not a calibrated probability: it is useful to **rank and classify** clients."),
        tecnico=t("El Random Forest se entrenó con class_weight='balanced', lo que desplaza las probabilidades hacia la "
                  f"clase positiva: sobrestima el riesgo frente a la tasa real ({pct(rate)}). Para usar el puntaje "
                  "como probabilidad habría que calibrarlo (p. ej., regresión isotónica).",
                  "The Random Forest was trained with class_weight='balanced', which shifts probabilities toward the "
                  f"positive class: it overestimates risk compared with the real rate ({pct(rate)}). To use the score "
                  "as a probability it would have to be calibrated (e.g. isotonic regression)."),
        pagina="/predecir", sug=t(["¿Qué son los votos de los árboles?", "Explícame «¿Qué empuja su riesgo?»"],
                                  ["What are the trees' votes?", "Explain “What drives their risk?”"]),
        mood="alert"))
    add(Intencion(
        "votos", t("Votos de los árboles", "Trees' votes"),
        t(["qué son los votos de los árboles", "cuadritos del bosque", "árboles votan incumple", "waffle de árboles",
           "por qué el puntaje no coincide con los votos", "cuántos árboles tiene el modelo"],
          ["what are the trees' votes", "forest squares", "trees vote default", "trees waffle",
           "why doesn't the score match the votes", "how many trees does the model have"]),
        t(f"El modelo es un bosque de **{n_trees} árboles**. Cada uno opina si el cliente incumplirá; los "
          "**cuadros** muestran qué porcentaje del bosque vota «incumple» (cada cuadro = 1 %). El puntaje promedia las "
          "*probabilidades* de todos los árboles, no solo sus votos, por eso puede diferir un poco.",
          f"The model is a forest of **{n_trees} trees**. Each one gives its opinion on whether the client will "
          "default; the **squares** show what percentage of the forest votes “default” (each square = 1%). The score "
          "averages the *probabilities* of all trees, not just their votes, so it may differ slightly."),
        pagina="/predecir", sug=t(["¿Cómo leo el puntaje de riesgo?", "¿Qué es Random Forest?"],
                                  ["How do I read the risk score?", "What is random forest?"])))
    add(Intencion(
        "historial", t("Historial del cliente", "Client history"),
        t(["explícame el historial del cliente", "facturado vs pagado", "barras azules y doradas del historial",
           "línea de estado de pago", "gráfica del historial"],
          ["explain the client history", "billed vs paid", "blue and gold bars in the history",
           "repayment status line", "history chart"]),
        t("En **Historial del cliente** las barras comparan lo **facturado** (azul) con lo **pagado** (dorado) cada "
          "mes, y la línea dorada es el **estado de pago**. Si la línea sube por encima de 0 hay atraso; si las barras "
          "doradas son mucho más bajas que las azules, el cliente paga poco de su deuda.",
          "In **Client history** the bars compare what was **billed** (blue) with what was **paid** (gold) each month, "
          "and the gold line is the **repayment status**. If the line rises above 0 there is a delay; if the gold "
          "bars are much lower than the blue ones, the client pays little of their debt."),
        tecnico=t("El modelo no usa las seis facturas por separado: las resume en nivel medio (log con signo), tendencia "
                  "mensual y número de meses con saldo a favor. Los PAY_x sí entran uno por uno.",
                  "The model does not use the six bills separately: it summarizes them as average level (signed log), "
                  "monthly trend and number of months with a credit balance. The PAY_x do enter one by one."),
        pagina="/predecir", sug=t(["Explícame «¿Qué empuja su riesgo?»", "¿Qué es BILL_AMT?"],
                                  ["Explain “What drives their risk?”", "What is BILL_AMT?"])))
    add(Intencion(
        "drivers", t("¿Qué empuja su riesgo?", "What drives their risk?"),
        t(["explícame «¿Qué empuja su riesgo?»", "qué empuja su riesgo", "aporte de cada grupo de variables",
           "puntos de riesgo que suma o resta", "por qué este cliente es riesgoso", "qué aumenta el riesgo del cliente",
           "por qué el puntaje de este cliente es alto", "qué explica el riesgo de este cliente", "qué lo hace riesgoso"],
          ["explain “What drives their risk?”", "what drives their risk", "contribution of each variable group",
           "risk points added or removed", "why is this client risky", "what increases the client's risk",
           "why is this client's score high", "what explains this client's risk", "what makes them risky"]),
        t("Cada barra responde: «si en este grupo de datos el cliente fuera como un **cliente típico**, ¿cuánto "
          "cambiaría su puntaje?». Los grupos son historial de pagos, montos pagados, facturación, cupo y perfil "
          "demográfico. Barras **doradas** suben el riesgo; **azules** lo bajan.",
          "Each bar answers: “if, in this group of data, the client were like a **typical client**, how much would "
          "their score change?”. The groups are payment history, amounts paid, billing, limit and demographic "
          "profile. **Gold** bars raise the risk; **blue** ones lower it."),
        tecnico=t("Explicación local por sustitución: se reemplaza cada grupo por la mediana/moda del cliente típico y se "
                  "mide la diferencia en el puntaje. Es aproximada: no suma exactamente el total porque los grupos "
                  "interactúan dentro del bosque (a diferencia de SHAP).",
                  "Local explanation by substitution: each group is replaced by the typical client's median/mode and "
                  "the difference in the score is measured. It is approximate: it does not add up exactly to the total "
                  "because the groups interact inside the forest (unlike SHAP)."),
        pagina="/predecir", sug=t(["Explícame «¿Qué pasaría si…?»", "¿Qué es SHAP?"],
                                  ["Explain “What if…?”", "What is SHAP?"])))
    add(Intencion(
        "whatif", t("¿Qué pasaría si…?", "What if…?"),
        t(["explícame «¿Qué pasaría si…?»", "qué pasaría si", "simulador qué pasaría si", "cambiar una sola variable",
           "curva what if", "qué es la estrella este cliente", "qué pasa si se atrasa un mes más"],
          ["explain “What if…?”", "what if", "what if simulator", "change a single variable", "what if curve",
           "what is the this client star", "what happens if they are one more month late"]),
        t("**¿Qué pasaría si…?** muestra el puntaje que tendría *este mismo* cliente si solo cambiara una variable: "
          "atraso en septiembre, cupo, pago de septiembre o edad. La **estrella** es su situación actual y la franja "
          "superior marca el riesgo alto. Por ejemplo, con «Atraso en septiembre» ves cuánto sube el riesgo con "
          "cada mes de atraso.",
          "**What if…?** shows the score *this same* client would have if only one variable changed: September "
          "delay, limit, September payment or age. The **star** is their current situation and the upper band marks "
          "high risk. For example, with “September delay” you see how much the risk rises with each month of delay."),
        tecnico=t("Es una curva ICE (dependencia individual): se fija el resto y se recorre una variable. En un bosque la "
                  "curva tiene escalones porque cada árbol corta en umbrales; describe al modelo, no implica causalidad.",
                  "It is an ICE curve (individual conditional expectation): the rest is fixed and one variable is "
                  "varied. In a forest the curve has steps because each tree splits at thresholds; it describes the "
                  "model and does not imply causality."),
        pagina="/predecir", sug=t(["Explícame «¿Qué empuja su riesgo?»", "¿Cómo leo el puntaje de riesgo?"],
                                  ["Explain “What drives their risk?”", "How do I read the risk score?"])))
    hp = meta.get("hiperparametros", {})
    add(Intencion(
        "serializacion", t("Cómo se serializó el modelo", "How the model was serialized"),
        t(["cómo se serializó el modelo", "qué es serializar", "qué es joblib", "qué es el archivo pkl",
           "modelo_credito.pkl", "cómo se guardó el modelo", "cómo se entrenó el modelo de predecir",
           "hiperparámetros del modelo serializado", "métricas de prueba del modelo"],
          ["how was the model serialized", "what is serializing", "what is joblib", "what is the pkl file",
           "modelo_credito.pkl", "how was the model saved", "how was the predict model trained",
           "hyperparameters of the serialized model", "test metrics of the model"]),
        t("**Serializar** es guardar un modelo ya entrenado en un archivo para usarlo sin reentrenar:\n\n"
          "1. **Entrenar** (`modelo/entrenar.py`) → 2. **Guardar** con `joblib.dump` en `modelo_credito.pkl` → "
          "3. **Cargar** con `joblib.load` al arrancar el tablero → 4. **Predecir** con `predict_proba` en cada cambio.\n\n"
          f"El .pkl guarda el pipeline completo: transformaciones del proyecto + one-hot + Random Forest "
          f"({meta.get('balanceo', 'pesos de clase')})."
          + (f" En prueba (20 %): F1 {prueba['f1']:.3f}, recall {prueba['recall']:.3f}, precisión "
             f"{prueba['precision']:.3f}, ROC-AUC {prueba['roc_auc']:.3f}." if prueba else ""),
          "**Serializing** means saving an already trained model to a file to use it without retraining:\n\n"
          "1. **Train** (`modelo/entrenar.py`) → 2. **Save** with `joblib.dump` to `modelo_credito.pkl` → "
          "3. **Load** with `joblib.load` when the dashboard starts → 4. **Predict** with `predict_proba` on each change.\n\n"
          f"The .pkl stores the whole pipeline: project transformations + one-hot + Random Forest "
          f"({meta.get('balanceo', 'class weights')})."
          + (f" On the test set (20%): F1 {prueba['f1']:.3f}, recall {prueba['recall']:.3f}, precision "
             f"{prueba['precision']:.3f}, ROC-AUC {prueba['roc_auc']:.3f}." if prueba else "")),
        tecnico=t(f"Búsqueda: {meta.get('busqueda', '—')}. Hiperparámetros: "
                  + ", ".join(f"{k} = {v}" for k, v in hp.items())
                  + f". Entrenado con {meta.get('n_entrenamiento', 0):,} clientes. Debe cargarse con la misma versión "
                    f"de scikit-learn ({meta.get('versiones', {}).get('scikit-learn', '—')}).",
                  f"Search: {meta.get('busqueda', '—')}. Hyperparameters: "
                  + ", ".join(f"{k} = {v}" for k, v in hp.items())
                  + f". Trained on {meta.get('n_entrenamiento', 0):,} clients. It must be loaded with the same "
                    f"scikit-learn version ({meta.get('versiones', {}).get('scikit-learn', '—')})."),
        pagina="/predecir", sug=t(["¿Qué son los votos de los árboles?", "¿Qué es Random Forest?"],
                                  ["What are the trees' votes?", "What is random forest?"])))

    # =====================================================================
    # Enlaces y equipo
    # =====================================================================
    titles = ", ".join(A.L(lk["title"]) for lk in A.LINKS)
    add(Intencion(
        "p_enlaces", t("Enlaces", "Links"),
        t(["explícame la página de enlaces", "dónde está el repositorio", "link del github", "dónde está el notebook",
           "jupyter book", "libro del proyecto", "dónde veo el código", "cómo reproduzco el análisis", "enlaces"],
          ["explain the links page", "where is the repository", "github link", "where is the notebook",
           "jupyter book", "project book", "where can I see the code", "how do I reproduce the analysis", "links"]),
        t("**Enlaces** reúne:\n\n"
          "- **Sobre el proyecto:** resumen del Jupyter Book.\n"
          f"- **Tarjetas de enlaces:** {titles}.\n"
          "- **Pipeline completo:** los siete notebooks en orden.\n"
          "- **Reproducir el análisis:** clonar, instalar con `pip install -r requirements.txt` y correr "
          "`python app.py`.",
          "**Links** gathers:\n\n"
          "- **About the project:** summary of the Jupyter Book.\n"
          f"- **Link cards:** {titles}.\n"
          "- **Full pipeline:** the seven notebooks in order.\n"
          "- **Reproduce the analysis:** clone, install with `pip install -r requirements.txt` and run "
          "`python app.py`."),
        pagina="/enlaces", sug=t(["¿Qué notebooks tiene el pipeline?", "¿Quiénes hicieron el proyecto?"],
                                 ["Which notebooks are in the pipeline?", "Who made the project?"])))
    add(Intencion(
        "notebooks", t("Pipeline de notebooks", "Notebook pipeline"),
        t(["qué notebooks tiene el pipeline", "pipeline completo", "lista de notebooks", "qué hace cada notebook",
           "notebook 00", "notebook de interpretabilidad"],
          ["which notebooks are in the pipeline", "full pipeline", "list of notebooks", "what does each notebook do",
           "notebook 00", "interpretability notebook"]),
        t("**Pipeline completo** (siete notebooks del libro):\n\n", "**Full pipeline** (the book's seven notebooks):\n\n") +
        "\n".join(f"- **{num} · {A.L(ti)}:** {A.L(d)}" for num, ti, _f, d in A.NOTEBOOKS),
        pagina="/enlaces", sug=t(["Explícame la página de enlaces", "¿Qué es SHAP?"],
                                 ["Explain the links page", "What is SHAP?"])))
    add(Intencion(
        "p_equipo", t("Equipo", "Team"),
        t(["quiénes hicieron el proyecto", "autores", "quién hizo este dashboard", "equipo", "quiénes son las autoras",
           "contacto de las autoras", "correo de las autoras", "de qué universidad son", "explícame la página de equipo"],
          ["who made the project", "authors", "who made this dashboard", "team", "who are the authors",
           "contact the authors", "authors' email", "which university are they from", "explain the team page"]),
        t("Este tablero lo hicieron:\n\n", "This dashboard was made by:\n\n") +
        "\n".join(f"- **{m['name']}** — {A.L(m['role'])} · {m['email']}" for m in A.TEAM) +
        t(f"\n\n{A.L(A.INSTITUTION)}. En la página **Equipo** cada tarjeta se voltea para ver la bio, GitHub, LinkedIn y "
          "un botón que copia el correo.",
          f"\n\n{A.L(A.INSTITUTION)}. On the **Team** page each card flips to show the bio, GitHub, LinkedIn and a "
          "button that copies the email."),
        pagina="/equipo", sug=t(["¿De qué trata el proyecto?", "Explícame la página de enlaces"],
                                ["What is the project about?", "Explain the links page"]), mood="happy"))

    # =====================================================================
    # Páginas, sugerencias por página
    # =====================================================================
    paginas = {p: A.L(lbl) for p, lbl, _ic in A.NAV}
    paginas["/"] = t("Inicio (portada)", "Home (cover)")
    intencion_de_pagina = {"/": "p_inicio", "/introduccion": "p_intro", "/problema": "p_problema", "/marco": "p_marco",
                           "/univariado": "p_uni", "/multivariado": "p_multi", "/modelos": "p_modelos",
                           "/predecir": "p_predecir", "/enlaces": "p_enlaces", "/equipo": "p_equipo"}
    sug_de_pagina = t({
        "/": ["¿De qué trata el proyecto?", "¿Cómo uso el tablero?", "¿Cuál es el hallazgo principal?"],
        "/introduccion": ["Explícame el vistazo rápido", "¿Cómo se limpiaron los datos?", "¿De dónde salen los datos?"],
        "/problema": ["¿Cuáles son las hipótesis?", "¿Cuál es la pregunta de investigación?", "¿Qué es el límite expuesto?"],
        "/marco": ["¿Qué es la pérdida esperada?", "¿Qué es Spearman?", "¿Qué es la V de Cramér?",
                   "Muéstrame el diccionario de variables"],
        "/univariado": ["Explícame la variable objetivo", "Explícame el explorador univariado", "¿Qué es PAY_0?",
                        "Explícame las distribuciones cuantitativas"],
        "/multivariado": ["Explícame la matriz de correlación", "Explícame las tasas por educación, estado civil y sexo",
                          "Explícame el boxplot del límite de crédito", "Explícame la gráfica de edad y atrasos"],
        "/modelos": ["¿Cuál es el mejor modelo?", "Explícame el carrusel de modelos", "Explícame la matriz de confusión",
                     "Explícame la gráfica de F1 vs ROC-AUC"],
        "/predecir": ["¿Cómo lleno el formulario?", "¿Cómo leo el puntaje de riesgo?", "¿Qué son los votos de los árboles?",
                      "Explícame «¿Qué pasaría si…?»"],
        "/enlaces": ["¿Qué notebooks tiene el pipeline?", "¿Cómo reproduzco el análisis?", "¿Quiénes hicieron el proyecto?"],
        "/equipo": ["¿Quiénes hicieron el proyecto?", "¿De qué trata el proyecto?"],
    }, {
        "/": ["What is the project about?", "How do I use the dashboard?", "What is the main finding?"],
        "/introduccion": ["Explain the quick look", "How was the data cleaned?", "Where does the data come from?"],
        "/problema": ["What are the hypotheses?", "What is the research question?", "What is the exposed limit?"],
        "/marco": ["What is expected loss?", "What is Spearman?", "What is Cramér's V?", "Show me the variable dictionary"],
        "/univariado": ["Explain the target variable", "Explain the univariate explorer", "What is PAY_0?",
                        "Explain the quantitative distributions"],
        "/multivariado": ["Explain the correlation matrix", "Explain the rates by education, marital status and sex",
                          "Explain the credit limit boxplot", "Explain the age and delays chart"],
        "/modelos": ["Which is the best model?", "Explain the model carousel", "Explain the confusion matrix",
                     "Explain the F1 vs ROC-AUC chart"],
        "/predecir": ["How do I fill in the form?", "How do I read the risk score?", "What are the trees' votes?",
                      "Explain “What if…?”"],
        "/enlaces": ["Which notebooks are in the pipeline?", "How do I reproduce the analysis?", "Who made the project?"],
        "/equipo": ["Who made the project?", "What is the project about?"],
    })
    return I, paginas, intencion_de_pagina, sug_de_pagina
