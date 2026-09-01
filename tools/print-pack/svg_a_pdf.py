"""Genera el PDF VECTORIAL de un SVG, con la página del tamaño EXACTO del dibujo.

Por qué PDF si ya hay SVG: porque es lo que una imprenta pide. Un SVG lo abre
un navegador y un programa de diseño; una imprenta trabaja con PDF, y encima
un PDF lleva el tamaño físico adentro, en milímetros, cosa que un SVG deja
librada a quien lo coloque.

⚠ POR QUÉ NO LO IMPRIME CHROME, que era lo primero que se probó: Chrome NO
entrega la página que se le pide. La lleva a una grilla propia y devuelve
hasta 0,7 px de más —o de menos, y de menos CORTA el dibujo—. La unidad no
cambia nada (se probó en pt, px, mm y pulgadas: las cuatro dan el mismo
número), pedir menos tampoco (190, 190,08, 190,16 y 190,32 devuelven las
cuatro 190,72), y el sobrante no se puede centrar desde el CSS porque la
página se maqueta con la medida PEDIDA y lo que sobra se agrega afuera de la
maquetación. **Que la herramienta que ya estaba a mano no pueda no es motivo
para entregar el trabajo torcido: se cambia la herramienta.**

`rsvg-convert` (librsvg) escribe la página con la medida exacta del SVG.
Se instala con `brew install librsvg`.

    python3 svg_a_pdf.py <entrada.svg> <salida.pdf>
    python3 svg_a_pdf.py <entrada.svg> <salida.eps> --eps

⚠ EL EPS ES PARA IMPRENTAS CON EQUIPOS VIEJOS, y se entrega por las dudas: el
formato está discontinuado hace años, pero sigue siendo lo primero que piden
algunos talleres. Lleva el mismo dibujo que el PDF.
"""

import re
import subprocess
import sys
from pathlib import Path

RSVG = "/opt/homebrew/bin/rsvg-convert"
POR_PULGADA = 96.0
MM_POR_PULGADA = 25.4


def medidas(svg):
    """El `viewBox` manda: es el sistema de coordenadas del dibujo."""
    caja = re.search(r'viewBox="([\d.\-\s]+)"', svg)

    if not caja:
        raise SystemExit("el SVG no declara viewBox: no sé de qué tamaño es")

    _, _, ancho, alto = [float(v) for v in caja.group(1).split()]
    return ancho, alto


def caja_del_pdf(ruta):
    """El tamaño real de la página, preguntado al propio PDF.

    Se lee con `pdfinfo` y no buscando `/MediaBox` a mano: librsvg guarda los
    objetos comprimidos, así que el rectángulo no está en el archivo como
    texto. ⚠ `pdfinfo` redondea a centésimas de punto, o sea 0,013 px: por eso
    la tolerancia de abajo no puede ser más fina que eso."""
    salida = subprocess.run(
        ["pdfinfo", str(Path(ruta).resolve())], check=True, capture_output=True, text=True
    ).stdout

    medida = re.search(r"Page size:\s*([\d.]+) x ([\d.]+) pts", salida)

    if not medida:
        raise SystemExit("pdfinfo no devolvió el tamaño de página")

    # el PDF mide en puntos: 72 por pulgada, contra los 96 px de la web
    return (
        float(medida.group(1)) / 72 * POR_PULGADA,
        float(medida.group(2)) / 72 * POR_PULGADA,
    )


def escribir_caja_fina(ruta, ancho_px, alto_px):
    """Le agrega al EPS el tamaño con decimales.

    Un EPS declara su tamaño en `%%BoundingBox`, y el formato obliga a que sean
    puntos ENTEROS: cairo redondea para afuera y deja hasta 1 punto (0,35 mm)
    de aire. El remedio está previsto en el propio formato: `%%HiResBoundingBox`
    admite decimales y es lo que mira el software moderno. Se agrega acá porque
    cairo no la escribe. Es una línea de comentario en un archivo de texto: no
    hay tabla de posiciones que se pueda romper, al revés que en un PDF."""
    texto = Path(ruta).read_text(errors="ignore")
    fina = f"%%HiResBoundingBox: 0 0 {ancho_px / POR_PULGADA * 72:.4f} {alto_px / POR_PULGADA * 72:.4f}"

    if "%%HiResBoundingBox" in texto:
        return

    texto = re.sub(r"(%%BoundingBox:[^\n]*\n)", rf"\1{fina}\n", texto, count=1)
    Path(ruta).write_text(texto)


def caja_del_eps(ruta):
    """El tamaño de un EPS lo declara su encabezado, en puntos.

    Se lee el `%%HiResBoundingBox`, que va con decimales; el `%%BoundingBox`
    de al lado está redondeado a puntos enteros y no sirve para verificar."""
    cabecera = Path(ruta).read_text(errors="ignore")[:4000]
    caja = re.search(
        r"%%HiResBoundingBox:\s*([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)\s+([\d.\-]+)", cabecera
    )

    if not caja:
        raise SystemExit("el EPS no declara HiResBoundingBox")

    x0, y0, x1, y1 = [float(v) for v in caja.groups()]
    return (x1 - x0) / 72 * POR_PULGADA, (y1 - y0) / 72 * POR_PULGADA


def a_pdf(entrada, salida, eps=False):
    svg = Path(entrada).read_text()

    if "<text" in svg:
        raise SystemExit(
            "este SVG todavía tiene texto: pasalo por svg_a_curvas.py primero.\n"
            "Un PDF con texto le pide la tipografía a quien lo abra, que es lo "
            "que el pack de imprenta existe para evitar."
        )

    ancho, alto = medidas(svg)

    subprocess.run(
        [
            RSVG,
            "--format=eps" if eps else "--format=pdf",
            f"--width={ancho}",
            f"--height={alto}",
            "--output", str(Path(salida).resolve()),
            str(Path(entrada).resolve()),
        ],
        check=True,
        capture_output=True,
    )

    if eps:
        escribir_caja_fina(salida, ancho, alto)

    real_ancho, real_alto = caja_del_eps(salida) if eps else caja_del_pdf(salida)
    desvio = max(abs(real_ancho - ancho), abs(real_alto - alto))

    print(
        f"{entrada} → {salida}   "
        f"({real_ancho:.4f} x {real_alto:.4f} px = "
        f"{real_ancho / POR_PULGADA * MM_POR_PULGADA:.3f} x "
        f"{real_alto / POR_PULGADA * MM_POR_PULGADA:.3f} mm"
        f"  ·  desvío {desvio:.4f} px)"
    )

    if desvio > 0.02:
        raise SystemExit(
            f"la página no salió del tamaño pedido (desvío {desvio:.4f} px). No se entrega así."
        )


if __name__ == "__main__":
    argumentos = [a for a in sys.argv[1:] if not a.startswith("--")]

    if len(argumentos) != 2:
        raise SystemExit(__doc__)

    a_pdf(argumentos[0], argumentos[1], eps="--eps" in sys.argv)
