// Portero de CB Odontología — endpoint POST /cargar-ausencia
//
// Carga una ausencia de un profesional, o un cierre de toda la clínica, y
// devuelve LOS TURNOS QUE QUEDAN TAPADOS por ella.
//
// 🔴 POR QUÉ DEVUELVE LOS TURNOS EN LUGAR DE CANCELARLOS, y es una decisión de
// Juan del 6-ago que acá pesa más que allá: el sistema AVISA y la persona
// llama. Cancelar solo mandaría un correo por turno, y **un correo no se
// desmanda**: un dedo mal puesto en una fecha le cancelaría el turno a cinco
// pacientes reales por un error de tipeo. La lista deja llamar a cada una y
// cancelar de a una con `POST /cancelar-del-panel`, que ya existe.
//
// 🔴 Y LOS DEVUELVE EN EL MISMO VIAJE, no en un endpoint aparte que la pantalla
// consulte antes. Entre un «¿hay turnos ese día?» y el «cargalo» alguien puede
// reservar por la web, y esa ventana devolvería una lista que ya no es cierta.
// Acá la ausencia ya está guardada cuando se cuentan los turnos.
//
// 🔒 EL ALCANCE VIAJA EXPLÍCITO —`alcance: 'propio' | 'clinica'`— y NO se
// deduce de un `profesional_id` ausente. Si se dedujera, un pedido al que se le
// cayó ese campo intentaría crear un cierre que tapa al plantel entero, y lo
// único entre eso y el consultorio cerrado sería el chequeo de nivel. La
// defensa sigue estando —`puedeTocar( )` lo rechaza—, pero un pedido ambiguo no
// tiene por qué llegar hasta ella.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y
// acá se lo deja prendido.
//
// ✅ MIGRACIÓN: `permitir_cargar_ausencias`, que da el `insert` por columnas.
// `activa` queda afuera y la pone la base con su `default true`: una ausencia
// nace tapando, y un alta que pudiera escribirla podría nacer apagada.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'

import { puedeTocar } from '../_shared/permisos.ts'

import { esFechaValida } from '../_shared/disponibilidad.ts'

import { turnosTapadosPor } from '../_shared/tapados.ts'


const TIPOS = [ 'unica', 'recurrente' ]

const SEMANA_MINIMA = 1

const SEMANA_MAXIMA = 5


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo cargar la ausencia' },
    { status: 500 },
  )
}


function sinAcceso(): Response {

  return Response.json(
    { error: 'Sin acceso a esta solapa' },
    { status: 403 },
  )
}


function pedidoInvalido( detalle: string ): Response {

  return Response.json(
    { error: detalle },
    { status: 400 },
  )
}


// Un texto del pedido, sin espacios de sobra. Cadena vacía si no vino o si no
// era texto: el que valida es el `if`, no esto. Copiado de
// `alta-de-profesional`, donde está escrito el mismo criterio.
function textoDelPedido( valor: unknown ): string {

  if ( typeof valor !== 'string' ) {
    return ''
  }

  return valor.trim()
}


export default {

  fetch: withSupabase< Database >(
    { auth: 'user' },
    async ( req, ctx ) => {

      // ── 1. La cerradura ───────────────────────────────────────────────────

      let quien

      try {
        quien = await quienPide( ctx )
      }
      catch {
        return falloDeBase()
      }

      if ( !quien ) {
        return sinAcceso()
      }

      // ── 2. El pedido ──────────────────────────────────────────────────────

      let cuerpo

      try {
        cuerpo = await req.json()
      }
      catch {
        return pedidoInvalido( 'El pedido no trae un cuerpo JSON' )
      }

      const descripcion = textoDelPedido( cuerpo.descripcion )

      if ( !descripcion ) {
        return pedidoInvalido(
          'Falta la descripción: es lo único que después explica por qué ese'
          + ' día está cerrado',
        )
      }

      const tipo = textoDelPedido( cuerpo.tipo )

      if ( !TIPOS.includes( tipo ) ) {
        return pedidoInvalido( "El tipo tiene que ser 'unica' o 'recurrente'" )
      }

      // ── 3. De quién va a ser la fila ──────────────────────────────────────
      //
      // 🔑 ARRANCA EN LA PROPIA Y SÓLO SE MUEVE CON PERMISO, que es el mismo
      // orden de `ausencias-del-panel` y por el mismo motivo: el default es el
      // seguro, así que un campo raro no desvía nada.
      const alcance = textoDelPedido( cuerpo.alcance )

      let profesionalIdDeLaFila: number | null = quien.id

      if ( alcance === 'clinica' ) {
        profesionalIdDeLaFila = null
      }
      else if ( alcance === 'propio' ) {

        const pedido = Number( cuerpo.profesional_id )

        if (
          quien.esAdmin
          && cuerpo.profesional_id !== undefined
          && Number.isInteger( pedido )
          && pedido >= 1
        ) {
          profesionalIdDeLaFila = pedido
        }
      }
      else {
        return pedidoInvalido( "El alcance tiene que ser 'propio' o 'clinica'" )
      }

      // 🔴 LA LÍNEA QUE NO SE PUEDE BORRAR. Sin ella, cualquier profesional con
      // sesión válida cierra el consultorio entero mandando
      // `alcance: 'clinica'`. El `esAdmin` sale de la cerradura, nunca del
      // pedido.
      if ( !puedeTocar( quien, profesionalIdDeLaFila ) ) {
        return sinAcceso()
      }

      // ── 4. Las columnas que corresponden a cada tipo ──────────────────────
      //
      // ⚠ LA BASE YA RECHAZA ESTO —son los cinco `check` de `excepciones`—, así
      // que acá no se repite la regla: se traduce a un 400 con texto legible.
      // Un `23514` crudo nombra la constraint y no dice qué falta.
      const fechaDesde = textoDelPedido( cuerpo.fecha_desde )

      const fechaHasta = textoDelPedido( cuerpo.fecha_hasta )

      const semana = Number( cuerpo.semana_del_mes )

      if ( tipo === 'unica' ) {

        if ( !esFechaValida( fechaDesde ) ) {
          return pedidoInvalido(
            'Una ausencia de fechas necesita el día de arranque, con la forma'
            + ' AAAA-MM-DD',
          )
        }

        if ( fechaHasta && !esFechaValida( fechaHasta ) ) {
          return pedidoInvalido( 'La fecha de fin no tiene la forma AAAA-MM-DD' )
        }

        if ( fechaHasta && fechaHasta < fechaDesde ) {
          return pedidoInvalido(
            'La fecha de fin es anterior a la de arranque',
          )
        }
      }

      if ( tipo === 'recurrente' ) {

        if (
          !Number.isInteger( semana )
          || semana < SEMANA_MINIMA
          || semana > SEMANA_MAXIMA
        ) {
          return pedidoInvalido(
            `La semana del mes va de ${ SEMANA_MINIMA } a ${ SEMANA_MAXIMA }`,
          )
        }
      }

      // ── 5. Se guarda ──────────────────────────────────────────────────────
      //
      // 🔑 CADA TIPO SE LEE CON COLUMNAS DISTINTAS, así que las que no son de
      // este tipo van explícitamente en `null`. No se omiten: dejarlas a la
      // vista evita que una lectura rápida crea que se perdieron por el camino.
      //
      // ⚠ Y una 'recurrente' CON fechas sería válida para la base —acotan desde
      // y hasta cuándo rige la regla—, pero esta pantalla no las carga: la
      // regla vive hasta que alguien la apaga.
      let fechaDesdeFinal: string | null = null

      let fechaHastaFinal: string | null = null

      let semanaFinal: number | null = null

      if ( tipo === 'unica' ) {

        fechaDesdeFinal = fechaDesde

        // Sin fecha de fin, la ausencia tapa un solo día: es como se carga un
        // feriado, y `tapaEsteDia( )` lo resuelve solo.
        if ( fechaHasta ) {
          fechaHastaFinal = fechaHasta
        }
      }

      if ( tipo === 'recurrente' ) {
        semanaFinal = semana
      }

      const nueva = await ctx.supabaseAdmin
        .from( 'excepciones' )
        .insert( {
          descripcion: descripcion,
          tipo: tipo,
          fecha_desde: fechaDesdeFinal,
          fecha_hasta: fechaHastaFinal,
          semana_del_mes: semanaFinal,
          profesional_id: profesionalIdDeLaFila,
        } )
        .select( `
          id, descripcion, tipo, fecha_desde, fecha_hasta,
          semana_del_mes, activa, profesional_id
        ` )
        .single()

      if ( nueva.error ) {
        console.error( 'No se pudo cargar la ausencia:', nueva.error )
        return falloDeBase()
      }

      // ── 6. Qué turnos quedaron tapados ────────────────────────────────────
      //
      // El cálculo vive en `_shared/tapados.ts` porque lo necesita también
      // `estado-de-ausencia`, cuando una ausencia apagada se vuelve a prender.
      const tapados = await turnosTapadosPor(
        ctx,
        nueva.data,
        profesionalIdDeLaFila,
      )

      if ( tapados === 'error-de-base' ) {

        // 🔑 LA AUSENCIA YA SE GUARDÓ, así que esto NO es un 500: contestar
        // error haría pensar que no se cargó y alguien la cargaría de nuevo.
        // Se devuelve la fila con el aviso de que el conteo no se pudo hacer.
        return Response.json(
          {
            ausencia: nueva.data,
            turnosTapados: [],
            sePudoContar: false,
          },
          { status: 201 },
        )
      }

      // 201 y no 200: se creó una fila. Es el mismo código que devuelven
      // `alta-de-profesional` y `turno-del-panel` cuando dan de alta.
      return Response.json(
        {
          ausencia: nueva.data,
          turnosTapados: tapados,
          sePudoContar: true,
        },
        { status: 201 },
      )
    },
  ),

}
