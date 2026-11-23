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

def test_filtro_reduce_y_restaura(app_mod):
    total = len(app_mod.DF_FULL)
    sub = app_mod.aplicar_filtro({"sex": [2]})
    assert 0 < len(sub) < total and set(sub["SEX"]) == {2}
    with app_mod.filtrado({"sex": [2]}) as d:
        assert len(app_mod.df) == len(d) == len(sub)
    assert app_mod.df is app_mod.DF_FULL


def test_filtro_muy_estrecho_vuelve_a_todos(app_mod):
    assert app_mod.aplicar_filtro({"age": [200, 201]}) is app_mod.DF_FULL
    assert app_mod.aplicar_filtro(None) is app_mod.DF_FULL


# --- Kyo ---

def test_kyo_pasa_su_evaluacion(app_mod):
    from asistente import evaluar
    assert evaluar.main() == 0


def test_kyo_rechaza_preguntas_fuera_del_tablero(app_mod):
    assert app_mod.BOT.responder("recommend me a movie", "/")["i"] is None
