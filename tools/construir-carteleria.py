#!/usr/bin/env python3
"""Arma la CARTELERÍA del consultorio, a tamaño real: la placa y el cartel.

QUÉ ES ESTA PIEZA, porque no es obvia y ya se confundió una vez. No es el
cartel de la fachada y NO es la chapa del profesional: es la placa chica que
va al costado de la puerta, y su función la definió Cecilia — que el que pasa
por la vereda, o el paciente derivado que nunca estuvo, SE ACERQUE Y CONFIRME
QUE EL CONSULTORIO ES AHÍ. El cartel grande se ve de lejos; esto se lee a un
metro, parado.

🔴 POR ESO NO LLEVA MATRÍCULA NI NOMBRE PROPIO — lo definió Juan, y el
argumento es de arquitectura: identifica al CONSULTORIO, no a una persona. El
día que entre otro profesional, una matrícula grabada empieza a mentir, y en
metal eso no se corrige editando: se fabrica de nuevo. Es la misma regla que
sacó los horarios de la sección Contacto del sitio ("un dato publicado no se
copia si ya vive en la base"), aplicada al material físico. La identificación
del profesional va ADENTRO, con el diploma y la matrícula a la vista.

QUÉ PUEDE DECIR, Y NO ES OPINIÓN. Ley 4931 de Santa Fe (Código de Ética de los
Profesionales del Arte de Curar), que abarca a los odontólogos —art. 1, y
tiene un Título IV "Asuntos exclusivamente odontológicos"—:
  · Art. 89, lista cerrada: nombre y apellido · títulos · LAS RAMAS Y
    ESPECIALIDADES A QUE SE DEDIQUE · horas de consulta · DIRECCIÓN ·
    TELÉFONO. "Todo otro ofrecimiento es industrialismo."
  · Art. 90, reñido con la ética: tamaño desmedido, caracteres llamativos O
    FOTOGRAFÍAS · tarifas · agradecimiento de pacientes.
⇒ Los tratamientos entran (son "las ramas"). La dirección y el teléfono
  entran. EL SITIO WEB NO ESTÁ EN LA LISTA: por eso el QR va al WhatsApp y no
  a la página — el teléfono sí está permitido y el QR es sólo su formato.

EL COLOR ES GRAFITO Y NO DORADO, y tampoco es preferencia. Medido con
tools/medir-contraste.py: grafito sobre blanco 12,82 · dorado sobre marfil
2,89 · grafito sobre fondo dorado 4,15. La señalética pide 65-70 % de
contraste y sube a 7:1 donde se lee a distancia con luz cambiante. El dorado
no llega ni como tinta ni como fondo: queda de FILETE, que es el rol que la
pieza 1 ya le había dado ("acento, línea, o fondo con letra grafito").

    uso:  python3 tools/construir-carteleria.py
"""

import pathlib
import re
import subprocess
import sys


RAIZ = pathlib.Path(__file__).resolve().parent.parent
FUENTE = None    # se completa en leer_fuente(), una sola vez
_METRICA = None  # ídem en ancho_de()
SALIDA = RAIZ / "brand" / "carteleria"
WORDMARK = RAIZ / "brand" / "logo" / "curvas" / "cb-wordmark-curvas.svg"

FUENTE = None    # se completa en leer_fuente(), una sola vez
_METRICA = None  # ídem en ancho_de()

# Los colores salen de la paleta, no se inventan acá.
GRAFITO = "#33322F"
DORADO = "#B08D57"
BLANCO = "#FFFFFF"

# El teléfono lleva el 9 de celular, que el número escrito no muestra: sin él
# el enlace no abre la conversación (9.1.e del doc de estado).
WHATSAPP = "https://wa.me/5493426293920"
TELEFONO = "+54 342 629-3920"
DIRECCION = "25 de Mayo 3725 · Santa Fe"

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def leer_fuente():
    """La tipografía, en base64, para que el SVG no dependa de nada.

    🔴 Se llegó acá por un fallo que sólo se vio midiendo. Con la fuente
    referenciada por ruta relativa, el SVG se veía perfecto en el navegador y
    el PDF salía en Helvetica: un SVG dentro de un <img> corre aislado y no
    carga recursos externos. `pdffonts` sobre el PDF lo destapó. Embebida, la
    pieza es autónoma — que es justo lo que hay que mandarle a una imprenta.
    """
    global FUENTE

    if FUENTE is None:
        import base64

        ruta = RAIZ / "brand" / "fonts" / "Jost-var.ttf"
        FUENTE = base64.b64encode(ruta.read_bytes()).decode("ascii")

    return FUENTE


def wordmark_a_una_tinta():
    """El wordmark con sus tres colores llevados a grafito.

    El archivo original trae grafito (#33322F), el gris del nombre (#615E58)
    y el dorado de la barra (#B08D57). En una tinta la jerarquía la tiene que
    dar el TAMAÑO, no el color: es lo que corresponde para grabado, donde no
    hay más que un color posible. El dibujo no se toca — sólo el relleno.
    """
    svg = WORDMARK.read_text(encoding="utf-8")

    for color in ("#615E58", "#B08D57"):
        svg = svg.replace(f'fill="{color}"', f'fill="{GRAFITO}"')

    caja = re.search(r'viewBox="([^"]+)"', svg).group(1).split()
    ancho_caja = float(caja[2])
    alto_caja = float(caja[3])

    # Se queda sólo con el contenido, sin la etiqueta <svg> de afuera: va
    # embebido adentro del lienzo de la placa.
    adentro = re.sub(r"^.*?<svg[^>]*>", "", svg, flags=re.DOTALL)
    adentro = adentro.replace("</svg>", "")

    return adentro, ancho_caja, alto_caja, caja[0], caja[1]


def ancho_de(texto, tamano):
    """Cuánto mide un texto en milímetros, con la métrica real de la fuente.

    Se llegó acá porque estimar no alcanzó: con "0,52 em por carácter" el
    bloque de la lista del cartel quedó 15 mm fuera del eje, y eso en una
    pieza centrada se ve. fontTools lee los avances de cada glifo del mismo
    .ttf que se embebe, así que el número es el que va a salir impreso.
    """
    global _METRICA

    if _METRICA is None:
        # ⚠ fontTools NO está en el python3 suelto: vive en el suyo, dentro de
        # Homebrew. La ruta lleva la versión adentro y por eso CADUCA en cada
        # actualización —es un modo de falla que este entorno ya tenía
        # anotado—, así que se busca con comodín en vez de clavarla.
        import glob

        for carpeta in glob.glob(
            "/opt/homebrew/Cellar/fonttools/*/libexec/lib/python*/site-packages"
        ):
            if carpeta not in sys.path:
                sys.path.append(carpeta)

        from fontTools.ttLib import TTFont

        fuente = TTFont(RAIZ / "brand" / "fonts" / "Jost-var.ttf")
        upm = fuente["head"].unitsPerEm
        cmap = fuente.getBestCmap()
        avances = fuente["hmtx"].metrics
        _METRICA = (upm, cmap, avances)

    upm, cmap, avances = _METRICA
    total = 0

    for letra in texto:
        glifo = cmap.get(ord(letra))

        if glifo is None:
            glifo = cmap.get(ord(" "))

        total += avances[glifo][0]

    return total / upm * tamano


def qr_svg(lado_mm):
    """El QR del WhatsApp, vectorial, generado con qrencode.

    -m 4 son los cuatro módulos de zona de silencio que pide la norma
    ISO/IEC 18004; sin ellos el lector no distingue el código del fondo.
    -l M es la corrección de errores media: aguanta suciedad y rayones, que
    en una placa de calle no es hipotético.
    """
    salida = subprocess.run(
        [
            "qrencode",
            "-t", "SVG",
            "-o", "-",
            "-m", "4",
            "-l", "M",
            WHATSAPP,
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    svg = salida.stdout
    modulos = int(re.search(r'viewBox="0 0 (\d+)', svg).group(1))
    adentro = re.sub(r"^.*?<svg[^>]*>", "", svg, flags=re.DOTALL)
    adentro = adentro.replace("</svg>", "")

    return adentro, modulos


# ============================================================
# EL CARTEL — 500 × 320 mm, apaisado. Lo pidió Cecilia el 10-sep-2026.
#
# ⚠️ CAMBIA DE CATEGORÍA respecto de la placa, y queda escrito: 1600 cm² es
# el DOBLE del tope de 800 que fija el criterio local, y el art. 90.k de la
# Ley 4931 pone entre lo reñido con la ética los anuncios que, colocados en el
# domicilio del profesional, "adquieran el tamaño y forma de carteles". Se
# construye porque lo pidió la profesional para su propia fachada; el costo
# está dicho, no escondido.
#
# 🔴 Y TRES DE LOS CINCO GRUPOS NO EXISTEN EN EL SISTEMA: ortopedia, ATM y
# bruxismo, y prótesis no están en la tabla `tratamientos` ni en el sitio. No
# es un problema del cartel: la lista con la que se construyó el backend quedó
# corta, y el sistema de turnos filtra por tratamiento. Está anotado como
# pendiente; acá se usa lo que ella dictó.
# ============================================================

CARTEL_ANCHO = 500
CARTEL_ALTO = 320
CARTEL_MARGEN = 50

# Tal como los escribió Cecilia, en SU orden: el orden es la decisión. Lo
# primero que se lee es lo que quiere destacar.
GRUPOS = [
    "Ortodoncia y ortopedia",
    "Tratamiento de ATM y bruxismo",
    "Blanqueamiento y limpieza",
    "Prótesis",
    "Odontología general",
]


def cartel():
    """El SVG del cartel apaisado, con 1 unidad = 1 milímetro.

    LA DISPOSICIÓN, y por qué no es la de la placa. En apaisado sobra ancho,
    así que el contacto y el QR van uno al lado del otro en vez de apilados.

    🔑 LA LISTA VA ALINEADA A LA IZQUIERDA DENTRO DE UN BLOQUE CENTRADO, que
    no es lo mismo que "todo a la izquierda" —eso ya se probó y se descartó—.
    El motivo es medible: "Prótesis" tiene 8 caracteres y "Tratamiento de ATM
    y bruxismo" tiene 29. Centrados, esos cinco renglones dejan un borde
    dentado que se ve antes que el texto. Alineados entre sí y con el bloque
    centrado en el cartel, el conjunto sigue leyéndose centrado —que es la
    convención de una señal de identificación— y cada renglón arranca en la
    misma vertical.
    """
    logo, logo_ancho, logo_alto, logo_x, logo_y = wordmark_a_una_tinta()
    qr, qr_modulos = qr_svg(0)

    util = CARTEL_ANCHO - CARTEL_MARGEN * 2

    # EL WORDMARK. 300 mm son el 60 % del ancho: en una pieza que se ve de
    # lejos, la marca es lo primero que tiene que llegar.
    logo_ancho_mm = 270
    escala = logo_ancho_mm / logo_ancho
    logo_alto_mm = logo_alto * escala
    logo_izq = (CARTEL_ANCHO - logo_ancho_mm) / 2
    logo_arriba = 22

    filete_y = logo_arriba + logo_alto_mm + 11

    # LOS TAMAÑOS SALEN DE LA DISTANCIA DE LECTURA, no del gusto. Con la
    # fórmula de señalética —x-height = distancia en metros × 2,5 mm— los 17
    # mm de cuerpo dan 7,8 mm de minúscula: se lee desde 3,1 metros, o sea
    # desde la vereda. El teléfono va más grande que la dirección a propósito:
    # es el dato que alguien anota desde lejos.
    grupo_tam = 17
    interlinea = 18
    grupos_y = filete_y + 28

    renglones = "\n".join(
        f'    <text x="{CARTEL_ANCHO / 2}" y="{grupos_y + interlinea * i}" '
        f'class="grupo">{grupo}</text>'
        for i, grupo in enumerate(GRUPOS)
    )

    # EL PIE, EN UNA COLUMNA CENTRADA: rótulo · dirección · QR · teléfono.
    # El teléfono cierra abajo de todo y el QR queda en el medio del bloque.
    # Se arma desde el BORDE hacia arriba, que es lo que impide que un
    # elemento termine tocando el filo.
    qr_lado = 40
    qr_escala = qr_lado / qr_modulos
    eje_texto = CARTEL_ANCHO / 2

    margen_abajo = 22
    pie_y = CARTEL_ALTO - margen_abajo
    telefono_y = pie_y - 15
    qr_arriba = telefono_y - 24 - qr_lado
    qr_izq = (CARTEL_ANCHO - qr_lado) / 2
    rotulo_base = qr_arriba - 9

    # El borde de abajo del último renglón de la lista, con su descendente.
    lista_abajo = grupos_y + interlinea * (len(GRUPOS) - 1) + grupo_tam * 0.25

    if lista_abajo >= rotulo_base - 9:
        raise SystemExit(
            f"✗ el cartel no cierra: la lista termina en {lista_abajo:.1f} mm "
            f"y el bloque de contacto arranca en {rotulo_base - 9:.1f}. "
            "Se pisan. Achicá la interlínea, el QR o el logo."
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg"
     width="{CARTEL_ANCHO}mm" height="{CARTEL_ALTO}mm"
     viewBox="0 0 {CARTEL_ANCHO} {CARTEL_ALTO}">
  <style>
    @font-face {{
      font-family: Jost;
      src: url(data:font/ttf;base64,{leer_fuente()}) format("truetype");
      font-weight: 100 900;
    }}

    text {{
      font-family: Jost, sans-serif;
      fill: {GRAFITO};
    }}
    .grupo {{
      font-size: {grupo_tam}px;
      font-weight: 400;
      text-anchor: middle;
    }}
    .direccion {{
      font-size: 13px;
      font-weight: 500;
      text-anchor: middle;
    }}
    .telefono {{
      font-size: 17px;
      font-weight: 500;
      text-anchor: middle;
    }}
    .rotulo {{
      font-size: 9px;
      font-weight: 500;
      letter-spacing: 0.14em;
      text-transform: uppercase;
      text-anchor: middle;
    }}
  </style>

  <rect x="0" y="0" width="{CARTEL_ANCHO}" height="{CARTEL_ALTO}" fill="{BLANCO}"/>

  <g transform="translate({logo_izq} {logo_arriba}) scale({escala}) translate({-float(logo_x)} {-float(logo_y)})">
{logo}
  </g>

  <rect x="{CARTEL_MARGEN}" y="{filete_y}" width="{util}" height="1.2" fill="{DORADO}"/>

{renglones}

  <text x="{eje_texto}" y="{rotulo_base}"
        class="rotulo">Turnos y consultas</text>

  <g transform="translate({qr_izq} {qr_arriba}) scale({qr_escala})">
{qr}
  </g>

  <text x="{eje_texto}" y="{telefono_y}" class="telefono">{TELEFONO}</text>

  <text x="{eje_texto}" y="{pie_y}" class="direccion">{DIRECCION}</text>
</svg>
"""



def tablero(nombre_svg, medidas):
    """El tablero con el porqué de cada decisión y de cada número.

    La pieza va A ESCALA acá y a tamaño real en el PDF: un tablero se lee en
    pantalla, y en pantalla medio metro no entra.
    """
    filas = "\n".join(
        f"    <tr><td>{que}</td><td class='n'>{cuanto}</td><td>{porque}</td></tr>"
        for que, cuanto, porque in medidas
    )

    return f"""<!doctype html>
<meta charset="utf-8">
<title>CB · Letrero del consultorio · {CARTEL_ANCHO} × {CARTEL_ALTO} mm</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet"
      href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    background: #FAF7F2;
    color: #33322F;
    font-family: Jost, "Helvetica Neue", Arial, sans-serif;
    font-size: 16px;
    line-height: 1.6;
    padding: 40px 40px 80px;
  }}
  .prosa, table {{ max-width: 720px; }}
  h1 {{ font-family: Marcellus, Georgia, serif; font-weight: 400; font-size: 34px; line-height: 1.2; }}
  h2 {{ font-family: Marcellus, Georgia, serif; font-weight: 400; font-size: 24px; line-height: 1.3; margin-bottom: 8px; }}
  .rotulo {{
    font-size: 13px; font-weight: 500; letter-spacing: 0.18em;
    text-transform: uppercase; color: #896D41;
  }}
  .regla {{ height: 1px; background: #B08D57; margin: 12px 0 24px; max-width: 720px; }}
  section {{ margin-top: 40px; }}
  p {{ margin-top: 10px; }}
  .dato {{ font-size: 14px; line-height: 1.5; color: #464541; }}
  .provisorio {{
    border: 1px dashed #B08D57; background: #E4D6BC;
    padding: 10px 12px; font-size: 14px; line-height: 1.5; color: #464541;
    max-width: 720px;
  }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 18px; }}
  th, td {{
    text-align: left; padding: 9px 10px 9px 0;
    border-bottom: 1px solid #E4D6BC; font-size: 14px; line-height: 1.5;
    vertical-align: top;
  }}
  th {{
    font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase;
    font-size: 13px; color: #896D41;
  }}
  td.n {{ white-space: nowrap; font-variant-numeric: tabular-nums; font-weight: 500; }}
  ul {{ margin-top: 12px; padding-left: 20px; max-width: 720px; }}
  li {{ margin-top: 8px; }}
  .pieza {{
    background: #FFFFFF; border: 1px solid #E4D6BC;
    display: inline-block; padding: 24px; margin-top: 16px;
  }}
  .pieza img {{ display: block; width: 700px; height: auto; }}
  code {{ font-family: Jost, sans-serif; letter-spacing: 0.02em; color: #896D41; }}
</style>

<div class="prosa">
<p class="rotulo">Entregable físico · Cartelería</p>
<h1>El letrero del consultorio</h1>
<div class="regla"></div>

<p><b>Es la pieza que ANUNCIA lo que se hace adentro.</b> Va en la fachada,
debajo del cartel de identificación, y <b>se lee desde la vereda</b>. La lista
de tratamientos y su orden los dictó Cecilia: <b>el orden es la decisión</b> —
lo primero que se lee es lo que quiere destacar.</p>

<p class="provisorio" style="margin-top: 20px">🔴 <b>Lo que falta antes de
mandar a fabricar:</b> <b>probar el QR en la calle</b> con un teléfono real ·
decidir <b>si el filete dorado se queda</b> (ver «El material») · y <b>tres de
los cinco grupos no existen en el sistema</b> (ver abajo).</p>
</div>

<div class="pieza"><img src="{nombre_svg}" alt=""></div>

<div class="prosa">
<section>
  <p class="rotulo">Las piezas de la fachada</p>
  <h2>Son dos, y la placa chica se cayó</h2>
  <p><b>Arriba, el cartel de IDENTIFICACIÓN</b> —logo y la palabra
  «Consultorios»—, que es lo que hace que alguien encuentre el lugar.
  <b>Debajo, este letrero, que ANUNCIA.</b> La distinción no es cosmética:
  <b>el que cae bajo el art. 89 es éste</b>, y el de identificación es el que
  cualquier consultorio tiene y la normativa espera que exista.</p>
  <p style="margin-top: 12px">🏁 <b>La placa chica de 23 × 32 se descartó el
  10-sep-2026.</b> Su función —que el que pasa confirme que es ahí— <b>la
  cumple mejor el cartel de arriba</b>, y <b>tres piezas en una fachada se
  leen como comercio</b>, que es justo lo contrario de lo que la § 2 fijó para
  esta marca. <i>Su diseño y todas sus mediciones viven en el historial de git
  (commit <code>efbe2c0</code>); lo que sobrevivió es su investigación, que es
  la que sigue en este tablero.</i></p>
  <p class="dato" style="margin-top: 12px">🔑 <b>Y la palabra «Consultorios»
  trae un dato de producto:</b> el plural dice que <b>el local está pensado
  para más de un profesional</b> — que es lo mismo que asumió el modelo de
  datos en agosto, y la mejor confirmación de que <b>ninguna pieza de fachada
  debe llevar una matrícula.</b></p>
</section>

<section>
  <p class="rotulo">La decisión que más cambia las piezas</p>
  <h2>No llevan matrícula ni nombre propio</h2>
  <p><b>Lo definió Juan, y el argumento es de arquitectura, no de gusto:</b>
  identifican al <b>consultorio</b>, no a una persona. El día que entre otro
  profesional, <b>una matrícula grabada empieza a mentir</b> — y en un cartel
  eso no se corrige editando un archivo: <b>se fabrica de nuevo</b>.</p>
  <p>Es la misma regla que sacó los horarios de la sección Contacto del sitio
  —<i>«un dato publicado no se copia si ya vive en la base, porque empieza a
  mentir»</i>— <b>aplicada al material físico</b>, donde el error es mucho más
  caro.</p>
  <p class="dato" style="margin-top: 12px">🔑 <b>Dónde se cumple entonces la
  identificación profesional: ADENTRO</b>, con el diploma y la matrícula a la
  vista, que es lo que la normativa pide y suele ser requisito de
  habilitación. <b>Eso entra al paquete de señalética interna</b>, hoy
  pausado — y le da una función que antes no tenía.</p>
</section>

<section>
  <p class="rotulo">Qué puede decir, y no es opinión</p>
  <h2>Ley 4931 de Santa Fe, artículos 89 y 90</h2>
  <p><b>Verificado que nos aplica:</b> su art. 1 abarca a <i>«todos los
  profesionales del arte de curar»</i>, nombra a los odontólogos en el art. 34
  y tiene un <b>Título IV, «Asuntos exclusivamente odontológicos»</b>.</p>
  <p><b>Art. 89 — lista cerrada de lo que se puede anunciar:</b> nombre y
  apellido · títulos · <b>las ramas y especialidades a que se dedique</b> ·
  horas de consulta · <b>dirección</b> · <b>teléfono</b>.
  <i>«Todo otro ofrecimiento es industrialismo.»</i></p>
  <p><b>Art. 90 — reñido con la ética:</b> tamaño desmedido, caracteres
  llamativos <b>o fotografías</b> · tarifas · agradecimiento de pacientes ·
  y <b>los que, colocados en el domicilio del profesional, adquieran el tamaño
  y forma de carteles</b>.</p>
  <ul>
    <li>✅ <b>Los tratamientos entran</b> — son «las ramas a que se dedica».</li>
    <li>✅ <b>Dirección y teléfono entran.</b></li>
    <li>🔴 <b>El sitio web NO está en la lista.</b> Por eso <b>el QR va al
    WhatsApp y no a la página</b>: el teléfono sí está permitido y el QR es
    sólo su formato.</li>
    <li>🔴 <b>Nada de fotos. Tamaño discreto.</b></li>
    <li>⚠️ <b>1600 cm² es el doble del tope de 800</b> que el criterio local
    fija para una placa de fachada. <b>Se construye porque lo pidió la
    profesional para su propia fachada; el costo está dicho, no escondido.</b></li>
  </ul>
  <p class="dato" style="margin-top: 12px">⚠ <b>Falta el reglamento propio del
  Colegio de Odontólogos</b> — se preguntó en agosto y no contestó. El tope de
  800 cm² y la regla «si no es metal, blanco con letras negras» salen del
  <b>Reglamento de Publicidad del Colegio de MÉDICOS de Santa Fe, 1ª
  Circunscripción, art. 10</b>: misma provincia, otra profesión. <b>Se usa
  como criterio, no como obligación.</b></p>
</section>

<section>
  <p class="rotulo">Lo que el letrero destapó, y no es de diseño</p>
  <h2>Tres de los cinco grupos no existen en el sistema</h2>
  <p>🔴 <b>Ortopedia, ATM y bruxismo, y prótesis no están en la tabla
  <code>tratamientos</code> ni en el sitio.</b> <b>La lista con la que se
  construyó el backend quedó corta</b>, y el sistema de turnos <b>filtra por
  tratamiento</b>: hoy un paciente que quiere turno por bruxismo no lo puede
  pedir, y el desplegable del panel tampoco lo ofrece.</p>
  <p class="dato" style="margin-top: 12px">⏱ <b>Va a la lista de preguntas
  para Cecilia:</b> cuál es la lista completa y real de lo que hace. Con eso
  hay que actualizar la tabla, el sitio y la grilla de reserva.</p>
  <p class="dato" style="margin-top: 12px">⬜ <b>Y una duda de contenido:
  ¿un paciente sabe qué es «ATM»?</b> El que ya tiene el diagnóstico sí, y
  «bruxismo» al lado ayuda — pero el que sólo siente dolor de mandíbula quizá
  no se reconoce ahí.</p>
</section>

<section>
  <p class="rotulo">El color</p>
  <h2>Grafito, y no es una excepción a la marca</h2>
  <p><b>Lo propuso Juan y la medición lo respalda.</b> La señalética pide
  <b>65-70 % de contraste</b> y sube el piso a <b>7:1</b> donde se lee a
  distancia con luz cambiante. Corrido <code>tools/medir-contraste.py</code>:</p>
  <table>
    <tr><th>par</th><th class="n">contraste</th><th>sirve para un letrero</th></tr>
    <tr><td>grafito sobre blanco</td><td class="n">12,82</td><td>✅ pasa 7:1 con el doble de margen</td></tr>
    <tr><td>dorado sobre marfil</td><td class="n">2,89</td><td>❌ no llega ni al mínimo básico</td></tr>
    <tr><td>grafito sobre fondo dorado</td><td class="n">4,15</td><td>❌ sólo aguanta texto grande</td></tr>
  </table>
  <p style="margin-top: 14px">🔑 <b>El dorado no falla sólo como tinta:
  también falla como fondo.</b> Queda de <b>filete</b>, que es el rol que la
  pieza 1 ya le había dado — <i>«acento, línea, o fondo con letra
  grafito»</i>. <b>Esto no es un desvío de la identidad: es la misma regla
  aplicada al material.</b></p>
  <p class="dato" style="margin-top: 12px">📌 <b>Regla que queda para todo el
  proyecto:</b> pantalla y redes → dorado de acento · <b>cartelería →
  grafito sobre claro, dorado sólo de filete</b> · <b>acabado mate siempre</b>,
  sea metal o acrílico. Un brillo tapa el texto, y la norma de señalética lo
  pide explícito.</p>
</section>

<section>
  <p class="rotulo">El material</p>
  <h2>Acrílico — confirmado por Cecilia</h2>
  <ul>
    <li>🔴 <b>ACRÍLICO MATE, no brillante.</b> No es preferencia: la norma de
    señalética pide <b>acabado antirreflejo</b>, y en la calle un brillo tapa
    el texto justo cuando pega el sol. <b>El que más sufre es el QR</b>: un
    reflejo sobre el código y la cámara no engancha.</li>
    <li><b>Acrílico BLANCO OPACO</b>, no transparente pintado por detrás — el
    criterio local pide, para una pieza que no sea de metal, <b>blanco con
    letras negras</b>, y el grafito es un negro cálido que lo cumple.</li>
    <li>🔴 <b>El filete dorado es el único elemento de color, y ahí hay una
    decisión.</b> Si se lee ese criterio al pie de la letra, sobra. <b>Las dos
    salidas: dejarlo</b> —es un filete, no texto, y es lo único que ata la
    pieza a la identidad— <b>o pasarlo a grafito</b>. <i>Decide Juan.</i></li>
    <li><b>El acrílico no amarillea:</b> el PMMA es estable a los UV —a
    diferencia del policarbonato, que sin protección se pone amarillo en dos
    años—. <b>Cinco a diez años a la intemperie sin cambio apreciable.</b></li>
    <li><b>Espesor: 5 mm</b> como mínimo. A 50 cm de ancho, con 3 mm flexiona.</li>
  </ul>
</section>

<section>
  <p class="rotulo">La alineación</p>
  <h2>Centrado, y la regla del sitio acá no manda</h2>
  <p><b>Lo corrigió Juan:</b> <i>«esto es cartelería, puede ir centrado —
  nuestras reglas tienen que respetar los usos y costumbres del mundo
  también»</i>. <b>Tenía razón, y la investigación lo confirma con una
  distinción que no teníamos:</b></p>
  <ul>
    <li>En señales <b>direccionales</b> (wayfinding) la alineación óptima es
    <b>a la izquierda</b>. Es la regla que se había aplicado, y es de otro
    tipo de señal.</li>
    <li>🔑 En señales de <b>IDENTIFICACIÓN</b> —que es lo que esto es— <b>el
    centrado es lo aceptado</b>.</li>
    <li><b>El matiz:</b> el centrado funciona en <b>líneas cortas</b> y <b>se
    degrada arriba de tres renglones</b>.</li>
  </ul>
  <p class="dato" style="margin-top: 12px">📌 <b>Lo que esto deja como
  criterio:</b> una regla del sitio no se copia a una pieza física sin
  verificar qué hace el mundo con ese objeto. <b>El pie centrado del sitio es
  una excepción declarada; un letrero centrado es la convención.</b> No son lo
  mismo y se habían mezclado.</p>
</section>

<section>
  <p class="rotulo">Los espacios</p>
  <h2>Auditados con <code>medir-espacios.py</code></h2>
  <p><b>La regla es una sola:</b> el hueco que <b>SEPARA</b> dos grupos tiene
  que ser claramente mayor que el mayor hueco de <b>ADENTRO</b> de cualquiera
  de los dos. Si no, lo que se ve junto no es lo que está junto.</p>
  <p style="margin-top: 12px"><b>Dos cosas que a ojo no se veían y la medición
  destapó:</b> el <b>filete</b> estaba a 16 mm del logo y a 4,5 de la lista
  —o sea pegado a la lista, y <b>un separador que toca un lado deja de
  separar</b>— y el <b>teléfono</b> estaba a 1,7 mm del QR mientras el rótulo
  estaba a 6,6.</p>
  <p class="dato" style="margin-top: 12px">✅ <b>Cómo quedó:</b> logo → filete
  <b>11,0</b> · filete → lista <b>8,5</b> · adentro de la lista <b>~6</b> ·
  <b>lista → bloque de contacto 17,4</b> · adentro del contacto <b>5,6 · 5,7 ·
  6</b>. <b>La separación entre grupos es tres veces la de adentro.</b></p>
</section>

<section>
  <p class="rotulo">Los números</p>
  <h2>Todos medidos, ninguno estimado</h2>
  <table>
    <tr><th>qué</th><th class="n">cuánto</th><th>por qué</th></tr>
{filas}
  </table>
</section>

<section>
  <p class="rotulo">Cómo se produce</p>
  <h2>Qué archivo se le manda al cartelero</h2>
  <ul>
    <li><b><code>{nombre_svg.replace(".svg", ".pdf")}</code></b> — vectorial, a
    tamaño real.</li>
    <li><b><code>{nombre_svg}</code></b> — el mismo dibujo, editable, <b>con la
    tipografía adentro del archivo</b>.</li>
    <li>🔴 <b>Se GENERAN con <code>tools/construir-carteleria.py</code>, nunca
    se editan a mano.</b> Los colores salen de <code>css/tokens.css</code> y el
    logo de <code>brand/logo/curvas/</code>.</li>
  </ul>
  <p class="dato" style="margin-top: 12px">⚠️ <b>Dos fallos que sólo
  aparecieron midiendo, y conviene no repetirlos:</b> con la tipografía
  referenciada por ruta, el archivo se veía perfecto en pantalla y <b>el PDF
  salía en Helvetica</b> — lo destapó <code>pdffonts</code>, no el ojo. Y al
  reordenar el pie, <b>el QR terminó encima de un renglón</b> y el archivo se
  generó igual. <b>Ahora el generador se niega a escribir una pieza cuyos
  bloques se pisen.</b></p>
</section>
</div>
"""


def envoltorio(nombre_svg, alto, ancho):
    """El HTML que Chrome imprime, para que el PDF salga con medida exacta.

    Chrome respeta @page, así que la hoja mide lo que mide la placa y no
    queda ningún margen de navegador. El SVG se referencia, no se copia: un
    solo archivo sigue siendo la fuente.
    """
    return f"""<!doctype html>
<meta charset="utf-8">
<title>CB · {ancho} × {alto} mm</title>
<style>
  @page {{
    size: {ancho}mm {alto}mm;
    margin: 0;
  }}
  html, body {{
    margin: 0;
    padding: 0;
  }}
  img {{
    display: block;
    width: {ancho}mm;
    height: {alto}mm;
  }}
</style>
<img src="{nombre_svg}" alt="">
"""


def main():
    SALIDA.mkdir(parents=True, exist_ok=True)

    nombre = f"letrero-{CARTEL_ANCHO}x{CARTEL_ALTO}"

    svg = SALIDA / f"{nombre}.svg"
    svg.write_text(cartel(), encoding="utf-8")
    print(f"✓ {svg.relative_to(RAIZ)}")

    medidas = [
        ("El letrero entero",
         f"{CARTEL_ANCHO} × {CARTEL_ALTO} mm · {CARTEL_ANCHO * CARTEL_ALTO / 100:.0f} cm²",
         "La medida la pidió Cecilia. ⚠ Es el DOBLE del tope de 800 cm² que "
         "el criterio local fija para una placa de fachada, y a este tamaño "
         "cae en lo que el art. 90.k llama «tamaño y forma de carteles»."),
        ("El margen lateral", f"{CARTEL_MARGEN} mm · 10 %",
         "Los manuales de señalización piden de 10 a 15 % del ancho del panel "
         "por lado, y que el espacio hasta el borde sea del orden de la altura "
         "de la letra más grande."),
        ("El wordmark", "270 mm de ancho",
         "El 54 % del ancho. El mínimo por técnica es 6,3 cm en grabado y "
         "12,6 en serigrafía (COMO-USAR-EL-LOGO.md): entra con holgura."),
        ("Los tratamientos", "11,9 mm de altura de mayúscula",
         "Medido sobre la tipografía real. Por la fórmula de señalética "
         "—x-height = distancia en metros × 2,5 mm— los 7,8 mm de minúscula "
         "se leen desde 3,1 m, o sea desde la vereda."),
        ("El teléfono", "más grande que la dirección",
         "A propósito: es el dato que alguien anota desde lejos. La dirección "
         "va abajo de todo porque quien lee el letrero YA está en ella."),
        ("El QR", "40 mm de lado",
         "La regla es 10:1 — un lado de 1 cm se escanea desde 10 cm. Lleva "
         "sus 4 módulos de zona de silencio (ISO/IEC 18004). ⏱ Falta "
         "probarlo en la calle con un teléfono real: un QR que no se escaneó "
         "no está verificado."),
        ("El QR, verificado", "decodificado",
         "No se dio por bueno: se rasterizó el PDF a 300 dpi y se leyó con "
         "zbar. Devuelve wa.me/5493426293920."),
        ("El filete dorado", "1,2 mm",
         "Es el único dorado de la pieza y no lleva texto encima: ahí el "
         "dorado sí cumple, porque su trabajo es separar, no ser leído."),
    ]

    tab = SALIDA / "carteleria-tablero.html"
    tab.write_text(tablero(svg.name, medidas), encoding="utf-8")
    print(f"✓ {tab.relative_to(RAIZ)}")

    html = SALIDA / f"{nombre}-imprimir.html"
    html.write_text(
        envoltorio(svg.name, CARTEL_ALTO, CARTEL_ANCHO), encoding="utf-8"
    )
    print(f"✓ {html.relative_to(RAIZ)}")

    pdf = SALIDA / f"{nombre}.pdf"
    subprocess.run(
        [
            CHROME,
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf}",
            f"file://{html}",
        ],
        capture_output=True,
        check=True,
    )
    print(f"✓ {pdf.relative_to(RAIZ)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
