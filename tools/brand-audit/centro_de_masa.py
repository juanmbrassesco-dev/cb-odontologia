"""Mide DÓNDE está la tinta de un dibujo, con precisión de centésima de píxel.

Por qué no alcanza con una caja de tinta: una caja necesita un umbral ("¿esto
ya es tinta?"), y cuando dos renders suavizan distinto los bordes, el umbral
cae en lugares distintos y el número miente. El centro de gravedad no: un
borde apenas teñido pesa poco y un trazo lleno pesa mucho, así que dos renders
con distinto suavizado dan el MISMO centro si la figura está en el mismo lugar.

    python3 centro_de_masa.py <a.png> <b.png> <escala> [x0 x1]

`escala` es el factor con el que se renderizó (el `--force-device-scale-factor`
de Chrome): sirve para devolver el corrimiento en píxeles de CSS y no de imagen.

⚠ LEER EL RESULTADO A UNA SOLA ESCALA NO ALCANZA. Un desvío de la grilla de
píxeles se achica al afinar la grilla; uno de dibujo se queda clavado en el
mismo número. Medí a 2x, 4x y 8x antes de corregir nada: el 31-ago-2026 una
corrección correcta estuvo a punto de tirarse por mirar sólo 2x.
"""

import sys

from leer_png import leer_png

FONDO = (250, 247, 242)   # el marfil de la marca


def centro_de_masa(ruta, x0=0, x1=10 ** 9, fondo=FONDO):
    ancho, alto, canales, filas = leer_png(ruta)
    suma_x = 0.0
    suma_y = 0.0
    masa = 0.0

    for y in range(alto):
        fila = filas[y]

        for x in range(x0, min(x1, ancho)):
            i = x * canales
            tinta = max(fondo[c] - fila[i + c] for c in range(3))

            if tinta > 0:
                masa += tinta
                suma_x += x * tinta
                suma_y += y * tinta

    if masa == 0:
        raise SystemExit(f"no hay tinta en {ruta} entre x={x0} y x={x1}")

    return suma_x / masa, suma_y / masa


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)

    ruta_a = sys.argv[1]
    ruta_b = sys.argv[2]
    escala = float(sys.argv[3])
    x0 = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    x1 = int(sys.argv[5]) if len(sys.argv) > 5 else 10 ** 9

    ax, ay = centro_de_masa(ruta_a, x0, x1)
    bx, by = centro_de_masa(ruta_b, x0, x1)

    print(f"{ruta_a}: centro en ({ax / escala:.4f}, {ay / escala:.4f}) px de CSS")
    print(f"{ruta_b}: centro en ({bx / escala:.4f}, {by / escala:.4f}) px de CSS")
    print(f"corrimiento: x {(bx - ax) / escala:+.4f} px · y {(by - ay) / escala:+.4f} px")
