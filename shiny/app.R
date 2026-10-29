# =============================================================================
#  TABLERO EDA — DEFAULT OF CREDIT CARD CLIENTS (UCI, Taiwán 2005)
#  R · Shiny · Plotly        (versión R del tablero Dash de la carpeta ../dash)
# =============================================================================
#  Ejecución local:
#     1) install.packages(c("shiny", "plotly", "ranger", "readxl", "jsonlite", "commonmark", "Matrix"))
#     2) Desde esta carpeta (shiny/):  shiny::runApp()
#
#  Estructura (Shiny carga solo los archivos de R/ en orden alfabético antes de este archivo):
#     R/00_config.R       idioma (ES/EN), autores, enlaces, rutas y paleta   <- editar nombres aquí
#     R/01_datos.R        carga y limpieza de datos (igual que el notebook 00_eda)
#     R/02_utils.R        formato, estadísticos, componentes y tema de las figuras
#     R/03_univariado.R   figuras e interpretaciones del EDA univariado
#     R/04_multivariado.R figuras e interpretaciones del EDA multivariado
#     R/05_modelos.R      resultados de las 112 combinaciones de modelos
#     R/06_variables.R    variables del modelo (mismas transformaciones del proyecto)
#     R/07_predecir.R     página Predecir (modelo serializado con saveRDS)
#     R/08_paginas.R      páginas, menú y navegación
#     R/09_kyo.R          asistente Kyo (TF-IDF + regresión logística)
#     www/                estilos (los mismos del Dash), JavaScript, fotos y Kyo
# =============================================================================

options(shiny.autoload.r = TRUE)

lang_switch <- function() tags$button(type = "button", class = "lang-switch", title = "Español / English",
                                      `aria-label` = "Cambiar idioma / Change language",
                                      tags$span(class = "ls-es", "ES"), tags$span(class = "ls-en", "EN"))
theme_toggle <- function() tags$button(type = "button", class = "theme-toggle",
                                       `aria-label` = "Cambiar entre modo claro y oscuro / Toggle light and dark mode",
                                       icon_("sun", "t-sun"), icon_("moon", "t-moon"))
both <- function(es, en) tagList(tags$span(class = "l-es", es), tags$span(class = "l-en", en))

ui <- tagList(
  tags$head(
    tags$meta(name = "viewport", content = "width=device-width, initial-scale=1"),
    tags$title("EDA · Riesgo Crediticio"),
    tags$link(rel = "preconnect", href = "https://fonts.googleapis.com"),
    tags$link(rel = "stylesheet", href = "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap"),
    tags$link(rel = "stylesheet", href = "estilos.css"),
    tags$link(rel = "stylesheet", href = "shiny.css"),
    tags$script(HTML("window.MathJax = { tex: { inlineMath: [['\\\\(', '\\\\)']], displayMath: [['$$', '$$']] },
                      chtml: { scale: 1 }, options: { skipHtmlTags: ['script', 'style', 'textarea', 'pre', 'code'] } };")),
    tags$script(src = "https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-chtml.js", async = NA)
  ),
  # interruptores de idioma y tema de la portada (solo visibles en la portada)
  div(class = "cover-toggle", lang_switch(), theme_toggle()),
  div(id = "shell", class = "app cover",
      uiOutput("sidebar", class = "sidebar"),
      div(class = "main",
          div(class = "topbar",
              div(class = "tb-left",
                  tags$button(id = "sb-btn", type = "button", class = "icon-btn",
                              title = "Mostrar u ocultar el menú lateral / Show or hide the side menu", icon_("panel")),
                  div(div(class = "t1", both(PROJECT_TITLE[1], PROJECT_TITLE[2])), div(class = "t2", both(COURSE[1], COURSE[2])))),
              div(class = "tb-right",
                  div(class = "badge", icon_("chip"),
                      both(sprintf("%s clientes · %s default", num(nrow(df)), pct(GLOBAL_RATE)),
                           sprintf("%s clients · %s default", num(nrow(df)), pct(GLOBAL_RATE)))),
                  tags$a(class = "icon-btn", href = NOTEBOOK_URL, target = "_blank", rel = "noopener noreferrer",
                         title = "Notebook del EDA / EDA notebook", icon_("notebook")),
                  tags$a(class = "icon-btn", href = REPO_PROJECT, target = "_blank", rel = "noopener noreferrer",
                         title = "Repositorio del proyecto / Project repository", icon_("github")),
                  lang_switch(), theme_toggle())),
          uiOutput("page", class = "content"),
          uiOutput("footer", class = "footer"))),
  # Asistente Kyo: panel lateral derecho
  tags$aside(id = "bot-panel", class = "bot-panel", `aria-label` = "Kyo",
    div(class = "bot-head",
        tags$img(class = "bot-av", src = "kyo/happy.svg", alt = ""),
        div(class = "bot-id", div(class = "bot-name", "Kyo", tags$span(class = "bot-dot")),
            div(class = "bot-sub", both("Asistente del tablero · entrenado con su contenido", "Dashboard assistant · trained on its content"))),
        tags$button(id = "bot-reset", type = "button", class = "icon-btn", title = "Nueva conversación / New conversation", icon_("reset")),
        tags$button(id = "bot-close", type = "button", class = "icon-btn", title = "Cerrar (Esc) / Close (Esc)", icon_("close"))),
    uiOutput("bot-where", class = "bot-where"),
    uiOutput("bot-msgs", class = "bot-msgs", role = "log", `aria-live` = "polite"),
    uiOutput("bot-sugs", class = "bot-sugs"),
    div(class = "bot-form",
        tags$input(id = "bot-input", type = "search", class = "bot-input", maxlength = "300", autocomplete = "off",
                   placeholder = "Pregúntame por cualquier parte del tablero…"),
        tags$button(id = "bot-send", type = "button", class = "bot-send", title = "Enviar / Send", icon_("send"))),
    tags$p(class = "bot-foot", both("Respondo con lo que aprendí del contenido de este tablero; no uso servicios externos.",
                                    "I answer with what I learned from this dashboard's content; I don't use external services."))),
  HTML(paste(readLines("kyo/walker.html", encoding = "UTF-8", warn = FALSE), collapse = "\n")),
  tags$script(src = "comun.js"),
  tags$script(src = "app.js")
)

server <- function(input, output, session) {
  lang <- reactive(if (identical(input$lang, "en")) "en" else "es")
  dark <- reactive(identical(input$theme, "dark"))
  route <- reactive({ r <- input$route %||% "/"; if (r %in% NAV_PATHS) r else "/" })
  fig <- function(expr_fn, mono = FALSE) renderPlotly({ set_lang(lang()); themed(expr_fn(), dark(), mono) })

  # ---------- Marco: menú, pie y página activa ----------
  output$sidebar <- renderUI({ set_lang(lang()); sidebar_content(route()) })
  output$footer <- renderUI({ set_lang(lang()); footer_content() })
  output$page <- renderUI({
    set_lang(lang())
    p <- route()
    body <- isolate(switch(p,
      "/" = page_home(),
      "/introduccion" = page_intro(),
      "/problema" = page_problem(),
      "/marco" = page_marco(),
      "/univariado" = page_uni(list(uni_var = input$uni_var, q_family = input$q_family, q_kind = input$q_kind)),
      "/multivariado" = page_multi(list(lim_scale = input$lim_scale, age_view = input$age_view, x_var = input$x_var,
                                        y_var = input$y_var, c_var = input$c_var, s_vars = input$s_vars)),
      "/modelos" = page_models(),
      "/predecir" = page_predict(pf_actual() %||% PROFILES$tipico[[2]], input$pf_whatif_var %||% "PAY_0"),
      "/conclusiones" = page_conclusions(),
      "/enlaces" = page_links(),
      "/equipo" = page_team(),
      page_home()))
    if (p == "/") body else div(class = "page-wrap", body, nav_buttons(p))
  })

  # ---------- Introducción ----------
  output$home_graph <- fig(fig_home, mono = TRUE)

  # ---------- EDA univariado ----------
  output$target_graph <- fig(fig_target, mono = TRUE)
  output$uni_graph <- renderPlotly({ set_lang(lang()); req(input$uni_var); themed(fig_uni(input$uni_var), dark(), TRUE) })
  output$uni_interp <- renderUI({ set_lang(lang()); req(input$uni_var); r <- interp_uni(input$uni_var); interp_block(r[[1]], r[[2]]) })
  output$q_graph <- renderPlotly({
    set_lang(lang()); req(input$q_family, input$q_kind)
    themed(fig_quant(input$q_family, input$q_kind), dark(), input$q_family %in% c("LIMIT_BAL", "AGE"))
  })
  output$q_interp <- renderUI({ set_lang(lang()); req(input$q_family); r <- interp_quant(input$q_family); interp_block(r[[1]], r[[2]]) })

  # ---------- EDA multivariado ----------
  output$corr_graph <- fig(fig_corr)
  output$rates_graph <- fig(fig_rates)
  output$lim_graph <- renderPlotly({ set_lang(lang()); req(input$lim_scale); themed(fig_limit_box(input$lim_scale), dark()) })
  output$age_graph <- renderPlotly({ set_lang(lang()); req(input$age_view); themed(fig_age(input$age_view), dark()) })
  output$age_interp <- renderUI({ set_lang(lang()); req(input$age_view); r <- interp_age(input$age_view); interp_block(r[[1]], r[[2]]) })
  cruce <- reactive({ set_lang(lang()); req(input$x_var, input$y_var, input$c_var); cross_fig(input$x_var, input$y_var, input$c_var) })
  output$x_graph <- renderPlotly({ themed(cruce()[[1]], dark()) })
  output$x_interp <- renderUI({ r <- cruce(); interp_block(r[[2]], r[[3]]) })
  output$s_graph_box <- renderUI({ n <- max(2, length(input$s_vars)); grafica("s_graph", max(480, 170 * n + 120)) })
  output$s_graph <- renderPlotly({
    set_lang(lang())
    v <- utils::head(input$s_vars, 6)
    validate(need(length(v) >= 2, tx("Elige al menos dos variables numéricas.", "Choose at least two numeric variables.")))
    themed(fig_splom(v), dark())
  })
  output$s_interp <- renderUI({
    set_lang(lang()); v <- utils::head(input$s_vars, 6); req(length(v) >= 2)
    r <- interp_splom(v); interp_block(r[[1]], r[[2]])
  })

  # ---------- Modelos ----------
  output$mdl_heat <- fig(fig_models_heat)
  output$mdl_scatter <- fig(fig_models_scatter)
  output$mdl_cm <- fig(fig_best_cm)

  # ---------- Predecir ----------
  pf_leer <- reactive({
    v <- lapply(INPUT_COLS, function(c) suppressWarnings(as.numeric(input[[paste0("pf_", c)]])))
    names(v) <- INPUT_COLS
    v
  })
  pf_actual <- reactiveVal(NULL)
  observe({ v <- pf_leer(); if (!any(vapply(v, function(x) length(x) == 0 || is.na(x), TRUE))) pf_actual(v) })
  pf <- debounce(pf_leer, 250)
  pf_ok <- reactive({
    v <- pf()
    faltan <- INPUT_COLS[vapply(v, function(x) length(x) == 0 || is.na(x), TRUE)]
    list(v = v, faltan = faltan, score = if (!length(faltan) && !is.null(MODELO)) predict_risk(v) else NA)
  })
  output$`pf-verdict` <- renderUI({
    set_lang(lang()); r <- pf_ok()
    if (length(r$faltan)) return(tags$p(class = "callout", paste0(tx("Completa los campos: ", "Fill in the fields: "),
                                                                  paste(vapply(utils::head(r$faltan, 4), pretty_var, ""), collapse = ", "),
                                                                  if (length(r$faltan) > 4) "…" else "")))
    predict_verdict(r$v, r$score)
  })
  output$`pf-trees` <- renderUI({ set_lang(lang()); r <- pf_ok(); req(!length(r$faltan)); trees_block(r$v) })
  output$pf_history <- renderPlotly({ set_lang(lang()); r <- pf_ok(); req(!length(r$faltan)); themed(fig_client_history(r$v), dark()) })
  output$pf_drivers <- renderPlotly({ set_lang(lang()); r <- pf_ok(); req(!length(r$faltan)); themed(fig_drivers(r$v, r$score), dark()) })
  output$pf_whatif <- renderPlotly({
    set_lang(lang()); r <- pf_ok(); req(!length(r$faltan))
    themed(fig_whatif(r$v, input$pf_whatif_var %||% "PAY_0", r$score), dark())
  })
  aplicar_perfil <- function(key) {
    v <- PROFILES[[key]][[2]]
    updateSliderInput(session, "pf_LIMIT_BAL", value = v$LIMIT_BAL)
    updateSliderInput(session, "pf_AGE", value = v$AGE)
    for (c in CAT_COLS) updateRadioButtons(session, paste0("pf_", c), selected = as.character(v[[c]]))
    for (c in PAY_COLS) updateSliderInput(session, paste0("pf_", c), value = v[[c]])
    for (c in c(BILL_COLS, PAYAMT_COLS)) updateNumericInput(session, paste0("pf_", c), value = v[[c]])
  }
  observeEvent(input$pf_prof_tipico, aplicar_perfil("tipico"))
  observeEvent(input$pf_prof_al_dia, aplicar_perfil("al-dia"))
  observeEvent(input$pf_prof_atrasos, aplicar_perfil("atrasos"))

  # ---------- Kyo ----------
  chat <- reactiveVal(list())
  observeEvent(input$bot_send, {
    txt <- trimws(substr(input$bot_send$t %||% "", 1, 300))
    if (!nzchar(txt)) return()
    hist <- utils::tail(chat(), 38)
    ult <- NULL
    for (m in rev(hist)) if (identical(m$r, "b") && !is.null(m$i)) { ult <- m$i; break }
    set_lang(lang())
    r <- kyo_responder(txt, route(), ult, lang())
    chat(c(hist, list(list(r = "u", t = txt)), list(c(list(r = "b"), r))))
  })
  observeEvent(input$bot_reset, chat(list()))
  output$`bot-where` <- renderUI({
    set_lang(lang())
    tagList(icon_("info"), tx("Estás en ", "You are on "), tags$b(kyo_nombre_pagina(route(), lang())))
  })
  output$`bot-msgs` <- renderUI({
    set_lang(lang()); path <- route()
    msgs <- c(list(c(list(r = "b"), kyo_bienvenida(path, lang()))), chat())
    tagList(lapply(msgs, kyo_msg_ui, path = path))
  })
  output$`bot-sugs` <- renderUI({
    set_lang(lang()); path <- route(); hist <- chat()
    sugs <- if (!length(hist)) kyo_bienvenida(path, lang())$s else {
      s <- hist[[length(hist)]]$s; if (length(s)) s else kyo_sug_pagina(path, lang())
    }
    tagList(lapply(unlist(sugs), function(s) tags$button(type = "button", class = "bot-sug", `data-q` = s, s)))
  })
}

shinyApp(ui, server)
