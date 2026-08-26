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

// La ficha del turno: los cuatro renglones que van igual en los dos correos del
// paciente. Lo único que cambia es el tiempo del verbo — 'Cuándo' mientras el
// turno va a pasar, 'Cuándo era' cuando ya no va a pasar.
function fichaDelTurno( datos: DatosDelAviso, motivo: MotivoDelAviso ): string[] {

  let cuando = 'Cuándo'

  if ( motivo === 'cancelacion' ) {
    cuando = 'Cuándo era'
  }

  return [
    `  Tratamiento: ${ datos.tratamiento }`,
    `  Profesional: ${ datos.profesionalNombre } ${ datos.profesionalApellido }`,
    `  ${ cuando }: ${ cuandoEnPalabras( datos.inicio ) }`,
    `  Duración: ${ datos.duracionMin } minutos`,
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
      subject: 'Tu turno en CB Odontología quedó cancelado',
      text: texto,
    }
  }

  const texto = [
    `Hola ${ datos.pacienteNombre },`,
    '',
    'Tu turno quedó reservado.',
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
    subject: 'Tu turno en CB Odontología quedó reservado',
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

  const renglones = [
    titular,
    '',
    `  Paciente: ${ datos.pacienteNombre } ${ datos.pacienteApellido }`,
    `  Contacto: ${ datos.pacienteCorreo }`,
    ...fichaDelTurno( datos, motivo ),
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
