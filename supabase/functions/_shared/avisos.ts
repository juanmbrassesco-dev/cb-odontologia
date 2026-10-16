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
const REMITENTE_DE_PRUEBA = 'CB Odontología y Estética <onboarding@resend.dev>'

const FIRMA = 'CB Odontología y Estética — Santa Fe'

// Dónde queda el consultorio. Va clavada y no en el entorno a propósito: es el
// mismo dato que el sitio publica en su sección de contacto, no una
// configuración — y un secreto que falta hace desaparecer el renglón sin fallar
// con error, que es la trampa que este archivo ya tiene documentada dos veces.
const DIRECCION = '25 de Mayo 3725 — Santa Fe'


// El pie del correo del PACIENTE: dónde queda el consultorio y por dónde
// escribirnos.
//
// 🔴 NO VA EN EL AVISO OPERATIVO, por el mismo motivo por el que ahí tampoco va
// el cierre: ese correo lo recibe quien trabaja acá. Decirle a Cecilia dónde
// queda su consultorio es ruido.
function pieDeContactoDelPaciente(): string[] {

  const renglones = [ DIRECCION ]

  const whatsapp = delEntorno( 'WHATSAPP_DEL_CONSULTORIO' )

  if ( whatsapp ) {
    renglones.push( `WhatsApp: ${ whatsapp }` )
  }

  return renglones
}

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

// ── CÓMO SE DESCRIBE UN CORREO, UNA SOLA VEZ ────────────────────────────────
//
// 🔴 POR QUÉ UNA ESTRUCTURA Y NO TEXTO ARMADO. Hasta el 16-oct-2026 cada correo
// se armaba como una lista de renglones que terminaba en `.join( '\n' )`: el
// contenido y su FORMA salían pegados, así que el día que hubo que mandar los
// mismos avisos con diseño no había dónde entrar. Las dos salidas obvias eran
// malas: adivinar la estructura leyendo el texto —clasificar por la forma, o sea
// adivinar con cara de saber— o escribir una segunda versión en paralelo, que
// duplica el contenido y **olvidarse de tocar una de las dos NO FALLA CON
// ERROR**, que es el modo de falla contra el que está escrito este archivo.
//
// Así que cada correo se describe UNA vez y dos funciones lo convierten:
// `aTexto( … )` y `aHtml( … )`. Mismo criterio con el que la grilla de horarios
// se mudó a `_shared/grilla.ts`: el cálculo se comparte, la presentación no.
//
// UN BLOQUE ES UN PEDAZO DEL CORREO QUE SABE QUÉ CLASE DE PEDAZO ES. Eso es lo
// que permite que el que dibuja no tenga que deducirlo: una ficha se dibuja como
// tabla, un párrafo como párrafo, y una acción como botón.

type RenglonDeFicha = {
  etiqueta: string
  valor: string
}

type Bloque =
  | {
      tipo: 'parrafo'
      // Puede traer saltos de línea adentro: el texto plano los respeta y el
      // HTML los cambia por un espacio, porque ahí envuelve el que lee.
      texto: string
    }
  | {
      tipo: 'ficha'
      renglones: RenglonDeFicha[]
    }
  | {
      tipo: 'accion'
      // Lo que se dice antes de la dirección, la dirección, y lo que se aclara
      // después. En texto van en tres renglones; en HTML, el del medio es un
      // botón.
      antes: string
      url: string
      despues: string
      // Lo que dice el botón. El texto plano NO lo usa —ahí la dirección se lee
      // entera— así que es el único campo de esta estructura que existe para una
      // sola de las dos salidas.
      rotulo: string
    }

type CuerpoDelCorreo = {
  // El operativo no saluda a nadie: lo recibe quien trabaja acá.
  saludo?: string
  titular: string
  bloques: Bloque[]
  pie: string
  // Dónde queda el consultorio, y va SÓLO en el correo del paciente: el correo
  // operativo lo lee quien trabaja ahí.
  //
  // 🔑 POR QUÉ SE AGREGÓ (16-oct-2026, decisión de Juan): el correo del turno es
  // lo que la paciente abre el día que viene, y hasta hoy no decía adónde ir —
  // había que buscarlo en el sitio.
  pieDeContacto?: string[]
}


// El correo escrito como texto plano.
//
// 🔴 ESTA FUNCIÓN TIENE UN CONTRATO MEDIBLE: produce EXACTAMENTE lo que producía
// el armado viejo, carácter por carácter. Así se verificó el refactor del
// 16-oct-2026 —`tools/armar-prueba-correos.ts` escribió los nueve textos antes,
// y después el `diff` tenía que venir vacío— y así se verifica cualquier cambio
// de acá en adelante.
//
// 🔑 LA REGLA QUE SOSTIENE TODO EL FORMATO ES UNA SOLA: entre dos bloques va una
// línea vacía. No hay casos especiales, y por eso los nueve correos salen
// iguales a los de antes sin que ninguno traiga su propia excepción.
function aTexto( cuerpo: CuerpoDelCorreo ): string {

  const renglones: string[] = []

  if ( cuerpo.saludo ) {
    renglones.push( cuerpo.saludo, '' )
  }

  renglones.push( cuerpo.titular )

  for ( const bloque of cuerpo.bloques ) {

    renglones.push( '' )

    if ( bloque.tipo === 'parrafo' ) {
      renglones.push( bloque.texto )
    }

    if ( bloque.tipo === 'ficha' ) {
      for ( const renglon of bloque.renglones ) {
        renglones.push( `  ${ renglon.etiqueta }: ${ renglon.valor }` )
      }
    }

    if ( bloque.tipo === 'accion' ) {
      renglones.push(
        bloque.antes,
        `  ${ bloque.url }`,
        bloque.despues,
      )
    }
  }

  renglones.push( '', cuerpo.pie )

  if ( cuerpo.pieDeContacto ) {
    renglones.push( '', ...cuerpo.pieDeContacto )
  }

  return renglones.join( '\n' )
}


// ── EL MISMO CORREO, CON LA MARCA PUESTA ────────────────────────────────────
//
// 🔴 UN CORREO NO ES UNA PÁGINA, y por eso casi nada del CSS del sitio sirve
// acá. Las tres reglas que lo gobiernan, y ninguna es opinión:
//
//   · El maquetado va con TABLAS y los estilos ADENTRO de cada etiqueta. No hay
//     hoja de estilos aparte ni `flex` ni `grid`: Outlook dibuja los correos con
//     el motor de Word, que no entiende nada de eso.
//   · LAS IMÁGENES VIENEN BLOQUEADAS por defecto en Gmail, así que el banner
//     tiene que leerse con el logo apagado. El color lo pinta la CELDA, nunca la
//     imagen, y el `alt` dice el nombre completo.
//     🔴 Y EL `alt` LLEVA SUS PROPIOS ESTILOS EN LA `<img>`, que es lo que casi
//     nadie hace: el texto alternativo HEREDA el color de la imagen, no el de la
//     celda, así que sin esto salía en el gris de la página sobre el banner
//     oscuro y no se leía. *Se vio en la primera captura, 16-oct-2026.*
//   · El fondo del banner es OSCURO a propósito. El modo oscuro de Gmail da
//     vuelta los fondos claros, y un banner blanco con el logo en grafito puede
//     terminar oscuro sobre oscuro; un fondo que ya es oscuro no se invierte.
//
// ⚠ LAS TIPOGRAFÍAS DE LA MARCA NO VIAJAN. Un correo no puede cargar una fuente
// propia con ninguna garantía, así que acá va una pila del sistema. Es la única
// parte de la identidad que se resigna, y se resigna porque la alternativa
// —imágenes con el texto adentro— no se puede leer ni buscar ni agrandar.

const LOGO_DEL_CORREO =
  'https://cbodontologiayestetica.com.ar/brand/logo/png/cb-apilado-1200-blanco.png'

// Los colores salen de `css/tokens.css` y se repiten acá porque un correo no
// puede leer ese archivo. Si allá cambian, acá se cambian a mano: no hay nada
// que avise.
const MARFIL = '#FAF7F2'
const BLANCO = '#FFFFFF'
const GRAFITO = '#33322F'
const GRAFITO_SUAVE = '#5A5853'
const DORADO = '#B08D57'
const DORADO_TEXTO = '#896D41'

const LETRA = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"


// 🔒 ESCAPAR NO ES PROLIJIDAD: ES LA DEFENSA, y el correo de texto no la
// necesitaba.
//
// Hay datos acá que los escribe el PACIENTE —su nombre y el motivo de consulta—
// y terminan dentro del correo que lee Cecilia. En texto plano un `<` es un `<`;
// adentro de HTML abre una etiqueta. Sin esta función, alguien que se anote como
// `<b>` deforma el correo, y con un poco más de trabajo puede meter un enlace
// que no pusimos nosotros en un mensaje que SÍ viene de nuestro dominio.
//
// El nombre del agujero es INYECCIÓN DE HTML (HTML injection); cuando lo que se
// cuela llega a ejecutarse, se llama CROSS-SITE SCRIPTING (XSS). Un cliente de
// correo no corre JavaScript, así que acá el riesgo es el del medio: contenido
// puesto por un tercero que se lee como nuestro.
//
// 🔑 SE ESCAPA AL DIBUJAR, NO AL GUARDAR. El dato se guarda como lo escribió la
// persona y cada salida lo prepara para SU destino: el texto plano no toca nada,
// el HTML escapa cinco caracteres. Al revés —guardar ya escapado— el nombre
// queda con `&amp;` para siempre, también en la pantalla y en la base.
function escaparHtml( texto: string ): string {

  return texto
    .replaceAll( '&', '&amp;' )
    .replaceAll( '<', '&lt;' )
    .replaceAll( '>', '&gt;' )
    .replaceAll( '"', '&quot;' )
    .replaceAll( "'", '&#39;' )
}


// Un párrafo del correo. El salto de línea que el texto plano respeta se cambia
// por un espacio: acá el que envuelve es el que lee.
function parrafoHtml( texto: string ): string {

  const limpio = escaparHtml( texto ).replaceAll( '\n', ' ' )

  return `<p style="margin:0 0 16px;font:16px/1.6 ${ LETRA };color:${ GRAFITO }">${ limpio }</p>`
}


// La ficha, como tabla de dos columnas: la etiqueta chica y en dorado, el valor
// grande y en grafito. En texto plano esto son renglones indentados con dos
// espacios, y ésa es toda la diferencia.
function fichaHtml( renglones: RenglonDeFicha[] ): string {

  const filas = renglones.map(
    ( renglon ) => `
      <tr>
        <td style="padding:5px 14px 5px 0;vertical-align:top;white-space:nowrap;font:13px/1.5 ${ LETRA };color:${ DORADO_TEXTO }">${ escaparHtml( renglon.etiqueta ) }</td>
        <td style="padding:5px 0;vertical-align:top;font:16px/1.5 ${ LETRA };color:${ GRAFITO }">${ escaparHtml( renglon.valor ) }</td>
      </tr>`,
  )

  return `<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="width:100%;border-collapse:collapse;margin:0 0 20px">
    <tbody>${ filas.join( '' ) }
    </tbody>
  </table>`
}


// La acción, como botón de verdad.
//
// ⚠ ES UN `<a>` CON FONDO, NO UN `<button>`: un botón de formulario no hace nada
// en un correo. Y el fondo se pinta DOS veces —en el atributo `bgcolor` de la
// celda y en su `style`— porque los clientes viejos leen uno y los nuevos el
// otro.
function accionHtml( antes: string, url: string, despues: string, rotulo: string ): string {

  return `${ parrafoHtml( antes ) }
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 16px">
    <tbody>
      <tr>
        <td bgcolor="${ DORADO }" style="background:${ DORADO };border-radius:4px">
          <a href="${ escaparHtml( url ) }" style="display:inline-block;padding:14px 28px;font:600 16px/1 ${ LETRA };color:${ BLANCO };text-decoration:none">${ escaparHtml( rotulo ) }</a>
        </td>
      </tr>
    </tbody>
  </table>
  <p style="margin:0 0 16px;font:14px/1.6 ${ LETRA };color:${ GRAFITO_SUAVE }">${ escaparHtml( despues ) }</p>`
}


function aHtml( cuerpo: CuerpoDelCorreo ): string {

  const partes: string[] = []

  if ( cuerpo.saludo ) {
    partes.push( parrafoHtml( cuerpo.saludo ) )
  }

  partes.push(
    `<p style="margin:0 0 20px;font:600 20px/1.4 ${ LETRA };color:${ GRAFITO }">${ escaparHtml( cuerpo.titular ) }</p>`,
  )

  for ( const bloque of cuerpo.bloques ) {

    if ( bloque.tipo === 'parrafo' ) {
      partes.push( parrafoHtml( bloque.texto ) )
    }

    if ( bloque.tipo === 'ficha' ) {
      partes.push( fichaHtml( bloque.renglones ) )
    }

    if ( bloque.tipo === 'accion' ) {
      partes.push(
        accionHtml( bloque.antes, bloque.url, bloque.despues, bloque.rotulo ),
      )
    }
  }

  // La firma, y debajo el pie postal separado por una línea dorada. El pie puede
  // no estar: el correo operativo no lo lleva.
  partes.push(
    `<p style="margin:24px 0 0;font:14px/1.6 ${ LETRA };color:${ GRAFITO_SUAVE }">${ escaparHtml( cuerpo.pie ) }</p>`,
  )

  if ( cuerpo.pieDeContacto ) {
    partes.push(
      `<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="width:100%;border-collapse:collapse;margin:20px 0 0">
        <tbody>
          <tr>
            <td style="border-top:1px solid ${ DORADO };padding:16px 0 0;font:13px/1.7 ${ LETRA };color:${ GRAFITO_SUAVE }">${ cuerpo.pieDeContacto.map( escaparHtml ).join( '<br>' ) }</td>
          </tr>
        </tbody>
      </table>`,
    )
  }

  // El sobre: una tabla que pinta el fondo de la pantalla y, adentro, la tarjeta
  // de 600 px, que es el ancho con el que se maqueta un correo desde siempre.
  //
  // 🔴 LOS 600 SON UN TECHO, NO UN ANCHO, y la diferencia se vio midiendo: con
  // `width="600"` el correo NO se achica en un teléfono y se sale de la pantalla
  // —medido a 390 px el 16-oct-2026, con el banner cortado del lado derecho—.
  // Va `width:100%` con `max-width:600px`: ocupa lo que haya y nunca pasa de 600.
  //
  // ⚠ COSTO ACEPTADO: el Outlook de escritorio ignora `max-width`, así que ahí
  // el correo se estira a lo ancho de la ventana. Se arregla con un bloque
  // condicional sólo para él; no se puso porque acá nadie lo usa. *Disparador
  // para agregarlo: que aparezca una paciente leyendo con Outlook y moleste.*
  return `<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width">
<title>${ escaparHtml( cuerpo.titular ) }</title>
</head>
<body style="margin:0;padding:0;background:${ MARFIL }">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:${ MARFIL }">
  <tbody>
    <tr>
      <td align="center" style="padding:24px 12px">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;background:${ BLANCO }">
          <tbody>
            <tr>
              <td align="center" bgcolor="${ GRAFITO }" style="background:${ GRAFITO };padding:30px 24px">
                <img src="${ LOGO_DEL_CORREO }" width="240" alt="CB Odontología y Estética" style="display:block;width:240px;max-width:100%;height:auto;border:0;font:600 18px/1.4 ${ LETRA };color:${ MARFIL }">
              </td>
            </tr>
            <tr>
              <td style="padding:32px 24px">
${ partes.join( '\n' ) }
              </td>
            </tr>
          </tbody>
        </table>
      </td>
    </tr>
  </tbody>
</table>
</body>
</html>`
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
function cierreDelCorreo( motivo: MotivoDelAviso ): Bloque[] {

  const pantalla = delEntorno( 'URL_MIS_TURNOS' )
  const whatsapp = delEntorno( 'WHATSAPP_DEL_CONSULTORIO' )
  const correo = delEntorno( 'CORREO_DEL_CONSULTORIO' )

  const bloques: Bloque[] = []

  // Cómo cancelar solo. Sólo si el turno sigue vivo —a un turno cancelado no se
  // lo cancela de nuevo— y sólo si la pantalla existe.
  if ( motivo === 'reserva' && pantalla ) {
    bloques.push( {
      tipo: 'accion',
      antes: 'Si no vas a poder venir, podés cancelarlo vos desde:',
      url: pantalla,
      despues: 'Entrá con el mismo correo con el que reservaste.',
      rotulo: 'Ver mis turnos',
    } )
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
    return bloques
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

  // La apertura y la vía son UN párrafo partido en dos renglones, no dos
  // párrafos: en el correo con diseño van seguidos, envolviendo donde la
  // pantalla lo pida.
  bloques.push( {
    tipo: 'parrafo',
    texto: `${ apertura }\n${ via }`,
  } )

  return bloques
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
  // Bajo qué cobertura se sacó el turno. Es el dato que el consultorio necesita
  // ANTES de atender, y por eso viaja en el correo y no sólo en la base: si
  // Cecilia tuviera que ir a buscarlo a una pantalla, el campo no estaría
  // cumpliendo para lo que se creó.
  //
  // Opcional porque la CANCELACIÓN no lo manda: ahí lo que importa es el hueco
  // que se libera, no bajo qué cobertura estaba tomado.
  //
  // ⚠ Y NO es opcional porque el dato pueda faltar en la base: `obra_social_id`
  // es `not null` desde la migración 20260918163840. Lo opcional es que quien
  // arma el aviso lo mande, no que exista.
  obraSocial?: string | null
  pacienteNombre: string
  pacienteApellido: string
  pacienteCorreo: string
  profesionalNombre: string
  profesionalApellido: string
  profesionalCorreo: string
  tieneObservaciones: boolean
}

// Un mensaje ya listo para el proveedor.
//
// ⚠ EL TEXTO NO ES OPCIONAL Y EL HTML SÍ, y el orden de los dos campos no es
// casualidad. Un correo se manda con las DOS versiones adentro (se llama
// MULTIPART) y el que lo recibe elige: el texto es el respaldo de todo lo que no
// pueda con el diseño, y un correo que viaja sin él puntúa peor en los filtros
// de spam. Así que el HTML se SUMA al texto, nunca lo reemplaza.
type Mensaje = {
  from: string
  to: string[]
  subject: string
  text: string
  html?: string
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
function fichaDelTurno( datos: DatosDelAviso, motivo: MotivoDelAviso ): RenglonDeFicha[] {

  let cuando = 'Cuándo'

  if ( motivo === 'cancelacion' ) {
    cuando = 'Cuándo era'
  }

  const renglones: RenglonDeFicha[] = [
    {
      etiqueta: 'Tratamiento',
      valor: datos.tratamiento,
    },
    {
      etiqueta: 'Profesional',
      valor: `${ datos.profesionalNombre } ${ datos.profesionalApellido }`,
    },
    {
      etiqueta: cuando,
      valor: cuandoEnPalabras( datos.inicio ),
    },
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
    renglones.push( {
      etiqueta: 'Antes era',
      valor: cuandoEnPalabras( horaAvisada ),
    } )
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

    const cuerpo: CuerpoDelCorreo = {
      saludo: `Hola ${ datos.pacienteNombre },`,
      titular: 'Tu turno quedó cancelado.',
      bloques: [
        {
          tipo: 'ficha',
          renglones: ficha,
        },
        {
          tipo: 'parrafo',
          texto: 'El horario vuelve a estar disponible para quien lo necesite. Si querés\nsacar otro turno, entrá al sitio cuando quieras.',
        },
        ...cierreDelCorreo( motivo ),
      ],
      pie: FIRMA,
      pieDeContacto: pieDeContactoDelPaciente(),
    }

    return {
      from: remitente,
      to: [ datos.pacienteCorreo ],
      subject: 'Tu turno quedó cancelado — CB Odontología y Estética',
      text: aTexto( cuerpo ),
      html: aHtml( cuerpo ),
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
  // 🔴 EL NOMBRE VA COMPLETO Y VA AL FINAL, y las dos mitades tienen motivo.
  //
  // COMPLETO porque «CB Odontología» a secas es el nombre de OTRO consultorio
  // —el de la Dra. Constanza Brión, en Buenos Aires, funcionando desde 2024—
  // y el sufijo «y Estética» es lo único que nos distingue de él. Hasta el
  // 1-sep-2026 los cuatro asuntos y el remitente lo decían cortado.
  //
  // AL FINAL porque en el teléfono el asunto se corta cerca de los 35
  // caracteres, y lo primero que tiene que leerse es QUÉ PASÓ. Con el nombre
  // adelante, «Tu turno en CB Odontología y Esté…» pierde justo la palabra que
  // distingue un aviso de otro, que es lo que el bloque de arriba explica que
  // no se puede perder. Quién manda el correo ya lo dice el remitente.
  let titular = 'Tu turno quedó agendado.'
  let asunto = 'Tu turno quedó agendado — CB Odontología y Estética'

  // Lo que se agrega debajo de la ficha, o nada. Empieza vacío porque el correo
  // de un turno nuevo no aclara nada: no hay nada anterior.
  const aclaracion: Bloque[] = []

  if ( queEsEsteAviso( datos ) === 'hora-nueva' ) {

    titular = 'El horario de tu turno cambió.'
    asunto = 'Cambió el horario de tu turno — CB Odontología y Estética'

    aclaracion.push( {
      tipo: 'parrafo',
      texto: 'El horario anterior ya no está reservado.',
    } )
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
    asunto = 'Cambió tu turno — CB Odontología y Estética'
  }

  const cuerpo: CuerpoDelCorreo = {
    saludo: `Hola ${ datos.pacienteNombre },`,
    titular: titular,
    bloques: [
      {
        tipo: 'ficha',
        renglones: ficha,
      },
      ...aclaracion,
      ...cierreDelCorreo( motivo ),
    ],
    pie: FIRMA,
    pieDeContacto: pieDeContactoDelPaciente(),
  }

  return {
    from: remitente,
    to: [ datos.pacienteCorreo ],
    subject: asunto,
    text: aTexto( cuerpo ),
    html: aHtml( cuerpo ),
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
  const motivoAnotado: RenglonDeFicha[] = []

  if ( datos.motivoConsulta && datos.motivoConsulta !== datos.tratamiento ) {
    motivoAnotado.push( {
      etiqueta: 'Vino por',
      valor: datos.motivoConsulta,
    } )
  }

  // 🔴 LA COBERTURA VA ACÁ POR EL MISMO MOTIVO QUE EL RENGLÓN DE ARRIBA, y hay
  // un argumento propio que lo hace todavía más claro: en la lista del
  // consultorio hay filas como `IAPOS CAPACIDADES DIFERENTES` e `IAPOS
  // EMBARAZADAS`. El nombre de la cobertura puede DECIR UNA CONDICIÓN DE SALUD,
  // así que es INFORMATION DISCLOSURE (divulgación de información) mandarlo a
  // un buzón que se reenvía, incluso al del propio paciente — que además ya
  // sabe con qué reservó.
  //
  // Cecilia y el profesional sí lo necesitan, y antes del turno: es el dato con
  // el que saben bajo qué concepto viene la persona. El paciente lo ve en su
  // pantalla, con la sesión iniciada, que es otro canal.
  //
  // El `if` no es cosmético, y lo que lo justifica cambió: la cobertura es
  // obligatoria en la base desde el 18-sep-2026, así que ningún turno la tiene
  // vacía. Lo que sí falta es el dato en la MANO de quien arma el aviso — la
  // cancelación no lo manda a propósito—, y un renglón que dijera
  // «Cobertura: null» sería peor que no estar.
  const coberturaAnotada: RenglonDeFicha[] = []

  if ( datos.obraSocial ) {
    coberturaAnotada.push( {
      etiqueta: 'Cobertura',
      valor: datos.obraSocial,
    } )
  }

  // La ficha del operativo es UNA sola lista con la del paciente en el medio:
  // el paciente y su contacto van arriba, y lo que sólo le sirve al consultorio
  // —duración, motivo, cobertura y número— abajo.
  const ficha: RenglonDeFicha[] = [
    {
      etiqueta: 'Paciente',
      valor: `${ datos.pacienteNombre } ${ datos.pacienteApellido }`,
    },
    {
      etiqueta: 'Contacto',
      valor: datos.pacienteCorreo,
    },
    ...fichaDelTurno( datos, motivo ),
    // La duración va SOLO acá: es lo que el consultorio necesita para armar la
    // agenda, y no viaja al correo del paciente.
    {
      etiqueta: 'Duración',
      valor: `${ datos.duracionMin } minutos`,
    },
    ...motivoAnotado,
    ...coberturaAnotada,
    {
      etiqueta: 'Turno número',
      valor: String( datos.turnoId ),
    },
  ]

  const bloques: Bloque[] = [
    {
      tipo: 'ficha',
      renglones: ficha,
    },
  ]

  if ( motivo === 'cancelacion' ) {
    bloques.push( {
      tipo: 'parrafo',
      texto: 'El horario vuelve a estar disponible en la grilla.',
    } )
  }

  // Se avisa QUE HAY una observación y no CUÁL es. El motivo está arriba de
  // todo, en el encabezado del archivo.
  //
  // Va sólo en la reserva: una vez cancelado el turno, recordar que había una
  // observación no le sirve a nadie para nada.
  if ( motivo === 'reserva' && datos.tieneObservaciones ) {
    bloques.push( {
      tipo: 'parrafo',
      texto: 'El paciente dejó una observación. Se lee en la ficha del turno.',
    } )
  }

  const cuerpo: CuerpoDelCorreo = {
    titular: titular,
    bloques: bloques,
    pie: FIRMA,
  }

  return {
    from: remitente,
    to: [ destino ],
    subject: `${ encabezadoDelAsunto } — ${ cuandoElDia( datos.inicio ) }`,
    text: aTexto( cuerpo ),
    html: aHtml( cuerpo ),
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
// 🔧 ESTÁ EXPORTADA PARA EL INSTRUMENTO, no porque algún endpoint la use.
// `tools/armar-prueba-correos.ts` arma las nueve variantes de correo y las
// escribe a un archivo para poder mirarlas sin reservar un turno. Importa ESTA
// función en vez de rearmar los mensajes por su cuenta: un instrumento que
// reimplementa lo que mide, miente.
export function armarMensajes( datos: DatosDelAviso, motivo: MotivoDelAviso ): Mensaje[] {

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
