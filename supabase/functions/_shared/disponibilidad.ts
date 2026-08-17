// El cálculo de disponibilidad, aparte del endpoint que lo usa.
//
// Vive separado por dos motivos. Uno: son funciones PURAS —les entra un dato y
// devuelven otro, no tocan la base ni la red— así que se pueden leer y probar
// sin desplegar nada. Dos: `POST /reservar` (etapa ③) tiene que preguntarse
// exactamente lo mismo que este endpoint, y dos copias de la misma regla se
// desincronizan siempre.

// La grilla entera del proyecto está construida sobre medias horas: la duración
// de los tratamientos es múltiplo de 30 por un `check` de la base, y los
// horarios de Cecilia caen en :00 y :30. Escrito acá una vez, con nombre, para
// que el día que el consultorio quiera cuartos de hora haya un solo lugar
// donde mirar.
export const MINUTOS_POR_BLOQUE = 30

// Toda la Argentina usa la misma hora: UTC-3, sin horario de verano desde 2009.
// Ninguna cuenta de este archivo depende de qué provincia sea, y esta constante
// no está acá por eso.
//
// Lo que se elige acá es CÓMO se escribe esa hora, que es otra cosa. Un
// `-03:00` tipeado a mano es un número congelado; el nombre de la zona es una
// consulta a la base de husos del sistema, que se actualiza cuando cambia una
// ley. El horario de verano ES una ley, no una ley de la naturaleza: el día que
// vuelva, la versión con el número fijo deja todos los turnos corridos una hora,
// en silencio y para todos.
//
// Y se nombra la zona de la región y no la de Buenos Aires porque esa base
// guarda las diferencias que YA hubo dentro del país: en diciembre de 2008
// Buenos Aires y Córdoba estaban en -02:00 por el horario de verano y San Luis
// en -03:00 (comprobado con `TZ=… date`). Santa Fe cae dentro de
// `America/Argentina/Cordoba`. Hoy las tres zonas devuelven lo mismo; la
// elección sólo se nota si un día vuelven a diferir.
export const ZONA = 'America/Argentina/Cordoba'


// ── Fechas ──────────────────────────────────────────────────────────────────

// ¿El texto es una fecha de verdad, y no sólo algo con forma de fecha?
//
// Las dos mitades hacen falta. La primera rechaza '17-08-2026' y 'ayer'; la
// segunda rechaza '2026-02-31', que pasa el molde y no existe en el almanaque.
// El truco de la segunda es que armamos la fecha y le preguntamos cómo se
// llama: si le pedimos el 31 de febrero, contesta '2026-03-03'.
export function esFechaValida( texto: string ): boolean {

  if ( !/^\d{4}-\d{2}-\d{2}$/.test( texto ) ) {
    return false
  }

  const fecha = new Date( `${ texto }T00:00:00Z` )

  if ( Number.isNaN( fecha.getTime() ) ) {
    return false
  }

  return fecha.toISOString().slice( 0, 10 ) === texto
}


// Todos los días del rango, de punta a punta, incluidos los dos extremos.
//
// La cuenta se hace en UTC —sumando un día de 24 horas exactas— y eso es
// correcto justamente porque acá no hay horas: son fechas de calendario. Un
// 17 de agosto es el 17 de agosto en cualquier huso. Las horas entran recién
// al armar los bloques, y ahí sí con la zona puesta.
export function listarDias( desde: string, hasta: string ): string[] {

  const dias: string[] = []

  const fin = new Date( `${ hasta }T00:00:00Z` )
  let actual = new Date( `${ desde }T00:00:00Z` )

  while ( actual <= fin ) {
    dias.push( actual.toISOString().slice( 0, 10 ) )
    actual = new Date( actual.getTime() + 24 * 60 * 60 * 1000 )
  }

  return dias
}


// Qué día de la semana es esa fecha, en la numeración ISO 8601: lunes 1 …
// domingo 7. Es la misma que guarda `horarios_base.dia_semana` desde la
// migración del 7-ago, así que el número que sale de acá se compara directo
// contra la tabla.
//
// JavaScript numera distinto —empieza en domingo 0— y por eso el domingo se
// traduce a mano. Es la clase de detalle que no falla con un error: devuelve
// los horarios del día equivocado.
export function diaSemanaISO( fecha: string ): number {

  const diaJS = new Date( `${ fecha }T00:00:00Z` ).getUTCDay()

  if ( diaJS === 0 ) {
    return 7
  }

  return diaJS
}


// Cuánto está corrida Santa Fe respecto de UTC ese día, con el formato que pide
// una fecha ISO: '-03:00'.
//
// Se pregunta por CADA fecha y no una sola vez para todo el rango porque un
// cambio de horario de verano cae en medio de un mes, no entre dos consultas.
//
// El mediodía UTC es a propósito: se pregunta por un instante lo bastante
// lejos de las dos medianoches como para que ningún desfase lo empuje al día
// anterior o al siguiente.
export function desfaseDeSantaFe( fecha: string ): string {

  const formato = new Intl.DateTimeFormat(
    'en-US',
    {
      timeZone: ZONA,
      timeZoneName: 'longOffset',
    },
  )

  const partes = formato.formatToParts( new Date( `${ fecha }T12:00:00Z` ) )
  const nombreDeZona = partes.find( ( parte ) => parte.type === 'timeZoneName' )

  // 'longOffset' devuelve 'GMT-03:00'. Sacado el prefijo queda lo que va
  // pegado al final de la fecha.
  return nombreDeZona.value.replace( 'GMT', '' )
}


// ── Horas ───────────────────────────────────────────────────────────────────

// Postgres devuelve las horas como '08:00:00'. Adentro del cálculo se trabajan
// como minutos desde la medianoche, que son un número común y corriente: así
// "media hora después" es sumar 30, sin cuentas con el 60.
export function aMinutos( hora: string ): number {

  const partes = hora.split( ':' )

  return Number( partes[ 0 ] ) * 60 + Number( partes[ 1 ] )
}


// El camino de vuelta: 510 → '08:30'. Se rellena con ceros a la izquierda
// porque '8:30' no es una hora válida en una fecha ISO.
export function aHora( minutos: number ): string {

  const horas = Math.floor( minutos / 60 )
  const resto = minutos % 60

  return `${ String( horas ).padStart( 2, '0' ) }:${ String( resto ).padStart( 2, '0' ) }`
}


// ── Excepciones ─────────────────────────────────────────────────────────────

// Una fila de `excepciones`, con lo poco que hace falta para decidir si tapa un
// día. No se pide la descripción ni el id: no entran en la cuenta y todo lo que
// se lee de más es algo que después hay que cuidar de no publicar.
export type Excepcion = {
  tipo: string,
  fecha_desde: string | null,
  fecha_hasta: string | null,
  semana_del_mes: number | null,
}


// ¿Esa fecha cae en la semana N del mes?
//
// "La tercera semana" en castellano es ambiguo, así que el proyecto eligió una
// sola lectura y la dejó escrita al lado del dato (migración
// `cargar_tercera_semana_de_cecilia`): es la fila del almanaque —de domingo a
// sábado— que contiene el día `7N − 6`. N=1 → día 1, N=2 → día 8, N=3 → día 15,
// N=4 → día 22.
//
// De domingo a sábado, y no de lunes a viernes, a propósito: Cecilia no atiende
// fines de semana y para ella da igual, pero para un profesional que sí trabaje
// sábados, "esa semana no vengo" incluye el sábado. Es lo que la frase quiere
// decir.
//
// La cuenta se hace parándose en el domingo de la semana de esa fecha y mirando
// los siete días de la fila: si alguno es el día ancla, es esa semana. Escrito
// así —y no calculando el número de semana— porque una fila del almanaque puede
// arrancar en el mes anterior (un mes que empieza martes tiene su semana 1 con
// el domingo y el lunes del mes pasado) y esa fila igual es la semana 1.
export function esSemanaDelMes( fecha: string, semana: number ): boolean {

  const diaAncla = 7 * semana - 6

  const dia = new Date( `${ fecha }T00:00:00Z` )
  const unDia = 24 * 60 * 60 * 1000

  // `getUTCDay()` numera desde el domingo en 0, así que restarlo es justo la
  // cantidad de días que hay que retroceder para llegar al domingo.
  const domingo = new Date( dia.getTime() - dia.getUTCDay() * unDia )

  let contador = 0

  while ( contador < 7 ) {

    const actual = new Date( domingo.getTime() + contador * unDia )

    if ( actual.getUTCDate() === diaAncla ) {
      return true
    }

    contador = contador + 1
  }

  return false
}


// ¿Esta excepción tapa ese día?
//
// Regla que atraviesa toda la función: una fila mal cargada SE IGNORA, nunca
// tapa "por las dudas". Tapar de más le cancela el turno a alguien real;
// ignorar de más deja un día abierto que la profesional ve en su agenda y
// arregla. Los dos errores no cuestan lo mismo.
//
// Las fechas se comparan como texto y es correcto, no una casualidad: el
// formato AAAA-MM-DD ordena igual alfabéticamente que en el almanaque, porque
// va de la unidad más grande a la más chica y todas van con ceros adelante.
function tapaEsteDia( fecha: string, excepcion: Excepcion ): boolean {

  if ( excepcion.tipo === 'unica' ) {

    // Sin fecha de inicio la fila no dice nada: no se sabe qué tapa.
    if ( !excepcion.fecha_desde ) {
      return false
    }

    // Sin fecha de fin tapa un solo día, que es como se carga un feriado.
    let ultimo = excepcion.fecha_desde

    if ( excepcion.fecha_hasta ) {
      ultimo = excepcion.fecha_hasta
    }

    return fecha >= excepcion.fecha_desde && fecha <= ultimo
  }

  if ( excepcion.tipo === 'recurrente' ) {

    if ( !excepcion.semana_del_mes ) {
      return false
    }

    // Las dos fechas acotan DESDE CUÁNDO y HASTA CUÁNDO rige la regla, no qué
    // días tapa. Vacías significan "sin fecha de fin", que es como está cargada
    // hoy la tercera semana.
    //
    // El apagador de todos los días es `activa`, que es lo que va a tocar la
    // profesional desde el panel. Estas dos fechas son el otro camino: dejar
    // programado por adelantado desde cuándo o hasta cuándo rige, sin que nadie
    // se tenga que acordar de apagarla ese día. Se miran acá porque si no se
    // miraran, cargar `fecha_hasta` no haría nada: la semana seguiría bloqueada
    // para siempre, sin error y sin aviso.
    if ( excepcion.fecha_desde && fecha < excepcion.fecha_desde ) {
      return false
    }

    if ( excepcion.fecha_hasta && fecha > excepcion.fecha_hasta ) {
      return false
    }

    return esSemanaDelMes( fecha, excepcion.semana_del_mes )
  }

  // Un `tipo` que no es ninguno de los dos es un dato que este código no sabe
  // leer. Misma regla que arriba: se ignora.
  return false
}


// El veredicto sobre un día, mirando todas las excepciones que llegaron.
//
// Las de la clínica (feriados, cierres) y las del profesional vienen mezcladas
// en la misma lista a propósito: para el paciente que mira el calendario el día
// está cerrado, y el motivo no le cambia nada.
export function diaTapado( fecha: string, excepciones: Excepcion[] ): boolean {

  return excepciones.some(
    ( excepcion ) => tapaEsteDia( fecha, excepcion ),
  )
}


// ── La grilla ───────────────────────────────────────────────────────────────

// Los bloques de media hora que entran en un tramo de agenda.
//
// El corte va con `fin`, NUNCA con `fin_maximo`. Un turno no puede EMPEZAR
// después del horario de cierre: `fin_maximo` sólo permite que uno que empezó
// a horario termine más tarde. Si esta función usara el techo, los lunes se
// ofrecería un turno a las 14:00, que es horario que la profesional no dio.
//
// La condición es "el bloque entero entra": el de las 13:30 termina 14:00 y
// entra justo; el de las 14:00 terminaría 14:30 y queda afuera.
export function bloquesDelTramo(
  fecha: string,
  inicio: string,
  fin: string,
  desfase: string,
): { inicio: string, estado: string }[] {

  const bloques: { inicio: string, estado: string }[] = []

  const primerMinuto = aMinutos( inicio )
  const ultimoMinuto = aMinutos( fin )

  let minuto = primerMinuto

  while ( minuto + MINUTOS_POR_BLOQUE <= ultimoMinuto ) {

    bloques.push( {
      inicio: `${ fecha }T${ aHora( minuto ) }:00${ desfase }`,
      estado: 'libre',
    } )

    minuto = minuto + MINUTOS_POR_BLOQUE
  }

  return bloques
}
