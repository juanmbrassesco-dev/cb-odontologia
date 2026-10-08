// Portero de CB Odontología — endpoint POST /cancelar-del-panel
//
// Cancela un turno DESDE EL PANEL, o sea cancelándoselo a otra persona.
//
// 🔴 POR QUÉ NO SE REUSA `/cancelar`, que ya existe y hace casi lo mismo: aquél
// ancla la identidad en el PACIENTE —filtra el turno con `pacientes!inner` y el
// correo del token—, así que un pedido de Cecilia sobre el turno de Marta no
// encuentra nada y recibe 403. La cerradura de aquél no es una validación de
// más que se pueda saltear: es su modelo de acceso entero.
//
// 🔴 EL CHEQUEO QUE JUSTIFICA ESTE ARCHIVO, y es el que el plan anticipó como
// «el IDOR de ⑤.1 pero escribiendo»: un profesional gestiona los turnos de SU
// agenda y nada más. Sin comparar `turnos.profesional_id` contra el `id` que
// devuelve `quien-pide.ts`, cualquier profesional con sesión válida cancela el
// turno de otro mandando un id que no es suyo — y el paciente se entera por el
// correo de cancelación, que sale igual.
//
// 🔑 Y EL TURNO AJENO SE CONTESTA COMO SI NO EXISTIERA, con el mismo 403 y el
// mismo texto. Dos respuestas distintas —«no existe» y «no es tuyo»— le dicen
// al que prueba ids cuáles existen, que es la mitad del trabajo de encontrar
// uno para atacar.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y acá
// se lo deja prendido.
//
// ✅ NO HACE FALTA MIGRACIÓN: `grant update ( activo ) on turnos to service_role`
// ya está, de `permitir_cancelacion_de_turnos`.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { enviarAvisos } from '../_shared/avisos.ts'

import { quienPide } from '../_shared/quien-pide.ts'


const TRATAMIENTO_SIN_CARGAR = 'Sin especificar'


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo cancelar el turno' },
    { status: 500 },
  )
}


// La MISMA respuesta para tres casos distintos: el turno no existe, ya estaba
// cancelado, o es de otro profesional. Separarlos sería contar de más.
function noSePuedeCancelar(): Response {

  return Response.json(
    { error: 'No se puede cancelar ese turno' },
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
        return Response.json(
          { error: 'Sin acceso al panel' },
          { status: 403 },
        )
      }

      // ── 2. Qué turno ──────────────────────────────────────────────────────

      // `req.json()` es la única línea que puede EXPLOTAR en vez de devolver
      // algo: un cuerpo que no es JSON lanza.
      let cuerpo

      try {
        cuerpo = await req.json()
      }
      catch {
        return Response.json(
          { error: 'El pedido no trae un cuerpo JSON' },
          { status: 400 },
        )
      }

      const turnoId = Number( cuerpo.turno_id )

      if ( !Number.isInteger( turnoId ) ) {
        return Response.json(
          { error: 'Falta turno_id, o no es un número entero' },
          { status: 400 },
        )
      }

      // ── 3. El turno, con todo lo que el aviso va a necesitar ──────────────

      const turno = await ctx.supabaseAdmin
        .from( 'turnos' )
        .select( `
          id,
          inicio,
          duracion_min,
          profesional_id,
          paciente:pacientes!inner ( nombre, apellido, email ),
          profesional:profesionales!inner ( nombre, apellido, email ),
          tratamiento:tratamientos!turnos_tratamiento_id_fkey ( nombre )
        ` )
        .eq( 'id', turnoId )
        .eq( 'activo', true )
        .maybeSingle()

      if ( turno.error ) {
        return falloDeBase()
      }

      if ( !turno.data ) {
        return noSePuedeCancelar()
      }

      // ── 4. ¿Es suyo? ──────────────────────────────────────────────────────
      //
      // 🔴 ESTA ES LA LÍNEA QUE NO SE PUEDE BORRAR. Un admin pasa de largo; un
      // profesional sólo sobre lo suyo. El `id` sale de la cerradura, nunca del
      // pedido: si viniera en el cuerpo, bastaría con escribir el ajeno.
      if ( !quien.esAdmin && turno.data.profesional_id !== quien.id ) {
        return noSePuedeCancelar()
      }

      // ── 5. El apagado ─────────────────────────────────────────────────────
      //
      // 🔴 EL `.eq( 'activo', true )` NO ES UNA COPIA DEL DE ARRIBA. Entre la
      // consulta y esta escritura pasan milisegundos, y en ese hueco entra el
      // segundo clic: los dos pedidos vieron el turno activo. Con la condición
      // puesta, el segundo `update` no encuentra nada que apagar y no sale un
      // segundo lote de correos por el mismo turno.
      const apagado = await ctx.supabaseAdmin
        .from( 'turnos' )
        .update( { activo: false } )
        .eq( 'id', turnoId )
        .eq( 'activo', true )
        .select( 'id' )
        .maybeSingle()

      if ( apagado.error ) {
        return falloDeBase()
      }

      if ( !apagado.data ) {
        return noSePuedeCancelar()
      }

      // ── 6. Los avisos ─────────────────────────────────────────────────────
      //
      // 🔴 LO QUE PASE ACÁ NO CAMBIA LA RESPUESTA: el turno YA está apagado. Si
      // esto devolviera 500, quien canceló lo intentaría de nuevo y recibiría
      // el 403 de arriba, convencido de que no entró — cuando entró.
      //
      // 🔴 Y EL CORREO DEL PACIENTE SALE DE LA FILA, NO DEL TOKEN. Es la
      // diferencia con `/cancelar`, donde los dos son el mismo: acá el que
      // cancela es el consultorio y el que tiene que enterarse es la paciente.
      // Tomado del token, el aviso de «te cancelamos el turno» le llegaría a
      // Cecilia y la paciente se presentaría igual.
      let nombreDelTratamiento = TRATAMIENTO_SIN_CARGAR

      if ( turno.data.tratamiento ) {
        nombreDelTratamiento = turno.data.tratamiento.nombre
      }

      // 🔴 EL CORREO DEL PACIENTE PUEDE SER NULO, y no es un caso raro: en
      // `pacientes` la columna es OPCIONAL a propósito —a diferencia de
      // `profesionales`, donde es obligatoria—, porque Cecilia carga a mano
      // pacientes que sólo dejaron un teléfono.
      //
      // 🔑 EL TURNO SE CANCELA IGUAL. Poder avisar no es condición para
      // cancelar: el horario tiene que quedar libre aunque no haya a quién
      // escribirle. Lo que cambia es la RESPUESTA, que lo dice, para que del
      // otro lado alguien levante el teléfono.
      //
      // ⚠ Lo encontró `deno check` al regenerar los tipos, no una prueba: el
      // código andaba y le habría pasado `null` a la función de avisos.
      const correoDelPaciente = turno.data.paciente.email

      if ( !correoDelPaciente ) {

        return Response.json( {
          cancelado: turno.data.id,
          avisadoAlPaciente: false,
        } )
      }

      await enviarAvisos( {
        turnoId: turno.data.id,
        inicio: turno.data.inicio,
        duracionMin: turno.data.duracion_min,
        tratamiento: nombreDelTratamiento,
        pacienteNombre: turno.data.paciente.nombre,
        pacienteApellido: turno.data.paciente.apellido,
        pacienteCorreo: correoDelPaciente,
        profesionalNombre: turno.data.profesional.nombre,
        profesionalApellido: turno.data.profesional.apellido,
        profesionalCorreo: turno.data.profesional.email,
        tieneObservaciones: false,
      },
      'cancelacion' )

      return Response.json( {
        cancelado: turno.data.id,
        avisadoAlPaciente: true,
      } )
    },
  ),

}
