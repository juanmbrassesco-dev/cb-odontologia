#!/usr/bin/env python3
"""Sirve el sitio en localhost para probarlo con el login de Google puesto.

POR QUÉ NO ALCANZA `python3 -m http.server`, que es lo que usábamos:

    Google pide que, al probar con HTTP en localhost, la página mande el
    encabezado `Referrer-Policy: no-referrer-when-downgrade`. Sin él, el
    navegador no le cuenta a Google desde qué origen viene el pedido, y
    Google rechaza el login sin decir por qué. El servidor pelado de Python
    no manda ese encabezado y no tiene forma de configurarlo.

    Esto es lo mismo de siempre más UNA línea: el encabezado.

CÓMO SE USA, siempre desde la raíz del repo:

    python3 tools/servidor-de-pruebas.py

    Y después se abre http://localhost:8000/reservar.html

EL PUERTO ES EL 8000 Y NO SE CAMBIA A LA LIGERA: es el que está registrado en
la consola de Google como origen autorizado de JavaScript. Con otro número el
login rebota con `origin_mismatch`.
"""

import http.server
import socketserver


PUERTO = 8000


class Servidor( http.server.SimpleHTTPRequestHandler ):
    """El servidor de archivos de siempre, con dos encabezados agregados."""

    def end_headers( self ):

        # ① EL QUE PIDE GOOGLE PARA EL LOGIN. El porqué, arriba del archivo.
        self.send_header(
            'Referrer-Policy',
            'no-referrer-when-downgrade'
        )

        # ② PROHIBIDO GUARDAR NADA EN EL CACHÉ — puesto el 30-sep-2026, después
        #    de perder un rato buscando un bug que no existía.
        #
        #    El servidor pelado manda `Last-Modified` y NINGUNA instrucción de
        #    caché. Ante esa falta el navegador NO pregunta: aplica su propia
        #    regla y se guarda el archivo un rato. Así, un `js/` recién escrito
        #    puede no llegar nunca a la pantalla, y lo que se prueba es la
        #    versión anterior.
        #
        #    🔴 ES EL PEOR MODO DE FALLA QUE HAY: no da error, no avisa, y todo
        #    lo que se mide queda mal medido. El síntoma es «lo arreglé y sigue
        #    igual», que manda a buscar el problema al único lado donde no está.
        #
        #    Las tres líneas son la instrucción completa: `no-store` para los
        #    navegadores de hoy, y las otras dos para los intermediarios viejos
        #    que sólo entienden HTTP/1.0.
        self.send_header( 'Cache-Control', 'no-store, no-cache, must-revalidate' )
        self.send_header( 'Pragma', 'no-cache' )
        self.send_header( 'Expires', '0' )

        super().end_headers()


def main():
    # `allow_reuse_address` evita el "Address already in use" de los 30
    # segundos siguientes a cortar el servidor: sin esto hay que esperar.
    socketserver.TCPServer.allow_reuse_address = True

    with socketserver.TCPServer( ( '', PUERTO ), Servidor ) as servidor:
        print( f'Sirviendo en http://localhost:{ PUERTO }/' )
        print( 'Para cortarlo: Control-C' )

        try:
            servidor.serve_forever()

        except KeyboardInterrupt:
            print( '\nCortado.' )


if __name__ == '__main__':
    main()
