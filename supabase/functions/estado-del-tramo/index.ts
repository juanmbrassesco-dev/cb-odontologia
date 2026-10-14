// Portero de CB Odontología — endpoint POST /estado-del-tramo
//
// Prende o apaga un tramo de la agenda semanal. Y cuando lo APAGA, devuelve los
// turnos futuros que quedan fuera de la agenda.
//
// 🔴 QUE PRENDA ES LA MITAD QUE JUSTIFICA LA COLUMNA. Juan eligió apagar en vez
// de borrar justamente por el caso «en verano no atiendo los viernes»: se apaga
// en diciembre y se vuelve a prender en marzo. Un endpoint que sólo apagara
// dejaría ese caso a medias y la única forma de volver atrás sería el Table
// Editor.
//
// 🔴 LA TRAMPA DE IDOR (Insecure Direct Object Reference): de quién es el tramo
// sale de la FILA LEÍDA, nunca del cuerpo del pedido. Mandar el id de un tramo
// ajeno junto con el `profesional_id` propio pasaría un chequeo de propiedad
// hecho sobre el pedido, y le apagaría media agenda a otra persona. Es el mismo
// orden que usan `mover-turno` y `estado-de-ausencia`: leer, después decidir.
//
// 🔑 POR QUÉ AVISA EN LUGAR DE CANCELAR, y es el precedente del 6-ago que ya
// rige en la baja de un profesional y en las ausencias: un correo no se
// desmanda. Apagar el tramo de los viernes con tres turnos agendados adentro no
// cancela nada — devuelve los tres para que alguien llame, o los MUEVA, que casi
// siempre es mejor para la paciente.
//
// ⚠️ Y LOS TURNOS YA AGENDADOS SIGUEN EN PIE: apagar un tramo saca horarios de
// la OFERTA, no de la agenda. El turno existe, la profesional lo ve en su día y
// lo atiende si quiere. Lo que ya no se puede es reservar ahí.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y
// acá se lo deja prendido.
//
// ✅ MIGRACIÓN: `permitir_editar_la_agenda`, que da `update ( activo )` — UNA
// sola columna, así que un error acá no puede correrle el horario a nadie.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'

import { puedeTocar } from '../_shared/permisos.ts'

import {
  aMinutos,
  diaSemanaISO,
  fechaEnSantaFe,
  horaEnSantaFe,
} from '../_shared/disponibilidad.ts'


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo cambiar el tramo' },
    { status: 500 },
  )
}


function sinAcceso(): Response {

  return Response.json(
    { error: 'Sin acceso a ese tramo' },
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
          { error: 'Falta el id del tramo, o no es un entero válido' },
          { status: 400 },
        )
      }

      // Boolean estricto: un `"false"` de texto, que es lo que manda un
      // formulario mal armado, no puede terminar prendiendo un tramo.
      const prender = cuerpo.activo === true

      // ── 3. La fila, ANTES de decidir ──────────────────────────────────────

      const tramo = await ctx.supabaseAdmin
        .from( 'horarios_base' )
        .select( 'id, profesional_id, dia_semana, inicio, fin, activo' )
        .eq( 'id', id )
        .maybeSingle()

      if ( tramo.error ) {
        console.error( 'No se pudo leer el tramo:', tramo.error )
        return falloDeBase()
      }

      // 🔒 UN ID QUE NO EXISTE CONTESTA LO MISMO QUE UNO AJENO: distinguir «no
      // existe» de «no es tuyo» le dice a quien prueba ids al azar cuáles
      // existen. Misma decisión que `cancelar-del-panel` y las ausencias.
      if ( !tramo.data ) {
        return sinAcceso()
      }

      // 🔴 ACÁ, Y NO ANTES: el dato que decide salió de la base.
      if ( !puedeTocar( quien, tramo.data.profesional_id ) ) {
        return sinAcceso()
      }

      // ── 4. Se cambia el estado ────────────────────────────────────────────

      const cambiado = await ctx.supabaseAdmin
        .from( 'horarios_base' )
        .update( { activo: prender } )
        .eq( 'id', id )

        // El mismo recurso que `pareja-del-panel` y `estado-de-ausencia`: con
        // la condición puesta, el segundo clic no encuentra nada que cambiar en
        // vez de reescribir la fila.
        .eq( 'activo', !prender )
        .select( 'id' )
        .maybeSingle()

      if ( cambiado.error ) {
        console.error( 'No se pudo cambiar el tramo:', cambiado.error )
        return falloDeBase()
      }

      // ── 5. Si se apagó, qué turnos quedan fuera de la agenda ──────────────
      //
      // 🔑 PRENDER NO DEJA A NADIE AFUERA: agrega oferta. Así que la lista sólo
      // tiene sentido al apagar, y al prender va vacía.
      if ( prender ) {

        return Response.json( {
          id: id,
          activo: true,
          yaEstaba: !cambiado.data,
          turnosAfectados: [],
          sePudoContar: true,
        } )
      }

      // 🔒 El `select` NO pide `observaciones_paciente`, que puede tener datos
      // de salud: para llamar a alguien hacen falta su nombre y su teléfono.
      const turnos = await ctx.supabaseAdmin
        .from( 'turnos' )
        .select( `
          id,
          inicio,
          duracion_min,
          paciente:pacientes!inner ( nombre, apellido, telefono ),
          tratamiento:tratamientos!turnos_tratamiento_id_fkey ( nombre )
        ` )
        .eq( 'profesional_id', tramo.data.profesional_id )
        .eq( 'activo', true )
        .gte( 'inicio', new Date().toISOString() )
        .order( 'inicio' )

      if ( turnos.error ) {
        console.error( 'No se pudieron leer los turnos:', turnos.error )

        // El cambio ya se guardó: contestar error haría pensar que no.
        return Response.json( {
          id: id,
          activo: false,
          yaEstaba: !cambiado.data,
          turnosAfectados: [],
          sePudoContar: false,
        } )
      }

      // 🔴 EL FILTRO ES POR DÍA DE LA SEMANA Y POR HORA LOCAL, y las dos mitades
      // importan. Un turno queda fuera de la agenda si cae en el mismo día de la
      // semana que el tramo Y arranca dentro de su horario.
      //
      // ⚠ La hora se convierte a la zona del consultorio, no se corta del
      // texto: la base devuelve en UTC, así que un turno de las 08:00 de Santa
      // Fe llega como '…T11:00:00+00:00' y recortar da «11:00» — una hora que
      // existe, bien escrita, y tres horas corrida.
      // ⚠ LOS TRES DATOS DEL TRAMO SE SACAN A CONSTANTES ANTES DEL FILTRO, y no
      // es estilo: adentro de la función de `filter`, TypeScript ya no sabe que
      // `tramo.data` dejó de poder ser nulo —el `if` que lo garantiza quedó
      // afuera— y se niega a compilar. Lo cazó `deno check`.
      const diaDelTramo = tramo.data.dia_semana

      const desde = aMinutos( tramo.data.inicio )

      const hasta = aMinutos( tramo.data.fin )

      const afectados = turnos.data.filter( ( turno ) => {

        const instante = new Date( turno.inicio )

        if ( diaSemanaISO( fechaEnSantaFe( instante ) ) !== diaDelTramo ) {
          return false
        }

        const minuto = aMinutos( horaEnSantaFe( instante ) )

        return minuto >= desde && minuto < hasta
      } )

      return Response.json( {
        id: id,
        activo: false,
        yaEstaba: !cambiado.data,
        turnosAfectados: afectados,
        sePudoContar: true,
      } )
    },
  ),

}
