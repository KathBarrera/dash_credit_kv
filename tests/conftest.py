"""Configuración común de las pruebas del tablero.

La app vive en dash/ y se importa como módulo de nivel superior (igual que gunicorn con
`--chdir dash app:server`), así que dash/ se agrega al path y se carga una sola vez por sesión.
"""
import sys
from pathlib import Path

import pytest

DASH_DIR = Path(__file__).resolve().parents[1] / "dash"
if str(DASH_DIR) not in sys.path:
    sys.path.insert(0, str(DASH_DIR))


@pytest.fixture(scope="session")
def app_mod():
    import app  # carga datos, modelos y entrena a Kyo (≈ 10 s)
    return app


@pytest.fixture(scope="session")
def client(app_mod):
    return app_mod.server.test_client()
