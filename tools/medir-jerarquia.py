#!/usr/bin/env python3
"""Mide la JERARQUÍA de un bloque maquetado.

Por qué existe. Los otros dos medidores atrapan lo que se puede mirar de a un
elemento por vez: `medir-contraste.py` dice si un par de colores se lee, y
`medir-alineacion.py` dice si cada bloque cae en una posición que el sistema
declara. Ninguno de los dos ve la RELACIÓN entre los elementos — cuál manda,
cuál acompaña — y ahí es donde se coló el error del 4-sep-2026: las tres
señales de «Nosotros», que son el contenido de menor rango de la sección,
llevaban una tarjeta blanca con filo dorado, que es el recurso más fuerte del
sistema. Lo cazó Juan mirando, no una herramienta.

Qué chequea, y cada regla tiene su fuente:

  1. CUÁNTOS TAMAÑOS DE LETRA. NN/g recomienda no pasar de tres por
     composición: más tamaños no es más jerarquía, es ruido.
  2. QUIÉN LLEVA SUPERFICIE. Un fondo propio, un filo o un radio son el recurso
     más caro que tiene el sistema. Se LISTAN, no se juzgan — y eso se corrigió
     el mismo día de escribir la herramienta: la primera versión reprobaba toda
     superficie que no estuviera en el texto más grande, y con esa regla
     reprobó las nueve tarjetas de tratamiento y las filas de contacto, que
     Juan ya había aprobado y están bien. En esas dos secciones la tarjeta ES
     el contenido; en «Nosotros» era el apoyo. La diferencia es de RANGO, y el
     rango no está en el CSS.
  3. GRIS SOBRE GRIS. Si el texto más grande usa el color más apagado, la
     jerarquía de color contradice a la de tamaño (Refactoring UI).
  4. PROXIMIDAD (Gestalt). Si el hueco DENTRO de un grupo es mayor o igual al
     que lo separa del grupo vecino, la agrupación miente: lo que se ve junto
     no es lo que está junto.

Lo que NO puede chequear, y hay que decirlo: el RANGO del contenido. Que un
párrafo sea "lo principal" es una decisión de producto, no un dato del CSS. La
herramienta muestra los hechos ordenados para que la inversión salte a la
vista; quien decide sigue siendo una persona.

    uso:  python3 tools/medir-jerarquia.py <archivo.html> [--selector .nosotros]
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


CHROME = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
)

# El script que corre DENTRO de la página. Chrome ejecuta el JavaScript antes
# de volcar el DOM, así que se deja el resultado en un <script type="text/x">
# y después se lo pesca con una expresión regular. Es el único camino sin
# instalar un navegador controlable.
SONDA = """
<script>
(function () {
  var raiz = document.querySelector("SELECTOR") || document.body;
  var fondo = getComputedStyle(document.body).backgroundColor;
  var salida = [];

  raiz.querySelectorAll("*").forEach(function (nodo) {
    var caja = nodo.getBoundingClientRect();

    if (caja.width === 0 || caja.height === 0) {
      return;
    }

    var estilo = getComputedStyle(nodo);
    var propio = (nodo.textContent || "").trim().slice(0, 40);

    salida.push({
      etiqueta: nodo.tagName.toLowerCase(),
      clase: nodo.className || "",
      padre: (nodo.parentElement && nodo.parentElement.className) || "",
      texto: propio,
      arriba: Math.round(caja.top),
      abajo: Math.round(caja.bottom),
      tamano: parseFloat(estilo.fontSize),
      peso: estilo.fontWeight,
      color: estilo.color,
      fondo: estilo.backgroundColor,
      borde: estilo.borderTopWidth + " " + estilo.borderLeftWidth,
      radio: estilo.borderTopLeftRadius,
      superficie: (
        estilo.backgroundColor !== fondo
        && estilo.backgroundColor !== "rgba(0, 0, 0, 0)"
      ) || parseFloat(estilo.borderTopWidth) > 0,
    });
  });

  var marca = document.createElement("script");
  marca.type = "text/medicion";
  marca.textContent = JSON.stringify({ fondo: fondo, nodos: salida });
  document.body.appendChild(marca);
})();
</script>
"""


def sondear(archivo, selector):
    """Abre la página en Chrome, le inyecta la sonda y recupera el JSON."""
    fuente = Path(archivo).read_text(encoding="utf-8")
    sonda = SONDA.replace("SELECTOR", selector)

    with tempfile.TemporaryDirectory() as carpeta:
        copia = Path(carpeta) / "medido.html"
        copia.write_text(fuente + sonda, encoding="utf-8")

        salida = subprocess.run(
            [
                CHROME,
                "--headless",
                "--disable-gpu",
                "--dump-dom",
                "--virtual-time-budget=2000",
                copia.as_uri(),
            ],
            capture_output=True,
            text=True,
        ).stdout

    hallado = re.search(
        r'<script type="text/medicion">(.*?)</script>',
        salida,
        re.S,
    )

    if not hallado:
        raise SystemExit("✗ no se pudo leer la medición: ¿existe el selector?")

    return json.loads(hallado.group(1))


def solo_texto(nodos):
    """Los nodos que llevan texto propio y no sólo envuelven a otros."""
    return [n for n in nodos if n["texto"]]


def revisar_tamanos(nodos):
    tamanos = sorted({n["tamano"] for n in solo_texto(nodos)}, reverse=True)
    linea = ", ".join(f"{t:g}px" for t in tamanos)

    if len(tamanos) > 3:
        return [f"✗ {len(tamanos)} tamaños de letra ({linea}) · el techo es 3"]

    return [f"✓ {len(tamanos)} tamaños de letra ({linea})"]


def revisar_superficies(nodos, ignorar=()):
    conmarco = [
        n
        for n in nodos
        if n["superficie"]
        and n["texto"]
        and not any(c and c in (n["clase"] or "") for c in ignorar)
    ]

    if not conmarco:
        return ["· ningún elemento lleva superficie propia"]

    mayor = max(n["tamano"] for n in solo_texto(nodos))
    avisos = []

    for n in conmarco:
        etiqueta = f"{n['etiqueta']}.{n['clase']}".strip(".")
        avisos.append(
            f"· superficie en «{n['texto'][:32]}» "
            f"({etiqueta}, {n['tamano']:g}px de {mayor:g}px máximo)"
        )

    avisos.append(
        "  ↳ ¿alguna de esas es contenido de APOYO? Entonces está invertida. "
        "Esto lo contesta una persona."
    )

    return avisos


def revisar_grises(nodos):
    """El texto más grande no puede ser el más apagado."""
    textos = solo_texto(nodos)

    if not textos:
        return []

    def luz(color):
        numeros = [int(x) for x in re.findall(r"\d+", color)[:3]]
        return sum(numeros) / 3 if numeros else 0

    grande = max(textos, key=lambda n: n["tamano"])
    apagado = max(textos, key=lambda n: luz(n["color"]))

    if grande is apagado and len({n["color"] for n in textos}) > 1:
        return ["✗ el texto más grande usa además el color más apagado"]

    return ["✓ el tamaño y el color no se contradicen"]


def revisar_proximidad(nodos, hermanos):
    """El hueco de adentro de un grupo tiene que ser menor que el de afuera."""
    grupo = [n for n in nodos if hermanos in (n["padre"] or "")]

    if len(grupo) < 2:
        return []

    grupo.sort(key=lambda n: n["arriba"])
    adentro = [
        grupo[i + 1]["arriba"] - grupo[i]["abajo"]
        for i in range(len(grupo) - 1)
    ]
    mayor_adentro = max(adentro)

    posteriores = [
        n["arriba"] - grupo[-1]["abajo"]
        for n in nodos
        if n["arriba"] >= grupo[-1]["abajo"] and n["texto"]
    ]
    afuera = min(posteriores) if posteriores else None

    if afuera is None:
        return [f"· hueco dentro del grupo: {mayor_adentro} px (no hay vecino)"]

    if afuera <= mayor_adentro:
        return [
            f"✗ el grupo no se lee como grupo: adentro {mayor_adentro} px, "
            f"contra el vecino {afuera} px"
        ]

    return [
        f"✓ el grupo se separa: adentro {mayor_adentro} px, "
        f"contra el vecino {afuera} px"
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archivo")
    parser.add_argument("--selector", default="body")
    parser.add_argument(
        "--ignorar",
        nargs="*",
        default=[],
        help="clases que NO son texto decorado (el hueco de una foto, p. ej.)",
    )
    parser.add_argument(
        "--grupo",
        default="",
        help="clase de los hermanos cuya proximidad se chequea",
    )
    args = parser.parse_args()

    if not Path(CHROME).exists():
        raise SystemExit("✗ no está Chrome donde se lo espera")

    medicion = sondear(args.archivo, args.selector)
    nodos = medicion["nodos"]

    print(f"{args.archivo} · {len(nodos)} elementos dibujados\n")

    avisos = []
    avisos += revisar_tamanos(nodos)
    avisos += revisar_grises(nodos)
    avisos += revisar_superficies(nodos, args.ignorar)

    if args.grupo:
        avisos += revisar_proximidad(nodos, args.grupo)

    for aviso in avisos:
        print(aviso)

    fallas = [a for a in avisos if a.startswith("✗")]
    print()

    if fallas:
        print(f"✗ {len(fallas)} señal(es) de jerarquía invertida.")
        return 1

    print("✓ ninguna señal de jerarquía invertida.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
