// Portero de CB Odontología — endpoint GET /profesionales-del-panel
//
// La lista de quién atiende, para el desplegable del panel.
//
// 🔴 POR QUÉ NO SE REUSA `GET /profesionales`, que ya existe y suena igual.
// Aquél contesta otra pregunta: «¿QUIÉNES HACEN TAL TRATAMIENTO?». Exige
// `?tratamiento=` y filtra por la pareja profesional-tratamiento, porque su
// trabajo es llenar la grilla del paciente con quien de verdad puede tomar
// ese turno. El panel necesita la lista COMPLETA: el consultorio es la
// autoridad sobre quién hace qué, y ahí no se filtra por la pareja.
//
// Hacerle aceptar la llamada sin `?tratamiento=` habría sido más corto y es
// peor: aquél es PÚBLICO (`auth: 'none'`), así que la lista entera del
// personal pasaría a estar al alcance de cualquiera. Dos preguntas distintas,
// con dos públicos distintos, son dos endpoints.
//
// 🔒 LAS CUATRO COLUMNAS Y NADA MÁS: id, nombre, apellido y si es admin. Ni el
// correo de contacto ni el de acceso — el de acceso es con el que esa persona
// entra, y un dato que no sale no se puede filtrar por accidente mañana.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y
// acá se lo deja prendido.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo leer la lista' },
    { status: 500 },
  )
}


export default {

  fetch: withSupabase< Database >(
    { auth: 'user' },
    async ( _req, ctx ) => {

      let quien

      try {
        quien = await quienPide( ctx )
      }
      catch {
        return falloDeBase()
      }

      if ( !quien ) {
        return Response.json(
          { error: 'Sin acceso al panel' },
          { status: 403 },
        )
      }

      // `activo = true` en la consulta y no en un `if` después: dar de baja a
      // alguien lo saca del desplegable en el pedido siguiente, sin ningún
      // paso extra que haya que acordarse de hacer.
      const profesionales = await ctx.supabaseAdmin
        .from( 'profesionales' )
        .select( 'id, nombre, apellido, es_admin' )
        .eq( 'activo', true )
        .order( 'apellido' )

      if ( profesionales.error ) {
        return falloDeBase()
      }

      return Response.json( {
        esAdmin: quien.esAdmin,
        yo: quien.id,
        profesionales: profesionales.data,
      } )
    },
  ),

}
