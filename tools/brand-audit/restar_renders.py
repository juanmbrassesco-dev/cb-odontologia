"""Resta dos renders del mismo dibujo y dice en qué se diferencian.

Es el instrumento más honesto que apareció midiendo el logo: no depende de
elegir bien QUÉ medir. Se ponen los dos al mismo tamaño, se restan, y lo que
queda encendido es exactamente lo que no coincide.

    python3 restar_renders.py <a.png> <b.png> [salida.png]

En la imagen de salida, NEGRO = coinciden.
"""

import struct
import sys
import zlib

from leer_png import leer_png


def escribir_png(ruta, ancho, alto, filas_rgb):
    crudo = b"".join(b"\x00" + bytes(f) for f in filas_rgb)

    def trozo(tipo, cuerpo):
        return (
            struct.pack(">I", len(cuerpo))
            + tipo
            + cuerpo
            + struct.pack(">I", zlib.crc32(tipo + cuerpo))
        )

    open(ruta, "wb").write(
        b"\x89PNG\r\n\x1a\n"
        + trozo(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0))
        + trozo(b"IDAT", zlib.compress(crudo, 6))
        + trozo(b"IEND", b"")
    )


def restar(ruta_a, ruta_b, ruta_salida=None):
    ancho, alto, can_a, filas_a = leer_png(ruta_a)
    ancho_b, alto_b, can_b, filas_b = leer_png(ruta_b)

    if (ancho, alto) != (ancho_b, alto_b):
        raise SystemExit(
            f"los dos renders tienen que medir lo mismo: {ancho}x{alto} contra {ancho_b}x{alto_b}"
        )

    peor = 0
    distintos = 0
    salida = []

    for y in range(alto):
        fa = filas_a[y]
        fb = filas_b[y]
        linea = bytearray(ancho * 3)

        if fa != fb:
            for x in range(ancho):
                ia = x * can_a
                ib = x * can_b
                d = max(abs(fa[ia + c] - fb[ib + c]) for c in range(3))

                if d:
                    distintos += 1
                    peor = max(peor, d)
                    # se multiplica por 4 para que una diferencia chica se vea
                    linea[x * 3] = linea[x * 3 + 1] = linea[x * 3 + 2] = min(255, d * 4)

        salida.append(linea)

    if ruta_salida:
        escribir_png(ruta_salida, ancho, alto, salida)

    total = ancho * alto
    print(f"lienzo                  : {ancho} x {alto} px ({total:,} px)")
    print(f"pixeles distintos       : {distintos:,} ({distintos / total * 100:.3f} %)")
    print(f"peor diferencia de canal: {peor} sobre 255")

    if ruta_salida:
        print(f"resta escrita en        : {ruta_salida}   (negro = coinciden)")

    return distintos, peor


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)

    restar(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
