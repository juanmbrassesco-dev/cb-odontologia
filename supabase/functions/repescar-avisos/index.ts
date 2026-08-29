// Portero de CB Odontología — POST /repescar-avisos
//
// LA RED DE ABAJO, no el camino principal. `reservar` y `cancelar` siguen
// avisando en el momento; esto levanta lo que a ellos se les escapó.
//
// Resuelve dos agujeros que ningún endpoint podía tapar:
//
//   1. Un turno que Cecilia carga a mano —WhatsApp, presencial, Table Editor—
//      no pasa por `reservar`, así que NADIE le manda nada al paciente.
//   2. Si el proveedor de correo falla, `reservar` igual contesta 201 —el turno
//      está anotado— y el aviso se perdía para siempre.
//
// Cómo: compara, en cada turno futuro, lo que el turno ES (`activo`) contra lo
// que el paciente SABE (`aviso_estado`), y manda lo que falte. Quién decide eso
// no es este archivo, es la función `reclamar_avisos_pendientes` de la base —
// acá sólo se manda y se marca.
//
// 🔒 ES UN ENDPOINT COMO CUALQUIER OTRO: si queda público, cualquiera lo llama y
// le dispara correos a los pacientes. Lleva `verify_jwt = false` en
// `config.toml` —lo llama una máquina, no una persona con sesión— y un SECRETO
// PROPIO en un header. Sin él, 401.
//
// ⚠ El secreto es propio A PROPÓSITO, no la llave maestra. Mandar la service key
// desde un archivo de CI sería poner la llave del proyecto entero a cambio de
// una sola cosa. Mismo criterio de menor privilegio que el paso F.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { enviarAvisos } from '../_shared/avisos.ts'

import type { MotivoDelAviso } from '../_shared/avisos.ts'


// Cuántos turnos toma UNA corrida. Cada turno son tres correos, así que veinte
// son sesenta: entra cómodo en el tiempo máximo de la función y lejos del tope
// diario del proveedor. Lo que sobra espera quince minutos.
const TOPE_POR_CORRIDA = 20

// Un turno cargado a mano puede no tener tratamiento. El correo no puede decir
// "undefined": dice esto. Mismo texto que usa `cancelar`.
const TRATAMIENTO_SIN_CARGAR = 'Sin especificar'


// Un secreto cargado con un espacio en blanco es un secreto que no existe, y el
// fallo sería mudo. Misma guarda que `_shared/avisos.ts`.
function delEntorno( nombre: string ): string | null {

  const crudo = Deno.env.get( nombre )

  if ( !crudo ) {
    return null
  }

  const limpio = crudo.trim()

  if ( limpio === '' ) {
    return null
  }

  return limpio
}


// No dice por qué. Quien no tiene el secreto no se merece saber si el secreto
// existe, si está mal escrito o si el endpoint hace algo.
function noAutorizado(): Response {

  return Response.json(
    { error: 'No autorizado' },
    { status: 401 },
  )
}


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo leer la cola de avisos' },
    { status: 500 },
  )
}


export default {

  fetch: withSupabase< Database >(
    { auth: 'none' },
    async ( req, ctx ) => {

      // ── La puerta ───────────────────────────────────────────────────────────

      const secreto = delEntorno( 'SECRETO_REPESCA' )

      if ( !secreto ) {

        // Sin secreto configurado el endpoint NO queda abierto: queda cerrado.
        // Un despliegue al que le falta el secreto tiene que fallar cerrado, no
        // abierto — es la diferencia entre un error y un agujero.
        console.error( 'repesca: no hay SECRETO_REPESCA cargado' )

        return noAutorizado()
      }

      if ( req.headers.get( 'x-secreto-repesca' ) !== secreto ) {
        return noAutorizado()
      }


      // ── El reclamo ──────────────────────────────────────────────────────────
      //
      // Marcar y devolver en una sola operación es lo que impide que dos
      // corridas simultáneas se lleven el mismo turno. El porqué completo está
      // en la migración; acá alcanza con no separar las dos cosas.

      const lote = await ctx.supabaseAdmin
        .rpc( 'reclamar_avisos_pendientes', { tope: TOPE_POR_CORRIDA } )

      if ( lote.error ) {

        console.error( `repesca: falló el reclamo — ${ lote.error.message }` )

        return falloDeBase()
      }

      const turnos = lote.data

      let avisados = 0
      let fallados = 0


      // ── Los envíos ──────────────────────────────────────────────────────────

      for ( const turno of turnos ) {

        // Qué correo corresponde lo dice el estado del turno, no de dónde vino:
        // uno vivo pide el aviso del turno, uno apagado pide la cancelación.
        let motivo: MotivoDelAviso = 'cancelacion'

        if ( turno.turno_activo ) {
          motivo = 'reserva'
        }

        let nombreDelTratamiento = TRATAMIENTO_SIN_CARGAR

        if ( turno.tratamiento_nombre ) {
          nombreDelTratamiento = turno.tratamiento_nombre
        }

        const salio = await enviarAvisos( {
          turnoId: turno.turno_id,
          inicio: turno.turno_inicio,
          duracionMin: turno.turno_duracion_min,
          tratamiento: nombreDelTratamiento,
          motivoConsulta: turno.motivo_nombre,
          pacienteNombre: turno.paciente_nombre,
          pacienteApellido: turno.paciente_apellido,
          pacienteCorreo: turno.paciente_email,
          profesionalNombre: turno.profesional_nombre,
          profesionalApellido: turno.profesional_apellido,
          profesionalCorreo: turno.profesional_email,
          tieneObservaciones: turno.tiene_observaciones,
        },
        motivo )


        // ── Qué queda escrito ─────────────────────────────────────────────────
        //
        // Los cuatro casos, uno por línea y a la vista. Si salió, la marca dice
        // lo que el paciente ahora sabe. Si no salió, se vuelve al estado
        // anterior para que la próxima corrida lo levante de nuevo.
        //
        // El estado anterior NO se deduce, se decide: un turno apagado pudo
        // llegar acá desde `reservado` o desde vacío, y los dos casos piden lo
        // mismo —mandar la cancelación—, así que devolverlo a `reservado` deja
        // al sistema haciendo lo correcto en los dos.
        let marca: string | null = null

        if (  salio &&  turno.turno_activo ) { marca = 'reservado' }
        if (  salio && !turno.turno_activo ) { marca = 'cancelado' }
        if ( !salio &&  turno.turno_activo ) { marca = null        }
        if ( !salio && !turno.turno_activo ) { marca = 'reservado' }


        // 🔴 EL SEGUNDO `.eq` NO ES ADORNO Y ES LA LÍNEA MÁS FÁCIL DE BORRAR.
        //
        // Entre el reclamo y esta escritura pasan segundos, y en ese hueco el
        // paciente puede haber cancelado: `cancelar` deja `cancelado`, y sin
        // esta condición la repesca se lo pisaría con `reservado`. Es el mismo
        // razonamiento del `.eq( 'activo', true )` de `cancelar`.
        const marcado = await ctx.supabaseAdmin
          .from( 'turnos' )
          .update( {
            aviso_estado: marca,
            aviso_at: new Date().toISOString(),
          } )
          .eq( 'id', turno.turno_id )
          .eq( 'aviso_estado', 'enviando' )

        if ( marcado.error ) {

          // No corta la corrida: el correo ya salió y el resto del lote sigue.
          // Lo peor que deja es un turno que se vuelve a avisar, que es el lado
          // benigno del error.
          console.error(
            `repesca: no se pudo marcar el turno — ${ marcado.error.message }`,
          )
        }

        if ( salio ) {
          avisados = avisados + 1
        }
        else {
          fallados = fallados + 1
        }
      }


      // ── La respuesta ────────────────────────────────────────────────────────
      //
      // 🔴 NÚMEROS, NUNCA NOMBRES. Esto lo lee el registro de GitHub Actions, y
      // el de un repositorio público lo lee cualquiera. Quién tiene turno con
      // quién no viaja por ahí.
      //
      // ⚠ Y si el lote entero falló, contesta con error. Sin eso, Actions marca
      // el trabajo en verde mientras no sale un solo correo, que es la clase de
      // fallo silencioso que este proyecto viene esquivando.
      let estado = 200

      if ( turnos.length > 0 && avisados === 0 ) {
        estado = 500
      }

      return Response.json(
        {
          tomados: turnos.length,
          avisados: avisados,
          fallados: fallados,
        },
        { status: estado },
      )
    },
  ),

}
