// Portero de CB Odontología — endpoint GET /tratamientos-del-profesional?profesional=<id>
//
// Qué hace cada profesional: el catálogo ENTERO, con una marca por tratamiento
// que dice si esa persona lo ofrece. Sólo admin.
//
// 🔴 DEVUELVE EL CATÁLOGO COMPLETO Y NO SÓLO LO QUE YA TIENE CARGADO, y es la
// decisión que hace útil a esta pantalla. Una lista de lo que ya hace sirve
// para mirar; para DECIDIR hace falta ver también lo que no hace, que es
// exactamente lo que se va a querer prender. Con la lista corta, agregar un
// tratamiento nuevo exigiría un buscador y otra pantalla.
//
// 🔑 LAS TRES SITUACIONES DE UN TRATAMIENTO, y la pantalla las dibuja igual
// pero la base no las guarda igual:
//   · hay pareja y está activa     → lo hace
//   · hay pareja y está apagada    → lo hacía y se apagó
//   · NO hay pareja                → nunca se cargó
// Las dos últimas se ven iguales para un paciente —no aparece— y son distintas
// para escribir: una se prende con un `update` y la otra necesita un `insert`.
// Por eso la respuesta trae `tienePareja`, que el endpoint de escritura usa
// para saber cuál de las dos cosas hacer.
//
// 🔴 POR QUÉ NO SE REUSA `GET /tratamientos`, que ya existe: aquél es PÚBLICO
// —lo lee el paciente desde el sitio para llenar el desplegable— y contesta
// «qué tratamientos hay». Éste contesta «qué hace esta persona», que es un
// dato del plantel. Dos preguntas con dos públicos distintos son dos
// endpoints.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y
// acá se lo deja prendido.
//
// ✅ NO HACE FALTA MIGRACIÓN: es sólo lectura, y los `grant select` de
// `tratamientos` y `profesional_tratamientos` están desde que se crearon.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo leer los tratamientos' },
    { status: 500 },
  )
}


function sinAcceso(): Response {

  return Response.json(
    { error: 'Sin acceso a esta solapa' },
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

      // 🔴 ES DE NIVEL, Y ACÁ NO ALCANZA CON «QUE SEA EL SUYO»: el interruptor
      // de tratamientos es de Cecilia sobre el suyo Y sobre el de todos. Un
      // profesional no puede apagar ni el propio, así que tampoco necesita
      // leer esta pantalla. La regla es de negocio y está en la § 6.
      if ( !quien.esAdmin ) {
        return sinAcceso()
      }

      // ── 2. De quién ───────────────────────────────────────────────────────

      const crudo = new URL( req.url ).searchParams.get( 'profesional' )

      if ( !crudo ) {
        return Response.json(
          { error: 'Falta profesional' },
          { status: 400 },
        )
      }

      const pedido = Number( crudo )

      if ( !Number.isInteger( pedido ) || pedido < 1 ) {
        return Response.json(
          { error: 'profesional no es un número entero válido' },
          { status: 400 },
        )
      }

      // ── 3. El catálogo y lo que esta persona hace ─────────────────────────
      //
      // 🔑 DOS CONSULTAS Y NO UN `left join`: el join daría una fila por
      // tratamiento con las columnas de la pareja al lado, que es más corto de
      // escribir y bastante más difícil de leer para quien venga a entender
      // por qué un tilde salió apagado. Son dos listas chicas —once
      // tratamientos y a lo sumo once parejas— así que lo que se paga es un
      // viaje más, no una consulta lenta.
      const tratamientos = await ctx.supabaseAdmin
        .from( 'tratamientos' )
        .select( 'id, nombre, orden' )
        .order( 'orden' )

      if ( tratamientos.error ) {
        return falloDeBase()
      }

      const parejas = await ctx.supabaseAdmin
        .from( 'profesional_tratamientos' )
        .select( 'tratamiento_id, activo' )
        .eq( 'profesional_id', pedido )

      if ( parejas.error ) {
        return falloDeBase()
      }

      // ── 4. Una fila por tratamiento, con su estado ────────────────────────

      const filas = tratamientos.data.map( ( tratamiento ) => {

        const pareja = parejas.data.find(
          ( una ) => una.tratamiento_id === tratamiento.id,
        )

        return {
          id: tratamiento.id,
          nombre: tratamiento.nombre,

          // `tienePareja` es lo que el endpoint de escritura necesita para
          // elegir entre crear la fila y cambiarle el estado a la que ya está.
          tienePareja: Boolean( pareja ),

          // Sin pareja, el tratamiento no se ofrece — que para un paciente se
          // ve igual que una pareja apagada.
          loHace: pareja ? pareja.activo : false,
        }
      } )

      return Response.json( {
        profesional: pedido,
        tratamientos: filas,
      } )
    },
  ),

}
