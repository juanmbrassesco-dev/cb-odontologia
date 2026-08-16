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

// Santa Fe se rige por esta zona. Se usa el NOMBRE y no un `-03:00` escrito a
// mano a propósito: hoy Argentina no aplica horario de verano —no lo usa desde
// 2009— pero eso es una ley, no una ley de la naturaleza. Con el desfase fijo,
// el día que vuelva, todos los turnos quedan corridos una hora, en silencio y
// para todos. Con el nombre, el desfase lo calcula el sistema cada vez.
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
