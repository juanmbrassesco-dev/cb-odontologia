"""Deja el lienzo de un SVG del tamaño EXACTO de su dibujo, midiéndolo.

    python3 recortar_lienzo.py <entrada.svg> <salida.svg>

POR QUÉ HACE FALTA, y por qué no lo hace `svg_a_curvas.py`. Aquel recorta
mientras convierte texto a contornos: sabe hasta dónde llega cada letra porque
la dibujó él. Y si encuentra un `<path>` ya escrito **se niega a recortar**, con
razón: calcular a mano hasta dónde llega un arco es otro problema y equivocarse
corta el dibujo.

Pero las piezas de `tools/letras-cb` salen del generador YA en `<path>`. Nunca
fueron `<text>`, así que aquel camino no les sirve.

LA SALIDA: en vez de calcular los arcos, **se los mide**. Se rasteriza el SVG a
muy alta resolución, se busca el primer y el último píxel con tinta en cada eje,
y esas cuatro coordenadas se vuelven el `viewBox`. A 8000 píxeles de ancho, un
píxel de error es el 0,0125 % del dibujo — sobre el wordmark, 0,008 mm. El
`svg_a_pdf.py` acepta hasta 0,05.

POR QUÉ IMPORTA que el lienzo sea el dibujo: un programa de diagramación escala
un PDF por su PÁGINA, así que cualquier aire invisible adentro del archivo se
convierte en un error de tamaño — se pide 50 mm y sale 49,8. Acá no queda aire
que se pueda convertir en nada.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert( 0, str( Path( __file__ ).resolve().parent.parent / "brand-audit" ) )
from leer_png import leer_png


ANCHO_DE_MEDIDA = 8000


def caja_de_tinta( svg ):
    """Las cuatro coordenadas del dibujo, en unidades del `viewBox`."""
    with tempfile.TemporaryDirectory() as tmp:
        png = Path( tmp ) / "medida.png"

        subprocess.run(
            [ "rsvg-convert", "-w", str( ANCHO_DE_MEDIDA ), str( svg ), "-o", str( png ) ],
            check = True,
            capture_output = True,
        )

        ancho, alto, canales, filas = leer_png( png )

    # El render sale con transparencia, así que la tinta es todo lo que NO es
    # transparente. Se toma cualquier resto de alfa, no un umbral: el borde
    # difuminado de una curva es parte del dibujo y recortarlo lo corta.
    if canales < 4:
        raise SystemExit( "el render no trajo transparencia y no puedo separar la tinta" )

    def hay_tinta( x, y ):
        return filas[ y ][ x * canales + 3 ] > 0

    columnas = [ x for x in range( ancho ) if any( hay_tinta( x, y ) for y in range( alto ) ) ]
    renglones = [ y for y in range( alto ) if any( hay_tinta( x, y ) for x in range( ancho ) ) ]

    if not columnas:
        raise SystemExit( "el SVG no tiene tinta que medir" )

    return columnas[ 0 ], renglones[ 0 ], columnas[ -1 ] + 1, renglones[ -1 ] + 1, ancho, alto


def recortar( entrada, salida ):
    svg = Path( entrada ).read_text()

    caja = re.search( r'viewBox="([\d.\- ]+)"', svg )

    if not caja:
        raise SystemExit( "el SVG no declara viewBox y no sé en qué unidades está" )

    vx, vy, vw, vh = [ float( n ) for n in caja.group( 1 ).split() ]

    x0, y0, x1, y1, ancho_px, alto_px = caja_de_tinta( entrada )

    # de píxeles del render de vuelta a unidades del dibujo
    por_pixel_x = vw / ancho_px
    por_pixel_y = vh / alto_px

    nx = vx + x0 * por_pixel_x
    ny = vy + y0 * por_pixel_y
    nw = ( x1 - x0 ) * por_pixel_x
    nh = ( y1 - y0 ) * por_pixel_y

    svg = svg.replace(
        caja.group( 0 ),
        f'viewBox="{nx:.4f} {ny:.4f} {nw:.4f} {nh:.4f}"',
    )

    Path( salida ).write_text( svg )
    print( f"{Path( salida ).name}   {nw:.4f} × {nh:.4f}" )


if __name__ == "__main__":
    argumentos = [ a for a in sys.argv[ 1: ] if not a.startswith( "--" ) ]

    if len( argumentos ) != 2:
        raise SystemExit( __doc__ )

    recortar( argumentos[ 0 ], argumentos[ 1 ] )
