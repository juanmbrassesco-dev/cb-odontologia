#!/usr/bin/env python3
"""Mide si todo lo de un tablero arranca en la misma línea vertical.

Mirar la alineación a ojo no sirve: una sangría de tres píxeles no se ve y
rompe igual. Esto recorre la captura fila por fila, encuentra dónde empieza
y dónde termina la tinta de cada bloque, y grita si alguno no arranca donde
arrancan los demás.

    python3 tools/medir-alineacion.py <captura.png> --margen 20
"""

import argparse
import pathlib
import sys


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "brand-audit"))
from leer_png import leer_png  # noqa: E402


# Cuánto se puede apartar un bloque del margen antes de que sea un error.
# Dos píxeles es el juego que dejan las panzas de las letras redondas.
TOLERANCIA = 2


def bandas(filas, ancho, canales, fondo, umbral=18):
    """Agrupa las filas con tinta en bloques, y da el x mínimo y máximo de cada uno."""
    encontradas = []
    actual = None

    for y, fila in enumerate(filas):
        izq = None
        der = None

        for x in range(ancho):
            i = x * canales
            distinto = (
                abs(fila[i] - fondo[0]) > umbral
                or abs(fila[i + 1] - fondo[1]) > umbral
                or abs(fila[i + 2] - fondo[2]) > umbral
            )
            if distinto:
                if izq is None:
                    izq = x
                der = x

        if izq is None:
            if actual is not None:
                encontradas.append(actual)
                actual = None
            continue

        if actual is None:
            actual = {"y0": y, "y1": y, "izq": izq, "der": der}
        else:
            actual["y1"] = y
            actual["izq"] = min(actual["izq"], izq)
            actual["der"] = max(actual["der"], der)

    if actual is not None:
        encontradas.append(actual)

    return encontradas


def main():
    partes = argparse.ArgumentParser()
    partes.add_argument("captura")
    partes.add_argument("--margen", type=int, required=True,
                        help="dónde debería arrancar todo, en píxeles")
    partes.add_argument("--tolerancia", type=int, default=TOLERANCIA,
                        help="cuánto se puede apartar un bloque, en píxeles")
    partes.add_argument("--alto-minimo", type=int, default=4,
                        help="ignora bandas más finas que esto (rayas, bordes)")
    args = partes.parse_args()

    ancho, alto, canales, filas = leer_png(args.captura)
    fondo = (filas[0][0], filas[0][1], filas[0][2])
    todas = bandas(filas, ancho, canales, fondo)
    utiles = [b for b in todas if b["y1"] - b["y0"] + 1 >= args.alto_minimo]

    if not utiles:
        print("✗ no se encontró contenido en la captura")
        return 1

    print(f"captura {ancho}×{alto} · fondo {fondo} · {len(utiles)} bloques")
    print()

    desviados = []

    for b in utiles:
        corrimiento = b["izq"] - args.margen
        marca = "✓" if abs(corrimiento) <= args.tolerancia else "✗"
        print(
            f"{marca}  y {b['y0']:>5}–{b['y1']:<5}"
            f"  izquierda {b['izq']:>4}  (corrimiento {corrimiento:+d})"
            f"  derecha {b['der']:>4}"
        )

        if abs(corrimiento) > args.tolerancia:
            desviados.append(b)

    print()

    if desviados:
        print(f"✗ {len(desviados)} de {len(utiles)} bloques no arrancan en {args.margen} px.")
        return 1

    print(f"✓ los {len(utiles)} bloques arrancan en {args.margen} px.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
