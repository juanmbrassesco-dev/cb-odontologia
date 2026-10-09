// Portero de CB Odontología — endpoint GET /buscar-pacientes?q=texto
//
// El buscador que va ANTES de cargar un turno a mano. Contesta una sola
// pregunta: ¿qué fichas de paciente coinciden con lo que Cecilia está
// tipeando?
//
// 🔴 POR QUÉ EXISTE, y no es comodidad. El paciente se elige de una LISTA,
// nunca se tipea su correo. Tipearlo reintroduce el agujero que el disparador
// de minúsculas tapó y agrega uno peor: una letra de más crea una ficha
// DUPLICADA, y el paciente deja de ver sus turnos porque están colgados de la
// otra. Elegir de una lista no tiene ese modo de falla.
//
// ⚠ NO ES `mis-pacientes`, aunque suene parecido. Aquél contesta «¿a qué
// pacientes puede pedirle turno el que está conectado?» y filtra por el correo
// del token: es del PACIENTE. Éste es del CONSULTORIO y busca en toda la
// tabla, por eso lleva la cerradura del panel.
//
// 🔒 QUIÉN PUEDE: cualquier profesional activo, no sólo admin. Un profesional
// carga turnos propios, y para eso necesita encontrar al paciente. La
// diferencia admin / no admin aparece en de QUIÉN es el turno, no en a quién
// se puede buscar.
//
// 🔒 QUÉ DEVUELVE, y por qué más que `mis-pacientes`: ahí van tres columnas
// porque las mira un paciente; acá las mira el consultorio y necesita el
// CORREO —para saber si esa ficha va a recibir el aviso, o si no tiene— y el
// TELÉFONO, que es con lo que lo llama si no lo tiene. Siguen quedando afuera
// el DNI y la fecha de nacimiento: no hacen falta para elegir una ficha.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y
// acá se lo deja prendido. Un pedido sin token muere antes de llegar.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'


// Menos de esto devuelve media tabla y no ayuda a nadie: con una letra, la
// lista es tan larga como buscar a ojo.
const MINIMO_DE_LETRAS = 2

function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo buscar' },
    { status: 500 },
  )
}


// 🔴 ESTO NO ES COSMÉTICA: ES LO QUE EVITA UNA INYECCIÓN DE FILTRO.
//
// El `.or( … )` de PostgREST recibe los filtros como UN SOLO TEXTO, separados
// por comas: `nombre.ilike.%ana%,apellido.ilike.%ana%`. Si el término que
// escribe el usuario entra ahí con una coma adentro, deja de ser un valor y
// pasa a ser un SEPARADOR — o sea que el que busca puede escribir filtros
// propios dentro de la consulta. Es la misma familia que una inyección SQL,
// aplicada a la sintaxis de PostgREST.
//
// Los paréntesis hacen lo mismo porque `or( )` los usa para agrupar. Y `%` y
// `_` son los comodines de `ilike`: no rompen nada, pero convierten una
// búsqueda en «traeme todo», así que salen por la misma puerta.
//
// Se SACAN en vez de escaparse: no hay ningún nombre de paciente que los
// necesite, y una lista de lo que se permite es más corta de auditar que una
// de lo que se escapa.
//
// ⚠ DESDE EL 9-oct-2026 LA INYECCIÓN DE FILTRO YA NO ES POSIBLE: la búsqueda
// pasó a una función de la base y el término viaja como PARÁMETRO, que no se
// puede confundir con la consulta que lo lleva. Esto se queda igual porque
// `%` y `_` SIGUEN siendo comodines de `ilike` adentro de la función — y
// porque una defensa que ya está probada no se saca cuando aparece otra.
function limpiarTermino( crudo: string ): string {

  return crudo
    .replace( /[,()%_\\*]/g, ' ' )
    .trim()
}


export default {

  fetch: withSupabase< Database >(
    { auth: 'user' },
    async ( req, ctx ) => {

      // ── 1. La cerradura, antes de mirar el pedido ─────────────────────────

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

      // ── 2. El término ─────────────────────────────────────────────────────

      const url = new URL( req.url )

      const termino = limpiarTermino( url.searchParams.get( 'q' ) ?? '' )

      // Devolver 400 acá sería castigar a quien todavía está tipeando: la
      // pantalla llama a este endpoint en cada tecla. Una lista vacía es la
      // respuesta correcta a «todavía no escribiste suficiente».
      if ( termino.length < MINIMO_DE_LETRAS ) {
        return Response.json( { pacientes: [] } )
      }

      // ── 3. La consulta ────────────────────────────────────────────────────

      // 🔴 LA BÚSQUEDA LA HACE LA BASE, no un filtro armado acá, y el motivo se
      // midió: el filtro comparaba el término contra CADA COLUMNA POR
      // SEPARADO, así que «rafa b» no coincidía con nadie —nadie tiene ese
      // texto adentro de su nombre ni adentro de su apellido— aunque «rafa»
      // devolviera a esa misma persona.
      //
      // El síntoma era peor que un cero: la pantalla abre el alta de ficha
      // cuando no hay coincidencias, así que al escribir el apellido los
      // resultados buenos desaparecían y aparecía el formulario para crear un
      // paciente que ya existía. Exactamente el agujero que este buscador
      // existe para tapar. Lo levantó Juan probándolo.
      //
      // `nombre || ' ' || apellido` no se puede expresar en un filtro de
      // PostgREST —comparan columnas contra valores, no saben concatenar—, y
      // en una función de la base es una línea. Detalle en la migración
      // 20261009160141.
      const pacientes = await ctx.supabaseAdmin
        .rpc( 'buscar_pacientes', { termino: termino } )

      if ( pacientes.error ) {
        return falloDeBase()
      }

      // Ninguna coincidencia NO es un error: es el caso que abre el alta en el
      // acto. La pantalla lo convierte en «no está, ¿lo creo?».
      return Response.json( { pacientes: pacientes.data } )
    },
  ),

}
