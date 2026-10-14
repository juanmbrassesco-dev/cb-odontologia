// Portero de CB Odontología — endpoint POST /cargar-tramo
//
// Agrega un tramo a la agenda semanal de alguien: «los viernes de 8 a 14».
//
// 🔒 CHEQUEO DE PROPIEDAD, con el bypass de la admin: cada profesional setea lo
// suyo y Cecilia puede sobre cualquiera. Es el requisito que ella precisó el
// 8-oct-2026 —la agenda propia la setea el PROFESIONAL, porque no tiene las
// mismas restricciones horarias que ella— y que pueda tocar la de otro queda
// como CAPACIDAD, no como el flujo previsto.
//
// ⚠️ ACÁ NO HAY CASO «DE LA CLÍNICA», al contrario de las ausencias:
// `horarios_base.profesional_id` es `not null`, así que un tramo es siempre de
// alguien. Se usa la misma `puedeTocar( )` y nunca se la llama con `null`.
//
// ⚠️ LOS TRES `check` DE LA TABLA NO SE REPITEN ACÁ —`dia_semana` entre 1 y 7,
// `fin > inicio`, `fin_maximo > fin`—: la base ya los aplica, y repetirlos en el
// código deja dos reglas que se separan el día que una cambie. Lo que hace este
// endpoint es traducir el `23514` a un 400 con texto legible, porque un error de
// Postgres nombra la constraint y no dice qué falta.
//
// 🔑 LO QUE SÍ VALIDA Y LA BASE NO PUEDE: que el tramo nuevo no se SOLAPE con
// otro activo del mismo día. Un `check` de fila no alcanza —compara una fila
// contra las otras— y el `EXCLUDE … USING gist` que lo haría bien es el que
// `turnos` usa para la doble reserva: correcto, y mucho más caro de leer para lo
// que acá está en juego. 🔴 Y hace falta porque el error NO SE VE: dos tramos
// pisados —lunes 8-14 y lunes 10-12— los fusiona `unificarBloques( )`, la grilla
// sale bien, y queda una agenda que nadie entiende el día que haya que
// corregirla.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y
// acá se lo deja prendido.
//
// ✅ MIGRACIÓN: `permitir_editar_la_agenda`, que da el `insert` por columnas.
// `activo` queda afuera y lo pone la base con su `default true`: un tramo nace
// atendiendo, y uno que naciera apagado estaría en la lista sin ofrecer turnos.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'

import { puedeTocar } from '../_shared/permisos.ts'

import { aMinutos } from '../_shared/disponibilidad.ts'


const DIA_MINIMO = 1

const DIA_MAXIMO = 7

// Una hora de reloj, 'HH:MM' o 'HH:MM:SS'. La base guarda `time`, que acepta
// las dos formas; lo que no acepta es texto libre.
const FORMA_DE_HORA = /^([01]\d|2[0-3]):[0-5]\d(:[0-5]\d)?$/


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo cargar el tramo' },
    { status: 500 },
  )
}


function sinAcceso(): Response {

  return Response.json(
    { error: 'Sin acceso a esa agenda' },
    { status: 403 },
  )
}


function pedidoInvalido( detalle: string ): Response {

  return Response.json(
    { error: detalle },
    { status: 400 },
  )
}


function horaDelPedido( valor: unknown ): string {

  if ( typeof valor !== 'string' ) {
    return ''
  }

  const limpio = valor.trim()

  if ( !FORMA_DE_HORA.test( limpio ) ) {
    return ''
  }

  return limpio
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

      const dia = Number( cuerpo.dia_semana )

      if (
        !Number.isInteger( dia )
        || dia < DIA_MINIMO
        || dia > DIA_MAXIMO
      ) {
        return pedidoInvalido(
          'El día de la semana va de 1 (lunes) a 7 (domingo)',
        )
      }

      const inicio = horaDelPedido( cuerpo.inicio )

      const fin = horaDelPedido( cuerpo.fin )

      if ( !inicio || !fin ) {
        return pedidoInvalido( 'La hora de inicio y la de fin van como HH:MM' )
      }

      if ( aMinutos( fin ) <= aMinutos( inicio ) ) {
        return pedidoInvalido( 'El cierre tiene que ser posterior al inicio' )
      }

      // 🔑 EL TECHO ES OPCIONAL Y EL VACÍO SIGNIFICA «ESTE TRAMO NO SE ESTIRA»,
      // no «se estira cero minutos». Es el mismo idioma que la columna ya tenía
      // escrito en `agregar_fin_maximo_a_horarios`.
      let finMaximo: string | null = null

      if ( cuerpo.fin_maximo ) {

        finMaximo = horaDelPedido( cuerpo.fin_maximo )

        if ( !finMaximo ) {
          return pedidoInvalido( 'El techo va como HH:MM, o vacío' )
        }

        if ( aMinutos( finMaximo ) <= aMinutos( fin ) ) {
          return pedidoInvalido(
            'El techo tiene que ser posterior al cierre: es hasta qué hora'
            + ' puede TERMINAR un turno que empezó antes de cerrar',
          )
        }
      }

      // ── 3. De quién va a ser el tramo ─────────────────────────────────────

      let profesionalId = quien.id

      const pedido = Number( cuerpo.profesional_id )

      if (
        quien.esAdmin
        && cuerpo.profesional_id !== undefined
        && Number.isInteger( pedido )
        && pedido >= 1
      ) {
        profesionalId = pedido
      }

      // 🔴 LA LÍNEA QUE NO SE PUEDE BORRAR: sin ella, cualquier profesional le
      // escribe la agenda a otro mandando su id. El `esAdmin` sale de la
      // cerradura, nunca del pedido.
      if ( !puedeTocar( quien, profesionalId ) ) {
        return sinAcceso()
      }

      // ── 4. ¿Se pisa con otro tramo de ese día? ────────────────────────────
      //
      // Sólo los ACTIVOS: un tramo apagado no ofrece nada, así que cargar uno
      // nuevo sobre su horario es legítimo —y es justo cómo se corrige un
      // horario sin borrar el viejo—.
      const delDia = await ctx.supabaseAdmin
        .from( 'horarios_base' )
        .select( 'inicio, fin' )
        .eq( 'profesional_id', profesionalId )
        .eq( 'dia_semana', dia )
        .eq( 'activo', true )

      if ( delDia.error ) {
        console.error( 'No se pudo leer la agenda del día:', delDia.error )
        return falloDeBase()
      }

      // Dos rangos se pisan si cada uno empieza antes de que el otro termine.
      // Tocarse NO es pisarse: un tramo que cierra 12:30 y otro que abre 12:30
      // conviven, y es el caso real de los martes de Cecilia.
      const desde = aMinutos( inicio )

      const hasta = aMinutos( fin )

      const pisado = delDia.data.find( ( otro ) => {

        return desde < aMinutos( otro.fin ) && aMinutos( otro.inicio ) < hasta
      } )

      if ( pisado ) {
        return pedidoInvalido(
          `Ese horario se pisa con el tramo de ${ pisado.inicio } a`
          + ` ${ pisado.fin } que ya está cargado ese día`,
        )
      }

      // ── 5. Se guarda ──────────────────────────────────────────────────────

      const nuevo = await ctx.supabaseAdmin
        .from( 'horarios_base' )
        .insert( {
          profesional_id: profesionalId,
          dia_semana: dia,
          inicio: inicio,
          fin: fin,
          fin_maximo: finMaximo,
        } )
        .select( 'id, dia_semana, inicio, fin, fin_maximo, activo' )
        .single()

      if ( nuevo.error ) {
        console.error( 'No se pudo cargar el tramo:', nuevo.error )
        return falloDeBase()
      }

      return Response.json(
        { tramo: nuevo.data },
        { status: 201 },
      )
    },
  ),

}
