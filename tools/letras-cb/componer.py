"""Las tres piezas, con la letra emparejada (+170 / −170) y el centrado óptico puesto."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import piezas as P
from fontTools.pens.boundsPen import BoundsPen

# el desvío óptico medido: el promedio entre centro de caja y centro de tinta
DX_SUBMARCA = 0.00   # decisión de Juan: la caja, cerrada
DY_SUBMARCA = 0.28


def alto_de(f, letra, alto_may):
    gs = f.getGlyphSet()
    bp = BoundsPen(gs)
    gs[f.getBestCmap()[ord(letra)]].draw(bp)
    return (bp.bounds[3] - bp.bounds[1]) / f["head"].unitsPerEm * (alto_may / P.REF)


def submarca(color="#E4D6BC", fondo="#33322F", alto_may=18.65):
    """El CB dentro del disco. Las dos iniciales salen en UN SOLO camino y sin
    `transform`: así la herramienta que arma la versión blanca las puede calar."""
    alto_B = alto_de(P.FB, "B", alto_may)
    yb = 48 + alto_B / 2 - DY_SUBMARCA

    # primera pasada: para saber cuánto hay que correr el par
    _, ic, rc = P.texto(P.FC, "C", alto_may, 0, yb, P.REF)
    _, ib, rb = P.texto(P.FB, "B", alto_may, rc + alto_may * 0.1229, yb, P.REF)
    corr = 48 - (ic + (rb - ic) / 2) - DX_SUBMARCA

    # segunda pasada: ya con el corrimiento adentro de las coordenadas
    dc, ic, rc = P.texto(P.FC, "C", alto_may, corr, yb, P.REF)
    db, _, _ = P.texto(P.FB, "B", alto_may, rc + alto_may * 0.1229, yb, P.REF)

    return (f'<svg viewBox="0 0 96 96" xmlns="http://www.w3.org/2000/svg" role="img" '
            f'aria-label="CB"><circle cx="48" cy="48" r="48" fill="{fondo}"/>'
            f'<path d="{dc} {db}" fill="{color}"/></svg>')


if __name__ == "__main__":
    AQUI = os.path.dirname(os.path.abspath(__file__))
    SALIDA = f"{AQUI}/salida"
    os.makedirs(SALIDA, exist_ok=True)

    # Las tres piezas, en color. Las versiones blancas NO salen de acá:
    # las arma `tools/print-pack/version_blanca.py`, que además cala la submarca.
    wordmark, ancho = P.wordmark()

    open(f"{SALIDA}/cb-wordmark.svg", "w").write(wordmark)
    open(f"{SALIDA}/cb-emblema.svg", "w").write(P.emblema())
    open(f"{SALIDA}/cb-submarca.svg", "w").write(submarca())

    print(f"tres piezas escritas en salida/ · el wordmark mide {ancho:.1f} de ancho")
