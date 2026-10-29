# =============================================================================
# 9. KYO: asistente del tablero (clasificador de intenciones entrenado con preguntas de ejemplo)
# =============================================================================
# Mismo motor que la versión Dash (dash/asistente/motor.py), reescrito en R:
#   1. Cada intención trae varias preguntas de ejemplo (kyo/conocimiento.json, en español e inglés).
#   2. Las preguntas se normalizan (minúsculas, sin tildes, sinónimos) y se convierten en vectores
#      TF-IDF de palabras y de letras (3–5 caracteres; tolera errores de escritura).
#   3. Con esos vectores se entrena una regresión logística multinomial con penalización L2
#      (el mismo objetivo y el mismo optimizador L-BFGS que LogisticRegression(C = 25) de scikit-learn).
#   4. Si ni la probabilidad ni la similitud con los ejemplos alcanzan un mínimo, Kyo dice que no
#      sabe en vez de inventar.
#   5. Se da un pequeño impulso a las intenciones de la página abierta.
# El modelo se entrena al arrancar la primera vez y se guarda en kyo/modelo_kyo.rds.
library(Matrix)

KYO_SIN <- c(
  "\\bgrafic[oa]s?\\b" = "grafica", "\\bplots?\\b" = "grafica", "\\bchart\\b" = "grafica", "\\bdiagramas?\\b" = "grafica",
  "\\bincumplimientos?\\b" = "default", "\\bimpagos?\\b" = "default", "\\bmoros[oa]s?\\b" = "default",
  "\\bmorosidad\\b" = "default", "\\bincumpl\\w*\\b" = "default", "\\bseccion(es)?\\b" = "pagina",
  "\\bpantallas?\\b" = "pagina", "\\bq\\b" = "que", "\\bcausa\\w*\\b" = "causal", "\\bpestanas?\\b" = "pagina",
  "\\bapartados?\\b" = "pagina", "\\bdashboard\\b" = "tablero", "\\bdash\\b" = "tablero", "\\bcupos?\\b" = "limite",
  "\\bmodelos?\\b" = "modelo", "\\bmodels?\\b" = "modelo", "\\b(charts?|graphs?)\\b" = "grafica",
  "\\bdefault(s|ers?|ing|ed)\\b" = "default", "\\bscreens?\\b" = "page", "\\bvariables?\\b" = "variable",
  "\\bclientes?\\b" = "cliente", "\\bexplicame\\b" = "explica", "\\bexplicas\\b" = "explica", "\\bexplicar\\b" = "explica",
  "\\bsignifica\\b" = "significa", "\\balgoritmos?\\b" = "modelo", "\\bclasificador(es)?\\b" = "modelo",
  "\\b(limit|bill|pay)\\s?(bal|amt|\\d)" = "\\1_\\2", "\\b(bill_amt|pay_amt)\\s(\\d)\\b" = "\\1\\2")

KYO_STOP <- c("el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al", "a", "en", "y", "o", "u",
  "me", "mi", "te", "se", "lo", "le", "les", "por", "para", "con", "sin", "sobre", "su", "sus", "es",
  "son", "que", "como", "cual", "cuales", "porfa", "favor", "puedes", "podrias", "quiero", "saber",
  "dime", "decir", "ser", "estar", "muy", "mas", "pero", "tambien", "ya", "dame", "muestrame", "cuentame",
  "explica", "donde", "cuando", "cuanto", "cuantos", "cuantas", "porque", "yo",
  "esta", "este", "estos", "estas", "tiene", "tienen", "hace", "hacer", "puedo", "algo", "ver",
  "the", "an", "of", "to", "in", "on", "at", "by", "is", "are", "was", "were", "be", "been", "it", "its",
  "and", "or", "for", "with", "about", "from", "do", "does", "did", "can", "could", "would", "should",
  "please", "tell", "explain", "give", "me", "my", "i", "there", "that", "these", "those",
  "any", "some", "into", "than", "then", "so", "very", "just", "also", "have", "has", "had", "get",
  "what", "how", "which", "who", "whom", "where", "when", "why", "am", "will", "quien", "quienes")

KYO_TILDES <- c("á" = "a", "é" = "e", "í" = "i", "ó" = "o", "ú" = "u", "ü" = "u", "ñ" = "n", "à" = "a", "è" = "e",
                "ì" = "i", "ò" = "o", "ù" = "u", "â" = "a", "ê" = "e", "î" = "i", "ô" = "o", "û" = "u", "ä" = "a",
                "ë" = "e", "ï" = "i", "ö" = "o", "ç" = "c", "ã" = "a", "Á" = "a", "É" = "e", "Í" = "i", "Ó" = "o",
                "Ú" = "u", "Ñ" = "n", "Ü" = "u")

kyo_normalizar <- function(texto) {
  t <- tolower(enc2utf8(texto %||% ""))
  for (k in names(KYO_TILDES)) t <- gsub(k, KYO_TILDES[[k]], t, fixed = TRUE)   # sin depender del locale
  t <- gsub("[^a-z0-9_ ]+", " ", t, perl = TRUE)
  t <- trimws(gsub("\\s+", " ", t, perl = TRUE))
  for (k in names(KYO_SIN)) t <- gsub(k, KYO_SIN[[k]], t, perl = TRUE)
  t
}
kyo_palabras <- function(t) { w <- strsplit(t, " ", fixed = TRUE)[[1]]; w[nzchar(w) & !w %in% KYO_STOP] }
kyo_contenido <- function(t) { p <- kyo_palabras(t); if (length(p)) paste(p, collapse = " ") else t }
kyo_letras <- function(t) {   # = analyzer "char_wb", ngram_range (3, 5) de scikit-learn
  out <- character(0)
  for (w in strsplit(t, " ", fixed = TRUE)[[1]]) {
    if (!nzchar(w)) next
    w <- paste0(" ", w, " "); n_w <- nchar(w)
    for (n in 3:5) {
      if (n_w <= n) { out <- c(out, w); break }
      out <- c(out, substring(w, 1:(n_w - n + 1), n:n_w))
    }
  }
  out
}

# TF-IDF como en scikit-learn: tf sublineal, idf suavizado, filas con norma L2
tfidf_fit <- function(tokens) {
  vocab <- sort(unique(unlist(tokens)))
  idx <- match(vocab, vocab); names(idx) <- vocab
  n <- length(tokens)
  dfreq <- tabulate(unlist(lapply(tokens, function(tk) idx[unique(tk)])), length(vocab))
  list(vocab = idx, idf = log((1 + n) / (1 + dfreq)) + 1)
}
tfidf_transform <- function(v, tokens) {
  rows <- list(); cols <- list(); vals <- list()
  for (i in seq_along(tokens)) {
    tk <- tokens[[i]]; tk <- tk[tk %in% names(v$vocab)]
    if (!length(tk)) next
    tb <- table(tk); j <- v$vocab[names(tb)]
    w <- (1 + log(as.numeric(tb))) * v$idf[j]
    w <- w / sqrt(sum(w^2))
    rows[[i]] <- rep(i, length(j)); cols[[i]] <- j; vals[[i]] <- w
  }
  sparseMatrix(i = as.integer(unlist(rows)), j = as.integer(unlist(cols)), x = as.numeric(unlist(vals)),
               dims = c(length(tokens), length(v$idf)))
}

KYO_DATA <- jsonlite::fromJSON("kyo/conocimiento.json", simplifyVector = FALSE)
KYO_UMBRAL_PROB <- 0.30; KYO_UMBRAL_SIM <- 0.30; KYO_UMBRAL_LETRAS <- 0.45; KYO_IMPULSO <- 0.10

# Regresión logística multinomial (softmax) con L2:  C · Σ log-pérdida + ½ ||W||²  (sin penalizar el intercepto)
kyo_logreg <- function(M, y, C = 25, maxit = 4000) {
  clases <- sort(unique(y)); K <- length(clases); p <- ncol(M); n <- nrow(M)
  Y <- sparseMatrix(i = seq_len(n), j = match(y, clases), x = 1, dims = c(n, K))
  Mt <- t(M)
  softmax <- function(Z) { Z <- Z - apply(Z, 1, max); E <- exp(Z); E / rowSums(E) }
  unpack <- function(th) list(W = matrix(th[seq_len(p * K)], p, K), b = th[p * K + seq_len(K)])
  fg <- function(th) {
    u <- unpack(th)
    Z <- as.matrix(M %*% u$W) + matrix(u$b, n, K, byrow = TRUE)
    P <- softmax(Z)
    f <- -C * sum(log(pmax(P[cbind(seq_len(n), match(y, clases))], 1e-300))) + 0.5 * sum(u$W^2)
    G <- C * (P - as.matrix(Y))
    list(f = f, g = c(as.numeric(as.matrix(Mt %*% G)) + as.numeric(u$W), colSums(G)))
  }
  cache <- new.env()
  f_ <- function(th) { r <- fg(th); cache$g <- r$g; cache$th <- th; r$f }
  g_ <- function(th) if (identical(th, cache$th)) cache$g else fg(th)$g
  opt <- stats::optim(rep(0, p * K + K), f_, g_, method = "L-BFGS-B", control = list(maxit = maxit, factr = 1e5))
  u <- unpack(opt$par)
  list(W = Matrix(u$W, sparse = FALSE), b = u$b, clases = clases, convergencia = opt$convergence, iter = opt$counts)
}
kyo_proba <- function(fit, X) {
  Z <- as.matrix(X %*% fit$W) + matrix(fit$b, nrow(X), length(fit$b), byrow = TRUE)
  Z <- Z - apply(Z, 1, max); E <- exp(Z); P <- E / rowSums(E)
  colnames(P) <- fit$clases
  P
}

kyo_entrenar <- function() {
  X <- c(); y <- c()
  for (lg in c("es", "en")) for (it in KYO_DATA[[lg]]$intenciones) {
    ej <- c(unlist(it$ejemplos), it$titulo)
    X <- c(X, vapply(ej, kyo_normalizar, "", USE.NAMES = FALSE)); y <- c(y, rep(it$id, length(ej)))
  }
  tw <- lapply(X, kyo_palabras); tc <- lapply(X, function(t) kyo_letras(kyo_contenido(t)))
  vw <- tfidf_fit(tw); vc <- tfidf_fit(tc)
  Mw <- tfidf_transform(vw, tw); Mc <- tfidf_transform(vc, tc)
  M <- cbind(Mw, Mc)
  fit <- kyo_logreg(M, y, C = 25)
  list(vw = vw, vc = vc, Mw = Mw, Mc = Mc, y = y, fit = fit, clases = fit$clases, n = length(X))
}

KYO <- local({
  ruta <- "kyo/modelo_kyo.rds"
  firma <- unname(tools::md5sum("kyo/conocimiento.json"))
  m <- if (file.exists(ruta)) tryCatch(readRDS(ruta), error = function(e) NULL) else NULL
  if (is.null(m) || !identical(m$firma, firma)) {
    message("[kyo] entrenando…")
    m <- kyo_entrenar(); m$firma <- firma
    try(saveRDS(m, ruta, compress = "xz"), silent = TRUE)
  }
  message(sprintf("[kyo] listo: %d preguntas (español e inglés) de %d temas", m$n, length(m$clases)))
  m
})
KYO_I <- lapply(c(es = "es", en = "en"), function(lg) {
  its <- KYO_DATA[[lg]]$intenciones; stats::setNames(its, vapply(its, `[[`, "", "id"))
})
KYO_PAGINA <- vapply(KYO_I$es, function(it) it$pagina %||% "", "")

kyo_clasificar <- function(texto, pagina = NULL) {
  t <- kyo_normalizar(texto)
  w <- tfidf_transform(KYO$vw, list(kyo_palabras(t)))
  c <- tfidf_transform(KYO$vc, list(kyo_letras(kyo_contenido(t))))
  if (Matrix::nnzero(c) == 0) return(list(id = NULL, prob = 0, sim = 0, cob = 0, sc = 0))
  p <- kyo_proba(KYO$fit, cbind(w, c))[1, ]
  if (!is.null(pagina)) p[KYO_PAGINA[names(p)] == pagina] <- p[KYO_PAGINA[names(p)] == pagina] + KYO_IMPULSO
  k <- which.max(p); cid <- names(p)[k]
  rows <- KYO$y == cid
  sw <- max(as.numeric(KYO$Mw[rows, , drop = FALSE] %*% t(w)))
  sc <- max(as.numeric(KYO$Mc[rows, , drop = FALSE] %*% t(c)))
  pal <- kyo_palabras(t)
  cob <- if (length(pal)) mean(pal %in% names(KYO$vw$vocab)) else 0
  list(id = cid, prob = min(p[[k]], 1), sim = (sw + sc) / 2, cob = cob, sc = sc)
}

kyo_entiende <- function(texto, pagina = NULL) {
  r <- kyo_clasificar(texto, pagina)
  if (is.null(r$id)) return(NULL)
  ok <- if (r$cob >= 0.75) r$prob >= KYO_UMBRAL_PROB || r$sim >= KYO_UMBRAL_SIM else
    if (r$cob >= 0.4) r$prob >= KYO_UMBRAL_PROB && r$sim >= KYO_UMBRAL_SIM else
      r$sc >= KYO_UMBRAL_LETRAS && r$prob >= 0.12
  if (ok) r$id else NULL
}

kyo_lg <- function(lang) if (identical(lang, "en")) "en" else "es"
kyo_paginas <- function(lang) KYO_DATA[[kyo_lg(lang)]]$paginas
kyo_sug_pagina <- function(pagina, lang) unlist(KYO_DATA[[kyo_lg(lang)]]$sug_de_pagina[[pagina]]) %||% character(0)
kyo_nombre_pagina <- function(pagina, lang) kyo_paginas(lang)[[pagina]] %||% kyo_paginas(lang)[["/"]]

kyo_paquete <- function(it, lang, texto = NULL, mood = NULL, sug = NULL) {
  tx_ <- KYO_DATA[[lang]]$textos
  s <- if (is.null(sug)) unlist(it$sug) else sug
  if (!is.null(it$tecnico) && is.null(texto) && !(tx_$tecnica %in% s)) s <- c(tx_$tecnica, s)
  list(t = texto %||% it$texto, i = it$id, m = mood %||% it$mood, p = it$pagina,
       n = if (!is.null(it$pagina)) kyo_paginas(lang)[[it$pagina]] %||% "" else "", s = utils::head(s, 4))
}

kyo_responder <- function(texto, pagina = "/", ultimo = NULL, lang = "es") {
  lang <- kyo_lg(lang); I <- KYO_I[[lang]]; tx_ <- KYO_DATA[[lang]]$textos
  if (is.null(kyo_paginas(lang)[[pagina]])) pagina <- "/"
  cid <- kyo_entiende(texto, pagina)
  if (is.null(cid)) {
    return(list(t = sub("{n}", kyo_nombre_pagina(pagina, lang), tx_$no_se, fixed = TRUE), i = NULL, m = "thinking",
                p = NULL, n = "", s = utils::head(kyo_sug_pagina(pagina, lang), 4)))
  }
  it <- I[[cid]]
  if (cid == "esta_pagina") {
    pid <- KYO_DATA[[lang]]$intencion_de_pagina[[pagina]] %||% "p_inicio"
    return(kyo_paquete(I[[pid]], lang))
  }
  if (cid == "mas_tecnico") {
    prev <- if (!is.null(ultimo)) I[[ultimo]] else NULL
    if (is.null(prev)) return(kyo_paquete(it, lang, tx_$primero, "thinking", kyo_sug_pagina(pagina, lang)))
    if (is.null(prev$tecnico)) return(kyo_paquete(prev, lang, sub("{t}", prev$titulo, tx_$sin_tecnica, fixed = TRUE), "thinking"))
    return(kyo_paquete(prev, lang, sub("{x}", prev$tecnico, sub("{t}", prev$titulo, tx_$version, fixed = TRUE), fixed = TRUE),
                       sug = unlist(prev$sug)))
  }
  kyo_paquete(it, lang)
}

kyo_bienvenida <- function(pagina = "/", lang = "es") {
  lang <- kyo_lg(lang); tx_ <- KYO_DATA[[lang]]$textos
  if (is.null(kyo_paginas(lang)[[pagina]])) pagina <- "/"
  list(t = sub("{n}", kyo_paginas(lang)[[pagina]], tx_$hola, fixed = TRUE), i = NULL, m = "happy", p = NULL, n = "",
       s = c(tx_$esta, utils::head(kyo_sug_pagina(pagina, lang), 3)))
}

# Mensaje del chat -> HTML (Markdown, fórmulas $$…$$ con MathJax y botón «Ir a…»)
kyo_msg_ui <- function(m, path) {
  if (identical(m$r, "u")) return(div(class = "bm user", div(class = "bm-bubble", m$t)))
  txt <- gsub("NT$", "NT&#36;", m$t, fixed = TRUE)
  txt <- gsub("\\$\\$(.+?)\\$\\$", "$$\\\\displaystyle \\1$$", txt, perl = TRUE)
  body <- list(md_html(txt))
  if (!is.null(m$p) && !identical(m$p, path)) {
    body[[2]] <- tags$a(class = "bot-go", href = paste0("#", m$p),
                        paste(tx("Ir a", "Go to"), if (nzchar(m$n %||% "")) m$n else tx("la sección", "the section")), icon_("arrow"))
  }
  div(class = "bm bot", tags$img(class = "bm-av", alt = "", src = paste0("kyo/", m$m %||% "happy", ".svg")),
      div(class = "bm-bubble", body))
}
