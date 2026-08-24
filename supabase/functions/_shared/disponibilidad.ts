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

// Cuánto antes hay que reservar. El bloque que arranca dentro de las próximas
// 12 horas se muestra igual, pero no se puede tomar: es el margen que pidió el
// consultorio para organizar el día.
//
// Es un piso DESLIZANTE, no "desde mañana": a las 20:00 de un lunes, el martes
// a las 9:00 ya no se puede reservar y el martes a las 15:00 sí.
export const HORAS_DE_ANTICIPACION = 12

// Hasta cuándo se puede reservar hacia adelante. Los días que caen más allá del
// techo no viajan en la respuesta: el calendario, sencillamente, no llega hasta
// ahí.
//
// Se cuenta en MESES de almanaque y no en una cantidad fija de días para que el
// techo signifique lo mismo que dice la frase con la que se decidió: "el mismo
// día, dos meses después".
export const MESES_DE_HORIZONTE = 2

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


// ¿El texto es un INSTANTE de verdad — un momento único, sin ambigüedad?
//
// Es la hermana de la de arriba, y la diferencia es todo el punto. Una FECHA
// ('2026-09-01') es un día del almanaque y significa lo mismo en cualquier
// lugar del mundo. Un INSTANTE es un día CON hora, y una hora sin huso no
// dice nada: las 09:00 de Santa Fe y las 09:00 de Madrid son dos momentos
// distintos.
//
// 🔴 Por eso el desfase es OBLIGATORIO y ésta es la mitad que importa. Si
// llegara '2026-09-01T09:00:00' pelado, JavaScript lo lee con el reloj del
// servidor —que en la nube está en UTC— y lo convierte en las 06:00 de Santa
// Fe. El turno entraría tres horas corrido, sin ningún error de por medio.
// Con el desfase puesto, el texto significa lo mismo lo lea quien lo lea.
//
// Se aceptan las dos formas que existen: '-03:00' (la que devuelve
// `GET /horarios-disponibles`) y 'Z', que es el nombre corto de '+00:00'.
export function esInstanteValido( texto: string ): boolean {

  const molde = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$/

  if ( !molde.test( texto ) ) {
    return false
  }

  // El molde deja pasar el 31 de febrero y las 25:00; esto no. `Date.parse`
  // devuelve NaN cuando el texto tiene la forma correcta y el almanaque no lo
  // admite.
  return !Number.isNaN( Date.parse( texto ) )
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


// La misma fecha, unos meses más adelante.
//
// No se puede hacer sumando días: los meses no miden todos lo mismo, así que
// "dos meses" no es un número fijo de días. Se cuenta en el almanaque.
//
// El caso que obliga a escribirla con cuidado es el 31: el 31 de diciembre más
// dos meses sería el 31 de febrero, que no existe. JavaScript, librado a su
// suerte, se pasa al 3 de marzo — o sea que el techo de reserva quedaría TRES
// DÍAS más lejos de lo que el consultorio autorizó, en silencio. Acá se recorta
// al último día del mes de destino.
export function sumarMeses( fecha: string, meses: number ): string {

  const partes = fecha.split( '-' )

  const anio = Number( partes[ 0 ] )
  const mes = Number( partes[ 1 ] )
  const dia = Number( partes[ 2 ] )

  // El mes de destino, apuntando al día 1, que existe en todos los meses.
  // `Date.UTC` numera los meses desde 0 y acepta que el número se pase de 11:
  // el mes 13 de 2026 es febrero de 2027. El fin de año se resuelve solo.
  const destino = new Date( Date.UTC( anio, ( mes - 1 ) + meses, 1 ) )

  // Cuántos días tiene ese mes: se pide el día 0 del mes SIGUIENTE, que es el
  // último día del mes de destino.
  const ultimoDelMes = new Date(
    Date.UTC(
      destino.getUTCFullYear(),
      destino.getUTCMonth() + 1,
      0,
    ),
  ).getUTCDate()

  let diaDestino = dia

  if ( diaDestino > ultimoDelMes ) {
    diaDestino = ultimoDelMes
  }

  destino.setUTCDate( diaDestino )

  return destino.toISOString().slice( 0, 10 )
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
// Una pieza suelta de las que devuelve `formatToParts`, buscada por nombre.
//
// `formatToParts` no devuelve un objeto con casilleros rotulados: devuelve una
// LISTA de piezas, y hay que ir a buscar la que se quiere. TypeScript no puede
// saber que la pieza está —depende de las opciones con que se armó el
// formato—, así que la pregunta se hace UNA vez acá adentro y no cuatro veces
// desparramadas por el archivo.
//
// Si la pieza faltara, sería un bug de este archivo y no un dato del mundo:
// por eso se rompe fuerte y con nombre, en vez de dejar que un vacío se cuele
// adentro de una fecha y arme un '2026-undefined-01' que nadie va a rastrear.
function parteDelFormato(
  partes: Intl.DateTimeFormatPart[],
  tipo: string,
): string {

  const parte = partes.find( ( candidata ) => candidata.type === tipo )

  if ( !parte ) {
    throw new Error( `El formato de fecha no devolvió la parte "${ tipo }"` )
  }

  return parte.value
}


export function desfaseDeSantaFe( fecha: string ): string {

  const formato = new Intl.DateTimeFormat(
    'en-US',
    {
      timeZone: ZONA,
      timeZoneName: 'longOffset',
    },
  )

  const partes = formato.formatToParts( new Date( `${ fecha }T12:00:00Z` ) )

  // 'longOffset' devuelve 'GMT-03:00'. Sacado el prefijo queda lo que va
  // pegado al final de la fecha.
  return parteDelFormato( partes, 'timeZoneName' ).replace( 'GMT', '' )
}


// Qué día del almanaque es en Santa Fe en ese instante.
//
// Hace falta porque "hoy" no tiene una sola respuesta: a las 22:00 de un lunes
// de Santa Fe, en UTC ya es martes. El techo de reserva se cuenta desde el día
// del consultorio, no desde el del servidor, que corre en otro país y ni se
// sabe en cuál.
//
// El instante ENTRA POR PARÁMETRO, no se pregunta acá adentro, y es a
// propósito: una función que mira el reloj por su cuenta devuelve algo distinto
// cada vez que se la llama y no se la puede probar. El reloj se mira una sola
// vez, arriba de todo, y el instante se pasa de mano en mano.
export function fechaEnSantaFe( instante: Date ): string {

  const formato = new Intl.DateTimeFormat(
    'en-US',
    {
      timeZone: ZONA,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    },
  )

  const partes = formato.formatToParts( instante )

  const anio = parteDelFormato( partes, 'year' )
  const mes = parteDelFormato( partes, 'month' )
  const dia = parteDelFormato( partes, 'day' )

  return `${ anio }-${ mes }-${ dia }`
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

// Un tramo de la agenda semanal, tal como viene de `horarios_base`.
//
// `fin_maximo` puede venir vacío, y eso NO es un dato faltante: significa "no
// hay nada después, el turno no se puede estirar". Cinco de los siete tramos de
// Cecilia tienen techo; los dos que cierran el día, no.
export type Tramo = {
  inicio: string,
  fin: string,
  fin_maximo: string | null,
}


// Los bloques de media hora que entran en un tramo de agenda, cada uno con el
// estado que le corresponde MIRANDO SÓLO EL TRAMO: acá no se sabe nada de
// turnos ya tomados ni de qué hora es ahora.
//
// El corte va con `fin`, NUNCA con `fin_maximo`. Un turno no puede EMPEZAR
// después del horario de cierre: `fin_maximo` sólo permite que uno que empezó
// a horario termine más tarde. Si esta función usara el techo para cortar, los
// lunes se ofrecería un turno a las 14:00, que es horario que la profesional no
// dio.
//
// La condición del corte es "el bloque entero entra": el de las 13:30 termina
// 14:00 y entra justo; el de las 14:00 terminaría 14:30 y queda afuera.
//
// Y una vez que el bloque existe, la segunda pregunta es si el TRATAMIENTO cabe
// ahí. Una limpieza de 60 minutos que arranca el martes a las 16:30 termina
// 17:30, y ese martes no hay nada después de las 17:00: el bloque existe, se
// muestra, y sale `no_entra`. La cuenta va sobre el RANGO del turno, no sobre
// cuántos bloques ocupa — con `fin_maximo` de por medio, el turno puede
// terminar donde ya no hay bloques.
export function bloquesDelTramo(
  fecha: string,
  tramo: Tramo,
  duracion: number,
  desfase: string,
): { inicio: string, estado: string }[] {

  const bloques: { inicio: string, estado: string }[] = []

  const primerMinuto = aMinutos( tramo.inicio )
  const ultimoMinuto = aMinutos( tramo.fin )

  // Hasta dónde puede TERMINAR un turno de este tramo. Sin techo cargado, el
  // límite es la hora de cierre.
  let techo = ultimoMinuto

  if ( tramo.fin_maximo ) {
    techo = aMinutos( tramo.fin_maximo )
  }

  let minuto = primerMinuto

  while ( minuto + MINUTOS_POR_BLOQUE <= ultimoMinuto ) {

    let estado = 'libre'

    if ( minuto + duracion > techo ) {
      estado = 'no_entra'
    }

    bloques.push( {
      inicio: `${ fecha }T${ aHora( minuto ) }:00${ desfase }`,
      estado: estado,
    } )

    minuto = minuto + MINUTOS_POR_BLOQUE
  }

  return bloques
}


// ── Turnos ya tomados ───────────────────────────────────────────────────────

// Una fila de `turnos`, con lo único que hace falta para saber si ocupa.
//
// Nombre, nota y observaciones NO se piden. No es prolijidad: lo que no se lee
// no se puede publicar por accidente, y `observaciones_paciente` puede tener
// datos de salud.
export type Turno = {
  inicio: string,
  duracion_min: number,
}


// Correr una fecha unos días, sin horas de por medio.
//
// Se suman días de 24 horas exactas en UTC, que es correcto por lo mismo que en
// `listarDias`: acá no hay horas, hay fechas de calendario.
export function sumarDias( fecha: string, dias: number ): string {

  const base = new Date( `${ fecha }T00:00:00Z` )
  const movida = new Date( base.getTime() + dias * 24 * 60 * 60 * 1000 )

  return movida.toISOString().slice( 0, 10 )
}


// ¿Se pisa con algún turno ya tomado un turno que empezara en `inicio` y durara
// `duracion` minutos?
//
// 🔴 Las dos desigualdades van ESTRICTAS, y no es un detalle de estilo: es la
// misma comparación que hace la base con `tstzrange`, que incluye el arranque y
// excluye el final. Un turno de 12:00 a 13:00 y otro de 13:00 a 13:30 NO se
// pisan. Si acá se escribiera `<=`, la grilla marcaría ocupado un bloque que la
// base acepta sin chistar: el error no falla, contesta mal en silencio.
//
// La comparación va sobre el RANGO ENTERO del turno, no bloque por bloque. Así
// un turno de 90 minutos tapa los tres bloques que toca, y la media hora que se
// estira más allá del cierre también ocupa — si no, la pantalla ofrecería un
// hueco y el `POST /reservar` lo rechazaría con un 409 que el paciente no puede
// entender.
//
// Un turno cancelado no llega hasta acá: se filtran por `activo` al pedirlos.
// El hueco vuelve entero a la grilla, que es la decisión del § 9.3.
export function bloqueOcupado(
  inicio: string,
  duracion: number,
  turnos: Turno[],
): boolean {

  const arranca = Date.parse( inicio )
  const termina = arranca + duracion * 60 * 1000

  return turnos.some( ( turno ) => {

    const turnoArranca = Date.parse( turno.inicio )
    const turnoTermina = turnoArranca + turno.duracion_min * 60 * 1000

    return turnoArranca < termina && turnoTermina > arranca
  } )
}


// El mismo horario, una sola vez.
//
// Dos tramos del mismo día que se pisen son un error de carga —hoy nada lo
// impide en la base— y sin esto el paciente vería las 11:00 dos veces en la
// pantalla. Se defiende acá porque el dato lo carga una persona a mano.
export function unificarBloques(
  bloques: { inicio: string, estado: string }[],
): { inicio: string, estado: string }[] {

  const vistos = new Set< string >()
  const unicos: { inicio: string, estado: string }[] = []

  bloques.forEach( ( bloque ) => {

    if ( vistos.has( bloque.inicio ) ) {
      return
    }

    vistos.add( bloque.inicio )
    unicos.push( bloque )
  } )

  return unicos
}


// ── La ventana de reserva ───────────────────────────────────────────────────

// ¿Ese bloque cae adentro del margen de anticipación, o sea demasiado cerca
// como para reservarlo?
//
// Se comparan dos INSTANTES, los dos en milisegundos desde 1970, así que acá no
// hay husos ni almanaques de por medio: `inicio` ya trae el `-03:00` puesto y da
// igual dónde esté el reloj del servidor.
//
// El bloque vencido no se saca de la respuesta, se marca. Si a las 10 de la
// mañana desaparecieran todos los bloques de hoy, el día de hoy se vería
// idéntico a un día en que el consultorio no atiende — que es exactamente lo
// que se decidió evitar el 6-ago con los bloques ocupados.
export function fueraDePlazo( inicio: string, ahora: Date ): boolean {

  const limite = ahora.getTime() + HORAS_DE_ANTICIPACION * 60 * 60 * 1000

  return Date.parse( inicio ) < limite
}
