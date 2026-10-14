// Portero de CB Odontología — endpoint GET /ausencias-del-panel
//
// La solapa «Ausencias»: las ausencias de una persona —activas y apagadas— y
// los cierres de clínica que la afectan.
//
// 🔴 POR QUÉ VIENEN MEZCLADAS LAS PROPIAS Y LAS DE LA CLÍNICA. Un profesional
// que ve su agenda cerrada un jueves tiene que poder enterarse de por qué, y el
// motivo puede no ser suyo: un feriado lo carga Cecilia y tapa a todos. Si esta
// pantalla mostrara sólo las propias, el día cerrado quedaría sin explicación
// en el único lugar donde se lo busca.
//
// 🔒 PERO NO PUEDE TOCARLAS, y la respuesta lo dice fila por fila con
// `puedoTocar`. ⚠ ESE CAMPO ES PARA LA PANTALLA, NO ES LA CERRADURA: sirve para
// no ofrecer un interruptor que va a dar en la cara. La cerradura la vuelve a
// aplicar `estado-de-ausencia`, que no le cree nada a lo que salió de acá.
//
// 🔑 LAS APAGADAS TAMBIÉN SALEN —no hay filtro por `activa`—, igual que
// `plantel-del-panel` devuelve a los de baja: una ausencia que terminó es lo
// que explica por qué esa semana estuvo cerrada, y apagarla no la borra.
//
// 🔑 Y DEVUELVE `semanasDelMes`, QUE NO SALE DE NINGUNA TABLA. Son las dos
// próximas fechas que tapa cada una de las cinco semanas posibles, calculadas
// acá. ⚠ El motivo es que «la tercera semana» es ambiguo en castellano y este
// proyecto eligió UNA lectura —la fila del almanaque que contiene el día
// 7N − 6—, escrita en la migración `cargar_tercera_semana_de_cecilia`. Quien
// carga la ausencia no lee migraciones, así que la pantalla le muestra las
// fechas de verdad. **El cálculo NO se puede copiar al navegador**: `js/*.js`
// son scripts globales y esto corre en Deno, no hay módulo que alcancen los
// dos, y una segunda copia de `esSemanaDelMes( )` prometería tapar una semana
// distinta de la que el portero tapa.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y
// acá se lo deja prendido.
//
// ✅ NO HACE FALTA MIGRACIÓN: es sólo lectura, y `grant select on excepciones`
// está puesto desde la etapa ①.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'

import { puedeTocar } from '../_shared/permisos.ts'

import {
  esSemanaDelMes,
  fechaEnSantaFe,
  sumarDias,
} from '../_shared/disponibilidad.ts'


// Hasta cuántos días adelante se buscan las dos próximas fechas de cada semana
// del mes. Con 80 alcanza de sobra: dos semanas del mismo número están a un mes
// de distancia, así que en 80 días entran siempre las dos.
const DIAS_QUE_SE_MIRAN = 80

// Las semanas del mes que la base acepta, y el 5 no es de más: la semana N es
// la fila del almanaque que contiene el día 7N − 6 —el 1, el 8, el 15, el 22 y
// el 29—, y el 29 existe todos los meses.
const SEMANAS_POSIBLES = [ 1, 2, 3, 4, 5 ]


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudieron leer las ausencias' },
    { status: 500 },
  )
}


function sinAcceso(): Response {

  return Response.json(
    { error: 'Sin acceso a esta solapa' },
    { status: 403 },
  )
}


/**
 * Los próximos dos tramos de almanaque que tapa la semana `semana` de cada mes.
 *
 * Devuelve algo como `[ { desde: '2026-10-11', hasta: '2026-10-17' }, … ]`: los
 * días consecutivos se juntan en un tramo, y se devuelven los dos primeros.
 */
function proximosTramos(
  semana: number,
  hoy: string,
): { desde: string, hasta: string }[] {

  const tramos: { desde: string, hasta: string }[] = []

  let dia = 0

  while ( dia < DIAS_QUE_SE_MIRAN && tramos.length < 2 ) {

    const fecha = sumarDias( hoy, dia )

    if ( esSemanaDelMes( fecha, semana ) ) {

      const ultimo = tramos[ tramos.length - 1 ]

      // Si el día de ayer ya estaba en el tramo abierto, este día lo estira en
      // lugar de abrir otro. Así una semana entera sale como UN tramo de
      // domingo a sábado y no como siete fechas sueltas.
      if ( ultimo && ultimo.hasta === sumarDias( fecha, -1 ) ) {
        ultimo.hasta = fecha
      }
      else {
        tramos.push( { desde: fecha, hasta: fecha } )
      }
    }

    dia = dia + 1
  }

  return tramos
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

      // ── 2. ¿De quién son las ausencias que se piden? ──────────────────────
      //
      // 🔑 EL ORDEN ES EL ARREGLO QUE YA SE PAGÓ UNA VEZ en
      // `horarios-del-panel`: la variable ARRANCA en la propia y sólo se mueve
      // si el pedido pasa las tres condiciones. `searchParams.get( … )`
      // devuelve `null` cuando el parámetro no vino, y `Number( null )` NO da
      // NaN: DA CERO, que `Number.isInteger( … )` acepta. Sin el `crudo` y el
      // `>= 1`, un admin que llama sin `?profesional=` pide las del
      // profesional 0 —que no existe— y recibe una lista vacía en vez de la
      // suya, sin ningún error.
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

      // ── 3. Las ausencias ──────────────────────────────────────────────────
      //
      // Las de esta persona Y las que no tienen profesional, que son los
      // cierres de clínica. Las de OTRO profesional no se piden: ni se
      // muestran ni se tocan desde esta pantalla.
      //
      // El número se pega adentro del texto del filtro y es seguro porque
      // `profesionalId` es un `number` del tipo: lo que llega es un número, no
      // lo que haya escrito quien armó la dirección. Mismo criterio que
      // `grilla.ts`.
      const ausencias = await ctx.supabaseAdmin
        .from( 'excepciones' )
        .select( `
          id, descripcion, tipo, fecha_desde, fecha_hasta,
          semana_del_mes, activa, profesional_id
        ` )
        .or( `profesional_id.is.null,profesional_id.eq.${ profesionalId }` )
        .order( 'activa', { ascending: false } )
        .order( 'id', { ascending: false } )

      if ( ausencias.error ) {
        console.error( 'No se pudieron leer las excepciones:', ausencias.error )
        return falloDeBase()
      }

      // ── 4. Las fechas de cada semana del mes ──────────────────────────────

      const hoy = fechaEnSantaFe( new Date() )

      const semanasDelMes = SEMANAS_POSIBLES.map( ( semana ) => {

        return {
          semana: semana,

          // El día del almanaque que define la semana, que es lo que después
          // se escribe en pantalla como «la semana que contiene el día 15».
          diaAncla: 7 * semana - 6,

          proximos: proximosTramos( semana, hoy ),
        }
      } )

      // ── 5. La respuesta ───────────────────────────────────────────────────

      const filas = ausencias.data.map( ( fila ) => {

        return {
          id: fila.id,
          descripcion: fila.descripcion,
          tipo: fila.tipo,
          fechaDesde: fila.fecha_desde,
          fechaHasta: fila.fecha_hasta,
          semanaDelMes: fila.semana_del_mes,
          activa: fila.activa,

          // `null` es «de la clínica», y la pantalla lo pinta distinto: tapa a
          // todos y no es de nadie.
          profesionalId: fila.profesional_id,

          esDeLaClinica: fila.profesional_id === null,

          puedoTocar: puedeTocar( quien, fila.profesional_id ),
        }
      } )

      return Response.json( {
        yo: quien.id,
        esAdmin: quien.esAdmin,
        profesional: profesionalId,
        hoy: hoy,
        ausencias: filas,
        semanasDelMes: semanasDelMes,
      } )
    },
  ),

}
