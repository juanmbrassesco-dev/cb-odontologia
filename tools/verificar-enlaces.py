#!/usr/bin/env python3
"""Revisa que ningún enlace del sitio apunte a la nada.

POR QUÉ EXISTE, y no es prevención abstracta: **los doce botones «Reservar» de
la landing estuvieron muertos y en silencio** hasta que Juan los tocó. Un ancla
que no existe —`href="#reservar"` sin ningún `id="reservar"`— **no da error, no
pinta nada distinto y no avisa**: el navegador simplemente no se mueve.

QUÉ REVISA, y los tres son el mismo bug con tres caras:

  1. **Anclas internas** (`#algo`): que exista un elemento con ese `id` EN ESA
     página. Es el caso que ya pasó.
  2. **Archivos relativos** (`css/styles.css`, `reservar.html`, una foto): que
     el archivo esté donde el HTML dice.
  3. **Enlaces externos** (`https://…`): NO se visitan —eso depende de la red y
     de terceros, y un chequeo que falla por motivos ajenos se empieza a
     ignorar—. Se LISTAN para que se miren de a uno cuando cambie alguno.

QUÉ NO REVISA: lo que arma JavaScript. Las tarjetas de «mis turnos» y las horas
del almanaque no están en el HTML, así que acá no aparecen.

CÓMO SE USA, desde la raíz del repo:

    python3 tools/verificar-enlaces.py

Sale con código 1 si encontró algo roto, para que un día pueda colgarse de un
hook o de una acción antes de publicar.
"""

from html.parser import HTMLParser
from pathlib import Path
import sys


RAIZ = Path( __file__ ).resolve().parent.parent

# Las páginas del sitio. Los tableros y las pruebas quedan afuera a propósito:
# son andamiaje, no lo que se publica.
PAGINAS = [ "index.html", "reservar.html", "mis-turnos.html" ]

# Atributos que apuntan a algún lado.
APUNTAN = ( "href", "src" )


class Lector( HTMLParser ):
    """Junta los `id` que la página define y los destinos a los que apunta."""

    def __init__( self ):
        super().__init__( convert_charrefs = True )
        self.ids = set()
        self.destinos = []

    def handle_starttag( self, etiqueta, atributos ):

        for nombre, valor in atributos:

            if nombre == "id" and valor:
                self.ids.add( valor )

            if nombre in APUNTAN and valor:
                self.destinos.append( ( etiqueta, nombre, valor ) )


def revisar( pagina ):
    """Devuelve (rotos, externos) de una página."""

    lector = Lector()
    lector.feed( ( RAIZ / pagina ).read_text( encoding = "utf-8" ) )

    rotos = []
    externos = []

    for etiqueta, atributo, destino in lector.destinos:

        # Lo que no es un enlace a un lugar: el correo, el teléfono, los datos
        # incrustados y los huecos a propósito.
        if destino.startswith( ( "mailto:", "tel:", "data:", "javascript:" ) ):
            continue

        if destino.startswith( ( "http://", "https://", "//" ) ):
            externos.append( destino )
            continue

        # Un ancla de la misma página.
        if destino.startswith( "#" ):

            nombre = destino[ 1 : ]

            if nombre and nombre not in lector.ids:
                rotos.append(
                    f"<{ etiqueta } { atributo }=\"{ destino }\"> — "
                    f"esta página no tiene ningún id=\"{ nombre }\""
                )
            continue

        # Un archivo. Se corta lo que viene después de `?` o de `#`, que no es
        # parte del nombre.
        archivo = destino.split( "?" )[ 0 ].split( "#" )[ 0 ]

        if not archivo:
            continue

        if not ( RAIZ / archivo ).exists():
            rotos.append(
                f"<{ etiqueta } { atributo }=\"{ destino }\"> — "
                f"no existe el archivo { archivo }"
            )

    return rotos, externos


def main():

    hubo_rotos = False
    todos_los_externos = set()

    for pagina in PAGINAS:

        rotos, externos = revisar( pagina )
        todos_los_externos.update( externos )

        if rotos:
            hubo_rotos = True
            print( f"\n✗ { pagina } — { len( rotos ) } roto(s):" )
            for roto in rotos:
                print( f"    { roto }" )
        else:
            print( f"✓ { pagina }" )

    print( f"\nEnlaces externos (no se visitan, se listan): { len( todos_los_externos ) }" )
    for externo in sorted( todos_los_externos ):
        print( f"    { externo }" )

    if hubo_rotos:
        sys.exit( 1 )


if __name__ == "__main__":
    main()
