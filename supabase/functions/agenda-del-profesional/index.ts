// Portero de CB Odontología — endpoint GET /agenda-del-profesional
//
// La solapa «Mi agenda»: los tramos de atención de una persona, día por día,
// los apagados incluidos.
//
// ⚠️ VOCABULARIO, y ya se prestó a confusión una vez en este proyecto:
// `horarios_base` es LA AGENDA —la regla semanal, «los martes de 11 a 12:30»,
// donde UNA fila cubre todos los martes del año— y `excepciones` es lo que la
// PISA en fechas concretas. Este endpoint es de la primera; las ausencias son
// `ausencias-del-panel`.
//
// 🔑 LOS APAGADOS SALEN, y sin eso la columna `activo` no serviría de nada: si
// la pantalla escondiera los tramos apagados, no habría desde dónde volver a
// prenderlos y la única salida sería el Table Editor — que es justo lo que esta
// etapa viene a sacar del medio. Mismo criterio que `plantel-del-panel` con los
// profesionales de baja.
//
// 🔑 Y VIENEN LOS SIETE DÍAS, también los que no tienen ni un tramo. Un arreglo
// de siete posiciones deja a la pantalla dibujar la semana entera sin tener que
// inventar los días que faltan, y «el viernes no atiendo» pasa a ser un dato
// que se VE en lugar de una ausencia de datos.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y
// acá se lo deja prendido.
//
// ✅ NO HACE FALTA MIGRACIÓN: es sólo lectura, y `grant select on horarios_base`
// está puesto desde la etapa ①.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'


// Los siete días de la semana con la numeración ISO 8601 que usa la tabla:
// lunes 1 … domingo 7. El nombre NO viaja desde acá —lo escribe la pantalla—
// pero el número sí, y en este orden.
const DIAS = [ 1, 2, 3, 4, 5, 6, 7 ]


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo leer la agenda' },
    { status: 500 },
  )
}


function sinAcceso(): Response {

  return Response.json(
    { error: 'Sin acceso a esta agenda' },
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

      // ── 2. ¿De quién es la agenda que se pide? ────────────────────────────
      //
      // Mismo orden que `ausencias-del-panel` y `horarios-del-panel`: arranca
      // en la propia y sólo se mueve si el pedido pasa las tres condiciones. El
      // `crudo` hace falta porque `Number( null )` da CERO, no NaN.
      const url = new URL( req.url )

      const crudo = url.searchParams.get( 'profesional' )

      const pedido = Number( crudo )

      let profesionalId = quien.id

      if (
        quien.esAdmin
        && crudo
        && Number.isInteger( pedido )
        && pedido >= 1
      ) {
        profesionalId = pedido
      }

      // ── 3. Los tramos ─────────────────────────────────────────────────────

      const tramos = await ctx.supabaseAdmin
        .from( 'horarios_base' )
        .select( 'id, dia_semana, inicio, fin, fin_maximo, activo' )
        .eq( 'profesional_id', profesionalId )
        .order( 'dia_semana' )
        .order( 'inicio' )

      if ( tramos.error ) {
        console.error( 'No se pudo leer la agenda:', tramos.error )
        return falloDeBase()
      }

      // ── 4. Un día por posición, con sus tramos adentro ────────────────────

      const semana = DIAS.map( ( dia ) => {

        const suyos = tramos.data.filter(
          ( tramo ) => tramo.dia_semana === dia,
        )

        return {
          dia: dia,

          tramos: suyos.map( ( tramo ) => {

            return {
              id: tramo.id,
              inicio: tramo.inicio,
              fin: tramo.fin,

              // 🔑 VIAJA AUNQUE ESTÉ VACÍO, y el vacío significa algo preciso:
              // «este tramo no se estira». No es un dato faltante.
              finMaximo: tramo.fin_maximo,

              activo: tramo.activo,
            }
          } ),
        }
      } )

      return Response.json( {
        yo: quien.id,
        esAdmin: quien.esAdmin,
        profesional: profesionalId,
        semana: semana,
      } )
    },
  ),

}
