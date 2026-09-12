#!/usr/bin/env python3
"""Prepara la maqueta para publicarla como artefacto y verla en el teléfono.

El tablero que vive en el repo NO se puede publicar tal cual, y no es un
detalle de formato: son tres cosas que un archivo local hace y una página
publicada no puede hacer.

  1. Las fotos se enlazan por RUTA RELATIVA (`../../fotos/…`). Publicada, esa
     carpeta no existe y las imágenes no cargan. Acá van embebidas.
  2. El ancho está CLAVADO en 390 px porque así se mide. En un teléfono real,
     un ancho fijo mayor que la pantalla obliga a arrastrar la página de
     costado.
  3. No lleva ningún aviso. Los testimonios son inventados y las fotos son de
     banco: publicados al lado del nombre y la matrícula de una persona real,
     se leen como ciertos.

    uso:  python3 tools/armar-artefacto.py [salida.html]
"""

import base64
import pathlib
import sys


RAIZ = pathlib.Path(__file__).resolve().parent.parent

ORIGEN = RAIZ / "brand" / "tableros" / "15-pagina" / "390-solo.html"

# Cada foto con su tipo: el `data:` lleva el tipo adentro y un PNG anunciado
# como JPEG no se dibuja.
FOTOS = (
    ("hero-ejemplo.jpg", "jpeg"),
    ("nosotros-ejemplo.jpg", "jpeg"),
    ("iconos-del-brief.png", "png"),
)

AVISO = """
<div class="aviso-maqueta">
  <b>MAQUETA EN CONSTRUCCIÓN.</b> Los testimonios y las fotos son de ejemplo
  y no se publican. El texto lo tiene que aprobar Cecilia.
</div>
"""

CSS_AVISO = """
.aviso-maqueta {
  background: var(--grafito);
  color: var(--marfil);
  font-size: var(--tipo-chico);
  line-height: var(--alto-chico);
  padding: 10px var(--margen-pagina);
}
.aviso-maqueta b { color: #FFFFFF; }
"""


def embeber_fotos(texto):
    """Mete cada foto adentro del archivo como data URI."""
    for nombre, tipo in FOTOS:
        crudo = (RAIZ / "brand" / "fotos" / nombre).read_bytes()
        dato = (
            f"data:image/{tipo};base64,"
            + base64.b64encode(crudo).decode("ascii")
        )
        texto = texto.replace(f"../../fotos/{nombre}", dato)

    return texto


def soltar_el_ancho(texto):
    """El ancho deja de estar clavado y pasa a ser un techo."""
    return texto.replace(
        "  width: 390px;",
        "  width: 100%;\n  max-width: 390px;\n  margin: 0 auto;",
        1,
    )


def limpiar_cabecera(texto):
    """El envoltorio de la publicación pone su propia cabecera."""
    texto = texto.replace('<!-- @dsCard group="Components" -->\n', "")
    texto = texto.replace('<meta charset="utf-8">\n', "")

    return texto.replace(
        "<title>CB · La página entera · 390</title>",
        "<title>CB Odontología y Estética</title>",
    )


def poner_el_aviso(texto):
    """La franja que dice que esto es una maqueta."""
    texto = texto.replace("</style>", CSS_AVISO + "</style>", 1)

    return texto.replace(
        '<div class="pagina',
        AVISO + '<div class="pagina',
        1,
    )


def main():
    if not ORIGEN.exists():
        print(f"✗ falta {ORIGEN.relative_to(RAIZ)}: corré antes el generador")
        return 1

    destino = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else (
        RAIZ / "brand" / "tableros" / "15-pagina" / "artefacto.html"
    )

    texto = ORIGEN.read_text(encoding="utf-8")
    texto = embeber_fotos(texto)
    texto = soltar_el_ancho(texto)
    texto = limpiar_cabecera(texto)
    texto = poner_el_aviso(texto)

    destino.write_text(texto, encoding="utf-8")

    quedaron = texto.count("../../fotos/")

    print(f"✓ {destino}  ({len(texto) / 1024:.0f} KB)")
    print(f"{'✓' if quedaron == 0 else '✗'} rutas relativas sin embeber: {quedaron}")

    return 0 if quedaron == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
