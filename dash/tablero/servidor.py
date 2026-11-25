# -*- coding: utf-8 -*-
"""La aplicación Dash y las rutas mínimas /ping y /health para Render y los monitores."""

from dash import Dash

from tablero.config import BASE_DIR
from tablero.prediccion import MODELO

# assets_folder explícito: la app se crea dentro de tablero/, pero los recursos siguen en dash/assets/
app = Dash(__name__, suppress_callback_exceptions=True, title="EDA · Riesgo Crediticio",
           assets_folder=str(BASE_DIR / "assets"))
server = app.server   # <- para despliegue (gunicorn app:server)


@server.route("/ping")
def ping():
    """Respuesta mínima para monitores (UptimeRobot, GitHub Actions) que mantienen despierto el
    servicio gratis de Render, sin cargar la página completa."""
    return "ok", 200, {"Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store"}


@server.route("/health")
def health():
    """Chequeo de salud para monitores externos y el workflow de GitHub: confirma que la app y el
    modelo están cargados, sin dibujar la página (responde en milisegundos)."""
    body = '{"status": "ok", "modelo": %s}' % ("true" if MODELO is not None else "false")
    return body, 200, {"Content-Type": "application/json", "Cache-Control": "no-store"}
