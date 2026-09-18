// Portero de CB Odontología — endpoint público GET /obras-sociales
//
// Devuelve las coberturas que acepta el consultorio, para el desplegable
// obligatorio del formulario de reserva.
//
// Público a conciencia, por la misma razón que `tratamientos`: es la lista que
// el consultorio le dice a cualquiera que llame por teléfono, y el paciente la
// necesita ANTES de tener sesión iniciada.

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
      //
      // `nombre` es lo que el paciente lee y elige; `entidad` es el título bajo
      // el que se agrupa en el desplegable, y en la mayoría de las filas repite
      // el nombre. `id` es lo que después viaja a /reservar.
      //
      // Los tres `.order` son uno solo partido en tres criterios, y el orden
      // entre ellos importa: primero la columna `orden` —que sube `Particular`
      // a la cabeza—, después la entidad, y dentro de cada entidad el nombre.
      // Ninguno vive en este archivo: el criterio lo manda la base.
      //
      // `activa` se filtra y no se devuelve: un convenio apagado no es una
      // opción, así que el que llega acá ya está todo activo.
      const respuesta = await ctx.supabaseAdmin
        .from('obras_sociales')
        .select('id, nombre, entidad')
        .eq('activa', true)
        .order('orden')
        .order('entidad')
        .order('nombre')

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
