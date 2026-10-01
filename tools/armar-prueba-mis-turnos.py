#!/usr/bin/env python3
"""Arma `pruebas/pantalla-mis-turnos.html`: la pantalla ⑥ con turnos inventados.

POR QUÉ EXISTE, y es el mismo motivo que las otras tres pruebas de pantalla:
los estados de esta pantalla **no se pueden provocar sin escribir en la base de
un consultorio real**. Para ver la lista hay que tener turnos; para ver el
estado vacío, no tener ninguno; y para ver «no pudimos cancelar» hay que
cancelar un turno que ya esté cancelado.

🔴 Y HAY UN SEGUNDO MOTIVO, MÁS FUERTE QUE EN LAS OTRAS: acá el camino de
prueba CANCELA TURNOS, y una cancelación dispara correos de verdad. Esto no
toca la base ni manda un correo: intercepta el pedido y contesta.

QUÉ NO ES: no reemplaza a `probar-cancelar.sh`. Prueba la PANTALLA —que la
tarjeta diga lo que el portero manda, que la hora salga en la zona de acá, que
el botón pregunte antes de cancelar y que cada respuesta lleve a su noticia—,
no que el portero cancele bien.

EL MARKUP NO SE COPIA: se recorta de `mis-turnos.html` cada vez que se corre, y
el código que dibuja es `js/mis-turnos.js` sin tocar.

CÓMO SE USA, desde la raíz del repo:

    python3 tools/armar-prueba-mis-turnos.py

Y después, con el servidor levantado:

    http://localhost:8000/pruebas/pantalla-mis-turnos.html?caso=dos
"""

from pathlib import Path
import json


RAIZ = Path( __file__ ).resolve().parent.parent

PAGINA  = RAIZ / "mis-turnos.html"
DESTINO = RAIZ / "pruebas" / "pantalla-mis-turnos.html"

SUBIR = "../"


# 🔴 LOS `inicio` VAN EN UTC —con `+00:00`— A PROPÓSITO, porque así es como los
# manda la base: un turno de las 15:30 en Santa Fe viaja como las 18:30 UTC. Si
# la pantalla cortara el texto en vez de convertirlo, acá se vería «18:30» y el
# error quedaría a la vista. Escribirlos ya convertidos sería armar una prueba
# que no puede fallar.
TURNOS = [
    {
        "id": 501,
        "inicio": "2026-10-08T18:30:00+00:00",
        "duracion_min": 30,
        "paciente": { "id": 225, "nombre": "María Fernanda", "apellido": "Gómez" },
        "profesional": { "nombre": "Cecilia", "apellido": "Brassesco" },
        "tratamiento": { "nombre": "consulta" },
        # El motivo DIFIERE del tratamiento: pidió ortodoncia y se agendó una
        # consulta. La tarjeta tiene que decir «ortodoncia».
        "motivo": { "nombre": "ortodoncia" },
        "obra_social": { "nombre": "IAPOS" },
    },
    {
        "id": 502,
        "inicio": "2026-10-30T12:00:00+00:00",
        "duracion_min": 60,
        "paciente": { "id": 226, "nombre": "Joaquín", "apellido": "Gómez" },
        "profesional": { "nombre": "Cecilia", "apellido": "Brassesco" },
        "tratamiento": { "nombre": "limpieza" },
        # Coinciden, así que el portero manda `motivo: null` y la tarjeta dice
        # «limpieza».
        "motivo": None,
        "obra_social": { "nombre": "Particular" },
    },
]


# Qué contesta el portero al cancelar, en cada caso.
CANCELACIONES = {
    "dos":     ( 200, { "id": 501, "activo": False } ),
    "uno":     ( 200, { "id": 501, "activo": False } ),
    "vacio":   ( 200, {} ),
    "sesion":  ( 403, { "error": "Sesión no válida", "codigo": "sesion_invalida" } ),
    "tarde":   ( 403, { "error": "Ese turno no se puede cancelar", "codigo": "no_cancelable" } ),
    "fallo":   ( 500, { "error": "No se pudo cancelar el turno" } ),
}


# Cuántos turnos devuelve la lista en cada caso.
CUANTOS = {
    "dos": 2,
    "uno": 1,
    "vacio": 0,
    "sesion": 2,
    "tarde": 2,
    "fallo": 2,
}


def recortar( id_de_la_pantalla ):
    """La <section> de una pantalla, tal cual está en `mis-turnos.html`.

    Se busca por el `id` y no por las clases, y el cierre se encuentra
    CONTANDO: el mismo recorte que ya salió mal una vez, con la ④, por confiar
    en el primer `</section>`.
    """
    pagina = PAGINA.read_text( encoding = "utf-8" )

    ancla    = pagina.index( f'id="{ id_de_la_pantalla }"' )
    arranque = pagina.rindex( "<section", 0, ancla )

    profundidad = 0
    cursor = arranque

    while True:

        abre   = pagina.find( "<section", cursor + 1 )
        cierra = pagina.find( "</section>", cursor + 1 )

        if 0 <= abre < cierra:
            profundidad += 1
            cursor = abre
            continue

        if profundidad == 0:
            cierre = cierra + len( "</section>" )
            break

        profundidad -= 1
        cursor = cierra

    return pagina[ arranque : cierre ]


def sin_hidden( pantalla ):
    """La pantalla a la vista. Sólo la primera marca: las de adentro se quedan."""
    return pantalla.replace( " hidden>", ">", 1 )


CUERPO_JS = r'''
  // ── LO QUE NORMALMENTE PONE `auth.js` ──
  //
  // Esta página no entra con Google, así que lo que `mis-turnos.js` espera
  // encontrar puesto se pone acá a mano, con los MISMOS nombres: si alguno
  // cambiara, esta prueba se rompe en vez de mentir.
  const SUPABASE_URL = 'https://ejemplo.invalido';
  const SUPABASE_CLAVE_PUBLICA = 'clave-de-prueba';

  function tokenDeLaSesion() {
    return 'token-de-prueba';
  }

  // El botón de Google NO se puede dibujar acá: lo dibuja su biblioteca y
  // necesita el origen autorizado. Se pone un cartel que dice qué va en ese
  // lugar, para que nadie lo confunda con el botón real.
  function prepararElBoton( { contenedor, alEntrar } ) {

    contenedor.textContent = '';

    const cartel = document.createElement( 'button' );
    cartel.className = 'btn btn-2';
    cartel.textContent = '(acá dibuja Google su botón) · entrar';

    cartel.addEventListener( 'click', alEntrar );

    contenedor.appendChild( cartel );
  }


  // ── LOS PEDIDOS AL PORTERO, INTERCEPTADOS ──
  const CASO = new URLSearchParams( location.search ).get( 'caso' ) || 'dos';

  const TURNOS = TURNOS_INVENTADOS;
  const CANCELACIONES = CANCELACIONES_INVENTADAS;
  const CUANTOS = CUANTOS_INVENTADOS;

  // Los turnos que «quedan»: cancelar uno tiene que sacarlo de la lista, y eso
  // sólo se ve si el segundo pedido contesta distinto que el primero.
  let quedan = TURNOS.slice( 0, CUANTOS[ CASO ] );

  const fetchDeVerdad = window.fetch;

  window.fetch = async function ( direccion, opciones ) {

    if ( String( direccion ).includes( 'mis-turnos' ) ) {

      avisar( 'GET /mis-turnos → ' + quedan.length + ' turno(s)' );

      return {
        ok: true,
        status: 200,
        json: async () => quedan
      };
    }

    if ( String( direccion ).includes( 'cancelar' ) ) {

      avisar( 'POST /cancelar ← ' + opciones.body );

      const respuesta = CANCELACIONES[ CASO ];

      if ( respuesta[ 0 ] === 200 ) {
        const cancelado = JSON.parse( opciones.body ).turno_id;
        quedan = quedan.filter( ( turno ) => turno.id !== cancelado );
      }

      return {
        ok: respuesta[ 0 ] === 200,
        status: respuesta[ 0 ],
        json: async () => respuesta[ 1 ]
      };
    }

    return fetchDeVerdad( direccion, opciones );
  };


  function avisar( texto ) {
    const registro = document.querySelector( '#registro' );
    registro.textContent = texto + '\n' + registro.textContent;
  }
'''


def armar():

    cuerpo = CUERPO_JS \
        .replace( "TURNOS_INVENTADOS", json.dumps( TURNOS, ensure_ascii = False ) ) \
        .replace( "CANCELACIONES_INVENTADAS", json.dumps( CANCELACIONES, ensure_ascii = False ) ) \
        .replace( "CUANTOS_INVENTADOS", json.dumps( CUANTOS, ensure_ascii = False ) )

    DESTINO.parent.mkdir( exist_ok = True )

    DESTINO.write_text( f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Prueba · la pantalla ⑥ con turnos inventados</title>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
  <link rel="stylesheet" href="{ SUBIR }css/tokens.css">
  <link rel="stylesheet" href="{ SUBIR }css/styles.css">
  <style>
    /* Lo de abajo NO es parte del sitio: es el tablero de mandos de la prueba. */
    .mandos {{
      padding: 10px 20px;
      background: #2b2a27;
      color: #fff;
      font: 13px/1.5 ui-monospace, monospace;
    }}
    .mandos a {{ color: #e8c87a; }}
    #registro {{
      margin: 0;
      padding: 10px 20px;
      max-height: 100px;
      overflow: auto;
      background: #1c1b19;
      color: #cfcdc7;
      font: 12px/1.5 ui-monospace, monospace;
      white-space: pre-wrap;
    }}
  </style>
</head>
<body>

<div class="mandos">
  la lista y lo que contesta el portero al cancelar:
  <a href="?caso=dos">dos turnos</a> ·
  <a href="?caso=uno">uno</a> ·
  <a href="?caso=vacio">ninguno</a> ·
  <a href="?caso=tarde">403 ya no se puede</a> ·
  <a href="?caso=sesion">403 sesión</a> ·
  <a href="?caso=fallo">500</a>
</div>
<pre id="registro"></pre>

  <main>
    <!-- `mis-turnos.js` cuelga el botón de Google y el aviso al cargar, y los
         busca por `id`. Acá la pantalla de entrar no está recortada, así que
         se le dejan los dos huecos: sin ellos el archivo se cae sobre `null`
         antes de dibujar nada. -->
    <div id="boton-google" hidden></div>
    <p id="aviso-entrar" hidden></p>

{ sin_hidden( recortar( "paso-turnos" ) ) }

{ recortar( "paso-mensaje" ) }
  </main>

<script>
{ cuerpo }
</script>
<script src="{ SUBIR }js/fechas.js"></script>
<script src="{ SUBIR }js/pasos.js"></script>
<script>
  // `pasos.js` arranca guardando la pantalla que está a la vista, y en la
  // página de verdad ésa es la de entrar. Acá no está, así que la de la lista
  // ocupa su lugar: sin esto, el primer cambio de pantalla se cae.
  pantallaALaVista = document.querySelector( '#paso-turnos' );
</script>
<script src="{ SUBIR }js/mis-turnos.js"></script>
<script>
  // Arranca la pantalla como lo haría el login.
  mostrarLosTurnos();
</script>
</body>
</html>
""", encoding = "utf-8" )

    print( f"✓ { DESTINO.relative_to( RAIZ ) }" )
    print( f"  { len( TURNOS ) } turnos inventados · { len( CANCELACIONES ) } respuestas" )


if __name__ == "__main__":
    armar()
