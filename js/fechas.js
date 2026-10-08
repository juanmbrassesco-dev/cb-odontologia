// CÓMO SE ESCRIBE UNA FECHA EN ESTE SITIO.
//
// QUÉ HACE ESTE ARCHIVO, en una línea: convierte lo que manda el portero en el
// texto que lee el paciente — «Jueves 8 de octubre, 15:30».
//
// 🔑 POR QUÉ ES UN ARCHIVO APARTE Y NO VIVE EN LA PANTALLA QUE LO USA: lo
// escriben TRES pantallas —la grilla de horas de la ④, la tarjeta de la ⑤ y la
// lista de «mis turnos», que además está en otra página—. Con los nombres de
// los meses copiados en cada una, el día que se decida abreviarlos o poner el
// año habría que acordarse de los tres lugares, y el que falte se descubre
// cuando un paciente ve dos formatos para el mismo turno.


// LOS NOMBRES, escritos una sola vez. El mes arranca en enero y el día en
// domingo porque ése es el orden en que los numera el navegador
// (`getMonth()` y `getDay()`), no el que usaríamos nosotros.
const NOMBRES_DE_MES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
];

const NOMBRES_DE_DIA = [
  'Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'
];


// LA ZONA HORARIA DEL CONSULTORIO, escrita con su NOMBRE y no como un número.
//
// Es la misma que usa el portero —está en `supabase/functions/_shared/
// disponibilidad.ts`, con el porqué completo—: Santa Fe cae dentro de
// `America/Argentina/Cordoba`. Un `-03:00` tipeado a mano es un número
// congelado; el nombre de la zona lo mantiene el sistema operativo.
const ZONA_DEL_CONSULTORIO = 'America/Argentina/Cordoba';


/**
 * Un día escrito como lo lee una persona: «Jueves 8 de octubre».
 *
 * Recibe el texto del día, '2026-10-08', que es como viaja en la agenda.
 *
 * ⚠️ LA FECHA SE ARMA CON 'T00:00:00' PEGADO y no con el texto solo: un
 * '2026-10-08' suelto lo lee el navegador como medianoche UTC, que en
 * Argentina es el día anterior a las 21. Con la hora puesta se lee como local
 * y el día no se corre.
 */
function diaEnPalabras( texto ) {

  const fecha = new Date( texto + 'T00:00:00' );

  return NOMBRES_DE_DIA[ fecha.getDay() ] + ' ' + fecha.getDate() +
    ' de ' + NOMBRES_DE_MES[ fecha.getMonth() ].toLowerCase();
}


/**
 * Un turno entero escrito: «Jueves 8 de octubre, 15:30».
 *
 * Recibe el `inicio` tal cual lo manda el portero, que es un INSTANTE con su
 * zona adentro — y ojo, porque no siempre viene con la de acá: la base lo
 * guarda en UTC y lo devuelve así ('2026-10-02T11:00:00+00:00' son las 08:00
 * en Santa Fe).
 *
 * 🔴 POR ESO ACÁ NO SE CORTA EL TEXTO, SE CONVIERTE. Cortar '2026-10-02T11:00'
 * y mostrar «11:00» sería mostrarle al paciente una hora a la que el
 * consultorio no lo espera, y el error no se ve: es una hora que existe, bien
 * escrita, tres horas más tarde.
 *
 * ⚠️ Y SE CONVIERTE A LA ZONA DEL CONSULTORIO, no a la del navegador: el turno
 * es a las 15:30 en Santa Fe aunque el que mire la pantalla esté de viaje.
 */
function turnoEnPalabras( inicio ) {

  const instante = new Date( inicio );

  // `formatToParts` devuelve la fecha partida en pedazos con nombre —año, mes,
  // día, hora, minuto— ya convertidos a la zona que se le pide. Se usa eso y no
  // el texto armado por el navegador porque el formato lo elegimos nosotros.
  const pedazos = new Intl.DateTimeFormat( 'es-AR', {
    timeZone: ZONA_DEL_CONSULTORIO,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  } ).formatToParts( instante );

  const dato = {};

  for ( const pedazo of pedazos ) {
    dato[ pedazo.type ] = pedazo.value;
  }

  const dia = dato.year + '-' + dato.month + '-' + dato.day;

  return diaEnPalabras( dia ) + ', ' + dato.hour + ':' + dato.minute;
}


/**
 * Sólo la hora de un turno, en la zona del consultorio: «15:30».
 *
 * La usa el PANEL, donde la fecha ya está escrita arriba de la lista y
 * repetirla en cada tarjeta sería decir treinta veces lo mismo.
 *
 * 🔴 CONVIERTE, NO CORTA, y es la misma trampa que explica `turnoEnPalabras`
 * acá arriba: la base devuelve el instante en UTC
 * ('2026-10-08T18:00:00+00:00' son las 15:00 en Santa Fe). Cortar el texto y
 * mostrar «18:00» pondría en la agenda una hora a la que no hay nadie citado,
 * y el error no se ve: es una hora válida, bien escrita, tres horas corrida.
 *
 * Vive acá y no en `panel.js` para que la zona del consultorio siga teniendo
 * UN solo lugar en todo el front.
 */
function horaDelTurno( inicio ) {

  return new Intl.DateTimeFormat( 'es-AR', {
    timeZone: ZONA_DEL_CONSULTORIO,
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  } ).format( new Date( inicio ) );
}
