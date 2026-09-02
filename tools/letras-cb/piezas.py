"""Arma las tres piezas del logo con la C y la B ya emparejadas (+170 / −170)."""
import os
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.misc.transform import Transform

AQUI = os.path.dirname(os.path.abspath(__file__))

# El aro y la media luna se leen de una copia CONGELADA del emblema original.
# Nunca del archivo que este guión escribe: eso sería morderse la cola.
src = open(f"{AQUI}/base-aro-y-luna.svg").read()
cu = src[src.index("<circle"):src.rindex("</svg>")]
ARO = cu[:cu.index("<!-- «C»")]
LUNA = cu[cu.index("<!-- LA MEDIA LUNA"):]

JOST = TTFont(f"{AQUI}/../../brand/fonts/Jost-Light-300.ttf")

# El nombre del wordmark se puede pedir en otro PESO. No es un capricho: es
# TAMAÑO ÓPTICO — un dibujo pensado en grande, pedido en chico, necesita el
# trazo más gordo, y engordarlo es lo que hace la tipografía desde el metal.
# Jost viene en variable, así que el peso sale del mismo archivo y no hace
# falta otra fuente. 300 es el de siempre: pedirlo devuelve el estático.
_JOSTS = {300: JOST}


def jost(peso=300):
    if peso not in _JOSTS:
        from fontTools.varLib.instancer import instantiateVariableFont
        var = TTFont(f"{AQUI}/../../brand/fonts/Jost-var.ttf")
        _JOSTS[peso] = instantiateVariableFont(var, {"wght": peso}, inplace=False)
    return _JOSTS[peso]


def caps(f):
    gs = f.getGlyphSet()
    bp = BoundsPen(gs)
    gs[f.getBestCmap()[ord("C")]].draw(bp)
    return (bp.bounds[3] - bp.bounds[1]) / f["head"].unitsPerEm


def texto(f, cad, alto, x, yb, ref, esp=0.0, fuente_por_letra=None):
    partes = []
    cur = x
    primero = True
    izq = der = None

    for L in cad:
        fu = (fuente_por_letra or {}).get(L, f)
        gs = fu.getGlyphSet()
        cm = fu.getBestCmap()
        u = fu["head"].unitsPerEm
        k = (alto / ref) / u
        g = gs[cm[ord(L)]]
        bp = BoundsPen(gs)
        g.draw(bp)

        if bp.bounds is None:
            cur += g.width * k + esp
            continue

        x0, y0, x1, y1 = bp.bounds

        if primero:
            cur = x - x0 * k
            primero = False

        p = SVGPathPen(gs)
        g.draw(TransformPen(p, Transform(k, 0, 0, -k, cur, yb)))
        partes.append(p.getCommands())

        a, b = cur + x0 * k, cur + x1 * k
        izq = a if izq is None else min(izq, a)
        der = b if der is None else max(der, b)
        cur += g.width * k + esp

    return " ".join(partes), izq, der


def anchura_por_cap(f, cad, track_em, ref):
    """Cuántas veces el alto de mayúscula mide la línea, a ese espaciado. Sirve
    para despejar el alto que entra en un ancho dado, en vez de tantearlo."""
    _, i, d = texto(f, cad, 100, 0, 0, ref, track_em * (100 / ref))
    return (d - i) / 100


FC = TTFont(f"{AQUI}/cb-inicial-c.ttf")     # la C angostada
FB = TTFont(f"{AQUI}/cb-inicial-b.ttf")      # la B ensanchada
REF = caps(FC)
RJ = caps(JOST)


def emblema(color_letra="#33322F"):
    b0, b1 = 95 - 0.90, 95 + 0.90
    _, i, r = texto(FC, "C", 30.70, 0, 92.86, REF)
    dC, _, _ = texto(FC, "C", 30.70, b0 - 11.80 - (r - i), 92.86, REF)
    dB, _, _ = texto(FB, "B", 30.70, b1 + 11.80, 92.86, REF)
    return (f'<svg viewBox="0 0 190 190" xmlns="http://www.w3.org/2000/svg">{ARO}'
            f'<path d="{dC}" fill="{color_letra}"/>'
            f'<rect x="{b0}" y="61.75" width="1.80" height="30.71" fill="#B08D57"/>'
            f'<path d="{dB}" fill="{color_letra}"/>{LUNA}</svg>')


# El espaciado del nombre, en EM.
#
# 0.24 es el valor MEDIDO en el wordmark del brief (pág. 5, a 1200 dpi): su
# línea larga mide 12.81 veces el alto de mayúscula y la nuestra a 0.24 mide
# 13.12 — la diferencia entra en el error de medir un cap de 74 px.
#
# ⚠ El 2-sep-2026 estuvo un rato en 0.15, porque para mayúsculas se recomienda
# entre 0.05 y 0.12 y 0.24 es el doble del techo. Se volvió a 0.24 al medir el
# brief entero: el wordmark tiene que COINCIDIR con el documento que Cecilia
# aprobó, y ahí el espaciado es éste. La recomendación tipográfica describe
# texto para leer, no un logotipo, y acá manda el brief.
TRACK = 0.24


# El peso del NOMBRE. Nuestra reconstrucción cargó Jost Light 300 y el brief
# está en 400: medido sobre su pág. 5 a 1200 dpi, su relación asta/altura de
# mayúscula da 0.122, y la de Jost 400 es 0.1181 — la de Light 300 es 0.0766,
# a un 74% de distancia. O sea que el nombre nos salió MÁS FINO que el
# original, y no por una decisión: por el archivo que se cargó.
# Corregido el 2-sep-2026, por orden de Juan: el wordmark coincide con el brief.
PESO = 400


def wordmark(peso=PESO, ancho_barra=1, track=TRACK):
    """`peso` es el del NOMBRE; `ancho_barra`, el de la barra; `track`, el
    espaciado en em. Los tres por defecto son los de la marca."""
    J = jost(peso)
    RJ_p = caps(J)
    AM = 38.6
    dc, ic, rc = texto(FC, "C", AM, 0, 45.7513, REF)
    db, ib, rb = texto(FB, "B", AM, rc + AM * 0.1229, 45.7513, REF)
    # los huecos del original, medidos: 19.79 de las iniciales a la barra
    # y 18.59 de la barra al nombre. Se conservan tal cual.
    bx = rb + 19.79
    nx = bx + ancho_barra + 18.59
    # el alto de mayúscula del nombre sube junto con el espaciado que se libera,
    # de modo que el wordmark conserva su ancho total
    cap = 11.15 * (13.12 / anchura_por_cap(J, "ODONTOLOGÍA", track, RJ_p))
    esp = track * (cap / RJ_p)
    d1, _, r1 = texto(J, "ODONTOLOGÍA", cap, nx, 21.2005, RJ_p, esp)
    d2, _, r2 = texto(J, "Y ESTÉTICA", cap, nx, 43.4974, RJ_p, esp)
    W = max(r1, r2) + 2
    return (f'<svg viewBox="0 0 {W:.1f} 54" xmlns="http://www.w3.org/2000/svg">'
            f'<path d="{dc}" fill="#33322F"/><path d="{db}" fill="#33322F"/>'
            f'<rect x="{bx:.2f}" y="8" width="{ancho_barra}" height="38" fill="#B08D57"/>'
            f'<path d="{d1}" fill="#615E58"/><path d="{d2}" fill="#615E58"/></svg>'), W


def apilado(track=TRACK, ancho=247.11, cb=0.215):
    """LA CUARTA DISPOSICIÓN: el CB arriba, la rayita en horizontal, el nombre
    en dos líneas debajo.

    🔴 POR QUÉ EXISTE, que no es estética. En la disposición horizontal el
    bloque `CB` + barra + huecos se lleva 100.8 de las 247 unidades ANTES de
    que empiece el nombre, así que a la palabra le queda el 59% del ancho para
    once mayúsculas espaciadas y su alto no puede pasar de 11.15. El grosor de
    trazo sale de ese alto, y por eso el nombre se cae a los tamaños chicos:
    no es el color ni la resolución, es la geometría. Apilado, el nombre deja
    de competir por el ancho, se queda con el 100% y su alto salta a ~20.8 —
    el trazo engorda 1.87x SIN tocar la tipografía ni su peso.

    Y no se inventó acá: el brief ya la usa en la señalética de su pág. 12.
    Estaba anotada en el doc de estado como «usada pero no declarada».

    Va donde el espacio aprieta: encabezado del sitio en el celular, firma de
    correo, tarjeta. La horizontal queda para donde sobra ancho.
    """
    J = jost()
    RJ_p = caps(J)

    # el alto de mayúscula sale de despejar, no de tantear: la línea larga
    # tiene que medir exactamente el ancho pedido
    cap = ancho / anchura_por_cap(J, "ODONTOLOGÍA", track, RJ_p)
    esp = track * (cap / RJ_p)
    # `cb` es el alto de las iniciales como fracción del ancho de la pieza.
    # 0.215 NO se eligió a ojo: es lo que mide la placa de fachada de la pág. 12
    # del brief, la versión apilada que el propio documento ya usaba. Medida
    # sobre el PDF a 1200 dpi el 2-sep-2026. En el wordmark horizontal la
    # fracción es 0.156, pero ahí el CB comparte renglón con el nombre.
    AM = cb * ancho

    # los tres renglones, de arriba hacia abajo
    y_cb = AM
    y_raya = y_cb + AM * 0.30
    y_l1 = y_raya + AM * 0.30 + cap
    y_l2 = y_l1 + cap * 1.45

    # las iniciales, centradas por su caja
    dc, ic, rc = texto(FC, "C", AM, 0, y_cb, REF)
    db, ib, rb = texto(FB, "B", AM, rc + AM * 0.1229, y_cb, REF)
    corr = (ancho - (rb - ic)) / 2 - ic
    dc, ic, rc = texto(FC, "C", AM, corr, y_cb, REF)
    db, _, _ = texto(FB, "B", AM, rc + AM * 0.1229, y_cb, REF)

    def centrada(cad, y):
        _, a, b = texto(J, cad, cap, 0, y, RJ_p, esp)
        d, _, _ = texto(J, cad, cap, (ancho - (b - a)) / 2, y, RJ_p, esp)
        return d

    d1 = centrada("ODONTOLOGÍA", y_l1)
    d2 = centrada("Y ESTÉTICA", y_l2)

    raya = ancho * 0.32
    alto = y_l2 + cap * 0.22

    return (f'<svg viewBox="0 0 {ancho:.1f} {alto:.1f}" xmlns="http://www.w3.org/2000/svg">'
            f'<path d="{dc}" fill="#33322F"/>'
            f'<path d="{db}" fill="#33322F"/>'
            f'<rect x="{(ancho - raya) / 2:.2f}" y="{y_raya:.2f}" '
            f'width="{raya:.2f}" height="{AM * 0.042:.2f}" fill="#B08D57"/>'
            f'<path d="{d1}" fill="#615E58"/>'
            f'<path d="{d2}" fill="#615E58"/></svg>'), alto


def submarca():
    AM = 18.65      # la altura de mayúscula que da el cuerpo 26.1 del original
    dc, ic, rc = texto(FC, "C", AM, 0, 57, REF)
    db, ib, rb = texto(FB, "B", AM, rc + AM * 0.1229, 57, REF)
    ancho = rb - ic
    corr = 48 - (ic + ancho / 2)
    return (f'<svg viewBox="0 0 96 96" xmlns="http://www.w3.org/2000/svg">'
            f'<circle cx="48" cy="48" r="48" fill="#33322F"/>'
            f'<g transform="translate({corr:.3f},0)">'
            f'<path d="{dc}" fill="#E4D6BC"/><path d="{db}" fill="#E4D6BC"/></g></svg>')
