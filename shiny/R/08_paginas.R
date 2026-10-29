# =============================================================================
# 8. PÁGINAS
# =============================================================================

md_html <- function(txt) {   # Markdown -> HTML (enlaces en pestaña nueva)
  h <- commonmark::markdown_html(txt, extensions = TRUE)
  HTML(gsub("<a href=", "<a target=\"_blank\" rel=\"noopener noreferrer\" href=", h, fixed = TRUE))
}
formula_ <- function(tex) div(class = "formula", paste0("$$\\displaystyle ", tex, "$$"))

# ---------------------------------------------------------------- Portada
stat_ <- function(label, value) div(class = "sig-stat", tags$span(label), tags$b(value))

page_home <- function() {
  front <- div(class = "cc-face cc-front",
    div(class = "cc-gloss"),
    div(class = "cc-top", tags$span(class = "cc-brand", tx("Riesgo de crédito", "Credit risk")), icon_("contactless", "cc-nfc")),
    div(class = "cc-chip"),
    div(class = "cc-number", "•••• •••• •••• 2005"),
    div(class = "cc-bottom",
        div(tags$span(class = "cc-lbl", tx("Titulares", "Cardholders")), lapply(AUTHORS, function(a) div(class = "cc-name", a$name))),
        div(class = "cc-valid", tags$span(class = "cc-lbl", tx("Periodo de datos", "Data period")),
            div(class = "cc-name", tx("ABR 2005 – SEP 2005", "APR 2005 – SEP 2005")))))
  back <- div(class = "cc-face cc-back",
    div(class = "cc-gloss"), div(class = "cc-mag"),
    div(class = "cc-sig", stat_(tx("Clientes", "Clients"), num(nrow(df))), stat_("Default", pct(GLOBAL_RATE)),
        stat_(tx("Periodo", "Period"), tx("Abr–Sep 2005", "Apr–Sep 2005"))),
    tags$p(class = "cc-fine", tx("Datos: UCI · Banco de Taiwán · Yeh & Lien (2009)", "Data: UCI · Taiwanese bank · Yeh & Lien (2009)")))
  card3d <- div(id = "cc", class = "cc", tabindex = "0",
                `aria-label` = tx("Tarjeta del proyecto. Púlsala para voltearla", "Project card. Press it to flip it"),
                div(class = "cc-inner", front, back))
  div(class = "cover",
      div(class = "bill-bg"),
      div(class = "cover-hero",
          div(class = "cc-scene", div(class = "cc-settle", card3d)),
          div(class = "cover-copy",
              div(class = "cover-tag", icon_("card"), tx("Proyecto EDA", "EDA Project")),
              tags$h1(L(PROJECT_TITLE)),
              tags$p(class = "hero-lead",
                     tx(sprintf("Quién deja de pagar el mes siguiente y qué señales lo anticipan: %s clientes de tarjeta de crédito de un banco de Taiwán, de abril a septiembre de 2005.", num(nrow(df))),
                        sprintf("Who stops paying the following month and which signals anticipate it: %s credit card clients of a Taiwanese bank, from April to September 2005.", num(nrow(df))))),
              tags$a(class = "btn primary big", href = "#/introduccion", tx("Iniciar recorrido", "Start the tour"), icon_("arrow")),
              div(class = "cover-hint", tags$span(tx("Haz clic o toca la tarjeta para voltearla.", "Click or tap the card to flip it.")),
                  tags$span(L(INSTITUTION))))))
}

fig_home <- function() {
  r <- tapply(df[[TARGET]], df$PAY_0, mean); n <- tapply(df[[TARGET]], df$PAY_0, length)
  ok <- n >= 100; r <- r[ok]; n <- n[ok]
  p <- plot_ly(x = fx(names(r)), y = as.numeric(r) * 100, type = "bar", marker = list(color = MONO), customdata = as.numeric(n),
               hovertemplate = paste0("PAY_0 = %{x}<br>Default: %{y:.1f}%<br>", tx("Clientes", "Clients"), ": %{customdata:,}<extra></extra>"))
  p <- layout(p, showlegend = FALSE,
              xaxis = list(title = tx("Estado de pago en septiembre (PAY_0)", "September repayment status (PAY_0)"), type = "category"),
              yaxis = list(title = tx("% que incumple el mes siguiente", "% defaulting the next month")),
              shapes = list(hline(GLOBAL_RATE * 100, color = WARM_GOLD)),
              annotations = list(nota(tx(paste("Tasa global", pct(GLOBAL_RATE)), paste("Overall rate", pct(GLOBAL_RATE))),
                                      0, GLOBAL_RATE * 100, color = WARM_GOLD)))
  style_fig(p, 310, legend_top = FALSE, margin = list(l = 55, r = 20, t = 24, b = 55))
}

quick_look <- function() {
  r_late <- mean(df[[TARGET]][df$PAY_0 >= 2]); r_ok <- mean(df[[TARGET]][df$PAY_0 <= 0])
  card(tx("Vistazo rápido: el atraso de septiembre anticipa el incumplimiento", "Quick look: September's delay anticipates default"),
       grafica("home_graph", 310),
       tags$p(class = "muted", tx(sprintf("Entre quienes tenían 2 o más meses de atraso en septiembre, %s incumplió el mes siguiente; entre quienes iban al día o pagaban el mínimo, %s.", pct(r_late, 0), pct(r_ok, 0)),
                                  sprintf("Among those 2 or more months late in September, %s defaulted the following month; among those up to date or paying the minimum, %s.", pct(r_late, 0), pct(r_ok, 0)))))
}

# ---------------------------------------------------------------- Introducción
page_intro <- function() {
  I <- DATA_INFO; best_lbl <- minfo(BEST$model, "label"); tech <- tolower(tech_lbl(BEST$technique))
  tagList(
    page_title(tx("Introducción", "Introduction")),
    quick_look(),
    div(class = "kpi-row k4",
        kpi(tx("Clientes analizados", "Clients analyzed"), num(nrow(df)), tx("tras la limpieza", "after cleaning"), "users"),
        kpi("Variables", "24", tx("23 predictoras + 1 objetivo", "23 predictors + 1 target"), "columns"),
        kpi(tx("Tasa de default", "Default rate"), pct(GLOBAL_RATE), paste(num(N_DEF), tx("clientes", "clients")), "alert"),
        kpi(tx("Periodo", "Period"), tx("Abr–Sep 2005", "Apr–Sep 2005"), tx("banco de Taiwán", "Taiwanese bank"), "calendar")),
    div(class = "grid g3 intro-grid",
        card(tx("Introducción", "Introduction"), cls = "span-2",
             tags$p(tx("Las tarjetas de crédito son una de las líneas de la banca minorista con mayor exposición al riesgo: cada cliente recibe un cupo (límite de crédito) y se espera que lo pague en las fechas pactadas. Cuando no lo hace, la entidad enfrenta pérdidas, mayores costos de cobranza y la necesidad de provisionar capital.",
                       "Credit cards are one of the retail banking lines with the highest risk exposure: each client receives a limit and is expected to repay it on the agreed dates. When they do not, the bank faces losses, higher collection costs and the need to set aside capital.")),
             tags$p(tx(sprintf("Este tablero recorre el proyecto completo con el conjunto Default of Credit Card Clients (UCI): %s clientes observados entre abril y septiembre de 2005, de quienes se conoce su límite de crédito, sus datos demográficos, seis meses de historial de pagos, los montos facturados y pagados, y si incumplieron el pago del mes siguiente.", num(I$filas_originales)),
                       sprintf("This dashboard walks through the whole project using the Default of Credit Card Clients dataset (UCI): %s clients observed between April and September 2005, with their credit limit, demographics, six-month payment history, billed and paid amounts, and whether they defaulted the following month.", num(I$filas_originales)))),
             tags$p(tx(sprintf("Primero se exploran los datos (EDA univariado y multivariado) para entender qué variables anticipan el incumplimiento. Luego se entrenan y comparan %d combinaciones de modelos (7 algoritmos × 4 técnicas de balanceo × 4 optimizadores). La mejor, %s con %s, logra un F1 de %.3f y detecta el %s de los incumplimientos. Por último, la página Predecir usa ese modelo para estimar el riesgo de un cliente nuevo.",
                               nrow(MR), best_lbl, tech, BEST$f1_mean, pct(BEST$recall_mean, 0)),
                       sprintf("First the data is explored (univariate and multivariate EDA) to see which variables anticipate default. Then %d model combinations are trained and compared (7 algorithms × 4 balancing techniques × 4 optimizers). The best one, %s with %s, reaches an F1 of %.3f and detects %s of defaults. Finally, the Predict page uses that model to estimate the risk of a new client.",
                               nrow(MR), best_lbl, tech, BEST$f1_mean, pct(BEST$recall_mean, 0)))),
             tags$p(tx("Cada gráfico trae una interpretación básica (lenguaje cotidiano) y una técnica (estadísticos y recomendaciones de modelado).",
                       "Each chart comes with a basic interpretation (everyday language) and a technical one (statistics and modeling recommendations)."))),
        card(tx("Fuentes", "Sources"),
             tags$p("Yeh, I-C. & Lien, C. (2009). The comparisons of data mining techniques for the predictive accuracy of probability of default of credit card clients. Expert Systems with Applications, 36(2), 2473–2480."),
             tags$p(tx("Datos: ", "Data: "), tags$a(href = DATA_URL, target = "_blank", rel = "noopener", "UCI Machine Learning Repository")),
             tags$p(tx("Cifras monetarias en dólares taiwaneses (NT$).", "Monetary figures in New Taiwan dollars (NT$).")),
             ul_(list(tx(paste(num(I$filas_originales), "clientes de un banco de Taiwán"), paste(num(I$filas_originales), "clients of a Taiwanese bank")),
                      tx("23 variables explicativas y 1 objetivo", "23 explanatory variables and 1 target"),
                      tx("Seis meses de historia: abril a septiembre de 2005", "Six months of history: April to September 2005"))))))
}

# ---------------------------------------------------------------- Problema y objetivos
page_problem <- function() {
  exposure <- sum(df$LIMIT_BAL[df[[TARGET]] == 1]); bill_def <- sum(pmax(df$BILL_AMT1[df[[TARGET]] == 1], 0))
  hip <- list(
    list("H1", tx("El historial reciente de pagos (PAY_0 … PAY_6) es el factor más fuertemente asociado al incumplimiento.",
                  "Recent payment history (PAY_0 … PAY_6) is the factor most strongly associated with default."),
         tx("Multivariado · Matriz de correlación", "Multivariate · Correlation matrix")),
    list("H2", tx("Los clientes con menor límite de crédito (LIMIT_BAL) presentan una mayor tasa de default.",
                  "Clients with a lower credit limit (LIMIT_BAL) have a higher default rate."),
         tx("Multivariado · Límite según default", "Multivariate · Limit by default")),
    list("H3", tx("Las variables demográficas (sexo, educación, estado civil, edad) se asocian con el default, pero con un tamaño de efecto pequeño.",
                  "Demographic variables (sex, education, marital status, age) are associated with default, but with a small effect size."),
         tx("Multivariado · Tasas por perfil y edad", "Multivariate · Rates by profile and age")),
    list("H4", tx("Los montos facturados mensuales (BILL_AMT1–6) están fuertemente correlacionados entre sí (multicolinealidad).",
                  "Monthly bill amounts (BILL_AMT1–6) are strongly correlated with each other (multicollinearity)."),
         tx("Univariado y Multivariado", "Univariate and Multivariate")),
    list("H5", tx("La clase «default» es minoritaria, por lo que el problema presenta desbalance de clases.",
                  "The “default” class is the minority, so the problem has class imbalance."),
         tx("Univariado · Variable objetivo", "Univariate · Target variable")))
  objs <- list(
    list(tx("Describir la calidad de los datos y documentar la limpieza aplicada (duplicados, categorías no documentadas, saldos negativos).",
            "Describe data quality and document the cleaning applied (duplicates, undocumented categories, negative balances)."), tx("Introducción", "Introduction")),
    list(tx("Caracterizar la distribución de cada variable, su asimetría y la presencia de valores atípicos.",
            "Characterize the distribution of each variable, its skewness and the presence of outliers."), tx("EDA Univariado", "Univariate EDA")),
    list(tx("Cuantificar el desbalance de clases de la variable objetivo.", "Quantify the class imbalance of the target variable."), tx("EDA Univariado", "Univariate EDA")),
    list(tx("Comparar a los clientes con y sin default según variables demográficas, de crédito y de pagos.",
            "Compare clients with and without default by demographic, credit and payment variables."), tx("EDA Multivariado", "Multivariate EDA")),
    list(tx("Identificar relaciones entre variables y detectar multicolinealidad (correlaciones, VIF).",
            "Identify relationships between variables and detect multicollinearity (correlations, VIF)."), tx("EDA Multivariado", "Multivariate EDA")),
    list(tx("Definir lineamientos de preprocesamiento para una futura etapa de modelado predictivo.",
            "Define preprocessing guidelines for a future predictive modeling stage."), tx("Hallazgos clave", "Key findings")))
  tagList(
    page_title(tx("Problema y Objetivos", "Problem and Objectives")),
    div(class = "grid g3",
        card(tx("Planteamiento del problema", "Problem statement"), cls = "span-2",
             tags$p(tx("Una entidad financiera otorga crédito sin saber con certeza quién pagará. Si concede cupos demasiado altos a clientes que luego incumplen, la cartera se deteriora: se pierde el capital no recuperado, aumentan los costos de cobranza y se deben constituir mayores provisiones. Si, por el contrario, restringe el crédito en exceso, pierde ingresos por intereses y comisiones.",
                       "A financial institution grants credit without knowing for sure who will pay. If it grants limits that are too high to clients who later default, the portfolio deteriorates: unrecovered capital is lost, collection costs rise and larger provisions must be set aside. If, on the other hand, it restricts credit too much, it loses interest and fee income.")),
             tags$p(tx(sprintf("En esta muestra, %s de los clientes (%s) no pagó su tarjeta el mes siguiente. Identificar tempranamente qué perfiles y comportamientos anticipan ese incumplimiento es la base para fijar límites, priorizar la cobranza preventiva y alimentar un modelo de scoring.", pct(GLOBAL_RATE), num(N_DEF)),
                       sprintf("In this sample, %s of clients (%s) did not pay their card the following month. Identifying early which profiles and behaviors anticipate that default is the basis for setting limits, prioritizing preventive collection and feeding a scoring model.", pct(GLOBAL_RATE), num(N_DEF)))),
             div(class = "kpi-row k3",
                 kpi(tx("Clientes en default", "Clients in default"), num(N_DEF), tx(paste(pct(GLOBAL_RATE), "de la muestra"), paste(pct(GLOBAL_RATE), "of the sample"))),
                 kpi(tx("Límite expuesto", "Exposed limit"), sprintf("NT$%s M", num(exposure / 1e6)), tx("suma de LIMIT_BAL de quienes incumplen", "sum of LIMIT_BAL of defaulters")),
                 kpi(tx("Saldo facturado (Sep)", "Billed balance (Sep)"), sprintf("NT$%s M", num(bill_def / 1e6)), tx("BILL_AMT1 positivo de quienes incumplen", "positive BILL_AMT1 of defaulters"))),
             tags$p(class = "muted", tx("Los errores no son simétricos: no detectar a quien incumplirá (falso negativo) suele costar más que revisar de más a quien sí pagaría (falso positivo).",
                                        "Errors are not symmetric: failing to detect someone who will default (false negative) usually costs more than over-reviewing someone who would pay (false positive)."))),
        card(tx("Pregunta de investigación", "Research question"),
             div(class = "callout", tx("¿Qué características del cliente, de su línea de crédito y de su historial reciente de pagos se asocian con el incumplimiento del mes siguiente, y con qué intensidad?",
                                       "Which characteristics of the client, their credit line and their recent payment history are associated with default the following month, and how strongly?")),
             tags$p(tags$b(tx("Preguntas específicas", "Specific questions"))),
             ul_(list(tx("¿Cómo se distribuyen las variables y qué problemas de calidad presentan?", "How are the variables distributed and what quality issues do they have?"),
                      tx("¿Qué tan desbalanceada está la variable objetivo?", "How imbalanced is the target variable?"),
                      tx("¿Qué variables separan mejor a los clientes que incumplen?", "Which variables best separate the clients who default?"),
                      tx("¿Existe redundancia entre las variables predictoras?", "Is there redundancy among the predictor variables?"))))),
    div(class = "grid g2",
        card(tx("Justificación", "Rationale"),
             tags$p(tx("Un EDA riguroso evita errores costosos en el modelado: revela datos mal codificados, variables redundantes, sesgos de muestreo y desbalance antes de que afecten al modelo.",
                       "A rigorous EDA prevents costly modeling mistakes: it reveals miscoded data, redundant variables, sampling biases and imbalance before they affect the model.")),
             tags$p(tx("Además permite explicar a perfiles no técnicos (riesgos, cobranza, gerencia) qué señales preceden al incumplimiento, con evidencia visual y estadística.",
                       "It also makes it possible to explain to non-technical audiences (risk, collections, management) which signals precede default, with visual and statistical evidence."))),
        card(tx("Alcance y limitaciones", "Scope and limitations"), ul_(list(
          tx("Datos de un solo banco de Taiwán y de un periodo corto (abril–septiembre de 2005): no se generalizan sin cautela a otros mercados o épocas.",
             "Data from a single Taiwanese bank over a short period (April–September 2005): they should not be generalized to other markets or times without caution."),
          tx("El análisis es asociativo; una correlación no implica causalidad.", "The analysis is associative; correlation does not imply causation."),
          tx("El EDA no construye modelos: deriva lineamientos para hacerlo. Los modelos se entrenan en el repositorio del proyecto y sus resultados se resumen en la sección Modelos.",
             "The EDA does not build models: it derives guidelines for doing so. The models are trained in the project repository and their results are summarized in the Models section."),
          tx("Los códigos −2 y 0 de PAY_x no están documentados con precisión en la fuente; se conservan sin recodificar.",
             "Codes −2 and 0 of PAY_x are not precisely documented in the source; they are kept without recoding."))))),
    card(tx("Hipótesis exploratorias", "Exploratory hypotheses"),
         tbl_(list("#", tx("Hipótesis", "Hypothesis"), tx("Dónde se evalúa", "Where it is assessed")),
              lapply(hip, function(h) list(tags$b(h[[1]]), h[[2]], h[[3]])))),
    card(tx("Objetivos", "Objectives"),
         div(class = "obj-label", tx("Objetivo general", "General objective")),
         div(class = "callout", tx("Analizar los factores que se asocian con el incumplimiento de pago (default) de los clientes de tarjetas de crédito mediante un análisis exploratorio de datos univariado y multivariado.",
                                   "Analyze the factors associated with payment default among credit card clients through a univariate and multivariate exploratory data analysis.")),
         div(class = "obj-label", tx("Objetivos específicos", "Specific objectives")),
         tags$ol(class = "obj-list", lapply(objs, function(o) tags$li(o[[1]], tags$span(class = "tag", o[[2]]))))))
}

# ---------------------------------------------------------------- Marco teórico
REFS <- c(
  "[1] I.-C. Yeh y C.-H. Lien, “The comparisons of data mining techniques for the predictive accuracy of probability of default of credit card clients,” *Expert Systems with Applications*, vol. 36, no. 2, pp. 2473-2480, 2009, doi: 10.1016/j.eswa.2007.12.020.",
  "[2] UCI Machine Learning Repository, “Default of Credit Card Clients,” conjunto de datos. [En línea]. Disponible: <https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients>. Consultado: 28 oct. 2026. Repositorio; excepción al filtro temporal.",
  "[3] S. M. Lundberg y S.-I. Lee, “A unified approach to interpreting model predictions,” en *Advances in Neural Information Processing Systems*, vol. 30, 2017, pp. 4765-4774.",
  "[4] N. Bussmann, P. Giudici, D. Marinelli y J. Papenbrock, “Explainable machine learning in credit risk management,” *Computational Economics*, vol. 57, pp. 203-216, 2021; publicación en línea, 2020, doi: 10.1007/s10614-020-10042-0.",
  "[5] P. Branco, L. Torgo y R. P. Ribeiro, “A survey of predictive modeling on imbalanced domains,” *ACM Computing Surveys*, vol. 49, no. 2, art. 31, 2016, doi: 10.1145/2907070.",
  "[6] A. Fernández, S. García, F. Herrera y N. V. Chawla, “SMOTE for learning from imbalanced data: Progress and challenges, marking the 15-year anniversary,” *Journal of Artificial Intelligence Research*, vol. 61, pp. 863-905, 2018, doi: 10.1613/jair.1.11192.",
  "[7] G. James, D. Witten, T. Hastie y R. Tibshirani, *An Introduction to Statistical Learning: With Applications in R*, 2.ª ed. Springer, 2021, doi: 10.1007/978-1-0716-1418-1.",
  "[8] M. B. A. McDermott, L. H. Hansen, H. Zhang, G. Angelotti y J. Gallifant, “A closer look at AUROC and AUPRC under class imbalance,” arXiv:2401.06091, versión 2, 2024. Prepublicación. [En línea]. Disponible: <https://arxiv.org/abs/2401.06091>.",
  "[9] T. Chen y C. Guestrin, “XGBoost: A scalable tree boosting system,” en *Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining*, 2016, pp. 785-794, doi: 10.1145/2939672.2939785.")

page_marco <- function() {
  var_table <- list(
    list("LIMIT_BAL", tx("Numérica continua", "Continuous numeric"), tx("Monto del crédito otorgado (individual + familiar/suplementario) en dólares taiwaneses (NT$).", "Amount of credit granted (individual + family/supplementary) in New Taiwan dollars (NT$).")),
    list("SEX", tx("Categórica", "Categorical"), tx("Género: 1 = hombre, 2 = mujer.", "Gender: 1 = male, 2 = female.")),
    list("EDUCATION", tx("Categórica ordinal", "Ordinal categorical"), tx("1 = posgrado, 2 = universidad, 3 = secundaria, 4 = otros (los códigos 0, 5 y 6 no documentados se reagrupan en «Otros»).", "1 = graduate school, 2 = university, 3 = high school, 4 = others (undocumented codes 0, 5 and 6 are grouped into “Others”).")),
    list("MARRIAGE", tx("Categórica", "Categorical"), tx("Estado civil: 1 = casado, 2 = soltero, 3 = otros (el código 0 se reagrupa en «Otros»).", "Marital status: 1 = married, 2 = single, 3 = others (code 0 is grouped into “Others”).")),
    list("AGE", tx("Numérica discreta", "Discrete numeric"), tx("Edad en años.", "Age in years.")),
    list("PAY_0, PAY_2–PAY_6", "Ordinal", tx("Estado de pago mensual de septiembre (PAY_0) hacia abril (PAY_6). −2/−1/0 = sin atraso; 1 = un mes de atraso; …; 8–9 = ≥8–9 meses.", "Monthly repayment status from September (PAY_0) back to April (PAY_6). −2/−1/0 = no delay; 1 = one month late; …; 8–9 = ≥8–9 months.")),
    list("BILL_AMT1–6", tx("Numérica continua", "Continuous numeric"), tx("Monto facturado en el estado de cuenta de septiembre (1) a abril (6), en NT$. Puede ser negativo (saldo a favor).", "Amount on the bill statement from September (1) to April (6), in NT$. It can be negative (credit balance).")),
    list("PAY_AMT1–6", tx("Numérica continua", "Continuous numeric"), tx("Monto efectivamente pagado de septiembre (1) a abril (6), en NT$.", "Amount actually paid from September (1) to April (6), in NT$.")),
    list("default_payment_next_month", tx("Binaria (objetivo)", "Binary (target)"), tx("1 = el cliente incumple el pago el mes siguiente (octubre 2005); 0 = no incumple.", "1 = the client defaults the following month (October 2005); 0 = does not default.")))
  rank <- tx("\\mathrm{rango}", "\\mathrm{rank}")
  tagList(
    page_title(tx("Marco Teórico", "Theoretical Framework")),
    div(class = "masonry",
        card(tx("1. Riesgo de crédito y default", "1. Credit risk and default"),
             tags$p(tx("El riesgo de crédito es la posibilidad de que una entidad sufra pérdidas porque un deudor no cumple, total o parcialmente, sus obligaciones. En la regulación bancaria (Basilea II) la pérdida esperada se descompone así:",
                       "Credit risk is the possibility that an institution suffers losses because a debtor fails, fully or partially, to meet their obligations. In banking regulation (Basel II) expected loss is broken down as follows:")),
             formula_("\\mathrm{EL} = \\mathrm{PD} \\times \\mathrm{LGD} \\times \\mathrm{EAD}"),
             ul_(list(tx("PD: probabilidad de incumplimiento en un horizonte dado (lo que estudian estos datos).", "PD: probability of default over a given horizon (what these data study)."),
                      tx("LGD: porcentaje de la exposición que se pierde si hay incumplimiento.", "LGD: percentage of the exposure lost if there is a default."),
                      tx("EAD: monto expuesto en el momento del incumplimiento.", "EAD: amount exposed at the time of default."))),
             tags$p(tx("En este proyecto, default es la variable binaria que indica si el cliente no pagó en el mes siguiente.",
                       "In this project, default is the binary variable indicating whether the client did not pay the following month."))),
        card(tx("2. Scoring crediticio", "2. Credit scoring"),
             tags$p(tx("Los modelos de scoring estiman la PD a partir de variables del cliente: comportamiento de pago, límite, deuda y perfil demográfico. Sirven para aprobar o rechazar solicitudes, fijar cupos y priorizar la cobranza.",
                       "Scoring models estimate PD from client variables: payment behavior, limit, debt and demographic profile. They are used to approve or reject applications, set limits and prioritize collections.")),
             tags$p(tx("Antes de modelar, el EDA revela la calidad de los datos, las variables más informativas y los problemas (colinealidad, desbalance, atípicos) que condicionarán al modelo.",
                       "Before modeling, the EDA reveals data quality, the most informative variables and the issues (collinearity, imbalance, outliers) that will affect the model."))),
        card(tx("3. Análisis exploratorio de datos (EDA)", "3. Exploratory data analysis (EDA)"),
             tags$p(tx("Propuesto por John W. Tukey (1977): explorar los datos con resúmenes numéricos y gráficos, antes de ajustar modelos, para descubrir patrones, anomalías y supuestos.",
                       "Proposed by John W. Tukey (1977): explore the data with numerical summaries and charts, before fitting models, to discover patterns, anomalies and assumptions.")),
             ul_(list(tx("Univariado: una variable a la vez (frecuencias, histograma, boxplot).", "Univariate: one variable at a time (frequencies, histogram, boxplot)."),
                      tx("Bivariado y multivariado: relaciones entre dos o más variables (correlaciones, tablas cruzadas, dispersión, comparación por grupos).",
                         "Bivariate and multivariate: relationships between two or more variables (correlations, cross tables, scatter plots, group comparisons).")))),
        card(tx("4. Estadística descriptiva y valores atípicos", "4. Descriptive statistics and outliers"),
             tags$p(tx("La asimetría (skewness) indica hacia dónde se alarga la cola de una distribución; la curtosis, qué tan pesadas son sus colas. Los montos de dinero suelen ser muy asimétricos.",
                       "Skewness indicates which way a distribution's tail stretches; kurtosis, how heavy its tails are. Money amounts are usually highly skewed.")),
             formula_(paste0("\\begin{gathered} x < Q_1 - 1.5\\,\\mathrm{IQR} \\quad \\text{", tx("ó", "or"),
                             "} \\quad x > Q_3 + 1.5\\,\\mathrm{IQR} \\\\ \\mathrm{IQR} = Q_3 - Q_1 \\end{gathered}")),
             tags$p(tx("La winsorización recorta los extremos a percentiles (por ejemplo P1–P99) sin eliminar clientes. La transformación logarítmica con signo suaviza colas largas cuando hay ceros o negativos.",
                       "Winsorization caps the extremes at percentiles (e.g. P1–P99) without removing clients. The signed log transformation smooths long tails when there are zeros or negatives."))),
        card(tx("5. Desbalance de clases", "5. Class imbalance"),
             tags$p(tx("Cuando una clase es mucho menos frecuente, un clasificador puede lograr alta exactitud ignorándola. Por eso se recomienda:",
                       "When one class is much less frequent, a classifier can achieve high accuracy by ignoring it. That is why it is recommended to:")),
             ul_(list(tx("Ponderar las clases (class_weight) o sobremuestrear la minoritaria (SMOTE, ADASYN) [5], [6].", "Weight the classes (class_weight) or oversample the minority (SMOTE, ADASYN) [5], [6]."),
                      tx("Ajustar el umbral de decisión.", "Adjust the decision threshold."),
                      tx("Evaluar con AUC-ROC, PR-AUC, F1 y recall de la clase minoritaria en lugar de accuracy [8].", "Evaluate with ROC-AUC, PR-AUC, F1 and minority-class recall instead of accuracy [8].")))),
        card(tx("6. Correlación de Spearman y multicolinealidad", "6. Spearman correlation and multicollinearity"),
             formula_(paste0("\\begin{aligned} \\rho_s &= r\\big(", rank, "(X),\\, ", rank, "(Y)\\big) \\\\ &= 1 - \\frac{6 \\sum d_i^2}{n\\,(n^2 - 1)} \\end{aligned}")),
             tags$p(tx("La segunda forma vale cuando no hay empates (dᵢ es la diferencia de rangos de cada cliente).", "The second form holds when there are no ties (dᵢ is each client's rank difference).")),
             tags$p(tx("Spearman (1904) mide asociación monótona usando los rangos de los datos. No exige linealidad ni normalidad y resiste los valores extremos. Se eligió sobre Pearson porque los montos (BILL_AMT, PAY_AMT) son muy asimétricos y con colas largas, las variables PAY_x son ordinales y la variable objetivo es binaria.",
                       "Spearman (1904) measures monotonic association using the ranks of the data. It requires neither linearity nor normality and is robust to extreme values. It was chosen over Pearson because the amounts (BILL_AMT, PAY_AMT) are highly skewed with long tails, the PAY_x variables are ordinal and the target is binary.")),
             formula_("\\mathrm{VIF}_j = \\frac{1}{1 - R_j^2}"),
             tags$p(tx("Hay multicolinealidad cuando las predictoras son casi redundantes: se inflan las varianzas de los coeficientes. Un VIF > 10 (algunos autores usan > 5) es señal de alerta.",
                       "Multicollinearity occurs when predictors are nearly redundant: the variances of the coefficients are inflated. A VIF > 10 (some authors use > 5) is a warning sign."))),
        card(tx("7. Asociación entre variables categóricas", "7. Association between categorical variables"),
             tags$p(tx("La prueba χ² de independencia contrasta si dos variables categóricas están asociadas. Su tamaño de efecto se mide con la V de Cramér, que va de 0 a 1:",
                       "The χ² test of independence checks whether two categorical variables are associated. Its effect size is measured with Cramér's V, which ranges from 0 to 1:")),
             formula_("V = \\sqrt{\\frac{\\chi^2}{n \\cdot \\min(r - 1,\\; c - 1)}}"),
             tags$p(tx("Como regla orientativa, V < 0.1 es un efecto pequeño y V ≈ 0.3 uno moderado.", "As a rule of thumb, V < 0.1 is a small effect and V ≈ 0.3 a moderate one."))),
        card(tx("8. Comparación de grupos y tamaño del efecto", "8. Group comparison and effect size"),
             ul_(list(tx("Mann–Whitney U: compara dos grupos sin suponer normalidad.", "Mann–Whitney U: compares two groups without assuming normality."),
                      tx("Kruskal–Wallis H: extiende la comparación a tres o más grupos.", "Kruskal–Wallis H: extends the comparison to three or more groups."),
                      tx("t de Welch: compara medias con varianzas distintas.", "Welch's t: compares means with unequal variances."))),
             formula_("U_1 = R_1 - \\frac{n_1 (n_1 + 1)}{2}"),
             formula_("H = \\frac{12}{N (N + 1)} \\sum_{g} \\frac{R_g^2}{n_g} - 3 (N + 1)"),
             formula_("t = \\frac{\\bar{x}_1 - \\bar{x}_2}{\\sqrt{\\dfrac{s_1^2}{n_1} + \\dfrac{s_2^2}{n_2}}}"),
             tags$p(tx("Con n ≈ 30 000 casi cualquier diferencia resulta significativa; por eso se reporta el tamaño del efecto y la relevancia práctica, no solo el p-value.",
                       "With n ≈ 30,000 almost any difference is significant; that is why the effect size and practical relevance are reported, not just the p-value.")))),
    div(class = "grid",
        card(tx("Antecedentes", "Background"),
             tags$p(tx("Yeh y Lien (2009) [1] compararon seis técnicas de minería de datos (regresión logística, análisis discriminante, k vecinos, Naive Bayes, redes neuronales y árboles de clasificación) para predecir el incumplimiento con estos mismos datos, y propusieron un método de suavizado por ordenamiento (Sorting Smoothing Method) para estimar la probabilidad real de incumplimiento.",
                       "Yeh and Lien (2009) [1] compared six data mining techniques (logistic regression, discriminant analysis, k-nearest neighbors, Naive Bayes, neural networks and classification trees) to predict default with this same data, and proposed the Sorting Smoothing Method to estimate the real probability of default.")),
             tags$p(tx("La sección Modelos retoma esa comparación con siete clasificadores, cuatro técnicas de balanceo y cuatro métodos de optimización de hiperparámetros.",
                       "The Models section revisits that comparison with seven classifiers, four balancing techniques and four hyperparameter optimization methods.")))),
    card(tx("Diccionario de variables", "Variable dictionary"),
         tbl_(list("Variable", tx("Tipo", "Type"), tx("Descripción", "Description")),
              lapply(var_table, function(v) list(tags$code(v[[1]]), v[[2]], v[[3]])))),
    tags$details(class = "card fold",
                 tags$summary(icon_("book"), sprintf("%s (%d)", tx("Referencias", "References"), length(REFS))),
                 div(class = "refs ieee", lapply(REFS, function(r) div(class = "ref-item", md_html(r))))))
}

# ---------------------------------------------------------------- EDA univariado
page_uni <- function(sel = list()) {
  it <- interp_target()
  tagList(
    page_title(tx("EDA Univariado", "Univariate EDA")),
    div(class = "kpi-row k4",
        kpi(tx("Total de registros", "Total records"), num(nrow(df)), tx("tras eliminar duplicados", "after removing duplicates"), "users"),
        kpi(tx("Tasa global de default", "Overall default rate"), pct(GLOBAL_RATE), paste(num(N_DEF), tx("clientes", "clients")), "alert"),
        kpi(tx("Límite de crédito promedio", "Average credit limit"), nt(mean(df$LIMIT_BAL)), paste(tx("mediana", "median"), nt(stats::median(df$LIMIT_BAL))), "coin"),
        kpi(tx("Edad promedio", "Average age"), sprintf("%.1f %s", mean(df$AGE), tx("años", "years")), sprintf("%s %.0f", tx("mediana", "median"), stats::median(df$AGE)), "clock")),
    div(class = "grid g2",
        card(tx("Variable objetivo: Default vs. No Default", "Target variable: Default vs. No Default"),
             grafica("target_graph", 478), target_strip(), interp_block(it[[1]], it[[2]])),
        card(tx("Explorador univariado", "Univariate explorer"),
             div(class = "controls", control("Variable", selectInput("uni_var", NULL, var_choices(ALL_VARS), sel$uni_var %||% "LIMIT_BAL", width = "100%"))),
             grafica("uni_graph", 520), uiOutput("uni_interp"))),
    card(tx("Distribuciones de variables cuantitativas", "Distributions of quantitative variables"),
         div(class = "controls",
             control(tx("Variable / familia", "Variable / family"),
                     radio_("q_family", c("LIMIT_BAL" = "LIMIT_BAL", "AGE" = "AGE", "BILL_AMT (1–6)" = "BILL_AMT", "PAY_AMT (1–6)" = "PAY_AMT"),
                            sel$q_family %||% "LIMIT_BAL")),
             control(tx("Tipo de gráfico", "Chart type"),
                     radio_("q_kind", stats::setNames(c("hist", "box", "dens"), c(tx("Histograma", "Histogram"), "Boxplot", tx("Densidad", "Density"))),
                            sel$q_kind %||% "hist"))),
         grafica("q_graph", 480), uiOutput("q_interp")))
}

# ---------------------------------------------------------------- EDA multivariado
page_multi <- function(sel = list()) {
  findings <- lapply(key_findings(), function(f) div(class = "finding", div(class = "find-title", f[[1]]), tags$p(f[[2]])))
  ic <- interp_corr(); ir <- interp_rates(); il <- interp_limit()
  tagList(
    page_title(tx("EDA Multivariado", "Multivariate EDA")),
    card(tx("Matriz de correlación de Spearman", "Spearman correlation matrix"), grafica("corr_graph", 740), interp_block(ic[[1]], ic[[2]])),
    div(class = "grid g2",
        card(tx("Incumplimiento por educación, estado civil y sexo", "Default by education, marital status and sex"),
             grafica("rates_graph", 480), interp_block(ir[[1]], ir[[2]])),
        card(tx("Límite de crédito según estado de default", "Credit limit by default status"),
             div(class = "controls", control(tx("Escala del eje Y", "Y-axis scale"),
                 radio_("lim_scale", stats::setNames(c("linear", "log"), c(tx("Lineal", "Linear"), tx("Logarítmica", "Logarithmic"))), sel$lim_scale %||% "linear"))),
             grafica("lim_graph", 470), interp_block(il[[1]], il[[2]]))),
    card(tx("Edad y patrones de atraso en pagos (PAY_0 a PAY_6)", "Age and payment delay patterns (PAY_0 to PAY_6)"),
         div(class = "controls", control(tx("Vista", "View"),
             radio_("age_view", stats::setNames(c("lines", "heat", "rate"), c(tx("Atraso promedio por mes", "Average delay by month"),
                                                                             tx("% con atraso ≥ 1 mes", "% with delay ≥ 1 month"),
                                                                             tx("Tasa de default por edad", "Default rate by age"))), sel$age_view %||% "lines"))),
         grafica("age_graph", 470), uiOutput("age_interp")),
    card(tx("Módulo interactivo: cruce de variables", "Interactive module: variable cross"),
         div(class = "controls",
             control(tx("Variable X", "X variable"), selectInput("x_var", NULL, var_choices(ALL_VARS), sel$x_var %||% "EDUCATION", width = "100%")),
             control(tx("Variable Y", "Y variable"), selectInput("y_var", NULL, var_choices(ALL_VARS), sel$y_var %||% "LIMIT_BAL", width = "100%")),
             control(tx("Color / grupo (opcional)", "Color / group (optional)"),
                     selectInput("c_var", NULL, c(stats::setNames("none", tx("(ninguna)", "(none)")), var_choices(ALL_VARS)), sel$c_var %||% TARGET, width = "100%"))),
         grafica("x_graph", 520), uiOutput("x_interp")),
    card(tx("Matriz de dispersión: 2 o más variables numéricas", "Scatter matrix: 2 or more numeric variables"),
         div(class = "controls", control(tx("Variables (elige entre 2 y 6)", "Variables (choose 2 to 6)"),
             selectizeInput("s_vars", NULL, var_choices(NUM_COLS), sel$s_vars %||% c("LIMIT_BAL", "AGE", "PAY_0", "BILL_AMT1", "PAY_AMT1"),
                            multiple = TRUE, width = "100%", options = list(maxItems = 6)))),
         uiOutput("s_graph_box"), uiOutput("s_interp")),
    div(class = "findings", tags$h3(class = "section-h", tx("Hallazgos multivariados clave", "Key multivariate findings")),
        div(class = "grid g4", findings)))
}

# ---------------------------------------------------------------- Conclusiones
page_conclusions <- function() {
  rho <- CORR[, "default"]
  r_late <- mean(df[[TARGET]][df$PAY_0 >= 2])
  qs <- cut(df$LIMIT_BAL, breaks = unique(stats::quantile(df$LIMIT_BAL, 0:4 / 4)), include.lowest = TRUE)
  qr <- tapply(df[[TARGET]], qs, mean)
  med1 <- stats::median(df$LIMIT_BAL[df[[TARGET]] == 1]); med0 <- stats::median(df$LIMIT_BAL[df[[TARGET]] == 0])
  cv <- vapply(c(SEX = "SEX", EDUCATION = "EDUCATION", MARRIAGE = "MARRIAGE"), function(v) cramers_v(table(df[[v]], df[[TARGET]])), 0)
  bc <- triu(CORR[BILL_COLS, BILL_COLS])
  ratio <- (1 - GLOBAL_RATE) / GLOBAL_RATE
  c <- BEST_CM; pos <- c$tp + c$fn; flagged <- c$tp + c$fp
  best_lbl <- minfo(BEST$model, "label"); tech <- tolower(tech_lbl(BEST$technique))
  yes <- tags$span(class = "tag verdict", tx("Se cumple", "Supported"))
  hyp <- list(
    list("H1", tx("El historial reciente de pagos es el factor más asociado al default.", "Recent payment history is the factor most associated with default."), yes,
         tx(sprintf("PAY_0 tiene la correlación más alta con el default (ρ = %.2f), seguida de PAY_2–PAY_4. Con 2 o más meses de atraso en septiembre, el %s incumple.", rho[["PAY_0"]], pct(r_late, 0)),
            sprintf("PAY_0 has the highest correlation with default (ρ = %.2f), followed by PAY_2–PAY_4. With 2 or more months late in September, %s default.", rho[["PAY_0"]], pct(r_late, 0)))),
    list("H2", tx("A menor límite de crédito, mayor tasa de default.", "The lower the credit limit, the higher the default rate."), yes,
         tx(sprintf("La tasa baja de %s en el cuartil de límite más bajo a %s en el más alto. Mediana del límite: NT$%s (default) frente a NT$%s (paga); ρ = %.2f.", pct(qr[1], 0), pct(qr[length(qr)], 0), num(med1), num(med0), rho[["LIMIT_BAL"]]),
            sprintf("The rate drops from %s in the lowest limit quartile to %s in the highest. Median limit: NT$%s (default) vs NT$%s (pays); ρ = %.2f.", pct(qr[1], 0), pct(qr[length(qr)], 0), num(med1), num(med0), rho[["LIMIT_BAL"]]))),
    list("H3", tx("Las variables demográficas se asocian con el default, pero con efecto pequeño.", "Demographic variables are associated with default, but with a small effect."), yes,
         tx(sprintf("Diferencias significativas, pero V de Cramér ≤ %.2f (educación %.2f, sexo %.2f, estado civil %.2f). La edad casi no influye (ρ = %.3f).", max(cv), cv[["EDUCATION"]], cv[["SEX"]], cv[["MARRIAGE"]], rho[["AGE"]]),
            sprintf("Significant differences, but Cramér's V ≤ %.2f (education %.2f, sex %.2f, marital status %.2f). Age barely matters (ρ = %.3f).", max(cv), cv[["EDUCATION"]], cv[["SEX"]], cv[["MARRIAGE"]], rho[["AGE"]]))),
    list("H4", tx("Los montos facturados BILL_AMT1–6 son muy redundantes entre sí.", "Bill amounts BILL_AMT1–6 are highly redundant with each other."), yes,
         tx(sprintf("Correlaciones entre %.2f y %.2f entre meses y VIF mayor a 20 en BILL_AMT2–5: multicolinealidad severa.", min(bc), max(bc)),
            sprintf("Correlations between %.2f and %.2f across months and VIF above 20 for BILL_AMT2–5: severe multicollinearity.", min(bc), max(bc)))),
    list("H5", tx("La clase default es minoritaria (desbalance).", "The default class is the minority (imbalance)."), yes,
         tx(sprintf("Solo el %s incumple (%.1f : 1). Sin balanceo el F1 medio es 0.453; con pesos de clase sube a 0.526, así que corregir el desbalance era necesario.", pct(GLOBAL_RATE), ratio),
            sprintf("Only %s default (%.1f : 1). Without balancing the mean F1 is 0.453; with class weights it rises to 0.526, so correcting the imbalance was necessary.", pct(GLOBAL_RATE), ratio))))
  tagList(
    page_title(tx("Conclusiones", "Conclusions")),
    card(tx("Respuesta a la pregunta de investigación", "Answer to the research question"),
         div(class = "callout", tx("El incumplimiento del mes siguiente lo anticipa sobre todo el comportamiento de pago reciente: cuántos meses de atraso lleva el cliente, en especial en septiembre. Le sigue, con menos fuerza, el límite de crédito (a menor cupo, más riesgo). Los datos demográficos aportan muy poco.",
                                   "Next month's default is anticipated mainly by recent payment behavior: how many months late the client is, especially in September. It is followed, less strongly, by the credit limit (the lower the limit, the higher the risk). Demographics add very little.")),
         tags$p(tx(sprintf("Con esas señales, el mejor modelo (%s con %s) logra un F1 de %.3f y un ROC-AUC de %.2f: detecta el %s de los incumplimientos y, de cada dos clientes que marca como riesgo, uno realmente incumple.", best_lbl, tech, BEST$f1_mean, BEST$roc_auc_mean, pct(c$tp / pos, 0)),
                   sprintf("With those signals, the best model (%s with %s) reaches an F1 of %.3f and a ROC-AUC of %.2f: it detects %s of defaults and, out of every two clients it flags as risky, one actually defaults.", best_lbl, tech, BEST$f1_mean, BEST$roc_auc_mean, pct(c$tp / pos, 0)))),
         div(class = "kpi-row k3",
             kpi(tx("Señal más fuerte", "Strongest signal"), "PAY_0", tx(sprintf("ρ = %.2f con el default", rho[["PAY_0"]]), sprintf("ρ = %.2f with default", rho[["PAY_0"]])), "alert"),
             kpi(tx("Mejor modelo", "Best model"), sprintf("F1 %.3f", BEST$f1_mean), paste(best_lbl, "·", tech), "trophy"),
             kpi(tx("Incumplimientos detectados", "Defaults detected"), pct(c$tp / pos, 0), tx(paste(num(c$tp), "de", num(pos)), paste(num(c$tp), "of", num(pos))), "target"))),
    card(tx("Veredicto de las hipótesis", "Hypothesis verdicts"),
         tbl_(list("#", tx("Hipótesis", "Hypothesis"), tx("Veredicto", "Verdict"), tx("Evidencia", "Evidence")),
              lapply(hyp, function(h) list(tags$b(h[[1]]), h[[2]], h[[3]], h[[4]])))),
    div(class = "grid g2",
        card(tx("Qué significa para el banco", "What it means for the bank"), ul_(list(
          tx("Vigilar el atraso reciente como alerta temprana: un cliente con 2 o más meses de atraso merece cobranza preventiva antes del siguiente corte.",
             "Monitor recent delays as an early warning: a client 2 or more months late deserves preventive collection before the next billing cycle."),
          tx("Revisar con más cuidado los cupos bajos, donde se concentra la mayor tasa de incumplimiento.", "Review low limits more carefully, where the highest default rate is concentrated."),
          tx(sprintf("Usar el modelo como filtro, no como decisión final: marca a %s clientes y %s de ellos sí pagarían, así que la alerta debe pasar por un analista.", num(flagged), num(c$fp)),
             sprintf("Use the model as a filter, not as the final decision: it flags %s clients and %s of them would pay, so the alert should go through an analyst.", num(flagged), num(c$fp))),
          tx("No basar decisiones en sexo, edad o estado civil: aportan poco y crean riesgo de discriminación.",
             "Do not base decisions on sex, age or marital status: they add little and create a discrimination risk.")))),
        card(tx("Limitaciones y próximos pasos", "Limitations and next steps"), ul_(list(
          tx("Datos de un solo banco de Taiwán en 2005: antes de usarlo en otro mercado hay que reentrenarlo con datos actuales.",
             "Data from a single Taiwanese bank in 2005: before using it in another market it must be retrained with current data."),
          tx("El análisis es asociativo: muestra qué anticipa el default, no qué lo causa.", "The analysis is associative: it shows what anticipates default, not what causes it."),
          tx("El umbral está fijo en 0.5. Ajustarlo según el costo real de cada error (un incumplimiento no detectado cuesta más que una falsa alarma) mejoraría el uso práctico.",
             "The threshold is fixed at 0.5. Tuning it to the real cost of each error (a missed default costs more than a false alarm) would improve practical use."),
          tx("Sumar variables que hoy no están (ingresos, deudas en otras entidades) y vigilar que el modelo no pierda precisión con el tiempo.",
             "Add variables that are missing today (income, debts at other institutions) and monitor that the model does not lose accuracy over time."))))))
}

# ---------------------------------------------------------------- Enlaces
link_cards <- function(compact = FALSE) {
  div(class = "link-grid", lapply(LINKS, function(lk) {
    title <- L(lk$title)
    tags$a(class = "link-card", href = lk$url, target = "_blank", rel = "noopener noreferrer", title = paste0(tx("Abrir", "Open"), ": ", title),
           div(class = "lc-top", tags$span(class = "lc-ico", icon_(lk$icon)), icon_("external", "lc-ext")),
           div(class = "lc-title", title), if (!compact) tags$p(L(lk$desc)))
  }))
}
PIPE_ICONS <- c("00" = "receipt", "01" = "card", "02" = "pos", "03" = "chip", "04" = "wallet", "05" = "cardpay", "06" = "contactless")

page_links <- function() {
  tagList(
    page_title(tx("Enlaces", "Links")),
    card(tx("Sobre el proyecto", "About the project"),
         tags$p(tx("Flujo completo de ciencia de datos y aprendizaje automático para predecir el incumplimiento de pago en clientes de tarjetas de crédito, a partir de los 30,000 registros del repositorio UCI.",
                   "A complete data science and machine learning workflow to predict payment default among credit card clients, based on the 30,000 records of the UCI repository.")),
         tags$p(tx("Incluye un pipeline de extracción, limpieza y transformación (ETL), un análisis exploratorio centrado en el desbalance de clases y la multicolinealidad severa entre los montos facturados, y un diseño factorial de 112 configuraciones que compara algoritmos, representaciones de variables, técnicas de balanceo y optimización (genética y bayesiana). El resultado mejora el F1 de la clase minoritaria y reduce los falsos negativos frente a la regresión logística base.",
                   "It includes an extraction, cleaning and transformation (ETL) pipeline, an exploratory analysis focused on class imbalance and the severe multicollinearity among billed amounts, and a factorial design of 112 configurations comparing algorithms, feature representations, balancing techniques and optimization (genetic and Bayesian). The result improves the minority-class F1 and reduces false negatives compared with the baseline logistic regression."))),
    link_cards(),
    card(tx("Pipeline completo", "Full pipeline"), div(class = "nb-list", lapply(NOTEBOOKS, function(nb) {
      tags$a(class = "nb-row", href = paste0(BOOK_URL, "notebooks/", nb[[3]]), target = "_blank", rel = "noopener noreferrer",
             tags$span(class = "nb-num", icon_(PIPE_ICONS[[nb[[1]]]]), tags$span(class = "nb-n", nb[[1]])),
             div(class = "nb-body", div(class = "nb-t", L(nb[[2]])), tags$p(L(nb[[4]]))),
             icon_("external", "nb-ext"))
    }))),
    card(tx("Reproducir el análisis", "Reproduce the analysis"), ul_(list(
      tagList(tx("Clona el repositorio del tablero e instala los paquetes de R con ", "Clone the dashboard repository and install the R packages with "),
              tags$code('install.packages(c("shiny", "plotly", "ranger", "readxl", "jsonlite", "commonmark", "glmnet", "Matrix"))'), "."),
      tagList(tx("Desde la carpeta ", "From the "), tags$code("shiny/"), tx(" ejecuta ", " folder run "), tags$code("shiny::runApp()"),
              tx(" y abre la dirección que aparece en la consola.", " and open the address shown in the console.")),
      tagList(tx("La versión en Python (Dash) está en la carpeta ", "The Python (Dash) version is in the "), tags$code("dash/"),
              tx(" del mismo repositorio.", " folder of the same repository.")),
      tagList(tx("El análisis original (notebooks) está en el repositorio del proyecto: ", "The original analysis (notebooks) is in the project repository: "),
              tags$a(href = REPO_PROJECT, target = "_blank", rel = "noopener", "Credit_Card_Project"), ".")), ordered = TRUE)))
}

# ---------------------------------------------------------------- Equipo
team_link <- function(ic, label, href) tags$a(class = "tc-link", href = href, title = label, target = "_blank", rel = "noopener noreferrer",
                                              icon_(ic), tags$span(label))
copy_email <- function(email) {
  tags$button(class = "tc-link tc-copy", type = "button", title = paste(tx("Copiar", "Copy"), email), `data-email` = email,
              icon_("mail"), tags$span(class = "tc-copy-txt", email),
              tags$span(class = "tc-copy-ok", `aria-live` = "polite", tx("¡Correo copiado!", "Email copied!")))
}
team_card <- function(m) {
  front <- div(class = "cc-face tc-front",
    div(class = "cc-gloss"),
    div(class = "cc-top", tags$span(class = "cc-brand", tx("Equipo · Uninorte", "Team · Uninorte")), icon_("contactless", "cc-nfc")),
    div(class = "tc-photo", tags$img(src = m$photo, alt = tx(paste("Foto de", m$name), paste("Photo of", m$name)))),
    div(class = "tc-mid", div(class = "cc-chip tc-chip"), div(class = "tc-number", paste("•••• •••• ••••", m$card_no))),
    div(tags$span(class = "cc-lbl", tx("Titular", "Cardholder")), div(class = "tc-name", m$name), div(class = "tc-role", L(m$role))),
    div(class = "tc-hint", icon_("flip"), tx("Toca para ver contacto", "Tap to see contact")))
  back <- div(class = "cc-face tc-back",
    div(class = "cc-gloss"), div(class = "cc-mag tc-mag"),
    div(class = "tc-sig", tags$span(class = "tc-sig-lbl", tx("Firma autorizada", "Authorized signature")), div(class = "tc-sig-name", m$short)),
    tags$p(class = "tc-bio", L(m$bio)),
    div(class = "tc-links", team_link("github", "GitHub", m$github), team_link("linkedin", "LinkedIn", m$linkedin), copy_email(m$email)),
    tags$p(class = "cc-fine tc-fine", L(INSTITUTION)))
  div(class = "tc", tabindex = "0", role = "button", `aria-pressed` = "false",
      `aria-label` = tx(paste0("Tarjeta de ", m$name, ". Púlsala para ver su contacto"), paste0(m$name, "'s card. Press it to see their contact")),
      div(class = "tc-inner", front, back))
}
page_team <- function() {
  tagList(
    page_title(tx("Equipo", "Team")),
    div(class = "team-grid", lapply(TEAM, function(m) div(class = "tc-scene", team_card(m)))),
    tags$p(class = "muted team-hint", tx("Haz clic o toca una tarjeta para voltearla y ver la bio y los enlaces.", "Click or tap a card to flip it and see the bio and links.")))
}

# ---------------------------------------------------------------- Navegación
nav_buttons <- function(path) {
  i <- match(path, NAV_PATHS); if (is.na(i)) i <- 1
  left <- if (i > 1) tags$a(class = "pn prev", href = paste0("#", NAV_PATHS[i - 1]), icon_("arrow", "flip"),
                            div(tags$small(tx("Anterior", "Previous")), tags$b(L(NAV[[i - 1]][[2]])))) else tags$span()
  right <- if (i < length(NAV)) tags$a(class = "pn next", href = paste0("#", NAV_PATHS[i + 1]),
                                       div(tags$small(tx("Siguiente", "Next")), tags$b(L(NAV[[i + 1]][[2]]))), icon_("arrow")) else tags$span()
  div(class = "pn-row", left, right)
}

sidebar_content <- function(path) {
  tagList(
    tags$a(class = "brand", href = "#/", title = tx("Ir a la portada", "Go to the cover"),
           div(class = "brand-tag", icon_("card"), tx("Proyecto EDA", "EDA Project")),
           div(class = "brand-title", L(PROJECT_TITLE)),
           tags$p(class = "brand-sub", L(PROJECT_SUBTITLE))),
    div(class = "nav", lapply(NAV, function(n) tags$a(href = paste0("#", n[[1]]), class = if (identical(path, n[[1]])) "active" else NULL,
                                                      icon_(n[[3]]), tags$span(L(n[[2]]))))),
    div(class = "authors", tags$h4(tx("Autores", "Authors")),
        lapply(AUTHORS, function(a) div(class = "author", div(class = "nm", a$name), div(class = "em", a$email))),
        div(class = "inst", L(INSTITUTION))))
}

footer_content <- function() {
  tagList(
    div(div(tags$b(tx("Autores: ", "Authors: ")), paste(vapply(AUTHORS, function(a) sprintf("%s (%s)", a$name, a$email), ""), collapse = " · ")),
        div(sprintf("%s · %s: UCI Machine Learning Repository (Yeh & Lien, 2009) · %s", L(INSTITUTION), tx("Datos", "Data"),
                    tx("Versión Shiny (R)", "Shiny version (R)")))),
    div(class = "footer-links", lapply(LINKS, function(lk) tags$a(href = lk$url, target = "_blank", rel = "noopener noreferrer", icon_(lk$icon), L(lk$title)))))
}
