# =============================================================================
# 5. MODELOS (resultados del repositorio Credit_Card_Project, notebooks 05, 06, 08 y 09)
# =============================================================================
# results/ tiene los mismos archivos que dash/results (los genera
# dash/herramientas/actualizar_resultados.py a partir de Credit_Card_Project/results):
#   - model_results.csv: combinaciones con validación cruzada anidada 5 x 5 (desviaciones con ddof=1). El
#     tablero usa las 112 de los 7 modelos base (4 técnicas de balanceo x 4 métodos de optimización) y las 4 del
#     modelo original CS-FOF (pesos de clase con los 4 métodos). SVM conserva el F1 de Colab y trae aparte
#     f1_cpu_refit_mean (reajuste con scikit-learn en CPU).
#   - diagnosticos.json: curvas ROC, precisión-recall y calibración, Friedman/Nemenyi y SHAP global (lo genera
#     dash/herramientas/diagnosticos_desde_proyecto.py).
#   - shap_by_fold.csv y lime_vs_shap.csv: interpretabilidad en los 5 folds (notebook 06).
#   - anytime_curves.csv y anytime_summary.csv: costo de los optimizadores (notebook 09).
MR <- utils::read.csv("results/model_results.csv", stringsAsFactors = FALSE)
# Alcance del tablero: el modelo original (CS-FOF) frente a los siete modelos de referencia exigidos por el curso.
# El archivo conserva las corridas de CatBoost y LightGBM, que quedan fuera de la comparación.
MR <- MR[!MR$model %in% c("catboost", "lightgbm"), ]
rownames(MR) <- NULL

MODEL_INFO <- list(
  random_forest = list(
    label = c("Random Forest",
             "Random Forest"),
    family = c("Ensamble de árboles (bagging)",
             "Tree ensemble (bagging)"),
    desc = c("Promedia muchos árboles entrenados sobre muestras distintas de clientes; capta relaciones no lineales entre el historial de pagos y el riesgo.",
             "Averages many trees trained on different samples of clients; captures non-linear relationships between payment history and risk."),
    note = c("A solo 0.0027 de CS-FOF: una diferencia menor que la variación entre folds. Con sus 16 combinaciones tiene el mejor rango medio de los siete modelos base, y es el que usa la página Predecir. CS-FOF parte de él y le agrega cortes oblicuos.",
             "Only 0.0027 behind CS-FOF: a difference smaller than the variation between folds. Across its 16 combinations it has the best mean rank of the seven base models, and it is the one used by the Predict page. CS-FOF starts from it and adds oblique splits.")),
  xgboost = list(
    label = c("XGBoost",
             "XGBoost"),
    family = c("Ensamble de árboles (boosting)",
             "Tree ensemble (boosting)"),
    desc = c("Construye árboles en secuencia: cada uno corrige los errores del anterior.",
             "Builds trees in sequence: each one corrects the errors of the previous one."),
    note = c("Mayor F1 de los siete modelos de referencia. Con CS-FOF y Random Forest forma un grupo de tres que las pruebas no separan: en la práctica empatan.",
             "Highest F1 of the seven baseline models. With CS-FOF and Random Forest it forms a group of three that the tests do not separate: in practice they tie.")),
  cs_fof = list(
    label = c("CS-FOF (original)",
             "CS-FOF (original)"),
    family = c("Modelo original · bosque oblicuo con costo",
             "Original model · cost-sensitive oblique forest"),
    desc = c("Bosque aleatorio propio: en cada nodo compara los cortes de una variable con un corte oblicuo en la dirección de Fisher, ponderada por el costo de no detectar a quien incumple.",
             "Our own random forest: at each node it compares single-variable splits with an oblique split along the Fisher direction, weighted by the cost of missing a defaulter."),
    note = c("Programado desde cero con numpy. Tiene el mayor F1 medio (+0.0014 sobre XGBoost) y el mayor ROC-AUC, pero la diferencia con XGBoost y Random Forest no es significativa.",
             "Programmed from scratch with numpy. It has the highest mean F1 (+0.0014 over XGBoost) and the highest ROC-AUC, but the difference with XGBoost and Random Forest is not significant.")),
  svm = list(
    label = c("SVM",
             "SVM"),
    family = c("Máquina de vectores de soporte (kernel RBF)",
             "Support vector machine (RBF kernel)"),
    desc = c("Busca la frontera que separa mejor a quienes pagan de quienes incumplen, con un margen máximo.",
             "Looks for the boundary that best separates payers from defaulters, with maximum margin."),
    note = c("Corrió en Colab con GPU (cuML). Al reajustarlo en CPU con scikit-learn, con los mismos hiperparámetros y folds, el F1 sube en promedio 0.009: su mejor combinación pasa de 0.539 a 0.545, a 0.002 de XGBoost. Aquí se muestra el valor de Colab, tal como se reportó.",
             "Run on Colab with a GPU (cuML). Refitting it on CPU with scikit-learn, with the same hyperparameters and folds, raises F1 by 0.009 on average: its best combination goes from 0.539 to 0.545, 0.002 behind XGBoost. The Colab value is shown here, as reported.")),
  knn = list(
    label = c("KNN",
             "KNN"),
    family = c("Vecinos más cercanos",
             "Nearest neighbors"),
    desc = c("Clasifica a cada cliente según lo que hicieron los clientes más parecidos a él.",
             "Classifies each client according to what the most similar clients did."),
    note = c("Con pesos de clase usa un ajuste propio del proyecto (el voto de cada vecino se pondera por la rareza de su clase), no un mecanismo estándar de scikit-learn. Corrió en GPU (cuML), pero sus predicciones coinciden con las de scikit-learn en 99.98 % a 100 % de los casos.",
             "With class weights it uses a project-specific adjustment (each neighbor's vote is weighted by the rarity of its class), not a standard scikit-learn mechanism. It ran on a GPU (cuML), but its predictions match scikit-learn's in 99.98% to 100% of cases.")),
  decision_tree = list(
    label = c("Árbol de decisión",
             "Decision tree"),
    family = c("Árbol de clasificación",
             "Classification tree"),
    desc = c("Una secuencia de preguntas sí/no sobre las variables; fácil de leer, pero inestable.",
             "A sequence of yes/no questions about the variables; easy to read, but unstable."),
    note = c("Queda por debajo del grupo superior, aunque la diferencia con Random Forest está justo en el límite de la significancia (Nemenyi, p = 0.050) y con XGBoost no lo es (p = 0.12).",
             "It falls below the top group, although the difference with Random Forest is right at the edge of significance (Nemenyi, p = 0.050) and with XGBoost it is not significant (p = 0.12).")),
  logistic_regression = list(
    label = c("Regresión logística",
             "Logistic regression"),
    family = c("Modelo lineal · línea base",
             "Linear model · baseline"),
    desc = c("Modelo de referencia: combina las variables de forma lineal para estimar la probabilidad de default.",
             "Reference model: combines the variables linearly to estimate the probability of default."),
    note = c("Sin balanceo es la combinación con menor F1 (0.378): solo detecta 27 % de quienes incumplen. Con SMOTE o pesos de clase sube a 0.516, con un ROC-AUC casi igual.",
             "Without balancing it is the combination with the lowest F1 (0.378): it detects only 27% of defaulters. With SMOTE or class weights it rises to 0.516, with almost the same ROC-AUC.")),
  naive_bayes = list(
    label = c("Naive Bayes",
             "Naive Bayes"),
    family = c("Probabilístico (gaussiano)",
             "Probabilistic (Gaussian)"),
    desc = c("Aplica el teorema de Bayes suponiendo que las variables son independientes entre sí.",
             "Applies Bayes' theorem assuming the variables are independent of each other."),
    note = c("Ese supuesto no se cumple con el historial de pagos, muy correlacionado mes a mes; por eso el balanceo casi no lo cambia (F1 entre 0.495 y 0.499).",
             "That assumption does not hold for payment history, which is highly correlated month to month; that is why balancing barely changes it (F1 between 0.495 and 0.499)."))
)
minfo <- function(model, key) L(MODEL_INFO[[model]][[key]])

TECH_LBL <- list(none = c("Sin balanceo", "No balancing"), class_weight = c("Pesos de clase", "Class weights"),
                 smote = c("SMOTE", "SMOTE"), adasyn = c("ADASYN", "ADASYN"))
TECH_ORDER <- c("none", "class_weight", "smote", "adasyn")
METHOD_LBL <- list(grid_search = c("Grid search", "Grid search"), random_search = c("Random search", "Random search"),
                   bayesian_optuna = c("Bayesiana (Optuna)", "Bayesian (Optuna)"),
                   genetic_deap = c("Genética (DEAP)", "Genetic (DEAP)"))
tech_lbl <- function(t) L(TECH_LBL[[t]])
method_lbl <- function(m) L(METHOD_LBL[[m]])

# Mejor combinación de cada modelo (por F1 medio), de mejor a peor
BEST_BY_MODEL <- do.call(rbind, lapply(split(MR, MR$model), function(s) s[which.max(s$f1_mean), ]))
BEST_BY_MODEL <- BEST_BY_MODEL[order(-BEST_BY_MODEL$f1_mean), ]
rownames(BEST_BY_MODEL) <- NULL
BEST <- BEST_BY_MODEL[1, ]
# Las 112 combinaciones del diseño factorial (7 modelos base) y, aparte, las corridas de CS-FOF, que buscan
# superar el mejor F1 de esas 112.
BASE_MODELS <- c("random_forest", "xgboost", "svm", "knn", "decision_tree", "logistic_regression", "naive_bayes")
N_BASE <- sum(MR$model %in% BASE_MODELS)
N_EXTRA <- nrow(MR) - N_BASE
BEST_BASE <- BEST_BY_MODEL[BEST_BY_MODEL$model %in% BASE_MODELS, ][1, ]
TWD_PER_USD_2005 <- 32.2   # tasa promedio de 2005 (Banco Central de la República de China)
BASELINE <- max(MR$f1_mean[MR$model == "logistic_regression" & MR$technique == "none"])
F1_MAX <- max(MR$f1_mean)
# Matrices de confusión fuera de pliegue (umbral 0.5) de CS-FOF y de XGBoost, el mejor modelo de referencia,
# reajustadas con los hiperparámetros de cada fold (experiments/comparacion_final/probabilidades_oof.npz).
XGB_CM <- list(tn = 19087, fp = 4248, fn = 2557, tp = 4073)
CSFOF_CM <- list(tn = 19660, fp = 3675, fn = 2737, tp = 3893)
TECH_COLORS <- c(none = GREY_BLUE, class_weight = WARM_GOLD, smote = DEEP_NAVY, adasyn = MID_BLUE)

fig_models_heat <- function() {
  ord <- BEST_BY_MODEL$model
  z <- sapply(TECH_ORDER, function(t) sapply(ord, function(m) {
    v <- MR$f1_mean[MR$model == m & MR$technique == t]
    if (length(v)) max(v) else NA_real_                   # celda vacía: el modelo no se corrió con esa técnica
  }))
  p <- plot_ly(z = unname(z), x = vapply(TECH_ORDER, tech_lbl, ""), y = vapply(ord, minfo, "", "label"),
               type = "heatmap", colorscale = SEQ_GOLD, textfont = list(size = 13),
               text = matrix(ifelse(is.na(z), "", sprintf("%.3f", z)), nrow = nrow(z)), texttemplate = "%{text}",   # celdas vacías sin «NaN»
               xgap = 3, ygap = 3, showscale = FALSE,   # cada celda ya muestra su valor
               hovertemplate = paste0("%{y} · %{x}<br>", tx("Mejor F1", "Best F1"), ": %{z:.4f}<extra></extra>"))
  p <- layout(p, yaxis = list(autorange = "reversed", showgrid = FALSE, title = ""),
              xaxis = list(side = "top", showgrid = FALSE, title = ""))
  style_fig(p, 480, legend_top = FALSE, margin = list(l = 125, r = 10, t = 30, b = 20))
}

fig_models_scatter <- function() {
  p <- plot_ly()
  for (t in TECH_ORDER) {
    d <- MR[MR$technique == t, ]
    cd <- lapply(seq_len(nrow(d)), function(i) list(minfo(d$model[i], "label"), method_lbl(d$method[i]), d$recall_mean[i]))
    p <- add_trace(p, x = d$roc_auc_mean, y = d$f1_mean, type = "scatter", mode = "markers", name = tech_lbl(t),
                   customdata = cd,
                   marker = list(size = 9, color = TECH_COLORS[[t]], opacity = .85, line = list(width = .6, color = WHITE)),
                   hovertemplate = paste0("<b>%{customdata[0]}</b> · ", tech_lbl(t),
                                          "<br>%{customdata[1]}<br>F1: %{y:.4f}<br>ROC-AUC: %{x:.4f}<br>Recall: %{customdata[2]:.3f}<extra></extra>"))
  }
  # Modelo original: rombos con borde oscuro
  d <- MR[MR$model == "cs_fof", ]
  p <- add_trace(p, x = d$roc_auc_mean, y = d$f1_mean, type = "scatter", mode = "markers", name = "CS-FOF",
                 customdata = vapply(d$method, method_lbl, ""),
                 marker = list(symbol = "diamond", size = 12, color = WARM_GOLD, line = list(width = 1.6, color = NAVY)),
                 hovertemplate = "<b>CS-FOF</b> · %{customdata}<br>F1: %{y:.4f}<br>ROC-AUC: %{x:.4f}<extra></extra>")
  # Mejor modelo: punto dorado brillante con un halo suave
  p <- add_trace(p, x = BEST$roc_auc_mean, y = BEST$f1_mean, type = "scatter", mode = "markers", showlegend = FALSE,
                 hoverinfo = "skip", marker = list(size = 34, color = "rgba(245,196,81,0.28)", line = list(width = 0)))
  p <- add_trace(p, x = BEST$roc_auc_mean, y = BEST$f1_mean, type = "scatter", mode = "markers",
                 name = tx("Mejor combinación", "Best combination"),
                 marker = list(symbol = "circle", size = 17, color = BRIGHT_GOLD, line = list(width = 2, color = WHITE)),
                 hovertemplate = sprintf("<b>%s: %s</b><br>%s · %s<br>F1: %%{y:.4f}<br>ROC-AUC: %%{x:.4f}<extra></extra>",
                                         tx("Mejor", "Best"), minfo(BEST$model, "label"), tech_lbl(BEST$technique), method_lbl(BEST$method)))
  p <- layout(p, xaxis = list(title = tx("ROC-AUC (capacidad de ordenar clientes)", "ROC-AUC (ability to rank clients)")),
              yaxis = list(title = tx("F1 de la clase default", "F1 of the default class")))
  style_fig(p, 420, margin = list(l = 60, r = 20, t = 50, b = 55))
}

fig_best_cm <- function() {   # matriz de confusión de CS-FOF, el modelo de mayor F1 medio
  c <- CSFOF_CM
  z <- matrix(c(c$tn, c$fp, c$fn, c$tp), 2, byrow = TRUE)
  txt <- matrix(c(sprintf("<b>%s</b><br>%s", num(c$tn), tx("Bien clasificados", "Correctly classified")),
                  sprintf("<b>%s</b><br>%s", num(c$fp), tx("Falsas alarmas", "False alarms")),
                  sprintf("<b>%s</b><br>%s", num(c$fn), tx("No detectados", "Missed")),
                  sprintf("<b>%s</b><br>%s", num(c$tp), tx("Detectados", "Detected"))), 2, byrow = TRUE)
  p <- plot_ly(z = z, x = c(tx("Predice: paga", "Predicted: pays"), tx("Predice: incumple", "Predicted: defaults")),
               y = c(tx("Real: paga", "Actual: pays"), tx("Real: incumple", "Actual: defaults")),
               type = "heatmap", text = txt, texttemplate = "%{text}", textfont = list(size = 13), showscale = FALSE,
               xgap = 4, ygap = 4, colorscale = list(c(0, CREAM), c(0.25, PALE_GOLD), c(1, NAVY)),
               hovertemplate = paste0("%{y} · %{x}<br>", tx("Clientes", "Clients"), ": %{z:,}<extra></extra>"))
  p <- layout(p, yaxis = list(autorange = "reversed", showgrid = FALSE, title = ""),
              xaxis = list(side = "top", showgrid = FALSE, title = ""))
  style_fig(p, 380, legend_top = FALSE, margin = list(l = 100, r = 20, t = 30, b = 20))
}

# ---------- Interpretabilidad en los 5 folds (06_interpretability, secciones 5 y 6) ----------
SHAP_FOLDS <- utils::read.csv("results/shap_by_fold.csv", stringsAsFactors = FALSE)
LIME_SHAP <- utils::read.csv("results/lime_vs_shap.csv", stringsAsFactors = FALSE)
FEAT_LBL <- list(LIMIT_BAL_LOG = c("LIMIT_BAL (log)", "LIMIT_BAL (log)"),
                 BILL_AMT_MEAN_6M_LOG = c("BILL_AMT media 6 m (log)", "BILL_AMT 6-mo mean (log)"),
                 BILL_AMT_TREND_6M_LOG = c("BILL_AMT tendencia 6 m (log)", "BILL_AMT 6-mo trend (log)"),
                 N_CREDIT_BALANCE_MONTHS = c("Meses con saldo a favor", "Months with credit balance"))
feat_lbl <- function(f) {
  if (!is.null(FEAT_LBL[[f]])) return(L(FEAT_LBL[[f]]))
  if (endsWith(f, "_LOG")) sub("_LOG$", " (log)", f) else f
}

# Spearman medio entre folds, Jaccard medio del top 5 y variables que siempre están en el top 5
shap_stability <- function(model) {
  d <- SHAP_FOLDS[SHAP_FOLDS$model == model, ]
  folds <- sort(unique(d$fold))
  feats <- sort(unique(d$feature))
  m <- sapply(folds, function(f) { x <- d[d$fold == f, ]; x$mean_abs_shap[match(feats, x$feature)] })
  rownames(m) <- feats
  pares <- utils::combn(seq_along(folds), 2)
  sp <- apply(pares, 2, function(ij) stats::cor(m[, ij[1]], m[, ij[2]], method = "spearman"))
  tops <- lapply(seq_along(folds), function(j) names(sort(m[, j], decreasing = TRUE))[1:5])
  jac <- apply(pares, 2, function(ij) length(intersect(tops[[ij[1]]], tops[[ij[2]]])) /
                                      length(union(tops[[ij[1]]], tops[[ij[2]]])))
  orden <- names(sort(rowMeans(m), decreasing = TRUE))
  always <- orden[vapply(orden, function(f) all(vapply(tops, function(t) f %in% t, TRUE)), TRUE)]
  list(sp = mean(sp), jac = mean(jac), always = always)
}

# Importancia SHAP (media de |SHAP|) de las variables principales en cada uno de los 5 folds
fig_shap_folds <- function(model, top = 10) {
  d <- SHAP_FOLDS[SHAP_FOLDS$model == model, ]
  media <- sort(tapply(d$mean_abs_shap, d$feature, mean), decreasing = TRUE)[1:top]
  orden <- rev(names(media))                       # la más importante queda arriba
  lv <- vapply(orden, feat_lbl, "")
  d <- d[d$feature %in% orden, ]
  yf <- function(f) factor(vapply(f, feat_lbl, ""), levels = lv)
  p <- plot_ly()
  for (f in orden) {   # rango entre folds como una línea tenue
    v <- d$mean_abs_shap[d$feature == f]
    p <- add_trace(p, x = c(min(v), max(v)), y = yf(c(f, f)), type = "scatter", mode = "lines", showlegend = FALSE,
                   hoverinfo = "skip", line = list(color = rgba(DEEP_NAVY, .25), width = 6))
  }
  cd <- lapply(seq_len(nrow(d)), function(i) list(d$fold[i] + 1, d$rank[i]))
  p <- add_trace(p, x = d$mean_abs_shap, y = yf(d$feature), type = "scatter", mode = "markers",
                 name = tx("Cada fold", "Each fold"), customdata = cd,
                 marker = list(size = 8, color = NAVY, opacity = .75, line = list(width = .6, color = WHITE)),
                 hovertemplate = paste0("%{y}<br>Fold %{customdata[0]}: %{x:.3f}<br>", tx("Puesto", "Rank"),
                                        " %{customdata[1]}<extra></extra>"))
  p <- add_trace(p, x = unname(media[orden]), y = yf(orden), type = "scatter", mode = "markers",
                 name = tx("Media de los 5 folds", "Mean of 5 folds"),
                 marker = list(symbol = "diamond", size = 12, color = WARM_GOLD, line = list(width = 1, color = WHITE)),
                 hovertemplate = paste0("%{y}<br>", tx("Media", "Mean"), ": %{x:.3f}<extra></extra>"))
  unidad <- if (model == "xgboost") "log-odds" else tx("probabilidad", "probability")
  p <- layout(p, xaxis = list(title = tx(sprintf("Importancia SHAP media |SHAP| (%s)", unidad),
                                         sprintf("Mean SHAP importance |SHAP| (%s)", unidad))),
              yaxis = list(title = "", showgrid = FALSE))
  style_fig(p, 420, margin = list(l = 170, r = 20, t = 50, b = 55))
}

interp_shap_folds <- function(model) {
  st <- shap_stability(model)
  alw <- paste(vapply(st$always, feat_lbl, ""), collapse = ", ")
  basic <- if (model == "random_forest")
    tx("En Random Forest la explicación es estable: las cuatro primeras variables (PAY_0, PAY_2, el límite de crédito y PAY_3) son las mismas y en el mismo orden en los cinco folds; solo cambia la quinta.",
       "In Random Forest the explanation is stable: the top four variables (PAY_0, PAY_2, the credit limit and PAY_3) are the same and in the same order in all five folds; only the fifth changes.") else
    tx("En XGBoost, PAY_0 es la primera variable en los cinco folds, pero el resto del top 5 cambia: en algunos folds PAY_2 y PAY_3 salen y entran los montos pagados. El orden fino de los montos no debe interpretarse.",
       "In XGBoost, PAY_0 is the top variable in all five folds, but the rest of the top 5 changes: in some folds PAY_2 and PAY_3 drop out and paid amounts come in. The fine order of the amounts should not be interpreted.")
  tech <- tx(sprintf("Spearman medio entre folds = %.2f; Jaccard medio del top 5 = %.2f; siempre en el top 5: %s. Cada fold usa los hiperparámetros de su propio bucle interno y SHAP (TreeExplainer, exacto) sobre 300 clientes de su fold de prueba. Las magnitudes entre folds no son estrictamente comparables; por eso la estabilidad se juzga por el orden.", st$sp, st$jac, alw),
             sprintf("Mean Spearman between folds = %.2f; mean top-5 Jaccard = %.2f; always in the top 5: %s. Each fold uses the hyperparameters of its own inner loop and SHAP (TreeExplainer, exact) on 300 clients from its test fold. Magnitudes across folds are not strictly comparable, so stability is judged by order.", st$sp, st$jac, alw))
  list(basic, tech)
}

lime_shap_table <- function() {
  g <- function(m, col) mean(LIME_SHAP[[col]][LIME_SHAP$model == m])
  filas <- list(list(tx("Coinciden en el signo del efecto (top 5)", "Agree on the sign of the effect (top 5)"), "sign_agreement_topk", TRUE),
                list(tx("Variables compartidas en el top 5", "Shared variables in the top 5"), "top5_overlap", FALSE),
                list(tx("Correlación de orden (Spearman)", "Rank correlation (Spearman)"), "spearman_abs", FALSE),
                list(tx("LIME consigo mismo entre semillas (top 5)", "LIME with itself across seeds (top 5)"), "lime_seed_topk_overlap", FALSE))
  fmt <- function(v, es_pct) if (es_pct) pct(v, 1) else sprintf("%.2f", v)
  tbl_(c(tx("Medida", "Measure"), "Random Forest", "XGBoost"),
       lapply(filas, function(f) list(f[[1]], fmt(g("random_forest", f[[2]]), f[[3]]), fmt(g("xgboost", f[[2]]), f[[3]]))))
}

CELL_LBL <- list(TP = c("Verdaderos positivos", "True positives"), FP = c("Falsas alarmas", "False alarms"),
                 TN = c("Verdaderos negativos", "True negatives"), FN = c("No detectados", "Missed"))

# Variables principales compartidas por LIME y SHAP (de 5), según la celda de la matriz de confusión
fig_lime_cells <- function() {
  cells <- c("TP", "FP", "TN", "FN")
  xl <- fx(vapply(cells, function(k) L(CELL_LBL[[k]]), ""))
  p <- plot_ly()
  for (m in c("random_forest", "xgboost")) {
    v <- vapply(cells, function(k) 5 * mean(LIME_SHAP$top5_overlap[LIME_SHAP$model == m & LIME_SHAP$outcome == k]), 0)
    p <- add_trace(p, x = xl, y = unname(v), type = "bar", name = minfo(m, "label"),
                   marker = list(color = if (m == "random_forest") NAVY else WARM_GOLD),
                   text = sprintf("%.1f", v), textposition = "outside", cliponaxis = FALSE,
                   hovertemplate = paste0("<b>", minfo(m, "label"), "</b> · %{x}<br>",
                                          tx("Variables compartidas", "Shared variables"), ": %{y:.2f} / 5<extra></extra>"))
  }
  p <- layout(p, barmode = "group", bargap = .3, xaxis = list(title = "", showgrid = FALSE),
              yaxis = list(range = c(0, 5), dtick = 1, title = tx("Variables compartidas (de 5)", "Shared variables (of 5)")))
  style_fig(p, 330, margin = list(l = 55, r = 10, t = 50, b = 40))
}

# ---------- Optimizadores: curvas anytime y multi-fidelidad (09_anytime_multifidelidad) ----------
ANYTIME <- utils::read.csv("results/anytime_curves.csv", stringsAsFactors = FALSE)
ANYTIME_SUM <- utils::read.csv("results/anytime_summary.csv", stringsAsFactors = FALSE)
ANY_METHODS <- c("grid_search", "random_search", "bayesian_optuna", "genetic_deap", "hyperband")
ANY_COLORS <- c(grid_search = GREY_BLUE, random_search = MID_BLUE, bayesian_optuna = WARM_GOLD,
                genetic_deap = DEEP_NAVY, hyperband = BROWN)
ANY_DASH <- c(grid_search = "solid", random_search = "solid", bayesian_optuna = "solid", genetic_deap = "dot", hyperband = "dash")
METHOD_LBL$hyperband <- c("Hyperband (multi-fidelidad)", "Hyperband (multi-fidelity)")
ANY_MODELS <- c("xgboost", "decision_tree", "logistic_regression")

# Arrepentimiento (mejor F1 interno posible - mejor F1 hallado) frente al costo acumulado
fig_anytime <- function(model) {
  d <- ANYTIME[ANYTIME$model == model, ]
  p <- plot_ly()
  for (m in ANY_METHODS) {
    r <- d[d$method == m, ]
    if (!nrow(r)) next
    r <- r[order(r$cost_s), ]
    col <- ANY_COLORS[[m]]
    p <- add_trace(p, x = c(r$cost_s, rev(r$cost_s)), y = c(r$regret_max, rev(r$regret_min)), type = "scatter",
                   mode = "lines", fill = "toself", fillcolor = rgba(col, .10), line = list(width = 0),
                   hoverinfo = "skip", showlegend = FALSE, legendgroup = m)
    p <- add_trace(p, x = r$cost_s, y = r$regret_med, type = "scatter", mode = "lines", name = method_lbl(m),
                   legendgroup = m, line = list(color = col, width = 2.4, dash = ANY_DASH[[m]]),
                   hovertemplate = paste0("<b>", method_lbl(m), "</b><br>", tx("Costo", "Cost"), ": %{x:.0f} s<br>",
                                          tx("Arrepentimiento", "Regret"), ": %{y:.4f}<extra></extra>"))
  }
  p <- layout(p, shapes = list(hline(0.002, color = WARM_GOLD, dash = "dot", width = 1)),
              annotations = list(nota(tx("objetivo: a 0.002 del mejor", "target: within 0.002 of the best"),
                                      0.01, 0.002, color = DEEP_NAVY)),
              xaxis = list(type = "log", title = tx("Costo de cómputo acumulado (s, escala log)", "Cumulative compute cost (s, log scale)")),
              yaxis = list(title = tx("Arrepentimiento en F1 interno", "Regret in inner F1")),
              legend = list(orientation = "h", yanchor = "top", y = -0.2, xanchor = "center", x = 0.5))
  style_fig(p, 460, legend_top = FALSE, margin = list(l = 60, r = 20, t = 24, b = 40))
}

anytime_table <- function(model) {
  d <- ANYTIME_SUM[ANYTIME_SUM$model == model, ]
  filas <- lapply(ANY_METHODS, function(m) {
    r <- d[d$method == m, ]
    tgt <- if (r$llegan > 0) sprintf("%s s (%d/3)", num(r$costo_objetivo_s), as.integer(r$llegan)) else
      tx("no llega (0/3)", "never (0/3)")
    list(method_lbl(m), sprintf("%.0f", r$evaluaciones), paste(num(r$costo_total_s), "s"), tgt,
         sprintf("%.3f ± %.3f", r$f1_externo, r$f1_externo_std))
  })
  tbl_(c(tx("Método", "Method"), tx("Evaluaciones", "Evaluations"), tx("Costo total", "Total cost"),
         tx("Costo hasta el objetivo", "Cost to target"), tx("F1 externo", "Outer F1")), filas)
}

interp_anytime <- function(model) {
  d <- ANYTIME_SUM[ANYTIME_SUM$model == model, ]
  lo <- min(d$f1_externo); hi <- max(d$f1_externo)
  cheap <- method_lbl(d$method[which.min(d$costo_total_s)])
  basic <- tx(sprintf("Cada línea muestra qué tan lejos está cada método del mejor resultado posible a medida que gasta tiempo de cómputo. Todos terminan muy cerca: el F1 en datos nuevos va de %.3f a %.3f. Lo que cambia es el costo para llegar; aquí el más barato es %s.", lo, hi, cheap),
              sprintf("Each line shows how far each method is from the best possible result as it spends compute time. All of them end very close: the F1 on new data ranges from %.3f to %.3f. What changes is the cost to get there; here the cheapest is %s.", lo, hi, cheap))
  tech <- tx("Mediana y rango entre los folds externos 0 a 2 (de 5), con pesos de clase y una semilla; arrepentimiento = mejor F1 interno visto por cualquier método a fidelidad completa − mejor F1 del método hasta ese punto. En la tabla maestra los cuatro optimizadores empatan (Friedman con 28 bloques, p = 0.080; F1 medio entre 0.5022 y 0.5040). Hyperband, implementado desde cero con la fracción de filas como fidelidad, logra un F1 externo 0.0022 mayor que Random Search (desviación 0.0051, 9 corridas) con un costo 1.12 veces mayor: no demuestra ventaja.",
             "Median and range over outer folds 0 to 2 (of 5), with class weights and one seed; regret = best inner F1 seen by any method at full fidelity − the method's best F1 so far. In the master table the four optimizers tie (Friedman with 28 blocks, p = 0.080; mean F1 between 0.5022 and 0.5040). Hyperband, implemented from scratch with the fraction of rows as fidelity, reaches an outer F1 0.0022 higher than Random Search (SD 0.0051, 9 runs) at 1.12 times the cost: it shows no advantage.")
  list(basic, tech)
}

# ---------- Tabla de líderes (todas las combinaciones, ordenable y filtrable) ----------
# Tiempo de inferencia (ms por 1,000 clientes, 25 columnas, pliegue 0, 4 núcleos), medido en
# experiments/robustez/escalabilidad.csv del proyecto. Solo se midió para los tres mejores modelos.
INFER_MS <- c(cs_fof = 253.1, xgboost = 4.8, random_forest = 9.4)

leaderboard_df <- function() {
  d <- MR
  best <- vapply(split(seq_len(nrow(d)), d$model), function(i) i[which.max(d$f1_mean[i])], 0L)
  d$mejor <- ifelse(seq_len(nrow(d)) %in% best, "★", "")
  d <- d[order(-d$f1_mean), ]
  r4 <- function(v) ifelse(is.na(v), NA_real_, round(v, 4))
  data.frame(
    `#` = seq_len(nrow(d)),
    Mejor = d$mejor,
    Modelo = vapply(d$model, minfo, "", "label"),
    Balanceo = vapply(d$technique, tech_lbl, ""),
    Busqueda = vapply(d$method, method_lbl, ""),
    F1 = sprintf("%.4f ± %.4f", d$f1_mean, d$f1_std),
    AUC = r4(d$roc_auc_mean), Recall = r4(d$recall_mean), Precision = r4(d$precision_mean),
    Inferencia = ifelse(d$mejor == "★" & d$model %in% names(INFER_MS), unname(INFER_MS[d$model]), NA_real_),
    check.names = FALSE, stringsAsFactors = FALSE)
}

# Tabla HTML propia (www/leaderboard.js la ordena al hacer clic en un encabezado y la filtra con el buscador).
# No usa DT: su JavaScript falla al cargarse con la página dinámica y corta el dibujo de otras gráficas.
leaderboard <- function() {
  d <- leaderboard_df()
  heads <- list(list("#", "num"), list(tx("Mejor", "Best"), "txt"), list(tx("Modelo", "Model"), "txt"),
                list(tx("Balanceo", "Balancing"), "txt"), list(tx("Búsqueda", "Search"), "txt"),
                list(tx("F1 media ± d.e.", "F1 mean ± s.d."), "num"), list("AUC-ROC", "num"), list("Recall", "num"),
                list(tx("Precisión", "Precision"), "num"), list(tx("Inferencia (ms / 1,000)", "Inference (ms / 1,000)"), "num"))
  fmt <- function(v) if (is.na(v)) "" else sprintf("%.4f", v)
  filas <- lapply(seq_len(nrow(d)), function(i) {
    r <- d[i, ]
    cls <- paste(c(if (r$Mejor == "★") "lb-best", if (grepl("CS-FOF", r$Modelo)) "lb-cs"), collapse = " ")
    tags$tr(class = if (nzchar(cls)) cls,
            tags$td(r[["#"]]), tags$td(r$Mejor), tags$td(r$Modelo), tags$td(r$Balanceo), tags$td(r$Busqueda),
            tags$td(`data-v` = sub(" .*", "", r$F1), r$F1), tags$td(fmt(r$AUC)), tags$td(fmt(r$Recall)),
            tags$td(fmt(r$Precision)), tags$td(if (is.na(r$Inferencia)) "" else sprintf("%.1f", r$Inferencia)))
  })
  div(class = "lb",
      tags$input(type = "search", class = "lb-search", placeholder = tx("Filtrar (por ejemplo, XGBoost o SMOTE)…", "Filter (for example, XGBoost or SMOTE)…"),
                 `aria-label` = tx("Filtrar la tabla", "Filter the table")),
      div(class = "table-wrap lb-wrap",
          tags$table(class = "vtable lb-table",
                     tags$thead(tags$tr(lapply(seq_along(heads), function(k)
                       tags$th(`data-k` = k - 1, `data-t` = heads[[k]][[2]], class = "lb-sort", tabindex = "0", heads[[k]][[1]])))),
                     tags$tbody(filas))),
      tags$p(class = "muted lb-count", `data-tpl` = tx("{n} de {t} combinaciones", "{n} of {t} combinations"),
             tx(sprintf("%d de %d combinaciones", nrow(d), nrow(d)), sprintf("%d of %d combinations", nrow(d), nrow(d)))))
}

# ---------- Diagnóstico del modelo elegido, diagrama de diferencia crítica y SHAP global ----------
DIAG <- jsonlite::fromJSON("results/diagnosticos.json", simplifyVector = FALSE)
DIAG_MODELS <- names(DIAG$modelos)
.num <- function(v) as.numeric(unlist(v))

fig_diag <- function(model) {
  ref <- if (model == "cs_fof") "xgboost" else "cs_fof"
  panel <- function(eje) {
    p <- plot_ly()
    for (m in c(ref, model)) {
      d <- DIAG$modelos[[m]]; nm <- minfo(m, "label")
      col <- if (m == ref) { if (ref == "cs_fof") PALE_GOLD else GREY_BLUE } else { if (model == "cs_fof") WARM_GOLD else NAVY }
      dsh <- if (m == ref) "dot" else "solid"
      if (eje == "roc") {
        p <- add_trace(p, x = .num(d$roc[[1]]), y = .num(d$roc[[2]]), type = "scatter", mode = "lines", name = nm,
                       legendgroup = m, line = list(color = col, width = 2.5, dash = dsh),
                       hovertemplate = paste0(nm, "<br>FPR %{x:.2f} · TPR %{y:.2f}<extra></extra>"))
      } else if (eje == "pr") {
        p <- add_trace(p, x = .num(d$pr[[1]]), y = .num(d$pr[[2]]), type = "scatter", mode = "lines", name = nm,
                       legendgroup = m, showlegend = FALSE, line = list(color = col, width = 2.5, dash = dsh),
                       hovertemplate = paste0(nm, "<br>Recall %{x:.2f} · ", tx("precisión", "precision"), " %{y:.2f}<extra></extra>"))
      } else {
        cal <- d$cal
        p <- add_trace(p, x = vapply(cal, function(c) c[[1]], 0), y = vapply(cal, function(c) c[[2]], 0),
                       customdata = vapply(cal, function(c) as.numeric(c[[3]]), 0),
                       type = "scatter", mode = "lines+markers", name = nm, legendgroup = m, showlegend = FALSE,
                       line = list(color = col, width = 2.5, dash = dsh),
                       hovertemplate = paste0(nm, "<br>", tx("Predicho", "Predicted"), " %{x:.2f} · ", tx("observado", "observed"),
                                              " %{y:.2f}<br>%{customdata:,} ", tx("clientes", "clients"), "<extra></extra>"))
      }
    }
    if (eje != "pr") p <- add_trace(p, x = c(0, 1), y = c(0, 1), type = "scatter", mode = "lines", showlegend = FALSE,
                                    hoverinfo = "skip", line = list(color = GREY_BLUE, width = 1, dash = "dash"))
    if (eje == "pr") p <- add_trace(p, x = c(0, 1), y = rep(DIAG$tasa, 2), type = "scatter", mode = "lines", showlegend = FALSE,
                                    hoverinfo = "skip", line = list(color = GREY_BLUE, width = 1, dash = "dash"))
    tit <- switch(eje, roc = c(tx("Tasa de falsos positivos", "False positive rate"), tx("Tasa de verdaderos positivos", "True positive rate")),
                  pr = c("Recall", tx("Precisión", "Precision")),
                  cal = c(tx("Probabilidad predicha", "Predicted probability"), tx("Tasa real de impago", "Observed default rate")))
    layout(p, xaxis = list(title = tit[1], range = if (eje == "cal") c(0, 1) else NULL),
           yaxis = list(title = tit[2], range = if (eje == "cal") c(0, 1) else NULL))
  }
  p <- subplot(panel("roc"), panel("pr"), panel("cal"), nrows = 1, margin = 0.05, titleX = TRUE, titleY = TRUE)
  ann <- lapply(seq_along(c(1, 2, 3)), function(i) list(
    text = c(tx("Curva ROC", "ROC curve"), tx("Precisión-recall", "Precision-recall"), tx("Calibración (10 grupos)", "Calibration (10 bins)"))[i],
    x = c(0.14, 0.5, 0.86)[i], y = 1.08, xref = "paper", yref = "paper", showarrow = FALSE, font = list(size = 13)))
  p <- layout(p, annotations = ann, legend = list(orientation = "h", x = 0.5, xanchor = "center", y = -0.3, yanchor = "top"))
  style_fig(p, 380, legend_top = FALSE, margin = list(l = 60, r = 20, t = 50, b = 95))
}

diag_interp <- function(model) {
  d <- DIAG$modelos[[model]]; cs <- DIAG$modelos$cs_fof; nm <- minfo(model, "label")
  c <- d$cm; pos <- c$tp + c$fn
  base <- tx(sprintf("%s: AUC-ROC %.3f, precisión media (AUC-PR) %.3f, Brier %.3f y error de calibración ECE %.3f. Con umbral 0.5 detecta %s de %s incumplimientos con %s falsas alarmas.",
                     nm, d$auc, d$ap, d$brier, d$ece, num(c$tp), num(pos), num(c$fp)),
             sprintf("%s: ROC-AUC %.3f, average precision (PR-AUC) %.3f, Brier %.3f and calibration error ECE %.3f. At the 0.5 threshold it detects %s of %s defaults with %s false alarms.",
                     nm, d$auc, d$ap, d$brier, d$ece, num(c$tp), num(pos), num(c$fp)))
  if (model != "cs_fof")
    base <- paste(base, tx(sprintf("CS-FOF (línea punteada): AUC-ROC %.3f y ECE %.3f.", cs$auc, cs$ece),
                           sprintf("CS-FOF (dotted line): ROC-AUC %.3f and ECE %.3f.", cs$auc, cs$ece)))
  tech <- tx("Predicciones fuera de pliegue de los 29,965 clientes: cada modelo se reentrenó con los hiperparámetros que eligió en cada pliegue externo. Las curvas ROC y precisión-recall miden cómo ordena a los clientes, sin depender del umbral; la de calibración compara la probabilidad predicha con la tasa real en 10 grupos (la diagonal es la calibración perfecta). Todos los modelos con pesos de clase o SMOTE quedan por debajo de la diagonal: sobreestiman el riesgo.",
             "Out-of-fold predictions for the 29,965 clients: each model was refit with the hyperparameters it chose in each outer fold. The ROC and precision-recall curves measure how it ranks clients, regardless of the threshold; the calibration curve compares the predicted probability with the observed rate in 10 bins (the diagonal is perfect calibration). All models with class weights or SMOTE fall below the diagonal: they overestimate risk.")
  interp_block(base, tech)
}

fig_cd <- function(fuente) {
  F <- DIAG$friedman[[fuente]]
  r <- sort(unlist(F$rangos)); k <- length(r); cd <- F$cd; vals <- unname(r)
  grupos <- list()
  for (a in seq_len(k)) {
    b <- max(which(vals - vals[a] <= cd))
    if (b > a && (!length(grupos) || b > grupos[[length(grupos)]][2])) grupos[[length(grupos) + 1]] <- c(a, b)
  }
  shapes <- list(list(type = "line", x0 = 1, x1 = k, y0 = 0, y1 = 0, line = list(color = GREY_BLUE, width = 1.5)),
                 list(type = "line", x0 = 1, x1 = 1 + cd, y0 = 0.9, y1 = 0.9, line = list(color = WARM_GOLD, width = 4)))
  for (g in seq_along(grupos)) {
    ab <- grupos[[g]]; y <- -0.35 - 0.18 * (g - 1)
    shapes[[length(shapes) + 1]] <- list(type = "line", x0 = vals[ab[1]] - .05, x1 = vals[ab[2]] + .05, y0 = y, y1 = y,
                                         line = list(color = NAVY, width = 6))
  }
  es_cs <- names(r) == "cs_fof"
  p <- plot_ly(x = vals, y = rep(0, k), type = "scatter", mode = "markers+text",
               text = vapply(names(r), minfo, "", "label"), customdata = vals,
               textposition = ifelse(seq_len(k) %% 2 == 1, "top center", "bottom center"),
               marker = list(size = ifelse(es_cs, 16, 11), color = ifelse(es_cs, WARM_GOLD, NAVY), line = list(width = 1.5, color = WHITE)),
               textfont = list(size = 11), showlegend = FALSE,
               hovertemplate = paste0("%{text}<br>", tx("Rango medio", "Mean rank"), ": %{customdata:.2f}<extra></extra>"))
  p <- layout(p, shapes = shapes,
              annotations = list(list(x = 1 + cd / 2, y = 1.05, showarrow = FALSE, font = list(color = WARM_GOLD, size = 12),
                                      text = tx(sprintf("Diferencia crítica = %.2f", cd), sprintf("Critical difference = %.2f", cd)))),
              xaxis = list(range = c(0.5, k + 0.5), dtick = 1, showgrid = FALSE, title = tx("Rango medio (1 = mejor)", "Mean rank (1 = best)")),
              yaxis = list(visible = FALSE, range = c(-0.35 - 0.18 * length(grupos) - 0.2, 1.2)))
  style_fig(p, 340, legend_top = FALSE, margin = list(l = 30, r = 30, t = 30, b = 50))
}

cd_interp <- function(fuente) {
  F <- DIAG$friedman[[fuente]]; r <- unlist(F$rangos)
  if (fuente == "taiwan") {
    base <- tx(sprintf("CS-FOF tiene el mejor rango medio (%.1f), seguido de XGBoost (%.1f) y Random Forest (%.1f). Las barras azules unen modelos que no se distinguen: CS-FOF queda en el mismo grupo que esos dos.",
                       r[["cs_fof"]], r[["xgboost"]], r[["random_forest"]]),
               sprintf("CS-FOF has the best mean rank (%.1f), followed by XGBoost (%.1f) and Random Forest (%.1f). The blue bars join models that cannot be told apart: CS-FOF is in the same group as those two.",
                       r[["cs_fof"]], r[["xgboost"]], r[["random_forest"]]))
    tech <- tx(sprintf("Friedman sobre los 5 pliegues externos de Taiwán: χ² = %.1f, p = %.1e; diferencia crítica de Nemenyi %.2f. Con un solo conjunto los pliegues no son bloques independientes, así que esta vista es descriptiva; la comparación entre conjuntos es la que usa bloques independientes.", F$chi2, F$p, F$cd),
               sprintf("Friedman over the 5 outer folds of Taiwan: χ² = %.1f, p = %.1e; Nemenyi critical difference %.2f. With a single dataset the folds are not independent blocks, so this view is descriptive; the across-datasets comparison is the one with independent blocks.", F$chi2, F$p, F$cd))
  } else {
    base <- tx(sprintf("En los 4 conjuntos (Taiwán, German, Australian y Polish), XGBoost es primero (%.2f), seguido de Random Forest (%.2f) y de CS-FOF (%.2f), que pierde terreno en Polish, con 4 %% de quiebras.",
                       r[["xgboost"]], r[["random_forest"]], r[["cs_fof"]]),
               sprintf("Across the 4 datasets (Taiwan, German, Australian and Polish), XGBoost is first (%.2f), followed by Random Forest (%.2f) and CS-FOF (%.2f), which loses ground on Polish, with 4%% bankruptcies.",
                       r[["xgboost"]], r[["random_forest"]], r[["cs_fof"]]))
    tech <- tx(sprintf("Friedman con corrección de Iman-Davenport, cada conjunto como bloque: F = %.2f, p = %.4f; diferencia crítica de Nemenyi %.2f. Con 4 conjuntos la potencia es baja.", F$F, F$p, F$cd),
               sprintf("Friedman with the Iman-Davenport correction, each dataset as a block: F = %.2f, p = %.4f; Nemenyi critical difference %.2f. With 4 datasets the power is low.", F$F, F$p, F$cd))
  }
  interp_block(base, tech)
}

fig_shap_global <- function(model) {
  S <- DIAG$shap_global; otro <- if (model == "cs_fof") "xgboost" else "cs_fof"
  d <- data.frame(f = unlist(S$variables), m = .num(S[[model]]), o = .num(S[[otro]]), stringsAsFactors = FALSE)
  d <- utils::tail(d[order(d$m), ], 10)
  y <- fx(vapply(d$f, feat_lbl, ""))
  p <- plot_ly()
  p <- add_trace(p, y = y, x = d$o, type = "bar", orientation = "h", name = minfo(otro, "label"), opacity = .55,
                 marker = list(color = if (otro == "cs_fof") PALE_GOLD else GREY_BLUE),
                 hovertemplate = paste0("%{y}: %{x:.4f}<extra>", minfo(otro, "label"), "</extra>"))
  p <- add_trace(p, y = y, x = d$m, type = "bar", orientation = "h", name = minfo(model, "label"),
                 marker = list(color = if (model == "cs_fof") WARM_GOLD else NAVY),
                 hovertemplate = paste0("%{y}: %{x:.4f}<extra>", minfo(model, "label"), "</extra>"))
  p <- layout(p, barmode = "group", xaxis = list(title = tx("Importancia media |SHAP| (probabilidad)", "Mean |SHAP| importance (probability)")),
              yaxis = list(title = "", showgrid = FALSE))
  style_fig(p, 400, margin = list(l = 170, r = 20, t = 40, b = 46))
}

shap_global_interp <- function(model) {
  S <- DIAG$shap_global
  p2 <- function(m) { v <- stats::setNames(.num(S[[m]]), unlist(S$variables)); v[["PAY_2"]] / v[["PAY_0"]] }
  interp_block(
    tx(sprintf("CS-FOF y XGBoost usan casi las mismas variables (correlación de Spearman %.2f entre sus importancias): el atraso de septiembre (PAY_0) y el cupo dominan. En CS-FOF el atraso de agosto (PAY_2) pesa el %s de PAY_0; en XGBoost, el %s.",
               S$spearman, pct(p2("cs_fof"), 0), pct(p2("xgboost"), 0)),
       sprintf("CS-FOF and XGBoost use almost the same variables (Spearman correlation %.2f between their importances): the September delay (PAY_0) and the limit dominate. In CS-FOF the August delay (PAY_2) weighs %s of PAY_0; in XGBoost, %s.",
               S$spearman, pct(p2("cs_fof"), 0), pct(p2("xgboost"), 0))),
    tx("SHAP por permutación (el mismo explicador para los dos, porque CS-FOF no es un árbol de scikit-learn) en 300 clientes de prueba del pliegue externo 1, con 50 clientes de fondo; los valores suman exactamente la probabilidad de cada cliente. Las barras tenues son el otro modelo.",
       "Permutation SHAP (the same explainer for both, because CS-FOF is not a scikit-learn tree) on 300 test clients of outer fold 1, with 50 background clients; the values add up exactly to each client's probability. The faint bars are the other model."))
}

# ---------- Carrusel de modelos (mismo diseño de tarjeta de crédito del Dash) ----------
mc_bar <- function(label, v, scale = 1, cls = "") {
  if (is.na(v)) return(div(class = "mc-metric", tags$span(label), div(class = "mc-bar na"),
                           tags$b(title = tx("No calculado", "Not computed"), tx("n/d", "n/a"))))
  div(class = trimws(paste("mc-metric", cls)), tags$span(label),
      div(class = "mc-bar", tags$span(style = sprintf("width:%.1f%%", min(v / scale, 1) * 100))),
      tags$b(sprintf("%.3f", v)))
}

model_slide <- function(row, rank) {
  m <- row$model; best <- rank == 1
  sub <- MR[MR$model == m, ]
  by_tech <- tapply(sub$f1_mean, sub$technique, max)
  top <- div(class = "mc-top", tags$span(class = "mc-rank", paste0("#", rank)),
             if (best) tags$span(class = "mc-badge", icon_("trophy"), tx("Mayor F1 medio", "Highest mean F1")) else
               tags$span(class = "mc-fam-top", tx(sprintf("%+.4f F1 vs. el mejor", row$f1_mean - F1_MAX),
                                                  sprintf("%+.4f F1 vs. the best", row$f1_mean - F1_MAX))))
  tags$article(class = paste0("mc-slide", if (best) " best" else ""),
    `aria-label` = tx(sprintf("Puesto %d: %s, F1 %.3f", rank, minfo(m, "label"), row$f1_mean),
                      sprintf("Rank %d: %s, F1 %.3f", rank, minfo(m, "label"), row$f1_mean)),
    div(class = "cc-gloss"), top,
    tags$h3(class = "mc-name", minfo(m, "label")),
    div(class = "mc-family", minfo(m, "family")),
    div(class = "mc-score", div(class = "cc-chip mc-chip"),
        div(tags$span(class = "cc-lbl", tx("F1 · clase default", "F1 · default class")),
            div(tags$span(class = "mc-f1", sprintf("%.3f", row$f1_mean)), tags$span(class = "mc-std", sprintf("± %.3f", row$f1_std))))),
    div(class = "mc-config", title = tx("Técnica de balanceo y método de optimización de su mejor combinación",
                                        "Balancing technique and optimization method of its best combination"),
        tags$span(class = "mc-pill", tech_lbl(row$technique)), tags$span(class = "mc-pill", method_lbl(row$method))),
    div(class = "mc-metrics", mc_bar(tx("Precisión", "Precision"), row$precision_mean), mc_bar("Recall", row$recall_mean),
        mc_bar("ROC-AUC", row$roc_auc_mean), mc_bar("PR-AUC", row$pr_auc_mean)),
    div(class = "mc-metrics mc-tech",
        tags$span(class = "cc-lbl", tx("Mejor F1 con cada técnica de balanceo", "Best F1 with each balancing technique")),
        lapply(TECH_ORDER, function(t) mc_bar(tech_lbl(t), if (t %in% names(by_tech)) by_tech[[t]] else NA, F1_MAX,
                                              if (t == row$technique) "on" else ""))),
    tags$p(class = "mc-desc", minfo(m, "desc")),
    tags$p(class = "mc-note", minfo(m, "note")),
    div(class = "mc-foot", tx(sprintf("%d combinaciones · F1 de %.3f a %.3f", nrow(sub), min(sub$f1_mean), max(sub$f1_mean)),
                              sprintf("%d combinations · F1 from %.3f to %.3f", nrow(sub), min(sub$f1_mean), max(sub$f1_mean)))))
}

models_carousel <- function() {
  n <- nrow(BEST_BY_MODEL)
  slides <- lapply(seq_len(n), function(i) model_slide(BEST_BY_MODEL[i, ], i))
  dots <- lapply(seq_len(n), function(i) tags$button(class = "mc-dot", type = "button", `data-i` = i - 1,
                                                     title = minfo(BEST_BY_MODEL$model[i], "label"),
                                                     `aria-label` = paste(tx("Ver", "Show"), minfo(BEST_BY_MODEL$model[i], "label"))))
  div(class = "mc-wrap",
      div(class = "mc-stage",
          tags$button(class = "mc-nav mc-prev", type = "button", title = tx("Modelo anterior", "Previous model"), icon_("chevron")),
          div(class = "mc-track", tabindex = "0", role = "region",
              `aria-label` = tx("Carrusel de modelos; usa las flechas para desplazarte", "Model carousel; use the arrows to move"),
              slides),
          tags$button(class = "mc-nav mc-next", type = "button", title = tx("Modelo siguiente", "Next model"), icon_("chevron"))),
      div(class = "mc-dots", dots),
      tags$p(class = "muted mc-hint", tx(sprintf("Desliza, usa las flechas o los puntos para recorrer los %d modelos.", n),
                                         sprintf("Swipe, or use the arrows or dots to browse the %d models.", n))))
}

page_models <- function(sel = list()) {
  b <- BEST; best_lbl <- minfo(b$model, "label"); c <- CSFOF_CM
  pos <- c$tp + c$fn; flagged <- c$tp + c$fp
  tagList(
    page_title(tx("Modelos", "Models")),
    div(class = "kpi-row k4",
        kpi(tx("Combinaciones evaluadas", "Combinations evaluated"), sprintf("%d + %d", N_BASE, N_EXTRA),
            tx(sprintf("%d del diseño factorial (7 × 4 × 4) y, aparte, %d corridas de CS-FOF", N_BASE, N_EXTRA),
               sprintf("%d from the factorial design (7 × 4 × 4) and, separately, %d runs of CS-FOF", N_BASE, N_EXTRA)), "layers"),
        kpi(tx("Mejor F1 (clase default)", "Best F1 (default class)"), sprintf("%.3f", b$f1_mean),
            tx(sprintf("CS-FOF, el mayor de los modelos comparados (%s: %.3f); la diferencia no es significativa.", minfo(BEST_BASE$model, "label"), BEST_BASE$f1_mean),
               sprintf("CS-FOF, the highest of the models compared (%s: %.3f); the difference is not significant.", minfo(BEST_BASE$model, "label"), BEST_BASE$f1_mean)), "trophy"),
        kpi(tx("Mejora sobre la línea base", "Improvement over baseline"), sprintf("+%.3f", b$f1_mean - BASELINE),
            tx(sprintf("Regresión logística sin balanceo: %.3f", BASELINE), sprintf("Logistic regression without balancing: %.3f", BASELINE)), "bars"),
        kpi(tx("Incumplimientos detectados", "Defaults detected"), pct(c$tp / pos, 0),
            tx(sprintf("%s de %s · %s, predicciones fuera de pliegue (umbral 0.5)", num(c$tp), num(pos), best_lbl),
               sprintf("%s of %s · %s, out-of-fold predictions (threshold 0.5)", num(c$tp), num(pos), best_lbl)), "target")),
    card(tx(sprintf("Tabla de líderes: %d combinaciones", nrow(MR)), sprintf("Leaderboard: %d combinations", nrow(MR))),
         leaderboard(),
         interp_block(
           tx("Haz clic en un encabezado para ordenar y escribe en el buscador para filtrar (por ejemplo, «XGBoost» o «SMOTE»). La estrella marca la mejor combinación de cada modelo, elegida por el F1 medio del bucle externo de la validación anidada 5 × 5.",
              "Click a header to sort and type in the search box to filter (for example, “XGBoost” or “SMOTE”). The star marks each model's best combination, chosen by the mean F1 of the outer loop of the 5 × 5 nested validation."),
           tx("El tiempo de inferencia se midió con el pliegue 0 (5,993 clientes, 4 núcleos) para los tres mejores modelos. CS-FOF es el más lento al predecir (253 ms por cada 1,000 clientes) porque sus árboles se recorren con numpy, sin código compilado como el de las librerías de los demás.",
              "Inference time was measured on fold 0 (5,993 clients, 4 cores) for the three best models. CS-FOF is the slowest to predict (253 ms per 1,000 clients) because its trees are traversed with numpy, without compiled code like the other models' libraries."))),
    card(tx("Comparación de modelos", "Model comparison"), models_carousel()),
    div(class = "grid g2",
        card(tx("F1 por modelo y técnica de balanceo", "F1 by model and balancing technique"),
             grafica("mdl_heat", 480),
             interp_block(
               tx("Cada celda es el mejor F1 que logró el modelo con esa técnica. Sin balanceo todos rinden peor, porque casi no detectan a quienes incumplen; con pesos de clase, los tres mejores llegan a 0.55. CS-FOF solo se corrió con pesos de clase (celdas vacías).",
                  "Each cell is the best F1 the model achieved with that technique. Without balancing all of them perform worse, because they barely detect defaulters; with class weights, the top three reach 0.55. CS-FOF was only run with class weights (empty cells)."),
               tx("Comparación por factor sobre las 112 combinaciones base (Friedman con 28 bloques modelo × método): χ² = 76.0, p ≈ 2·10⁻¹⁶. Sin balanceo el F1 medio es 0.455, frente a 0.526 (pesos de clase), 0.520 (SMOTE) y 0.513 (ADASYN); «sin balanceo» es peor que las tres (Nemenyi, p ≤ 0.010). Pesos de clase supera a ADASYN (p < 10⁻⁴) y no se distingue de SMOTE (p = 0.35); SMOTE supera a ADASYN (p = 0.007). Naive Bayes es el único modelo al que el balanceo casi no le cambia el F1.",
                  "Comparison by factor over the 112 base combinations (Friedman with 28 model × method blocks): χ² = 76.0, p ≈ 2·10⁻¹⁶. Without balancing the mean F1 is 0.455, versus 0.526 (class weights), 0.520 (SMOTE) and 0.513 (ADASYN); “no balancing” is worse than all three (Nemenyi, p ≤ 0.010). Class weights beat ADASYN (p < 10⁻⁴) and are indistinguishable from SMOTE (p = 0.35); SMOTE beats ADASYN (p = 0.007). Naive Bayes is the only model whose F1 barely changes with balancing."))),
        card(tx("Balancear mueve el umbral, no la capacidad de ordenar", "Balancing moves the threshold, not the ranking ability"),
             grafica("mdl_scatter", 420),
             interp_block(
               tx(sprintf("Cada punto es una combinación: las %d del diseño factorial y las %d corridas de CS-FOF (rombos). Las que no balancean (gris) quedan abajo: aciertan poco con quienes incumplen. Pero no quedan más a la izquierda: ordenan a los clientes casi igual de bien; lo que cambia es dónde se pone el corte entre «paga» e «incumple».", N_BASE, N_EXTRA),
                  sprintf("Each point is one combination: the %d from the factorial design and the %d runs of CS-FOF (diamonds). Those without balancing (grey) sit at the bottom: they rarely get defaulters right. But they are not further to the left: they rank clients almost equally well; what changes is where the cut between “pays” and “defaults” is placed.", N_BASE, N_EXTRA)),
               tx("ROC-AUC medio por técnica (96 combinaciones sin SVM): 0.759 sin balanceo, 0.762 con pesos de clase, 0.754 con SMOTE y 0.750 con ADASYN. Al umbral de 0.5 el recall pasa de 0.378 a 0.607 y la precisión baja de 0.621 a 0.464, así que la ganancia de F1 (0.458 → 0.524) viene en gran parte del umbral y no de un modelo que discrimine mejor.",
                  "Mean ROC-AUC by technique (96 combinations without SVM): 0.759 without balancing, 0.762 with class weights, 0.754 with SMOTE and 0.750 with ADASYN. At the 0.5 threshold recall goes from 0.378 to 0.607 and precision drops from 0.621 to 0.464, so the F1 gain (0.458 → 0.524) comes largely from the threshold rather than from a model that discriminates better.")))),
    div(class = "grid g2",
        card(tx(paste("Mayor F1 medio:", best_lbl), paste("Highest mean F1:", best_lbl)),
             grafica("mdl_cm", 380),
             div(class = "kpi-row k2 kpi-compact",
                 kpi("Recall", pct(c$tp / pos, 0), tx("incumplimientos detectados", "defaults detected"), "target"),
                 kpi(tx("Precisión", "Precision"), pct(c$tp / flagged, 0), tx("de los señalados sí incumple", "of those flagged do default"), "alert"),
                 kpi(tx("Especificidad", "Specificity"), pct(c$tn / (c$tn + c$fp), 0),
                     tx("de quienes pagan, bien clasificados", "of payers, correctly classified"), "users"),
                 kpi(tx("Exactitud", "Accuracy"), pct((c$tp + c$tn) / (pos + c$tn + c$fp), 0), tx("de todos los clientes", "of all clients"), "bars")),
             interp_block(
               tx(sprintf("De los %s clientes que incumplieron, el modelo detecta %s (%s). A cambio marca %s falsas alarmas: de los %s clientes que señala como riesgosos, %s sí incumple.",
                          num(pos), num(c$tp), pct(c$tp / pos, 0), num(c$fp), num(flagged), pct(c$tp / flagged, 0)),
                  sprintf("Of the %s clients who defaulted, the model detects %s (%s). In exchange it raises %s false alarms: of the %s clients it flags as risky, %s actually default.",
                          num(pos), num(c$tp), pct(c$tp / pos, 0), num(c$fp), num(flagged), pct(c$tp / flagged, 0))),
               tx(sprintf("%s y optimización %s. Predicciones out-of-fold de los cinco modelos de los folds externos, con umbral 0.5 (AUC agrupado 0.783). Las probabilidades no están calibradas (ECE = 0.180) porque el peso de costo infla la clase positiva. Ajustar el umbral según el costo de cada tipo de error es el siguiente paso natural. XGBoost, el mejor modelo de referencia, detecta %s incumplimientos con %s falsas alarmas.",
                          tech_lbl(b$technique), tolower(method_lbl(b$method)), num(XGB_CM$tp), num(XGB_CM$fp)),
                  sprintf("%s and %s optimization. Out-of-fold predictions from the five outer-fold models, with a 0.5 threshold (pooled AUC 0.783). The probabilities are not calibrated (ECE = 0.180) because the cost weight inflates the positive class. Tuning the threshold to the cost of each type of error is the natural next step. XGBoost, the best baseline model, detects %s defaults with %s false alarms.",
                          tech_lbl(b$technique), tolower(method_lbl(b$method)), num(XGB_CM$tp), num(XGB_CM$fp))))),
        card(tx("Qué variables pesan más: SHAP global", "Which variables matter most: global SHAP"),
             div(class = "controls", control(tx("Modelo", "Model"),
                 radio_("shap_model", c("XGBoost" = "xgboost", "Random Forest" = "random_forest", "CS-FOF" = "cs_fof"), sel$shap_model %||% "xgboost"))),
             grafica("shap_graph", 420),
             uiOutput("shap_interp"),
             tags$p(class = "callout", tx("Coincide con el EDA: el historial de pagos (PAY_0 primero) es la señal más fuerte del incumplimiento, le sigue el límite de crédito, y el perfil demográfico pesa poco.",
                                          "This matches the EDA: payment history (PAY_0 first) is the strongest signal of default, followed by the credit limit, and the demographic profile matters little.")))),
    card(tx("Diagnóstico del modelo seleccionado", "Diagnostics of the selected model"),
         div(class = "controls", control(tx("Modelo", "Model"),
             radio_("diag_model", stats::setNames(DIAG_MODELS, vapply(DIAG_MODELS, minfo, "", "label")), sel$diag_model %||% "cs_fof"))),
         grafica("diag_graph", 380),
         uiOutput("diag_interp")),
    card(tx("Comparación estadística: diagrama de diferencia crítica", "Statistical comparison: critical difference diagram"),
         div(class = "controls", control(tx("Comparar sobre", "Compare over"),
             radio_("cd_src", stats::setNames(c("taiwan", "conjuntos"), c(tx("Taiwán (5 pliegues)", "Taiwan (5 folds)"), tx("4 conjuntos de datos", "4 datasets"))),
                    sel$cd_src %||% "taiwan"))),
         grafica("cd_graph", 340),
         uiOutput("cd_interp")),
    card(tx("¿LIME y SHAP explican lo mismo?", "Do LIME and SHAP explain the same thing?"),
         div(class = "grid g2", div(lime_shap_table()), grafica("lime_graph", 330)),
         interp_block(
           tx("Casi siempre coinciden en la dirección: si una variable sube el riesgo para SHAP, también lo sube para LIME. Pero no en el orden: comparten entre 3 y 4 de sus 5 variables principales.",
              "They almost always agree on direction: if a variable raises the risk for SHAP, it also raises it for LIME. But not on order: they share 3 to 4 of their top 5 variables."),
           tx("200 observaciones por modelo (10 al azar de cada celda de la matriz de confusión en cada fold) y LIME con 3 semillas. Como LIME coincide más consigo mismo (0.85 y 0.88) que con SHAP (0.72 y 0.63), la diferencia entre métodos no es solo ruido de LIME. El acuerdo es mayor en los verdaderos positivos. Solo se comparan orden y signo: SHAP está en log-odds (XGBoost) o probabilidad (Random Forest) y LIME en probabilidad.",
              "200 observations per model (10 at random from each confusion-matrix cell in each fold) and LIME with 3 seeds. Since LIME agrees more with itself (0.85 and 0.88) than with SHAP (0.72 and 0.63), the difference between methods is not just LIME noise. Agreement is highest on true positives. Only order and sign are compared: SHAP is in log-odds (XGBoost) or probability (Random Forest) and LIME in probability."))),
    card(tx("Optimizadores: mismo destino, distinto costo", "Optimizers: same destination, different cost"),
         div(class = "controls", control(tx("Modelo", "Model"),
             radio_("any_model", stats::setNames(ANY_MODELS, vapply(ANY_MODELS, minfo, "", "label")), sel$any_model %||% "xgboost"))),
         div(class = "grid g2", grafica("any_graph", 460), uiOutput("any_table")),
         uiOutput("any_interp"))
  )
}
