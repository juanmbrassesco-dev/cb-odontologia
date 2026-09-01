"""
Mide el emblema CB contra los seis numeros del brief, MAS el perfil de grosor
del arco. Se calibra solo: la escala sale del diametro del circulo, no se pasa
a mano. Descarta islas de pocos pixeles, que son antialias y no dibujo.

    python3 medir_emblema_calibrado.py <archivo.png>
"""

import sys

from leer_png import leer_png


# El brief, en pixeles de un circulo de 190. Es la vara, no se toca.
# Medido el 31-ago-2026 sobre el emblema de la FILA DE VERSIONES de la pag. 5
# (el rotulado "SECUNDARIA"), a 1600 dpi. Ojo: el brief dibuja el mismo emblema
# otra vez mas abajo, en el diagrama de espacio de reserva, y NO coincide: alla
# el trazo queda mas fino porque el original tiene grosores fijos en pixeles.
OBJETIVO = {
    "altura de mayuscula":  30.7,
    "ancho de las letras":  70.4,
    "ancho de la sonrisa":  40.9,
    "alto de la sonrisa":   15.9,
    "hueco letras->arco":   30.1,
    "grupo bajo el centro":  6.2,
}

DIAMETRO_DE_REFERENCIA = 190.0

# Un trazo del brief mide 0,84 % del diametro. Por debajo de esta fraccion de
# su largo, una mancha no es trazo: es el borde difuminado de otra cosa.
MINIMO_DE_ISLA = 8


def es_dorado(r, g, b):
    return 110 < r < 230 and 80 < g < 190 and 40 < b < 150 and r > b + 30


def es_oscuro(r, g, b):
    return r < 110 and g < 110 and b < 110


def pintados(filas, ancho, alto, canales, prueba):
    """Todos los pixeles que pasan la prueba, como conjunto de (x, y)."""
    encontrados = set()

    for y in range(alto):
        fila = filas[y]

        for x in range(ancho):
            i = x * canales

            if prueba(fila[i], fila[i + 1], fila[i + 2]):
                encontrados.add((x, y))

    return encontrados


def islas(puntos, minimo=MINIMO_DE_ISLA):
    """Agrupa los pixeles que se tocan y tira los grupos chicos."""
    visto = set()
    grupos = []

    for punto in puntos:
        if punto in visto:
            continue

        pila = [punto]
        grupo = []
        visto.add(punto)

        while pila:
            x, y = pila.pop()
            grupo.append((x, y))

            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    vecino = (x + dx, y + dy)

                    if vecino in puntos and vecino not in visto:
                        visto.add(vecino)
                        pila.append(vecino)

        if len(grupo) >= minimo:
            grupos.append(grupo)

    return grupos


def caja(puntos):
    xs = [x for x, _ in puntos]
    ys = [y for _, y in puntos]

    return min(xs), min(ys), max(xs), max(ys)


def medir(archivo):
    ancho, alto, canales, filas = leer_png(archivo)

    dorados = pintados(filas, ancho, alto, canales, es_dorado)
    oscuros = pintados(filas, ancho, alto, canales, es_oscuro)

    # El circulo es la isla dorada mas grande, y ademas es cuadrada.
    grupos = sorted(islas(dorados), key=len, reverse=True)

    if not grupos:
        raise SystemExit("no encontre nada dorado en " + archivo)

    aro = grupos[0]
    ax0, ay0, ax1, ay1 = caja(aro)

    diametro = ((ax1 - ax0) + (ay1 - ay0)) / 2
    escala = diametro / DIAMETRO_DE_REFERENCIA
    cx = (ax0 + ax1) / 2
    cy = (ay0 + ay1) / 2
    radio = diametro / 2

    def adentro(x, y, margen):
        return ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 < radio - margen

    # Las letras y la barra: lo oscuro que cae adentro del circulo.
    letras = [p for g in islas(oscuros) for p in g if adentro(p[0], p[1], radio * 0.06)]

    if not letras:
        raise SystemExit("no encontre las letras en " + archivo)

    lx0, ly0, lx1, ly1 = caja(letras)

    # El arco: lo dorado que esta bien adentro del aro y por debajo de las letras.
    arco = [
        p
        for g in islas(dorados)
        for p in g
        if adentro(p[0], p[1], radio * 0.10) and p[1] > ly1
    ]

    if not arco:
        raise SystemExit("no encontre el arco en " + archivo)

    sx0, sy0, sx1, sy1 = caja(arco)

    medido = {
        "altura de mayuscula":  (ly1 - ly0) / escala,
        "ancho de las letras":  (lx1 - lx0) / escala,
        "ancho de la sonrisa":  (sx1 - sx0) / escala,
        "alto de la sonrisa":   (sy1 - sy0) / escala,
        "hueco letras->arco":   (sy0 - ly1) / escala,
        "grupo bajo el centro": ((ly0 + sy1) / 2 - cy) / escala,
    }

    return escala, diametro, arco, medido


def informe(archivo):
    escala, diametro, arco, medido = medir(archivo)

    print(archivo)
    print("  circulo: %.1f px de imagen  ->  escala %.4f (1 px de logo = %.3f px de imagen)"
          % (diametro, escala, escala))
    print()
    print("  %-22s %8s %8s %8s" % ("", "brief", "medido", "falta"))

    peor = 0.0

    for clave, valor in OBJETIVO.items():
        falta = valor - medido[clave]
        peor = max(peor, abs(falta))
        print("  %-22s %8.1f %8.1f %8.1f" % (clave, valor, medido[clave], falta))

    print("  %-22s %8s %8s %8.1f" % ("PEOR DESVIO", "", "", peor))

    # El perfil de grosor: por columna, cuanto mide el arco de alto.
    columnas = {}

    for x, y in arco:
        columnas.setdefault(x, []).append(y)

    xs = sorted(columnas)
    x0, x1 = xs[0], xs[-1]

    print()
    print("  PERFIL DE GROSOR del arco (px de logo):")
    print("  %-12s %s" % ("posicion", "grosor"))

    for fraccion in (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0):
        x = min(xs, key=lambda c: abs(c - (x0 + fraccion * (x1 - x0))))
        alturas = columnas[x]
        grosor = (max(alturas) - min(alturas) + 1) / escala

        if fraccion == 0.0:
            etiqueta = "punta izq"
        elif fraccion == 1.0:
            etiqueta = "punta der"
        elif fraccion == 0.5:
            etiqueta = "CENTRO"
        else:
            etiqueta = "%d%%" % (fraccion * 100)

        print("  %-12s %.2f" % (etiqueta, grosor))


if __name__ == "__main__":
    for archivo in sys.argv[1:]:
        informe(archivo)
        print()
