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

body {{
  width: {ancho}px;
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
}}

h1 {{ font-size: var(--tipo-h1); line-height: var(--alto-h1); }}
h2 {{ font-size: var(--tipo-h2); line-height: var(--alto-h2); }}
h3 {{ font-size: var(--tipo-h3); line-height: var(--alto-h3); }}

p {{ max-width: var(--columna); }}

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


def tarjeta_turno(cuando, tratamiento, profesional, quien):
    return (
        '\n    <div class="turno">'
        '\n      <div class="datos">'
        f'\n        <h3>{cuando}</h3>'
        f'\n        <p class="que">{tratamiento} {profesional}</p>'
        f'\n        <p class="quien">{quien}</p>'
        '\n      </div>'
        '\n      <button class="btn btn-2">Cancelar turno</button>'
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
  min-height: 48px;
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


def celda_dia(numero, clase, con_lugar):
    if clase == "vacío":
        return '\n        <span></span>'

    marca = '<span class="marca"></span>' if con_lugar else ''
    apagado = " disabled" if clase == "dia-apagado" else ""
    return f'\n        <button class="dia {clase}"{apagado}>{numero}{marca}</button>'


def almanaque():
    letras = "".join(
        f'\n        <span class="letra">{l}</span>'
        for l in ("L", "M", "M", "J", "V", "S", "D")
    )
    celdas = "".join(celda_dia(*d) for d in DIAS)

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
    re.compile(r'<p class="(?:ayuda|muestra-texto)">.*?</p>', re.DOTALL),
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
  padding: 8px var(--margen-pagina);
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

.menu-fila a {
  color: var(--grafito);
  text-decoration: none;
  font-size: var(--tipo-rotulo);
  line-height: var(--alto-rotulo);
  letter-spacing: var(--letra-rotulo);
  text-transform: uppercase;
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
  {barra(wordmark, "wordmark", ancho, "boton" if chico else "fila", not chico)}
  <p class="marca-muestra">Apilado · {ENCABEZADO_LOGO[ancho]} px de ancho ·
  <b>{alto_a} px de alto</b></p>
  {barra(apilado, "apilado", ancho, "boton" if chico else "fila", not chico)}
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
  <p>Las tres cosas que pide la § 4 —el logo, los enlaces y el botón
  <b>Reservar</b>— <b>no entran juntas a {ancho} px</b>, y no es una
  impresión: el logo mide 200, el botón 160 y el de menú 44, más dos huecos
  de 12. Son <b>428 px</b> contra los <b>350</b> que deja el margen de
  página.</p>
  <p style="margin-top: 12px">🏁 <b>Resuelto por Juan: el que se va del
  encabezado es el BOTÓN.</b> Queda el logo y el menú, y el <b>Reservar</b>
  vive en el hero —que es donde el paciente llega leyendo— y adentro del menú
  abierto. <i>El encabezado no es el único lugar donde puede estar la acción;
  el menú sí es el único lugar donde pueden estar los enlaces.</i></p>
  <p class="marca-muestra">El encabezado, cerrado</p>
  {barra(wordmark, "wordmark", ancho, "boton", False)}
  <p class="marca-muestra">Con el menú abierto</p>
  {barra(wordmark, "wordmark", ancho, "boton", False, abierto=True)}
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

H1 = ("Odontología y estética dental en Santa Fe, "
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
{barra(logo, "wordmark", ancho, "boton" if chico else "fila", not chico)}
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
.grilla-tratamientos {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 20px;
  max-width: var(--columna-lista);
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
</style>

<p class="rotulo">Fase ⑧ · Pieza 11 · {ancho} px</p>
<h1>Tratamientos</h1>
<div class="regla"></div>
<p><b>Los nombres no se inventan.</b> Son las filas de la tabla
<code>tratamientos</code>, la misma lista que alimenta el desplegable de la
reserva: si mañana se agrega uno, aparece en los dos lados.</p>

<section>
  <p class="rotulo">La grilla, a 1:1</p>
  <h2>Nueve tarjetas</h2>
  {grilla_tratamientos()}
</section>

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
    "burbuja":
        '<path d="M20.6 11.6 a8.4 8.4 0 0 1-12.2 7.5 L3.8 20.4 l1.4-4.5 '
        'a8.4 8.4 0 1 1 15.4-4.3 z"/>',
    "sobre":
        '<rect x="3.2" y="5.4" width="17.6" height="13.2" rx="2.4"/>'
        '<path d="M3.9 7 l8.1 5.9 l8.1-5.9"/>',
}

CSS_CONTACTO = """
/* La tarjeta es blanca sobre marfil, y ese par mide 1,03: la forma la marca
   el BORDE, nunca el relleno. Es la misma regla del campo, del botón apagado
   y de la tarjeta de tratamiento — la cuarta vez que aparece. */
.contacto {
  background: var(--blanco);
  border: 1px solid var(--dorado-claro);
  border-radius: var(--radio);
  max-width: var(--columna-lista);
  margin-top: 20px;
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
    """Un ícono de 24, del mismo trazo que los de la grilla de tratamientos."""
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


def tarjeta_contacto():
    telefono = fila_enlace(
        "telefono",
        "tel:" + TELEFONO_MARCADO,
        TELEFONO_ESCRITO,
        "Llamar al consultorio",
    )
    whatsapp = fila_enlace(
        "burbuja",
        "https://wa.me/" + WHATSAPP,
        "Escribinos por WhatsApp",
        "Abrir la conversación de WhatsApp",
    )
    correo = fila_texto("sobre", CORREO)

    return f"""
  <div class="contacto">
    {fila_direccion()}
    {telefono}
    {whatsapp}
    {correo}
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
{CSS_CONTACTO}
</style>

<p class="rotulo">Fase ⑧ · Pieza 12 · {ancho} px</p>
<h1>Contacto</h1>
<div class="regla"></div>
<p><b>Los datos no se inventan.</b> La dirección, el teléfono y el correo son
los que dio Cecilia el 1-sep-2026 (§ 9.1.e). <b>Acá se copian una sola vez</b>,
en las constantes del generador.</p>

<section>
  <p class="rotulo">La tarjeta, a 1:1</p>
  <h2>Cuatro datos</h2>
  {tarjeta_contacto()}
</section>

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

  <p class="rotulo">Una marca que no es nuestra</p>
  <h2>El logotipo de WhatsApp no entra al sitio</h2>
  <p><b>Decisión de Juan, 4-sep-2026: «si es verde, no va».</b> El logotipo
  oficial existe en un solo color —su verde <code>#25D366</code>— y las reglas
  de Meta dicen textual <b>«you shouldn't modify any colors in our logos»</b>:
  no hay versión dorada permitida. <b>O entra su verde, o no entra el
  logotipo.</b></p>
  <p style="margin-top: 12px"><b>Y sus propias reglas empujan para el mismo
  lado:</b> <i>«DON'T make WhatsApp the most distinctive or prominent feature
  of your materials»</i>. Un verde saturado adentro de una tarjeta de íconos
  dorados sería lo más llamativo de la página — justo lo que la § 4 no quiere,
  porque WhatsApp acá es <b>canal secundario: disponible, no promovido</b>.</p>
  <p class="dato" style="margin-top: 12px">🔴 <b>El límite que hay que vigilar
  al dibujar el nuestro:</b> <i>«DON'T use an image confusingly similar to the
  WhatsApp telephone logo»</i>. Nuestra burbuja <b>no lleva el teléfono
  adentro</b>. El día que alguien se lo dibuje «para que se reconozca mejor»,
  cae justo en lo prohibido.</p>
  <p class="dato" style="margin-top: 12px">⏱ <b>Lo que esto le deja a la pieza
  14, y se resuelve ahí:</b> el botón flotante es <b>sólo ícono</b> (§ 4). Sin
  el logotipo verde, una burbuja sola puede leerse como «chat» y no como
  WhatsApp. <b>O el botón gana una palabra, o cambia de forma.</b></p>
  <p class="dato" style="margin-top: 12px">📌 <b>Y toca los textos:</b> se
  escribe <b>WhatsApp</b>, con las dos mayúsculas, y <b>nunca como verbo</b> —
  las dos son reglas textuales de ellos. «Escribinos por WhatsApp» cumple.</p>

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
    <li><b>El mapa se apunta con coordenada, nunca con la dirección
    escrita.</b> «25 de Mayo 3725, Santa Fe» tiene dos lugares posibles en la
    misma provincia.</li>
    <li><b>La matrícula no va acá: va en el pie</b> (pieza 13). Es un renglón
    fijo de toda pieza pública, y el pie es donde se lo busca.</li>
  </ul>
</section>
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
        destino = SALIDA / "12-contacto" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            fijar_al_ancho(tablero_contacto(tokens, css, ancho), ancho),
            encoding="utf-8",
        )
        print(f"✓ {destino.relative_to(RAIZ)}")

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
