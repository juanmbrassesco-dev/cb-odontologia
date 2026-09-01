"""Convierte el TEXTO de un SVG en CONTORNOS: las letras dejan de ser letras.

Por qué hace falta. Mientras un `<text>` sea texto, el archivo le pide a quien
lo abra que tenga la tipografía instalada. Si no la tiene, el navegador pone
otra y el logo sale mal — no falla, sale MAL, que es peor. Una imprenta no
tiene por qué tener Marcellus ni Jost. Pasado a contornos, el archivo no
depende de nada: son dibujos.

Y por eso mismo NO se hace antes de tiempo: pasar a curvas CONGELA. Después ya
no se puede cambiar una letra sin rehacer el paso.

    /opt/homebrew/opt/fonttools/libexec/bin/python3 svg_a_curvas.py <entrada.svg> <salida.svg> [--recortar]

Con `--recortar` deja además el lienzo del tamaño exacto del dibujo, sin aire
alrededor. Ver `recortar()` para por qué ese aire aparece solo.

⚠ Se corre con el Python de fonttools, no con el `python3` suelto: el módulo
`fontTools` vive adentro del entorno que instaló Homebrew.
"""

import re
import sys
from pathlib import Path

from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

from kerning import tabla_de_kerning

FUENTES = Path(__file__).resolve().parents[2] / "brand" / "fonts"

# Qué archivo real corresponde a cada `font-family` del SVG.
CATALOGO = {
    "Marcellus": FUENTES / "Marcellus-Regular.ttf",
    "Jost": FUENTES / "Jost-Light-300.ttf",
}

_cache = {}

AVISO_NUEVO = """
  ✅ YA NO HAY TEXTO ACÁ: cada letra es un dibujo. Este archivo se ve igual en
  cualquier máquina, tenga o no instaladas Marcellus y Jost — que es lo que
  necesita una imprenta. Generado por `tools/print-pack/svg_a_curvas.py` a
  partir del archivo con texto; ése sigue siendo la fuente y éste, el derivado.

  ⚠ NO SE EDITA A MANO. Para cambiar algo se toca el original con texto y se
  vuelve a convertir: ése es la fuente, éste el derivado.

  ✅ ÉSTE ES EL LOGO QUE SE ENTREGA, para todo: web e imprenta. El archivo con
  texto NO es una segunda versión del logo — es el original editable, y no sale
  del repositorio. Un logo que le pide la tipografía a quien lo abre puede
  aparecer en Georgia un día que la red falle, y eso es peor que cualquier
  diferencia de grosor.
"""


def cargar(familia):
    if familia not in _cache:
        fuente = TTFont(CATALOGO[familia])
        _cache[familia] = (fuente, tabla_de_kerning(fuente))
    return _cache[familia]


def atributo(bloque, nombre, por_defecto=None):
    hallazgo = re.search(rf'{nombre}="([^"]*)"', bloque)
    return hallazgo.group(1) if hallazgo else por_defecto


def familia_de(valor):
    """El `font-family` trae una lista de respaldos: manda el primero."""
    primera = valor.split(",")[0].strip().strip("'\"")

    if primera not in CATALOGO:
        raise SystemExit(f"no tengo el archivo de la tipografía «{primera}»")

    return primera


def a_pixeles(valor, tamano):
    """`letter-spacing` puede venir en em o en píxeles."""
    if valor is None:
        return 0.0

    valor = valor.strip()

    if valor.endswith("em"):
        return float(valor[:-2]) * tamano

    return float(valor.rstrip("px") or 0)


def contornos(texto, familia, tamano, espaciado, x, y, anclaje):
    fuente, kern = cargar(familia)
    upem = fuente["head"].unitsPerEm
    escala = tamano / upem
    cmap = fuente.getBestCmap()
    glifos = fuente.getGlyphSet()

    nombres = []
    for caracter in texto:
        if ord(caracter) not in cmap:
            raise SystemExit(f"la tipografía {familia} no tiene el glifo «{caracter}»")
        nombres.append(cmap[ord(caracter)])

    # El KERNING de cada pareja, en píxeles del dibujo. Sin esto el texto sale
    # más ancho y el error se ACUMULA: la primera letra cae bien y la última
    # cae lejos. El porqué, en kerning.py.
    ajustes = [0.0] + [
        kern(nombres[i - 1], nombres[i]) * escala for i in range(1, len(nombres))
    ]

    # El ancho total se necesita ANTES de dibujar, porque `text-anchor` decide
    # dónde arranca la primera letra en función de cuánto mide todo junto.
    ancho = sum(glifos[n].width * escala + espaciado for n in nombres) + sum(ajustes)

    if anclaje == "middle":
        lapiz = x - ancho / 2
    elif anclaje == "end":
        lapiz = x - ancho
    else:
        lapiz = x

    partes = []
    caja = [10 ** 9, 10 ** 9, -10 ** 9, -10 ** 9]

    for nombre, ajuste in zip(nombres, ajustes):
        lapiz += ajuste
        glifo = glifos[nombre]
        pluma = SVGPathPen(glifos)

        # La misma transformación, pero midiendo en vez de dibujar: así se sabe
        # hasta dónde llega la TINTA, que no es lo mismo que hasta dónde llega
        # la caja de la letra.
        medidor = BoundsPen(glifos)
        glifo.draw(TransformPen(medidor, (escala, 0, 0, -escala, lapiz, y)))

        if medidor.bounds:
            x0, y0, x1, y1 = medidor.bounds
            caja[0] = min(caja[0], x0)
            caja[1] = min(caja[1], y0)
            caja[2] = max(caja[2], x1)
            caja[3] = max(caja[3], y1)

        # La transformación hace dos cosas de una: lleva las unidades de la
        # tipografía a las del dibujo, y DA VUELTA la `y`. En una tipografía la
        # `y` crece hacia arriba; en SVG crece hacia abajo.
        glifo.draw(TransformPen(pluma, (escala, 0, 0, -escala, lapiz, y)))

        trazo = pluma.getCommands()
        if trazo:
            partes.append(trazo)

        lapiz += glifo.width * escala + espaciado

    return " ".join(partes), (None if caja[2] < caja[0] else tuple(caja))


def caja_de_figuras(svg):
    """Los `<rect>` y `<circle>` que ya estaban en el archivo también son tinta.

    Un `<path>` escrito a mano NO se mide acá: calcular hasta dónde llega un
    arco es otro problema, y hacerlo mal recortaría el dibujo. Si aparece uno,
    el recorte se niega en vez de arriesgarse."""
    cajas = []

    for rect in re.finditer(r"<rect\b[^>]*/?>", svg, re.S):
        b = rect.group(0)
        x = float(atributo(b, "x", "0"))
        y = float(atributo(b, "y", "0"))
        cajas.append((x, y, x + float(atributo(b, "width", "0")), y + float(atributo(b, "height", "0"))))

    for circulo in re.finditer(r"<circle\b[^>]*/?>", svg, re.S):
        b = circulo.group(0)
        cx = float(atributo(b, "cx", "0"))
        cy = float(atributo(b, "cy", "0"))
        # el trazo se dibuja MONTADO sobre el radio: la mitad sobresale
        r = float(atributo(b, "r", "0")) + float(atributo(b, "stroke-width", "0")) / 2
        cajas.append((cx - r, cy - r, cx + r, cy + r))

    return cajas


def recortar(svg, cajas):
    """Deja el lienzo del tamaño exacto del dibujo.

    Por qué hace falta. La caja de este wordmark venía de una fila de CSS, y una
    línea de texto en CSS es más alta que sus letras: reserva lugar arriba para
    los acentos y abajo para las colas de la «p» y la «g». «CB» no tiene ni una
    ni otra, así que ese lugar queda VACÍO — y no en partes iguales. El archivo
    sale con aire invisible y asimétrico, y quien lo centre en un espacio lo va
    a ver corrido.

    No se mueve ni un número del dibujo: se cambia el `viewBox`, que es
    justamente el recorte con el que se mira el lienzo."""
    x0 = min(c[0] for c in cajas)
    y0 = min(c[1] for c in cajas)
    x1 = max(c[2] for c in cajas)
    y1 = max(c[3] for c in cajas)
    ancho, alto = x1 - x0, y1 - y0

    svg = re.sub(
        r'viewBox="[^"]*"',
        f'viewBox="{x0:.4f} {y0:.4f} {ancho:.4f} {alto:.4f}"',
        svg,
        count=1,
    )
    svg = re.sub(r'width="[^"]*"', f'width="{ancho:.4f}"', svg, count=1)
    svg = re.sub(r'height="[^"]*"', f'height="{alto:.4f}"', svg, count=1)

    print(f"  recortado a la tinta: {ancho:.4f} x {alto:.4f}")
    return svg


def convertir(entrada, salida, recorte=False):
    svg = Path(entrada).read_text()
    convertidos = 0
    cajas = []

    for bloque in re.findall(r"<text\b.*?</text>", svg, re.S):
        contenido = re.search(r">([^<]*)</text>", bloque, re.S).group(1).strip()
        tamano = float(atributo(bloque, "font-size"))
        familia = familia_de(atributo(bloque, "font-family"))

        d, caja = contornos(
            texto=contenido,
            familia=familia,
            tamano=tamano,
            espaciado=a_pixeles(atributo(bloque, "letter-spacing"), tamano),
            x=float(atributo(bloque, "x", "0")),
            y=float(atributo(bloque, "y", "0")),
            anclaje=atributo(bloque, "text-anchor", "start"),
        )

        reemplazo = (
            f"<!-- «{contenido}» — {familia} {tamano:g}, ya en contornos. -->\n"
            f"  <path\n"
            f'    d="{d}"\n'
            f'    fill="{atributo(bloque, "fill", "#000000")}"\n'
            f"  />"
        )

        svg = svg.replace(bloque, reemplazo)
        convertidos += 1

        if caja:
            cajas.append(caja)

    if recorte:
        if re.search(r"<path\b", Path(entrada).read_text()):
            raise SystemExit(
                "este SVG trae un <path> escrito a mano y no sé hasta dónde llega: "
                "no lo recorto. Medir un arco es otro problema, y recortar de más "
                "corta el dibujo."
            )
        svg = recortar(svg, cajas + caja_de_figuras(svg))

    # El archivo de entrada avisa que su texto TODAVÍA es texto. En la salida
    # eso ya no es cierto, y un aviso vencido miente igual que un dato falso.
    aviso_viejo = re.search(r"  ⚠ EL TEXTO TODAVÍA ES TEXTO.*?licencia OFL\.", svg, re.S)

    if aviso_viejo:
        svg = svg.replace(aviso_viejo.group(0), AVISO_NUEVO.strip("\n"))

    Path(salida).write_text(svg)
    print(f"{entrada} → {salida}   ({convertidos} textos pasados a contornos)")

    if "<text" in Path(salida).read_text():
        raise SystemExit("QUEDÓ un <text> sin convertir: revisar")


if __name__ == "__main__":
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]

    if len(argumentos) != 2:
        raise SystemExit(__doc__)

    convertir(argumentos[0], argumentos[1], recorte="--recortar" in sys.argv)
