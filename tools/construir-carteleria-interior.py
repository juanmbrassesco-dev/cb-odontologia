#!/usr/bin/env python3
"""Arma la CARTELERÍA DE INTERIOR del consultorio, a tamaño real.

QUÉ ES ESTA PIEZA, y no es la de `construir-carteleria.py`. Aquélla es la placa
de ENTRADA: se lee desde la vereda, lleva el wordmark y el QR, y su función es
que el que pasa confirme que el consultorio es ahí. Éstas son las placas de
ADENTRO: el paciente YA entró, ya sabe dónde está, y lo único que necesita es
saber por qué puerta pasar. Orientan, no identifican.

⇒ POR ESO NO LLEVAN LOGO. La marca va en el umbral, no en cada puerta. A 160 mm
  de placa, con un número de 74 mm, un wordmark quedaría de ~20 mm: ilegible y
  compitiendo con lo único que importa. Es la misma lógica que ya sacó la
  matrícula de la placa de entrada —la pieza identifica al LUGAR, no a alguien—.

EL COLOR, y está medido, no elegido. Con `tools/medir-contraste.py`:
    grafito sobre blanco   12,82 : 1
    dorado  sobre blanco    3,09 : 1
La señalética pide 65-70 % de contraste. El dorado no llega como TINTA, así que
la tinta es grafito y el dorado queda de FILETE y de MARCO — que es el rol que
la paleta ya le daba: acento, línea, borde.

EL MARCO SÍ VA, y esto corrige una lectura anterior. La placa de entrada usa el
dorado como filete horizontal, y de esa única pieza se dedujo que la marca "no
usa marcos". Una pieza no hace un sistema. Un cartel de pared necesita el marco
por una razón física que la placa de entrada no tiene: va contra una pared
clara, y sin borde el blanco de la placa se come el canto y las letras quedan
flotando. El marco tampoco rompe nada — un marco también es una línea.

EL 3 DE MARCELLUS CUELGA, y por eso acá no se centra por la línea base. Marcellus
dibuja cifras semi-antiguas: el 1 y el 2 apoyan en la línea base y el 3 la pasa
de largo. Medido sobre la placa armada: la mancha del 3 mide 160 px contra 130 y
132 del 1 y el 2. Si los tres se centran por la línea base, el 3 se ve hundido.
Acá cada cifra se centra POR SU PROPIO CONTORNO —se le pregunta a la fuente
dónde empieza y dónde termina la tinta— así que el ajuste no es un número mágico
metido a mano: sale de la fuente y seguiría estando bien si mañana cambia el
cuerpo o el número.

    uso:  /opt/homebrew/opt/fonttools/libexec/bin/python3 \
              tools/construir-carteleria-interior.py

    (con ese intérprete y no con `python3` a secas: Homebrew guarda fontTools
     adentro de su propio entorno, igual que para `tools/print-pack/`.)
"""

import pathlib
import re
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "brand" / "carteleria-interior"
PRINT_PACK = RAIZ / "tools" / "print-pack"
FUENTE_ARCHIVO = RAIZ / "brand" / "fonts" / "Marcellus-Regular.ttf"

PYTHON_FONTTOOLS = "/opt/homebrew/opt/fonttools/libexec/bin/python3"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# Los colores salen de la paleta (css/tokens.css), no se inventan acá.
GRAFITO = "#33322F"
DORADO = "#B08D57"
BLANCO = "#FFFFFF"

# ---- LA GEOMETRÍA, toda en MILÍMETROS ----
# El viewBox del SVG se declara en las mismas unidades, así que 1 unidad = 1 mm
# y lo que se lee acá es lo que mide la pieza en la pared.

ANCHO = 160.0          # un solo ancho para las cinco piezas
ALTO_CUADRADA = 160.0  # consultorio
ALTO_ANCHA = 60.0      # baño y salida

MARCO_MARGEN = 9.0     # del borde de la placa al marco
MARCO_RADIO = 9.0
MARCO_TRAZO = 1.2

ROTULO_CUERPO = 10.8   # "CONSULTORIO"
ROTULO_TRACKING = 0.16  # en em
ROTULO_DESDE_ARRIBA = 27.0  # del borde de la placa al techo de las letras

FILETE_AIRE = 6.8      # del pie del rótulo al filete
FILETE_ANCHO = 0.74    # proporción del ancho interior del marco
FILETE_TRAZO = 0.8

NUMERO_CUERPO = 74.0
PALABRA_CUERPO = 21.0  # "BAÑO" y "SALIDA"
PALABRA_TRACKING = 0.16

PIEZAS = [
    ("consultorio-1", "1"),
    ("consultorio-2", "2"),
    ("consultorio-3", "3"),
    ("bano", "BAÑO"),
    ("salida", "SALIDA"),
]


# ---------------------------------------------------------------------------
# MEDIR LA TINTA
# ---------------------------------------------------------------------------

_fuente = None


def fuente():
    """Abre Marcellus una sola vez y la deja lista para que la midan."""
    global _fuente

    if _fuente is None:
        from fontTools.ttLib import TTFont
        _fuente = TTFont(FUENTE_ARCHIVO)

    return _fuente


def contorno_de(texto, cuerpo):
    """Dónde empieza y dónde termina la TINTA de este texto, en milímetros.

    Devuelve (techo, piso) medidos desde la línea base y hacia arriba: el techo
    es positivo y el piso es negativo cuando la letra baja de la línea —que es
    exactamente lo que hace el 3 de Marcellus—.

    No mide la caja de la tipografía (que es siempre la misma para todas las
    letras) sino el dibujo real, que es lo que el ojo ve.
    """
    from fontTools.pens.boundsPen import BoundsPen

    tipografia = fuente()
    upem = tipografia["head"].unitsPerEm
    escala = cuerpo / upem
    mapa = tipografia.getBestCmap()
    glifos = tipografia.getGlyphSet()

    techo = None
    piso = None

    for caracter in texto:
        if caracter == " ":
            continue

        nombre = mapa.get(ord(caracter))

        if nombre is None:
            raise SystemExit(f"Marcellus no tiene el glifo «{caracter}»")

        medidor = BoundsPen(glifos)
        glifos[nombre].draw(medidor)

        if medidor.bounds is None:
            continue

        _, abajo, _, arriba = medidor.bounds

        techo = arriba if techo is None else max(techo, arriba)
        piso = abajo if piso is None else min(piso, abajo)

    return techo * escala, piso * escala


def base_para_centrar(texto, cuerpo, centro):
    """La línea base que deja la MANCHA del texto centrada en `centro`.

    Acá está el arreglo del 3. Centrar por la línea base pondría las tres cifras
    a la misma altura de apoyo y dejaría al 3 colgando; centrar por la mancha
    las deja a las tres con el mismo peso arriba y abajo.
    """
    techo, piso = contorno_de(texto, cuerpo)
    medio_de_la_tinta = (techo + piso) / 2

    return centro + medio_de_la_tinta


# ---------------------------------------------------------------------------
# DIBUJAR
# ---------------------------------------------------------------------------

AVISO = """
  ⚠ EL TEXTO TODAVÍA ES TEXTO. Este archivo es el ORIGINAL EDITABLE y NO se
  entrega: pide Marcellus a quien lo abra, y una imprenta sin esa tipografía
  lo abre en Georgia sin avisar. El que se entrega es el `-curvas.svg` y su
  PDF. Marcellus se usa bajo licencia OFL.
"""


def cabecera(ancho, alto):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg"\n'
        f'     width="{ancho}mm"\n'
        f'     height="{alto}mm"\n'
        f'     viewBox="0 0 {ancho:g} {alto:g}">\n'
        f"<!--{AVISO}-->\n"
        f'  <rect x="0" y="0" width="{ancho:g}" height="{alto:g}" fill="{BLANCO}"/>\n'
    )


def marco(ancho, alto):
    lado = MARCO_MARGEN

    return (
        f'  <rect\n'
        f'    x="{lado:g}"\n'
        f'    y="{lado:g}"\n'
        f'    width="{ancho - lado * 2:g}"\n'
        f'    height="{alto - lado * 2:g}"\n'
        f'    rx="{MARCO_RADIO:g}"\n'
        f'    fill="none"\n'
        f'    stroke="{DORADO}"\n'
        f'    stroke-width="{MARCO_TRAZO:g}"\n'
        f'  />\n'
    )


def texto(contenido, cuerpo, tracking, y, ancho):
    return (
        f'  <text\n'
        f'    x="{ancho / 2:g}"\n'
        f'    y="{y:.4f}"\n'
        f'    font-family="Marcellus"\n'
        f'    font-size="{cuerpo:g}"\n'
        f'    letter-spacing="{tracking:g}em"\n'
        f'    text-anchor="middle"\n'
        f'    fill="{GRAFITO}"\n'
        f'  >{contenido}</text>\n'
    )


def filete(y, ancho):
    interior = ancho - MARCO_MARGEN * 2
    largo = interior * FILETE_ANCHO

    return (
        f'  <rect\n'
        f'    x="{(ancho - largo) / 2:g}"\n'
        f'    y="{y:.4f}"\n'
        f'    width="{largo:g}"\n'
        f'    height="{FILETE_TRAZO:g}"\n'
        f'    fill="{DORADO}"\n'
        f'  />\n'
    )


def placa_consultorio(numero):
    """La placa cuadrada: rótulo arriba, filete al medio, número abajo."""
    partes = [cabecera(ANCHO, ALTO_CUADRADA), marco(ANCHO, ALTO_CUADRADA)]

    # El rótulo se cuelga de su TECHO, no de la línea base: así "CONSULTORIO"
    # arranca siempre a 27 mm del borde, mida lo que mida la tipografía.
    techo_rotulo, piso_rotulo = contorno_de("CONSULTORIO", ROTULO_CUERPO)
    base_rotulo = ROTULO_DESDE_ARRIBA + techo_rotulo

    partes.append(texto("CONSULTORIO", ROTULO_CUERPO, ROTULO_TRACKING, base_rotulo, ANCHO))

    y_filete = base_rotulo - piso_rotulo + FILETE_AIRE

    partes.append(filete(y_filete, ANCHO))

    # La zona del número: del filete al borde interior del marco.
    borde_interior = ALTO_CUADRADA - MARCO_MARGEN - MARCO_TRAZO / 2
    centro = (y_filete + FILETE_TRAZO + borde_interior) / 2
    base_numero = base_para_centrar(numero, NUMERO_CUERPO, centro)

    partes.append(texto(numero, NUMERO_CUERPO, 0, base_numero, ANCHO))
    partes.append("</svg>\n")

    return "".join(partes)


def placa_palabra(palabra):
    """La placa ancha: una sola palabra, centrada en el marco."""
    partes = [cabecera(ANCHO, ALTO_ANCHA), marco(ANCHO, ALTO_ANCHA)]

    centro = ALTO_ANCHA / 2
    base = base_para_centrar(palabra, PALABRA_CUERPO, centro)

    partes.append(texto(palabra, PALABRA_CUERPO, PALABRA_TRACKING, base, ANCHO))
    partes.append("</svg>\n")

    return "".join(partes)


# ---------------------------------------------------------------------------
# LA CADENA DE PRODUCCIÓN — es la misma que la de la placa de entrada
# ---------------------------------------------------------------------------

def a_curvas(entrada, salida):
    """Cambia cada letra por su dibujo. Después de esto el archivo no nombra
    ninguna tipografía, que es lo que necesita una imprenta."""
    subprocess.run(
        [
            PYTHON_FONTTOOLS,
            str(PRINT_PACK / "svg_a_curvas.py"),
            str(entrada),
            str(salida),
        ],
        check=True,
        capture_output=True,
        cwd=PRINT_PACK,
    )


def envoltorio(nombre_svg, ancho, alto):
    """El HTML que Chrome imprime, para que el PDF salga con medida exacta.

    Es el mismo envoltorio que usa `construir-carteleria.py`: Chrome respeta
    `@page` al milímetro. ⚠ NO se usa `print-pack/svg_a_pdf.py` acá, aunque
    también haga PDF: ése lee el viewBox como PÍXELES a 96 por pulgada, que es
    lo correcto para el logo y da 42 mm para una placa de 160. Se probó, y por
    eso queda escrito.
    """
    return (
        f'<!doctype html>\n'
        f'<meta charset="utf-8">\n'
        f'<title>CB · {ancho:g} × {alto:g} mm</title>\n'
        f'<style>\n'
        f'  @page {{ size: {ancho:g}mm {alto:g}mm; margin: 0; }}\n'
        f'  html, body {{ margin: 0; padding: 0; }}\n'
        f'  img {{ display: block; width: {ancho:g}mm; height: {alto:g}mm; }}\n'
        f'</style>\n'
        f'<img src="{nombre_svg}" alt="">\n'
    )


def a_pdf(entrada, salida, ancho, alto):
    """Imprime el SVG a un PDF del tamaño físico exacto, y lo VERIFICA."""
    pagina = entrada.parent / f"_imprimir-{entrada.stem}.html"
    pagina.write_text(envoltorio(entrada.name, ancho, alto))

    subprocess.run(
        [
            CHROME,
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={salida}",
            f"file://{pagina}",
        ],
        check=True,
        capture_output=True,
    )

    pagina.unlink()
    verificar_medida(salida, ancho, alto)


def verificar_medida(pdf, ancho, alto):
    """Le pregunta al PDF cuánto mide y corta si no es lo pedido.

    Va acá y no en una revisión a ojo porque un PDF del tamaño equivocado se
    ABRE bien: no da error, se ve idéntico en pantalla y sale mal de imprenta.
    Ya pasó una vez con este mismo juego de piezas.
    """
    salida = subprocess.run(
        ["pdfinfo", str(pdf)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    medida = re.search(r"Page size:\s*([\d.]+) x ([\d.]+) pts", salida)

    if not medida:
        raise SystemExit(f"pdfinfo no devolvió el tamaño de {pdf.name}")

    ancho_real = float(medida.group(1)) / 72 * 25.4
    alto_real = float(medida.group(2)) / 72 * 25.4

    if abs(ancho_real - ancho) > 0.2 or abs(alto_real - alto) > 0.2:
        raise SystemExit(
            f"{pdf.name} mide {ancho_real:.2f} × {alto_real:.2f} mm "
            f"y tenía que medir {ancho:g} × {alto:g}"
        )


def vista_previa(archivos, salida):
    """Una sola imagen con las cinco piezas, para mirar. NO sirve para producir."""
    tarjetas = ""

    for nombre, svg in archivos:
        tarjetas += (
            f'<figure><img src="file://{svg}"><figcaption>{nombre}</figcaption></figure>\n'
        )

    html = f"""<!doctype html><meta charset="utf-8">
<style>
  body {{ margin:0; padding:38px; width:1060px; background:#FAF7F2;
          font-family:"Helvetica Neue", Arial, sans-serif; color:#33322F; }}
  h1 {{ font-size:19px; font-weight:600; letter-spacing:.06em; margin:0 0 4px; }}
  p.nota {{ font-size:14px; color:#464541; margin:0 0 26px; }}
  .grilla {{ display:flex; flex-wrap:wrap; gap:26px; align-items:flex-start; }}
  figure {{ margin:0; }}
  /* 1,8 px por mm: las cinco piezas comparten ancho fisico, asi que un
     solo ancho en pixeles las deja a todas a la misma escala. */
  img {{ display:block; width:288px; height:auto;
         box-shadow:0 1px 6px rgba(0,0,0,.14); }}
  figcaption {{ font-size:13px; color:#464541; margin-top:7px; letter-spacing:.04em; }}
</style>
<h1>CB Odontología — cartelería de interior</h1>
<p class="nota">Cinco piezas, un solo ancho de 160 mm. Vista al 1,8 px/mm: NO sirve para producir.</p>
<div class="grilla">
{tarjetas}</div>
"""
    pagina = SALIDA / "_vista-previa.html"
    pagina.write_text(html)

    subprocess.run(
        [
            CHROME,
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            "--force-device-scale-factor=1",
            "--window-size=1060,660",
            f"--screenshot={salida}",
            f"file://{pagina}",
        ],
        check=True,
        capture_output=True,
    )

    pagina.unlink()


def main():
    if not pathlib.Path(PYTHON_FONTTOOLS).exists():
        raise SystemExit(
            f"no encuentro el intérprete con fontTools en {PYTHON_FONTTOOLS}.\n"
            "Se instala con `brew install fonttools`."
        )

    SALIDA.mkdir(parents=True, exist_ok=True)
    entregables = []

    for nombre, contenido in PIEZAS:
        if nombre.startswith("consultorio"):
            svg = placa_consultorio(contenido)
            alto_pieza = ALTO_CUADRADA
        else:
            svg = placa_palabra(contenido)
            alto_pieza = ALTO_ANCHA

        medida = f"{ANCHO:g} × {alto_pieza:g} mm"

        original = SALIDA / f"{nombre}.svg"
        curvas = SALIDA / f"{nombre}-curvas.svg"
        pdf = SALIDA / f"{nombre}-curvas.pdf"

        original.write_text(svg)
        a_curvas(original, curvas)
        a_pdf(curvas, pdf, ANCHO, alto_pieza)

        entregables.append((f"{nombre} — {medida}", curvas))
        print(f"  ✅ {nombre:16s} {medida:18s} → svg + curvas + pdf")

    vista_previa(entregables, SALIDA / "_vista-previa.png")
    print(f"\n  📁 {SALIDA}")


if __name__ == "__main__":
    main()
