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

import time

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


# ── LO QUE CONTESTAN LOS ENDPOINTS DE LA ⑤.3 ────────────────────────────────
#
# Tres apellidos que se parecen a propósito: así se ve si la lista de
# resultados se puede recorrer con la vista o si hay que leer renglón por
# renglón. Y uno SIN CORREO, que es el caso que la pantalla tiene que decir en
# voz alta — es el que no va a recibir ningún aviso.
PACIENTES = [
    { "id": 101, "nombre": "Marta",     "apellido": "Brassesco",
      "email": "marta.brassesco@ejemplo.test", "telefono": "3425550101" },
    { "id": 102, "nombre": "Rodrigo",   "apellido": "Brassesco",
      "email": "rodri.brassesco@ejemplo.test", "telefono": None },
    { "id": 103, "nombre": "Valentina", "apellido": "Bravo",
      "email": None, "telefono": "3425550103" },
]

PROFESIONALES = [
    { "id": 1,  "nombre": "Cecilia", "apellido": "Brassesco", "es_admin": True },
    { "id": 2,  "nombre": "Martín",  "apellido": "Brassesco", "es_admin": False },
]

TRATAMIENTOS_INVENTADOS = [
    { "id": 1, "nombre": "consulta" },
    { "id": 2, "nombre": "limpieza" },
    { "id": 3, "nombre": "ortodoncia" },
    { "id": 4, "nombre": "blanqueamiento" },
]

COBERTURAS = [
    { "id": 1, "nombre": "Particular" },
    { "id": 2, "nombre": "OSDE" },
    { "id": 3, "nombre": "IAPOS" },
]


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

  const PACIENTES_INVENTADOS     = PACIENTES_DE_PRUEBA;
  const PROFESIONALES_INVENTADOS = PROFESIONALES_DE_PRUEBA;
  const TRATAMIENTOS_DE_PRUEBA   = TRATAMIENTOS_PUESTOS;
  const COBERTURAS_INVENTADAS    = COBERTURAS_PUESTAS;

  // ── EL PLANTEL INVENTADO — siete filas elegidas por lo que cada una PRUEBA ──
  const PLANTEL = [
    // La que administra y además atiende: tiene que decir las dos cosas.
    { id: 1, nombre: 'Cecilia', apellido: 'Brassesco',
      esAdmin: true, activo: true, fechaBaja: null },

    // Activo y sin nada que atender: es la fila que se apaga, porque no pide
    // ninguna acción. Y sin botón, que es lo que hay que poder ver.
    { id: 2, nombre: 'Martín', apellido: 'Sosa',
      esAdmin: false, activo: true, fechaBaja: null },

    // UN solo turno: el singular del renglón, que con un plural automático
    // diría «1 turnos».
    { id: 3, nombre: 'Lucía', apellido: 'Ferreyra',
      esAdmin: false, activo: true, fechaBaja: null },

    // 🔴 EL CASO CRÍTICO DE LA PANTALLA: de baja Y con gente esperándolo. Son
    // seis personas que van a viajar al consultorio a ver a alguien que no
    // está, y esta fila es lo único que lo dice.
    { id: 4, nombre: 'Rodrigo', apellido: 'Paz Etchegoyen',
      esAdmin: false, activo: false,
      fechaBaja: '2026-08-12T18:30:00+00:00' },

    // De baja y ya resuelto: no queda nada que hacer con esta fila.
    { id: 5, nombre: 'Valentina', apellido: 'Ruiz',
      esAdmin: false, activo: false,
      fechaBaja: '2026-05-03T14:00:00+00:00' },

    // ⚠ APAGADO SIN FECHA: pasa con lo que se apagó a mano desde el Table
    // Editor, antes de que esta pantalla existiera. La fila no inventa una
    // fecha, dice «de baja» y nada más.
    { id: 6, nombre: 'Esteban', apellido: 'Molina',
      esAdmin: false, activo: false, fechaBaja: null },

    // Un nombre largo de verdad, para ver qué le pasa al ancho a 390.
    { id: 7, nombre: 'María de los Ángeles', apellido: 'Giménez Taborda',
      esAdmin: false, activo: true, fechaBaja: null }
  ];


  // ── LOS TURNOS DE LA LUPA — `de` es de quién es cada uno ──
  //
  // Los seis del profesional 4 son el caso que importa: es el que está de baja
  // con gente esperando. Cada uno prueba una variante del renglón.
  const TURNOS_DE_LA_LUPA = [
    { de: 4, id: 101, inicio: '2026-11-17T12:00:00+00:00', duracion_min: 30,
      paciente: { nombre: 'Marta', apellido: 'Giménez',
                  telefono: '342 155-4821', email: 'marta@ejemplo.com' },
      tratamiento: { nombre: 'consulta' },
      observaciones_paciente:
        'Vengo con dolor fuerte del lado derecho desde el jueves, ' +
        'no puedo morder. Tomo ibuprofeno cada ocho horas.' },

    // Sólo correo: el teléfono es opcional en `pacientes`.
    { de: 4, id: 102, inicio: '2026-11-18T13:30:00+00:00', duracion_min: 60,
      paciente: { nombre: 'Joaquín', apellido: 'Sosa',
                  telefono: null, email: 'joaquin.sosa@ejemplo.com' },
      tratamiento: { nombre: 'limpieza' },
      observaciones_paciente: null },

    // 🔴 NI TELÉFONO NI CORREO: a esta persona no se la puede llamar, y la
    // pantalla tiene que decirlo en voz alta en vez de mostrar un hueco.
    { de: 4, id: 103, inicio: '2026-11-19T16:00:00+00:00', duracion_min: 30,
      paciente: { nombre: 'Pedro', apellido: 'Sin Contacto',
                  telefono: null, email: null },
      tratamiento: { nombre: 'consulta' },
      observaciones_paciente: 'Me da ansiedad la luz verde del aparato.' },

    // ⚠ SIN TRATAMIENTO: `tratamiento_id` acepta nulo, así que un turno
    // cargado a mano puede no tenerlo. Con `!inner` esta fila desaparecería.
    { de: 4, id: 104, inicio: '2026-11-20T12:30:00+00:00', duracion_min: 90,
      paciente: { nombre: 'Esteban', apellido: 'Molina',
                  telefono: '342 154-0099', email: null },
      tratamiento: null,
      observaciones_paciente: null },

    { de: 4, id: 105, inicio: '2026-12-02T17:30:00+00:00', duracion_min: 30,
      paciente: { nombre: 'Valentina', apellido: 'Ruiz',
                  telefono: '342 156-7731', email: 'vale.ruiz@ejemplo.com' },
      tratamiento: { nombre: 'blanqueamiento' },
      observaciones_paciente: 'Prefiero a la tarde.' },

    { de: 4, id: 106, inicio: '2027-03-09T14:00:00+00:00', duracion_min: 60,
      paciente: { nombre: 'Rodrigo', apellido: 'Paz',
                  telefono: '342 155-1234', email: null },
      tratamiento: { nombre: 'ortodoncia' },
      observaciones_paciente: null },

    // Los de otros, para que el filtro de la lupa se pueda ver funcionando.
    { de: 1, id: 107, inicio: '2026-11-17T15:00:00+00:00', duracion_min: 30,
      paciente: { nombre: 'Lucía', apellido: 'Ferreyra',
                  telefono: '342 155-8080', email: 'lucia@ejemplo.com' },
      tratamiento: { nombre: 'consulta' },
      observaciones_paciente: null },

    { de: 3, id: 108, inicio: '2026-11-21T12:00:00+00:00', duracion_min: 30,
      paciente: { nombre: 'Ana', apellido: 'Vera',
                  telefono: null, email: 'ana.vera@ejemplo.com' },
      tratamiento: { nombre: 'limpieza' },
      observaciones_paciente: null },

    { de: 6, id: 109, inicio: '2026-11-24T13:00:00+00:00', duracion_min: 30,
      paciente: { nombre: 'Carlos', apellido: 'Duarte',
                  telefono: '342 155-3344', email: null },
      tratamiento: { nombre: 'consulta' },
      observaciones_paciente: null },

    { de: 6, id: 110, inicio: '2026-12-15T16:30:00+00:00', duracion_min: 60,
      paciente: { nombre: 'Silvia', apellido: 'Ponce',
                  telefono: '342 154-7788', email: 'silvia@ejemplo.com' },
      tratamiento: { nombre: 'limpieza' },
      observaciones_paciente: null },

    { de: 7, id: 111, inicio: '2026-11-25T14:00:00+00:00', duracion_min: 30,
      paciente: { nombre: 'Nicolás', apellido: 'Ibarra',
                  telefono: '342 156-2211', email: 'nico@ejemplo.com' },
      tratamiento: { nombre: 'consulta' },
      observaciones_paciente: null },

    // 🔴 LOS SEIS DE ABAJO NO SON RELLENO — 13-oct-2026, lo levantó Juan: «los
    // turnos parece que está trayendo lo que se le canta». La coherencia estaba
    // bien (se midió fila por fila y las siete coincidían), pero el REPARTO era
    // malo: seis de siete profesionales traían cero o un turno, así que tocabas
    // tres botones seguidos y veías una tarjeta sola cada vez. Una pantalla que
    // siempre muestra UNO no se puede juzgar, y es exactamente el motivo por el
    // que esta herramienta existe desde el 8-oct.
    //
    // 🔑 El reparto que queda tiene sentido de consultorio: Cecilia 4 —es la
    // que más atiende—, Rodrigo 6 —el que se fue y dejó gente colgada—, María 3,
    // Lucía y Esteban 2, y dos en cero.
    { de: 1, id: 112, inicio: '2026-11-17T16:30:00+00:00', duracion_min: 60,
      paciente: { nombre: 'Gabriela', apellido: 'Lorenzo',
                  telefono: '342 155-9012', email: 'gabi.lorenzo@ejemplo.com' },
      tratamiento: { nombre: 'ortodoncia' },
      observaciones_paciente: 'Se me soltó un bracket de abajo.' },

    { de: 1, id: 113, inicio: '2026-11-19T13:00:00+00:00', duracion_min: 30,
      paciente: { nombre: 'Tomás', apellido: 'Arriola',
                  telefono: '342 154-5566', email: null },
      tratamiento: { nombre: 'consulta' },
      observaciones_paciente: null },

    { de: 1, id: 114, inicio: '2026-12-04T12:30:00+00:00', duracion_min: 90,
      paciente: { nombre: 'Elena', apellido: 'Quiroga',
                  telefono: '342 156-4433', email: 'elena.q@ejemplo.com' },
      tratamiento: { nombre: 'prótesis' },
      observaciones_paciente: null },

    { de: 3, id: 115, inicio: '2026-12-10T15:00:00+00:00', duracion_min: 30,
      paciente: { nombre: 'Facundo', apellido: 'Rivas',
                  telefono: '342 155-2020', email: null },
      tratamiento: { nombre: 'blanqueamiento' },
      observaciones_paciente: null },

    { de: 7, id: 116, inicio: '2026-11-26T12:00:00+00:00', duracion_min: 60,
      paciente: { nombre: 'Claudia', apellido: 'Benítez',
                  telefono: '342 155-6677', email: 'claudia.b@ejemplo.com' },
      tratamiento: { nombre: 'limpieza' },
      observaciones_paciente: 'Soy alérgica a la penicilina.' },

    { de: 7, id: 117, inicio: '2027-02-11T14:30:00+00:00', duracion_min: 30,
      paciente: { nombre: 'Hernán', apellido: 'Vidal',
                  telefono: null, email: 'hernan.vidal@ejemplo.com' },
      tratamiento: null,
      observaciones_paciente: null }
  ];


  // 🔴 EL CONTEO DE CADA FILA SE CALCULA DE LA LISTA DE ARRIBA, no se escribe a
  // mano en el plantel. Y esto no es prolijidad: la primera versión los tenía
  // tipeados y TRES DE SIETE no coincidían — la fila decía «4 turnos sin
  // atender» y la lupa abría con uno solo.
  //
  // 🔑 Lo que importa es QUÉ ENSEÑABA ESA PRUEBA: exactamente la contradicción
  // que el caso 25 de `probar-panel.sh` existe para cazar en el sistema real.
  // Una página de prueba que muestra un bug inventado hace perder el tiempo
  // buscándolo en el código, donde no está. Lo encontró Juan mirando la
  // pantalla, el 13-oct-2026.
  for ( const fila of PLANTEL ) {

    fila.turnosPendientes = TURNOS_DE_LA_LUPA.filter(
      ( turno ) => turno.de === fila.id
    ).length;
  }


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

    // ── LOS ENDPOINTS DE LA ⑤.3 ──
    //
    // El buscador filtra DE VERDAD sobre la lista inventada, en vez de
    // devolverla entera: así la pantalla se prueba con el caso que importa —
    // escribir algo que no está y que se abra el alta.
    if ( String( direccion ).includes( 'buscar-pacientes' ) ) {

      const q = new URL( direccion, location.origin )
        .searchParams.get( 'q' ).toLowerCase();

      const encontrados = PACIENTES_INVENTADOS.filter( ( p ) =>
        ( p.nombre + ' ' + p.apellido + ' ' + ( p.email || '' ) )
          .toLowerCase()
          .includes( q )
      );

      avisar( 'GET /buscar-pacientes?q=' + q +
              ' → 200, ' + encontrados.length + ' paciente(s)' );

      return {
        ok: true,
        status: 200,
        json: async () => ( { pacientes: encontrados } )
      };
    }

    // 🔴 LA GRILLA SE ARMA ACÁ ADENTRO EN VEZ DE DEVOLVER UNA LISTA FIJA, y
    // es lo que hace que esta prueba valga: lo que hay que poder juzgar es
    // que al cambiar la duración CAMBIE qué entra. Con bloques fijos la
    // pantalla se vería igual siempre y la prueba no mediría nada.
    //
    // El día inventado: se atiende de 08:00 a 12:00, hay un turno tomado de
    // 09:30 a 10:30, y lo que no llega al cierre sale como `no_entra`.
    if ( String( direccion ).includes( 'horarios-del-panel' ) ) {

      const parametros = new URL( direccion, location.origin ).searchParams;

      const dura = Number( parametros.get( 'duracion' ) );
      const dia  = parametros.get( 'fecha' );

      const ABRE   = 8 * 60;
      const CIERRA = 12 * 60;

      const TOMADO_DESDE = 9 * 60 + 30;
      const TOMADO_HASTA = 10 * 60 + 30;

      const bloques = [];

      for ( let minuto = ABRE; minuto < CIERRA; minuto += 30 ) {

        const hh = String( Math.floor( minuto / 60 ) ).padStart( 2, '0' );
        const mm = String( minuto % 60 ).padStart( 2, '0' );

        // Se pisa con lo tomado si los dos rangos se cruzan — la misma cuenta
        // que hace `bloqueOcupado` del lado del portero.
        const sePisa = minuto < TOMADO_HASTA && ( minuto + dura ) > TOMADO_DESDE;

        // No entra si lo que arranca acá termina después del cierre.
        const noEntra = ( minuto + dura ) > CIERRA;

        let estado = 'libre';

        if ( noEntra ) { estado = 'no_entra'; }
        if ( sePisa )  { estado = 'ocupado'; }

        bloques.push( {
          inicio: dia + 'T' + hh + ':' + mm + ':00-03:00',
          estado: estado
        } );
      }

      const libres = bloques.filter( ( b ) => b.estado === 'libre' ).length;

      avisar( 'GET /horarios-del-panel?fecha=' + dia + '&duracion=' + dura +
              ' → 200, ' + libres + ' libre(s) de ' + bloques.length );

      return {
        ok: true,
        status: 200,
        json: async () => ( {
          fecha: dia,
          profesional: 1,
          duracion_min: dura,
          bloques: bloques
        } )
      };
    }

    if ( String( direccion ).includes( 'profesionales-del-panel' ) ) {

      // `?admin=no` apaga el desplegable de profesional, que es la mitad de
      // esta pantalla que sólo ve Cecilia. Sin este interruptor, la vista del
      // no-admin no se puede mirar nunca.
      const esAdmin = new URLSearchParams( location.search )
        .get( 'admin' ) !== 'no';

      avisar( 'GET /profesionales-del-panel → 200, esAdmin: ' + esAdmin );

      return {
        ok: true,
        status: 200,
        json: async () => ( {
          esAdmin: esAdmin,
          yo: 2,
          profesionales: PROFESIONALES_INVENTADOS
        } )
      };
    }

    if ( String( direccion ).includes( 'obras-sociales' ) ) {
      return { ok: true, status: 200, json: async () => COBERTURAS_INVENTADAS };
    }

    if ( String( direccion ).includes( 'tratamientos' ) ) {
      return { ok: true, status: 200, json: async () => TRATAMIENTOS_DE_PRUEBA };
    }

    if ( String( direccion ).includes( 'paciente-del-panel' ) ) {

      const enviado = JSON.parse( opciones.body );

      avisar( 'POST /paciente-del-panel → 201' );

      return {
        ok: true,
        status: 201,
        json: async () => ( {
          paciente: {
            id: 999,
            nombre: enviado.nombre,
            apellido: enviado.apellido,
            email: enviado.email || null,
            telefono: enviado.telefono || null
          }
        } )
      };
    }

    if ( String( direccion ).includes( 'turno-del-panel' ) ) {

      const enviado = JSON.parse( opciones.body );

      avisar( 'POST /turno-del-panel → 201, inicio ' + enviado.inicio +
              ', ' + enviado.duracion_min + ' min' );

      return {
        ok: true,
        status: 201,
        json: async () => ( {
          id: 500,
          inicio: enviado.inicio,
          duracion_min: enviado.duracion_min,
          profesional: enviado.profesional_id || 2,
          avisadoAlPaciente: true
        } )
      };
    }

    // ── LOS DOS ENDPOINTS DE LA ⑤.6, REBANADA A ──
    //
    // 🔴 POR QUÉ HACEN FALTA SIETE FILAS INVENTADAS Y NO DOS: en la base real
    // hay dos profesionales, los dos activos y los dos admin. Con eso no se
    // puede juzgar esta lista — no se ve el renglón de una baja con fecha, ni
    // la fila apagada del que no tiene nada que atender, ni qué le pasa al
    // ancho con un apellido compuesto. Es el mismo motivo por el que esta
    // herramienta nació el 8-oct.
    if ( String( direccion ).includes( 'plantel-del-panel' ) ) {

      avisar( 'GET /plantel-del-panel → 200, ' + PLANTEL.length + ' fila(s)' );

      return {
        ok: true,
        status: 200,
        json: async () => ( { yo: 1, plantel: PLANTEL } )
      };
    }

    if ( String( direccion ).includes( 'turnos-del-profesional' ) ) {

      const deQuien = Number(
        new URL( direccion, location.origin ).searchParams.get( 'profesional' )
      );

      const suyos = TURNOS_DE_LA_LUPA.filter(
        ( turno ) => turno.de === deQuien
      );

      avisar( 'GET /turnos-del-profesional?profesional=' + deQuien +
              ' → 200, ' + suyos.length + ' turno(s)' );

      return {
        ok: true,
        status: 200,
        json: async () => ( { profesional: deQuien, turnos: suyos } )
      };
    }

    return fetchDeVerdad( direccion, opciones );
  };


  function avisar( texto ) {
    const registro = document.querySelector( '#registro' );
    registro.textContent = texto + '\n' + registro.textContent;
  }
'''


# 🔴 EL SELLO QUE LE SACA EL CACHÉ DE ENCIMA AL NAVEGADOR — 13-oct-2026.
#
# QUÉ PASÓ: se corrigieron `js/fechas.js` y `js/panel.js`, se rearmó esta
# página, Juan recargó y seguía viendo la versión vieja. El HTML se regenera en
# cada corrida y por eso llega siempre fresco; los `.js` y el `.css` NO se
# regeneran, se enlazan — así que el navegador los sirve de su propia memoria.
#
# ⚠ Y NO ALCANZA CON QUE EL SERVIDOR MANDE `no-store`, que ya lo manda: esa
# cabecera viaja con la RESPUESTA, y para un archivo que el navegador decidió
# no volver a pedir no hay respuesta donde ponerla. El pedido nunca sale.
#
# 🔑 LA SALIDA ES CAMBIAR LA DIRECCIÓN, no pedir permiso: con `?v=<momento>`
# pegado, cada armado produce una URL que el navegador nunca vio, así que no
# tiene nada guardado que reusar. Es la misma idea que el `dist/` versionado
# del sitio, aplicada a una página de prueba.
#
# Esto reemplaza al «acordate de hacer Cmd+Shift+R», que es trabajo manual para
# algo que la herramienta puede garantizar.
SELLO = str( int( time.time() ) )


def armar():

    def comoJs( datos ):
        return json.dumps( datos, ensure_ascii = False )

    cuerpo = CUERPO_JS \
        .replace( "TURNOS_INVENTADOS", comoJs( TURNOS ) ) \
        .replace( "CASOS_INVENTADOS", comoJs( CASOS ) ) \
        .replace( "PACIENTES_DE_PRUEBA", comoJs( PACIENTES ) ) \
        .replace( "PROFESIONALES_DE_PRUEBA", comoJs( PROFESIONALES ) ) \
        .replace( "TRATAMIENTOS_PUESTOS", comoJs( TRATAMIENTOS_INVENTADOS ) ) \
        .replace( "COBERTURAS_PUESTAS", comoJs( COBERTURAS ) )

    pacientes_json = comoJs( PACIENTES )

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
  <link rel="stylesheet" href="{ SUBIR }css/tokens.css?v={ SELLO }">
  <link rel="stylesheet" href="{ SUBIR }css/styles.css?v={ SELLO }">
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
  <br>
  cargar un turno:
  <a href="?caso=cargar">como Cecilia (admin)</a> ·
  <a href="?caso=cargar&amp;admin=no">como un profesional</a>
  <br>
  altas y bajas:
  <a href="?caso=plantel">el plantel</a> ·
  <a href="?caso=plantel&amp;lupa=4">la lupa del que está de baja</a>
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

{ recortar( "paso-cargar" ) }

{ recortar( "paso-plantel" ) }

{ recortar( "paso-lupa" ) }

{ recortar_el_cartel() }
  </main>

<script>
{ cuerpo }
</script>
<script src="{ SUBIR }js/fechas.js?v={ SELLO }"></script>
<script src="{ SUBIR }js/pasos.js?v={ SELLO }"></script>
<script>
  // `pasos.js` arranca guardando la pantalla que está a la vista, y en la
  // página de verdad ésa es la de entrar. Acá no está, así que la de la agenda
  // ocupa su lugar: sin esto, el primer cambio de pantalla se cae.
  pantallaALaVista = document.querySelector( '#paso-agenda' );
</script>
<script src="{ SUBIR }js/panel.js?v={ SELLO }"></script>
<script>
  const PACIENTES_PUESTOS = { pacientes_json };

  // Arranca la pantalla como lo haría el login.
  irAlDia( '{ DIA }' );

  // 🔴 EL AUTOCHEQUEO DE VERSIÓN — 13-oct-2026, y nació de una tarde perdida.
  //
  // QUÉ PASÓ: se corrigió el código, Juan recargó y seguía viendo lo viejo. Se
  // verificó el código ejecutándolo —estaba bien—, se verificó el archivo en
  // disco —estaba bien— y aun así la pantalla mostraba otra cosa. No había
  // ninguna forma de saber QUÉ VERSIÓN estaba corriendo el navegador, así que
  // las dos partes discutían sobre pantallas distintas.
  //
  // 🔑 LO QUE ESTA LÍNEA RESUELVE: la página se mide a sí misma y lo dice en
  // voz alta. Si el renglón no aparece, el JS ni siquiera llegó hasta acá; si
  // aparece con la fecha vieja, el navegador está sirviendo código viejo y el
  // problema no está en el código. Un diagnóstico que antes costaba una ronda
  // de mensajes ahora se lee de la pantalla.
  avisar(
    'versión ' + { SELLO } + ' · prueba de fecha: "' +
    diaDeUnInstante( '2026-08-12T18:30:00+00:00' ) +
    '" ← tiene que decir «12 de agosto de 2026»'
  );

  // El atajo a la solapa: `?caso=plantel` la abre sola, y `&lupa=<id>` entra
  // directo a los turnos de ese profesional. Una captura no toca botones.
  const atajo = new URLSearchParams( location.search );

  if ( atajo.get( 'caso' ) === 'plantel' ) {{

    document.querySelector( '#ir-al-plantel' ).click();

    const deQuien = atajo.get( 'lupa' );

    if ( deQuien ) {{

      // El plantel se dibuja con un `await`, así que el renglón todavía no
      // existe cuando esto corre. Mismo motivo y mismo remedio que el retardo
      // de la pantalla de carga, unas líneas más abajo.
      setTimeout( () => {{

        const fila = PLANTEL.find(
          ( uno ) => String( uno.id ) === deQuien
        );

        if ( fila ) {{
          irALaLupa( fila );
        }}
      }}, 300 );
    }}
  }}

  // El caso `cargar` entra directo a la pantalla de la ⑤.3, que de otro modo
  // sólo se alcanza tocando el botón — y una captura no toca botones.
  if ( new URLSearchParams( location.search ).get( 'caso' ) === 'cargar' ) {{

    document.querySelector( '#ir-a-cargar' ).click();

    // 🔴 LOS TRES ESTADOS DE ESTA PANTALLA NO SE ALCANZAN SIN TOCAR NADA, y
    // una captura no toca nada. `?con=` los enciende:
    //
    //   buscando → la lista de resultados a la vista
    //   elegido  → el formulario del turno, que es el estado largo
    //   alta     → la ficha nueva, que sólo aparece si no hay coincidencias
    const con = new URLSearchParams( location.search ).get( 'con' );

    // ⚠ EL RETARDO NO ES UN ADORNO: el oyente de «Cargar un turno» es `async`
    // y llena los desplegables con un `await`, así que lo de abajo correría
    // ANTES de que estén puestos. Con la grilla de horas eso se vio enseguida
    // —salía el texto «elegí día y duración» con el día ya en pantalla—, y es
    // el modo de falla típico de una prueba que simula clics: no da error,
    // fotografía un estado intermedio.
    setTimeout( () => {{

      if ( con === 'buscando' || con === 'elegido' ) {{
        elegirPaciente( PACIENTES_PUESTOS[ 0 ] );
      }}

      if ( con === 'buscando' ) {{
        volverAlBuscador();
        dibujarResultados( PACIENTES_PUESTOS );
        document.querySelector( '#buscar-resultados' ).hidden = false;
      }}

      if ( con === 'alta' ) {{
        mostrarElAlta( true );
      }}

      // La duración se puede fijar desde la dirección: es lo que deja mirar
      // en una captura que con 90 minutos entran muchos menos bloques.
      const dura = new URLSearchParams( location.search ).get( 'dura' );

      if ( dura ) {{
        const campo = document.querySelector( '#turno-duracion' );
        campo.value = dura;
        campo.dispatchEvent( new Event( 'change' ) );
      }}

    }}, 150 );
  }}
</script>
</body>
</html>
""", encoding = "utf-8" )

    print( f"✓ { DESTINO.relative_to( RAIZ ) }" )
    print( "  http://localhost:8000/pruebas/pantalla-panel.html?caso=lleno" )


if __name__ == "__main__":
    armar()
