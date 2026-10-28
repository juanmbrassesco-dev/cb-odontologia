"""
EL BRIEF DEL FOTÓGRAFO, EN PDF — para mandarlo por WhatsApp o imprimirlo.

PARA QUÉ EXISTE. El brief vive en `brand/BRIEF-PARA-EL-FOTOGRAFO.md`, que se
lee bien en GitHub pero no se manda: un fotógrafo recibe un archivo, no un
enlace a un repositorio.

🔑 LEE EL MARKDOWN, NO LO COPIA. Es la regla que este proyecto ya pagó varias
veces: un archivo que repite el contenido de otro se desincroniza, y nadie se
entera hasta que alguien manda la versión vieja. El texto vive en UN lugar.

⚠ EL RENDERIZADOR ES MÍNIMO A PROPÓSITO. Cubre exactamente lo que ese brief
usa —títulos, tablas, listas, citas, negrita, itálica, código y líneas— y nada
más. No es una biblioteca de markdown y no pretende serlo: si el brief crece
con algo nuevo, se agrega acá, a la vista.

CÓMO SE CORRE, parado en la raíz del repo:

    python3 tools/construir-brief-pdf.py
"""

import html
import re
import subprocess
from pathlib import Path


RAIZ = Path( __file__ ).resolve().parent.parent

ENTRADA = RAIZ / 'brand' / 'BRIEF-PARA-EL-FOTOGRAFO.md'
SALIDA = RAIZ / 'brand' / 'brief-fotografo'

CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

MARFIL = '#FAF7F2'
GRAFITO = '#33322F'
DORADO = '#B08D57'
DORADO_TEXTO = '#896D41'
GRIS = '#5A5853'
BLANCO = '#FFFFFF'

FUENTES = RAIZ / 'brand' / 'fonts'
LOGO = RAIZ / 'brand' / 'logo' / 'png' / 'cb-apilado-1200.png'


# ── De markdown a HTML, sólo lo que el brief usa ─────────────────────────────

def en_linea( texto ):
    """Negrita, itálica y código. El orden importa: el código se protege
    primero, y la negrita va antes que la itálica porque `**` contiene `*`."""

    texto = html.escape( texto )

    texto = re.sub( r'`([^`]+)`', r'<code>\1</code>', texto )
    texto = re.sub( r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', texto )
    texto = re.sub( r'\*([^*]+)\*', r'<em>\1</em>', texto )

    return texto


def fila_de_tabla( linea ):

    celdas = [ c.strip() for c in linea.strip().strip( '|' ).split( '|' ) ]

    return celdas


def es_separador_de_tabla( linea ):

    return bool( re.fullmatch( r'\|[\s:|-]+\|', linea.strip() ) )


def a_html( markdown ):

    salida = []

    # Estado: qué lista o tabla está abierta en este momento.
    lista_abierta = None
    tabla_abierta = False
    cita_abierta = False
    parrafo = []

    # El ítem de lista que se está juntando, con sus renglones de
    # continuación. Se emite recién cuando se sabe que terminó.
    item = { 'partes': [], 'clase': '' }

    def cerrar_item():

        if item[ 'partes' ]:
            texto = ' '.join( item[ 'partes' ] )
            salida.append( f'<li{ item[ "clase" ] }>{ en_linea( texto ) }</li>' )
            item[ 'partes' ] = []
            item[ 'clase' ] = ''

    def cerrar_parrafo():

        if parrafo:
            salida.append( f'<p>{ en_linea( " ".join( parrafo ) ) }</p>' )
            parrafo.clear()

    def cerrar_todo():

        nonlocal lista_abierta, tabla_abierta, cita_abierta

        cerrar_item()
        cerrar_parrafo()

        if lista_abierta:
            salida.append( f'</{ lista_abierta }>' )
            lista_abierta = None

        if tabla_abierta:
            salida.append( '</tbody></table>' )
            tabla_abierta = False

        if cita_abierta:
            salida.append( '</blockquote>' )
            cita_abierta = False

    for cruda in markdown.split( '\n' ):

        linea = cruda.rstrip()

        # Renglón vacío: cierra el párrafo, pero NO la lista — una lista con
        # un renglón en blanco en el medio sigue siendo la misma lista.
        if not linea.strip():
            cerrar_parrafo()
            continue

        # Línea horizontal.
        if linea.strip() == '---':
            cerrar_todo()
            salida.append( '<hr>' )
            continue

        # Títulos.
        titulo = re.match( r'^(#{1,4})\s+(.*)$', linea )

        if titulo:
            cerrar_todo()
            nivel = len( titulo.group( 1 ) )
            salida.append( f'<h{ nivel }>{ en_linea( titulo.group( 2 ) ) }</h{ nivel }>' )
            continue

        # Tablas.
        if linea.strip().startswith( '|' ):

            if es_separador_de_tabla( linea ):
                continue

            if not tabla_abierta:
                cerrar_parrafo()
                salida.append( '<table><thead><tr>' )
                for celda in fila_de_tabla( linea ):
                    salida.append( f'<th>{ en_linea( celda ) }</th>' )
                salida.append( '</tr></thead><tbody>' )
                tabla_abierta = True
                continue

            salida.append( '<tr>' )
            for celda in fila_de_tabla( linea ):
                salida.append( f'<td>{ en_linea( celda ) }</td>' )
            salida.append( '</tr>' )
            continue

        if tabla_abierta:
            salida.append( '</tbody></table>' )
            tabla_abierta = False

        # Citas.
        if linea.startswith( '>' ):

            if not cita_abierta:
                cerrar_parrafo()
                salida.append( '<blockquote>' )
                cita_abierta = True

            salida.append( f'<p>{ en_linea( linea.lstrip( ">" ).strip() ) }</p>' )
            continue

        if cita_abierta:
            salida.append( '</blockquote>' )
            cita_abierta = False

        # Listas. La sangría de dos espacios marca el segundo nivel, y acá se
        # aplana a propósito: en un brief de una carilla, un sub-nivel que se
        # ve como tal cuesta más de lo que aclara.
        punto = re.match( r'^(\s*)[-*]\s+(.*)$', linea )
        numerado = re.match( r'^(\s*)\d+\.\s+(.*)$', linea )

        if punto or numerado:

            cerrar_item()

            cual = punto if punto else numerado
            etiqueta = 'ul' if punto else 'ol'
            sangria = len( cual.group( 1 ) )

            if lista_abierta != etiqueta:
                cerrar_parrafo()
                if lista_abierta:
                    salida.append( f'</{ lista_abierta }>' )
                salida.append( f'<{ etiqueta }>' )
                lista_abierta = etiqueta

            item[ 'clase' ] = ' class="hijo"' if sangria >= 2 else ''
            item[ 'partes' ] = [ cual.group( 2 ) ]
            continue

        # 🔴 UN RENGLÓN SANGRADO QUE NO ES LISTA CONTINÚA EL ÍTEM ANTERIOR, Y
        # SE ACUMULA EN VEZ DE EMITIRSE. Si se emitiera suelto, una negrita o
        # una itálica que arranca en un renglón y cierra en el siguiente
        # quedaría partida en dos y los asteriscos saldrían impresos. Pasó.
        if item[ 'partes' ] and cruda.startswith( '  ' ):
            item[ 'partes' ].append( linea.strip() )
            continue

        cerrar_item()

        if lista_abierta:
            salida.append( f'</{ lista_abierta }>' )
            lista_abierta = None

        parrafo.append( linea.strip() )

    cerrar_todo()

    return '\n'.join( salida )


# ── La página ────────────────────────────────────────────────────────────────

def pagina( cuerpo ):

    return f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Brief de fotos — CB Odontología y Estética</title>
<style>
  @font-face {{
    font-family: Marcellus;
    src: url("file://{ FUENTES / 'Marcellus-Regular.ttf' }") format("truetype");
  }}

  @font-face {{
    font-family: Jost;
    src: url("file://{ FUENTES / 'Jost-var.ttf' }") format("truetype");
  }}

  @page {{
    size: A4;
    margin: 16mm 15mm 18mm;
  }}

  * {{
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}

  body {{
    margin: 0;
    background: { MARFIL };
    color: { GRAFITO };
    font-family: Jost, "Helvetica Neue", Arial, sans-serif;
    font-size: 10.5pt;
    line-height: 1.55;
  }}

  .tapa {{
    display: flex;
    align-items: center;
    gap: 18px;
    padding-bottom: 14px;
    margin-bottom: 10px;
    border-bottom: 2px solid { DORADO };
  }}

  .tapa img {{
    width: 86px;
    height: auto;
  }}

  .tapa .que {{
    font-size: 9pt;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: { DORADO_TEXTO };
  }}

  h1 {{
    font-family: Marcellus, Georgia, serif;
    font-size: 21pt;
    line-height: 1.2;
    margin: 0;
  }}

  h2 {{
    font-family: Marcellus, Georgia, serif;
    font-size: 15pt;
    margin: 26px 0 8px;
    padding-top: 10px;
    border-top: 1px solid { DORADO };
    break-after: avoid;
  }}

  h3 {{
    font-family: Marcellus, Georgia, serif;
    font-size: 12.5pt;
    margin: 20px 0 6px;
    color: { DORADO_TEXTO };
    break-after: avoid;
  }}

  p {{
    margin: 0 0 8px;
  }}

  strong {{
    font-weight: 600;
  }}

  em {{
    color: { GRIS };
  }}

  code {{
    font-family: ui-monospace, "SF Mono", Menlo, monospace;
    font-size: 9.5pt;
    background: { BLANCO };
    padding: 1px 4px;
    border-radius: 3px;
  }}

  ul, ol {{
    margin: 0 0 10px;
    padding-left: 18px;
  }}

  li {{
    margin-bottom: 5px;
    break-inside: avoid;
  }}

  li.hijo {{
    margin-left: 16px;
    list-style-type: circle;
  }}

  p.suelto {{
    margin: 4px 0 8px 18px;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0 14px;
    font-size: 9.5pt;
    break-inside: avoid;
  }}

  th {{
    text-align: left;
    padding: 7px 9px;
    background: { GRAFITO };
    color: { MARFIL };
    font-weight: 500;
  }}

  td {{
    padding: 7px 9px;
    border-bottom: 1px solid #E3DED4;
    vertical-align: top;
  }}

  tbody tr:nth-child(odd) td {{
    background: { BLANCO };
  }}

  blockquote {{
    margin: 10px 0 14px;
    padding: 10px 14px;
    background: { BLANCO };
    border-left: 3px solid { DORADO };
  }}

  blockquote p:last-child {{
    margin-bottom: 0;
  }}

  hr {{
    border: 0;
    height: 0;
    margin: 0;
  }}

  h2, h3, table, blockquote {{
    break-inside: avoid;
  }}
</style>
</head>
<body>

<div class="tapa">
  <img src="file://{ LOGO }" alt="CB Odontología y Estética">
  <div>
    <div class="que">Brief de fotos · para el fotógrafo</div>
    <h1>CB Odontología y Estética</h1>
  </div>
</div>

{ cuerpo }

</body>
</html>'''


def main():

    SALIDA.mkdir( parents = True, exist_ok = True )

    markdown = ENTRADA.read_text( encoding = 'utf-8' )

    # El `# título` del markdown ya lo dibuja la tapa: se saca para que no
    # aparezca dos veces.
    markdown = re.sub( r'^# .*\n', '', markdown, count = 1 )

    archivo_html = SALIDA / 'brief.html'
    archivo_pdf = SALIDA / 'brief-fotos-cb-odontologia.pdf'

    archivo_html.write_text( pagina( a_html( markdown ) ), encoding = 'utf-8' )
    print( f'✓ { archivo_html.relative_to( RAIZ ) }' )

    subprocess.run(
        [
            CHROME,
            '--headless',
            '--disable-gpu',
            '--no-pdf-header-footer',
            f'--print-to-pdf={ archivo_pdf }',
            f'file://{ archivo_html }',
        ],
        capture_output = True,
        check = True,
    )

    print( f'✓ { archivo_pdf.relative_to( RAIZ ) }' )


main()
