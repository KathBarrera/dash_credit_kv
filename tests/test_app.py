"""Pruebas de humo del tablero: arranca, responde, dibuja cada página y predice.

Uso, desde la raíz del repositorio:  python -m pytest tests/ -q
"""
import json

import pytest


# --- arranque y rutas de salud (las usan Render y el workflow «Mantener despierto») ---

def test_ping(client):
    r = client.get("/ping")
    assert r.status_code == 200
    assert r.get_data(as_text=True) == "ok"


def test_health_reporta_el_modelo_cargado(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert json.loads(r.get_data(as_text=True)) == {"status": "ok", "modelo": True}


def test_portada_y_layout_responden(client):
    assert client.get("/").status_code == 200
    assert client.get("/_dash-layout").status_code == 200
    assert client.get("/_dash-dependencies").status_code == 200


# --- cada página del menú se construye sin errores en los dos idiomas ---

def _rutas():
    import app
    return [ruta for ruta, *_ in app.NAV]


@pytest.mark.parametrize("lang", ["es", "en"])
def test_todas_las_paginas_se_construyen(app_mod, lang):
    for ruta in _rutas():
        assert app_mod.route(ruta, lang) is not None, ruta


# --- modelos de «Predecir» ---

def test_modelos_serializados_cargan(app_mod):
    assert app_mod.MODELO is not None, getattr(app_mod, "MODELO_ERROR", "")
    assert set(app_mod.MODELOS) == {"xgboost", "cs_fof"}


@pytest.mark.parametrize("modelo", ["xgboost", "cs_fof"])
def test_puntajes_validos_y_ordenados(app_mod, modelo):
    perfiles = {k: v for k, (_, v) in app_mod.PROFILES.items()}
    p = {k: app_mod.predict_risk(v, modelo) for k, v in perfiles.items()}
    assert all(0.0 <= x <= 1.0 for x in p.values()), p
    # un cliente con atrasos recientes debe salir más riesgoso que uno al día con cupo alto
    assert p["atrasos"] > p["al-dia"], p


@pytest.mark.parametrize("modelo", ["xgboost", "cs_fof"])
def test_sexo_otro_promedia_hombre_y_mujer(app_mod, modelo):
    base = dict(app_mod.PROFILES["atrasos"][1])
    h, m, o = (app_mod.predict_risk({**base, "SEX": s}, modelo) for s in (1, 2, app_mod.SEX_OTHER))
    assert o == pytest.approx((h + m) / 2)


def test_umbral_y_metadatos_del_modelo(app_mod):
    meta = app_mod._meta("xgboost")
    assert meta["versiones"]["scikit-learn"]
    assert app_mod._mk("no-existe") == "xgboost"


# --- filtro global del EDA ---

def test_filtro_reduce_sin_tocar_los_datos(app_mod):
    total = len(app_mod.DF)
    sub = app_mod.aplicar_filtro({"sex": [2]})
    assert 0 < len(sub) < total and set(sub["SEX"]) == {2}
    assert len(app_mod.DF) == total


def test_filtro_muy_estrecho_vuelve_a_todos(app_mod):
    assert app_mod.aplicar_filtro({"age": [200, 201]}) is app_mod.DF
    assert app_mod.aplicar_filtro(None) is app_mod.DF


def _total_barras(fig):
    return sum(sum(t.y) for t in fig.data if t.type == "bar")


def test_las_figuras_usan_el_subconjunto(app_mod):
    sub = app_mod.aplicar_filtro({"sex": [2]})
    assert _total_barras(app_mod.fig_target(data=sub)) == len(sub)
    assert _total_barras(app_mod.fig_target()) == len(app_mod.DF)
    # la matriz de Spearman también sigue al filtro
    assert not app_mod.spearman(sub).equals(app_mod.spearman())


def _pedir_target(app_mod, f):
    """Llama al callback real de la gráfica objetivo por HTTP, como lo hace el navegador."""
    payload = {"output": "target-graph.figure", "outputs": {"id": "target-graph", "property": "figure"},
               "inputs": [{"id": "eda-filter", "property": "data", "value": f},
                          {"id": "theme", "property": "data", "value": "light"},
                          {"id": "lang", "property": "data", "value": "es"}],
               "changedPropIds": ["eda-filter.data"], "state": []}
    r = app_mod.server.test_client().post("/_dash-update-component", json=payload)
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    fig = r.get_json()["response"]["target-graph"]["figure"]
    return sum(_valores(t["y"]).sum() for t in fig["data"] if t["type"] == "bar")


def _valores(y):
    """Plotly manda los arreglos de numpy como {"dtype", "bdata"} (base64); listas simples, tal cual."""
    import base64
    import numpy as np
    if isinstance(y, dict):
        return np.frombuffer(base64.b64decode(y["bdata"]), dtype=y["dtype"])
    return np.asarray(y)


def test_peticiones_simultaneas_no_se_mezclan(app_mod):
    """Sin estado global, varios filtros distintos a la vez dan cada uno su propio resultado."""
    from concurrent.futures import ThreadPoolExecutor
    filtros = [{"sex": [1]}, {"sex": [2]}, None] * 6
    esperado = [len(app_mod.aplicar_filtro(f)) for f in filtros]
    with ThreadPoolExecutor(8) as ex:
        assert list(ex.map(lambda f: _pedir_target(app_mod, f), filtros)) == esperado


# --- Kyo ---

def test_kyo_pasa_su_evaluacion(app_mod):
    from asistente import evaluar
    assert evaluar.main() == 0


def test_kyo_rechaza_preguntas_fuera_del_tablero(app_mod):
    assert app_mod.BOT.responder("recommend me a movie", "/")["i"] is None
