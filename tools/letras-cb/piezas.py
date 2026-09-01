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


def wordmark():
    AM = 38.6
    dc, ic, rc = texto(FC, "C", AM, 0, 45.7513, REF)
    db, ib, rb = texto(FB, "B", AM, rc + AM * 0.1229, 45.7513, REF)
    # los huecos del original, medidos: 19.79 de las iniciales a la barra
    # y 18.59 de la barra al nombre. Se conservan tal cual.
    bx = rb + 19.79
    nx = bx + 1 + 18.59
    d1, _, r1 = texto(JOST, "ODONTOLOGÍA", 11.15, nx, 21.2005, RJ, 15.6 * 0.24)
    d2, _, r2 = texto(JOST, "Y ESTÉTICA", 11.15, nx, 43.4974, RJ, 15.6 * 0.24)
    W = max(r1, r2) + 2
    return (f'<svg viewBox="0 0 {W:.1f} 54" xmlns="http://www.w3.org/2000/svg">'
            f'<path d="{dc}" fill="#33322F"/><path d="{db}" fill="#33322F"/>'
            f'<rect x="{bx:.2f}" y="8" width="1" height="38" fill="#D9CBAA"/>'
            f'<path d="{d1}" fill="#615E58"/><path d="{d2}" fill="#615E58"/></svg>'), W


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
