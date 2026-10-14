// QUÉ TURNOS TAPA UNA AUSENCIA — el cálculo que comparten los dos endpoints
// que la pueden poner en vigencia.
//
// 🔴 POR QUÉ ES UN ARCHIVO Y NO UN BLOQUE ADENTRO DE UN ENDPOINT: lo necesitan
// DOS —`cargar-ausencia`, cuando se crea, y `estado-de-ausencia`, cuando una
// apagada se vuelve a prender—, y las dos veces la pregunta es idéntica:
// «¿a quién hay que llamar?». Copiado en los dos, la primera vez que alguien
// arregle un borde en uno, el otro sigue contestando lo viejo — y el síntoma
// sería el peor posible: una lista vacía, que se lee como «no hay nadie a quien
// avisar». Es el mismo criterio con el que la ⑤.3 extrajo la grilla.
//
// 🔑 LO QUE QUEDA AFUERA, Y ES LA FRONTERA: acá no se decide nada. No se
// cancela, no se avisa, no se juzga si la ausencia se puede cargar. Entra una
// excepción y sale la lista de turnos que caen adentro.

import type { SupabaseContext } from 'npm:@supabase/server@^1'

import type { Database } from './tipos-de-la-base.ts'

import {
  diaTapado,
  fechaEnSantaFe,
} from './disponibilidad.ts'

import type { Excepcion } from './disponibilidad.ts'


export type TurnoTapado = {
  id: number
  inicio: string
  duracion_min: number
}


/**
 * Los turnos activos y futuros que la excepción `excepcion` deja tapados.
 *
 * `profesionalId` en `null` significa que la excepción es de la clínica y tapa
 * a todo el plantel, así que no se filtra por persona.
 *
 * Devuelve la lista, o `'error-de-base'` si la consulta falló — quien llama
 * decide qué contestar, porque el texto del error de Postgres nombra tablas y
 * columnas y no puede viajar al navegador.
 */
export async function turnosTapadosPor(
  ctx: SupabaseContext< Database >,
  excepcion: Excepcion,
  profesionalId: number | null,
) {

  // 🔒 EL `select` NO PIDE `observaciones_paciente`, que puede tener datos de
  // salud. Para llamar a alguien hacen falta su nombre y su teléfono, y lo que
  // no se lee no se puede publicar por accidente.
  let consulta = ctx.supabaseAdmin
    .from( 'turnos' )
    .select( `
      id,
      inicio,
      duracion_min,
      paciente:pacientes!inner ( nombre, apellido, telefono ),
      profesional:profesionales!inner ( id, nombre, apellido ),
      tratamiento:tratamientos!turnos_tratamiento_id_fkey ( nombre )
    ` )
    .eq( 'activo', true )

    // Sólo los que todavía no se atendieron: a un turno de la semana pasada no
    // hay a quién llamarle.
    .gte( 'inicio', new Date().toISOString() )
    .order( 'inicio' )

  if ( profesionalId !== null ) {
    consulta = consulta.eq( 'profesional_id', profesionalId )
  }

  const turnos = await consulta

  if ( turnos.error ) {
    console.error( 'No se pudieron leer los turnos tapados:', turnos.error )
    return 'error-de-base' as const
  }

  // 🔑 SE PREGUNTA CON `diaTapado( )`, LA MISMA FUNCIÓN QUE USA LA GRILLA DEL
  // PACIENTE. No hay una segunda regla de tapado en el proyecto, y por eso lo
  // que esta lista dice coincide con lo que el almanaque va a dejar de ofrecer.
  return turnos.data.filter( ( turno ) => {

    const fecha = fechaEnSantaFe( new Date( turno.inicio ) )

    return diaTapado( fecha, [ excepcion ] )
  } )
}
