// Portero de CB Odontología — endpoint GET /plantel-del-panel
//
// La solapa «Altas y bajas»: una fila por profesional, con su estado y cuántos
// turnos futuros tiene sin atender.
//
// 🔴 POR QUÉ NO SE REUSA `GET /profesionales-del-panel`, que ya existe y
// devuelve casi las mismas columnas. Aquél contesta «¿a quién le puedo cargar
// un turno?» y por eso filtra `activo = true`: un profesional dado de baja no
// tiene que aparecer en un desplegable donde se elige a quién agendarle.
// Ésta contesta «¿cómo está el plantel?», y para eso los de baja son
// justamente las filas que importan. Hacerle aceptar un `?incluir_bajas=`
// habría sido más corto y es peor: aquél lo pide CUALQUIER profesional para
// llenar su desplegable, y esta solapa es sólo de Cecilia. Dos preguntas
// distintas, con dos públicos distintos, son dos endpoints.
//
// 🔴 ES DE NIVEL, NO DE PROPIEDAD, y es la primera vez que el panel estrena
// este chequeo solo. En `cancelar-del-panel` la pregunta era «¿este turno es
// tuyo?»; acá no hay nada que sea de nadie: la pregunta es «¿sos admin?». Un
// profesional con sesión válida recibe 403 aunque pida su propia fila.
//
// 🔒 LAS COLUMNAS DE CORREO NO SALEN, y es decisión: `email` es a dónde se le
// avisa y `email_de_acceso` es la cuenta con la que entra. Esta pantalla
// muestra estado y conteo, así que ninguno de los dos hace falta — y un dato
// que no sale no se puede filtrar por accidente mañana. El día que la solapa
// quiera mostrar con qué cuenta entra cada uno, se agrega acá y se escribe el
// porqué, no se agrega de paso.
//
// 🔑 EL CONTEO SON LOS TURNOS FUTUROS Y ACTIVOS, nunca los pasados: ya se
// atendieron y no hay a quién avisarle. Es lo que decide si la baja necesita
// la advertencia o es directa.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y
// acá se lo deja prendido.
//
// ✅ NO HACE FALTA MIGRACIÓN: es sólo lectura, y `grant select on profesionales`
// y `on turnos` ya están puestos desde que se crearon las tablas.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo leer el plantel' },
    { status: 500 },
  )
}


// El MISMO texto para dos casos distintos: el que pide no es personal de la
// clínica, o lo es y no es admin. Separarlos le diría al que prueba cuál de
// las dos cosas le falta.
function sinAcceso(): Response {

  return Response.json(
    { error: 'Sin acceso a esta solapa' },
    { status: 403 },
  )
}


export default {

  fetch: withSupabase< Database >(
    { auth: 'user' },
    async ( _req, ctx ) => {

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

      // 🔴 ESTA ES LA LÍNEA QUE NO SE PUEDE BORRAR, y no hay ninguna otra que
      // la cubra: sin ella, cualquier profesional lee el plantel entero con
      // quién está de baja y desde cuándo. El `esAdmin` sale de la cerradura,
      // nunca del pedido.
      if ( !quien.esAdmin ) {
        return sinAcceso()
      }

      // ── 2. El plantel entero, de baja incluidos ───────────────────────────

      const plantel = await ctx.supabaseAdmin
        .from( 'profesionales' )
        .select( 'id, nombre, apellido, es_admin, activo, fecha_baja' )
        .order( 'apellido' )

      if ( plantel.error ) {
        return falloDeBase()
      }

      // ── 3. Los turnos que todavía no se atendieron ────────────────────────
      //
      // 🔑 POR QUÉ DOS CONSULTAS Y NO UN CONTEO AGRUPADO EN LA BASE: la base
      // sabe agrupar y contar sola, pero el pedido que lo hace se lee mucho
      // peor que estas dos líneas, y el que va a volver a leer esto cuando algo
      // no cuadre es Juan. El plantel son unas pocas filas y los turnos futuros
      // también: lo que se paga es un viaje más a la base, no una consulta
      // lenta. El día que el consultorio tenga miles de turnos futuros, esto se
      // cambia por un conteo agrupado y el motivo queda escrito acá.
      const ahora = new Date().toISOString()

      const pendientes = await ctx.supabaseAdmin
        .from( 'turnos' )
        .select( 'profesional_id' )
        .eq( 'activo', true )
        .gte( 'inicio', ahora )

      if ( pendientes.error ) {
        return falloDeBase()
      }

      // ── 4. Una fila por profesional, con su conteo ────────────────────────

      const filas = plantel.data.map( ( profesional ) => {

        const suyos = pendientes.data.filter(
          ( turno ) => turno.profesional_id === profesional.id,
        )

        return {
          id: profesional.id,
          nombre: profesional.nombre,
          apellido: profesional.apellido,
          esAdmin: profesional.es_admin,
          activo: profesional.activo,
          fechaBaja: profesional.fecha_baja,
          turnosPendientes: suyos.length,
        }
      } )

      return Response.json( {
        yo: quien.id,
        plantel: filas,
      } )
    },
  ),

}
