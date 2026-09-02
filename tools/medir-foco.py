#!/usr/bin/env python3
"""Mide si un estado de foco SE NOTA, en vez de suponerlo.

Un anillo de 2 px sobre un botón grande cambia el 3 % de la imagen: está
dibujado, pasa el contraste, y a simple vista no se ve. Esto compara la
captura del botón en reposo contra la del mismo botón con foco y dice qué
porcentaje de la superficie cambió de verdad.

    python3 tools/medir-foco.py reposo.png foco.png [--piso 10]
"""

import argparse
import pathlib
import sys


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "brand-audit"))
from leer_png import leer_png  # noqa: E402


# Un canal tiene que moverse más que esto para contar como cambio visible.
UMBRAL_CANAL = 12


def comparar(ruta_a, ruta_b):
    ancho_a, alto_a, canales_a, filas_a = leer_png(ruta_a)
    ancho_b, alto_b, canales_b, filas_b = leer_png(ruta_b)

    if (ancho_a, alto_a) != (ancho_b, alto_b):
        raise SystemExit(f"✗ las capturas no miden lo mismo: {ancho_a}×{alto_a} vs {ancho_b}×{alto_b}")

    distintos = 0
    total = ancho_a * alto_a
    salto_maximo = 0

    for y in range(alto_a):
        fila_a = filas_a[y]
        fila_b = filas_b[y]

        for x in range(ancho_a):
            ia = x * canales_a
            ib = x * canales_b
            salto = max(
                abs(fila_a[ia] - fila_b[ib]),
                abs(fila_a[ia + 1] - fila_b[ib + 1]),
                abs(fila_a[ia + 2] - fila_b[ib + 2]),
            )

            if salto > salto_maximo:
                salto_maximo = salto

            if salto > UMBRAL_CANAL:
                distintos += 1

    return distintos, total, salto_maximo


def filo(ruta, pagina, holgura=14):
    """Devuelve los primeros píxeles del control sobre su fila central.

    Si el píxel del filo se parece al de la página, el control se lee como si
    se hubiera ACHICADO en vez de haber ganado un borde. Es el error que un
    anillo blanco o marfil comete sobre un fondo claro."""
    ancho, alto, canales, filas = leer_png(ruta)
    fila = filas[alto // 2]
    borde = tuple(fila[i] for i in range(3))
    parece_pagina = all(abs(borde[i] - pagina[i]) <= holgura for i in range(3))
    return borde, parece_pagina


def main():
    partes = argparse.ArgumentParser()
    partes.add_argument("reposo")
    partes.add_argument("foco")
    partes.add_argument("--pagina", default=None,
                        help="color de la página, RRGGBB: chequea que el filo no se le confunda")
    partes.add_argument("--piso", type=float, default=10.0,
                        help="porcentaje mínimo de superficie que tiene que cambiar")
    args = partes.parse_args()

    distintos, total, salto = comparar(args.reposo, args.foco)
    porcentaje = 100 * distintos / total
    pasa = porcentaje >= args.piso
    marca = "✓" if pasa else "✗"

    print(f"{marca}  cambia el {porcentaje:5.1f} % de la superficie"
          f"  (piso {args.piso} %)  ·  salto máximo de canal: {salto}")

    if args.pagina:
        pagina = tuple(int(args.pagina.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
        borde, parece = filo(args.foco, pagina)

        if parece:
            print(f"✗  el filo del control quedó en {borde}, casi el color de la "
                  f"página {pagina}: se lee como si el botón se hubiera ACHICADO, "
                  f"no como un borde.")
            pasa = False
        else:
            print(f"✓  el filo del control quedó en {borde}: la silueta se conserva.")

    return 0 if pasa else 1


if __name__ == "__main__":
    sys.exit(main())
