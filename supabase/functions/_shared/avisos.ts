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

// Cómo se le dice al paciente dónde ve y cancela sus turnos.
//
// 🔴 LA DIRECCIÓN NO ESTÁ CLAVADA EN EL CÓDIGO Y NO LLEVA NINGÚN TOKEN.
//
//   - No está clavada porque la pantalla todavía no existe: el día que el sitio
//     se publique se carga `URL_MIS_TURNOS` como secreto y este correo la
//     nombra, sin volver a desplegar la función. Anotado en § 14 con disparador.
//   - No lleva token porque un correo se reenvía. Un link con token adentro es
//     una CREDENCIAL AL PORTADOR (bearer credential): el que lo tiene, entra.
//     Ésta es pelada: del otro lado hay que iniciar sesión igual, así que si se
//     filtra no sirve para nada. (Decisión del 25-ago-2026, § 6.)
//
// ⚠ Si el secreto no está cargado, el correo cae en la frase de siempre. No
// falla con error, que es exactamente por qué está anotado como pendiente.
function comoSeCancela(): string {

  const pantalla = delEntorno( 'URL_MIS_TURNOS' )

  if ( !pantalla ) {
    return 'Si no vas a poder venir, escribinos y lo cancelamos.'
  }

  return [
    'Si no vas a poder venir, podés cancelarlo vos desde:',
    `  ${ pantalla }`,
    'Entrá con el mismo correo con el que reservaste.',
  ].join( '\n' )
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

  return [
    `  Tratamiento: ${ datos.tratamiento }`,
    `  Profesional: ${ datos.profesionalNombre } ${ datos.profesionalApellido }`,
    `  ${ cuando }: ${ cuandoEnPalabras( datos.inicio ) }`,
  ]
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
      '',
      FIRMA,
    ].join( '\n' )

    return {
      from: remitente,
      to: [ datos.pacienteCorreo ],
      subject: `Tu turno en CB Odontología quedó cancelado — ${ cuandoCompacto( datos.inicio ) }`,
      text: texto,
    }
  }

  // 🔴 «AGENDADO», NO «RESERVADO», Y LA FECHA VA EN EL ASUNTO.
  //
  // Este mismo correo sale DOS veces por el mismo turno: cuando nace y cuando
  // le mueven la hora. Decía «quedó reservado» las dos veces, y así la paciente
  // leía dos altas en vez de un cambio — creía tener dos turnos y se presentaba
  // al viejo. Lo levantó Juan el 28-ago-2026 leyendo los correos en fila: en la
  // tabla hay UNA fila y todo parece bien.
  //
  // Lo que distingue un aviso del otro es la FECHA EN EL ASUNTO. Sin ella los
  // dos correos tienen asunto idéntico, el cliente de correo los agrupa en una
  // sola conversación y la paciente ni siquiera los ve como dos mensajes.
  //
  // Se probó también un renglón que decía «si tenías otro horario anotado, éste
  // lo reemplaza», y se sacó: es una condición que la paciente no puede
  // resolver —no sabe si tenía otro— y ocupa un renglón sin informar.
  const texto = [
    `Hola ${ datos.pacienteNombre },`,
    '',
    'Tu turno quedó agendado.',
    '',
    ...ficha,
    '',
    comoSeCancela(),
    '',
    FIRMA,
  ].join( '\n' )

  return {
    from: remitente,
    to: [ datos.pacienteCorreo ],
    subject: `Tu turno en CB Odontología quedó agendado — ${ cuandoCompacto( datos.inicio ) }`,
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

  let titular = 'Entró un turno nuevo por la web.'
  let encabezadoDelAsunto = 'Nuevo turno'

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
    subject: `${ encabezadoDelAsunto } — ${ cuandoCompacto( datos.inicio ) } — ${ datos.pacienteApellido }`,
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
