# Evalúa a Kyo (versión R) con las mismas preguntas de prueba del Dash (dash/asistente/evaluar.py).
# Uso (desde la carpeta shiny/):   Rscript herramientas/evaluar_kyo.R
suppressPackageStartupMessages({ library(shiny) })
`%||%` <- function(a, b) if (is.null(a)) b else a
source("R/00_config.R"); source("R/09_kyo.R")
P <- jsonlite::fromJSON("kyo/pruebas.json", simplifyVector = FALSE)
total_ok <- TRUE
for (lg in c("es", "en")) {
  casos <- P[[lg]]; fallos <- 0
  for (cs in casos) {
    q <- cs[[1]]; esperado <- cs[[2]]; pag <- cs[[3]]
    r <- kyo_clasificar(q, pag); acept <- kyo_entiende(q, pag)
    if (!identical(r$id, esperado) || is.null(acept)) {
      fallos <- fallos + 1
      cat(sprintf("   ✗ «%s» esperaba %s, dio %s (p=%.2f, sim=%.2f%s)\n", q, esperado, r$id %||% "-", r$prob, r$sim, if (is.null(acept)) ", rechazada" else ""))
    }
  }
  acc <- 1 - fallos / length(casos); total_ok <- total_ok && acc >= 0.9
  cat(sprintf("Preguntas nuevas (%s): %.1f%% (%d/%d)\n", lg, 100 * acc, length(casos) - fallos, length(casos)))
}
mal <- 0
for (q in unlist(P$fuera)) { r <- kyo_responder(q, "/"); if (!is.null(r$i)) { mal <- mal + 1; cat(sprintf("   ✗ «%s» respondió %s\n", q, r$i)) } }
cat(sprintf("Preguntas fuera del tablero rechazadas: %d/%d\n", length(P$fuera) - mal, length(P$fuera)))
pares <- list()
for (id in names(KYO_I$es)) { a <- unlist(KYO_I$es[[id]]$sug); b <- unlist(KYO_I$en[[id]]$sug); for (k in seq_along(a)) pares[[paste(a[k], b[k])]] <- c(a[k], b[k]) }
for (ruta in names(KYO_DATA$es$sug_de_pagina)) { a <- unlist(KYO_DATA$es$sug_de_pagina[[ruta]]); b <- unlist(KYO_DATA$en$sug_de_pagina[[ruta]]); for (k in seq_along(a)) pares[[paste(a[k], b[k])]] <- c(a[k], b[k]) }
malas <- 0
for (p in pares) { a <- kyo_entiende(p[1], "/"); b <- kyo_entiende(p[2], "/"); if (is.null(a) || is.null(b) || a != b) { malas <- malas + 1; cat(sprintf("   ✗ «%s» → %s | «%s» → %s\n", p[1], a %||% "-", p[2], b %||% "-")) } }
cat(sprintf("Sugerencias que llevan al mismo tema en ambos idiomas: %d/%d\n", length(pares) - malas, length(pares)))
