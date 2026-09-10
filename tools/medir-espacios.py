#!/usr/bin/env python3
"""Mide TODOS los huecos verticales de una pieza de cartelería.

Por qué existe. `medir-jerarquia.py` mira la proximidad de UN grupo contra su
vecino, y sólo entre textos. Acá hace falta lo otro: la lista completa de
huecos de una pieza, incluidos el logo, el filete y el QR, para poder ver de
un vistazo si el aire agrupa lo que tiene que agrupar.

🔑 LA REGLA QUE SE CHEQUEA, y es una sola: el hueco que SEPARA dos grupos
tiene que ser claramente mayor que el mayor hueco de ADENTRO de cualquiera de
los dos. Si no, lo que se ve junto no es lo que está junto (Gestalt).

⚠ LO QUE ESTA HERRAMIENTA NO PUEDE DECIR: cuáles elementos forman un grupo.
Eso es una decisión de contenido —el teléfono y la dirección son el mismo dato
aunque el CSS no lo sepa—. La herramienta ordena los hechos; agrupar lo
decide una persona.

    uso:  python3 tools/medir-espacios.py brand/carteleria/cartel-500x320.svg
"""

import pathlib
import re
import subprocess
import sys
import tempfile


CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# La sonda corre DENTRO del archivo: pide el recuadro real de cada elemento
# dibujado, que es lo único que sabe dónde terminó el texto después de
# aplicarle la tipografía. Un número calculado desde el CSS no lo sabe.
SONDA = """
<script><![CDATA[
window.addEventListener("load", function () {
  var filas = [];
  var raiz = document.documentElement;
  var caja_raiz = raiz.getBoundingClientRect();

  // Se mide en PÍXELES de pantalla y se convierte a milímetros con la
  // escala real del dibujo. getBBox() no sirve para un grupo: devuelve
  // coordenadas locales, SIN el transform que lo posiciona — el logo y el QR
  // salían los dos arriba de todo.
  var por_mm = caja_raiz.height / raiz.viewBox.baseVal.height;

  function anotar(nombre, elemento) {
    var caja = elemento.getBoundingClientRect();

    if (caja.height <= 0) {
      return;
    }

    var arriba = (caja.top - caja_raiz.top) / por_mm;
    var abajo = (caja.bottom - caja_raiz.top) / por_mm;
    filas.push(nombre + "|" + arriba.toFixed(1) + "|" + abajo.toFixed(1));
  }

  document.querySelectorAll("text").forEach(function (elemento) {
    anotar(elemento.textContent.trim().slice(0, 26), elemento);
  });

  // Sólo los hijos DIRECTOS: adentro del QR hay un rect por módulo, y son
  // cientos. Contarlos no dice nada de los espacios de la pieza.
  document.querySelectorAll("svg > rect").forEach(function (elemento) {
    if (elemento.getBBox().width < raiz.viewBox.baseVal.width * 0.98) {
      anotar("[filete]", elemento);
    }
  });

  document.querySelectorAll("svg > g").forEach(function (elemento) {
    anotar(elemento.querySelector("rect") ? "[QR]" : "[logo]", elemento);
  });

  var marca = document.createElementNS("http://www.w3.org/2000/svg", "desc");
  marca.setAttribute("id", "medida");
  marca.textContent = filas.join(" ;; ");
  document.documentElement.appendChild(marca);
});
]]></script>
"""


def medir(ruta):
    """Devuelve los elementos de la pieza, ordenados de arriba abajo."""
    svg = ruta.read_text(encoding="utf-8")

    with tempfile.NamedTemporaryFile(
        "w", suffix=".svg", delete=False, dir=ruta.parent, encoding="utf-8"
    ) as copia:
        copia.write(svg.replace("</svg>", SONDA + "</svg>"))
        temporal = pathlib.Path(copia.name)

    try:
        salida = subprocess.run(
            [
                CHROME,
                "--headless",
                "--disable-gpu",
                "--virtual-time-budget=3000",
                "--dump-dom",
                f"file://{temporal}",
            ],
            capture_output=True,
            text=True,
        )
    finally:
        temporal.unlink()

    encontrado = re.search(
        r'id="medida"[^>]*>(.*?)</desc>', salida.stdout, re.DOTALL
    )

    if not encontrado:
        raise SystemExit("✗ la sonda no devolvió nada: ¿el archivo abre?")

    import html

    elementos = []

    for fila in html.unescape(encontrado.group(1)).split(" ;; "):
        nombre, arriba, abajo = fila.rsplit("|", 2)
        elementos.append((nombre, float(arriba), float(abajo)))

    elementos.sort(key=lambda e: e[1])

    return elementos


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)

    ruta = pathlib.Path(sys.argv[1]).resolve()
    elementos = medir(ruta)

    print(f"{ruta.name} · {len(elementos)} elementos dibujados\n")
    print(f"{'elemento':30} {'arriba':>8} {'abajo':>8} {'hueco':>8}")

    huecos = []
    anterior = None

    for nombre, arriba, abajo in elementos:
        hueco = "" if anterior is None else f"{arriba - anterior:.1f}"

        if anterior is not None:
            huecos.append((arriba - anterior, nombre))

        print(f"{nombre[:30]:30} {arriba:8.1f} {abajo:8.1f} {hueco:>8}")
        anterior = abajo

    if not huecos:
        return 0

    print()
    mayor, donde = max(huecos)
    print(f"· el hueco más grande son {mayor:.1f} mm, antes de «{donde[:30]}»")
    print("· ése tiene que ser el que separa un grupo del otro.")
    print(
        "  ⚠ Un hueco NEGATIVO no es un error: los recuadros de dos renglones "
        "seguidos se solapan\n    porque incluyen ascendentes y descendentes "
        "que el texto no usa."
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
