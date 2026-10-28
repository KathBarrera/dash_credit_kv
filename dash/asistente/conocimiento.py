# -*- coding: utf-8 -*-
"""Base de conocimiento de Kyo: qué sabe del tablero y con qué preguntas se entrena.

`construir_conocimiento(A)` recibe el módulo de la aplicación (app.py ya cargado) y arma las
intenciones con las cifras reales del tablero: las interpretaciones de cada gráfica salen de las
mismas funciones que usa la página (interp_corr, interp_rates, ...), así el bot nunca contradice
lo que se ve en pantalla.

Para enseñarle algo nuevo: agrega un Intencion(...) a la lista con varias preguntas de ejemplo
(cuantas más formas distintas de preguntar, mejor) y su respuesta. Se reentrena al arrancar.
"""
import numpy as np

from .motor import Intencion


def construir_conocimiento(A):
    """Devuelve (intenciones, paginas, intencion_de_pagina, sug_de_pagina)."""
    df, T = A.df, A.TARGET
    n, n_def, rate = len(df), int(df[T].sum()), A.GLOBAL_RATE
    DI = A.DATA_INFO
    nt = A.nt
    pct = lambda x: f"{x:.1%}"
    B, BL = A.BEST, A.BASELINE
    best_lbl = A.MODEL_INFO[B["model"]]["label"]
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

    def interp(fn, *a):
        b, t = fn(*a)
        return b, t

    I = []
    add = I.append

    # =====================================================================
    # Conversación general
    # =====================================================================
    add(Intencion(
        "saludo", "Saludo",
        ["hola", "buenas", "buenos días", "buenas tardes", "hey kyo", "hola kyo", "qué tal", "holi",
         "hola cómo estás", "buenas noches"],
        "¡Hola! Soy **Kyo**. Puedo explicarte cualquier página, gráfica, variable o modelo de este tablero. "
        "Si quieres, empiezo por la página en la que estás.",
        sug=["Explícame esta página", "¿Qué puedo preguntarte?", "¿Cuál es el hallazgo principal?"], mood="happy"))
    add(Intencion(
        "quien_eres", "Quién es Kyo",
        ["quién eres", "qué eres", "hola quién eres", "y tú quién eres", "cómo funcionas", "cómo te entrenaron", "eres una inteligencia artificial",
         "cómo aprendiste", "con qué te entrenaron", "qué modelo usas para responder", "eres un bot",
         "cómo sabes las respuestas", "de dónde sacas la información"],
        "Soy **Kyo**, un bot entrenado con el contenido de este tablero:\n\n"
        "- Cada página, gráfica, variable y modelo es una *intención* con varias preguntas de ejemplo.\n"
        "- Las preguntas se convierten en vectores **TF-IDF** (palabras y fragmentos de letras, así tolero "
        "errores de escritura) y con ellos se entrena una **regresión logística** de scikit-learn.\n"
        "- Cuando preguntas, calculo la intención más probable. Si no me parezco a nada de lo aprendido, "
        "te lo digo en vez de inventar.\n"
        "- Las cifras salen de las mismas funciones que dibujan el tablero, así que coinciden con lo que ves.\n\n"
        "No me conecto a servicios externos: todo corre dentro de la app.",
        sug=["¿Qué puedo preguntarte?", "Explícame esta página"], mood="proud"))
    add(Intencion(
        "ayuda", "Qué puedo preguntar",
        ["qué puedo preguntarte", "ayuda", "en qué me ayudas", "qué sabes hacer", "qué sabes",
         "dame ideas de preguntas", "qué temas conoces", "help", "no sé qué preguntar", "opciones"],
        "Puedo explicarte:\n\n"
        "- **Cualquier página**: escribe «explícame esta página» o el nombre de la sección.\n"
        "- **Cada gráfica**: la matriz de correlación, las tasas por perfil, el boxplot del límite, la edad, "
        "el cruce de variables, el carrusel de modelos, la matriz de confusión, el puntaje de riesgo…\n"
        "- **Variables**: PAY_0, LIMIT_BAL, BILL_AMT, PAY_AMT, EDUCATION…\n"
        "- **Conceptos**: Spearman, V de Cramér, F1, recall, SMOTE, SHAP, validación cruzada…\n\n"
        "Después de cada respuesta puedes pedir **la explicación técnica**.",
        sug=["Explícame esta página", "¿Qué es PAY_0?", "¿Cuál es el mejor modelo?", "¿Qué es el F1?"],
        mood="happy"))
    add(Intencion(
        "gracias", "Agradecimiento",
        ["gracias", "muchas gracias", "perfecto gracias", "genial", "listo", "ok gracias", "chévere", "excelente",
         "súper", "entendido", "vale gracias", "adiós", "chao", "hasta luego"],
        "¡Con gusto! Cuando quieras, tócame de nuevo: estoy en la esquina inferior derecha de la pantalla.",
        sug=["Explícame esta página", "¿Cuál es el hallazgo principal?"], mood="happy"))
    add(Intencion(
        "esta_pagina", "Esta página",
        ["explícame esta página", "qué hay en esta página", "qué estoy viendo", "de qué trata esta sección",
         "explica esto", "qué es esto", "qué muestra esta página", "resúmeme esta página", "dónde estoy",
         "qué significa lo que estoy viendo", "explícame lo que hay aquí", "qué hay aquí",
         "explica la página actual", "explícame esta parte", "qué contiene esta sección",
         "no entiendo esta página", "ayúdame a entender esta sección", "no entiendo lo que veo"],
        "", mood="explaining"))
    add(Intencion(
        "mas_tecnico", "Versión técnica",
        ["dame la explicación técnica", "explicación técnica", "más técnico", "explícalo técnicamente",
         "dame más detalle", "con estadísticos", "versión técnica", "quiero más detalle técnico",
         "profundiza", "detalles técnicos", "explícalo con más rigor", "interpretación técnica"],
        "", mood="explaining"))
    add(Intencion(
        "navegacion", "Cómo usar el tablero",
        ["cómo uso el tablero", "cómo navego", "cómo cambio a modo oscuro", "cómo oculto el menú",
         "para qué sirve el botón de sol y luna", "cómo voy a la siguiente página", "cómo me muevo por el dash",
         "dónde está el menú", "modo oscuro", "botones anterior y siguiente", "cómo se usa el dashboard",
         "cambiar el tema", "tema oscuro", "modo claro"],
        "Así te mueves por el tablero:\n\n"
        "- **Menú lateral** (izquierda): las diez secciones en orden. El botón de panel de la barra superior "
        "lo oculta o lo muestra.\n"
        "- **Sol y luna**: cambia entre modo claro y oscuro (se recuerda en tu navegador).\n"
        "- **Anterior / Siguiente**: al final de cada página te llevan por el tablero en orden.\n"
        "- **Interpretaciones**: bajo cada gráfica, el botón **Ver interpretación** despliega la explicación "
        "básica y la técnica.\n"
        "- **Yo**: estoy en la esquina inferior derecha; tócame para abrir este panel y la **X** para cerrarlo.",
        sug=["Explícame esta página", "¿Qué puedo preguntarte?"], mood="happy"))
    add(Intencion(
        "resumen", "Resumen del proyecto",
        ["de qué trata el proyecto", "resumen del tablero", "resume todo el dashboard", "cuál es el hallazgo principal",
         "conclusiones", "qué encontraron", "cuáles son las conclusiones del análisis", "en pocas palabras qué dice el dash",
         "qué aprendieron", "hallazgos principales", "qué es lo más importante del análisis"],
        f"El tablero estudia **{n:,} clientes** de tarjeta de crédito de un banco de Taiwán (abril–septiembre "
        f"2005) para entender quién deja de pagar el mes siguiente ({pct(rate)} lo hizo). Lo más importante:\n\n"
        f"1. **El historial de pagos domina.** {findings[0][1]}\n"
        f"2. **Menor cupo, más riesgo.** {findings[2][1]}\n"
        f"3. **Lo demográfico pesa poco.** {findings[3][1]}\n"
        f"4. **Las facturas son redundantes.** {findings[1][1]}\n"
        f"5. **Modelos:** el mejor es {best_lbl} con {A.TECH_LBL[B['technique']].lower()} "
        f"(F1 {B['f1_mean']:.3f} frente a {BL:.3f} de la línea base); balancear las clases es lo que más ayuda.",
        sug=["¿Qué es PAY_0?", "¿Cuál es el mejor modelo?", "Explícame la matriz de correlación"], mood="proud"))

    # =====================================================================
    # Portada
    # =====================================================================
    add(Intencion(
        "p_inicio", "Inicio (portada)",
        ["portada", "página de inicio", "inicio", "qué es la tarjeta de la portada", "por qué hay una tarjeta de crédito",
         "la tarjeta que se voltea", "qué dice la tarjeta", "pantalla principal", "home"],
        "La **portada** presenta el proyecto con una tarjeta de crédito interactiva:\n\n"
        "- **Frente:** los titulares (las autoras) y el periodo de los datos (abril–septiembre 2005).\n"
        f"- **Reverso** (haz clic para voltearla): {n:,} clientes, {pct(rate)} de default y el periodo.\n"
        "- **Iniciar recorrido** te lleva a la Introducción; desde ahí el menú lateral muestra todas las secciones.",
        pagina="/", sug=["¿De qué trata el proyecto?", "Explícame la introducción", "¿Cómo uso el tablero?"],
        mood="happy"))

    # =====================================================================
    # Introducción
    # =====================================================================
    add(Intencion(
        "p_intro", "Introducción",
        ["explícame la introducción", "qué hay en la introducción", "página de introducción", "contexto del proyecto",
         "para qué es este tablero", "cuál es el contexto"],
        "La **Introducción** da el contexto:\n\n"
        "- **Vistazo rápido:** una gráfica que muestra que el atraso de septiembre anticipa el incumplimiento.\n"
        f"- **KPIs:** {n:,} clientes, 24 variables (23 predictoras + 1 objetivo), {pct(rate)} de default y el "
        "periodo abril–septiembre 2005.\n"
        "- **Fuente y alcance:** datos de Yeh & Lien (2009) en UCI; montos en NT$; el análisis es descriptivo.\n"
        "- **Preparación de los datos:** qué limpieza se hizo.\n"
        "- **Cómo recorrer el tablero:** qué hay en cada sección.",
        pagina="/introduccion", sug=["Explícame el vistazo rápido", "¿Cómo se limpiaron los datos?",
                                     "¿De dónde salen los datos?"]))
    b_home = (f"Cada barra es la tasa de default para un valor de **PAY_0** (estado de pago de septiembre). "
              f"Entre quienes tenían 2 o más meses de atraso, **{r_late:.0%}** incumplió el mes siguiente; entre "
              f"quienes iban al día o pagaban el mínimo, **{r_ok:.0%}**. La línea punteada es la tasa global "
              f"({pct(rate)}). Solo se muestran valores con al menos 100 clientes.")
    add(Intencion(
        "intro_vistazo", "Vistazo rápido (PAY_0)",
        ["explícame el vistazo rápido", "gráfica del vistazo rápido", "la gráfica de barras de la introducción",
         "el atraso de septiembre anticipa el incumplimiento", "tasa de default según PAY_0",
         "qué muestra la primera gráfica", "barras por estado de pago de septiembre"],
        b_home,
        tecnico=("Se agrupa por PAY_0 y se calcula la media de la variable objetivo en cada grupo (grupos con n ≥ 100). "
                 "La tasa salta de forma no lineal al pasar de 0 (pago mínimo) a 1–2 meses de atraso, por eso PAY_0 "
                 "conviene tratarla como ordinal o categórica (dummies) y no como una variable lineal. Es la variable "
                 "con mayor ρ de Spearman con el default y la primera en importancia SHAP del mejor modelo."),
        pagina="/introduccion", sug=["¿Qué es PAY_0?", "¿Qué variables pesan más en el modelo?"]))
    add(Intencion(
        "intro_limpieza", "Preparación de los datos",
        ["cómo se limpiaron los datos", "qué limpieza hicieron", "preparación de los datos", "duplicados",
         "qué pasó con los códigos no documentados", "saldos negativos", "por qué no hay PAY_1",
         "calidad de los datos", "transformaciones aplicadas a los datos", "cuántos duplicados había",
         "borraron filas", "quitaron registros duplicados", "limpieza del dataset", "filas eliminadas"],
        f"La preparación de los datos (Introducción):\n\n"
        f"- Se eliminaron **{DI['duplicados']}** filas duplicadas exactas (de {DI['filas_originales']:,} a {n:,}).\n"
        f"- **{DI['edu_reagrupadas']}** registros con EDUCATION = 0, 5 o 6 (códigos sin documentar) pasaron a «Otros».\n"
        f"- **{DI['mar_reagrupadas']}** registros con MARRIAGE = 0 pasaron a «Otros».\n"
        f"- Se conservaron **{DI['bill_neg_clientes']:,}** clientes con saldo facturado negativo: es saldo a favor "
        "y es válido.\n"
        "- El estado de pago de septiembre se llama PAY_0: el dataset no trae PAY_1.",
        pagina="/introduccion", sug=["¿De dónde salen los datos?", "¿Qué es EDUCATION?", "¿Qué es BILL_AMT?"]))
    add(Intencion(
        "dataset", "Fuente de los datos",
        ["de dónde salen los datos", "qué dataset usaron", "fuente de los datos", "UCI", "Yeh y Lien",
         "cuántos clientes hay", "de qué banco son los datos", "de qué año son los datos", "en qué moneda están",
         "cuántas variables tiene el dataset", "default of credit card clients", "qué periodo cubren los datos"],
        f"Los datos son **Default of Credit Card Clients** (UCI Machine Learning Repository), publicados por "
        f"Yeh & Lien (2009). Son {DI['filas_originales']:,} clientes de un banco de **Taiwán** observados de "
        f"**abril a septiembre de 2005** ({n:,} tras quitar duplicados), con 24 variables: cupo, datos "
        "demográficos, estado de pago de seis meses, montos facturados y montos pagados, y si incumplió en "
        "octubre (variable objetivo). Los montos están en **dólares taiwaneses (NT$)**.",
        pagina="/introduccion", sug=["¿Qué variables tiene?", "¿Qué es la variable objetivo?",
                                     "¿Cómo se limpiaron los datos?"]))

    # =====================================================================
    # Problema y objetivos
    # =====================================================================
    add(Intencion(
        "p_problema", "Problema y Objetivos",
        ["explícame problema y objetivos", "cuál es el problema", "planteamiento del problema", "página del problema",
         "por qué es importante este análisis", "qué problema resuelven", "justificación del proyecto"],
        "**Problema y Objetivos** explica por qué importa el análisis:\n\n"
        "- **Planteamiento:** el banco presta sin saber quién pagará; si se equivoca pierde capital o, si "
        f"restringe de más, pierde ingresos. Aquí {pct(rate)} ({n_def:,} clientes) no pagó.\n"
        f"- **KPIs:** clientes en default, límite expuesto (NT${exposure / 1e6:,.0f} M) y saldo facturado de "
        f"septiembre de quienes incumplen (NT${bill_def / 1e6:,.0f} M).\n"
        "- **Pregunta de investigación**, **justificación**, **alcance y limitaciones**.\n"
        "- **Cinco hipótesis** (H1–H5) y los **objetivos** general y específicos.",
        tecnico=("Los errores no son simétricos: un falso negativo (no detectar a quien incumplirá) suele costar más "
                 "que un falso positivo. Por eso más adelante se privilegian F1 y recall de la clase default sobre "
                 "la exactitud (accuracy)."),
        pagina="/problema", sug=["¿Cuáles son las hipótesis?", "¿Cuál es la pregunta de investigación?",
                                 "¿Cuáles son los objetivos?"]))
    add(Intencion(
        "pregunta", "Pregunta de investigación",
        ["cuál es la pregunta de investigación", "qué pregunta responde el análisis", "preguntas específicas",
         "qué se quiere responder"],
        "**Pregunta de investigación:** ¿qué características del cliente, de su línea de crédito y de su historial "
        "reciente de pagos se asocian con el incumplimiento del mes siguiente, y con qué intensidad?\n\n"
        "Preguntas específicas: cómo se distribuyen las variables y qué problemas de calidad tienen, qué tan "
        "desbalanceada está la variable objetivo, qué variables separan mejor a quienes incumplen y si hay "
        "redundancia entre predictoras.",
        pagina="/problema", sug=["¿Cuáles son las hipótesis?", "¿Cuáles son los objetivos?"]))
    add(Intencion(
        "hipotesis", "Hipótesis",
        ["cuáles son las hipótesis", "hipótesis exploratorias", "H1", "qué hipótesis plantearon",
         "se cumplieron las hipótesis", "tabla de hipótesis", "H2 H3 H4 H5"],
        "Las **cinco hipótesis** y lo que muestra el tablero:\n\n"
        "- **H1** El historial de pagos (PAY_0…PAY_6) es el factor más asociado al default → **se apoya**: PAY_0 "
        "tiene la mayor correlación y domina en SHAP.\n"
        f"- **H2** Menor límite de crédito, más default → **se apoya**: mediana {nt(lim1)} (default) vs. "
        f"{nt(lim0)}.\n"
        "- **H3** Lo demográfico se asocia, pero con efecto pequeño → **se apoya**: V de Cramér < 0.1.\n"
        f"- **H4** Las BILL_AMT están muy correlacionadas → **se apoya**: ρ entre {bill_rho.min():.2f} y "
        f"{bill_rho.max():.2f}.\n"
        f"- **H5** La clase default es minoritaria → **se apoya**: {pct(rate)} frente a {pct(1 - rate)}.",
        pagina="/problema", sug=["Explícame la matriz de correlación", "¿Qué es la V de Cramér?",
                                 "¿Qué es el desbalance de clases?"]))
    add(Intencion(
        "objetivos", "Objetivos",
        ["cuáles son los objetivos", "objetivo general", "objetivos específicos", "qué buscan con el análisis",
         "metas del análisis"],
        "**Objetivo general:** analizar los factores que se asocian con el incumplimiento de pago de los clientes "
        "de tarjeta de crédito mediante un EDA univariado y multivariado.\n\n"
        "**Específicos:** documentar la calidad y la limpieza de los datos (Introducción); caracterizar cada "
        "variable y cuantificar el desbalance (Univariado); comparar clientes con y sin default y detectar "
        "multicolinealidad (Multivariado); y definir lineamientos de preprocesamiento para el modelado "
        "(Hallazgos clave).",
        pagina="/problema", sug=["¿Cuáles son las hipótesis?", "¿Cuáles son los hallazgos clave?"]))
    add(Intencion(
        "limitaciones", "Alcance y limitaciones",
        ["limitaciones", "alcance del análisis", "qué limitaciones tiene", "se puede generalizar",
         "correlación implica causalidad", "es causal el análisis", "causalidad", "los hallazgos son causa y efecto",
         "sirve para otros países", "por qué no se puede generalizar"],
        "**Alcance y limitaciones:**\n\n"
        "- Datos de un solo banco de Taiwán y un periodo corto (abril–septiembre 2005): no se generalizan sin cautela.\n"
        "- El análisis es **asociativo**: una correlación no implica causalidad.\n"
        "- El EDA no construye modelos; los modelos se entrenaron en el repositorio del proyecto y se resumen en "
        "la sección Modelos.\n"
        "- Los códigos −2 y 0 de PAY_x no están documentados con precisión; se conservan sin recodificar.",
        pagina="/problema", sug=["¿Qué es PAY_0?", "¿De dónde salen los datos?"]))
    add(Intencion(
        "kpis_problema", "Límite expuesto y saldo facturado",
        ["qué es el límite expuesto", "saldo facturado de septiembre", "KPIs del problema",
         "cuánto dinero está en riesgo", "cuánto suman los cupos de quienes incumplen"],
        f"En Problema y Objetivos hay tres cifras de negocio:\n\n"
        f"- **Clientes en default:** {n_def:,} ({pct(rate)}).\n"
        f"- **Límite expuesto:** NT${exposure / 1e6:,.0f} millones, la suma de los cupos (LIMIT_BAL) de quienes "
        "incumplen.\n"
        f"- **Saldo facturado (Sep):** NT${bill_def / 1e6:,.0f} millones, la suma de BILL_AMT1 positivo de quienes "
        "incumplen.\n\nDan una idea del tamaño del problema para el banco.",
        pagina="/problema", sug=["¿Qué es LIMIT_BAL?", "¿Qué es la pérdida esperada?"]))

    # =====================================================================
    # Marco teórico
    # =====================================================================
    add(Intencion(
        "p_marco", "Marco Teórico",
        ["explícame el marco teórico", "qué hay en el marco teórico", "página del marco teórico",
         "qué conceptos usan", "fundamentos teóricos", "teoría del proyecto"],
        "El **Marco Teórico** reúne los conceptos que sustentan el análisis, en ocho tarjetas:\n\n"
        "1. Riesgo de crédito y default (EL = PD × LGD × EAD)\n2. Scoring crediticio\n3. EDA (Tukey)\n"
        "4. Estadística descriptiva y atípicos\n5. Desbalance de clases\n6. Spearman y multicolinealidad (VIF)\n"
        "7. χ² y V de Cramér\n8. Mann-Whitney, Kruskal-Wallis y t de Welch\n\n"
        "Además: antecedentes (Yeh & Lien, 2009), referencias y el **diccionario de variables**.",
        pagina="/marco", sug=["¿Qué es la pérdida esperada?", "¿Qué es Spearman?", "Muéstrame el diccionario de variables"]))
    add(Intencion(
        "perdida_esperada", "Riesgo de crédito y pérdida esperada",
        ["qué es la pérdida esperada", "EL = PD x LGD x EAD", "qué es PD", "qué es LGD", "qué es EAD",
         "qué es el riesgo de crédito", "qué es default", "qué significa default", "Basilea"],
        "El **riesgo de crédito** es la posibilidad de perder dinero porque un deudor no paga. En Basilea II la "
        "pérdida esperada es **EL = PD × LGD × EAD**:\n\n"
        "- **PD:** probabilidad de incumplimiento (lo que estudian estos datos).\n"
        "- **LGD:** porcentaje que se pierde si hay incumplimiento.\n"
        "- **EAD:** monto expuesto en ese momento.\n\n"
        "Aquí **default** es la variable binaria que indica si el cliente no pagó el mes siguiente.",
        pagina="/marco", sug=["¿Qué es el scoring crediticio?", "¿Qué es la variable objetivo?"]))
    add(Intencion(
        "scoring", "Scoring crediticio",
        ["qué es el scoring crediticio", "qué es un modelo de scoring", "para qué sirve el scoring",
         "puntaje crediticio", "score crediticio", "para qué sirve un score", "qué es un score de riesgo"],
        "Un **modelo de scoring** estima la probabilidad de incumplimiento (PD) con datos del cliente: "
        "comportamiento de pago, límite, deuda y perfil. Sirve para aprobar o rechazar solicitudes, fijar cupos y "
        "priorizar la cobranza. Antes de modelar, el EDA revela la calidad de los datos, las variables más "
        "informativas y los problemas (colinealidad, desbalance, atípicos). La sección **Predecir** es un ejemplo "
        "de scoring con el mejor modelo.",
        pagina="/marco", sug=["Explícame la página Predecir", "¿Qué es el EDA?"]))
    add(Intencion(
        "eda_concepto", "Qué es el EDA",
        ["qué es el EDA", "qué es análisis exploratorio de datos", "qué significa EDA", "Tukey",
         "diferencia entre univariado y multivariado", "qué es univariado", "qué es multivariado"],
        "El **análisis exploratorio de datos (EDA)**, propuesto por John W. Tukey (1977), explora los datos con "
        "resúmenes y gráficos antes de ajustar modelos, para descubrir patrones, anomalías y supuestos.\n\n"
        "- **Univariado:** una variable a la vez (frecuencias, histograma, boxplot) → página EDA Univariado.\n"
        "- **Multivariado:** relaciones entre variables (correlaciones, cruces, comparaciones por grupo) → "
        "página EDA Multivariado.",
        pagina="/marco", sug=["Explícame el EDA univariado", "Explícame el EDA multivariado"]))
    add(Intencion(
        "atipicos", "Asimetría, atípicos y winsorización",
        ["qué es un valor atípico", "qué son los outliers", "regla de Tukey", "qué es la asimetría",
         "qué es la curtosis", "qué es winsorizar", "qué es la winsorización", "qué es el IQR", "transformación logarítmica",
         "qué es skewness", "qué es el recorte P99", "qué es el percentil 99"],
        "- **Asimetría (skewness):** hacia dónde se alarga la cola; los montos de dinero suelen tener una cola "
        "larga a la derecha.\n- **Curtosis:** qué tan pesadas son las colas.\n"
        "- **Atípico de Tukey:** x < Q1 − 1.5·IQR o x > Q3 + 1.5·IQR, con IQR = Q3 − Q1.\n"
        "- **Winsorizar:** recortar los extremos a percentiles (p. ej. P1–P99) sin eliminar clientes.\n"
        "- **Recorte P99 en las gráficas:** solo cambia la *vista*, para que unos pocos montos enormes no aplasten "
        "el gráfico; los datos no se modifican.\n"
        "- **Log con signo:** suaviza colas largas cuando hay ceros o negativos.",
        pagina="/marco", sug=["Explícame el explorador univariado", "¿Qué es BILL_AMT?"]))
    add(Intencion(
        "desbalance", "Desbalance de clases",
        ["qué es el desbalance de clases", "por qué las clases están desbalanceadas", "clases desbalanceadas",
         "por qué no usar accuracy", "qué tan desbalanceada está la variable objetivo", "clase minoritaria"],
        f"Hay **desbalance de clases** cuando una clase es mucho menos frecuente. Aquí solo {pct(rate)} incumple "
        f"(razón ≈ {(1 - rate) / rate:.1f}:1), así que un modelo que diga «todos pagan» acertaría {pct(1 - rate)} "
        "de las veces sin servir para nada. Por eso:\n\n"
        "- se ponderan las clases (**class_weight**) o se sobremuestrea la minoritaria (**SMOTE**, **ADASYN**);\n"
        "- se ajusta el umbral de decisión;\n"
        "- se evalúa con **F1, recall y AUC** en lugar de accuracy.",
        pagina="/marco", sug=["¿Qué técnicas de balanceo usaron?", "¿Qué es el F1?", "Explícame la variable objetivo"]))
    add(Intencion(
        "spearman", "Correlación de Spearman y VIF",
        ["qué es Spearman", "qué es la correlación de Spearman", "por qué Spearman y no Pearson", "qué es rho",
         "qué es el VIF", "qué es la multicolinealidad", "factor de inflación de la varianza", "qué es ρ"],
        "**Spearman** (ρ) es la correlación de Pearson calculada sobre los *rangos* de los datos. Mide asociación "
        "monótona, no exige linealidad ni normalidad y resiste valores extremos. Se eligió sobre Pearson porque los "
        "montos son muy asimétricos, PAY_x es ordinal y la variable objetivo es binaria.\n\n"
        "**Multicolinealidad:** predictoras casi redundantes que inflan la varianza de los coeficientes. Se mide "
        "con el **VIF = 1 / (1 − R²)**; un VIF > 10 (o > 5) es alerta. En este dataset las BILL_AMT superan 20.",
        pagina="/marco", sug=["Explícame la matriz de correlación", "¿Qué es BILL_AMT?"]))
    add(Intencion(
        "cramer", "χ² y V de Cramér",
        ["qué es la V de Cramér", "qué es chi cuadrado", "prueba chi cuadrado", "qué es χ²", "tamaño del efecto categórico",
         "asociación entre variables categóricas", "chi2"],
        "La prueba **χ² de independencia** contrasta si dos variables categóricas están asociadas. Su tamaño de "
        "efecto es la **V de Cramér** = √(χ² / (n · min(r−1, c−1))), de 0 a 1: V < 0.1 es pequeño y V ≈ 0.3 "
        "moderado. En el tablero, educación, estado civil y sexo dan V < 0.1: hay diferencias, pero pequeñas.",
        pagina="/marco", sug=["Explícame las tasas por educación, estado civil y sexo", "¿Qué es el p-value?"]))
    add(Intencion(
        "pruebas_grupos", "Mann-Whitney, Kruskal-Wallis y t de Welch",
        ["qué es Mann-Whitney", "qué es Kruskal-Wallis", "qué es la t de Welch", "pruebas no paramétricas",
         "comparación de grupos", "qué es el p-value", "qué significa p<0.001", "qué es significancia estadística",
         "tamaño del efecto"],
        "- **Mann-Whitney U:** compara dos grupos sin suponer normalidad (usa rangos).\n"
        "- **Kruskal-Wallis H:** lo mismo para tres o más grupos.\n"
        "- **t de Welch:** compara medias con varianzas distintas.\n\n"
        f"Ojo con el **p-value**: con n ≈ {n:,} casi cualquier diferencia sale «significativa» (p < 0.05). Por eso el "
        "tablero reporta también el **tamaño del efecto** y la relevancia práctica.",
        pagina="/marco", sug=["Explícame el boxplot del límite de crédito", "¿Qué es la V de Cramér?"]))
    add(Intencion(
        "antecedentes", "Antecedentes y referencias",
        ["antecedentes", "referencias", "bibliografía", "qué hicieron Yeh y Lien", "estudios previos",
         "sorting smoothing method"],
        "**Antecedentes:** Yeh y Lien (2009) compararon seis técnicas (regresión logística, análisis discriminante, "
        "k vecinos, Naive Bayes, redes neuronales y árboles) con estos mismos datos y propusieron el *Sorting "
        "Smoothing Method* para estimar la probabilidad real de incumplimiento. La sección **Modelos** retoma esa "
        "comparación con 7 clasificadores, 4 técnicas de balanceo y 4 métodos de optimización.\n\n"
        "Las **referencias** incluyen Basilea II, Chawla et al. (SMOTE), Cramér, Kruskal-Wallis, Mann-Whitney, "
        "Spearman, Tukey y Yeh & Lien.",
        pagina="/marco", sug=["Explícame la página de modelos", "¿Qué es SMOTE?"]))
    add(Intencion(
        "diccionario", "Diccionario de variables",
        ["muéstrame el diccionario de variables", "qué variables tiene", "lista de variables", "diccionario de datos",
         "qué significa cada variable", "qué columnas hay", "variables del dataset"],
        "**Diccionario de variables** (Marco Teórico):\n\n"
        "- **LIMIT_BAL:** cupo de crédito en NT$.\n- **SEX:** 1 hombre, 2 mujer.\n"
        "- **EDUCATION:** 1 posgrado, 2 universidad, 3 secundaria, 4 otros.\n"
        "- **MARRIAGE:** 1 casado, 2 soltero, 3 otros.\n- **AGE:** edad en años.\n"
        "- **PAY_0, PAY_2…PAY_6:** estado de pago de septiembre a abril (−2/−1/0 sin atraso; 1…8 meses de atraso).\n"
        "- **BILL_AMT1–6:** monto facturado de septiembre (1) a abril (6).\n"
        "- **PAY_AMT1–6:** monto pagado de septiembre (1) a abril (6).\n"
        "- **default_payment_next_month:** 1 si incumple en octubre de 2005.",
        pagina="/marco", sug=["¿Qué es PAY_0?", "¿Qué es LIMIT_BAL?", "¿Qué es la variable objetivo?"]))

    # =====================================================================
    # Variables
    # =====================================================================
    b, t = interp(A.interp_uni, "LIMIT_BAL")
    add(Intencion(
        "v_limit", "LIMIT_BAL (cupo de crédito)",
        ["qué es LIMIT_BAL", "limit_bal", "límite de crédito", "qué es el cupo", "cuánto cupo tienen los clientes",
         "distribución del límite de crédito"],
        f"**LIMIT_BAL** es el cupo de crédito (individual + familiar) en NT$. {b}",
        tecnico=t, pagina="/univariado",
        sug=["Explícame el boxplot del límite de crédito", "¿Qué es PAY_0?"]))
    b, t = interp(A.interp_uni, "AGE")
    add(Intencion(
        "v_age", "AGE (edad)",
        ["qué es AGE", "edad de los clientes", "cuántos años tienen los clientes", "distribución de la edad",
         "edad promedio"],
        f"**AGE** es la edad en años. {b}",
        tecnico=t, pagina="/univariado",
        sug=["Explícame la gráfica de edad y atrasos", "¿Influye la edad en el default?"]))
    add(Intencion(
        "v_sex", "SEX (sexo)",
        ["qué es SEX", "variable sexo", "hombres y mujeres", "género", "incumplen más los hombres o las mujeres",
         "diferencia por sexo"],
        f"**SEX** es el sexo registrado: 1 = hombre, 2 = mujer (el dataset solo trae esas dos categorías). "
        f"{A.interp_uni('SEX')[0]} En la tasa de default: {A.interp_rates()[0].split('. Por')[0]}.",
        tecnico=A.interp_uni("SEX")[1], pagina="/univariado",
        sug=["Explícame las tasas por educación, estado civil y sexo", "¿Qué es la V de Cramér?"]))
    add(Intencion(
        "v_edu", "EDUCATION (educación)",
        ["qué es EDUCATION", "nivel educativo", "educación de los clientes", "variable educación",
         "influye la educación", "categoría otros en educación"],
        f"**EDUCATION**: 1 = posgrado, 2 = universidad, 3 = secundaria, 4 = otros (los códigos 0, 5 y 6 sin "
        f"documentar se agruparon en «Otros»). {A.interp_uni('EDUCATION')[0]}",
        tecnico=A.interp_uni("EDUCATION")[1], pagina="/univariado",
        sug=["Explícame las tasas por educación, estado civil y sexo", "¿Cómo se limpiaron los datos?"]))
    add(Intencion(
        "v_mar", "MARRIAGE (estado civil)",
        ["qué es MARRIAGE", "estado civil", "casados y solteros", "variable estado civil"],
        f"**MARRIAGE**: 1 = casado, 2 = soltero, 3 = otros (el código 0 pasó a «Otros»). "
        f"{A.interp_uni('MARRIAGE')[0]}",
        tecnico=A.interp_uni("MARRIAGE")[1], pagina="/univariado",
        sug=["Explícame las tasas por educación, estado civil y sexo"]))
    b, t = interp(A.interp_uni, "PAY_0")
    add(Intencion(
        "v_pay", "PAY_0 … PAY_6 (estado de pago)",
        ["qué es PAY_0", "pay_0", "qué significa PAY", "estado de pago", "qué significa -2 -1 0 en PAY",
         "historial de pagos", "PAY_2", "PAY_6", "meses de atraso", "qué es el atraso", "por qué no existe PAY_1",
         "qué significa pago mínimo en PAY"],
        "**PAY_0, PAY_2 … PAY_6** son el estado de pago mensual: PAY_0 es septiembre y PAY_6 abril.\n\n"
        "- **−2:** sin consumo · **−1:** pagó todo · **0:** pago mínimo (crédito rotativo)\n"
        "- **1 a 8:** meses de atraso\n\n"
        f"{b} Es **la variable más importante** del análisis: {findings[0][1]}",
        tecnico=t, pagina="/univariado",
        sug=["Explícame el vistazo rápido", "¿Qué variables pesan más en el modelo?", "¿Qué es BILL_AMT?"]))
    b, t = interp(A.interp_quant, "BILL_AMT")
    add(Intencion(
        "v_bill", "BILL_AMT1–6 (facturación)",
        ["qué es BILL_AMT", "bill_amt", "monto facturado", "facturas mensuales", "qué es la facturación",
         "por qué hay facturas negativas", "saldo a favor", "BILL_AMT1"],
        f"**BILL_AMT1–6** es el monto facturado en el estado de cuenta, de septiembre (1) a abril (6), en NT$. {b}",
        tecnico=t, pagina="/univariado",
        sug=["¿Qué es PAY_AMT?", "¿Qué es la multicolinealidad?", "Explícame la matriz de correlación"]))
    b, t = interp(A.interp_quant, "PAY_AMT")
    add(Intencion(
        "v_payamt", "PAY_AMT1–6 (montos pagados)",
        ["qué es PAY_AMT", "pay_amt", "montos pagados", "cuánto pagan los clientes", "pagos mensuales",
         "diferencia entre PAY y PAY_AMT", "PAY_AMT1"],
        f"**PAY_AMT1–6** es lo que el cliente pagó, de septiembre (1) a abril (6), en NT$. No confundir con "
        f"PAY_x, que es el *estado* de pago. {b}",
        tecnico=t, pagina="/univariado", sug=["¿Qué es BILL_AMT?", "¿Qué es PAY_0?"]))
    b, t = interp(A.interp_target)
    add(Intencion(
        "v_target", "Variable objetivo (default)",
        ["qué es la variable objetivo", "default_payment_next_month", "explícame la variable objetivo",
         "cuántos clientes incumplen", "tasa de default", "qué porcentaje no paga", "gráfica default vs no default",
         "qué es target", "cuál es la tasa global de default"],
        f"La **variable objetivo** (default_payment_next_month) vale 1 si el cliente no pagó en octubre de 2005. {b}",
        tecnico=t, pagina="/univariado",
        sug=["¿Qué es el desbalance de clases?", "¿Qué técnicas de balanceo usaron?"], mood="alert"))

    # =====================================================================
    # EDA univariado
    # =====================================================================
    add(Intencion(
        "p_uni", "EDA Univariado",
        ["explícame el EDA univariado", "qué hay en el EDA univariado", "página univariada", "análisis univariado",
         "qué muestra el univariado"],
        "El **EDA Univariado** mira cada variable por separado:\n\n"
        f"- **KPIs:** {n:,} registros, tasa de default {pct(rate)}, límite promedio {nt(df['LIMIT_BAL'].mean())} "
        f"y edad promedio {df['AGE'].mean():.1f} años.\n"
        "- **Variable objetivo:** barras con cuántos pagan y cuántos no (desbalance).\n"
        "- **Explorador univariado:** eliges una variable y ves su histograma + boxplot o sus barras.\n"
        "- **Distribuciones cuantitativas:** LIMIT_BAL, AGE y los seis meses de BILL_AMT y PAY_AMT en "
        "histograma, boxplot o densidad.",
        pagina="/univariado",
        sug=["Explícame la variable objetivo", "Explícame el explorador univariado",
             "Explícame las distribuciones cuantitativas"]))
    add(Intencion(
        "uni_explorador", "Explorador univariado",
        ["explícame el explorador univariado", "cómo uso el explorador univariado", "histograma con boxplot",
         "qué significa la línea de la mediana", "qué es recortar cola superior", "el selector de variable",
         "para qué sirve el checkbox de P99"],
        "En el **Explorador univariado** eliges cualquier variable:\n\n"
        "- **Numéricas:** histograma arriba y boxplot abajo; la línea dorada punteada es la **mediana** y en el "
        "boxplot la línea punteada es la media.\n"
        "- **Categóricas** (SEX, EDUCATION, PAY_x…): barras con el porcentaje de cada categoría.\n"
        "- **Recortar cola superior (P99):** oculta el 1 % de valores más altos *solo en la vista*, para que se "
        "vea la forma de la distribución.\n\n"
        "En **Ver interpretación**, la explicación se actualiza sola con la variable que elijas.",
        tecnico=("La interpretación técnica reporta n, media, mediana, σ, IQR, asimetría, curtosis y % de atípicos de "
                 "Tukey. Si |asimetría| > 2 sugiere transformación logarítmica con signo. Para PAY_x informa la moda y "
                 "el % con atraso ≥ 1 mes, y recomienda tratarla como ordinal/categórica."),
        pagina="/univariado", sug=["¿Qué es un valor atípico?", "¿Qué es LIMIT_BAL?", "¿Qué es PAY_0?"]))
    b, t = interp(A.interp_quant, "BILL_AMT")
    add(Intencion(
        "uni_cuant", "Distribuciones de variables cuantitativas",
        ["explícame las distribuciones cuantitativas", "histograma boxplot densidad", "qué es la densidad",
         "qué es un boxplot", "qué es un histograma", "comparar los seis meses de BILL_AMT",
         "familia de variables", "gráfica de densidad"],
        "La tarjeta **Distribuciones de variables cuantitativas** compara LIMIT_BAL, AGE y las familias BILL_AMT y "
        "PAY_AMT (un color por mes). Puedes verla como:\n\n"
        "- **Histograma:** cuántos clientes caen en cada rango.\n"
        "- **Boxplot:** la caja va del 25 % al 75 % de los datos, la línea es la mediana y los bigotes los "
        "valores típicos.\n- **Densidad:** una curva suavizada de la forma de la distribución.\n\n"
        f"La vista se limita al rango P1–P99. Por ejemplo, para BILL_AMT: {b}",
        tecnico=t, pagina="/univariado", sug=["¿Qué es PAY_AMT?", "¿Qué es un valor atípico?"]))

    # =====================================================================
    # EDA multivariado
    # =====================================================================
    add(Intencion(
        "p_multi", "EDA Multivariado",
        ["explícame el EDA multivariado", "qué hay en el multivariado", "página multivariada", "análisis multivariado",
         "qué muestra el multivariado"],
        "El **EDA Multivariado** estudia relaciones entre variables y con el default:\n\n"
        "1. **Matriz de correlación de Spearman**\n2. **Incumplimiento por educación, estado civil y sexo**\n"
        "3. **Límite de crédito según default** (boxplots)\n4. **Edad y patrones de atraso** (tres vistas)\n"
        "5. **Módulo interactivo de cruce de variables**\n6. **Matriz de dispersión**\n"
        "7. **Hallazgos multivariados clave**",
        pagina="/multivariado",
        sug=["Explícame la matriz de correlación", "Explícame las tasas por educación, estado civil y sexo",
             "¿Cuáles son los hallazgos clave?"]))
    b, t = interp(A.interp_corr)
    add(Intencion(
        "corr", "Matriz de correlación de Spearman",
        ["explícame la matriz de correlación", "mapa de calor de correlación", "qué significan los colores de la matriz",
         "correlaciones entre variables", "heatmap de correlación", "qué variable se relaciona más con el default",
         "bloque dorado de la matriz", "matriz de Spearman"],
        f"Cada celda es la correlación de Spearman entre dos variables: **dorado** = relación directa, **azul** = "
        f"inversa, crema = casi nada. {b}",
        tecnico=t, pagina="/multivariado", sug=["¿Qué es Spearman?", "¿Qué es la multicolinealidad?", "¿Qué es PAY_0?"]))
    b, t = interp(A.interp_rates)
    add(Intencion(
        "rates", "Default por educación, estado civil y sexo",
        ["explícame las tasas por educación, estado civil y sexo", "tasa de default por perfil demográfico",
         "barras doradas y azules", "incumplimiento por educación", "default por estado civil",
         "quién incumple más", "perfil demográfico", "influye el sexo en el default"],
        f"Cada barra es la tasa de default de un grupo; la línea punteada es la tasa global ({pct(rate)}). Las "
        f"barras **doradas** están por encima del promedio y las **azules** por debajo. {b}",
        tecnico=t, pagina="/multivariado", sug=["¿Qué es la V de Cramér?", "¿Qué es EDUCATION?"]))
    b, t = interp(A.interp_limit)
    add(Intencion(
        "limit_box", "Límite de crédito según default",
        ["explícame el boxplot del límite de crédito", "límite de crédito según default", "LIMIT_BAL por default",
         "tienen menos cupo los que incumplen", "escala logarítmica del boxplot", "boxplot de LIMIT_BAL",
         "cómo leo el boxplot", "cupo de quienes no pagan frente a quienes pagan", "límite de los morosos vs los cumplidos",
         "los que incumplen tienen un límite menor", "mediana del límite por default"],
        f"Son dos cajas: **azul** = clientes que pagaron, **dorada** = los que incumplieron. La línea dentro de "
        f"la caja es la mediana. {b} Puedes cambiar a escala **logarítmica** para ver mejor los valores bajos.",
        tecnico=t, pagina="/multivariado", sug=["¿Qué es Mann-Whitney?", "¿Qué es LIMIT_BAL?"]))
    bl, tl = interp(A.interp_age, "lines")
    bh, th = interp(A.interp_age, "heat")
    br, tr = interp(A.interp_age, "rate")
    add(Intencion(
        "age", "Edad y patrones de atraso",
        ["explícame la gráfica de edad y atrasos", "influye la edad en el default", "edad y patrones de atraso",
         "atraso promedio por mes y grupo de edad", "porcentaje con atraso por edad", "tasa de default por edad",
         "los jóvenes incumplen más", "mapa de calor de edad"],
        "La tarjeta **Edad y patrones de atraso** tiene tres vistas:\n\n"
        f"- **Atraso promedio por mes:** {bl}\n"
        f"- **% con atraso ≥ 1 mes:** {bh}\n"
        f"- **Tasa de default por edad:** {br}",
        tecnico=f"{tl} {th} {tr}", pagina="/multivariado", sug=["¿Qué es AGE?", "¿Qué es PAY_0?"]))
    add(Intencion(
        "cross", "Módulo interactivo de cruce de variables",
        ["explícame el cruce de variables", "módulo interactivo", "cómo uso el cruce de variables",
         "variable X variable Y color", "qué gráfico sale en el cruce", "ejes ajustados al percentil 99",
         "cruzar dos variables"],
        "En el **cruce de variables** eliges **X**, **Y** y, si quieres, una tercera como **color/grupo**. El "
        "tipo de gráfico se ajusta solo:\n\n"
        "- numérica × numérica → **dispersión** con línea de tendencia;\n"
        "- categórica × numérica → **boxplots** por grupo;\n"
        "- categórica × default → **barras de tasa**;\n"
        "- categórica × categórica → **mapa de calor**.\n\n"
        "«Ejes ajustados al percentil 99» corta la vista donde está el 99 % de los clientes. La interpretación "
        "(botón **Ver interpretación**) cambia con tu elección.",
        tecnico=("Según el tipo de par se reportan Spearman, Mann-Whitney / Kruskal-Wallis o χ² con V de Cramér. "
                 "Con n ≈ 30 000 el p-value casi siempre es significativo, por eso conviene mirar el tamaño del efecto."),
        pagina="/multivariado", sug=["¿Qué es Kruskal-Wallis?", "¿Qué es la V de Cramér?"]))
    add(Intencion(
        "splom", "Matriz de dispersión",
        ["explícame la matriz de dispersión", "scatter matrix", "splom", "puntos azules y dorados",
         "cruzar varias variables a la vez", "matriz de dispersión de 2 a 6 variables"],
        "La **matriz de dispersión** cruza entre 2 y 6 variables numéricas a la vez sobre una muestra de 1,500 "
        "clientes. Cada punto es un cliente: **azul** = pagó, **dorado** = incumplió. Si los puntos dorados se "
        "concentran en una zona, esa combinación separa a los clientes de riesgo. La interpretación indica qué "
        "par de variables se parece más.",
        tecnico="Se reportan los pares con mayor |ρ| de Spearman; sirve para detectar colinealidad entre predictoras "
                "y regiones donde se concentra la clase 1.",
        pagina="/multivariado", sug=["Explícame la matriz de correlación", "Explícame el cruce de variables"]))
    add(Intencion(
        "hallazgos", "Hallazgos multivariados clave",
        ["cuáles son los hallazgos clave", "hallazgos multivariados", "tarjetas de hallazgos",
         "qué concluye el multivariado", "resumen del multivariado", "conclusiones del EDA multivariado",
         "hallazgos de las relaciones entre variables", "tarjetas finales del multivariado",
         "qué conclusiones hay en esta página multivariada"],
        "**Hallazgos multivariados clave:**\n\n" +
        "\n".join(f"- **{ti}.** {tx}" for ti, tx in findings),
        pagina="/multivariado", sug=["¿Cuál es el mejor modelo?", "¿Qué es PAY_0?"], mood="proud"))

    # =====================================================================
    # Modelos
    # =====================================================================
    add(Intencion(
        "p_modelos", "Modelos",
        ["explícame la página de modelos", "qué hay en modelos", "sección de modelos", "qué modelos usaron",
         "cuántos modelos compararon", "qué clasificadores probaron", "112 combinaciones"],
        f"**Modelos** resume {len(A.MR)} combinaciones: **7 clasificadores × 4 técnicas de balanceo × 4 métodos de "
        "optimización**, con validación cruzada anidada.\n\n"
        f"- **KPIs:** mejor F1 {B['f1_mean']:.3f} ({best_lbl}), mejora de +{B['f1_mean'] - BL:.3f} sobre la línea "
        f"base y {B['recall_mean']:.0%} de incumplimientos detectados.\n"
        "- **Carrusel:** la mejor combinación de cada modelo.\n"
        "- **F1 por modelo y técnica** (mapa de calor) y **F1 vs. ROC-AUC** (dispersión).\n"
        "- **Matriz de confusión** del mejor modelo y **resumen SHAP**.",
        pagina="/modelos", sug=["¿Cuál es el mejor modelo?", "Explícame el carrusel de modelos",
                                "¿Qué técnicas de balanceo usaron?"]))
    add(Intencion(
        "mejor_modelo", "Mejor modelo",
        ["cuál es el mejor modelo", "qué modelo ganó", "modelo campeón", "cuál fue el mejor F1",
         "qué modelo recomiendan", "cuánto mejoró sobre la línea base", "qué tan bueno es el modelo",
         "qué modelo funcionó mejor", "cuál dio mejores resultados", "el modelo ganador"],
        f"El mejor es **{best_lbl}** con **{A.TECH_LBL[B['technique']].lower()}** y optimización "
        f"**{A.METHOD_LBL[B['method']].lower()}**:\n\n"
        f"- **F1:** {B['f1_mean']:.3f} ± {B['f1_std']:.3f} (línea base: {BL:.3f}, +{B['f1_mean'] - BL:.3f})\n"
        f"- **Recall:** {B['recall_mean']:.1%} · **Precisión:** {B['precision_mean']:.1%}\n"
        f"- **ROC-AUC:** {B['roc_auc_mean']:.3f} · **PR-AUC:** {B['pr_auc_mean']:.3f}\n\n"
        "Ojo: está prácticamente **empatado** con XGBoost y SVM; la diferencia es menor que la variación entre folds.",
        tecnico=("Validación cruzada anidada 3×3; la prueba de Nemenyi no separa a Random Forest, XGBoost y SVM "
                 "(p ≥ 0.88), aunque Random Forest sí supera al árbol de decisión (p = 0.018). 15 de las 112 "
                 "combinaciones quedan a menos de una desviación estándar del mejor F1."),
        pagina="/modelos", sug=["Explícame la matriz de confusión", "¿Qué es el F1?", "¿Cómo le fue a XGBoost?"],
        mood="proud"))
    add(Intencion(
        "carrusel", "Carrusel de modelos",
        ["explícame el carrusel de modelos", "cómo leo las tarjetas de los modelos", "qué significan las barras del carrusel",
         "tarjetas deslizables de modelos", "qué es el borde dorado", "comparación de modelos", "ranking de modelos"],
        "El **carrusel** muestra una tarjeta por modelo, con su **mejor combinación**, ordenadas por F1:\n\n"
        "- puesto, familia del modelo y F1 ± desviación estándar;\n"
        "- la técnica de balanceo y el método de optimización que lo lograron;\n"
        "- barras de precisión, recall, ROC-AUC y PR-AUC;\n"
        "- su mejor F1 con cada técnica de balanceo;\n- una descripción y una nota.\n\n"
        "El **borde dorado** marca el mejor. Ranking: " +
        ", ".join(f"{i + 1}. {A.MODEL_INFO[r['model']]['label']} ({r['f1_mean']:.3f})"
                  for i, r in A.BEST_BY_MODEL.iterrows()) + ".",
        pagina="/modelos", sug=["¿Cuál es el mejor modelo?", "¿Qué es el F1?", "¿Qué es el PR-AUC?"]))
    add(Intencion(
        "heat_modelos", "F1 por modelo y técnica de balanceo",
        ["explícame el mapa de calor de F1", "F1 por modelo y técnica de balanceo", "qué técnica de balanceo es mejor",
         "sirve balancear", "sin balanceo vs pesos de clase", "heatmap de modelos"],
        "Cada celda es el **mejor F1** de un modelo con una técnica de balanceo. Sin balanceo todos rinden peor "
        "porque casi no detectan a quienes incumplen; con **pesos de clase**, Random Forest y XGBoost llegan a 0.55.",
        tecnico=("Friedman (28 bloques modelo × método): χ² = 59.8, p ≈ 7·10⁻¹³. F1 medio: 0.453 sin balanceo, 0.526 "
                 "pesos de clase, 0.519 SMOTE y 0.513 ADASYN. «Sin balanceo» es peor que las tres (Nemenyi p ≤ 10⁻⁴); "
                 "pesos de clase supera a ADASYN (p = 0.020) y empata con SMOTE (p = 0.67). Naive Bayes casi no cambia."),
        pagina="/modelos", sug=["¿Qué técnicas de balanceo usaron?", "Explícame la gráfica de F1 vs ROC-AUC"]))
    add(Intencion(
        "scatter_modelos", "F1 vs. ROC-AUC",
        ["explícame la gráfica de F1 vs ROC-AUC", "balancear mueve el umbral", "dispersión de las 112 combinaciones",
         "por qué los puntos grises están abajo", "qué es la estrella en la dispersión de modelos",
         "balancear mueve el umbral no la capacidad de ordenar"],
        "Cada punto es una de las 112 combinaciones (color = técnica de balanceo; la **estrella** es la mejor). Las "
        "que no balancean (**gris**) quedan abajo: aciertan poco con quienes incumplen. Pero **no** quedan más a la "
        "izquierda: ordenan a los clientes casi igual de bien. Lo que cambia es dónde se pone el corte entre "
        "«paga» e «incumple».",
        tecnico=("ROC-AUC medio: 0.758 sin balanceo, 0.761 pesos de clase, 0.754 SMOTE y 0.749 ADASYN. Con umbral 0.5 "
                 "el recall pasa de 0.377 a 0.610 y la precisión baja de 0.618 a 0.460: la ganancia de F1 "
                 "(0.456 → 0.523) viene sobre todo del umbral y no de un modelo que discrimine mejor."),
        pagina="/modelos", sug=["¿Qué es el ROC-AUC?", "¿Qué es el umbral de decisión?"]))
    add(Intencion(
        "cm", "Matriz de confusión del mejor modelo",
        ["explícame la matriz de confusión", "qué es una matriz de confusión", "falsas alarmas", "no detectados",
         "falsos positivos y falsos negativos", "cuántos morosos detecta el modelo", "verdaderos positivos"],
        f"La **matriz de confusión** cruza lo real con lo que predijo {best_lbl} (umbral 0.5) sobre "
        f"{sum(cm.values()):,} clientes:\n\n"
        f"- **Detectados:** {cm['tp']:,} de {pos:,} que incumplieron ({cm['tp'] / pos:.0%}).\n"
        f"- **No detectados** (falsos negativos): {cm['fn']:,}.\n"
        f"- **Falsas alarmas** (falsos positivos): {cm['fp']:,}.\n"
        f"- **Bien clasificados que pagan:** {cm['tn']:,}.\n\n"
        f"De los {flagged:,} que marca como riesgosos, {cm['tp'] / flagged:.0%} sí incumple.",
        tecnico=("Predicciones out-of-fold de los tres modelos de los folds externos (AUC agrupado 0.781). Las "
                 "probabilidades no están calibradas (ECE = 0.196) porque el balanceo infla la clase positiva; una "
                 "recalibración isotónica la baja a 0.017 en un fold. Ajustar el umbral según el costo de cada "
                 "error es el siguiente paso."),
        pagina="/modelos", sug=["¿Qué es el recall?", "¿Qué es el umbral de decisión?"]))
    add(Intencion(
        "shap", "SHAP: variables que más pesan",
        ["qué variables pesan más en el modelo", "qué es SHAP", "importancia de variables", "interpretabilidad",
         "qué variable es más importante para el modelo", "explícame el resumen SHAP", "LIME"],
        "**SHAP** reparte la predicción de un modelo entre las variables para ver cuánto aporta cada una. En el "
        "mejor modelo:\n\n"
        "- **PAY_0 domina:** más meses de atraso en septiembre empujan hacia el default.\n"
        "- Le siguen **PAY_2 y PAY_3**, luego PAY_4 a PAY_6.\n"
        "- **Mayor LIMIT_BAL, menor riesgo.**\n"
        "- **Montos pagados y facturados:** efecto pequeño.\n\n"
        "Coincide con el EDA: el historial de pagos es la señal más fuerte y lo demográfico pesa poco.",
        tecnico=("SHAP del Random Forest sobre 100 clientes de un fold (notebook 06_interpretability). Con variables "
                 "correlacionadas SHAP reparte la importancia entre ellas, así que el orden exacto entre PAY_2…PAY_6 "
                 "es aproximado."),
        pagina="/modelos", sug=["¿Qué es PAY_0?", "Explícame «¿Qué empuja su riesgo?»"]))
    add(Intencion(
        "como_leer", "Qué tan distintos son los modelos",
        ["cómo leer los resultados de los modelos", "están empatados los modelos", "qué es Nemenyi", "qué es la prueba de Friedman",
         "importa el método de optimización", "son comparables los resultados de SVM", "diferencia significativa entre modelos"],
        "**Qué tan distintos son los modelos:**\n\n"
        "- Los primeros lugares están **prácticamente empatados**: 15 de 112 combinaciones quedan a menos de una "
        "desviación del mejor F1 y Nemenyi no separa ningún par.\n"
        "- Lo que sí importa es **balancear**. El método de optimización casi no cambia el F1 (0.5022 a 0.5032): "
        "conviene elegirlo por su costo.\n"
        "- SVM se corrió en Colab con GPU y no es estrictamente comparable; KNN y Naive Bayes con pesos de clase "
        "usan ajustes propios.\n"
        "- Validación cruzada anidada 3×3: con 3 folds las pruebas tienen poca potencia.",
        tecnico=("Friedman + Nemenyi: diferencia crítica 115.4 frente a 107.7 de diferencia máxima de rangos. La "
                 "desviación del F1 usa ddof = 1."),
        pagina="/modelos", sug=["¿Qué es la validación cruzada anidada?", "¿Qué métodos de optimización usaron?"]))
    add(Intencion(
        "metricas", "Métricas: F1, precisión, recall, ROC-AUC, PR-AUC",
        ["qué es el F1", "qué es el recall", "qué es la precisión", "qué es el ROC-AUC", "qué es el PR-AUC",
         "qué métricas usaron", "diferencia entre precisión y recall", "qué es AUC", "qué es sensibilidad",
         "por qué usan F1"],
        "Métricas de la clase **default**:\n\n"
        "- **Recall:** de quienes incumplen, qué parte detecta el modelo.\n"
        "- **Precisión:** de quienes marca como riesgosos, qué parte sí incumple.\n"
        "- **F1:** equilibrio entre ambas (media armónica). Es la métrica principal.\n"
        "- **ROC-AUC:** qué tan bien *ordena* a los clientes de más a menos riesgo (0.5 = azar, 1 = perfecto).\n"
        "- **PR-AUC:** como el AUC pero centrado en la clase minoritaria.\n\n"
        "No se usa accuracy porque, con 78 % de clientes que pagan, engaña.",
        pagina="/modelos", sug=["¿Cuál es el mejor modelo?", "¿Qué es el desbalance de clases?"]))
    add(Intencion(
        "balanceo", "Técnicas de balanceo",
        ["qué técnicas de balanceo usaron", "qué es SMOTE", "qué es ADASYN", "qué es class weight", "qué son pesos de clase",
         "class_weight balanced", "sobremuestreo", "cómo balancearon las clases"],
        "Las 4 opciones de **balanceo** comparadas:\n\n"
        "- **Sin balanceo:** los datos tal cual (línea base).\n"
        "- **Pesos de clase** (class_weight): equivocarse con un cliente que incumple «cuesta» más al entrenar. "
        "Fue la mejor.\n"
        "- **SMOTE:** crea clientes sintéticos de la clase minoritaria interpolando entre vecinos.\n"
        "- **ADASYN:** como SMOTE, pero genera más ejemplos donde la clase es más difícil de aprender.",
        pagina="/modelos", sug=["Explícame el mapa de calor de F1", "¿Qué métodos de optimización usaron?"]))
    add(Intencion(
        "optimizacion", "Métodos de optimización",
        ["qué métodos de optimización usaron", "qué es grid search", "qué es random search", "optimización bayesiana",
         "qué es Optuna", "algoritmo genético", "qué es DEAP", "hiperparámetros", "cómo optimizaron los hiperparámetros"],
        "Los **4 métodos de optimización** de hiperparámetros:\n\n"
        "- **Grid search:** prueba todas las combinaciones de una rejilla.\n"
        "- **Random search:** prueba combinaciones al azar.\n"
        "- **Bayesiana (Optuna):** usa los resultados previos para elegir la siguiente prueba.\n"
        "- **Genética (DEAP):** «evoluciona» una población de configuraciones.\n\n"
        "Casi no cambian el F1 (0.5022 a 0.5032 en promedio), así que conviene elegir por costo computacional.",
        pagina="/modelos", sug=["¿Qué es la validación cruzada anidada?", "¿Qué técnicas de balanceo usaron?"]))
    add(Intencion(
        "validacion", "Validación cruzada anidada",
        ["qué es la validación cruzada anidada", "validación cruzada", "folds", "cómo validaron los modelos",
         "qué son los folds externos e internos", "cross validation", "nested cv"],
        "En la **validación cruzada anidada** hay dos niveles: los **3 folds internos** eligen los hiperparámetros y "
        "los **3 folds externos** miden el rendimiento con datos que el ajuste nunca vio. Así el F1 reportado no "
        "está inflado por la búsqueda de hiperparámetros. El «±» del F1 es la desviación entre los folds externos.",
        pagina="/modelos", sug=["¿Están empatados los modelos?", "¿Qué es el F1?"]))
    for _, r in A.BEST_BY_MODEL.iterrows():
        m = r["model"]
        info = A.MODEL_INFO[m]
        lbl = info["label"]
        rank = int(_) + 1
        alias = {"random_forest": ["bosque aleatorio", "random forest"], "xgboost": ["xgboost", "xgb", "gradient boosting"],
                 "svm": ["svm", "máquina de vectores de soporte", "support vector machine"],
                 "knn": ["knn", "k vecinos", "vecinos más cercanos"],
                 "decision_tree": ["árbol de decisión", "decision tree", "árbol"],
                 "logistic_regression": ["regresión logística", "línea base", "logistic regression"],
                 "naive_bayes": ["naive bayes", "bayes ingenuo"]}[m]
        ej = []
        for a in alias:
            ej += [f"qué es {a}", f"cómo le fue a {a}", f"resultados de {a}", f"explícame {a}"]
        ej += [f"en qué puesto quedó {alias[0]}", f"F1 de {alias[0]}"]
        add(Intencion(
            f"m_{m}", lbl, ej,
            f"**{lbl}** · {info['family']} · puesto **#{rank}** de 7.\n\n{info['desc']}\n\n"
            f"Mejor combinación: {A.TECH_LBL[r['technique']].lower()} + {A.METHOD_LBL[r['method']].lower()} → "
            f"**F1 {r['f1_mean']:.3f}** ± {r['f1_std']:.3f}, recall {r['recall_mean']:.3f}, precisión "
            f"{r['precision_mean']:.3f}, ROC-AUC {r['roc_auc_mean']:.3f}.\n\n{info['note']}",
            pagina="/modelos", sug=["¿Cuál es el mejor modelo?", "Explícame el carrusel de modelos"],
            mood="proud" if rank == 1 else "explaining"))

    # =====================================================================
    # Predecir
    # =====================================================================
    add(Intencion(
        "p_predecir", "Predecir",
        ["explícame la página Predecir", "cómo funciona Predecir", "cómo predigo el riesgo de un cliente",
         "qué hace la sección predecir", "simulador de riesgo", "cómo evalúo un cliente",
         "calcular el riesgo de un cliente", "predecir si un cliente nuevo va a pagar", "probar el modelo con un cliente"],
        "En **Predecir** llenas los datos de un cliente y el modelo serializado calcula su riesgo **en vivo**:\n\n"
        f"1. **Flujo:** datos → transformaciones → {n_trees} árboles opinan → puntaje y decisión.\n"
        "2. **Formulario:** perfil (cupo, edad, sexo, educación, estado civil), estado de pago por mes y montos.\n"
        "3. **Resultado:** una tarjeta de crédito con el puntaje y el veredicto, señales y votos de los árboles.\n"
        "4. **Historial del cliente**, **¿Qué empuja su riesgo?** y **¿Qué pasaría si…?**\n"
        "5. **Cómo se serializó el modelo** (joblib).",
        pagina="/predecir",
        sug=["¿Cómo lleno el formulario?", "¿Cómo leo el puntaje de riesgo?", "Explícame «¿Qué pasaría si…?»"]))
    add(Intencion(
        "formulario", "Formulario del cliente",
        ["cómo lleno el formulario", "qué son los perfiles de ejemplo", "cliente típico", "atrasos recientes",
         "al día cupo alto", "deslizadores de estado de pago", "qué pongo en facturado y pagado", "qué significa Otro en sexo",
         "botones prueba un ejemplo"],
        "El **formulario** tiene tres bloques:\n\n"
        "- **Perfil:** cupo y edad con deslizadores; sexo, educación y estado civil con tarjetas.\n"
        "- **Estado de pago por mes** (abril → septiembre): −2 sin consumo, −1 pagó todo, 0 pago mínimo, "
        "1–8 meses de atraso.\n"
        "- **Montos por mes:** lo facturado y lo pagado en NT$.\n\n"
        "Los botones **Prueba un ejemplo** cargan tres perfiles: *cliente típico* (mediana y moda), *al día, cupo "
        "alto* y *atrasos recientes*. Con sexo «Otro» el modelo promedia las predicciones como hombre y mujer, "
        "porque el dataset solo registra esas dos.",
        pagina="/predecir", sug=["¿Cómo leo el puntaje de riesgo?", "¿Qué son los votos de los árboles?"]))
    thr = meta.get("umbral", 0.5)
    add(Intencion(
        "gauge", "Puntaje de riesgo y veredicto",
        ["cómo leo el puntaje de riesgo", "qué significa el porcentaje de la tarjeta", "qué es el umbral de decisión", "riesgo alto o bajo",
         "por qué 50 por ciento", "es una probabilidad el puntaje", "qué significa el veredicto", "el puntaje de la tarjeta",
         "qué son las señales del resultado", "a partir de qué puntaje es riesgo alto", "cuándo se considera riesgo alto",
         "por qué la tarjeta está rota", "qué significan las grietas de la tarjeta", "por qué se parte la tarjeta",
         "la tarjeta de crédito del resultado"],
        f"La **tarjeta de crédito** del resultado muestra el puntaje de 0 a 100 %. Desde el **umbral de {thr:.0%}** el veredicto es "
        "«riesgo alto: probable incumplimiento» (dorado); por debajo, «riesgo bajo» (azul).\n\n"
        "Además se rompe según el riesgo: está intacta con riesgo bajo, **se agrieta desde 30 %**, se tiñe de "
        "rojo y muestra la fractura principal desde el umbral, y **se parte en dos desde 75 %**.\n\nDebajo aparecen "
        "**señales** en lenguaje simple: atrasos, qué parte de lo facturado pagó y cómo es su cupo frente a los demás.\n\n"
        + (f"Con ese umbral el modelo detecta {prueba.get('recall', 0):.0%} de quienes incumplen y acierta en "
           f"{prueba.get('precision', 0):.0%} de los que marca (datos de prueba). " if prueba else "")
        + "No es una probabilidad calibrada: sirve para **ordenar y clasificar** clientes.",
        tecnico=("El Random Forest se entrenó con class_weight='balanced', lo que desplaza las probabilidades hacia la "
                 f"clase positiva: sobrestima el riesgo frente a la tasa real ({pct(rate)}). Para usar el puntaje "
                 "como probabilidad habría que calibrarlo (p. ej., regresión isotónica)."),
        pagina="/predecir", sug=["¿Qué son los votos de los árboles?", "Explícame «¿Qué empuja su riesgo?»"],
        mood="alert"))
    add(Intencion(
        "votos", "Votos de los árboles",
        ["qué son los votos de los árboles", "cuadritos del bosque", "árboles votan incumple", "waffle de árboles",
         "por qué el puntaje no coincide con los votos", "cuántos árboles tiene el modelo"],
        f"El modelo es un bosque de **{n_trees} árboles**. Cada uno opina si el cliente incumplirá; los "
        "**cuadros** muestran qué porcentaje del bosque vota «incumple» (cada cuadro = 1 %). El puntaje promedia las "
        "*probabilidades* de todos los árboles, no solo sus votos, por eso puede diferir un poco.",
        pagina="/predecir", sug=["¿Cómo leo el puntaje de riesgo?", "¿Qué es Random Forest?"]))
    add(Intencion(
        "historial", "Historial del cliente",
        ["explícame el historial del cliente", "facturado vs pagado", "barras azules y doradas del historial",
         "línea de estado de pago", "gráfica del historial"],
        "En **Historial del cliente** las barras comparan lo **facturado** (azul) con lo **pagado** (dorado) cada "
        "mes, y la línea dorada es el **estado de pago**. Si la línea sube por encima de 0 hay atraso; si las barras "
        "doradas son mucho más bajas que las azules, el cliente paga poco de su deuda.",
        tecnico=("El modelo no usa las seis facturas por separado: las resume en nivel medio (log con signo), tendencia "
                 "mensual y número de meses con saldo a favor. Los PAY_x sí entran uno por uno."),
        pagina="/predecir", sug=["Explícame «¿Qué empuja su riesgo?»", "¿Qué es BILL_AMT?"]))
    add(Intencion(
        "drivers", "¿Qué empuja su riesgo?",
        ["explícame «¿Qué empuja su riesgo?»", "qué empuja su riesgo", "aporte de cada grupo de variables",
         "puntos de riesgo que suma o resta", "por qué este cliente es riesgoso", "qué aumenta el riesgo del cliente",
         "por qué el puntaje de este cliente es alto", "qué explica el riesgo de este cliente", "qué lo hace riesgoso"],
        "Cada barra responde: «si en este grupo de datos el cliente fuera como un **cliente típico**, ¿cuánto "
        "cambiaría su puntaje?». Los grupos son historial de pagos, montos pagados, facturación, cupo y perfil "
        "demográfico. Barras **doradas** suben el riesgo; **azules** lo bajan.",
        tecnico=("Explicación local por sustitución: se reemplaza cada grupo por la mediana/moda del cliente típico y se "
                 "mide la diferencia en el puntaje. Es aproximada: no suma exactamente el total porque los grupos "
                 "interactúan dentro del bosque (a diferencia de SHAP)."),
        pagina="/predecir", sug=["Explícame «¿Qué pasaría si…?»", "¿Qué es SHAP?"]))
    add(Intencion(
        "whatif", "¿Qué pasaría si…?",
        ["explícame «¿Qué pasaría si…?»", "qué pasaría si", "simulador qué pasaría si", "cambiar una sola variable",
         "curva what if", "qué es la estrella este cliente", "qué pasa si se atrasa un mes más"],
        "**¿Qué pasaría si…?** muestra el puntaje que tendría *este mismo* cliente si solo cambiara una variable: "
        "atraso en septiembre, cupo, pago de septiembre o edad. La **estrella** es su situación actual y la franja "
        "superior marca el riesgo alto. Por ejemplo, con «Atraso en septiembre» ves cuánto sube el riesgo con "
        "cada mes de atraso.",
        tecnico=("Es una curva ICE (dependencia individual): se fija el resto y se recorre una variable. En un bosque la "
                 "curva tiene escalones porque cada árbol corta en umbrales; describe al modelo, no implica causalidad."),
        pagina="/predecir", sug=["Explícame «¿Qué empuja su riesgo?»", "¿Cómo leo el puntaje de riesgo?"]))
    hp = meta.get("hiperparametros", {})
    add(Intencion(
        "serializacion", "Cómo se serializó el modelo",
        ["cómo se serializó el modelo", "qué es serializar", "qué es joblib", "qué es el archivo pkl",
         "modelo_credito.pkl", "cómo se guardó el modelo", "cómo se entrenó el modelo de predecir",
         "hiperparámetros del modelo serializado", "métricas de prueba del modelo"],
        "**Serializar** es guardar un modelo ya entrenado en un archivo para usarlo sin reentrenar:\n\n"
        "1. **Entrenar** (`modelo/entrenar.py`) → 2. **Guardar** con `joblib.dump` en `modelo_credito.pkl` → "
        "3. **Cargar** con `joblib.load` al arrancar el tablero → 4. **Predecir** con `predict_proba` en cada cambio.\n\n"
        f"El .pkl guarda el pipeline completo: transformaciones del proyecto + one-hot + Random Forest "
        f"({meta.get('balanceo', 'pesos de clase')})."
        + (f" En prueba (20 %): F1 {prueba['f1']:.3f}, recall {prueba['recall']:.3f}, precisión "
           f"{prueba['precision']:.3f}, ROC-AUC {prueba['roc_auc']:.3f}." if prueba else ""),
        tecnico=(f"Búsqueda: {meta.get('busqueda', '—')}. Hiperparámetros: "
                 + ", ".join(f"{k} = {v}" for k, v in hp.items())
                 + f". Entrenado con {meta.get('n_entrenamiento', 0):,} clientes. Debe cargarse con la misma versión "
                   f"de scikit-learn ({meta.get('versiones', {}).get('scikit-learn', '—')})."),
        pagina="/predecir", sug=["¿Qué son los votos de los árboles?", "¿Qué es Random Forest?"]))

    # =====================================================================
    # Enlaces y equipo
    # =====================================================================
    add(Intencion(
        "p_enlaces", "Enlaces",
        ["explícame la página de enlaces", "dónde está el repositorio", "link del github", "dónde está el notebook",
         "jupyter book", "libro del proyecto", "dónde veo el código", "cómo reproduzco el análisis", "enlaces"],
        "**Enlaces** reúne:\n\n"
        "- **Sobre el proyecto:** resumen del Jupyter Book.\n"
        "- **Tarjetas de enlaces:** " + ", ".join(L["title"] for L in A.LINKS) + ".\n"
        "- **Pipeline completo:** los siete notebooks en orden.\n"
        "- **Reproducir el análisis:** clonar, instalar con `pip install -r requirements.txt` y correr "
        "`python app.py`.",
        pagina="/enlaces", sug=["¿Qué notebooks tiene el pipeline?", "¿Quiénes hicieron el proyecto?"]))
    add(Intencion(
        "notebooks", "Pipeline de notebooks",
        ["qué notebooks tiene el pipeline", "pipeline completo", "lista de notebooks", "qué hace cada notebook",
         "notebook 00", "notebook de interpretabilidad"],
        "**Pipeline completo** (siete notebooks del libro):\n\n" +
        "\n".join(f"- **{num} · {ti}:** {d}" for num, ti, _f, d in A.NOTEBOOKS),
        pagina="/enlaces", sug=["Explícame la página de enlaces", "¿Qué es SHAP?"]))
    add(Intencion(
        "p_equipo", "Equipo",
        ["quiénes hicieron el proyecto", "autores", "quién hizo este dashboard", "equipo", "quiénes son las autoras",
         "contacto de las autoras", "correo de las autoras", "de qué universidad son", "explícame la página de equipo"],
        "Este tablero lo hicieron:\n\n" +
        "\n".join(f"- **{m['name']}** — {m['role']} · {m['email']}" for m in A.TEAM) +
        f"\n\n{A.INSTITUTION}. En la página **Equipo** cada tarjeta se voltea para ver la bio, GitHub, LinkedIn y "
        "un botón que copia el correo.",
        pagina="/equipo", sug=["¿De qué trata el proyecto?", "Explícame la página de enlaces"], mood="happy"))

    # =====================================================================
    # Páginas, sugerencias por página
    # =====================================================================
    paginas = {p: lbl for p, lbl, _ic in A.NAV}
    paginas["/"] = "Inicio (portada)"
    intencion_de_pagina = {"/": "p_inicio", "/introduccion": "p_intro", "/problema": "p_problema", "/marco": "p_marco",
                           "/univariado": "p_uni", "/multivariado": "p_multi", "/modelos": "p_modelos",
                           "/predecir": "p_predecir", "/enlaces": "p_enlaces", "/equipo": "p_equipo"}
    sug_de_pagina = {
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
    }
    return I, paginas, intencion_de_pagina, sug_de_pagina
