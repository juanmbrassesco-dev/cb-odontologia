"""Lector de PNG sin dependencias, para medir el logo del brief pixel a pixel."""

import struct
import zlib


def leer_png(ruta):
    datos = open(ruta, "rb").read()
    assert datos[:8] == b"\x89PNG\r\n\x1a\n", "no es un PNG"

    pos = 8
    cabecera = None
    comprimido = b""

    while pos < len(datos):
        largo, tipo = struct.unpack(">I4s", datos[pos:pos + 8])
        cuerpo = datos[pos + 8:pos + 8 + largo]
        pos += 12 + largo

        if tipo == b"IHDR":
            cabecera = struct.unpack(">IIBBBBB", cuerpo)
        elif tipo == b"IDAT":
            comprimido += cuerpo
        elif tipo == b"IEND":
            break

    ancho, alto, bits, color, _, _, _ = cabecera
    assert bits == 8, "sólo 8 bits por canal"

    canales = {0: 1, 2: 3, 4: 2, 6: 4}[color]
    crudo = zlib.decompress(comprimido)
    paso = ancho * canales

    filas = []
    previa = bytearray(paso)

    for y in range(alto):
        inicio = y * (paso + 1)
        filtro = crudo[inicio]
        linea = bytearray(crudo[inicio + 1:inicio + 1 + paso])

        for i in range(paso):
            a = linea[i - canales] if i >= canales else 0
            b = previa[i]
            c = previa[i - canales] if i >= canales else 0

            if filtro == 1:
                linea[i] = (linea[i] + a) & 0xFF
            elif filtro == 2:
                linea[i] = (linea[i] + b) & 0xFF
            elif filtro == 3:
                linea[i] = (linea[i] + (a + b) // 2) & 0xFF
            elif filtro == 4:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pred = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                linea[i] = (linea[i] + pred) & 0xFF

        filas.append(bytes(linea))
        previa = linea

    return ancho, alto, canales, filas


def caja(filas, ancho, canales, prueba, recorte=None):
    """Devuelve (x0, y0, x1, y1) de los píxeles que pasan `prueba`."""
    x0, y0, x1, y1 = 10**9, 10**9, -1, -1
    rx0, ry0, rx1, ry1 = recorte or (0, 0, ancho, len(filas))

    for y in range(ry0, min(ry1, len(filas))):
        fila = filas[y]
        for x in range(rx0, min(rx1, ancho)):
            i = x * canales
            if prueba(fila[i], fila[i + 1], fila[i + 2]):
                if x < x0: x0 = x
                if x > x1: x1 = x
                if y < y0: y0 = y
                if y > y1: y1 = y

    return (x0, y0, x1, y1) if x1 >= 0 else None
