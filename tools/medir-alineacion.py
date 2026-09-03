#!/usr/bin/env python3
"""Mide si cada bloque de un tablero está en un lugar LEGÍTIMO.

Mirar la alineación a ojo no sirve: una sangría de tres píxeles no se ve y
rompe igual. Esto recorre la captura fila por fila, encuentra dónde empieza y
dónde termina la tinta de cada bloque, y grita si alguno cae donde no va.

    python3 tools/medir-alineacion.py <captura.png> --margen 20 --sangria 22

⚠️ HASTA EL 3-SEP-2026 MEDÍA UNA SOLA COSA —"¿arranca en el margen?"— y por eso
gritaba sobre dos cosas que están BIEN: los botones, que el sistema centra a
propósito desde ese día, y las líneas seguidas de una lista con sangría
colgante. Con 8 falsos por tablero, la lista dejaba de leerse.

LO QUE NO SE HIZO: bajarle el piso. El sistema no aflojó su alineación, ganó
DOS EXCEPCIONES DECLARADAS, así que el instrumento pasa de medir una posición a
medir un CONJUNTO de posiciones legítimas:

  1. EN EL MARGEN     — arranca donde arranca todo lo demás.
  2. CENTRADO         — el hueco de la izquierda mide lo mismo que el de la
                        derecha. No se declara: se MIDE, así que un bloque no
                        puede decir que está centrado sin estarlo. Se mide
                        contra la COLUMNA DE CONTENIDO, no contra la página:
                        en escritorio el sitio escribe adentro de 640 px, y un
                        botón centrado ahí no está centrado en 1280.
  3. SANGRADO         — arranca a una distancia declarada con --sangria. Ésta
                        sí hay que decirla, porque una sangría de 22 px y un
                        error de 22 px son el mismo píxel.

Cualquier otra posición sigue siendo un error.

⚠️ Y queda escrito el límite, porque un medidor que no lo dice miente por
omisión: un bloque corrido por error que además termine simétrico se va a leer
como centrado. Es raro y es el precio de no tener que declarar a mano cada
botón; lo que la herramienta NO puede hacer es adivinar la intención.
"""

import argparse
import pathlib
import sys


sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "brand-audit"))
from leer_png import leer_png  # noqa: E402


# Cuánto se puede apartar un bloque de una posición legítima antes de que sea
# un error. Dos píxeles es el juego que dejan las panzas de las letras redondas
# — y, en el centrado, el píxel que sobra cuando el ancho del bloque es impar.
TOLERANCIA = 2


def ubicar(bloque, margen, columnas, sangrias, tolerancia):
    """Dice en cuál de las posiciones legítimas cae el bloque, o None."""
    if abs(bloque["izq"] - margen) <= tolerancia:
        return "en el margen"

    for sangria in sangrias:
        if abs(bloque["izq"] - margen - sangria) <= tolerancia:
            return f"sangrado {sangria}"

    # Centrado en alguna de las medidas que el sistema declara.
    hueco_izq = bloque["izq"] - margen

    for columna in columnas:
        hueco_der = margen + columna - bloque["der"] - 1

        if abs(hueco_izq - hueco_der) <= tolerancia:
            return f"centrado en {columna}"

    return None


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
    partes.add_argument("--sangria", type=int, action="append", default=[],
                        metavar="PX",
                        help="sangría declarada del sistema; se puede repetir")
    partes.add_argument("--columna", type=int, action="append", default=[],
                        metavar="PX",
                        help="ancho de una columna de contenido; se puede "
                             "repetir. Por defecto, toda la página menos los "
                             "dos márgenes")
    args = partes.parse_args()

    ancho, alto, canales, filas = leer_png(args.captura)
    fondo = (filas[0][0], filas[0][1], filas[0][2])
    todas = bandas(filas, ancho, canales, fondo)
    utiles = [b for b in todas if b["y1"] - b["y0"] + 1 >= args.alto_minimo]

    if not utiles:
        print("✗ no se encontró contenido en la captura")
        return 1

    columnas = args.columna or [ancho - 2 * args.margen]

    print(f"captura {ancho}×{alto} · fondo {fondo}"
          f" · columnas {', '.join(str(c) for c in columnas)}"
          f" · {len(utiles)} bloques")
    print()

    desviados = []
    cuenta = {}

    for b in utiles:
        donde = ubicar(b, args.margen, columnas, args.sangria, args.tolerancia)
        marca = "✓" if donde else "✗"
        cuenta[donde or "fuera de lugar"] = cuenta.get(donde or "fuera de lugar", 0) + 1

        print(
            f"{marca}  y {b['y0']:>5}–{b['y1']:<5}"
            f"  izquierda {b['izq']:>4}  derecha {b['der']:>4}"
            f"  · {donde or 'FUERA DE LUGAR'}"
        )

        if not donde:
            desviados.append(b)

    print()
    print("  ".join(f"{n} {nombre}" for nombre, n in sorted(cuenta.items())))
    print()

    if desviados:
        print(f"✗ {len(desviados)} de {len(utiles)} bloques caen fuera de lugar.")
        return 1

    print(f"✓ los {len(utiles)} bloques caen en una posición legítima.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
