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
    """El servidor de archivos de siempre, con el encabezado que Google pide."""

    def end_headers( self ):
        self.send_header(
            'Referrer-Policy',
            'no-referrer-when-downgrade'
        )
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
