#!/usr/bin/env python3
"""Arma `pruebas/pantalla-panel.html`: la agenda del panel con turnos inventados.

POR QUÉ EXISTE, y es el mismo motivo que las otras pruebas de pantalla: los
estados de esta pantalla **no se pueden provocar sin escribir en la base de un
consultorio real**. Para ver un día lleno habría que cargar seis turnos de
mentira en la agenda de Cecilia; para ver el estado vacío, borrarlos; y para
ver «esta página no es para pacientes» habría que entrar con una cuenta que no
es staff.

🔴 Y ÉSTE ES EL CASO QUE LO HIZO FALTA, el 8-oct-2026: Juan abrió el panel
recién terminado y vio UN solo turno, porque uno solo hay en la base. Con un
turno no se puede juzgar una agenda — ni el ritmo de la lista, ni dónde se
corta la lectura, ni si el día se entiende de un vistazo.

QUÉ NO ES: no reemplaza a `probar-panel.sh`. Prueba la PANTALLA —que la hora
salga en la zona de acá, que el motivo mande sobre el tratamiento, que el día
vacío diga algo—, no que el portero filtre bien por quién pide.

EL MARKUP NO SE COPIA: se recorta de `panel.html` cada vez que se corre, y el
código que dibuja es `js/panel.js` sin tocar. Si la página cambia, la prueba
cambia con ella en vez de quedar mintiendo.

CÓMO SE USA, desde la raíz del repo:

    python3 tools/armar-prueba-panel.py

Y después, con el servidor levantado:

    http://localhost:8000/pruebas/pantalla-panel.html?caso=lleno
"""

from pathlib import Path
import json


RAIZ = Path( __file__ ).resolve().parent.parent

PAGINA  = RAIZ / "panel.html"
DESTINO = RAIZ / "pruebas" / "pantalla-panel.html"

SUBIR = "../"


# 🔴 LOS `inicio` VAN EN UTC —con `+00:00`— A PROPÓSITO, porque así es como los
# manda la base: un turno de las 09:00 en Santa Fe viaja como las 12:00 UTC. Si
# la pantalla cortara el texto en vez de convertirlo, acá se vería «12:00» y el
# error sería invisible: una hora válida, bien escrita, tres horas corrida.
#
# El día elegido es un jueves cualquiera; lo que importa es que todos los
# turnos caigan en el mismo.
DIA = "2026-10-15"


def turno( id_, hora_utc, duracion, paciente, apellido, tratamiento,
           motivo = None, obra_social = "Particular", profesional = "Cecilia" ):

    return {
        "id": id_,
        "inicio": f"{ DIA }T{ hora_utc }:00+00:00",
        "duracion_min": duracion,
        "canal": "web",
        "paciente": { "id": id_, "nombre": paciente, "apellido": apellido },
        "profesional": { "id": 1, "nombre": profesional, "apellido": "Brassesco" },
        "tratamiento": { "nombre": tratamiento },
        "motivo": { "nombre": motivo } if motivo else None,
        "obra_social": { "nombre": obra_social },
    }


# Un día de consultorio como es: turnos pegados, duraciones distintas, un
# motivo que no coincide con el tratamiento —que es el caso que la tarjeta
# tiene que mostrar bien— y una cobertura que no es particular.
TURNOS = [
    turno( 1, "12:00", 30, "Marta",    "Giménez",  "consulta", motivo = "ortodoncia" ),
    turno( 2, "12:30", 60, "Rodrigo",  "Paz",      "limpieza", obra_social = "OSDE" ),
    turno( 3, "13:30", 30, "Valentina", "Ruiz",    "consulta", motivo = "bruxismo",
           obra_social = "A.M.U.R." ),
    turno( 4, "16:00", 90, "Esteban",  "Molina",   "consulta", motivo = "prótesis" ),
    turno( 5, "17:30", 30, "Lucía",    "Ferreyra", "blanqueamiento" ),
    turno( 6, "18:00", 60, "Joaquín",  "Sosa",     "limpieza", obra_social = "IAPOS",
           profesional = "Martín" ),
]


CASOS = {
    "lleno":  { "estado": 200, "cuantos": 6 },
    "uno":    { "estado": 200, "cuantos": 1 },
    "vacio":  { "estado": 200, "cuantos": 0 },
    "ajeno":  { "estado": 403, "cuantos": 0 },
    "fallo":  { "estado": 500, "cuantos": 0 },
}


def recortar( id_de_la_pantalla ):
    """La <section> de una pantalla, tal cual está en `panel.html`.

    Se busca por el `id` y el cierre se encuentra CONTANDO, no con el primer
    `</section>`: es el recorte que ya salió mal una vez en la prueba de la ⑥.
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


def recortar_el_cartel():
    """El `<dialog>` de la pregunta, tal cual está en `panel.html`.

    🔴 VA APARTE DEL RECORTE DE PANTALLAS porque no es una `<section>`, y sin
    esta función la prueba se quedaba sin el cartel: `panel.js` lo busca por
    `id` al cargar y se cae sobre `null` antes de dibujar un solo turno.

    Se busca desde el `id` HACIA ATRÁS y no con el primer `"<dialog"` del
    archivo: el comentario que está arriba del cartel nombra la etiqueta, así
    que el recorte simple arrancaría adentro del comentario y lo partiría.
    """
    pagina = PAGINA.read_text( encoding = "utf-8" )

    ancla    = pagina.index( 'id="cartel-cancelar"' )
    arranque = pagina.rindex( "<dialog", 0, ancla )
    cierre   = pagina.index( "</dialog>", ancla ) + len( "</dialog>" )

    return pagina[ arranque : cierre ]


def sin_hidden( pantalla ):
    """La pantalla a la vista. Sólo la primera marca: las de adentro se quedan."""
    return pantalla.replace( " hidden>", ">", 1 )


CUERPO_JS = r'''
  // ── LO QUE NORMALMENTE PONE `auth.js` ──
  //
  // Esta página no entra con Google, así que lo que `panel.js` espera
  // encontrar puesto se pone acá a mano, con los MISMOS nombres: si alguno
  // cambiara, esta prueba se rompe en vez de mentir.
  const SUPABASE_URL = 'https://ejemplo.invalido';
  const SUPABASE_CLAVE_PUBLICA = 'clave-de-prueba';

  function tokenDeLaSesion() {
    return 'token-de-prueba';
  }

  // En la prueba NO hay sesión: así el arranque de `panel.js` no dispara solo
  // y la pantalla la enciende el pie de este archivo, con el caso elegido.
  function haySesion() {
    return false;
  }

  function prepararElBoton( { contenedor } ) {

    contenedor.textContent = '';

    const cartel = document.createElement( 'button' );
    cartel.className = 'btn btn-2';
    cartel.textContent = '(acá dibuja Google su botón)';

    contenedor.appendChild( cartel );
  }


  // ── EL PEDIDO AL PORTERO, INTERCEPTADO ──
  const CASO = new URLSearchParams( location.search ).get( 'caso' ) || 'lleno';

  const TURNOS = TURNOS_INVENTADOS;
  const CASOS  = CASOS_INVENTADOS;

  const fetchDeVerdad = window.fetch;

  window.fetch = async function ( direccion, opciones ) {

    if ( String( direccion ).includes( 'agenda-del-dia' ) ) {

      const caso = CASOS[ CASO ];

      // La fecha que contesta el portero es la que le pidieron: así las
      // flechas y el almanaque se pueden probar de verdad.
      const pedida = new URL( direccion, location.origin )
        .searchParams.get( 'fecha' );

      avisar( 'GET /agenda-del-dia?fecha=' + pedida +
              ' → ' + caso.estado + ', ' + caso.cuantos + ' turno(s)' );

      return {
        ok: caso.estado === 200,
        status: caso.estado,
        json: async () => ( {
          fecha: pedida,
          esAdmin: true,
          turnos: TURNOS.slice( 0, caso.cuantos )
        } )
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
        .replace( "CASOS_INVENTADOS", json.dumps( CASOS, ensure_ascii = False ) )

    DESTINO.parent.mkdir( exist_ok = True )

    DESTINO.write_text( f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Prueba · la agenda del panel con turnos inventados</title>
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
  qué contesta el portero:
  <a href="?caso=lleno">un día lleno</a> ·
  <a href="?caso=uno">un turno</a> ·
  <a href="?caso=vacio">ninguno</a> ·
  <a href="?caso=ajeno">403 no es staff</a> ·
  <a href="?caso=fallo">500</a>
</div>
<pre id="registro"></pre>

  <main>
    <!-- `panel.js` busca estos dos por `id` al cargar. Acá la pantalla de
         entrar no está recortada, así que se le dejan los huecos: sin ellos el
         archivo se cae sobre `null` antes de dibujar nada. -->
    <div id="boton-google" hidden></div>
    <p id="aviso-entrar" hidden></p>

{ sin_hidden( recortar( "paso-agenda" ) ) }

{ recortar( "paso-sin-acceso" ) }

{ recortar_el_cartel() }
  </main>

<script>
{ cuerpo }
</script>
<script src="{ SUBIR }js/fechas.js"></script>
<script src="{ SUBIR }js/pasos.js"></script>
<script>
  // `pasos.js` arranca guardando la pantalla que está a la vista, y en la
  // página de verdad ésa es la de entrar. Acá no está, así que la de la agenda
  // ocupa su lugar: sin esto, el primer cambio de pantalla se cae.
  pantallaALaVista = document.querySelector( '#paso-agenda' );
</script>
<script src="{ SUBIR }js/panel.js"></script>
<script>
  // Arranca la pantalla como lo haría el login.
  irAlDia( '{ DIA }' );
</script>
</body>
</html>
""", encoding = "utf-8" )

    print( f"✓ { DESTINO.relative_to( RAIZ ) }" )
    print( "  http://localhost:8000/pruebas/pantalla-panel.html?caso=lleno" )


if __name__ == "__main__":
    armar()
