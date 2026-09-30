// LA PANTALLA ④ — «¿qué día y a qué hora?».
//
// QUÉ HACE ESTE ARCHIVO, en una línea: resuelve CON QUIÉN, QUÉ DÍA y A QUÉ
// HORA es el turno.
//
// LAS TRES COSAS CUELGAN UNA DE OTRA, en este orden: `GET /horarios-disponibles`
// EXIGE un profesional —no acepta varios—, así que la agenda es por persona por
// diseño del portero; elegir el día abre las horas de ese día; y elegir la hora
// es lo último que falta para poder reservar.
//
// 🔑 PEDIR Y DIBUJAR SON DOS TRABAJOS SEPARADOS en todo el archivo, y no es
// prolijidad: `dibujarElAlmanaque()` no habla con la base, así que el almanaque
// se puede dibujar con datos inventados para mirarlo sin entrar con Google y
// sin tocar la agenda real. Es el mismo motivo por el que
// `prepararLaPantallaDeDiaHora` RECIBE la lista de profesionales en vez de
// pedirla.


const DIRECCION_DE_PROFESIONALES = SUPABASE_URL + '/functions/v1/profesionales';


// CON QUIÉN ES EL TURNO. Guarda el `id`, que es lo que pide `POST /reservar`.
let profesionalElegido = null;


/**
 * Le pide al portero quiénes hacen ese tratamiento.
 *
 * Devuelve la lista, o `null` si el pedido falló. Quien llama decide qué
 * mostrar: este archivo no dibuja errores.
 */
async function pedirLosProfesionales( tratamiento ) {

  const respuesta = await fetch(
    DIRECCION_DE_PROFESIONALES + '?tratamiento=' + tratamiento,
    {
      headers: {
        'apikey': SUPABASE_CLAVE_PUBLICA
      }
    }
  );

  if ( !respuesta.ok ) {
    console.error( 'No se pudo leer los profesionales. Estado:', respuesta.status );
    return null;
  }

  return await respuesta.json();
}


/**
 * Arma la pantalla según CUÁNTOS profesionales hagan el tratamiento elegido.
 *
 * Devuelve 'mostrar' o 'falló', igual que `prepararLaPantallaDeQuien`: la
 * pantalla que llama decide si avanza o si avisa.
 *
 * 🔑 LA FORMA LA DECIDEN LOS DATOS, NO UNA BANDERA NUESTRA. El día que Cecilia
 * sume a alguien, el portero devuelve dos filas y la pregunta aparece sola. No
 * hay nada que acordarse de encender.
 *
 * RECIBE la lista en vez de pedirla, por el mismo motivo escrito en `quien.js`:
 * así se la puede correr con una lista inventada y mirar los dos casos sin
 * tocar la base. Hoy la base tiene UNA sola profesional, así que el caso de dos
 * no se podría probar de ninguna otra forma.
 */
function prepararLaPantallaDeDiaHora( profesionales ) {

  if ( profesionales === null || profesionales.length === 0 ) {
    return 'falló';
  }

  // EL DESPLEGABLE VA SIEMPRE, haya uno o haya cinco —decidido por Juan el
  // 30-sep-2026—. Con una sola profesional queda un desplegable de una opción,
  // que parece de más y no lo es: es el MISMO control en los dos casos, así
  // que el día que Cecilia sume a alguien no cambia la pantalla, cambia lo que
  // el control tiene adentro. Una pantalla que se transforma según los datos
  // es una pantalla que hay que probar dos veces y acordarse de las dos.
  const desplegable = document.querySelector( '#profesional' );

  desplegable.textContent = '';

  for ( const profesional of profesionales ) {

    const opcion = document.createElement( 'option' );

    opcion.value = profesional.id;

    // `textContent` y no HTML pegado: es un nombre que escribió una persona en
    // la base. Misma defensa contra XSS que en `quien.js` y en `motivo.js`.
    opcion.textContent = profesional.nombre + ' ' + profesional.apellido;

    desplegable.appendChild( opcion );
  }

  // El primero queda elegido: con el desplegable cerrado hay que mostrar algo,
  // y «Elegí una opción» obligaría a un toque que no decide nada cuando el
  // paciente no tiene preferencia — y con una sola profesional, a un toque que
  // no decide nada nunca.
  profesionalElegido = Number( desplegable.value );

  // EL ALMANAQUE ARRANCA EN EL MES DE HOY. Se pide sin esperar la respuesta
  // —no hay `await`— a propósito: la pantalla se muestra enseguida con el
  // desplegable ya lleno, y el mes aparece cuando llega. Esperar acá dejaría
  // la pantalla anterior congelada mientras el portero contesta.
  mesVisible = new Date( new Date().getFullYear(), new Date().getMonth(), 1 );

  diaElegido = null;
  horaElegida = null;

  document.querySelector( '#horarios' ).hidden = true;

  traerElMesYDibujarlo();

  return 'mostrar';
}


// CAMBIAR DE PROFESIONAL CAMBIA LA AGENDA, y por eso vuelve a pedirla entera.
// No alcanza con redibujar: los días con lugar de una persona no son los de la
// otra, así que lo que hay en pantalla deja de ser cierto en el momento en que
// se suelta el desplegable.
document.querySelector( '#profesional' ).addEventListener( 'change', async ( evento ) => {

  profesionalElegido = Number( evento.target.value );

  // Se suelta lo elegido con el profesional viejo: un horario de la agenda de
  // otra persona no significa nada en ésta.
  diaElegido = null;
  horaElegida = null;

  document.querySelector( '#horarios' ).hidden = true;

  await traerElMesYDibujarlo();
} );


document.querySelector( '#dia-hora-atras' ).addEventListener( 'click', () => {
  history.back();
} );


// ══════════════════════════════════════════════════════════════════════
// EL ALMANAQUE Y LA GRILLA DE HORARIOS
// ══════════════════════════════════════════════════════════════════════


const DIRECCION_DE_HORARIOS = SUPABASE_URL + '/functions/v1/horarios-disponibles';


// La semana arranca en LUNES, como el almanaque de pared. JavaScript la
// arranca en domingo, así que hay una cuenta para acomodarla — está abajo, en
// `columnaDelDia`, escrita una sola vez.
const LETRAS_DE_LA_SEMANA = [ 'L', 'M', 'M', 'J', 'V', 'S', 'D' ];

const NOMBRES_DE_MES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

const NOMBRES_DE_DIA = [
  'Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'
];


// CUÁNTOS MESES ADELANTE SE PUEDE MIRAR. Sale de la ventana de reserva, que
// es decisión del 15-ago-2026: piso de 12 horas, techo de DOS MESES. El
// portero ya la hace cumplir —devuelve `fuera_de_plazo`—, así que esto no es
// la defensa: es no ofrecerle al paciente meses que van a venir todos grises.
const MESES_QUE_SE_PUEDEN_MIRAR = 2;


// El primer día del mes que se está mostrando.
let mesVisible = null;

// Lo último que contestó el portero, tal cual: una lista de `{ fecha, bloques }`.
let diasConHorarios = [];

// La fecha elegida, en texto 'AAAA-MM-DD'. Es la que abre la grilla de horas.
let diaElegido = null;

// La hora elegida, con desfase ('2026-09-21T08:00:00-03:00'). Es lo que
// `POST /reservar` va a pedir como `inicio`.
let horaElegida = null;


/**
 * La fecha en texto 'AAAA-MM-DD', leída en la hora DE ACÁ.
 *
 * 🔴 POR QUÉ NO SE USA `toISOString()`, QUE ES LA FORMA OBVIA: ése convierte a
 * UTC antes de escribir, y Argentina está tres horas atrás. Un turno del 21 a
 * las 22:00 se escribiría como el 22 — el almanaque mostraría el día siguiente
 * y nadie vería un error, sólo una fecha corrida. Es el mismo modo de falla
 * que el caché del navegador: no avisa, contesta mal.
 */
function enTextoDeFecha( fecha ) {

  const mes = String( fecha.getMonth() + 1 ).padStart( 2, '0' );
  const dia = String( fecha.getDate() ).padStart( 2, '0' );

  return fecha.getFullYear() + '-' + mes + '-' + dia;
}


/**
 * En qué columna del almanaque cae una fecha, contando desde el lunes.
 *
 * `getDay()` devuelve 0 para el domingo y 6 para el sábado. Corriendo seis y
 * tomando el resto de siete, el lunes pasa a ser 0 y el domingo 6, que es el
 * orden en que están las letras de arriba.
 */
function columnaDelDia( fecha ) {
  return ( fecha.getDay() + 6 ) % 7;
}


/** El último día del mes de `fecha`, como número. */
function ultimoDiaDelMes( fecha ) {

  // El día 0 del mes SIGUIENTE es el último del actual. Es la forma de
  // preguntarlo sin tener que saber cuáles tienen 30, 31 o 28.
  return new Date( fecha.getFullYear(), fecha.getMonth() + 1, 0 ).getDate();
}


/**
 * Le pide al portero la agenda de un rango de días.
 *
 * Devuelve la lista de días, o `null` si el pedido falló. Como el resto de
 * este archivo: no dibuja errores, los informa a quien lo llamó.
 */
async function pedirLosHorarios( desde, hasta ) {

  const consulta =
    '?profesional=' + profesionalElegido +
    '&tratamiento=' + tratamientoElegido +
    '&desde=' + desde +
    '&hasta=' + hasta;

  // ESTE ENDPOINT PIDE TOKEN desde el 24-sep-2026, y es la decisión de Juan:
  // «una persona que no se registra no tiene derecho a ver la disponibilidad
  // de la agenda del consultorio».
  const respuesta = await fetch(
    DIRECCION_DE_HORARIOS + consulta,
    {
      headers: {
        'apikey': SUPABASE_CLAVE_PUBLICA,
        'Authorization': 'Bearer ' + tokenDeLaSesion()
      }
    }
  );

  if ( !respuesta.ok ) {
    console.error( 'No se pudo leer la agenda. Estado:', respuesta.status );
    return null;
  }

  const contenido = await respuesta.json();

  return contenido.dias;
}


/** Si ese día tiene al menos un bloque que se pueda reservar. */
function elDiaTieneLugar( dia ) {

  return dia.bloques.some( ( bloque ) => bloque.estado === 'libre' );
}


/**
 * Dibuja el mes entero: el encabezado con las flechas y las casillas.
 *
 * NO PIDE NADA: dibuja con lo que ya hay en `diasConHorarios`. Pedir y dibujar
 * son dos trabajos y se separan a propósito — así el almanaque se puede dibujar
 * con datos inventados para mirarlo, sin base y sin entrar con Google.
 */
function dibujarElAlmanaque() {

  const caja = document.querySelector( '#almanaque' );

  caja.textContent = '';

  // ── el encabezado: el mes y las dos flechas ──
  const encabezado = document.createElement( 'div' );

  encabezado.className = 'mes';

  const titulo = document.createElement( 'h3' );

  titulo.textContent =
    NOMBRES_DE_MES[ mesVisible.getMonth() ] + ' ' + mesVisible.getFullYear();

  encabezado.appendChild( titulo );

  const pasar = document.createElement( 'div' );

  pasar.className = 'pasar';

  // LAS FLECHAS SE APAGAN EN LOS BORDES en vez de desaparecer: un control que
  // se va deja la fila saltando de lugar, y el que queda cambia de posición
  // justo cuando el dedo ya salió a tocarlo.
  const atras = document.createElement( 'button' );

  atras.type = 'button';
  atras.innerHTML = '&lsaquo;';
  atras.setAttribute( 'aria-label', 'Mes anterior' );
  atras.disabled = !sePuedeMirarElMes( -1 );
  atras.addEventListener( 'click', () => cambiarDeMes( -1 ) );

  const adelante = document.createElement( 'button' );

  adelante.type = 'button';
  adelante.innerHTML = '&rsaquo;';
  adelante.setAttribute( 'aria-label', 'Mes siguiente' );
  adelante.disabled = !sePuedeMirarElMes( 1 );
  adelante.addEventListener( 'click', () => cambiarDeMes( 1 ) );

  pasar.appendChild( atras );
  pasar.appendChild( adelante );
  encabezado.appendChild( pasar );
  caja.appendChild( encabezado );

  // ── la cuadrícula: siete letras y después las casillas ──
  const semana = document.createElement( 'div' );

  semana.className = 'semana';

  for ( const letra of LETRAS_DE_LA_SEMANA ) {

    const rotulo = document.createElement( 'span' );

    rotulo.className = 'letra';
    rotulo.textContent = letra;

    semana.appendChild( rotulo );
  }

  // LAS CASILLAS VACÍAS DE ADELANTE. Si el mes no arranca un lunes, el día 1
  // tiene que caer en su columna: se rellena con casillas que no dicen nada.
  for ( let i = 0; i < columnaDelDia( mesVisible ); i++ ) {
    semana.appendChild( document.createElement( 'span' ) );
  }

  for ( let numero = 1; numero <= ultimoDiaDelMes( mesVisible ); numero++ ) {

    const fecha = new Date(
      mesVisible.getFullYear(),
      mesVisible.getMonth(),
      numero
    );

    semana.appendChild( casillaDelDia( numero, enTextoDeFecha( fecha ) ) );
  }

  caja.appendChild( semana );
}


/**
 * Una casilla del mes, del material que corresponde a su estado.
 *
 * 🔑 EL DÍA QUE NO SE PUEDE TOCAR NO ES UN CONTROL APAGADO: ES OTRA COSA. Un
 * `<a>` sin destino igual recibe foco y el que navega con teclado se lo come;
 * un `<span>` no. `disabled` no existe fuera de los controles, así que lo que
 * se lo dice al lector de pantalla es `aria-disabled`.
 */
function casillaDelDia( numero, texto ) {

  const dia = diasConHorarios.find( ( candidato ) => candidato.fecha === texto );

  const tieneLugar = dia !== undefined && elDiaTieneLugar( dia );

  if ( !tieneLugar ) {

    const cerrado = document.createElement( 'span' );

    cerrado.className = 'dia dia-apagado';
    cerrado.textContent = numero;
    cerrado.setAttribute( 'aria-disabled', 'true' );

    return cerrado;
  }

  // EL DÍA ABIERTO ES UN ENLACE AL CAJÓN DE HORARIOS —la «opción D», decidida
  // por Juan—: en el teléfono el mes y las horas no entran juntos, así que
  // tocar un día BAJA a las horas. Un <button> no puede llevar un ancla, y
  // hacerlo con `scrollIntoView()` mueve la pantalla pero DEJA EL FOCO ARRIBA.
  const abierto = document.createElement( 'a' );

  abierto.className = 'dia';
  abierto.href = '#horarios';
  abierto.textContent = numero;

  if ( texto === diaElegido ) {
    abierto.classList.add( 'dia-elegido' );
    abierto.setAttribute( 'aria-current', 'date' );
  }

  // El punto dorado va ADEMÁS del color, no en su lugar: los días sin lugar ya
  // son grises, así que la diferencia no depende de ver un punto de 5 px.
  const marca = document.createElement( 'span' );

  marca.className = 'marca';

  abierto.appendChild( marca );

  abierto.addEventListener( 'click', () => elegirElDia( texto ) );

  return abierto;
}


/** Si se puede mover el almanaque tantos meses, sin salirse de la ventana. */
function sePuedeMirarElMes( cuantos ) {

  const candidato = new Date(
    mesVisible.getFullYear(),
    mesVisible.getMonth() + cuantos,
    1
  );

  const hoy = new Date();

  const primerMes = new Date( hoy.getFullYear(), hoy.getMonth(), 1 );

  const ultimoMes = new Date(
    hoy.getFullYear(),
    hoy.getMonth() + MESES_QUE_SE_PUEDEN_MIRAR,
    1
  );

  return candidato >= primerMes && candidato <= ultimoMes;
}


/** Pasa de mes y vuelve a pedir la agenda de ese mes. */
async function cambiarDeMes( cuantos ) {

  if ( !sePuedeMirarElMes( cuantos ) ) {
    return;
  }

  mesVisible = new Date(
    mesVisible.getFullYear(),
    mesVisible.getMonth() + cuantos,
    1
  );

  // AL CAMBIAR DE MES SE SUELTA EL DÍA ELEGIDO, y no es una limpieza de más:
  // si no, el cajón de horarios sigue mostrando las horas de un día que ya no
  // está en pantalla, y el título dice una fecha que nadie ve.
  diaElegido = null;
  horaElegida = null;

  document.querySelector( '#horarios' ).hidden = true;

  await traerElMesYDibujarlo();
}


/** Pide la agenda del mes visible entero y dibuja. */
async function traerElMesYDibujarlo() {

  const desde = enTextoDeFecha( mesVisible );

  const hasta = enTextoDeFecha( new Date(
    mesVisible.getFullYear(),
    mesVisible.getMonth(),
    ultimoDiaDelMes( mesVisible )
  ) );

  const dias = await pedirLosHorarios( desde, hasta );

  // Un pedido que falla deja el almanaque VACÍO, no a medias con los días del
  // mes anterior: un mes de septiembre con el título de octubre es peor que un
  // mes en blanco, porque el segundo se ve roto y el primero no.
  diasConHorarios = dias === null ? [] : dias;

  dibujarElAlmanaque();

  return dias === null ? 'falló' : 'mostrar';
}


/** Elegir un día abre el cajón de horarios con las horas de ESE día. */
function elegirElDia( texto ) {

  diaElegido = texto;
  horaElegida = null;

  dibujarElAlmanaque();
  dibujarLaGrilla();
}


/** Las horas del día elegido, con sus cuatro estados. */
function dibujarLaGrilla() {

  const cajon = document.querySelector( '#horarios' );
  const cuando = document.querySelector( '#dia-hora-cuando' );
  const grilla = document.querySelector( '#grilla-de-horas' );

  const dia = diasConHorarios.find(
    ( candidato ) => candidato.fecha === diaElegido
  );

  if ( dia === undefined ) {
    cajon.hidden = true;
    return;
  }

  // QUÉ DÍA SE ESTÁ MIRANDO, ESCRITO. El ancla baja a una grilla de horas y el
  // almanaque queda arriba, fuera de la vista: sin esta línea, las horas no
  // dicen de cuándo son.
  const fecha = new Date( diaElegido + 'T00:00:00' );

  cuando.textContent =
    NOMBRES_DE_DIA[ fecha.getDay() ] + ' ' + fecha.getDate() +
    ' de ' + NOMBRES_DE_MES[ fecha.getMonth() ].toLowerCase();

  grilla.textContent = '';

  for ( const bloque of dia.bloques ) {
    grilla.appendChild( casillaDeLaHora( bloque ) );
  }

  cajon.hidden = false;
}


/**
 * Un bloque de la grilla de horas.
 *
 * 🔑 LOS BLOQUES QUE NO SE PUEDEN TOMAR SE MUESTRAN, NO SE ESCONDEN —decisión
 * del 6-ago-2026—: un día con todo tomado tiene que verse distinto de un día
 * en que no se atiende, y escondiendo lo que no sirve los dos quedan iguales.
 *
 * El portero distingue tres motivos de «no» —`ocupado`, `no_entra` y
 * `fuera_de_plazo`— y la pantalla los pinta con el mismo gris. Distinguirlos
 * en la respuesta cuesta cero; mezclarlos es irreversible.
 */
function casillaDeLaHora( bloque ) {

  const hora = document.createElement( 'button' );

  hora.type = 'button';
  hora.className = 'hora';

  // La hora se lee del texto que mandó el portero y NO se convierte a fecha:
  // el dato ya viene con el desfase de acá ('...T08:00:00-03:00'), y pasarlo
  // por `new Date()` para volver a escribirlo es abrir la puerta a que se
  // corra una hora sin que nadie lo note.
  hora.textContent = bloque.inicio.slice( 11, 16 );

  if ( bloque.estado !== 'libre' ) {

    hora.className = 'hora hora-apagada';
    hora.disabled = true;

    return hora;
  }

  if ( bloque.inicio === horaElegida ) {
    hora.classList.add( 'hora-elegida' );
  }

  hora.addEventListener( 'click', () => {
    horaElegida = bloque.inicio;
    dibujarLaGrilla();
  } );

  return hora;
}
