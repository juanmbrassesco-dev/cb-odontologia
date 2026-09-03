"""Arma el pack de marca ENTERO, de una sola corrida.

Hasta el 2-sep-2026 esto era una lista de comandos en un README y había que
correrlos a mano, pieza por pieza y formato por formato. Con tres piezas ya era
tedioso; con la cuarta —la apilada— pasa a ser una fuente de errores: alcanza
con olvidarse de un `--recortar` para que un PDF salga con aire adentro y nadie
se entere hasta la imprenta.

    /opt/homebrew/opt/fonttools/libexec/bin/python3 tools/construir-pack.py

⚠ Se corre con el Python de fonttools, no con el `python3` suelto: el módulo
`fontTools` vive adentro del entorno que instaló Homebrew.

QUÉ HACE, en orden:

  1. Le pide a `tools/letras-cb` las cuatro piezas en color.
  2. Recorta el lienzo al dibujo, que es de dónde sale la medida del PDF.
  3. Arma la versión blanca de cada una (y CALA las letras de la submarca).
  4. Escribe PDF, EPS y los PNG de cada tamaño con su uso.

BORRA Y REESCRIBE `brand/logo/` entero. Todo eso está versionado en git, así
que si algo sale mal se vuelve con `git checkout brand/logo`.
"""

import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path( __file__ ).resolve().parent.parent
LETRAS = RAIZ / "tools" / "letras-cb"
PRINT_PACK = RAIZ / "tools" / "print-pack"
SALIDA = LETRAS / "salida"
DESTINO = RAIZ / "brand" / "logo"

PYTHON = sys.executable


# Los PNG están nombrados por su ancho en píxeles porque un archivo de pantalla
# se mide en píxeles y no en milímetros. Cada uno tiene un uso y por eso existe:
# ninguno está "por las dudas".
PNGS = [
    # pieza        ancho  sufijo          fondo marfil
    ( "submarca",     32, "",             False ),   # favicon
    ( "submarca",    180, "",             False ),   # ícono al guardar en un iPhone
    ( "submarca",    640, "-avatar",      True  ),   # perfil de WhatsApp
    ( "submarca",   1000, "-avatar",      True  ),   # perfil de Instagram
    ( "wordmark",    600, "",             False ),   # firma de correo, documentos
    ( "wordmark",   1200, "",             False ),   # encabezado del sitio
    ( "wordmark",   1200, "-marfil",      True  ),   # el mismo, sobre fondo opaco
    ( "wordmark",   2400, "",             False ),   # el mismo, a doble densidad
    ( "apilado",     600, "",             False ),   # encabezado del celular
    ( "apilado",    1200, "",             False ),   # el mismo, a doble densidad
    ( "emblema",     512, "",             False ),   # posteos de redes
    ( "emblema",    1024, "",             False ),
]

# Las versiones blancas van sobre fondo oscuro o sobre una foto. No son
# opcionales: el emblema dorado sobre el grafito de la marca DESAPARECE, y eso
# está medido, no supuesto.
PNGS_BLANCOS = [
    ( "submarca",  1000 ),
    ( "wordmark",  1200 ),
    ( "apilado",   1200 ),
    ( "emblema",   1024 ),
]

# 🔴 LAS FOTOS DE PERFIL SE MUESTRAN RECORTADAS EN CÍRCULO, no en cuadrado. Por
# eso estas piezas NO salen del dibujo pelado como el resto de los PNG: pasan
# antes por `lienzo_cuadrado.py`, que las centra en un cuadrado con el aire que
# manda el manual medido contra la circunferencia. El porqué está allá.
#
# La submarca no está acá y no es un olvido: ya es un disco de 1 a 1, llena el
# círculo sola y no hay nada que acomodar. Las que necesitan lienzo son las
# piezas ANCHAS, que metidas en un círculo pierden las puntas.
PNGS_AVATAR = [
    # pieza      aire   anchos
    ( "apilado", 0.215, [ 640, 1000 ] ),   # perfil de WhatsApp · de Instagram
]

PIEZAS = [ "wordmark", "apilado", "emblema", "submarca" ]


# Cada archivo entregado se abre con esto. No es decoración: es lo único que ve
# el que abre el SVG suelto, y lo que le dice que NO lo edite a mano. La primera
# corrida de este guión se los llevó puestos porque los escribía el camino viejo
# — se recuperan acá, que es donde nacen los archivos.
ENCABEZADOS = {
    "wordmark": "Wordmark (versión principal)",
    "apilado":  "Wordmark apilado — la misma información, para cuando el ancho aprieta",
    "emblema":  "Emblema (versión secundaria)",
    "submarca": "Submarca / ícono",
}


def con_encabezado( pieza, svg ):
    return (
        f"<!--\n"
        f"  { ENCABEZADOS[ pieza ] } — CB Odontología y Estética.\n"
        f"\n"
        f"  Las letras ya están en CONTORNOS: este archivo no depende de ninguna\n"
        f"  tipografía instalada.\n"
        f"\n"
        f"  ⚠ NO SE EDITA A MANO. La fuente son los dos archivos de `tools/letras-cb/`\n"
        f"  más los guiones que componen las piezas; para cambiar algo se toca eso y\n"
        f"  se vuelve a correr `tools/construir-pack.py`.\n"
        f"-->\n"
    ) + svg


def correr( guion, *args ):
    orden = [ PYTHON, str( PRINT_PACK / guion ), *[ str( a ) for a in args ] ]
    hecho = subprocess.run( orden, capture_output = True, text = True )

    if hecho.returncode != 0:
        print( hecho.stdout )
        print( hecho.stderr )
        raise SystemExit( f"falló {guion} con {args}" )

    return hecho.stdout.strip()


def escribir_las_piezas():
    """Le pide a `letras-cb` las cuatro piezas en color, sin recortar todavía."""
    sys.path.insert( 0, str( LETRAS ) )
    import piezas as P
    import componer as C

    SALIDA.mkdir( exist_ok = True )

    wordmark, ancho = P.wordmark()
    apilado, alto = P.apilado()

    ( SALIDA / "cb-wordmark.svg" ).write_text( con_encabezado( "wordmark", wordmark ) )
    ( SALIDA / "cb-apilado.svg" ).write_text( con_encabezado( "apilado", apilado ) )
    ( SALIDA / "cb-emblema.svg" ).write_text( con_encabezado( "emblema", P.emblema() ) )
    ( SALIDA / "cb-submarca.svg" ).write_text( con_encabezado( "submarca", C.submarca() ) )

    print( f"  wordmark  {ancho:.2f} de ancho" )
    print( f"  apilado   {alto:.2f} de alto" )
    print( "  emblema, submarca" )


def main():
    print( "① las cuatro piezas, desde el generador" )
    escribir_las_piezas()

    print( "\n② el lienzo, recortado al dibujo" )
    curvas = DESTINO / "curvas"
    shutil.rmtree( curvas, ignore_errors = True )
    curvas.mkdir( parents = True )

    for pieza in PIEZAS:
        # Las piezas salen del generador YA en <path>, así que no hay texto que
        # convertir: lo único que falta es sacarles el aire del lienzo, y eso se
        # MIDE. El porqué, en el encabezado de `recortar_lienzo.py`.
        print( "  " + correr(
            "recortar_lienzo.py",
            SALIDA / f"cb-{pieza}.svg",
            curvas / f"cb-{pieza}-curvas.svg",
        ) )

    print( "\n③ las versiones blancas" )
    for pieza in PIEZAS:
        blanca = curvas / f"cb-{pieza}-blanco-curvas.svg"
        correr( "version_blanca.py", curvas / f"cb-{pieza}-curvas.svg", blanca )

        # En la submarca las letras se CALAN en vez de pintarse de blanco: si se
        # pintaran, la pieza sería un disco liso — el disco ya es blanco.
        if pieza == "submarca":
            correr( "version_blanca.py", "--calar", blanca )

        print( f"  cb-{pieza}-blanco-curvas.svg" )

    print( "\n④ PDF y EPS" )
    for carpeta, extra in ( ( "pdf", [] ), ( "eps", [ "--eps" ] ) ):
        destino = DESTINO / carpeta
        shutil.rmtree( destino, ignore_errors = True )
        destino.mkdir( parents = True )

        for pieza in PIEZAS:
            for variante in ( "", "-blanco" ):
                nombre = f"cb-{pieza}{variante}"
                correr(
                    "svg_a_pdf.py",
                    curvas / f"{nombre}-curvas.svg",
                    destino / f"{nombre}.{carpeta}",
                    *extra,
                )
        print( f"  {carpeta}/ — {len( PIEZAS ) * 2} archivos" )

    print( "\n⑤ los PNG" )
    pngs = DESTINO / "png"
    shutil.rmtree( pngs, ignore_errors = True )
    pngs.mkdir( parents = True )

    for pieza, ancho, sufijo, fondo in PNGS:
        salida = pngs / f"cb-{pieza}-{ancho}{sufijo}.png"
        extra = [ "--fondo" ] if fondo else []
        correr(
            "svg_a_png.py",
            curvas / f"cb-{pieza}-curvas.svg",
            salida,
            "--ancho", ancho,
            *extra,
        )
        print( f"  {salida.name}" )

    for pieza, ancho in PNGS_BLANCOS:
        salida = pngs / f"cb-{pieza}-{ancho}-blanco.png"
        correr(
            "svg_a_png.py",
            curvas / f"cb-{pieza}-blanco-curvas.svg",
            salida,
            "--ancho", ancho,
        )
        print( f"  {salida.name}" )

    for pieza, aire, anchos in PNGS_AVATAR:
        # el lienzo cuadrado se arma UNA vez y de ahí salen todos sus tamaños
        cuadrado = SALIDA / f"cb-{pieza}-cuadrado.svg"
        correr(
            "lienzo_cuadrado.py",
            curvas / f"cb-{pieza}-curvas.svg",
            cuadrado,
            "--aire", aire,
        )

        for ancho in anchos:
            salida = pngs / f"cb-{pieza}-{ancho}-avatar.png"
            correr(
                "svg_a_png.py",
                cuadrado,
                salida,
                "--ancho", ancho,
                "--fondo",
            )
            print( f"  {salida.name}" )

    cuenta = sum( 1 for _ in DESTINO.rglob( "*" ) if _.is_file() )
    print( f"\n✅ pack completo: {cuenta} archivos en brand/logo/" )


if __name__ == "__main__":
    main()
