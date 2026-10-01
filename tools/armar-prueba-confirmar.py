#!/usr/bin/env python3
"""Arma `pruebas/pantalla-confirmar.html`: la pantalla ⑤ y sus cinco respuestas.

POR QUÉ EXISTE, y es el mismo motivo que las otras dos pruebas de pantalla: de
las cinco respuestas que puede dar `POST /reservar`, **la agenda real sólo deja
ver una sin romper nada**. Para mirar «ya tenés un turno con este profesional»
habría que dejar un turno abierto en la base de un consultorio de verdad; para
mirar «se cerró tu sesión», esperar a que el token se venza; y el fallo
genérico sólo aparece si alguien toma la hora en el segundo exacto.

🔴 Y EL SEGUNDO MOTIVO ES MÁS FUERTE: probar esto contra el portero CREA TURNOS
REALES, con sus tres correos saliendo. Acá no se escribe nada: se intercepta el
pedido y se contesta lo que haga falta. La base queda como está.

QUÉ NO ES: esto no reemplaza la batería `probar-reservar.sh`. Prueba la
PANTALLA —que la tarjeta diga lo que el paciente eligió, que el desplegable
agrupe, que cada respuesta lleve a la noticia correcta y con el botón que
corresponde—, no que el portero reserve bien. Eso ya está probado del otro lado.

EL MARKUP NO SE COPIA: se recorta de `reservar.html` cada vez que se corre, y
el código que dibuja es `js/confirmar.js` sin tocar. Lo único inventado son los
datos y la respuesta.

CÓMO SE USA, desde la raíz del repo:

    python3 tools/armar-prueba-confirmar.py

Y después, con el servidor levantado:

    http://localhost:8000/pruebas/pantalla-confirmar.html?caso=feliz
"""

from pathlib import Path
import json


RAIZ = Path( __file__ ).resolve().parent.parent

PAGINA  = RAIZ / "reservar.html"
DESTINO = RAIZ / "pruebas" / "pantalla-confirmar.html"

# La prueba vive una carpeta más adentro que el sitio, así que sus rutas suben.
SUBIR = "../"


# Las obras sociales inventadas. El reparto NO es decorativo: hay una entidad
# con UN plan y entidades con VARIOS, porque la regla del desplegable es que
# sólo se agrupa lo que tiene más de uno. Con una lista toda agrupada —o toda
# suelta— la mitad de la regla queda sin mirar.
OBRAS_SOCIALES = [
    { "id": 1, "nombre": "Particular",            "entidad": "Particular" },
    { "id": 2, "nombre": "IAPOS",                 "entidad": "IAPOS" },
    { "id": 3, "nombre": "IAPOS Plan Superior",   "entidad": "IAPOS" },
    { "id": 4, "nombre": "IAPOS Jubilados",       "entidad": "IAPOS" },
    { "id": 5, "nombre": "OSDE 210",              "entidad": "OSDE" },
    { "id": 6, "nombre": "OSDE 310",              "entidad": "OSDE" },
    { "id": 7, "nombre": "Swiss Medical",         "entidad": "Swiss Medical" },
]


# Qué contesta el portero en cada caso: el estado y el cuerpo, tal cual los
# manda `supabase/functions/reservar/index.ts`.
CASOS = {
    "feliz":  ( 201, { "id": 999, "inicio": "2026-10-08T15:30:00-03:00", "duracion_min": 30 } ),

    "limite": ( 409, {
        "error": "Ya tenés un turno con este profesional. "
                 "Podés cancelarlo desde «mis turnos», o escribinos si necesitás otro.",
        "codigo": "limite_alcanzado",
    } ),

    "hora":   ( 409, {
        "error": "Esa hora se acaba de ocupar. Elegí otra, por favor",
        "codigo": "hora_tomada",
    } ),

    "sesion": ( 403, { "error": "Sesión no válida" } ),

    "fallo":  ( 500, { "error": "No se pudo reservar el turno" } ),
}


def recortar( id_de_la_pantalla ):
    """La <section> de una pantalla, tal cual está en `reservar.html`.

    Se busca por el `id` y no por las clases, por lo mismo que en las otras dos
    pruebas: las clases se mueven, el `id` lo usa `pasos.js` para mostrar el
    paso y nadie lo toca de pasada.

    🔴 EL CIERRE SE BUSCA CONTANDO y no con el primer `</section>`. Hoy ninguna
    de estas dos pantallas tiene una <section> adentro, así que contar no hace
    falta — y se cuenta igual, porque el día que una la tenga el recorte saldría
    cortado y el error se leería como un error de la pantalla. Ya pasó una vez,
    con la ④, el 30-sep-2026.
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
    """La pantalla a la vista: acá es lo único que hay."""
    return pantalla.replace( " hidden>", ">", 1 )


CUERPO_JS = r'''
  // ── LO QUE NORMALMENTE PONEN LAS CUATRO PANTALLAS ANTERIORES ──
  //
  // Esta página no entra con Google ni pasa por el flujo, así que todo lo que
  // `confirmar.js` espera encontrar puesto se pone acá a mano. Son las MISMAS
  // variables y las mismas funciones, con los mismos nombres: si alguna
  // cambiara de nombre, esta prueba se rompe en vez de mentir.
  const SUPABASE_URL = 'https://ejemplo.invalido';
  const SUPABASE_CLAVE_PUBLICA = 'clave-de-prueba';

  function tokenDeLaSesion() {
    return 'token-de-prueba';
  }

  // De `motivo.js` y de `dia-hora.js`.
  let tratamientoElegido = 1;
  let nombreDelTratamiento = 'Ortodoncia';
  let profesionalElegido = 1;
  let nombreDelProfesional = 'Cecilia Brassesco';
  let diaElegido = '2026-10-08';
  let horaElegida = '2026-10-08T15:30:00-03:00';

  // El «Volver a la agenda» del fallo genérico la llama. Acá no hay agenda que
  // recargar, así que se deja dicho en la página qué habría pasado.
  async function recargarLaAgenda() {
    avisar( 'Se llamó a recargarLaAgenda(): en el sitio, acá se vuelve a pedir el mes.' );
  }

  // De `quien.js`. El caso con `paciente_id` es el más común —la persona ya
  // figura— y el de alta se mira cambiando esto a mano.
  let pacienteElegido = {
    pedido: { paciente_id: 225 },
    nombre: 'María Fernanda Gómez'
  };

  // De `auth.js`. El botón de Google NO se puede dibujar acá: lo dibuja su
  // biblioteca y necesita el origen autorizado. Se pone un cartel que dice qué
  // va en ese lugar, para que nadie confunda este recuadro con el botón real.
  function prepararElBoton( { contenedor, alEntrar } ) {

    contenedor.textContent = '';

    const cartel = document.createElement( 'button' );
    cartel.className = 'btn btn-2';
    cartel.textContent = '(acá dibuja Google su botón) · entrar';

    cartel.addEventListener( 'click', alEntrar );

    contenedor.appendChild( cartel );
  }


  // ── EL PEDIDO AL PORTERO, INTERCEPTADO ──
  //
  // Se reemplaza `fetch` en vez de llamar a `darLaNoticia(…)` a mano, y la
  // diferencia importa: así corre el camino ENTERO —armar el cuerpo, mandarlo,
  // leer el estado, elegir la noticia—. Saltearse el pedido dejaría sin probar
  // justo la parte que más se toca.
  const CASO = new URLSearchParams( location.search ).get( 'caso' ) || 'feliz';

  const RESPUESTAS = RESPUESTAS_INVENTADAS;

  const fetchDeVerdad = window.fetch;

  window.fetch = async function ( direccion, opciones ) {

    if ( String( direccion ).includes( 'obras-sociales' ) ) {

      return {
        ok: true,
        status: 200,
        json: async () => OBRAS_INVENTADAS
      };
    }

    if ( String( direccion ).includes( 'reservar' ) ) {

      // Lo que la pantalla mandó queda escrito arriba: es la mitad que no se
      // ve mirando la pantalla, y es la que tiene que llegarle al portero.
      avisar( 'POST /reservar ← ' + opciones.body );

      // SIN RED: el caso en que el pedido no llega a salir. `fetch` lanza, y lo
      // que se prueba es que la pantalla igual diga algo en vez de quedarse
      // muda con el botón apagado.
      if ( CASO === 'red' ) {
        throw new TypeError( 'Failed to fetch (simulado)' );
      }

      const respuesta = RESPUESTAS[ CASO ];

      return {
        ok: respuesta[ 0 ] === 201,
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
        .replace( "OBRAS_INVENTADAS", json.dumps( OBRAS_SOCIALES, ensure_ascii = False ) ) \
        .replace( "RESPUESTAS_INVENTADAS", json.dumps( CASOS, ensure_ascii = False ) )

    DESTINO.parent.mkdir( exist_ok = True )

    DESTINO.write_text( f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Prueba · la pantalla ⑤ y sus cinco respuestas</title>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
  <link rel="stylesheet" href="{ SUBIR }css/tokens.css">
  <link rel="stylesheet" href="{ SUBIR }css/styles.css">
  <style>
    /* Lo de abajo NO es parte del sitio: es el tablero de mandos de la prueba.
       Va con un fondo distinto para que no se confunda con la pantalla. */
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
      max-height: 120px;
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
  <a href="?caso=feliz">201 reservado</a> ·
  <a href="?caso=limite">409 tope</a> ·
  <a href="?caso=hora">409 hora tomada</a> ·
  <a href="?caso=sesion">403 sesión</a> ·
  <a href="?caso=fallo">500</a> ·
  <a href="?caso=red">sin red</a>
</div>
<pre id="registro"></pre>

  <main>
    <!-- `pasos.js` arranca guardando la pantalla que está a la vista, y en el
         sitio ésa es la de entrar. Acá no está, así que se le deja una vacía
         para esconder: sin esto, el primer cambio de pantalla se cae. -->
    <section id="paso-entrar" hidden></section>

{ sin_hidden( recortar( "paso-confirmar" ) ) }

{ recortar( "paso-mensaje" ) }
  </main>

<script>
{ cuerpo }
</script>
<script src="{ SUBIR }js/fechas.js"></script>
<script src="{ SUBIR }js/pasos.js"></script>
<script>
  // 🔴 `pasos.js` arranca anotando que la pantalla a la vista es la de entrar,
  // porque en el sitio ésa es la única sin `hidden`. Acá la que está a la vista
  // es la ⑤, y sin corregirlo la noticia aparecía DEBAJO del formulario en vez
  // de reemplazarlo: `mostrarPantalla` escondía la pantalla equivocada.
  //
  // ⚠️ Era un defecto de la PRUEBA y no del sitio —en el flujo de verdad se
  // llega a la ⑤ con `avanzarA`, que sí la anota—, y se arregla acá porque una
  // prueba que dibuja algo que el sitio no hace es peor que no tenerla.
  pantallaALaVista = document.querySelector( '#paso-confirmar' );
</script>
<script src="{ SUBIR }js/confirmar.js"></script>
<script>
  // Arranca la pantalla como lo haría el «Continuar» de la ④.
  prepararLaPantallaDeConfirmar();
</script>
</body>
</html>
""", encoding = "utf-8" )

    print( f"✓ { DESTINO.relative_to( RAIZ ) }" )
    print( f"  { len( OBRAS_SOCIALES ) } obras sociales inventadas · { len( CASOS ) + 1 } respuestas" )


if __name__ == "__main__":
    armar()
