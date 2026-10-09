// Portero de CB Odontología — endpoint POST /turno-del-panel
//
// Cargar un turno a mano: lo que entra por teléfono, por WhatsApp o en el
// mostrador. Es el endpoint que cierra el hueco más viejo del proyecto — hasta
// hoy, un turno que no pasaba por `POST /reservar` no le avisaba a NADIE.
//
// 🔴 LAS CUATRO DIFERENCIAS CON `reservar`, y ninguna es un detalle:
//
//   1. NO se llama a `conQueArranca( … )`. Esa función convierte el pedido del
//      paciente en «consulta de 30 minutos», y vale para el canal `web` y para
//      nada más. Cecilia agenda la ortodoncia de verdad, que dura 90 o 120:
//      LA DURACIÓN LA ELIGE ELLA.
//
//   2. `canal = 'manual'`, y no es cosmético. El disparador
//      `limitar_turnos_por_paciente` abre con `if new.canal <> 'web' then
//      return new;` — o sea que el límite de un turno por profesional está
//      APAGADO a propósito para el panel. El límite es del FORMULARIO, no del
//      consultorio: Cecilia tiene que poder darle un turno más a quien lo
//      necesite. Si este endpoint se escribiera copiando de `reservar` y
//      quedara en `'web'`, el límite frenaría el flujo que la § 6 da por
//      normal —la endodoncia después de la consulta— con un 409 que parece un
//      bug y no lo es.
//
//   3. NO se valida la pareja profesional-tratamiento. `reservar` sí lo hace,
//      porque ahí elige el paciente y la grilla sólo ofrece lo que existe.
//      Acá elige el consultorio, que es la autoridad sobre quién hace qué: si
//      Cecilia le agenda algo nuevo a un profesional, el sistema no está para
//      discutírselo. Mismo criterio que el punto 2. *Lo que sí se verifica es
//      que el profesional y el tratamiento EXISTAN.*
//
//   4. `confirmado_en` queda VACÍO. Un turno web está confirmado por
//      construcción —lo sacó el paciente—; éste lo cargó un tercero, y hasta
//      que la persona conteste no hay ninguna prueba de que se haya enterado.
//      El flujo para confirmar entra en la ⑤.3.b.
//
// 🔒 EL IDOR DE ESCRITURA, que es el riesgo propio de este endpoint. El cuerpo
// trae `profesional_id`, y si se obedeciera sin preguntar quién pide, un
// profesional cualquiera llenaría la agenda de otro. LA REGLA ES LA MISMA QUE
// EN `agenda-del-dia`: si el que pide no es admin, el campo se IGNORA y el
// turno se crea a su nombre. Sólo Cecilia agenda para terceros.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y
// acá se lo deja prendido.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'

import { enviarAvisos } from '../_shared/avisos.ts'

import {
  LARGO_MAXIMO_OBSERVACIONES,
  textoLimpio,
} from '../_shared/texto.ts'


// El código que devuelve PostgreSQL cuando dos turnos se pisan. Lo pone la
// restricción `turnos_sin_solapar`, no nuestro código.
const CHOQUE_DE_TURNOS = '23P01'

// La duración va en minutos y en bloques de 30, que es la unidad con la que
// piensa el consultorio (§ 6). El tope existe para que un cero de más no
// bloquee la agenda de un día entero.
const DURACION_MINIMA = 30
const DURACION_MAXIMA = 300
const BLOQUE          = 30


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo crear el turno' },
    { status: 500 },
  )
}


function pedidoInvalido( detalle: string ): Response {

  return Response.json(
    { error: detalle },
    { status: 400 },
  )
}


function unNumero( valor: unknown ): number | null {

  const numero = Number( valor )

  if ( !Number.isInteger( numero ) || numero <= 0 ) {
    return null
  }

  return numero
}


export default {

  fetch: withSupabase< Database >(
    { auth: 'user' },
    async ( req, ctx ) => {

      if ( req.method !== 'POST' ) {
        return Response.json(
          { error: 'Este endpoint sólo acepta POST' },
          { status: 405 },
        )
      }

      // ── 1. La cerradura, antes de mirar el cuerpo ─────────────────────────

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

      // ── 2. El cuerpo ──────────────────────────────────────────────────────

      let cuerpo

      try {
        cuerpo = await req.json()
      }
      catch {
        return pedidoInvalido( 'El cuerpo del pedido no es JSON válido' )
      }

      const pacienteId = unNumero( cuerpo.paciente_id )

      if ( !pacienteId ) {
        return pedidoInvalido( 'Falta el paciente' )
      }

      const tratamientoId = unNumero( cuerpo.tratamiento_id )

      if ( !tratamientoId ) {
        return pedidoInvalido( 'Falta el tratamiento' )
      }

      const obraSocialId = unNumero( cuerpo.obra_social_id )

      // La cobertura es `not null` en la base desde el 18-sep-2026. Si no se
      // sabe con qué viene la persona, va `Particular` — eso se decidió
      // sabiendo el costo (§ 9, migración `exigir_obra_social_en_turnos`).
      if ( !obraSocialId ) {
        return pedidoInvalido( 'Falta la cobertura' )
      }

      const duracion = unNumero( cuerpo.duracion_min )

      if (
        !duracion
        || duracion < DURACION_MINIMA
        || duracion > DURACION_MAXIMA
        || duracion % BLOQUE !== 0
      ) {
        return pedidoInvalido(
          `La duración va en bloques de ${ BLOQUE } minutos, `
          + `entre ${ DURACION_MINIMA } y ${ DURACION_MAXIMA }`,
        )
      }

      // El instante del turno llega armado desde la pantalla, con el desfase
      // de Santa Fe puesto. Se valida que sea una fecha que JavaScript
      // entienda: un texto cualquiera acá entraría a la base como error feo.
      const inicioCrudo = cuerpo.inicio

      if (
        typeof inicioCrudo !== 'string'
        || Number.isNaN( Date.parse( inicioCrudo ) )
      ) {
        return pedidoInvalido( 'El inicio no es un instante válido' )
      }

      const inicio = new Date( inicioCrudo ).toISOString()

      let observaciones: string | null = null

      if (
        cuerpo.observaciones_paciente !== undefined
        && cuerpo.observaciones_paciente !== ''
      ) {

        observaciones = textoLimpio(
          cuerpo.observaciones_paciente,
          LARGO_MAXIMO_OBSERVACIONES,
        )

        if ( !observaciones ) {
          return pedidoInvalido( 'La observación es demasiado larga' )
        }
      }

      // ── 3. De quién es el turno ───────────────────────────────────────────
      //
      // Acá se aplica la regla del IDOR de arriba. Para un no-admin, lo que
      // venga en el cuerpo no se mira.

      const pedido = unNumero( cuerpo.profesional_id )

      const profesionalId = quien.esAdmin
        ? ( pedido ?? quien.id )
        : quien.id

      // ── 4. Que las tres filas existan ─────────────────────────────────────
      //
      // Sin esto, un id inventado se estrella contra la foreign key y la
      // respuesta sería un 500 genérico. Preguntando antes, el que se equivocó
      // recibe un 400 que dice QUÉ no existe.

      const [ paciente, profesional, tratamiento ] = await Promise.all( [

        ctx.supabaseAdmin
          .from( 'pacientes' )
          .select( 'id, nombre, apellido, email' )
          .eq( 'id', pacienteId )
          .maybeSingle(),

        ctx.supabaseAdmin
          .from( 'profesionales' )
          .select( 'id, nombre, apellido, email, activo' )
          .eq( 'id', profesionalId )
          .maybeSingle(),

        ctx.supabaseAdmin
          .from( 'tratamientos' )
          .select( 'id, nombre' )
          .eq( 'id', tratamientoId )
          .maybeSingle(),
      ] )

      if ( paciente.error || profesional.error || tratamiento.error ) {
        return falloDeBase()
      }

      if ( !paciente.data ) {
        return pedidoInvalido( 'Ese paciente no existe' )
      }

      if ( !profesional.data || !profesional.data.activo ) {
        return pedidoInvalido(
          'Ese profesional no existe o está dado de baja',
        )
      }

      if ( !tratamiento.data ) {
        return pedidoInvalido( 'Ese tratamiento no existe' )
      }

      // La cobertura se lee aparte porque su nombre viaja en el correo, y lo
      // que viaja es el de la TABLA, nunca un texto que haya mandado nadie.
      const obraSocial = await ctx.supabaseAdmin
        .from( 'obras_sociales' )
        .select( 'id, nombre, activa' )
        .eq( 'id', obraSocialId )
        .maybeSingle()

      if ( obraSocial.error ) {
        return falloDeBase()
      }

      if ( !obraSocial.data || !obraSocial.data.activa ) {
        return pedidoInvalido( 'Esa cobertura no existe o ya no está vigente' )
      }

      // ── 5. El turno ───────────────────────────────────────────────────────

      const turno = await ctx.supabaseAdmin
        .from( 'turnos' )
        .insert( {
          paciente_id: pacienteId,
          profesional_id: profesionalId,
          tratamiento_id: tratamientoId,
          // 🔑 VACÍO A PROPÓSITO, y es la regla sin excepciones de `reservar`
          // leída al revés: `motivo_consulta_id` guarda lo que ELIGIÓ el
          // paciente. Acá no eligió el paciente, así que el vacío dice la
          // verdad — «no eligió nadie», o sea un turno del consultorio.
          motivo_consulta_id: null,
          inicio: inicio,
          duracion_min: duracion,
          obra_social_id: obraSocialId,
          canal: 'manual',
          activo: true,
          observaciones_paciente: observaciones,
        } )
        .select( 'id, inicio, duracion_min' )
        .single()

      if ( turno.error ) {

        // La base hace de árbitro: dos turnos no pueden pisarse. No es una
        // falla del sistema, es el sistema funcionando, y por eso se contesta
        // 409 y no 500 — nadie se equivocó de código.
        if ( turno.error.code === CHOQUE_DE_TURNOS ) {
          return Response.json(
            { error: 'Ese horario se pisa con otro turno' },
            { status: 409 },
          )
        }

        return falloDeBase()
      }

      // ── 6. Los avisos ─────────────────────────────────────────────────────
      //
      // ⚠ UN PACIENTE SIN CORREO ES UN CASO REAL: `pacientes.email` acepta
      // nulo porque Cecilia carga gente que sólo dejó un teléfono. El turno se
      // crea IGUAL —poder avisar no es condición para agendar— y la respuesta
      // lo dice, para que del otro lado alguien levante el teléfono.
      //
      // ⬜ HUECO CONOCIDO, y se escribe en vez de taparse a medias: en ese
      // caso tampoco sale el aviso OPERATIVO, así que un profesional que no
      // sea Cecilia no se entera del turno que le cargaron. `enviarAvisos`
      // pide el correo del paciente como obligatorio y partirlo en dos
      // caminos es una etapa propia. `cancelar-del-panel` tiene exactamente el
      // mismo hueco: se arreglan juntos o quedan dos comportamientos.

      const correoDelPaciente = paciente.data.email

      let avisado = false

      if ( correoDelPaciente ) {

        avisado = await enviarAvisos( {
          turnoId: turno.data.id,
          inicio: turno.data.inicio,
          duracionMin: turno.data.duracion_min,
          tratamiento: tratamiento.data.nombre,
          canal: 'manual',
          obraSocial: obraSocial.data.nombre,
          pacienteNombre: paciente.data.nombre,
          pacienteApellido: paciente.data.apellido,
          pacienteCorreo: correoDelPaciente,
          profesionalNombre: profesional.data.nombre,
          profesionalApellido: profesional.data.apellido,
          profesionalCorreo: profesional.data.email,
          tieneObservaciones: observaciones !== null,
        },
        'reserva' )
      }

      // 🔴 LA MARCA VA DESPUÉS DEL ENVÍO Y CONDICIONADA A QUE HAYA SALIDO.
      // `aviso_estado` no dice qué ES el turno —eso lo dice `activo`—: dice lo
      // último que el paciente SABE de él. Marcarlo sin que el correo hubiera
      // salido sería anotar una mentira, y la repesca pasaría de largo justo
      // sobre el único que no se enteró.
      if ( avisado ) {

        await ctx.supabaseAdmin
          .from( 'turnos' )
          .update( {
            aviso_estado: 'reservado',
            aviso_at: new Date().toISOString(),
            inicio_avisado: turno.data.inicio,
          } )
          .eq( 'id', turno.data.id )
      }

      return Response.json(
        {
          id: turno.data.id,
          inicio: turno.data.inicio,
          duracion_min: turno.data.duracion_min,
          profesional: profesionalId,
          avisadoAlPaciente: avisado,
        },
        { status: 201 },
      )
    },
  ),

}
