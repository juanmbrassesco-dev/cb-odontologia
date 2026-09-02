#!/usr/bin/env python3
"""Mide el contraste WCAG de los pares declarados en css/tokens.css.

No inventa nada: lee los colores y los pares del mismo archivo que usa el
sitio, así que si el CSS cambia y un par deja de pasar, esto grita. Sale
con código 1 si UN solo par no llega a su piso.

    python3 tools/medir-contraste.py
"""

import pathlib
import re
import sys


TOKENS = pathlib.Path(__file__).resolve().parent.parent / "css" / "tokens.css"


def leer_tokens(texto):
    """Devuelve {nombre: '#RRGGBB'} resolviendo los var(--otro) de un salto."""
    crudos = dict(
        re.findall(
            r"--([a-z0-9-]+)\s*:\s*(#[0-9A-Fa-f]{6}|var\(--[a-z0-9-]+\))",
            texto,
        )
    )
    resueltos = {}

    for nombre, valor in crudos.items():
        if valor.startswith("var("):
            apuntado = valor[6:-1]
            valor = crudos.get(apuntado, "")
        if valor.startswith("#"):
            resueltos[nombre] = valor.upper()

    return resueltos


def leer_pares(texto):
    """Devuelve [(texto, fondo, piso, para_que)] de los renglones @par."""
    patron = r"@par\s+([a-z0-9-]+)\s+sobre\s+([a-z0-9-]+)\s*>=\s*([\d.]+)\s*·\s*(.+)"
    return [
        (a, b, float(piso), uso.strip())
        for a, b, piso, uso in re.findall(patron, texto)
    ]


def luminancia(hexc):
    """Luminancia relativa de WCAG 2.1 — la fórmula, no una aproximación."""
    canales = []

    for i in (1, 3, 5):
        v = int(hexc[i:i + 2], 16) / 255
        if v <= 0.03928:
            canales.append(v / 12.92)
        else:
            canales.append(((v + 0.055) / 1.055) ** 2.4)

    r, g, b = canales
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def razon(hex_a, hex_b):
    la = luminancia(hex_a)
    lb = luminancia(hex_b)
    alto = max(la, lb)
    bajo = min(la, lb)
    return (alto + 0.05) / (bajo + 0.05)


def medir():
    texto = TOKENS.read_text(encoding="utf-8")
    tokens = leer_tokens(texto)
    pares = leer_pares(texto)
    filas = []

    for nombre_a, nombre_b, piso, uso in pares:
        falta = [n for n in (nombre_a, nombre_b) if n not in tokens]

        if falta:
            filas.append((nombre_a, nombre_b, None, piso, uso, "TOKEN INEXISTENTE: " + ", ".join(falta)))
            continue

        valor = razon(tokens[nombre_a], tokens[nombre_b])
        filas.append((nombre_a, nombre_b, valor, piso, uso, None))

    return filas


def main():
    filas = medir()

    if not filas:
        print("✗ no hay ningún par declarado en css/tokens.css")
        return 1

    fallados = 0

    for nombre_a, nombre_b, valor, piso, uso, error in filas:
        etiqueta = f"{nombre_a} sobre {nombre_b}"

        if error is not None:
            print(f"✗  {etiqueta:38} {error}")
            fallados += 1
            continue

        pasa = valor >= piso
        marca = "✓" if pasa else "✗"
        print(f"{marca}  {etiqueta:38} {valor:5.2f}  (piso {piso})  {uso}")

        if not pasa:
            fallados += 1

    print()

    if fallados:
        print(f"✗ {fallados} de {len(filas)} pares NO llegan al piso. No se publica.")
        return 1

    print(f"✓ los {len(filas)} pares pasan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
