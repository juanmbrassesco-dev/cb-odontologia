// Portero de CB Odontología — endpoint público GET /profesionales
//
// Contesta una sola pregunta: quién puede atender ESE tratamiento.
//
// Es el frente ⑥, decidido el 6-ago-2026 y construido recién ahora: el paciente
// elige a qué viene, ve SÓLO los profesionales que hacen eso, elige uno, y
// recién ahí se le muestra la agenda. Hasta hoy `profesionales` se consultaba en
// `reservar` y en `horarios-disponibles`, pero en los dos casos para VALIDAR una
// pareja ya elegida — nunca para listar.
//
// Público a conciencia, igual que /tratamientos y /horarios-disponibles: el
// paciente tiene que poder ver si hay turno ANTES de registrarse (§ 4).
//
// Devuelve `id`, `nombre` y `apellido`, y nada más. `email` y `fecha_baja` se
// quedan en la base: lo que no se lee no se puede publicar por accidente.

import { withSupabase } from 'npm:@supabase/server@^1'

// Los tipos de la base entran por acá. No cambian NADA de lo que el endpoint
// hace: son para que TypeScript sepa qué columnas existen y avise en el editor
// cuando una consulta pide algo que no está.

import type { Database } from '../_shared/tipos-de-la-base.ts'

// Un pedido mal armado se contesta con el motivo: lo escribió quien está
// construyendo la pantalla y necesita saber qué corregir. Mismo estilo que
// `horarios-disponibles`, a propósito: dos endpoints públicos que rechazan
// distinto le enseñan a la pantalla dos formas de leer el error.
function pedidoInvalido( mensaje: string ): Response {

  return Response.json(
    { error: mensaje },
    { status: 400 },
  )
}

// Un fallo de la base se contesta SIN el detalle. El texto de Postgres nombra
// tablas, columnas y roles, y esto lo ve cualquiera.
function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo leer la lista de profesionales' },
    { status: 500 },
  )
}

export default {

  fetch: withSupabase< Database >(
    { auth: 'none' },
    async ( req, ctx ) => {

      const url = new URL( req.url )

      const tratamientoPedido = url.searchParams.get( 'tratamiento' )

      // Se valida TODO del lado del servidor, incluso lo que la pantalla ya va
      // a validar. El navegador corre en la máquina del paciente y cualquiera
      // edita lo que manda.

      if ( !tratamientoPedido ) {
        return pedidoInvalido( 'Falta el dato: tratamiento' )
      }

      const tratamientoId = Number( tratamientoPedido )

      if ( !Number.isInteger( tratamientoId ) ) {
        return pedidoInvalido( 'tratamiento tiene que ser un número' )
      }

      // ── Las TRES condiciones que tiene que cumplir un profesional ────────
      //
      // 1. estar activo (`profesionales.activo`),
      // 2. tener la pareja ACTIVA con ese tratamiento, y
      // 3. tener al menos un horario base cargado.
      //
      // La tercera no es un adorno: un profesional recién dado de alta, sin
      // agenda, aparecería en la lista y llevaría al paciente a una grilla
      // VACÍA de la que no se vuelve. Y el filtro es seguro porque las
      // `excepciones` sólo TAPAN días, nunca los abren: sin `horarios_base` no
      // hay agenda posible.
      //
      // `!inner` es lo que convierte una tabla hija en un FILTRO. Sin él,
      // PostgREST trae al profesional igual y le cuelga una lista vacía; con
      // él, el que no tiene fila hija no sale.
      //
      // La pareja se APAGA, no se borra (§ 9.3), y por eso hace falta pedir
      // `activo` además de que la fila exista.
      const respuesta = await ctx.supabaseAdmin
        .from( 'profesionales' )
        .select( `
          id,
          nombre,
          apellido,
          profesional_tratamientos!inner ( id ),
          horarios_base!inner ( id )
        ` )
        .eq( 'activo', true )
        .eq( 'profesional_tratamientos.tratamiento_id', tratamientoId )
        .eq( 'profesional_tratamientos.activo', true )
        .order( 'apellido' )

      // El orden se pide explícito. Sin `order`, Postgres devuelve las filas en
      // el orden que le conviene, y la lista puede cambiar de posición entre dos
      // cargas de la misma pantalla.

      if ( respuesta.error ) {
        return falloDeBase()
      }

      // Las tablas hijas se pidieron para FILTRAR, no para publicar: se usan y
      // se tiran. Lo que sale son tres campos, elegidos uno por uno.
      const profesionales = respuesta.data.map(
        ( fila ) => ( {
          id: fila.id,
          nombre: fila.nombre,
          apellido: fila.apellido,
        } ),
      )

      // Lista VACÍA es una respuesta legítima, no un error: pasa apenas Cecilia
      // apague una pareja. Va `200` con `[]`, y la pantalla dice "por ahora no
      // estamos tomando turnos web para eso" con el enlace de WhatsApp. Un 404
      // acá mentiría: el tratamiento existe, lo que no hay es quién lo tome.
      return Response.json( profesionales )
    },
  ),

}
