// Portero de CB Odontología — endpoint público GET /tratamientos
//
// Devuelve la lista de tratamientos que ofrece el consultorio.
// Público a conciencia: es la misma lista que va publicada en la landing.

import { withSupabase } from 'npm:@supabase/server@^1'

export default {

  fetch: withSupabase(
    { auth: 'none' },
    async (req, ctx) => {

      // llave maestra: es el único que puede leer la tabla.
      // el orden lo manda la columna `orden` de la base, no el código
      const respuesta = await ctx.supabaseAdmin
        .from('tratamientos')
        .select('nombre')
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
