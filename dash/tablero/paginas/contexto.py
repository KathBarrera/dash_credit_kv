# -*- coding: utf-8 -*-
"""Páginas Introducción, Problema y Objetivos, y Marco Teórico."""

from dash import dcc, html

from tablero.componentes import (_tbl, _ul, card, kpi, page_title)
from tablero.config import tx
from tablero.datos import DATA_INFO, DF, TARGET
from tablero.iconos import icon, zoom_btn
from tablero.paginas.inicio import quick_look
from tablero.resultados import (BEST, BEST_BASE, N_BASE, N_EXTRA, TWD_PER_USD_2005, minfo)
from tablero.utilidades import GLOBAL_RATE


def page_intro():
    n_def = int(DF[TARGET].sum())
    I = DATA_INFO
    return html.Div([
        page_title(tx("Introducción", "Introduction"), ""),
        quick_look(),
        html.Div([
            kpi(tx("Clientes analizados", "Clients analyzed"), f"{len(DF):,}", tx("tras la limpieza", "after cleaning"),
                ico="users"),
            kpi("Variables", "24", tx("23 predictoras + 1 objetivo · 21 columnas al modelar",
                                      "23 predictors + 1 target · 21 columns for modeling"), ico="columns"),
            kpi(tx("Tasa de default", "Default rate"), f"{GLOBAL_RATE:.1%}", f"{n_def:,} {tx('clientes', 'clients')}",
                ico="alert"),
            kpi(tx("Periodo", "Period"), tx("Abr a Sep 2005", "Apr to Sep 2005"), tx("banco de Taiwán", "Taiwanese bank"),
                ico="calendar"),
        ], className="kpi-row k4"),
        html.Div([
            card(tx("Introducción", "Introduction"), [
                html.P(tx("Las tarjetas de crédito son una de las líneas de la banca minorista con mayor exposición "
                          "al riesgo: cada cliente recibe un cupo (límite de crédito) y se espera que lo pague en las "
                          "fechas pactadas. Cuando no lo hace, la entidad enfrenta pérdidas, mayores costos de cobranza "
                          "y la necesidad de provisionar capital.",
                          "Credit cards are one of the retail banking lines with the highest risk exposure: each client "
                          "receives a limit and is expected to repay it on the agreed dates. When they do not, the bank "
                          "faces losses, higher collection costs and the need to set aside capital.")),
                html.P(tx(f"Este tablero recorre el proyecto completo con el conjunto Default of Credit Card Clients "
                          f"(UCI): {I['filas_originales']:,} clientes observados entre abril y septiembre de 2005, de "
                          "quienes se conoce su límite de crédito, sus datos demográficos, seis meses de historial de "
                          "pagos, los montos facturados y pagados, y si incumplieron el pago del mes siguiente.",
                          f"This dashboard walks through the whole project using the Default of Credit Card Clients "
                          f"dataset (UCI): {I['filas_originales']:,} clients observed between April and September 2005, "
                          "with their credit limit, demographics, six-month payment history, billed and paid amounts, "
                          "and whether they defaulted the following month.")),
                html.P(tx("Tras la limpieza quedan 24 variables (23 predictoras y 1 objetivo); el conjunto final de "
                          "modelado tiene 21 columnas porque las 6 BILL_AMT se resumen en 3 variables derivadas.",
                          "After cleaning there are 24 variables (23 predictors and 1 target); the final modeling set has "
                          "21 columns because the 6 BILL_AMT are summarized into 3 derived variables.")),
                html.P(tx("Primero se exploran los datos (EDA univariado y multivariado) para entender qué variables "
                          f"anticipan el incumplimiento. Luego se comparan {N_BASE} combinaciones de modelos tradicionales "
                          "(diseño factorial: 7 algoritmos × 4 técnicas de balanceo × 4 optimizadores) y, aparte, "
                          f"{N_EXTRA} corridas de CS-FOF, el modelo original del proyecto, que busca "
                          f"superar el mejor F1 de esas {N_BASE}. La mejor de las {N_BASE} es "
                          f"{minfo(BEST_BASE['model'], 'label')} (F1 {BEST_BASE['f1_mean']:.3f}). CS-FOF obtiene el mayor "
                          f"F1 medio ({BEST['f1_mean']:.3f}), pero la diferencia es menor que 0.002 y "
                          "ninguna prueba estadística las separa. Por último, la página Predecir usa XGBoost con pesos de "
                          "clase, el mejor modelo de referencia, o CS-FOF, para estimar el riesgo de un cliente nuevo.",
                          "First the data is explored (univariate and multivariate EDA) to see which variables "
                          f"anticipate default. Then {N_BASE} traditional model combinations are compared (factorial "
                          "design: 7 algorithms × 4 balancing techniques × 4 optimizers) and, separately, "
                          f"{N_EXTRA} runs of CS-FOF, the project's original model, which tries to "
                          f"beat the best F1 of those {N_BASE}. The best of the {N_BASE} is "
                          f"{minfo(BEST_BASE['model'], 'label')} (F1 {BEST_BASE['f1_mean']:.3f}). CS-FOF has the highest "
                          f"mean F1 ({BEST['f1_mean']:.3f}), but the difference is below 0.002 and no "
                          "statistical test separates them. Finally, the Predict page uses XGBoost with class weights, the "
                          "best baseline model, or CS-FOF, to estimate the risk of a new client.")),
                html.P(tx("Cada gráfico trae una interpretación básica (lenguaje cotidiano) y una técnica "
                          "(estadísticos y recomendaciones de modelado).",
                          "Each chart comes with a basic interpretation (everyday language) and a technical one "
                          "(statistics and modeling recommendations).")),
            ], cls="span-2"),
            card(tx("Fuentes", "Sources"), [
                html.P("Yeh, I-C. & Lien, C. (2009). The comparisons of data mining techniques for the predictive "
                       "accuracy of probability of default of credit card clients. Expert Systems with Applications, "
                       "36(2), 2473-2480."),
                html.P([tx("Datos: ", "Data: "),
                        html.A("UCI Machine Learning Repository",
                               href="https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients",
                               target="_blank", rel="noopener")]),
                html.P(tx("Cifras monetarias en dólares taiwaneses (NT$).", "Monetary figures in New Taiwan dollars (NT$).")),
                _ul([tx(f"{I['filas_originales']:,} clientes de un banco de Taiwán", f"{I['filas_originales']:,} clients of a Taiwanese bank"),
                     tx("23 variables explicativas y 1 objetivo", "23 explanatory variables and 1 target"),
                     tx("Seis meses de historia: abril a septiembre de 2005", "Six months of history: April to September 2005")]),
            ]),
        ], className="grid g3 intro-grid"),
    ])


def money_kpi(label, amount, note):
    """KPI de un monto en millones de NT$ con su equivalente en dólares debajo (el valor no se parte en dos líneas)."""
    return html.Div([zoom_btn(), html.Div(html.Div(label, className="kpi-label"), className="kpi-head"),
                     html.Div(f"NT$\u00a0{amount / 1e6:,.0f}\u00a0M", className="kpi-value"),
                     html.Div(f"≈ US$\u00a0{amount / TWD_PER_USD_2005 / 1e6:,.1f}\u00a0M", className="kpi-usd"),
                     html.Div(note, className="kpi-note")], className="kpi kpi-money")


def page_problem():
    n_def = int(DF[TARGET].sum())
    exposure = DF.loc[DF[TARGET] == 1, "LIMIT_BAL"].sum()
    bill_def = DF.loc[DF[TARGET] == 1, "BILL_AMT1"].clip(lower=0).sum()
    hip = [
        ("H1", tx("El historial reciente de pagos (PAY_0 … PAY_6) es el factor más fuertemente asociado al incumplimiento.",
                  "Recent payment history (PAY_0 … PAY_6) is the factor most strongly associated with default."),
         tx("Multivariado · Matriz de correlación", "Multivariate · Correlation matrix")),
        ("H2", tx("Los clientes con menor límite de crédito (LIMIT_BAL) presentan una mayor tasa de default.",
                  "Clients with a lower credit limit (LIMIT_BAL) have a higher default rate."),
         tx("Multivariado · Límite según default", "Multivariate · Limit by default")),
        ("H3", tx("Las variables demográficas (sexo, educación, estado civil, edad) se asocian con el default, pero con "
                  "un tamaño de efecto pequeño.",
                  "Demographic variables (sex, education, marital status, age) are associated with default, but with "
                  "a small effect size."),
         tx("Multivariado · Tasas por perfil y edad", "Multivariate · Rates by profile and age")),
        ("H4", tx("Los montos facturados mensuales (BILL_AMT1 a BILL_AMT6) están fuertemente correlacionados entre sí "
                  "(multicolinealidad).",
                  "Monthly bill amounts (BILL_AMT1 to BILL_AMT6) are strongly correlated with each other (multicollinearity)."),
         tx("Univariado y Multivariado", "Univariate and Multivariate")),
        ("H5", tx("La clase «default» es minoritaria, por lo que el problema presenta desbalance de clases.",
                  "The “default” class is the minority, so the problem has class imbalance."),
         tx("Univariado · Variable objetivo", "Univariate · Target variable")),
    ]
    # Objetivos específicos: los mismos 7 del libro del proyecto (introduccion.md), con modelado incluido
    objs = [
        (tx("Describir el problema y el conjunto de datos, incluida la variable objetivo y su nivel de desbalance.",
            "Describe the problem and the dataset, including the target variable and its level of imbalance."),
         tx("Introducción y EDA Univariado", "Introduction and Univariate EDA")),
        (tx("Documentar de forma reproducible el proceso ETL, justificando cada decisión de limpieza.",
            "Document the ETL process reproducibly, justifying each cleaning decision."), tx("Introducción", "Introduction")),
        (tx("Caracterizar estadísticamente las variables mediante un EDA univariado y bivariado, y evaluar la "
            "multicolinealidad.",
            "Statistically characterize the variables through a univariate and bivariate EDA, and assess "
            "multicollinearity."), tx("EDA Univariado y Multivariado", "Univariate and Multivariate EDA")),
        (tx("Entrenar un modelo base (regresión logística) sobre una partición train/test aislada de fuga de "
            "información, y cuantificar su margen de mejora, en especial en falsos negativos y falsos positivos.",
            "Train a baseline model (logistic regression) on a train/test split free of information leakage, and "
            "quantify its room for improvement, especially in false negatives and false positives."),
         tx("Modelos", "Models")),
        (tx("Comparar 112 configuraciones (7 modelos × 4 técnicas de balanceo × 4 métodos de optimización) con "
            "validación cruzada anidada y el F1 de la clase default como métrica principal.",
            "Compare 112 configurations (7 models × 4 balancing techniques × 4 optimization methods) with nested "
            "cross-validation and the default-class F1 as the main metric."), tx("Modelos", "Models")),
        (tx("Contrastar estadísticamente las configuraciones y analizar la calibración de probabilidades y el costo "
            "computacional.",
            "Statistically compare the configurations and analyze probability calibration and computational cost."),
         tx("Modelos y Modelo original", "Models and Original model")),
        (tx("Interpretar los modelos con SHAP y LIME para identificar las variables que más influyen en la predicción.",
            "Interpret the models with SHAP and LIME to identify the variables that most influence the prediction."),
         tx("Modelos", "Models")),
    ]
    return html.Div([
        page_title(tx("Problema y Objetivos", "Problem and Objectives"), ""),
        html.Div([
            card(tx("Planteamiento del problema", "Problem statement"), [
                html.P(tx("Una entidad financiera otorga crédito sin saber con certeza quién pagará. Si concede cupos "
                          "demasiado altos a clientes que luego incumplen, la cartera se deteriora: se pierde el capital "
                          "no recuperado, aumentan los costos de cobranza y se deben constituir mayores provisiones. Si, "
                          "por el contrario, restringe el crédito en exceso, pierde ingresos por intereses y comisiones.",
                          "A financial institution grants credit without knowing for sure who will pay. If it grants "
                          "limits that are too high to clients who later default, the portfolio deteriorates: "
                          "unrecovered capital is lost, collection costs rise and larger provisions must be set aside. "
                          "If, on the other hand, it restricts credit too much, it loses interest and fee income.")),
                html.P(tx(f"En esta muestra, {GLOBAL_RATE:.1%} de los clientes ({n_def:,}) no pagó su tarjeta el mes "
                          "siguiente. Identificar tempranamente qué perfiles y comportamientos anticipan ese "
                          "incumplimiento es la base para fijar límites, priorizar la cobranza preventiva y alimentar "
                          "un modelo de scoring.",
                          f"In this sample, {GLOBAL_RATE:.1%} of clients ({n_def:,}) did not pay their card the "
                          "following month. Identifying early which profiles and behaviors anticipate that default is "
                          "the basis for setting limits, prioritizing preventive collection and feeding a scoring model.")),
                html.Div([
                    kpi(tx("Clientes en default", "Clients in default"), f"{n_def:,}",
                        tx(f"{GLOBAL_RATE:.1%} de la muestra", f"{GLOBAL_RATE:.1%} of the sample")),
                    money_kpi(tx("Límite expuesto", "Exposed limit"), exposure,
                              tx("suma de LIMIT_BAL de quienes incumplen", "sum of LIMIT_BAL of defaulters")),
                    money_kpi(tx("Saldo facturado (Sep)", "Billed balance (Sep)"), bill_def,
                              tx("BILL_AMT1 positivo de quienes incumplen", "positive BILL_AMT1 of defaulters")),
                ], className="kpi-row k3"),
                html.P(tx(f"Conversión a dólares estadounidenses con la tasa promedio de 2005: {TWD_PER_USD_2005} NT$ por US$.",
                          f"Conversion to US dollars at the 2005 average rate: {TWD_PER_USD_2005} NT$ per US$."),
                       className="muted kpi-fx"),
                html.P(tx("Los errores no son simétricos: no detectar a quien incumplirá (falso negativo) suele costar "
                          "más que revisar de más a quien sí pagaría (falso positivo).",
                          "Errors are not symmetric: failing to detect someone who will default (false negative) "
                          "usually costs more than over-reviewing someone who would pay (false positive)."),
                       className="muted"),
            ], cls="span-2"),
            card(tx("Pregunta de investigación", "Research question"), [
                html.Div(tx("¿Qué características del cliente, de su línea de crédito y de su historial reciente de pagos "
                            "se asocian con el incumplimiento del mes siguiente, y con qué intensidad?",
                            "Which characteristics of the client, their credit line and their recent payment history "
                            "are associated with default the following month, and how strongly?"), className="callout"),
                html.P(html.B(tx("Preguntas específicas", "Specific questions"))),
                _ul([tx("¿Cómo se distribuyen las variables y qué problemas de calidad presentan?",
                        "How are the variables distributed and what quality issues do they have?"),
                     tx("¿Qué tan desbalanceada está la variable objetivo?", "How imbalanced is the target variable?"),
                     tx("¿Qué variables separan mejor a los clientes que incumplen?",
                        "Which variables best separate the clients who default?"),
                     tx("¿Existe redundancia entre las variables predictoras?",
                        "Is there redundancy among the predictor variables?"),
                     tx("¿Qué combinación de algoritmo, técnica de balanceo y método de optimización detecta mejor a los "
                        "clientes en riesgo de incumplimiento, y qué parte de la mejora se debe a cada decisión?",
                        "Which combination of algorithm, balancing technique and optimization method best detects "
                        "clients at risk of default, and how much of the improvement is due to each decision?")]),
            ]),
        ], className="grid g3"),
        html.Div([
            card(tx("Justificación", "Rationale"), [
                html.P(tx("Un EDA riguroso evita errores costosos en el modelado: revela datos mal codificados, "
                          "variables redundantes, sesgos de muestreo y desbalance antes de que afecten al modelo.",
                          "A rigorous EDA prevents costly modeling mistakes: it reveals miscoded data, redundant "
                          "variables, sampling biases and imbalance before they affect the model.")),
                html.P(tx("Además permite explicar a perfiles no técnicos (riesgos, cobranza, gerencia) qué señales "
                          "preceden al incumplimiento, con evidencia visual y estadística.",
                          "It also makes it possible to explain to non-technical audiences (risk, collections, "
                          "management) which signals precede default, with visual and statistical evidence.")),
            ]),
            card(tx("Alcance y limitaciones", "Scope and limitations"), _ul([
                tx("Datos de un solo banco de Taiwán y de un periodo corto (abril a septiembre de 2005): no se generalizan "
                   "sin cautela a otros mercados o épocas.",
                   "Data from a single Taiwanese bank over a short period (April to September 2005): they should not be "
                   "generalized to other markets or times without caution."),
                tx("El análisis es asociativo; una correlación no implica causalidad.",
                   "The analysis is associative; correlation does not imply causation."),
                tx("Los códigos −2 y 0 de PAY_x no están documentados con precisión en la fuente; se conservan sin recodificar.",
                   "Codes −2 and 0 of PAY_x are not precisely documented in the source; they are kept without recoding."),
            ])),
        ], className="grid g2"),
        card(tx("Hipótesis exploratorias", "Exploratory hypotheses"),
             _tbl(["#", tx("Hipótesis", "Hypothesis"), tx("Dónde se evalúa", "Where it is assessed")],
                  [(html.B(a), b, c) for a, b, c in hip])),
        card(tx("Objetivos", "Objectives"), [
            html.Div(tx("Objetivo general", "General objective"), className="obj-label"),
            html.Div(tx("Evaluar de forma sistemática el efecto del preprocesamiento, el algoritmo, la técnica de "
                        "balanceo y el método de optimización de hiperparámetros sobre la capacidad de predecir el "
                        "incumplimiento de pago de clientes de tarjetas de crédito.",
                        "Systematically evaluate the effect of preprocessing, the algorithm, the balancing technique and "
                        "the hyperparameter optimization method on the ability to predict payment default among credit "
                        "card clients."),
                     className="callout"),
            html.Div(tx("Objetivos específicos", "Specific objectives"), className="obj-label"),
            html.Ol([html.Li([t, html.Span(s, className="tag")]) for t, s in objs], className="obj-list"),
        ]),
    ])


def page_marco():
    # Referencias en formato IEEE (texto tal cual lo entregó el equipo; [1] es el artículo base del dataset)
    refs = [
        "[1] I.-C. Yeh y C.-H. Lien, “The comparisons of data mining techniques for the predictive accuracy of "
        "probability of default of credit card clients,” *Expert Systems with Applications*, vol. 36, no. 2, "
        "pp. 2473-2480, 2009, doi: 10.1016/j.eswa.2007.12.020.",
        "[2] UCI Machine Learning Repository, “Default of Credit Card Clients,” conjunto de datos. [En línea]. "
        "Disponible: <https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients>. Consultado: 28 oct. "
        "2026. Repositorio; excepción al filtro temporal.",
        "[3] S. M. Lundberg y S.-I. Lee, “A unified approach to interpreting model predictions,” en *Advances in "
        "Neural Information Processing Systems*, vol. 30, 2017, pp. 4765-4774.",
        "[4] N. Bussmann, P. Giudici, D. Marinelli y J. Papenbrock, “Explainable machine learning in credit risk "
        "management,” *Computational Economics*, vol. 57, pp. 203-216, 2021; publicación en línea, 2020, "
        "doi: 10.1007/s10614-020-10042-0.",
        "[5] P. Branco, L. Torgo y R. P. Ribeiro, “A survey of predictive modeling on imbalanced domains,” *ACM "
        "Computing Surveys*, vol. 49, no. 2, art. 31, 2016, doi: 10.1145/2907070.",
        "[6] A. Fernández, S. García, F. Herrera y N. V. Chawla, “SMOTE for learning from imbalanced data: Progress "
        "and challenges, marking the 15-year anniversary,” *Journal of Artificial Intelligence Research*, vol. 61, "
        "pp. 863-905, 2018, doi: 10.1613/jair.1.11192.",
        "[7] G. James, D. Witten, T. Hastie y R. Tibshirani, *An Introduction to Statistical Learning: With "
        "Applications in R*, 2.ª ed. Springer, 2021, doi: 10.1007/978-1-0716-1418-1.",
        "[8] M. B. A. McDermott, L. H. Hansen, H. Zhang, G. Angelotti y J. Gallifant, “A closer look at AUROC and "
        "AUPRC under class imbalance,” arXiv:2401.06091, versión 2, 2024. Prepublicación. [En línea]. "
        "Disponible: <https://arxiv.org/abs/2401.06091>.",
        "[9] T. Chen y C. Guestrin, “XGBoost: A scalable tree boosting system,” en *Proc. 22nd ACM SIGKDD Int. Conf. "
        "Knowledge Discovery and Data Mining*, 2016, pp. 785-794, doi: 10.1145/2939672.2939785.",
    ]
    var_table = [
        ("LIMIT_BAL", tx("Numérica continua", "Continuous numeric"),
         tx("Monto del crédito otorgado (individual + familiar/suplementario) en dólares taiwaneses (NT$).",
            "Amount of credit granted (individual + family/supplementary) in New Taiwan dollars (NT$).")),
        ("SEX", tx("Categórica", "Categorical"), tx("Género: 1 = hombre, 2 = mujer.", "Gender: 1 = male, 2 = female.")),
        ("EDUCATION", tx("Categórica ordinal", "Ordinal categorical"),
         tx("1 = posgrado, 2 = universidad, 3 = secundaria, 4 = otros (los códigos 0, 5 y 6 no documentados se "
            "reagrupan en «Otros»).",
            "1 = graduate school, 2 = university, 3 = high school, 4 = others (undocumented codes 0, 5 and 6 are "
            "grouped into “Others”).")),
        ("MARRIAGE", tx("Categórica", "Categorical"),
         tx("Estado civil: 1 = casado, 2 = soltero, 3 = otros (el código 0 se reagrupa en «Otros»).",
            "Marital status: 1 = married, 2 = single, 3 = others (code 0 is grouped into “Others”).")),
        ("AGE", tx("Numérica discreta", "Discrete numeric"), tx("Edad en años.", "Age in years.")),
        ("PAY_0, PAY_2-PAY_6", "Ordinal",
         tx("Estado de pago mensual de septiembre (PAY_0) hacia abril (PAY_6). −2/−1/0 = sin atraso; 1 = un mes de "
            "atraso; …; 8 = 8 meses; 9 = 9 meses o más.",
            "Monthly repayment status from September (PAY_0) back to April (PAY_6). −2/−1/0 = no delay; "
            "1 = one month late; …; 8 = 8 months; 9 = 9 months or more.")),
        ("BILL_AMT1-6", tx("Numérica continua", "Continuous numeric"),
         tx("Monto facturado en el estado de cuenta de septiembre (1) a abril (6), en NT$. Puede ser negativo "
            "(saldo a favor).",
            "Amount on the bill statement from September (1) to April (6), in NT$. It can be negative "
            "(credit balance).")),
        ("PAY_AMT1-6", tx("Numérica continua", "Continuous numeric"),
         tx("Monto efectivamente pagado de septiembre (1) a abril (6), en NT$.",
            "Amount actually paid from September (1) to April (6), in NT$.")),
        ("default_payment_next_month", tx("Binaria (objetivo)", "Binary (target)"),
         tx("1 = el cliente incumple el pago el mes siguiente (octubre 2005); 0 = no incumple.",
            "1 = the client defaults the following month (October 2005); 0 = does not default.")),
    ]
    # Fórmulas en LaTeX (MathJax incluido en Dash); r"..." evita escapar las barras
    F = lambda tex: dcc.Markdown(f"$$\\displaystyle {tex}$$", mathjax=True, className="formula")
    rank = tx(r"\mathrm{rango}", r"\mathrm{rank}")
    return html.Div([
        page_title(tx("Marco Teórico", "Theoretical Framework"), ""),
        html.Div([
            card(tx("1. Riesgo de crédito y default", "1. Credit risk and default"), [
                html.P(tx("El riesgo de crédito es la posibilidad de que una entidad sufra pérdidas porque un deudor "
                          "no cumple, total o parcialmente, sus obligaciones. En la regulación bancaria (Basilea II) la "
                          "pérdida esperada se descompone así:",
                          "Credit risk is the possibility that an institution suffers losses because a debtor fails, "
                          "fully or partially, to meet their obligations. In banking regulation (Basel II) expected loss "
                          "is broken down as follows:")),
                F(r"\mathrm{EL} = \mathrm{PD} \times \mathrm{LGD} \times \mathrm{EAD}"),
                _ul([tx("PD: probabilidad de incumplimiento en un horizonte dado (lo que estudian estos datos).",
                        "PD: probability of default over a given horizon (what these data study)."),
                     tx("LGD: porcentaje de la exposición que se pierde si hay incumplimiento.",
                        "LGD: percentage of the exposure lost if there is a default."),
                     tx("EAD: monto expuesto en el momento del incumplimiento.",
                        "EAD: amount exposed at the time of default.")]),
                html.P(tx("En este proyecto, default es la variable binaria que indica si el cliente no pagó en el mes siguiente.",
                          "In this project, default is the binary variable indicating whether the client did not pay "
                          "the following month.")),
            ]),
            card(tx("2. Scoring crediticio", "2. Credit scoring"), [
                html.P(tx("Los modelos de scoring estiman la PD a partir de variables del cliente: comportamiento de pago, "
                          "límite, deuda y perfil demográfico. Sirven para aprobar o rechazar solicitudes, fijar cupos y "
                          "priorizar la cobranza.",
                          "Scoring models estimate PD from client variables: payment behavior, limit, debt and "
                          "demographic profile. They are used to approve or reject applications, set limits and "
                          "prioritize collections.")),
                html.P(tx("Antes de modelar, el EDA revela la calidad de los datos, las variables más informativas y los "
                          "problemas (colinealidad, desbalance, atípicos) que condicionarán al modelo.",
                          "Before modeling, the EDA reveals data quality, the most informative variables and the "
                          "issues (collinearity, imbalance, outliers) that will affect the model.")),
            ]),
            card(tx("3. Análisis exploratorio de datos (EDA)", "3. Exploratory data analysis (EDA)"), [
                html.P(tx("Propuesto por John W. Tukey (1977): explorar los datos con resúmenes numéricos y gráficos, "
                          "antes de ajustar modelos, para descubrir patrones, anomalías y supuestos.",
                          "Proposed by John W. Tukey (1977): explore the data with numerical summaries and charts, "
                          "before fitting models, to discover patterns, anomalies and assumptions.")),
                _ul([tx("Univariado: una variable a la vez (frecuencias, histograma, boxplot).",
                        "Univariate: one variable at a time (frequencies, histogram, boxplot)."),
                     tx("Bivariado y multivariado: relaciones entre dos o más variables (correlaciones, tablas cruzadas, "
                        "dispersión, comparación por grupos).",
                        "Bivariate and multivariate: relationships between two or more variables (correlations, "
                        "cross tables, scatter plots, group comparisons).")]),
            ]),
            card(tx("4. Estadística descriptiva y valores atípicos", "4. Descriptive statistics and outliers"), [
                html.P(tx("La asimetría (skewness) indica hacia dónde se alarga la cola de una distribución; la curtosis, "
                          "qué tan pesadas son sus colas. Los montos de dinero suelen ser muy asimétricos.",
                          "Skewness indicates which way a distribution's tail stretches; kurtosis, how heavy its tails "
                          "are. Money amounts are usually highly skewed.")),
                F(r"\begin{gathered} x < Q_1 - 1.5\,\mathrm{IQR} \quad \text{" + tx("ó", "or")
                  + r"} \quad x > Q_3 + 1.5\,\mathrm{IQR} \\ \mathrm{IQR} = Q_3 - Q_1 \end{gathered}"),
                html.P(tx("La winsorización recorta los extremos a percentiles (por ejemplo P1 a P99) sin eliminar clientes. "
                          "La transformación logarítmica con signo suaviza colas largas cuando hay ceros o negativos.",
                          "Winsorization caps the extremes at percentiles (e.g. P1 to P99) without removing clients. "
                          "The signed log transformation smooths long tails when there are zeros or negatives.")),
            ]),
            card(tx("5. Desbalance de clases", "5. Class imbalance"), [
                html.P(tx("Cuando una clase es mucho menos frecuente, un clasificador puede lograr alta exactitud "
                          "ignorándola. Por eso se recomienda:",
                          "When one class is much less frequent, a classifier can achieve high accuracy by ignoring "
                          "it. That is why it is recommended to:")),
                _ul([tx("Ponderar las clases (class_weight) o sobremuestrear la minoritaria (SMOTE, ADASYN) [5], [6].",
                        "Weight the classes (class_weight) or oversample the minority (SMOTE, ADASYN) [5], [6]."),
                     tx("Ajustar el umbral de decisión.", "Adjust the decision threshold."),
                     tx("Evaluar con AUC-ROC, PR-AUC, F1 y recall de la clase minoritaria en lugar de accuracy [8].",
                        "Evaluate with ROC-AUC, PR-AUC, F1 and minority-class recall instead of accuracy [8].")]),
            ]),
            card(tx("6. Correlación de Spearman y multicolinealidad", "6. Spearman correlation and multicollinearity"), [
                F(r"\begin{aligned} \rho_s &= r\big(" + rank + r"(X),\, " + rank + r"(Y)\big) \\ "
                  r"&= 1 - \frac{6 \sum d_i^2}{n\,(n^2 - 1)} \end{aligned}"),
                html.P(tx("La segunda forma vale cuando no hay empates (dᵢ es la diferencia de rangos de cada cliente).",
                          "The second form holds when there are no ties (dᵢ is each client's rank difference).")),
                html.P(tx("Spearman (1904) mide asociación monótona usando los rangos de los datos. No exige linealidad "
                          "ni normalidad y resiste los valores extremos. Se eligió sobre Pearson porque los montos "
                          "(BILL_AMT, PAY_AMT) son muy asimétricos y con colas largas, las variables PAY_x son ordinales "
                          "y la variable objetivo es binaria.",
                          "Spearman (1904) measures monotonic association using the ranks of the data. It requires "
                          "neither linearity nor normality and is robust to extreme values. It was chosen over Pearson "
                          "because the amounts (BILL_AMT, PAY_AMT) are highly skewed with long tails, the PAY_x "
                          "variables are ordinal and the target is binary.")),
                F(r"\mathrm{VIF}_j = \frac{1}{1 - R_j^2}"),
                html.P(tx("Hay multicolinealidad cuando las predictoras son casi redundantes: se inflan las varianzas de "
                          "los coeficientes. Un VIF > 10 (algunos autores usan > 5) es señal de alerta.",
                          "Multicollinearity occurs when predictors are nearly redundant: the variances of the "
                          "coefficients are inflated. A VIF > 10 (some authors use > 5) is a warning sign.")),
            ]),
            card(tx("7. Asociación entre variables categóricas", "7. Association between categorical variables"), [
                html.P(tx("La prueba χ² de independencia contrasta si dos variables categóricas están asociadas. Su "
                          "tamaño de efecto se mide con la V de Cramér, que va de 0 a 1:",
                          "The χ² test of independence checks whether two categorical variables are associated. Its "
                          "effect size is measured with Cramér's V, which ranges from 0 to 1:")),
                F(r"V = \sqrt{\frac{\chi^2}{n \cdot \min(r - 1,\; c - 1)}}"),
                html.P(tx("Como regla orientativa, V < 0.1 es un efecto pequeño y V ≈ 0.3 uno moderado.",
                          "As a rule of thumb, V < 0.1 is a small effect and V ≈ 0.3 a moderate one.")),
            ]),
            card(tx("8. Comparación de grupos y tamaño del efecto", "8. Group comparison and effect size"), [
                _ul([tx("Mann-Whitney U: compara dos grupos sin suponer normalidad.",
                        "Mann-Whitney U: compares two groups without assuming normality."),
                     tx("Kruskal-Wallis H: extiende la comparación a tres o más grupos.",
                        "Kruskal-Wallis H: extends the comparison to three or more groups."),
                     tx("t de Welch: compara medias con varianzas distintas.",
                        "Welch's t: compares means with unequal variances.")]),
                F(r"U_1 = R_1 - \frac{n_1 (n_1 + 1)}{2}"),
                F(r"H = \frac{12}{N (N + 1)} \sum_{g} \frac{R_g^2}{n_g} - 3 (N + 1)"),
                F(r"t = \frac{\bar{x}_1 - \bar{x}_2}{\sqrt{\dfrac{s_1^2}{n_1} + \dfrac{s_2^2}{n_2}}}"),
                html.P(tx("Con n ≈ 30 000 casi cualquier diferencia resulta significativa; por eso se reporta el tamaño del "
                          "efecto y la relevancia práctica, no solo el p-value.",
                          "With n ≈ 30,000 almost any difference is significant; that is why the effect size and "
                          "practical relevance are reported, not just the p-value.")),
            ]),
            card(tx("9. Calibración de probabilidades", "9. Probability calibration"), [
                html.P(tx("Un modelo está calibrado si, entre los clientes a los que asigna 30 % de riesgo, cerca del 30 % "
                          "incumple. Ordenar bien (AUC) no basta: los pesos de clase y el sobremuestreo inflan las "
                          "probabilidades de la clase minoritaria. Se miden con el puntaje de Brier y el error de "
                          "calibración esperado (ECE):",
                          "A model is calibrated if, among the clients it assigns a 30% risk, about 30% default. Ranking "
                          "well (AUC) is not enough: class weights and oversampling inflate the minority-class "
                          "probabilities. Calibration is measured with the Brier score and the expected calibration "
                          "error (ECE):")),
                F(r"\mathrm{Brier} = \frac{1}{n} \sum_{i=1}^{n} (\hat p_i - y_i)^2"),
                F(r"\mathrm{ECE} = \sum_{b=1}^{B} \frac{n_b}{n} \,\big|\, \bar y_b - \bar p_b \,\big|"),
                html.P(tx("En el ECE las probabilidades se agrupan en B intervalos (10 en este proyecto); ȳ_b es la tasa "
                          "real de incumplimiento y p̄_b la probabilidad media en el intervalo b. En ambos, menor es mejor. "
                          "La página Modelos reporta el ECE del mejor modelo y la página Modelo original compara el Brier "
                          "de los tres mejores.",
                          "In the ECE, probabilities are grouped into B bins (10 in this project); ȳ_b is the real default "
                          "rate and p̄_b the mean probability in bin b. For both, lower is better. The Models page reports "
                          "the best model's ECE and the Original model page compares the Brier score of the top three.")),
            ]),
        ], className="masonry"),
        html.Div([
            card(tx("Antecedentes", "Background"), [
                html.P(tx("Yeh y Lien (2009) [1] compararon seis técnicas de minería de datos (regresión logística, análisis "
                          "discriminante, k vecinos, Naive Bayes, redes neuronales y árboles de clasificación) para "
                          "predecir el incumplimiento con estos mismos datos, y propusieron un método de suavizado por "
                          "ordenamiento (Sorting Smoothing Method) para estimar la probabilidad real de incumplimiento.",
                          "Yeh and Lien (2009) [1] compared six data mining techniques (logistic regression, discriminant "
                          "analysis, k-nearest neighbors, Naive Bayes, neural networks and classification trees) to "
                          "predict default with this same data, and proposed the Sorting Smoothing Method to estimate "
                          "the real probability of default.")),
                html.P(tx("La sección Modelos retoma esa comparación con siete clasificadores, cuatro técnicas de "
                          "balanceo y cuatro métodos de optimización de hiperparámetros, y la amplía con "
                          "un modelo original propuesto en este proyecto (CS-FOF).",
                          "The Models section revisits that comparison with seven classifiers, four balancing "
                          "techniques and four hyperparameter optimization methods, and extends it with "
                          "an original model proposed in this project (CS-FOF).")),
            ]),
        ], className="grid"),
        card(tx("Diccionario de variables", "Variable dictionary"),
             _tbl(["Variable", tx("Tipo", "Type"), tx("Descripción", "Description")],
                  [(html.Code(v), t, d) for v, t, d in var_table])),
        html.Details([html.Summary([icon("book"), f"{tx('Referencias', 'References')} ({len(refs)})"]),
                      html.Div([dcc.Markdown(r, link_target="_blank", className="ref-item") for r in refs],
                               className="refs ieee")], className="card fold"),
    ])
