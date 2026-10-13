// Portero de CB Odontología — endpoint POST /mover-turno
//
// Cambia a qué hora es un turno y cuánto dura. La otra mitad de la ⑤.4; la
// primera —cancelar— ya estaba.
//
// 🔴 EL CHEQUEO QUE JUSTIFICA ESTE ARCHIVO es el mismo de `cancelar-del-panel`
// y de ahí se copió: un profesional gestiona los turnos de SU agenda y nada
// más. Sin comparar `turnos.profesional_id` contra el `id` que devuelve
// `quien-pide.ts`, cualquier profesional con sesión válida le mueve el turno a
// otro mandando un id que no es suyo — y el paciente se entera por el correo,
// que sale igual.
//
// 🔑 EL CORREO DE «TE CAMBIAMOS LA HORA» YA EXISTE Y NO SE ESCRIBE ACÁ, que es
// lo que hizo esta etapa mucho más corta de lo estimado. `avisos.ts` decide
// qué clase de aviso es comparando `inicioAvisado` contra `inicio`: cuando
// difieren devuelve 'hora-nueva' y arma un correo con su propio asunto y un
// texto que AFIRMA el cambio en vez de preguntarlo. Lo montó la repesca el
// 29-ago; acá sólo se le pasa la hora vieja.
//
// 🔴 POR ESO `inicio_avisado` NO SE TOCA ANTES DE ENVIAR. Esa columna guarda
// qué hora sabe el paciente, no qué hora es el turno. Si se actualizara junto
// con `inicio`, las dos coincidirían, `avisos.ts` leería 'datos-nuevos' y
// saldría un correo que no nombra el cambio — la paciente leería un turno
// nuevo y se presentaría al viejo. Es el bug exacto que Juan levantó el
// 28-ago-2026 leyendo los correos en fila.
//
// ⚠ LO QUE ESTE ENDPOINT NO PUEDE HACER, y lo garantiza la base: cambiar de
// paciente, de profesional, de tratamiento o de cobertura. La migración
// `permitir_mover_turnos` da `update` sobre `inicio` y `duracion_min` Y NADA
// MÁS, así que un error acá no puede terminar pasándole el turno a otra
// persona.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y
// acá se lo deja prendido.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { enviarAvisos } from '../_shared/avisos.ts'

import { quienPide } from '../_shared/quien-pide.ts'

import { duracionValida, porQueNoVale } from '../_shared/duracion.ts'


// Lo que Postgres contesta cuando la fila nueva se pisa con otra. Sólo lo
// puede producir `turnos_sin_solapar`: no hay otra restricción de ese tipo.
const CHOQUE_DE_TURNOS = '23P01'


const TRATAMIENTO_SIN_CARGAR = 'Sin especificar'


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo mover el turno' },
    { status: 500 },
  )
}


// La MISMA respuesta para tres casos: el turno no existe, ya estaba cancelado,
// o es de otro profesional. Separarlos sería contar de más.
function noSePuedeMover(): Response {

  return Response.json(
    { error: 'No se puede mover ese turno' },
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

      // ── 2. El pedido ──────────────────────────────────────────────────────

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

      if ( !Number.isInteger( turnoId ) || turnoId < 1 ) {
        return Response.json(
          { error: 'Falta turno_id, o no es un número entero válido' },
          { status: 400 },
        )
      }

      const duracion = Number( cuerpo.duracion_min )

      if ( !duracionValida( duracion ) ) {
        return Response.json(
          { error: porQueNoVale() },
          { status: 400 },
        )
      }

      // El instante llega armado desde la pantalla, con el desfase de Santa Fe
      // puesto — igual que en `turno-del-panel`. Se valida que JavaScript lo
      // entienda: un texto cualquiera entraría a la base como error feo.
      const inicioCrudo = cuerpo.inicio

      if ( typeof inicioCrudo !== 'string' || !inicioCrudo ) {
        return Response.json(
          { error: 'Falta el inicio' },
          { status: 400 },
        )
      }

      const cuando = new Date( inicioCrudo )

      if ( Number.isNaN( cuando.getTime() ) ) {
        return Response.json(
          { error: 'El inicio no es una fecha válida' },
          { status: 400 },
        )
      }

      const inicioNuevo = cuando.toISOString()

      // ── 3. El turno, con todo lo que el aviso va a necesitar ──────────────

      const turno = await ctx.supabaseAdmin
        .from( 'turnos' )
        .select( `
          id,
          inicio,
          inicio_avisado,
          duracion_min,
          canal,
          profesional_id,
          paciente:pacientes!inner ( nombre, apellido, email ),
          profesional:profesionales!inner ( nombre, apellido, email ),
          tratamiento:tratamientos!turnos_tratamiento_id_fkey ( nombre ),
          obra_social:obras_sociales!inner ( nombre )
        ` )
        .eq( 'id', turnoId )
        .eq( 'activo', true )
        .maybeSingle()

      if ( turno.error ) {
        return falloDeBase()
      }

      if ( !turno.data ) {
        return noSePuedeMover()
      }

      // ── 4. ¿Es suyo? ──────────────────────────────────────────────────────
      //
      // 🔴 ESTA ES LA LÍNEA QUE NO SE PUEDE BORRAR, y es la misma de
      // `cancelar-del-panel`. Un admin pasa de largo; un profesional sólo sobre
      // lo suyo. El `id` sale de la cerradura, nunca del pedido.
      if ( !quien.esAdmin && turno.data.profesional_id !== quien.id ) {
        return noSePuedeMover()
      }

      // 🔑 LA HORA QUE EL PACIENTE SABE, GUARDADA ANTES DE ESCRIBIR. Después
      // del `update` ya no se puede leer de ningún lado, y es lo que hace que
      // el correo pueda decir que el turno cambió.
      const horaQueSabia = turno.data.inicio_avisado

      // ── 5. El movimiento ──────────────────────────────────────────────────
      //
      // 🔴 EL `.eq( 'activo', true )` NO ES UNA COPIA DEL FILTRO DE ARRIBA:
      // entre la consulta y esta escritura entra el clic de alguien que lo
      // cancela. Con la condición puesta, el `update` no encuentra nada que
      // mover y no sale un correo de cambio por un turno ya cancelado.
      const movido = await ctx.supabaseAdmin
        .from( 'turnos' )
        .update( {
          inicio: inicioNuevo,
          duracion_min: duracion,
        } )
        .eq( 'id', turnoId )
        .eq( 'activo', true )
        .select( 'id, inicio, duracion_min' )
        .maybeSingle()

      if ( movido.error ) {

        // 🔑 EL CHOQUE NO ES UN ERROR DEL SISTEMA: es la defensa funcionando.
        // Ese horario ya está ocupado, y quien lo intentó no se equivocó en
        // nada — se contesta 409, igual que la doble reserva de la web, con un
        // `codigo` para que la pantalla pueda decirlo con sus palabras.
        if ( movido.error.code === CHOQUE_DE_TURNOS ) {

          return Response.json(
            {
              error: 'Ese horario se pisa con otro turno',
              codigo: 'HORARIO_OCUPADO',
            },
            { status: 409 },
          )
        }

        console.error( 'No se pudo mover el turno:', movido.error )

        return falloDeBase()
      }

      if ( !movido.data ) {
        return noSePuedeMover()
      }

      // ── 6. El aviso ───────────────────────────────────────────────────────
      //
      // 🔴 LO QUE PASE ACÁ NO CAMBIA LA RESPUESTA: el turno YA se movió. Si
      // esto devolviera 500, quien lo movió lo intentaría de nuevo y chocaría
      // contra su propio turno nuevo con un 409, convencido de que no entró.
      let nombreDelTratamiento = TRATAMIENTO_SIN_CARGAR

      if ( turno.data.tratamiento ) {
        nombreDelTratamiento = turno.data.tratamiento.nombre
      }

      const correoDelPaciente = turno.data.paciente.email

      // El correo del paciente puede ser nulo: Cecilia carga a mano gente que
      // sólo dejó un teléfono. El turno se mueve igual —el horario tiene que
      // quedar como ella decidió— y lo que cambia es la RESPUESTA, que lo dice
      // para que del otro lado alguien levante el teléfono.
      if ( !correoDelPaciente ) {

        return Response.json( {
          movido: movido.data.id,
          inicio: movido.data.inicio,
          avisadoAlPaciente: false,
        } )
      }

      const salieron = await enviarAvisos( {
        turnoId: turno.data.id,
        inicio: inicioNuevo,
        duracionMin: duracion,
        canal: turno.data.canal,
        tratamiento: nombreDelTratamiento,

        // 🔑 ACÁ ESTÁ TODA LA PIEZA: se le pasa la hora que el paciente sabía,
        // no la nueva. `avisos.ts` las compara y, al verlas distintas, arma el
        // correo que dice que el turno cambió.
        inicioAvisado: horaQueSabia,

        pacienteNombre: turno.data.paciente.nombre,
        pacienteApellido: turno.data.paciente.apellido,
        pacienteCorreo: correoDelPaciente,
        profesionalNombre: turno.data.profesional.nombre,
        profesionalApellido: turno.data.profesional.apellido,
        profesionalCorreo: turno.data.profesional.email,
        obraSocial: turno.data.obra_social.nombre,
        tieneObservaciones: false,
      },
      'reserva' )

      // ── 7. La marca ───────────────────────────────────────────────────────
      //
      // Va DESPUÉS del envío y condicionada a que haya salido, igual que en
      // `reservar`: si el correo no salió, el paciente sigue sabiendo la hora
      // vieja, y la columna tiene que seguir diciendo eso. Así la repesca lo
      // encuentra y vuelve a intentar.
      if ( salieron ) {

        await ctx.supabaseAdmin
          .from( 'turnos' )
          .update( {
            aviso_estado: 'reservado',
            aviso_at: new Date().toISOString(),
            inicio_avisado: inicioNuevo,
          } )
          .eq( 'id', turnoId )
      }

      return Response.json( {
        movido: movido.data.id,
        inicio: movido.data.inicio,
        avisadoAlPaciente: salieron,
      } )
    },
  ),

}
