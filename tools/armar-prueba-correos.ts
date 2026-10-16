// INSTRUMENTO — las NUEVE variantes de correo, escritas a un archivo para poder
// mirarlas sin reservar un turno.
//
// PARA QUÉ EXISTE. Un correo no se juzga leyendo el código que lo arma: se
// juzga mirándolo. Y hasta hoy la única forma de ver uno era reservar un turno
// de verdad, lo que tiene dos costos: cada corrida de `probar-reservar.sh` deja
// dos o tres filas de prueba en la base real, y para comparar las nueve
// variantes habría que provocar las nueve situaciones.
//
// 🔑 IMPORTA `armarMensajes( … )` DE `avisos.ts` Y NO REARMA NADA. Es la regla
// que este proyecto ya pagó cuatro veces —el falso portero de la prueba del
// panel, el medidor de alineación, los dos tableros—: un instrumento que
// reimplementa lo que mide, MIENTE. Lo que se ve acá es exactamente lo que sale.
//
// QUÉ ESCRIBE, los dos en `pruebas/`:
//
//   correos.txt   Los nueve textos, con su asunto y su destinatario adelante.
//                 Es el lado de arriba del `diff` que prueba que un refactor no
//                 cambió ni una frase.
//   correos.html  Los nueve correos enmarcados a 600 px, que es el ancho del
//                 cuerpo de un correo, para iterar la forma sin mandar nada.
//
// CÓMO SE CORRE, parado en la raíz del repo:
//
//   deno run --allow-env --allow-write tools/armar-prueba-correos.ts
//
// ⚠ EL ENTORNO SE FABRICA ACÁ ADENTRO, con valores de mentira. No lee el `.env`
// a propósito: este archivo se versiona y no tiene por qué saber ni la
// dirección real de Cecilia ni la de nadie.

import {
  armarMensajes,
  type DatosDelAviso,
  type MotivoDelAviso,
} from '../supabase/functions/_shared/avisos.ts'


// ── El entorno de mentira ────────────────────────────────────────────────────
//
// Son los mismos cuatro datos que `avisos.ts` busca en el entorno. Si alguno
// faltara, el correo saldría igual pero sin ese renglón, que es justamente la
// trampa que el archivo tiene documentada: lo que no está cargado no se nota
// hasta que alguien lee un correo.
//
// 🔴 `CORREO_DE_PRUEBA` NO SE SETEA, Y ES A PROPÓSITO. Con ese secreto puesto,
// `armarMensajes` reescribe los tres destinatarios a una sola casilla; acá
// queremos ver a quién va cada uno de verdad.

const ENTORNO_DE_MENTIRA: Record< string, string > = {
  'CORREO_REMITENTE': 'CB Odontología y Estética <turnos@avisos.ejemplo.com.ar>',
  'CORREO_DEL_CONSULTORIO': 'contacto@ejemplo.com.ar',
  'URL_MIS_TURNOS': 'https://ejemplo.com.ar/mis-turnos',
  'WHATSAPP_DEL_CONSULTORIO': '+54 342 000-0000',
}

for ( const [ nombre, valor ] of Object.entries( ENTORNO_DE_MENTIRA ) ) {
  Deno.env.set( nombre, valor )
}


// ── El turno de mentira ──────────────────────────────────────────────────────
//
// Los datos elegidos NO son neutros, y cada uno hace aparecer un renglón que
// con datos tibios no se vería:
//
//   motivoConsulta distinto de tratamiento  → el renglón «Vino por»
//   obraSocial con una condición en el nombre → el renglón «Cobertura», que es
//                                               el caso que el código usa para
//                                               explicar por qué no viaja al
//                                               paciente
//   tieneObservaciones en true              → el aviso de que hay observación
//
// ⚠ El correo del consultorio queda IGUAL al del profesional, como en
// producción hoy: así `armarMensajes` deduplica y salen DOS mensajes, no tres.
// El tercero diría exactamente lo mismo con otro destinatario.

const TURNO: DatosDelAviso = {
  turnoId: 428,
  inicio: '2026-11-23T12:00:00+00:00',
  duracionMin: 60,
  tratamiento: 'Limpieza',
  motivoConsulta: 'Ortodoncia',
  obraSocial: 'IAPOS EMBARAZADAS',
  canal: 'web',
  pacienteNombre: 'Rafaela',
  pacienteApellido: 'Giménez',
  pacienteCorreo: 'rafaela@ejemplo.com',
  profesionalNombre: 'Cecilia',
  profesionalApellido: 'Brassesco',
  profesionalCorreo: 'contacto@ejemplo.com.ar',
  tieneObservaciones: true,
}


// ── Los cinco escenarios ─────────────────────────────────────────────────────
//
// Cinco y no nueve porque cada uno devuelve DOS mensajes —el del paciente y el
// operativo—, y las nueve variantes de contenido salen de estas cinco
// situaciones. La única repetida es el correo del paciente de los dos primeros:
// a él no le cambia nada que el turno lo haya cargado Cecilia a mano.
//
// 🔑 `inicioAvisado` ES EL DATO QUE DECIDE QUÉ CLASE DE AVISO ES, y por eso los
// escenarios se distinguen por él y no por un campo nuevo:
//
//   vacío                      → nunca se le avisó        → «quedó agendado»
//   distinto de `inicio`       → se le avisó otra hora     → «cambió el horario»
//   igual a `inicio`           → se le avisó esta hora, y
//                                algo cambió igual         → «hubo un cambio»

type Escenario = {
  nombre: string
  porQue: string
  datos: DatosDelAviso
  motivo: MotivoDelAviso
}

const ESCENARIOS: Escenario[] = [
  {
    nombre: 'A · Turno nuevo, reservado por la web',
    porQue: 'El caso más común: una paciente saca un turno sola.',
    datos: TURNO,
    motivo: 'reserva',
  },
  {
    nombre: 'B · Turno nuevo, cargado a mano en el panel',
    porQue: 'Cambia SÓLO el aviso operativo: el titular no puede decir «por la web».',
    datos: {
      ...TURNO,
      canal: 'manual',
    },
    motivo: 'reserva',
  },
  {
    nombre: 'C · Le movieron la hora',
    porQue: 'El correo tiene que dejar claro que REEMPLAZA al anterior, o la paciente cree que tiene dos turnos.',
    datos: {
      ...TURNO,
      inicioAvisado: '2026-11-23T10:30:00+00:00',
    },
    motivo: 'reserva',
  },
  {
    nombre: 'D · Le cambiaron otro dato',
    porQue: 'La hora avisada es la misma y algo cambió igual. No sabemos QUÉ, así que no se nombra.',
    datos: {
      ...TURNO,
      inicioAvisado: '2026-11-23T12:00:00+00:00',
    },
    motivo: 'reserva',
  },
  {
    nombre: 'E · Cancelado',
    porQue: 'Ni el motivo de consulta ni la cobertura viajan: lo que importa es el hueco que se libera.',
    datos: {
      ...TURNO,
      motivoConsulta: null,
      obraSocial: null,
      canal: null,
      inicioAvisado: '2026-11-23T12:00:00+00:00',
    },
    motivo: 'cancelacion',
  },
]


// ── La URL del logo, de la nube a la carpeta ─────────────────────────────────
//
// En un correo la imagen va por URL absoluta: no hay otra opción, porque el
// que lo abre no tiene nuestros archivos. Pero para ITERAR la forma, esperar un
// `git push` y unos minutos de Cloudflare por cada cambio no se sostiene, así
// que acá esa dirección se cambia por la ruta a la copia del repo.
//
// ⚠ Las dos tienen que seguir empalmando a mano: el día que cambie la de
// `avisos.ts`, esta constante se cambia con ella. No hay nada que avise.

const LOGO_EN_LA_NUBE = 'https://cbodontologiayestetica.com.ar/brand/logo/png/'
const LOGO_EN_EL_REPO = '../brand/logo/png/'


// ── Armar los textos ─────────────────────────────────────────────────────────

function comoTexto(): string {

  const partes: string[] = [
    'LOS NUEVE CORREOS, EN TEXTO',
    'Generado por tools/armar-prueba-correos.ts — no se edita a mano.',
    '',
  ]

  for ( const escenario of ESCENARIOS ) {

    const mensajes = armarMensajes( escenario.datos, escenario.motivo )

    partes.push(
      '',
      '═══════════════════════════════════════════════════════════════',
      escenario.nombre,
      `(${ escenario.porQue })`,
      '═══════════════════════════════════════════════════════════════',
    )

    for ( const mensaje of mensajes ) {
      partes.push(
        '',
        '───────────────────────────────────────────────────────────────',
        `Para:    ${ mensaje.to.join( ', ' ) }`,
        `Asunto:  ${ mensaje.subject }`,
        '───────────────────────────────────────────────────────────────',
        mensaje.text,
      )
    }
  }

  partes.push( '' )

  return partes.join( '\n' )
}


// ── Armar la página para mirarlos ────────────────────────────────────────────
//
// Cada correo va dentro de un marco de 600 px, que es el ancho del cuerpo de un
// correo: mirarlo al ancho de la pantalla no dice nada de cómo se va a ver.
//
// ⚠ MIENTRAS NO HAYA HTML, cada correo se muestra en texto preformateado. No es
// un adorno: así este archivo sirve desde hoy, y el día que la plantilla exista
// se ve la de verdad sin tocar el instrumento.
//
// 🔴 Y ESTA PÁGINA NO ES GMAIL. Sirve para iterar la forma, NUNCA para aprobarla:
// Gmail recorta estilos, bloquea imágenes y da vuelta colores, y nada de eso se
// ve acá. La aprobación es con el correo recibido en el teléfono.

function escaparHtml( texto: string ): string {

  return texto
    .replaceAll( '&', '&amp;' )
    .replaceAll( '<', '&lt;' )
    .replaceAll( '>', '&gt;' )
}


// El estilo del VISOR, que no es el del correo: éste sólo pinta el marco de
// alrededor. Va en un texto de varias líneas —las comillas inclinadas— en vez de
// un renglón por propiedad, para que se lea como el CSS que es.
//
// El ancho de 600 px es el único número que importa acá: es el ancho del cuerpo
// de un correo, y mirar uno al ancho de la pantalla no dice nada de cómo se ve.
const ESTILO_DEL_VISOR = `  <style>
    body {
      margin: 0;
      padding: 32px 16px;
      background: #E8E6E1;
      font: 14px/1.5 system-ui, sans-serif;
      color: #33322F;
    }

    h1,
    h2,
    .porque,
    .aviso,
    .sobre {
      max-width: 600px;
      margin-left: auto;
      margin-right: auto;
    }

    h1 {
      font-size: 20px;
    }

    h2 {
      font-size: 16px;
      margin-top: 40px;
      margin-bottom: 4px;
    }

    .aviso {
      margin-bottom: 24px;
      padding: 12px 16px;
      background: #FFF;
      border-left: 4px solid #B08D57;
    }

    .porque {
      margin-bottom: 12px;
      color: #5A5853;
    }

    .sobre {
      margin-bottom: 32px;
    }

    .cabecera {
      padding: 8px 12px;
      background: #33322F;
      color: #FAF7F2;
      font-size: 12px;
    }

    .cabecera span {
      display: inline-block;
      width: 52px;
      color: #B08D57;
    }

    .marco {
      background: #FFF;
    }

    pre {
      margin: 0;
      padding: 20px;
      white-space: pre-wrap;
      font: 13px/1.6 ui-monospace, monospace;
    }
  </style>`


function comoPagina(): string {

  const bloques: string[] = []

  for ( const escenario of ESCENARIOS ) {

    const mensajes = armarMensajes( escenario.datos, escenario.motivo )

    bloques.push(
      `<h2>${ escaparHtml( escenario.nombre ) }</h2>`,
      `<p class="porque">${ escaparHtml( escenario.porQue ) }</p>`,
    )

    for ( const mensaje of mensajes ) {

      const cuerpo = mensaje.html
        ? mensaje.html.replaceAll( LOGO_EN_LA_NUBE, LOGO_EN_EL_REPO )
        : `<pre>${ escaparHtml( mensaje.text ) }</pre>`

      bloques.push(
        '<div class="sobre">',
        `  <div class="cabecera">`,
        `    <span>Para</span> ${ escaparHtml( mensaje.to.join( ', ' ) ) }<br>`,
        `    <span>Asunto</span> ${ escaparHtml( mensaje.subject ) }`,
        `  </div>`,
        `  <div class="marco">${ cuerpo }</div>`,
        '</div>',
      )
    }
  }

  return [
    '<!doctype html>',
    '<html lang="es">',
    '<head>',
    '  <meta charset="utf-8">',
    '  <title>Los nueve correos — CB Odontología</title>',
    ESTILO_DEL_VISOR,
    '</head>',
    '<body>',
    '  <h1>Los nueve correos</h1>',
    '  <div class="aviso">',
    '    <strong>Esto no es Gmail.</strong> Sirve para iterar la forma, nunca para',
    '    aprobarla: Gmail recorta estilos, bloquea las imágenes y da vuelta los',
    '    colores. La aprobación es con el correo recibido en el teléfono.',
    '  </div>',
    ...bloques,
    '</body>',
    '</html>',
    '',
  ].join( '\n' )
}


// ── Escribir los dos archivos ────────────────────────────────────────────────

await Deno.writeTextFile( 'pruebas/correos.txt', comoTexto() )
await Deno.writeTextFile( 'pruebas/correos.html', comoPagina() )

console.log( '✓ pruebas/correos.txt' )
console.log( '✓ pruebas/correos.html' )
console.log( '' )
console.log( `  ${ ESCENARIOS.length } escenarios · abrilos con:` )
console.log( '    code pruebas/correos.txt' )
console.log( '    open pruebas/correos.html' )
