// LA PAREJA PROFESIONAL–TRATAMIENTO — una sola pregunta, un solo lugar.
//
// Qué es: la consulta que contesta si un profesional dado ofrece HOY un
// tratamiento dado. Vive acá porque la hacen DOS endpoints —`reservar` y
// `horarios-disponibles`— y hasta el 25-ago-2026 estaba calcada en los dos
// archivos, palabra por palabra.
//
// 🔴 POR QUÉ SE MUDÓ, y es el motivo entero: la condición `activo` que agregó
// la migración 21 tiene que valer en los dos endpoints o no vale en ninguno.
// Con la consulta duplicada, agregarla en uno y olvidarla en el otro deja la
// grilla ofreciendo horas de un tratamiento que el profesional ya no hace, y el
// paciente se entera recién al chocar contra el `POST /reservar`. Ese olvido no
// falla con error: contesta mal en silencio. Escrita una sola vez, no se puede
// aplicar a medias.
//
// La pareja se APAGA, no se borra (§ 9.3 del documento de estado): los turnos
// pasados siguen apuntando a una pareja que la base todavía recuerda.

import type { SupabaseContext } from 'npm:@supabase/server@^1'

import type { Database } from './tipos-de-la-base.ts'


// Los tres desenlaces posibles de la pregunta.
//
// La consulta NO devuelve una respuesta HTTP y es a propósito: cada endpoint
// arma la suya con sus propios helpers, y uno de los dos podría querer contestar
// distinto mañana. Acá se contesta QUÉ PASÓ; el endpoint decide qué hacer con
// eso.
//
// `no-la-hace` junta dos casos que al paciente le dan lo mismo: la pareja nunca
// existió, o existió y está apagada. Distinguirlos por fuera no cambia ninguna
// decisión y le contaría a cualquiera qué dejó de ofrecer el consultorio.
export type EstadoDeLaPareja =
  | 'error-de-base'
  | 'no-la-hace'
  | 'la-hace'


export async function estadoDeLaPareja(
  ctx: SupabaseContext< Database >,
  profesionalId: number,
  tratamientoId: number,
): Promise< EstadoDeLaPareja > {

  const pareja = await ctx.supabaseAdmin
    .from( 'profesional_tratamientos' )
    .select( 'id' )
    .eq( 'profesional_id', profesionalId )
    .eq( 'tratamiento_id', tratamientoId )
    .eq( 'activo', true )
    .maybeSingle()

  if ( pareja.error ) {
    return 'error-de-base'
  }

  if ( !pareja.data ) {
    return 'no-la-hace'
  }

  return 'la-hace'
}
