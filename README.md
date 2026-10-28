# Riesgo de Incumplimiento en Tarjetas de Crédito

**Dashboard interactivo de análisis exploratorio (EDA) del dataset Default of Credit Card Clients**



## Ver Dashboard en Vivo

[Ver Dashboard](https://dashcreditkv-production.up.railway.app/)



---

## Descripción del Proyecto

Las tarjetas de crédito son una de las líneas de la banca minorista con mayor exposición al riesgo: cada cliente recibe un cupo y se espera que lo pague en las fechas pactadas. Cuando no lo hace, la entidad enfrenta pérdidas, mayores costos de cobranza y la necesidad de provisionar capital. Entender qué perfiles y comportamientos anticipan el incumplimiento permite fijar límites, priorizar la cobranza y alimentar modelos de scoring.

Este proyecto presenta un tablero desarrollado con **Dash y Plotly** sobre el conjunto de datos *Default of Credit Card Clients* (UCI), con información de clientes de un banco de Taiwán entre abril y septiembre de 2005: límite de crédito, características demográficas, historial de pagos de seis meses, montos facturados, montos pagados y si el cliente incumplió el pago del mes siguiente. Cada gráfico incluye una interpretación básica (lenguaje cotidiano) y una técnica (estadísticos y recomendaciones de modelado).

El análisis incluye:
- Análisis Exploratorio de Datos (EDA) univariado y multivariado, con módulos interactivos de cruce de variables y matriz de dispersión
- Matriz de correlación de Spearman, robusta a valores extremos y adecuada para variables ordinales y binarias
- Pruebas estadísticas: χ² con V de Cramér, Mann-Whitney, t de Welch y Kruskal-Wallis
- Diagnóstico de multicolinealidad entre las variables de facturación (BILL_AMT)
- Análisis del desbalance de clases de la variable objetivo
- Sección **Predecir**: formulario visual (deslizadores y tarjetas con íconos) que devuelve en vivo el puntaje de riesgo de un cliente (mostrado como una tarjeta de crédito que se rompe por la mitad y se abre según el riesgo) usando un Random Forest **serializado con `joblib`** (`dash/modelo/modelo_credito.pkl`), con indicador, votos de los árboles, historial del cliente, aporte de cada grupo de variables y simulador «¿Qué pasaría si…?»
- **Español e inglés**: botón **ES | EN** en la barra superior (y en la portada) que traduce todo el tablero — textos, interpretaciones, gráficas, formulario y a Kyo — y se recuerda en el navegador
- Modo claro y oscuro, y menú lateral plegable
- **Kyo, asistente del tablero**: una mascota fija en la esquina inferior derecha; al tocarla se abre a la derecha un panel de chat (estilo Copilot de VS Code) que explica cada página, gráfica, variable, modelo y concepto del dash. Es un bot **entrenado** con scikit-learn (TF-IDF + regresión logística) sobre preguntas de ejemplo, usa las mismas cifras que dibujan las gráficas y reconoce cuando una pregunta no es del tablero
- Sección **Modelos**: carrusel deslizable con los siete clasificadores del proyecto (mejor combinación de cada uno), el mejor modelo resaltado, F1 por técnica de balanceo, F1 frente a ROC-AUC de las 112 combinaciones, matriz de confusión del mejor modelo y resumen de SHAP

---

## Dataset

El dataset utilizado es [Default of Credit Card Clients](https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients) (UCI Machine Learning Repository), de Yeh & Lien (2009). Contiene 30 000 clientes y 24 variables (23 predictoras y una variable objetivo).

> **Nota:** El archivo `default_of_credit_card_clients.xls` está incluido en la carpeta `dash/`. Si la aplicación no lo encuentra, intenta descargarlo automáticamente desde UCI; si esa descarga falla, descárguelo manualmente desde la fuente y colóquelo junto a `app.py`.

---

## Estructura del Proyecto

```
dash_credit_kv/
├── README.md                                # Este archivo
├── .gitignore
├── assets/
│   └── imagen_presentacion.jpeg             # Captura del dashboard
└── dash/
    ├── app.py                               # Aplicación completa (datos, figuras, páginas y callbacks)
    ├── results/
    │   └── model_results.csv                # 112 combinaciones de modelos (del repositorio Credit_Card_Project)
    └── modelo/
        ├── features.py                      # Transformaciones de variables del proyecto (las usa el .pkl)
        ├── entrenar.py                      # Entrena y serializa el modelo (python -m modelo.entrenar)
        ├── modelo_credito.pkl               # Modelo serializado con joblib
        └── modelo_credito.json              # Métricas, hiperparámetros y versiones
    ├── asistente/                           # Kyo, el bot que explica el tablero
    │   ├── motor.py                         # Clasificador de intenciones (TF-IDF + regresión logística)
    │   ├── conocimiento.py                  # Qué sabe: temas, preguntas de entrenamiento y respuestas
    │   ├── mascota.py                       # La mascota en SVG (con sus expresiones)
    │   └── evaluar.py                       # Evaluación con preguntas nuevas (python -m asistente.evaluar)
    ├── requirements.txt                     # Dependencias del proyecto
    └── default_of_credit_card_clients.xls   # Dataset
```

La aplicación tiene estas secciones: Introducción, Problema y Objetivos, Marco Teórico, EDA Univariado, EDA Multivariado, Modelos, Predecir, Enlaces y Equipo, más el asistente Kyo disponible en todas.

### Modelo serializado (sección Predecir)

El modelo se entrena una sola vez y se guarda en disco con `joblib`; el tablero solo lo carga y predice:

```bash
cd dash
python -m modelo.entrenar        # entrena, guarda modelo/modelo_credito.pkl y verifica que cargue
```

```python
import joblib
joblib.dump(modelo, "modelo/modelo_credito.pkl", compress=3)   # serializar
modelo = joblib.load("modelo/modelo_credito.pkl")              # cargar en app.py
riesgo = modelo.predict_proba(cliente)[0, 1]                   # predecir
```

El `.pkl` guarda el pipeline completo (transformaciones del proyecto + one-hot + Random Forest con `class_weight="balanced"`), así que recibe las 23 variables originales del dataset. Debe cargarse con la misma versión de scikit-learn con la que se guardó (fijada en `requirements.txt`).

### Idioma (español / inglés)

Cada texto del tablero está escrito en los dos idiomas con `tx("español", "english")` (o como par `("es", "en")` en las constantes). El botón **ES | EN** guarda el idioma en el navegador y los callbacks dibujan cada página, gráfica e interpretación en ese idioma. Para agregar un texto nuevo, escríbelo así: `tx("Hola", "Hello")`.

### Asistente Kyo (bot entrenado)

Kyo está fijo en la esquina inferior derecha de la pantalla y saluda con un globo al abrir el tablero. Al tocarlo se abre un panel a la derecha que empuja el contenido, como el chat de Copilot en VS Code; se cierra con la **X** o con `Esc`.

Cómo está entrenado:

1. `asistente/conocimiento.py` define unos 80 temas (cada página, gráfica, variable, modelo y concepto) con varias preguntas de ejemplo cada uno. Las respuestas toman las cifras de las mismas funciones que dibujan el tablero (`interp_corr`, `interp_rates`, …), así que siempre coinciden con lo que se ve.
2. `asistente/motor.py` convierte las preguntas en vectores TF-IDF de palabras y de fragmentos de letras (tolera errores de escritura) y entrena una regresión logística multiclase. El entrenamiento tarda menos de un segundo y se hace al arrancar la app.
3. Usa el contexto: «explícame esta página» responde según la página abierta y «dame la explicación técnica» amplía la última respuesta.
4. Es bilingüe: cada tema tiene preguntas y respuestas en español e inglés; se entrena con ambas y responde en el idioma elegido con el botón ES | EN.
5. Si una pregunta no se parece a nada de lo aprendido, lo dice en vez de inventar. No usa servicios externos ni claves de API.

Para evaluarlo con preguntas que no están en su entrenamiento:

```bash
cd dash
python -m asistente.evaluar
```

Para enseñarle algo nuevo, agrega un `Intencion(...)` en `asistente/conocimiento.py` con varias formas de preguntar y su respuesta, usando `t("español", "english")`.

`results/model_results.csv` resume los resultados de [Credit_Card_Project](https://github.com/valeriaflorezs/Credit_Card_Project) (`results/experiments_posthoc_metrics.csv` para los 96 experimentos locales y `results/svm_gpu_results_colab.csv` para SVM): F1, precisión, recall, ROC-AUC y PR-AUC medios de cada combinación modelo × técnica de balanceo × método de optimización.

---

## Cómo ejecutar la aplicación

**1. Clonar el repositorio**

```bash
git clone https://github.com/KathBarrera/dash_credit_kv.git
cd dash_credit_kv
```

**2. (Opcional) Crear un entorno virtual**

```bash
conda create -n mi_env python=3.13
conda activate mi_env
```

**3. Instalar las dependencias**

```bash
cd dash
pip install -r requirements.txt
```

**4. Verificar el dataset**

Confirma que `default_of_credit_card_clients.xls` esté en la carpeta `dash/`. Si no está, descárgalo desde [UCI](https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients) y colócalo ahí.

**5. Ejecutar la aplicación**

```bash
python app.py
```

**6. Abrir en el navegador**

```
http://localhost:8050/
```

---

## Despliegue en Render (gratis)

El repositorio trae `render.yaml`, así que Render toma la configuración solo:

1. En [render.com](https://render.com) entra con GitHub y elige **New + → Blueprint**, con el repositorio `KathBarrera/dash_credit_kv` (rama `main`).
2. Render instala `requirements.txt` y arranca un solo worker de gunicorn (con 4 hilos y sin `--preload`). El plan gratis tiene 512 MB y así el tablero usa unos 350 MB; con 2 workers se pasaría.
3. Copia la URL pública que te da Render (algo como `https://dash-credit-kv.onrender.com`).

### Mantenerlo despierto

En el plan gratis, Render apaga el servicio tras 15 minutos sin visitas y la siguiente visita tarda entre 30 y 60 segundos en despertarlo. Para evitarlo, algo externo debe visitar `/ping` (una respuesta mínima que no carga la página) cada pocos minutos. Hay dos opciones; se pueden usar las dos:

- **UptimeRobot o cron-job.org** (necesaria): en [uptimerobot.com](https://uptimerobot.com) crea un monitor *HTTP(s)* con la URL `https://dash-credit-kv.onrender.com/ping` y un intervalo de 5 minutos (o en [cron-job.org](https://cron-job.org) una tarea cada 5 minutos a esa URL).
- **GitHub Actions** (solo respaldo): `.github/workflows/mantener-despierto.yml` pide visitar `/ping` cada 10 minutos, pero GitHub retrasa mucho las tareas programadas (en la práctica se ejecutó cada 4–5 horas), así que por sí sola no evita que Render duerma el servicio. Si tu URL no es `https://dash-credit-kv.onrender.com`, créala como variable del repositorio `RENDER_URL` en *Settings → Secrets and variables → Actions → Variables*. GitHub desactiva las tareas programadas si el repositorio pasa 60 días sin cambios; se reactivan desde la pestaña *Actions*.

Un servicio encendido todo el mes usa unas 744 de las 750 horas gratis mensuales de Render, así que conviene tener un solo servicio gratis en la cuenta.

## Despliegue en Railway

El repositorio ya trae la configuración (`railway.json`, `requirements.txt` y `.python-version` en la raíz):

1. En [railway.com](https://railway.com) crea un proyecto con **New Project → Deploy from GitHub repo** y elige `KathBarrera/dash_credit_kv` (rama `main`).
2. No hace falta cambiar el *Root Directory*: Railway instala `dash/requirements.txt` y arranca con
   `gunicorn --chdir dash app:server --bind 0.0.0.0:$PORT --workers 2 --preload --timeout 120`.
3. En **Settings → Networking** pulsa **Generate Domain** para obtener la URL pública.

El dataset está en `dash/`; si faltara, la aplicación lo descarga de UCI al arrancar (una sola vez gracias a `--preload`).

El modelo de la sección Predecir ya viene serializado en `dash/modelo/modelo_credito.pkl`, así que Railway no entrena nada: solo instala dependencias y arranca. Para reentrenarlo, ejecuta `python -m modelo.entrenar` dentro de `dash/` y sube el `.pkl` y el `.json` nuevos.

---

## Equipo

Este proyecto fue desarrollado por:

- **Katherin Barrera** —  [GitHub](https://github.com/KathBarrera)
- **Valeria Flórez** —[GitHub](https://github.com/valeriaflorezs)
