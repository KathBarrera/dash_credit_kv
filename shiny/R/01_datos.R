# =============================================================================
# 1. CARGA Y LIMPIEZA DE DATOS (mismas decisiones que el notebook 00_eda.ipynb)
# =============================================================================
TARGET <- "default_payment_next_month"
PAY_COLS <- c("PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6")
BILL_COLS <- paste0("BILL_AMT", 1:6)
PAYAMT_COLS <- paste0("PAY_AMT", 1:6)
NUM_COLS <- c("LIMIT_BAL", "AGE", PAY_COLS, BILL_COLS, PAYAMT_COLS)
CAT_COLS <- c("SEX", "EDUCATION", "MARRIAGE")
DISCRETE <- c(CAT_COLS, PAY_COLS, TARGET)          # variables tratadas como categorías
INPUT_COLS <- c("LIMIT_BAL", "SEX", "EDUCATION", "MARRIAGE", "AGE", PAY_COLS, BILL_COLS, PAYAMT_COLS)
ALL_VARS <- c("LIMIT_BAL", "SEX", "EDUCATION", "MARRIAGE", "AGE", PAY_COLS, BILL_COLS, PAYAMT_COLS, TARGET)

leer_datos <- function() {
  # Busca el archivo local; si no existe, lo descarga del repositorio UCI.
  cands <- c("data/default_of_credit_card_clients.xls", "default_of_credit_card_clients.xls")
  ruta <- cands[file.exists(cands)][1]
  if (is.na(ruta)) {
    ruta <- tempfile(fileext = ".xls")
    utils::download.file(paste0("https://archive.ics.uci.edu/ml/machine-learning-databases/00350/",
                                "default%20of%20credit%20card%20clients.xls"), ruta, mode = "wb")
  }
  message("[datos] leyendo ", ruta)
  d <- as.data.frame(readxl::read_excel(ruta, skip = 1))
  tcol <- grep("default", names(d), ignore.case = TRUE, value = TRUE)[1]
  names(d)[names(d) == tcol] <- TARGET
  names(d)[names(d) == "PAY_1"] <- "PAY_0"
  d$ID <- NULL
  d[] <- lapply(d, as.numeric)
  d
}

preparar <- function(raw) {
  # Limpieza: duplicados exactos y categorías no documentadas -> «Otros»
  info <- list(filas_originales = nrow(raw))
  d <- raw[!duplicated(raw), , drop = FALSE]
  rownames(d) <- NULL
  info$duplicados <- info$filas_originales - nrow(d)
  info$edu_reagrupadas <- sum(d$EDUCATION %in% c(0, 5, 6))
  info$mar_reagrupadas <- sum(d$MARRIAGE == 0)
  d$EDUCATION[d$EDUCATION %in% c(0, 5, 6)] <- 4
  d$MARRIAGE[d$MARRIAGE == 0] <- 3
  info$bill_neg_clientes <- sum(apply(d[BILL_COLS] < 0, 1, any))
  list(df = d, info = info)
}

.prep <- preparar(leer_datos())
df <- .prep$df
DATA_INFO <- .prep$info
rm(.prep)

# Grupos de edad (para el análisis AGE vs. PAY)
AGE_LABELS <- c("21–25", "26–30", "31–35", "36–40", "41–45", "46–50", "51–55", "56–60", "61+")
df$AGE_GRP <- cut(df$AGE, breaks = c(20, 25, 30, 35, 40, 45, 50, 55, 60, 80), labels = AGE_LABELS)

GLOBAL_RATE <- mean(df[[TARGET]])
N_DEF <- sum(df[[TARGET]])

# ---------- Etiquetas de categorías y meses -------------------------------------
CAT_LABELS <- list(
  SEX = list(`1` = c("Hombre", "Male"), `2` = c("Mujer", "Female")),
  EDUCATION = list(`1` = c("Posgrado", "Graduate school"), `2` = c("Universidad", "University"),
                   `3` = c("Secundaria", "High school"), `4` = c("Otros", "Others")),
  MARRIAGE = list(`1` = c("Casado", "Married"), `2` = c("Soltero", "Single"), `3` = c("Otros", "Others"))
)
CAT_LABELS[[TARGET]] <- list(`0` = c("No default", "No default"), `1` = c("Default", "Default"))

cat_labels <- function(col) vapply(CAT_LABELS[[col]], L, "")

MONTH_ORDER <- c("PAY_6", "PAY_5", "PAY_4", "PAY_3", "PAY_2", "PAY_0")   # cronológico (abr → sep)
month <- function(i) {
  es <- c("Sep", "Ago", "Jul", "Jun", "May", "Abr"); en <- c("Sep", "Aug", "Jul", "Jun", "May", "Apr")
  (if (lang_actual() == "en") en else es)[i]
}
month_lbl <- function() vapply(6:1, month, "")

pretty_var <- function(col) {
  if (col == "LIMIT_BAL") return(tx("LIMIT_BAL · Límite de crédito (NT$)", "LIMIT_BAL · Credit limit (NT$)"))
  if (col == "AGE") return(tx("AGE · Edad (años)", "AGE · Age (years)"))
  if (col == "SEX") return(tx("SEX · Sexo", "SEX · Sex"))
  if (col == "EDUCATION") return(tx("EDUCATION · Nivel educativo", "EDUCATION · Education level"))
  if (col == "MARRIAGE") return(tx("MARRIAGE · Estado civil", "MARRIAGE · Marital status"))
  if (col == TARGET) return(tx("default · Incumplimiento próximo mes", "default · Default next month"))
  if (col == "PAY_0") return(tx("PAY_0 · Estado de pago (Sep)", "PAY_0 · Repayment status (Sep)"))
  k <- as.integer(substring(col, nchar(col)))
  if (startsWith(col, "PAY_AMT")) return(sprintf("%s · %s (%s)", col, tx("Monto pagado", "Amount paid"), month(k)))
  if (startsWith(col, "PAY_")) return(sprintf("%s · %s (%s)", col, tx("Estado de pago", "Repayment status"), month(k)))
  if (startsWith(col, "BILL_AMT")) return(sprintf("%s · %s (%s)", col, tx("Monto facturado", "Bill amount"), month(k)))
  col
}

# Columna como factor ordenado con etiquetas legibles
as_cat <- function(col, x = df[[col]]) {
  if (col %in% names(CAT_LABELS)) {
    lab <- cat_labels(col)
    return(factor(unname(lab[as.character(x)]), levels = unname(lab)))
  }
  vals <- sort(unique(df[[col]]))
  factor(as.character(as.integer(x)), levels = as.character(as.integer(vals)))
}
cat_order <- function(col) levels(as_cat(col))

var_choices <- function(cols) stats::setNames(cols, vapply(cols, pretty_var, ""))
