// Portero de CB Odontología — endpoint POST /pareja-del-panel
//
// Prende o apaga un tratamiento para un profesional. Sólo admin.
//
// 🔴 ES SÓLO DE CECILIA, Y ROMPE A PROPÓSITO LA SIMETRÍA DEL RESTO DEL PANEL.
// En todo lo demás cada profesional manda sobre lo suyo; acá no: un profesional
// NO PUEDE apagar ni su propio tratamiento. El motivo es de negocio y no
// técnico —ella es la referente de la clínica y decide cómo se hacen las
// cosas—, y está escrito en la § 6 del documento de estado con una advertencia
// que vale repetir: quien construya esto leyendo sólo el bullet de los
// permisos acumulativos le da el interruptor al profesional equivocado.
//
// 🔑 LO QUE ESTE ENDPOINT DECIDE SOLO, y es la razón de que sea uno y no dos:
// prender un tratamiento que nunca se cargó necesita un `insert`, y prender
// uno que estaba apagado necesita un `update`. Para quien usa la pantalla las
// dos cosas son el mismo tilde, así que la diferencia se resuelve acá y no se
// le pasa a la pantalla.
//
// ⚠ APAGAR UN TRATAMIENTO NO TOCA LOS TURNOS YA AGENDADOS, y es deliberado:
// los que ya están siguen en pie. Lo que cambia es qué se puede reservar de
// acá en adelante. Un apagado que cancelara turnos sería una bomba escondida
// detrás de un tilde.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y
// acá se lo deja prendido.
//
// ✅ MIGRACIONES: `permitir_crear_parejas` (el `insert` por columnas) y
// `permitir_apagar_parejas` (el `update` sobre `activo` Y NADA MÁS: sin eso,
// un error acá podría MUDAR una pareja a otra persona en vez de apagarla).

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'


// El código que Postgres devuelve cuando una fila choca contra un `unique`.
// Acá sólo puede pasar por una carrera: dos pedidos creando la misma pareja.
const YA_EXISTE = '23505'


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo cambiar el tratamiento' },
    { status: 500 },
  )
}


function sinAcceso(): Response {

  return Response.json(
    { error: 'Sin acceso a esta solapa' },
    { status: 403 },
  )
}


function entero( valor: unknown ): number | null {

  if ( valor === undefined || valor === null ) {
    return null
  }

  const numero = Number( valor )

  if ( !Number.isInteger( numero ) || numero < 1 ) {
    return null
  }

  return numero
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

      if ( !quien.esAdmin ) {
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

      const profesionalId = entero( cuerpo.profesional_id )
      const tratamientoId = entero( cuerpo.tratamiento_id )

      if ( profesionalId === null || tratamientoId === null ) {
        return Response.json(
          { error: 'Faltan profesional_id o tratamiento_id, o no son'
            + ' enteros válidos' },
          { status: 400 },
        )
      }

      // Boolean estricto: un `"false"` de texto, que es lo que manda un
      // formulario mal armado, no puede terminar prendiendo algo.
      const prender = cuerpo.activo === true

      // ── 3. ¿La pareja ya existe? ──────────────────────────────────────────

      const pareja = await ctx.supabaseAdmin
        .from( 'profesional_tratamientos' )
        .select( 'id, activo' )
        .eq( 'profesional_id', profesionalId )
        .eq( 'tratamiento_id', tratamientoId )
        .maybeSingle()

      if ( pareja.error ) {
        return falloDeBase()
      }

      // ── 4a. No existe: se crea, pero sólo si lo que se pide es PRENDER ────
      //
      // 🔑 APAGAR ALGO QUE NUNCA SE CARGÓ NO ESCRIBE NADA, y no es pereza: el
      // efecto que se busca —que ese profesional no ofrezca ese tratamiento—
      // ya se cumple sin la fila. Crearla apagada sumaría una fila que no dice
      // nada que la ausencia no dijera, y la tabla pasaría a tener once filas
      // por profesional en vez de las que de verdad hace.
      if ( !pareja.data ) {

        if ( !prender ) {

          return Response.json( {
            profesional: profesionalId,
            tratamiento: tratamientoId,
            activo: false,
            yaEstaba: true,
          } )
        }

        const creada = await ctx.supabaseAdmin
          .from( 'profesional_tratamientos' )
          .insert( {
            profesional_id: profesionalId,
            tratamiento_id: tratamientoId,
          } )
          .select( 'id' )
          .single()

        if ( creada.error ) {

          // Dos pedidos creando la misma pareja a la vez. No es un error de
          // nadie y el mundo ya quedó como se pedía, así que no es un 500.
          if ( creada.error.code === YA_EXISTE ) {

            return Response.json( {
              profesional: profesionalId,
              tratamiento: tratamientoId,
              activo: true,
              yaEstaba: true,
            } )
          }

          console.error( 'No se pudo crear la pareja:', creada.error )

          return falloDeBase()
        }

        return Response.json( {
          profesional: profesionalId,
          tratamiento: tratamientoId,
          activo: true,
          yaEstaba: false,
        } )
      }

      // ── 4b. Existe: se le cambia el estado ────────────────────────────────

      const cambiada = await ctx.supabaseAdmin
        .from( 'profesional_tratamientos' )
        .update( { activo: prender } )
        .eq( 'id', pareja.data.id )

        // El mismo recurso que usa cancelar: con la condición puesta, el
        // segundo clic no encuentra nada que cambiar en vez de reescribir.
        .eq( 'activo', !prender )
        .select( 'id' )
        .maybeSingle()

      if ( cambiada.error ) {
        console.error( 'No se pudo cambiar la pareja:', cambiada.error )
        return falloDeBase()
      }

      return Response.json( {
        profesional: profesionalId,
        tratamiento: tratamientoId,
        activo: prender,
        yaEstaba: !cambiada.data,
      } )
    },
  ),

}
