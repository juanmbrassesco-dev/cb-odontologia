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
import re
import sys


# La raíz es el repo, o la carpeta que se le pase: así el mismo chequeo sirve
# para el sitio tal como está y para `dist/`, que es lo que de verdad se
# publica. Revisar sólo el repo dejaría sin mirar el único momento en que un
# archivo puede faltar: cuando se arma la publicación.
RAIZ = Path( sys.argv[ 1 ] ).resolve() if len( sys.argv ) > 1 \
    else Path( __file__ ).resolve().parent.parent

# Las páginas del sitio. Los tableros y las pruebas quedan afuera a propósito:
# son andamiaje, no lo que se publica.
PAGINAS = [ "index.html", "reservar.html", "mis-turnos.html" ]

# Las hojas de estilo, para mirar adentro lo que piden con `url( … )`.
HOJAS = [ "css/styles.css", "css/tokens.css" ]

# `url( "algo" )`, con comillas o sin ellas.
URL_DEL_CSS = re.compile( r'url\(\s*[\'"]?([^\'")]+)[\'"]?\s*\)' )

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


def existe( destino ):
    """Si ese destino se puede servir, con las reglas del sitio publicado.

    🔴 SON TRES FORMAS DE NOMBRAR UN ARCHIVO Y LAS TRES VALEN, porque así lo
    publica Cloudflare: `/reservar` sirve `reservar.html`, y `/` sirve
    `index.html`. Los enlaces del sitio usan la forma sin extensión desde el
    2-oct-2026 — con el `.html` cada navegación interna pagaba un 307 de más.

    ⚠️ Sin esta función, el verificador cantaría como ROTOS todos los enlaces
    internos del sitio, que es peor que no verificar: un chequeo que falla
    siempre se empieza a ignorar.
    """
    # La barra del principio es de la raíz del sitio, que acá es la del repo.
    relativo = destino.lstrip( "/" )

    if not relativo:
        relativo = "index.html"

    if ( RAIZ / relativo ).exists():
        return True

    # La forma sin extensión: `/reservar` es el archivo `reservar.html`.
    return ( RAIZ / ( relativo + ".html" ) ).exists()


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

        if not existe( archivo ):
            rotos.append(
                f"<{ etiqueta } { atributo }=\"{ destino }\"> — "
                f"no existe el archivo { archivo }"
            )

    return rotos, externos


def revisar_la_hoja( hoja ):
    """Los archivos que una hoja de estilo pide con `url( … )` y no están.

    🔴 ESTO SE SUMÓ EL 1-oct-2026 PORQUE FALTABA Y COSTÓ CARO: el sitio se
    publicó con las DOS tipografías en 404 y nadie lo vio, porque el navegador
    las reemplaza por otras parecidas sin decir nada. **Un archivo que sólo
    nombra el CSS no aparece en el HTML**, así que ninguna lista escrita a mano
    lo incluye.

    ⚠️ LAS RUTAS DEL CSS SON RELATIVAS A LA HOJA, no a la raíz: un
    `../brand/…` escrito en `css/styles.css` significa `brand/…`. Resolverlo
    mal haría que el chequeo no encuentre nada y cante que está todo bien, que
    es peor que no tenerlo.
    """
    ruta = RAIZ / hoja
    rotos = []

    for destino in URL_DEL_CSS.findall( ruta.read_text( encoding = "utf-8" ) ):

        if destino.startswith( ( "data:", "http://", "https://", "//" ) ):
            continue

        archivo = ( ruta.parent / destino.split( "?" )[ 0 ] ).resolve()

        if not archivo.exists():
            rotos.append( destino + " — no está" )

    return rotos


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

    for hoja in HOJAS:

        rotos = revisar_la_hoja( hoja )

        if rotos:
            hubo_rotos = True
            print( f"\n✗ { hoja } — { len( rotos ) } roto(s):" )
            for roto in rotos:
                print( f"    { roto }" )
        else:
            print( f"✓ { hoja }" )

    print( f"\nEnlaces externos (no se visitan, se listan): { len( todos_los_externos ) }" )
    for externo in sorted( todos_los_externos ):
        print( f"    { externo }" )

    if hubo_rotos:
        sys.exit( 1 )


if __name__ == "__main__":
    main()
