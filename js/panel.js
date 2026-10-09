// EL PANEL — etapa ⑤.1, la agenda del día.
//
// QUÉ HACE ESTE ARCHIVO, en una línea: muestra los turnos de un día y deja
// moverse de día en día.
//
// 🔑 LO QUE SE MUESTRA NO LO DECIDE ESTA PANTALLA: el portero devuelve todos
// los profesionales si el que entró es admin, y sólo los suyos si no lo es.
// Acá no se filtra nada, así que no hay forma de que la pantalla muestre de
// más — y tampoco de que un botón escondido tape un permiso que falta.
//
// 🔴 Y POR ESO ESTA PÁGINA NO PREGUNTA SI ALGUIEN ES ADMIN PARA DECIDIR QUÉ
// PEDIR. Pide la agenda y dibuja lo que vuelve. Si la cerradura se rompiera
// mañana, lo que falla es el portero, no esta pantalla: una sola cosa que
// arreglar y un solo lugar donde mirar.


const DIRECCION_DE_LA_AGENDA = SUPABASE_URL + '/functions/v1/agenda-del-dia';

const DIRECCION_DE_CANCELAR = SUPABASE_URL + '/functions/v1/cancelar-del-panel';


const titulo = document.querySelector( '#agenda-titulo' );

const campoFecha = document.querySelector( '#agenda-fecha' );

const lista = document.querySelector( '#agenda-lista' );

const vacia = document.querySelector( '#agenda-vacia' );

const aviso = document.querySelector( '#agenda-aviso' );


// ══════════════════════════════════════════════════════════════════════
// QUÉ DÍA ES HOY
// ══════════════════════════════════════════════════════════════════════

/**
 * El día de hoy EN SANTA FE, como 'AAAA-MM-DD'.
 *
 * 🔴 No se usa `new Date().toISOString().slice( 0, 10 )`, que es la forma
 * corta y está mal acá: eso da el día en UTC, y a las 21:30 de un jueves de
 * Santa Fe en UTC ya es viernes. El panel abriría en la agenda de mañana
 * justo en el horario en que alguien lo estaría mirando para cerrar el día.
 *
 * Es la misma distinción que `fechas.js` resuelve para los turnos: el día del
 * consultorio no es el día del servidor ni el del navegador.
 */
function hoyEnSantaFe() {

  const pedazos = new Intl.DateTimeFormat( 'en-CA', {
    timeZone: ZONA_DEL_CONSULTORIO,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  } ).format( new Date() );

  // 'en-CA' devuelve justamente 'AAAA-MM-DD', que es la forma que pide el
  // portero y la que entiende un `input type="date"`.
  return pedazos;
}


/** El día de al lado: `cuantos` puede ser -1 o 1. */
function diaCorrido( fecha, cuantos ) {

  // La cuenta va en UTC a propósito y es correcta porque acá no hay horas: un
  // 9 de octubre es el 9 de octubre en cualquier huso. Es el mismo criterio
  // que usa `listarDias` en el portero.
  const instante = new Date( fecha + 'T00:00:00Z' );

  instante.setUTCDate( instante.getUTCDate() + cuantos );

  return instante.toISOString().slice( 0, 10 );
}


// ══════════════════════════════════════════════════════════════════════
// PEDIR Y DIBUJAR
// ══════════════════════════════════════════════════════════════════════

/**
 * Le pide al portero la agenda de un día.
 *
 * Devuelve el paquete, o el texto 'sin-acceso' si el portero contestó 403, o
 * `null` si falló por otra cosa.
 *
 * 🔑 EL 403 SE SEPARA DE LOS DEMÁS ERRORES porque significan cosas distintas
 * para el que mira: uno es «esta página no es para vos» y el otro es «probá de
 * nuevo». Juntarlos le haría reintentar a quien nunca va a entrar.
 */
async function pedirLaAgenda( fecha ) {

  const respuesta = await fetch(
    DIRECCION_DE_LA_AGENDA + '?fecha=' + fecha,
    {
      headers: {
        'apikey': SUPABASE_CLAVE_PUBLICA,
        'Authorization': 'Bearer ' + tokenDeLaSesion()
      }
    }
  );

  if ( respuesta.status === 403 ) {
    return 'sin-acceso';
  }

  if ( !respuesta.ok ) {
    console.error( 'No se pudo leer la agenda. Estado:', respuesta.status );
    return null;
  }

  return await respuesta.json();
}


/**
 * Qué dice la segunda línea de la tarjeta: «consulta · Cecilia Brassesco».
 *
 * 🔑 EL MOTIVO MANDA SOBRE EL TRATAMIENTO CUANDO SON DISTINTOS, igual que en
 * la pantalla del paciente: el turno se agenda como `consulta` y a qué vino
 * queda en `motivo_consulta_id`. Mostrar «consulta» a secas le esconde a quien
 * atiende el dato que necesita para prepararse.
 *
 * ⚠️ Y EL PROFESIONAL VA SIEMPRE, también cuando hay uno solo. El día que
 * entre el segundo, la agenda del admin mezcla a los dos y la tarjeta tiene
 * que decir de quién es el turno sin que haya que cambiar nada acá.
 */
function queDiceElTurno( turno ) {

  const nombre = turno.motivo ? turno.motivo.nombre : turno.tratamiento.nombre;

  const partes = [
    nombre,
    turno.profesional.nombre + ' ' + turno.profesional.apellido,
  ];

  // LA COBERTURA SÓLO SI VINO. Es el dato que la § 14 pedía explícito —«el
  // panel nace con la columna puesta»— y va al final del renglón callado: hace
  // falta tenerla a mano, no es lo primero que se busca.
  if ( turno.obra_social ) {
    partes.push( turno.obra_social.nombre );
  }

  return partes.join( ' · ' );
}


/**
 * Arma UN renglón de la agenda.
 *
 * 🔴 TODO LO QUE VIENE DE LA BASE SE ESCRIBE CON `textContent` y nunca pegando
 * HTML: son nombres que escribió una persona, y pegados como HTML un nombre
 * con `<script>` adentro se ejecutaría. Es la defensa contra XSS
 * (Cross-Site Scripting), la misma de las otras pantallas.
 *
 * 🔴 NO USA LA PIEZA `.turno` DEL PACIENTE, y el porqué está escrito al lado de
 * `.turno-agenda` en el CSS: las dos muestran un turno, pero una se mira de a
 * una y la otra se barre de a diez. El error del 8-oct-2026 fue suponer que
 * eran la misma pieza porque llevan el mismo dato.
 */
function renglonDeTurno( turno ) {

  const renglon = document.createElement( 'div' );
  renglon.className = 'turno-agenda';

  const hora = document.createElement( 'div' );
  hora.className = 'agenda-hora';

  const numero = document.createElement( 'span' );
  numero.className = 'agenda-numero';
  numero.textContent = horaDelTurno( turno.inicio );

  const dura = document.createElement( 'span' );
  dura.className = 'agenda-dura';
  dura.textContent = turno.duracion_min + ' min';

  hora.append( numero, dura );

  const datos = document.createElement( 'div' );
  datos.className = 'agenda-datos';

  const paciente = document.createElement( 'p' );
  paciente.className = 'agenda-paciente';
  paciente.textContent = turno.paciente.nombre + ' ' + turno.paciente.apellido;

  const detalle = document.createElement( 'p' );
  detalle.className = 'agenda-detalle';
  detalle.textContent = queDiceElTurno( turno );

  datos.append( paciente, detalle );

  renglon.append( hora, datos, accionesDelTurno( turno ) );

  return renglon;
}


/**
 * Los dos botones de un renglón.
 *
 * 🔴 NINGUNO HACE NADA SOLO: los dos abren el cartel que pregunta. Cancelar no
 * se deshace —libera el horario, que alguien puede tomar en el minuto
 * siguiente, y dispara los tres correos—, así que la pregunta no es una
 * formalidad. Es la misma decisión que ya tomó la pantalla del paciente el
 * 2-oct-2026, y por el mismo motivo: si el mismo píxel cambia de significado,
 * dos toques rápidos cancelan sin que nadie lea nada.
 */
function accionesDelTurno( turno ) {

  const caja = document.createElement( 'div' );
  caja.className = 'agenda-acciones';

  const modificar = document.createElement( 'button' );
  modificar.type = 'button';
  modificar.className = 'btn btn-2';
  modificar.textContent = 'Modificar';

  // ⏳ TODAVÍA NO HAY A DÓNDE MANDARLO: mover un turno de hora choca contra el
  // constraint de no-solapamiento, que rebota con 409, y eso es una pantalla
  // con su propia conversación. Queda APAGADO y no escondido, a propósito: el
  // botón dice que la acción va a existir, y apagado no miente sobre hoy.
  modificar.disabled = true;
  modificar.classList.add( 'btn-apagado' );
  modificar.title = 'Todavía no disponible';

  const cancelar = document.createElement( 'button' );
  cancelar.type = 'button';
  cancelar.className = 'btn btn-2';
  cancelar.textContent = 'Cancelar';

  cancelar.addEventListener( 'click', () => {
    abrirElCartel( turno );
  } );

  caja.append( modificar, cancelar );

  return caja;
}


/**
 * Pide un día y lo dibuja.
 *
 * Devuelve 'ok', 'sin-acceso' o 'falló'.
 */
async function mostrarElDia( fecha ) {

  aviso.hidden = true;

  const datos = await pedirLaAgenda( fecha );

  if ( datos === 'sin-acceso' ) {
    return 'sin-acceso';
  }

  if ( !datos ) {
    return 'falló';
  }

  titulo.textContent = diaEnPalabras( datos.fecha );

  campoFecha.value = datos.fecha;

  // Se vacía antes de colgar: sin esto, cambiar de día APILA los turnos del
  // día nuevo debajo de los del anterior. No falla con error — muestra el
  // doble.
  lista.replaceChildren();

  const hayTurnos = datos.turnos.length > 0;

  for ( const turno of datos.turnos ) {
    lista.appendChild( renglonDeTurno( turno ) );
  }

  lista.hidden = !hayTurnos;
  vacia.hidden = hayTurnos;

  return 'ok';
}


/** Cambia de día y avisa si algo salió mal. */
async function irAlDia( fecha ) {

  const resultado = await mostrarElDia( fecha );

  if ( resultado === 'sin-acceso' ) {
    reemplazarPor( '#paso-sin-acceso' );
    return;
  }

  if ( resultado === 'falló' ) {
    aviso.hidden = false;
    aviso.textContent = 'No pudimos leer la agenda de ese día. Probá de nuevo.';
  }
}


// ══════════════════════════════════════════════════════════════════════
// EL CARTEL QUE PREGUNTA ANTES DE CANCELAR
// ══════════════════════════════════════════════════════════════════════

// EL TURNO QUE EL CARTEL ESTÁ PREGUNTANDO SI SE CANCELA, o `null` si está
// cerrado. Se guarda el turno ENTERO y no sólo su `id` porque el cartel tiene
// que DECIR CUÁL: flota encima de la lista y tapa el renglón que se acaba de
// tocar.
let turnoDelCartel = null;


const cartel = document.querySelector( '#cartel-cancelar' );


/** Abre el cartel preguntando por un turno. */
function abrirElCartel( turno ) {

  turnoDelCartel = turno;

  document.querySelector( '#cartel-cuando' ).textContent =
    horaDelTurno( turno.inicio ) + ' · ' + turno.duracion_min + ' min';

  // 🔴 EL NOMBRE DE LA PACIENTE VA EN EL CARTEL, y en el panel no es lo mismo
  // que en la pantalla del paciente: allá todos los turnos son de quien mira.
  // Acá la lista puede tener diez de diez personas distintas, y este renglón
  // es lo único que separa cancelar el turno correcto de cancelarle a otra.
  document.querySelector( '#cartel-que' ).textContent =
    turno.paciente.nombre + ' ' + turno.paciente.apellido + ' — ' + queDiceElTurno( turno );

  cartel.showModal();
}


function cerrarElCartel() {

  turnoDelCartel = null;

  cartel.close();
}


document.querySelector( '#cartel-no' ).addEventListener( 'click', cerrarElCartel );


document.querySelector( '#cartel-si' ).addEventListener( 'click', async () => {

  // Se guarda antes de cerrar: cerrar vacía `turnoDelCartel`.
  const turno = turnoDelCartel;

  const boton = document.querySelector( '#cartel-si' );

  // 🔴 EL BOTÓN SE APAGA MIENTRAS VIAJA EL PEDIDO. Sin esto, dos toques mandan
  // dos cancelaciones del mismo turno: la segunda rebota con 403 —el portero
  // la frena— pero quien mira ve un error donde no hubo ninguno.
  boton.disabled = true;

  let respuesta;

  try {
    respuesta = await fetch(
      DIRECCION_DE_CANCELAR,
      {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_CLAVE_PUBLICA,
          'Authorization': 'Bearer ' + tokenDeLaSesion(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify( { turno_id: turno.id } )
      }
    );
  }
  catch {
    respuesta = null;
  }

  boton.disabled = false;

  cerrarElCartel();

  if ( !respuesta || !respuesta.ok ) {
    aviso.hidden = false;
    aviso.textContent = 'No pudimos cancelar ese turno. Probá de nuevo.';
    return;
  }

  const datos = await respuesta.json();

  // 🔴 SE RECARGA EL DÍA EN VEZ DE SACAR EL RENGLÓN A MANO. Sacarlo sería más
  // rápido y mentiría en un caso real: entre que se abrió la agenda y se tocó
  // cancelar, otra persona pudo reservar ese hueco. Lo que se vuelve a dibujar
  // es lo que la base dice ahora.
  await irAlDia( campoFecha.value );

  // ⚠️ EL AVISO SÓLO CUANDO NO SE LE PUDO ESCRIBIR A LA PACIENTE. El portero
  // cancela igual —el horario tiene que quedar libre— pero si no tenía correo
  // cargado, nadie le avisó: alguien tiene que llamarla.
  if ( datos.avisadoAlPaciente === false ) {
    aviso.hidden = false;
    aviso.textContent =
      'Turno cancelado. ⚠️ Esta paciente no tiene correo cargado, así que NO se le avisó: hay que llamarla.';
  }
} );


// ══════════════════════════════════════════════════════════════════════
// LA NAVEGACIÓN DE DÍAS
// ══════════════════════════════════════════════════════════════════════

document.querySelector( '#dia-anterior' ).addEventListener( 'click', () => {
  irAlDia( diaCorrido( campoFecha.value, -1 ) );
} );


document.querySelector( '#dia-siguiente' ).addEventListener( 'click', () => {
  irAlDia( diaCorrido( campoFecha.value, 1 ) );
} );


// `change` y no `input`: el almanaque del teléfono dispara `input` mientras la
// persona gira las ruedas, y eso pediría la agenda de cada día que pasa por
// delante.
campoFecha.addEventListener( 'change', () => {

  // El campo puede quedar vacío si se borra a mano, y un pedido sin fecha da
  // 400. Se vuelve a hoy, que es la respuesta útil.
  irAlDia( campoFecha.value || hoyEnSantaFe() );
} );


// ══════════════════════════════════════════════════════════════════════
// CARGAR UN TURNO A MANO — etapa ⑤.3
// ══════════════════════════════════════════════════════════════════════
//
// 🔑 LA PANTALLA NO DEFIENDE NADA, igual que la agenda. Esconde el desplegable
// de profesional cuando quien entró no es admin, pero eso es para no ofrecer
// lo que después va a rebotar — la defensa está en el portero, que ignora ese
// campo si quien pide no es admin. Si mañana alguien edita el HTML desde su
// navegador, no consigue nada.

const DIRECCION_DE_BUSCAR = SUPABASE_URL + '/functions/v1/buscar-pacientes';

const DIRECCION_DE_FICHA = SUPABASE_URL + '/functions/v1/paciente-del-panel';

const DIRECCION_DEL_TURNO = SUPABASE_URL + '/functions/v1/turno-del-panel';

const DIRECCION_DEL_STAFF = SUPABASE_URL + '/functions/v1/profesionales-del-panel';

const DIRECCION_DE_LAS_HORAS = SUPABASE_URL + '/functions/v1/horarios-del-panel';

const DIRECCION_DE_TRATAMIENTOS = SUPABASE_URL + '/functions/v1/tratamientos';

const DIRECCION_DE_COBERTURAS = SUPABASE_URL + '/functions/v1/obras-sociales';


// A quién se le está cargando el turno. Vacío mientras no se haya elegido, y
// es lo que decide si el bloque de abajo se ve o no.
let pacienteElegido = null;

// El instante elegido en la grilla, tal cual lo mandó el portero
// ('2026-10-15T09:00:00-03:00'). Vacío mientras no se haya tocado ninguno.
//
// 🔑 SE GUARDA EL TEXTO DEL PORTERO, NO UNA FECHA. El dato ya viene con el
// desfase de acá puesto; pasarlo por `new Date()` para volver a escribirlo es
// abrir la puerta a que se corra una hora sin que nadie lo note. Es la misma
// decisión que tomó la grilla del paciente.
let horaElegida = null;

// Los desplegables se llenan UNA sola vez por visita a la pantalla. Sin esta
// marca, entrar y salir dos veces duplicaría las opciones.
let desplegablesListos = false;


function cabecerasConSesion() {

  return {
    'apikey': SUPABASE_CLAVE_PUBLICA,
    'Authorization': 'Bearer ' + tokenDeLaSesion()
  };
}


/**
 * Abre o cierra el alta de ficha.
 *
 * 🔑 Y DE PASO ESCONDE «Volver a la agenda», que es el motivo por el que esto
 * es una función y no un `hidden` suelto en tres lugares. Con el alta abierta
 * quedaban DOS botones «Volver» uno debajo del otro, iguales de forma y de
 * color: la pantalla ofrecía dos salidas sin decir a dónde va cada una.
 * Mientras se está en el medio de algo, la única salida visible es la de ese
 * algo.
 */
function mostrarElAlta( abierta ) {

  document.querySelector( '#alta-paciente' ).hidden = !abierta;

  document.querySelector( '#volver-a-agenda' ).hidden = abierta;
}


function avisarEnLaCarga( texto ) {

  const cartel = document.querySelector( '#cargar-aviso' );

  cartel.hidden = !texto;
  cartel.textContent = texto || '';
}


// ── EL BUSCADOR ───────────────────────────────────────────────────────

/**
 * Le pide al portero los pacientes que coinciden con lo tipeado.
 *
 * Devuelve la lista, o `null` si el pedido falló. Una lista vacía NO es un
 * fallo: es la respuesta que abre el alta de ficha.
 */
async function buscarPacientes( termino ) {

  const respuesta = await fetch(
    DIRECCION_DE_BUSCAR + '?q=' + encodeURIComponent( termino ),
    { headers: cabecerasConSesion() }
  );

  if ( !respuesta.ok ) {
    console.error( 'No se pudo buscar. Estado:', respuesta.status );
    return null;
  }

  const datos = await respuesta.json();

  return datos.pacientes;
}


/**
 * Dibuja los resultados como botones: se elige tocando, nunca tipeando.
 */
function dibujarResultados( pacientes ) {

  const caja = document.querySelector( '#buscar-resultados' );

  caja.textContent = '';

  pacientes.forEach( ( paciente ) => {

    const fila = document.createElement( 'button' );

    fila.type = 'button';
    fila.className = 'resultado-paciente';

    const quien = document.createElement( 'span' );

    quien.className = 'resultado-quien';
    quien.textContent = paciente.apellido + ', ' + paciente.nombre;

    const contacto = document.createElement( 'span' );

    contacto.className = 'resultado-contacto';

    // ⚠️ «Sin correo» se DICE, no se deja en blanco. Es el dato que decide si
    // esa persona se va a enterar de su turno, y un renglón vacío se lee como
    // «no lo cargamos todavía» en vez de como «no tiene».
    contacto.textContent = paciente.email
      || paciente.telefono
      || 'Sin correo ni teléfono';

    fila.append( quien, contacto );

    fila.addEventListener( 'click', () => {
      elegirPaciente( paciente );
    } );

    caja.appendChild( fila );
  } );

  caja.hidden = pacientes.length === 0;
}


function elegirPaciente( paciente ) {

  pacienteElegido = paciente;

  document.querySelector( '#buscar-resultados' ).hidden = true;
  document.querySelector( '#buscar-ayuda' ).hidden = true;
  document.querySelector( '#buscar-paciente' ).hidden = true;

  mostrarElAlta( false );

  document.querySelector( '#elegido-quien' ).textContent =
    paciente.apellido + ', ' + paciente.nombre;

  document.querySelector( '#elegido-contacto' ).textContent =
    paciente.email || 'Sin correo: este turno no le avisa a nadie';

  document.querySelector( '#paciente-elegido' ).hidden = false;
  document.querySelector( '#datos-del-turno' ).hidden = false;

  avisarEnLaCarga( '' );

  // El bloque del turno recién aparece acá, así que éste es el primer momento
  // en que la grilla tiene sentido.
  dibujarLasHoras();
}


function volverAlBuscador() {

  pacienteElegido = null;
  horaElegida = null;

  document.querySelector( '#paciente-elegido' ).hidden = true;
  document.querySelector( '#datos-del-turno' ).hidden = true;

  mostrarElAlta( false );

  const campo = document.querySelector( '#buscar-paciente' );

  campo.hidden = false;
  campo.value = '';
  campo.focus();

  document.querySelector( '#buscar-ayuda' ).hidden = false;
  document.querySelector( '#buscar-resultados' ).hidden = true;

  avisarEnLaCarga( '' );
}


// ── LOS DESPLEGABLES ──────────────────────────────────────────────────

function opcionesDe( select, filas, comoSeLee ) {

  select.textContent = '';

  filas.forEach( ( fila ) => {

    const opcion = document.createElement( 'option' );

    opcion.value = fila.id;
    opcion.textContent = comoSeLee( fila );

    select.appendChild( opcion );
  } );
}


/**
 * Llena los tres desplegables que vienen de la base.
 *
 * 🔑 EL DE PROFESIONAL SÓLO SE MUESTRA A UN ADMIN. Quien no lo sea carga
 * turnos para sí mismo, y el portero fuerza eso aunque la pantalla mandara
 * otra cosa.
 */
async function llenarLosDesplegables() {

  if ( desplegablesListos ) {
    return;
  }

  // Los dos públicos no mandan sesión: el catálogo de tratamientos y la lista
  // de coberturas los lee también el paciente desde el sitio.
  const sinSesion = { headers: { 'apikey': SUPABASE_CLAVE_PUBLICA } };

  const [ staff, tratamientos, coberturas ] = await Promise.all( [
    fetch( DIRECCION_DEL_STAFF, { headers: cabecerasConSesion() } ),
    fetch( DIRECCION_DE_TRATAMIENTOS, sinSesion ),
    fetch( DIRECCION_DE_COBERTURAS, sinSesion )
  ] );

  if ( !staff.ok || !tratamientos.ok || !coberturas.ok ) {
    avisarEnLaCarga( 'No pudimos cargar las listas. Probá de nuevo.' );
    return;
  }

  const datosStaff = await staff.json();

  if ( datosStaff.esAdmin ) {

    opcionesDe(
      document.querySelector( '#turno-profesional' ),
      datosStaff.profesionales,
      ( fila ) => fila.nombre + ' ' + fila.apellido
    );

    document.querySelector( '#campo-profesional' ).hidden = false;
  }

  opcionesDe(
    document.querySelector( '#turno-tratamiento' ),
    await tratamientos.json(),
    ( fila ) => fila.nombre
  );

  opcionesDe(
    document.querySelector( '#turno-cobertura' ),
    await coberturas.json(),
    ( fila ) => fila.nombre
  );

  desplegablesListos = true;
}


// ── EL ALTA DE FICHA ──────────────────────────────────────────────────

async function crearLaFicha() {

  const correo = document.querySelector( '#alta-correo' ).value.trim();

  const repetido = document.querySelector( '#alta-correo-2' ).value.trim();

  // 🔒 La comparación se hace TAMBIÉN acá, aunque el portero la repita. No es
  // defensa duplicada: es que rebotar en el navegador le avisa a quien escribe
  // en el acto, mientras todavía tiene el teléfono en la mano.
  if ( correo && correo.toLowerCase() !== repetido.toLowerCase() ) {
    avisarEnLaCarga( 'Los dos correos no coinciden.' );
    return;
  }

  const respuesta = await fetch(
    DIRECCION_DE_FICHA,
    {
      method: 'POST',
      headers: {
        ...cabecerasConSesion(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify( {
        nombre: document.querySelector( '#alta-nombre' ).value,
        apellido: document.querySelector( '#alta-apellido' ).value,
        telefono: document.querySelector( '#alta-telefono' ).value,
        email: correo,
        email_repetido: repetido
      } )
    }
  );

  const datos = await respuesta.json();

  if ( !respuesta.ok ) {
    avisarEnLaCarga( datos.error || 'No pudimos crear la ficha.' );
    return;
  }

  elegirPaciente( datos.paciente );
}


// ── LA GRILLA DE HORAS ────────────────────────────────────────────────

/**
 * Le pide al portero los bloques de ese día, con ESA duración.
 *
 * Devuelve la lista de bloques, o `null` si el pedido falló.
 */
async function pedirLasHoras( fecha, duracion, profesionalId ) {

  let direccion = DIRECCION_DE_LAS_HORAS
    + '?fecha=' + fecha
    + '&duracion=' + duracion;

  // Sólo viaja si hay desplegable de profesional, o sea si quien entró es
  // admin. El portero lo ignora igual cuando no corresponde.
  if ( profesionalId ) {
    direccion = direccion + '&profesional=' + profesionalId;
  }

  const respuesta = await fetch( direccion, { headers: cabecerasConSesion() } );

  if ( !respuesta.ok ) {
    console.error( 'No se pudieron leer las horas. Estado:', respuesta.status );
    return null;
  }

  const datos = await respuesta.json();

  return datos.bloques;
}


/**
 * Una casilla de la grilla.
 *
 * 🔑 LOS BLOQUES QUE NO SE PUEDEN ELEGIR SE DIBUJAN IGUAL, APAGADOS. Es la
 * decisión del 6-ago: un día con todo tomado tiene que verse distinto de un
 * día en que no se atiende, y escondiendo lo que no sirve los dos quedan
 * iguales. Acá además importa más que en la web — lo que quien atiende
 * necesita ver es DÓNDE se pisa, no sólo dónde entra.
 */
function casillaDeLaHora( bloque ) {

  const hora = document.createElement( 'button' );

  hora.type = 'button';
  hora.className = 'hora';

  // La hora se lee del texto que mandó el portero y NO se convierte a fecha:
  // el dato ya viene con el desfase de acá puesto.
  hora.textContent = bloque.inicio.slice( 11, 16 );

  if ( bloque.estado !== 'libre' ) {

    hora.className = 'hora hora-apagada';
    hora.disabled = true;

    // ⚠️ EL MOTIVO VA EN EL `title` Y NO A LA VISTA. En la grilla del paciente
    // los tres motivos se pintan con el mismo gris a propósito; acá quien
    // atiende sí necesita distinguirlos —«ocupado» se destraba cancelando, «no
    // entra» no—, pero ponerlo en cada casilla llenaría la grilla de texto.
    hora.title = bloque.estado === 'ocupado'
      ? 'Ya hay un turno en ese horario'
      : 'No entra un turno de esa duración';

    return hora;
  }

  if ( bloque.inicio === horaElegida ) {
    hora.classList.add( 'hora-elegida' );
  }

  hora.addEventListener( 'click', () => {
    horaElegida = bloque.inicio;
    dibujarLasHoras();
  } );

  return hora;
}


/**
 * Vuelve a pedir y a dibujar la grilla.
 *
 * 🔴 SE LLAMA CADA VEZ QUE CAMBIA EL DÍA, LA DURACIÓN O EL PROFESIONAL, y los
 * tres importan: la grilla contesta «qué entra», y esa respuesta cambia con
 * los tres. Volver a pedirla sólo al cambiar el día dejaría los bloques
 * dibujados para una duración que ya no es la elegida — y se vería bien.
 */
async function dibujarLasHoras() {

  const caja = document.querySelector( '#turno-horas' );

  const ayuda = document.querySelector( '#horas-ayuda' );

  const fecha = document.querySelector( '#turno-fecha' ).value;

  const duracion = document.querySelector( '#turno-duracion' ).value;

  if ( !fecha ) {

    caja.hidden = true;
    ayuda.hidden = false;
    ayuda.textContent = 'Elegí día y duración para ver los horarios.';

    return;
  }

  const campoProfesional = document.querySelector( '#campo-profesional' );

  const profesionalId = campoProfesional.hidden
    ? null
    : document.querySelector( '#turno-profesional' ).value;

  const bloques = await pedirLasHoras( fecha, duracion, profesionalId );

  if ( bloques === null ) {

    caja.hidden = true;
    ayuda.hidden = false;
    ayuda.textContent = 'No pudimos leer los horarios. Probá de nuevo.';

    return;
  }

  // Un día sin bloques es el domingo, o el feriado, o una ausencia cargada.
  // No es un error y se dice con sus palabras.
  if ( bloques.length === 0 ) {

    caja.hidden = true;
    ayuda.hidden = false;
    ayuda.textContent = 'Ese día no se atiende.';

    return;
  }

  caja.textContent = '';

  bloques.forEach( ( bloque ) => {
    caja.appendChild( casillaDeLaHora( bloque ) );
  } );

  caja.hidden = false;

  // ⚠️ SI TODO ESTÁ APAGADO SE DICE, aunque la grilla se vea. Una pantalla
  // llena de casillas grises sin una línea que lo explique se lee como un
  // error de carga.
  const hayAlguno = bloques.some( ( bloque ) => bloque.estado === 'libre' );

  ayuda.hidden = hayAlguno;

  if ( !hayAlguno ) {
    ayuda.textContent = 'Con esa duración no entra ningún turno ese día.';
  }
}


// ── AGENDAR ───────────────────────────────────────────────────────────

async function agendarElTurno() {

  const dia = document.querySelector( '#turno-fecha' ).value;

  if ( !horaElegida ) {
    avisarEnLaCarga( 'Elegí un horario de la grilla.' );
    return;
  }

  // 🔑 EL INSTANTE ES EL QUE MANDÓ EL PORTERO, tal cual, con su desfase ya
  // puesto. No se arma pegando el día y la hora: ese camino —el del campo de
  // hora que esta pantalla tenía antes— obliga a calcular la zona horaria acá,
  // y cualquier error ahí corre el turno sin que nada falle.
  const inicio = horaElegida;

  const cuerpo = {
    paciente_id: pacienteElegido.id,
    tratamiento_id: Number( document.querySelector( '#turno-tratamiento' ).value ),
    obra_social_id: Number( document.querySelector( '#turno-cobertura' ).value ),
    duracion_min: Number( document.querySelector( '#turno-duracion' ).value ),
    inicio: inicio,
    observaciones_paciente: document.querySelector( '#turno-nota' ).value
  };

  // Sólo viaja si el campo está a la vista, o sea si quien entró es admin. El
  // portero lo ignora igual cuando no corresponde: esto es para no mandar un
  // dato que no significa nada.
  const campoProfesional = document.querySelector( '#campo-profesional' );

  if ( !campoProfesional.hidden ) {
    cuerpo.profesional_id =
      Number( document.querySelector( '#turno-profesional' ).value );
  }

  const respuesta = await fetch(
    DIRECCION_DEL_TURNO,
    {
      method: 'POST',
      headers: {
        ...cabecerasConSesion(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify( cuerpo )
    }
  );

  const datos = await respuesta.json();

  // 🔑 EL 409 SE DICE CON SUS PALABRAS, no como un error del sistema: significa
  // que ese horario ya está ocupado, que es información útil y no una falla.
  if ( respuesta.status === 409 ) {
    avisarEnLaCarga( 'Ese horario se pisa con otro turno. Probá otra hora.' );
    return;
  }

  if ( !respuesta.ok ) {
    avisarEnLaCarga( datos.error || 'No pudimos agendar el turno.' );
    return;
  }

  // ⚠️ LO QUE SE DICE AL VOLVER CAMBIA SEGÚN SI EL AVISO SALIÓ. Un turno
  // agendado del que el paciente no se enteró necesita que alguien lo llame, y
  // esa diferencia no puede quedar sólo en la respuesta del portero.
  volverAlBuscador();

  irAlDia( dia );

  reemplazarPor( '#paso-agenda' );

  const cartel = document.querySelector( '#agenda-aviso' );

  cartel.hidden = false;

  cartel.textContent = datos.avisadoAlPaciente
    ? 'Turno agendado y avisado por correo.'
    : 'Turno agendado. El paciente NO tiene correo: hay que avisarle por teléfono.';
}


// ── LOS OYENTES ───────────────────────────────────────────────────────

document.querySelector( '#ir-a-cargar' ).addEventListener( 'click', async () => {

  reemplazarPor( '#paso-cargar' );

  volverAlBuscador();

  // 🔴 EL DÍA SE PONE ANTES DEL `await`, y el orden importa. La grilla de
  // horas se dibuja al elegir el paciente, y si para entonces este campo
  // todavía estuviera vacío, saldría el texto «elegí día y duración» con el
  // día ya puesto en pantalla. Nada falla: la grilla simplemente no aparece.
  //
  // El día arranca en el que se está mirando: lo más probable es que el turno
  // sea para ese día, que es el que Cecilia tiene delante.
  document.querySelector( '#turno-fecha' ).value =
    campoFecha.value || hoyEnSantaFe();

  await llenarLosDesplegables();
} );


document.querySelector( '#volver-a-agenda' ).addEventListener( 'click', () => {
  reemplazarPor( '#paso-agenda' );
} );


document.querySelector( '#cambiar-paciente' ).addEventListener(
  'click',
  volverAlBuscador
);


document.querySelector( '#alta-cancelar' ).addEventListener(
  'click',
  volverAlBuscador
);


document.querySelector( '#alta-guardar' ).addEventListener(
  'click',
  crearLaFicha
);


document.querySelector( '#turno-guardar' ).addEventListener(
  'click',
  agendarElTurno
);


// 🔴 LOS TRES CAMPOS QUE CAMBIAN LA RESPUESTA DE LA GRILLA, y los tres tienen
// que volver a pedirla. Es el punto de toda esta pantalla: con qué duración se
// mira cambia qué entra, y un hueco de media hora no sirve para una ortodoncia
// de 90.
//
// ⚠️ LA HORA ELEGIDA SE BORRA al cambiar cualquiera de los tres. Dejarla
// puesta es el modo de falla silencioso de esta pieza: se elige un bloque con
// 30 minutos, se cambia la duración a 90, y el bloque sigue marcado aunque ya
// no entre. El turno se mandaría contra un horario que la grilla nueva no
// ofrece — y la base lo rebotaría con un 409 que parece un bug.
[ '#turno-fecha', '#turno-duracion', '#turno-profesional' ].forEach( ( cual ) => {

  document.querySelector( cual ).addEventListener( 'change', () => {
    horaElegida = null;
    dibujarLasHoras();
  } );
} );


// 🔑 EL BUSCADOR ESPERA A QUE LA PERSONA DEJE DE TIPEAR, y sin esto cada tecla
// sería un pedido: escribir «Brassesco» son diez. El reloj se reinicia en cada
// tecla y recién dispara cuando pasaron 300 ms sin ninguna.
let relojDeLaBusqueda = null;

// 🔴 EL NÚMERO DE PEDIDO — y esto NO es precaución teórica, es el segundo bug
// que apareció el 9-oct-2026 pegado al primero.
//
// `clearTimeout` cancela el pedido que todavía NO SALIÓ; al que ya está en
// vuelo no lo alcanza. Así que si se escribe una letra más mientras la
// respuesta viene en camino, hay DOS pedidos vivos y **vuelven en el orden que
// quieran** — el de la red, no el del teclado. Si el viejo llega último, pisa
// los resultados buenos con los suyos.
//
// Y pisarlos no es sólo mostrar de más: si el viejo trae CERO, la pantalla
// esconde la lista y abre el alta de ficha. Desde afuera se ve como lo
// describió Juan: «aparece un momento, desaparece, no te deja clickearlo».
//
// Cada búsqueda se lleva un número. Al volver, la que no sea la última se
// DESCARTA sin tocar nada.
let ultimaBusqueda = 0;

document.querySelector( '#buscar-paciente' ).addEventListener( 'input', ( evento ) => {

  clearTimeout( relojDeLaBusqueda );

  const termino = evento.target.value.trim();

  const ayuda = document.querySelector( '#buscar-ayuda' );

  if ( termino.length < 2 ) {

    document.querySelector( '#buscar-resultados' ).hidden = true;

    mostrarElAlta( false );

    ayuda.hidden = false;
    ayuda.textContent = 'Escribí al menos dos letras.';

    return;
  }

  relojDeLaBusqueda = setTimeout( async () => {

    ultimaBusqueda = ultimaBusqueda + 1;

    const mia = ultimaBusqueda;

    const pacientes = await buscarPacientes( termino );

    // Llegó tarde: mientras venía, se escribió otra letra y salió otro pedido.
    // Lo que esta respuesta dice ya no es lo que hay en el campo.
    if ( mia !== ultimaBusqueda ) {
      return;
    }

    if ( pacientes === null ) {
      avisarEnLaCarga( 'No pudimos buscar. Probá de nuevo.' );
      return;
    }

    dibujarResultados( pacientes );

    // Ninguna coincidencia es el caso que abre el alta: es la única puerta
    // para crear una ficha, y se llega a ella DESPUÉS de haber buscado.
    const nadie = pacientes.length === 0;

    mostrarElAlta( nadie );

    ayuda.hidden = !nadie;

    if ( nadie ) {
      ayuda.textContent = 'No aparece nadie con ese dato. Podés crear la ficha.';
    }

  }, 300 );
} );


// ══════════════════════════════════════════════════════════════════════
// EL ARRANQUE
// ══════════════════════════════════════════════════════════════════════

// SI YA ENTRÓ EN ESTA PESTAÑA, LA AGENDA SALE DIRECTO — el mismo arreglo que
// `mis-turnos.js`: para quien usa el sitio no hay dos páginas, hay un lugar
// donde ya se identificó.
//
// 🔑 Se cambia de pantalla ANTES de que lleguen los datos, a propósito: si se
// esperara la respuesta, asomaría la pantalla de entrar y desaparecería. Lo
// que se ve mientras tanto es el título y nada más, que es la verdad.
if ( haySesion() ) {

  reemplazarPor( '#paso-agenda' );

  irAlDia( hoyEnSantaFe() );
}


prepararElBoton( {

  contenedor: document.querySelector( '#boton-google' ),

  alEntrar: async () => {

    const resultado = await mostrarElDia( hoyEnSantaFe() );

    // 🔴 EL 403 SE ATIENDE ACÁ Y NO DESPUÉS DE MOSTRAR LA AGENDA: un paciente
    // que entre a esta dirección con su cuenta tiene que ver «esta página no
    // es para pacientes», no una agenda vacía que lo deje creyendo que el
    // sistema se rompió.
    if ( resultado === 'sin-acceso' ) {
      reemplazarPor( '#paso-sin-acceso' );
      return;
    }

    if ( resultado === 'falló' ) {
      const avisoEntrar = document.querySelector( '#aviso-entrar' );
      avisoEntrar.hidden = false;
      avisoEntrar.textContent = 'Entraste, pero no pudimos leer la agenda. Probá de nuevo.';
      return;
    }

    reemplazarPor( '#paso-agenda' );
  },

  alFallar: () => {
    const avisoEntrar = document.querySelector( '#aviso-entrar' );
    avisoEntrar.hidden = false;
    avisoEntrar.textContent = 'No pudimos entrar. Probá de nuevo.';
  }
} );
