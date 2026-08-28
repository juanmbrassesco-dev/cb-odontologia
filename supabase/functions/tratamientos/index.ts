// Portero de CB Odontología — endpoint público GET /tratamientos
//
// Devuelve la lista de tratamientos que ofrece el consultorio.
// Público a conciencia: es la misma lista que va publicada en la landing.

import { withSupabase } from 'npm:@supabase/server@^1'

// Los tipos de la base entran por acá. No cambian NADA de lo que el endpoint
// hace: son para que TypeScript sepa qué columnas existen y avise en el editor
// cuando una consulta pide algo que no está.

import type { Database } from '../_shared/tipos-de-la-base.ts'

export default {

  fetch: withSupabase< Database >(
    { auth: 'none' },
    async (req, ctx) => {

      // llave maestra: es el único que puede leer la tabla.
      // el orden lo manda la columna `orden` de la base, no el código.
      //
      // `id` lo necesita el desplegable de la pantalla: es lo que después viaja
      // a /profesionales y a /reservar. `duracion_web_min` dice cuánto espacio
      // ocupa el bloque (30 o 60) y viene en null en los que no se reservan por
      // la web. Ninguno de los dos es dato del paciente ni precio: publicarlos
      // no filtra nada.
      const respuesta = await ctx.supabaseAdmin
        .from('tratamientos')
        .select('id, nombre, duracion_web_min')
        .order('orden')

      // si la base falló, se avisa SIN contar por qué:
      // el detalle del error nombra tablas y roles, y esto lo ve cualquiera
      if (respuesta.error) {
        return Response.json(
          { error: 'No se pudo leer la lista' },
          { status: 500 },
        )
      }

      return Response.json(respuesta.data)
    },
  ),

}
