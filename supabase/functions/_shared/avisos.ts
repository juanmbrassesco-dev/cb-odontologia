// Portero de CB Odontología — los avisos por correo de un turno
//
// DOS MOTIVOS, EL MISMO CAMINO: se reservó un turno, o se canceló. Cambian los
// textos y el asunto; NO cambia nada más — el remitente, la lectura del
// entorno, el formato de la fecha, la deduplicación consultorio/profesional y
// la redirección a la casilla de prueba son los mismos para los dos.
//
// 🔴 POR QUÉ UN SOLO ARCHIVO CON UN `motivo` Y NO DOS ARCHIVOS CALCADOS: es el
// mismo motivo por el que la consulta de la pareja se mudó a `parejas.ts` el
// 25-ago-2026. Todo lo de arriba tiene que valer para los dos avisos o no vale
// para ninguno; con dos copias, el día que se borre `CORREO_DE_PRUEBA` habría
// que acordarse de tocar las dos, y olvidarse de una NO FALLA CON ERROR: manda
// correos de verdad a pacientes de verdad desde el archivo que quedó viejo.
//
// UN SOLO DISPARO, TRES DESTINATARIOS: el paciente (confirmación), el
// consultorio y el profesional (aviso operativo). Van en un ÚNICO pedido al
// proveedor —un "lote"— y aun así cada uno recibe su propio texto: el paciente
// lee "tu turno quedó reservado", los otros dos leen "entró un turno".
//
// 🔴 ESTE MÓDULO NO PUEDE HACER FALLAR NI UNA RESERVA NI UNA CANCELACIÓN. Si el
// proveedor está caído, si la clave venció o si falta un dato, devuelve `false`
// y se acabó. El turno ya está anotado —o ya está apagado— y un correo caído no
// lo puede deshacer. Por eso NINGUNA función de acá lanza un error: todas
// devuelven algo.
//
// ⚠ LAS OBSERVACIONES DEL PACIENTE NO VIAJAN EN NINGÚN CORREO, y no es un
// olvido. Pueden traer datos de salud, y un correo se copia solo: queda en el
// servidor del proveedor, en el de Gmail, en tres casillas y en los teléfonos
// de esas tres personas. El aviso dice QUE HAY una observación; el texto se lee
// donde vive, que es la base. El término es MINIMIZACIÓN DE DATOS (data
// minimization): no mover un dato sensible más lejos de lo que el trabajo pide.

import { ZONA } from './disponibilidad.ts'

// La dirección del proveedor para mandar VARIOS mensajes en un solo pedido.
// Existe también `/emails` para uno solo; se usa la de lote porque el § 6 del
// documento pide un disparo, no tres.
const RESEND_LOTE = 'https://api.resend.com/emails/batch'

// Mientras el dominio no esté verificado, el proveedor sólo deja mandar DESDE
// esta dirección suya. El nombre de adelante sí es libre, y es lo único que ve
// el que recibe.
const REMITENTE_DE_PRUEBA = 'CB Odontología <onboarding@resend.dev>'

const FIRMA = 'CB Odontología y Estética — Santa Fe'

// Por qué salió este correo. Es un texto de dos valores y no un `true`/`false`
// a propósito: `enviarAvisos( datos, true )` no se entiende sin ir a leer la
// función, y `enviarAvisos( datos, 'cancelacion' )` se entiende solo. Misma
// forma que `EstadoDeLaPareja` en `parejas.ts`.
export type MotivoDelAviso =
  | 'reserva'
  | 'cancelacion'

// Un dato del entorno, o `null` si no está cargado.
//
// Es el mismo `textoLimpio` de `reservar`, pero sobre el entorno en vez de
// sobre el cuerpo de un pedido: un secreto cargado con un espacio en blanco
// adentro existe para `Deno.env.get` y no sirve para nada.
function delEntorno( nombre: string ): string | null {

  const valor = Deno.env.get( nombre )

  if ( !valor ) {
    return null
  }

  const limpio = valor.trim()

  if ( limpio.length === 0 ) {
    return null
  }

  return limpio
}

// El instante del turno, escrito como lo lee una persona:
// 'martes, 1 de septiembre de 2026, 09:00'.
//
// La zona sale de `disponibilidad.ts` y no se vuelve a escribir acá: el turno
// se guarda con desfase, pero el que lo lee está en Santa Fe y espera la hora
// de Santa Fe.
function cuandoEnPalabras( inicio: string ): string {

  return new Intl.DateTimeFormat(
    'es-AR',
    {
      timeZone: ZONA,
      dateStyle: 'full',
      timeStyle: 'short',
    },
  ).format( new Date( inicio ) )
}

// Lo mismo, corto, para que entre en el asunto: '1/9, 09:00'.
function cuandoCompacto( inicio: string ): string {

  return new Intl.DateTimeFormat(
    'es-AR',
    {
      timeZone: ZONA,
      day: 'numeric',
      month: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    },
  ).format( new Date( inicio ) )
}

// Sólo el día, sin la hora: '1/9'. Va únicamente en el asunto del aviso
// operativo, como referencia mínima para que Cecilia ubique el correo en la
// bandeja sin abrirlo.
//
// 🔴 POR QUÉ EL DÍA Y NADA MÁS. Hasta el 29-ago-2026 ese asunto decía
// '3/9, 09:00 a. m. — Pérez': fecha, hora y apellido del paciente juntos, en el
// lugar más expuesto del mensaje. Que la casilla sea del consultorio no cambia
// dónde se muestra ni por dónde viaja. Se sacó el apellido y la hora, y quedó
// el día, que es lo mínimo para ordenar la bandeja. (Decisión de Juan: el
// número de turno tampoco, aunque no identifique a nadie.)
function cuandoElDia( inicio: string ): string {

  return new Intl.DateTimeFormat(
    'es-AR',
    {
      timeZone: ZONA,
      day: 'numeric',
      month: 'numeric',
    },
  ).format( new Date( inicio ) )
}

// EL CIERRE DEL CORREO DEL PACIENTE — cómo cancela y por dónde nos ubica, en
// un solo lugar.
//
// 🔴 POR QUÉ ES UNA FUNCIÓN Y NO DOS. Eran dos —una para cancelar, otra para el
// contacto— y las dos terminaban diciéndole lo mismo con verbos distintos:
// «escribinos», «avisanos», «dejanos un mensaje». Cuatro renglones seguidos
// pidiendo la misma acción con cuatro palabras. Juntas en una función, la
// repetición no se puede colar: el texto se arma de una sola pasada.
// (Lo levantó Juan el 29-ago-2026 leyendo el correo, no el código.)
//
// 🔴 LA DIRECCIÓN DE LA PANTALLA NO ESTÁ CLAVADA Y NO LLEVA NINGÚN TOKEN.
//
//   - No está clavada porque la pantalla todavía no existe: el día que el sitio
//     se publique se carga `URL_MIS_TURNOS` como secreto y este correo la
//     nombra, sin volver a desplegar la función. Anotado en § 14 con disparador.
//   - No lleva token porque un correo se reenvía. Un link con token adentro es
//     una CREDENCIAL AL PORTADOR (bearer credential): el que lo tiene, entra.
//     Ésta es pelada: del otro lado hay que iniciar sesión igual, así que si se
//     filtra no sirve para nada. (Decisión del 25-ago-2026, § 6.)
//
// 🔴 NO VA EN EL AVISO OPERATIVO, y no es un olvido: ese correo lo recibe
// Cecilia. Decirle «contactate con nosotros» es mandarla a escribirse a sí
// misma.
//
// ⚠ LOS TRES DATOS SALEN DEL ENTORNO Y NINGUNO FALLA CON ERROR SI FALTA. Sin
// pantalla, el correo cae en la frase que pide avisar; sin correo y sin
// WhatsApp, el cierre DESAPARECE ENTERO. Es la trampa de siempre: lo que no
// está cargado no se nota hasta que alguien lee un correo.
function cierreDelCorreo( motivo: MotivoDelAviso ): string[] {

  const pantalla = delEntorno( 'URL_MIS_TURNOS' )
  const whatsapp = delEntorno( 'WHATSAPP_DEL_CONSULTORIO' )
  const correo = delEntorno( 'CORREO_DEL_CONSULTORIO' )

  const renglones: string[] = []

  // Cómo cancelar solo. Sólo si el turno sigue vivo —a un turno cancelado no se
  // lo cancela de nuevo— y sólo si la pantalla existe.
  if ( motivo === 'reserva' && pantalla ) {
    renglones.push(
      '',
      'Si no vas a poder venir, podés cancelarlo vos desde:',
      `  ${ pantalla }`,
      'Entrá con el mismo correo con el que reservaste.',
    )
  }

  // Por dónde nos ubican. Las tres formas van escritas enteras y no armadas por
  // pedazos: lo que se lee es la oración, no el código.
  let via = ''

  if ( correo && whatsapp ) {
    via = `por correo a ${ correo } o por WhatsApp al ${ whatsapp }.`
  }

  if ( correo && !whatsapp ) {
    via = `por correo a ${ correo }.`
  }

  if ( !correo && whatsapp ) {
    via = `por WhatsApp al ${ whatsapp }.`
  }

  if ( !via ) {
    return renglones
  }

  // 🔑 LA APERTURA CAMBIA SEGÚN LO QUE YA SE DIJO ARRIBA, y ahí está toda la
  // gracia de haberlas juntado. Si el turno está vivo y NO hay pantalla, éste
  // es el único renglón que le dice cómo cancelar, así que lo nombra. En los
  // otros dos casos —ya se explicó arriba, o el turno está cancelado— nombrarlo
  // sería repetir o hablar de un turno que ya no existe.
  let apertura = 'Para cualquier consulta, contactate con nosotros'

  if ( motivo === 'reserva' && !pantalla ) {
    apertura = 'Si no vas a poder venir o necesitás consultarnos algo, contactate con nosotros'
  }

  renglones.push( '', apertura, via )

  return renglones
}

// Todo lo que hace falta para escribir los tres correos. Lo arma el endpoint,
// que es el único que tuvo todos estos datos a mano.
export type DatosDelAviso = {
  turnoId: number
  inicio: string
  duracionMin: number
  tratamiento: string
  // A qué vino el paciente, que NO siempre es lo que se agenda: el que pide
  // ortodoncia se lleva una consulta de 30 (`_shared/arranque.ts`). Opcional
  // porque la cancelación no lo manda: ahí lo que importa es el hueco que se
  // libera, y un dato de salud que no hace falta no viaja.
  motivoConsulta?: string | null
  // Qué hora se le comunicó al paciente la última vez POR ESTE TURNO. Vacía si
  // nunca se le avisó nada, que es el caso de toda reserva nueva. Sólo la
  // repesca la manda: es la única que avisa de turnos que ya existían.
  //
  // ⚠ EL TIPO GENERADO DEL RPC LA DA COMO `string` Y MIENTE. El generador no
  // sabe qué columnas de una función pueden venir vacías, así que TypeScript no
  // va a exigir el chequeo por su cuenta: lo hace `queEsEsteAviso` a mano. Le
  // pasa lo mismo a `tratamiento_nombre`, y por eso la repesca ya lo chequeaba.
  inicioAvisado?: string | null
  // Cómo entró el turno al sistema: 'web' o 'manual', los dos únicos valores
  // que la base acepta desde la migración 20260828135023. Es la columna
  // `turnos.canal`, y sirve para una sola cosa acá: que el aviso operativo no
  // diga «entró por la web» de un turno que Cecilia cargó a mano.
  //
  // Opcional porque quien no lo sepa no tiene que inventarlo: sin este dato el
  // aviso usa un texto neutro, que es cierto en los dos casos.
  canal?: string | null
  pacienteNombre: string
  pacienteApellido: string
  pacienteCorreo: string
  profesionalNombre: string
  profesionalApellido: string
  profesionalCorreo: string
  tieneObservaciones: boolean
}

// Un mensaje ya listo para el proveedor.
type Mensaje = {
  from: string
  to: string[]
  subject: string
  text: string
}

// QUÉ ES ESTE AVISO PARA EL PACIENTE, deducido de un solo dato.
//
// El mismo turno puede mandar el correo de «reserva» más de una vez: cuando
// nace, y cada vez que Cecilia le cambia algo desde el Table Editor —el trigger
// de la migración 20260828204527 borra la marca y la repesca lo levanta—. Los
// tres casos piden textos distintos, y ninguno necesita un estado nuevo:
//
//   `inicio_avisado` VACÍA          → nunca se le avisó nada       → 'primero'
//   LLENA y distinta de `inicio`    → se le avisó otra hora        → 'hora-nueva'
//   LLENA e igual a `inicio`        → se le avisó esta misma hora,
//                                     y algo cambió igual          → 'datos-nuevos'
//
// El tercero existe porque el trigger borra la marca ante CINCO datos, no sólo
// la hora: si le cambian el profesional y la hora queda igual, el correo viejo
// pasa a mentir lo mismo. Lo levantó Juan el 29-ago-2026, y de paso mostró que
// no hacía falta guardar nada más: el profesional actual ya viaja en la ficha,
// que se arma leyendo la tabla. Una cosa es INFORMAR un dato —gratis, está en
// la base— y otra DETECTAR que cambió, que es lo único que pide memoria.
//
// ⚠ SE COMPARAN INSTANTES, NO TEXTOS. La misma hora puede volver de la base
// escrita de dos formas —'...+00:00' y '...Z'—, y comparadas como texto darían
// distintas. `getTime()` las lleva a un número, que es el mismo para las dos.
function queEsEsteAviso(
  datos: DatosDelAviso,
): 'primero' | 'hora-nueva' | 'datos-nuevos' {

  if ( !datos.inicioAvisado ) {
    return 'primero'
  }

  const avisada = new Date( datos.inicioAvisado ).getTime()
  const real    = new Date( datos.inicio ).getTime()

  if ( avisada !== real ) {
    return 'hora-nueva'
  }

  return 'datos-nuevos'
}

// La ficha del turno: los TRES renglones que van igual en todos los correos. Lo
// único que cambia es el tiempo del verbo — 'Cuándo' mientras el turno va a
// pasar, 'Cuándo era' cuando ya no va a pasar.
//
// 🔴 LA DURACIÓN NO ESTÁ ACÁ Y NO SE VUELVE A SUMAR. Era un cuarto renglón de
// esta ficha, así que viajaba también al correo del paciente — y la duración es
// dato de la agenda del consultorio, no algo que el paciente necesite para
// venir. El correo del paciente lleva lo mínimo para presentarse; el operativo
// se la agrega por su cuenta, que es donde sí hace falta.
//
// Lo levantó Juan el 28-ago-2026 leyendo un correo de prueba. Es divulgación de
// información (information disclosure) de baja gravedad, y la regla que la
// corrige es la misma que ordena los permisos: cada destinatario recibe lo que
// necesita y nada más.
function fichaDelTurno( datos: DatosDelAviso, motivo: MotivoDelAviso ): string[] {

  let cuando = 'Cuándo'

  if ( motivo === 'cancelacion' ) {
    cuando = 'Cuándo era'
  }

  const renglones = [
    `  Tratamiento: ${ datos.tratamiento }`,
    `  Profesional: ${ datos.profesionalNombre } ${ datos.profesionalApellido }`,
    `  ${ cuando }: ${ cuandoEnPalabras( datos.inicio ) }`,
  ]

  // El cuarto renglón aparece SÓLO cuando el turno se movió de hora, y va en
  // los TRES correos —decisión de Juan, 29-ago-2026: «que vaya a todos para que
  // no haya confusiones»—. El paciente necesita saber cuál turno reemplaza;
  // Cecilia y el profesional, qué hueco quedó libre.
  //
  // En la cancelación no va: ahí no hay nada que reemplace a nada.
  //
  // `horaAvisada` se saca a una variable en vez de usarse directo porque el
  // `if` que la chequea es también el que le prueba a TypeScript que no está
  // vacía. Sobre el campo del objeto esa prueba no se sostiene sola.
  const horaAvisada = datos.inicioAvisado

  if (
    motivo === 'reserva'
    && horaAvisada
    && queEsEsteAviso( datos ) === 'hora-nueva'
  ) {
    renglones.push( `  Antes era: ${ cuandoEnPalabras( horaAvisada ) }` )
  }

  return renglones
}

function correoParaElPaciente(
  datos: DatosDelAviso,
  remitente: string,
  motivo: MotivoDelAviso,
): Mensaje {

  const ficha = fichaDelTurno( datos, motivo )

  if ( motivo === 'cancelacion' ) {

    const texto = [
      `Hola ${ datos.pacienteNombre },`,
      '',
      'Tu turno quedó cancelado.',
      '',
      ...ficha,
      '',
      'El horario vuelve a estar disponible para quien lo necesite. Si querés',
      'sacar otro turno, entrá al sitio cuando quieras.',
      ...cierreDelCorreo( motivo ),
      '',
      FIRMA,
    ].join( '\n' )

    return {
      from: remitente,
      to: [ datos.pacienteCorreo ],
      subject: 'Tu turno en CB Odontología quedó cancelado',
      text: texto,
    }
  }

  // 🔴 ESTE CORREO SALE VARIAS VECES POR EL MISMO TURNO, Y NO PUEDEN SER TODOS
  // IGUALES.
  //
  // Sale cuando el turno nace, cuando le mueven la hora y cuando le cambian
  // cualquier otro dato. Decía «quedó reservado» las tres veces, y así la
  // paciente leía altas nuevas en vez de cambios — creía tener dos turnos y se
  // presentaba al viejo. Lo levantó Juan el 28-ago-2026 leyendo los correos en
  // fila: en la tabla hay UNA fila y todo parece bien.
  //
  // 🔑 LOS TRES ASUNTOS SON DISTINTOS ENTRE SÍ, y eso no es estética: con el
  // asunto repetido, varios gestores de correo los agrupan en una sola
  // conversación y la paciente ni ve que llegó otro mensaje.
  //
  // 🔴 Y NINGUNO LLEVA LA FECHA, aunque hasta el 29-ago-2026 la llevaban.
  //
  // La fecha de un turno médico es DATO DE SALUD, y el asunto es el peor lugar
  // donde ponerlo: se muestra en la pantalla bloqueada del teléfono —lo lee
  // cualquiera que pase al lado— y queda escrito en los registros de servidores
  // de correo que no controlamos. La regla se llama MINIMIZACIÓN DE DATOS: no
  // viaja lo que no hace falta que viaje, y acá no hace falta porque el cuerpo
  // ya lo dice. Lo levantó Juan.
  //
  // La fecha estaba puesta para que los correos no se agruparan, y ese motivo
  // era flojo: el agrupado depende del gestor de correo, y lo que de verdad
  // distingue un aviso de otro es EL TEXTO diciendo que es un cambio. Los
  // cuatro asuntos difieren entre sí sin nombrar ninguna fecha.
  //
  // ⚠ Se probó también un renglón que decía «si tenías otro horario anotado,
  // éste lo reemplaza», y se sacó por CONDICIONAL: le pedía a la paciente
  // resolver un «si» que ella no podía chequear. Lo de acá abajo no pregunta,
  // afirma — la base sabe cuál era la hora anterior.
  let titular = 'Tu turno quedó agendado.'
  let asunto = 'Tu turno en CB Odontología quedó agendado'

  // Renglones que se agregan debajo de la ficha, o ninguno. Empieza vacío
  // porque el correo de un turno nuevo no aclara nada: no hay nada anterior.
  const aclaracion: string[] = []

  if ( queEsEsteAviso( datos ) === 'hora-nueva' ) {

    titular = 'El horario de tu turno cambió.'
    asunto = 'Cambió el horario de tu turno en CB Odontología'

    aclaracion.push(
      '',
      'El horario anterior ya no está reservado.',
    )
  }

  // 🔴 NO SABEMOS QUÉ CAMBIÓ, así que no se nombra: el trigger borra la marca
  // ante cinco datos y no deja dicho cuál fue. Decir «cambió el profesional»
  // cuando lo que cambió fue el tratamiento sería mentir con cara de precisión.
  //
  // Lo que sí se puede hacer, y alcanza: dejar clarísimo que la ficha de abajo
  // es LO NUEVO. Se dice en el mismo titular, no en un renglón aparte.
  //
  // ⚠ Acá hubo un renglón que decía «si querés ver qué cambió, comparalos con
  // el correo anterior», y lo sacó Juan el 29-ago-2026 con dos motivos: no hace
  // falta aclararlo —quien tenga la duda va a buscar el correo viejo igual— y
  // no queda profesional. **Un correo no le da tareas al paciente.**
  if ( queEsEsteAviso( datos ) === 'datos-nuevos' ) {

    titular = 'Hubo un cambio en tu turno. Estos son los datos nuevos:'
    asunto = 'Cambió tu turno en CB Odontología'
  }

  const texto = [
    `Hola ${ datos.pacienteNombre },`,
    '',
    titular,
    '',
    ...ficha,
    ...aclaracion,
    ...cierreDelCorreo( motivo ),
    '',
    FIRMA,
  ].join( '\n' )

  return {
    from: remitente,
    to: [ datos.pacienteCorreo ],
    subject: asunto,
    text: texto,
  }
}

// El aviso operativo. Es el mismo texto para el consultorio y para el
// profesional: los dos necesitan saber lo mismo.
function avisoOperativo(
  datos: DatosDelAviso,
  remitente: string,
  destino: string,
  motivo: MotivoDelAviso,
): Mensaje {

  // 🔴 EL TITULAR NO PUEDE AFIRMAR EL ORIGEN SI NO LO SABE.
  //
  // Decía siempre «entró un turno nuevo por la web», también cuando el turno lo
  // había cargado Cecilia a mano y el aviso salía por la repesca. Lo levantó
  // Juan el 29-ago-2026, y tenía razón dos veces: el correo mentía, y mi
  // respuesta —«no puedo distinguir el origen»— era falsa. `turnos.canal` lo
  // dice desde el 28-ago; lo que faltaba era traerlo hasta acá.
  //
  // El texto neutro es el que se usa cuando el dato no viaja. No es un caso
  // teórico: `cancelar` no lo manda, porque para una cancelación el origen del
  // turno no le dice nada a nadie.
  let titular = 'Entró un turno nuevo.'
  let encabezadoDelAsunto = 'Nuevo turno'

  if ( datos.canal === 'web' ) {
    titular = 'Entró un turno nuevo por la web.'
  }

  if ( datos.canal === 'manual' ) {
    titular = 'Se le avisó al paciente de un turno cargado a mano.'
  }

  // Los tres avisos de un turno vivo se distinguen igual que los del paciente y
  // por el mismo motivo: con el asunto repetido, la casilla del consultorio los
  // agrupa en una conversación y el segundo pasa desapercibido.
  //
  // El `motivo === 'reserva'` de las dos condiciones no sobra: `queEsEsteAviso`
  // contesta lo mismo para un turno cancelado —también tiene hora avisada— y
  // sin ese chequeo una cancelación saldría titulada «se movió un turno».
  if ( motivo === 'reserva' && queEsEsteAviso( datos ) === 'hora-nueva' ) {
    titular = 'Se movió un turno de horario.'
    encabezadoDelAsunto = 'Turno movido'
  }

  if ( motivo === 'reserva' && queEsEsteAviso( datos ) === 'datos-nuevos' ) {
    titular = 'Cambió un dato de un turno.'
    encabezadoDelAsunto = 'Turno modificado'
  }

  if ( motivo === 'cancelacion' ) {
    titular = 'Se canceló un turno desde la web.'
    encabezadoDelAsunto = 'Turno cancelado'
  }

  // 🔴 EL MOTIVO VA ACÁ Y SÓLO ACÁ — en el aviso operativo, nunca en el correo
  // del paciente. "Vengo por ortodoncia" es un DATO DE SALUD: el paciente ya
  // sabe a qué viene, y cada correo que se lo repite lo saca del sistema hacia
  // un buzón que no controlamos. El término es INFORMATION DISCLOSURE
  // (divulgación de información). Cecilia y el profesional sí lo necesitan:
  // les dice, antes de que la persona entre, si en esa consulta pueden
  // ofrecerle ese tratamiento sin que resulte invasivo.
  //
  // Y sólo cuando DIFIERE de lo que se agenda: al que pidió una limpieza y se
  // agendó una limpieza, repetírselo es ruido.
  const motivoAnotado: string[] = []

  if ( datos.motivoConsulta && datos.motivoConsulta !== datos.tratamiento ) {
    motivoAnotado.push( `  Vino por: ${ datos.motivoConsulta }` )
  }

  const renglones = [
    titular,
    '',
    `  Paciente: ${ datos.pacienteNombre } ${ datos.pacienteApellido }`,
    `  Contacto: ${ datos.pacienteCorreo }`,
    ...fichaDelTurno( datos, motivo ),
    // La duración va SOLO acá: es lo que el consultorio necesita para armar la
    // agenda, y no viaja al correo del paciente.
    `  Duración: ${ datos.duracionMin } minutos`,
    ...motivoAnotado,
    `  Turno número: ${ datos.turnoId }`,
  ]

  if ( motivo === 'cancelacion' ) {
    renglones.push(
      '',
      'El horario vuelve a estar disponible en la grilla.',
    )
  }

  // Se avisa QUE HAY una observación y no CUÁL es. El motivo está arriba de
  // todo, en el encabezado del archivo.
  //
  // Va sólo en la reserva: una vez cancelado el turno, recordar que había una
  // observación no le sirve a nadie para nada.
  if ( motivo === 'reserva' && datos.tieneObservaciones ) {
    renglones.push(
      '',
      'El paciente dejó una observación. Se lee en la ficha del turno.',
    )
  }

  renglones.push( '', FIRMA )

  return {
    from: remitente,
    to: [ destino ],
    subject: `${ encabezadoDelAsunto } — ${ cuandoElDia( datos.inicio ) }`,
    text: renglones.join( '\n' ),
  }
}

// Los tres mensajes, ya con los destinatarios definitivos.
//
// Acá pasan las dos cosas que decidimos el 24-ago-2026, y las dos valen para
// los DOS motivos, que es justamente por qué esta función no se duplicó:
//
//   1. SI ESTÁ CARGADO `CORREO_DE_PRUEBA`, TODO VA A ESA CASILLA. Es la única
//      forma de probar tres destinatarios mientras el proveedor sólo entregue a
//      la casilla dueña de la cuenta. Se llama REDIRECCIÓN DE DESTINATARIOS
//      (recipient override) y el destinatario real queda escrito adelante del
//      asunto, para poder distinguir los tres.
//      🔴 SE BORRA EL DÍA QUE EL DOMINIO QUEDE VERIFICADO. Si queda puesto en
//      producción, nadie recibe nada y NO FALLA CON ERROR.
//
//   2. SI EL PROFESIONAL Y EL CONSULTORIO COMPARTEN CASILLA —hoy es el caso,
//      Cecilia es los dos— se manda UNO SOLO. Dos correos idénticos a la misma
//      persona no informan el doble.
function armarMensajes( datos: DatosDelAviso, motivo: MotivoDelAviso ): Mensaje[] {

  const remitente = delEntorno( 'CORREO_REMITENTE' ) ?? REMITENTE_DE_PRUEBA
  const consultorio = delEntorno( 'CORREO_DEL_CONSULTORIO' )
  const casillaDePrueba = delEntorno( 'CORREO_DE_PRUEBA' )

  const mensajes: Mensaje[] = [
    correoParaElPaciente( datos, remitente, motivo ),
    avisoOperativo( datos, remitente, datos.profesionalCorreo, motivo ),
  ]

  // El consultorio puede no estar cargado todavía: es un aviso menos, no un
  // motivo para no mandar los otros dos.
  if ( !consultorio ) {
    console.error( 'avisos: falta CORREO_DEL_CONSULTORIO, va sin ese aviso' )
  }
  else if ( consultorio.toLowerCase() !== datos.profesionalCorreo.toLowerCase() ) {
    mensajes.push( avisoOperativo( datos, remitente, consultorio, motivo ) )
  }

  if ( !casillaDePrueba ) {
    return mensajes
  }

  return mensajes.map(
    ( mensaje ) => ( {
      ...mensaje,
      to: [ casillaDePrueba ],
      subject: `[para: ${ mensaje.to[ 0 ] }] ${ mensaje.subject }`,
    } ),
  )
}

// Manda los avisos. Devuelve si salieron o no, y NUNCA lanza.
//
// Lo que se escribe en el registro cuando falla es el motivo y nada más: ni el
// cuerpo de los mensajes, ni la clave, ni los correos de nadie. Un registro lo
// lee cualquiera que tenga acceso al panel.
export async function enviarAvisos(
  datos: DatosDelAviso,
  motivo: MotivoDelAviso,
): Promise< boolean > {

  const clave = delEntorno( 'RESEND_API_KEY' )

  if ( !clave ) {
    console.error( 'avisos: no hay RESEND_API_KEY cargada' )
    return false
  }

  const mensajes = armarMensajes( datos, motivo )

  try {

    const respuesta = await fetch(
      RESEND_LOTE,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${ clave }`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify( mensajes ),
      },
    )

    if ( !respuesta.ok ) {

      // El MOTIVO lo escribe el proveedor y viene en su respuesta. Sin él, un
      // fallo dice "no salió" y no dice por qué, que es la mitad inútil de un
      // registro.
      //
      // ⚠ Lo que se registra es la respuesta DE ELLOS, nunca los mensajes
      // nuestros: ahí no hay datos de ningún paciente, hay un texto de error.
      const motivoDelFallo = await respuesta.text()

      console.error(
        `avisos: el proveedor contestó ${ respuesta.status } — ${ motivoDelFallo }`,
      )

      return false
    }

    return true
  }
  catch {
    // Acá se cae la red, no el proveedor: el pedido nunca llegó a destino.
    console.error( 'avisos: no se pudo hablar con el proveedor' )
    return false
  }
}
