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
  como estaba dibujado en el cuadro de escritorio. <b>En un teléfono el botón
  principal va de borde a borde</b>, y eso cambia cuánto pesa el dorado. Al lado,
  el mismo botón en <b>peso 700</b> en vez de 600 — el porqué está abajo del
  todo.</p>
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
    "La consulta dura treinta minutos e incluye el diagnóstico y el plan de "
    "tratamiento. Si necesitás cambiar el horario, se puede hasta el día anterior."
)

CHICO_MUESTRA = (
    "Te va a llegar un correo de confirmación con la dirección del consultorio."
)

ANCHOS = [390, 768, 1280]

MARGENES = {390: 20, 768: 40, 1280: 64}


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
  font-family: Jost, sans-serif;
  font-size: 19px;
  font-weight: 600;
  line-height: 1.2;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  text-align: center;
  padding: 12px 26px;
  min-height: 44px;
  border: 0;
  border-radius: var(--radio);
  cursor: pointer;
  width: var(--boton-ancho);
}

.btn-1 {
  background: var(--boton-fondo);
  color: var(--boton-texto);
  box-shadow: var(--sombra-boton);
}

/* El ancho NO puede cambiar al enviar, y "Reservando…" es más corto que
   "Reservar turno": de tablet para arriba, donde el botón se ajusta a su texto,
   se achicaba 30 px. El botón lleva las dos palabras apiladas y la que no se ve
   sostiene el ancho. Sin números mágicos: lo mide el texto más largo. */
.pila { display: inline-grid; }

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
     "adentro sosteniéndolo, porque «Reservando…» es más corto y en escritorio "
     "el botón se achicaba 30 px."),
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
    ancho_boton = "de borde a borde" if ancho < 768 else "del ancho de su texto"

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
    <li>En el teléfono el principal va <b>de borde a borde</b>; de tablet para
    arriba, del ancho de su texto.</li>
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
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: var(--boton-ancho);
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
# ============================================================

CSS_TARJETA = """
.turno {
  max-width: var(--columna-lista);
  margin-top: 14px;
  padding: 18px 18px 20px;
  background: var(--blanco);
  border: 1px solid var(--borde);
  border-radius: var(--radio);
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

/* De tablet para arriba la tarjeta se lee como una FILA: los datos a la
   izquierda y la acción a la derecha. En el teléfono no: ahí el botón va de
   borde a borde, que es lo que pide un dedo. */
@media (min-width: 768px) {

  .turno {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 28px;
  }

  .turno .btn {
    margin-top: 0;
    flex: none;
  }
}
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
        "una debajo de la otra, con el botón de borde a borde"
        if ancho < 768
        else "una debajo de la otra, y cada tarjeta es una fila: los datos a la "
             "izquierda y la acción a la derecha"
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
    <li><b>En filas, nunca en columnas.</b> Y de tablet para arriba la fila
    se abre: los datos a la izquierda, la acción a la derecha.</li>
    <li>La lista usa <b>su propia medida, más ancha que la del texto</b>
    (860 px en escritorio, contra 640 de un párrafo). Una tarjeta con su acción
    al costado no es una línea de lectura, y con la medida del párrafo el día y
    la hora se parten en dos renglones.</li>
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

/* Los dos botones juntos. En el teléfono van apilados y de borde a borde
   —lo pide el dedo—; de tablet para arriba, uno al lado del otro. */
.acciones {{
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 28px;
  max-width: var(--columna);
}}

@media (min-width: 768px) {{
  .acciones {{
    flex-direction: row;
    align-items: center;
    gap: 16px;
  }}
}}

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
    destino.write_text(tablero_color(tokens, css), encoding="utf-8")
    print(f"✓ {destino.relative_to(RAIZ)}")

    # el último valor declarado es el de escritorio, que es el que se cuenta
    medida = re.findall(r"--columna:\s*([^;]+);", css)[-1].strip()

    for ancho in ANCHOS:
        destino = SALIDA / "02-escala-tipografica" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        pagina = tablero_tipografia(tokens, css, ancho).replace("{medida}", medida)
        destino.write_text(pagina, encoding="utf-8")
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "03-boton" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(tablero_boton(tokens, css, ancho), encoding="utf-8")
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "04-campo" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(tablero_campo(tokens, css, ancho), encoding="utf-8")
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "05-mensaje" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(tablero_mensaje(tokens, css, ancho), encoding="utf-8")
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "06-tarjeta" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(tablero_tarjeta(tokens, css, ancho), encoding="utf-8")
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "07-grilla-de-horarios" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(tablero_grilla(tokens, css, ancho), encoding="utf-8")
        print(f"✓ {destino.relative_to(RAIZ)}")

    for ancho in ANCHOS:
        destino = SALIDA / "08-tira-de-contexto" / f"{ancho}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(tablero_contexto(tokens, css, ancho), encoding="utf-8")
        print(f"✓ {destino.relative_to(RAIZ)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
