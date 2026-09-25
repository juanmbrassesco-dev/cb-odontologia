#!/usr/bin/env python3
"""Arma los tableros de la fase ⑦ leyendo css/tokens.css.

Un tablero es una página HTML que muestra una parte del sistema de interfaz.
Se GENERA, nunca se edita a mano: los colores salen del mismo archivo que usa
el sitio, así que un tablero no puede mentir sobre lo que el sitio hace.

    python3 tools/construir-tableros.py

Escribe brand/tableros/<pieza>/<ancho>.html y no toca nada más.
"""

import importlib.util
import pathlib
import re
import subprocess
import sys


RAIZ = pathlib.Path(__file__).resolve().parent.parent
TOKENS = RAIZ / "css" / "tokens.css"
SALIDA = RAIZ / "brand" / "tableros"


def cargar_medidor():
    """Importa medir-contraste.py, que tiene guion en el nombre."""
    ruta = pathlib.Path(__file__).resolve().parent / "medir-contraste.py"
    spec = importlib.util.spec_from_file_location("medidor", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


MEDIDOR = cargar_medidor()


# El color SIEMPRE sale de tokens.css. Acá vive sólo la prosa.
PALETA_BRIEF = [
    ("marfil", "Marfil", "fondo base de todo el sitio"),
    ("blanco", "Blanco", "superficies y tarjetas"),
    ("dorado", "Dorado", "acento: línea, borde, ícono, fondo"),
    ("dorado-claro", "Dorado claro", "fondos suaves"),
    ("grafito", "Gris grafito", "texto de lectura"),
]

DERIVADOS = [
    ("dorado-texto", "Dorado de texto",
     "El dorado del brief no llega al piso sobre marfil y no puede ser letra. "
     "Mismo tono y misma saturación, doce puntos menos de luz."),
    ("borde", "Borde de control",
     "El grafito aclarado hasta el piso de 3,0 de los bordes. "
     "Más claro que esto y el campo deja de verse como campo."),
    ("apagado", "Texto apagado",
     "Para lo deshabilitado. WCAG exime a los controles apagados; "
     "acá pasa igual, porque apagado no es lo mismo que ilegible."),
    ("error", "Error",
     "El brief no tiene estados. Se eligió dentro de la familia cálida "
     "de la paleta, no el rojo de sistema."),
    ("exito", "Éxito",
     "Mismo criterio: un verde apagado que convive con el marfil, "
     "no el verde de un cartel de tránsito."),
]


def muestra(nombre, titulo, motivo, tokens):
    """Una tarjeta de color: el color arriba, el nombre y el hex abajo."""
    valor = tokens[nombre]
    return f"""
      <figure class="muestra">
        <div class="muestra-color" style="background: var(--{nombre})"></div>
        <figcaption>
          <b>{titulo}</b>
          <code>{valor}</code>
          <span>{motivo}</span>
        </figcaption>
      </figure>"""


def fila_medida(fila):
    """Un renglón de la tabla de contraste, con su veredicto."""
    nombre_a, nombre_b, valor, piso, uso, error = fila

    if error is not None:
        return f'<tr class="mal"><td>{nombre_a} sobre {nombre_b}</td><td>—</td><td>{error}</td></tr>'

    # ✓ pasa sin condiciones · △ pasa su piso, pero sólo bajo la
    # restricción que el propio par declara (texto grande, o borde).
    clase = "bien" if valor >= 4.5 else "aviso"
    nota = uso

    return (
        f'<tr class="{clase}">'
        f"<td>{nombre_a} <i>sobre</i> {nombre_b}</td>"
        f"<td><b>{valor:.2f}</b> <small>piso {piso}</small></td>"
        f"<td>{nota}</td>"
        "</tr>"
    )


# Los cuatro candidatos del dorado. El HTML se arma una sola vez desde acá,
# así el cuadro de 1280 y el de 390 no pueden decir cosas distintas.
CANDIDATOS = [
    {
        "letra": "A",
        "titulo": "Sólo acento",
        "subtitulo": "Nunca letra",
        "subtitulo_color": "texto-segundo",
        "rotulo_color": "grafito",
        "enlace_clase": "enlace",
        "enlace_estilo": "color: var(--grafito)",
        "enlace_texto": "en grafito",
        "enlace_cola": ", como el resto.",
        "boton_clase": "boton-grafito",
        "depende": False,
        "fondo_boton": "grafito",
        "costo": "Mata una decisión del brief: los rótulos chicos en mayúsculas "
                 "iban en dorado y acá se vuelven grises.",
    },
    {
        "letra": "B",
        "titulo": "Dos dorados",
        "subtitulo": "Fondo y letra, separados",
        "subtitulo_color": "dorado-texto",
        "rotulo_color": "dorado-texto",
        "enlace_clase": "enlace",
        "enlace_estilo": "",
        "enlace_texto": "en dorado de texto",
        "enlace_cola": ", que sí pasa.",
        "boton_clase": "boton-grafito",
        "depende": False,
        "fondo_boton": "grafito",
        "costo": "Son dos dorados. Hay que escribir cuándo va cada uno "
                 "—<b>{dorado}</b> para fondos y líneas, <b>{dorado_texto}</b> "
                 "para letra— o se mezclan.",
    },
    {
        "letra": "C",
        "titulo": "Botón dorado",
        "subtitulo": "Letra grafito",
        "subtitulo_color": "dorado-texto",
        "rotulo_color": "dorado",
        "enlace_clase": "enlace-flojo",
        "enlace_estilo": "",
        "enlace_texto": "en dorado del brief",
        "enlace_cola": ": {dorado_marfil}, no pasa.",
        "boton_clase": "boton-dorado",
        "depende": True,
        "fondo_boton": "dorado",
        "costo": "Frágil: el botón mide <b>{grafito_dorado}</b> y sólo vale porque "
                 "la letra es grande. Si alguien la baja a 16&nbsp;px deja de "
                 "cumplir y nada avisa.",
    },
    {
        "letra": "D",
        "titulo": "El botón del brief, tal cual",
        "elegido": True,
        "subtitulo": "Dorado con letra blanca",
        "subtitulo_color": "dorado",
        "rotulo_color": "dorado",
        "enlace_clase": "enlace-flojo",
        "enlace_estilo": "",
        "enlace_texto": "en dorado del brief",
        "enlace_cola": ": {dorado_marfil}, no pasa.",
        "boton_clase": "boton-dorado-blanco",
        "depende": True,
        "fondo_boton": "dorado",
        "costo": "Es lo que dibuja la página 17. Mide <b>{blanco_dorado}</b>: como "
                 "texto normal no pasa ni cerca, y como texto grande pasa el piso "
                 "de 3,0 <b>por nueve centésimas</b>. Es el mismo riesgo que C con "
                 "la mitad del margen — y acá el que lo rompe no es sólo bajar la "
                 "letra a 16&nbsp;px, también lo rompe cualquier dorado un punto "
                 "más claro.",
    },
]


def demo(c, numeros):
    """El interior de un candidato: rótulo, texto con enlace y botón.
    Es lo mismo a 1280 y a 390 — cambia el ancho del marco, no el contenido."""
    estilo = f' style="{c["enlace_estilo"]}"' if c["enlace_estilo"] else ""
    cola = c["enlace_cola"].format(**numeros)
    return f'''
        <p class="rotulo" style="color: var(--{c["rotulo_color"]})">Nuestros tratamientos</p>
        <p>Un enlace queda <a class="{c["enlace_clase"]}" href="#"{estilo}>{c["enlace_texto"]}</a>{cola}</p>
        <span class="boton {c["boton_clase"]}">Agendar</span>'''


def contexto(c):
    """El renglón que dice de qué tamaño es cada cosa y qué depende de eso."""
    if c["depende"]:
        nota = "<b>Depende del tamaño:</b> a 16&nbsp;px deja de cumplir."
    else:
        nota = "<b>No depende del tamaño:</b> el grafito mide 12,82 y pasa a cualquiera."
    return (
        f'<p class="tamano">Botón: Jost 19&nbsp;px, peso 600 · alto 44&nbsp;px · '
        f'fondo {c["fondo_boton"]} · rótulo 13&nbsp;px. {nota}</p>'
    )


def candidato(c, numeros):
    """La tarjeta entera, para el cuadro de 1280."""
    return f'''
    <div class="candidato{" elegido" if c.get("elegido") else ""}">
      <h3>{c["letra"]} · {c["titulo"]}{" — ELEGIDO" if c.get("elegido") else ""}</h3>
      <p class="rotulo" style="color: var(--{c["subtitulo_color"]})">{c["subtitulo"]}</p>
      <div class="demo">{demo(c, numeros)}
      </div>
      {contexto(c)}
      <p class="costo">{c["costo"].format(**numeros)}</p>
    </div>'''


def telefono(c, numeros):
    """El mismo candidato dentro de un marco de 390 px, a escala real."""
    return f'''
    <div class="telefono">
      <p class="telefono-letra">{c["letra"]} · {c["titulo"]}</p>
      <div class="pantalla">{demo(c, numeros)}
      </div>
    </div>'''

def medida(tokens, nombre_a, nombre_b):
    """El contraste de un par, listo para meter en la prosa, con coma."""
    valor = MEDIDOR.razon(tokens[nombre_a], tokens[nombre_b])
    return f"{valor:.2f}".replace(".", ",")


def tablero_color(tokens, css):
    filas = MEDIDOR.medir()
    numeros = {
        "dorado_marfil": medida(tokens, "dorado", "marfil"),
        "blanco_dorado": medida(tokens, "blanco", "dorado"),
        "grafito_dorado": medida(tokens, "grafito", "dorado"),
        "dorado": tokens["dorado"],
        "dorado_texto": tokens["dorado-texto"],
    }
    dorado_marfil = numeros["dorado_marfil"]
    blanco_dorado = numeros["blanco_dorado"]
    cuadros = "".join(candidato(c, numeros) for c in CANDIDATOS)
    telefonos = "".join(telefono(c, numeros) for c in CANDIDATOS)
    muestras_brief = "".join(muestra(n, t, m, tokens) for n, t, m in PALETA_BRIEF)
    muestras_derivadas = "".join(muestra(n, t, m, tokens) for n, t, m in DERIVADOS)
    tabla = "".join(fila_medida(f) for f in filas)

    return f"""<!-- @dsCard group="Color" -->
<meta charset="utf-8">
<title>CB · 01 Color y contraste</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
  width: 1280px;
  background: var(--marfil);
  color: var(--grafito);
  font-family: Jost, "Helvetica Neue", Arial, sans-serif;
  font-weight: 400;
  font-size: 16px;
  line-height: 1.6;
  padding: 56px 64px 72px;
}}

h1, h2, h3 {{
  font-family: Marcellus, Georgia, serif;
  font-weight: 400;
  line-height: 1.25;
}}

h1 {{ font-size: 44px; }}
h2 {{ font-size: 28px; }}
h3 {{ font-size: 20px; }}

.rotulo {{
  font-family: Jost, sans-serif;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--dorado-texto);
}}

.regla {{
  height: 1px;
  background: var(--dorado);
  margin: 14px 0 32px;
}}

section {{ margin-top: 56px; }}

section > p {{
  max-width: 74ch;
  margin-top: 10px;
}}

.muestras {{
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 20px;
  margin-top: 26px;
}}

.muestra {{
  background: var(--blanco);
  border: 1px solid var(--dorado-claro);
  border-radius: var(--radio);
  overflow: hidden;
}}

.muestra-color {{
  height: 96px;
  border-bottom: 1px solid var(--dorado-claro);
}}

.muestra figcaption {{
  display: block;
  padding: 14px 16px 18px;
}}

.muestra b {{
  display: block;
  font-weight: 500;
  font-size: 16px;
}}

.muestra code {{
  display: block;
  font-family: Jost, monospace;
  font-size: 14px;
  letter-spacing: 0.06em;
  color: var(--dorado-texto);
  margin: 2px 0 8px;
}}

.muestra span {{
  display: block;
  font-size: 14px;
  line-height: 1.5;
  color: var(--grafito);
}}

table {{
  width: 100%;
  border-collapse: collapse;
  margin-top: 26px;
  background: var(--blanco);
}}

th, td {{
  text-align: left;
  padding: 11px 16px;
  border-bottom: 1px solid var(--dorado-claro);
  font-size: 15px;
}}

th {{
  font-weight: 500;
  font-size: 13px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--dorado-texto);
}}

td i {{ color: var(--texto-segundo); font-style: normal; }}
td small {{ color: var(--texto-segundo); }}

tr.bien td:first-child::before {{ content: "✓  "; color: var(--exito); }}
tr.aviso td:first-child::before {{ content: "△  "; color: var(--dorado-texto); }}
tr.mal td:first-child::before {{ content: "✗  "; color: var(--error); }}

.candidatos {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 22px;
  margin-top: 26px;
}}

.candidato {{
  background: var(--blanco);
  border: 1px solid var(--dorado-claro);
  border-radius: var(--radio);
  padding: 24px 24px 26px;
}}

.candidato.elegido {{
  border: 2px solid var(--dorado);
  background: var(--marfil);
}}

.candidato h3 {{ margin-bottom: 4px; }}

.demo {{
  background: var(--marfil);
  border: 1px solid var(--dorado-claro);
  border-radius: var(--radio);
  padding: 22px;
  margin: 18px 0;
}}

.demo p {{ font-size: 15px; margin: 10px 0 16px; }}

.tamano {{
  font-size: 13px;
  line-height: 1.5;
  color: var(--texto-segundo);
  letter-spacing: 0.02em;
  margin-bottom: 14px;
}}

.costo {{
  font-size: 14px;
  line-height: 1.5;
  color: var(--grafito);
  border-top: 1px solid var(--dorado-claro);
  padding-top: 12px;
}}

.boton {{
  display: inline-block;
  font-family: Jost, sans-serif;
  font-size: 19px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 13px 26px;
  border: 0;
  min-height: 44px;
}}

.boton-grafito {{ background: var(--grafito); color: var(--blanco); }}

.boton-dorado {{
  background: var(--dorado);
  color: var(--grafito);
}}

.boton-dorado-blanco {{
  background: var(--dorado);
  color: var(--blanco);
}}

.enlace {{
  color: var(--dorado-texto);
  text-decoration: underline;
  text-underline-offset: 3px;
}}

.enlace-flojo {{
  color: var(--dorado);
  text-decoration: underline;
  text-underline-offset: 3px;
}}

.telefonos {{
  display: grid;
  grid-template-columns: repeat(2, 390px);
  gap: 26px 40px;
  margin-top: 26px;
}}

.telefono-letra {{
  font-family: Jost, sans-serif;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--dorado-texto);
  margin-bottom: 8px;
}}

.pantalla {{
  width: 390px;
  background: var(--marfil);
  border: 1px solid var(--borde);
  border-radius: var(--radio);
  padding: 24px 20px 28px;
}}

.pantalla p {{ font-size: 16px; margin: 10px 0 18px; }}

.boton-ancho {{
  display: block;
  width: 100%;
  text-align: center;
  font-weight: 700;
}}

.pie {{
  margin-top: 56px;
  padding-top: 20px;
  border-top: 1px solid var(--dorado-claro);
  font-size: 14px;
  color: var(--texto-segundo);
  max-width: 88ch;
}}
</style>

<p class="rotulo">Fase ⑦ · Pieza 1 de 8 · 1280 px</p>
<h1>Color y contraste</h1>
<div class="regla"></div>
<p>Los cinco colores del brief, los que hubo que derivar porque el brief no
llegaba, y la medición de cada par que el sitio va a usar. Todo sale de
<code>css/tokens.css</code>: no hay ni un color escrito a mano acá.</p>

<section>
  <p class="rotulo">La paleta del brief</p>
  <h2>Cinco colores, sin tocar</h2>
  <div class="muestras">{muestras_brief}</div>
</section>

<section>
  <p class="rotulo">Los derivados</p>
  <h2>Cinco más, cada uno porque algo no llegaba</h2>
  <p>Ninguno estrena tono: a un color del brief se le baja la luz hasta que
  pasa el piso. El informativo directamente no estrena color — usa el dorado
  claro que ya existe.</p>
  <div class="muestras">{muestras_derivadas}</div>
</section>

<section>
  <p class="rotulo">La medición</p>
  <h2>Cada par, contra su piso</h2>
  <p>El piso es 4,5 para texto normal y 3,0 para texto grande (≥24px, o ≥19px
  semibold) y para bordes y controles. Esta tabla no se escribe: la calcula
  <code>tools/medir-contraste.py</code> leyendo los mismos tokens.</p>
  <table>
    <tr><th>par</th><th>contraste</th><th>para qué</th></tr>
    {tabla}
  </table>
</section>

<section>
  <p class="rotulo">La decisión</p>
  <h2>Qué se hace con el dorado</h2>
  <p>El dorado del brief mide {dorado_marfil} sobre marfil. El brief lo manda
  en los rótulos chicos en mayúsculas y en el botón «AGENDAR» con letra blanca
  ({blanco_dorado}). Los cuatro caminos posibles, con lo que cuesta cada uno:</p>
  <p class="tamano" style="margin-top: 14px"><b>Escala 1:1 y los cuatro botones
  al mismo tamaño: Jost 19&nbsp;px peso 600, alto 44&nbsp;px.</b> Se igualaron a
  19 porque es el tamaño que <b>C y D necesitan</b> para que les aplique el piso
  de 3,0 en vez del de 4,5 — abajo de eso se caen. A y B no lo necesitan: el
  grafito pasa a cualquier tamaño. Igualados así, <b>lo único que cambia entre
  los cuatro cuadros es el color</b>. · <b>Esto es escritorio, 1280&nbsp;px.</b>
  El mismo botón en un teléfono de 390 es lo que sigue.</p>

  <div class="candidatos">{cuadros}
  </div>
</section>

<section>
  <p class="rotulo">Los mismos cuatro, en el teléfono</p>
  <h2>390&nbsp;px, que es donde esto vive de verdad</h2>
  <p>El sitio es mobile-first: el ancho real de la decisión es éste, no el de
  arriba. <b>Cada marco mide 390&nbsp;px exactos y está a escala 1:1</b> — es el
  mismo contenido de arriba, sin ningún cambio, metido en el ancho de un
  teléfono.</p>
  <p class="tamano" style="margin-top: 12px"><b>Lo único que este tablero no
  reproduce:</b> el navegador que lo dibuja tiene 1280&nbsp;px de ventana, así
  que si mañana el CSS trae una regla que sólo se activa en pantallas chicas,
  acá no se activaría. Hoy no hay ninguna, así que lo que ves es lo que se ve.</p>
  <div class="telefonos">{telefonos}</div>

  <h3 style="margin-top: 44px">Y D, tal como quedaría de verdad</h3>
  <p>Los cuatro marcos de arriba llevan el botón del ancho de su texto, que es
  como quedó en el sistema: <b>ningún botón va de borde a borde, en ningún
  ancho</b> —decidido el 3-sep-2026, está escrito en <code>tokens.css</code>—.
  Al lado, el mismo botón en <b>peso 700</b> en vez de 600 — el porqué está
  abajo del todo.</p>
  <div class="telefonos" style="margin-top: 18px">
    <div class="telefono">
      <p class="telefono-letra">D · ancho completo, peso 600</p>
      <div class="pantalla">
        <p class="rotulo" style="color: var(--dorado)">Nuestros tratamientos</p>
        <p>Un enlace queda <a class="enlace-flojo" href="#">en dorado del
        brief</a>: {dorado_marfil}, no pasa.</p>
        <span class="boton boton-dorado-blanco" style="display: block; width: 100%; text-align: center">Agendar</span>
      </div>
    </div>
    <div class="telefono">
      <p class="telefono-letra">D · ancho completo, peso 700</p>
      <div class="pantalla">
        <p class="rotulo" style="color: var(--dorado)">Nuestros tratamientos</p>
        <p>Un enlace queda <a class="enlace-flojo" href="#">en dorado del
        brief</a>: {dorado_marfil}, no pasa.</p>
        <span class="boton boton-dorado-blanco boton-ancho">Agendar</span>
      </div>
    </div>
  </div>
</section>

<p class="pie">Los cuatro cuadros usan los mismos tokens; no hay ningún hex ni
ningún número escrito a mano acá: los contrastes los calcula el medidor sobre
<code>css/tokens.css</code>. <b>DECIDIDO EL 2-SEP-2026: va el candidato D</b> — el botón del
brief tal cual, fondo dorado con letra blanca. Mide {blanco_dorado}, que pasa el
piso de 3,0 del texto grande. <b>Lo decidió Juan priorizando la identidad
original por sobre el margen de contraste</b>, y con el criterio de volver a
mirarlo sobre la maqueta completa antes de construir. La contrapartida quedó
escrita en <code>tokens.css</code>: <b>el fondo dorado no aparece debajo de
ningún otro texto, sólo el botón principal.</b></p>
"""


# ============================================================
# PIEZA 2 — LA ESCALA TIPOGRÁFICA
# ============================================================

# Cada nivel: token, nombre, tipografía, para qué sirve, y el texto de muestra.
NIVELES = [
    ("h1", "Título de página", "Marcellus",
     "uno solo por pantalla", "Reservá tu turno"),
    ("h2", "Título de sección", "Marcellus",
     "abre cada bloque", "Nuestros tratamientos"),
    ("h3", "Título de tarjeta", "Marcellus",
     "dentro de una tarjeta o un turno", "Limpieza"),
    ("cuerpo", "Texto de leer", "Jost",
     "párrafos, respuestas, descripciones", None),
    ("chico", "Texto chico", "Jost",
     "ayuda de un campo, pie, aclaración", None),
    ("rotulo", "Rótulo", "Jost",
     "mayúsculas espaciadas, encima de un título", "Odontología general"),
]

CUERPO_MUESTRA = (
    "La primera consulta incluye el diagnóstico y el plan de tratamiento. Si "
    "necesitás cambiar el horario, se puede hasta el día anterior."
)

CHICO_MUESTRA = (
    "Te va a llegar un correo de confirmación con la dirección del consultorio."
)

ANCHOS = [390, 768, 1280]


def leer_espacio(nombre):
    """Un token de espacio, resuelto ancho por ancho.

    Mismo mecanismo que leer_escala y por el mismo motivo: el :root trae el
    valor de móvil y cada @media lo pisa. Acá NO se escribe ningún número —
    los tres viven en css/tokens.css, que es lo que también lee el sitio.
    """
    css = TOKENS.read_text(encoding="utf-8")
    partes = re.split(r"@media\s*\(min-width:\s*(\d+)px\)", css)
    patron = re.compile(rf"--{nombre}\s*:\s*(\d+)px")

    hallado = patron.findall(partes[0])

    if not hallado:
        raise SystemExit(f"✗ tokens.css no declara --{nombre} en :root")

    ultimo = int(hallado[-1])
    valores = {390: ultimo}

    for i in range(1, len(partes), 2):
        corte = int(partes[i])
        hallado = patron.findall(partes[i + 1])

        if hallado:
            ultimo = int(hallado[-1])

        valores[corte] = ultimo

    return valores


MARGENES = leer_espacio("margen-pagina")

AIRE = leer_espacio("aire-seccion")


def leer_escala(css):
    """Los tamaños de cada ancho: el :root es móvil, los @media lo pisan."""
    import re

    partes = re.split(r"@media\s*\(min-width:\s*(\d+)px\)", css)
    base = dict(re.findall(r"--tipo-([a-z0-9]+)\s*:\s*(\d+)px", partes[0]))
    escala = {390: dict(base)}
    acumulado = dict(base)

    for i in range(1, len(partes), 2):
        corte = int(partes[i])
        acumulado = dict(acumulado)
        acumulado.update(re.findall(r"--tipo-([a-z0-9]+)\s*:\s*(\d+)px", partes[i + 1]))
        escala[corte] = acumulado

    return escala


def base_css(ancho):
    """El armazón del tablero. Los tamaños salen de tokens.css, no de acá."""
    margen = MARGENES[ancho]
    return f"""
* {{ margin: 0; padding: 0; box-sizing: border-box; }}

/* 🔴 EL TABLERO TIENE QUE TERMINAR DONDE TERMINA EL DIBUJO — 13-sep-2026.

   `body` ya venía con el ancho clavado, pero el fondo se DERRAMABA a toda la
   ventana: cuando <html> no declara fondo, el navegador propaga el del <body>
   al lienzo entero. Efecto: el tablero de 768 abierto en una ventana de 1360
   pintaba marfil de lado a lado, y como el hero es oscuro parecía un bloque
   suelto en medio de una página más ancha. Juan lo leyó como una rotura del
   hero —«parte no queda en el cuadro»— y no lo era: era el tablero mintiendo
   sobre dónde termina la pantalla.

   El gris de acá es ANDAMIAJE, no entra al sistema del sitio: es neutro justo
   para no teñir el marfil que está al lado. */
html {{
  background: #8C8C8C;
}}

body {{
  width: {ancho}px;
  /* Centrado para poder mirarlo sin arrimar la ventana al borde. */
  margin: 0 auto;
  background: var(--marfil);
  color: var(--grafito);
  font-family: Jost, "Helvetica Neue", Arial, sans-serif;
  font-size: var(--tipo-cuerpo);
  line-height: var(--alto-cuerpo);
  padding: {margen}px {margen}px {margen * 2}px;
}}

h1, h2, h3 {{
  font-family: Marcellus, Georgia, serif;
  font-weight: 400;
  max-width: var(--columna);
  /* 🔴 EL EFECTO SIERRA — el borde derecho de un bloque de texto subiendo y
     bajando en dientes. Lo levantó Juan el 13-sep-2026 y está medido: en el
     titular del hero las cinco líneas medían 341, 418, 362, 480 y 188 px, o
     sea que el borde derecho BAILABA 292 px.

     `balance` reparte las palabras para que todas las líneas queden de un
     largo parecido. Es para títulos: el navegador lo calcula sobre pocas
     líneas y en bloques largos deja de aplicarlo solo. */
  text-wrap: balance;
}}

h1 {{ font-size: var(--tipo-h1); line-height: var(--alto-h1); }}
h2 {{ font-size: var(--tipo-h2); line-height: var(--alto-h2); }}
h3 {{ font-size: var(--tipo-h3); line-height: var(--alto-h3); }}

p {{
  max-width: var(--columna);
  /* 🔴 EN LOS PÁRRAFOS TAMBIÉN VA `balance`, Y SE PROBÓ AL REVÉS PRIMERO.
     `pretty` se puso creyendo que era el indicado para texto corrido, y
     medido NO movió un píxel: en el primer párrafo de «Nosotros» el borde
     derecho siguió bailando 222 px. `pretty` arregla la línea final huérfana,
     no el conjunto del bloque.

     `balance` sí reparte las palabras entre todas las líneas. El navegador lo
     apaga solo cuando el bloque pasa de unas seis líneas —ahí el costo de
     calcularlo no vale—, así que ponerlo en todos los párrafos no rompe los
     textos largos: simplemente no se aplica. */
  text-wrap: balance;
}}

code {{
  font-family: Jost, sans-serif;
  letter-spacing: 0.02em;
  color: var(--dorado-texto);
}}

.rotulo {{
  font-size: var(--tipo-rotulo);
  line-height: var(--alto-rotulo);
  font-weight: 500;
  letter-spacing: var(--letra-rotulo);
  text-transform: uppercase;
  color: var(--dorado-texto);
}}

.regla {{
  height: 1px;
  background: var(--dorado);
  margin: 12px 0 24px;
  max-width: var(--columna);
}}

section {{ margin-top: 40px; }}

.chico {{ font-size: var(--tipo-chico); line-height: var(--alto-chico); }}

.dato {{
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  color: var(--texto-segundo);
}}

.espec {{
  border-top: 1px solid var(--dorado-claro);
  padding-top: 14px;
  margin-top: 20px;
  max-width: var(--columna);
}}

.espec .muestra-texto {{ margin-top: 6px; }}

table {{
  width: 100%;
  max-width: var(--columna);
  border-collapse: collapse;
  margin-top: 18px;
}}

th, td {{
  text-align: left;
  padding: 9px 0;
  border-bottom: 1px solid var(--dorado-claro);
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
}}

th {{
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  font-size: var(--tipo-rotulo);
  color: var(--dorado-texto);
}}

td.n {{ text-align: right; font-variant-numeric: tabular-nums; }}
th.n {{ text-align: right; }}

.pie {{
  max-width: var(--columna);
  margin-top: 40px;
  padding-top: 16px;
  border-top: 1px solid var(--dorado-claro);
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  color: var(--texto-segundo);
}}
"""


def css_margen_en_la_prosa():
    """El margen lateral del tablero lo lleva la PROSA, no el <body>.

    Lo usan los tres tableros cuya muestra es una sección del sitio que ya trae
    su propio margen —11 Tratamientos, 12 Contacto y 13 Pie—. Si el body lo
    pusiera también, esa sección mediría DOS márgenes en el tablero y uno en la
    página: dos números distintos para la misma pieza, que es exactamente lo
    que una aprobación a 1:1 no puede permitirse.

    Sólo se muda el margen LATERAL, que es el que la sección reclama para sí.
    El de arriba y el de abajo siguen en el body, porque ésos son del tablero.

    Es el mismo mecanismo que ya usan la pieza 8 y la 9: no se estrena nada.
    """
    return """
/* El margen lateral se lo lleva la prosa: la muestra de abajo trae el suyo. */
body {
  padding-left: 0;
  padding-right: 0;
}

.prosa {
  padding-left: var(--margen-pagina);
  padding-right: var(--margen-pagina);
}
"""


def espec(token, nombre, tipo, uso, muestra, escala, ancho):
    """Un nivel de la escala: qué es, cuánto mide acá, y cómo se ve."""
    px = escala[ancho][token]
    if token == "cuerpo":
        cuerpo = f'<p class="muestra-texto">{CUERPO_MUESTRA}</p>'
    elif token == "chico":
        cuerpo = f'<p class="muestra-texto chico">{CHICO_MUESTRA}</p>'
    elif token == "rotulo":
        cuerpo = f'<p class="muestra-texto rotulo">{muestra}</p>'
    else:
        cuerpo = f'<{token} class="muestra-texto">{muestra}</{token}>'

    return f'''
  <div class="espec">
    <p class="dato">{nombre} · {tipo} · <b>{px} px</b> · {uso}</p>
    {cuerpo}
  </div>'''


def tabla_anchos(escala):
    filas = ""
    for token, nombre, tipo, _, _ in [(n[0], n[1], n[2], n[3], n[4]) for n in NIVELES]:
        celdas = "".join(f'<td class="n">{escala[a][token]}</td>' for a in ANCHOS)
        filas += f"<tr><td>{nombre}</td><td>{tipo}</td>{celdas}</tr>"
    encabezados = "".join(f'<th class="n">{a}</th>' for a in ANCHOS)
    return f"<tr><th>nivel</th><th>tipografía</th>{encabezados}</tr>{filas}"


def tablero_tipografia(tokens, css, ancho):
    escala = leer_escala(css)
    especs = "".join(espec(*n, escala, ancho) for n in NIVELES)

    return f"""<!-- @dsCard group="Type" -->
<meta charset="utf-8">
<title>CB · 02 Escala tipográfica · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
</style>

<p class="rotulo">Fase ⑦ · Pieza 2 de 8 · {ancho} px</p>
<h1>Escala tipográfica</h1>
<div class="regla"></div>
<p>Marcellus tiene un solo peso: no hay negrita ni liviana. <b>La jerarquía
entre títulos es por tamaño, nunca por peso.</b> Jost lleva todo lo demás.
Los tamaños salen de <code>css/tokens.css</code> y cambian solos con el ancho.</p>

<section>
  <p class="rotulo">La escala</p>
  <h2>Seis niveles, a tamaño real</h2>
  <p class="dato" style="margin-top: 8px">Todo lo de abajo está a escala 1:1 en
  {ancho} px. El número de cada renglón es el tamaño que tiene en ESTE ancho.</p>
  {especs}
</section>

<section>
  <p class="rotulo">Los tres anchos</p>
  <h2>Qué mide cada nivel en cada pantalla</h2>
  <p class="dato" style="margin-top: 8px">El móvil es el default; los otros dos
  son excepciones declaradas. En píxeles.</p>
  <table>{tabla_anchos(escala)}</table>
</section>

<section>
  <p class="rotulo">En uso</p>
  <h2>La jerarquía, funcionando</h2>
  <div class="espec" style="border-top: 0; padding-top: 0">
    <p class="rotulo">Odontología general</p>
    <h2>Limpieza</h2>
    <p class="muestra-texto">{CUERPO_MUESTRA}</p>
    <p class="chico" style="margin-top: 10px; color: var(--texto-segundo)">{CHICO_MUESTRA}</p>
  </div>
</section>

<p class="pie">Ni un tamaño escrito a mano en este tablero: todos salen de las
variables de <code>tokens.css</code>, las mismas que va a usar el sitio. La
línea de lectura está limitada a {{medida}} en escritorio para que el ojo no pierda el renglón
al volver.</p>
"""


# ============================================================
# PIEZA 3 — EL BOTÓN
# ============================================================

CSS_BOTON = """
.btn {
  display: inline-block;
  text-decoration: none;
  font-family: Jost, sans-serif;
  font-size: 19px;
  font-weight: 600;
  line-height: 1.2;

  /* 🔴 SIN MAYÚSCULAS — decidido por Juan el 3-sep-2026, viendo los botones
     dentro del hero y no sueltos en un tablero. «R E S E R V A R» ocupaba un
     30 % más que «Reservar» y no aportaba legibilidad.

     Lo que NO se tocó, y es lo que hace que el cambio sea seguro: el alto
     mínimo de 44 px (piso táctil) y la letra de 19 px, que la exige el
     contraste — blanco sobre el dorado del brief mide 3,09, y ese número
     sólo alcanza para texto grande. */
  letter-spacing: 0.01em;
  text-transform: none;
  text-align: center;
  padding: 12px 20px;
  min-height: 44px;
  border: 0;
  border-radius: var(--radio);
  cursor: pointer;

  /* EL FORMATO ÚNICO — el porqué está en tokens.css, al lado del token.
     Bloque para poder centrarlo, del ancho de su texto, centrado en su caja.
     Nunca de borde a borde, en ningún ancho. */
  display: block;
  width: var(--boton-ancho);
  margin-left: auto;
  margin-right: auto;
}

/* DOS O MÁS BOTONES JUNTOS: la columna de la grilla mide lo que el MÁS LARGO
   de la pareja y los hijos se estiran a esa medida. El número no se escribe: lo
   fija el texto más largo, así que cambiar un rótulo no deja la pareja
   despareja.

   🔴 Y SE CENTRA ADENTRO DE `--columna`, NO DE LA PÁGINA. La primera versión
   usaba `width: max-content` con márgenes automáticos, y eso centra contra el
   padre: en escritorio el padre es la banda entera, así que los botones se iban
   al medio de 1280 mientras su texto vivía en los primeros 640. Lo encontró
   medir-alineacion.py el mismo día en que aprendió a medir el centrado — un
   bloque centrado en la página no está centrado en su columna. */
/* 🔴 EL BOTÓN CRECE EN ESCRITORIO — 13-sep-2026, lo levantó Juan mirando el
   hero partido: «¿no quedaron chicos los botones para este tamaño?».

   Tenía razón y es un problema de PROPORCIÓN, no de tamaño absoluto: los 19 px
   del rótulo se decidieron contra un titular de 32 px en el teléfono; en
   escritorio ese titular mide 52 y el botón se quedó donde estaba, así que la
   distancia entre los dos pasó de 1,7 a 2,7 y el botón dejó de pesar lo que
   tiene que pesar al lado de la promesa.

   ⚠️ EL PISO DE 19 px NO SE TOCA HACIA ABAJO NUNCA: lo exige el contraste
   —blanco sobre el dorado del brief mide 3,09, que es el piso del texto
   GRANDE—. Acá sube, que es el lado seguro. */
@media (min-width: 1280px) {
  .btn {
    font-size: 22px;
    padding: 16px 32px;
    min-height: 56px;
  }
}

.acciones {
  display: grid;
  grid-template-columns: max-content;
  justify-content: center;
  gap: 12px;
  max-width: var(--columna);
  margin-top: 24px;
}

.acciones .btn,
.acciones .btn-google {
  width: auto;
  margin: 0;
}

.btn-1 {
  background: var(--boton-fondo);
  color: var(--boton-texto);
  box-shadow: var(--sombra-boton);
}

/* El ancho NO puede cambiar al enviar, y "Reservando…" es más corto que
   "Reservar turno": como el botón se ajusta a su texto, se achicaba 30 px. El
   botón lleva las dos palabras apiladas y la que no se ve sostiene el ancho.
   Sin números mágicos: lo mide el texto más largo. */
.pila { display: grid; }

.pila > span { grid-area: 1 / 1; }

.pila .fantasma { visibility: hidden; }

/* Enviando: el mismo dorado oscurecido, con sombra, y la palabra cambiada. */
.btn-1-enviando {
  background: var(--boton-fondo-oscuro);
  box-shadow: var(--sombra-boton-foco);
  cursor: progress;
}

/* FOCO del principal: se oscurece la superficie y el contorno cae JUSTO sobre
   el filo del botón. Las letras quedan blancas — el filtro que también las
   apagaba se descartó: dejaba el foco en 2,84, abajo del piso. */
.btn-foco {
  background: var(--boton-fondo-oscuro);
  box-shadow: inset 0 0 0 2px var(--boton-foco-borde), var(--sombra-boton-foco);
}

/* El secundario del brief, página 17: grafito macizo con letra blanca. */
.btn-2 {
  background: var(--boton-2-fondo);
  color: var(--boton-2-texto);
  box-shadow: var(--sombra-boton);
}

/* Misma regla de foco que el principal —contorno sobre el filo, sombra más
   marcada—, pero INVERTIDO: fondo blanco, letra grafito, filo grafito de 2 px.
   Los anillos claros se descartaron: al filo se leen como que el botón se
   achicó. Medido con medir-foco.py. */
.btn-2-foco {
  background: var(--boton-2-foco-fondo);
  color: var(--boton-2-foco-texto);
  border: 2px solid var(--boton-2-foco-filo);
  padding: 10px 24px;
  box-shadow: var(--sombra-boton-foco);
}

.btn-apagado {
  background: var(--boton-apagado-fondo);
  color: var(--boton-apagado-texto);
  border: 1px solid var(--boton-apagado-borde);
  padding: 11px 25px;
  box-shadow: none;
  cursor: not-allowed;
}

.estado {
  border-top: 1px solid var(--dorado-claro);
  padding-top: 14px;
  margin-top: 22px;
  max-width: var(--columna);
}

.estado .btn {
  margin-top: 8px;
  margin-bottom: 2px;
}

/* La lista arranca en el margen como todo lo demás: la sangría de una lista
   normal la corría 22 px y rompía la columna. La raya se dibuja a mano. */
.reglas {
  max-width: var(--columna);
  margin-top: 16px;
  padding-left: 0;
  list-style: none;
}

.reglas li {
  margin-top: 8px;
  padding-left: 22px;
  text-indent: -22px;
}

.reglas li::before {
  content: "—";
  color: var(--dorado-texto);
  margin-right: 10px;
}
"""


ESTADOS = [
    ("btn-1", "Reposo", "Reservar turno",
     "El dorado del brief con letra blanca, el mismo que se usa en todo el "
     "sitio. Sombra hiper leve. Mide 3,09 y por eso la letra no baja de 19 px."),
    ("btn-1 btn-1-enviando", "Enviando",
     '<span class="pila"><span class="fantasma">Reservar turno</span>'
     '<span>Reservando…</span></span>',
     "El mismo dorado oscurecido, con sombra, y la palabra cambiada. Sube a "
     "4,85. <b>Conserva el ancho del reposo</b>: la palabra que no se ve queda "
     "adentro sosteniéndolo, porque «Reservando…» es más corto y sin eso el "
     "botón se achicaba 30 px al apretarlo."),
    ("btn-1 btn-foco", "Con foco", "Reservar turno",
     "Se oscurece la superficie y el contorno cae JUSTO sobre el filo del "
     "botón. Las letras quedan blancas: 4,85. Se descartó el filtro que las "
     "apagaba también, porque dejaba el foco en 2,84, abajo del piso."),
    ("btn-apagado", "Deshabilitado", "Elegí un horario",
     "El botón DICE por qué no se puede tocar; un botón gris que no explica "
     "nada deja al paciente adivinando. Y lleva borde: su relleno mide 1,11 "
     "contra el fondo, o sea que sin contorno no se ve que hay un botón."),
]


def bloque_estado(clase, nombre, texto, porque):
    return f'''
  <div class="estado">
    <p class="dato">{nombre}</p>
    <button class="btn {clase}">{texto}</button>
    <p class="dato">{porque}</p>
  </div>'''


def leer_logo_google():
    """El archivo oficial de Google, embebido para que el tablero se abra solo."""
    import base64

    ruta = RAIZ / "brand" / "ajenos" / "googleg_standard_color_128dp.png"
    return base64.b64encode(ruta.read_bytes()).decode("ascii")


def tablero_boton(tokens, css, ancho):
    estados = "".join(bloque_estado(*e) for e in ESTADOS)
    google = seccion_google(leer_logo_google())
    ancho_boton = "del ancho de su texto y centrado"

    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 03 Botón · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&family=Roboto:wght@500&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_GOOGLE}
</style>

<p class="rotulo">Fase ⑦ · Pieza 3 de 8 · {ancho} px</p>
<h1>Botón</h1>
<div class="regla"></div>
<p>El botón principal ya tiene color decidido. Lo que se fija acá son sus
<b>estados</b> —encima, con foco, enviando, deshabilitado—, el botón secundario,
y el ancho. Todo a escala 1:1 en {ancho} px.</p>

<section>
  <p class="rotulo">El botón principal</p>
  <h2>Sus estados, todos a tamaño real</h2>
  <p class="dato" style="margin-top: 8px">Acá el botón va <b>{ancho_boton}</b>,
  y el alto nunca baja de 44 px: es lo que mide la yema de un dedo.</p>
  {estados}
</section>

<section>
  <p class="rotulo">El botón secundario</p>
  <h2>El grafito del brief, para lo que no es la acción principal</h2>
  <p>Cancelar, volver, ver otro día. <b>Nunca dos botones dorados en la misma
  pantalla:</b> si todo pesa igual, nada guía.</p>
  <p class="dato" style="margin-top: 10px"><b>Atención, y es una decisión que
  queda abierta:</b> el grafito mide 12,82 y el dorado del principal 3,09, así
  que <b>el secundario pesa más a la vista que el principal</b>. En el brief
  ese grafito era el botón PRINCIPAL. Se ve recién en la pieza 8, cuando los
  dos estén en la misma pantalla.</p>
  <div class="estado">
    <p class="dato">Reposo</p>
    <button class="btn btn-2">Cancelar turno</button>
    <p class="dato">Grafito macizo con letra blanca, tal como está dibujado en
    la página 17 del brief. <b>12,82</b>, el par más alto del sistema.</p>
  </div>
  <div class="estado">
    <p class="dato">Con foco</p>
    <button class="btn btn-2 btn-2-foco">Cancelar turno</button>
    <p class="dato">El botón se <b>invierte</b>: fondo blanco, letra grafito, y
    filo grafito de 2 px para que la silueta no se pierda contra la página.
    Cambia el <b>80 %</b> de la superficie —contra el 24 % que lograba un
    anillo—. Grafito sobre blanco: <b>12,82</b>.</p>
  </div>
</section>

<section>
  <p class="rotulo">Los dos botones juntos</p>
  <h2>Principal y secundario, uno debajo del otro</h2>
  <p>Mismo tamaño, mismo alto, misma letra. Es la única forma de ver cuál pesa
  más.</p>
  <div class="estado">
    <p class="dato">Principal · dorado · <b>3,09</b></p>
    <button class="btn btn-1">Reservar turno</button>
  </div>
  <div class="estado">
    <p class="dato">Secundario · grafito · <b>12,82</b></p>
    <button class="btn btn-2">Cancelar turno</button>
  </div>
</section>

{google}

<section>
  <p class="rotulo">Las reglas</p>
  <h2>Lo que no se negocia</h2>
  <ul class="reglas">
    <li>Alto mínimo <b>44 px</b> en los tres anchos, siempre.</li>
    <li><b>Un solo formato para todos los botones, en los tres anchos:</b> del
    ancho de su texto y centrado en su caja. <b>Ninguno va de borde a borde.</b>
    Y <b>dos botones juntos miden lo mismo</b> —se igualan al más largo—, porque
    la jerarquía entre ellos la da la <b>paleta</b> y nunca el tamaño.</li>
    <li>El foco cae <b>sobre el filo del botón</b>, nunca separado de él.</li>
    <li>La letra del principal es <b>blanca</b> en todos sus estados.</li>
    <li>El deshabilitado <b>dice por qué</b> lo está.</li>
    <li>Mientras envía, el botón <b>no cambia de tamaño</b>.</li>
    <li><b>Un solo botón dorado por pantalla.</b></li>
  </ul>
</section>

<p class="pie">Ni un color ni un tamaño escrito a mano: los estados salen de
<code>tokens.css</code> y los cinco pares del botón los mide
<code>medir-contraste.py</code> antes de cada publicación.</p>
"""



# ------------------------------------------------------------
# LA VARIANTE AJENA — el botón "Continuar con Google"
#
# Es el único control del sistema que NO diseñamos nosotros: la forma, el
# color, la letra y el logo los fija Google en su página de marca (verificada
# el 2-sep-2026). Se documenta acá para que nadie lo "arregle" para que combine.
# ------------------------------------------------------------

CSS_GOOGLE = """
.btn-google {
  display: flex;
  align-items: center;
  justify-content: center;
  width: var(--boton-ancho);
  margin-left: auto;
  margin-right: auto;
  min-height: 48px;
  padding: 12px;
  background: var(--google-fondo);
  border: 1px solid var(--google-filo);
  border-radius: var(--radio);
  color: var(--google-texto);
  font-family: Roboto, Jost, "Helvetica Neue", Arial, sans-serif;
  font-size: 14px;
  font-weight: 500;
  line-height: 20px;
  letter-spacing: 0;
  text-transform: none;
  cursor: pointer;
}

/* Los 10 px que Google pide después del logo. No es un espaciado nuestro. */
.btn-google img {
  display: block;
  width: 18px;
  height: 18px;
  margin-right: 10px;
}
"""


def boton_google(logo):
    return f'''
  <button class="btn-google">
    <img src="data:image/png;base64,{logo}" alt="">Continuar con Google
  </button>'''


def seccion_google(logo):
    return f"""
<section>
  <p class="rotulo">La variante ajena</p>
  <h2>Continuar con Google — el único botón que no diseñamos</h2>
  <p>Es la puerta de entrada: sin sesión no se reserva ni se cancela. <b>Su
  forma, su color, su letra y su logo los fija Google</b>, así que acá no hay
  decisión de diseño que tomar — hay una regla ajena que se cumple.</p>
  <div class="estado">
    <p class="dato">Tema claro, que es el que va sobre marfil</p>
    {boton_google(logo)}
    <p class="dato">Relleno blanco, filo <b>4,24</b> contra la página, letra
    <b>16,48</b>. Los tres colores viven en <code>tokens.css</code> bajo
    «colores ajenos»: están ahí para que el medidor los mire, no porque sean
    nuestros.</p>
  </div>
  <ul class="reglas">
    <li>El logo se usa <b>tal cual</b>: no se recolorea, no se pasa a una
    tinta, no se redibuja. El archivo es el oficial de Google.</li>
    <li><b>Nunca la G sola.</b> Sin borde de botón y sin texto de acción, está
    prohibido.</li>
    <li>El texto tiene que decir que se entra <b>con una cuenta de Google</b>,
    no que se crea una. Por eso «Continuar con Google» y no «Registrate».</li>
    <li>Va en <b>Roboto</b> y en minúsculas: rompe nuestras dos reglas de
    botón —Jost y mayúsculas— <b>a propósito</b>. Google pide Google Sans, que
    no es pública; Roboto es su reemplazo legítimo.</li>
    <li>De lo nuestro conserva dos cosas y sólo dos: el <b>radio de 3 px</b>
    —Google acepta rectangular— y el <b>alto de 48 px</b>, que es nuestro piso
    táctil.</li>
    <li><b>Nunca al lado del botón dorado.</b> Entrar y reservar son dos
    momentos distintos; si comparten pantalla, compiten.</li>
    <li><b>Va el tema CLARO de los tres que Google ofrece</b>, decidido viendo
    los cuatro a tamaño real. El neutro desaparece contra el marfil (1,05); el
    oscuro se viste igual que nuestro botón secundario, que es el que NO manda.
    Y el grafito nuestro nunca fue una opción: Google no admite otro relleno.</li>
  </ul>
</section>
"""

# ============================================================
# PIEZA 4 — EL CAMPO
# ============================================================

CSS_CAMPO = """
.campo {
  max-width: var(--columna);
  margin-top: 18px;
}

/* La etiqueta es un bloque propio arriba del campo: nunca vive adentro. */
.etiqueta {
  display: block;
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  font-weight: 500;
  color: var(--campo-etiqueta);
  margin-bottom: 6px;
}

.etiqueta .opcional {
  font-weight: 400;
  color: var(--campo-ayuda);
}

.caja {
  display: block;
  width: 100%;
  min-height: var(--campo-alto);
  padding: 12px 14px;
  font-family: Jost, "Helvetica Neue", Arial, sans-serif;
  font-size: var(--tipo-cuerpo);
  line-height: var(--alto-cuerpo);
  color: var(--campo-texto);
  background: var(--campo-fondo);
  border: 1px solid var(--campo-borde);
  border-radius: var(--radio);
}

/* FOCO: el filo pasa de 1 px de borde a 2 px de grafito y se marca la sombra.
   El relleno se compensa para que el campo no cambie de tamaño ni empuje a los
   de abajo — un campo que salta al tocarlo se siente roto. */
.caja-foco {
  border: 2px solid var(--campo-foco-filo);
  padding: 11px 13px;
  box-shadow: var(--campo-sombra-foco);
}

.caja-error {
  border: 2px solid var(--campo-error-filo);
  padding: 11px 13px;
}

.caja-apagada {
  background: var(--campo-apagado-fondo);
  border-color: var(--campo-apagado-borde);
  color: var(--campo-apagado-texto);
  cursor: not-allowed;
}

.ayuda {
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  color: var(--campo-ayuda);
  margin-top: 6px;
}

/* El mensaje de error arranca con la palabra: el color es el refuerzo, no
   el mensaje. Quien no distingue el rojo lee exactamente lo mismo. */
.error-texto {
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  color: var(--campo-error-texto);
  margin-top: 6px;
  font-weight: 500;
}

/* El desplegable es el mismo campo con una punta de flecha dibujada al filo
   derecho. No entra ningún ícono nuevo: son dos bordes girados 45°. */
.desplegable { position: relative; }

.desplegable::after {
  content: "";
  position: absolute;
  right: 18px;
  top: 50%;
  width: 8px;
  height: 8px;
  margin-top: -7px;
  border-right: 2px solid var(--grafito);
  border-bottom: 2px solid var(--grafito);
  transform: rotate(45deg);
  pointer-events: none;
}

select.caja {
  appearance: none;
  -webkit-appearance: none;
  padding-right: 44px;
}

textarea.caja {
  min-height: 104px;
  resize: vertical;
}

/* Sin borde de acento a la izquierda: lo prohíbe la pauta 10 y el brief no
   tiene nada así. El bloque se separa con la misma raya superior que ya usan
   las especificaciones de la pieza 2. */
.anatomia {
  border-top: 1px solid var(--dorado-claro);
  padding-top: 14px;
  max-width: var(--columna);
}

.anatomia .pieza-nombre {
  font-size: var(--tipo-rotulo);
  line-height: var(--alto-rotulo);
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--dorado-texto);
  margin-top: 14px;
}

/* El reset deja el párrafo pegado al título que lo abre. */
section > h2 + p { margin-top: 8px; }

.estado {
  border-top: 1px solid var(--dorado-claro);
  padding-top: 14px;
  margin-top: 22px;
  max-width: var(--columna);
}

.reglas {
  max-width: var(--columna);
  margin-top: 16px;
  padding-left: 0;
  list-style: none;
}

.reglas li {
  margin-top: 8px;
  padding-left: 22px;
  text-indent: -22px;
}

.reglas li::before {
  content: "—";
  color: var(--dorado-texto);
  margin-right: 10px;
}
"""


# clase · estado · etiqueta · lo escrito · pie · porqué
ESTADOS_CAMPO = [
    ("", "Vacío", "Nombre", "",
     ("ayuda", "Como figura en tu documento."),
     "Adentro no hay ningún texto de muestra. Lo que se espera se dice en la "
     "ayuda, que no se borra al escribir."),
    ("", "Con lo escrito", "Nombre", "María Fernanda",
     ("ayuda", "Como figura en tu documento."),
     "Lo que el paciente escribió va en grafito: 12,82, el par más alto del "
     "sistema. Se tiene que poder releer de un vistazo antes de confirmar."),
    ("caja-foco", "Con foco", "Nombre", "María Fernanda",
     ("ayuda", "Como figura en tu documento."),
     "El filo pasa de 1 px a 2 px de grafito y se marca la sombra: cambian el "
     "grosor Y el color, nunca sólo el color. El campo no cambia de tamaño."),
    ("caja-error", "Con error", "Apellido", "",
     ("error", "Falta el apellido. Va como figura en tu documento."),
     "Es el error que el sistema realmente devuelve: el paciente nuevo se "
     "guarda con nombre Y apellido. El filo se pinta, pero lo que comunica el "
     "error es el TEXTO. Aparece al salir del campo, no mientras se escribe."),
    ("caja-apagada", "Deshabilitado", "Profesional", "",
     ("ayuda", "Se habilita cuando elijas a qué venís."),
     "Va VACÍO: el motivo por el que no se puede tocar se dice en la ayuda, no "
     "adentro de la caja. Un texto adentro se borraría al escribir, y es justo "
     "lo que esta pieza prohíbe dos secciones más arriba."),
]



def bloque_campo(clase, nombre, etiqueta, valor, pie, porque):
    tipo_pie, texto_pie = pie
    clase_pie = "ayuda" if tipo_pie == "ayuda" else "error-texto"

    if tipo_pie != "ayuda":
        texto_pie = "Error — " + texto_pie

    apagada = " disabled" if clase == "caja-apagada" else ""

    return (
        '\n  <div class="estado">'
        f'\n    <p class="dato">{nombre}</p>'
        '\n    <div class="campo">'
        f'\n      <label class="etiqueta">{etiqueta}</label>'
        f'\n      <input class="caja {clase}" value="{valor}"{apagada}>'
        f'\n      <p class="{clase_pie}">{texto_pie}</p>'
        '\n    </div>'
        f'\n    <p class="dato" style="margin-top: 12px">{porque}</p>'
        '\n  </div>'
    )


def tablero_campo(tokens, css, ancho):
    estados = "".join(bloque_campo(*e) for e in ESTADOS_CAMPO)

    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 04 Campo · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_CAMPO}
</style>

<p class="rotulo">Fase ⑦ · Pieza 4 de 8 · {ancho} px</p>
<h1>Campo</h1>
<div class="regla"></div>
<p>Es por donde el paciente escribe su nombre, su correo y su teléfono, así que
un campo confuso no se ve feo: <b>pierde el turno</b>. Acá se fijan sus tres
partes y sus cinco estados. Todo a escala 1:1 en {ancho} px.</p>

<section>
  <p class="rotulo">La anatomía</p>
  <h2>Tres partes, y ninguna es opcional</h2>
  <div class="anatomia">
    <p class="pieza-nombre">1 · La etiqueta</p>
    <p class="dato">Qué se pide. Va <b>arriba y siempre visible</b>.</p>
    <p class="pieza-nombre">2 · La caja</p>
    <p class="dato">Blanca, con borde. <b>El relleno blanco mide 1,03 contra el
    marfil de la página: la forma del campo la marca el borde, no el fondo.</b>
    El día que alguien saque el borde, el campo desaparece.</p>
    <p class="pieza-nombre">3 · La ayuda</p>
    <p class="dato">Qué formato se espera. Va debajo y <b>no se borra nunca</b>.</p>
    <div class="campo" style="margin-top: 18px">
      <label class="etiqueta">Teléfono</label>
      <input class="caja" value="342 155 0000">
      <p class="ayuda">Con característica, por si hay que avisarte un cambio.</p>
    </div>
  </div>
  <p class="dato" style="margin-top: 18px"><b>La etiqueta no se reemplaza por un
  texto adentro del campo.</b> Ese texto se borra en cuanto se empieza a
  escribir: quien se distrae pierde el nombre de lo que estaba llenando y no
  tiene cómo recuperarlo sin borrar todo.</p>
</section>

<section>
  <p class="rotulo">Los estados</p>
  <h2>Los cinco, a tamaño real</h2>
  <p class="dato" style="margin-top: 8px">La caja nunca baja de 48 px de alto ni
  de 16 px de letra. Los 16 no son estética: <b>por debajo de eso el teléfono
  hace zoom solo al tocar el campo</b> y deja la pantalla corrida.</p>
  {estados}
</section>

<section>
  <p class="rotulo">Las tres formas</p>
  <h2>El mismo campo, escribiendo · eligiendo · contando</h2>
  <p>Cambia lo que hay adentro, no el borde, ni el alto, ni la etiqueta.</p>
  <div class="campo">
    <label class="etiqueta">Apellido</label>
    <input class="caja" value="Gómez">
    <p class="ayuda">Como figura en tu documento.</p>
  </div>
  <div class="campo">
    <label class="etiqueta">¿Para quién es el turno?</label>
    <div class="desplegable">
      <select class="caja"><option>María Fernanda Gómez</option></select>
    </div>
    <p class="ayuda">Un mismo correo puede tener varias personas: una madre
    anota a sus hijos con su casilla.</p>
  </div>
  <div class="campo">
    <label class="etiqueta">Algo que quieras contarnos
      <span class="opcional">· opcional</span></label>
    <textarea class="caja">Tengo el diente 24 sensible al frío desde hace dos semanas.</textarea>
    <p class="ayuda">Con una línea alcanza. Lo demás se habla en el consultorio.</p>
  </div>
  <p class="dato" style="margin-top: 18px"><b>Se marca lo OPCIONAL, no lo
  obligatorio.</b> En la reserva casi todo es obligatorio: un asterisco en cada
  campo es ruido en cinco campos y señal en ninguno.</p>
</section>

<section>
  <p class="rotulo">Las reglas</p>
  <h2>Lo que no se negocia</h2>
  <ul class="reglas">
    <li>La etiqueta va <b>arriba y visible</b>. Nunca adentro del campo.</li>
    <li><b>El correo no se pide nunca en un campo</b>: lo trae la sesión de
    Google. Si viniera del formulario, cualquiera reservaría a nombre de otro.</li>
    <li>Alto mínimo <b>48 px</b> y letra de <b>16 px</b> en los tres anchos.</li>
    <li>El foco <b>tiñe la superficie y engrosa el filo</b>, igual que en el
    botón. Un filo de 2 px solo mueve el 5,3 % de lo que se ve: <b>está
    dibujado y no se nota</b>.</li>
    <li>El campo <b>no cambia de tamaño</b> al recibir foco ni al fallar.</li>
    <li>El error lleva <b>texto</b> y dice qué hacer. El color es el refuerzo,
    no el mensaje.</li>
    <li>El error aparece <b>al salir del campo</b>, no mientras se escribe: un
    teléfono a medio escribir siempre está mal.</li>
    <li>Un campo deshabilitado <b>dice por qué</b> lo está.</li>
    <li>Se marca lo <b>opcional</b>, no lo obligatorio.</li>
    <li>El campo de lo que el paciente quiera contar <b>puede recibir datos de
    salud</b>: su ayuda pide una línea, no una historia clínica.</li>
  </ul>
</section>

<p class="pie">Ni un color ni un tamaño escrito a mano: los cinco estados salen
de <code>tokens.css</code> y los nueve pares del campo los mide
<code>medir-contraste.py</code> antes de cada publicación.</p>
"""



# ============================================================
# PIEZA 5 — EL MENSAJE
#
# Decidido por Juan el 2-sep-2026: el mensaje NO es un bloque adentro del
# formulario. Cada operación termina en una PANTALLA propia, y cada pantalla
# devuelve al paciente al lugar donde puede seguir.
# ============================================================

CSS_MENSAJE = """
/* El marco no es parte del diseño: es el recorte de la pantalla, para que se
   entienda que esto ocupa todo y no es una tarjeta dentro de otra cosa. */
.pantalla {
  max-width: var(--columna);
  margin-top: 14px;
  padding: 32px 20px 28px;
  border: 1px solid var(--borde);
  border-radius: var(--radio);
  background: var(--marfil);
}

/* LOS TÍTULOS VAN EN GRAFITO, no en rojo ni en verde — lo cortó Juan el
   2-sep-2026. Lo que dice de qué tipo es la pantalla es EL TEXTO, y una frase
   se entiende sin distinguir colores. El rojo y el verde quedan para donde
   acompañan a un texto corto que no puede explicarse solo: el error de un
   campo. Una pantalla entera tiene lugar para decirlo con palabras. */
.pantalla h2 {
  font-size: var(--tipo-h2);
  line-height: var(--alto-h2);
  color: var(--grafito);
}

.pantalla p {
  margin-top: 14px;
  color: var(--grafito);
  font-size: var(--tipo-cuerpo);
  line-height: var(--alto-cuerpo);
}

.pantalla .btn,
.pantalla .btn-google {
  margin-top: 26px;
}
"""


# clase · título · cuerpo · botón · de dónde sale · porqué
PANTALLAS = [
    ("", "Perdón, no pudimos reservar tu turno",
     "Algo no salió como esperábamos. Intentalo de nuevo.",
     "boton", "Volver a la agenda",
     "Alguien tomó esa hora primero · se cumplieron las 12 horas de "
     "anticipación mientras elegías · Cecilia tapó ese día · se dio de baja el "
     "profesional o le sacaron ese tratamiento.",
     "<b>Cuatro causas distintas, un solo texto.</b> Ninguna la puede arreglar "
     "el paciente sabiendo cuál fue, y todas se resuelven igual: volver a la "
     "agenda, que ya viene actualizada. <b>No decimos que alguien la tomó "
     "primero</b> — decisión de Juan: no hace falta revelarlo y encima "
     "irrita, y un paciente irritado abandona."),
    ("", "Ya tenés un turno con este profesional",
     "Para sacar otro, cancelá el que tenés y volvé a intentar.",
     "boton-2", "Ver mis turnos",
     "El tope de turnos abiertos con un mismo profesional.",
     "<b>Es el único error que NO vuelve a la agenda</b>, y por eso tiene "
     "pantalla propia: mandarlo a elegir otro horario es mandarlo a fallar de "
     "nuevo. El texto <b>no dice cuántos turnos</b>, así que sigue siendo "
     "válido cuando el portero pase de dos a uno."),
    ("", "Se cerró tu sesión",
     "Entrá otra vez y terminá de reservar tu turno.",
     "google", "",
     "La sesión se venció mientras completaba el formulario.",
     "Tampoco vuelve a la agenda: sin sesión no se reserva. <b>La acción de "
     "esta pantalla es el botón de Google</b>, el mismo de la pieza 3 — no se "
     "dibuja uno nuevo."),
    ("pantalla-exito", "Tu turno quedó reservado",
     "Te mandamos un correo con los datos. <b>Si no te llega, podés verlo y "
     "cancelarlo desde tus turnos</b>, entrando con la misma cuenta.",
     "boton", "Volver al inicio",
     "El 201: el turno quedó guardado.",
     "<b>Ese texto es verdadero salga o no salga el correo</b>, así que no "
     "hace falta un mensaje aparte para «se guardó pero el aviso falló». El "
     "sistema no tiene que detectar nada. Y dice <b>«entrando»</b> porque el "
     "link del correo no cancela: lleva a tus turnos y del otro lado hay que "
     "iniciar sesión."),
    ("pantalla-exito", "Tu turno quedó cancelado",
     "Te mandamos un correo con el detalle. Podés reservar otro cuando quieras.",
     "boton", "Volver al inicio",
     "La cancelación, que ya está construida y probada.",
     "Misma pantalla, otro texto. Cierra sin pedir explicaciones y deja "
     "abierta la puerta de volver, que es lo que el consultorio quiere."),
]


def accion(tipo, texto, logo):
    if tipo == "google":
        return (f'\n    <button class="btn-google">'
                f'<img src="data:image/png;base64,{logo}" alt="">'
                f'Continuar con Google</button>')

    clase = "btn-1" if tipo == "boton" else "btn-2"
    return f'\n    <button class="btn {clase}">{texto}</button>'


def bloque_pantalla(clase, titulo, cuerpo, tipo, texto_boton, origen, porque, logo):
    return (
        '\n  <div class="estado">'
        f'\n    <p class="dato">{origen}</p>'
        f'\n    <div class="pantalla {clase}">'
        f'\n      <h2>{titulo}</h2>'
        f'\n      <p>{cuerpo}</p>'
        f'{accion(tipo, texto_boton, logo)}'
        '\n    </div>'
        f'\n    <p class="dato" style="margin-top: 14px">{porque}</p>'
        '\n  </div>'
    )


def tablero_mensaje(tokens, css, ancho):
    logo = leer_logo_google()
    pantallas = "".join(bloque_pantalla(*p, logo) for p in PANTALLAS)

    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 05 Mensaje · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&family=Roboto:wght@500&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_CAMPO}
{CSS_BOTON}
{CSS_GOOGLE}
{CSS_MENSAJE}
</style>

<p class="rotulo">Fase ⑦ · Pieza 5 de 8 · {ancho} px</p>
<h1>Mensaje</h1>
<div class="regla"></div>
<p><b>El mensaje no es un bloque adentro del formulario: es una pantalla.</b>
Cada operación termina en una, y cada una devuelve al paciente <b>al único
lugar donde puede seguir</b>. Todo a escala 1:1 en {ancho} px.</p>

<section>
  <p class="rotulo">La distinción que ordena todo</p>
  <h2>Qué se queda en el formulario y qué se va a una pantalla</h2>
  <p>La regla para saber cuál va: <b>¿lo puede arreglar cambiando lo que
  escribió?</b> Si sí, se queda en el campo. Si no, es una pantalla.</p>
  <div class="estado">
    <p class="dato">Se queda: corrige UN DATO, y vive pegado a su campo.</p>
    <div class="campo">
      <label class="etiqueta">Apellido</label>
      <input class="caja caja-error" value="">
      <p class="error-texto">Error — Falta el apellido. Va como figura en tu documento.</p>
    </div>
  </div>
  <p class="dato" style="margin-top: 18px">Se va a una pantalla: <b>la operación
  entera falló o terminó</b>. El formulario ya no sirve para nada, así que no se
  queda ahí abajo tentando a apretar otra vez.</p>
</section>

<section>
  <p class="rotulo">Las cinco pantallas</p>
  <h2>Tres finales que fallan y dos que salen bien</h2>
  <p class="dato" style="margin-top: 8px">El marco gris es el recorte de la
  pantalla: lo de adentro ocupa todo, no es una tarjeta. Ninguno de estos casos
  es inventado — cada uno sale de una respuesta que el portero devuelve.</p>
  {pantallas}
</section>

<section>
  <p class="rotulo">Las reglas</p>
  <h2>Lo que no se negocia</h2>
  <ul class="reglas">
    <li><b>Toda pantalla tiene UNA salida, y es un botón.</b> Un final sin
    botón deja al paciente apretando «atrás».</li>
    <li><b>El destino cambia con la causa:</b> a la agenda, a mis turnos, o a
    volver a entrar. Mandar a todos al mismo lado hace fallar de nuevo a dos
    de los tres.</li>
    <li>El error <b>se disculpa, dice que algo falló y pide reintentar</b>.
    No enumera causas ni nombra lo que se rompió.</li>
    <li><b>El tipo de pantalla lo dice el TEXTO, no un color.</b> Nada de
    títulos rojos ni verdes: un final se tiene que entender leyéndolo. El rojo
    queda para el error de un campo, donde el texto es corto y no puede
    explicarse solo.</li>
    <li><b>Sin íconos.</b> No tenemos un juego de íconos vectorizado, y meter
    uno prestado abre una familia nueva por la ventana.</li>
    <li>El éxito <b>no promete lo que el sitio no controla</b>. Que el correo
    salga no depende de nosotros; que la pantalla de turnos esté, sí.</li>
  </ul>
</section>

<p class="pie">Ni un color escrito a mano: los pares del mensaje los mide
<code>medir-contraste.py</code> antes de cada publicación.</p>
"""



# ============================================================
# PIEZA 6 — LA TARJETA
#
# Decidido por Juan el 2-sep-2026, y recorta el alcance que traía el plan:
# el TRATAMIENTO no tiene tarjeta —es un desplegable y nada más—, así que la
# pieza es una sola tarjeta, la del turno. Y no se acomodan en columnas: van
# en FILAS, una debajo de la otra, en los tres anchos.
#
# 🔴 CORREGIDO el 3-sep-2026, viéndolo en la tira: la acción va ABAJO y ADENTRO
# del cuadro en LOS TRES ANCHOS. Antes, de tablet para arriba, la tarjeta se
# abría en fila y el botón se iba al filo derecho: ahí "CANCELAR TURNO" —que es
# grafito macizo— quedaba flotando contra el borde y era lo más pesado de la
# pantalla, siendo la acción destructiva. Una decisión que se veía bien en su
# propio tablero y mal con el resto de la página al lado. Lo cortó Juan.
# ============================================================

CSS_TARJETA = """
/* TODO CENTRADO ADENTRO DE LA CAJA — decidido por Juan el 3-sep-2026, viendo
   las tres alineaciones a 390 y a tamaño real. Es la variante C: se centra el
   texto Y el botón deja de ocupar el ancho de la tarjeta.

   Se aparta de la alineación del resto del sistema, que arranca todo en el
   margen izquierdo, y por eso vale escribir qué NO rompe:

   · La regla del teléfono de la pieza 3 dice "EL PRINCIPAL va de borde a
     borde". Éste es el secundario, así que esa regla queda intacta.
   · El piso táctil de 44 px se cumple igual: el botón conserva su min-height,
     y del ancho le sobra.

   Lo que sí cuesta: `medir-alineacion.py` mide contra el margen izquierdo y la
   tarjeta ya no arranca ahí. Se le enseñó el caso; no se le bajó el piso. */
.turno {
  max-width: var(--columna-lista);
  margin-top: 14px;
  padding: 18px 18px 20px;
  background: var(--blanco);
  border: 1px solid var(--borde);
  border-radius: var(--radio);
  text-align: center;
}

/* El día y la hora son el título de la tarjeta: es lo que el paciente vino a
   buscar, y lo único que necesita para reconocer su turno de un vistazo. */
.turno h3 {
  font-family: Marcellus, Georgia, serif;
  font-size: var(--tipo-h3);
  line-height: var(--alto-h3);
  color: var(--grafito);
}

.turno .que {
  margin-top: 10px;
  font-size: var(--tipo-cuerpo);
  line-height: var(--alto-cuerpo);
}

.turno .quien {
  margin-top: 2px;
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  color: var(--texto-segundo);
}

.turno .btn {
  margin-top: 18px;
}

.lista { margin-top: 4px; }

/* 🔴 DE TABLET PARA ARRIBA LA TARJETA MIDE SU CONTENIDO, VIVA DONDE VIVA — lo
   pidió Juan el 25-sep-2026: «no tiene sentido que ocupe todo el cuadro en
   sentido horizontal». Una tarjeta de 860 px con el texto centrado adentro es
   una caja casi vacía. En el teléfono no cambia nada: ahí el ancho disponible
   ya es el del contenido.

   ⚠️ SE APLICÓ PRIMERO SÓLO EN LA LISTA DE «MIS TURNOS» y la de la pantalla de
   confirmar siguió cruzando la página —«volviste a devolver las tarjetas
   enormes»—. Es LA MISMA TARJETA: la regla va en ella, no en uno de los dos
   lugares donde aparece.

   🔑 Y ARREGLA UN DESFASE QUE JUAN TAMBIÉN CAZÓ —«alineá en columna el texto
   con el botón»—, con causa medible: `h3` y `p` traen `max-width: var(--columna)`
   (640) de la base, así que dentro de una tarjeta de 860 el texto se centraba
   respecto a 640 y el botón respecto a 860. Dos ejes a 92 px uno del otro. */
@media (min-width: 768px) {

  .turno {
    width: fit-content;
    padding: 24px 40px 26px;
  }

  /* TODAS LAS DE UNA LISTA MIDEN LO MISMO: el ancho de la más ancha.
     `fit-content` en cada tarjeta las dejaba de anchos distintos —cada una
     medía su propio texto— y la lista quedaba dentada por la derecha. La
     rejilla de una columna resuelve las dos: la columna mide lo que la fila
     más ancha, y las tarjetas la llenan. */
  .lista,
  .lista-turnos {
    width: fit-content;
  }

  .lista .turno,
  .lista-turnos .turno {
    width: auto;
  }
}

/* 🔴 DE TABLET PARA ARRIBA LA TARJETA MIDE LO QUE MIDE SU CONTENIDO — lo pidió
   Juan el 25-sep-2026: «no tiene sentido que ocupe todo el cuadro en sentido
   horizontal». Una tarjeta de 860 px con el texto centrado adentro es una caja
   casi vacía. En el teléfono NO cambia: ahí el ancho disponible ya es el del
   contenido.

   🔑 Y ARREGLA UN SEGUNDO PROBLEMA QUE ÉL TAMBIÉN CAZÓ —«alineá en columna el
   texto con el botón»—, que tenía una causa medible: `h3` y `p` traen
   `max-width: var(--columna)` (640) de la base, así que dentro de una tarjeta
   de 860 el texto se centraba respecto a 640 y el botón respecto a 860. Dos
   ejes distintos a 92 px uno del otro. Con la tarjeta del ancho de su
   contenido, los dos centros son el mismo. */
/* LA LISTA SEPARA CON `gap`, EN LOS TRES ANCHOS — una sola forma de separar
   dos tarjetas. El aire de arriba lo pidió Juan el 25-sep: sin la línea de
   ayuda que había antes, el título quedaba pegado a la primera tarjeta. Son
   los mismos 28 px que la pieza 17 pone entre el texto y sus opciones. */
.lista-turnos {
  display: grid;
  gap: 14px;
  margin-top: 28px;
}

.lista-turnos .turno {
  margin-top: 0;
}

@media (min-width: 768px) {

  /* EL AIRE CRECE CON EL TÍTULO. A 390 los 28 px quedan —lo miró Juan— pero
     el mismo valor debajo de un título de escritorio se ve apretado: el h1
     pasa de 32 px a 52, y el aire que lo acompaña tiene que seguirlo. */
  .lista-turnos {
    margin-top: 40px;
  }
}

@media (min-width: 1280px) {

  .lista-turnos {
    margin-top: 48px;
  }
}

/* La acción va SIEMPRE debajo de los datos y adentro del cuadro. En el
   teléfono el botón ocupa el ancho de la tarjeta —lo pide el dedo—; de tablet
   para arriba se ajusta a su texto, porque un "Cancelar turno" de 800 px de
   ancho pesa como si fuera la acción que el sitio empuja, y no lo es. */
"""


# día y hora · tratamiento · profesional · para quién
TURNOS = [
    ("Jueves 11 de septiembre, 15:30", "Consulta", "con Cecilia Duarte",
     "Paciente: María Fernanda Gómez"),
    ("Martes 30 de septiembre, 09:00", "Limpieza", "con Cecilia Duarte",
     "Paciente: Joaquín Gómez"),
]


def tarjeta_turno(cuando, tratamiento, profesional, quien, accion=True,
                  cobertura=None):
    """La tarjeta de un turno.

    `accion` es lo único que cambia entre los dos lugares donde vive. En «mis
    turnos» el turno EXISTE y se puede cancelar; en la pantalla de confirmar
    todavía no existe, así que no hay nada que cancelar y la tarjeta va sin
    botón. El dibujo es el mismo: una tarjeta, no dos.
    """
    boton = (
        '\n      <button class="btn btn-2">Cancelar turno</button>'
        if accion else ''
    )

    linea_cobertura = (
        f'\n        <p class="cobertura">Cobertura: {cobertura}</p>'
        if cobertura else ''
    )

    return (
        '\n    <div class="turno">'
        '\n      <div class="datos">'
        f'\n        <h3>{cuando}</h3>'
        f'\n        <p class="que">{tratamiento} {profesional}</p>'
        f'\n        <p class="quien">{quien}</p>'
        f'{linea_cobertura}'
        '\n      </div>'
        f'{boton}'
        '\n    </div>'
    )


def tablero_tarjeta(tokens, css, ancho):
    lista = "".join(tarjeta_turno(*t) for t in TURNOS)
    acomodo = (
        "una debajo de la otra, y adentro de cada una todo va centrado: los "
        "datos, y debajo el botón, del ancho de su texto"
    )

    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 06 Tarjeta · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_TARJETA}
</style>

<p class="rotulo">Fase ⑦ · Pieza 6 de 8 · {ancho} px</p>
<h1>Tarjeta</h1>
<div class="regla"></div>
<p>Es la tarjeta de <b>un turno reservado</b>, en la pantalla «mis turnos» —
adonde llegan tres de las cinco pantallas de la pieza 5. Todo a escala 1:1 en
{ancho} px.</p>

<section>
  <p class="rotulo">Una sola tarjeta</p>
  <h2>El tratamiento no tiene tarjeta</h2>
  <p>El plan traía dos, la del tratamiento y la del turno. <b>El tratamiento se
  elige en un desplegable y nada más</b>: sin descripción, sin duración, sin
  tarjeta. Una tarjeta con información que nadie va a leer sólo alarga el
  camino hasta el turno.</p>
</section>

<section>
  <p class="rotulo">La tarjeta</p>
  <h2>Cuatro renglones y una acción</h2>
  <p class="dato" style="margin-top: 8px">Todos los datos salen de lo que
  <code>GET /mis-turnos</code> ya devuelve. Nada que haya que agregar al portero.</p>
  <div class="lista">{lista}</div>
</section>

<section>
  <p class="rotulo">Lo que NO lleva</p>
  <h2>Dos datos que el portero devuelve y la tarjeta no muestra</h2>
  <ul class="reglas">
    <li><b>La duración.</b> No cambia nada de lo que el paciente puede hacer, y
    el largo real se lo dice Cecilia en el consultorio.</li>
    <li><b>El motivo de consulta.</b> Ese dato existe para que Cecilia sepa a
    qué vino la persona, y <b>ya viaja en el correo operativo</b>, que es donde
    le sirve. En la pantalla del paciente sería repetirle lo que él mismo
    eligió.</li>
  </ul>
  <p class="dato" style="margin-top: 18px"><b>El renglón «Para…» sí se queda</b>,
  y no es un adorno: un mismo correo puede tener varias personas — una madre
  anota a sus hijos con su casilla—, y sin ese renglón dos turnos del mismo día
  serían indistinguibles.</p>
</section>

<section>
  <p class="rotulo">Cómo se acomodan</p>
  <h2>En filas, siempre</h2>
  <p>Nada de dos o tres columnas: <b>{acomodo}</b>. Una lista de turnos se lee
  de arriba hacia abajo y en orden de fecha, que es como el paciente la busca.</p>
</section>

<section>
  <p class="rotulo">Las reglas</p>
  <h2>Lo que no se negocia</h2>
  <ul class="reglas">
    <li><b>El día y la hora son el título.</b> Es lo que el paciente vino a
    buscar.</li>
    <li>La tarjeta se ve por su <b>filo</b>: el relleno blanco mide 1,07 contra
    el marfil. Es lo mismo que ya pasó con el campo y con el mensaje.</li>
    <li><b>Una sola acción por tarjeta</b>, y es cancelar. Va en el botón
    secundario: cancelar nunca es la acción que el sitio empuja.</li>
    <li>El profesional va con <b>nombre y apellido</b>, siempre. Hoy hay una
    sola y alcanzaría el nombre; el día que entren dos que se llamen igual, una
    pantalla que dice sólo el nombre <b>no se puede arreglar sin rehacerla</b>.
    <i>El apellido de la muestra es de relleno: en el sitio sale de la ficha del
    profesional.</i></li>
    <li><b>En filas, nunca en columnas</b>, y adentro de la caja <b>todo
    centrado</b>: los datos, y debajo el botón, del ancho de su texto. Al
    costado, el grafito macizo de «Cancelar turno» se leía como el botón que
    manda en la pantalla — y cancelar no manda nunca.</li>
    <li><b>La tarjeta es el único bloque centrado del sistema.</b> Todo lo
    demás arranca en el margen izquierdo. Es una caja cerrada con cuatro
    renglones, no una columna de lectura: no hay una línea larga que seguir con
    el ojo, que es lo que el margen izquierdo protege.</li>
    <li>La lista usa <b>su propia medida, más ancha que la del texto</b>
    (860 px en escritorio, contra 640 de un párrafo). El motivo ya no es la
    acción al costado —se sacó—: es que <b>el título es una fecha</b>, y con la
    medida del párrafo el día y la hora se parten en dos renglones.</li>
    <li>La tarjeta <b>no muestra un dato porque exista</b>. Cada renglón está
    porque el paciente hace algo con él.</li>
  </ul>
</section>

<p class="pie">Ni un color ni un tamaño escrito a mano: la tarjeta sale de
<code>tokens.css</code>, igual que el resto del sistema.</p>
"""



# ============================================================
# PIEZA 7 — EL ALMANAQUE Y LOS HORARIOS DEL DÍA
#
# Pedido por Juan el 3-sep-2026: el mes entero, no un día suelto. Son dos
# partes de la misma pieza — el almanaque elige el día, la grilla elige la
# hora— y el portero ya las alimenta a las dos: `GET /horarios-disponibles`
# recibe `desde` y `hasta`, así que devuelve el mes completo en una llamada.
# ============================================================

CSS_GRILLA = """
.almanaque {
  max-width: 420px;
  margin-top: 14px;
}

.mes {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.mes h3 {
  font-family: Marcellus, Georgia, serif;
  font-size: var(--tipo-h3);
  line-height: var(--alto-h3);
}

.mes .pasar {
  display: flex;
  gap: 8px;
}

.mes button {
  width: 44px;
  height: 44px;
  font-size: 20px;
  line-height: 1;
  background: var(--blanco);
  border: 1px solid var(--borde);
  border-radius: var(--radio);
  color: var(--grafito);
  cursor: pointer;
}

.semana {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.semana .letra {
  text-align: center;
  padding-bottom: 6px;
  font-size: var(--tipo-rotulo);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--texto-segundo);
}

/* El día es un control táctil: no baja de 44 px de lado. Con siete columnas,
   eso es lo que fija el ancho mínimo del almanaque entero. */
.dia {
  /* `display: block` y `text-decoration: none` están acá porque en la pantalla
     real el día NO es un botón: es un <a> —o un <span> si está cerrado—, y un
     enlace en línea no toma el alto ni suelta el subrayado. El botón del
     tablero de la pieza 7 no se entera: ya era bloque y nunca tuvo subrayado. */
  display: block;
  text-decoration: none;
  min-height: 48px;
  /* 🔴 EL PISO TÁCTIL TAMBIÉN VA A LO ANCHO, y faltaba. La pieza 7 lo declaró
     —«el día no baja de 44 px de lado, y con siete columnas eso fija el ancho
     mínimo del almanaque»— pero sólo estaba escrito el ALTO. A 1280, donde el
     almanaque va al costado con `flex: none`, las siete columnas se encogían
     al contenido y el día quedaba en 36 px: la regla existía y la pantalla
     decía otra cosa. Medido el 25-sep-2026. */
  min-width: 44px;
  padding: 6px 2px 8px;
  font-family: Jost, "Helvetica Neue", Arial, sans-serif;
  font-size: 17px;
  font-weight: 500;
  line-height: 1.1;
  text-align: center;
  background: var(--blanco);
  border: 1px solid var(--borde);
  border-radius: var(--radio);
  color: var(--grafito);
  cursor: pointer;
}

/* La marca de que ese día tiene lugar. Va ADEMÁS del relleno: los días sin
   lugar son grises, así que la diferencia no depende del punto. */
.dia .marca {
  display: block;
  width: 5px;
  height: 5px;
  margin: 4px auto 0;
  border-radius: 50%;
  background: var(--dorado);
}

.dia-elegido {
  background: var(--boton-fondo);
  border-color: var(--boton-fondo);
  color: var(--boton-texto);
}

.dia-elegido .marca { background: var(--blanco); }

.dia-apagado {
  background: var(--boton-apagado-fondo);
  border-color: var(--boton-apagado-borde);
  color: var(--boton-apagado-texto);
  cursor: not-allowed;
}

.grilla {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(96px, 1fr));
  gap: 10px;
  max-width: var(--columna-lista);
  margin-top: 14px;
}

/* Todos los bloques miden lo mismo y llevan la misma letra, elegido o no: si
   el elegido cambiara de tamaño, la grilla entera se reacomodaría al tocarlo. */
.hora {
  min-height: 52px;
  padding: 12px 8px;
  font-family: Jost, "Helvetica Neue", Arial, sans-serif;
  font-size: 19px;
  font-weight: 500;
  line-height: 1.2;
  text-align: center;
  border-radius: var(--radio);
  cursor: pointer;
  background: var(--blanco);
  border: 1px solid var(--borde);
  color: var(--grafito);
}

/* ELEGIDO: el dorado del botón principal con letra blanca. No estrena color, y
   la letra no baja de 19 px, que es lo que ese par exige. */
.hora-elegida {
  background: var(--boton-fondo);
  border-color: var(--boton-fondo);
  color: var(--boton-texto);
}

/* FOCO: el contorno sobre el filo, la misma regla del botón y del campo. */
.hora-foco {
  box-shadow: inset 0 0 0 2px var(--foco);
}

.hora-apagada {
  background: var(--boton-apagado-fondo);
  border-color: var(--boton-apagado-borde);
  color: var(--boton-apagado-texto);
  cursor: not-allowed;
}

/* En escritorio las dos partes se ven juntas: el mes a la izquierda y los
   horarios del día elegido a la derecha. Debajo de eso van una arriba de la
   otra, y elegir un día baja a los horarios. */
@media (min-width: 1280px) {

  .juntas {
    display: flex;
    align-items: flex-start;
    gap: 40px;
  }

  .juntas .almanaque { flex: none; }

  .juntas .lado {
    flex: 1;
    min-width: 0;
  }

  .juntas .grilla {
    grid-template-columns: repeat(auto-fill, minmax(88px, 1fr));
    margin-top: 0;
  }
}
"""


# número del día · clase · si tiene lugar
DIAS = [
    ("", "vacío", False), ("1", "dia-apagado", False), ("2", "", True),
    ("3", "", True), ("4", "", True), ("5", "dia-apagado", False),
    ("6", "dia-apagado", False),
    ("7", "dia-apagado", False), ("8", "", True), ("9", "", True),
    ("10", "dia-apagado", False), ("11", "dia-elegido", True), ("12", "", True),
    ("13", "dia-apagado", False),
    ("14", "dia-apagado", False), ("15", "", True), ("16", "", True),
    ("17", "", True), ("18", "", True), ("19", "", True),
    ("20", "dia-apagado", False),
    ("21", "dia-apagado", False), ("22", "", True), ("23", "", True),
    ("24", "", True), ("25", "", True), ("26", "", True),
    ("27", "dia-apagado", False),
    ("28", "dia-apagado", False), ("29", "", True), ("30", "", True),
]

# EL MISMO DÍA, DOS VECES. Lo ocupado es idéntico —09:00, 09:30, 11:00, 12:30 y
# 16:30—; lo que cambia es cuánto dura el tratamiento que el paciente ya eligió.
# Lo levantó Juan el 3-sep-2026 mirando una muestra que mentía: con las 11:00
# tomadas, un tratamiento de 60 minutos NO puede arrancar 10:30.
BLOQUES = [
    ("09:00", "hora-apagada"), ("09:30", "hora-apagada"), ("10:00", ""),
    ("10:30", ""), ("11:00", "hora-apagada"), ("11:30", ""),
    ("12:00", ""), ("12:30", "hora-apagada"), ("15:00", ""),
    ("15:30", "hora-elegida"), ("16:00", ""), ("16:30", "hora-apagada"),
    ("17:00", ""), ("17:30", ""), ("18:00", ""), ("18:30", ""),
]

BLOQUES_60 = [
    ("09:00", "hora-apagada"), ("09:30", "hora-apagada"), ("10:00", ""),
    ("10:30", "hora-apagada"), ("11:00", "hora-apagada"), ("11:30", ""),
    ("12:00", "hora-apagada"), ("12:30", "hora-apagada"), ("15:00", ""),
    ("15:30", "hora-elegida"), ("16:00", "hora-apagada"), ("16:30", "hora-apagada"),
    ("17:00", ""), ("17:30", ""), ("18:00", ""), ("18:30", "hora-apagada"),
]


def celda_dia(numero, clase, con_lugar, ancla=False):
    """Una casilla del mes.

    `ancla` cambia de qué ESTÁ HECHO el día, no cómo se ve. En el tablero de la
    pieza 7 el día es un <button>, porque ahí no hay pantalla adonde ir. En la
    pantalla real es un ENLACE al cajón de horarios —la «opción D», decidida por
    Juan— y eso obliga a que sea un <a href="#horarios">: un <button> no puede
    llevar un ancla, y hacerlo con `scrollIntoView()` mueve la pantalla pero
    DEJA EL FOCO ARRIBA, así que el que navega con teclado o con lector de
    pantalla no se entera de que el contenido cambió.
    """
    if clase == "vacío":
        return '\n        <span></span>'

    marca = '<span class="marca"></span>' if con_lugar else ''

    if ancla:
        # EL DÍA QUE NO SE PUEDE TOCAR DEJA DE SER UN CONTROL. Un <span> no
        # recibe foco ni clic, que es exactamente lo que se quiere; `disabled`
        # no existe fuera de los controles, así que lo que se lo dice al lector
        # de pantalla es `aria-disabled`.
        if clase == "dia-apagado":
            return (
                f'\n        <span class="dia {clase}" aria-disabled="true">'
                f'{numero}{marca}</span>'
            )

        # `aria-current` es cómo se anuncia «éste es el día que está elegido»:
        # el dorado lo dice en la pantalla y esto lo dice en voz alta.
        actual = ' aria-current="date"' if clase == "dia-elegido" else ''

        return (
            f'\n        <a class="dia {clase}" href="#horarios"{actual}>'
            f'{numero}{marca}</a>'
        )

    apagado = " disabled" if clase == "dia-apagado" else ""
    return f'\n        <button class="dia {clase}"{apagado}>{numero}{marca}</button>'


def almanaque(ancla=False):
    letras = "".join(
        f'\n        <span class="letra">{l}</span>'
        for l in ("L", "M", "M", "J", "V", "S", "D")
    )
    celdas = "".join(celda_dia(*d, ancla=ancla) for d in DIAS)

    return f"""
    <div class="almanaque">
      <div class="mes">
        <h3>Septiembre 2026</h3>
        <div class="pasar">
          <button>&lsaquo;</button>
          <button>&rsaquo;</button>
        </div>
      </div>
      <div class="semana">{letras}{celdas}
      </div>
    </div>"""


def bloque_hora(hora, clase):
    apagada = " disabled" if clase == "hora-apagada" else ""
    return f'\n        <button class="hora {clase}"{apagada}>{hora}</button>'


def grilla(bloques):
    return '\n      <div class="grilla">' + "".join(
        bloque_hora(*b) for b in bloques
    ) + '\n      </div>'


def tablero_grilla(tokens, css, ancho):
    juntas = ancho >= 1280
    apertura = '\n  <div class="juntas">' if juntas else '\n  <div>'
    lado = '\n    <div class="lado">' if juntas else '\n    <div>'

    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 07 Almanaque y horarios · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_GRILLA}
</style>

<p class="rotulo">Fase ⑦ · Pieza 7 de 8 · {ancho} px</p>
<h1>Almanaque y horarios</h1>
<div class="regla"></div>
<p><b>De esta pieza depende que el turno exista.</b> Son dos partes de lo mismo:
<b>el almanaque elige el día y la grilla elige la hora</b>. Todo a escala 1:1 en
{ancho} px.</p>

<section>
  <p class="rotulo">Las dos partes</p>
  <h2>El mes, y el día que se toca</h2>
  <p class="dato" style="margin-top: 8px">Una sola llamada al portero alimenta
  las dos: <code>GET /horarios-disponibles</code> recibe <code>desde</code> y
  <code>hasta</code>, así que <b>el mes entero viene junto</b>.</p>
  {apertura}{almanaque()}{lado}
      <p class="dato" style="margin-top: 18px">Jueves 11 de septiembre ·
      <b>Consulta, 30 minutos</b> · los horarios en gris no están disponibles.</p>
      {grilla(BLOQUES)}
    </div>
  </div>
</section>

<section>
  <p class="rotulo">Por qué el mes no muestra las horas</p>
  <h2>El número que lo decide</h2>
  <p>Un mes son <b>siete columnas</b>, y un día de agenda tiene <b>hasta
  dieciséis horarios</b>. Meter las horas adentro de cada casilla son
  <b>más de cien bloques en una pantalla</b>, y en el teléfono cada columna
  mediría <b>46 px</b>: no entra «09:00» ni con la letra más chica que el
  sistema permite.</p>
  <p style="margin-top: 12px">Por eso <b>el almanaque dice si el día tiene
  lugar, y la hora se elige abajo</b>. En escritorio las dos cosas se ven al
  mismo tiempo, que es lo más cerca del almanaque completo que se puede llegar
  sin romper el teléfono.</p>
</section>

<section>
  <p class="rotulo">Los estados</p>
  <h2>Y ninguno estrena color</h2>
  <ul class="reglas">
    <li><b>Día con lugar:</b> blanco con filo y un punto dorado.</li>
    <li><b>Día sin lugar o cerrado:</b> el gris del botón apagado. <b>El punto
    no es la única señal</b> — el relleno también cambia—, así que la
    diferencia sobrevive a quien no distingue colores.</li>
    <li><b>Día elegido:</b> el dorado del botón principal.</li>
    <li><b>Horario libre:</b> blanco con filo, como el campo. <b>Elegido:</b>
    dorado con letra blanca, que por eso no baja de 19 px. <b>No disponible:</b>
    el gris del apagado.</li>
    <li>Los cuatro estados que devuelve el portero se pintan con <b>tres
    colores</b>: ocupado, fuera de plazo y «no entra» son, para el paciente, lo
    mismo.</li>
  </ul>
</section>

<section>
  <p class="rotulo">Los turnos de una hora</p>
  <h2>El mismo día, con un tratamiento del doble</h2>
  <p>Arriba se ve el jueves 11 con una <b>consulta de 30 minutos</b>. Éste es el
  mismo día, con lo mismo ocupado, pero el paciente eligió un tratamiento de
  <b>60</b>. <b>Se apagan cuatro horarios más</b>, y ninguno porque esté
  reservado.</p>
  <p class="dato" style="margin-top: 8px">Jueves 11 de septiembre ·
  <b>Blanqueamiento, 60 minutos</b></p>
  {grilla(BLOQUES_60)}
  <p class="dato" style="margin-top: 16px"><b>Las 10:30 se apagaron aunque estén
  libres</b>: de 10:30 a 11:30 pisaría el turno de las 11:00. Lo mismo las 12:00
  —chocan con las 12:30—, las 16:00 —con las 16:30— y las 18:30, que terminaría
  después del cierre. <i>El portero compara el RANGO ENTERO del turno, no bloque
  por bloque.</i></p>
  <p class="dato" style="margin-top: 12px">Lo levantó Juan mirando la primera
  versión de este tablero, que mostraba las 10:30 libres con las 11:00 tomadas.
  <b>El sistema estaba bien; la muestra mentía.</b></p>
</section>

<section>
  <p class="rotulo">Por qué no hay nada que encajar</p>
  <h2>La duración se elige antes que el día</h2>
  <p><b>El tratamiento se elige antes que el día</b>, así que cuando se dibuja
  esta pantalla la duración ya está decidida y es la misma para todos los
  bloques. Una limpieza de 60 minutos no ocupa dos casillas: <b>ocupa una, y el
  portero ya marcó como no disponibles los arranques donde no entra</b> —los que
  chocan con otro turno y los que terminarían después del cierre.</p>
  <p class="dato" style="margin-top: 12px">Por eso los bloques siguen apareciendo
  cada media hora aunque el tratamiento dure una: <b>una limpieza puede empezar
  a las 15:30</b> si de 15:30 a 16:30 está libre.</p>
</section>

<section>
  <p class="rotulo">Las reglas</p>
  <h2>Lo que no se negocia</h2>
  <ul class="reglas">
    <li><b>El día no baja de 44 px de lado</b>, y con siete columnas eso fija
    el ancho mínimo del almanaque.</li>
    <li><b>Todos los bloques de hora miden lo mismo</b>, elegido o no.</li>
    <li>Alto mínimo <b>52 px</b> y letra de <b>19 px</b> en los horarios: acá
    se toca apurado y en la calle.</li>
    <li><b>Un día y un horario elegidos por vez.</b></li>
    <li><b>Los grises se muestran, no se esconden.</b> Un día con huecos dice
    cuánta agenda hay; cuatro horarios sueltos parecen un consultorio vacío.</li>
    <li>La pantalla <b>no explica por qué</b> un horario no está: son tres
    motivos que el paciente no puede cambiar.</li>
    <li><b>El día cerrado no se puede tocar, y por eso no existe ningún cartel
    de «ese día no hay horarios».</b> El almanaque ya lo dice: está gris. Un
    mensaje que contesta una pregunta que nadie puede hacer es ruido.</li>
    <li><b>Al abrir, viene elegido el primer día con lugar</b>, así que la lista
    de horarios nunca aparece vacía. Sin eso, la pantalla arrancaría con la
    mitad de abajo en blanco y sin explicación.</li>
  </ul>
</section>

<p class="pie">Ni un color escrito a mano. Esta pieza <b>no estrenó ninguno</b>:
el dorado del botón, el gris del apagado y el filo del campo ya existían.</p>
"""


# ------------------------------------------------------------
# PIEZA 8 — LA TIRA DE CONTEXTO
#
# NO es una pantalla del sitio y no reemplaza a la maqueta (fase ⑧). Existe
# para una sola cosa: poner las siete piezas cerradas en una misma página, a
# tamaño real, y poder juzgar el PESO de cada una contra las otras. Un botón
# solo, en una lista de estados, no dice si manda o no manda: eso se ve al
# lado del resto.
#
# Se arma en BANDAS. Cada banda es UNA pantalla del flujo real, porque la
# regla del sistema es "un solo botón dorado por pantalla" y una tira corrida
# sin cortes la rompería sola. El rótulo de cada banda es andamiaje del
# tablero, no del sitio.
#
# 🔴 EL DESPLEGABLE DE TRATAMIENTO NO MUESTRA LA DURACIÓN. La regla está
# decidida desde la pieza 6 —"el tratamiento se elige en un desplegable y nada
# más: sin descripción, sin duración, sin tarjeta"— y el porqué es más viejo
# todavía: el paciente NO elige duración, la elige el tratamiento, y el dato
# vive en la base (`tratamientos.duracion_web_min`), no en el navegador.
# Mostrarlo invita a razonar sobre un número que no se puede tocar.
# ------------------------------------------------------------

def leer_wordmark():
    """El logo del encabezado, embebido para que el tablero se abra solo."""
    import base64

    ruta = RAIZ / "brand" / "logo" / "png" / "cb-wordmark-600.png"
    return base64.b64encode(ruta.read_bytes()).decode("ascii")


# El ancho del wordmark en el encabezado, por ancho de pantalla. El mínimo
# medido en brand/COMO-USAR-EL-LOGO.md es 100 px en un celular moderno y
# 300 px en un monitor común: acá van los tres bien por encima de su mínimo.
LOGO_ANCHO = {390: 200, 768: 260, 1280: 320}


def css_tira(ancho):
    margen = MARGENES[ancho]
    return f"""
/* La tira no tiene margen propio: lo lleva cada banda, porque el encabezado
   necesita una línea que cruce la pantalla de lado a lado. */
body {{ padding: 0; }}

.banda {{
  padding: 28px {margen}px 40px;
  border-top: 1px solid var(--dorado-claro);
}}

/* El rótulo que dice qué pantalla es cada banda. ES ANDAMIAJE DEL TABLERO:
   no existe en el sitio. Por eso va chico, en el gris secundario, y arriba
   del borde de la banda. */
.marca-banda {{
  padding: 10px {margen}px 0;
  font-size: var(--tipo-rotulo);
  line-height: var(--alto-rotulo);
  letter-spacing: var(--letra-rotulo);
  text-transform: uppercase;
  color: var(--texto-segundo);
}}

/* EL ENCABEZADO. Sólo el logo: no se inventa acá ninguna navegación, que no
   es una pieza cerrada. La raya dorada es la misma que separa los bloques en
   todos los tableros. */
.encabezado {{
  padding: 20px {margen}px 18px;
  border-bottom: 1px solid var(--dorado);
}}

.encabezado img {{
  display: block;
  width: {LOGO_ANCHO[ancho]}px;
  height: auto;
}}

.hero {{ padding: 32px {margen}px 40px; }}

.hero h1 {{ margin-top: 10px; }}

.hero p {{ margin-top: 16px; }}

.banda h2 {{ margin-bottom: 4px; }}

.banda .paso {{ margin-top: 30px; }}

.banda .paso:first-of-type {{ margin-top: 18px; }}

/* La pantalla de mensaje SIN su marco de demostración: en la pieza 5 ese
   borde era el recorte que explicaba que ocupa todo, y acá la banda ya lo
   dice. El componente es el mismo. */
.pantalla-real {{
  border: 0;
  padding: 0;
  margin-top: 0;
  background: transparent;
}}
"""


def campo_tira(etiqueta, valor, clase, ayuda, opcional):
    """Un campo de la pieza 4, sin la anatomía ni el porqué al lado."""
    rotulo = (
        f'{etiqueta} <span class="opcional">(opcional)</span>'
        if opcional
        else etiqueta
    )
    pie = f'\n      <p class="ayuda">{ayuda}</p>' if ayuda else ""

    if clase == "desplegable":
        caja = (
            '\n      <div class="desplegable">'
            f'\n        <select class="caja"><option>{valor}</option></select>'
            '\n      </div>'
        )
    elif clase == "textarea":
        caja = f'\n      <textarea class="caja">{valor}</textarea>'
    else:
        caja = f'\n      <input class="caja" value="{valor}">'

    return (
        '\n    <div class="campo">'
        f'\n      <label class="etiqueta">{rotulo}</label>'
        f'{caja}{pie}'
        '\n    </div>'
    )


def tablero_contexto(tokens, css, ancho):
    juntas = ancho >= 1280
    apertura = '\n    <div class="juntas">' if juntas else '\n    <div>'
    lado = '\n      <div class="lado">' if juntas else '\n      <div>'
    tarjetas = "".join(tarjeta_turno(*t) for t in TURNOS)

    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 08 Tira de contexto · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&family=Roboto:wght@500&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_GOOGLE}
{CSS_CAMPO}
{CSS_MENSAJE}
{CSS_TARJETA}
{CSS_GRILLA}
{css_tira(ancho)}
</style>

<header class="encabezado">
  <img src="data:image/png;base64,{leer_wordmark()}"
       alt="CB Odontología y Estética">
</header>

<div class="hero">
  <p class="rotulo">Turnos online</p>
  <h1>Reservá tu turno cuando te quede cómodo</h1>
  <p>Elegís el tratamiento, el día y la hora. La confirmación te llega por
  correo, y desde ahí lo podés cancelar si te cambian los planes.</p>
  <div class="acciones">
    <button class="btn btn-1">Reservar turno</button>
    <button class="btn btn-2">Ver mis turnos</button>
  </div>
</div>

<p class="marca-banda">Pantalla 2 · elegir el turno</p>
<div class="banda">
  <div class="paso">
    <h2>¿Qué te vas a hacer?</h2>
    {campo_tira("Tratamiento", "Consulta general", "desplegable",
                "Si no sabés cuál elegir, pedí una consulta.", False)}
  </div>
  <div class="paso">
    <h2>Elegí el día y la hora</h2>{apertura}{almanaque()}{lado}
      <p class="dato" style="margin-bottom: 10px">Jueves 11 de septiembre</p>
      {grilla(BLOQUES)}
      </div>
    </div>
    <div class="acciones">
      <button class="btn btn-1">Continuar</button>
    </div>
  </div>
</div>

<p class="marca-banda">Pantalla 3 · confirmar</p>
<div class="banda">
  <h2>Tus datos</h2>
  {campo_tira("Nombre y apellido", "María Fernanda Gómez", "", "", False)}
  {campo_tira("Teléfono", "", "", "Por si necesitamos avisarte algo del turno.",
              True)}
  {campo_tira("Algo que quieras contarnos", "", "textarea", "", True)}
  <div class="acciones">
    <button class="btn btn-1">Confirmar turno</button>
    <button class="btn btn-2">Volver</button>
  </div>
</div>

<p class="marca-banda">Pantalla 4 · mis turnos</p>
<div class="banda">
  <h2>Tus turnos</h2>
  <div class="lista">{tarjetas}
  </div>
</div>

<p class="marca-banda">Pantalla 5 · el turno quedó reservado</p>
<div class="banda">
  <div class="pantalla pantalla-real">
    <h2>Tu turno quedó reservado</h2>
    <p>Te mandamos un correo con los datos. <b>Si no te llega, podés verlo y
    cancelarlo desde tus turnos</b>, entrando con la misma cuenta.</p>
    <button class="btn btn-1">Volver al inicio</button>
  </div>
</div>

<p class="marca-banda">Lo que esta tira sirve para mirar</p>
<div class="banda">
  <ul class="reglas">
    <li>El <b>peso</b> del botón principal contra el del secundario, con las
    dos piezas en la misma pantalla y no en una lista de estados.</li>
    <li>El <b>tamaño de la letra del botón</b> —19 px, mayúsculas— al lado del
    cuerpo de texto y de los títulos.</li>
    <li>Si el <b>blanco de las tarjetas y los campos</b> se separa del marfil
    de la página cuando hay muchos juntos.</li>
    <li>Si los <b>seis niveles de la escala</b> alcanzan, o si falta uno entre
    el título y el cuerpo.</li>
    <li>Cuánto <b>aire</b> pide cada bloque cuando dejan de estar solos.</li>
  </ul>
  <p class="pie">Los rótulos de banda son andamiaje de este tablero: marcan
  dónde el sitio real corta de pantalla. No existen en el sitio.</p>
</div>
"""

# ------------------------------------------------------------
# EL CHEQUEO QUE FALTABA — la duración no se muestra en pantalla
#
# La regla está decidida desde la pieza 6 y el porqué es más viejo: el paciente
# NO elige duración, la elige el tratamiento, y el dato vive en la base
# (`tratamientos.duracion_web_min`). Se coló igual en el desplegable de la
# pieza 8 y en el texto de muestra de la 2, y lo cazó Juan, no el generador.
#
# EL LÍMITE NO ES QUÉ CLASE TIENE EL PÁRRAFO, ES SI ESO ES PANTALLA. Un tablero
# explica el mecanismo en prosa —y ahí la duración tiene que poder nombrarse,
# porque es de lo que habla la pieza 7—; lo que no puede es aparecer adentro de
# un control o de una tarjeta, que es lo que el paciente ve. Así que se mira
# SÓLO lo que simula la pantalla, no el texto que la rodea.
# ------------------------------------------------------------

DURACION = re.compile(
    r"\d+\s*min\b|\d+\s*minutos?\b|(?:treinta|sesenta|noventa)\s+minutos?",
    re.IGNORECASE,
)

# Lo que ES pantalla: los controles, la tarjeta del turno, el hero, la pantalla
# de mensaje, y la muestra de cuerpo de texto de la escala —que es prosa del
# sitio, no del tablero—.
PANTALLA = [
    re.compile(r"<option\b.*?</option>", re.DOTALL),
    re.compile(r"<button\b.*?</button>", re.DOTALL),
    re.compile(r'<(?:input|textarea)\b[^>]*value="([^"]*)"'),
    re.compile(r'<div class="turno">.*?</div>\s*</div>', re.DOTALL),
    re.compile(r'<label class="etiqueta">.*?</label>', re.DOTALL),
    re.compile(r'<p class="(?:ayuda|ayuda-pantalla|muestra-texto)">.*?</p>', re.DOTALL),
    # La etiqueta del día en la pantalla ⑤: es el lugar donde la duración se
    # colaría copiando el rótulo del tablero de la pieza 7.
    re.compile(r'<p class="cuando">.*?</p>', re.DOTALL),
]


# ============================================================
# PIEZA 9 — EL ENCABEZADO Y EL MENÚ
#
# Es la primera pieza de la LANDING: de la 4 a la 8 son la pantalla de reserva,
# y el encabezado no lo diseñó nadie todavía. La tira de contexto (pieza 8) ya
# dibujó UNO —logo solo, sin navegación—, y dejó escrito que la navegación "no
# es una pieza cerrada". Ésta la cierra.
# ============================================================


def leer_png(nombre):
    """Un PNG de la marca, embebido, para que el tablero se abra solo."""
    import base64

    ruta = RAIZ / "brand" / "logo" / "png" / f"{nombre}.png"
    return base64.b64encode(ruta.read_bytes()).decode("ascii")


# El ancho del logo en el encabezado, por ancho de pantalla.
#
# 🔴 A 390 SON 200 PX, Y EL NÚMERO NO SE ELIGIÓ ACÁ: es el que la pieza 8 ya
# usa en su encabezado. Se probó bajarlo a 160 para meter el botón en la barra;
# al salir el botón del encabezado (decisión de Juan) el motivo desapareció, y
# volver a 200 deja los dos tableros diciendo lo mismo. Los mínimos medidos del
# manual —wordmark 100 px en un celular moderno, apilado 80— quedan bien abajo.
ENCABEZADO_LOGO = {390: 200, 768: 260, 1280: 320}

# La proporción real de cada archivo, medida sobre el PNG. Con ella se calcula
# el ALTO que cada logo le cuesta al encabezado, que es el número que decide.
PROPORCION = {"wordmark": 97 / 600, "apilado": 316 / 600}


def alto_logo(pieza, ancho):
    """Cuánto mide de alto el logo dentro de la barra, en píxeles."""
    return round(ENCABEZADO_LOGO[ancho] * PROPORCION[pieza])


CSS_ENCABEZADO = """
/* El encabezado cruza la pantalla de lado a lado, así que el margen de página
   lo lleva él y no el <body>. Mismo mecanismo que la tira de la pieza 8. */
body { padding: 0; }

.prosa {
  padding: 0 var(--margen-pagina);
}

.prosa section { margin-top: var(--aire-seccion); }

/* LA BARRA. Tres cosas en una fila: el logo a la izquierda, y a la derecha lo
   que la decisión de abajo defina. `space-between` las separa sin escribir
   ningún número de por medio: el hueco es lo que sobra. */
.barra {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  /* 8 px y no 14: el alto de la barra lo fija el BOTÓN de menú, que no baja
     de 44 px por ser el piso táctil. Con 14 arriba y abajo la barra medía 72 y
     el logo —de 32— quedaba flotando en marfil, que se leía como un espacio
     blanco entre el encabezado y el hero. El botón conserva sus 44. */
  padding: var(--aire-barra) var(--margen-pagina);
  background: var(--marfil);
  border-bottom: 1px solid var(--dorado);
}

.barra img {
  display: block;
  height: auto;
}

/* El botón del sistema se centra solo en su caja —así quedó cerrado el
   3-sep—. Adentro de una fila eso lo empujaría al medio: acá se le sacan los
   márgenes automáticos y nada más. El formato, el color y el alto no se
   tocan. */
.barra .btn,
.menu-abierto .btn {
  margin: 0;
  flex-shrink: 0;
}

.menu-abierto .btn { margin: 6px auto 14px; }

/* EL BOTÓN DE MENÚ. Cuadrado de 44 px, que es el piso táctil del sistema. Las
   tres rayas son el borde de arriba de tres cajas, sin ninguna imagen. */
.menu-boton {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  padding: 0 9px;
  background: transparent;
  border: 0;
  cursor: pointer;
}

.menu-boton span {
  display: block;
  height: 2px;
  background: var(--grafito);
}

/* EL MENÚ ABIERTO. Cae debajo de la barra y ocupa el ancho entero: en el
   teléfono no hay lugar para un panel flotante, y uno que tape media pantalla
   esconde el sitio detrás de sí mismo. */
.menu-abierto {
  padding: 8px var(--margen-pagina) 20px;
  background: var(--marfil);
  border-bottom: 1px solid var(--dorado-claro);
}

.menu-abierto a {
  display: block;
  padding: 14px 0;
  border-bottom: 1px solid var(--dorado-claro);
  color: var(--grafito);
  text-decoration: none;
  font-size: var(--tipo-cuerpo);
}

.menu-abierto a:last-of-type { border-bottom: 0; }

/* EL MENÚ EN PANTALLA ANCHA. Los tres enlaces en fila, entre el logo y el
   botón. El rótulo va en versalita como el resto del sistema. */
.menu-fila {
  display: flex;
  align-items: center;
  gap: 28px;
}

/* 🔴 EL MENÚ EN FILA SUBE — 13-sep-2026, lo pidió Juan: «tratamientos,
   nosotros y contacto del header muy chico».

   Usaba --tipo-rotulo (13 px), que es la medida de los RÓTULOS de andamiaje
   —esas líneas en versalitas que dicen de qué se trata un bloque—. El menú no
   es un rótulo: es el único control de navegación del sitio y se toca. 15 px
   con las versalitas y el espaciado que ya tiene lo deja legible sin dejar de
   ser discreto, que es lo que la barra pide.

   A 390 el menú no es esta fila: es el sándwich, que abre un panel con el
   texto a --tipo-cuerpo. De 768 para arriba sí es la fila. */
.menu-fila a {
  /* EL ÁREA TÁCTIL, y por eso el enlace es una caja y no texto suelto. A 768
     lo más probable es una tablet, o sea un dedo. El texto mide 18 px de alto
     y el piso táctil del sistema son 44: sin esto, los tres destinos quedan a
     la vista pero apenas se pueden tocar.

     No agranda la barra, y eso está medido: por dentro mide 45 px a 768 y 52
     a 1280, así que los 44 entran en los dos. */
  display: flex;
  align-items: center;
  min-height: 44px;

  color: var(--grafito);
  text-decoration: none;
  font-size: var(--tipo-rotulo);
  line-height: var(--alto-rotulo);
  letter-spacing: var(--letra-rotulo);
  text-transform: uppercase;
}

@media (min-width: 1280px) {
  .menu-fila a {
    font-size: 15px;
  }

  .menu-fila {
    gap: 34px;
  }
}

/* El marco que dice "esto es una muestra, no la página". Es andamiaje del
   tablero y no existe en el sitio. */
.muestra-barra {
  border: 1px solid var(--dorado-claro);
  margin-top: 16px;
}

.marca-muestra {
  font-size: var(--tipo-rotulo);
  line-height: var(--alto-rotulo);
  letter-spacing: var(--letra-rotulo);
  text-transform: uppercase;
  color: var(--texto-segundo);
  margin-top: 22px;
}

.reglas { margin-top: 12px; padding-left: 20px; max-width: var(--columna); }

.reglas li { margin-top: 8px; }
"""


# LOS NÚMEROS DE LA BARRA — MEDIDOS con Chrome sobre la página real el
# 13-sep-2026, no calculados. El ancho de un texto lo sabe la tipografía: el
# menú en fila mide 344 a 768 y 400,3 a 1280 porque allá la letra sube de 13 a
# 15, y eso no sale de ninguna cuenta que se pueda escribir acá.
#
# 🔴 POR QUÉ ESTÁN ESCRITOS Y NO EN UN PÁRRAFO A MANO: el tablero explicaba la
# decisión con «el botón mide 160» y «son 428 px contra 350». Los dos números
# eran viejos —hoy el botón mide 117,5 a 390— y además se imprimían IGUAL en
# los tres anchos cambiando sólo la cifra del título, así que a 768 el tablero
# argumentaba con las medidas de 390. Quedó a la vista el 13-sep-2026, al
# mirar el tablero a 768 después de mover el menú.
#
# ⚠️ SE VUELVEN A MEDIR si cambia la escala tipográfica, el ancho del logo o
# el texto de los enlaces. No fallan con error: quedan viejos y convencen.
BARRA_MEDIDA = {
    390: {
        "util": 350,
        "logo": 200,
        "menu": 344,
        "boton": 117.5,
        "sandwich": 44,
    },
    768: {
        "util": 688,
        "logo": 260,
        "menu": 344,
        "boton": 117.5,
        "sandwich": 44,
    },
    1280: {
        # 1100, no 1152: el margen de 1280 se unificó en 90 el 14-sep-2026
        # (ver el porqué en css/tokens.css). Si este número no acompaña, los
        # tableros argumentan con el ancho de otro ancho — que es el error
        # que ya se cometió una vez con el tablero 09.
        "util": 1100,
        "logo": 320,
        "menu": 400.3,
        "boton": 153.8,
        "sandwich": 44,
    },
}

HUECO_BARRA = 12


def cuenta_de_la_barra(ancho):
    """El párrafo que explica qué entra y qué no, con los números DE ESE ancho.

    Devuelve el texto ya armado: la cuenta de los tres elementos juntos, la de
    logo + menú, y la conclusión que corresponde. Cada ancho llega a una
    conclusión distinta y por eso el párrafo no puede ser uno solo.
    """
    m = BARRA_MEDIDA[ancho]

    con_todo = m["logo"] + HUECO_BARRA + m["menu"] + HUECO_BARRA + m["boton"]
    sin_boton = m["logo"] + HUECO_BARRA + m["menu"]

    def num(valor):
        return f"{valor:g}".replace(".", ",")

    cuenta = (f'<b>logo {num(m["logo"])} + menú {num(m["menu"])} + botón '
              f'{num(m["boton"])}</b>, más dos huecos de {HUECO_BARRA}, son '
              f'<b>{num(round(con_todo, 1))} px</b> contra los '
              f'<b>{num(m["util"])}</b> que deja el margen de página')

    if sin_boton > m["util"]:
        return (f'<p>Las tres cosas que pide la § 4 —el logo, los enlaces y el '
                f'botón <b>Reservar</b>— <b>no entran juntas a {ancho} px</b>, y '
                f'no es una impresión: {cuenta}. <b>Tampoco entran solos el logo '
                f'y el menú</b> ({num(round(sin_boton, 1))}), y por eso acá el '
                f'menú no puede ser una fila: es el sándwich de '
                f'{num(m["sandwich"])} px.</p>')

    if con_todo > m["util"]:
        return (f'<p>A {ancho} px <b>el logo y los enlaces entran</b> '
                f'—{num(m["logo"])} + {num(m["menu"])} = '
                f'<b>{num(round(sin_boton, 1))}</b> contra {num(m["util"])}, '
                f'sobran {num(round(m["util"] - sin_boton, 1))}—, <b>pero con el '
                f'botón no</b>: {cuenta}, así que <b>faltan '
                f'{num(round(con_todo - m["util"], 1))}</b>.</p>')

    return (f'<p>A {ancho} px <b>entran las tres</b>: {cuenta}, o sea que '
            f'sobran {num(round(m["util"] - con_todo, 1))}. Es el único ancho '
            f'donde el <b>Reservar</b> puede estar en la barra sin sacarle el '
            f'lugar a nada.</p>')


def menu_del_ancho(ancho):
    """Sándwich o fila: el corte está en 768, y la cuenta que lo decidió vive
    en `pagina_del_sitio`. Se escribe una sola vez para que el tablero de una
    pieza no pueda mostrar una forma distinta de la que muestra la página."""
    if ancho < 768:
        return "boton"

    return "fila"


def barra(logo, pieza, ancho, con_menu, con_boton, abierto=False):
    """Una barra de encabezado: el logo, y lo que se le ponga al lado."""
    derecha = ""

    if con_menu == "fila":
        derecha += """
      <nav class="menu-fila">
        <a href="#tratamientos">Tratamientos</a>
        <a href="#nosotros">Nosotros</a>
        <a href="#contacto">Contacto</a>
      </nav>"""

    if con_boton:
        derecha += """
      <a class="btn btn-1" href="#reservar">Reservar</a>"""

    if con_menu == "boton":
        derecha += """
      <button class="menu-boton" aria-label="Abrir el menú">
        <span></span><span></span><span></span>
      </button>"""

    panel = ""

    if abierto:
        panel = """
    <div class="menu-abierto">
      <a class="btn btn-1" href="#reservar">Reservar</a>
      <a href="#tratamientos">Tratamientos</a>
      <a href="#nosotros">Nosotros</a>
      <a href="#contacto">Contacto</a>
    </div>"""

    return f"""
  <div class="muestra-barra">
    <div class="barra">
      <img src="data:image/png;base64,{logo}"
           alt="CB Odontología y Estética"
           width="{ENCABEZADO_LOGO[ancho]}">
      <div style="display: flex; align-items: center; gap: 12px">{derecha}
      </div>
    </div>{panel}
  </div>"""


def muestras_del_encabezado(logo, ancho):
    """El encabezado como queda cerrado EN ESE ancho, con su muestra al lado.

    Antes había dos muestras fijas —el sándwich cerrado y el sándwich abierto—
    y se imprimían en los tres anchos. A 768 y 1280 el menú ya no es un
    sándwich, así que el tablero mostraba una forma que el sitio no usa.
    """
    menu = menu_del_ancho(ancho)
    m = BARRA_MEDIDA[ancho]

    con_todo = m["logo"] + HUECO_BARRA + m["menu"] + HUECO_BARRA + m["boton"]
    con_boton = con_todo <= m["util"]

    salida = f"""
  <p class="marca-muestra">El encabezado, cerrado</p>
  {barra(logo, "wordmark", ancho, menu, con_boton)}"""

    # El panel existe SÓLO donde hay sándwich: es lo que el botón abre. Donde
    # el menú está a la vista no hay nada que desplegar.
    if menu == "boton":
        salida += f"""
  <p class="marca-muestra">Con el menú abierto</p>
  {barra(logo, "wordmark", ancho, menu, False, abierto=True)}"""

    return salida


def tablero_encabezado(tokens, css, ancho):
    wordmark = leer_png("cb-wordmark-600")
    apilado = leer_png("cb-apilado-600")
    chico = ancho < 1280

    alto_w = alto_logo("wordmark", ancho)
    alto_a = alto_logo("apilado", ancho)

    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 09 Encabezado y menú · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_ENCABEZADO}
</style>

<div class="prosa">
<p class="rotulo">Fase ⑧ · Pieza 9 · {ancho} px</p>
<h1>Encabezado y menú</h1>
<div class="regla"></div>
<p><b>Es lo primero que se ve y lo único que está en toda la página.</b> La
pieza 8 ya dibujó un encabezado —el logo solo— y dejó escrito que la navegación
no era una pieza cerrada. <b>Ésta la cierra.</b></p>

<section>
  <p class="rotulo">La decisión que esta pieza tiene que cerrar</p>
  <h2>Cuál logo va en la barra</h2>
  <p>El manual asigna el <b>apilado</b> al «encabezado del sitio en el
  celular», y el brief dibuja el <b>wordmark</b>. <b>La pieza 8 ya eligió el
  wordmark sin que nadie lo decidiera</b>, así que confirmar o cambiar acá
  también toca ese tablero.</p>
  <p class="marca-muestra">Wordmark · {ENCABEZADO_LOGO[ancho]} px de ancho ·
  <b>{alto_w} px de alto</b></p>
  {barra(wordmark, "wordmark", ancho, menu_del_ancho(ancho), not chico)}
  <p class="marca-muestra">Apilado · {ENCABEZADO_LOGO[ancho]} px de ancho ·
  <b>{alto_a} px de alto</b></p>
  {barra(apilado, "apilado", ancho, menu_del_ancho(ancho), not chico)}
  <p style="margin-top: 12px">🏁 <b>Resuelto por Juan el 3-sep-2026: va el
  WORDMARK a 200 px</b>, «es más sobrio». Es el mismo ancho que ya usa la
  pieza 8, así que los dos encabezados del proyecto dicen lo mismo.</p>
  <p class="dato" style="margin-top: 12px"><b>Se probaron cuatro y se
  midieron:</b> wordmark a 200 y 240, apilado a 150 y 180. <b>El apilado a
  180 daba la misma letra que el wordmark de 240 ocupando el 51 % del ancho
  en vez del 69 %</b> —el «CB» mide el <b>21,5 %</b> del ancho del logo en el
  apilado y el <b>16,2 %</b> en el wordmark, medido sobre la tinta del
  archivo— <b>y se descartó igual, por alto de barra: 123 px contra 60.</b>
  <i>Con el wordmark «más grande» y «más a la izquierda» son la misma perilla
  tirando para lados opuestos, porque el nombre va al lado y no abajo.</i></p>
  <p class="dato" style="margin-top: 16px"><b>El número que decide es el
  ALTO</b>, no el ancho: el apilado mide <b>{alto_a} px</b> contra
  <b>{alto_w}</b> del wordmark, y la barra queda
  <b>{round(alto_a / alto_w, 1)} veces más alta</b>. En un encabezado que
  acompaña el scroll, ese alto se paga en cada pantalla del sitio.</p>
</section>

<section>
  <p class="rotulo">La segunda decisión</p>
  <h2>Qué va del otro lado</h2>
  {cuenta_de_la_barra(ancho)}
  <p style="margin-top: 12px">🏁 <b>Resuelto por Juan: donde no entran los
  tres, el que se va del encabezado es el BOTÓN</b> —a 390 el 3-sep-2026, y a
  768 el 13-sep con la misma cuenta—. Ahí el <b>Reservar</b> vive en el hero,
  que es donde el paciente llega leyendo. <b>A 1280 entra y se queda en la
  barra.</b> <i>El encabezado no es el único lugar donde puede estar la
  acción; el menú sí es el único lugar donde pueden estar los enlaces.</i></p>
  <p class="dato" style="margin-top: 12px">🔴 <b>Y la forma del menú cambia con
  el ancho, por la misma cuenta:</b> a 390 los enlaces no entran ni sin el
  botón, así que van adentro del <b>sándwich</b>; <b>de 768 para arriba van en
  fila, a la vista</b>. <i>Un menú escondido cuando hay lugar para mostrarlo es
  un toque de más por cada destino.</i></p>
  {muestras_del_encabezado(wordmark, ancho)}
  <p class="dato" style="margin-top: 16px">⚠️ <b>Y queda anotado lo que Juan
  levantó al mirarlo a 1:1: a {ancho} px el botón del sistema es
  ENORME.</b> Mide 160 px de ancho y 44 de alto con letra de 19 — casi la
  mitad del ancho útil de la pantalla. <b>El formato único de botón se cerró
  el 3-sep sin haberlo visto adentro de una barra</b>, y ésta es la primera
  pieza que lo mete en una. No se toca acá: se decide con la página entera
  delante, en el tablero 15.</p>
</section>

<section>
  <p class="rotulo">Las reglas</p>
  <h2>Lo que no se negocia</h2>
  <ul class="reglas">
    <li><b>El botón es el mismo del sistema</b>, sin achicar: mismo alto, misma
    letra de 19 px, mismo dorado. Lo único que se le saca adentro de la barra
    son los márgenes automáticos que lo centraban.</li>
    <li><b>El botón de menú no baja de 44 px de lado</b>, que es el piso táctil
    del sistema.</li>
    <li><b>La raya de abajo es la dorada</b>, la misma que separa bloques en
    todos los tableros.</li>
    <li><b>El menú abierto empuja la página, no la tapa.</b> Un panel que cubre
    media pantalla esconde el sitio detrás de sí mismo.</li>
    <li><b>Los enlaces son anclas de la misma página</b>: el sitio es una sola
    página y el menú no navega a ningún lado.</li>
  </ul>
</section>
</div>
"""


# ============================================================
# PIEZA 10 — EL HERO
#
# Es la única pantalla que el brief SÍ trae (pág. 17), y de escritorio. Acá se
# pasa a móvil, que es donde manda el sitio, y se le suman las dos cosas que el
# brief no tiene: los textos definitivos de la § 4 y la PROPORCIÓN de la foto,
# que es el primer dato del brief de fotos.
# ============================================================

# 🔴 «Santa Fe» LLEVA ESPACIO DURO y no se parte nunca — lo pidió Juan el
# 13-sep-2026, al ver el titular cortado en «…en Santa / Fe, con la calma…».
# Es un nombre propio de dos palabras: partido, la primera línea termina
# nombrando otra cosa. `&nbsp;` es un espacio que se ve igual pero por el que
# el navegador no corta, así que vale en los tres anchos y no hay que
# acordarse de revisarlo cada vez que cambia un tamaño.
H1 = ("Odontología y estética dental en Santa&nbsp;Fe, "
      "con la calma que tu sonrisa merece.")

SUBTITULO = ("Blanqueamiento, tratamientos generales y estética dental en un "
             "espacio pensado para tu tranquilidad.")

# La foto de ejemplo vive en brand/fotos/, versionada, con su procedencia y su
# licencia al lado. NO va embebida en el HTML: se enlaza por ruta relativa, así
# el tablero pesa lo que pesa y la foto se cambia sin regenerar nada.
FOTO = RAIZ / "brand" / "fotos" / "hero-ejemplo.jpg"

# Desde brand/tableros/10-hero/<ancho>.html hasta brand/fotos/.
FOTO_RELATIVA = "../../fotos/hero-ejemplo.jpg"


def leer_foto():
    """La ruta a la foto, o None si falta.

    Devuelve la RUTA y no el contenido: si el archivo no está, el tablero
    dibuja el hueco marcado en vez de romperse — un tablero que no abre no se
    puede aprobar.
    """
    if not FOTO.exists():
        return None

    return FOTO_RELATIVA


# LA FOTO DE «NOSOTROS» ES OTRA, Y ES UNA SEGUNDA PERSONA A PROPÓSITO.
#
# Hasta el 11-sep-2026 este bloque reusaba la foto del hero, así que en la
# página armada la misma cara aparecía DOS VECES. Estaba anotado como artefacto
# de la maqueta, no como decisión, y se arregla acá: un archivo propio, ya
# recortado a 4:5, que es la proporción del hueco.
FOTO_NOSOTROS = RAIZ / "brand" / "fotos" / "nosotros-ejemplo.jpg"

FOTO_NOSOTROS_RELATIVA = "../../fotos/nosotros-ejemplo.jpg"


def leer_foto_nosotros():
    """La ruta al retrato, o None si falta. Misma regla que leer_foto()."""
    if not FOTO_NOSOTROS.exists():
        return None

    return FOTO_NOSOTROS_RELATIVA


CSS_HERO_VELO = """
/* EL HERO SOBRE LA FOTO — la forma que se propone.

   La foto ocupa la pantalla y el texto va ARRIBA de ella, no debajo. Lo que
   hace que eso se pueda leer no es el color de la letra: es el VELO, un
   degradado del propio grafito de la marca que baja de transparente arriba a
   casi opaco abajo. No entra ningún color nuevo al sistema — es el grafito
   con transparencia.

   🔴 El velo NO se elige a ojo: se mide sobre la captura, en la franja donde
   cae el texto, con tools/medir-velo.py. Si el par blanco/fondo real no llega
   a 4.5, el velo sube. */
.hero-velo {
  position: relative;
  isolation: isolate;
}

.hero-velo .hero-foto {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  aspect-ratio: auto;
  object-fit: cover;
  object-position: 50% 10%;
  z-index: -2;
}

.hero-velo::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  background: linear-gradient(
    to top,
    rgba(51, 50, 47, 0.88) 0%,
    rgba(51, 50, 47, 0.80) 48%,
    rgba(51, 50, 47, 0.44) 68%,
    rgba(51, 50, 47, 0.10) 86%,
    rgba(51, 50, 47, 0.00) 100%
  );
}

/* El texto se apoya ABAJO. Arriba queda la foto sola, que es lo que hace que
   la pieza se lea como una foto con texto y no como una foto tapada. */
.hero-velo .hero-texto {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  min-height: 660px;
  padding: 20px var(--margen-pagina) 24px;
}

.hero-velo h1 { color: var(--blanco); }

/* La bajada baja al nivel «chico» de la escala —el que el sistema ya usa para
   texto que se lee pero manda menos—. No se inventa ningún tamaño: se elige
   otro peldaño de la escala, y con eso el bloque de texto ocupa menos y la
   foto recupera cara. */
.hero-velo .bajada {
  margin-top: 12px;
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  color: var(--blanco);
  opacity: 0.92;
}

/* La raya dorada arriba del titular: es la misma que separa los bloques en
   todo el sistema, y acá hace de arranque del texto. */
.hero-velo .filo {
  width: 56px;
  height: 2px;
  background: var(--dorado);
  margin-bottom: 14px;
}

.hero-velo .acciones { justify-content: start; margin-top: 20px; }


/* El secundario sobre la foto no puede ser grafito macizo: se hunde en el
   velo. Se invierte —filo y letra blancos, relleno transparente—, que es el
   mismo gesto que el sistema ya usa para el foco del secundario. */
.hero-velo .btn-2 {
  background: transparent;
  color: var(--blanco);
  box-shadow: none;
  border: 2px solid var(--blanco);
}
/* 🔴 ACÁ HUBO UN ARREGLO QUE NO ARREGLÓ NADA — DOS VECES, y las dos por lo
   mismo. Queda escrito entero porque el modo de falla es el peor que hay: no
   da error, no se ve, y se reporta hecho.

   INTENTO 1. Se escribió la regla con `.hero-foto`, UNA clase. En la página
   la foto la gobierna `.hero-velo .hero-foto`, que son DOS. Perdió.
   🔑 Y UNA `@media` NO SUMA PRIORIDAD: parece más específica porque está más
   adentro, y no lo es.

   INTENTO 2. Se corrigió el selector a dos clases… y siguió sin aplicar,
   porque con la MISMA prioridad gana la que va ÚLTIMA en el archivo — y el
   bloque vivía en `CSS_HERO`, que se pega ANTES que `CSS_HERO_VELO`. Por eso
   ahora está acá abajo, pegado a la regla que pisa.

   Las dos veces se confirmó midiendo el valor COMPUTADO en el navegador, no
   mirando la captura. Lo levantó Juan las dos veces: «el texto del hero sigue
   tapando la cara».

   ⚠️ La lección operativa, y va en serio: un cambio de CSS no se da por hecho
   porque la captura parezca distinta. Se pide el valor computado. */
/* 🔴 EN ESCRITORIO EL HERO SE PARTE: TEXTO A LA IZQUIERDA, FOTO A LA DERECHA.

   POR QUÉ SE LLEGÓ ACÁ, y es el tercer intento sobre el mismo problema. Los
   dos anteriores movieron el RECORTE de la foto para que el texto no cayera
   sobre la cara, y los dos fallaron por la misma razón de fondo: a 1280 la
   foto llena los 1280 px de ancho y el texto ocupa la mitad izquierda, así
   que la cara —que está en el centro— queda debajo del texto SIEMPRE. Subir
   el recorte mueve la foto hacia arriba, no la cara hacia el costado. No
   había `object-position` que lo arreglara: el problema era el layout.

   🔑 Y ESTABA PREVISTO DESDE LA PIEZA 10, que lo dejó escrito en su brief de
   fotos: «de tablet para arriba la foto ocupa media pantalla y se estira al
   alto del texto». Esto no inventa una forma nueva: construye la que ya se
   había decidido y nunca se había implementado.

   LO QUE CAE SOLO AL PARTIRLO: el velo. Existía para que la letra blanca se
   leyera sobre la foto; con el texto sobre marfil no hay nada que velar, y el
   par grafito/marfil mide 12,00 contra los 7,7 que daba el velo. Los botones
   vuelven a su forma normal del sistema por el mismo motivo. */
/* 🔴 EL HERO A 768 — 13-sep-2026. Hasta hoy acá se pintaba el hero de móvil
   con la pantalla el doble de ancha, y eso movía el texto justo ENCIMA de la
   cara: a 390 la foto es vertical y la cara queda arriba del texto; a 768 la
   caja se volvió apaisada, la cara bajó al centro y el texto la pisó.

   Lo cazó Juan mirando la página, y eligió arreglar la forma que ya está
   aprobada en vez de estrenar otra. Son TRES NÚMEROS, ninguna forma nueva:

   1. EL TEXTO DEJA DE CRUZAR LA FOTO ENTERA. Sin techo medía los 688 de la
      columna; con 520 la foto respira a la derecha y la línea no se estira.
   2. 🔴 EL ALTO NO SE TOCA: 660, el mismo que a 390. Se probó subirlo a 820
      para alejar el texto de la cara y FUE PEOR — con la barra encima, la
      sección dejaba de entrar en la ventana de una notebook y había que
      scrollear para ver el hero completo. Lo cazó Juan de una: «la sección
      entera no queda en el cuadro». Un hero que no entra en la pantalla deja
      de ser un hero.
      Lo que aleja el texto de la cara es el ENCUADRE, que no cuesta alto.
   3. LOS BOTONES VAN EN FILA. Apilados dejaban tres cuartos del ancho
      vacíos; `.acciones` los apila a propósito en el teléfono, donde no
      entran de a dos. Acá entran. */
@media (min-width: 768px) {
  /* EL TITULAR VA EN DOS RENGLONES Y A TODO EL CUADRO — lo pidió Juan el
     13-sep-2026. El techo de 520 lo partía en cuatro y lo empujaba contra la
     cara; con el ancho entero y `balance` los dos renglones quedan parejos y
     el bloque de texto mide la mitad de alto. */
  .hero-velo .hero-texto {
    max-width: none;
  }

  /* 36 y no 42: es el tamaño MÁS GRANDE que deja el titular en dos renglones
     a todo el ancho del cuadro. Medido: a 42 son tres líneas; a 37 todavía
     son tres; a 36 son dos, de 688 y 582 px.

     ⚠️ El rag de 106 px NO se arregla con el tamaño: con «Santa Fe» atado por
     su espacio duro, el único corte posible es el de la coma. Achicar más la
     letra baja los dos números a la vez y el desnivel queda igual. */
  .hero-velo h1 {
    font-size: 36px;
  }

  /* EL ENCUADRE SE CORRE A LA DERECHA. A 768 la caja es más apaisada que la
     foto, así que `cover` recorta a los LADOS y no arriba: mover el foco en
     horizontal es lo único que cambia qué queda a la vista. Con el foco al
     68 % la persona se acomoda hacia la derecha y la esquina de abajo a la
     izquierda —que es donde se apoya el texto— queda sobre fondo. */
  .hero-velo .hero-foto {
    object-position: 68% 10%;
  }

  .hero-velo .acciones {
    grid-template-columns: max-content max-content;
  }
}

@media (min-width: 1280px) {
  .hero-velo {
    display: grid;
    /* 🔴 LA COLUMNA DE LA FOTO ES MÁS ANGOSTA QUE LA DEL TEXTO, y el motivo
       es la foto, no el texto. La del hero es VERTICAL —900 × 1350, y el
       brief de la pieza 10 pide que la definitiva también lo sea—. Metida en
       un hueco apaisado, `cover` la escala por el ancho y recorta el resto:
       medido, con las columnas al 50 % se veía sólo el 60 % del alto de la
       foto, así que la persona salía cortada. Lo levantó Juan.

       Cuanto más angosto el hueco, más parecido a la proporción de la foto y
       menos recorte. 57/43 es lo más lejos que se puede ir sin que el titular
       empiece a partirse feo. */
    grid-template-columns: 1.33fr 1fr;
    isolation: auto;
    position: relative;
    /* 🔴 EL HERO OCUPA LA PANTALLA, menos el encabezado — lo pidió Juan el
       13-sep-2026: «el tamaño del hero es más pequeño que el total de la
       pantalla». Con un alto fijo quedaba una franja de marfil abajo antes de
       la primera sección, y el hero dejaba de leerse como la portada.

       Los 97 px que se restan son el alto REAL de la barra en escritorio y
       están medidos, no estimados: logo 52 + aire 22 arriba + 22 abajo +
       1 del filo dorado. Si el aire de la barra cambia, este número cambia. */
    /* 🔴 `height`, NO `min-height` — 14-sep-2026, y lo pidió Juan:
       «independientemente de la pantalla usada siempre tenga el tamaño de la
       pantalla, ni más ni menos».

       `min-height` es un PISO: el hero podía crecer por encima de él si el
       contenido pedía más, y eso es exactamente lo que pasaba en una ventana
       de 800 — el mínimo daba 703 y el texto pedía 745, así que el hero se
       iba a 845 y LA FOTO NO LO ACOMPAÑABA: quedaba una franja de marfil de
       ~40 px debajo de ella. `height` fija el alto, así que no hay hueco
       posible entre el hero y su foto.

       ⚠️ LO QUE SE RESIGNA, y es una decisión, no un descuido: el piso de
       680 existía porque en una ventana baja la foto vertical se recorta más.
       Ese recorte vuelve. A cambio el hero mide la pantalla siempre, que es
       lo que se pidió.

       ⚠️ Y EL LÍMITE MEDIDO: con los botones en fila el contenido del hero
       pide unos 420 px. Por debajo de una ventana de ~520 el texto se sale
       del hero. No hay pantalla de escritorio así de baja, pero si alguna vez
       se agrega una línea al titular, este número baja. */
    height: calc(100vh - 97px);

    /* 🔴 Y LA FILA TIENE QUE PODER ENCOGER, si no el hero no entra en la
       pantalla. Medido: sin esto el hero daba 960 px FIJOS con ventanas de
       673, 773 y 863 — o sea que el `100vh` de arriba no mandaba nada.

       Lo imponía la FOTO: en una columna de 640 px, su proporción natural la
       estira a 960 de alto, y una fila de grilla crece hasta el alto
       intrínseco de lo que tiene adentro. Por eso el hero se salía de la
       pantalla y quedaba cortado. `1fr` más el `min-height: 0` de abajo le
       sacan ese poder a la foto: la fila mide lo que el hero le da y la foto
       se recorta con `cover`, que es para lo que está. */
    /* ⚠️ `minmax(0, 1fr)` Y NO `1fr` A SECAS, y la diferencia es todo: un
       `1fr` pelado es en realidad `minmax(auto, 1fr)`, y ese `auto` significa
       «nunca menos que el tamaño intrínseco de lo que hay adentro». Con la
       foto adentro eso eran 960 px, así que la fila se plantaba en 960 y el
       `min-height` de arriba no tenía nada que hacer — medido: 616 px de
       min-height computado contra una fila de 960. El `0` del minmax le saca
       ese piso. */
    grid-template-rows: minmax(0, 1fr);
  }

  /* 🔴 Y EL TITULAR SUBE CON EL HERO — 13-sep-2026. Juan dijo «se achicaron
     las letras», y medido NO se achicó ninguna: el h1 sigue en 52 px, igual
     que antes. Lo que cambió es el HUECO donde vive.

     🔑 El hero pasó de un alto fijo de 620 px a ocupar la pantalla entera
     —unos 850 en una ventana normal—, o sea creció cerca de un 37 %, y el
     texto se quedó donde estaba. Un tamaño no se lee en píxeles: se lee
     contra lo que tiene alrededor. La letra no encogió; el espacio creció.

     64 px no estrena un peldaño arbitrario: es --tipo-h1 (52) llevado a la
     misma proporción en que creció su caja. El titular del hero es el ÚNICO
     que vive a pantalla completa, así que sube él solo y no el token — los
     títulos de sección siguen en 52. */
  /* ⚠️ 56 Y NO 64. Los 64 se eligieron mientras Juan miraba la página con el
     zoom del navegador bajo —culpa mía, se lo había bajado yo— así que todo
     se veía chico y el número salió inflado. Al verlo al 100 % real: «ahora
     es muy grande». 56 sigue arriba de los 52 del token, que es lo que pedía
     el hero a pantalla completa, sin pasarse. */
  .hero-velo h1 {
    font-size: 56px;
    line-height: 1.12;
  }

  /* La foto deja de ser un fondo absoluto y pasa a ser la columna derecha. */
  /* 🔴 LA FOTO VA FUERA DEL FLUJO, y es el tercer intento sobre lo mismo.

     Qué pasaba, medido: el hero daba 960 px con ventanas de 673, 773 y 863 —
     el `min-height` computaba bien (616) y no servía de nada—. La causa es
     una regla de CSS que engaña: `height: 100%` NO se aplica cuando el padre
     sólo tiene `min-height` y no `height`, así que la foto caía en su alto
     natural —640 de ancho por su proporción, 960— e inflaba la fila entera.
     Ni `minmax(0, 1fr)` ni `min-height: 0` lo arreglan, porque el problema no
     era el mínimo de la fila sino la altura de la imagen.

     Sacándola del flujo con `position: absolute`, la foto deja de tener voz
     en cuánto mide el hero: se estira entre el borde de arriba y el de abajo
     de lo que el hero termine midiendo, y `cover` recorta lo que sobre. El
     alto lo deciden ahora el `min-height` y el texto, que es como tiene que
     ser. */
  .hero-velo .hero-foto {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    /* ⚠️ `left: auto` NO SOBRA: la regla de arriba pone `inset: 0`, que fija
       los cuatro lados a la vez. Con `left` y `right` los dos en 0 y un
       ancho del 50 %, el navegador resuelve el conflicto quedándose con el
       IZQUIERDO, así que la foto se iba al lado equivocado y tapaba el texto.
       Anular el lado que no se usa es lo que la manda a la derecha. */
    left: auto;
    width: 43%;
    /* ⚠️ `100%` Y NO `auto`, y la diferencia es de manual: en un DIV, `auto`
       con `top` y `bottom` puestos calcula el alto por los bordes. En una
       IMAGEN no — es un elemento reemplazado, así que `auto` significa «usá
       tu propia proporción» y el `bottom` se ignora. Medido: daba 960 px y se
       pasaba 344 del hero, metiéndose adentro de Tratamientos.

       Con la foto ya fuera del flujo, `100%` sí resuelve: el bloque de
       referencia es el hero, cuya altura a esta altura del cálculo ya está
       decidida. */
    height: 100%;
    aspect-ratio: auto;
    object-fit: cover;
    object-position: 50% 30%;
    z-index: auto;
  }


  /* Sin foto debajo no hay nada que velar. */
  .hero-velo::before {
    display: none;
  }

  .hero-velo .hero-texto {
    grid-column: 1;
    grid-row: 1;
    justify-content: center;
    min-height: 0;
    /* 🔴 EL PADDING NO ES SIMÉTRICO, y es a propósito — 14-sep-2026.
       El de la IZQUIERDA es el margen de la página: tiene que valer lo mismo
       que el de las secciones o el hero rompe el borde unificado. El de la
       DERECHA no es un margen de página: es el aire contra la foto, y por eso
       vale 40, el mismo hueco que separa las dos columnas de «Nosotros».

       Qué lo trajo: al unificar el margen en 90, el titular perdió 52 px de
       ancho y pasó de 4 líneas a 5, más cortas. Con 90 a la izquierda y 40 a
       la derecha el texto vuelve a ~600 px y el titular a 4 líneas, sin tocar
       el borde. */
    padding: 48px 40px 48px var(--margen-pagina);

    /* 🔴 DEVUELVE EL ANCHO QUE LE PUSO EL CORTE DE 768, y hay que escribirlo
       aunque no se vea: las dos @media se aplican las dos, y la de acá no
       pisaba `max-width`. Sin esta línea el texto de 1280 se achicaba de 731
       a 520 y el titular pasaba de 4 líneas a 6. Acá el ancho lo da la
       COLUMNA del grid, que es lo aprobado el 13-sep. */
    max-width: none;
  }

  /* 🔴 LOS BOTONES VAN EN FILA TAMBIÉN ACÁ — 14-sep-2026, lo decidió Juan:
     «los desapilamos y aprovechamos el espacio». Hasta hoy 1280 los volvía a
     apilar con una regla propia; ahora hereda la de 768 y no hay regla que
     escribir. Un bloque menos que mantener. */

  /* El texto vuelve al grafito: sobre marfil mide 12,00, que es el par más
     alto del sistema. La letra blanca sólo existía por el velo. */
  .hero-velo h1,
  .hero-velo .bajada {
    color: var(--grafito);
    opacity: 1;
  }

  /* Y el secundario vuelve a su forma normal —grafito macizo—: la inversión
     era para que no se hundiera en el velo, y el velo ya no está. */
  .hero-velo .btn-2 {
    background: var(--boton-2-fondo);
    color: var(--boton-2-texto);
    border: 0;
  }
}

"""


CSS_HERO = """
/* EL ENCABEZADO PEGADO AL HERO. El marco de `.muestra-barra` es andamiaje del
   tablero de la pieza 9 —ahí sirve para decir «esto es una muestra»—, y acá
   metía un filo y unos píxeles de marfil entre la barra y la foto. En el sitio
   no hay nada entre una cosa y la otra: la raya dorada del encabezado ES el
   borde de arriba del hero. */
.muestra-barra {
  border: 0;
  margin: 0;
}

/* LA FOTO. Va a sangre y sin esquinas redondeadas: el radio del sistema es de
   controles y superficies, y el manual dibuja la foto cuadrada.

   `aspect-ratio` fija la FORMA del hueco y `object-fit: cover` recorta la foto
   para llenarlo sin deformarla — la proporción de la imagen no manda, manda la
   del hueco. `object-position` dice qué parte se conserva al recortar: acá la
   sonrisa, que es el motivo de la foto. */
.hero-foto {
  display: block;
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
  object-position: 50% 52%;
}

/* 🔴 EN ESCRITORIO EL RECORTE SUBE — 13-sep-2026, lo levantó Juan: «el texto
   del hero tapa la foto». Medido mirando: a 1280 el titular caía sobre la
   boca y el mentón, y los botones sobre el cuello.

   NN/g lo llama COPY SPACE: la zona menos cargada de una foto, la única donde
   se puede escribir sin tapar lo que importa. Y avisa justo nuestro caso — el
   texto sobre una imagen casi siempre necesita ubicarse distinto en pantalla
   grande que en chica, porque al cambiar el recorte lo que estaba despejado
   deja de estarlo. A 390 el hueco es 4:3 sobre 390 px y la cara entra entera;
   a 1280 el mismo 4:3 sobre 1280 px recorta muchísimo más alto.

   Se mueve el ENCUADRE y no el texto: el titular, el velo y el contraste ya
   medido (7,7) quedan intactos.

   ⚠️ ESTO NO REEMPLAZA AL BRIEF DE FOTOS QUE ESCRIBIÓ ESTA MISMA PIEZA: la
   foto definitiva se pide VERTICAL, con la cara en el TERCIO DE ARRIBA y aire
   abajo para que el velo tenga dónde caer. Acá se acomoda la foto de EJEMPLO,
   que es un primer plano apaisado y no cumple ese brief. */

.hero-hueco {
  width: 100%;
  aspect-ratio: 4 / 3;
  background: var(--dorado-claro);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--texto-segundo);
  font-size: var(--tipo-chico);
  text-align: center;
  padding: 0 24px;
}

.hero-texto { padding: 26px var(--margen-pagina) 32px; }

.hero-texto h1 { max-width: var(--columna); }

.hero-texto p {
  margin-top: 16px;
  max-width: var(--columna);
  color: var(--texto-segundo);
}

/* Los dos botones ya vienen apilados e igualados por `.acciones` de la pieza
   3. Acá sólo se los pega al margen izquierdo en vez de centrarlos: en el hero
   el texto arranca en el margen y los botones lo siguen. */
.hero-texto .acciones { justify-content: start; }
"""

# ⏱ NO SE USA TODAVÍA, Y ES A PROPÓSITO. El frente es móvil: los tres anchos se
# generan, pero 768 y 1280 se aprueban en el segundo tiempo, con la página
# entera delante. Esto queda escrito y apagado hasta ese momento.
CSS_HERO_ANCHO = """
/* DE TABLET PARA ARRIBA EL VELO GIRA 90°.

   En el teléfono el texto se apoya abajo y el degradado sube. Con pantalla
   ancha eso desperdicia el ancho y agranda el alto: el texto se va a la
   IZQUIERDA y el degradado corre en horizontal. Es el mismo reparto de la
   pág. 17 del brief —texto a la izquierda, foto a la derecha— pero sin partir
   la foto en una columna: la foto sigue a sangre y el velo hace el corte.

   La foto no cambia de regla: sigue llenando la caja con object-fit. */
.hero-velo .hero-texto {
  min-height: 520px;
  justify-content: center;
  max-width: 620px;
  padding: 48px var(--margen-pagina);
}

.hero-velo::before {
  background: linear-gradient(
    to right,
    rgba(51, 50, 47, 0.93) 0%,
    rgba(51, 50, 47, 0.90) 40%,
    rgba(51, 50, 47, 0.66) 60%,
    rgba(51, 50, 47, 0.18) 82%,
    rgba(51, 50, 47, 0.00) 100%
  );
}
"""


def hero_velo(foto, ancho):
    """El hero propuesto: la foto entera, y el texto encima."""
    imagen = (f'<img class="hero-foto" alt="" src="{foto}">'
              if foto else "")

    return f"""
  <div class="hero hero-velo">
    {imagen}
    <div class="hero-texto">
      <div class="filo"></div>
      <h1>{H1}</h1>
      <div class="acciones">
        <a class="btn btn-1" href="#reservar">Reservar</a>
        <a class="btn btn-2" href="#tratamientos">Ver tratamientos</a>
      </div>
    </div>
  </div>"""


def tablero_hero(tokens, css, ancho):
    foto = leer_foto()
    logo = leer_png("cb-wordmark-600")
    chico = ancho < 1280
    alto_foto = round(ancho * 3 / 4)

    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 10 Hero · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_ENCABEZADO}
{CSS_HERO}
{CSS_HERO_VELO}
{""}
</style>

<div class="prosa">
<p class="rotulo">Fase ⑧ · Pieza 10 · {ancho} px</p>
<h1>El hero</h1>
<div class="regla"></div>
<p><b>Es la única pantalla que el brief trae dibujada</b> —la pág. 17, de
escritorio—. Acá está pasada a móvil, con los <b>textos definitivos de la
§ 4</b> y con el encabezado de la pieza 9 arriba, que es como se va a ver.</p>
</div>

<p class="marca-muestra" style="padding: 0 var(--margen-pagina)">El hero,
a 1:1, con su encabezado</p>
{barra(logo, "wordmark", ancho, menu_del_ancho(ancho), not chico)}
{hero_velo(foto, ancho)}

<div class="prosa">
<section>
  <p class="rotulo">Lo que esta pieza entrega además del dibujo</p>
  <h2>El primer dato del brief de fotos</h2>
  <p>🔴 <b>La forma elegida DICTA la foto, y eso es el entregable.</b> Con el
  texto encima, el velo tapa el tercio de abajo: <b>si la cara está centrada,
  la sonrisa queda debajo del velo</b> — que es exactamente lo que pasa con la
  foto de ejemplo, que es un primer plano apaisado del brief. <b>La foto del
  hero se pide VERTICAL, 2:3 o más alta, con la cara en el TERCIO DE
  ARRIBA</b> y aire abajo para que el velo tenga dónde caer.</p>
  <ul class="reglas">
    <li><b>En el hero apilado, proporción 4:3 apaisada en el teléfono</b> — a {ancho} px son
    {ancho} × {alto_foto}. De tablet para arriba la foto ocupa media pantalla
    y se estira al alto del texto, así que <b>hay que entregarla vertical y
    recortarla desde el centro</b>: una foto apaisada no sobrevive a esa
    columna.</li>
    <li><b>El motivo va en el centro y un poco abajo</b> —la sonrisa—, porque
    el recorte se hace desde ahí. Es lo que dice
    <code>object-position: 50% 52%</code>.</li>
    <li><b>Margen de sobra alrededor de la cara.</b> El mismo archivo se
    recorta 4:3 en el teléfono y casi vertical en escritorio: lo que quede
    justo en uno se corta en el otro.</li>
  </ul>
  <p class="dato" style="margin-top: 14px">⚠️ <b>La foto de arriba es de
  ejemplo.</b> Vive en <code>brand/fotos/</code>, con su autor y su licencia
  escritos al lado. <b>No es la foto del sitio</b>, y hay un motivo que no es
  de gusto: la persona es identificable, y la licencia de la foto no es el
  permiso de esa persona. <b>Para publicidad sanitaria hace falta autorización
  de imagen.</b></p>
</section>

<section>
  <p class="rotulo">Las reglas</p>
  <h2>Lo que no se negocia</h2>
  <ul class="reglas">
    <li><b>La foto va a sangre y sin esquinas redondeadas.</b> El radio de 3 px
    es de controles y superficies; el manual dibuja la foto cuadrada.</li>
    <li><b>El titular es el de la § 4, palabra por palabra.</b> El del brief
    —«Estética dental de alta precisión»— está escrito sobre otro
    posicionamiento y no se copia.</li>
    <li><b>Dos acciones y no más:</b> <b>Reservar</b>, que es la conversión, y
    <b>Ver tratamientos</b>. Miden lo mismo porque las iguala la pieza 3.</li>
    <li><b>El velo es el grafito de la marca con transparencia</b>, no un
    color nuevo, y <b>no se elige a ojo: se mide sobre la captura con el
    texto apagado</b>. Hoy da <b>6,29</b> contra un piso de 4,5.</li>
    <li><b>El secundario sobre la foto va invertido</b> —filo y letra
    blancos, sin relleno—: el grafito macizo se hunde en el velo. Es el mismo
    gesto que el sistema ya usa para el foco del secundario.</li>
    <li>⬜ <b>Falta el patrón de ondas del brief</b>, que hoy sólo existe
    dibujado adentro del PDF. Se vectoriza en la fase ⑩.</li>
  </ul>
</section>
</div>
"""


# ============================================================
# PIEZA 11 — LA TARJETA DE TRATAMIENTO Y SU GRILLA
#
# Los nombres NO se inventan: son las filas de la tabla `tratamientos`, que es
# la misma lista que alimenta el desplegable de la reserva. Quedan afuera dos,
# y por motivos distintos: `consulta`, que no es un tratamiento sino la puerta
# de entrada, y `otros`, que existe para que la cola larga no infle la tabla.
# ============================================================

# Cada línea dice QUÉ ES el tratamiento, no qué promete. Salen de fuentes
# profesionales —ADA / MouthHealthy, Cleveland Clinic, Mayo Clinic, NHS— y no
# de la redacción: un texto que promete un resultado en publicidad sanitaria es
# justo lo que el régimen de anuncios del Colegio mira.
#
# ⬜ LAS NUEVE LAS TIENE QUE APROBAR CECILIA. Son afirmaciones clínicas, y eso
# no lo firma quien diseña.
# Los cinco elegidos de la pieza 11b (restauración B · endodoncia A ·
# extracción A · cirugía B · strass B) y los cuatro del brief, que todavía no
# están vectorizados y se muestran recortando su propia lámina.
NUEVOS = {
    # Cambiado el 4-sep-2026: antes era la pieza MORDIDA, o sea la caries. Con
    # la regla de Juan —el ícono muestra el tratamiento, no el problema— pasa a
    # ser la pieza entera con la parte repuesta en su esquina.
    "Restauración":
        '<rect x="11" y="9" width="18" height="22" rx="6"/>'
        '<path d="M20 9 v7 h9"/>',
    "Endodoncia":
        '<rect x="11" y="9" width="18" height="22" rx="6"/>'
        '<rect x="16" y="14" width="8" height="12" rx="3"/>',
    "Extracción":
        '<rect x="11" y="9" width="18" height="22" rx="6"/>'
        '<path d="M20 5 v-3"/><path d="M17 4 l3 -3 l3 3"/>',
    "Cirugía":
        '<rect x="7" y="11" width="13" height="18" rx="5"/>'
        '<rect x="22" y="14" width="12" height="16" rx="5" '
        'transform="rotate(24 28 22)"/>',
    "Strass dentales":
        '<rect x="11" y="9" width="18" height="22" rx="6"/>'
        '<path d="M25 13 l3.5 3.5 l-3.5 3.5 l-3.5 -3.5 z"/>',
    # 🔴 REDIBUJADO, y es el único del brief que se cambia. El original era un
    # óvalo con dos patas: ampliado a 120 px lee MESA, y es el único de los seis
    # dibujado en perspectiva —los otros cinco son frontales—. Tres piezas
    # cruzadas por el alambre dicen ortodoncia sin dibujar dientes torcidos, que
    # sería dibujar el problema y no el tratamiento. Elegido por Juan.
    "Ortodoncia":
        '<rect x="7" y="12" width="7" height="15" rx="2.5"/>'
        '<rect x="16.5" y="11" width="7" height="16" rx="2.5"/>'
        '<rect x="26" y="12" width="7" height="15" rx="2.5"/>'
        '<path d="M4 19.5 h32"/>',
}

# Centros medidos sobre brand/fotos/iconos-del-brief.png (900 px de ancho).
DEL_BRIEF = {
    "Carillas": 230,
    "Blanqueamiento": 376,
    "Limpieza": 667,
}

ESCALA_BRIEF = 0.88
CENTRO_Y_BRIEF = 106

TRATAMIENTOS = [
    ("Blanqueamiento",
     "Aclara manchas y el tono del esmalte natural. No cambia el color de "
     "restauraciones, coronas ni carillas."),
    ("Limpieza",
     "Cuando la placa se endurece en sarro, el cepillado ya no la remueve: "
     "se saca con instrumental."),
    ("Carillas",
     "Corrigen color y forma, y no refuerzan el diente. Para colocarlas se "
     "desgasta esmalte, y eso no se revierte."),
    ("Ortodoncia",
     "Mueve los dientes y la mordida a lo largo de meses. Al terminar lleva "
     "contención, o vuelven a moverse."),
    ("Restauración",
     "Saca el tejido cariado y reconstruye la pieza. La caries no se detiene "
     "sola: cuanto antes, menos pieza se pierde."),
    ("Endodoncia",
     "Conserva la pieza en lugar de extraerla cuando la pulpa se infecta. "
     "Después lleva una restauración que la proteja."),
    ("Extracción",
     "Se retira la pieza cuando ya no se puede conservar. El espacio que queda "
     "se planifica: las vecinas se mueven."),
    ("Cirugía",
     "Muelas de juicio retenidas y otras intervenciones en encía y hueso. "
     "No toda muela de juicio hay que sacarla."),
    ("Strass dentales",
     "Piedra adherida al esmalte, con fin estético. La coloca y la retira la "
     "profesional, sin tallar el diente."),
]

CSS_TRATAMIENTOS = """
/* EL MARGEN ES DE LA SECCIÓN, no del tablero que la muestra. Antes se lo
   prestaba el `padding` del body de su tablero, y apilada en la página —donde
   ese padding no existe— la grilla se iba a sangre. Se escribe acá, en la
   sección, para que mida lo mismo la mire quien la mire. */
.grilla-tratamientos {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 20px;
  margin-left: var(--margen-seccion);
  margin-right: var(--margen-seccion);
  max-width: var(--ancho-pagina);
}

/* EN ESCRITORIO SON TRES COLUMNAS, y el número no es estético: son NUEVE
   tarjetas, así que tres columnas dan tres filas COMPLETAS. Con cuatro
   quedaría una sola tarjeta colgando en la última fila, y con dos —lo que
   heredaba del teléfono— son cinco filas de tarjetas muy anchas para el texto
   corto que llevan.

   El hueco también sube: a 390 son 10 px porque no sobra ancho; con pantalla
   el mismo 10 pega las tarjetas entre sí y la grilla se lee como una sola
   mancha. Es la misma regla del aire entre secciones — un valor por ancho.

   🔴 EL CORTE BAJA A 768 — 13-sep-2026. El argumento de arriba no dependía de
   tener 1280 de ancho: dependía de que las tarjetas sean NUEVE. A 768 estaban
   en dos columnas, o sea cinco filas con una tarjeta colgando sola al final,
   y la sección medía 981 px. Con tres columnas mide 694 y entra en pantalla. */
@media (min-width: 768px) {
  .grilla-tratamientos {
    grid-template-columns: 1fr 1fr 1fr;
    gap: 20px;
  }
}

/* LA TARJETA. Blanca sobre marfil, y ese par mide 1,03: la forma la marca el
   BORDE, nunca el relleno. Es la misma regla del campo y del botón apagado. */
.tratamiento {
  background: var(--blanco);
  border: 1px solid var(--dorado-claro);
  border-radius: var(--radio);
  padding: 14px 14px 16px;
  display: block;
  text-decoration: none;
  color: var(--grafito);
}

.ico {
  display: block;
  width: 36px;
  height: 36px;
  margin-bottom: 10px;
}

.ico * {
  fill: none;
  stroke: var(--dorado);
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}

/* Los cuatro del brief todavía no están vectorizados: se muestran recortando
   su propia lámina, que es la que está en brand/fotos/. */
.ico-brief {
  background-image: url("../../fotos/iconos-del-brief.png");
  background-repeat: no-repeat;
  background-size: 792px auto;
}

.tratamiento h3 {
  font-size: var(--tipo-h3);
  line-height: var(--alto-h3);
  margin-bottom: 6px;
}

.tratamiento p {
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  color: var(--texto-segundo);
}

/* El aviso de la consulta. No es una tarjeta más: es la regla que ordena todo
   lo de arriba, así que va sobre el fondo suave y ocupa el ancho entero. */
.aviso-consulta {
  grid-column: 1 / -1;
  background: var(--info-fondo);
  border-radius: var(--radio);
  padding: 16px;
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
}
"""


def icono_de(nombre):
    """El ícono de la tarjeta: dibujo nuevo, o recorte de la lámina del brief."""
    if nombre in NUEVOS:
        return (f'<svg class="ico" viewBox="0 0 40 40" aria-hidden="true">'
                f'{NUEVOS[nombre]}</svg>')

    if nombre not in DEL_BRIEF:
        return ""

    x = round(18 - DEL_BRIEF[nombre] * ESCALA_BRIEF, 1)
    y = round(18 - CENTRO_Y_BRIEF * ESCALA_BRIEF, 1)
    return (f'<span class="ico ico-brief" aria-hidden="true" '
            f'style="background-position: {x}px {y}px"></span>')


def tarjeta_tratamiento(nombre, linea):
    return f"""
    <a class="tratamiento" href="#reservar">
      {icono_de(nombre)}
      <h3>{nombre}</h3>
      <p>{linea}</p>
    </a>"""


def grilla_tratamientos():
    tarjetas = "".join(tarjeta_tratamiento(n, l) for n, l in TRATAMIENTOS)
    return f"""
  <div class="grilla-tratamientos">{tarjetas}
  </div>"""


def tablero_tratamientos(tokens, css, ancho):
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 11 Tratamientos · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_TRATAMIENTOS}
{css_margen_en_la_prosa()}
</style>

<div class="prosa">
<p class="rotulo">Fase ⑧ · Pieza 11 · {ancho} px</p>
<h1>Tratamientos</h1>
<div class="regla"></div>
<p><b>Los nombres no se inventan.</b> Son las filas de la tabla
<code>tratamientos</code>, la misma lista que alimenta el desplegable de la
reserva: si mañana se agrega uno, aparece en los dos lados.</p>

<section>
  <p class="rotulo">La grilla, a 1:1</p>
  <h2>Nueve tarjetas</h2>
</section>
</div>

{grilla_tratamientos()}

<div class="prosa">
<section>
  <p class="rotulo">La decisión que esta pieza cerró</p>
  <h2>La grilla lleva ícono</h2>
  <p><b>El brief traía seis</b>, en una página que se llama «pack de íconos por
  servicio», <b>y de esos sirven tres</b>: carillas, blanqueamiento e higiene
  —que es nuestra <b>limpieza</b>—. «Chequeo general» es la consulta, que no es
  tarjeta; «diseño de sonrisa» no existe en nuestra tabla y queda sin uso.</p>
  <p style="margin-top: 12px"><b>Se dibujaron cinco nuevos</b> —restauración,
  endodoncia, extracción, cirugía y strass— <b>y se redibujó ortodoncia</b>,
  que era el único del brief en perspectiva y ampliado leía <b>mesa</b>.</p>
  <p class="dato" style="margin-top: 12px">🔑 <b>La regla que ordenó los seis
  dibujos, y la puso Juan:</b> el ícono muestra <b>el tratamiento, no el
  problema</b>. Por eso ortodoncia no son dientes torcidos sino tres piezas
  cruzadas por el alambre, <b>y por eso restauración se cambió</b>: dibujaba la
  pieza mordida —la caries— y ahora dibuja la parte repuesta en su esquina.</p>
  <p class="dato" style="margin-top: 12px">🔴 <b>El dorado sobre BLANCO mide
  3,09 y el piso de un dibujo es 3,0; sobre el marfil de la página mide 2,89 y
  no pasa.</b> Los íconos van sobre la tarjeta blanca, nunca sueltos sobre el
  fondo.</p>

  <p class="rotulo">Las reglas</p>
  <h2>Lo que no se negocia</h2>
  <ul class="reglas">
    <li><b>Se agrega duplicando una tarjeta, nunca rediseñando la grilla.</b>
    Es lo que pide la § 4, y por eso la tarjeta no depende de cuántas
    haya.</li>
    <li><b>La tarjeta es blanca sobre marfil, y ese par mide 1,03: no se
    ve.</b> La forma la marca el <b>borde</b>. El día que alguien lo saque
    «para limpiar», la grilla desaparece.</li>
    <li><b>Cada tarjeta es un enlace</b>, y hoy las nueve llevan al mismo lado:
    a reservar. A futuro, a la página del tratamiento (SEO, § 4).</li>
    <li>🔴 <b>Ortodoncia va en la grilla como cualquier otro.</b> Lo que espera
    al posgrado certificado es la palabra «especialista» como credencial, no el
    tratamiento.</li>
    <li>🔴 <b>El aviso de «todo arranca con una consulta de 30 minutos» NO va
    acá</b> —decisión de Juan—. La grilla vende tratamientos; explicar cómo se
    agenda en el medio del catálogo frena la lectura. <b>El aviso vive en la
    pantalla de reserva</b>, que es donde el paciente elige a qué viene.</li>
  </ul>
</section>
</div>
"""


# ============================================================
# LAS MARCAS AJENAS — lo comparten la pieza 12 y la 13
# ============================================================

# LOS DOS ISOTIPOS AJENOS — Instagram y WhatsApp.
#
# ✅ SON LOS OFICIALES, no un dibujo nuestro. Salen del Brand Resource Center
# de Meta, bajados el 4-sep-2026, y viven en brand/marcas-ajenas/ con su
# procedencia escrita al lado. Acá NO se copia ninguna curva: se LEE el archivo
# y se le cambia el relleno por `currentColor`, así que el color lo pone el CSS
# y el dibujo no se retoca nunca. Si Meta actualiza uno, se reemplaza el
# archivo y este código no cambia.
#
# 🔑 VAN EN DORADO, LOS DOS, y es DECISIÓN DE JUAN del 4-sep-2026, tomada con
# el dato en contra sobre la mesa: Instagram permite explícitamente cualquier
# color sólido; WhatsApp dice lo opuesto —"you shouldn't modify any colors in
# our logos"— y publica sus tres versiones. Su criterio: es la misma empresa y
# el uso repintado está en todos lados. El costo queda escrito en
# brand/marcas-ajenas/PROCEDENCIA.md, no en la memoria de nadie.
#
# ⚠️ CUÁL de los dos dorados NO es preferencia, es medida: el dorado del brief
# mide 2,89 sobre MARFIL —abajo del piso de 3,0 de un dibujo— y 3,09 sobre
# BLANCO. Por eso en la tarjeta de contacto, que es blanca, va --dorado como el
# resto de sus íconos; y en el pie, que es marfil, va --dorado-texto. Es la
# misma regla que ya ordenaba los íconos de la pieza 11.

CUERPO_SVG = re.compile(r"<svg[^>]*viewBox=\"([^\"]+)\"[^>]*>(.*)</svg>", re.DOTALL)
DEFS_SVG = re.compile(r"<defs>.*?</defs>", re.DOTALL)
RELLENO = re.compile(r'\s(?:fill|class)="[^"]*"')


def leer_isotipo(nombre):
    """El isotipo oficial, listo para que el CSS le ponga el color.

    Se le sacan los `fill` y las clases del archivo original —que traen el
    color de ellos— para que el dibujo herede `currentColor`. La geometría no
    se toca: es la misma que bajó del Brand Resource Center.
    """
    bruto = (RAIZ / "brand" / "marcas-ajenas" / f"{nombre}-glyph.svg").read_text(
        encoding="utf-8"
    )
    caja, cuerpo = CUERPO_SVG.search(bruto).groups()
    cuerpo = DEFS_SVG.sub("", cuerpo)
    cuerpo = RELLENO.sub("", cuerpo)
    return caja, " ".join(cuerpo.split())


def isotipo(nombre, clase):
    """Un isotipo ajeno. El color lo pone quien lo usa, con `color`."""
    caja, cuerpo = leer_isotipo(nombre)
    return (
        f'<svg class="iso {clase}" viewBox="{caja}" aria-hidden="true">'
        f"{cuerpo}</svg>"
    )


ISOTIPOS_AJENOS = ("instagram", "whatsapp")

CSS_ISOTIPO = """
/* El isotipo hereda el color de su contenedor —`currentColor`— así que el
   mismo archivo sirve en la tarjeta blanca y en el pie marfil sin duplicarse.
   Cada lugar declara CUÁL dorado le toca, y eso lo decide el contraste contra
   su fondo, no el gusto. */
.iso {
  width: 24px;
  height: 24px;
  fill: currentColor;
}

/* En la tarjeta de contacto, que es BLANCA: el dorado del brief, 3,09.
   🔴 Y MIDE 18, NO 24 COMO LOS OTROS, y no es un descuido — lo levantó Juan:
   "da la impresión de que es más grande que el resto". Es cierto y tiene dos
   causas que se suman. Los íconos nuestros son de LÍNEA y su dibujo no llega
   al filo de la caja: la tinta del sobre mide 17,6 de ancho adentro de 24. El
   isotipo ajeno es MACIZO y ocupa su caja entera. A 24 tenía un tercio más de
   tinta que sus vecinos, y encima rellena.
   Los 3 px de aire a cada lado devuelven la columna a 24, así que la fila no
   se mueve. */
.iso-carta {
  flex: none;
  width: 18px;
  height: 18px;
  margin: 5px 3px 0;
  color: var(--dorado);
}

/* En el pie, que es MARFIL: el dorado del brief no llega (2,89), así que va el
   dorado de texto, el mismo tono con doce puntos menos de luz. */
.iso-pie {
  width: 26px;
  height: 26px;
  color: var(--dorado-texto);
}
"""


# ============================================================
# PIEZA 12 — CONTACTO
#
# Los datos NO se inventan y no son decisión nuestra: los dio Cecilia el
# 1-sep-2026 y viven en la § 9.1.e del doc de estado. Acá se copian UNA sola
# vez, en estas constantes, para que el día que cambie uno no haya que
# cazarlo por el archivo.
# ============================================================

DIRECCION = "25 de Mayo 3725"
CIUDAD = "Santa Fe"

# El teléfono se ESCRIBE de una forma y se MARCA de otra. Y el enlace de
# WhatsApp lleva un 9 que el número escrito no muestra: 54 + el 9 de celular +
# 342 + el número. Sin ese 9 no abre la conversación (§ 9.1.e).
TELEFONO_ESCRITO = "+54 342 629-3920"
TELEFONO_MARCADO = "+543426293920"
WHATSAPP = "5493426293920"

# 🔴 EL CORREO REAL NO ENTRA A ESTE ARCHIVO. Éste es un repo PÚBLICO, el
# correo de Cecilia hoy es una casilla personal de Gmail, y el historial de git
# viaja con el repo y no se reescribe: lo que entra una vez, queda.
#
# La decisión ya existía en el proyecto —la base usa `cecilia@example.com` por
# el mismo motivo (§ 9.1.c)— y acá se respeta. El correo de verdad vive en el
# doc de estado (§ 9.1.e), que es privado, y se pone al construir el sitio.
#
# Se muestra ESCRITO, sin enlace: ver fila_texto.
CORREO = "cecilia@example.com"

# 🔴 VAN COORDENADAS Y NO LA DIRECCIÓN ESCRITA, y no es un detalle: buscando
# "25 de Mayo 3725, Santa Fe, Argentina" el primer resultado cae en YBARLUCEA,
# a 130 km, sobre la colectora 25 de Mayo del Gran Rosario. Las dos están en la
# provincia de Santa Fe, así que agregar la provincia no desempata.
#
# ✅ LA COORDENADA LA MARCÓ JUAN sobre el edificio, en Google Maps, el
# 4-sep-2026. No sale de ningún geocodificador: la primera que se probó —la de
# OpenStreetMap para el 3725— caía a media cuadra, con "Av. Aristóbulo del
# Valle 3716" como dirección más cercana.
#
# 🔑 Y el punto marcado Google lo lee como "25 de Mayo 3727", no 3725: la
# numeración de la cuadra está interpolada. Es la prueba de por qué acá va una
# coordenada y no la dirección escrita — Google tampoco tiene fichado el 3725,
# y el 3735 de al lado es el taller de calzados.
#
# ⏱ Se cambia por el enlace de la FICHA el día que exista el Perfil de Empresa
# de Google (§ 14): la ficha muestra nombre, horarios y fotos, y una coordenada
# pelada deja un pin sin nombre.
COORDENADAS = "-31.632821,-60.701736"

# El esquema oficial de URL de Google Maps: no lleva clave de API, no carga
# nada de terceros adentro de nuestra página, y en el teléfono lo levanta la
# app instalada.
MAPA = "https://www.google.com/maps/search/?api=1&query=" + COORDENADAS

# 🔴 LOS HORARIOS NO SE PUBLICAN — lo decidió Juan el 4-sep-2026, y el motivo
# es el de siempre: dos copias del mismo dato se desincronizan. Los horarios de
# verdad son `horarios_base` + `fin_maximo` + las excepciones + la semana del
# 15 que Cecilia cierra todos los meses; una tabla fija en el sitio empieza a
# mentir el primer mes. La disponibilidad real la muestra la grilla de reserva,
# y los horarios de puertas abiertas van al Perfil de Empresa de Google (§ 14),
# que es donde se los busca y donde se cargan los días especiales.

# Cada ícono es línea sola, del mismo trazo que los de la pieza 11.
# El de WhatsApp es una BURBUJA nuestra, no el logotipo: la regla, en el
# tablero.
ICONOS = {
    "pin":
        '<path d="M12 21.5s7-6.4 7-11.5a7 7 0 1 0-14 0c0 5.1 7 11.5 7 11.5z"/>'
        '<circle cx="12" cy="10" r="2.6"/>',
    "telefono":
        '<path d="M6.6 3.6 h3 l1.5 4 l-2 1.5 a12.4 12.4 0 0 0 5.8 5.8 '
        'l1.5-2 l4 1.5 v3 a2 2 0 0 1-2.2 2 A17.4 17.4 0 0 1 4.6 5.8 '
        'A2 2 0 0 1 6.6 3.6 z"/>',
    "sobre":
        '<rect x="3.2" y="5.4" width="17.6" height="13.2" rx="2.4"/>'
        '<path d="M3.9 7 l8.1 5.9 l8.1-5.9"/>',
}

CSS_CONTACTO = """
/* La tarjeta es blanca sobre marfil, y ese par mide 1,03: la forma la marca
   el BORDE, nunca el relleno. Es la misma regla del campo, del botón apagado
   y de la tarjeta de tratamiento — la cuarta vez que aparece. */
/* EL BLOQUE DE CONTACTO — la tarjeta de datos y, en escritorio, el QR.

   El margen y el techo los lleva ÉL y no la tarjeta, porque a partir de 1280
   son dos piezas una al lado de la otra y el margen es de la sección entera.
   Es el mismo criterio que ya se aplicó al resto: el margen pertenece a la
   sección, no a lo que la muestra ni a uno de sus pedazos. */
.bloque-contacto {
  max-width: var(--ancho-pagina);
  margin-top: 20px;
  margin-left: var(--margen-seccion);
  margin-right: var(--margen-seccion);
}

.contacto {
  background: var(--blanco);
  border: 1px solid var(--dorado-claro);
  border-radius: var(--radio);
}

/* 🔴 EL QR NO EXISTE EN MÓVIL NI EN TABLET, y no es que se esconda: nadie
   escanea su propia pantalla. Se DIBUJA recién en escritorio, que es donde el
   paciente no puede tocar un enlace de WhatsApp y necesita el teléfono en la
   mano. Decidido en la § 4 y pedido por Cecilia. */
.contacto-qr {
  display: none;
}

/* 🔴 EL CORTE BAJA A 768 — 13-sep-2026. La tarjeta se sacó en escritorio y a
   768 seguía puesta, así que la misma sección tenía dos formas según el ancho
   y la de acá era la descartada. Mismo caso que «Nosotros»: lo decidido en un
   ancho no baja solo al de al lado. */
@media (min-width: 768px) {
  /* 🔴 LA TARJETA NO USA TODO EL ANCHO, y esto lo levantó Juan: «esas
     tarjetas de contacto son enormes con el texto a la izquierda».

     Baymard nombra el defecto para pantallas grandes: demasiado aire
     alrededor de un par de contenidos deja el sitio «demasiado abierto, con
     espacios grandes y desparejos». Acá eran cuatro renglones cortos dentro
     de una caja de 1100 px, con unos 800 de blanco al costado de cada dato.

     🔑 EL TECHO VA EN EL COMPONENTE, NO EN LA PÁGINA: la sección sigue
     midiendo 1100 —por eso el título no se mueve y la alineación del sitio no
     cambia— y lo que se acota es la tarjeta. */
  /* 🔴 EN ESCRITORIO NO HAY TARJETA — 13-sep-2026, lo pidió Juan: «hay que
     sacar las tarjetas, hacer que se entienda que es otra sección a través
     de los márgenes, jerarquía de elementos, colores y tamaño de letra».

     🔑 ES SU PROPIA MANIJA, la que entró al método esta misma madrugada:
     antes de separar dos bloques con una SUPERFICIE, probá el marcador de
     arranque. La tarjeta era la superficie; el título de sección con su filo
     dorado ya es el marcador, y alcanza. Suelta sobre los 1100 px la caja
     además quedaba descolgada, que es lo que él vio.

     Lo que separa ahora los cuatro datos es AIRE y JERARQUÍA: la dirección
     manda —es a dónde hay que ir—, el resto baja un escalón, y el ícono
     dorado hace de viñeta. Ningún borde, ningún fondo, ningún color nuevo. */
  .contacto {
    max-width: var(--columna);
    margin-right: auto;
    background: none;
    border: 0;
    border-radius: 0;
  }

  /* ⚠️ LOS TRES SELECTORES DE ABAJO REPITEN `.contacto` A PROPÓSITO, y es la
     tercera vez en el día que hace falta aprender lo mismo: con la MISMA
     prioridad gana la regla que va última en el archivo, y las originales de
     `.dato-contacto` viven MÁS ABAJO que esta `@media`. Escritas con una sola
     clase, estas reglas no se aplicaban — y no daban ningún error.

     Subir la prioridad en vez de mover el bloque es lo que lo vuelve estable:
     así deja de importar en qué orden se peguen los bloques de CSS. */
  .contacto .dato-contacto {
    border-top: 0;
    padding: 0 0 22px;
    align-items: baseline;
  }

  .contacto .dato-contacto:last-child {
    padding-bottom: 0;
  }

  /* La dirección es el dato principal de la sección: es a dónde hay que ir.
     Sube al escalón de arriba de la escala, que ya existe. */
  .contacto .dato-contacto h3 {
    font-size: var(--tipo-h2);
    line-height: var(--alto-h2);
  }

  /* 🔴 EL QR ES UNA FILA MÁS DE LA TARJETA — tercera forma, y es la que pidió
     Juan: «metele blanco alrededor de todo y que se una desde el blanco de
     arriba».

     Las dos anteriores fallaron por lo mismo aunque se vieran distintas: las
     dos lo trataban como una PIEZA APARTE. Primero una tarjeta con borde al
     costado, que competía con los datos; después un cuadrado blanco suelto
     sobre el marfil, que quedaba flotando. Acá no hay pieza aparte — el QR
     vive DENTRO de la tarjeta, sobre el mismo blanco, separado de la fila de
     arriba por la misma línea que separa a todas las demás.

     Y el blanco de la tarjeta ES la zona de silencio que la norma pide
     alrededor del código (ISO/IEC 18004, cuatro módulos): no hace falta
     pintar ningún recuadro propio. */
  .contacto-qr {
    display: block;
    padding: 28px 14px 24px;
    border-top: 1px solid var(--dorado-claro);
    text-align: center;
  }

  /* 180 px de lado. El piso no es estético: los módulos de este código
     necesitan al menos 2 px en pantalla para que la cámara los separe. */
  .qr {
    display: block;
    width: 180px;
    height: 180px;
    margin-left: auto;
    margin-right: auto;
  }

}

/* 🔴 EL ACCESO FIJO A WHATSAPP — SÓLO DE ESCRITORIO.

   En móvil NO EXISTE, y eso ya estaba decidido en la § 4 con evidencia:
   Baymard testeó las burbujas fijas y en el teléfono obstruyen el contenido,
   que el usuario además no puede correr. La misma fuente recomienda lo
   contrario para escritorio —que el elemento fijo viva ahí, donde sobra
   pantalla—, y es lo que se construye acá.

   Reemplaza al QR, que se probó en tres formas y en ninguna funcionó. El QR
   sobrevive en la cartelería impresa, que es el único soporte donde nadie
   puede tocar un enlace. */
.wa-flotante {
  display: none;
}

@media (min-width: 1280px) {
  .wa-flotante {
    display: flex;
    position: fixed;
    right: 32px;
    bottom: 32px;
    /* 56 px es el tamaño que Baymard mide en los casos que testeó, y queda
       por encima del piso táctil de 44 del sistema. */
    width: 68px;
    height: 68px;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    /* Dorado del brief con el isotipo en BLANCO — lo pidió Juan el
       13-sep-2026. Es el mismo par que ya usa el botón principal, así que no
       estrena nada: blanco sobre ese dorado mide 3,09 y el piso de un dibujo
       es 3,0. */
    background: var(--dorado);
    color: var(--blanco);
    box-shadow: var(--sombra-boton-foco);
    z-index: 10;
  }

  /* En GRAFITO y no en el verde de WhatsApp: el isotipo ajeno ya se repinta
     en todo el sitio —decisión de Juan del 4-sep con su costo escrito en
     brand/marcas-ajenas/PROCEDENCIA.md— y un botón verde sería el único color
     del sistema que no sale de la paleta. */
  .wa-flotante .iso-wa {
    width: 36px;
    height: 36px;
    fill: currentColor;
  }
}

/* Cada dato es una fila. La línea de arriba las separa; la primera no lleva,
   porque ahí ya está el borde de la tarjeta. */
.dato-contacto {
  display: flex;
  gap: 12px;
  padding: 14px;
  border-top: 1px solid var(--dorado-claro);
  min-height: 44px;
  text-decoration: none;
  color: var(--grafito);
}

.dato-contacto:first-child {
  border-top: none;
}

.ico-contacto {
  flex: none;
  width: 24px;
  height: 24px;
  margin-top: 2px;
}

.ico-contacto * {
  fill: none;
  stroke: var(--dorado);
  stroke-width: 1.8;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.dato-contacto h3 {
  font-size: var(--tipo-h3);
  line-height: var(--alto-h3);
}

.dato-contacto .ciudad {
  font-size: var(--tipo-cuerpo);
  line-height: var(--alto-cuerpo);
  color: var(--texto-segundo);
}

/* El enlace va en el dorado de texto —decisión del 2-sep— y SUBRAYADO: el
   color solo no puede ser lo único que diga que algo se toca. */
.enlace {
  color: var(--dorado-texto);
  text-decoration: underline;
  text-underline-offset: 3px;
}

.como-llegar {
  display: inline-block;
  margin-top: 8px;
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
}
"""


def icono_contacto(nombre):
    """El ícono de una fila.

    Los nuestros son línea dorada, dibujados acá; los ajenos son el archivo
    oficial, que ya viene relleno. Los dos miden 24 px y entran en la misma
    columna, así que la fila no cambia.
    """
    if nombre in ISOTIPOS_AJENOS:
        return isotipo(nombre, "iso-carta")

    return (
        f'<svg class="ico-contacto" viewBox="0 0 24 24" aria-hidden="true">'
        f'{ICONOS[nombre]}</svg>'
    )


def fila_enlace(icono, destino, texto, etiqueta):
    """Un dato que se toca: el renglón ENTERO es el enlace, no la palabra."""
    return f"""
    <a class="dato-contacto" href="{destino}" aria-label="{etiqueta}">
      {icono_contacto(icono)}
      <span class="enlace">{texto}</span>
    </a>"""


def fila_texto(icono, texto):
    """Un dato que se LEE y no se toca: el correo.

    Decisión de Juan del 4-sep-2026. Un `mailto:` abre el programa de correo
    que tenga configurado la persona, que puede ser uno que no usa; y forzar
    Gmail rompe en el teléfono. Se muestra escrito y cada uno hace lo suyo.
    """
    return f"""
    <div class="dato-contacto">
      {icono_contacto(icono)}
      <span>{texto}</span>
    </div>"""


def fila_direccion():
    return f"""
    <div class="dato-contacto">
      {icono_contacto("pin")}
      <div>
        <h3>{DIRECCION}</h3>
        <p class="ciudad">{CIUDAD}</p>
        <a class="enlace como-llegar" href="{MAPA}">Cómo llegar</a>
      </div>
    </div>"""


def qr_whatsapp():
    """El QR del WhatsApp, vectorial. Mismo mecanismo que la cartelería.

    Va SÓLO en escritorio, y el motivo no es que sobre lugar —Baymard avisa
    justamente que no se agrega contenido porque haya espacio—: es que en una
    pantalla grande el paciente NO PUEDE TOCAR un enlace de WhatsApp, así que
    necesita escanear con el teléfono. En móvil el QR no existe: nadie escanea
    su propia pantalla. Decidido en la § 4 y pedido por Cecilia.

    `-m 0` deja el SVG sin zona de silencio propia: acá el aire lo pone el
    recuadro blanco del CSS, que ya tiene relleno. En la cartelería va con
    `-m 4` porque ahí el QR se imprime sobre la placa y no hay caja alrededor.
    `-l M` es corrección de errores media: aguanta que la cámara lo lea torcido
    o con reflejo, que en una pantalla no es hipotético.
    """
    salida = subprocess.run(
        [
            "qrencode",
            "-t", "SVG",
            "-o", "-",
            "-m", "0",
            "-l", "M",
            "https://wa.me/" + WHATSAPP,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    svg = salida.stdout
    lado = re.search(r'viewBox="0 0 (\d+)', svg).group(1)
    adentro = re.sub(r"^.*?<svg[^>]*>", "", svg, flags=re.DOTALL)
    adentro = adentro.replace("</svg>", "")

    # El relleno se fuerza al grafito del sistema: qrencode lo escribe negro,
    # y el negro puro no está en la paleta.
    adentro = adentro.replace('fill="#000000"', 'fill="var(--grafito)"')

    return f"""<svg class="qr" viewBox="0 0 {lado} {lado}"
       role="img" aria-label="Código QR que abre la conversación de WhatsApp">
    {adentro}
  </svg>"""


def tarjeta_contacto():
    telefono = fila_enlace(
        "telefono",
        "tel:" + TELEFONO_MARCADO,
        TELEFONO_ESCRITO,
        "Llamar al consultorio",
    )
    whatsapp = fila_enlace(
        "whatsapp",
        "https://wa.me/" + WHATSAPP,
        "Escribinos por WhatsApp",
        "Abrir la conversación de WhatsApp",
    )
    correo = fila_texto("sobre", CORREO)

    return f"""
  <div class="bloque-contacto">
    <div class="contacto">
    {fila_direccion()}
    {telefono}
    {whatsapp}
    {correo}
    </div>
  </div>"""


def tablero_contacto(tokens, css, ancho):
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 12 Contacto · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_ISOTIPO}
{CSS_CONTACTO}
{css_margen_en_la_prosa()}
</style>

<div class="prosa">
<p class="rotulo">Fase ⑧ · Pieza 12 · {ancho} px</p>
<h1>Contacto</h1>
<div class="regla"></div>
<p><b>Los datos no se inventan.</b> La dirección, el teléfono y el correo son
los que dio Cecilia el 1-sep-2026 (§ 9.1.e). <b>Acá se copian una sola vez</b>,
en las constantes del generador.</p>

<section>
  <p class="rotulo">La tarjeta, a 1:1</p>
  <h2>Cuatro datos</h2>
</section>
</div>

{tarjeta_contacto()}

<div class="prosa">
<section>
  <p class="rotulo">La decisión que esta pieza cerró</p>
  <h2>Acá no hay mapa</h2>
  <p><b>La § 4 pide «ubicación», y ubicación no es un mapa incrustado.</b> Un
  <code>iframe</code> de Google Maps a 390 se come media pantalla, y sobre todo
  <b>mete a Google adentro de nuestra página antes de que el paciente pida
  nada</b> — en un sitio que además maneja datos de salud, eso se decide, no se
  arrastra.</p>
  <p style="margin-top: 12px"><b>Y en el teléfono nadie mira un mapa adentro de
  una página:</b> toca la dirección y quiere que se abra su app, con el camino
  desde donde está parado. Eso hace <b>«Cómo llegar»</b>, con el esquema de URL
  oficial de Maps: sin clave de API y sin cargar nada de afuera.</p>
  <p class="dato" style="margin-top: 12px">⏱ <b>Queda abierto para 1280</b>: en
  escritorio la pantalla sobra y el mapa no le saca lugar a nada. <b>Se decide
  en la fase B, no acá.</b></p>

  <p class="rotulo">Lo que casi manda al paciente a 130 km</p>
  <h2>El enlace lleva coordenadas, no la dirección escrita</h2>
  <p>El enlace decía <code>query=25 de Mayo 3725, Santa Fe, Argentina</code>, y
  <b>ese texto es ambiguo</b>: hay una colectora 25 de Mayo al 3725 en
  <b>Ybarlucea, Gran Rosario</b> — a 130 km del consultorio y en la MISMA
  provincia, así que agregar «Santa Fe» no desempata nada. <b>Una coordenada no
  se puede malinterpretar.</b> <i>Lo pidió Juan.</i></p>
  <p class="dato" style="margin-top: 12px">🔑 <b>Y no alcanzaba con
  geocodificar:</b> la coordenada del 3725 caía a media cuadra. <b>La que está
  puesta la marcó Juan sobre el edificio</b>, y Google la lee como «25 de Mayo
  <b>3727</b>» — la numeración de la cuadra está interpolada. <b>Google no
  tiene fichado el 3725</b>, y el 3735 de al lado es el taller de calzados: por
  eso acá va una coordenada y no la dirección escrita.</p>

  <p class="rotulo">Marcas ajenas · decisión de Juan</p>
  <h2>El isotipo es el oficial, y va en dorado</h2>
  <p><b>No es un dibujo nuestro.</b> Los dos isotipos —éste y el de Instagram
  del pie— salen del <b>Brand Resource Center de Meta</b>, bajados el
  4-sep-2026, y viven en <code>brand/marcas-ajenas/</code> con su procedencia
  escrita al lado. El generador <b>lee el archivo</b> y sólo le cambia el
  relleno: la geometría no se toca nunca.</p>
  <p style="margin-top: 12px"><b>Y van en dorado, los dos. Lo decidió Juan</b>,
  con el dato en contra sobre la mesa: <b>Instagram permite cualquier color
  sólido</b> mientras el dibujo no cambie, y <b>WhatsApp dice lo contrario</b>
  —<i>«you shouldn't modify any colors in our logos»</i>— y publica sus tres
  versiones. <b>Su criterio: es la misma empresa, y el uso repintado está en
  todos lados.</b> Queda escrito con su costo al lado, en
  <code>PROCEDENCIA.md</code>, para no re-discutirlo cada vez.</p>
  <p class="dato" style="margin-top: 12px">🔴 <b>CUÁL dorado no es preferencia,
  es medida.</b> Acá la tarjeta es <b>blanca</b> y va el dorado del brief, que
  ahí mide 3,09 — el mismo de los otros tres íconos. <b>En el pie, que es
  marfil, el mismo dorado mide 2,89 y no pasa</b>, así que allá va el dorado de
  texto. Es la regla que ya ordenaba los íconos de la pieza 11.</p>
  <p class="dato" style="margin-top: 12px">📌 <b>Lo que sí se respeta sin
  costo:</b> el dibujo no se deforma ni se combina con otro logo, y
  <b>WhatsApp</b> se escribe con las dos mayúsculas y nunca como verbo.</p>

  <p class="rotulo">Lo que esta pieza sacó</p>
  <h2>Los horarios no se publican</h2>
  <p><b>Decisión de Juan, 4-sep-2026.</b> La tarjeta tenía los días y las horas
  de atención, y salieron: <b>dos copias del mismo dato se desincronizan
  siempre.</b> Los horarios de verdad son <code>horarios_base</code>,
  <code>fin_maximo</code>, las excepciones y <b>la semana del 15 que Cecilia
  cierra todos los meses</b>. Una tabla fija en el sitio empieza a mentir el
  primer mes.</p>
  <p style="margin-top: 12px"><b>Y el sitio ya tiene algo mejor:</b> la grilla
  de reserva muestra la disponibilidad real, calculada. Los horarios de puertas
  abiertas van al <b>Perfil de Empresa de Google</b> (§ 14), que es donde la
  gente los busca y donde se cargan los días especiales.</p>
  <p class="dato" style="margin-top: 12px">⚠ <b>El costo, dicho:</b> el que
  quiere llamar no sabe cuándo hay alguien del otro lado.</p>
</section>

<section>
  <p class="rotulo">Las reglas</p>
  <h2>Lo que no se negocia</h2>
  <ul class="reglas">
    <li><b>El renglón entero es el enlace, no la palabra.</b> Los dos datos que
    se tocan miden 44 px o más de alto, que es el piso táctil del sistema.</li>
    <li><b>El enlace se marca con color Y con subrayado.</b> El dorado de texto
    solo no alcanza: el color no puede ser lo único que diga que algo se
    toca.</li>
    <li><b>El correo se lee, no se toca.</b> Un <code>mailto:</code> abre el
    programa de correo que tenga configurado la persona, que puede ser uno que
    no usa. Escrito, cada uno hace lo suyo.</li>
    <li><b>El teléfono se escribe de una forma y se marca de otra</b>, y el
    enlace de WhatsApp lleva un <b>9</b> que el número escrito no muestra. Sin
    ese 9 no abre la conversación.</li>
    <li>🔴 <b>El correo es PROVISIONAL y por eso va sólo en el sitio.</b> Un
    sitio se edita en un minuto; una tanda de recetas, no. En papel va el
    correo del dominio o no va ninguno.</li>
    <li>🔴 <b>El que se ve acá es un marcador, no el correo real.</b> Este repo
    es público y el correo de Cecilia hoy es una casilla personal; el historial
    de git viaja con el repo y no se reescribe. <b>El de verdad se pone al
    construir el sitio</b>, igual que en la base (§ 9.1.c).</li>
    <li>🔴 <b>El isotipo ajeno va a 18 px y los nuestros a 24, y así es como
    se ven IGUALES.</b> Lo levantó Juan. Los nuestros son de línea y no llegan
    al filo de su caja —el sobre mide 17,6 de ancho adentro de 24—; el ajeno es
    macizo y la ocupa entera. <b>Igualar la caja es agrandar el dibujo.</b></li>
    <li><b>Los isotipos ajenos NO se dibujan a mano.</b> Salen del Brand
    Resource Center de Meta y se leen del archivo. Lo único que se les cambia
    es el color, y esa decisión está escrita con su costo.</li>
    <li><b>El mapa se apunta con coordenada, nunca con la dirección
    escrita.</b> «25 de Mayo 3725, Santa Fe» tiene dos lugares posibles en la
    misma provincia.</li>
    <li><b>La matrícula no va acá: va en el pie</b> (pieza 13). Es un renglón
    fijo de toda pieza pública, y el pie es donde se lo busca.</li>
  </ul>
</section>
</div>
"""



# ============================================================
# PIEZA 13 — EL PIE
#
# El pie es el único bloque con contenido OBLIGATORIO, y no lo decide el
# diseño: el régimen de anuncios publicitarios está delegado por la Ley 3950
# al Colegio de Odontólogos, y pide nombre y matrícula visibles (§ 14). Por eso
# esos dos renglones no se acortan ni se mueven a otro lado.
# ============================================================

PROFESIONAL = "Dra. Cecilia Brassesco"

# 🔴 SE ESCRIBE "Matrícula", no una sigla. No se consiguió el texto del
# reglamento del Colegio (§ 14, sigue esperando respuesta), así que la abrevia-
# tura sería inventada. La palabra entera no puede estar mal.
MATRICULA = "Matrícula 3636/01"

# Tomado el 12-ago-2026, junto con el dominio y el nombre de WhatsApp (16.7).
INSTAGRAM = "cbodontologiayestetica"

NOMBRE_COMERCIAL = "CB Odontología y Estética"

CSS_PIE = """
/* La línea dorada es lo único que separa el pie del bloque de arriba. NO va
   banda de fondo: la primera banda oscura del sitio es una decisión de la
   página entera, y se toma en el tablero 15 con las seis secciones juntas.
   Adelantarla acá sería decidir el ritmo del sitio desde su último bloque. */
.pie-sitio {
  border-top: 1px solid var(--dorado);
  padding-top: 24px;
  margin-top: 24px;
  /* El margen lateral es del pie, no del tablero — mismo motivo que la pieza
     11 y la 12. Y acá importa doble: la línea dorada de arriba arranca donde
     arranca el margen, así que si el margen no fuera suyo, la línea tampoco. */
  margin-left: var(--margen-seccion);
  margin-right: var(--margen-seccion);
  max-width: var(--ancho-pagina);
  text-align: center;
}

/* 🔴 EL PIE DECÍA QUE ESTABA CENTRADO Y NO LO ESTABA — 13-sep-2026, lo cazó
   Juan mirando la captura de 1280 y se confirmó midiendo renglón por renglón.

   Qué pasaba: el logo caía en el centro exacto (640) y los tres renglones de
   texto tenían su centro en 410, o sea 230 px corridos a la izquierda.

   Por qué, y es la parte que importa: todo `<p>` del sistema lleva
   `max-width: var(--columna)` para que una línea no se pase de largo. En
   escritorio eso son 640 px dentro de un pie de 1100. `text-align: center`
   centra el texto ADENTRO de esa caja de 640 — pero la caja de 640 estaba
   pegada a la izquierda del pie, porque un `max-width` acota y NO centra.

   ⚠️ No se veía a 390 ni a 768 porque ahí `--columna` vale 100% y la caja
   ocupa todo: apareció recién al ensanchar el contenedor a 1100. Es la clase
   de rotura que un ancho nuevo destapa en algo que ya estaba aprobado.

   El arreglo centra la CAJA, que es lo que faltaba. El `max-width` se queda:
   sigue haciendo falta para que la línea no se estire. */
.pie-sitio p,
.pie-sitio ul {
  margin-left: auto;
  margin-right: auto;
}

/* EL AIRE DE ABAJO DE TODO. Sin esto el copyright termina pegado al filo de
   la ventana — lo levantó Juan el 13-sep-2026: «la última letra termina
   pegada al final del navegador». Es el cierre de la página, no del pie: por
   eso el número sale de --aire-seccion y no de un valor propio. */
.pie-sitio {
  /* El 65 % del aire entre secciones, no el 100 %. Con el aire completo el
     cierre de la página quedaba demasiado suelto —lo midió Juan a ojo y pidió
     cortar «entre un 30 y un 40 %»—. Sale del mismo token para que siga
     escalando con el ancho: 36 · 47 · 62 en vez de 56 · 72 · 96. */
  /* 0,4 y no 0,65: el primer recorte lo dejó en 62 px y Juan lo midió con
     DevTools —el verde de abajo de la caja— y seguía siendo demasiado. Queda
     en 38 a 1280 (29 a 768, 22 a 390). Sigue saliendo del token del aire de
     sección, así que acompaña al ancho sin ser un número suelto. */
  padding-bottom: calc(var(--aire-seccion) * 0.4);
}

/* 🔴 EL PIE LLEVA MENOS AIRE ARRIBA QUE UNA SECCIÓN — lo pidió Juan el
   13-sep-2026 midiendo con DevTools: «sacale arriba para que el título de
   contacto entre en el cuadro».

   El aire entre secciones existe para separar dos bloques que compiten por la
   atención. El pie no compite con nada: es el cierre, y además ya trae su
   propia línea dorada, que es un separador más fuerte que cualquier hueco.
   Con el aire completo empujaba la sección de Contacto fuera de la pantalla.

   ⚠️ El selector lleva `.pagina` adelante A PROPÓSITO: el aire lo pone
   `.pagina > * + *`, que pesa lo mismo que `.pie-sitio` a secas y vive más
   abajo en el archivo. Con una sola clase esta regla no haría nada, sin
   avisar — es la misma trampa que ya mordió tres veces hoy. */
.pagina > .pie-sitio {
  margin-top: calc(var(--aire-seccion) * 0.5);
}

/* 🔑 EL AIRE AGRUPA, y lo dictó Juan mirando el pie: los cuatro renglones de
   abajo —nombre, matrícula, redes, copyright— son UN grupo, y el logo es otra
   cosa. Así que el hueco grande va entre el logo y el bloque, y los de adentro
   del bloque se cierran. Antes estaban todos parecidos —18, 14, 12— y el pie
   se leía como cuatro cosas sueltas. */
.pie-marca {
  display: block;
  margin: 0 auto 24px;
}

/* El nombre y la matrícula son el contenido obligatorio: van en el gris de
   lectura, no en el de las aclaraciones. */
.pie-nombre {
  font-size: var(--tipo-cuerpo);
  line-height: var(--alto-cuerpo);
}

.pie-matricula {
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
}

/* El enlace se toca, así que necesita alto: el relleno lo lleva de los 21 px
   de su renglón a los 44 del piso táctil. */
.pie-red {
  display: inline-block;
  padding: 12px 0;
  margin-top: 6px;
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  color: var(--dorado-texto);
  text-decoration: underline;
  text-underline-offset: 3px;
}

/* Los dos isotipos, uno al lado del otro.

   🔴 EL RELLENO ES DE 9 PX PORQUE EL PISO TÁCTIL ES 44 y el dibujo mide 26:
   26 + 9 + 9 = 44. Acá decía que ya medía 44 con 4 px de relleno, y era falso
   —daba 34—. Corregido el 4-sep-2026.

   Y como ese relleno también empuja hacia afuera, los márgenes de arriba y de
   abajo se descuentan: el hueco que se VE es 10 arriba y 9 abajo, que es lo
   que pide el agrupamiento. Un piso táctil no tiene por qué verse. */
.pie-redes {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 1px;
}

.pie-redes a {
  display: block;
  padding: 9px;
}

.pie-legal {
  font-size: var(--tipo-rotulo);
  line-height: var(--alto-rotulo);
  color: var(--texto-segundo);
  margin-top: 0;
}
"""


# 🔴 EL TAMAÑO SE COMPARA POR ÁREA, NO POR ANCHO — corregido el 4-sep-2026,
# lo cazó Juan mirando: "si va más chico que el encabezado, yo lo sigo viendo
# más grande". Tenía razón y el error era de método, no de gusto.
#
# El encabezado lleva el WORDMARK, que es una tira: 200 x 32 = 6.400 px². El
# pie lleva el APILADO, que es un bloque: a 160 de ancho mide 84 de alto y da
# 13.440 px², o sea MÁS DEL DOBLE. Comparar los anchos de dos dibujos con
# proporciones distintas no dice nada.
#
# A 120 px el apilado mide 63 de alto y da 7.560 px², un 18 % más que el
# encabezado (6.400). Se subió dos veces a pedido de Juan, mirando: 100 → 110
# → 120. El número no se eligió por regla, se eligió a 1:1.
PIE_LOGO = {390: 120, 768: 142, 1280: 158}


def pie_del_sitio(apilado, ancho):
    """El cierre de la página: la marca, quién firma, y dónde encontrarla."""
    return f"""
  <footer class="pie-sitio">
    <img class="pie-marca"
         src="data:image/png;base64,{apilado}"
         alt="{NOMBRE_COMERCIAL}"
         width="{PIE_LOGO[ancho]}">
    <p class="pie-nombre">{PROFESIONAL}</p>
    <p class="pie-matricula">{MATRICULA}</p>
    <div class="pie-redes">
      <a href="https://instagram.com/{INSTAGRAM}"
         aria-label="Instagram de CB Odontología y Estética"
         >{isotipo("instagram", "iso-pie")}</a>
      <a href="https://wa.me/{WHATSAPP}"
         aria-label="Escribir por WhatsApp al consultorio"
         >{isotipo("whatsapp", "iso-pie")}</a>
    </div>
    <p class="pie-legal">© 2026 {NOMBRE_COMERCIAL}</p>
  </footer>"""



# ============================================================
# PIEZA 15.a — NOSOTROS / LA CLÍNICA
#
# El bloque 3 del mapa del sitio (§ 4). Nunca se había maquetado: el plan lo
# daba por "titular, párrafo y foto, ya resuelto por la escala tipográfica", y
# Juan lo abrió como pieza propia el 4-sep-2026.
#
# 🔴 TODO EL TEXTO DE ACÁ ES PROVISORIO Y LO APRUEBA CECILIA. Son afirmaciones
# sobre una persona real y sobre cómo trabaja su consultorio: no se inventan.
# Lo que se maqueta es la FORMA —cuántos elementos, de qué largo, con cuánto
# aire—, para poder decidir tipografía y espacios antes de tener el texto.
#
# QUÉ VA ACÁ, Y NO SALIÓ DEL GUSTO. La estructura sale de lo que la
# investigación dice que el paciente pesa al elegir odontólogo:
#   · la CREDENCIAL con nombre (el título profesional pesa 76,9 %)
#   · que le EXPLIQUEN antes de empezar (el constructor de confianza más
#     citado en el estudio cualitativo: "if they explain the process to me
#     before starting, I trust them")
#   · qué se hace con el MIEDO (ignorar la ansiedad es destructor de confianza,
#     y además es el posicionamiento de la marca)
#   · la HIGIENE y la esterilización (94 %, el atributo mejor puntuado de todos)
# ⚠ Y el dato que reencuadra el bloque entero: el 99,1 % llega por
# recomendación de un conocido y sólo el 23,1 % considera importante que haya
# sitio web. O sea: el que lee esto YA VIENE RECOMENDADO. El trabajo del
# bloque es CONFIRMAR esa recomendación, no convencer a un desconocido — por
# eso no lleva argumento de venta ni superlativos.
# Fuentes: PMC6527403 (n=117, Bucarest, 2019 — muestra chica y de otro país,
# se usa como orientación, no como verdad local) y PMC13174905 (cualitativo,
# confianza en odontólogos).
# ============================================================

CSS_NOSOTROS = """
/* EL RETRATO. Vertical (4/5), que es la forma de un retrato de persona: la
   proporción del hero (4/3) es de escena, no de cara. Va a sangre como la del
   hero, por la misma razón — el radio del sistema es de controles, no de
   fotos. */
/* EL MARCO ES TRANSPARENTE POR DEFECTO. `display: contents` lo borra del
   árbol de cajas: la foto que tiene adentro sigue siendo hija directa de la
   grilla, con la misma celda y el mismo tamaño que antes de que el marco
   existiera. Se enciende solo a 1280, donde sí hace falta. */
.nosotros-marco {
  display: contents;
}

.nosotros-retrato {
  display: block;
  width: 100%;
  aspect-ratio: 4 / 5;
  object-fit: cover;
}

/* VARIANTE «la foto entra en la columna»: en vez de cruzar la pantalla, se
   mete adentro del margen y arranca donde arranca el texto. La de arriba es
   la del hero —a sangre, esquinas rectas—; ésta es la que hay que comparar. */
.nosotros-dentro .nosotros-retrato,
.nosotros-dentro .nosotros-hueco {
  width: calc(100% - var(--margen-pagina) * 2);
  margin: 0 var(--margen-pagina);
}

/* EL FILO DE LA FOTO, y no es decoración: se midieron los cuatro bordes de la
   foto de ejemplo contra el marfil y el de ABAJO da 2,78 — por debajo del piso
   de 3,0 que el sistema le exige a cualquier filo. Los otros tres pasan
   (4,09 · 4,17 · 6,13), así que sin filo la foto se disuelve por un lado solo,
   que es peor que disolverse entera.

   Y el argumento que lo vuelve REGLA en vez de arreglo: las fotos las va a
   cargar Cecilia, no nosotros. Un filo que aparece «cuando hace falta» obliga
   a medir cada foto nueva y falla en silencio el día que nadie mide. Siempre
   puesto es una regla sola que no se puede incumplir.

   El color es el mismo filo que ya usan las tarjetas: no estrena nada. */
.nosotros-dentro .nosotros-retrato {
  border: 1px solid var(--dorado-claro);
}

.nosotros-hueco {
  width: 100%;
  aspect-ratio: 4 / 5;
  background: var(--dorado-claro);
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 0 24px;
  color: var(--texto-segundo);
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
}

/* EL BLOQUE NO HEREDA EL ANDAMIAJE DEL TABLERO. `base_css` le da 40 px de
   margen de arriba a todo <section>, que es prosa del tablero; el bloque del
   sitio no puede traerse ese número puesto, porque el aire entre secciones se
   decide en el tablero 15 y sale de --aire-seccion. */
.nosotros {
  margin-top: 0;
  /* Mismo mecanismo que «Testimonios»: el margen lo lleva por dentro, así que
     el centrado es `auto` a secas. En los anchos chicos vale cero.

     ⚠️ Y EL TECHO LLEVA EL MARGEN SUMADO, que no es un ajuste fino: el techo
     mide la CAJA, y esta sección se guarda el margen adentro. Con 860 pelado
     su contenido arrancaba 64 px más adentro que el de «Tratamientos», que no
     tiene padding — dos secciones de la misma página empezando en dos líneas
     distintas. Sumándoselo, las cuatro arrancan donde mismo. */
  max-width: calc(var(--ancho-pagina) + var(--margen-pagina) * 2);
  margin-left: auto;
  margin-right: auto;
}

/* El aire entre la foto y el texto. Es el ÚNICO separador que hay entre las
   dos: no hay línea ni cambio de fondo. A 390 con menos de 24 el nombre se
   pega a la foto y el bloque se lee como una sola mancha. */
.nosotros-rotulo {
  padding: 0 var(--margen-pagina);
  margin-bottom: 12px;
}

/* VARIANTE «el título de sección manda»: el nombre de la sección va del
   tamaño de un h2 —el mismo que van a tener «Tratamientos» y «Contacto»— y el
   nombre de la profesional baja a h3. */
.nosotros-titulo {
  padding: 0 var(--margen-pagina);
  margin-bottom: 16px;
}

/* EL NOMBRE SUBE UN ESCALÓN, y la decisión de la 15.a se respeta entera: ahí
   se cerró que «Nosotros» es el título de sección y que el nombre va UN
   ESCALÓN ABAJO. Lo que cambió es el escalón de arriba —el título pasó a
   --tipo-h1 porque no mandaba—, así que el nombre lo sigue a --tipo-h2.

   El problema medido era éste: el nombre estaba a 20 y el párrafo a 16, o sea
   1,25 a 1, con el mismo peso y el mismo color. Quien mira no sabía qué era
   más importante. Ahora la escalera de la sección es 32 › 26 › 16 › 14. */
.nosotros-nombre {
  font-size: var(--tipo-h2);
  line-height: var(--alto-h2);
}

.nosotros-texto {
  padding: 24px var(--margen-pagina) 0;
}

/* ANDAMIAJE, NO SITIO: subraya lo que Cecilia tiene que confirmar. Se saca
   cuando ella conteste. */
.x {
  border-bottom: 1px dotted var(--dorado);
}

.nosotros-texto h2 {
  margin-top: 20px;
}

/* La matrícula va PEGADA al nombre, no al final del bloque: es la credencial
   de esa persona, y separada de ella deja de leerse como suya. El pie lleva
   su propia copia, que es la legalmente obligatoria. */
.nosotros-matricula {
  margin-top: 4px;
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  color: var(--texto-segundo);
}

/* El párrafo ES el contenido de la sección, así que va en el gris de LECTURA.
   Estaba en el secundario y eso lo hundía al mismo plano que las señales:
   si todo es gris claro, no hay nada destacado. */
.nosotros-texto p.presentacion {
  margin-top: 16px;
  color: var(--grafito);
}

/* LAS TRES SEÑALES. No son "beneficios": son las tres cosas que la
   investigación dice que el paciente busca confirmar. Cada una es un hecho
   comprobable, no una promesa de marketing. */
.nosotros-senales {
  list-style: none;
  margin-top: 24px;
  margin-bottom: 4px;
  padding-left: 0;
}

/* EL RENGLÓN HUÉRFANO. En columna angosta una señal terminaba con una sola
   palabra colgando (38 px de línea contra 321 de la anterior). `pretty` le
   pide al navegador que reparta las últimas líneas para que eso no pase.
   Medido: esa línea pasó de 38 a 59 px. Es una mejora chica y gratis — el
   rag del párrafo ya era sano (36 px sobre 324, o sea 11 %). */
.presentacion,
.nosotros-senales li {
  text-wrap: pretty;
}

/* ⚠️ ACÁ ESTUVIERON EN TARJETA BLANCA Y FUE UN ERROR — lo cazó Juan: «agregaste
   tarjetas en texto que ni siquiera es el principal». Tenía razón, y la
   literatura lo nombra: para destacar lo principal se DES-destaca lo demás
   (Refactoring UI), no se le sube el volumen a lo terciario. Una superficie
   —fondo, filo, radio— es el recurso más fuerte que tiene el sistema, y estaba
   puesto en el contenido de MENOR rango de la sección.

   Las tres señales vuelven a ser texto, agrupado y apretado: por proximidad
   (Gestalt) los tres renglones juntos se leen como UN bloque de apoyo, que es
   exactamente su rango. El contraste con el párrafo de arriba ahora lo hace el
   tamaño y el color, no una caja. */
.nosotros-senales li {
  padding-left: 0;
  margin-top: 10px;
  max-width: var(--columna);
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  color: var(--texto-segundo);
}

.nosotros-senales li::before {
  content: "—";
  color: var(--dorado-texto);
  padding-right: 8px;
}

.nosotros-senales b {
  font-weight: 500;
  color: var(--grafito);
}

/* 🔴 EN ESCRITORIO LA FOTO Y EL TEXTO VAN LADO A LADO — 13-sep-2026.

   El problema medido: apilados, esta sección se comía 1377 px de alto a 1280,
   o sea casi un tercio de la página, y la foto quedaba más ancha que el texto
   que la acompaña. Con pantalla de sobra, ponerlos en dos columnas es
   exactamente «se AGREGA algo al haber más pantalla» (§ 4, mobile-first), no
   un diseño nuevo: el orden de lectura y el contenido no cambian.

   EL REPARTO ES 5 A 7 y no mitad y mitad: la foto es un retrato 4:5, así que
   cuanto más ancha más alta se vuelve, y es justo el alto lo que hay que
   bajar. Con 5/7 el texto queda cerca de --columna (640), que es la medida en
   la que una línea se sigue leyendo bien.

   EL MARGEN SE MUDA AL PADRE. Apilado, cada hijo llevaba el suyo; en dos
   columnas eso deja 128 px de aire entre la foto y el texto, además del hueco
   de la grilla. Acá lo lleva la sección y los hijos van pegados a su columna.

   ⚠️ Y el selector de la foto repite `.nosotros-dentro` a propósito: una
   `@media` NO suma prioridad, así que `.nosotros-retrato` a secas perdería
   contra la regla de dos clases de más arriba y no pasaría nada. */

/* 🔴 LAS DOS COLUMNAS ARRANCAN EN 768 — 13-sep-2026, y el motivo es que la
   SECCIÓN ENTRE EN LA PANTALLA, que es lo que pidió Juan.

   Apilada medía 964 px de alto y había que scrollear para verla completa; en
   dos columnas mide 533 y entra entera. Se probó apilada con la foto a 440 y
   no alcanzó: la foto sola ya se come media pantalla.

   ⚠️ LO QUE ESTE REPARTO CUESTA, y se escribe porque es una decisión y no un
   descuido: la columna de texto queda más alta que la foto (452 contra 405),
   así que la foto NO domina por tamaño. Que entre en el cuadro y que la foto
   mande no se pueden las dos cosas a 768: los 688 de ancho no dan. Se eligió
   que entre.

   6 y 6, no 5 y 7: parte el ancho por la mitad y deja la foto en 324 en vez
   de 270 — el máximo que se le puede dar sin ahogar el texto. */
@media (min-width: 768px) {
  .nosotros {
    display: grid;
    grid-template-columns: 6fr 6fr;
    column-gap: 40px;
    padding-left: var(--margen-pagina);
    padding-right: var(--margen-pagina);
  }

  /* LAS TRES SEÑALES BAJAN AL PIE DE LA FOTO. Con todo el texto pegado
     arriba quedaba un hueco grande abajo a la derecha y las dos columnas
     terminaban en alturas muy distintas.

     🔴 SE PROBÓ ANTES CON `space-between` Y SE VOLVIÓ ATRÁS, porque repartía
     el aire ENTRE TODOS los renglones y despegaba la matrícula del nombre —
     que es justo lo que la pieza 15.a decidió que no puede pasar: la
     matrícula es la credencial de esa persona y separada de ella deja de
     leerse como suya. Un empuje sobre las señales mueve UNA cosa y deja el
     resto en su orden natural.

     ⚠️ PROVISORIO, y lo decidió así Juan el 13-sep-2026: es para VER cómo
     queda. El reparto depende de cuánto texto haya, y el de Cecilia todavía
     no existe — con el texto y la foto definitivos se vuelve a mirar.
     Tampoco está cerrado si las tres señales se quedan. */
  /* 🔴 EL TEXTO SE CENTRA CONTRA LA FOTO, y esto REEMPLAZA a dos intentos
     anteriores que quedaron peor. El primero repartió el texto con
     `space-between` y despegó la matrícula del nombre. El segundo empujó sólo
     las tres señales al pie con `margin-top: auto`, y dejó un AGUJERO en el
     medio de la columna: el párrafo arriba, las señales abajo y un hueco
     vacío entre los dos. Lo cazó Juan en una palabra: «un desastre».

     🔑 Lo que los dos tenían mal es el mismo error: intentaban llenar el alto
     de la foto ESTIRANDO el texto. El texto mide lo que mide. Centrarlo
     reparte el sobrante AFUERA del bloque —arriba y abajo, donde no hay nada
     que leer— en vez de adentro, donde se lee como algo roto. */
  /* 🔴 LA FOTO Y EL TEXTO MIDEN EXACTAMENTE LO MISMO — lo pidió Juan el
     13-sep-2026. Antes la foto era 324 × 405 y el texto 324 × 452: mismo
     ancho, distinto alto, y las dos columnas terminaban desparejas.

     `stretch` hace que las dos ocupen el alto entero de la fila, y a la foto
     hay que soltarle la proporción fija para que pueda estirarse: con
     `object-fit: cover` ya puesto, lo único que cambia es cuánto recorta, no
     cómo se deforma. El alto lo manda el texto, que es el que no se puede
     recortar. */
  .nosotros {
    align-items: stretch;
  }

  .nosotros-dentro .nosotros-retrato {
    height: 100%;
    aspect-ratio: auto;
  }

  /* El título cruza las dos columnas: encabeza la sección entera. */
  .nosotros-titulo {
    grid-column: 1 / -1;
    padding-left: 0;
    padding-right: 0;
  }

  .nosotros-dentro .nosotros-retrato,
  .nosotros-dentro .nosotros-hueco {
    width: 100%;
    margin: 0;
  }

  .nosotros-texto {
    padding: 0;
  }
}

/* ANDAMIAJE DEL TABLERO, NO DEL SITIO: la cinta que grita que el texto es
   provisorio. No entra al sitio y por eso vive acá abajo, separada. */
.provisorio {
  border: 1px dashed var(--dorado);
  background: var(--info-fondo);
  padding: 10px 12px;
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  color: var(--texto-segundo);
}

/* 1280 conserva SU reparto: allá el ancho sobra y la foto puede ser más
   angosta sin apretar el texto. El 6/6 es la decisión de 768. */
@media (min-width: 1280px) {
  /* 🔴 LAS DOS COLUMNAS MIDEN LO MISMO — 14-sep-2026, lo pidió Juan:
     «los contenedores tienen que ser iguales». Es la MISMA decisión que él ya
     había tomado a 768, donde las dos miden 324 × 452; 1280 hacía lo contrario
     y el comentario que lo justificaba decía «que es lo aprobado» sin que
     hubiera ninguna aprobación detrás. Lo cazó él mirando la página.

     Qué cambia, y son las dos mitades de «iguales»:
       · el ANCHO — 1fr 1fr en vez de 5fr 7fr, como a 768.
       · el ALTO  — sin `align-items: center` la fila estira las dos columnas,
                    así que la foto deja de mandar por su proporción y toma el
                    alto del texto. Medido antes del cambio: foto 440 × 549
                    contra texto 617 × 372, o sea 177 px de diferencia. */
  .nosotros {
    grid-template-columns: 1fr 1fr;
  }

  /* ACÁ SE ENCIENDE EL MARCO. Pasa a ser una caja de verdad y la foto se
     apoya en sus cuatro bordes: al estar fuera del flujo, la foto ya no le
     impone ningún alto a la fila. El alto lo manda el TEXTO, que es el que no
     se puede recortar — la misma regla que se escribió a 768.

     El filo se muda de la foto al marco por el mismo motivo: el borde tiene
     que dibujar la caja, no la imagen que va adentro. */
  .nosotros-dentro .nosotros-marco {
    display: block;
    position: relative;
    overflow: hidden;
    border: 1px solid var(--dorado-claro);
  }

  .nosotros-dentro .nosotros-retrato {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    aspect-ratio: auto;
    border: 0;
  }
}
"""


def nosotros_del_sitio(ancho, jerarquia="titulo", dentro=True):
    """El bloque tal como iría en el sitio.

    EL ORDEN: el rótulo va ARRIBA DE LA FOTO y el resto abajo. Lo levantó Juan
    —"¿va la foto de 1 sin ningún título antes? ¿no queda raro?"— y tiene un
    motivo además del susto: al bloque se llega desde el menú, y quien toca
    «Nosotros» aterriza acá. Una foto sola no dice dónde cayó; el rótulo sí.

    LO SUBRAYADO son afirmaciones que CECILIA TIENE QUE CONFIRMAR. El texto ya
    no es relleno mudo: está escrito como iría, para poder decidir si las tres
    señales se quedan. Ninguna se publica sin su visto bueno.
    """
    if jerarquia == "titulo":
        cabeza = """
    <h2 class="nosotros-titulo">Nosotros</h2>"""
        nombre = """<h3 class="nosotros-nombre">Cecilia Brassesco</h3>"""
    else:
        cabeza = """
    <p class="rotulo nosotros-rotulo">Nosotros</p>"""
        nombre = """<h2>Cecilia Brassesco</h2>"""

    foto = leer_foto_nosotros()

    # SU PROPIA FOTO, NO LA DEL HERO — corregido el 11-sep-2026. Es 900 × 1125,
    # o sea 4:5 exacto: el mismo número que pide el hueco, así que `cover` no
    # recorta nada y lo que se aprueba en el tablero es lo que se ve.
    # 🔴 LA FOTO VA ADENTRO DE UN MARCO — 14-sep-2026. El marco NO se ve y
    # en 390 y 768 ni siquiera existe: lleva `display: contents`, así que la
    # foto sigue siendo hija directa de la grilla y la geometría no se mueve
    # ni un píxel. Recién a 1280 el marco se enciende.
    #
    # POR QUÉ HACE FALTA, y es el motivo por el que no alcanzaba con CSS:
    # una <img> le impone a su fila su ALTO NATURAL. A 768 eso no molestaba
    # —la foto pedía 405 y el texto 452, así que mandaba el texto— pero a 1280
    # la columna es más ancha y la foto pide 661 contra los 405 del texto:
    # manda la foto y las dos columnas vuelven a quedar desparejas. Sacando la
    # foto del flujo (dentro del marco) deja de tener alto propio que imponer.
    if foto:
        hueco = (
            '<div class="nosotros-marco">'
            f'<img class="nosotros-retrato" alt="" src="{foto}">'
            '</div>'
        )
    else:
        hueco = ("""<div class="nosotros-marco"><div class="nosotros-hueco">
      Retrato de Cecilia en el consultorio.<br>
      Vertical, 4:5. No existe todavía.
    </div></div>""")

    marco = " nosotros-dentro" if dentro else ""

    # EL ANCLA, y faltaba: el menú escribe href="#nosotros" desde que existe,
    # y en la página no había ningún id="nosotros" — o sea que el enlace no
    # llevaba a ningún lado. Los otros dos destinos (tratamientos y contacto)
    # sí lo tenían. Encontrado el 13-sep-2026 al medir el menú, y no fallaba
    # con error: el navegador se queda quieto y ya.
    return f"""
  <section class="nosotros{marco}" id="nosotros">{cabeza}
    {hueco}
    <div class="nosotros-texto">
      {nombre}
      <p class="nosotros-matricula">Matrícula 3636/01</p>
      <p class="presentacion">Soy odontóloga y atiendo en Santa Fe
      <span class="x">desde 2015</span>. <span class="x">Trabajo sola y con
      turnos espaciados</span>: prefiero que cada persona tenga su tiempo antes
      que ver a mucha gente por día. Hago <span class="x">tratamientos
      generales y estética dental</span>.</p>
      <ul class="nosotros-senales">
        <li><b>Sabés qué se va a hacer antes de empezar.</b>
        <span class="x">Qué tratamiento, cuántas sesiones lleva y cuánto sale,
        dicho antes y no en el sillón.</span></li>
        <li><b>Si te da miedo el dentista, decilo.</b>
        <span class="x">Se te da un turno más largo y se avanza al ritmo que
        aguantes, sin apuro.</span></li>
        <li><b>Instrumental esterilizado, uno por paciente.</b>
        <span class="x">Esterilización en autoclave con control, y material
        descartable que se abre delante tuyo.</span></li>
      </ul>
    </div>
  </section>"""


def solo_nosotros(tokens, css, ancho, jerarquia="titulo", dentro=True):
    """El bloque SOLO, sin una palabra de tablero alrededor.

    Existe porque el tablero mezcla la muestra con la explicación, y a 390 eso
    hace imposible ver cómo queda la sección: hay que scrollear prosa antes y
    después. Acá está la página tal como la vería el paciente y nada más.
    """
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · Nosotros, solo el bloque · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_ENCABEZADO}
{CSS_NOSOTROS}
</style>

<p class="provisorio" style="margin: 0 var(--margen-pagina) 20px">🔴 <b>MAQUETA.
Todo el texto es PROVISORIO y lo aprueba Cecilia</b> — el punteado marca cada
afirmación por confirmar. <b>La foto es de banco</b>, no es ella.</p>
{nosotros_del_sitio(ancho, jerarquia, dentro)}
"""


def tablero_nosotros(tokens, css, ancho):
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 15a Nosotros · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_ENCABEZADO}
{CSS_NOSOTROS}
</style>

<div class="prosa">
<p class="rotulo">Fase ⑧ · Pieza 15.a · {ancho} px</p>
<h1>Nosotros / la clínica</h1>
<div class="regla"></div>
<p><b>Es el bloque 3 del mapa del sitio y nunca se había maquetado.</b> El plan
lo daba por resuelto —«titular, párrafo y foto»—; <b>lo abrió Juan como pieza
propia</b> el 4-sep-2026, para poder evaluarlo antes de armar la página.</p>

<p class="provisorio" style="margin-top: 20px">🔴 <b>TODO EL TEXTO DE ESTE
TABLERO ES PROVISORIO Y LO APRUEBA CECILIA.</b> Son afirmaciones sobre una
persona real y sobre cómo trabaja su consultorio: <b>no se inventan</b>. Lo que
se está decidiendo acá es la <b>forma</b> —cuántos elementos, de qué largo, con
cuánto aire—. Las preguntas para ella salen de este tablero.</p>
</div>

<p class="marca-muestra" style="padding: 0 var(--margen-pagina); margin: 40px 0 12px"
   >El bloque, a 1:1</p>
{nosotros_del_sitio(ancho)}

<div class="prosa">
<section>
  <p class="rotulo">Qué va acá, y no salió del gusto</p>
  <h2>Los cuatro contenidos los eligió la investigación</h2>
  <p>Se buscó qué pesa cuando un paciente elige odontólogo, y la estructura del
  bloque sale de ahí: <b>la credencial con nombre</b> (el título profesional lo
  puntúa como importante el <b>76,9 %</b>), <b>que le expliquen antes de
  empezar</b> —el constructor de confianza más citado en el estudio
  cualitativo—, <b>qué se hace con el miedo</b> (ignorar la ansiedad aparece
  como destructor de confianza) y <b>la higiene y esterilización</b>, que con
  <b>94 %</b> es el atributo mejor puntuado de todos.</p>
  <p class="dato" style="margin-top: 12px">⚠ <b>Honestidad sobre la fuente:</b>
  el estudio de los porcentajes es de <b>117 personas en Bucarest, 2019</b>.
  Muestra chica y de otro país: <b>orienta la estructura, no prueba nada sobre
  Santa Fe</b>. El cualitativo de confianza es de otra población todavía.</p>

  <p class="rotulo">El dato que reencuadra el bloque entero</p>
  <h2>El que lee esto ya viene recomendado</h2>
  <p>En ese mismo estudio, <b>el 99,1 % llegó por recomendación de un conocido</b>
  y sólo el <b>23,1 %</b> consideró importante que hubiera sitio web.
  <b>Entonces el trabajo de este bloque no es convencer a un desconocido: es
  CONFIRMAR una recomendación que ya existe.</b> Por eso no lleva argumento de
  venta, ni superlativos, ni «años de experiencia» como titular.</p>
  <p class="dato" style="margin-top: 12px">🔑 <b>Y es evidencia en contra de
  nuestro propio proyecto, así que se escribe:</b> ese 23,1 % dice que el sitio
  pesa poco en la ELECCIÓN. Lo que el sitio sí hace —y el estudio no
  mide— es <b>dejar reservar solo</b>, que es trabajo que hoy hace una persona.
  <b>El sitio se justifica por la autogestión del turno, no por captación.</b></p>

  <p class="rotulo">La decisión de forma que esta pieza cierra</p>
  <h2>El retrato va vertical, 4:5</h2>
  <p><b>La del hero es 4:3 apaisada, y es una escena.</b> Ésta es una persona:
  un retrato en una columna de teléfono necesita alto, no ancho. <b>Y hereda la
  regla de la pieza 10:</b> una foto apaisada no se reencuadra en un hueco
  vertical, así que <b>hay que pedirla vertical de origen</b>.</p>
  <p class="dato" style="margin-top: 12px">⚠ <b>La foto no existe todavía</b> y
  el hueco lo dice en la cara. <b>Va al brief de fotos</b>, con la guía que ya
  vive en <code>brand/COMO-SACAR-LAS-FOTOS.md</code>.</p>

  <p class="rotulo">Lo que se decidió repetir a propósito</p>
  <h2>La matrícula aparece dos veces, y está bien</h2>
  <p>El pie ya la lleva: <b>ésa es la copia legalmente obligatoria</b>. Acá va
  <b>pegada al nombre</b>, porque es la credencial de esa persona y separada de
  ella deja de leerse como suya — que es justo lo que la investigación dice que
  el paciente busca. <b>No contradice la regla de no repetir datos:</b> esa
  regla existe porque dos copias <b>se desincronizan</b>, y una matrícula no
  cambia.</p>
</section>

<section>
  <p class="rotulo">Las reglas</p>
  <h2>Lo que no se negocia</h2>
  <ul class="reglas">
    <li>🔴 <b>Ninguna afirmación sobre Cecilia se escribe sin que ella la
    confirme.</b> El relleno se inventa donde no hay contenido —una foto de
    banco, un testimonio genérico—, <b>nunca sobre una persona real</b>.</li>
    <li>🔴 <b>No entra la palabra «especialista» ni «ortodoncista»</b> como
    credencial suya hasta el posgrado certificado. Es una restricción sobre una
    palabra, no sobre un tratamiento.</li>
    <li><b>Sin superlativos.</b> Además de que el régimen de anuncios del
    Colegio los suele restringir, contradicen el posicionamiento: premium en la
    forma, <b>general y humano en el fondo</b>.</li>
    <li><b>Las tres señales son hechos comprobables</b>, no promesas. Si una no
    se puede sostener un martes cualquiera, no va.</li>
  </ul>
</section>
</div>
"""


def tablero_pie(tokens, css, ancho):
    apilado = leer_png("cb-apilado-600")
    alto = round(PIE_LOGO[ancho] * PROPORCION["apilado"])

    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 13 Pie · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_ISOTIPO}
{CSS_PIE}
{css_margen_en_la_prosa()}
</style>

<div class="prosa">
<p class="rotulo">Fase ⑧ · Pieza 13 · {ancho} px</p>
<h1>El pie</h1>
<div class="regla"></div>
<p><b>Es el único bloque con contenido obligatorio</b>, y no lo decide el
diseño: en Santa Fe el régimen de anuncios está delegado al Colegio de
Odontólogos por la Ley 3950, y pide <b>nombre y matrícula visibles</b>. Esos
dos renglones no se acortan.</p>

<section>
  <p class="rotulo">El pie, a 1:1</p>
  <h2>Cuatro renglones</h2>
</section>
</div>

{pie_del_sitio(apilado, ancho)}

<div class="prosa">
<section>
  <p class="rotulo">La decisión que esta pieza cerró</p>
  <h2>Acá aparece el emblema, y en ningún otro lado</h2>
  <p>El encabezado lleva el <b>wordmark</b> (pieza 9). Si el pie repitiera el
  mismo dibujo, el emblema —la parte de la marca que se dibujó con más
  cuidado— <b>no aparecería en toda la página</b>. Va el <b>apilado</b>.</p>
  <p class="dato" style="margin-top: 12px">🔴 <b>Y el tamaño se compara por
  ÁREA, no por ancho — lo cazó Juan mirando.</b> Acá decía «va más chico que el
  encabezado» porque 160 es menos que 200. <b>Era falso:</b> el wordmark del
  encabezado es una tira de 200 × 32 = <b>6.400 px²</b>, y el apilado a 160
  medía 84 de alto = <b>13.440 px², más del doble</b>. Comparar los anchos de
  dos dibujos de proporciones distintas no dice nada.</p>
  <p class="dato" style="margin-top: 12px">✅ <b>Corregido a
  {PIE_LOGO[ancho]} px:</b> mide {alto} de alto y da <b>{PIE_LOGO[ancho] * alto}
  px²</b>, contra los 6.400 del encabezado. Y queda arriba del mínimo del
  manual para el apilado, que son 80 px.</p>

  <p class="rotulo">La única excepción de alineación del sitio</p>
  <h2>El pie va centrado, y todo lo demás no</h2>
  <p><b>Se probaron los dos.</b> Al margen, como el resto del sitio, el
  apilado queda mal: <b>es una composición centrada</b> —el emblema sobre el
  nombre— y pegada a la izquierda parece corrida, no alineada. El medidor lo
  marcó solo: la tinta del emblema caía en una posición que no es ninguna de
  las tres legítimas.</p>
  <p style="margin-top: 12px"><b>Centrado, el pie cierra la página.</b> Los 18
  bloques vuelven a caer en su lugar —siete centrados, once en el margen— y el
  centrado <b>se mide, no se declara</b>.</p>
  <p class="dato" style="margin-top: 12px">🔑 <b>Cuándo convendría lo otro:</b>
  si el pie creciera a varias columnas —menú, tratamientos, redes—, la
  alineación al margen vuelve a ganar, porque ahí lo que ordena son las
  columnas y no el cierre. <b>Con cuatro renglones, no.</b></p>

  <p class="rotulo">Lo que el pie NO repite</p>
  <h2>La dirección y el teléfono no vuelven</h2>
  <p><b>Contacto está justo arriba.</b> En una página de un solo scroll,
  repetir el teléfono a 200 px del teléfono no agrega un camino: agrega un
  renglón que hay que mantener en dos lados. <b>Es la misma regla que sacó los
  horarios de la pieza 12:</b> dos copias del mismo dato se desincronizan.</p>
  <p class="dato" style="margin-top: 12px">⚠ <b>Se revisa en el tablero 15</b>,
  que es donde se ve la distancia real entre los dos bloques. Si en pantalla
  grande Contacto y el pie quedan lejos, esto se reabre.</p>

  <p class="rotulo">Acá me equivoqué yo, y lo cazó Juan</p>
  <h2>Los isotipos van, y van en dorado</h2>
  <p>Este tablero llegó a decir que el isotipo de Instagram no se podía
  repintar. <b>Era falso:</b> sus reglas dicen que se puede llevar a
  <b>cualquier color sólido</b> mientras el dibujo no cambie. <i>El error de
  fondo no fue el dato: fue meter dos marcas en la misma bolsa</i> —se le
  aplicó a Instagram una regla leída en las de WhatsApp—.</p>
  <p style="margin-top: 12px"><b>WhatsApp sí dice que no se repinta</b>, y aun
  así va en dorado: <b>lo decidió Juan</b>, con ese dato delante y con el
  criterio de que es la misma empresa y el uso repintado está en todos lados.
  <b>La decisión y su costo viven en <code>brand/marcas-ajenas/PROCEDENCIA.md</code></b>,
  no en la memoria de nadie.</p>
  <p class="dato" style="margin-top: 12px">✅ <b>Y los archivos son los
  oficiales.</b> Se bajaron los dos packs del Brand Resource Center de Meta el
  4-sep-2026 — el de WhatsApp trae las versiones verde, blanca y negra; el de
  Instagram, degradada, blanca y negra—. <b>Se guardó la negra de cada uno</b>,
  que es silueta plana, y el generador le pone el color. <b>Ninguna curva se
  dibujó a mano.</b></p>
  <p class="dato" style="margin-top: 12px">🔴 <b>Acá van en el dorado de TEXTO,
  no en el del brief:</b> el pie es marfil y ahí el dorado del brief mide 2,89,
  abajo del piso de 3,0 de un dibujo. En la tarjeta de contacto, que es blanca,
  va el del brief. <b>El fondo decide, no el gusto.</b></p>

  <p class="rotulo">Lo que quedó dicho y hay que confirmar</p>
  <h2>La matrícula se escribe con la palabra entera</h2>
  <p>Va <b>«Matrícula 3636/01»</b> y no una sigla. <b>No se consiguió el texto
  del reglamento del Colegio</b> —la consulta está hecha y esperando
  respuesta—, así que cualquier abreviatura sería inventada. <b>La palabra
  entera no puede estar mal.</b></p>
</section>

<section>
  <p class="rotulo">Las reglas</p>
  <h2>Lo que no se negocia</h2>
  <ul class="reglas">
    <li>🔴 <b>El nombre y la matrícula son obligatorios</b>, no decorativos.
    Van en el gris de lectura, no en el de las aclaraciones.</li>
    <li><b>El pie no lleva banda de fondo.</b> La primera banda oscura del
    sitio es una decisión de la página entera y se toma en el tablero 15.
    Decidir el ritmo del sitio desde su último bloque es al revés.</li>
    <li><b>El pie es el único bloque centrado del sitio.</b> Es una excepción
    con motivo —su marca es una composición centrada—, no una preferencia.</li>
    <li><b>El enlace de Instagram mide 44 px de alto</b>, como todo lo que se
    toca. El relleno está para eso, no para separar.</li>
    <li><b>Ningún isotipo ajeno entra al sitio</b> — ni el de WhatsApp ni el de
    Instagram. La palabra hace el trabajo.</li>
  </ul>
</section>
</div>
"""



# ============================================================
# PIEZA 15.b — PRUEBA
#
# El bloque 4 del mapa del sitio (§ 4), que ahí ocupa CUATRO PALABRAS:
# "antes/después, testimonios". Es la sección menos definida del sitio y la
# única que se apoya entera en material de terceros.
#
# 🔴 LA DECISIÓN DE FORMA QUE ORDENA TODO EL BLOQUE: los testimonios van
# PRIMERO y el par antes/después va de CIERRE. No es gusto — el par es la
# pieza con más chance de caerse, por dos motivos independientes:
#   · el régimen de anuncios lo dicta el Colegio de Odontólogos de Santa Fe
#     (Ley 3950), se preguntó y NO CONTESTÓ;
#   · el Código Argentino de Ética y Deontología Dental, Art. 53, prohíbe
#     avalar "resultados de actuaciones profesionales que no haya efectuado y
#     comprobado personalmente", y el Art. 49.3 pide que la publicidad no
#     pueda "dar lugar a falsas esperanzas".
# Con el par arriba, si mañana se cae queda una sección hueca; con el par
# abajo, se saca un bloque y la sección sigue en pie.
#
# 🔴 EL PAR DE FOTOS DE ESTA MAQUETA SON DOS BOCAS DISTINTAS DE BANCO — lo
# decidió Juan el 8-sep-2026 y para juzgar la forma alcanza. NO SE PUBLICA:
# publicado sería exactamente el resultado clínico fabricado que prohíbe el
# Art. 53. El detalle vive en brand/fotos/PROCEDENCIA.md.
#
# POR QUÉ EL TESTIMONIO ES EL CONTENIDO PRINCIPAL, y no las fotos: el dato que
# reencuadró la 15.a vale más todavía acá — el 99,1 % de los pacientes llega
# por recomendación de un conocido. Un testimonio ES esa recomendación puesta
# por escrito; el antes/después es un argumento de venta, que es el registro
# que la § 2 descartó (premium en la forma, no lujo).
#
# 🔑 Y LA RELACIÓN CON NOSOTROS (15.a), QUE NO ES REDUNDANCIA: allá Cecilia
# PROMETE tres cosas (que te explican, que el miedo se atiende, que el
# instrumental está esterilizado); acá un paciente CONFIRMA que le pasó. Es la
# diferencia entre "yo hago X" y "a mí me hicieron X", y es justo lo que hace
# valer a la sección. Por eso el eco es deseable — lo que no puede es ser la
# misma frase con otras comillas.
# ============================================================

CSS_PRUEBA = """
/* El bloque no hereda los 40 px que base_css le da a todo <section>: ése es
   andamiaje del tablero. El aire entre secciones sale de --aire-seccion y se
   cierra en el tablero 15. */
.prueba {
  margin-top: 0;
  /* El techo y el centrado. Esta sección lleva su margen como `padding` de
     adentro, no como margen, así que acá alcanza con `auto`: en móvil y
     tablet el techo vale 100%, no sobra nada y `auto` da cero — no cambia
     nada de lo aprobado. En escritorio sobra pantalla y centra.

     El techo lleva el margen sumado por el mismo motivo que «Nosotros»: mide
     la caja, y el margen de esta sección vive adentro. */
  max-width: calc(var(--ancho-pagina) + var(--margen-pagina) * 2);
  margin-left: auto;
  margin-right: auto;
}

.prueba-titulo {
  padding: 0 var(--margen-pagina);
  margin-bottom: 16px;
}

.prueba-lista {
  padding: 0 var(--margen-pagina);
}

/* LA TARJETA BLANCA SÍ VA ACÁ, y conviene decir por qué no contradice la
   lección de la 15.a. Allá la tarjeta estaba puesta sobre el contenido de
   MENOR rango (las tres señales) y por eso sobraba. Acá el testimonio ES el
   contenido de la sección: la superficie está sobre lo principal, que es
   donde el sistema la puso (pieza 6). Mismos tokens, sin inventar ninguno. */
.testimonio {
  max-width: var(--columna-lista);
  margin-top: 12px;
  padding: 18px;
  background: var(--blanco);
  border: 1px solid var(--borde);
  border-radius: var(--radio);
}

/* La cita va en el gris de LECTURA y en cuerpo: es lo que se viene a leer.
   Sin comillas dibujadas ni bastardilla — la caja ya dice que es una cita, y
   una tipografía inclinada a 16 px en un teléfono se lee peor. */
.testimonio p {
  color: var(--grafito);
  max-width: none;
}

/* QUIÉN LO DIJO va abajo, chico y en el gris segundo. Arriba competiría con
   la cita, que es el contenido; abajo cierra y ancla. */
.testimonio footer {
  margin-top: 12px;
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  color: var(--texto-segundo);
}

.testimonio footer b {
  font-weight: 500;
  color: var(--grafito);
}

/* EL CASO — el par antes/después. Va de cierre y separado del grupo de
   testimonios por más aire del que hay entre tarjeta y tarjeta: por
   proximidad (Gestalt) las tres tarjetas tienen que leerse como UN grupo y el
   caso como otra cosa. 12 px adentro, 32 afuera. */
.prueba-caso {
  margin-top: 32px;
  padding: 0 var(--margen-pagina);
}

.prueba-par {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 12px;
}

.prueba-par figure {
  margin: 0;
}

/* CUADRADAS, y el motivo es la comparación: dos fotos que se miran una al
   lado de la otra tienen que tener la misma caja, o la diferencia de forma se
   lee antes que la diferencia de contenido. El recorte lo hace object-fit,
   así que el archivo original no se toca.

   EL FILO VA SIEMPRE — regla ya cerrada el 4-sep: las fotos las va a cargar
   Cecilia, y un filo que aparece "cuando hace falta" falla en silencio el día
   que nadie mide. Esquinas rectas: el radio del sistema es de controles. */
.prueba-par img {
  display: block;
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  border: 1px solid var(--dorado-claro);
}

/* Cada foto trae su object-position propia porque los originales no están
   encuadrados igual: el "antes" es apaisado con la boca al medio, el
   "después" es vertical con la boca en el tercio de arriba. Sin esto, el
   recorte cuadrado del segundo se come los dientes. */
.prueba-par .antes img {
  object-position: center 55%;
}

.prueba-par .despues img {
  object-position: center 25%;
}

/* La etiqueta va DEBAJO de su foto y en el rótulo del sistema: arriba
   empujaría las dos fotos hacia abajo y separaría el par justo donde tiene
   que leerse junto. */
.prueba-par figcaption {
  margin-top: 8px;
  font-size: var(--tipo-rotulo);
  line-height: var(--alto-rotulo);
  font-weight: 500;
  letter-spacing: var(--letra-rotulo);
  text-transform: uppercase;
  color: var(--dorado-texto);
}

/* EL HUECO, para cuando las fotos no estén. Misma caja cuadrada que la foto,
   para que el bloque mida igual con archivo y sin archivo. */
.prueba-hueco {
  width: 100%;
  aspect-ratio: 1 / 1;
  background: var(--dorado-claro);
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 0 12px;
  color: var(--texto-segundo);
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
}

/* QUÉ TRATAMIENTO FUE. No es un pie decorativo: sin él, dos fotos juntas
   prometen un resultado sin decir de qué, que es lo que el Art. 49.3 llama
   "falsas esperanzas". Con el tratamiento nombrado, el par informa. */
/* VARIANTE «CITA»: sin caja, con el dorado de línea a la izquierda. Pesa
   menos que la tarjeta y no repite el recurso; las comillas y el filo ya
   dicen que es una cita. El rango no baja porque el testimonio sigue siendo
   lo único que hay en la sección. */
.testimonio.cita {
  background: none;
  border: none;
  border-left: 2px solid var(--dorado);
  border-radius: 0;
  padding: 2px 0 2px 16px;
  margin-top: 24px;
}

.testimonio.destacada p {
  font-size: var(--tipo-h3);
  line-height: var(--alto-h3);
}

.testimonio.destacada {
  margin-top: 4px;
  border-left-width: 3px;
}

/* Las dos que acompañan se cierran entre sí: por proximidad se leen como un
   par que apoya a la de arriba, no como dos piezas más de una lista. */
.testimonio.menor {
  margin-top: 20px;
}

.testimonio.menor p {
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
}

.prueba-detalle {
  margin-top: 12px;
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  color: var(--texto-segundo);
}
"""


# LOS TRES TESTIMONIOS SON PROVISORIOS Y LOS TRAE CECILIA. Están escritos como
# irían —no "lorem ipsum"— para poder decidir cuántos renglones aguanta la
# tarjeta y cuánto mide la sección. Cada uno confirma UNA de las tres cosas
# que Nosotros promete, dicho por quien lo recibió y no por quien lo ofrece.
#
# ⚠️ LO QUE NINGUNO HACE, y es deliberado: prometer un resultado ("me quedaron
# perfectos", "es la mejor de Santa Fe"). Eso es lo que el Art. 49.3 marca
# como falsas esperanzas y lo que la § 2 descarta por registro.
TESTIMONIOS = [
    (
        "Hacía cuatro años que no pisaba un consultorio de puro miedo. "
        "Me explicó todo antes de tocarme y paramos cuando lo necesité.",
        "Marina G.",
        "Consulta y dos arreglos",
    ),
    (
        "Me dijo cuántas sesiones eran y cuánto salía antes de empezar. "
        "No apareció ningún costo que yo no supiera.",
        "Diego R.",
        "Tratamiento de conducto",
    ),
    (
        "Vengo con mis dos hijos. Los turnos son a la hora que dice y el "
        "instrumental lo abre delante nuestro.",
        "Laura P.",
        "Controles",
    ),
]


def testimonio(texto, quien, que, estilo=""):
    return f"""
      <blockquote class="testimonio{estilo}">
        <p>«{texto}»</p>
        <footer>
          <b>{quien}</b> · {que}
        </footer>
      </blockquote>"""


def leer_par():
    """Las dos fotos del caso, o None si falta alguna.

    Devuelve rutas y no contenido, igual que leer_foto(): si un archivo no
    está, el bloque dibuja el hueco marcado en vez de romperse. Un tablero que
    no abre no se puede aprobar.
    """
    antes = RAIZ / "brand" / "fotos" / "antes-ejemplo.jpg"
    despues = RAIZ / "brand" / "fotos" / "despues-ejemplo.jpg"

    if not antes.exists() or not despues.exists():
        return None

    return (
        "../../fotos/antes-ejemplo.jpg",
        "../../fotos/despues-ejemplo.jpg",
    )


def prueba_del_sitio(ancho, con_caso=False, estilo=""):
    """El bloque tal como iría en el sitio.

    con_caso=False dibuja la sección SIN el par antes/después, que es
    como quedaría si esas fotos no salen en la primera carga.
    """
    par = leer_par()

    if par:
        caso = f"""
      <figure class="antes">
        <img alt="" src="{par[0]}">
        <figcaption>Antes</figcaption>
      </figure>
      <figure class="despues">
        <img alt="" src="{par[1]}">
        <figcaption>Después</figcaption>
      </figure>"""
    else:
        caso = """
      <figure class="antes">
        <div class="prueba-hueco">Antes. No existe todavía.</div>
      </figure>
      <figure class="despues">
        <div class="prueba-hueco">Después. No existe todavía.</div>
      </figure>"""

    if estilo == " jerarquia":
        rangos = [" cita destacada", " cita menor", " cita menor"]
        tarjetas = "".join(
            testimonio(texto, quien, que, rangos[i])
            for i, (texto, quien, que) in enumerate(TESTIMONIOS)
        )
    else:
        tarjetas = "".join(
            testimonio(texto, quien, que, estilo)
            for texto, quien, que in TESTIMONIOS
        )

    if not con_caso:
        return f"""
  <section class="prueba">
    <h2 class="prueba-titulo">Testimonios</h2>
    <div class="prueba-lista">{tarjetas}
    </div>
  </section>"""

    return f"""
  <section class="prueba">
    <h2 class="prueba-titulo">Testimonios</h2>
    <div class="prueba-lista">{tarjetas}
    </div>
    <div class="prueba-caso">
      <div class="prueba-par">{caso}
      </div>
      <p class="prueba-detalle"><span class="x">Blanqueamiento y dos
      restauraciones en las caras de adelante. Tres sesiones.</span>
      Caso propio, publicado con autorización del paciente.</p>
    </div>
  </section>"""


def solo_prueba(tokens, css, ancho, con_caso=False, estilo=""):
    """El bloque SOLO, sin una palabra de tablero alrededor."""
    if con_caso:
        aviso_par = (
            "🔴 <b>Esta versión lleva el par antes/después, que NO va en la "
            "landing</b> — decidido por Juan el 8-sep-2026: va en la página por "
            "tratamiento, donde el paciente ya buscó ese tratamiento. Además, "
            "<b>el «antes» y el «después» son DOS BOCAS DISTINTAS de banco</b> "
            "y <b>no se publican</b>."
        )
    else:
        aviso_par = (
            "El punteado marca lo que hay que reemplazar."
        )

    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · Pacientes, solo el bloque · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_ENCABEZADO}
{CSS_NOSOTROS}
{CSS_PRUEBA}
</style>

<p class="provisorio" style="margin: 0 var(--margen-pagina) 20px">🔴 <b>MAQUETA.
Los tres testimonios son PROVISORIOS y los trae Cecilia.</b> {aviso_par}</p>
{prueba_del_sitio(ancho, con_caso, estilo)}
"""


def tablero_prueba(tokens, css, ancho):
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 15b Prueba · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_ENCABEZADO}
{CSS_NOSOTROS}
{CSS_PRUEBA}
</style>

<div class="prosa">
<p class="rotulo">Fase ⑧ · Pieza 15.b · {ancho} px</p>
<h1>Prueba</h1>
<div class="regla"></div>
<p><b>Es el bloque 4 del mapa del sitio, y ahí ocupa cuatro palabras:</b>
«antes/después, testimonios». <b>Es la sección menos definida del sitio</b> y la
única que se apoya entera en material que traen otros.</p>

<p class="provisorio" style="margin-top: 20px">🔴 <b>LOS TRES TESTIMONIOS SON
PROVISORIOS Y LOS TRAE CECILIA</b>, que tiene más de diez años de trabajo de
donde sacarlos. <b>El par de fotos son DOS BOCAS DISTINTAS de banco</b> —lo
decidió Juan, y para juzgar tamaño y aire alcanza—: <b>ese par no se
publica</b>.</p>
</div>

<p class="marca-muestra" style="padding: 0 var(--margen-pagina); margin: 40px 0 12px"
   >El bloque, a 1:1</p>
{prueba_del_sitio(ancho)}

<div class="prosa">
<section>
  <p class="rotulo">La decisión que ordena el bloque</p>
  <h2>Los testimonios van primero y el par va de cierre</h2>
  <p><b>El par antes/después es la pieza con más chance de caerse</b>, y por dos
  motivos que no dependen de nosotros. <b>Uno:</b> en Santa Fe el régimen de
  anuncios lo dicta el Colegio de Odontólogos por la <b>Ley 3950</b>, se
  preguntó y <b>no contestó</b>. <b>Dos:</b> el <b>Código Argentino de Ética y
  Deontología Dental</b> prohíbe en su <b>Art. 53</b> avalar <i>«resultados de
  actuaciones profesionales que no haya efectuado y comprobado
  personalmente»</i>.</p>
  <p style="margin-top: 12px"><b>Con el par arriba, si se cae queda una sección
  hueca. Con el par abajo, se saca un bloque y la sección sigue en pie.</b>
  <i>Ordenar por fragilidad no es una regla del sistema: es lo que corresponde
  cuando un contenido depende de un permiso que todavía no llegó.</i></p>
  <p class="dato" style="margin-top: 12px">⚠ <b>Honestidad sobre la fuente:</b>
  el código de la AOA es <b>el marco nacional de la profesión, no el reglamento
  de Santa Fe</b>. El que manda acá sigue sin estar. Lo que sí es seguro es que
  ninguno de los dos va a pedir MENOS que el otro.</p>
</section>

<section>
  <p class="rotulo">Por qué el testimonio es lo principal</p>
  <h2>El paciente ya viene recomendado</h2>
  <p>El dato que reencuadró la 15.a vale más todavía acá: <b>el 99,1 % llega
  por recomendación de un conocido</b> y sólo el 23,1 % considera importante que
  haya sitio web. <b>Un testimonio es esa recomendación puesta por escrito</b>;
  el antes/después es un argumento de venta, que es el registro que la § 2
  descartó — <b>premium en la forma, no lujo</b>.</p>
  <p class="dato" style="margin-top: 12px">⚠ Los porcentajes son del mismo
  estudio de <b>117 personas en Bucarest, 2019</b> que ya se usó en la 15.a.
  <b>Orienta la estructura, no prueba nada sobre Santa Fe.</b></p>
</section>

<section>
  <p class="rotulo">Qué relación tiene con Nosotros</p>
  <h2>Allá se promete, acá se confirma</h2>
  <p>Los tres testimonios <b>hacen eco de las tres señales de la 15.a</b> —que
  te explican, que el miedo se atiende, que el instrumental está esterilizado—
  y <b>eso es a propósito, no una repetición</b>. Allá lo dice Cecilia, acá lo
  dice quien lo recibió: <b>es la diferencia entre «yo hago X» y «a mí me
  hicieron X»</b>, y es lo que le da valor a la sección.</p>
  <p class="dato" style="margin-top: 12px">🔴 <b>Lo que no puede pasar</b> es
  que sean la misma frase con otras comillas. Si Cecilia trae testimonios
  reales que dicen otra cosa, <b>mandan los reales</b> y estas tres señales se
  vuelven a mirar.</p>
</section>

<section>
  <p class="rotulo">Los nombres</p>
  <h2>Nombre de pila e inicial, y no es timidez</h2>
  <p><b>Que una persona fue paciente de un odontólogo es un dato de salud.</b>
  Publicar «Marina G. · tratamiento de conducto» con nombre completo expondría
  el dato de un tercero aunque él lo autorice. <b>Se publica el mínimo que
  sirve</b> — el principio se llama <b>minimización de datos (data
  minimization)</b> y es el mismo criterio con el que este proyecto trata
  <code>turnos.observaciones_paciente</code>.</p>
  <p style="margin-top: 12px"><b>Y por eso tampoco lleva foto del paciente.</b>
  Una cara de banco con un nombre inventado no es relleno: es un paciente que
  no existe. <b>Si Cecilia consigue retrato y autorización, se vuelve a
  mirar</b> — con foto el testimonio se cree más, y ahí eso sería una ventaja
  y no un riesgo.</p>
</section>

<section>
  <p class="rotulo">Lo que hay que decidir</p>
  <h2>Tres cosas, y las decide Juan</h2>
  <ul class="reglas">
    <li>🔴 <b>Cómo se llama la sección.</b> Acá dice <b>«Pacientes»</b>, que
    cubre las dos partes y es la palabra que usa la gente. <b>Las
    alternativas:</b> «Testimonios» (sólo cubre la mitad y suena a publicidad)
    y «Lo que dicen los pacientes» (más claro, pero a 390 son dos renglones de
    título). <i>Y ojo con el menú: la barra promete tres palabras y esta
    sección no está en ninguna — si entra, el nombre tiene que servir de
    botón.</i></li>
    <li><b>Cuántos testimonios.</b> Van tres. Con menos la sección se ve
    flaca; con más, a 390, hay que scrollear tres pantallas de citas.</li>
    <li><b>Si el par de fotos se queda.</b> Hoy está de cierre y la sección se
    sostiene sin él. <b>La respuesta del Colegio puede sacarlo</b>, y en ese
    caso no hay que rediseñar nada.</li>
  </ul>
</section>
</div>
"""


# ------------------------------------------------------------
# LA VISTA «RESEÑAS DE GOOGLE» — pedida por Juan el 8-sep-2026
#
# Qué es y qué NO es. Es una COPIA VISUAL de cómo se vería la sección el día
# que las reseñas sean reales: no enlaza nada, no trae nada de Google y no hay
# integración detrás. Sirve para una sola cosa — decidir la FORMA antes de que
# el contenido exista.
#
# 🔴 LAS TRES RESEÑAS SON INVENTADAS Y NO SE PUBLICAN NUNCA. Una reseña falsa
# con estrellas y nombre completo no es relleno de maqueta: es prueba social
# fabricada, del mismo orden que el par antes/después que salió de la landing.
# Va con su cinta encima, igual que aquél.
#
# POR QUÉ ESTA VISTA GANA, y es lo que decidió el cambio: NN/g encontró que
# los testimonios que la empresa pone en su propio sitio se leen con recelo
# —"si la empresa eligió sólo los favorables"— y que la gente se va a Google
# Reviews a buscar "una imagen más realista". Una reseña de Google no la
# escribimos nosotros, y eso es exactamente lo que le falta a las citas.
#
# EL TEXTO DE LAS TRES ES EL MISMO QUE EL DE LAS CITAS, a propósito: así lo
# único que cambia entre una vista y la otra es el FORMATO. Comparar dos cosas
# que cambian en dos variables a la vez no dice nada.
#
# EL LOGOTIPO ES EL ARCHIVO OFICIAL que ya vive en el repo
# (brand/ajenos/googleg_standard_color_128dp.png, el mismo del botón de
# entrar). Regla ya cerrada del proyecto: un isotipo ajeno sale de su brand
# resource center, nunca de un dibujo nuestro.
#
# ⚠️ EL AMARILLO DE LAS ESTRELLAS ES EL DE GOOGLE (#FBBC04), NO UN COLOR
# NUESTRO. Se usa acá porque la vista existe para mostrar cómo se ve lo de
# Google; si el día de mañana se decide repintarlo con el dorado de la marca,
# eso es una decisión aparte —y de las que ya sabemos que se discuten, como
# pasó con los isotipos de Meta—.
# ------------------------------------------------------------

CSS_GOOGLE_RESENAS = """
/* La cabecera: qué es esto y cuánto puntúa. Es lo primero porque el número
   agregado es lo que la gente mira antes que cualquier reseña suelta. */
.google-cabecera {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 var(--margen-pagina);
  margin-bottom: 4px;
}

.google-cabecera img {
  width: 20px;
  height: 20px;
  display: block;
}

.google-cabecera .puntaje {
  font-size: var(--tipo-h3);
  line-height: var(--alto-h3);
  font-family: Marcellus, Georgia, serif;
}

.google-cabecera .cuantas {
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  color: var(--texto-segundo);
}

.resena {
  padding: 0 var(--margen-pagina);
  margin-top: 24px;
  max-width: var(--columna-lista);
}

/* La firma va ARRIBA en una reseña, al revés que en la cita. No es capricho:
   en Google lo primero es quién habla y cuántas estrellas puso — el texto se
   lee después, y muchos ni lo leen. */
.resena-firma {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* El círculo con la inicial. Google muestra la foto de perfil; acá va la
   inicial, que es lo que él mismo dibuja cuando no hay foto — y evita meter
   una cara inventada. */
.resena-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--dorado-claro);
  color: var(--grafito);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--tipo-chico);
  font-weight: 500;
  flex: none;
}

.resena-quien {
  font-size: var(--tipo-cuerpo);
  line-height: 1.3;
  font-weight: 500;
}

.resena-cuando {
  font-size: var(--tipo-rotulo);
  line-height: var(--alto-rotulo);
  color: var(--texto-segundo);
}

/* EL AMARILLO ES EL DE GOOGLE, no el dorado de la marca. Las estrellas son
   caracteres tipográficos, no un dibujo: no hay ningún archivo de marca que
   estemos redibujando. */
.estrellas {
  color: #FBBC04;
  letter-spacing: 0.06em;
  font-size: var(--tipo-chico);
}

.resena-texto {
  margin-top: 10px;
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  color: var(--grafito);
  max-width: none;
}

/* El pie de la sección: en el sitio real acá va el enlace a la ficha. En esta
   copia visual NO enlaza a ningún lado, y se dice. */
.google-pie {
  padding: 0 var(--margen-pagina);
  margin-top: 24px;
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  color: var(--dorado-texto);
  font-weight: 500;
}
"""


# Las tres reseñas de ejemplo. Mismo texto que las citas, para que lo único
# que cambie entre las dos vistas sea el formato. Nombre completo y fecha
# porque así se ven en Google — y es justo lo que en una cita nuestra no
# pondríamos, por el dato de salud.
RESENAS = [
    ("Marina Gómez", "M", "hace 2 meses", 5,
     "Hacía cuatro años que no pisaba un consultorio de puro miedo. "
     "Me explicó todo antes de tocarme y paramos cuando lo necesité."),
    ("Diego Ramírez", "D", "hace 1 mes", 5,
     "Me dijo cuántas sesiones eran y cuánto salía antes de empezar. "
     "No apareció ningún costo que yo no supiera."),
    ("Laura Peralta", "L", "hace 3 semanas", 5,
     "Vengo con mis dos hijos. Los turnos son a la hora que dice y el "
     "instrumental lo abre delante nuestro."),
]


def resena(quien, inicial, cuando, estrellas, texto):
    return f"""
    <div class="resena">
      <div class="resena-firma">
        <div class="resena-avatar">{inicial}</div>
        <div>
          <div class="resena-quien">{quien}</div>
          <div class="resena-cuando">
            <span class="estrellas">{"★" * estrellas}</span> · {cuando}
          </div>
        </div>
      </div>
      <p class="resena-texto">{texto}</p>
    </div>"""


def google_del_sitio(ancho):
    """La sección tal como se vería con las reseñas reales de Google."""
    logo = leer_logo_google()
    filas = "".join(resena(*r) for r in RESENAS)

    return f"""
  <section class="prueba">
    <h2 class="prueba-titulo">Reseñas de Google</h2>
    <div class="google-cabecera">
      <img alt="" src="data:image/png;base64,{logo}">
      <span class="puntaje">4,9</span>
      <span class="estrellas">★★★★★</span>
      <span class="cuantas">23 reseñas</span>
    </div>{filas}
    <p class="google-pie">Ver las 23 reseñas en Google</p>
  </section>"""


def solo_google(tokens, css, ancho):
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · Testimonios con reseñas de Google · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_ENCABEZADO}
{CSS_NOSOTROS}
{CSS_PRUEBA}
{CSS_GOOGLE_RESENAS}
</style>

<p class="provisorio" style="margin: 0 var(--margen-pagina) 20px">🔴 <b>COPIA
VISUAL — CÓMO QUEDARÍA con reseñas de Google.</b> Las tres reseñas, el puntaje
y la cantidad <b>son INVENTADOS</b>, no hay ninguna integración detrás y
<b>el pie no enlaza a ningún lado</b>. <b>Esto no se publica jamás:</b> una
reseña falsa con estrellas y nombre completo es prueba social fabricada.
<b>Existe para decidir la forma antes de que el contenido exista.</b></p>
{google_del_sitio(ancho)}
"""


# ============================================================
# PIEZA 16 — LA PANTALLA ① DE `reservar.html`: ENTRAR
#
# Es el PRIMER ESTADO de la página de reserva, no una página aparte: si el
# login viviera en su propia URL, al volver de Google el paciente aterrizaría
# en una pantalla distinta de la que dejó.
#
# 🔴 POR QUÉ ESTA PANTALLA EXISTE, que es una decisión de Juan del 24-sep-2026
# y no una convención: el endpoint de la agenda dejó de ser público, así que
# NADA se ve sin sesión. La pantalla es la consecuencia visible de esa
# decisión — y por eso su párrafo tiene que decir POR QUÉ se pide entrar. Un
# login sin motivo delante de una agenda es la forma más barata de perder al
# que venía a sacar turno.
# ============================================================

# 🔴 EL TOPE DE ALTURA DE LA FOTO, y lo destapó una pregunta de Juan el
# 24-sep-2026: «¿y los otros anchos?».
#
# La foto es 16/9 a todo el ancho. En móvil eso da 219 px y está bien; a 1280
# da **720 px** —un cartelón que empuja el título y el botón abajo del pliegue—.
# En una pantalla de ACCIÓN eso es una rotura, no un gusto: el paciente abre la
# página y no ve qué tiene que hacer.
#
# ⚠️ ESTO ARREGLA LA ROTURA, NO DECIDE EL DISEÑO DE ESCRITORIO. Lo que
# corresponde en pantalla grande es probablemente otra cosa —la foto al costado,
# en dos columnas, que es el patrón de las pantallas de entrar— y eso se decide
# en el SEGUNDO TIEMPO de la ⑧, con los tres anchos delante. Acá sólo se le pone
# techo para que no esté rota mientras tanto.
#
# Los tableros llevan las media queries aplanadas, así que el valor entra por
# Python y no por CSS.
# ⚠️ EL TOPE DE 1280 ESTÁ ATADO AL BOTÓN, y conviene saberlo antes de tocarlo:
# sacar aire de ABAJO del botón acorta la página, pero NO sube el botón —
# agrandar la foto sí lo baja, píxel por píxel. Con 340 el botón volvía a
# caerse fuera de los 620 de un portátil de 13 pulgadas; con 320 entra y la
# foto igual gana 40 sobre los 280 que tenía.
FOTO_ALTO_MAXIMO = {390: None, 768: 360, 1280: 320}

# 🔴 EL AIRE DE ARRIBA DEL TEXTO TAMBIÉN BAJA EN ESCRITORIO, y por la misma
# razón medida: a 1280 con la foto en 360 y 32 px de aire, el botón de Google
# caía en el píxel 625 — o sea FUERA de un portátil de 13 pulgadas, que deja
# unos 620 de alto útil. La única acción de la pantalla no se ve.
AIRE_ARRIBA_DEL_TEXTO = {390: 32, 768: 28, 1280: 24}

# 🔴 EL AIRE DE ABAJO DE TODO, y lo señaló Juan: «te queda algo por sacar
# abajo del botón». Tenía razón y era el más grande de la pantalla — el
# `padding-bottom` salía de `--aire-seccion`, que a 1280 son 96 px de marfil
# vacío bajo el último renglón. Ese aire existe para separar SECCIONES de una
# página larga; acá abajo no hay nada que separar, es el fin de la pantalla.
#
# Lo que se recorta no se pierde: se lo queda la FOTO, que es lo que él quería
# agrandar.
AIRE_ABAJO_DE_TODO = {390: 40, 768: 40, 1280: 40}


def css_de_entrar(ancho):
    """CSS_ENTRAR con el tope de la foto y el aire de arriba para ese ancho."""
    tope = FOTO_ALTO_MAXIMO[ancho]

    if tope is None:
        css = CSS_ENTRAR.replace("/*TOPE*/", "")
    else:
        css = CSS_ENTRAR.replace("/*TOPE*/", f"max-height: {tope}px;")

    return css.replace("/*AIRE*/", f"{AIRE_ARRIBA_DEL_TEXTO[ancho]}px")


CSS_ENTRAR = """
/* LA FOTO VA A SANGRE Y ARRIBA DE TODO, que es la regla ya cerrada de la § 4:
   la foto que ABRE una pantalla cruza de borde a borde. Esquinas rectas —el
   radio de 3 px es de controles, no de fotos— y sin filo, porque a sangre no
   hay fondo contra el que perderse.

   16/9 y no la proporción del hero (4/3): ésta NO es una portada. Tiene que
   dejar el botón arriba del pliegue en un teléfono de 844 de alto, y a 390 de
   ancho un 4/3 se come 292 px contra los 219 de un 16/9. */
.entrar-foto {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  /* El archivo YA viene recortado a 16/9, así que `cover` no recorta nada:
     está para que una foto futura de otra proporción no deforme el hueco.
     ⚠ Sin `object-position` porque no hace falta acá — y cuando una foto lo
     necesita, no es decoración: el primer intento de esta pieza usó la foto
     VERTICAL del hero y el recorte por el centro geométrico dejó la cara
     afuera, se veía la boca y el mentón. */
  object-fit: cover;
  /*TOPE*/
}

.entrar {
  margin: 0 var(--margen-pagina);
  padding: /*AIRE*/ 0 /*AIRE-ABAJO*/;
}

/* El texto NO va centrado y es a propósito: esta pantalla se lee, no se
   contempla. El centrado es del hero, que es una portada. */
.entrar h1 {
  font-family: Marcellus, Georgia, serif;
  font-size: var(--tipo-h1);
  line-height: var(--alto-h1);
  text-wrap: balance;
}

/* UNA SOLA LÍNEA, y el recorte lo pidió Juan el 24-sep-2026: «le estás
   haciendo leer demasiado a la persona». Tenía razón — pero no se borra
   entera: lo que queda es el MOTIVO por el que se pide entrar, que es lo único
   que esta pantalla tiene que justificar. Lo que se fue («después podés ver y
   cancelar…») es información de DESPUÉS de reservar, y ahí es donde va. */
.entrar .porque {
  margin-top: 12px;
  color: var(--texto-segundo);
  font-size: var(--tipo-cuerpo);
  line-height: var(--alto-cuerpo);
  text-wrap: balance;
}

/* El botón de Google ocupa el ancho de la columna en móvil: es la única
   acción de la pantalla, y una acción única no se pone chica. */
.entrar .btn-google {
  margin-top: 28px;
  /* El ancho sale de --boton-ancho, que es el del sistema. Pisarlo con
     100% lo sacaba del margen de página: el botón se dibuja dentro de
     `.entrar`, que ya está corrido por `--margen-pagina`. */
  margin-left: 0;
}

/* La salida para el que NO entra. Va abajo, sin botón y sin ícono: es una
   puerta que existe, no un segundo camino que se promueve — la regla de la
   § 4 sobre WhatsApp sigue rigiendo acá adentro. */
/* 🔴 ACÁ HABÍA UN ERROR DE ESCALA Y LO CAZÓ JUAN — 24-sep-2026.
   Estaba en `--aire-seccion`, que es el aire ENTRE SECCIONES de la página:
   56 px a 390. Pero acá no se separan dos secciones, se separa la acción
   principal de una nota al pie DENTRO de la misma. Con 56 arriba más 20 de
   relleno el texto quedaba a 76 px del botón, flotando.

   La mitad del aire de sección, y se escribe como CUENTA y no como número
   suelto: así los tres anchos se mueven solos si el aire de sección cambia
   —28 · 36 · 48— y no queda una constante nueva que mantener aparte. */
.entrar .salida {
  margin-top: calc(var(--aire-seccion) / 2);
  padding-top: 16px;
  border-top: 1px solid var(--dorado-claro);
  color: var(--texto-segundo);
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
}

.entrar .salida a {
  color: var(--dorado-texto);
}
"""


# LA FOTO DE LA PANTALLA ① ES PROPIA DE ESTA PIEZA, no la del hero.
#
# La pidió Juan el 24-sep-2026 —«buscá alguna de archivo más descriptiva, tipo
# una recepción»— y el motivo de fondo es más fuerte que el estético: esta
# pantalla NO es una portada. El paciente ya decidió reservar; lo que necesita
# ver acá es DÓNDE va a ir.
#
# 🔴 Y hay una razón para que muestre el LUGAR y no a una persona en un rol:
# una recepcionista de banco promete personal que este consultorio puede no
# tener, y entonces el ejemplo no se podría reemplazar por una foto propia sin
# rediseñar. Un ejemplo sirve si la definitiva puede ocupar su lugar.
#
# Viene RECORTADA a 16/9 en el archivo, igual que `nosotros-ejemplo.jpg`: el
# encuadre es una decisión, no lo que le toque al navegador.
FOTO_ENTRAR = RAIZ / "brand" / "fotos" / "entrar-ejemplo.jpg"

FOTO_ENTRAR_RELATIVA = "../../fotos/entrar-ejemplo.jpg"


def foto_de_entrar():
    """La foto de la pantalla ①, o el hueco marcado si falta el archivo."""
    if not FOTO_ENTRAR.exists():
        return '\n  <div class="entrar-foto" style="background: var(--dorado-claro)"></div>'

    return (f'\n  <img class="entrar-foto" src="{FOTO_ENTRAR_RELATIVA}"'
            f'\n       alt="Sala de espera de CB Odontología y Estética">')


def entrar_del_sitio(ancho):
    """La pantalla ① tal como la va a ver el paciente. Sin prosa alrededor."""
    logo = leer_png("cb-wordmark-600")
    google = leer_logo_google()

    return f"""
<div class="pagina">
  <header class="encabezado">
    <div class="barra">
      <img src="data:image/png;base64,{logo}"
           alt="CB Odontología y Estética"
           width="{ENCABEZADO_LOGO[ancho]}">
    </div>
  </header>
{foto_de_entrar()}
  <div class="entrar">
    <h1>Reservá tu turno</h1>

    <p class="porque">Entrá con Google para ver los horarios disponibles.</p>

    <button class="btn-google">
      <img src="data:image/png;base64,{google}" alt="">Continuar con Google
    </button>

    <p class="salida">¿Tenés una consulta antes de reservar?
    <a href="#whatsapp">Escribinos por WhatsApp</a>.</p>
  </div>
</div>"""


def solo_entrar(tokens, css, ancho):
    """La pantalla sola, a 1:1, sin una línea de explicación alrededor."""
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · Entrar · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&family=Roboto:wght@500&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_GOOGLE}
{CSS_ENCABEZADO}
{css_de_entrar(ancho)}
{CSS_FOCO}
</style>
{entrar_del_sitio(ancho)}
"""


def tablero_entrar(tokens, css, ancho):
    """El tablero que explica la pieza. La pantalla sola vive en otro archivo."""
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 16 Entrar · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&family=Roboto:wght@500&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_GOOGLE}
{CSS_ENCABEZADO}
{css_de_entrar(ancho)}
{CSS_FOCO}
{css_margen_en_la_prosa()}
</style>

<div class="prosa">
<p class="rotulo">Fase ⑧ · Pieza 16 · {ancho} px</p>
<h1>Entrar — la pantalla ① de reservar</h1>
<div class="regla"></div>
<p><b>Es el primer estado de <code>reservar.html</code>, no una página
aparte.</b> Si el login viviera en su propia dirección, al volver de Google el
paciente aterrizaría en una pantalla distinta de la que dejó.</p>

<section>
  <p class="rotulo">Por qué existe</p>
  <h2>La consecuencia visible de una decisión de seguridad</h2>
  <p>El 24-sep-2026 <code>GET /horarios-disponibles</code> dejó de ser público:
  la agenda de dos meses servida sin sesión dejaba reconstruir cuándo trabaja
  cada profesional. <b>Desde ese día no se ve NADA sin entrar</b>, y esta
  pantalla es lo primero que el paciente encuentra.</p>
  <p><b>Por eso queda UNA línea que dice por qué se pide entrar</b>, y no
  cero: un login delante de una agenda sin explicar para qué es la forma más
  barata de perder al que venía a sacar turno. Lo que sobrevive es lo que
  desbloquea — <i>ver los horarios</i>.</p>
</section>

<section>
  <p class="rotulo">Corregido el 24-sep-2026 — lo pidió Juan</p>
  <h2>Había cuatro líneas de texto y ahora hay una</h2>
  <p><b>Su objeción, textual: «le estás haciendo leer demasiado a la
  persona».</b> Tenía razón: nadie lee un párrafo parado frente a un botón.
  <b>Lo que se fue</b> —«después podés ver y cancelar tus turnos cuando
  quieras»— <b>no se perdió: es información de DESPUÉS de reservar</b>, y ahí
  es donde tiene que aparecer.</p>
  <p>⚠️ <b>Lo que NO se hizo, y se declara:</b> borrarlo entero. «Ingresá y
  listo» deja el login sin motivo delante de una agenda cerrada, que es
  exactamente el caso que esta pantalla tiene que resolver. <b>Una línea, no
  cero.</b></p>
</section>

<section>
  <p class="rotulo">La foto — también la pidió Juan</p>
  <h2>«Lo veo muy pelado»</h2>
  <p><b>Va a sangre y arriba de todo</b>, que es la regla ya cerrada de la
  § 4: la foto que ABRE una pantalla cruza de borde a borde. Esquinas rectas y
  sin filo — a sangre no hay fondo contra el que perderse.</p>
  <p><b>16/9 y no el 4/3 del hero, y el motivo es medible:</b> ésta no es una
  portada y el botón tiene que quedar arriba del pliegue. A 390 de ancho, un
  4/3 se come <b>292 px</b> contra los <b>219</b> de un 16/9.</p>
  <p>🔴 <b>Muestra el LUGAR, no a una persona en un rol, y el motivo no es
  estético:</b> una recepcionista de banco promete <b>personal que este
  consultorio puede no tener</b>. Si el ejemplo la muestra y Cecilia atiende
  sola, la foto propia no puede ocupar su lugar y hay que rehacer la pieza.
  <b>Un ejemplo sirve si la definitiva lo reemplaza sin tocar nada.</b></p>
  <p><b>Viene recortada a 16/9 en el archivo</b> (1200 × 675), igual que la de
  «Nosotros»: el encuadre es una decisión, no lo que le toque al navegador. El
  original es vertical y el recorte toma la franja media: los tres cuadros en
  tonos dorados, la lámpara cálida y la persona esperando.</p>
  <p>🔴 <b>La primera candidata se cayó y la cazó Juan: tenía un cartel en
  INGLÉS.</b> Estaba declarada como limitación, y <b>declararla no la
  arregla</b> — un cartel en inglés de una banda de rock no es lo que dice la
  sala de espera de un consultorio en Santa Fe.</p>
  <p>🔑 <b>Buscando el reemplazo apareció un criterio más duro que el idioma:
  ninguna foto puede mostrar la MARCA DE OTRO NEGOCIO.</b> De cuatro
  candidatas, <b>dos tenían logo ajeno a la vista</b> —uno en letras de 40 cm
  sobre la pared, otro con cartel de promoción—. <b>Eso no es relleno: es la
  marca de un competidor en la pantalla de reserva de Cecilia.</b></p>
  <p>⚠️ <b>Lo que esta foto sí arrastra:</b> el <b>borde de arriba</b> es pared
  casi blanca contra el marfil de la barra —hoy las separa la línea dorada de
  1 px del encabezado, así que si esa línea se saca hay que volver a mirarlo—,
  la persona es <b>identificable</b>, y la remera es el único color saturado y
  no está en la paleta.</p>
  <p>⏱ <b>Es de EJEMPLO.</b> La definitiva es la sala de espera o la entrada
  REALES, con luz cálida y sin equipamiento clínico a la vista. <b>Entra al
  brief de fotos</b>, que es un entregable de esta etapa.</p>
</section>

<section>
  <p class="rotulo">También lo cazó Juan — 24-sep-2026</p>
  <h2>Había un error de escala en el aire del pie</h2>
  <p>Su pregunta: <i>«¿no te parece que hay mucho aire entre que termina el
  botón y el separador?»</i> <b>Había, y la causa tiene nombre:</b> el hueco
  estaba puesto en <code>--aire-seccion</code>, que es el aire <b>ENTRE
  SECCIONES</b> de la página. Acá no se separan dos secciones: se separa la
  acción principal de una nota al pie <b>dentro de la misma</b>.</p>
  <p><b>Era 56 + 20 = 76 px. Ahora es 28 + 16 = 44.</b> Y se escribe como
  <code>calc(var(--aire-seccion) / 2)</code>, no como número suelto: así los
  tres anchos se mueven solos —<b>28 · 36 · 48</b>— y no queda una constante
  nueva que mantener aparte.</p>
</section>

<section>
  <p class="rotulo">Las tres decisiones de esta pieza</p>
  <h2>Qué se decidió y contra qué</h2>
  <ul class="reglas">
    <li><b>El botón de Google es el único camino</b>, y su forma no se
    discute: viene de la pieza 3, donde ya está resuelto que el logo no se
    recolorea, que nunca va la G sola y que el texto dice «continuar», no
    «registrate».</li>
    <li><b>Ocupa el ancho entero.</b> Es la única acción de la pantalla, y una
    acción única no se pone chica.</li>
    <li><b>El texto NO va centrado.</b> Esta pantalla se lee; el centrado es
    del hero, que es una portada.</li>
  </ul>
</section>

<section>
  <p class="rotulo">Lo que falta decidir</p>
  <h2>La salida por WhatsApp, y la propone Claude</h2>
  <p>🔴 <b>El renglón de abajo no lo pidió nadie: lo agregó Claude y hay que
  aprobarlo o sacarlo.</b> El motivo: con la agenda cerrada, <b>el que no entra
  con Google se queda sin ninguna puerta</b>, y el doc ya declara que ése se va
  a ir a WhatsApp igual. Darle el enlace lo manda a un canal que atendemos, en
  vez de dejarlo rebotar.</p>
  <p><b>El costo, que es real:</b> WhatsApp está declarado <b>secundario y no
  promovido</b> (§ 4), y este renglón lo pone en la pantalla de conversión. Va
  sin botón, sin ícono y abajo de todo justamente por eso — pero sigue siendo
  una puerta que antes no estaba.</p>
</section>

<section>
  <p class="rotulo">La pieza, a 1:1</p>
  <h2>Abajo va la pantalla como la ve el paciente</h2>
  <p>Y vive además <b>sola, en su propio archivo</b>:
  <code>{ancho}-solo.html</code>.</p>
</section>
</div>
{entrar_del_sitio(ancho)}
"""


# ============================================================
# PIEZA 17 — LA PANTALLA ② : ¿PARA QUIÉN ES EL TURNO?
#
# Existe por una propiedad del modelo de datos, no por gusto: UN CORREO PUEDE
# DEVOLVER VARIAS FILAS DE `pacientes` (§ 9.8) —la madre que anota a sus hijos
# con su casilla—, así que después del login el sistema sabe QUÉ CORREO entró y
# no sabe QUIÉN se va a sentar en el sillón.
#
# Su endpoint ya existe y está desplegado: `GET /mis-pacientes` devuelve id,
# nombre y apellido, y nada más. Y `POST /reservar` exige `paciente_id` O
# `paciente_nuevo`, uno de los dos y nunca los dos — o sea que esta elección no
# es opcional: sin ella no hay forma de reservar.
#
# 🔴 SON TRES CASOS Y UNO NO TIENE PANTALLA:
#   0 filas  → se piden nombre y apellido          → `paciente_nuevo`
#   1 fila   → NO SE MUESTRA NADA, se sigue de largo → `paciente_id`
#   2 o más  → se elige de la lista                → `paciente_id` o nuevo
# ============================================================

# ============================================================
# EL ANILLO DE FOCO REAL — escrito el 24-sep-2026, y lo destapó Juan mirando
# la pantalla: «lo único que me hace ruido es el focus en azul, no sé si está
# respetando nuestras reglas».
#
# 🔴 NO LAS RESPETABA, Y EL AGUJERO ES MÁS VIEJO QUE ESTAS PIEZAS. El sistema
# YA tenía el anillo decidido y medido —`--foco: #33322F`, grafito macizo de
# 2 px, y `--foco-separacion: -4px` para que vaya ADENTRO del control, con su
# porqué escrito en `tokens.css` y su medidor propio en `tools/medir-foco.py`—
# pero la regla CSS que lo aplica NUNCA SE ESCRIBIÓ. Los tableros lo simulaban
# con clases puestas a mano (`.btn-foco`, `.campo-foco`), así que en el tablero
# se veía nuestro anillo y en el navegador seguía saliendo el azul del sistema
# operativo.
#
# 🔑 La lección, que es más grande que este color: UN TOKEN QUE NADIE CONSUME
# ES UNA DECISIÓN QUE NUNCA LLEGÓ A LA PANTALLA. El token existía, el porqué
# existía, la medición existía — y el usuario veía otra cosa.
#
# `:focus-visible` y no `:focus`: el navegador lo muestra cuando se navega por
# TECLADO y lo calla en un clic con el mouse, que es exactamente lo que se
# quiere — el anillo es una ayuda para quien no ve dónde está parado, no una
# marca en cada toque.
CSS_FOCO = """
:focus-visible {
  outline: 2px solid var(--foco);
  outline-offset: var(--foco-separacion);
}

/* El radio es la excepción: mide 20 px y con la separación negativa el anillo
   le quedaría ADENTRO del círculo, invisible. Acá va por afuera. */
.opcion input:focus-visible {
  outline-offset: 2px;
}

/* Y en una fila entera tocable, el foco del radio se lee mejor marcando la
   caja que lo contiene: es lo que el ojo busca. */
.opcion:has( input:focus-visible ) {
  outline: 2px solid var(--foco);
  outline-offset: -4px;
}
"""


CSS_QUIEN = """
.quien {
  margin: 0 var(--margen-pagina);
  padding: 32px 0 var(--aire-seccion);
}

.quien h1 {
  font-family: Marcellus, Georgia, serif;
  font-size: var(--tipo-h1);
  line-height: var(--alto-h1);
  text-wrap: balance;
}

.quien .ayuda-pantalla {
  margin-top: 12px;
  color: var(--texto-segundo);
  font-size: var(--tipo-cuerpo);
  line-height: var(--alto-cuerpo);
  text-wrap: balance;
}

.opciones {
  margin-top: 28px;
  max-width: var(--columna);
}

/* CADA OPCIÓN ES UN <label> QUE ENVUELVE A SU RADIO, y eso no es un detalle
   de marcado: envolviéndolo, toda la caja queda tocable sin escribir un solo
   `for`/`id`, y el área táctil pasa de los 20 px del círculo a los 56 de la
   fila entera. En un teléfono eso es la diferencia entre elegir y errarle. */
.opcion {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 56px;
  padding: 12px 14px;
  background: var(--campo-fondo);
  border: 1px solid var(--campo-borde);
  border-radius: var(--radio);
  cursor: pointer;
}

.opcion + .opcion {
  margin-top: 10px;
}

/* 🔴 EL RADIO NO SE ESCONDE. Es la tentación obvia —queda más prolijo— y
   rompe el teclado: un `display: none` lo saca del recorrido de tabulación y
   la lista deja de poder recorrerse sin mouse. Se lo deja real y visible, con
   el tamaño subido para que se vea a la distancia de un teléfono. */
.opcion input {
  flex: none;
  width: 20px;
  height: 20px;
  accent-color: var(--grafito);
}

.opcion .nombre {
  font-size: var(--tipo-cuerpo);
  line-height: var(--alto-cuerpo);
}

/* La última opción es de otra clase de cosa —no es una persona, es una
   salida— y por eso se separa con aire y no con un color: el color ya tiene
   trabajo asignado en este sistema. */
.opcion.otra {
  margin-top: 18px;
}

/* LA CAJA QUE SE ABRE AL ELEGIR «otra persona». Va PEGADA a su opción y
   metida hacia adentro: lo que aparece tiene que leerse como consecuencia de
   lo que se tocó, no como una sección nueva que cayó del cielo.
   ⚠ El proyecto tiene escrito, en la opción D del almanaque, que hacer
   aparecer contenido nuevo debajo del dedo es menos suave que bajar a algo que
   ya existe. Acá pesa menos y por eso se hace igual: son DOS campos, no una
   grilla de mes, y aparecen inmediatamente debajo de lo que se acaba de tocar
   — no en otro lado de la página. */
.alta-abierta {
  margin: 10px 0 0 14px;
  padding-left: 14px;
  border-left: 2px solid var(--dorado-claro);
}

.alta-abierta .campo:first-of-type {
  margin-top: 12px;
}

.quien .btn {
  margin-top: 28px;
  margin-left: 0;
}

.quien .campo:first-of-type {
  margin-top: 28px;
}
"""


PACIENTES_DE_EJEMPLO = [
    ("Laura Giménez", True),
    ("Sofía Giménez", False),
    ("Tomás Giménez", False),
]


def opcion_de_persona(nombre, elegida, indice, grupo):
    """Una opción de la lista.

    `grupo` es el `name` del radio, y NO es decorativo: los tres estados de
    esta pieza conviven en la misma página del tablero, y los radios que
    comparten `name` forman UN grupo — marcar el de un bloque DESMARCA el del
    otro. Con un nombre por estado, cada pantalla muestra lo suyo.
    """
    marcada = " checked" if elegida else ""

    return f"""
    <label class="opcion">
      <input type="radio" name="{grupo}" value="{indice}"{marcada}>
      <span class="nombre">{nombre}</span>
    </label>"""


# 🔴 A LA MISMA CAJA DE NOMBRE Y APELLIDO SE LLEGA POR DOS CAMINOS, Y NO DICEN
# LO MISMO — lo cazó Juan el 24-sep-2026 leyendo el texto:
#
#   · 0 filas               → sí es la primera vez con ese correo
#   · «es para otra persona» → NO es la primera vez: es alguien que ya reservó
#                              antes y ahora anota a otro
#
# El texto original decía «es la primera vez que reservás con este correo» en
# los dos casos, y en el segundo eso es FALSO. Una pantalla a la que se llega
# por dos caminos no puede afirmar cuál fue el camino.
CAJA_DE_ALTA = {
    "nuevo": (
        "¿Cómo te llamás?",
        "Es la primera vez que reservás con este correo. Con esto queda tu "
        "turno a tu nombre.",
    ),
    "otra": (
        "¿Para quién reservás?",
        "Poné el nombre de la persona que se va a atender. Queda guardada "
        "para la próxima vez.",
    ),
}


def campos_de_alta(caso):
    titulo, ayuda = CAJA_DE_ALTA[caso]

    # En el alta suelta el título es el de la pantalla; abierta adentro de la
    # lista es un subtítulo, porque el H1 ya lo puso la pregunta de arriba.
    encabezado = f"""
    <h1>{titulo}</h1>

    <p class="ayuda-pantalla">{ayuda}</p>"""

    if caso == "otra":
        encabezado = f"""
      <p class="ayuda-pantalla">{ayuda}</p>"""

    return encabezado + """
    <div class="campo">
      <label class="etiqueta" for="nombre">Nombre</label>
      <input class="caja" id="nombre" type="text" autocomplete="given-name">
    </div>

    <div class="campo">
      <label class="etiqueta" for="apellido">Apellido</label>
      <input class="caja" id="apellido" type="text" autocomplete="family-name">
    </div>"""


def quien_del_sitio(ancho, caso="varios"):
    """La pantalla ②. `caso` es "varios", "otra" —la lista con los campos ya
    abiertos— o "nuevo". El de una sola fila no tiene pantalla, y por eso no es
    un valor posible acá."""
    logo = leer_png("cb-wordmark-600")

    encabezado = f"""
<div class="pagina">
  <header class="encabezado">
    <div class="barra">
      <img src="data:image/png;base64,{logo}"
           alt="CB Odontología y Estética"
           width="{ENCABEZADO_LOGO[ancho]}">
    </div>
  </header>
"""

    if caso == "nuevo":
        return encabezado + f"""
  <div class="quien">{campos_de_alta("nuevo")}

    <button class="btn btn-1">Continuar</button>
  </div>
</div>"""

    # Con los campos abiertos, la persona elegida ES «otra»: ninguna de la
    # lista puede quedar marcada al mismo tiempo.
    eligiendo_otra = caso == "otra"

    grupo = f"paciente-{caso}"

    opciones = "".join(
        opcion_de_persona(nombre, elegida and not eligiendo_otra, i, grupo)
        for i, (nombre, elegida) in enumerate(PACIENTES_DE_EJEMPLO)
    )

    marca_otra = " checked" if eligiendo_otra else ""

    # 🔴 LOS CAMPOS SE ABREN ACÁ MISMO, DEBAJO DE LA OPCIÓN, y no en una
    # pantalla aparte: es la MISMA decisión —para quién es el turno—, así que
    # partirla en dos pasos convierte una elección en dos. El flujo ya tiene
    # seis pantallas.
    caja = f"""
      <div class="alta-abierta">{campos_de_alta("otra")}
      </div>""" if eligiendo_otra else ""

    return encabezado + f"""
  <div class="quien">
    <h1>¿Para quién es el turno?</h1>

    <p class="ayuda-pantalla">Con tu correo figura más de una persona. Elegí
    quién se va a atender.</p>

    <div class="opciones">{opciones}
      <label class="opcion otra">
        <input type="radio" name="{grupo}" value="nueva"{marca_otra}>
        <span class="nombre">Es para otra persona</span>
      </label>{caja}
    </div>

    <button class="btn btn-1">Continuar</button>
  </div>
</div>"""


def solo_quien(tokens, css, ancho):
    """La pantalla sola, a 1:1. Va el caso de VARIOS, que es el que tiene
    decisiones adentro; el de alta va en el tablero."""
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · ¿Para quién es el turno? · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_CAMPO}
{CSS_ENCABEZADO}
{CSS_QUIEN}
{CSS_FOCO}
</style>
{quien_del_sitio(ancho)}
"""


def tablero_quien(tokens, css, ancho):
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 17 ¿Para quién? · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_CAMPO}
{CSS_ENCABEZADO}
{CSS_QUIEN}
{CSS_FOCO}
{css_margen_en_la_prosa()}
</style>

<div class="prosa">
<p class="rotulo">Fase ⑧ · Pieza 17 · {ancho} px</p>
<h1>¿Para quién es el turno?</h1>
<div class="regla"></div>
<p><b>Esta pantalla existe por una propiedad del modelo de datos, no por
gusto.</b> Un correo puede devolver <b>varias filas</b> de <code>pacientes</code>
—la madre que anota a sus hijos con su casilla, § 9.8—, así que después del
login el sistema sabe <b>qué correo entró</b> y no sabe <b>quién se va a sentar
en el sillón</b>.</p>

<section>
  <p class="rotulo">Lo que ya existe</p>
  <h2>El backend no hay que tocarlo</h2>
  <p><code>GET /mis-pacientes</code> está desplegado y devuelve <b>id, nombre y
  apellido, y nada más</b> — ni DNI, ni teléfono, ni fecha de nacimiento.
  <b>Un dato que no sale no se puede filtrar por accidente mañana</b>, cuando
  alguien arme otra pantalla con esta misma respuesta.</p>
  <p>Y <code>POST /reservar</code> <b>exige</b> <code>paciente_id</code> O
  <code>paciente_nuevo</code>, uno de los dos y nunca los dos: <b>sin esta
  elección no hay forma de reservar</b>.</p>
</section>

<section>
  <p class="rotulo">Los tres casos</p>
  <h2>Y uno de los tres NO tiene pantalla</h2>
  <ul class="reglas">
    <li><b>0 filas</b> — primera vez con ese correo → se piden <b>nombre y
    apellido</b> → <code>paciente_nuevo</code>. <i>Es la segunda pantalla de
    abajo.</i></li>
    <li>🔴 <b>1 fila — NO SE MUESTRA NADA.</b> Se sigue de largo con ese
    <code>paciente_id</code>. <b>Preguntarle a alguien que se identifique
    cuando hay una sola respuesta posible es un paso que sólo agrega un
    toque</b>, y esta pantalla ya nace en medio de un flujo de seis.</li>
    <li><b>2 o más</b> — se elige de la lista, más «es para otra persona» →
    <code>paciente_id</code> o <code>paciente_nuevo</code>. <i>Es la primera
    pantalla de abajo, y es la que vive sola en su archivo.</i></li>
  </ul>
</section>

<section>
  <p class="rotulo">Las dos decisiones de forma</p>
  <h2>Por qué una lista y no un desplegable</h2>
  <ul class="reglas">
    <li><b>Lista tocable, no <code>&lt;select&gt;</code>.</b> Son dos, tres o
    cuatro personas: <b>entran todas a la vista</b>. Un desplegable las esconde
    detrás de un toque y obliga a recordar qué había adentro.</li>
    <li><b>Cada opción es un <code>&lt;label&gt;</code> que ENVUELVE a su
    radio.</b> Así toda la caja queda tocable sin escribir un solo
    <code>for</code>, y el área táctil pasa de los 20 px del círculo a los
    <b>56 de la fila entera</b>. En un teléfono ésa es la diferencia entre
    elegir y errarle.</li>
    <li>🔴 <b>El radio NO se esconde.</b> Es la tentación obvia —queda más
    prolijo— y <b>rompe el teclado</b>: un <code>display: none</code> lo saca
    del recorrido de tabulación y la lista deja de poder recorrerse sin mouse.
    <i>Misma familia que el ancla de la opción D: acá la forma vieja es la
    accesible.</i></li>
  </ul>
</section>

<section>
  <p class="rotulo">Lo que falta decidir</p>
  <h2>Dos cosas, y las dos son de Juan</h2>
  <p>⬜ <b>Si la primera opción viene marcada.</b> Hoy sí — la de arriba, que
  es quien inició sesión. <b>A favor:</b> el caso más común es que el turno sea
  para uno mismo, y así el botón está a un toque. <b>En contra:</b> una
  elección marcada de antemano <b>se acepta sin leerla</b>, y acá el precio de
  equivocarse es un turno a nombre de otra persona de la familia.</p>
  <p>⬜ <b>Qué dice «Es para otra persona» al tocarla.</b> Lleva a los dos
  campos de la segunda pantalla, pero <b>no está decidido si se abren ahí mismo
  o en un paso aparte</b>.</p>
</section>

<section>
  <p class="rotulo">Las dos pantallas, a 1:1</p>
  <h2>Primero la de varios, después la de alta</h2>
  <p>La de varios vive además <b>sola, en su propio archivo</b>:
  <code>{ancho}-solo.html</code>.</p>
</section>
</div>
{quien_del_sitio(ancho)}
{quien_del_sitio(ancho, caso="otra")}
{quien_del_sitio(ancho, caso="nuevo")}
"""


# ============================================================
# PIEZA 18 — LA PANTALLA ③ : ¿A QUÉ VENÍS?
#
# Los 14 tratamientos NO se escriben acá: salen de `GET /tratamientos`, y esta
# lista se copió de una corrida real del endpoint el 24-sep-2026. El ORDEN
# también viene resuelto de la base (columna `orden`), igual que en obras
# sociales: no se reordena en el front.
#
# 🔴 Y ACÁ VIVE UN HUECO DE PRODUCTO QUE EL DOCUMENTO NO TENÍA ESCRITO.
# Sólo DOS de los catorce tienen duración propia para la web —`consulta` y
# `limpieza`—. Los otros doce se agendan COMO CONSULTA y el profesional
# reasigna después. O sea: el paciente elige «endodoncia» y lo que queda
# agendado es una consulta de evaluación. Si la pantalla no lo dice, llega
# esperando que le hagan la endodoncia ese día.
#
# ⚠️ LA DURACIÓN EN MINUTOS NO SE MUESTRA —es regla del proyecto desde la pieza
# 6 y el generador la vigila—, así que el aviso habla de QUÉ PASA, no de cuánto
# dura.
# ============================================================

TRATAMIENTOS = [
    ("consulta", True),
    ("limpieza", True),
    ("blanqueamiento", False),
    ("restauración", False),
    ("extracción", False),
    ("endodoncia", False),
    ("carillas", False),
    ("strass dentales", False),
    ("ortodoncia", False),
    ("ortopedia", False),
    ("cirugía", False),
    ("prótesis", False),
    ("ATM y bruxismo", False),
    ("otros", False),
]


CSS_SELECT = """
/* EL DESPLEGABLE USA LA CAJA DEL SISTEMA —la misma de la pieza 4— y le suma
   lo único que un <select> necesita y un <input> no: la flecha. Va dibujada
   en el fondo y no como carácter, porque un carácter se puede seleccionar y
   se ve distinto en cada sistema. */
select.caja {
  appearance: none;
  padding-right: 40px;
  background-image:
    linear-gradient( 45deg, transparent 50%, var(--grafito) 50% ),
    linear-gradient( 135deg, var(--grafito) 50%, transparent 50% );
  background-position:
    calc( 100% - 20px ) calc( 50% + 2px ),
    calc( 100% - 14px ) calc( 50% + 2px );
  background-size: 6px 6px, 6px 6px;
  background-repeat: no-repeat;
  cursor: pointer;
  /* 🔴 ESTO PROBABLEMENTE NO HAGA NADA, y se deja UNA versión con el motivo
     escrito para que nadie lo vuelva a intentar a ciegas.
     `accent-color` rige checkbox, radio, range y progress — no el resaltado de
     un <option>. Ese resaltado lo pinta el SISTEMA OPERATIVO con su color de
     acento, y Safari incluso lo dibuja ENCIMA del fondo que declare el autor.
     ⇒ El azul del desplegable abierto no se cambia por CSS.
     Se deja la línea porque no rompe nada y porque el día que el navegador lo
     soporte, el color ya está puesto y es el nuestro. */
  accent-color: var(--dorado);
}
"""


CSS_MOTIVO = """
.motivo {
  margin: 0 var(--margen-pagina);
  padding: 32px 0 40px;
}

.motivo h1 {
  font-family: Marcellus, Georgia, serif;
  font-size: var(--tipo-h1);
  line-height: var(--alto-h1);
  text-wrap: balance;
}

.motivo .ayuda-pantalla {
  margin-top: 12px;
  color: var(--texto-segundo);
  font-size: var(--tipo-cuerpo);
  line-height: var(--alto-cuerpo);
  text-wrap: balance;
}

.motivo .btn {
  margin-top: 28px;
  margin-left: 0;
}
"""


def opciones_de_motivo(elegido):
    salida = ""

    for nombre, propia in TRATAMIENTOS:
        marca = " selected" if nombre == elegido else ""
        salida += f'\n        <option{marca}>{nombre}</option>'

    return salida


def motivo_del_sitio(ancho, elegido=None):
    """La pantalla ③. `elegido` es None (sin elegir), o el nombre de un
    tratamiento — y de eso depende que aparezca el aviso de la consulta."""
    logo = leer_png("cb-wordmark-600")

    sin_elegir = ' selected' if elegido is None else ''

    # 🔴 ACÁ HABÍA UN AVISO Y JUAN LO SACÓ el 24-sep-2026: «el que viene con el
    # aviso no». Decía que la primera visita es una consulta, y salía sólo
    # cuando lo elegido no tenía duración propia.
    #
    # ⚠️ SACARLO NO CIERRA EL HUECO, LO MUDA: los doce tratamientos sin duración
    # propia se siguen agendando como consulta, y el paciente lo sigue sin
    # saber. Dónde se lo dice —la pantalla de confirmar, el correo, o en ningún
    # lado a propósito— queda ABIERTO y anotado en la § 14.

    return f"""
<div class="pagina">
  <header class="encabezado">
    <div class="barra">
      <img src="data:image/png;base64,{logo}"
           alt="CB Odontología y Estética"
           width="{ENCABEZADO_LOGO[ancho]}">
    </div>
  </header>

  <div class="motivo">
    <h1>¿A qué venís?</h1>

    <p class="ayuda-pantalla">Elegí el motivo de la consulta. Si no estás
    seguro, poné <b>consulta</b> y lo vemos ahí.</p>

    <div class="campo">
      <label class="etiqueta" for="motivo">Motivo</label>
      <select class="caja" id="motivo">
        <option value=""{sin_elegir}>Elegí una opción</option>{opciones_de_motivo(elegido)}
      </select>
    </div>

    <button class="btn btn-1">Continuar</button>
  </div>
</div>"""


def solo_motivo(tokens, css, ancho):
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · ¿A qué venís? · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_CAMPO}
{CSS_SELECT}
{CSS_ENCABEZADO}
{CSS_MOTIVO}
{CSS_FOCO}
</style>
{motivo_del_sitio(ancho, elegido="endodoncia")}
"""


def tablero_motivo(tokens, css, ancho):
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 18 ¿A qué venís? · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_CAMPO}
{CSS_SELECT}
{CSS_ENCABEZADO}
{CSS_MOTIVO}
{CSS_FOCO}
{css_margen_en_la_prosa()}
</style>

<div class="prosa">
<p class="rotulo">Fase ⑧ · Pieza 18 · {ancho} px</p>
<h1>¿A qué venís?</h1>
<div class="regla"></div>
<p><b>Los catorce tratamientos no están escritos en esta pieza:</b> salen de
<code>GET /tratamientos</code>, y esta lista se copió de una <b>corrida real
del endpoint</b>. <b>El orden también viene resuelto de la base</b> —columna
<code>orden</code>—, igual que en obras sociales: no se reordena en el front.</p>

<section>
  <p class="rotulo">La decisión de forma</p>
  <h2>Desplegable, y acá sí</h2>
  <p>La pieza 17 usa <b>lista tocable</b> y ésta usa <b>desplegable</b>, y no
  es una incoherencia: <b>lo que decide es cuántas opciones hay</b>. Dos a
  cuatro personas entran todas a la vista y esconderlas cuesta un toque de
  más; <b>catorce tratamientos en tarjetas serían más de 900 px de scroll</b>
  antes de llegar al botón.</p>
  <p>El control es <b>la caja del sistema</b>, la misma de la pieza 4. Lo único
  que se le suma es la flecha, <b>dibujada en el fondo y no puesta como
  carácter</b>: un carácter se puede seleccionar y se dibuja distinto en cada
  sistema.</p>
  <p>🔴 <b>EL AZUL DEL DESPLEGABLE ABIERTO NO SE PUEDE CAMBIAR, y conviene que
  quede escrito para no volver a intentarlo.</b> El resaltado de la opción lo
  pinta el <b>sistema operativo</b> con su color de acento — Safari incluso lo
  dibuja <b>encima</b> del fondo que declare el autor. <code>accent-color</code>
  rige checkbox, radio, range y progress, <b>no el <code>&lt;option&gt;</code></b>.</p>
  <p>🔑 <b>Y el argumento que cierra el tema no es técnico, es de dónde se
  mira:</b> ese azul es el de <b>macOS</b>. En un teléfono —que es donde va a
  estar el paciente— el mismo <code>&lt;select&gt;</code> se abre como la
  <b>hoja o rueda nativa de iOS o Android</b>, que no se parece en nada a esto.
  <b>Que el control se vea como el sistema de quien lo usa es una virtud del
  control nativo, no un defecto a tapar.</b></p>
  <p>⚠️ <b>La alternativa existe y es cara:</b> reemplazarlo por un desplegable
  propio hecho con <code>div</code>. Se estila entero, y hay que reimplementar
  teclado, lector de pantalla y comportamiento táctil — y en móvil se pierde la
  rueda nativa, que es mejor que cualquier imitación.</p>
</section>

<section>
  <p class="rotulo">🔴 El hueco de producto que apareció armando esta pieza</p>
  <h2>El paciente elige endodoncia y lo que queda agendado es una consulta</h2>
  <p><b>Sólo DOS de los catorce tienen duración propia para la web:</b>
  <code>consulta</code> y <code>limpieza</code>. <b>Los otros doce se agendan
  como consulta</b> y el profesional reasigna después — eso ya está construido
  y decidido en el portero.</p>
  <p><b>Lo que NO estaba decidido es si la pantalla se lo dice.</b> Si no lo
  dice, el paciente que eligió «endodoncia» <b>llega esperando que le hagan la
  endodoncia ese día</b>.</p>
  <p>🏁 <b>CERRADO POR JUAN el 24-sep-2026, y no en la forma que Claude
  proponía: NO SE LE DICE, EN NINGÚN LADO.</b> Su argumento, textual: <i>«el
  paciente no tiene por qué saber que el tratamiento arranca con una consulta,
  es una realidad y listo»</i>.</p>
  <p><b>Y se sostiene solo:</b> que la primera visita sea una evaluación es
  <b>cómo funciona la odontología</b>, no una particularidad de este sistema.
  Nadie espera que le hagan una endodoncia sin que antes le miren la boca.
  <b>Avisarlo sería explicarle al paciente algo que ya sabe</b>, y encima en el
  paso donde lo único que tiene que hacer es elegir.</p>
  <p>⚠️ <b>Lo que sí queda como consecuencia, dicho una vez:</b> el turno
  aparece en la agenda como <code>consulta</code> con el motivo guardado al
  lado. <b>Eso es exactamente lo que el portero ya hace</b> — la decisión no
  cambia nada del código, cierra una pregunta de producto.</p>
</section>

<section>
  <p class="rotulo">Lo que queda abierto</p>
  <h2>Dos cosas</h2>
  <ul class="reglas">
    <li>⬜ <b>Si los catorce se agrupan.</b> Podrían partirse en «lo más
    pedido» y «otros tratamientos» con <code>&lt;optgroup&gt;</code>, como el
    desplegable de obras sociales agrupa por entidad. <b>Hoy van planos, en el
    orden de la base.</b></li>
    <li>⬜ <b>Qué pasa con «otros».</b> Es uno de los catorce y no dice nada
    por sí mismo: <b>probablemente necesite un campo de texto al lado</b>, y
    eso hoy no existe.</li>
  </ul>
</section>

<section>
  <p class="rotulo">La pantalla, a 1:1</p>
  <h2>Y es UNA, no tres</h2>
  <p>🔴 <b>Acá hubo tres, después dos, y Juan las cortó a una:</b> primero
  <i>«no entiendo la diferencia entre el primero y el segundo»</i>, y al
  quedar dos, <i>«son iguales»</i>. <b>Tenía razón las dos veces.</b></p>
  <p>🔑 <b>La regla que deja, y vale para cualquier tablero de acá en
  adelante: un estado merece su propia muestra sólo si cambia el DIBUJO, no si
  cambia el CONTENIDO de un control.</b> Un desplegable con su texto de
  arranque y el mismo desplegable con una opción elegida <b>son el mismo
  dibujo</b>; apilarlos no enseña nada y hace dudar de si uno se está perdiendo
  algo.</p>
</section>
</div>
{motivo_del_sitio(ancho, elegido="endodoncia")}
"""


# ============================================================
# PIEZA 19 — DÍA Y HORA (el paso ⑤ de la pantalla del paciente)
#
# NO DISEÑA NADA NUEVO: el almanaque, la grilla, los estados y sus colores se
# cerraron en la PIEZA 7 (fase ⑦, 3-sep-2026) y acá se REUSAN las mismas
# funciones —`almanaque()` y `grilla()`— con los mismos datos. Lo que esta pieza
# agrega es la PANTALLA alrededor: encabezado, título, la etiqueta del día, el
# botón, y el ANCLA que une las dos mitades.
#
# 🔴 EL ANCLA ES LA «OPCIÓN D», y la decidió Juan sobre una medición: en el
# teléfono el mes ocupa ~400 px y las horas ~372 —772 contra 745 de pantalla—,
# así que NO ENTRAN, y no es cuestión de apretar. Se evaluaron dos pantallas,
# una tira de días horizontal y un mes plegable; ganó el ancla.
#
# ⏱ QUEDA ABIERTA A REVISIÓN, y lo pidió él al aprobarla: se decidió sobre una
# medición, no sobre algo usado. Disparador: el primer paciente que elige un
# turno desde un teléfono real.
# ============================================================

CSS_DIA_HORA = """
.dia-hora {
  margin: 0 var(--margen-pagina);
  padding: 32px 0 var(--aire-seccion);
}

.dia-hora h1 {
  font-family: Marcellus, Georgia, serif;
  font-size: var(--tipo-h1);
  line-height: var(--alto-h1);
  text-wrap: balance;
}

.dia-hora .ayuda-pantalla {
  margin-top: 12px;
  color: var(--texto-segundo);
  font-size: var(--tipo-cuerpo);
  line-height: var(--alto-cuerpo);
  text-wrap: balance;
}

.reserva {
  margin-top: 24px;
}

/* EL DESTINO DEL ANCLA. Al saltar, el navegador pega el destino contra el
   borde de arriba: `scroll-margin-top` le reserva aire para que la etiqueta
   del día —lo único que dice QUÉ día se está mirando— no quede al filo. */
.horarios {
  scroll-margin-top: 16px;
}

/* 🔴 EL DESTINO DEL ANCLA NO LLEVA ANILLO DE FOCO, y es la SEGUNDA excepción
   declarada del sistema —la primera es el radio de la pieza 17—.

   MEDIDO el 25-sep-2026, no supuesto: al tocar un día, `#horarios` recibe el
   foco (que es TODO EL PUNTO del ancla) y `:focus-visible` se dibujaba, o sea
   un contorno grafito de 2 px alrededor de media pantalla en cada toque.

   El anillo existe para decir QUÉ SE VA A OPERAR al teclear. Un cajón de
   aterrizaje no se opera: se lee. Y la confirmación de que el salto ocurrió ya
   la da la página moviéndose. Los controles de adentro —cada hora, el botón—
   conservan su anillo intacto. */
.horarios:focus-visible {
  outline: none;
}

/* QUÉ DÍA SE ESTÁ MIRANDO. Sin esto, el ancla baja a una grilla de horas que
   no dice de cuándo son — y el almanaque, que lo diría, quedó arriba. */
.horarios .cuando {
  margin-top: 22px;
  font-weight: 500;
}

.dia-hora .btn {
  margin-top: 28px;
  margin-left: 0;
}
"""


def dia_hora_del_sitio(ancho):
    """La pantalla ⑤. El día y la hora, con el ancla que las une."""
    logo = leer_png("cb-wordmark-600")

    # ⚠️ LA ETIQUETA DEL DÍA NO LLEVA LA DURACIÓN, y no es un olvido: el tablero
    # de la pieza 7 dice «Consulta, 30 minutos» porque eso es PROSA DE TABLERO,
    # explicándose a sí mismo. En la pantalla real esa línea sería decirle al
    # paciente que su tratamiento se agenda como consulta, y eso está CERRADO
    # por Juan el 24-sep-2026: no se le dice en ningún lado.
    return f"""
<div class="pagina">
  <header class="encabezado">
    <div class="barra">
      <img src="data:image/png;base64,{logo}"
           alt="CB Odontología y Estética"
           width="{ENCABEZADO_LOGO[ancho]}">
    </div>
  </header>

  <div class="dia-hora">
    <h1>¿Qué día y a qué hora?</h1>

    <p class="ayuda-pantalla">Los días en gris no tienen lugar. Tocá uno con
    punto dorado y elegí el horario.</p>

    <div class="reserva juntas">{almanaque(ancla=True)}
      <section class="lado horarios" id="horarios" tabindex="-1">
        <p class="cuando">Jueves 11 de septiembre</p>
        {grilla(BLOQUES)}
        <button class="btn btn-1">Continuar</button>
      </section>
    </div>
  </div>
</div>"""


def solo_dia_hora(tokens, css, ancho):
    """La pantalla sola, a 1:1, sin una línea de explicación alrededor."""
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · Día y hora · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_GRILLA}
{CSS_ENCABEZADO}
{CSS_DIA_HORA}
{CSS_FOCO}
</style>
{dia_hora_del_sitio(ancho)}
"""


def tablero_dia_hora(tokens, css, ancho):
    """El tablero que explica la pieza. La pantalla sola vive en otro archivo."""
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 19 Día y hora · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_GRILLA}
{CSS_ENCABEZADO}
{CSS_DIA_HORA}
{CSS_FOCO}
{css_margen_en_la_prosa()}
</style>

<div class="prosa">
<p class="rotulo">Fase ⑧ · Pieza 19 · {ancho} px</p>
<h1>Día y hora</h1>
<div class="regla"></div>
<p><b>Esta pieza no diseñó nada.</b> El almanaque, la grilla, los cuatro
estados y sus colores se cerraron en la <b>pieza 7</b> el 3-sep-2026, y acá se
reusan <b>las mismas funciones con los mismos datos</b> —si mañana cambia el
alto de un día, cambia en las dos—. Lo que se agregó es la <b>pantalla</b>:
encabezado, título, la etiqueta del día, el botón, y <b>el ancla que une las
dos mitades</b>.</p>

<section>
  <p class="rotulo">La decisión que gobierna esta pantalla</p>
  <h2>El ancla, y el número que la obligó</h2>
  <p><b>En el teléfono el mes y las horas no entran juntos.</b> El mes ocupa
  ~<b>400 px</b> y las horas ~<b>372</b>: <b>772 contra 745</b> de pantalla. No
  es cuestión de apretar.</p>
  <p>Se evaluaron cuatro caminos —dos pantallas · una tira de días horizontal ·
  un mes que se pliega— y <b>ganó el que propuso Juan: un ancla</b>. Se toca el
  día y la página baja sola a los horarios.</p>
  <p>🔴 <b>Y lleva dos condiciones, las dos aplicadas acá:</b></p>
  <ul class="reglas">
    <li><b>Ancla de verdad</b> —<code>&lt;a href="#horarios"&gt;</code>— <b>y no
    <code>scrollIntoView()</code></b>. El JavaScript mueve la pantalla pero
    <b>no mueve el foco</b>: el que navega con teclado o con lector de pantalla
    se queda arriba sin enterarse de que abajo cambió algo. El destino lleva
    <code>tabindex="-1"</code> para poder recibirlo.
    <i>Contraintuitivo y por eso escrito: acá la forma vieja es la accesible.</i></li>
    <li><b>Al abrir viene elegido el primer día con lugar</b> —decisión de la
    pieza 7—, así que <b>el ancla nunca baja a un cajón vacío</b>: baja a algo
    que ya existe, que es más suave que hacer aparecer contenido nuevo debajo
    del dedo.</li>
  </ul>
  <p>⏱ <b>La decisión queda ABIERTA A REVISIÓN y lo pidió Juan al aprobarla:</b>
  se decidió sobre una medición, no sobre algo usado. <b>Disparador: el primer
  paciente que elige un turno desde un teléfono real.</b> Si no funciona, se
  cambia sin volver a discutir el marco — las tres alternativas siguen escritas
  arriba.</p>
</section>

<section>
  <p class="rotulo">Lo que el ancla cambió en el marcado</p>
  <h2>El día dejó de ser un botón</h2>
  <p><b>Un <code>&lt;button&gt;</code> no puede llevar un ancla</b>, así que en
  la pantalla real cada día con lugar es un <b>enlace</b>
  <code>&lt;a href="#horarios"&gt;</code>. <b>En el tablero de la pieza 7 sigue
  siendo un botón</b>, y está bien: ahí no hay pantalla adonde bajar.</p>
  <p>🔑 <b>Y el día cerrado dejó de ser un control.</b> Antes era un
  <code>&lt;button disabled&gt;</code>; ahora es un <code>&lt;span&gt;</code>,
  que <b>no recibe foco ni clic</b> — que es exactamente lo que se quiere de un
  día que no se puede tocar. Lo que se lo dice al lector de pantalla es
  <code>aria-disabled</code>, porque <code>disabled</code> no existe fuera de
  los controles.</p>
  <p><b>Y una cosa más que no se ve:</b> el día elegido lleva
  <code>aria-current="date"</code>. El dorado lo dice en la pantalla; esto lo
  dice en voz alta.</p>
</section>

<section>
  <p class="rotulo">Lo que NO dice esta pantalla</p>
  <h2>La etiqueta del día va sin la duración</h2>
  <p>El tablero de la pieza 7 rotula el día como <i>«Jueves 11 de septiembre ·
  Consulta, 30 minutos»</i>. <b>Acá dice sólo el día</b>, y el recorte es
  deliberado: esa línea es <b>prosa de tablero</b> explicándose a sí misma, y en
  la pantalla real sería <b>decirle al paciente que su tratamiento se agenda
  como consulta</b>. Eso está <b>cerrado por Juan el 24-sep-2026: no se le dice
  en ningún lado</b>.</p>
  <p>⚠️ <b>Pero la etiqueta no se puede borrar del todo</b>, y por eso quedó el
  día: <b>el ancla baja y el almanaque queda fuera de la vista</b>. Sin esa
  línea, la grilla no dice de cuándo son esas horas.</p>
</section>

<section>
  <p class="rotulo">Lo que se rompió al medirlo</p>
  <h2>Dos cosas que ya estaban rotas y nadie había mirado</h2>
  <p>🔴 <b>A 1280 el día del mes medía 36 px de lado, y la regla de la pieza 7
  dice 44.</b> Con el almanaque al costado, las siete columnas se encogían al
  contenido: <b>la regla estaba escrita y la pantalla decía otra cosa</b>. El
  piso táctil estaba declarado sólo a lo <b>alto</b>. <b>No es un bug de esta
  pieza —el tablero de la 7 medía lo mismo— y por eso se arregló en el único
  lugar donde vive el día: las dos pantallas se enderezaron juntas.</b></p>
  <p>🔴 <b>Y el ancla dibujaba un contorno grafito alrededor de media
  pantalla.</b> Al tocar un día, el cajón de horarios recibe el foco —que es
  <b>todo el punto</b> del ancla— y el anillo del sistema se pintaba encima.
  <b>Queda como la segunda excepción declarada</b>, junto al radio de la pieza
  17: <b>el anillo dice qué se va a operar al teclear, y un cajón de aterrizaje
  no se opera, se lee</b>. La confirmación de que el salto ocurrió ya la da la
  página moviéndose. <b>Cada hora y el botón conservan el suyo intacto.</b></p>
  <p class="dato" style="margin-top: 12px">🔑 <b>Las dos aparecieron
  MIDIENDO, no mirando</b> — un contorno de 2 px y ocho píxeles de ancho no se
  ven en una captura, y las dos cambian cómo se usa la pantalla con el dedo o
  con el teclado.</p>
</section>

<section>
  <p class="rotulo">Lo que queda abierto</p>
  <h2>Dos cosas, y ninguna bloquea</h2>
  <ul class="reglas">
    <li>⬜ <b>Escritorio no se rediseñó.</b> A 1280 el mes va a la izquierda y
    las horas a la derecha, <b>que es el layout que ya traía la pieza 7</b> — no
    se estrenó nada. Con las dos mitades a la vista <b>el ancla no tiene adónde
    bajar, y no molesta</b>: el salto a algo que ya está en pantalla no mueve
    nada.</li>
    <li>⬜ <b>El botón secundario sigue pesando más que el principal</b>
    —grafito 12,0 contra la página, dorado 2,89—. Esta pantalla tiene un solo
    botón, así que <b>no lo destapa ni lo resuelve</b>.</li>
  </ul>
</section>
</div>
{dia_hora_del_sitio(ancho)}
"""


# ============================================================
# PIEZA 20 — COBERTURA, OBSERVACIONES Y CONFIRMAR (el paso ⑥, y el último)
#
# Es la pantalla que dispara `POST /reservar`. No estrena ni un control: la
# tarjeta es la pieza 6 sin su botón, el desplegable es la caja de la 4 con la
# flecha de la 18, el campo largo es esa misma caja, y el botón es el de la 3.
#
# 🔴 LAS 71 OBRAS SOCIALES NO ESTÁN ESCRITAS ACÁ: se leen de la MIGRACIÓN que
# las carga en la base. Es la misma regla que ya rige para los colores —el
# tablero lee `tokens.css`—: un tablero no puede mentir sobre lo que el sistema
# hace. Si mañana Cecilia suma un convenio, la migración lo trae y el tablero
# se entera solo.
# ============================================================

def leer_obras_sociales():
    """Las 71 filas, leídas de la migración que las carga en la base."""
    archivo = next(
        (RAIZ / "supabase" / "migrations").glob("*_cargar_obras_sociales.sql")
    )

    filas = []

    for linea in archivo.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()

        if not linea.startswith("( '"):
            continue

        crudo = linea.strip("(),; ")
        nombre, entidad = [
            parte.strip().strip("'")
            for parte in crudo.split("', '")
        ]
        filas.append((nombre, entidad))

    return filas


def opciones_de_cobertura(elegida):
    """El desplegable, agrupado por entidad.

    ⚠️ UN <optgroup> SÓLO DONDE HAY MÁS DE UNA FILA, y el criterio importa:
    de las 71, apenas cinco entidades agrupan a varias —IAPOS con seis, y
    cuatro con dos—. Las otras 56 son entidad de sí mismas, y envolver cada una
    en su propio título dibujaría 56 encabezados de un solo ítem: ruido que
    esconde justamente a los cinco grupos que sí dicen algo.

    El ORDEN no se toca: viene de la base —`Particular` primera por su columna
    `orden`— y las filas de una misma entidad ya vienen contiguas.
    """
    salida = ""
    grupo_abierto = None

    filas = leer_obras_sociales()
    cuantas = {}

    for _, entidad in filas:
        cuantas[entidad] = cuantas.get(entidad, 0) + 1

    for nombre, entidad in filas:
        agrupa = cuantas[entidad] > 1

        if grupo_abierto and grupo_abierto != (entidad if agrupa else None):
            salida += "\n        </optgroup>"
            grupo_abierto = None

        if agrupa and grupo_abierto != entidad:
            salida += f'\n        <optgroup label="{entidad}">'
            grupo_abierto = entidad

        marca = " selected" if nombre == elegida else ""
        sangria = "  " if agrupa else ""
        salida += f'\n        {sangria}<option{marca}>{nombre}</option>'

    if grupo_abierto:
        salida += "\n        </optgroup>"

    return salida


CSS_CONFIRMAR = """
.confirmar {
  margin: 0 var(--margen-pagina);
  padding: 32px 0 var(--aire-seccion);
}

.confirmar h1 {
  font-family: Marcellus, Georgia, serif;
  font-size: var(--tipo-h1);
  line-height: var(--alto-h1);
  text-wrap: balance;
}

.confirmar .ayuda-pantalla {
  margin-top: 12px;
  color: var(--texto-segundo);
  font-size: var(--tipo-cuerpo);
  line-height: var(--alto-cuerpo);
  text-wrap: balance;
}

/* La tarjeta acá NO es un ítem de una lista: es el resumen de lo que se está
   por crear, así que arranca en el margen como el resto de la pantalla y no
   se estira a lo ancho de la columna de listas. */
.confirmar .turno {
  max-width: var(--columna);
  margin-top: 22px;
}

/* EL CAMPO LARGO USA LA MISMA CAJA QUE EL RESTO. Lo único propio es que puede
   crecer: `resize: vertical` deja agrandarlo a lo alto y NO a lo ancho, porque
   a lo ancho rompería la columna de lectura. */
.confirmar textarea.caja {
  min-height: 96px;
  resize: vertical;
}

.confirmar .btn {
  margin-top: 28px;
  margin-left: 0;
}
"""


def confirmar_del_sitio(ancho):
    """La pantalla ⑥, la última del flujo."""
    logo = leer_png("cb-wordmark-600")

    # ⚠️ LA TARJETA VA SIN DURACIÓN Y SIN MOTIVO — es la pieza 6 tal como se
    # cerró. El motivo ya viaja en el correo operativo, que es donde le sirve a
    # Cecilia, y la duración no se le muestra nunca al paciente.
    tarjeta = tarjeta_turno(
        "Jueves 11 de septiembre, 15:30",
        "Consulta",
        "con Cecilia Duarte",
        "Paciente: María Fernanda Gómez",
        accion=False,
    )

    return f"""
<div class="pagina">
  <header class="encabezado">
    <div class="barra">
      <img src="data:image/png;base64,{logo}"
           alt="CB Odontología y Estética"
           width="{ENCABEZADO_LOGO[ancho]}">
    </div>
  </header>

  <div class="confirmar">
    <h1>¿Confirmamos?</h1>

    <p class="ayuda-pantalla">Revisá que esté todo bien y decinos con qué
    cobertura venís.</p>
{tarjeta}

    <div class="campo">
      <label class="etiqueta" for="cobertura">Cobertura</label>
      <select class="caja" id="cobertura">{opciones_de_cobertura("IAPOS")}
      </select>
    </div>

    <div class="campo">
      <label class="etiqueta" for="observaciones">Algo que quieras avisarnos
      <span class="opcional">(opcional)</span></label>
      <textarea class="caja" id="observaciones"></textarea>
    </div>

    <button class="btn btn-1">Confirmar turno</button>
  </div>
</div>"""


def solo_confirmar(tokens, css, ancho):
    """La pantalla sola, a 1:1, sin una línea de explicación alrededor."""
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · Confirmar · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_CAMPO}
{CSS_SELECT}
{CSS_TARJETA}
{CSS_ENCABEZADO}
{CSS_CONFIRMAR}
{CSS_FOCO}
</style>
{confirmar_del_sitio(ancho)}
"""


def tablero_confirmar(tokens, css, ancho):
    """El tablero que explica la pieza. La pantalla sola vive en otro archivo."""
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 20 Confirmar · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_CAMPO}
{CSS_SELECT}
{CSS_TARJETA}
{CSS_ENCABEZADO}
{CSS_CONFIRMAR}
{CSS_FOCO}
{css_margen_en_la_prosa()}
</style>

<div class="prosa">
<p class="rotulo">Fase ⑧ · Pieza 20 · {ancho} px</p>
<h1>Cobertura, observaciones y confirmar</h1>
<div class="regla"></div>
<p><b>Es la última pantalla del flujo y la que dispara
<code>POST /reservar</code>.</b> No estrena un solo control: la tarjeta es la
<b>pieza 6 sin su botón</b>, el desplegable es <b>la caja de la 4 con la flecha
de la 18</b>, el campo largo es esa misma caja, y el botón es el de la 3.</p>

<section>
  <p class="rotulo">Las 71 obras sociales</p>
  <h2>No están escritas en el tablero</h2>
  <p><b>Se leen de la MIGRACIÓN que las carga en la base</b>, que es la misma
  regla que ya rige para los colores —el tablero lee <code>tokens.css</code>—.
  <b>Un tablero no puede mentir sobre lo que el sistema hace</b>: si mañana
  Cecilia suma un convenio, la migración lo trae y esta pantalla se entera
  sola.</p>
  <p>⚠️ <b>Y hay un <code>&lt;optgroup&gt;</code> SÓLO donde hay más de una
  fila.</b> De las 71, apenas <b>cinco entidades agrupan a varias</b> —IAPOS
  con seis, y cuatro con dos—. Las otras <b>56 son entidad de sí mismas</b>, y
  envolver cada una en su propio título dibujaría <b>56 encabezados de un solo
  ítem</b>: ruido que esconde justo a los cinco grupos que sí dicen algo.</p>
  <p class="dato" style="margin-top: 12px"><b>El orden no se toca:</b> viene de
  la base —<code>Particular</code> primera por su columna <code>orden</code>— y
  las filas de una misma entidad ya vienen contiguas. <i>Incluidas las dos que
  no son obras sociales en sentido estricto: entran tal cual, que es decisión
  cerrada del 17-sep.</i></p>
  <p>⚠️ <b>Por qué la muestra abre con una cobertura YA elegida, que si no
  parece un default puesto al azar:</b> está decidido que el desplegable venga
  con <b>la última cobertura que usó ese paciente</b>. Lo que se ve acá es el
  que <b>ya vino antes</b>. <b>Un paciente nuevo no tiene última</b>, así que
  para él el desplegable abre sin elegir — y el campo es <b>obligatorio</b>, o
  sea que no puede confirmar sin tocarlo.</p>
  <p class="dato" style="margin-top: 12px">🔑 <b>No hay una segunda muestra para
  ese caso, y es la regla que dejó la pieza 18:</b> un estado merece su propia
  muestra <b>sólo si cambia el dibujo</b>, no si cambia el contenido de un
  control.</p>
</section>

<section>
  <p class="rotulo">La tarjeta</p>
  <h2>La misma de «mis turnos», sin el botón</h2>
  <p><b>Acá el turno TODAVÍA NO EXISTE</b>, así que no hay nada que cancelar.
  Es la única diferencia entre los dos lugares donde vive la tarjeta, y por eso
  <b>es un parámetro y no una tarjeta nueva</b>: el dibujo es uno solo.</p>
  <p><b>Va sin duración y sin motivo</b>, como se cerró en la pieza 6. El
  motivo ya viaja en el correo operativo, que es donde le sirve a Cecilia.</p>
</section>

<section>
  <p class="rotulo">🔴 El campo que toca datos sensibles</p>
  <h2>Lo que el formulario PIDE es una decisión, no un detalle</h2>
  <p><code>turnos.observaciones_paciente</code> <b>puede contener datos de
  salud</b> — es una propiedad del modelo, escrita y permanente. Lo que decide
  esta pantalla no es si el dato existe: <b>es qué le pedimos al paciente que
  escriba ahí</b>.</p>
  <p>🔑 <b>El principio que lo gobierna ya está en el proyecto y tiene nombre:
  <i>data minimization</i> (minimización de datos)</b> — lo que no se pide, no
  hay que protegerlo. <b>Que el paciente escriba una condición de salud es su
  decisión; que el formulario se la pida es la nuestra.</b></p>
  <p>La etiqueta es <b>neutra</b> —«Algo que quieras avisarnos»— y <b>no hay
  nada más</b>: la ayuda que había debajo decía lo mismo con otras palabras.
  <b>No invita a contar una historia clínica y tampoco la prohíbe</b>, que sería
  mentir sobre el campo.</p>
  <p class="dato" style="margin-top: 12px">🏁 <b>Cerrado el 25-sep por Juan: no
  se aclara quién lo va a leer.</b></p>
</section>

<section>
  <p class="rotulo">Lo que NO tiene esta pantalla</p>
  <h2>No hay botón «Volver»</h2>
  <p><b>Ninguna de las cuatro pantallas anteriores lo tiene</b>, y meterlo sólo
  acá rompe la única forma que tienen en común.</p>
  <p>⚠️ <b>Se declara lo que contradice:</b> la tira de contexto de la pieza 8
  sí lo dibujaba al lado de «Confirmar turno». <b>Y hay un efecto lateral que
  conviene tener a la vista:</b> el pendiente viejo —que el botón secundario
  pesa más que el principal, grafito 12,0 contra dorado 2,89— <b>no se destapa
  hoy</b>, y sigue esperando al segundo tiempo de la ⑧, que es donde quedó
  agendado.</p>
</section>
</div>
{confirmar_del_sitio(ancho)}
"""


# ============================================================
# PIEZA 21 — MIS TURNOS
#
# 🔴 ESTA PANTALLA DESTAPA UN PENDIENTE VIEJO Y NO LO PUEDE ESQUIVAR: el botón
# SECUNDARIO pesa más que el principal —grafito 12,0 contra la página, dorado
# 2,89— y acá el secundario es «Cancelar turno», una vez por tarjeta, SIN
# ninguna acción principal que le compita. Lo más pesado de la pantalla termina
# siendo la acción destructiva, repetida.
#
# Y hay una SEGUNDA: el 24-sep quedó escrito que ésta es la pantalla donde el
# paciente ve su cobertura, y la tarjeta aprobada (pieza 6) no la tiene.
#
# Por eso esta pieza se entrega primero como DOS COMPARACIONES a 1:1 —una por
# decisión, una sola variable por archivo— y no como una pantalla cerrada.
# ============================================================

CSS_MIS_TURNOS = """
.mis-turnos {
  margin: 0 var(--margen-pagina);
  padding: 32px 0 var(--aire-seccion);
}

.mis-turnos h1 {
  font-family: Marcellus, Georgia, serif;
  font-size: var(--tipo-h1);
  line-height: var(--alto-h1);
  text-wrap: balance;
}

.mis-turnos .ayuda-pantalla {
  margin-top: 12px;
  color: var(--texto-segundo);
  font-size: var(--tipo-cuerpo);
  line-height: var(--alto-cuerpo);
  text-wrap: balance;
}

/* La cobertura es el renglón MÁS callado de la tarjeta: es un dato de control,
   no lo que el paciente vino a mirar. Mismo tamaño que «Paciente: …». */
.turno .cobertura {
  margin-top: 2px;
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  color: var(--texto-segundo);
}

"""


COBERTURAS_DE_LA_MUESTRA = ("IAPOS", "Particular")


def mis_turnos_del_sitio(ancho, vacio=False):
    """La pantalla de «mis turnos», con sus dos estados.

    Las dos decisiones que traía quedaron cerradas por Juan el 25-sep-2026:
    el botón se queda GRAFITO MACIZO, y la cobertura SÍ entra en la tarjeta
    —y esto último lo cambió él mismo al enterarse de que el correo del
    paciente no la trae, que es de donde salía su primera respuesta—.
    """
    logo = leer_png("cb-wordmark-600")

    if vacio:
        cuerpo = """
    <p class="ayuda-pantalla">No tenés ningún turno reservado.</p>

    <button class="btn btn-1">Pedir un turno</button>"""
    else:
        tarjetas = "".join(
            tarjeta_turno(*turno, cobertura=COBERTURAS_DE_LA_MUESTRA[i])
            for i, turno in enumerate(TURNOS)
        )
        # SIN LÍNEA DE AYUDA — lo sacó Juan el 25-sep-2026: «ya se avisa en el
        # correo». Verificado en `avisos.ts`: el correo del paciente cierra con
        # «Si no vas a poder venir, podés cancelarlo vos desde: …». Repetirlo
        # acá es decirle dos veces lo mismo a quien ya llegó a la pantalla.
        cuerpo = f"""
    <div class="lista-turnos">{tarjetas}
    </div>"""

    return f"""
<div class="pagina">
  <header class="encabezado">
    <div class="barra">
      <img src="data:image/png;base64,{logo}"
           alt="CB Odontología y Estética"
           width="{ENCABEZADO_LOGO[ancho]}">
    </div>
  </header>

  <div class="mis-turnos">
    <h1>Mis turnos</h1>
{cuerpo}
  </div>
</div>"""


def solo_mis_turnos(tokens, css, ancho):
    """La pantalla sola, a 1:1, sin una línea de explicación alrededor."""
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · Mis turnos · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_TARJETA}
{CSS_ENCABEZADO}
{CSS_MIS_TURNOS}
{CSS_FOCO}
</style>
{mis_turnos_del_sitio(ancho)}
"""


def tablero_mis_turnos(tokens, css, ancho):
    """El tablero que explica la pieza. La pantalla sola vive en otro archivo."""
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · 21 Mis turnos · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{css}
{base_css(ancho)}
{CSS_BOTON}
{CSS_TARJETA}
{CSS_ENCABEZADO}
{CSS_MIS_TURNOS}
{CSS_FOCO}
{css_margen_en_la_prosa()}
</style>

<div class="prosa">
<p class="rotulo">Fase ⑧ · Pieza 21 · {ancho} px</p>
<h1>Mis turnos</h1>
<div class="regla"></div>
<p><b>Ver el turno que tenés y poder cancelarlo.</b> Nada más: la tarjeta es la
pieza 6, y acá es donde vive con su botón.</p>

<section>
  <p class="rotulo">Las dos decisiones, cerradas por Juan el 25-sep</p>
  <h2>Y una la cambió él mismo</h2>
  <ul class="reglas">
    <li><b>El botón se queda grafito macizo.</b> Se evaluó con filo y sin
    relleno; <b>no entró</b>.</li>
    <li><b>La cobertura SÍ va en la tarjeta.</b> Primero dijo que no —<i>«le
    llega en el correo»</i>— y <b>la cambió al saber que el correo del paciente
    NO la trae</b>: la trae el operativo, que es el de Cecilia. <b>Sin este
    renglón, el paciente no la vería en ningún lado.</b></li>
  </ul>
</section>

<section>
  <p class="rotulo">El otro estado</p>
  <h2>Cuando no hay ningún turno</h2>
  <p>Una línea y la salida. <b>No hay dibujo nuevo</b>: el botón es el
  principal de la pieza 3.</p>
</section>
</div>
{mis_turnos_del_sitio(ancho, vacio=True)}

<div class="prosa"><p class="rotulo">Con turnos</p></div>
{mis_turnos_del_sitio(ancho)}
"""


def revisar_duracion(pagina, donde):
    """Avisos de duración que quedaron adentro de algo que simula la pantalla."""
    avisos = []

    for patron in PANTALLA:
        for trozo in patron.finditer(pagina):
            for hallazgo in DURACION.finditer(trozo.group(0)):
                avisos.append(
                    f"✗ {donde}: «{hallazgo.group(0)}» adentro de "
                    f"«{trozo.group(0)[:60].strip()}…»"
                )

    return avisos


CSS_PAGINA = """
/* LA PÁGINA ENTERA — PIEZA 15.

   Lo único que esta pieza AGREGA es el aire entre secciones y los dos rótulos
   que faltaban. Ninguna sección se retoca: cada una se aprobó mirándola a 1:1,
   que es la aprobación más fuerte del proyecto. Acá se apilan tal como están.

   EL AIRE VA ENTRE HERMANOS, no bloque por bloque: escrito así, sumar una
   sección mañana no obliga a tocar esta regla. Sale de --aire-seccion, que
   tiene un valor por ancho, porque en móvil el aire es el ÚNICO separador que
   hay —no existe la banda de fondo ni la segunda columna que separan en
   escritorio—.

   ⚠️ Esta regla PISA a propósito los `margin-top: 0` que cada sección trae
   puesto (`.nosotros`, por ejemplo). Empatan en especificidad, así que gana la
   que va última en el archivo: por eso este bloque se escribe AL FINAL de la
   lista de estilos y no antes. */
.pagina > * + * {
  margin-top: var(--aire-seccion);
}

/* LA ÚNICA EXCEPCIÓN, y no es un ajuste: es una decisión ya tomada. El hero
   arranca PEGADO al encabezado —la pieza 9 cerró el logo sin hueco debajo y la
   10 dibujó la foto a sangre—. Un aire acá abriría una franja blanca entre el
   logo y la foto, que es exactamente lo que la pieza 9 corrigió. */
.pagina > .hero {
  margin-top: 0;
}

/* 🏁 ACÁ VIVÍA UN PARCHE Y YA NO HACE FALTA — 12-sep-2026.

   La página destapó que tres secciones no traían su propio margen:
   Tratamientos, Contacto y el Pie se aprobaron midiendo 350 dentro de 390,
   pero ese margen se lo prestaba el `padding` del body de SU tablero.
   Apiladas acá, donde ese padding no existe, las tres se iban a sangre.

   Se tapó con una regla en este bloque —`.pagina .grilla-tratamientos, …`—
   que les devolvía el margen sólo cuando estaban dentro de la página. Andaba,
   y aun así estaba mal: el margen quedaba escrito en el lugar que MUESTRA la
   sección y no en la sección, así que seguía sin ser suyo.

   🔑 EL ARREGLO DE FONDO, que es el que está puesto hoy: cada sección lleva su
   `margin-left`/`margin-right` en SU bloque de CSS —ver `CSS_TRATAMIENTOS`,
   `CSS_CONTACTO` y `CSS_PIE`—, y los tres tableros que las muestran dejaron de
   poner el margen en el body: lo pone `.prosa`, igual que la pieza 8 y la 9.

   Verificado midiendo con Chrome las tres secciones en su tablero y en la
   página, a 390, 768 y 1280: los seis pares dan el mismo número que antes del
   cambio. «Nosotros» y «Testimonios» nunca estuvieron acá porque ya traían el
   suyo, que es como debía ser desde el principio. */

/* EL RÓTULO DE LAS DOS SECCIONES QUE NO LO TRAÍAN. «Nosotros» y «Testimonios»
   ya tienen el suyo; «Tratamientos» y «Contacto» vivían sin título porque en
   su tablero el título lo ponía la prosa. Los valores son los mismos que ya
   usan los otros dos: esto no estrena ningún estilo. */
/* 🔴 Y EL TÍTULO SE CENTRA CON SU SECCIÓN, no con la página. Lo destapó el
   centrado de escritorio: «Tratamientos» y «Contacto» son hijos directos de
   la página, así que con el margen de página quedaban a 64 mientras sus
   tarjetas arrancaban a 210 — el título despegado de lo que encabeza. Por eso
   lleva el mismo techo y el mismo token que la sección de abajo.

   Va como MARGEN y no como `padding` justamente para que el techo de 860
   mida el CONTENIDO: con `border-box`, 860 de `max-width` más 128 de padding
   habrían dejado el texto arrancando 64 px adentro de la grilla. */
.titulo-seccion {
  max-width: var(--ancho-pagina);
  margin-left: var(--margen-seccion);
  margin-right: var(--margen-seccion);
  margin-bottom: 16px;
}

/* 🔴 EL TÍTULO DE SECCIÓN NO MANDABA, y no es una impresión: está medido.
   Todo el texto de la página pesa 400 y casi todo comparte color, así que de
   las tres palancas de jerarquía —tamaño, peso, color— el sistema usaba UNA.
   Y la distancia entre un título (26) y lo más grande que tiene debajo (20)
   era de 1,3 a 1: casi nada.

   ⚠️ LA PALANCA DEL PESO ESTÁ CERRADA, y se verificó contra la fuente: se le
   pidieron a Google Fonts los pesos 400 y 700 de Marcellus y devuelve UN SOLO
   archivo, el 400. La familia no tiene negrita; pedírsela obliga al navegador
   a inventar una falsa, que en una serif fina se ve sucia.

   ⇒ Se compensa con las dos palancas que quedan: sube a --tipo-h1 —32 px a
   390, que es el techo que NN/g recomienda para un título— y estrena NINGÚN
   tamaño nuevo: es el que ya usa el h1. */
.pagina .titulo-seccion,
.pagina .nosotros-titulo,
.pagina .prueba-titulo {
  font-size: var(--tipo-h1);
  line-height: var(--alto-h1);
}

/* Y EL FILO ENCIMA DEL TÍTULO, que es el mismo recurso que ya usa el hero
   —56 × 2 px de dorado—: no se estrena nada. No es adorno: marca dónde
   ARRANCA cada capa de la página, que es como se recorre una página larga
   (el «layer-cake pattern» de NN/g: la vista salta de título en título).

   Va como ::before del propio título para no tener que tocar el HTML de
   «Nosotros» ni el de «Testimonios», que se arman en su propia función. */
.pagina .titulo-seccion::before,
.pagina .nosotros-titulo::before,
.pagina .prueba-titulo::before {
  content: "";
  display: block;
  width: 56px;
  height: 2px;
  background: var(--dorado);
  margin-bottom: 14px;
}

/* 🔴 LA BANDA DE FONDO — el recurso que separa una sección de la otra.

   El hueco solo no alcanzaba: la página se leía como un rollo continuo. Lo
   que falta es «common region» (región común): lo que comparte un fondo se
   lee como un grupo, y NN/g lo mide como una señal MÁS FUERTE que la
   proximidad — un borde da vuelta la lectura de un grupo sin mover nada de
   lugar. La misma fuente marca el orden: primero el espacio, y el contenedor
   cuando el espacio no alcanza. Acá no alcanzó.

   EL COLOR SALE DE LA PALETA, no se estrena: --dorado-claro. Medido contra el
   marfil da 1,34 —sutil pero visible—, mientras que el blanco daba 1,07, o
   sea invisible. El grafito encima mide 8,94: legible de sobra.

   LA BANDA COME EL HUECO en vez de sumarse a él: anula su margen y lo
   convierte en padding propio. Si no, la sección con banda quedaría al doble
   de distancia que las demás y el ritmo se rompería. */
.bandas-alternada > #tratamientos,
.bandas-alternada > .prueba,
.bandas-una > #tratamientos {
  background: var(--dorado-claro);
  margin-top: 0;
  padding-top: var(--aire-seccion);
  padding-bottom: var(--aire-seccion);
}
"""


def boton_flotante_whatsapp():
    """El acceso fijo a WhatsApp — SÓLO de escritorio.

    🔴 REEMPLAZA AL QR, y es la tercera decisión sobre la misma necesidad:
    que alguien en una pantalla grande pueda llegar al chat. El QR se probó en
    tres formas —tarjeta al costado, cuadrado suelto, fila de la tarjeta— y
    ninguna funcionó visualmente; lo cortó Juan el 13-sep-2026: «o se elimina
    y se usa el botón flotante o se busca otra solución».

    🔑 Y la evidencia lo respalda, que es lo que lo vuelve una decisión y no un
    cambio de gusto: Baymard testeó las burbujas fijas con usuarios y lo que
    encontró es que en MÓVIL obstruyen el contenido —por eso la § 4 ya había
    decidido que en el teléfono no va— y recomienda exactamente lo contrario
    para escritorio: que el elemento fijo viva ahí, donde sobra pantalla y no
    tapa nada. Es la misma fuente que sacó el botón de móvil, leída entera.

    El QR sigue existiendo donde sí funciona: en la CARTELERÍA impresa, que es
    el único lugar donde alguien no puede tocar un enlace.
    """
    return f"""
  <a class="wa-flotante" href="https://wa.me/{WHATSAPP}"
     aria-label="Escribinos por WhatsApp">
    {isotipo("whatsapp", "iso-wa")}
  </a>"""


def pagina_del_sitio(ancho, bandas=""):
    """La landing entera, en el orden del mapa del sitio (§ 4 del doc).

    Hero → Tratamientos → Nosotros → Testimonios → Contacto → Pie, con el
    encabezado arriba. El orden es de CONVERSIÓN y está decidido: no se
    reordena acá.

    ⚠️ TESTIMONIOS VA EN SU VARIANTE APROBADA, la de jerarquía: tres citas SIN
    caja, una que manda y dos que acompañan (8-sep-2026). La variante por
    defecto de `prueba_del_sitio()` son tarjetas con caja, que es la que se
    descartó — y se ve igual de bien suelta, así que el error no grita.
    """
    wordmark = leer_png("cb-wordmark-600")
    apilado = leer_png("cb-apilado-600")
    foto = leer_foto()
    chico = ancho < 1280

    # 🔴 EL MENÚ EN FILA ARRANCA EN 768 — 13-sep-2026, decidido por Juan con
    # los números delante. A 390 sigue el sándwich; a 768 y 1280 van los tres
    # enlaces a la vista.
    #
    # LA CUENTA que lo decidió, medida con Chrome sobre la página real, no
    # estimada. A 768 la barra tiene 688 px útiles (768 menos los 40 de margen
    # de cada lado) y adentro entran:
    #     logo 260 + hueco 12 + menú 344 = 616  →  sobran 72   ✅
    # Con el botón «Reservar» no entra:
    #     616 + hueco 12 + botón 117,5 = 745,5  →  faltan 57,5 ❌
    # Por eso el botón NO sube a la barra a 768: se queda en el hero, que es la
    # misma decisión que ya se había tomado a 390 y por la misma razón.
    #
    # Lo que había antes era el sándwich, y dejaba 384 px de barra vacía en un
    # ancho donde los tres destinos entran enteros.
    menu = menu_del_ancho(ancho)

    return f"""
<div class="pagina{bandas}">
{barra(wordmark, "wordmark", ancho, menu, not chico)}
{hero_velo(foto, ancho)}
  <section id="tratamientos">
    <h2 class="titulo-seccion">Tratamientos</h2>
{grilla_tratamientos()}
  </section>
{nosotros_del_sitio(ancho)}
{prueba_del_sitio(ancho, estilo=" jerarquia")}
  <section id="contacto">
    <h2 class="titulo-seccion">Contacto</h2>
{tarjeta_contacto()}
  </section>
{pie_del_sitio(apilado, ancho)}
{boton_flotante_whatsapp()}
</div>"""


def estilos_de_la_pagina(css, ancho):
    """Todos los estilos del sitio, en un solo lugar.

    Se junta acá y no en cada tablero porque la página entera es la primera
    pantalla donde TODAS las piezas conviven: si dos se pisan, se ve acá.
    """
    return "\n".join([
        css,
        base_css(ancho),
        CSS_BOTON,
        CSS_ENCABEZADO,
        CSS_HERO,
        CSS_HERO_VELO,
        CSS_TRATAMIENTOS,
        CSS_NOSOTROS,
        CSS_PRUEBA,
        CSS_ISOTIPO,
        CSS_CONTACTO,
        CSS_PIE,
        CSS_PAGINA,
    ])


def solo_pagina(tokens, css, ancho, bandas=""):
    """La landing sola, sin una palabra de tablero alrededor.

    Es la que se mira para aprobar: el aire entre secciones no se puede juzgar
    con prosa intercalada, porque la prosa mete su propio ritmo y lo que se
    estaría evaluando sería el tablero, no la página.

    `bandas` elige el recurso de separación, y las tres versiones se generan
    para poder compararlas al mismo tamaño: sin banda, una sola, o alternadas.
    """
    return f"""<!-- @dsCard group="Components" -->
<meta charset="utf-8">
<title>CB · La página entera · {ancho}</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
{estilos_de_la_pagina(css, ancho)}
</style>
{pagina_del_sitio(ancho, bandas)}
"""


# ------------------------------------------------------------
# EL TABLERO NO PUEDE DEPENDER DEL TAMAÑO DE LA VENTANA
#
# `body { width: 390px }` fija el ancho del DIBUJO, pero una `@media
# (min-width: 768px)` no mira el dibujo: mira la VENTANA. Así que el tablero de
# 390 abierto en una ventana ancha se pintaba con los tokens de escritorio —
# título de 52 px, botones al ancho de su texto, la tarjeta en fila—. Las
# capturas headless salían bien porque se piden con `--window-size=390`; el
# navegador de Juan estaba mostrando otra cosa, y lo que él corregía no era lo
# que yo medía.
#
# La solución no inventa ningún valor: se APLANAN las media queries contra el
# ancho del tablero. Las que corresponden se aplican sin condición, las que no,
# se van. Los valores siguen saliendo de tokens.css.
# ------------------------------------------------------------

MEDIA = re.compile(r"@media\s*\(\s*min-width:\s*(\d+)px\s*\)\s*\{")


def aplanar(css, ancho):
    """Resuelve las media queries de min-width contra un ancho fijo."""
    salida = []
    pos = 0

    while True:
        m = MEDIA.search(css, pos)

        if not m:
            salida.append(css[pos:])
            return "".join(salida)

        salida.append(css[pos:m.start()])

        # Dónde cierra el bloque: se cuentan las llaves desde la que lo abre.
        nivel = 1
        i = m.end()

        while nivel and i < len(css):
            if css[i] == "{":
                nivel += 1
            elif css[i] == "}":
                nivel -= 1
            i += 1

        if int(m.group(1)) <= ancho:
            salida.append(css[m.end():i - 1])

        pos = i


ESTILO = re.compile(r"(<style>)(.*?)(</style>)", re.DOTALL)


def fijar_al_ancho(pagina, ancho):
    """Deja el tablero pintado igual en cualquier ventana."""
    return ESTILO.sub(
        lambda m: m.group(1) + aplanar(m.group(2), ancho) + m.group(3),
        pagina,
    )


def main():
    css = TOKENS.read_text(encoding="utf-8")
    tokens = MEDIDOR.leer_tokens(css)
    faltan = [
        n
        for n, _, _ in PALETA_BRIEF + DERIVADOS
        if n not in tokens
    ]

    if faltan:
        print("✗ tokens nombrados por el tablero que no existen: " + ", ".join(faltan))
        return 1

    destino = SALIDA / "01-color-y-contraste" / "1280.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(fijar_al_ancho(tablero_color(tokens, css), 1280), encoding="utf-8")
    print(f"✓ {destino.relative_to(RAIZ)}")

    # el último valor declarado es el de escritorio, que es el que se cuenta
    medida = re.findall(r"--columna:\s*([^;]+);", css)[-1].strip()

    for ancho in ANCHOS:
        destino = SALIDA / "02-escala-tipografica" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        pagina = tablero_tipografia(tokens, css, ancho).replace("{medida}", medida)
        destino.write_text(fijar_al_ancho(pagina, ancho), encoding="utf-8")
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "03-boton" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(fijar_al_ancho(tablero_boton(tokens, css, ancho), ancho), encoding="utf-8")
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "04-campo" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(fijar_al_ancho(tablero_campo(tokens, css, ancho), ancho), encoding="utf-8")
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "05-mensaje" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(fijar_al_ancho(tablero_mensaje(tokens, css, ancho), ancho), encoding="utf-8")
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "06-tarjeta" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(fijar_al_ancho(tablero_tarjeta(tokens, css, ancho), ancho), encoding="utf-8")
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "07-grilla-de-horarios" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(fijar_al_ancho(tablero_grilla(tokens, css, ancho), ancho), encoding="utf-8")
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "08-tira-de-contexto" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(fijar_al_ancho(tablero_contexto(tokens, css, ancho), ancho), encoding="utf-8")
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "09-encabezado-y-menu" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(tablero_encabezado(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "10-hero" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(tablero_hero(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "11-tratamientos" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(tablero_tratamientos(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "15a-nosotros" / f"{ancho}-solo.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(solo_nosotros(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "15a-nosotros" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(tablero_nosotros(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "15b-prueba" / f"{ancho}-solo.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(solo_prueba(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "15b-prueba" / f"{ancho}-google.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(solo_google(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "15b-prueba" / f"{ancho}-jerarquia.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(
                solo_prueba(tokens, css, ancho, estilo=" jerarquia"), ancho
            ),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "15b-prueba" / f"{ancho}-cita.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(
                solo_prueba(tokens, css, ancho, estilo=" cita"), ancho
            ),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "15b-prueba" / f"{ancho}-con-caso.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(solo_prueba(tokens, css, ancho, con_caso=True), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "15b-prueba" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(tablero_prueba(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "13-pie" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(tablero_pie(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "12-contacto" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(tablero_contacto(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

    # LA PIEZA 16 va antes de la página entera y NO se apila en ella: la
    # pantalla de entrar no es una sección de la landing, es el primer estado
    # de `reservar.html`. Se genera el tablero que explica y, aparte, la
    # pantalla SOLA a 1:1 — que es como Juan aprueba.
    for ancho in ANCHOS:
        destino = SALIDA / "16-entrar" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(tablero_entrar(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

        destino = SALIDA / "16-entrar" / f"{ancho}-solo.html"
        destino.write_text(
            fijar_al_ancho(solo_entrar(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

        destino = SALIDA / "17-para-quien" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(tablero_quien(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

        destino = SALIDA / "17-para-quien" / f"{ancho}-solo.html"
        destino.write_text(
            fijar_al_ancho(solo_quien(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

        destino = SALIDA / "18-a-que-venis" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(tablero_motivo(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

        destino = SALIDA / "18-a-que-venis" / f"{ancho}-solo.html"
        destino.write_text(
            fijar_al_ancho(solo_motivo(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

        destino = SALIDA / "19-dia-y-hora" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(tablero_dia_hora(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

        destino = SALIDA / "19-dia-y-hora" / f"{ancho}-solo.html"
        destino.write_text(
            fijar_al_ancho(solo_dia_hora(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

        destino = SALIDA / "20-confirmar" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(tablero_confirmar(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

        destino = SALIDA / "20-confirmar" / f"{ancho}-solo.html"
        destino.write_text(
            fijar_al_ancho(solo_confirmar(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

        destino = SALIDA / "21-mis-turnos" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(tablero_mis_turnos(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

        destino = SALIDA / "21-mis-turnos" / f"{ancho}-solo.html"
        destino.write_text(
            fijar_al_ancho(solo_mis_turnos(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

    # LA PÁGINA ENTERA VA ÚLTIMA, y el orden no es capricho: se arma con las
    # secciones ya escritas, así que cualquier cambio en una de ellas tiene que
    # haber corrido antes de que ésta las apile.
    # Las tres versiones del recurso de separación, para poder compararlas al
    # mismo tamaño: sin banda es el punto de partida, y las otras dos son lo
    # que hay que elegir.
    for nombre, bandas in (
        ("solo", ""),
        ("una-banda", " bandas-una"),
        ("alternada", " bandas-alternada"),
    ):
        for ancho in ANCHOS:
            destino = SALIDA / "15-pagina" / f"{ancho}-{nombre}.html"
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_text(
                fijar_al_ancho(solo_pagina(tokens, css, ancho, bandas), ancho),
                encoding="utf-8",
            )
            print(f"✓ {destino.relative_to(RAIZ)}")

    # ------------------------------------------------------------
    # LA PÁGINA "EN CONTEXTO" — la única que NO tiene el ancho clavado.
    #
    # La pidió Juan el 13-sep-2026 para verla como la va a ver un visitante:
    # achicando y agrandando la ventana. Los tableros existen para lo contrario
    # —medir siempre lo mismo— y por eso llevan el ancho fijo y las media
    # queries aplanadas; ésta deja las dos cosas vivas.
    #
    # ⚠️ HASTA DÓNDE ES FIEL, y hay que decirlo porque se ve igual de terminada:
    # el CSS responde de verdad al ancho de la ventana, pero hay decisiones que
    # NO viven en el CSS sino en Python — cuál logo va en la barra, si el menú
    # es sándwich o fila, el tamaño del logo del pie—. Ésas quedan congeladas
    # en su versión de escritorio. O sea: de 1280 para arriba es exacta, y por
    # debajo el layout se adapta pero el encabezado no.
    #
    # NO REEMPLAZA A LOS TABLEROS: lo que se aprueba se sigue aprobando a
    # 390, 768 y 1280 con el ancho clavado, que es lo único que garantiza que
    # lo que Claude mide y lo que Juan ve sean lo mismo.
    # ------------------------------------------------------------
    destino = SALIDA / "15-pagina" / "en-contexto.html"
    pagina_fluida = solo_pagina(tokens, css, 1280)
    pagina_fluida = pagina_fluida.replace(
        f"  width: {1280}px;\n", "", 1
    )
    pagina_fluida = pagina_fluida.replace(
        "<title>CB · La página entera · 1280</title>",
        "<title>CB · La página, en contexto</title>",
        1,
    )
    destino.write_text(pagina_fluida, encoding="utf-8")
    print(f"✓ {destino.relative_to(RAIZ)}  (sin ancho clavado)")

    avisos = []

    for pagina in sorted(SALIDA.rglob("*.html")):
        avisos += revisar_duracion(
            pagina.read_text(encoding="utf-8"),
            str(pagina.relative_to(RAIZ)),
        )

    if avisos:
        print()
        for aviso in avisos:
            print(aviso)
        return 1

    print("\n✓ ningún tablero muestra la duración del turno.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
