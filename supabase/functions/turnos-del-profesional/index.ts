// Portero de CB Odontología — endpoint GET /turnos-del-profesional?profesional=<id>
//
// Los turnos que ese profesional todavía no atendió, con los datos que hacen
// falta para llamar a cada paciente uno por uno.
//
// LO PIDEN DOS PANTALLAS, y conviene saber las dos antes de tocar este archivo:
//   · LA LUPA de la solapa «Altas y bajas» — Cecilia, sobre CUALQUIER
//     profesional. Para eso nació.
//   · «MIS PRÓXIMOS TURNOS», adentro de «Mi agenda» — cada profesional, sobre
//     SÍ MISMO. Sumada el 15-oct-2026.
// Quién puede cuál lo decide el bloque 2.b, no la pantalla.
//
// 🔴 PARA QUÉ EXISTE, y el porqué no es de pantalla: si Cecilia da de baja a
// alguien que tenía seis turnos reservados, apagarlo NO los cancela ni avisa a
// nadie — quedan seis personas que van a viajar al consultorio a ver a alguien
// que no está. Esta lista es lo que le permite resolverlo por teléfono. Y se
// puede abrir DESPUÉS de la baja, que es el punto: la advertencia del momento
// se puede cerrar sin anotar nada, y entonces los teléfonos ya se perdieron.
//
// 🔴 POR QUÉ NO SE REUSA `GET /agenda-del-dia`: aquél contesta por DÍA y para
// trabajar la jornada. Acá la pregunta no tiene fecha —son todos los futuros,
// estén la semana que viene o en marzo— y el motivo de la consulta es ir
// cerrando una lista, no atender una agenda.
//
// 🔒 ESTE ES EL ÚNICO ENDPOINT DEL PROYECTO QUE DEVUELVE
// `observaciones_paciente`, y la decisión se tomó el 13-oct-2026 con su
// porqué, así que no se copia a otro endpoint sin volver a discutirla:
//   · Esa columna PUEDE TRAER DATOS DE SALUD. Por eso `mis-turnos`,
//     `mis-pacientes` y `agenda-del-dia` NO la devuelven.
//   · Acá sale porque esta pantalla la USA: el motivo por el que alguien pidió
//     el turno es lo que decide a quién se llama primero. Mínimo privilegio no
//     es «que nadie lo vea», es «cada pantalla devuelve lo que usa».
//   · Y lo que sostiene que salga es el chequeo del bloque 2.b.
//     🔀 ESTE RENGLÓN DECÍA, HASTA EL 15-oct-2026: «si este endpoint se
//     reusara alguna vez en una pantalla de profesional, la columna saldría
//     con él: ahí está el riesgo». PASÓ — y la decisión la tomó Juan ese día,
//     con el riesgo sobre la mesa: que el profesional vea el motivo de
//     consulta de SUS turnos es para lo que la columna existe. Lo que el
//     renglón viejo anticipaba bien, y sigue vigente, es que la columna viaja
//     con el endpoint: por eso el chequeo pasó a mirar también la PROPIEDAD,
//     y no se afloja ninguno de los dos.
//
// ⚠ LO QUE ESTO NO RESUELVE, para que nadie lo lea como resuelto: el
// consentimiento y el aviso de privacidad de la Ley 25.326 siguen pendientes
// (ítem 2 de la § 14). Ese frente lo abrió el `insert` que guarda la columna,
// no este `select`, y se cierra aparte.
//
// 🔑 SON LOS FUTUROS Y ACTIVOS, igual que el conteo de `plantel-del-panel`:
// las dos pantallas tienen que dar el mismo número o la lupa desmiente a la
// fila que se clickeó para abrirla.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y
// acá se lo deja prendido.
//
// ✅ NO HACE FALTA MIGRACIÓN: es sólo lectura, y los `grant select` de
// `turnos`, `pacientes` y `tratamientos` ya están puestos.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo leer los turnos' },
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

      // 🔴 EL CHEQUEO DE QUIÉN PUEDE VER ESTA LISTA NO ESTÁ ACÁ, Y EL MOTIVO
      // ESTÁ ESCRITO DONDE SÍ ESTÁ: necesita el id pedido ya convertido, así
      // que vive después del bloque 2. Lo único que se decide en este punto es
      // que el que pide sea personal de la clínica, y eso ya lo contestó el
      // `if ( !quien )` de arriba.
      //
      // ⚠️ EL ORDEN IMPORTA Y NO ES ESTÉTICO: dejando el parseo antes, un
      // profesional que manda un parámetro mal formado recibe 400 y no 403.
      // Eso está bien porque a esta altura YA SE SABE que es de la casa; lo
      // que no puede pasar es que un 400 le conteste algo a alguien de afuera,
      // y de ésos no queda ninguno después del `if ( !quien )`.

      // ── 2. De quién ───────────────────────────────────────────────────────

      const url = new URL( req.url )

      // 🔴 LA PRESENCIA SE CHEQUEA ANTES DE CONVERTIR, y el orden no es
      // estético: lo cazó el caso 24 de la batería, que esperaba 400 y
      // recibió 200.
      //
      // `searchParams.get( … )` devuelve `null` cuando el parámetro no vino, y
      // `Number( null )` NO da NaN: DA CERO. Así que un `Number.isInteger( … )`
      // solo contesta `true` para un pedido que no trae nada, el endpoint
      // consulta el profesional 0 —que no existe— y devuelve 200 con una lista
      // vacía. No falla: contesta bien a una pregunta que nadie hizo.
      //
      // 🔑 Y el `< 1` no es paranoia: los id de la base son
      // `generated by default as identity`, así que arrancan en 1. Un 0 o un
      // negativo no son "un profesional que no está": son un pedido mal
      // formado, y eso es 400, no una lista vacía.
      const crudo = url.searchParams.get( 'profesional' )

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

      // ── 2.b La cerradura de verdad: nivel O propiedad ─────────────────────
      //
      // 🔴 ESTAS SON LAS LÍNEAS QUE NO SE PUEDEN BORRAR, y acá valen doble: lo
      // que sale de este endpoint incluye `observaciones_paciente`. Sin ellas,
      // cualquier profesional logueado lee el motivo de consulta de los
      // pacientes de todos los demás mandando un id que no es suyo. Eso tiene
      // nombre: IDOR (Insecure Direct Object Reference) de lectura.
      //
      // 🔀 HASTA EL 15-oct-2026 ESTE CHEQUEO ERA SÓLO DE NIVEL, y el comentario
      // que lo explicaba decía: «un profesional no abre esta solapa ni para
      // verse a sí mismo, porque la solapa entera es de Cecilia». Era cierto
      // mientras la única pantalla que pedía acá fuera la lupa de «Altas y
      // bajas». Dejó de serlo: lo levantó Juan mirando el panel —un
      // profesional entra, ve el día que tiene en el campo de fecha, y un
      // turno de la semana que viene no existe para él hasta que adivine la
      // fecha—.
      //
      // 🔑 POR QUÉ SE AMPLÍA ESTE ENDPOINT EN VEZ DE ESCRIBIR OTRO: la lista
      // que las dos pantallas necesitan es la misma —los turnos futuros y
      // activos de un profesional—, y la pregunta no cambia según quién la
      // haga. Lo que cambia es quién tiene derecho a hacerla, y eso es
      // exactamente lo que decide este bloque. Un segundo endpoint sería un
      // segundo `select` con la columna sensible adentro: dos lugares que
      // auditar en vez de uno, para la única columna del proyecto que puede
      // traer datos de salud.
      //
      // ⚠️ LO QUE SIGUE SIENDO SÓLO DE CECILIA no es esta lista: es la solapa
      // de «Altas y bajas» desde donde se abre la lupa, y eso lo cierran sus
      // propios endpoints (`plantel-del-panel`, `baja-de-profesional`).
      if ( !quien.esAdmin && quien.id !== pedido ) {
        return sinAcceso()
      }

      // ── 3. Los turnos, con lo que hace falta para llamar ──────────────────
      //
      // 🔑 `pacientes!inner` y no `pacientes`: un turno SIEMPRE tiene paciente
      // —`paciente_id` es not null—, y el `!inner` es lo que le dice al tipo
      // que la casilla no viene vacía. Sin él habría que escribir un `if` por
      // cada dato del paciente que no cambia nada en tiempo de ejecución.
      //
      // 🔑 `tratamientos` SIN `!inner`, y la diferencia no es de estilo:
      // `tratamiento_id` ACEPTA NULO —un turno cargado a mano puede no tener
      // tratamiento todavía—, así que con `!inner` esas filas desaparecerían
      // de la lista. Justo las que hay que llamar.
      const turnos = await ctx.supabaseAdmin
        .from( 'turnos' )
        .select( `
          id,
          inicio,
          duracion_min,
          observaciones_paciente,
          paciente:pacientes!inner ( nombre, apellido, email, telefono ),
          tratamiento:tratamientos!turnos_tratamiento_id_fkey ( nombre )
        ` )
        .eq( 'profesional_id', pedido )
        .eq( 'activo', true )
        .gte( 'inicio', new Date().toISOString() )
        .order( 'inicio' )

      if ( turnos.error ) {
        return falloDeBase()
      }

      return Response.json( {
        profesional: pedido,
        turnos: turnos.data,
      } )
    },
  ),

}
