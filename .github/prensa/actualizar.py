#!/usr/bin/env python3
"""Prensa de Javier: prepara noticias.json con la API de Anthropic.

Lo lanza GitHub Actions (.github/workflows/prensa.yml). Pasos:
  1. Lee las portadas (RSS o, si no hay, la web) de los seis periódicos.
  2. Claude elige las noticias más destacadas de cada uno.
  3. Descarga cada artículo y Claude escribe titular y resumen para el oído.
  4. Claude elige la portada (hechos distintos) y se guarda noticias.json.

Variables de entorno:
  ANTHROPIC_API_KEY  clave de la API (secreto del repositorio).
  MODELO             modelo a usar (por defecto claude-haiku-5-5).
  FORZAR=1           actualiza aunque ya se haya hecho hoy o no sea la hora.
  PRUEBA=1           solo comprueba que se leen los periódicos; no llama a la API ni escribe nada.
"""
import datetime as dt
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARCHIVO = os.path.join(RAIZ, "noticias.json")
MADRID = ZoneInfo("Europe/Madrid")
MODELO = os.environ.get("MODELO", "claude-haiku-5-5")
HORA_MINIMA = 11  # no actualiza antes de las 11:00 de Madrid (salvo FORZAR)
POR_DIARIO = 3
MIN_NOTICIAS = 6  # si salen menos, no se sobrescribe lo anterior

DIARIOS = [
    {"id": "ld", "nombre": "Libertad Digital", "dominio": "libertaddigital.com",
     "rss": ["https://feeds2.feedburner.com/libertaddigital/portada",
             "https://www.libertaddigital.com/rss/portada.xml"],
     "web": "https://www.libertaddigital.com/"},
    {"id": "ee", "nombre": "El Español", "dominio": "elespanol.com",
     "rss": ["https://www.elespanol.com/rss/"],
     "web": "https://www.elespanol.com/"},
    {"id": "ed", "nombre": "El Debate", "dominio": "eldebate.com",
     "rss": ["https://www.eldebate.com/rss/home.xml", "https://www.eldebate.com/rss/"],
     "web": "https://www.eldebate.com/"},
    {"id": "to", "nombre": "The Objective", "dominio": "theobjective.com",
     "rss": ["https://theobjective.com/feed/"],
     "web": "https://theobjective.com/"},
    {"id": "ok", "nombre": "OKDiario", "dominio": "okdiario.com", "filtro": "/espana/",
     "rss": ["https://okdiario.com/feed/espana", "https://okdiario.com/espana/feed"],
     "web": "https://okdiario.com/espana"},
    {"id": "edi", "nombre": "elDiario.es", "dominio": "eldiario.es",
     "rss": ["https://www.eldiario.es/rss/"],
     "web": "https://www.eldiario.es/"},
]

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")

GASTO = {"entrada": 0, "salida": 0}


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- descarga

def bajar(url, intentos=2):
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA, "Accept-Language": "es-ES,es;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
            with urllib.request.urlopen(req, timeout=25) as r:
                datos = r.read()
                cs = r.headers.get_content_charset() or "utf-8"
                return datos.decode(cs, errors="replace")
        except Exception as e:  # noqa: BLE001
            if i == intentos - 1:
                log(f"   ✗ {url}: {e}")
            time.sleep(2)
    return None


def limpiar(texto):
    texto = re.sub(r"<[^>]+>", " ", texto or "")
    texto = html.unescape(texto)
    return re.sub(r"\s+", " ", texto).strip()


def candidatos_rss(diario):
    for url in diario["rss"]:
        xml = bajar(url)
        if not xml or "<item" not in xml and "<entry" not in xml:
            continue
        try:
            raiz = ET.fromstring(xml.encode("utf-8", errors="replace"))
        except ET.ParseError:
            continue
        lista = []
        for it in raiz.iter():
            tag = it.tag.split("}")[-1]
            if tag not in ("item", "entry"):
                continue
            titulo = enlace = desc = ""
            for h in it:
                t = h.tag.split("}")[-1]
                ns = h.tag.split("}")[0] if "}" in h.tag else ""
                if "search.yahoo.com/mrss" in ns:  # media:title, media:description… (pies de foto)
                    continue
                if t == "title" and not titulo:
                    titulo = limpiar(h.text)
                elif t == "link" and not enlace:
                    enlace = (h.text or h.get("href") or "").strip()
                elif t in ("description", "summary") and not desc:
                    desc = limpiar(h.text)[:300]
            if titulo and enlace:
                lista.append({"titulo": titulo, "url": enlace, "entradilla": desc})
        if lista:
            return lista, "rss"
    return [], None


def candidatos_web(diario):
    pagina = bajar(diario["web"])
    if not pagina:
        return [], None
    vistos, lista = set(), []
    for m in re.finditer(r'<a\b[^>]*href="([^"#]+)"[^>]*>(.*?)</a>', pagina, re.S | re.I):
        url = urllib.parse.urljoin(diario["web"], html.unescape(m.group(1)))
        texto = limpiar(m.group(2))
        p = urllib.parse.urlparse(url)
        if diario["dominio"] not in p.netloc or not (35 <= len(texto) <= 220):
            continue
        if len([s for s in p.path.split("/") if s]) < 2 or url in vistos:
            continue
        vistos.add(url)
        lista.append({"titulo": texto, "url": url, "entradilla": ""})
    return lista, "web"


def candidatos(diario):
    lista, origen = candidatos_rss(diario)
    if len(lista) < 5:
        lista2, origen2 = candidatos_web(diario)
        if len(lista2) > len(lista):
            lista, origen = lista2, origen2
    filtro = diario.get("filtro")
    if filtro:
        lista = [c for c in lista if filtro in c["url"]]
    lista = [c for c in lista if diario["dominio"] in urllib.parse.urlparse(c["url"]).netloc]
    vistos, unicos = set(), []
    for c in lista:
        if c["url"] not in vistos:
            vistos.add(c["url"])
            unicos.append(c)
    return unicos[:35], origen


def texto_articulo(url):
    pagina = bajar(url)
    if not pagina:
        return ""
    # 1) articleBody de JSON-LD (lo traen casi todos los diarios)
    for bloque in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', pagina, re.S | re.I):
        try:
            datos = json.loads(bloque.strip())
        except Exception:  # noqa: BLE001
            continue
        pila = datos if isinstance(datos, list) else [datos]
        while pila:
            d = pila.pop()
            if isinstance(d, dict):
                if isinstance(d.get("articleBody"), str) and len(d["articleBody"]) > 400:
                    return limpiar(d["articleBody"])[:9000]
                pila.extend(v for v in d.values() if isinstance(v, (dict, list)))
            elif isinstance(d, list):
                pila.extend(d)
    # 2) párrafos de la página
    parrafos = [limpiar(p) for p in re.findall(r"<p\b[^>]*>(.*?)</p>", pagina, re.S | re.I)]
    parrafos = [p for p in parrafos if len(p) > 60]
    entr = re.search(r'<meta[^>]+property="og:description"[^>]+content="([^"]*)"', pagina)
    texto = (limpiar(entr.group(1)) + "\n" if entr else "") + "\n".join(parrafos[:30])
    return texto[:9000]


# ---------------------------------------------------------------- Claude

SIN_RAZONAR = {"ok": True}  # se apaga si la API no admite desactivar el razonamiento


def claude(sistema, mensaje, max_tokens=4000):
    clave = os.environ["ANTHROPIC_API_KEY"]
    for intento in range(5):
        peticion = {"model": MODELO, "max_tokens": max_tokens, "system": sistema,
                    "messages": [{"role": "user", "content": mensaje}]}
        if SIN_RAZONAR["ok"]:
            peticion["thinking"] = {"type": "disabled"}
        else:
            peticion["max_tokens"] = max_tokens + 6000  # deja sitio al razonamiento
        cuerpo = json.dumps(peticion).encode("utf-8")
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=cuerpo, method="POST",
            headers={"x-api-key": clave, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                resp = json.loads(r.read().decode("utf-8"))
            uso = resp.get("usage", {})
            GASTO["entrada"] += uso.get("input_tokens", 0)
            GASTO["salida"] += uso.get("output_tokens", 0)
            texto = "".join(b.get("text", "") for b in resp.get("content", []) if b.get("type") == "text")
            if not texto.strip():
                tipos = [b.get("type") for b in resp.get("content", [])]
                log(f"   API sin texto: stop_reason={resp.get('stop_reason')} bloques={tipos} uso={uso}")
            return texto
        except urllib.error.HTTPError as e:
            detalle = e.read().decode("utf-8", errors="replace")[:300]
            log(f"   API {e.code}: {detalle}")
            if e.code == 400 and SIN_RAZONAR["ok"] and "thinking" in detalle:
                SIN_RAZONAR["ok"] = False
                continue
            if e.code in (429, 500, 502, 503, 529) and intento < 3:
                time.sleep(15 * (intento + 1))
                continue
            raise
        except urllib.error.URLError as e:
            log(f"   API sin conexión: {e}")
            if intento < 3:
                time.sleep(10)
                continue
            raise
    raise RuntimeError("La API no respondió")


def json_de(texto):
    texto = texto.strip()
    if "{" not in texto and "[" not in texto:
        log(f"   respuesta sin JSON: {texto[:300]!r}")
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto)
    ini = min([i for i in (texto.find("{"), texto.find("[")) if i >= 0], default=-1)
    fin = max(texto.rfind("}"), texto.rfind("]"))
    if ini < 0 or fin < 0:
        raise ValueError("Claude no devolvió JSON")
    return json.loads(texto[ini:fin + 1])


SIS_ELEGIR = (
    "Eres el editor de una web que le lee la prensa en voz alta a un señor mayor casi ciego. "
    "Te paso los titulares de la portada de un periódico español. Elige las {n} noticias más "
    "destacadas e importantes de hoy, de hechos distintos entre sí. Salta opinión, columnas, "
    "pasatiempos, horóscopo, el tiempo, precios de gasolina o de la luz, publicidad, ofertas, "
    "directos sin contenido, vídeos y galerías. Responde SOLO con JSON: {{\"elegidas\": [números]}}, "
    "en orden de importancia."
)

SIS_ESCRIBIR = (
    "Escribes para la web «Prensa de Javier», que le LEE EN VOZ ALTA las noticias a Javier, un señor "
    "mayor casi ciego. Todo debe sonar natural al oído.\n"
    "Para la noticia que te paso escribe, con TUS PROPIAS PALABRAS (nunca copies frases del artículo; "
    "como mucho una cita breve de menos de 15 palabras si es imprescindible):\n"
    "- titular: claro y corto, entendible al oírlo.\n"
    "- resumen: entre 110 y 170 palabras, frases cortas, tono neutro, atribuyendo al periódico o a "
    "las fuentes las afirmaciones polémicas («según {nombre}…»). Para el oído: nada de siglas raras "
    "sin explicar, fechas como «29 de noviembre» (no «29-N»), sin paréntesis ni viñetas, números "
    "romanos escritos con letra. Solo hechos que estén en el artículo; no inventes nada.\n"
    "Si el texto no trae información suficiente para un resumen fiable, responde {{\"vacio\": true}}.\n"
    "Responde SOLO con JSON: {{\"titular\": \"…\", \"resumen\": \"…\"}}"
)

SIS_PORTADA = (
    "Eres el editor de la web «Prensa de Javier». Te paso las noticias de hoy de varios periódicos "
    "(id y titular). Elige entre 7 y 9 para la portada: las más importantes del día, mezclando "
    "periódicos, empezando por la más importante. Cada una debe ser de un HECHO DISTINTO: si dos "
    "periódicos cuentan lo mismo (el mismo suceso, declaración o votación, aunque con otro enfoque), "
    "elige solo una. Responde SOLO con JSON: {\"portada\": [\"id\", …]}"
)


def elegir(diario, lista):
    lineas = "\n".join(
        f"{i}. {c['titulo']}" + (f" — {c['entradilla'][:160]}" if c["entradilla"] else "")
        for i, c in enumerate(lista))
    sis = SIS_ELEGIR.format(n=POR_DIARIO + 2)  # 2 de reserva por si algún artículo no se lee
    datos = json_de(claude(sis, f"Periódico: {diario['nombre']}\n\n{lineas}", 400))
    idx = [i for i in datos.get("elegidas", []) if isinstance(i, int) and 0 <= i < len(lista)]
    return [lista[i] for i in dict.fromkeys(idx)]


def escribir(diario, cand, texto):
    sis = SIS_ESCRIBIR.format(nombre=diario["nombre"])
    msg = (f"Periódico: {diario['nombre']}\nTitular original: {cand['titulo']}\n"
           f"URL: {cand['url']}\n\nTexto del artículo:\n{texto}")
    datos = json_de(claude(sis, msg, 1200))
    if datos.get("vacio") or not datos.get("titular") or not datos.get("resumen"):
        return None
    palabras = len(datos["resumen"].split())
    if palabras < 60:
        return None
    return {"titular": datos["titular"].strip(), "resumen": datos["resumen"].strip()}


# ---------------------------------------------------------------- principal

def main():
    ahora = dt.datetime.now(MADRID)
    forzar = os.environ.get("FORZAR") == "1"
    prueba = os.environ.get("PRUEBA") == "1"
    hoy = ahora.date().isoformat()

    anterior = {}
    try:
        with open(ARCHIVO, encoding="utf-8") as f:
            anterior = json.load(f)
    except Exception:  # noqa: BLE001
        pass

    if not prueba and not forzar:
        if ahora.hour < HORA_MINIMA:
            log(f"Son las {ahora:%H:%M} en Madrid: todavía no toca (a partir de las {HORA_MINIMA}:00).")
            return 0
        if anterior.get("fecha") == hoy:
            log("Ya estaba actualizada hoy.")
            return 0
    if not prueba and not os.environ.get("ANTHROPIC_API_KEY"):
        log("Falta el secreto ANTHROPIC_API_KEY en el repositorio.")
        return 1

    diarios_out, fallos = [], []
    for d in DIARIOS:
        log(f"\n== {d['nombre']}")
        lista, origen = candidatos(d)
        log(f"   {len(lista)} titulares (de {origen or 'ninguna fuente'})")
        if prueba:
            for c in lista[:5]:
                log(f"   · {c['titulo'][:90]}")
            if lista:
                t = texto_articulo(lista[0]["url"])
                log(f"   texto del primer artículo: {len(t)} caracteres")
            continue
        if len(lista) < 3:
            fallos.append(d["nombre"])
            continue
        try:
            elegidas = elegir(d, lista)
        except Exception as e:  # noqa: BLE001
            log(f"   ✗ al elegir: {e}")
            fallos.append(d["nombre"])
            continue
        noticias = []
        for cand in elegidas:
            if len(noticias) == POR_DIARIO:
                break
            texto = texto_articulo(cand["url"])
            if len(texto) < 400:
                log(f"   - sin texto suficiente: {cand['url']}")
                continue
            try:
                n = escribir(d, cand, texto)
            except Exception as e:  # noqa: BLE001
                log(f"   ✗ al escribir: {e}")
                continue
            if n:
                n = {"id": f"{d['id']}{len(noticias) + 1}", **n, "url": cand["url"]}
                noticias.append(n)
                log(f"   ✓ {n['id']}: {n['titular']}")
        if noticias:
            diarios_out.append({"id": d["id"], "nombre": d["nombre"], "noticias": noticias})
        else:
            fallos.append(d["nombre"])

    if prueba:
        log("\nPrueba terminada: no se ha escrito nada.")
        return 0

    todas = [n for d in diarios_out for n in d["noticias"]]
    if len(todas) < MIN_NOTICIAS:
        log(f"\nSolo {len(todas)} noticias: no sobrescribo las anteriores.")
        return 1

    ids = {n["id"] for n in todas}
    lineas = "\n".join(f"{n['id']} ({d['nombre']}): {n['titular']}"
                       for d in diarios_out for n in d["noticias"])
    try:
        portada = json_de(claude(SIS_PORTADA, lineas, 300)).get("portada", [])
    except Exception as e:  # noqa: BLE001
        log(f"✗ al elegir la portada: {e}")
        portada = []
    portada = [i for i in dict.fromkeys(portada) if i in ids][:9]
    if len(portada) < 7:  # completa con la primera de cada periódico, luego la segunda…
        for k in range(POR_DIARIO):
            for d in diarios_out:
                if len(d["noticias"]) > k and d["noticias"][k]["id"] not in portada and len(portada) < 8:
                    portada.append(d["noticias"][k]["id"])

    ahora = dt.datetime.now(MADRID).replace(microsecond=0)
    salida = {
        "fecha": ahora.date().isoformat(),
        "fechaTexto": f"{DIAS[ahora.weekday()]} {ahora.day} de {MESES[ahora.month - 1]}",
        "actualizado": ahora.isoformat(),
        "portada": portada,
        "diarios": diarios_out,
    }
    urls = [n["url"] for n in todas]
    assert len(urls) == len(set(urls)), "URLs repetidas"
    with open(ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=1)
        f.write("\n")

    coste = GASTO["entrada"] / 1e6 * 0.10 + GASTO["salida"] / 1e6 * 0.50
    log(f"\nGuardadas {len(todas)} noticias, {len(portada)} en portada."
        + (f" Fallaron: {', '.join(fallos)}." if fallos else "")
        + f" Tokens: {GASTO['entrada']} de entrada y {GASTO['salida']} de salida"
        + (f" (≈ {coste:.3f} $ con Haiku)." if "haiku" in MODELO else "."))
    with open(os.environ.get("GITHUB_STEP_SUMMARY", os.devnull), "a", encoding="utf-8") as f:
        f.write(f"Guardadas {len(todas)} noticias ({salida['actualizado']}). "
                + (f"Fallaron: {', '.join(fallos)}. " if fallos else "")
                + f"Tokens: {GASTO['entrada']} entrada / {GASTO['salida']} salida.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
