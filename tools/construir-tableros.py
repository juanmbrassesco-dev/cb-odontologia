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
        "subtitulo_color": "apagado",
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

td i {{ color: var(--apagado); font-style: normal; }}
td small {{ color: var(--apagado); }}

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
  padding: 22px;
  margin: 18px 0;
}}

.demo p {{ font-size: 15px; margin: 10px 0 16px; }}

.tamano {{
  font-size: 13px;
  line-height: 1.5;
  color: var(--apagado);
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
  color: var(--apagado);
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
     "dentro de una tarjeta o un turno", "Limpieza y profilaxis"),
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
  color: var(--apagado);
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
  color: var(--apagado);
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
    <h2>Limpieza y profilaxis</h2>
    <p class="muestra-texto">{CUERPO_MUESTRA}</p>
    <p class="chico" style="margin-top: 10px; color: var(--apagado)">{CHICO_MUESTRA}</p>
  </div>
</section>

<p class="pie">Ni un tamaño escrito a mano en este tablero: todos salen de las
variables de <code>tokens.css</code>, las mismas que va a usar el sitio. La
línea de lectura está limitada a {{medida}} en escritorio para que el ojo no pierda el renglón
al volver.</p>
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

    return 0


if __name__ == "__main__":
    sys.exit(main())
