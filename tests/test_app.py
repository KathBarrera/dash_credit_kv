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


def test_assets_se_sirven_desde_dash_assets(client):
    """La app se crea en tablero/, pero los JS e imágenes siguen en dash/assets/."""
    html = client.get("/").get_data(as_text=True)
    assert "/assets/card_focus.js" in html
    assert client.get("/assets/card_focus.js").status_code == 200
    assert client.get("/assets/team/katherin.jpg").status_code == 200


# --- cada página del menú se construye sin errores en los dos idiomas ---

@pytest.mark.parametrize("lang", ["es", "en"])
def test_todas_las_paginas_se_construyen(app_mod, lang):
    for ruta in [ruta for ruta, *_ in app_mod.NAV]:
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


# --- CS-FOF y HIB: glosario de símbolos, pipeline y pestaña de mejora ---

def _texto(c):
    """Todo el texto de un componente de Dash, en orden."""
    if isinstance(c, (str, int, float)):
        return str(c)
    if isinstance(c, (list, tuple)):
        return " ".join(_texto(x) for x in c)
    return _texto(getattr(c, "children", None)) if c is not None else ""


def test_glosario_completo_en_los_dos_idiomas():
    from tablero.glosario import CODIGO, GLOSARIO
    assert set(GLOSARIO) == {"csfof", "hib"}
    for sc, d in GLOSARIO.items():
        for tok, (sym, es, en) in d.items():
            assert sym and len(es) == 2 and len(en) == 2 and all(es) and all(en), (sc, tok)
    for sc, m in CODIGO.items():
        assert set(m.values()) <= set(GLOSARIO[sc]), sc   # cada identificador del código apunta a un símbolo del glosario


def test_el_glosario_llega_a_la_pagina(client):
    html = client.get("/").get_data(as_text=True)
    assert "window.EQ_GLOSS=" in html and "Regularización" in html
    assert client.get("/assets/ecuaciones.js").status_code == 200
    assert client.get("/assets/pipeline.js").status_code == 200


@pytest.mark.parametrize("lang", ["es", "en"])
def test_pipeline_tiene_todas_las_etapas(app_mod, lang):
    from tablero.pipeline import ETAPAS, pipeline_body
    app_mod.set_lang(lang)
    try:
        cuerpo = pipeline_body()
        assert len(ETAPAS) == 11
        assert _texto(cuerpo).count("HIB") >= 2
    finally:
        app_mod.set_lang("es")


@pytest.mark.parametrize("lang", ["es", "en"])
def test_botones_de_pipeline_apuntan_a_etapas_que_existen(app_mod, lang):
    from tablero.pipeline import ETAPAS
    ids = {e[0] for e in ETAPAS}
    for ruta in ("/introduccion", "/univariado", "/multivariado", "/modelos", "/modelo-original", "/predecir", "/conclusiones"):
        pagina = app_mod.route(ruta, lang)
        encontrados = set()

        def recorrer(c):
            if isinstance(c, (list, tuple)):
                for x in c:
                    recorrer(x)
            elif hasattr(c, "children"):
                etapa = getattr(c, "data-pipe-open", None)
                if etapa:
                    encontrados.add(etapa)
                recorrer(c.children)
        recorrer(pagina)
        assert encontrados and encontrados <= ids, (ruta, encontrados)


@pytest.mark.parametrize("lang", ["es", "en"])
def test_pestana_de_mejora_sin_stacking_lr_ni_redes(app_mod, lang):
    from tablero.paginas.mejoras import csfof_beyond
    app_mod.set_lang(lang)
    try:
        txt = _texto(csfof_beyond())
        assert "HIB" in txt and "Wilcoxon" in txt
        # el stacking con regresión logística como combinador y las redes neuronales no se muestran
        assert "Stacking con regresión logística" not in txt and "Logistic regression stacking" not in txt
        for red in ("TabM", "TabPFN"):
            assert red not in txt
    finally:
        app_mod.set_lang("es")


def test_cifras_de_hib_coinciden_con_la_confirmacion_v2():
    """Las cifras clave de HIB salen de los resultados de la confirmación v2 (25 pliegues)."""
    from tablero.paginas.mejoras import BEYOND_ROWS
    v2 = next(r for r in BEYOND_ROWS if r[0].startswith("HIB, confirmación v2"))
    assert v2[2] == 0.5505 and v2[3] == 0.0037 and v2[6] == "21/25"
    assert all(r[9] < 0.05 for r in BEYOND_ROWS if r[10] in ("hib", "ens"))   # todos pasan Wilcoxon-Holm frente a XGBoost
    assert all(r[7] > 0.04 for r in BEYOND_ROWS if r[10] in ("ens", "hib"))    # y ninguno pasa Nadeau-Bengio con holgura (v2: 0.049)


@pytest.mark.parametrize("q, lang, tema", [
    ("¿qué es HIB?", "es", "hib"), ("explícame el pipeline del proyecto", "es", "pipeline"),
    ("¿qué es Wilcoxon con Holm?", "es", "wilcoxon_holm"), ("what is HIB?", "en", "hib"),
    ("what is the project pipeline?", "en", "pipeline")])
def test_kyo_conoce_hib_y_el_pipeline(app_mod, q, lang, tema):
    assert app_mod.BOT.responder(q, "/modelo-original", lang=lang)["i"] == tema
