// Portero de CB Odontología — los avisos por correo de una reserva
//
// UN SOLO DISPARO, TRES DESTINATARIOS: el paciente (confirmación), el
// consultorio y el profesional al que le reservaron (aviso operativo). Van en
// un ÚNICO pedido al proveedor —un "lote"— y aun así cada uno recibe su propio
// texto: el paciente lee "tu turno quedó reservado", los otros dos leen "entró
// un turno".
//
// 🔴 ESTE MÓDULO NO PUEDE HACER FALLAR UNA RESERVA. Si el proveedor está caído,
// si la clave venció o si falta un dato, devuelve `false` y se acabó. El turno
// ya está anotado en la base y un correo caído no puede desanotarlo. Por eso
// NINGUNA función de acá lanza un error: todas devuelven algo.
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

// Todo lo que hace falta para escribir los tres correos. Se arma en
// `reservar/index.ts`, que es el único que tuvo todos estos datos a mano.
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

function correoParaElPaciente( datos: DatosDelAviso, remitente: string ): Mensaje {

  const texto = [
    `Hola ${ datos.pacienteNombre },`,
    '',
    'Tu turno quedó reservado.',
    '',
    `  Tratamiento: ${ datos.tratamiento }`,
    `  Profesional: ${ datos.profesionalNombre } ${ datos.profesionalApellido }`,
    `  Cuándo: ${ cuandoEnPalabras( datos.inicio ) }`,
    `  Duración: ${ datos.duracionMin } minutos`,
    '',
    'Si no vas a poder venir, escribinos y lo cancelamos.',
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
): Mensaje {

  const renglones = [
    'Entró un turno nuevo por la web.',
    '',
    `  Paciente: ${ datos.pacienteNombre } ${ datos.pacienteApellido }`,
    `  Contacto: ${ datos.pacienteCorreo }`,
    `  Tratamiento: ${ datos.tratamiento }`,
    `  Profesional: ${ datos.profesionalNombre } ${ datos.profesionalApellido }`,
    `  Cuándo: ${ cuandoEnPalabras( datos.inicio ) }`,
    `  Duración: ${ datos.duracionMin } minutos`,
    `  Turno número: ${ datos.turnoId }`,
  ]

  // Se avisa QUE HAY una observación y no CUÁL es. El motivo está arriba de
  // todo, en el encabezado del archivo.
  if ( datos.tieneObservaciones ) {
    renglones.push(
      '',
      'El paciente dejó una observación. Se lee en la ficha del turno.',
    )
  }

  renglones.push( '', FIRMA )

  return {
    from: remitente,
    to: [ destino ],
    subject: `Nuevo turno — ${ cuandoCompacto( datos.inicio ) } — ${ datos.pacienteApellido }`,
    text: renglones.join( '\n' ),
  }
}

// Los tres mensajes, ya con los destinatarios definitivos.
//
// Acá pasan las dos cosas que decidimos el 24-ago-2026:
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
function armarMensajes( datos: DatosDelAviso ): Mensaje[] {

  const remitente = delEntorno( 'CORREO_REMITENTE' ) ?? REMITENTE_DE_PRUEBA
  const consultorio = delEntorno( 'CORREO_DEL_CONSULTORIO' )
  const casillaDePrueba = delEntorno( 'CORREO_DE_PRUEBA' )

  const mensajes: Mensaje[] = [
    correoParaElPaciente( datos, remitente ),
    avisoOperativo( datos, remitente, datos.profesionalCorreo ),
  ]

  // El consultorio puede no estar cargado todavía: es un aviso menos, no un
  // motivo para no mandar los otros dos.
  if ( !consultorio ) {
    console.error( 'avisos: falta CORREO_DEL_CONSULTORIO, va sin ese aviso' )
  }
  else if ( consultorio.toLowerCase() !== datos.profesionalCorreo.toLowerCase() ) {
    mensajes.push( avisoOperativo( datos, remitente, consultorio ) )
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
export async function enviarAvisos( datos: DatosDelAviso ): Promise< boolean > {

  const clave = delEntorno( 'RESEND_API_KEY' )

  if ( !clave ) {
    console.error( 'avisos: no hay RESEND_API_KEY cargada' )
    return false
  }

  const mensajes = armarMensajes( datos )

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
      const motivo = await respuesta.text()

      console.error(
        `avisos: el proveedor contestó ${ respuesta.status } — ${ motivo }`,
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
