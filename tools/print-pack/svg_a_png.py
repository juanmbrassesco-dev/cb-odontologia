"""Genera el PNG de alta resolución de un SVG, con su tamaño físico adentro.

Un PNG es una grilla de píxeles y nada más: por sí solo NO sabe de qué tamaño
tiene que imprimirse. Lo que lo dice es un dato aparte —los `pHYs`— que declara
cuántos píxeles entran en un metro. Sin ese dato, el que lo reciba tiene que
adivinar la escala, y adivinar es exactamente lo que este pack existe para
evitar.

⚠ UN PNG NO PUEDE TENER EL TAMAÑO EXACTO, Y NO ES UN DESCUIDO: es el formato.
300 puntos por pulgada sobre un dibujo de 50,271 mm dan 593,75 píxeles, y un
píxel no se parte. Se redondea, y el tamaño impreso queda hasta medio píxel
—0,04 mm— del tamaño del PDF. **Los píxeles se dejan CUADRADOS y la resolución
declarada es 300 justos**, que es lo que espera cualquier programa; la
alternativa —estirar la resolución de un eje para que la cuenta cierre— da un
tamaño exacto pero píxeles rectangulares, y eso confunde a la mitad de los
programas de maquetación.

🔑 **Por eso el PNG NO es el archivo de imprenta: el exacto es el PDF.** Este
sirve para lo que un vector no entra —una plantilla de redes, un documento de
oficina, una vista rápida— y ahí 0,04 mm no existen.

    python3 svg_a_png.py <entrada.svg> <salida.png> [--ancho 1200] [--fondo]

⚠ CON `--ancho` SE PIDE EL TAMAÑO EN PÍXELES, y es la forma NORMAL de pedirlo.
Un PNG se usa en pantalla, y en pantalla no existen los milímetros: existe el
alto del avatar de Instagram y el ancho del logo en el encabezado del sitio.
Los dpi son para el papel, y para el papel está el PDF.

Sin `--fondo` sale con fondo TRANSPARENTE, que es como se entrega un logo: el
fondo lo pone el soporte.
"""

import struct
import subprocess
import sys
import zlib
from pathlib import Path

from svg_a_pdf import POR_PULGADA, medidas

RSVG = "/opt/homebrew/bin/rsvg-convert"
DPI = 300
MARFIL = "#FAF7F2"
MM_POR_PULGADA = 25.4


def escribir_phys(ruta, ppp_x, ppp_y):
    """Le mete al PNG el dato del tamaño físico.

    El `pHYs` guarda PÍXELES POR METRO y en números enteros, así que se
    redondea: sobre un metro, un entero de más o de menos no mueve nada.
    Va antes de los datos de la imagen, que es donde el formato lo espera."""
    crudo = Path(ruta).read_bytes()
    por_metro_x = round(ppp_x / MM_POR_PULGADA * 1000)
    por_metro_y = round(ppp_y / MM_POR_PULGADA * 1000)

    cuerpo = struct.pack(">IIB", por_metro_x, por_metro_y, 1)   # 1 = el metro es la unidad
    trozo = (
        struct.pack(">I", len(cuerpo))
        + b"pHYs"
        + cuerpo
        + struct.pack(">I", zlib.crc32(b"pHYs" + cuerpo))
    )

    # el IHDR son 25 bytes justos después de la firma de 8
    corte = 8 + 25
    sin_viejo = crudo[:corte] + crudo[corte:].replace(b"", b"", 1)

    # si ya venía uno, se saca para no dejar dos datos que se contradigan
    if b"pHYs" in crudo:
        inicio = crudo.index(b"pHYs") - 4
        sin_viejo = crudo[:inicio] + crudo[inicio + 21 :]
    else:
        sin_viejo = crudo

    Path(ruta).write_bytes(sin_viejo[:corte] + trozo + sin_viejo[corte:])


def medidas_del_png(ruta):
    crudo = Path(ruta).read_bytes()
    ancho, alto = struct.unpack(">II", crudo[16:24])

    if b"pHYs" not in crudo:
        return ancho, alto, None, None

    i = crudo.index(b"pHYs") + 4
    por_metro_x, por_metro_y, _ = struct.unpack(">IIB", crudo[i : i + 9])
    return (
        ancho,
        alto,
        por_metro_x * MM_POR_PULGADA / 1000,
        por_metro_y * MM_POR_PULGADA / 1000,
    )


def a_png(entrada, salida, fondo=None, ancho_pedido=None):
    svg = Path(entrada).read_text()

    if "<text" in svg:
        raise SystemExit("este SVG todavía tiene texto: pasalo por svg_a_curvas.py primero.")

    ancho, alto = medidas(svg)
    pulgadas_x = ancho / POR_PULGADA
    pulgadas_y = alto / POR_PULGADA

    if ancho_pedido:
        # manda el ancho en píxeles; el alto sale de la proporción del dibujo
        pixeles_x = int(ancho_pedido)
        pixeles_y = round(pixeles_x * alto / ancho)
    else:
        # píxeles CUADRADOS a 300 dpi justos: se redondea al entero más cercano
        pixeles_x = round(pulgadas_x * DPI)
        pixeles_y = round(pulgadas_y * DPI)

    orden = [
        RSVG,
        "--format=png",
        f"--width={pixeles_x}",
        f"--height={pixeles_y}",
        "--output", str(Path(salida).resolve()),
    ]

    if fondo:
        orden.insert(1, f"--background-color={fondo}")

    subprocess.run(orden + [str(Path(entrada).resolve())], check=True, capture_output=True)

    escribir_phys(salida, pixeles_x / pulgadas_x, pixeles_y / pulgadas_y)

    px, py, dpi_x, dpi_y = medidas_del_png(salida)
    mm_x = px / dpi_x * MM_POR_PULGADA
    mm_y = py / dpi_y * MM_POR_PULGADA

    print(
        f"{entrada} → {salida}\n"
        f"    {px} x {py} px  ·  {dpi_x:.2f} x {dpi_y:.2f} dpi  ·  "
        f"{mm_x:.3f} x {mm_y:.3f} mm  ·  fondo {fondo or 'transparente'}"
    )

    desvio = max(abs(mm_x - ancho / POR_PULGADA * MM_POR_PULGADA),
                 abs(mm_y - alto / POR_PULGADA * MM_POR_PULGADA))

    if desvio > max(0.05, 25.4 / dpi_x):
        raise SystemExit(f"el tamaño declarado se fue más de un píxel del dibujo ({desvio:.4f} mm)")


if __name__ == "__main__":
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]
    argumentos = [a for a in argumentos if not a.isdigit()]

    if len(argumentos) != 2:
        raise SystemExit(__doc__)

    pedido = None
    for i, a in enumerate(sys.argv):
        if a == "--ancho":
            pedido = int(sys.argv[i + 1])

    a_png(
        argumentos[0],
        argumentos[1],
        MARFIL if "--fondo" in sys.argv else None,
        pedido,
    )
