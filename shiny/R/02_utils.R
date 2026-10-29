# =============================================================================
# 2. UTILIDADES: formato, estadísticos, estilo de figuras y componentes de interfaz
# =============================================================================
library(shiny)
library(plotly)

# ---------- Formato -------------------------------------------------------------
num <- function(x, d = 0) formatC(x, format = "f", digits = d, big.mark = ",")
pct <- function(x, d = 1) paste0(formatC(100 * x, format = "f", digits = d), "%")
signo <- function(x, d = 2) paste0(ifelse(x >= 0, "+", "−"), formatC(abs(x), format = "f", digits = d))
nt <- function(x) ifelse(x < 0, paste0("-NT$", num(abs(x))), paste0("NT$", num(x)))
sig <- function(p) if (is.na(p)) "p=n/a" else if (p < 0.001) "p<0.001" else sprintf("p=%.3f", p)
is_money <- function(col) col == "LIMIT_BAL" || startsWith(col, "BILL_AMT") || startsWith(col, "PAY_AMT")
fmt_val <- function(col, v) if (is_money(col)) nt(v) else num(v, 1)

# ---------- Estadísticos ----------------------------------------------------------
q <- function(x, p) unname(stats::quantile(x, p, type = 7))
skewness <- function(x) { m <- mean(x); s2 <- mean((x - m)^2); mean((x - m)^3) / s2^1.5 }   # = scipy (sesgado)
kurtosis <- function(x) { m <- mean(x); s2 <- mean((x - m)^2); mean((x - m)^4) / s2^2 - 3 }  # exceso (Fisher)
tukey_outliers_pct <- function(s) {
  q1 <- q(s, .25); q3 <- q(s, .75); iqr <- q3 - q1
  mean(s < q1 - 1.5 * iqr | s > q3 + 1.5 * iqr) * 100
}
cramers_v <- function(ct) {
  chi2 <- suppressWarnings(stats::chisq.test(ct, correct = FALSE)$statistic)
  k <- min(dim(ct)) - 1
  if (k > 0) as.numeric(sqrt(chi2 / (sum(ct) * k))) else 0
}
chi2_test <- function(ct) suppressWarnings(stats::chisq.test(ct))   # Yates solo en tablas 2x2 (= scipy)
spearman <- function(x, y) suppressWarnings(stats::cor.test(x, y, method = "spearman", exact = FALSE))

# Correlación de Spearman de todas las numéricas + el objetivo (datos originales)
CORR <- stats::cor(cbind(df[NUM_COLS], default = df[[TARGET]]), method = "spearman")

# ---------- Íconos (los mismos SVG del Dash, definidos en estilos.css) -------------
icon_ <- function(name, cls = "") tags$span(class = trimws(paste("ico", paste0("ico-", name), cls)),
                                            `aria-hidden` = "true")

# ---------- Componentes ------------------------------------------------------------
card <- function(title, ..., cls = "") {
  div(class = trimws(paste("card", cls)), tags$h3(class = "card-title", title), ...)
}
kpi <- function(label, value, note = "", ico = NULL) {
  div(class = "kpi",
      div(class = "kpi-head", if (!is.null(ico)) icon_(ico), div(class = "kpi-label", label)),
      div(class = "kpi-value", value),
      div(class = "kpi-note", note))
}
interp_block <- function(basic, tech) {
  tags$details(class = "interp-wrap",
    tags$summary(class = "interp-btn", icon_("info"), tx("Ver interpretación", "Show interpretation"),
                 icon_("chevron", "interp-chev")),
    div(class = "interp-body",
        div(class = "interp basic", tags$b(tx("Básica", "Basic")), tags$p(basic)),
        div(class = "interp tech", tags$b(tx("Técnica", "Technical")), tags$p(tech))))
}
control <- function(label, comp) div(class = "control", tags$label(class = "ctl-label", label), comp)
PAGE_ICONS <- c("Introducción" = "info", "Problema y Objetivos" = "target", "Marco Teórico" = "book",
                "EDA Univariado" = "bars", "EDA Multivariado" = "scatter", "Modelos" = "layers",
                "Predecir" = "gauge", "Conclusiones" = "flag", "Enlaces" = "link", "Equipo" = "users",
                "Introduction" = "info", "Problem and Objectives" = "target", "Theoretical Framework" = "book",
                "Univariate EDA" = "bars", "Multivariate EDA" = "scatter", "Models" = "layers",
                "Predict" = "gauge", "Conclusions" = "flag", "Links" = "link", "Team" = "users")
page_title <- function(title) {
  ic <- PAGE_ICONS[title]
  div(class = "page-title", tags$h2(if (!is.na(ic)) icon_(ic, "pt-ico"), title))
}
ul_ <- function(items, ordered = FALSE) {
  li <- lapply(items, tags$li)
  if (ordered) tags$ol(li) else tags$ul(li)
}
tbl_ <- function(header, rows) {
  div(class = "table-wrap", tags$table(class = "vtable",
      tags$tr(lapply(header, tags$th)),
      lapply(rows, function(r) tags$tr(lapply(r, tags$td)))))
}
# Radio con el mismo estilo del Dash (botones .radio) para los selectores de las gráficas
radio_ <- function(id, choices, selected, cls = "radio") {
  div(id = id, class = paste("shiny-input-radiogroup", cls), `data-value` = selected,
      lapply(seq_along(choices), function(i) {
        v <- unname(choices[[i]])
        tags$label(tags$input(type = "radio", name = id, value = v,
                              checked = if (identical(v, selected)) NA else NULL),
                   names(choices)[i])
      }))
}
# Gráfica Plotly con alto fijo (el contenedor define el tamaño)
grafica <- function(id, h = 460) plotlyOutput(id, height = paste0(h, "px"))

# ---------- Estilo de las figuras ------------------------------------------------
titulo <- function(text) list(text = text, font = list(size = 16, color = DEEP_NAVY), x = 0.02, xanchor = "left")

style_fig <- function(p, h = 460, legend_top = TRUE, title = NULL, margin = list(l = 55, r = 30, t = 70, b = 50)) {
  p <- layout(p, margin = margin,
              paper_bgcolor = WHITE, plot_bgcolor = CREAM, colorway = PALETTE,
              font = list(color = DEEP_NAVY, family = FONT_FAMILY),
              hoverlabel = list(bgcolor = DEEP_NAVY, font = list(color = WHITE)))
  if (!is.null(title)) p <- layout(p, title = titulo(title))
  if (legend_top) p <- layout(p, legend = list(orientation = "h", yanchor = "bottom", y = 1.0, xanchor = "right", x = 1))
  p
}

# Rejilla suave en todos los ejes (incluidos los de subgráficas)
.grid_axes <- function(lay) {
  for (nm in grep("^[xy]axis[0-9]*$", names(lay), value = TRUE)) {
    lay[[nm]]$gridcolor <- lay[[nm]]$gridcolor %||% paste0(DEEP_RGBA, "0.08)")
    lay[[nm]]$zeroline <- lay[[nm]]$zeroline %||% FALSE
  }
  lay
}

# ---------- Tema claro / oscuro para las figuras ------------------------------------
DARK_CARD <- "#1B2338"; DARK_PLOT <- "#151C2E"
DARK_MAP <- c("#1A233D" = "#AEB8D6", "#36456D" = "#8E9CC6", "#66749C" = "#7F8EB9", "#8A6E3A" = "#B39A63",
              "#9A7A33" = "#BFA25A", "#6E5628" = "#9C8250", "rgba(26,35,61," = "rgba(174,184,214,")

themed <- function(p, dark = FALSE, mono = FALSE) {
  b <- plotly_build(p)
  b$x$layout <- .grid_axes(b$x$layout)
  b$x$config$displaylogo <- FALSE
  b$x$config$locale <- if (lang_actual() == "en") "en" else "es"
  if (!isTRUE(dark)) return(b)
  mp <- DARK_MAP
  if (mono) mp <- c(c("#1A233D" = PALE_GOLD, "rgba(26,35,61," = "rgba(210,187,137,", "#B88F3D" = CREAM),
                    mp[!names(mp) %in% c("#1A233D", "rgba(26,35,61,")])
  rep_ <- function(s) {
    for (k in names(mp)) s <- gsub(k, mp[[k]], s, fixed = TRUE, ignore.case = FALSE)
    s
  }
  b$x$data <- rapply(b$x$data, rep_, classes = "character", how = "replace")
  b$x$layout <- rapply(b$x$layout, rep_, classes = "character", how = "replace")
  lay <- b$x$layout
  lay$paper_bgcolor <- DARK_CARD; lay$plot_bgcolor <- DARK_PLOT
  lay$font$color <- CREAM
  if (is.list(lay$title)) lay$title$font$color <- CREAM
  lay$hoverlabel <- list(bgcolor = CREAM, font = list(color = DEEP_NAVY))
  for (nm in grep("^[xy]axis[0-9]*$", names(lay), value = TRUE)) {
    lay[[nm]]$gridcolor <- "rgba(249,240,222,0.12)"
    lay[[nm]]$zerolinecolor <- "rgba(249,240,222,0.25)"
    lay[[nm]]$linecolor <- "rgba(249,240,222,0.30)"
  }
  if (!is.null(lay$annotations)) {
    lay$annotations <- lapply(lay$annotations, function(a) {
      if (is.null(a$font$color)) a$font$color <- CREAM
      a
    })
  }
  b$x$layout <- lay
  b
}

`%||%` <- function(a, b) if (is.null(a)) b else a
# Texto como categorías en el orden dado (plotly en R ordena el texto alfabéticamente)
fx <- function(v) factor(v, levels = unique(v))

# Línea horizontal / vertical como «shape» (equivalente a add_hline/add_vline de Python)
hline <- function(y, color = DEEP_NAVY, dash = "dash", width = 1.6, xref = "paper", yref = "y") {
  list(type = "line", xref = xref, x0 = 0, x1 = 1, yref = yref, y0 = y, y1 = y,
       line = list(color = color, dash = dash, width = width))
}
vline <- function(x, color = DEEP_NAVY, dash = "dash", width = 1.6, xref = "x", yref = "paper") {
  list(type = "line", xref = xref, x0 = x, x1 = x, yref = yref, y0 = 0, y1 = 1,
       line = list(color = color, dash = dash, width = width))
}
nota <- function(text, x, y, xref = "paper", yref = "y", color = DEEP_NAVY, xanchor = "left", yanchor = "bottom") {
  list(text = text, x = x, y = y, xref = xref, yref = yref, showarrow = FALSE,
       xanchor = xanchor, yanchor = yanchor, font = list(color = color, size = 12))
}
