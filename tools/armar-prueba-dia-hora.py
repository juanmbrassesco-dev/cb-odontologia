#!/usr/bin/env python3
"""Arma `pruebas/pantalla-dia-hora.html`: la pantalla ④ con una agenda inventada.

POR QUÉ EXISTE, y es el mismo motivo que `armar-prueba-quien.py`: la pantalla
del almanaque tiene CUATRO estados de hora —`libre`, `ocupado`, `no_entra` y
`fuera_de_plazo`— más dos de día, y **la agenda real no los muestra todos a la
vez**. Un día cualquiera del consultorio tiene libres y ocupados; para ver un
feriado, un día lleno y un bloque vencido hay que esperar a que pasen.

🔴 Y HAY UN SEGUNDO MOTIVO, MÁS FUERTE: mirar la pantalla contra la agenda de
verdad obliga a ESCRIBIR en la base de un consultorio real para provocar cada
estado. Acá no se escribe nada: se intercepta el pedido y se contesta con una
agenda armada. La base queda como está.

QUÉ NO ES: esto no reemplaza probar contra el portero. Prueba la PANTALLA —que
dibuje bien los seis estados y que el ancla, las flechas y la elección
anden—, no que el portero calcule bien. Eso ya tiene su propia batería.

EL MARKUP NO SE COPIA: se recorta de `reservar.html` cada vez que se corre, y
el código que dibuja es `js/dia-hora.js` sin tocar. Lo único inventado son los
datos.

CÓMO SE USA, desde la raíz del repo:

    python3 tools/armar-prueba-dia-hora.py

Y después, con el servidor levantado:

    http://localhost:8000/pruebas/pantalla-dia-hora.html
"""

from datetime import date, datetime, timedelta
from pathlib import Path
import json


RAIZ = Path( __file__ ).resolve().parent.parent

PAGINA  = RAIZ / "reservar.html"
DESTINO = RAIZ / "pruebas" / "pantalla-dia-hora.html"

# La prueba vive una carpeta más adentro que el sitio, así que sus rutas suben.
SUBIR = "../"

# Las horas que atiende el consultorio, en bloques de 30. Salen de la agenda
# real de Cecilia (§ 9.1), pero acá son sólo el molde de la prueba.
HORAS = [
    "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
    "12:00", "12:30",
    "15:00", "15:30", "16:00", "16:30", "17:00", "17:30", "18:00", "18:30",
]


def recortar_la_pantalla():
    """La <section> de la pantalla ④, tal cual está en `reservar.html`.

    Se busca por el `id` y no por las clases, por lo mismo que en
    `armar-prueba-quien.py`: las clases se mueven, el `id` lo usa `pasos.js`
    para mostrar el paso y nadie lo toca de pasada.
    """
    pagina = PAGINA.read_text( encoding = "utf-8" )

    ancla    = pagina.index( 'id="paso-dia-hora"' )
    arranque = pagina.rindex( "<section", 0, ancla )

    # 🔴 EL CIERRE SE BUSCA CONTANDO, NO CON EL PRIMER `</section>`, y esto se
    # arregló el 30-sep-2026 después de que saliera mal: ESTA pantalla tiene
    # una <section> ADENTRO —el cajón de horarios—, así que el primer cierre
    # que aparece es el de adentro. El recorte salía cortado justo antes de los
    # botones, la pantalla cargaba sin ellos, y `dia-hora.js` se caía buscando
    # un botón que no estaba: un error de RECORTE que se leía como un error de
    # la pantalla.
    profundidad = 0
    cursor = arranque

    while True:

        abre  = pagina.find( "<section", cursor + 1 )
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

    # Sin `hidden`: acá la pantalla es lo único que hay, y arranca a la vista.
    # El `hidden` del cajón de horarios SÍ se conserva —por eso el `1`—: ése no
    # es la pantalla, es una parte que aparece recién al elegir un día.
    return pagina[ arranque : cierre ].replace( " hidden>", ">", 1 )


def agenda_inventada():
    """Dos meses de agenda con los seis estados repartidos a propósito.

    El reparto NO es al azar: cada regla de abajo existe para que un estado
    quede visible en algún lado. Un mes generado al azar puede salir sin un
    solo día lleno y dejar ese caso sin mirar, que es justo lo que esta
    herramienta viene a evitar.
    """
    hoy = date.today()

    primero = hoy.replace( day = 1 )

    dias = []

    # Dos meses corridos desde el 1 del mes actual: es la ventana de reserva.
    fecha = primero

    while fecha < primero + timedelta( days = 62 ):

        dias.append( { "fecha": fecha.isoformat(), "bloques": bloques_del_dia( fecha, hoy ) } )

        fecha += timedelta( days = 1 )

    return dias


def bloques_del_dia( fecha, hoy ):
    """Las horas de un día, con el estado que le toca por la regla de arriba."""

    # SÁBADO Y DOMINGO NO SE ATIENDE: la lista vacía es «ese día no hay
    # agenda», que es distinto de «hay agenda y está toda tomada». El portero
    # hace esa misma distinción y la pantalla tiene que verse igual en las dos.
    if fecha.weekday() >= 5:
        return []

    # EL DÍA 8 DE CADA MES ES UN FERIADO: agenda vacía en medio de la semana.
    if fecha.day == 8:
        return []

    bloques = []

    for numero, hora in enumerate( HORAS ):

        inicio = f"{ fecha.isoformat() }T{ hora }:00-03:00"

        bloques.append( { "inicio": inicio, "estado": estado_del_bloque( fecha, hoy, numero ) } )

    return bloques


def estado_del_bloque( fecha, hoy, numero ):
    """Qué estado le toca a un bloque, para que los cuatro se vean."""

    # TODO LO QUE YA PASÓ, Y LO DE HOY, ESTÁ FUERA DE PLAZO. La ventana de
    # reserva tiene un piso de 12 horas, así que el día en curso nunca se puede
    # reservar entero.
    if fecha <= hoy:
        return "fuera_de_plazo"

    # EL DÍA 15 DE CADA MES ESTÁ LLENO: sirve para ver un día que tiene agenda
    # y aun así viene gris en el almanaque.
    if fecha.day == 15:
        return "ocupado"

    # UN BLOQUE DE CADA CINCO, TOMADO.
    if numero % 5 == 2:
        return "ocupado"

    # EL ÚLTIMO DE LA MAÑANA NO ENTRA: un tratamiento de 60 minutos no cabe
    # antes del corte del mediodía. Es el estado que más cuesta provocar en la
    # agenda real, porque depende de qué tratamiento se eligió.
    if HORAS[ numero ] == "12:30":
        return "no_entra"

    return "libre"


CUERPO_JS = r'''
  // ── LO QUE NORMALMENTE PONEN `auth.js` Y `motivo.js` ──
  //
  // Esta página no entra con Google ni pasa por las pantallas anteriores, así
  // que las tres cosas que `dia-hora.js` espera encontrar puestas se ponen acá
  // a mano. Son las MISMAS variables, con los mismos nombres: si alguna
  // cambiara de nombre, esta prueba se rompe en vez de mentir.
  const SUPABASE_URL = 'https://ejemplo.invalido';
  const SUPABASE_CLAVE_PUBLICA = 'clave-de-prueba';

  function tokenDeLaSesion() {
    return 'token-de-prueba';
  }

  let tratamientoElegido = 1;

  const AGENDA = AGENDA_INVENTADA;

  const PROFESIONALES = [
    { id: 1, nombre: 'Cecilia', apellido: 'Brassesco' },
    { id: 2, nombre: 'Ana', apellido: 'Ruiz' }
  ];

  // ── EL PEDIDO AL PORTERO, INTERCEPTADO ──
  //
  // Se reemplaza `fetch` en vez de llamar a `dibujarElAlmanaque()` con datos
  // puestos a mano, y la diferencia importa: así corre el camino ENTERO —armar
  // la consulta, leer la respuesta, filtrar por día y dibujar—. Saltearse el
  // pedido dejaría sin probar justo la parte que más se toca.
  const fetchDeVerdad = window.fetch;

  window.fetch = async function ( direccion ) {

    if ( String( direccion ).includes( 'horarios-disponibles' ) ) {

      const pedido = new URL( direccion );
      const desde = pedido.searchParams.get( 'desde' );
      const hasta = pedido.searchParams.get( 'hasta' );

      // Se recorta igual que lo haría el portero: la pantalla pide un mes y
      // tiene que recibir un mes, no los dos.
      const dias = AGENDA.filter( ( dia ) => dia.fecha >= desde && dia.fecha <= hasta );

      return {
        ok: true,
        json: async () => ( { dias: dias } )
      };
    }

    return fetchDeVerdad( direccion );
  };
'''


def armar():
    pantalla = recortar_la_pantalla()

    cuerpo = CUERPO_JS.replace(
        "AGENDA_INVENTADA",
        json.dumps( agenda_inventada() ),
    )

    DESTINO.parent.mkdir( exist_ok = True )

    DESTINO.write_text( f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Prueba · la pantalla ④ con una agenda inventada</title>
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Marcellus&family=Jost:wght@300;400;500;600;700&display=swap">
  <link rel="stylesheet" href="{ SUBIR }css/tokens.css">
  <link rel="stylesheet" href="{ SUBIR }css/styles.css">
</head>
<body>
  <main>
{ pantalla }
  </main>

<script>
{ cuerpo }
</script>
<script src="{ SUBIR }js/pasos.js"></script>
<script src="{ SUBIR }js/dia-hora.js"></script>
<script>
  // Arranca la pantalla como lo haría `motivo.js` al tocar «Continuar».
  prepararLaPantallaDeDiaHora( PROFESIONALES );
</script>
</body>
</html>
""", encoding = "utf-8" )

    print( f"✓ { DESTINO.relative_to( RAIZ ) }" )
    print( f"  { len( agenda_inventada() ) } días inventados, desde el 1 del mes actual" )


if __name__ == "__main__":
    armar()
