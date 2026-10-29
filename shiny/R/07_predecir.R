# =============================================================================
# 7. PREDECIR: modelo serializado con saveRDS (modelo/modelo_credito.rds)
# =============================================================================
# El .rds lo genera `Rscript modelo/entrenar_modelo.R`: un Random Forest (ranger) con pesos
# de clase sobre las variables de preparar_variables(). Aquí solo se CARGA y se usa.
library(ranger)
MODELO <- tryCatch(readRDS("modelo/modelo_credito.rds"), error = function(e) NULL)
MODELO_META <- tryCatch(jsonlite::fromJSON("modelo/modelo_credito.json"), error = function(e) list())
UMBRAL <- MODELO_META$umbral %||% 0.5
N_TREES <- if (is.null(MODELO)) 0 else MODELO$num.trees

PAY_CHRONO <- MONTH_ORDER                         # PAY_6 ... PAY_0 (abril → septiembre)
BILL_CHRONO <- paste0("BILL_AMT", 6:1)
PAYAMT_CHRONO <- paste0("PAY_AMT", 6:1)
SEX_OTHER <- 3                                    # «Otro»: el dataset solo registra 1 = hombre y 2 = mujer

moda <- function(x) as.numeric(names(sort(-table(x)))[1])
profile_typical <- function() {
  out <- list()
  for (c in c(CAT_COLS, PAY_COLS)) out[[c]] <- moda(df[[c]])
  for (c in c(BILL_COLS, PAYAMT_COLS)) out[[c]] <- round(stats::median(df[[c]]) / 100) * 100
  out$LIMIT_BAL <- round(stats::median(df$LIMIT_BAL) / 1e4) * 1e4
  out$AGE <- floor(stats::median(df$AGE))
  out[INPUT_COLS]
}
PROFILES <- list(
  tipico = list(c("Cliente típico", "Typical client"), profile_typical(), "users"),
  `al-dia` = list(c("Al día, cupo alto", "Up to date, high limit"),
                  c(list(LIMIT_BAL = 360000, SEX = 2, EDUCATION = 1, MARRIAGE = 2, AGE = 36),
                    stats::setNames(as.list(rep(-1, 6)), PAY_COLS),
                    stats::setNames(as.list(c(18500, 21000, 15800, 19200, 12400, 16900)), BILL_COLS),
                    stats::setNames(as.list(c(21000, 15800, 19200, 12400, 16900, 14000)), PAYAMT_COLS))[INPUT_COLS], "target"),
  atrasos = list(c("Atrasos recientes", "Recent delays"),
                 c(list(LIMIT_BAL = 50000, SEX = 1, EDUCATION = 3, MARRIAGE = 1, AGE = 47),
                   stats::setNames(as.list(c(2, 2, 2, 0, 0, 0)), PAY_COLS),
                   stats::setNames(as.list(c(49200, 48100, 46800, 45100, 44300, 43000)), BILL_COLS),
                   stats::setNames(as.list(c(0, 0, 1500, 1600, 1700, 1800)), PAYAMT_COLS))[INPUT_COLS], "alert")
)

DRIVER_GROUPS <- list(list(c("Historial de pagos", "Payment history"), PAY_COLS),
                      list(c("Montos pagados", "Amounts paid"), PAYAMT_COLS),
                      list(c("Facturación", "Billing"), BILL_COLS),
                      list(c("Cupo de crédito", "Credit limit"), "LIMIT_BAL"),
                      list(c("Perfil demográfico", "Demographic profile"), c("AGE", "SEX", "EDUCATION", "MARRIAGE")))
WHATIF <- list(
  PAY_0 = list(c("Atraso en septiembre", "September delay"), -2:8, c("Estado de pago en septiembre", "September repayment status")),
  LIMIT_BAL = list(c("Cupo", "Limit"), seq(10000, 1000000, by = 30000), c("Cupo de crédito (NT$)", "Credit limit (NT$)")),
  PAY_AMT1 = list(c("Pago de septiembre", "September payment"),
                  c(0, sort(unique(round(exp(seq(log(500), log(200000), length.out = 22)) / 100) * 100))),
                  c("Monto pagado en septiembre (NT$)", "Amount paid in September (NT$)")),
  AGE = list(c("Edad", "Age"), seq(21, 75, by = 2), c("Edad (años)", "Age (years)"))
)
PAY_SHORT <- list(`-2` = c("Sin uso", "No use"), `-1` = c("Al día", "Paid"), `0` = c("Mínimo", "Minimum"))
pay_short <- function(v) if (as.character(v) %in% names(PAY_SHORT)) L(PAY_SHORT[[as.character(v)]]) else tx(paste(v, "m atraso"), paste(v, "m late"))

# Lista de clientes (cada uno, lista con las 23 variables) -> puntajes 0–1.
# Con SEX = 3 («Otro») promedia las predicciones como hombre y como mujer.
predict_scores <- function(rows) {
  d <- do.call(rbind, lapply(rows, function(r) as.data.frame(r[INPUT_COLS])))
  other <- d$SEX == SEX_OTHER
  d$SEX[other] <- 1
  p <- predict(MODELO, preparar_variables(d))$predictions[, "1"]
  if (any(other)) {
    d2 <- d[other, , drop = FALSE]; d2$SEX <- 2
    p[other] <- (p[other] + predict(MODELO, preparar_variables(d2))$predictions[, "1"]) / 2
  }
  p
}
predict_risk <- function(values) predict_scores(list(values))[1]

# Cuántos árboles dan probabilidad ≥ 0.5 de incumplir (los «votos»)
tree_votes <- function(values) {
  rows <- if (values$SEX != SEX_OTHER) list(values) else list(modifyList(values, list(SEX = 1)), modifyList(values, list(SEX = 2)))
  d <- do.call(rbind, lapply(rows, function(r) as.data.frame(r[INPUT_COLS])))
  pa <- predict(MODELO, preparar_variables(d), predict.all = TRUE)$predictions   # [cliente, clase, árbol]
  yes <- mean(apply(pa[, 2, , drop = FALSE] >= 0.5, 1, mean)) * MODELO$num.trees
  c(round(yes), MODELO$num.trees)
}

fig_client_history <- function(values) {
  ml <- month_lbl()
  st <- vapply(PAY_CHRONO, function(c) as.numeric(values[[c]]), 0)
  p <- plot_ly()
  p <- add_trace(p, x = ml, y = vapply(BILL_CHRONO, function(c) as.numeric(values[[c]] %||% 0), 0), type = "bar",
                 name = tx("Facturado", "Billed"), marker = list(color = NAVY),
                 hovertemplate = paste0("%{x} · ", tx("facturado", "billed"), ": NT$ %{y:,.0f}<extra></extra>"))
  p <- add_trace(p, x = ml, y = vapply(PAYAMT_CHRONO, function(c) as.numeric(values[[c]] %||% 0), 0), type = "bar",
                 name = tx("Pagado", "Paid"), marker = list(color = PALE_GOLD),
                 hovertemplate = paste0("%{x} · ", tx("pagado", "paid"), ": NT$ %{y:,.0f}<extra></extra>"))
  p <- add_trace(p, x = ml, y = unname(st), type = "scatter", mode = "lines+markers", yaxis = "y2",
                 name = tx("Estado de pago", "Repayment status"), customdata = vapply(st, pay_short, ""),
                 line = list(color = WARM_GOLD, width = 2.5),
                 marker = list(size = 12, color = ifelse(st >= 1, WARM_GOLD, GREY_BLUE), line = list(width = 1.5, color = WHITE)),
                 hovertemplate = paste0("%{x} · ", tx("estado", "status"), ": %{customdata}<extra></extra>"))
  p <- layout(p, barmode = "group", bargap = .28,
              xaxis = list(title = "", categoryorder = "array", categoryarray = ml),
              yaxis = list(title = "NT$", tickformat = "~s"),
              yaxis2 = list(title = tx("Estado de pago", "Repayment status"), overlaying = "y", side = "right",
                            range = c(-2.8, 9.2), showgrid = FALSE, tickvals = c(-2, -1, 0, 2, 4, 6, 8),
                            ticktext = c(pay_short(-2), pay_short(-1), pay_short(0), "2 m", "4 m", "6 m", "8 m")))
  style_fig(p, 340, margin = list(l = 60, r = 70, t = 40, b = 36))
}

fig_drivers <- function(values, score) {
  typical <- PROFILES$tipico[[2]]
  rows <- lapply(DRIVER_GROUPS, function(g) modifyList(values, typical[g[[2]]]))
  alt <- predict_scores(rows)
  d <- data.frame(grupo = vapply(DRIVER_GROUPS, function(g) L(g[[1]]), ""), aporte = (score - alt) * 100)
  d <- d[order(abs(d$aporte)), ]
  lim <- max(5, max(abs(d$aporte)) * 1.6)
  p <- plot_ly(x = d$aporte, y = d$grupo, type = "bar", orientation = "h",
               marker = list(color = ifelse(d$aporte > 0, WARM_GOLD, NAVY)),
               text = sprintf("%+.1f pts", d$aporte), textposition = "outside", cliponaxis = FALSE,
               hovertemplate = paste0("%{y}: %{x:+.1f} ", tx("puntos frente a un cliente típico", "points vs. a typical client"), "<extra></extra>"))
  p <- layout(p, showlegend = FALSE, shapes = list(vline(0, color = GREY_BLUE, dash = "solid", width = 1)),
              xaxis = list(title = tx("Puntos de riesgo que suma (+) o resta (−)", "Risk points added (+) or removed (−)"),
                           range = c(-lim, lim), zeroline = FALSE),
              yaxis = list(title = "", categoryorder = "array", categoryarray = d$grupo))
  style_fig(p, 340, legend_top = FALSE, margin = list(l = 150, r = 30, t = 20, b = 46))
}

fig_whatif <- function(values, var, score) {
  w <- WHATIF[[var]]; lbl <- L(w[[1]]); grid <- w[[2]]; xtitle <- L(w[[3]])
  rows <- lapply(grid, function(x) { v <- values; v[[var]] <- x; v })
  pr <- predict_scores(rows) * 100
  thr <- UMBRAL * 100
  is_pay <- var == "PAY_0"
  xs <- if (is_pay) vapply(grid, pay_short, "") else grid
  cur <- values[[var]]
  p <- plot_ly()
  p <- add_trace(p, x = xs, y = pr, type = "scatter", mode = "lines+markers", name = lbl,
                 line = list(color = NAVY, width = 3, shape = if (is_pay) "linear" else "spline"),
                 marker = list(size = 7, color = NAVY),
                 hovertemplate = paste0(xtitle, ": %{x}<br>", tx("Puntaje", "Score"), ": %{y:.0f}%<extra></extra>"))
  p <- add_trace(p, x = if (is_pay) pay_short(cur) else cur, y = score * 100, type = "scatter", mode = "markers+text",
                 marker = list(symbol = "star", size = 20, color = PALE_GOLD, line = list(width = 1.5, color = GOLD_DARK)),
                 text = tx("Este cliente", "This client"), textposition = "top center", textfont = list(color = GOLD_DARK),
                 name = tx("Este cliente", "This client"),
                 hovertemplate = paste0(tx("Este cliente", "This client"), ": %{y:.0f}%<extra></extra>"))
  xa <- list(title = xtitle)
  if (is_pay) xa <- c(xa, list(type = "category", categoryorder = "array", categoryarray = xs)) else if (var != "AGE") xa$tickformat <- "~s"
  p <- layout(p, showlegend = FALSE, xaxis = xa,
              yaxis = list(title = tx("Puntaje de riesgo (%)", "Risk score (%)"), range = c(0, 100), ticksuffix = "%"),
              shapes = list(list(type = "rect", xref = "paper", x0 = 0, x1 = 1, yref = "y", y0 = thr, y1 = 100,
                                 fillcolor = "rgba(184,143,61,0.10)", line = list(width = 0), layer = "below"),
                            hline(thr, color = WARM_GOLD, width = 1.5)),
              annotations = list(nota(tx(sprintf("Umbral %.0f%%: por encima, «riesgo alto»", thr),
                                         sprintf("Threshold %.0f%%: above it, “high risk”", thr)), 0, thr, color = GOLD_MID)))
  style_fig(p, 360, legend_top = FALSE, margin = list(l = 60, r = 24, t = 24, b = 50))
}

# ---------- Tarjeta de riesgo: una tarjeta de crédito que se rompe según el puntaje ----------
# Lienzo de 160 x 100. < 30 % intacta · 30–50 % la fractura crece · 50–92 % se abre.
RC_SPLIT <- matrix(c(98.7, 0, 101.9, 14, 101.9, 29, 104, 44, 107.2, 58, 108.9, 72, 111.5, 86, 110.7, 100), ncol = 2, byrow = TRUE)
RC_CENTER_Y <- 44; RC_CRACK_FROM <- 0.30; RC_SPLIT_FROM <- 0.50; RC_SPLIT_FULL <- 0.92

rc_x_at <- function(y) stats::approx(RC_SPLIT[, 2], RC_SPLIT[, 1], xout = y, ties = "ordered")$y
rc_svg <- function(score) {
  t <- min(max((score - RC_CRACK_FROM) / (RC_SPLIT_FROM - RC_CRACK_FROM), 0), 1)
  if (t <= 0) return("none")
  top <- RC_CENTER_Y * (1 - t); bot <- RC_CENTER_Y + (100 - RC_CENTER_Y) * t
  mid <- RC_SPLIT[RC_SPLIT[, 2] > top & RC_SPLIT[, 2] < bot, , drop = FALSE]
  pts <- rbind(c(rc_x_at(top), top), mid, c(rc_x_at(bot), bot))
  d <- paste0("M", paste(sprintf("%.1f %.1f", pts[, 1], pts[, 2]), collapse = " L"))
  svg <- paste0('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 100" preserveAspectRatio="none">',
                '<path d="', d, '" fill="none" stroke="rgba(5,8,20,.6)" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>',
                '<path d="', d, '" fill="none" stroke="rgba(255,255,255,.8)" stroke-width=".6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
  sprintf('url("data:image/svg+xml,%s")', utils::URLencode(svg, reserved = TRUE))
}
rc_clip <- function(side) {
  line <- paste(sprintf("%.1f%% %.1f%%", RC_SPLIT[, 1] / 1.6, RC_SPLIT[, 2]), collapse = ", ")
  if (side == "l") paste0("polygon(0% 0%, ", line, ", 0% 100%)") else paste0("polygon(100% 0%, ", line, ", 100% 100%)")
}

risk_card <- function(score, thr) {
  high <- score >= thr
  k <- min(max((score - RC_SPLIT_FROM) / (RC_SPLIT_FULL - RC_SPLIT_FROM), 0), 1)
  title <- if (high) tx("Riesgo alto: probable incumplimiento", "High risk: likely default") else tx("Riesgo bajo: probable pago", "Low risk: likely to pay")
  cracks <- rc_svg(score)
  face <- function(clip, hidden = FALSE) {
    div(class = "cc-face rc-face", style = paste0("clip-path:", clip), `aria-hidden` = if (hidden) "true" else NULL,
        div(class = "cc-gloss"),
        div(class = "cc-top", tags$span(class = "cc-brand", tx("Riesgo de crédito", "Credit risk")), icon_("contactless", "cc-nfc")),
        div(class = "rc-mid", div(class = "cc-chip rc-chip"),
            div(tags$span(class = "cc-lbl", tx("Puntaje de riesgo", "Risk score")), div(class = "rc-score", pct(score, 0)))),
        div(class = "cc-bottom",
            div(tags$span(class = "cc-lbl", tx("Veredicto", "Verdict")), div(class = "rc-verdict", title)),
            div(class = "cc-valid", tags$span(class = "cc-lbl", tx("Umbral", "Threshold")), div(class = "cc-name", pct(thr, 0)))),
        div(class = "rc-cracks", style = paste0("background-image:", cracks)))
  }
  left <- sprintf("transform:translate(%.1fpx, %.1fpx) rotate(%.2fdeg)", -12 * k, 5 * k, -3.5 * k)
  right <- sprintf("visibility:%s;transform:translate(%.1fpx, %.1fpx) rotate(%.2fdeg)", if (k > 0) "visible" else "hidden", 12 * k, -3 * k, 4.5 * k)
  heat <- min(max((score - 0.3) / 0.6, 0), 1)
  div(class = paste0("rc ", if (high) "hi" else "lo", if (k > 0) " split" else ""), style = sprintf("--heat:%.3f", heat), role = "img",
      `aria-label` = tx(sprintf("%s. Puntaje %s, umbral %s.", title, pct(score, 0), pct(thr, 0)),
                        sprintf("%s. Score %s, threshold %s.", title, pct(score, 0), pct(thr, 0))),
      div(class = "rc-piece", style = left, face(if (k > 0) rc_clip("l") else "none")),
      div(class = "rc-piece", style = right, face(rc_clip("r"), hidden = TRUE)))
}

predict_verdict <- function(values, score) {
  pr <- MODELO_META$prueba
  late <- month_lbl()[vapply(PAY_CHRONO, function(c) (values[[c]] %||% 0) >= 1, TRUE)]
  signals <- list()
  if ((values$PAY_0 %||% 0) >= 1) {
    n <- values$PAY_0
    signals[[1]] <- list("alert", tx(sprintf("%d %s de atraso en septiembre: la señal que más pesa en el modelo.", n, if (n == 1) "mes" else "meses"),
                                     sprintf("%d %s late in September: the signal that weighs most in the model.", n, if (n == 1) "month" else "months")))
  } else if (length(late)) {
    signals[[1]] <- list("calendar", tx(sprintf("Tuvo atrasos en %s, aunque en septiembre está al día.", paste(late, collapse = ", ")),
                                        sprintf("Was late in %s, although up to date in September.", paste(late, collapse = ", "))))
  } else {
    signals[[1]] <- list("target", tx("Sin atrasos en los seis meses.", "No delays in the six months."))
  }
  bills <- sum(vapply(BILL_COLS, function(c) as.numeric(values[[c]] %||% 0), 0))
  paid <- sum(vapply(PAYAMT_COLS, function(c) as.numeric(values[[c]] %||% 0), 0))
  if (bills > 0) signals[[length(signals) + 1]] <- list("coin", tx(sprintf("Pagó el %s de lo facturado en el periodo.", pct(min(paid / bills, 9.99), 0)),
                                                                   sprintf("Paid %s of the amount billed in the period.", pct(min(paid / bills, 9.99), 0))))
  qq <- mean(df$LIMIT_BAL < (values$LIMIT_BAL %||% 0))
  signals[[length(signals) + 1]] <- list("card", tx(sprintf("Su cupo supera al de %s de los clientes.", pct(qq, 0)),
                                                    sprintf("Their limit is higher than that of %s of clients.", pct(qq, 0))))
  lectura <- paste0(
    if (!is.null(pr)) tx(sprintf("Con el umbral de 50 %% el modelo detecta %s de quienes incumplen y acierta en %s de los clientes que marca como riesgosos (datos de prueba). ", pct(pr$recall, 0), pct(pr$precision, 0)),
                         sprintf("With the 50%% threshold the model detects %s of defaulters and is right about %s of the clients it flags as risky (test data). ", pct(pr$recall, 0), pct(pr$precision, 0))) else "",
    tx("No es una probabilidad calibrada: el modelo se entrenó con pesos de clase, que lo hacen sobrestimar el riesgo frente a la tasa real (22 %). Sirve para ordenar y clasificar clientes.",
       "It is not a calibrated probability: the model was trained with class weights, which make it overestimate the risk compared with the real rate (22%). It is useful to rank and classify clients."))
  tagList(
    risk_card(score, UMBRAL),
    tags$ul(class = "pf-signals", lapply(signals, function(s) tags$li(icon_(s[[1]]), tags$span(s[[2]])))),
    tags$details(class = "pf-details", tags$summary(tx("¿Cómo leer el puntaje?", "How to read the score?")), tags$p(lectura)))
}

trees_block <- function(values) {
  v <- tree_votes(values); yes <- v[1]; n <- v[2]
  share <- if (n) yes / n else 0; cells <- round(share * 100)
  div(class = "pf-trees",
      div(class = "pf-trees-h", icon_("tree"), tags$b(tx(sprintf("%d de %d árboles votan «incumple»", yes, n),
                                                         sprintf("%d of %d trees vote “default”", yes, n)))),
      div(class = "pf-waffle", title = tx(paste(pct(share, 0), "de los árboles"), paste(pct(share, 0), "of the trees")),
          lapply(0:99, function(i) tags$span(class = paste0("pf-cell", if (i < cells) " on" else "")))),
      tags$p(class = "muted", tx("Cada cuadro es 1 % del bosque. El puntaje promedia las probabilidades de todos los árboles, por eso puede diferir un poco de esta proporción.",
                                 "Each square is 1% of the forest. The score averages the probabilities of all the trees, so it may differ slightly from this proportion.")))
}

# ---------- Formulario -------------------------------------------------------------
SEX_TILES <- list(list(1, c("Hombre", "Male"), "male"), list(2, c("Mujer", "Female"), "female"), list(SEX_OTHER, c("Otro", "Other"), "gender"))
EDU_TILES <- list(list(1, c("Posgrado", "Graduate"), "cap"), list(2, c("Universidad", "University"), "book"),
                  list(3, c("Secundaria", "High school"), "pencil"), list(4, c("Otros", "Others"), "dots"))
MAR_TILES <- list(list(1, c("Casado", "Married"), "rings"), list(2, c("Soltero", "Single"), "person"), list(3, c("Otros", "Others"), "dots"))

pf_field <- function(label, comp, cls = "") div(class = trimws(paste("pf-field", cls)), tags$label(class = "ctl-label", label), comp)

# Opciones como tarjetas con ícono (radio de Shiny con el mismo HTML/CSS del Dash)
tiles <- function(id, options, value, cls = "pf-tiles") {
  div(id = id, class = paste("shiny-input-radiogroup", cls), role = "radiogroup",
      lapply(options, function(o) {
        tags$label(class = "dash-options-list-option",
                   tags$span(class = "dash-options-list-option-wrapper",
                             tags$input(type = "radio", name = id, value = o[[1]], class = "pf-tile-in",
                                        checked = if (identical(as.character(o[[1]]), as.character(value))) NA else NULL)),
                   tags$span(class = "pf-tile", tags$span(if (!is.null(o[[3]])) icon_(o[[3]], "pf-tile-ico"),
                                                          tags$span(class = "pf-tile-txt", L(o[[2]])))))
      }))
}
num_in <- function(col, value, min = NULL) {
  tags$input(id = paste0("pf_", col), type = "number", value = value, step = "any", min = min, class = "pf-input",
             placeholder = pretty_var(col), `aria-label` = pretty_var(col))
}

model_info_card <- function() {
  m <- MODELO_META; pr <- m$prueba; hp <- m$hiperparametros; ver <- m$versiones
  rows <- list(
    list(tx("Modelo", "Model"), paste(m$modelo %||% "—", "·", tx("pesos de clase balanceados", "balanced class weights"))),
    list(tx("Hiperparámetros", "Hyperparameters"), paste(sprintf("%s = %s", names(hp), unlist(hp)), collapse = ", ")),
    list(tx("Prueba (20 %)", "Test (20%)"), if (!is.null(pr)) sprintf("F1 %.3f · recall %.3f · %s %.3f · ROC-AUC %.3f", pr$f1, pr$recall,
                                                                      tx("precisión", "precision"), pr$precision, pr$roc_auc) else "—"),
    list(tx("Entrenado", "Trained"), sprintf("%s %s · %s", num(m$n_entrenamiento %||% 0), tx("clientes", "clients"), m$fecha %||% "—")),
    list(tx("Versiones", "Versions"), sprintf("R %s · ranger %s", ver$R %||% "—", ver$ranger %||% "—")))
  steps <- list(list(tx("Entrenar", "Train"), tx("Se ajusta el bosque con los datos históricos (modelo/entrenar_modelo.R).",
                                                 "The forest is fitted on the historical data (modelo/entrenar_modelo.R)."), "tree"),
                list(tx("Guardar", "Save"), tx("saveRDS escribe el modelo en un archivo .rds.", "saveRDS writes the model to an .rds file."), "save"),
                list(tx("Cargar", "Load"), tx("La app lo lee con readRDS al arrancar, sin reentrenar.", "The app reads it with readRDS at startup, without retraining."), "notebook"),
                list(tx("Predecir", "Predict"), tx("Cada cambio del formulario llama a predict().", "Every form change calls predict()."), "gauge"))
  code <- tx('library(ranger)

# 1) Entrenar y guardar (modelo/entrenar_modelo.R)
modelo <- ranger(x = X, y = y, probability = TRUE, case.weights = pesos,
                 num.trees = 291, max.depth = 14, mtry = 4, min.bucket = 10)
saveRDS(modelo, "modelo/modelo_credito.rds", compress = "xz")

# 2) Cargar en la app (R/07_predecir.R), una sola vez al arrancar
modelo <- readRDS("modelo/modelo_credito.rds")

# 3) Predecir con los datos del formulario
cliente <- preparar_variables(valores)
riesgo <- predict(modelo, cliente)$predictions[, "1"]  # puntaje de 0 a 1',
'library(ranger)

# 1) Train and save (modelo/entrenar_modelo.R)
modelo <- ranger(x = X, y = y, probability = TRUE, case.weights = pesos,
                 num.trees = 291, max.depth = 14, mtry = 4, min.bucket = 10)
saveRDS(modelo, "modelo/modelo_credito.rds", compress = "xz")

# 2) Load in the app (R/07_predecir.R), once at startup
modelo <- readRDS("modelo/modelo_credito.rds")

# 3) Predict with the form data
cliente <- preparar_variables(valores)
riesgo <- predict(modelo, cliente)$predictions[, "1"]  # score from 0 to 1')
  card(tx("Cómo se serializó el modelo", "How the model was serialized"),
       tags$p(tx("Serializar es guardar un modelo ya entrenado en un archivo para usarlo después sin volver a entrenarlo. Así funciona esta sección:",
                 "Serializing means saving an already trained model to a file to use it later without retraining it. This is how this section works:")),
       div(class = "pf-steps", lapply(seq_along(steps), function(i) div(class = "pf-step", tags$span(class = "pf-step-n", i),
                                                                        icon_(steps[[i]][[3]], "pf-step-ico"), tags$b(steps[[i]][[1]]), tags$p(steps[[i]][[2]])))),
       tags$details(class = "pf-details", tags$summary(tx("Ver el código", "Show the code")), tags$pre(class = "pf-code", tags$code(code))),
       tbl_(list(tx("Detalle", "Detail"), tx("Valor", "Value")), rows))
}

pf_flow <- function() {
  items <- list(list("users", tx("1. Datos del cliente", "1. Client data"), tx("Perfil, pagos y montos de abril a septiembre.", "Profile, payments and amounts from April to September.")),
                list("layers", tx("2. Se transforman", "2. They are transformed"), tx("Logaritmos y resumen de las facturas, igual que en el proyecto.", "Logarithms and bill summary, just as in the project.")),
                list("tree", tx(sprintf("3. %d árboles opinan", N_TREES), sprintf("3. %d trees give their opinion", N_TREES)),
                     tx("Cada árbol del bosque estima si el cliente incumplirá.", "Each tree in the forest estimates whether the client will default.")),
                list("gauge", tx("4. Puntaje y decisión", "4. Score and decision"), tx("Se promedian sus opiniones; desde 50 % es «riesgo alto».", "Their opinions are averaged; from 50% it is “high risk”.")))
  out <- list()
  for (i in seq_along(items)) {
    it <- items[[i]]
    out[[length(out) + 1]] <- div(class = "pf-flow-item", tags$span(class = "pf-flow-ico", icon_(it[[1]])), div(tags$b(it[[2]]), tags$p(it[[3]])))
    if (i < length(items)) out[[length(out) + 1]] <- tags$span(class = "pf-flow-arrow", icon_("chevron"))
  }
  div(class = "pf-flow", out)
}

# `base`: valores con los que se dibuja el formulario (se conservan al cambiar de idioma)
page_predict <- function(base = PROFILES$tipico[[2]], whatif = "PAY_0") {
  head <- page_title(tx("Predecir", "Predict"))
  if (is.null(MODELO)) return(tagList(head, card(tx("El modelo no está disponible", "The model is not available"),
    tags$p(tx("No se encontró modelo/modelo_credito.rds. Para generarlo, desde la carpeta shiny/ ejecuta ",
              "modelo/modelo_credito.rds was not found. To generate it, from the shiny/ folder run "), tags$code("Rscript modelo/entrenar_modelo.R")))))
  ml <- month_lbl(); k <- tx("mil", "k")
  form <- card(tx("Datos del cliente", "Client data"), cls = "pf-form",
    div(class = "pf-profiles", tags$span(class = "pf-hint", tx("Prueba un ejemplo:", "Try an example:")),
        lapply(names(PROFILES), function(key) tags$button(id = paste0("pf_prof_", gsub("-", "_", key)), type = "button",
                                                          class = "btn ghost pf-prof action-button",
                                                          icon_(PROFILES[[key]][[3]]), L(PROFILES[[key]][[1]])))),
    tags$h4(class = "pf-h", icon_("users"), tx("Perfil", "Profile")),
    div(class = "pf-grid pf-g2",
        pf_field(tx("Cupo de crédito", "Credit limit"),
                 sliderInput("pf_LIMIT_BAL", NULL, min = 10000, max = 1000000, step = 10000, value = base$LIMIT_BAL,
                             pre = "NT$ ", sep = ",", ticks = FALSE, width = "100%")),
        pf_field(tx("Edad", "Age"), sliderInput("pf_AGE", NULL, min = 21, max = 79, step = 1, value = base$AGE,
                                               post = paste0(" ", tx("años", "years")), ticks = FALSE, width = "100%"))),
    pf_field(tx("Sexo", "Sex"), tiles("pf_SEX", SEX_TILES, base$SEX)),
    tags$p(class = "pf-hint pf-note", tx("El dataset solo registra hombre y mujer; con «Otro» el modelo promedia ambas predicciones.",
                                         "The dataset only records male and female; with “Other” the model averages both predictions.")),
    pf_field(tx("Educación", "Education"), tiles("pf_EDUCATION", EDU_TILES, base$EDUCATION), cls = "pf-row"),
    pf_field(tx("Estado civil", "Marital status"), tiles("pf_MARRIAGE", MAR_TILES, base$MARRIAGE), cls = "pf-row"),
    tags$h4(class = "pf-h", icon_("calendar"), tx("Estado de pago por mes (2005)", "Repayment status by month (2005)")),
    div(class = "pf-keys", tags$span(class = "pf-key k-ok", tx("−2 sin consumo", "−2 no use")),
        tags$span(class = "pf-key k-ok", tx("−1 pagó todo", "−1 paid in full")),
        tags$span(class = "pf-key k-mid", tx("0 pago mínimo", "0 minimum payment")),
        tags$span(class = "pf-key k-late", tx("1 a 8: meses de atraso", "1 to 8: months late"))),
    div(class = "pf-pay", lapply(seq_along(PAY_CHRONO), function(i) {
      c <- PAY_CHRONO[i]
      div(class = "pf-pay-row", tags$span(class = "pf-pay-m", ml[i]),
          div(class = "pf-pay-slider", sliderInput(paste0("pf_", c), NULL, min = -2, max = 8, step = 1, value = base[[c]], ticks = TRUE, width = "100%")))
    })),
    tags$h4(class = "pf-h", icon_("coin"), tx("Montos por mes (NT$)", "Amounts by month (NT$)")),
    div(class = "table-wrap", div(class = "pf-amounts",
        tags$span(), lapply(ml, function(m) tags$span(class = "pf-mh", m)),
        tags$span(class = "pf-rh", tx("Facturado", "Billed")), lapply(BILL_CHRONO, function(c) num_in(c, base[[c]])),
        tags$span(class = "pf-rh", tx("Pagado", "Paid")), lapply(PAYAMT_CHRONO, function(c) num_in(c, base[[c]], min = 0)))))
  result <- card(tx("Resultado", "Result"), cls = "pf-result", uiOutput("pf-verdict"), uiOutput("pf-trees"))
  whatif_opts <- lapply(names(WHATIF), function(v) list(v, WHATIF[[v]][[1]], NULL))
  tagList(
    head, pf_flow(),
    div(class = "pf-layout", form, div(class = "pf-side", result)),
    div(class = "grid g2",
        card(tx("Historial del cliente", "Client history"), grafica("pf_history", 340),
             interp_block(
               tx("Las barras comparan lo que le facturaron con lo que pagó cada mes; la línea dorada muestra su estado de pago. Cuando la línea sube por encima de 0 hay atraso, y cuando las barras doradas son mucho más bajas que las azules, el cliente está pagando poco de su deuda.",
                  "The bars compare what was billed with what was paid each month; the gold line shows the repayment status. When the line rises above 0 there is a delay, and when the gold bars are much lower than the blue ones, the client is paying little of their debt."),
               tx("El modelo no usa las seis facturas por separado: las resume en nivel medio (log con signo), tendencia mensual y número de meses con saldo a favor, como en el proyecto. Los estados de pago (PAY_0 … PAY_6) sí entran uno por uno y son las variables más importantes según SHAP.",
                  "The model does not use the six bills separately: it summarizes them as average level (signed log), monthly trend and number of months with a credit balance, as in the project. The repayment statuses (PAY_0 … PAY_6) do enter one by one and are the most important variables according to SHAP."))),
        card(tx("¿Qué empuja su riesgo?", "What drives their risk?"), grafica("pf_drivers", 340),
             interp_block(
               tx("Cada barra responde: «si en este grupo de datos el cliente fuera como un cliente típico, ¿cuánto cambiaría su puntaje?». Las barras doradas suben el riesgo y las azules lo bajan.",
                  "Each bar answers: “if, in this group of data, the client were like a typical client, how much would their score change?”. Gold bars raise the risk and blue ones lower it."),
               tx("Explicación local por sustitución: se reemplaza cada grupo de variables por los valores del cliente típico (mediana o moda) y se mide la diferencia en el puntaje. Es aproximada: no suma exactamente el total porque los grupos interactúan dentro del bosque (a diferencia de SHAP).",
                  "Local explanation by substitution: each group of variables is replaced by the typical client's values (median or mode) and the difference in the score is measured. It is approximate: it does not add up exactly to the total because the groups interact inside the forest (unlike SHAP).")))),
    card(tx("¿Qué pasaría si…?", "What if…?"),
         tiles("pf_whatif_var", whatif_opts, whatif, cls = "pf-tiles pf-seg"),
         grafica("pf_whatif", 360),
         interp_block(
           tx("La línea muestra el puntaje que tendría este mismo cliente si solo cambiara la variable elegida; la estrella es su situación actual. Por ejemplo, con «Atraso en septiembre» se ve cuánto sube el riesgo con cada mes de atraso.",
              "The line shows the score this same client would have if only the chosen variable changed; the star is their current situation. For example, with “September delay” you can see how much the risk rises with each month of delay."),
           tx("Es una curva de dependencia individual (ICE): se fija el resto de variables y se recorre una sola. En un bosque la curva tiene escalones porque cada árbol corta la variable en umbrales; no implica causalidad, solo describe cómo responde el modelo.",
              "It is an individual conditional expectation (ICE) curve: the other variables are fixed and only one is varied. In a forest the curve has steps because each tree splits the variable at thresholds; it does not imply causality, it only describes how the model responds."))),
    model_info_card())
}
