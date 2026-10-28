# -*- coding: utf-8 -*-
"""Motor de Kyo: un clasificador de intenciones entrenado con preguntas de ejemplo.

Cómo funciona
    1. Cada intención (una página, una gráfica, un concepto) trae varias preguntas de ejemplo.
    2. Las preguntas se normalizan (minúsculas, sin tildes, sinónimos) y se convierten en vectores
       TF-IDF de palabras (1-2 gramas) y de caracteres (3-5 gramas, tolera errores de escritura).
    3. Con esos vectores se entrena una regresión logística multiclase (scikit-learn).
    4. Para una pregunta nueva, el modelo da la probabilidad de cada intención. Si ni la
       probabilidad ni la similitud con los ejemplos alcanzan un mínimo, Kyo reconoce que no
       sabe la respuesta en vez de inventarla.
    5. El contexto importa: se da un pequeño impulso a las intenciones de la página abierta, y
       «explícame esta página» o «dame la versión técnica» usan la página y la última respuesta.
"""
import re
import unicodedata
from dataclasses import dataclass, field

import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Palabras que se unifican antes de vectorizar (después de quitar tildes)
SINONIMOS = {
    r"\bgrafic[oa]s?\b": "grafica",
    r"\bplots?\b": "grafica",
    r"\bchart\b": "grafica",
    r"\bdiagramas?\b": "grafica",
    r"\bincumplimientos?\b": "default",
    r"\bimpagos?\b": "default",
    r"\bmoros[oa]s?\b": "default",
    r"\bmorosidad\b": "default",
    r"\bincumpl\w*\b": "default",
    r"\bseccion(es)?\b": "pagina",
    r"\bpantallas?\b": "pagina",
    r"\bq\b": "que",
    r"\bcausa\w*\b": "causal",
    r"\bpestanas?\b": "pagina",
    r"\bapartados?\b": "pagina",
    r"\bdashboard\b": "tablero",
    r"\bdash\b": "tablero",
    r"\bcupos?\b": "limite",
    r"\bmodelos?\b": "modelo",
    r"\bmodels?\b": "modelo",
    r"\b(charts?|graphs?)\b": "grafica",
    r"\bdefault(s|ers?|ing|ed)\b": "default",
    r"\bscreens?\b": "page",
    r"\bvariables?\b": "variable",
    r"\bclientes?\b": "cliente",
    r"\bexplicame\b": "explica",
    r"\bexplicas\b": "explica",
    r"\bexplicar\b": "explica",
    r"\bsignifica\b": "significa",
    r"\balgoritmos?\b": "modelo",
    r"\bclasificador(es)?\b": "modelo",
    r"\b(limit|bill|pay)\s?(bal|amt|\d)": r"\1_\2",   # «limit bal», «pay 0», «pay0» -> limit_bal, pay_0
    r"\b(bill_amt|pay_amt)\s(\d)\b": r"\1\2",
}
_SIN = [(re.compile(k), v) for k, v in SINONIMOS.items()]

# Palabras vacías para el analizador de palabras (no se quitan «esta», «aqui», «tecnica»...)
STOP = {"el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al", "a", "en", "y", "o", "u",
        "me", "mi", "te", "se", "lo", "le", "les", "por", "para", "con", "sin", "sobre", "su", "sus", "es",
        "son", "que", "como", "cual", "cuales", "porfa", "favor", "puedes", "podrias", "quiero", "saber",
        "dime", "decir", "ser", "estar", "muy", "mas", "pero", "tambien", "ya", "dame", "muestrame", "cuentame",
        "explica", "donde", "cuando", "cuanto", "cuantos", "cuantas", "porque", "yo",
        "esta", "este", "estos", "estas", "tiene", "tienen", "hace", "hacer", "puedo", "algo", "ver",
        # inglés
        "the", "an", "of", "to", "in", "on", "at", "by", "is", "are", "was", "were", "be", "been", "it", "its",
        "and", "or", "for", "with", "about", "from", "do", "does", "did", "can", "could", "would", "should",
        "please", "tell", "explain", "give", "me", "my", "i", "there", "that", "these", "those",
        "any", "some", "into", "than", "then", "so", "very", "just", "also", "have", "has", "had", "get",
        "what", "how", "which", "who", "whom", "where", "when", "why", "am", "will", "quien", "quienes"}


def normalizar(texto):
    t = unicodedata.normalize("NFD", (texto or "").lower())
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    t = re.sub(r"[^a-z0-9_ ]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    for rx, rep in _SIN:
        t = rx.sub(rep, t)
    return t


def _palabras(t):
    return [w for w in t.split() if w not in STOP]


def _contenido(t):
    """Texto sin palabras vacías: las letras se comparan solo sobre lo que tiene significado."""
    return " ".join(_palabras(t)) or t


@dataclass
class Intencion:
    id: str
    titulo: str                      # nombre corto (se usa en enlaces y en «versión técnica de…»)
    ejemplos: list                   # preguntas de entrenamiento
    texto: str                       # respuesta principal (markdown)
    tecnico: str = None              # versión técnica opcional
    pagina: str = None               # ruta de la página donde está (para el botón «Ir a…»)
    sug: list = field(default_factory=list)   # preguntas sugeridas para seguir
    mood: str = "explaining"         # expresión de la mascota


TEXTOS = {   # frases fijas del asistente por idioma
    "es": {"tecnica": "Dame la explicación técnica", "esta": "Explícame esta página", "pagina": "esta página",
           "primero": "Primero pregúntame por alguna parte del tablero y luego te doy su explicación técnica.",
           "sin_tecnica": "**{t}** no tiene una versión más técnica que la que te di. Puedes preguntarme por otra "
                          "parte del tablero.",
           "version": "**Versión técnica · {t}**\n\n{x}",
           "no_se": "No tengo eso en lo que aprendí del tablero, así que prefiero no inventar. Puedo explicarte "
                    "cualquier página, gráfica o concepto del dash. Por ejemplo, de **{n}**:",
           "hola": "¡Hola! Soy **Kyo**, el asistente de este tablero. Me entrenaron con su contenido para "
                   "explicarte cada parte. Estás en **{n}**: pregúntame lo que quieras o toca una sugerencia."},
    "en": {"tecnica": "Give me the technical explanation", "esta": "Explain this page", "pagina": "this page",
           "primero": "First ask me about some part of the dashboard and then I'll give you its technical explanation.",
           "sin_tecnica": "**{t}** has no more technical version than the one I gave you. You can ask me about "
                          "another part of the dashboard.",
           "version": "**Technical version · {t}**\n\n{x}",
           "no_se": "That's not in what I learned from the dashboard, so I'd rather not make it up. I can explain "
                    "any page, chart or concept of the dashboard. For example, from **{n}**:",
           "hola": "Hi! I'm **Kyo**, this dashboard's assistant. I was trained on its content to explain every part "
                   "of it. You're on **{n}**: ask me anything or tap a suggestion."},
}


class Asistente:
    UMBRAL_PROB = 0.30
    UMBRAL_SIM = 0.30
    UMBRAL_LETRAS = 0.45
    IMPULSO_PAGINA = 0.10

    def __init__(self, por_idioma):
        """por_idioma: {"es": (intenciones, paginas, intencion_de_pagina, sug_de_pagina), "en": (...)}.

        Las intenciones tienen los mismos id en ambos idiomas: el clasificador se entrena con las preguntas
        de los dos, y la respuesta se toma del idioma elegido.
        """
        self.idiomas = list(por_idioma)
        self.I = {lg: {it.id: it for it in d[0]} for lg, d in por_idioma.items()}
        self.paginas = {lg: d[1] for lg, d in por_idioma.items()}             # ruta -> nombre visible
        self.intencion_de_pagina = por_idioma[self.idiomas[0]][2]             # ruta -> id de su intención
        self.sug_de_pagina = {lg: d[3] for lg, d in por_idioma.items()}       # ruta -> preguntas sugeridas
        X, y = [], []
        for lg, d in por_idioma.items():
            for it in d[0]:
                for e in list(it.ejemplos) + [it.titulo]:
                    X.append(normalizar(e))
                    y.append(it.id)
        self.vw = TfidfVectorizer(analyzer=_palabras, sublinear_tf=True)                  # palabras
        self.vc = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True,  # letras
                                  preprocessor=_contenido)
        self.Mw, self.Mc = self.vw.fit_transform(X), self.vc.fit_transform(X)
        self.M = hstack([self.Mw, self.Mc]).tocsr()
        self.y = np.array(y)
        self.clf = LogisticRegression(C=25, max_iter=4000)
        self.clf.fit(self.M, self.y)
        self.clases = list(self.clf.classes_)
        self.n_ejemplos = len(X)
        self.n_temas = len(self.I[self.idiomas[0]])

    def _lg(self, lang):
        return lang if lang in self.I else self.idiomas[0]

    # ------------------------------------------------------------------ clasificar
    def _vector(self, texto):
        t = normalizar(texto)
        w, c = self.vw.transform([t]), self.vc.transform([t])
        return w, c, hstack([w, c]).tocsr()

    def clasificar(self, texto, pagina=None):
        """Devuelve (id, probabilidad, similitud media, cobertura, similitud por letras).

        cobertura = fracción de palabras con contenido de la pregunta que el bot vio al entrenar.
        """
        w, c, v = self._vector(texto)
        if c.nnz == 0:
            return None, 0.0, 0.0, 0.0, 0.0
        p = self.clf.predict_proba(v)[0].copy()
        if pagina:
            base = self.I[self.idiomas[0]]
            for i, cl in enumerate(self.clases):
                if base[cl].pagina == pagina:
                    p[i] += self.IMPULSO_PAGINA
        k = int(np.argmax(p))
        cid = self.clases[k]
        rows = self.y == cid
        sw = (self.Mw[rows] @ w.T).toarray().ravel().max()   # coseno por palabras
        sc = (self.Mc[rows] @ c.T).toarray().ravel().max()   # coseno por letras
        palabras = _palabras(normalizar(texto))
        cobertura = (sum(x in self.vw.vocabulary_ for x in palabras) / len(palabras)) if palabras else 0.0
        return cid, float(min(p[k], 1.0)), float((sw + sc) / 2), float(cobertura), float(sc)

    def entiende(self, texto, pagina=None):
        """(id o None, probabilidad): None si la pregunta no se parece a nada de lo aprendido."""
        cid, prob, sim, cob, sc = self.clasificar(texto, pagina)
        if cid is None:
            return None, 0.0
        if cob >= 0.75:     # casi todo el vocabulario es conocido: basta una de las dos señales
            ok = prob >= self.UMBRAL_PROB or sim >= self.UMBRAL_SIM
        elif cob >= 0.4:    # mitad conocida: se exigen las dos
            ok = prob >= self.UMBRAL_PROB and sim >= self.UMBRAL_SIM
        else:               # casi todo desconocido: solo se acepta si parece un error de escritura
            ok = sc >= self.UMBRAL_LETRAS and prob >= 0.12
        return (cid if ok else None), prob

    # ------------------------------------------------------------------ responder
    def _paquete(self, it, lang, texto=None, mood=None, sug=None):
        s = list(sug if sug is not None else it.sug)
        tec = TEXTOS[lang]["tecnica"]
        if it.tecnico and texto is None and tec not in s:
            s = [tec] + s
        return {"t": texto or it.texto, "i": it.id, "m": mood or it.mood, "p": it.pagina,
                "n": self.paginas[lang].get(it.pagina, ""), "s": s[:4]}

    def responder(self, texto, pagina="/", ultimo=None, lang="es"):
        lang = self._lg(lang)
        I, tx = self.I[lang], TEXTOS[lang]
        pagina = pagina if pagina in self.paginas[lang] else "/"
        cid, _prob = self.entiende(texto, pagina)
        if cid is None:
            return self._no_se(pagina, lang)
        it = I[cid]
        if cid == "esta_pagina":
            pid = self.intencion_de_pagina.get(pagina, "p_inicio")
            return self._paquete(I[pid], lang)
        if cid == "mas_tecnico":
            prev = I.get(ultimo)
            if prev is None:
                return self._paquete(it, lang, tx["primero"], "thinking", self.sug_de_pagina[lang].get(pagina, []))
            if not prev.tecnico:
                return self._paquete(prev, lang, tx["sin_tecnica"].format(t=prev.titulo), "thinking")
            return self._paquete(prev, lang, tx["version"].format(t=prev.titulo, x=prev.tecnico), sug=prev.sug)
        return self._paquete(it, lang)

    def _no_se(self, pagina, lang="es"):
        lang = self._lg(lang)
        nombre = self.paginas[lang].get(pagina, TEXTOS[lang]["pagina"])
        return {"t": TEXTOS[lang]["no_se"].format(n=nombre),
                "i": None, "m": "thinking", "p": None, "n": "", "s": self.sug_de_pagina[lang].get(pagina, [])[:4]}

    def bienvenida(self, pagina="/", lang="es"):
        lang = self._lg(lang)
        pagina = pagina if pagina in self.paginas[lang] else "/"
        return {"t": TEXTOS[lang]["hola"].format(n=self.paginas[lang][pagina]),
                "i": None, "m": "happy", "p": None, "n": "",
                "s": [TEXTOS[lang]["esta"]] + self.sug_de_pagina[lang].get(pagina, [])[:3]}

    def nombre_pagina(self, pagina, lang="es"):
        lang = self._lg(lang)
        return self.paginas[lang].get(pagina, self.paginas[lang].get("/", ""))
