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
