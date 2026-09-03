"""Centra un dibujo en un lienzo CUADRADO, con aire para un recorte REDONDO.

    python3 lienzo_cuadrado.py <entrada.svg> <salida.svg> [--aire 0.215]

POR QUÉ EXISTE, y es el hermano al revés de `recortar_lienzo.py`. Aquel le saca
al lienzo todo el aire hasta dejarlo del tamaño del dibujo, que es lo que pide
una imprenta. Éste hace lo contrario, y para el caso contrario: **una foto de
perfil**.

🔴 UNA FOTO DE PERFIL NO ES UN RECTÁNGULO: WhatsApp e Instagram la muestran
RECORTADA EN CÍRCULO. El archivo que se sube es cuadrado, pero todo lo que
quede fuera del círculo inscripto no lo ve nadie. Un dibujo ancho —el apilado
mide 1,9 a 1— metido en un cuadrado sin pensar pierde las puntas.

CUÁNTO AIRE, y por qué no se elige a ojo. El manual de marca ya fija la regla:
alrededor del logo tiene que quedar libre **por lo menos el alto de la letra
"C"**, y ahí no entra nada — tampoco el borde de la placa. Acá la placa es el
círculo, así que la regla se aplica contra la circunferencia.

⚠ **Y el punto del dibujo que primero se acerca al borde redondo NO es su
costado: es una ESQUINA de su caja.** Por eso la cuenta arranca en la media
diagonal y no en la mitad del ancho — usar el ancho dejaría las esquinas
comidas y el error solo se vería en el archivo final.

`--aire` se pide como FRACCIÓN DEL ANCHO de la pieza, que es como el generador
guarda esa medida: en `tools/letras-cb/piezas.py` el alto de las iniciales del
apilado es `cb = 0.215` del ancho. Si algún día cambia allá, cambia el número
que se pasa acá — no hay una copia escondida.

LA SALIDA sale TRANSPARENTE, igual que la entrada. El marfil de las fotos de
perfil lo pone `svg_a_png.py --fondo`, que ya existe para eso: un solo lugar
decide el color del fondo.
"""

import re
import sys
from pathlib import Path


# el alto de la "C" del apilado, como fracción de su ancho — sale de `piezas.py`
AIRE_POR_DEFECTO = 0.215


def cuadrar( entrada, salida, aire = AIRE_POR_DEFECTO ):
    svg = Path( entrada ).read_text()

    caja = re.search( r'viewBox="([\d.\- ]+)"', svg )

    if not caja:
        raise SystemExit( "el SVG no declara viewBox y no sé en qué unidades está" )

    vx, vy, ancho, alto = [ float( n ) for n in caja.group( 1 ).split() ]

    # La esquina de la caja es lo que primero toca el círculo, así que lo que
    # tiene que entrar es la MEDIA DIAGONAL. Sumarle el aire da el radio, y el
    # doble del radio es el lado del cuadrado.
    media_diagonal = ( ancho ** 2 + alto ** 2 ) ** 0.5 / 2
    radio = media_diagonal + aire * ancho
    lado = radio * 2

    # el dibujo, centrado: se corre a la mitad del sobrante de cada eje, y se le
    # descuenta de dónde arrancaba su propio viewBox
    izquierda = ( lado - ancho ) / 2 - vx
    arriba = ( lado - alto ) / 2 - vy

    abre = re.search( r"<svg[^>]*>", svg ).group( 0 )

    svg = svg.replace(
        abre,
        abre.replace( caja.group( 0 ), f'viewBox="0 0 {lado:.4f} {lado:.4f}"' )
        + f'<g transform="translate({izquierda:.4f},{arriba:.4f})">',
        1,
    )

    svg = svg.replace( "</svg>", "</g></svg>" )

    Path( salida ).write_text( svg )
    print(
        f"{Path( salida ).name}   {lado:.4f} × {lado:.4f}   "
        f"el dibujo se lleva el {ancho / lado * 100:.1f} % del lado"
    )


if __name__ == "__main__":
    argumentos = [ a for a in sys.argv[ 1: ] if not a.startswith( "--" ) ]
    argumentos = [ a for a in argumentos if not a.replace( ".", "" ).isdigit() ]

    if len( argumentos ) != 2:
        raise SystemExit( __doc__ )

    pedido = AIRE_POR_DEFECTO

    for i, a in enumerate( sys.argv ):
        if a == "--aire":
            pedido = float( sys.argv[ i + 1 ] )

    cuadrar( argumentos[ 0 ], argumentos[ 1 ], pedido )
