// Portero de CB Odontología — endpoint POST /estado-de-ausencia
//
// Prende o apaga una ausencia. Y cuando la PRENDE, devuelve los turnos que
// quedan tapados, igual que `cargar-ausencia`.
//
// 🔴 POR QUÉ PRENDE Y NO SÓLO APAGA. La primera versión del plan tenía un
// endpoint llamado «apagar», y eso dejaba la etapa a medias: una ausencia
// apagada por un toque mal dado no se podía volver a prender desde el panel, y
// la única salida era el Table Editor — justo lo que esta etapa viene a sacar
// del medio. Y además existe el caso al que sirve: *«en verano no atiendo los
// viernes»* se apaga en marzo y se prende en diciembre.
//
// 🔴 LA TRAMPA DE IDOR (Insecure Direct Object Reference) DE ESTE ENDPOINT, y
// es la razón del orden de los pasos: **de quién es la ausencia sale de la FILA
// LEÍDA, nunca del cuerpo del pedido.** Si saliera del cuerpo, mandar el `id`
// de la ausencia de Cecilia junto con el `profesional_id` propio pasaría el
// chequeo de propiedad y le apagaría las vacaciones a otra persona. Es el mismo
// orden que ya usa `mover-turno`: leer, después decidir.
//
// 🔒 Y APAGAR UN CIERRE DE CLÍNICA ES DE NIVEL, no de propiedad: la fila no es
// de nadie, así que `puedeTocar( )` exige admin. Un profesional no puede
// destapar un feriado que Cecilia cerró.
//
// ⚠ NO HAY `delete` EN NINGUNA PARTE DE ESTA ETAPA: no se borran filas, se
// apaga el estado. Una excepción borrada no deja rastro de por qué esa semana
// estuvo cerrada durante meses.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y
// acá se lo deja prendido.
//
// ✅ MIGRACIÓN: `permitir_cargar_ausencias`, que da `update ( activa )` — UNA
// sola columna. Con un `update` sobre la tabla entera este endpoint podría
// reescribir `profesional_id` o las fechas, o sea mudarle la ausencia a otra
// persona, y la base no lo frenaría.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'

import { puedeTocar } from '../_shared/permisos.ts'

import { turnosTapadosPor } from '../_shared/tapados.ts'


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo cambiar la ausencia' },
    { status: 500 },
  )
}


function sinAcceso(): Response {

  return Response.json(
    { error: 'Sin acceso a esta ausencia' },
    { status: 403 },
  )
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
        return Response.json(
          { error: 'El pedido no trae un cuerpo JSON' },
          { status: 400 },
        )
      }

      const id = Number( cuerpo.id )

      if ( !Number.isInteger( id ) || id < 1 ) {
        return Response.json(
          { error: 'Falta el id de la ausencia, o no es un entero válido' },
          { status: 400 },
        )
      }

      // Boolean estricto: un `"false"` de texto, que es lo que manda un
      // formulario mal armado, no puede terminar prendiendo una ausencia que
      // tapa días. Mismo criterio que `pareja-del-panel`.
      const prender = cuerpo.activa === true

      // ── 3. La fila, ANTES de decidir ──────────────────────────────────────

      const fila = await ctx.supabaseAdmin
        .from( 'excepciones' )
        .select( `
          id, descripcion, tipo, fecha_desde, fecha_hasta,
          semana_del_mes, activa, profesional_id
        ` )
        .eq( 'id', id )
        .maybeSingle()

      if ( fila.error ) {
        console.error( 'No se pudo leer la ausencia:', fila.error )
        return falloDeBase()
      }

      // 🔒 UN ID QUE NO EXISTE CONTESTA LO MISMO QUE UNO AJENO, y es a
      // propósito: distinguir «no existe» de «no es tuya» le dice a quien
      // prueba ids al azar cuáles existen. Es la misma decisión que ya está
      // escrita en `cancelar-del-panel`.
      if ( !fila.data ) {
        return sinAcceso()
      }

      // 🔴 ACÁ, Y NO ANTES: el dato que decide salió de la base.
      if ( !puedeTocar( quien, fila.data.profesional_id ) ) {
        return sinAcceso()
      }

      // ── 4. Se cambia el estado ────────────────────────────────────────────

      const cambiada = await ctx.supabaseAdmin
        .from( 'excepciones' )
        .update( { activa: prender } )
        .eq( 'id', id )

        // El mismo recurso que usan `cancelar` y `pareja-del-panel`: con la
        // condición puesta, el segundo clic no encuentra nada que cambiar en
        // vez de reescribir la fila.
        .eq( 'activa', !prender )
        .select( 'id' )
        .maybeSingle()

      if ( cambiada.error ) {
        console.error( 'No se pudo cambiar la ausencia:', cambiada.error )
        return falloDeBase()
      }

      // ── 5. Si quedó prendida, a quién hay que llamar ──────────────────────
      //
      // 🔑 PRENDER UNA AUSENCIA TAPA DÍAS IGUAL QUE CREARLA, así que la
      // advertencia tiene que ser la misma. Apagarla, al contrario, DESTAPA:
      // no hay nadie a quien avisarle y la lista va vacía.
      if ( !prender ) {

        return Response.json( {
          id: id,
          activa: false,
          yaEstaba: !cambiada.data,
          turnosTapados: [],
          sePudoContar: true,
        } )
      }

      const tapados = await turnosTapadosPor(
        ctx,
        fila.data,
        fila.data.profesional_id,
      )

      if ( tapados === 'error-de-base' ) {

        // El cambio ya se guardó: contestar error haría pensar que no.
        return Response.json( {
          id: id,
          activa: true,
          yaEstaba: !cambiada.data,
          turnosTapados: [],
          sePudoContar: false,
        } )
      }

      return Response.json( {
        id: id,
        activa: true,
        yaEstaba: !cambiada.data,
        turnosTapados: tapados,
        sePudoContar: true,
      } )
    },
  ),

}
