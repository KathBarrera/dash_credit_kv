# =============================================================================
# 5. MODELOS (resultados del repositorio Credit_Card_Project, notebooks 04, 05 y 07)
# =============================================================================
# results/model_results.csv resume las 112 combinaciones (7 modelos x 4 técnicas de
# balanceo x 4 métodos de optimización, validación cruzada anidada 3 x 3).
MR <- utils::read.csv("results/model_results.csv", stringsAsFactors = FALSE)

MODEL_INFO <- list(
  random_forest = list(
    label = c("Random Forest", "Random Forest"),
    family = c("Ensamble de árboles (bagging)", "Tree ensemble (bagging)"),
    desc = c("Promedia muchos árboles entrenados sobre muestras distintas de clientes; capta relaciones no lineales entre el historial de pagos y el riesgo.",
             "Averages many trees trained on different samples of clients; captures non-linear relationships between payment history and risk."),
    note = c("Mayor F1 medio de las 112 combinaciones. Encabeza el grupo superior junto a XGBoost y SVM, sin diferencia significativa entre los tres (Nemenyi, p ≥ 0.88).",
             "Highest mean F1 of the 112 combinations. It leads the top group together with XGBoost and SVM, with no significant difference among the three (Nemenyi, p ≥ 0.88).")),
  xgboost = list(
    label = c("XGBoost", "XGBoost"),
    family = c("Ensamble de árboles (boosting)", "Tree ensemble (boosting)"),
    desc = c("Construye árboles en secuencia: cada uno corrige los errores del anterior.",
             "Builds trees in sequence: each one corrects the errors of the previous one."),
    note = c("A menos de una milésima del primer lugar: la diferencia es mucho menor que la variación entre folds, así que en la práctica empata con Random Forest.",
             "Less than a thousandth behind first place: the difference is much smaller than the variation between folds, so in practice it ties with Random Forest.")),
  svm = list(
    label = c("SVM", "SVM"),
    family = c("Máquina de vectores de soporte (kernel RBF)", "Support vector machine (RBF kernel)"),
    desc = c("Busca la frontera que separa mejor a quienes pagan de quienes incumplen, con un margen máximo.",
             "Looks for the boundary that best separates payers from defaulters, with maximum margin."),
    note = c("Corrida en Colab con GPU (cuML): no es estrictamente comparable con los demás modelos y no tiene PR-AUC calculado.",
             "Run on Colab with a GPU (cuML): not strictly comparable with the other models and without a computed PR-AUC.")),
  knn = list(
    label = c("KNN", "KNN"),
    family = c("Vecinos más cercanos", "Nearest neighbors"),
    desc = c("Clasifica a cada cliente según lo que hicieron los clientes más parecidos a él.",
             "Classifies each client according to what the most similar clients did."),
    note = c("Con pesos de clase usa un ajuste propio del proyecto (el voto de cada vecino se pondera por la rareza de su clase), no un mecanismo estándar de scikit-learn.",
             "With class weights it uses a project-specific adjustment (each neighbor's vote is weighted by the rarity of its class), not a standard scikit-learn mechanism.")),
  decision_tree = list(
    label = c("Árbol de decisión", "Decision tree"),
    family = c("Árbol de clasificación", "Classification tree"),
    desc = c("Una secuencia de preguntas sí/no sobre las variables; fácil de leer, pero inestable.",
             "A sequence of yes/no questions about the variables; easy to read, but unstable."),
    note = c("Queda por debajo del grupo superior: Random Forest lo supera de forma significativa (p = 0.018).",
             "It falls below the top group: Random Forest beats it significantly (p = 0.018).")),
  logistic_regression = list(
    label = c("Regresión logística", "Logistic regression"),
    family = c("Modelo lineal · línea base", "Linear model · baseline"),
    desc = c("Modelo de referencia: combina las variables de forma lineal para estimar la probabilidad de default.",
             "Reference model: combines the variables linearly to estimate the probability of default."),
    note = c("Sin balanceo es la combinación con menor F1 (0.378): solo detecta 26 % de quienes incumplen. Con SMOTE o pesos de clase sube a 0.515, con un ROC-AUC casi igual.",
             "Without balancing it is the combination with the lowest F1 (0.378): it detects only 26% of defaulters. With SMOTE or class weights it rises to 0.515, with almost the same ROC-AUC.")),
  naive_bayes = list(
    label = c("Naive Bayes", "Naive Bayes"),
    family = c("Probabilístico (gaussiano)", "Probabilistic (Gaussian)"),
    desc = c("Aplica el teorema de Bayes suponiendo que las variables son independientes entre sí.",
             "Applies Bayes' theorem assuming the variables are independent of each other."),
    note = c("Ese supuesto no se cumple con el historial de pagos, muy correlacionado mes a mes; por eso el balanceo casi no lo cambia (F1 entre 0.494 y 0.499).",
             "That assumption does not hold for payment history, which is highly correlated month to month; that is why balancing barely changes it (F1 between 0.494 and 0.499)."))
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
BASELINE <- max(MR$f1_mean[MR$model == "logistic_regression" & MR$technique == "none"])
F1_MAX <- max(MR$f1_mean)
# Matriz de confusión out-of-fold de la mejor combinación (05_results_analysis.ipynb)
BEST_CM <- list(tn = 19295, fp = 4040, fn = 2624, tp = 4006)
TECH_COLORS <- c(none = GREY_BLUE, class_weight = WARM_GOLD, smote = DEEP_NAVY, adasyn = MID_BLUE)

fig_models_heat <- function() {
  ord <- BEST_BY_MODEL$model
  z <- sapply(TECH_ORDER, function(t) sapply(ord, function(m) max(MR$f1_mean[MR$model == m & MR$technique == t])))
  p <- plot_ly(z = unname(z), x = vapply(TECH_ORDER, tech_lbl, ""), y = vapply(ord, minfo, "", "label"),
               type = "heatmap", colorscale = SEQ_GOLD, texttemplate = "%{z:.3f}", textfont = list(size = 13),
               xgap = 3, ygap = 3, colorbar = list(title = "F1", thickness = 12),
               hovertemplate = paste0("%{y} · %{x}<br>", tx("Mejor F1", "Best F1"), ": %{z:.4f}<extra></extra>"))
  p <- layout(p, yaxis = list(autorange = "reversed", showgrid = FALSE, title = ""),
              xaxis = list(side = "top", showgrid = FALSE, title = ""))
  style_fig(p, 400, legend_top = FALSE, margin = list(l = 130, r = 20, t = 24, b = 40))
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

fig_best_cm <- function() {
  c <- BEST_CM
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
  style_fig(p, 340, legend_top = FALSE, margin = list(l = 100, r = 20, t = 24, b = 40))
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
             if (best) tags$span(class = "mc-badge", icon_("trophy"), tx("Mejor modelo", "Best model")) else
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
    div(class = "mc-foot", tx(sprintf("16 combinaciones · F1 de %.3f a %.3f", min(sub$f1_mean), max(sub$f1_mean)),
                              sprintf("16 combinations · F1 from %.3f to %.3f", min(sub$f1_mean), max(sub$f1_mean)))))
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
      tags$p(class = "muted mc-hint", tx("Desliza, usa las flechas o los puntos para recorrer los siete modelos.",
                                         "Swipe, or use the arrows or dots to browse the seven models.")))
}

page_models <- function() {
  b <- BEST; best_lbl <- minfo(b$model, "label"); c <- BEST_CM
  pos <- c$tp + c$fn; flagged <- c$tp + c$fp
  tagList(
    page_title(tx("Modelos", "Models")),
    div(class = "kpi-row k4",
        kpi(tx("Combinaciones evaluadas", "Combinations evaluated"), nrow(MR),
            tx("7 modelos × 4 balanceos × 4 optimizadores", "7 models × 4 balancing × 4 optimizers"), "layers"),
        kpi(tx("Mejor F1 (clase default)", "Best F1 (default class)"), sprintf("%.3f", b$f1_mean),
            paste(best_lbl, "·", tech_lbl(b$technique)), "trophy"),
        kpi(tx("Mejora sobre la línea base", "Improvement over baseline"), sprintf("+%.3f", b$f1_mean - BASELINE),
            tx(sprintf("Regresión logística sin balanceo: %.3f", BASELINE), sprintf("Logistic regression without balancing: %.3f", BASELINE)), "bars"),
        kpi(tx("Incumplimientos detectados", "Defaults detected"), pct(b$recall_mean, 0),
            tx("Recall del mejor modelo (umbral 0.5)", "Recall of the best model (threshold 0.5)"), "target")),
    card(tx("Comparación de modelos", "Model comparison"), models_carousel()),
    div(class = "grid g2",
        card(tx("F1 por modelo y técnica de balanceo", "F1 by model and balancing technique"),
             grafica("mdl_heat", 400),
             interp_block(
               tx("Cada celda es el mejor F1 que logró el modelo con esa técnica. Sin balanceo todos rinden peor, porque casi no detectan a quienes incumplen; con pesos de clase, Random Forest y XGBoost llegan a 0.55.",
                  "Each cell is the best F1 the model achieved with that technique. Without balancing all of them perform worse, because they barely detect defaulters; with class weights, Random Forest and XGBoost reach 0.55."),
               tx("Comparación por factor (Friedman con 28 bloques modelo × método): χ² = 59.8, p ≈ 7·10⁻¹³. Sin balanceo el F1 medio es 0.453, frente a 0.526 (pesos de clase), 0.519 (SMOTE) y 0.513 (ADASYN); «sin balanceo» es peor que las tres (Nemenyi, p ≤ 10⁻⁴). Pesos de clase supera a ADASYN (p = 0.020) y no se distingue de SMOTE (p = 0.67). Naive Bayes es el único modelo al que el balanceo casi no le cambia el F1.",
                  "Comparison by factor (Friedman with 28 model × method blocks): χ² = 59.8, p ≈ 7·10⁻¹³. Without balancing the mean F1 is 0.453, versus 0.526 (class weights), 0.519 (SMOTE) and 0.513 (ADASYN); “no balancing” is worse than all three (Nemenyi, p ≤ 10⁻⁴). Class weights beat ADASYN (p = 0.020) and are indistinguishable from SMOTE (p = 0.67). Naive Bayes is the only model whose F1 barely changes with balancing."))),
        card(tx("Balancear mueve el umbral, no la capacidad de ordenar", "Balancing moves the threshold, not the ranking ability"),
             grafica("mdl_scatter", 420),
             interp_block(
               tx("Cada punto es una de las 112 combinaciones. Las que no balancean (gris) quedan abajo: aciertan poco con quienes incumplen. Pero no quedan más a la izquierda: ordenan a los clientes casi igual de bien; lo que cambia es dónde se pone el corte entre «paga» e «incumple».",
                  "Each point is one of the 112 combinations. Those without balancing (grey) sit at the bottom: they rarely get defaulters right. But they are not further to the left: they rank clients almost equally well; what changes is where the cut between “pays” and “defaults” is placed."),
               tx("ROC-AUC medio por técnica (96 combinaciones locales): 0.758 sin balanceo, 0.761 con pesos de clase, 0.754 con SMOTE y 0.749 con ADASYN. Al umbral de 0.5 el recall pasa de 0.377 a 0.610 y la precisión baja de 0.618 a 0.460, así que la ganancia de F1 (0.456 → 0.523) viene en gran parte del umbral y no de un modelo que discrimine mejor.",
                  "Mean ROC-AUC by technique (96 local combinations): 0.758 without balancing, 0.761 with class weights, 0.754 with SMOTE and 0.749 with ADASYN. At the 0.5 threshold recall goes from 0.377 to 0.610 and precision drops from 0.618 to 0.460, so the F1 gain (0.456 → 0.523) comes largely from the threshold rather than from a model that discriminates better.")))),
    div(class = "grid g2",
        card(tx(paste("Mejor combinación:", best_lbl), paste("Best combination:", best_lbl)),
             grafica("mdl_cm", 340),
             interp_block(
               tx(sprintf("De los %s clientes que incumplieron, el modelo detecta %s (%s). A cambio marca %s falsas alarmas: de los %s clientes que señala como riesgosos, %s sí incumple.",
                          num(pos), num(c$tp), pct(c$tp / pos, 0), num(c$fp), num(flagged), pct(c$tp / flagged, 0)),
                  sprintf("Of the %s clients who defaulted, the model detects %s (%s). In exchange it raises %s false alarms: of the %s clients it flags as risky, %s actually default.",
                          num(pos), num(c$tp), pct(c$tp / pos, 0), num(c$fp), num(flagged), pct(c$tp / flagged, 0))),
               tx(sprintf("%s y optimización %s. Predicciones out-of-fold de los tres modelos de los folds externos, con umbral 0.5 (AUC agrupado 0.781). Las probabilidades no están calibradas (ECE = 0.196) porque el balanceo infla la clase positiva; una recalibración isotónica la baja a 0.017 en un fold. Ajustar el umbral según el costo de cada tipo de error es el siguiente paso natural.",
                          tech_lbl(b$technique), tolower(method_lbl(b$method))),
                  sprintf("%s and %s optimization. Out-of-fold predictions from the three outer-fold models, with a 0.5 threshold (pooled AUC 0.781). The probabilities are not calibrated (ECE = 0.196) because balancing inflates the positive class; isotonic recalibration lowers it to 0.017 on one fold. Tuning the threshold to the cost of each type of error is the natural next step.",
                          tech_lbl(b$technique), tolower(method_lbl(b$method)))))),
        card(tx("Qué variables pesan más en el mejor modelo (SHAP)", "Which variables matter most in the best model (SHAP)"),
             ul_(list(
               tagList(tags$b(tx("PAY_0 domina: ", "PAY_0 dominates: ")),
                       tx("el atraso de septiembre es, con diferencia, la variable más importante; más meses de atraso empujan la predicción hacia el default.",
                          "September's delay is by far the most important variable; more months of delay push the prediction toward default.")),
               tagList(tags$b(tx("Le siguen PAY_2 y PAY_3, ", "PAY_2 and PAY_3 follow, ")),
                       tx("y más abajo PAY_4 a PAY_6: en todas, más atraso, más riesgo.", "and further down PAY_4 to PAY_6: in all of them, more delay means more risk.")),
               tagList(tags$b(tx("Mayor límite de crédito, menor riesgo: ", "Higher credit limit, lower risk: ")),
                       tx("los valores altos de LIMIT_BAL reducen la probabilidad de default.", "high LIMIT_BAL values reduce the probability of default.")),
               tagList(tags$b(tx("Montos pagados y facturados: ", "Paid and billed amounts: ")),
                       tx("pagar más se asocia con menor riesgo, pero con un efecto individual pequeño; la facturación media aparece quinta y discrimina poco.",
                          "paying more is associated with lower risk, but with a small individual effect; average billing comes fifth and discriminates little.")))),
             tags$p(class = "callout", tx("Coincide con el EDA: el historial de pagos es la señal más fuerte del incumplimiento y el perfil demográfico pesa poco.",
                                          "This matches the EDA: payment history is the strongest signal of default and the demographic profile matters little."))))
  )
}
