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

  // 🔑 ESTE BOTÓN NO PREGUNTA NADA Y EL DE AL LADO SÍ, y la diferencia es de
  // fondo: mover lleva a una pantalla donde se elige el horario nuevo y recién
  // ahí se confirma —el paso de la grilla ES la pregunta—, mientras cancelar
  // pasa de un toque a un turno liberado y tres correos. Un cartel acá sería
  // preguntar «¿seguro?» antes de mostrar lo que se va a decidir.
  modificar.addEventListener( 'click', () => {
    irAMover( turno );
  } );

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

  // 🔒 EL BOTÓN DE «ALTAS Y BAJAS» SE DESTAPA ACÁ y no en una función propia,
  // porque este es el único lugar donde el front ya sabe si quien entró es
  // admin: el dato viene en la respuesta de la agenda, que es el primer pedido
  // que hace la pantalla. No hay una segunda consulta para preguntarlo.
  //
  // ⚠ Y ESCONDERLO NO ES LA CERRADURA: los dos endpoints de esa solapa
  // contestan 403 a un no-admin. Esto sólo evita ofrecer una puerta cerrada.
  document.querySelector( '#ir-al-plantel' ).hidden = !datos.esAdmin;

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

// LA GRILLA DE ESTA PANTALLA, descrita en un objeto.
//
// 🔑 HAY DOS PANTALLAS QUE ELIGEN HORA —cargar un turno y moverlo— Y LA GRILLA
// ES UNA SOLA PIEZA, dibujada por una sola función. Lo que cambia de una a la
// otra es DATO, no lógica: en qué ids dibuja, de qué profesional es, qué turno
// no cuenta como ocupado, y qué hora está elegida. Por eso viaja en un objeto
// en vez de duplicar las tres funciones. *(Es el mismo criterio con el que la
// ⑤.3 extrajo el cálculo a `_shared/grilla.ts`: el cálculo se comparte.)*
//
// 🔑 LA HORA ELEGIDA SE GUARDA COMO EL TEXTO QUE MANDÓ EL PORTERO, NO COMO UNA
// FECHA ('2026-10-15T09:00:00-03:00'). El dato ya viene con el desfase de acá
// puesto; pasarlo por `new Date()` para volver a escribirlo es abrir la puerta
// a que se corra una hora sin que nadie lo note. Es la misma decisión que tomó
// la grilla del paciente.
const grillaDeCarga = {

  caja: '#turno-horas',
  ayuda: '#horas-ayuda',
  fecha: '#turno-fecha',
  duracion: '#turno-duracion',

  // Lo pone quien pide el dibujado y no se lee adentro de la función: en esta
  // pantalla sale del desplegable, y en la de mover sale del turno.
  profesionalId: null,

  // El turno que no cuenta como ocupado. Acá no hay ninguno: en esta pantalla
  // el turno todavía no existe.
  excepto: null,

  elegida: null
};

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
  refrescarLaCarga();
}


function volverAlBuscador() {

  pacienteElegido = null;
  grillaDeCarga.elegida = null;

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
async function pedirLasHoras( fecha, duracion, profesionalId, excepto ) {

  let direccion = DIRECCION_DE_LAS_HORAS
    + '?fecha=' + fecha
    + '&duracion=' + duracion;

  // Sólo viaja si hay desplegable de profesional, o sea si quien entró es
  // admin. El portero lo ignora igual cuando no corresponde.
  if ( profesionalId ) {
    direccion = direccion + '&profesional=' + profesionalId;
  }

  // 🔑 SÓLO LO MANDA LA PANTALLA DE MOVER: dice qué turno NO cuenta como
  // ocupado. Sin esto el turno que se está moviendo se tapa a sí mismo y no se
  // lo puede dejar a la misma hora con otra duración.
  if ( excepto ) {
    direccion = direccion + '&excepto=' + excepto;
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
function casillaDeLaHora( bloque, grilla ) {

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

  if ( bloque.inicio === grilla.elegida ) {
    hora.classList.add( 'hora-elegida' );
  }

  hora.addEventListener( 'click', () => {
    grilla.elegida = bloque.inicio;
    dibujarLasHoras( grilla );
  } );

  return hora;
}


/**
 * Vuelve a pedir y a dibujar UNA grilla — la de cargar o la de mover.
 *
 * `grilla` es uno de los dos objetos descriptores (`grillaDeCarga`,
 * `grillaDeMover`): de ahí salen los ids donde dibujar, de qué profesional es
 * y qué turno no cuenta como ocupado.
 *
 * 🔴 SE LLAMA CADA VEZ QUE CAMBIA EL DÍA, LA DURACIÓN O EL PROFESIONAL, y los
 * tres importan: la grilla contesta «qué entra», y esa respuesta cambia con
 * los tres. Volver a pedirla sólo al cambiar el día dejaría los bloques
 * dibujados para una duración que ya no es la elegida — y se vería bien.
 *
 * 🔑 NO LEE NINGÚN ID A MANO, y es lo que la deja servir a las dos pantallas.
 * Hasta el 13-oct-2026 nombraba adentro los cinco ids de la pantalla de cargar
 * un turno; la alternativa era copiarla con otros cinco, y entonces el día que
 * se arregle un modo de falla de la grilla habría que acordarse de arreglarlo
 * dos veces.
 */
async function dibujarLasHoras( grilla ) {

  const caja = document.querySelector( grilla.caja );

  const ayuda = document.querySelector( grilla.ayuda );

  const fecha = document.querySelector( grilla.fecha ).value;

  const duracion = document.querySelector( grilla.duracion ).value;

  if ( !fecha ) {

    caja.hidden = true;
    ayuda.hidden = false;
    ayuda.textContent = 'Elegí día y duración para ver los horarios.';

    return;
  }

  const bloques = await pedirLasHoras(
    fecha,
    duracion,
    grilla.profesionalId,
    grilla.excepto
  );

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
    caja.appendChild( casillaDeLaHora( bloque, grilla ) );
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


/**
 * Pone al día de quién es la grilla de CARGA y la vuelve a dibujar.
 *
 * 🔑 EL PROFESIONAL SE LEE ACÁ Y NO ADENTRO DE `dibujarLasHoras`, porque de
 * dónde sale es justamente lo que distingue a las dos pantallas: en ésta sale
 * del desplegable —y sólo hay desplegable si quien entró es admin—, y en la de
 * mover sale del turno que se está moviendo.
 */
function refrescarLaCarga() {

  const campoProfesional = document.querySelector( '#campo-profesional' );

  grillaDeCarga.profesionalId = campoProfesional.hidden
    ? null
    : document.querySelector( '#turno-profesional' ).value;

  dibujarLasHoras( grillaDeCarga );
}


// ── AGENDAR ───────────────────────────────────────────────────────────

async function agendarElTurno() {

  const dia = document.querySelector( '#turno-fecha' ).value;

  if ( !grillaDeCarga.elegida ) {
    avisarEnLaCarga( 'Elegí un horario de la grilla.' );
    return;
  }

  // 🔑 EL INSTANTE ES EL QUE MANDÓ EL PORTERO, tal cual, con su desfase ya
  // puesto. No se arma pegando el día y la hora: ese camino —el del campo de
  // hora que esta pantalla tenía antes— obliga a calcular la zona horaria acá,
  // y cualquier error ahí corre el turno sin que nada falle.
  const inicio = grillaDeCarga.elegida;

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
    grillaDeCarga.elegida = null;
    refrescarLaCarga();
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


// ── LA SOLAPA DEL PLANTEL Y LA LUPA — etapa ⑤.6, rebanada A ───────────────

const DIRECCION_DEL_PLANTEL = SUPABASE_URL + '/functions/v1/plantel-del-panel';

const DIRECCION_DE_LA_LUPA =
  SUPABASE_URL + '/functions/v1/turnos-del-profesional'

const DIRECCION_DEL_ALTA = SUPABASE_URL + '/functions/v1/alta-de-profesional'

const DIRECCION_DE_LA_BAJA = SUPABASE_URL + '/functions/v1/baja-de-profesional'


// Quién está mirando. Lo contesta el portero junto con el plantel, y se guarda
// para una sola cosa: no dibujarle el botón de darse de baja a sí mismo.
let yoSoy = null;


/**
 * Qué dice el renglón callado de una fila del plantel.
 *
 * 🔑 EL ESTADO Y EL CONTEO VAN EN LA MISMA FRASE, no en dos columnas: «de baja
 * el martes 12 de agosto de 2026 · 6 turnos sin atender» se lee de un tirón, y
 * es exactamente la combinación que decide si hay que hacer algo. Partidos en
 * dos columnas obligan a cruzar la vista para armar el sentido.
 */
function queDiceLaFila( fila ) {

  const partes = [];

  if ( fila.activo ) {
    partes.push( 'en actividad' );
  }
  else if ( fila.fechaBaja ) {
    partes.push( 'de baja el ' + diaDeUnInstante( fila.fechaBaja ) );
  }
  else {
    // Apagado sin fecha: pasa con las filas que se apagaron antes de que
    // existiera esta pantalla, o a mano desde el Table Editor. No se inventa
    // una fecha.
    partes.push( 'de baja' );
  }

  if ( fila.esAdmin ) {
    partes.push( 'administra' );
  }

  if ( fila.turnosPendientes === 0 ) {
    partes.push( 'sin turnos pendientes' );
  }
  else if ( fila.turnosPendientes === 1 ) {
    partes.push( '1 turno sin atender' );
  }
  else {
    partes.push( fila.turnosPendientes + ' turnos sin atender' );
  }

  return partes.join( ' · ' );
}


/**
 * Arma UN renglón del plantel.
 *
 * 🔴 TODO LO QUE VIENE DE LA BASE VA CON `textContent`, nunca pegando HTML:
 * son nombres que escribió una persona. Misma defensa contra XSS
 * (Cross-Site Scripting) que el resto de las pantallas.
 *
 * 🔑 EL BOTÓN DE LOS TURNOS SÓLO APARECE SI HAY TURNOS. Un botón que abre una
 * lista vacía no informa: hace que alguien toque, espere y no encuentre nada.
 * Que esté o no esté ES el dato.
 */
function renglonDelPlantel( fila ) {

  const renglon = document.createElement( 'div' );
  renglon.className = 'fila-plantel';

  const datos = document.createElement( 'div' );
  datos.className = 'plantel-datos';

  const quien = document.createElement( 'p' );
  quien.className = 'plantel-quien';
  quien.textContent = fila.nombre + ' ' + fila.apellido;

  const estado = document.createElement( 'p' );
  estado.className = 'plantel-estado';
  estado.textContent = queDiceLaFila( fila );

  // Las filas sobre las que no hay nada que hacer se dicen más apagadas. No es
  // decoración: en una lista de diez, lo que se busca son las que piden algo.
  if ( fila.activo && fila.turnosPendientes === 0 ) {
    estado.classList.add( 'plantel-sin-nada' );
  }

  datos.append( quien, estado );

  renglon.appendChild( datos );

  const acciones = document.createElement( 'div' );
  acciones.className = 'plantel-acciones';

  if ( fila.turnosPendientes > 0 ) {

    const ver = document.createElement( 'button' );
    ver.type = 'button';
    ver.className = 'btn btn-2';
    ver.textContent = 'Ver turnos';

    // El nombre entero va en la etiqueta accesible: «Ver turnos» repetido ocho
    // veces no le dice a un lector de pantalla de quién es cada uno.
    ver.setAttribute(
      'aria-label',
      'Ver los turnos sin atender de ' + fila.nombre + ' ' + fila.apellido
    );

    ver.addEventListener( 'click', () => {
      irALaLupa( fila );
    } );

    acciones.appendChild( ver );
  }

  // 🔴 LA PROPIA FILA NO LLEVA BOTÓN DE BAJA, y el `yo` que lo decide sale del
  // portero, no de nada que el navegador sepa por su cuenta. Apagarse a sí
  // mismo hace perder el acceso al panel en el pedido siguiente, y si era el
  // único admin ya no queda nadie que pueda devolverlo desde acá.
  //
  // ⚠ Esconder el botón NO es la cerradura: `baja-de-profesional` contesta 409
  // a ese pedido aunque llegue. Esto sólo evita ofrecer una puerta que no abre.
  if ( fila.id !== yoSoy ) {

    const estado = document.createElement( 'button' );
    estado.type = 'button';
    estado.className = 'btn btn-2';

    const quien = fila.nombre + ' ' + fila.apellido;

    if ( fila.activo ) {

      estado.textContent = 'Dar de baja';
      estado.setAttribute( 'aria-label', 'Dar de baja a ' + quien );

      // 🔴 EL BOTÓN NO APAGA NADA SOLO: abre el cartel que pregunta. Dar de
      // baja deja gente esperando un turno con alguien que ya no está, así que
      // la pregunta no es una formalidad.
      estado.addEventListener( 'click', () => {
        abrirElCartelDeBaja( fila );
      } );
    }
    else {

      estado.textContent = 'Volver a activar';
      estado.setAttribute( 'aria-label', 'Volver a activar a ' + quien );

      // 🔑 ÉSTE SÍ VA DIRECTO, Y NO ES UNA INCONSISTENCIA: prender a alguien no
      // le saca nada a nadie y se deshace con el botón de al lado. Preguntar
      // en los dos lados enseñaría a contestar que sí sin leer, que es lo que
      // hace inútil la pregunta del lado que importa.
      estado.addEventListener( 'click', () => {
        cambiarElEstado( fila, true );
      } );
    }

    acciones.appendChild( estado );
  }

  // 🔑 EL BOTÓN DE TRATAMIENTOS SÓLO PARA QUIEN ESTÁ EN ACTIVIDAD, y no es una
  // regla del portero: a alguien que no atiende, qué tratamientos tenía
  // prendidos no le cambia nada a nadie. Ofrecerlo sumaría un tercer botón en
  // la fila donde menos sirve.
  //
  // ⚠ Esta fila SÍ lo lleva cuando es la propia: el interruptor es de Cecilia
  // sobre el suyo Y sobre el de todos.
  if ( fila.activo ) {

    const cuales = document.createElement( 'button' );
    cuales.type = 'button';
    cuales.className = 'btn btn-2';
    cuales.textContent = 'Tratamientos';

    cuales.setAttribute(
      'aria-label',
      'Qué tratamientos hace ' + fila.nombre + ' ' + fila.apellido
    );

    cuales.addEventListener( 'click', () => {
      irALosTratamientos( fila );
    } );

    acciones.appendChild( cuales );
  }

  if ( acciones.childElementCount > 0 ) {
    renglon.appendChild( acciones );
  }

  return renglon;
}


/** Pide el plantel. Devuelve los datos, 'sin-acceso' o null. */
async function pedirElPlantel() {

  const respuesta = await fetch(
    DIRECCION_DEL_PLANTEL,
    { headers: cabecerasConSesion() }
  );

  if ( respuesta.status === 403 ) {
    return 'sin-acceso';
  }

  if ( !respuesta.ok ) {
    console.error( 'No se pudo leer el plantel. Estado:', respuesta.status );
    return null;
  }

  return await respuesta.json();
}


async function mostrarElPlantel() {

  const ayuda = document.querySelector( '#plantel-ayuda' );
  const lista = document.querySelector( '#plantel-lista' );
  const aviso = document.querySelector( '#plantel-aviso' );

  aviso.hidden = true;
  lista.hidden = true;
  ayuda.hidden = false;
  ayuda.textContent = 'Cargando el plantel…';

  const datos = await pedirElPlantel();

  if ( datos === 'sin-acceso' ) {
    ayuda.hidden = true;
    aviso.hidden = false;
    aviso.textContent = 'Esta solapa es sólo para quien administra.';
    return;
  }

  if ( !datos ) {
    ayuda.hidden = true;
    aviso.hidden = false;
    aviso.textContent = 'No pudimos cargar el plantel. Probá de nuevo.';
    return;
  }

  yoSoy = datos.yo;

  // Se vacía antes de colgar: sin esto, entrar dos veces a la solapa APILA el
  // plantel debajo del anterior. No falla con error — muestra el doble.
  lista.replaceChildren();

  for ( const fila of datos.plantel ) {
    lista.appendChild( renglonDelPlantel( fila ) );
  }

  ayuda.hidden = true;
  lista.hidden = false;
}


/**
 * Arma UN renglón de la lupa.
 *
 * 🔒 ES EL ÚNICO LUGAR DEL FRONT QUE MUESTRA `observaciones_paciente`, que
 * puede traer datos de salud. Va separado por una línea y al final del
 * renglón: no se mezcla con el tratamiento, y quien llama lo lee último,
 * cuando ya sabe a quién está llamando.
 *
 * 🔑 EL CONTACTO VA EN EL COLOR DE LECTURA Y NO EN EL CALLADO, al revés que en
 * la agenda: acá el teléfono no es un detalle de la ficha, es LA ACCIÓN de
 * esta pantalla.
 */
function renglonDeLaLupa( turno ) {

  const renglon = document.createElement( 'div' );
  renglon.className = 'fila-lupa';

  const cuando = document.createElement( 'p' );
  cuando.className = 'lupa-cuando';
  // CON AÑO, al revés que la agenda: esta lista cruza años —hay turnos de
  // noviembre y de marzo juntos— y sin el año no se sabe si uno falta un mes
  // o trece. Es el dato que decide a quién se llama primero.
  cuando.textContent = turnoEnPalabras( turno.inicio, true );

  const quien = document.createElement( 'p' );
  quien.className = 'lupa-quien';
  quien.textContent = turno.paciente.nombre + ' ' + turno.paciente.apellido;

  renglon.append( cuando, quien );

  // 🔴 LOS DOS DATOS DE CONTACTO PUEDEN SER NULOS, y no es un caso raro: en
  // `pacientes` las dos columnas son opcionales a propósito, porque Cecilia
  // carga a mano gente que sólo dejó un teléfono. Si no hay ninguno, la
  // pantalla LO DICE en vez de mostrar un renglón vacío: quien llama tiene que
  // saber que a esa persona no la va a poder llamar.
  const contacto = document.createElement( 'p' );
  contacto.className = 'lupa-contacto';

  const comoSeLoLlama = [];

  if ( turno.paciente.telefono ) {
    comoSeLoLlama.push( turno.paciente.telefono );
  }

  if ( turno.paciente.email ) {
    comoSeLoLlama.push( turno.paciente.email );
  }

  if ( comoSeLoLlama.length > 0 ) {
    contacto.textContent = comoSeLoLlama.join( ' · ' );
  }
  else {
    contacto.textContent = 'Sin teléfono ni correo en la ficha';
  }

  renglon.appendChild( contacto );

  const detalle = document.createElement( 'p' );
  detalle.className = 'lupa-detalle';

  const tratamiento = turno.tratamiento
    ? turno.tratamiento.nombre
    : 'Tratamiento sin cargar';

  detalle.textContent = tratamiento + ' · ' + turno.duracion_min + ' min';

  renglon.appendChild( detalle );

  if ( turno.observaciones_paciente ) {

    const motivo = document.createElement( 'p' );
    motivo.className = 'lupa-motivo';
    motivo.textContent = turno.observaciones_paciente;

    renglon.appendChild( motivo );
  }

  return renglon;
}


/** Pide los turnos de uno. Devuelve los datos, 'sin-acceso' o null. */
async function pedirLosTurnosDe( profesionalId ) {

  const respuesta = await fetch(
    DIRECCION_DE_LA_LUPA + '?profesional=' + profesionalId,
    { headers: cabecerasConSesion() }
  );

  if ( respuesta.status === 403 ) {
    return 'sin-acceso';
  }

  if ( !respuesta.ok ) {
    console.error( 'No se pudo leer los turnos. Estado:', respuesta.status );
    return null;
  }

  return await respuesta.json();
}


/**
 * Abre la lupa de un profesional.
 *
 * Recibe la FILA entera y no sólo el id, porque el título de la pantalla lleva
 * el nombre: pedirlo de nuevo al portero sería un viaje para un dato que el
 * renglón que se acaba de tocar ya tenía.
 */
async function irALaLupa( fila ) {

  const titulo = document.querySelector( '#lupa-titulo' );
  const ayuda = document.querySelector( '#lupa-ayuda' );
  const paraQue = document.querySelector( '#lupa-para-que' );
  const lista = document.querySelector( '#lupa-lista' );
  const aviso = document.querySelector( '#lupa-aviso' );

  titulo.textContent = 'Turnos de ' + fila.nombre + ' ' + fila.apellido;

  aviso.hidden = true;
  lista.hidden = true;
  paraQue.hidden = true;
  ayuda.hidden = false;
  ayuda.textContent = 'Cargando los turnos…';

  avanzarA( '#paso-lupa' );

  const datos = await pedirLosTurnosDe( fila.id );

  if ( datos === 'sin-acceso' ) {
    ayuda.hidden = true;
    aviso.hidden = false;
    aviso.textContent = 'Esta solapa es sólo para quien administra.';
    return;
  }

  if ( !datos ) {
    ayuda.hidden = true;
    aviso.hidden = false;
    aviso.textContent = 'No pudimos cargar los turnos. Probá de nuevo.';
    return;
  }

  lista.replaceChildren();

  for ( const turno of datos.turnos ) {
    lista.appendChild( renglonDeLaLupa( turno ) );
  }

  ayuda.hidden = true;
  lista.hidden = false;

  // La advertencia aparece SÓLO con turnos en la lista: sin ninguno no hay a
  // quién llamar, y un aviso sobre una lista vacía es ruido.
  paraQue.hidden = datos.turnos.length === 0;

  if ( datos.turnos.length === 0 ) {
    ayuda.hidden = false;
    ayuda.textContent = 'Este profesional no tiene turnos sin atender.';
  }
}


// ── LOS OYENTES DE LA SOLAPA ──────────────────────────────────────────────

document.querySelector( '#ir-al-plantel' ).addEventListener( 'click', () => {

  // 🔑 `avanzarA` Y NO `reemplazarPor`, al revés que el paso de cargar: la
  // solapa es un DESVÍO de la agenda y el «atrás» del navegador tiene que
  // traer de vuelta a la agenda. En la carga de un turno el «atrás» no tenía
  // sentido porque la pantalla tiene su propio botón de salida.
  avanzarA( '#paso-plantel' );

  mostrarElPlantel();
} );


document.querySelector( '#volver-de-plantel' ).addEventListener(
  'click',
  () => {
    reemplazarPor( '#paso-agenda' );
  }
);


document.querySelector( '#volver-de-lupa' ).addEventListener( 'click', () => {
  reemplazarPor( '#paso-plantel' );
} );


// ── DAR DE BAJA Y VOLVER A ACTIVAR ────────────────────────────────────────

// A quién apunta el cartel abierto. Se guarda acá y no en el botón porque el
// que confirma es un botón FIJO del cartel, no el de la fila: cuando se toca
// «Sí», la fila ya no está en ninguna parte de la pantalla.
let elDeLaBaja = null


function abrirElCartelDeBaja( fila ) {

  elDeLaBaja = fila

  const quien = fila.nombre + ' ' + fila.apellido

  document.querySelector( '#baja-quien' ).textContent = quien

  // 🔴 EL CARTEL DICE CUÁNTA GENTE QUEDA COLGADA, y ése es el dato que hace
  // contestable la pregunta. Apagar a alguien NO cancela sus turnos ni le
  // avisa a ningún paciente: un cartel que sólo dijera «¿seguro?» escondería
  // justo la consecuencia.
  const cuantos = fila.turnosPendientes

  let que = 'No tiene turnos sin atender.'

  if ( cuantos === 1 ) {
    que = 'Tiene 1 turno sin atender. Darlo de baja no lo cancela ni le avisa'
      + ' a esa persona: hay que llamarla.'
  }

  if ( cuantos > 1 ) {
    que = 'Tiene ' + cuantos + ' turnos sin atender. Darlo de baja no los'
      + ' cancela ni le avisa a nadie: hay que llamar a cada paciente.'
  }

  document.querySelector( '#baja-que' ).textContent = que

  document.querySelector( '#cartel-baja' ).showModal()
}


function cerrarElCartelDeBaja() {

  document.querySelector( '#cartel-baja' ).close()

  elDeLaBaja = null
}


/**
 * Apaga o prende a alguien y vuelve a dibujar el plantel.
 *
 * 🔑 SE REDIBUJA ENTERO EN VEZ DE TOCAR EL RENGLÓN: la fila cambia de estado,
 * de texto, de botón y de orden en la lista. Parchear cuatro cosas a mano es
 * donde se cuela el renglón que quedó diciendo lo viejo, y la lista son siete
 * filas — volver a pedirla cuesta un viaje y no deja nada desincronizado.
 */
async function cambiarElEstado( fila, prender ) {

  const aviso = document.querySelector( '#plantel-aviso' )

  aviso.hidden = true

  let respuesta

  try {

    respuesta = await fetch( DIRECCION_DE_LA_BAJA, {
      method: 'POST',
      headers: {
        ...cabecerasConSesion(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify( {
        profesional_id: fila.id,
        activo: prender
      } )
    } )
  }
  catch {

    aviso.hidden = false
    aviso.textContent = 'No pudimos conectarnos. Probá de nuevo.'
    return
  }

  if ( !respuesta.ok ) {

    // El 409 trae un texto escrito para que lo lea una persona —«no podés
    // darte de baja a vos mismo»— y por eso se muestra tal cual en vez de
    // taparlo con un mensaje genérico. Los demás códigos sí van con uno
    // propio: el detalle de un 500 no le sirve a nadie de este lado.
    let texto = 'No pudimos cambiar el estado. Probá de nuevo.'

    if ( respuesta.status === 409 ) {

      const cuerpo = await respuesta.json()

      texto = cuerpo.error
    }

    aviso.hidden = false
    aviso.textContent = texto
    return
  }

  await mostrarElPlantel()

  // 🔑 DESPUÉS DE LA BAJA SE ABRE LA LUPA SOLA, y es la mitad que resuelve el
  // problema: la lista de a quién llamar aparece sin que nadie tenga que
  // acordarse de buscarla. Es la solución de Juan del 6-ago-2026 —«que se
  // resuelva en pantalla y no por correo»— y sin esto el cartel avisa de seis
  // personas colgadas y después las esconde.
  if ( !prender && fila.turnosPendientes > 0 ) {
    irALaLupa( fila )
  }
}


// ── EL ALTA DE UN PROFESIONAL ─────────────────────────────────────────────

/** Abre o cierra el alta, y esconde las salidas de la pantalla mientras está abierta. */
function mostrarElAltaDeProfesional( abierta ) {

  document.querySelector( '#alta-profesional' ).hidden = !abierta

  // Mismo criterio que la ficha nueva de un paciente: con el alta abierta, la
  // única salida visible es la del alta. Dos botones de salir uno debajo del
  // otro no dicen a dónde va cada uno.
  document.querySelector( '#abrir-alta-profesional' ).hidden = abierta
  document.querySelector( '#volver-de-plantel' ).hidden = abierta

  if ( abierta ) {
    document.querySelector( '#nuevo-nombre' ).focus()
  }
}


function vaciarElAlta() {

  for ( const id of [ 'nuevo-nombre', 'nuevo-apellido', 'nuevo-email',
                      'nuevo-acceso' ] ) {

    document.querySelector( '#' + id ).value = ''
  }

  document.querySelector( '#nuevo-admin' ).checked = false
}


async function darDeAlta() {

  const aviso = document.querySelector( '#plantel-aviso' )

  aviso.hidden = true

  const nombre = document.querySelector( '#nuevo-nombre' ).value.trim()
  const apellido = document.querySelector( '#nuevo-apellido' ).value.trim()
  const email = document.querySelector( '#nuevo-email' ).value.trim()
  const acceso = document.querySelector( '#nuevo-acceso' ).value.trim()

  // 🔑 LOS TRES OBLIGATORIOS SE CHEQUEAN ACÁ Y TAMBIÉN EN EL PORTERO, y no es
  // una duplicación por desconfianza: acá es para no hacer viajar un pedido
  // que ya se sabe incompleto, allá es la validación DE VERDAD. La de este
  // lado se saltea escribiendo el pedido a mano; la del portero no.
  if ( !nombre || !apellido || !email ) {

    aviso.hidden = false
    aviso.textContent = 'Faltan el nombre, el apellido o el correo.'
    return
  }

  let respuesta

  try {

    respuesta = await fetch( DIRECCION_DEL_ALTA, {
      method: 'POST',
      headers: {
        ...cabecerasConSesion(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify( {
        nombre: nombre,
        apellido: apellido,
        email: email,
        email_de_acceso: acceso,
        es_admin: document.querySelector( '#nuevo-admin' ).checked
      } )
    } )
  }
  catch {

    aviso.hidden = false
    aviso.textContent = 'No pudimos conectarnos. Probá de nuevo.'
    return
  }

  if ( !respuesta.ok ) {

    // El 409 es «ya hay alguien con ese correo», que no es un error del
    // sistema sino una persona que ya está cargada. Se muestra su texto.
    let texto = 'No pudimos dar de alta. Probá de nuevo.'

    if ( respuesta.status === 409 || respuesta.status === 400 ) {

      const cuerpo = await respuesta.json()

      texto = cuerpo.error
    }

    aviso.hidden = false
    aviso.textContent = texto
    return
  }

  vaciarElAlta()

  mostrarElAltaDeProfesional( false )

  await mostrarElPlantel()
}


// ── LOS OYENTES DEL ALTA Y LA BAJA ────────────────────────────────────────

document.querySelector( '#abrir-alta-profesional' ).addEventListener(
  'click',
  () => {
    mostrarElAltaDeProfesional( true )
  }
)


document.querySelector( '#alta-profesional-cancelar' ).addEventListener(
  'click',
  () => {
    vaciarElAlta()
    mostrarElAltaDeProfesional( false )
  }
)


document.querySelector( '#alta-profesional-guardar' ).addEventListener(
  'click',
  darDeAlta
)


document.querySelector( '#baja-no' ).addEventListener(
  'click',
  cerrarElCartelDeBaja
)


document.querySelector( '#baja-si' ).addEventListener( 'click', () => {

  const fila = elDeLaBaja

  cerrarElCartelDeBaja()

  if ( fila ) {
    cambiarElEstado( fila, false )
  }
} )


// ── QUÉ HACE CADA PROFESIONAL — etapa ⑤.6, rebanada C ─────────────────────

const DIRECCION_DE_SUS_TRATAMIENTOS =
  SUPABASE_URL + '/functions/v1/tratamientos-del-profesional'

const DIRECCION_DE_LA_PAREJA = SUPABASE_URL + '/functions/v1/pareja-del-panel'


/**
 * Arma UN renglón con su tilde.
 *
 * 🔑 EL `<label>` ENVUELVE TODO y por eso la fila entera prende el tilde. Con
 * once renglones seguidos, apuntarle a un cuadrado de 20 px con el pulgar es
 * donde se prende el tratamiento equivocado.
 *
 * 🔴 NO HAY BOTÓN DE GUARDAR, y es una decisión: cada tilde manda su propio
 * pedido. Un «guardar» al final obligaría a juntar once cambios y a decidir
 * qué pasa si uno falla y los otros no. Así, lo que falla es uno solo y la
 * fila vuelve a donde estaba.
 */
function renglonDeTratamiento( fila, profesionalId ) {

  const renglon = document.createElement( 'label' )
  renglon.className = 'fila-tratamiento'

  const tilde = document.createElement( 'input' )
  tilde.type = 'checkbox'
  tilde.checked = fila.loHace

  const nombre = document.createElement( 'span' )
  nombre.className = 'tratamiento-nombre'
  nombre.textContent = fila.nombre

  tilde.addEventListener( 'change', () => {
    cambiarLaPareja( renglon, tilde, profesionalId, fila.id )
  } )

  renglon.append( tilde, nombre )

  return renglon
}


/**
 * Prende o apaga un tratamiento.
 *
 * 🔴 SI EL PEDIDO FALLA, EL TILDE VUELVE SOLO. Sin esto, la pantalla queda
 * mostrando prendido algo que la base tiene apagado, y es el peor resultado
 * posible: nadie vuelve a mirar una pantalla que ya dice lo que quería ver.
 */
async function cambiarLaPareja( renglon, tilde, profesionalId, tratamientoId ) {

  const aviso = document.querySelector( '#tratamientos-aviso' )
  const comoEstaba = !tilde.checked

  aviso.hidden = true

  // Mientras el pedido viaja, la fila no acepta otro clic: dos toques rápidos
  // mandarían dos pedidos cruzados sobre la misma pareja.
  renglon.classList.add( 'tratamiento-esperando' )

  let respuesta

  try {

    respuesta = await fetch( DIRECCION_DE_LA_PAREJA, {
      method: 'POST',
      headers: {
        ...cabecerasConSesion(),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify( {
        profesional_id: profesionalId,
        tratamiento_id: tratamientoId,
        activo: tilde.checked
      } )
    } )
  }
  catch {

    tilde.checked = comoEstaba
    renglon.classList.remove( 'tratamiento-esperando' )
    aviso.hidden = false
    aviso.textContent = 'No pudimos conectarnos. Probá de nuevo.'
    return
  }

  renglon.classList.remove( 'tratamiento-esperando' )

  if ( !respuesta.ok ) {

    tilde.checked = comoEstaba
    aviso.hidden = false
    aviso.textContent = 'No pudimos cambiar ese tratamiento. Probá de nuevo.'
  }
}


/** Pide qué hace un profesional. Devuelve los datos, 'sin-acceso' o null. */
async function pedirSusTratamientos( profesionalId ) {

  const respuesta = await fetch(
    DIRECCION_DE_SUS_TRATAMIENTOS + '?profesional=' + profesionalId,
    { headers: cabecerasConSesion() }
  )

  if ( respuesta.status === 403 ) {
    return 'sin-acceso'
  }

  if ( !respuesta.ok ) {
    console.error( 'No se pudo leer los tratamientos:', respuesta.status )
    return null
  }

  return await respuesta.json()
}


async function irALosTratamientos( fila ) {

  const titulo = document.querySelector( '#tratamientos-titulo' )
  const ayuda = document.querySelector( '#tratamientos-ayuda' )
  const paraQue = document.querySelector( '#tratamientos-para-que' )
  const lista = document.querySelector( '#tratamientos-lista' )
  const aviso = document.querySelector( '#tratamientos-aviso' )

  titulo.textContent = 'Qué hace ' + fila.nombre + ' ' + fila.apellido

  aviso.hidden = true
  lista.hidden = true
  paraQue.hidden = true
  ayuda.hidden = false
  ayuda.textContent = 'Cargando…'

  avanzarA( '#paso-tratamientos' )

  const datos = await pedirSusTratamientos( fila.id )

  if ( datos === 'sin-acceso' ) {
    ayuda.hidden = true
    aviso.hidden = false
    aviso.textContent = 'Esta solapa es sólo para quien administra.'
    return
  }

  if ( !datos ) {
    ayuda.hidden = true
    aviso.hidden = false
    aviso.textContent = 'No pudimos cargar los tratamientos. Probá de nuevo.'
    return
  }

  lista.replaceChildren()

  for ( const tratamiento of datos.tratamientos ) {
    lista.appendChild( renglonDeTratamiento( tratamiento, fila.id ) )
  }

  ayuda.hidden = true
  lista.hidden = false
  paraQue.hidden = false
}


document.querySelector( '#volver-de-tratamientos' ).addEventListener(
  'click',
  () => {
    // Se vuelve al plantel REDIBUJÁNDOLO: apagar todos los tratamientos de
    // alguien no cambia su fila, pero volver con la lista vieja puesta es como
    // se cuela un renglón que quedó diciendo lo de antes.
    reemplazarPor( '#paso-plantel' )
    mostrarElPlantel()
  }
)


// ══════════════════════════════════════════════════════════════════════
// LAS DURACIONES — UNA sola lista para las dos pantallas que la eligen
// ══════════════════════════════════════════════════════════════════════
//
// 🔑 ESTABAN ESCRITAS A MANO EN EL HTML y se mudaron acá el 13-oct-2026, al
// sumar la pantalla de MOVER: con dos listas escritas a mano, agregar una
// duración en una y no en la otra no falla con error — deja dos pantallas del
// mismo panel ofreciendo cosas distintas, y eso se descubre usándolas.
//
// ⚠️ EL TECHO DE VERDAD NO ESTÁ ACÁ: lo pone `_shared/duracion.ts` en el
// portero (30 a 300, en bloques de 30). Esta lista ofrece hasta 3 horas porque
// es lo que el consultorio usa; si hiciera falta más, el portero ya lo acepta.
const DURACIONES_DEL_PANEL = [
  { minutos: 30, comoSeLee: '30 minutos' },
  { minutos: 60, comoSeLee: '1 hora' },
  { minutos: 90, comoSeLee: '1 hora y media' },
  { minutos: 120, comoSeLee: '2 horas' },
  { minutos: 150, comoSeLee: '2 horas y media' },
  { minutos: 180, comoSeLee: '3 horas' }
];


function llenarLasDuraciones( select ) {

  select.textContent = '';

  DURACIONES_DEL_PANEL.forEach( ( cuanto ) => {

    const opcion = document.createElement( 'option' );

    opcion.value = cuanto.minutos;
    opcion.textContent = cuanto.comoSeLee;

    select.appendChild( opcion );
  } );
}


// Los dos desplegables se llenan al cargar la página y no al entrar a cada
// pantalla: la lista no viene de la base, así que no hay nada que esperar ni
// nada que pueda fallar en el camino.
llenarLasDuraciones( document.querySelector( '#turno-duracion' ) );

llenarLasDuraciones( document.querySelector( '#mover-duracion' ) );


// ══════════════════════════════════════════════════════════════════════
// MOVER UN TURNO DE HORA — etapa ⑤.4
// ══════════════════════════════════════════════════════════════════════
//
// QUÉ HACE: cambia a qué hora es un turno y cuánto dura. Nada más — ni de
// paciente, ni de profesional, ni de tratamiento. Eso no es una decisión de
// esta pantalla: el portero tiene permiso de escritura sobre `inicio` y
// `duracion_min` Y NADA MÁS, así que ofrecer el resto sería prometer algo que
// la base rechaza.
//
// 🔴 LA PANTALLA NO DEFIENDE NADA, igual que las otras tres del panel. Quien
// mueve un turno que no es suyo recibe 403 del portero, y eso no depende de
// que este archivo esconda un botón.

const DIRECCION_DE_MOVER = SUPABASE_URL + '/functions/v1/mover-turno';


// El turno que se está moviendo, tal cual lo mandó la agenda. Vacío fuera de
// esta pantalla.
let turnoQueSeMueve = null;


// La grilla de ESTA pantalla. Es la misma pieza que la de cargar un turno —la
// dibuja `dibujarLasHoras`— y se diferencia en tres datos.
const grillaDeMover = {

  caja: '#mover-horas',
  ayuda: '#mover-horas-ayuda',
  fecha: '#mover-fecha',
  duracion: '#mover-duracion',

  // Los tres se ponen al abrir la pantalla, en `irAMover`.
  profesionalId: null,
  excepto: null,
  elegida: null
};


/**
 * Se asegura de que el desplegable de duración OFREZCA la del turno.
 *
 * 🔴 EL MODO DE FALLA QUE TAPA ES SILENCIOSO: el portero acepta hasta 300
 * minutos y esta lista ofrece hasta 180, así que un turno de 240 —cargado
 * antes, o desde el Table Editor— deja el desplegable sin ninguna opción
 * elegida. Y entonces `value` es el texto vacío, la grilla pide
 * `?duracion=` sin número, el portero contesta 400 y la pantalla se abre muda
 * sin decir por qué. Agregar la opción que falta cuesta cuatro líneas; ésta
 * cuesta un rato de buscar el bug en el lugar equivocado.
 *
 * Y de paso evita duplicarla: se pregunta por el `<option>`, no por la lista.
 */
function asegurarLaDuracion( minutos ) {

  const select = document.querySelector( '#mover-duracion' );

  if ( select.querySelector( 'option[value="' + minutos + '"]' ) ) {
    return;
  }

  const opcion = document.createElement( 'option' );

  opcion.value = minutos;
  opcion.textContent = minutos + ' minutos';

  select.appendChild( opcion );
}


function avisarEnMover( texto ) {

  const cartel = document.querySelector( '#mover-aviso' );

  cartel.hidden = !texto;
  cartel.textContent = texto || '';
}


/**
 * Abre la pantalla de mover con un turno puesto.
 *
 * 🔴 EL DÍA SE SACA CON `diaDeUnInstante` Y NO CORTANDO EL TEXTO. La base
 * devuelve el instante en UTC ('2026-10-15T12:00:00+00:00' son las 09:00 de
 * Santa Fe), así que `inicio.slice( 0, 10 )` da el día correcto casi siempre y
 * el equivocado para todo turno de las 21 en adelante. Es una fecha válida,
 * bien escrita, un día corrida.
 *
 * 🔑 LA GRILLA ARRANCA SIN NINGUNA HORA ELEGIDA, a propósito, aunque el turno
 * ya tenga una. Dejar marcado el bloque de ahora ahorraría un toque en el caso
 * de cambiar sólo la duración, y a cambio el botón «Guardar» quedaría activo
 * sin que nadie haya elegido nada: un toque de más en el lugar equivocado
 * mandaría un turno a la hora que ya tenía. La hora de hoy se LEE en la
 * tarjeta de arriba; la de la grilla se ELIGE.
 */
function irAMover( turno ) {

  turnoQueSeMueve = turno;

  document.querySelector( '#mover-quien' ).textContent =
    turno.paciente.nombre + ' ' + turno.paciente.apellido
    + ' — ' + queDiceElTurno( turno );

  document.querySelector( '#mover-ahora' ).textContent =
    'Ahora: ' + turnoEnPalabras( turno.inicio )
    + ' · ' + turno.duracion_min + ' min';

  document.querySelector( '#mover-fecha' ).value = diaDeUnInstante( turno.inicio );

  asegurarLaDuracion( turno.duracion_min );

  document.querySelector( '#mover-duracion' ).value = turno.duracion_min;

  // 🔑 DE QUIÉN ES LA AGENDA QUE SE MIRA SALE DEL TURNO, no de un desplegable:
  // un turno no se le puede pasar a otro profesional desde acá, así que la
  // grilla que importa es la de su dueño. Para un admin que mira el turno de
  // otra persona, esto es lo que hace que vea los huecos correctos.
  grillaDeMover.profesionalId = turno.profesional.id;

  // Y el turno no se cuenta a sí mismo como ocupado.
  grillaDeMover.excepto = turno.id;

  grillaDeMover.elegida = null;

  avisarEnMover( '' );

  avanzarA( '#paso-mover' );

  dibujarLasHoras( grillaDeMover );
}


/**
 * Manda el cambio.
 *
 * 🔑 LOS DOS CHEQUEOS DE ACÁ NO DEFIENDEN LA BASE —eso es del portero—, evitan
 * dos cosas que confunden: mandar sin haber elegido hora, y mandar un cambio
 * que no cambia nada. Lo segundo no es inofensivo: el portero movería el turno
 * a la hora que ya tenía y le escribiría a la paciente un correo diciéndole que
 * su turno cambió.
 */
async function guardarElCambio() {

  if ( !grillaDeMover.elegida ) {
    avisarEnMover( 'Elegí un horario nuevo de la grilla.' );
    return;
  }

  const duracion = Number( document.querySelector( '#mover-duracion' ).value );

  // 🔴 SE COMPARAN INSTANTES, NO TEXTOS. El portero manda la hora con el desfase
  // de Santa Fe puesto ('…T09:00:00-03:00') y la base guarda el mismo instante
  // en UTC ('…T12:00:00+00:00'): son dos escrituras distintas de la misma hora,
  // así que compararlas como texto diría «cambió» siempre.
  const mismaHora =
    Date.parse( grillaDeMover.elegida ) === Date.parse( turnoQueSeMueve.inicio );

  if ( mismaHora && duracion === turnoQueSeMueve.duracion_min ) {
    avisarEnMover( 'Ese es el horario que ya tiene. No hay nada que cambiar.' );
    return;
  }

  const boton = document.querySelector( '#mover-guardar' );

  // El botón se apaga mientras viaja el pedido, igual que en el cartel de
  // cancelar: dos toques mandan dos movimientos y dos correos.
  boton.disabled = true;

  let respuesta;

  try {
    respuesta = await fetch(
      DIRECCION_DE_MOVER,
      {
        method: 'POST',
        headers: {
          ...cabecerasConSesion(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify( {
          turno_id: turnoQueSeMueve.id,
          inicio: grillaDeMover.elegida,
          duracion_min: duracion
        } )
      }
    );
  }
  catch {
    respuesta = null;
  }

  boton.disabled = false;

  if ( !respuesta ) {
    avisarEnMover( 'No pudimos conectar. Probá de nuevo.' );
    return;
  }

  // 🔑 EL 409 SE DICE CON SUS PALABRAS Y NO COMO UN ERROR DEL SISTEMA: significa
  // que ese horario se pisa con otro turno, que es información útil. Nadie se
  // equivocó, y el que rebota es el constraint `turnos_sin_solapar` haciendo su
  // trabajo. La grilla se vuelve a dibujar porque el choque puede ser con un
  // turno que entró después de que esta pantalla pidió los horarios.
  if ( respuesta.status === 409 ) {

    avisarEnMover( 'Ese horario se pisa con otro turno. Elegí otro.' );

    grillaDeMover.elegida = null;

    dibujarLasHoras( grillaDeMover );

    return;
  }

  if ( !respuesta.ok ) {
    avisarEnMover( 'No pudimos mover el turno. Probá de nuevo.' );
    return;
  }

  const datos = await respuesta.json();

  // Se vuelve al día NUEVO del turno y no al que se estaba mirando: si el
  // turno se movió de día, la agenda del día viejo ya no lo tiene, y quien
  // acaba de moverlo se queda sin ver el resultado de lo que hizo.
  const diaNuevo = document.querySelector( '#mover-fecha' ).value;

  await irAlDia( diaNuevo );

  reemplazarPor( '#paso-agenda' );

  aviso.hidden = false;

  // ⚠️ LO QUE SE DICE CAMBIA SEGÚN SI EL AVISO SALIÓ, igual que al agendar. Un
  // turno movido del que la paciente no se enteró es peor que no haberlo
  // movido: va a venir a la hora vieja, y alguien tiene que llamarla.
  aviso.textContent = datos.avisadoAlPaciente
    ? 'Turno movido y avisado por correo.'
    : 'Turno movido. ⚠️ NO se le pudo avisar a la paciente: hay que llamarla.';
}


document.querySelector( '#mover-guardar' ).addEventListener(
  'click',
  guardarElCambio
);


document.querySelector( '#volver-de-mover' ).addEventListener( 'click', () => {
  reemplazarPor( '#paso-agenda' );
} );


// LOS DOS CAMPOS QUE CAMBIAN LA RESPUESTA DE LA GRILLA. El profesional no está
// en la lista porque acá no se puede cambiar: es el dueño del turno.
//
// ⚠️ LA HORA ELEGIDA SE BORRA al cambiar cualquiera de los dos, por el mismo
// modo de falla silencioso que en cargar un turno: se elige un bloque con 30
// minutos, se pasa la duración a 90, y el bloque sigue marcado aunque ya no
// entre.
[ '#mover-fecha', '#mover-duracion' ].forEach( ( cual ) => {

  document.querySelector( cual ).addEventListener( 'change', () => {

    grillaDeMover.elegida = null;

    dibujarLasHoras( grillaDeMover );
  } );
} );
