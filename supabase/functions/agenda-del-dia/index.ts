// Portero de CB Odontología — endpoint GET /agenda-del-dia?fecha=AAAA-MM-DD
//
// La primera entrega de verdad del panel: los turnos activos de un día.
//
// QUIÉN VE QUÉ, y sale de la cerradura, no del pedido:
//   admin        → todos los profesionales
//   profesional  → sólo los suyos
//
// 🔴 LA TRAMPA DE ESTE ENDPOINT, y es la que justifica que el filtro NO se lea
// del pedido. Acepta `?profesional_id=` para que Cecilia pueda mirar la agenda
// de una sola persona. Si ese parámetro se obedeciera sin preguntar quién pide,
// un profesional cualquiera lo mandaría con el id de otro y vería sus turnos,
// con los nombres de pacientes que no son suyos. Tiene nombre: IDOR (Insecure
// Direct Object Reference), y es de la misma familia que A01.
//
// LA REGLA: si el que pide no es admin, el parámetro se IGNORA y el filtro se
// fuerza a su propio id. No se rechaza el pedido —un 403 ahí le confirmaría al
// que prueba que el id existe—: se contesta su propia agenda, que es lo que
// tiene derecho a ver.
//
// 🔒 `observaciones_paciente` NO ENTRA EN EL SELECT, y es decisión escrita:
// puede traer datos de salud y el frente de la Ley 25.326 está abierto. Entra
// en ⑤.6, que es la etapa que la necesita de verdad. `nota` queda afuera por
// el mismo criterio: no hace falta para ver el día, y un dato que no sale no se
// puede filtrar por accidente mañana, cuando alguien arme otra pantalla con
// esta misma respuesta.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y acá
// se lo deja prendido. Un pedido sin token muere antes de llegar.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'

import {
  desfaseDeSantaFe,
  esFechaValida,
  sumarDias,
} from '../_shared/disponibilidad.ts'


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo leer la agenda' },
    { status: 500 },
  )
}


export default {

  fetch: withSupabase< Database >(
    { auth: 'user' },
    async ( req, ctx ) => {

      // ── 1. La cerradura, antes de mirar el pedido ──────────────────────────

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

      // ── 2. La fecha ───────────────────────────────────────────────────────

      const url = new URL( req.url )

      const fecha = url.searchParams.get( 'fecha' )

      if ( !fecha || !esFechaValida( fecha ) ) {
        return Response.json(
          { error: 'Falta la fecha, o no tiene la forma AAAA-MM-DD' },
          { status: 400 },
        )
      }

      // 🔴 EL DÍA SE ACOTA CON EL DESFASE DE SANTA FE PUESTO, y sin esto el
      // endpoint contesta mal en silencio: `turnos.inicio` es un instante, y
      // un día argentino va de las 03:00 UTC a las 03:00 UTC del siguiente.
      // Filtrando por UTC pelado, los turnos de 00:00 a 03:00 caerían en el
      // día de al lado — y el de las 21:00 aparecería como del día siguiente.
      const desfase = desfaseDeSantaFe( fecha )

      const desde = `${ fecha }T00:00:00${ desfase }`
      const hasta = `${ sumarDias( fecha, 1 ) }T00:00:00${ desfase }`

      // ── 3. De quién son los turnos que se devuelven ───────────────────────

      const pedido = url.searchParams.get( 'profesional_id' )

      // Acá se aplica la regla de arriba. Para un no-admin, `pedido` no se
      // mira: el filtro es su propio id, siempre.
      const filtroProfesional = quien.esAdmin
        ? pedido
        : String( quien.id )

      // ── 4. La consulta ────────────────────────────────────────────────────

      // El `!` nombra la relación por su constraint: `turnos` apunta DOS VECES
      // a `tratamientos` —el tratamiento y el motivo de consulta— y sin eso
      // PostgREST no sabe cuál seguir. Falla ruidoso, pero falla.
      let consulta = ctx.supabaseAdmin
        .from( 'turnos' )
        .select( `
          id,
          inicio,
          duracion_min,
          canal,
          paciente:pacientes!inner ( id, nombre, apellido ),
          profesional:profesionales!inner ( id, nombre, apellido ),
          tratamiento:tratamientos!turnos_tratamiento_id_fkey ( nombre ),
          motivo:tratamientos!turnos_motivo_consulta_id_fkey ( nombre ),
          obra_social:obras_sociales ( nombre )
        ` )
        .eq( 'activo', true )
        .gte( 'inicio', desde )
        .lt( 'inicio', hasta )

      // `Number( … )` y no el texto pelado: la columna es `bigint` y el
      // parámetro de la URL siempre llega como string. Lo cazó `deno check`.
      if ( filtroProfesional ) {
        consulta = consulta.eq( 'profesional_id', Number( filtroProfesional ) )
      }

      const turnos = await consulta.order( 'inicio' )

      if ( turnos.error ) {
        return falloDeBase()
      }

      // El día vacío es una respuesta válida, no un error: es el domingo, o el
      // feriado. La pantalla que lo reciba dibuja el estado vacío.
      return Response.json( {
        fecha,
        esAdmin: quien.esAdmin,
        turnos: turnos.data,
      } )
    },
  ),

}
