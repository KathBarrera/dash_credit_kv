# =============================================================================
# 10. MODELO ORIGINAL: CS-FOF (Cost-Sensitive Fisher Oblique Forest)
# Cuatro pestañas en orden de presentación: Teoría, Metodología, Código y Resultados.
# Las cifras de las pruebas salen de experiments/comparacion_final del repositorio del proyecto.
# =============================================================================

# ---------- Teoría visual: corte recto frente a corte oblicuo con clientes reales ----------
# Dos variables de este conjunto (límite de crédito y monto pagado en septiembre, en log10). Se comparan
# el mejor corte recto (una variable), un árbol clásico de 3 niveles (hasta 7 cortes rectos) y un solo
# corte en la dirección de Fisher ponderada por costo, que es lo que CS-FOF evalúa en cada nodo.
csfof_toy <- function() {
  a <- log10(df$LIMIT_BAL)
  b <- log10(pmax(df$PAY_AMT1, 0) + 1)
  y <- df[[TARGET]]
  X <- cbind(a, b)
  c_ <- sum(y == 0) / sum(y == 1)                           # costo del moroso, como en CS-FOF
  w <- ifelse(y == 1, c_, 1)
  gini <- function(wt, pw) { p <- pw / wt; 2 * p * (1 - p) }
  W <- sum(w); P <- sum(w * y); g0 <- gini(W, P)
  ganancia <- function(hoja) {
    g0 - sum(vapply(split(seq_along(y), hoja), function(i) sum(w[i]) / W * gini(sum(w[i]), sum((w * y)[i])), 0))
  }
  # mejor umbral sobre una proyección z (97 cuantiles, al menos 50 clientes por lado)
  mejor_corte <- function(z, idx = seq_along(y), minimo = 50) {
    yy <- y[idx]; ww <- w[idx]; zz <- z
    o <- order(zz); zs <- zz[o]; cw <- cumsum(ww[o]); cp <- cumsum((ww * yy)[o])
    Wn <- sum(ww); Pn <- sum(ww * yy); best <- 0; thr <- NA
    for (q in unique(stats::quantile(zs, seq(.02, .98, length.out = 97), names = FALSE))) {
      i <- findInterval(q, zs)
      if (i < minimo || i > length(zs) - minimo) next
      wl <- cw[i]; pl <- cp[i]
      g <- gini(Wn, Pn) - wl / Wn * gini(wl, pl) - (Wn - wl) / Wn * gini(Wn - wl, Pn - pl)
      if (g > best) { best <- g; thr <- q }
    }
    list(g = best, t = thr)
  }
  g_axis <- max(mejor_corte(a)$g, mejor_corte(b)$g)
  mu <- colMeans(X); sd_ <- apply(X, 2, stats::sd)
  Z <- sweep(sweep(X, 2, mu), 2, sd_, "/")
  fisher <- function(idx) {
    yy <- y[idx]; ww <- w[idx]; zz <- Z[idx, , drop = FALSE]
    m1 <- colSums(zz[yy == 1, ] * ww[yy == 1]) / sum(ww[yy == 1]); m0 <- colMeans(zz[yy == 0, ])
    solve(stats::cov(zz[yy == 1, ]) + stats::cov(zz[yy == 0, ]) + 0.1 * diag(2), m1 - m0)
  }
  v <- fisher(seq_along(y))
  oc <- mejor_corte(as.vector(Z %*% v))
  # árbol oblicuo de 3 cortes (Fisher en cada nodo) para comparar con el mismo número de cortes rectos
  corte_en <- function(idx) {
    vv <- fisher(idx); s <- as.vector(Z[idx, ] %*% vv)
    r <- mejor_corte(s, idx, minimo = 200)
    if (is.na(r$t)) rep(TRUE, length(idx)) else s <= r$t
  }
  hojas <- integer(length(y)); izq <- corte_en(seq_along(y)); hojas[!izq] <- 1L
  for (k in 0:1) { s_ <- which(hojas == k); hojas[s_[!corte_en(s_)]] <- 10L + k }
  g_obl3 <- ganancia(hojas)
  # árboles clásicos (CART con los mismos pesos): 3 niveles y 2 niveles
  dat <- data.frame(a = a, b = b, y = factor(y))
  cart <- function(d) rpart::rpart(y ~ a + b, data = dat, weights = w, method = "class",
                                   # cp = -1: crece completo (rpart poda por errores de clasificación, no por Gini)
                                   control = rpart::rpart.control(maxdepth = d, minbucket = 200, minsplit = 400, cp = -1,
                                                                  xval = 0, maxcompete = 0, maxsurrogate = 0))
  tree <- cart(3)
  g_tree <- ganancia(tree$where)
  g_axis3 <- ganancia(cart(2)$where)
  # segmentos de cada corte recto del árbol, dentro de la región de su nodo (la «escalera»)
  fr <- tree$frame; internos <- which(fr$var != "<leaf>")
  sp <- tree$splits; nodos <- as.integer(rownames(fr)); segs <- list()
  recorrer <- function(nodo, x0, x1, y0, y1) {
    k <- match(nodo, nodos)
    if (is.na(k) || fr$var[k] == "<leaf>") return(invisible())
    j <- match(k, internos); var <- as.character(fr$var[k]); th <- sp[j, "index"]; izq_menor <- sp[j, "ncat"] < 0
    if (var == "a") {
      segs[[length(segs) + 1]] <<- list(x = c(th, th), y = c(y0, y1))
      if (izq_menor) { recorrer(2 * nodo, x0, th, y0, y1); recorrer(2 * nodo + 1, th, x1, y0, y1) }
      else { recorrer(2 * nodo, th, x1, y0, y1); recorrer(2 * nodo + 1, x0, th, y0, y1) }
    } else {
      segs[[length(segs) + 1]] <<- list(x = c(x0, x1), y = c(th, th))
      if (izq_menor) { recorrer(2 * nodo, x0, x1, y0, th); recorrer(2 * nodo + 1, x0, x1, th, y1) }
      else { recorrer(2 * nodo, x0, x1, th, y1); recorrer(2 * nodo + 1, x0, x1, y0, th) }
    }
  }
  recorrer(1L, min(a), max(a), 0, max(b))
  gx <- seq(min(a), max(a), length.out = 220); gy <- seq(0, max(b), length.out = 220)
  G <- expand.grid(a = gx, b = gy)
  reg_tree <- matrix(as.integer(as.character(stats::predict(tree, G, type = "class"))), nrow = length(gy), byrow = TRUE)
  zg <- as.vector(sweep(sweep(as.matrix(G), 2, mu), 2, sd_, "/") %*% v)
  reg_obl <- matrix(as.integer(zg > oc$t), nrow = length(gy), byrow = TRUE)
  set.seed(42)
  idx <- c(sample(which(y == 0), 1300), sample(which(y == 1), 1300))
  list(a = a[idx] + stats::rnorm(length(idx), 0, .03), b = b[idx] + stats::rnorm(length(idx), 0, .03), y = y[idx],
       gx = gx, gy = gy, reg_tree = reg_tree, reg_obl = reg_obl, segs = segs, g_axis = g_axis, g_tree = g_tree,
       g_obl = oc$g, g_axis3 = g_axis3, g_obl3 = g_obl3, n_cuts = length(internos), c = c_, v = v / max(abs(v)))
}
CS_TOY <- csfof_toy()

fig_csfof_toy <- function(kind) {
  T_ <- CS_TOY
  reg <- if (kind == "tree") T_$reg_tree else T_$reg_obl
  p <- plot_ly() |>
    add_trace(x = T_$gx, y = T_$gy, z = reg, type = "heatmap", showscale = FALSE, hoverinfo = "skip", zsmooth = FALSE,
              colorscale = list(c(0, "rgba(0,0,0,0)"), c(1, paste0(DEEP_RGBA, "0.13)"))))
  for (k in 0:1) {
    m <- T_$y == k
    p <- add_trace(p, x = T_$a[m], y = T_$b[m], type = "scattergl", mode = "markers", hoverinfo = "skip",
                   name = if (k == 0) tx("Paga", "Pays") else tx("Incumple", "Defaults"),
                   marker = list(size = 4, color = if (k == 0) GREY_BLUE else WARM_GOLD, opacity = if (k == 0) .55 else .75))
  }
  if (kind == "tree") {
    for (s in T_$segs) p <- add_trace(p, x = s$x, y = s$y, type = "scatter", mode = "lines", showlegend = FALSE,
                                      hoverinfo = "skip", line = list(color = DEEP_NAVY, width = 2.2))
  } else {
    p <- add_trace(p, x = T_$gx, y = T_$gy, z = reg, type = "contour", showscale = FALSE, hoverinfo = "skip",
                   contours = list(start = .5, end = .5, size = 1, coloring = "none"),
                   line = list(color = DEEP_NAVY, width = 2.4), showlegend = FALSE)
  }
  p <- layout(p,
    xaxis = list(title = tx("Límite de crédito (NT$)", "Credit limit (NT$)"),
                 tickvals = c(4, log10(3e4), 5, log10(3e5), 6), ticktext = c("10k", "30k", "100k", "300k", "1M")),
    yaxis = list(title = tx("Pagó en septiembre (NT$)", "Paid in September (NT$)"),
                 tickvals = c(0, 2, 3, 4, 5, 6), ticktext = c("0", "100", "1k", "10k", "100k", "1M")))
  config(style_fig(p, 360, margin = list(l = 70, r = 16, t = 40, b = 55)), displayModeBar = FALSE)
}

cs_step <- function(n, title, body, formula = NULL) {
  div(class = "cs-step", tags$span(class = "cs-num", n), tags$h4(title), tags$p(body),
      if (!is.null(formula)) div(class = "formula", paste0("$$", formula, "$$")))
}

csfof_theory <- function() {
  T_ <- CS_TOY
  rho_pay <- CORR["PAY_0", "PAY_2"]
  bc <- stats::cor(df[paste0("BILL_AMT", 1:6)], method = "spearman")
  bmin <- min(bc[upper.tri(bc)])
  mejora <- T_$g_obl / T_$g_axis - 1
  tagList(
    card(tx("La idea en una imagen", "The idea in one picture"),
      tags$p(tx("Cada punto es un cliente real. Un árbol clásico solo puede cortar en línea recta sobre una variable a la vez, así que para separar a quienes incumplen arma una escalera de cortes. Pero el riesgo no depende del límite o del pago por separado, sino de la combinación de ambos: es una frontera en diagonal. CS-FOF puede trazarla con un solo corte.",
                "Each point is a real client. A classic tree can only cut in a straight line on one variable at a time, so to separate defaulters it builds a staircase of cuts. But risk does not depend on the limit or the payment separately; it depends on their combination: a diagonal boundary. CS-FOF can draw it with a single cut.")),
      div(class = "grid g2",
          div(div(class = "cs-fig-t", tx(sprintf("Árbol clásico: %d cortes rectos", T_$n_cuts), sprintf("Classic tree: %d straight cuts", T_$n_cuts))),
              grafica("cs_toy_tree", 360)),
          div(div(class = "cs-fig-t on", tx("CS-FOF: 1 corte oblicuo", "CS-FOF: 1 oblique cut")), grafica("cs_toy_obl", 360))),
      tags$p(class = "muted", tx("¿Cuánto separa cada opción? Reducción de impureza (Gini ponderado) con el mismo número de cortes:",
                                 "How much does each option separate? Impurity reduction (weighted Gini) with the same number of cuts:")),
      div(class = "kpi-row k3",
          kpi(tx("Con 1 corte", "With 1 cut"), sprintf("+%.0f%%", 100 * mejora),
              tx(sprintf("oblicuo %.4f frente a recto %.4f", T_$g_obl, T_$g_axis), sprintf("oblique %.4f vs straight %.4f", T_$g_obl, T_$g_axis)), "target"),
          kpi(tx("Con 3 cortes", "With 3 cuts"), sprintf("%+.0f%%", 100 * (T_$g_obl3 / T_$g_axis3 - 1)),
              tx(sprintf("oblicuos %.4f frente a rectos %.4f", T_$g_obl3, T_$g_axis3), sprintf("oblique %.4f vs straight %.4f", T_$g_obl3, T_$g_axis3)), "layers"),
          kpi(tx(sprintf("%d cortes rectos", T_$n_cuts), sprintf("%d straight cuts", T_$n_cuts)), sprintf("%.4f", T_$g_tree),
              tx("la escalera ya alcanza a la diagonal", "the staircase catches up with the diagonal"), "bars")),
      div(class = "callout", tx("La ventaja del corte oblicuo es grande cuando hay pocos cortes y se achica a medida que la escalera de cortes rectos se acerca a la diagonal. Un bosque completo tiene miles de cortes; por eso, en los resultados, CS-FOF empata con los mejores modelos en vez de superarlos con amplitud.",
                                "The oblique cut's advantage is large when there are few cuts and shrinks as the staircase of straight cuts approaches the diagonal. A full forest has thousands of cuts; that is why, in the results, CS-FOF ties with the best models instead of clearly beating them.")),
      interp_block(
        tx("La zona sombreada es donde cada modelo diría «incumple». El árbol necesita varios escalones para seguir la diagonal; el corte oblicuo la sigue de una vez: menos límite y menos pago, más riesgo.",
           "The shaded area is where each model would say “defaults”. The tree needs several steps to follow the diagonal; the oblique cut follows it at once: lower limit and lower payment, higher risk."),
        tx(sprintf("Variables en log10, 29 965 clientes; se muestran 2 600 al azar (mitad de cada clase). Dirección de Fisher (estandarizada) ∝ (%+.2f, %+.2f). Pesos de costo c = n₀/n₁ = %.2f. El árbol clásico es CART (rpart) con profundidad 3, hoja mínima 200 y los mismos pesos. Es una ilustración en 2 variables; en el modelo real cada nodo usa √p variables al azar.", T_$v[1], T_$v[2], T_$c),
           sprintf("Variables in log10, 29,965 clients; 2,600 shown at random (half of each class). Fisher direction (standardized) ∝ (%+.2f, %+.2f). Cost weights c = n₀/n₁ = %.2f. The classic tree is CART (rpart) with depth 3, minimum leaf 200 and the same weights. It is a 2-variable illustration; in the real model each node uses √p random variables.", T_$v[1], T_$v[2], T_$c)))),
    card(tx("Cómo decide cada nodo", "How each node decides"),
      div(class = "cs-steps",
        cs_step(1, tx("Cortes rectos", "Straight cuts"),
                tx("Como en Random Forest, prueba umbrales sobre √p variables elegidas al azar.", "As in Random Forest, it tries thresholds on √p randomly chosen variables.")),
        cs_step(2, tx("Dirección de Fisher con costo", "Cost-weighted Fisher direction"),
                tx("Con los clientes de ese nodo calcula la combinación de variables que mejor separa a las dos clases, pesando más a quienes incumplen.",
                   "With the clients in that node it computes the combination of variables that best separates the two classes, giving more weight to defaulters."),
                "\\mathbf{v}=S_w^{-1}(\\mu_1-\\mu_0)"),
        cs_step(3, tx("Se queda con el mejor", "Keeps the best one"),
                tx("Compara todos los cortes con el Gini ponderado y elige el que más lo reduce. Por eso el corte elegido nunca es peor que el mejor corte recto (Proposición 1).",
                   "It compares all cuts with the weighted Gini and picks the one that reduces it most. That is why the chosen cut is never worse than the best straight cut (Proposition 1)."),
                "\\Delta G(\\text{elegido})\\ \\ge\\ \\max_j \\Delta G(\\text{recto}_j)"))),
    card(tx("Por qué encaja con estos datos", "Why it fits this data"),
      div(class = "kpi-row k4",
        kpi(tx("Atrasos correlacionados", "Correlated delays"), sprintf("ρ = %.2f", rho_pay),
            tx("PAY_0 con PAY_2: el riesgo vive en combinaciones", "PAY_0 with PAY_2: risk lives in combinations"), "layers"),
        kpi(tx("Montos redundantes", "Redundant amounts"), sprintf("ρ ≥ %.2f", bmin), tx("entre BILL_AMT1 a BILL_AMT6 (VIF > 20)", "among BILL_AMT1 to BILL_AMT6 (VIF > 20)"), "columns"),
        kpi(tx("Desbalance", "Imbalance"), pct(GLOBAL_RATE),
            tx(sprintf("incumple; cada moroso pesa %.1f veces más", T_$c), sprintf("default; each defaulter weighs %.1f× more", T_$c)), "alert"),
        kpi(tx("Cortes oblicuos usados", "Oblique cuts used"), "71 %",
            tx("de los nodos del modelo final; quitarlos baja el F1", "of the final model's nodes; removing them lowers F1"), "target")),
      div(class = "callout", tx("Lo que la teoría no garantiza: la Proposición 1 asegura que cada corte es al menos tan bueno como el mejor corte recto en los datos de entrenamiento, no que el bosque completo prediga mejor en clientes nuevos que métodos como CatBoost o XGBoost. Eso solo lo dicen las pruebas estadísticas (pestaña 4).",
                                "What the theory does not guarantee: Proposition 1 ensures each cut is at least as good as the best straight cut on the training data, not that the whole forest predicts new clients better than methods like CatBoost or XGBoost. Only the statistical tests can say that (tab 4)."))))
}

# ---------- Metodología (estructura de la «Guía de redacción metodológica» del curso) ----------
METH_FLOW <- list(
  list(c("Formulación", "Formulation"), c("Clasificación binaria f: ℝ²⁰ → {0, 1}; 1 = incumple el pago del mes siguiente.", "Binary classification f: ℝ²⁰ → {0, 1}; 1 = defaults next month.")),
  list(c("Datos", "Data"), c("UCI Taiwán: 29 965 clientes, 20 variables, 22.1 % de incumplimiento. Preprocesamiento dentro de cada pliegue.", "UCI Taiwan: 29,965 clients, 20 variables, 22.1% default. Preprocessing inside each fold.")),
  list(c("Modelo propuesto", "Proposed model"), c("Bosque con cortes oblicuos de Fisher ponderados por costo (ecuaciones 1 a 5).", "Forest with cost-weighted Fisher oblique cuts (equations 1 to 5).")),
  list(c("Entrenamiento", "Training"), c("4 búsquedas de hiperparámetros (malla, aleatoria, Optuna, genético); semilla 42.", "4 hyperparameter searches (grid, random, Optuna, genetic); seed 42.")),
  list(c("Baselines", "Baselines"), c("9 modelos: 7 clásicos + LightGBM y CatBoost, con el mismo presupuesto de búsqueda.", "9 models: 7 classic + LightGBM and CatBoost, with the same search budget.")),
  list(c("Evaluación", "Evaluation"), c("Validación anidada 5 × 5; F1, AUC-ROC, AUC-PR, MCC; Friedman, Nadeau-Bengio, Wilcoxon, DeLong.", "Nested 5 × 5 validation; F1, ROC-AUC, PR-AUC, MCC; Friedman, Nadeau-Bengio, Wilcoxon, DeLong.")),
  list(c("Ablación", "Ablation"), c("Mismo bosque sin corte oblicuo y variantes del corte, con todo lo demás fijo.", "Same forest without the oblique cut and variants of the cut, all else fixed.")),
  list(c("Reproducibilidad", "Reproducibility"), c("Código en GitHub (MIT), 14 pruebas en GitHub Actions, datos de UCI.", "Code on GitHub (MIT), 14 tests on GitHub Actions, UCI data.")))

PSEUDO <- "Entrada: D = {(xᵢ, yᵢ)}, T árboles, profundidad d, hoja mínima h, q variables, ε
1  wᵢ ← c·1{yᵢ = 1} + 1{yᵢ = 0},  c = n₀ / n₁                      ▷ ec. (1)
2  para t = 1, …, T:
3      tomar una muestra bootstrap y crecer el árbol por niveles
4      para cada nodo con ≥ 2h clientes, sin ser puro y con profundidad < d:
5          F ← q variables al azar
6          mejor ← el corte recto sobre F de menor G                ▷ ec. (2)
7          v ← dirección de Fisher con los clientes del nodo        ▷ ec. (3) y (4)
8          si el mejor umbral sobre vᵀx tiene menor G: mejor ← oblicuo
9          si mejor deja ≥ h clientes por lado: dividir; si no: hoja
10 f(x) ← promedio de las probabilidades de hoja de los T árboles  ▷ ec. (5)"

ABLATION <- list(
  list(c("CS-FOF base (1 candidato oblicuo, q = √p, d = 10, h = 20)", "Base CS-FOF (1 oblique candidate, q = √p, d = 10, h = 20)"), "0.5493", c("Referencia", "Reference")),
  list(c("Sin corte oblicuo", "Without oblique cut"), "0.5452", c("El corte oblicuo aporta +0.004", "The oblique cut adds +0.004")),
  list(c("Oblicuo con p/2 variables", "Oblique with p/2 variables"), "0.5449", c("Un corte más fuerte sobreajusta", "A stronger cut overfits")),
  list(c("Dos candidatos oblicuos por nodo", "Two oblique candidates per node"), "0.5482", c("Sin mejora", "No improvement")),
  list(c("Más profundo (d = 14, h = 10)", "Deeper (d = 14, h = 10)"), "0.5238", c("Sobreajuste claro", "Clear overfitting")),
  list(c("128 bins", "128 bins"), "0.5458", c("Sin mejora", "No improvement")))

CHECKLIST <- list(
  list("ok", c("La tarea, la pérdida y la notación están definidas formalmente.", "Task, loss and notation are formally defined.")),
  list("ok", c("Particiones antes de cualquier ajuste; imputación, escalado y SMOTE dentro de cada pliegue (sin fuga).", "Splits before any fitting; imputation, scaling and SMOTE inside each fold (no leakage).")),
  list("ok", c("El modelo tiene diagrama, ecuaciones, pseudocódigo y complejidad.", "The model has a diagram, equations, pseudocode and complexity.")),
  list("ok", c("Baselines recientes (LightGBM, CatBoost) con el mismo presupuesto de búsqueda.", "Recent baselines (LightGBM, CatBoost) with the same search budget.")),
  list("ok", c("Media y desviación estándar sobre 5 pliegues externos.", "Mean and standard deviation over 5 outer folds.")),
  list("ok", c("Pruebas estadísticas: Friedman-Nemenyi, Nadeau-Bengio, Wilcoxon con Holm, DeLong y McNemar.", "Statistical tests: Friedman-Nemenyi, Nadeau-Bengio, Wilcoxon with Holm, DeLong and McNemar.")),
  list("mid", c("Ablación por componente: hecha solo en el pliegue 1 y sin la variante «sin costo».", "Ablation per component: done only on fold 1 and without the “no cost” variant.")),
  list("ok", c("Código, datos y versiones disponibles (GitHub, UCI, requirements.txt); DOI de Zenodo pendiente.", "Code, data and versions available (GitHub, UCI, requirements.txt); Zenodo DOI pending.")),
  list("ok", c("Figuras del artículo en PDF vectorial, en inglés, desde un solo script.", "Paper figures in vector PDF, in English, from one script.")))

cs_eq <- function(n, tex, why) {
  div(class = "cs-eq", div(class = "cs-eq-n", sprintf("(%d)", n)),
      div(class = "cs-eq-body", div(class = "formula", paste0("$$", tex, "$$")),
          tags$p(class = "cs-eq-why", tags$b(tx("Por qué: ", "Why: ")), why)))
}

csfof_method <- function() {
  flow <- div(class = "cs-flow", lapply(seq_along(METH_FLOW), function(i)
    div(class = "cs-flow-item", tags$span(class = "cs-num", i), tags$b(L(METH_FLOW[[i]][[1]])), tags$p(L(METH_FLOW[[i]][[2]])))))
  eqs <- list(
    cs_eq(1, "w_i = c\\,\\mathbb{1}\\{y_i=1\\}+\\mathbb{1}\\{y_i=0\\},\\quad c=\\frac{n_0}{n_1}",
          tx("con 22 % de morosos, no detectar a uno cuesta más que una falsa alarma; c ≈ 3.5 iguala el peso de las dos clases.",
             "with 22% defaulters, missing one costs more than a false alarm; c ≈ 3.5 equalizes the weight of both classes.")),
    cs_eq(2, "G(L,R)=W_L\\,2p_L(1-p_L)+W_R\\,2p_R(1-p_R),\\quad p_A=\\frac{\\sum_{i\\in A}w_iy_i}{\\sum_{i\\in A}w_i}",
          tx("un solo criterio, con los mismos pesos, para comparar con justicia cortes rectos y oblicuos.",
             "a single criterion, with the same weights, to compare straight and oblique cuts fairly.")),
    cs_eq(3, "S_w=\\frac{1}{\\sum_i w_i}\\sum_i w_i(\\mathbf{x}_{i,F}-\\mu_{y_i})(\\mathbf{x}_{i,F}-\\mu_{y_i})^\\top+\\varepsilon\\,\\frac{\\operatorname{tr}S}{q}\\,I_q",
          tx("los montos facturados son casi colineales y los nodos profundos tienen pocos clientes: ε evita que S_w sea casi singular.",
             "billed amounts are nearly collinear and deep nodes have few clients: ε keeps S_w from being nearly singular.")),
    cs_eq(4, "\\mathbf{v}=\\frac{S_w^{-1}(\\mu_1-\\mu_0)}{\\lVert S_w^{-1}(\\mu_1-\\mu_0)\\rVert}",
          tx("es la dirección que mejor separa a las dos clases en el nodo (Proposición 2), calculada solo con sus clientes.",
             "it is the direction that best separates the two classes in the node (Proposition 2), computed only with its clients.")),
    cs_eq(5, "f(\\mathbf{x})=\\frac1T\\sum_{t=1}^{T}\\hat p_t(\\mathbf{x}),\\quad \\hat p_{\\text{hoja}}=\\frac{\\sum_{i\\in\\text{hoja}}w_iy_i}{\\sum_{i\\in\\text{hoja}}w_i}",
          tx("promediar árboles entrenados con muestras bootstrap distintas reduce la varianza, como en Random Forest.",
             "averaging trees trained on different bootstrap samples reduces variance, as in Random Forest.")))
  hp <- tbl_(c(tx("Hiperparámetro", "Hyperparameter"), tx("Rango buscado", "Search range"), tx("Modelo final", "Final model")),
             list(list("n_estimators (T)", "100-500", "359"), list("max_depth (d)", "6-14", "11"),
                  list("min_samples_leaf (h)", "10-60", "51"), list("max_features (q)", "sqrt, log2", "log2"),
                  list("eps (ε)", tx("0.01 a 1 (escala log)", "0.01 to 1 (log scale)"), "0.324")))
  nuevo <- tbl_(c(tx("Se reutiliza", "Reused"), tx("Es nuevo en CS-FOF", "New in CS-FOF")), list(
    list(tx("Bosque aleatorio: bootstrap, q variables al azar por nodo y promedio de árboles (Breiman, 2001).", "Random forest: bootstrap, q random variables per node and averaging of trees (Breiman, 2001)."),
         tx("La regla de partición: una dirección de Fisher local, ponderada por costo, que compite con los cortes rectos.", "The split rule: a local, cost-weighted Fisher direction that competes with straight cuts.")),
    list(tx("La idea de cortes oblicuos (Murthy et al., 1994; Menze et al., 2011).", "The idea of oblique cuts (Murthy et al., 1994; Menze et al., 2011)."),
         tx("Ambos tipos de corte se evalúan con el mismo Gini ponderado por costo, así el corte oblicuo nunca empeora un nodo.", "Both cut types are scored with the same cost-weighted Gini, so the oblique cut never worsens a node.")),
    list(tx("El discriminante lineal de Fisher (1936).", "Fisher's linear discriminant (1936)."),
         tx("Su aplicación a la predicción de incumplimiento en tarjetas de crédito (sin antecedentes en Web of Science ni Scopus).", "Its application to credit card default prediction (no precedent in Web of Science or Scopus)."))))
  abl <- tbl_(c(tx("Variante", "Variant"), "F1", tx("Lectura", "Reading")),
              lapply(seq_along(ABLATION), function(i) { a <- ABLATION[[i]]; list(L(a[[1]]), if (i == 1) tags$b(a[[2]]) else a[[2]], L(a[[3]])) }))
  check <- tags$ul(class = "cs-checklist", lapply(CHECKLIST, function(ck)
    tags$li(tags$span(class = paste("cs-chk", ck[[1]]), if (ck[[1]] == "ok") "✓" else "◐"), tags$span(L(ck[[2]])))))
  props <- tags$ul(class = "cs-props",
    tags$li(tags$b(tx("Proposición 1. ", "Proposition 1. ")), tx("El corte elegido nunca tiene más impureza que el mejor corte recto sobre las mismas variables.", "The chosen cut never has more impurity than the best straight cut on the same variables.")),
    tags$li(tags$b(tx("Proposición 2. ", "Proposition 2. ")), tx("Con ε = 0, v maximiza el criterio de Fisher J(u) = (uᵀ(μ₁ − μ₀))² / uᵀS_w u (Cauchy-Schwarz).", "With ε = 0, v maximizes Fisher's criterion J(u) = (uᵀ(μ₁ − μ₀))² / uᵀS_w u (Cauchy-Schwarz).")),
    tags$li(tags$b(tx("Proposición 3. ", "Proposition 3. ")), tx("Cada árbol termina y tiene a lo sumo ⌊n/h⌋ hojas.", "Each tree terminates and has at most ⌊n/h⌋ leaves.")),
    tags$li(tags$b(tx("Tiempo. ", "Time. ")), tx("Entrenar un árbol cuesta O(d·n(q log n + q²)); predecir un cliente, O(T·d·p).", "Training one tree costs O(d·n(q log n + q²)); predicting one client, O(T·d·p).")),
    tags$li(tags$b(tx("Memoria. ", "Memory. ")), tx("Cada nodo guarda q coeficientes y un umbral; el modelo final pesa 5 MB.", "Each node stores q coefficients and a threshold; the final model weighs 5 MB.")),
    tags$li(tags$b(tx("Verificación. ", "Verification. ")), tx("Las tres proposiciones se comprueban con pruebas unitarias (pestaña Código).", "The three propositions are checked with unit tests (Code tab).")))
  tagList(
    card(tx("Flujo de la metodología", "Methodology flow"),
         tags$p(class = "muted", tx("Sigue los ocho pasos de la guía de redacción metodológica del curso, aplicados a este proyecto.",
                                    "It follows the eight steps of the course's methodology writing guide, applied to this project.")), flow),
    card(tx("Modelo propuesto: ecuaciones", "Proposed model: equations"),
         tags$p(class = "muted", tx("Datos D = {(xᵢ, yᵢ)}, i = 1…n, con xᵢ ∈ ℝᵖ y yᵢ ∈ {0, 1}. Cada componente lleva su justificación.",
                                    "Data D = {(xᵢ, yᵢ)}, i = 1…n, with xᵢ ∈ ℝᵖ and yᵢ ∈ {0, 1}. Each component comes with its justification.")), eqs),
    card(tx("Pseudocódigo", "Pseudocode"), tags$pre(class = "pf-code cs-pseudo", PSEUDO)),
    div(class = "grid g2",
        card(tx("Propiedades y complejidad", "Properties and complexity"), props),
        card(tx("Entrenamiento y optimización", "Training and optimization"),
             tags$p(class = "muted", tx("Los 5 hiperparámetros se buscan con los mismos 4 métodos y presupuesto que los demás modelos (malla de 32, 25 aleatorias, 30 de Optuna y genético 16 × 10), dentro de la validación anidada.",
                                        "The 5 hyperparameters are searched with the same 4 methods and budget as the other models (grid of 32, 25 random, 30 Optuna and genetic 16 × 10), inside the nested validation.")), hp)),
    card(tx("Qué es nuevo y qué se reutiliza", "What is new and what is reused"), nuevo),
    card(tx("Diseño del estudio de ablación", "Ablation study design"),
         tags$p(class = "muted", tx("Cada variante cambia un solo componente y mantiene todo lo demás fijo. Se evaluó solo con el entrenamiento del pliegue externo 1 (validación interna de 3 pliegues), sin tocar datos de prueba.",
                                    "Each variant changes a single component and keeps everything else fixed. It was evaluated only on the training set of outer fold 1 (3-fold inner validation), without touching test data.")), abl),
    card(tx("Lista de verificación de la guía", "Guide checklist"), check,
         div(class = "muted", tx("✓ cumplido · ◐ parcial. Los puntos parciales se declaran como desviaciones en el protocolo del proyecto.",
                                 "✓ done · ◐ partial. Partial items are declared as deviations in the project protocol."))))
}

# ---------- Código: fragmentos reales de original_model.py (se leen del archivo, no se copian a mano) ----------
CSFOF_SRC <- readLines("modelo/cs_fof/original_model.py", encoding = "UTF-8", warn = FALSE)
CSFOF_TESTS_SRC <- readLines("modelo/cs_fof/test_original_model.py", encoding = "UTF-8", warn = FALSE)
CSFOF_URL <- paste0(REPO_PROJECT, "/blob/main/src/original_model.py")
CSFOF_TESTS_URL <- paste0(REPO_PROJECT, "/blob/main/tests/test_original_model.py")

# Función o clase de nivel superior: desde su «def»/«class» hasta la siguiente línea sin sangría
py_seg <- function(src, name) {
  i <- grep(sprintf("^(def|class) %s\\b", name), src)[1]
  rest <- (i + 1):length(src)
  j <- rest[grepl("^[^[:space:]#]", src[rest])][1]
  out <- src[i:(if (is.na(j)) length(src) else j - 1)]
  while (length(out) && !nzchar(trimws(out[length(out)]))) out <- out[-length(out)]
  paste(out, collapse = "\n")
}
# Líneas desde la que contiene `start` hasta antes de la que contiene `end`, sin la sangría común
py_between <- function(src, start, end) {
  i <- grep(start, src, fixed = TRUE)[1]
  j <- i + grep(end, src[(i + 1):length(src)], fixed = TRUE)[1]
  out <- src[i:(j - 1)]
  while (length(out) && !nzchar(trimws(out[length(out)]))) out <- out[-length(out)]
  ind <- min(nchar(out[nzchar(trimws(out))]) - nchar(sub("^ +", "", out[nzchar(trimws(out))])))
  paste(substring(out, ind + 1), collapse = "\n")
}
py_code <- function(src) tags$pre(class = "pf-code cs-code", tags$code(class = "language-python", src))

csfof_code <- function() {
  n_lines <- length(CSFOF_SRC)
  bloques <- list(
    list(tx("Ecuación (1): pesos de costo", "Equation (1): cost weights"), py_seg(CSFOF_SRC, "_pesos_de_clase"),
         tx("El moroso pesa c = n₀/n₁ cuando class_weight = «balanced».", "A defaulter weighs c = n₀/n₁ when class_weight = “balanced”.")),
    list(tx("Ecuación (2): Gini ponderado", "Equation (2): weighted Gini"), py_seg(CSFOF_SRC, "_gini_ponderado"),
         tx("El mismo criterio para los dos tipos de corte.", "The same criterion for both cut types.")),
    list(tx("Ecuaciones (3) y (4): dirección de Fisher por nodo", "Equations (3) and (4): Fisher direction per node"),
         py_seg(CSFOF_SRC, "direccion_fisher_por_nodo"),
         tx("Vectorizada: calcula a la vez la dirección de todos los nodos de un nivel con np.bincount.",
            "Vectorized: it computes the direction of every node in a level at once with np.bincount.")),
    list(tx("El corazón del modelo: los cortes compiten", "The heart of the model: cuts compete"),
         py_between(CSFOF_SRC, "# --- candidatos por ejes", "# --- aplicar cortes"),
         tx("Primero los cortes rectos; luego el oblicuo reemplaza al ganador solo si tiene menor G (Proposición 1).",
            "First the straight cuts; then the oblique one replaces the winner only if it has a lower G (Proposition 1).")),
    list(tx("Ecuación (5): predicción del bosque", "Equation (5): forest prediction"), py_between(CSFOF_SRC, "def predict_proba", "def predict(self"),
         tx("Promedio de las probabilidades de hoja de los T árboles.", "Average of the leaf probabilities of the T trees.")))
  uso <- paste(c(
    "from sklearn.pipeline import make_pipeline",
    "from sklearn.preprocessing import StandardScaler",
    "from src.original_model import CSFisherObliqueForest",
    "",
    "modelo = make_pipeline(StandardScaler(), CSFisherObliqueForest(",
    "    n_estimators=359, max_depth=11, min_samples_leaf=51, max_features=\"log2\",",
    "    eps=0.324, class_weight=\"balanced\", random_state=42, n_jobs=8))",
    "modelo.fit(X_train, y_train)",
    "riesgo = modelo.predict_proba(X_test)[:, 1]          # puntaje de incumplimiento",
    "print(modelo[-1].fraccion_cortes_oblicuos())        # 0.71 en el modelo final"), collapse = "\n")
  pruebas <- paste(py_seg(CSFOF_TESTS_SRC, "test_frontera_diagonal_la_capta_un_solo_corte_oblicuo"),
                   py_seg(CSFOF_TESTS_SRC, "test_prop1_corte_oblicuo_nunca_peor_que_ejes"), sep = "\n\n\n")
  enlace <- function(href, label) tags$a(class = "cs-link", href = href, target = "_blank", rel = "noopener noreferrer", icon_("github"), label)
  tagList(
    card(tx("Implementación propia", "Own implementation"),
      tags$p(class = "muted", tx(sprintf("CS-FOF está escrito desde cero en un solo archivo de %d líneas. Solo usa numpy para el cálculo; de scikit-learn hereda únicamente la interfaz fit / predict, para poder compararlo con los demás modelos en los mismos pipelines. No usa redes neuronales ni importa ningún modelo de árboles. Esta versión del tablero lo muestra leyendo el archivo original.", n_lines),
                                 sprintf("CS-FOF is written from scratch in a single %d-line file. It only uses numpy for computation; from scikit-learn it inherits just the fit / predict interface, so it can be compared with the other models in the same pipelines. It uses no neural networks and imports no tree model. This version of the dashboard shows it by reading the original file.", n_lines))),
      div(class = "kpi-row k4",
          kpi(tx("Líneas de código", "Lines of code"), n_lines, tx("un solo archivo, numpy", "one file, numpy"), "columns"),
          kpi(tx("Pruebas unitarias", "Unit tests"), "14", tx("en GitHub Actions en cada push", "on GitHub Actions on every push"), "target"),
          kpi(tx("Ajuste de un bosque", "Fitting one forest"), "≈ 13 s", tx("29 965 clientes, 4 procesos", "29,965 clients, 4 processes"), "clock"),
          kpi(tx("Modelo serializado", "Serialized model"), "5 MB", "artifacts/cs_fof.joblib", "save")),
      div(class = "cs-links", enlace(CSFOF_URL, tx("Ver original_model.py en GitHub", "See original_model.py on GitHub")),
          enlace(CSFOF_TESTS_URL, tx("Ver las 14 pruebas", "See the 14 tests")))),
    lapply(bloques, function(b) card(b[[1]], tags$p(class = "muted", b[[3]]), py_code(b[[2]]))),
    card(tx("Cómo se usa", "How to use it"),
         tags$p(class = "muted", tx("Igual que cualquier modelo de scikit-learn, con los hiperparámetros del modelo final.", "Like any scikit-learn model, with the final model's hyperparameters.")),
         py_code(uso)),
    card(tx("Pruebas de las propiedades", "Tests of the properties"),
         tags$p(class = "muted", tx("Dos de las 14 pruebas: un solo corte oblicuo capta una frontera diagonal, y la Proposición 1.",
                                    "Two of the 14 tests: a single oblique cut captures a diagonal boundary, and Proposition 1.")),
         py_code(pruebas)),
    card(tx(sprintf("Archivo completo (%d líneas)", n_lines), sprintf("Full file (%d lines)", n_lines)),
         tags$details(tags$summary(class = "cs-sum", tx("Mostrar original_model.py", "Show original_model.py")),
                      py_code(paste(CSFOF_SRC, collapse = "\n")))))
}

# ---------- Resultados ----------
CSFOF_TESTS <- list(  # rival, diferencia F1, folds ganados, p Nadeau-Bengio (Holm), δ de Cliff, p DeLong, McNemar
  list("catboost", -0.0001, 2, 1.000, -0.04, "0.273", "429 / 936"),
  list("xgboost", 0.0014, 4, 1.000, 0.36, "0.561", "434 / 827"),
  list("lightgbm", 0.0018, 3, 1.000, 0.12, "—", "345 / 782"),
  list("random_forest", 0.0027, 4, 1.000, 0.36, "0.171", "313 / 615"),
  list("svm", 0.0092, 5, 0.014, 0.76, "—", "—"),
  list("knn", 0.0216, 5, 0.056, 0.92, "—", "—"),
  list("decision_tree", 0.0225, 5, 0.003, 1.00, "—", "—"),
  list("logistic_regression", 0.0297, 5, 0.014, 1.00, "—", "—"),
  list("naive_bayes", 0.0493, 5, 0.0003, 1.00, "—", "—"))
CROSS_DATA <- list(   # F1 en Taiwán y en los tres conjuntos adicionales; rango medio
  list("catboost", 0.548, 0.605, 0.878, 0.733, 1.25), list("xgboost", 0.547, 0.599, 0.880, 0.682, 2.75),
  list("cs_fof", 0.548, 0.589, 0.874, 0.430, 4.75), list("random_forest", 0.545, 0.600, 0.874, 0.446, 4.75),
  list("lightgbm", 0.546, 0.575, 0.874, 0.658, 4.75))
# CS-FOF frente a Random Forest: pliegues (validación anidada) y robustez (exploratoria)
CS_VS_RF <- list(
  folds = list(x = c("1", "2", "3", "4", "5"), cs = c(0.5484, 0.5447, 0.5441, 0.5572, 0.5453),
               rf = c(0.5510, 0.5404, 0.5375, 0.5556, 0.5417), cs_sd = NULL, rf_sd = NULL),
  size = list(x = c("10 %", "25 %", "50 %", "100 %"), cs = c(0.5356, 0.5429, 0.5473, 0.5483), rf = c(0.5375, 0.5415, 0.5405, 0.5434),
              cs_sd = c(0.0073, 0.0065, 0.0073, 0.0078), rf_sd = c(0.0091, 0.0084, 0.0093, 0.0076)),
  noise = list(x = c("0 %", "5 %", "10 %", "20 %"), cs = c(0.5483, 0.5455, 0.5455, 0.5336), rf = c(0.5434, 0.5423, 0.5414, 0.5303),
               cs_sd = c(0.0078, 0.0081, 0.0085, 0.0147), rf_sd = c(0.0076, 0.0085, 0.0109, 0.0148)))
CSRF_X <- list(folds = c("Pliegue externo", "Outer fold"), size = c("Datos de entrenamiento usados", "Training data used"),
               noise = c("Etiquetas de entrenamiento invertidas", "Training labels flipped"))

# Líneas que se dibujan punto por punto (botón Reproducir y deslizador) con la diferencia en cada paso
fig_cs_vs_rf <- function(scn) {
  D <- CS_VS_RF[[scn]]; n <- length(D$x); xs <- D$x
  allv <- c(D$cs, D$rf); pad <- if (is.null(D$cs_sd)) 0.006 else 0.012
  arriba <- D$cs >= D$rf
  series <- list(list("CS-FOF", D$cs, D$cs_sd, WARM_GOLD, "diamond", ifelse(arriba, "top center", "bottom center")),
                 list("Random Forest", D$rf, D$rf_sd, DEEP_NAVY, "circle", ifelse(arriba, "bottom center", "top center")))
  trazas <- function(k) lapply(series, function(s) {
    tr <- list(type = "scatter", x = xs[seq_len(k)], y = s[[2]][seq_len(k)], mode = "lines+markers+text", name = s[[1]],
               text = sprintf("%.3f", s[[2]][seq_len(k)]), textposition = s[[6]][seq_len(k)],
               textfont = list(size = 11, color = s[[4]]), line = list(color = s[[4]], width = 3),
               marker = list(size = 12, symbol = s[[5]], color = s[[4]], line = list(width = 1.5, color = WHITE)),
               hovertemplate = sprintf("<b>%s</b><br>%%{x}<br>F1: %%{y:.4f}<extra></extra>", s[[1]]))
    if (!is.null(s[[3]])) tr$error_y <- list(type = "data", array = s[[3]][seq_len(k)], color = s[[4]], thickness = 1.2, width = 4, visible = TRUE)
    tr
  })
  nota_k <- function(k) {
    d <- D$cs[k] - D$rf[k]; quien <- if (d > 0) "CS-FOF" else "Random Forest"
    list(list(xref = "paper", yref = "paper", x = 0, y = 1.22, showarrow = FALSE, xanchor = "left", yanchor = "bottom",
              font = list(size = 13, color = if (d > 0) WARM_GOLD else DEEP_NAVY),
              text = tx(sprintf("<b>%s</b>: gana %s por %.4f", xs[k], quien, abs(d)), sprintf("<b>%s</b>: %s wins by %.4f", xs[k], quien, abs(d)))))
  }
  p <- plotly_build(style_fig(plot_ly(type = "scatter", mode = "markers"), 400, margin = list(l = 60, r = 20, t = 100, b = 120)))
  p$x$data <- trazas(n)
  # nombres únicos por escenario: así una animación en curso no se mezcla con el escenario nuevo
  p$x$frames <- lapply(seq_len(n), function(k) list(name = paste0(scn, "-", k), data = trazas(k), layout = list(annotations = nota_k(k))))
  p$x$layout$annotations <- nota_k(n)
  p$x$config$displayModeBar <- FALSE
  p$x$layout$xaxis <- modifyList(p$x$layout$xaxis %||% list(), list(title = L(CSRF_X[[scn]]), type = "category",
                                                                   categoryorder = "array", categoryarray = xs, range = c(-0.4, n - 0.6)))
  p$x$layout$yaxis <- modifyList(p$x$layout$yaxis %||% list(), list(title = tx("F1 de la clase default", "F1 of the default class"),
                                                                   range = c(min(allv) - pad, max(allv) + pad)))
  # botón con texto oscuro fijo (no lo cambia el modo oscuro) para que se lea sobre el fondo crema
  p$x$layout$updatemenus <- list(list(type = "buttons", showactive = FALSE, x = 0, y = -0.32, xanchor = "left", yanchor = "top",
    bgcolor = CREAM, bordercolor = PALE_GOLD, font = list(color = "#2B2F3A"),
    buttons = list(list(label = tx("▶ Reproducir", "▶ Play"), method = "animate",
      args = list(NULL, list(frame = list(duration = 900, redraw = TRUE), transition = list(duration = 450, easing = "cubic-in-out"),
                             fromcurrent = FALSE, mode = "immediate"))))))
  p$x$layout$sliders <- list(list(active = n - 1, x = 0.2, len = 0.8, y = -0.27, yanchor = "top", pad = list(t = 0),
    currentvalue = list(visible = FALSE), font = list(color = GREY_BLUE),
    steps = lapply(seq_len(n), function(k) list(label = xs[k], method = "animate",
      args = list(list(paste0(scn, "-", k)), list(mode = "immediate", frame = list(duration = 0, redraw = TRUE), transition = list(duration = 300)))))))
  p
}

cs_vs_rf_interp <- function(scn) {
  D <- CS_VS_RF[[scn]]; gana <- sum(D$cs > D$rf)
  if (scn == "folds") {
    interp_block(tx(sprintf("CS-FOF le gana a Random Forest en %d de 5 pliegues, pero por poco: 0.003 de F1 en promedio, menos que lo que cambia el F1 de un pliegue a otro.", gana),
                    sprintf("CS-FOF beats Random Forest in %d of 5 folds, but narrowly: 0.003 of F1 on average, less than F1 changes from one fold to another.", gana)),
                 tx("Validación anidada 5 × 5, mejor combinación de cada uno (pesos de clase + búsqueda aleatoria). Nadeau-Bengio con Holm p = 1.000; δ de Cliff = 0.36 (efecto mediano); DeLong p = 0.171; McNemar p < 0.001 (313 errores exclusivos de CS-FOF frente a 615).",
                    "Nested 5 × 5 validation, best combination of each (class weights + random search). Nadeau-Bengio with Holm p = 1.000; Cliff's δ = 0.36 (medium effect); DeLong p = 0.171; McNemar p < 0.001 (313 exclusive CS-FOF errors vs 615)."))
  } else if (scn == "size") {
    interp_block(tx("Con 25 % de los datos o más, CS-FOF queda arriba y sigue mejorando al recibir más clientes; Random Forest se estanca. Con muy pocos datos (10 %), Random Forest queda apenas por encima: calcular la dirección de Fisher en cada nodo necesita suficientes clientes.",
                    "With 25% of the data or more, CS-FOF stays on top and keeps improving with more clients; Random Forest plateaus. With very little data (10%), Random Forest is slightly ahead: computing the Fisher direction at each node needs enough clients."),
                 tx("Exploratorio: fracción estratificada del entrenamiento de cada pliegue, prueba completa, hiperparámetros elegidos en la validación anidada (sin búsqueda nueva). Barras: ± 1 desviación estándar entre los 5 pliegues. Sin pruebas de hipótesis.",
                    "Exploratory: stratified fraction of each fold's training set, full test set, hyperparameters chosen in the nested validation (no new search). Bars: ± 1 standard deviation across the 5 folds. No hypothesis tests."))
  } else {
    interp_block(tx("Al ensuciar las etiquetas de entrenamiento, los dos pierden casi lo mismo, y CS-FOF se mantiene arriba en todos los niveles.",
                    "When the training labels are corrupted, both lose almost the same, and CS-FOF stays on top at every level."),
                 tx("Exploratorio: se invierte al azar una fracción de las etiquetas de entrenamiento (la misma para los dos modelos); la prueba es limpia. Pérdida con 20 % de ruido: CS-FOF −0.015, Random Forest −0.013. Barras: ± 1 desviación estándar entre pliegues; se solapan, así que la diferencia no es concluyente.",
                    "Exploratory: a random fraction of training labels is flipped (the same for both models); the test set is clean. Loss with 20% noise: CS-FOF −0.015, Random Forest −0.013. Bars: ± 1 standard deviation across folds; they overlap, so the difference is not conclusive."))
  }
}

csfof_results <- function(scn = "folds") {
  sig <- function(p) if (p < 0.05) tags$b(if (p < 0.001) "< 0.001" else sprintf("%.3f", p)) else sprintf("%.3f", p)
  tests <- tbl_(c(tx("Rival", "Rival"), tx("Dif. F1", "F1 diff."), tx("Gana en", "Wins in"), "p Nadeau-Bengio (Holm)",
                  tx("δ de Cliff", "Cliff's δ"), "p DeLong", tx("Errores exclusivos (CS-FOF / rival)", "Exclusive errors (CS-FOF / rival)")),
                lapply(CSFOF_TESTS, function(r) list(minfo(r[[1]], "label"), sprintf("%+.4f", r[[2]]), sprintf("%d/5", r[[3]]),
                                                     sig(r[[4]]), sprintf("%+.2f", r[[5]]), r[[6]], r[[7]])))
  cross <- tbl_(c(tx("Modelo", "Model"), tx("Taiwán", "Taiwan"), "German", "Australian", tx("Polish (año 1)", "Polish (year 1)"), tx("Rango medio", "Mean rank")),
                lapply(CROSS_DATA, function(r) list(if (r[[1]] == "cs_fof") tags$b(minfo(r[[1]], "label")) else minfo(r[[1]], "label"),
                                                    sprintf("%.3f", r[[2]]), sprintf("%.3f", r[[3]]), sprintf("%.3f", r[[4]]),
                                                    sprintf("%.3f", r[[5]]), sprintf("%.2f", r[[6]]))))
  tagList(
    card(tx("CS-FOF frente a Random Forest, el modelo básico más parecido", "CS-FOF vs Random Forest, the most similar basic model"),
      tags$p(class = "muted", tx("CS-FOF es un Random Forest al que se le agregó el corte oblicuo con costo, así que esta comparación aísla lo que aporta la idea nueva. Elige un escenario y presiona Reproducir.",
                                 "CS-FOF is a Random Forest with the cost-sensitive oblique cut added, so this comparison isolates what the new idea contributes. Pick a scenario and press Play.")),
      div(class = "controls", control(tx("Escenario", "Scenario"),
          radio_("csrf_scn", stats::setNames(c("folds", "size", "noise"), c(tx("Los 5 pliegues", "The 5 folds"), tx("Menos datos", "Less data"), tx("Más ruido", "More noise"))), scn))),
      uiOutput("csrf_box")),
    card(tx("Pruebas frente a cada modelo (Taiwán)", "Tests against each model (Taiwan)"),
      tags$p(class = "muted", tx("Validación cruzada anidada 5 × 5 con los mismos folds, preprocesamiento y presupuesto de búsqueda para los 10 modelos. Métrica principal: F1 de la clase default. En negrita, p < 0.05.",
                                 "Nested 5 × 5 cross-validation with the same folds, preprocessing and search budget for the 10 models. Main metric: F1 of the default class. In bold, p < 0.05.")), tests),
    card(tx("Consistencia en otros conjuntos de crédito (F1)", "Consistency on other credit datasets (F1)"),
      tags$p(class = "muted", tx("Los 10 modelos con pesos de clase y búsqueda aleatoria en tres conjuntos públicos de UCI.",
                                 "The 10 models with class weights and random search on three public UCI datasets.")), cross),
    card(tx("Métricas fuera de pliegue que pide la guía", "Out-of-fold metrics required by the guide"),
      tags$p(class = "muted", tx("Predicciones fuera de pliegue de los 29 965 clientes (reajuste con los hiperparámetros de cada pliegue), umbral 0.5. Descriptivas: solo el AUC-ROC tiene prueba (DeLong).",
                                 "Out-of-fold predictions for the 29,965 clients (refit with each fold's hyperparameters), threshold 0.5. Descriptive: only ROC-AUC has a test (DeLong).")),
      tbl_(c(tx("Modelo", "Model"), "MCC", "AUC-PR", tx("Brier (menor es mejor)", "Brier (lower is better)"), "F1"),
           list(list(tags$b("CS-FOF (original)"), tags$b("0.411"), tags$b("0.560"), tags$b("0.168"), tags$b("0.548")),
                list("CatBoost", "0.402", "0.558", "0.179", "0.547"), list("XGBoost", "0.401", "0.555", "0.175", "0.545"),
                list("Random Forest", "0.400", "0.558", "0.173", "0.543"),
                list(tx("LightGBM (reajuste con AUC menor)", "LightGBM (refit with lower AUC)"), "0.401", "0.528", "0.190", "0.546")))),
    card(tx("Veredicto", "Verdict"),
      div(class = "callout", tx("CS-FOF empata con los mejores métodos del estado del arte en el problema principal, con la menor variación entre folds, pero no es superior de forma significativa a CatBoost, XGBoost, LightGBM ni Random Forest, y en los conjuntos adicionales queda por detrás de CatBoost.",
                                "CS-FOF ties with the best state-of-the-art methods on the main problem, with the lowest variation between folds, but it is not significantly superior to CatBoost, XGBoost, LightGBM or Random Forest, and on the additional datasets it falls behind CatBoost.")),
      interp_block(
        tx("En el problema principal CS-FOF acierta tanto como los mejores modelos y es el más estable. Comete menos errores que solo él cometa, pero eso se debe a que marca menos clientes como riesgosos, no a que ordene mejor. En el conjunto polaco, con muy pocas quiebras (4 %), los métodos de boosting le sacan mucha ventaja.",
           "On the main problem CS-FOF is as accurate as the best models and is the most stable. It makes fewer errors that only it makes, but that is because it flags fewer clients as risky, not because it ranks them better. On the Polish dataset, with very few bankruptcies (4%), boosting methods are far ahead."),
        tx("Friedman sobre los 10 modelos: χ² = 40.3, p = 6.7·10⁻⁶; rangos medios CatBoost 2.0 y CS-FOF 2.4; diferencia crítica de Nemenyi 6.06. Wilcoxon con 5 folds no puede bajar de p = 0.0625. DeLong y McNemar usan predicciones fuera de pliegue de los 29 965 clientes; el reajuste de LightGBM dio un AUC menor que el de su validación (0.773 frente a 0.784), por eso no se reporta su DeLong. Entre los 4 conjuntos, Iman-Davenport F = 4.38, p = 0.0013, sin diferencias significativas de CS-FOF tras Holm.",
           "Friedman over the 10 models: χ² = 40.3, p = 6.7·10⁻⁶; mean ranks CatBoost 2.0 and CS-FOF 2.4; Nemenyi critical difference 6.06. Wilcoxon with 5 folds cannot go below p = 0.0625. DeLong and McNemar use out-of-fold predictions for the 29,965 clients; the LightGBM refit gave a lower AUC than its validation (0.773 vs 0.784), so its DeLong is not reported. Across the 4 datasets, Iman-Davenport F = 4.38, p = 0.0013, with no significant CS-FOF differences after Holm."))))
}

# ---------- Página ----------
page_original <- function(sel = list()) {
  c_ <- CSFOF_CM; pos <- c_$tp + c_$fn
  tab_btn <- function(val, lbl, on = FALSE) tags$button(type = "button", class = paste("cs-tab", if (on) "cs-tab--on"), `data-tab` = val, lbl)
  pane <- function(val, kids, on = FALSE) div(class = "cs-pane", `data-pane` = val, style = if (!on) "display:none", kids)
  tagList(
    page_title(tx("Modelo original", "Original model")),
    card("CS-FOF · Cost-Sensitive Fisher Oblique Forest",
      tags$p(tx("Es el modelo propuesto en este proyecto: un bosque aleatorio programado desde cero, sin redes neuronales, cuyos árboles pueden cortar en diagonal combinando varias variables, en la dirección de Fisher ponderada por el costo de no detectar a quien incumple. Las pestañas siguen el orden de una presentación: la idea (Teoría), cómo se construyó y evaluó (Metodología), el código y cómo le fue (Resultados).",
                "It is the model proposed in this project: a random forest programmed from scratch, without neural networks, whose trees can cut diagonally by combining several variables, along the Fisher direction weighted by the cost of missing a defaulter. The tabs follow the order of a presentation: the idea (Theory), how it was built and evaluated (Methodology), the code and how it performed (Results).")),
      div(class = "kpi-row k4",
          kpi("F1", "0.548 ± 0.005", tx("2.º de 10, a 0.0001 de CatBoost", "2nd of 10, 0.0001 behind CatBoost"), "trophy"),
          kpi("ROC-AUC", "0.785", tx("el mayor de los 10 modelos", "the highest of the 10 models"), "target"),
          kpi(tx("Cortes oblicuos", "Oblique splits"), "71 %", tx("de los nodos del modelo final", "of the final model's nodes"), "layers"),
          kpi(tx("Incumplimientos detectados", "Defaults detected"), pct(c_$tp / pos, 0),
              tx(sprintf("%s de %s; %s falsas alarmas", num(c_$tp), num(pos), num(c_$fp)), sprintf("%s of %s; %s false alarms", num(c_$tp), num(pos), num(c_$fp))), "bars"))),
    div(class = "cs-tabs-wrap", div(class = "cs-tabs", role = "tablist",
        tab_btn("teoria", tx("1 · Teoría", "1 · Theory"), TRUE), tab_btn("metodologia", tx("2 · Metodología", "2 · Methodology")),
        tab_btn("codigo", tx("3 · Código", "3 · Code")), tab_btn("resultados", tx("4 · Resultados", "4 · Results")))),
    pane("teoria", csfof_theory(), TRUE),
    pane("metodologia", csfof_method()),
    pane("codigo", csfof_code()),
    pane("resultados", csfof_results(sel$csrf_scn %||% "folds")))
}
