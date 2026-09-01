"""Arma la versión TODA BLANCA del logo, la que va sobre fondo oscuro o sobre una foto.

No es un extra: es una de las dos versiones que cualquier entrega profesional
da por obligatorias, junto con la de color. Acá pesa más que en otros
proyectos, porque **el emblema dorado desaparece sobre el grafito de la marca**
—está medido en el doc de estado— y las placas de señalética del brief son
claras.

    python3 version_blanca.py <entrada.svg> <salida.svg>          pinta todo de blanco
    python3 version_blanca.py --calar <archivo-en-curvas.svg>     CALA las letras

⚠ EL CALADO ES PARA LA SUBMARCA Y HACE FALTA, no es un adorno: si el disco y
las letras quedan los dos blancos, la pieza es un círculo blanco liso. Calar
significa **agujerear** el disco con la forma de las letras, para que por ahí
se vea el fondo que haya atrás. Se hace uniendo el disco y las letras en UN
solo camino y declarando `fill-rule="evenodd"`: esa regla dice que donde dos
contornos se superponen, no se pinta.

Se corre DESPUÉS de pasar a curvas, porque hasta que las letras no son
contornos no hay nada que unir.
"""

import re
import sys
from pathlib import Path

BLANCO = "#FFFFFF"


def a_blanco(entrada, salida):
    svg = Path(entrada).read_text()
    # todo lo que sea un color se vuelve blanco; `none` no es un color
    svg = re.sub(r'(fill|stroke)="#[0-9A-Fa-f]{6}"', rf'\1="{BLANCO}"', svg)
    Path(salida).write_text(svg)
    print(f"{entrada} → {salida}   (todo en blanco)")


def circulo_a_camino(bloque):
    """Un `<circle>` escrito como camino: dos medias vueltas.

    Hace falta porque para calar hay que UNIR el disco con las letras en un
    solo camino, y un `<circle>` no se puede unir con nada: es una figura
    aparte."""
    cx = float(re.search(r'cx="([\d.]+)"', bloque).group(1))
    cy = float(re.search(r'cy="([\d.]+)"', bloque).group(1))
    r = float(re.search(r'r="([\d.]+)"', bloque).group(1))

    return (
        f"M{cx - r} {cy} "
        f"A{r} {r} 0 1 0 {cx + r} {cy} "
        f"A{r} {r} 0 1 0 {cx - r} {cy} Z"
    )


def calar(archivo):
    svg = Path(archivo).read_text()

    circulo = re.search(r"<circle\b[^>]*/>", svg, re.S)
    letras = re.search(r'<path\s+d="([^"]+)"\s+fill="[^"]*"\s*/>', svg, re.S)

    if not circulo or not letras:
        raise SystemExit("esperaba un <circle> y un <path> de letras, y no los encontré")

    unido = (
        "<!-- El disco y las letras, en UN solo camino. `evenodd` deja las\n"
        "       letras como AGUJEROS: por ahí se ve el fondo que haya atrás. -->\n"
        "  <path\n"
        f'    d="{circulo_a_camino(circulo.group(0))} {letras.group(1)}"\n'
        f'    fill="{BLANCO}"\n'
        '    fill-rule="evenodd"\n'
        "  />"
    )

    svg = svg.replace(circulo.group(0), unido)
    svg = svg.replace(letras.group(0), "")
    Path(archivo).write_text(svg)
    print(f"{archivo}   (letras caladas)")


if __name__ == "__main__":
    if "--calar" in sys.argv:
        calar([a for a in sys.argv[1:] if not a.startswith("--")][0])
    elif len(sys.argv) == 3:
        a_blanco(sys.argv[1], sys.argv[2])
    else:
        raise SystemExit(__doc__)
