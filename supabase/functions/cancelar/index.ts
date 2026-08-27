// Portero de CB Odontología — endpoint POST /cancelar
//
// EL SEGUNDO QUE ESCRIBE, y el primero que MODIFICA algo que ya estaba. No
// borra la fila: le apaga el `activo`. En este proyecto nada se borra (§ 6 del
// documento de estado), porque el turno cancelado sigue siendo historia del
// consultorio.
//
// 🔒 EXIGE SESIÓN INICIADA, igual que `/reservar` y `/mis-turnos`, y por eso
// tampoco lleva bloque en `config.toml`: la plataforma pide un JWT válido por
// defecto y acá no se lo apaga. El correo sale del token; del cuerpo del pedido
// viene UN SOLO dato, el número de turno.
//
// LO QUE HACE, en orden:
//   1. mira quién es (el token)
//   2. busca el turno con TODAS las condiciones en una sola consulta
//   3. lo apaga
//   4. avisa a los tres, y el aviso no puede cambiar la respuesta
//
// 🔴 EL `update` DE ESTA FUNCIÓN SÓLO PUEDE ESCRIBIR `activo`. La migración 22
// dio `grant update ( activo ) on turnos to service_role` — una columna, no la
// tabla. Si alguien agrega acá otra columna al `update`, Postgres lo frena con
// un `42501` ruidoso. Es a propósito: es una defensa que NO depende de que este
// código esté bien escrito.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { enviarAvisos } from '../_shared/avisos.ts'

// Cuando el turno no tiene tratamiento asignado —uno que Cecilia cargó a mano—
// el correo tiene que decir algo igual. `tratamiento_id` es la única de las tres
// tablas emparentadas que puede venir vacía.
const TRATAMIENTO_SIN_CARGAR = 'Sin especificar'

// Un pedido mal armado se contesta con el motivo: lo escribió quien está
// construyendo la pantalla y necesita saber qué corregir.
function pedidoInvalido( mensaje: string ): Response {

  return Response.json(
    { error: mensaje },
    { status: 400 },
  )
}

// Un fallo de la base se contesta SIN el detalle: el texto de Postgres nombra
// tablas, columnas y roles, y esto lo ve cualquiera.
function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo cancelar el turno' },
    { status: 500 },
  )
}

// 🔒 LA RESPUESTA ÚNICA PARA LAS CUATRO FORMAS DE FALLAR: que el turno no
// exista, que exista y sea de otro paciente, que ya esté cancelado, y que ya
// haya pasado. Tienen que ser INDISTINGUIBLES —mismo número y mismo texto—, y
// el motivo es el mismo que en `reservar` con `paciente_id`: si contestaran
// distinto, cualquiera con una sesión válida manda `turno_id` 1, 2, 3… y el
// código de respuesta le va dibujando la agenda del consultorio. No ve los
// nombres, pero sabe qué números existen y cuáles están activos. Eso es
// ENUMERACIÓN (enumeration).
//
// 🔴 EL COSTO, ACEPTADO A CONCIENCIA: un doble clic del paciente contesta lo
// mismo que un id ajeno. La segunda cancelación no encuentra el turno activo y
// recibe este 403. Es peor mensaje para el que se equivoca de buena fe, y es el
// precio de no tener cuatro respuestas que un desconocido pueda leer.
//
// Va en 403 y no en 404 porque acá hay sesión: la respuesta honesta es "estás
// identificado y esto no te corresponde". Un 404 afirmaría "eso no existe", que
// en tres de los cuatro casos es mentira.
function noSePuedeCancelar(): Response {

  return Response.json(
    { error: 'Ese turno no se puede cancelar' },
    { status: 403 },
  )
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

      // ── Quién pide ────────────────────────────────────────────────────────
      //
      // `userClaims` son los datos de adentro del token, ya verificados por la
      // librería contra las claves del proyecto. No es lo que el cliente dice
      // ser: es lo que el sistema de cuentas firmó.
      const correo = ctx.userClaims?.email

      if ( !correo ) {
        return Response.json(
          { error: 'Sesión no válida' },
          { status: 403 },
        )
      }

      // ── El cuerpo del pedido ──────────────────────────────────────────────
      //
      // `req.json()` es la única línea del archivo que puede EXPLOTAR en vez de
      // devolver un error: si el cuerpo no es JSON, lanza. Por eso va adentro
      // de un `try`.
      let cuerpo: Record< string, unknown >

      try {
        cuerpo = await req.json()
      }
      catch {
        return pedidoInvalido( 'El cuerpo del pedido no es JSON válido' )
      }

      if ( !cuerpo || typeof cuerpo !== 'object' ) {
        return pedidoInvalido( 'El cuerpo del pedido tiene que ser un objeto' )
      }

      const turnoId = Number( cuerpo.turno_id )

      // Esto es lo ÚNICO que se contesta distinto, y no filtra nada: "mandaste
      // una letra donde va un número" no dice nada sobre qué turnos existen.
      if ( !Number.isInteger( turnoId ) ) {
        return pedidoInvalido( 'turno_id tiene que ser un número' )
      }

      // El reloj se mira UNA vez y el instante viaja de ahí en más, igual que
      // en `horarios-disponibles`, en `reservar` y en `mis-turnos`.
      const ahora = new Date().toISOString()

      // ── ¿Existe un turno que este paciente pueda cancelar? ────────────────
      //
      // 🔒 LAS CUATRO CONDICIONES VAN EN LA MISMA CONSULTA, Y ESO *ES* LA
      // DEFENSA. Preguntando de a una —¿existe? ¿es tuyo? ¿está activo? ¿ya
      // pasó?— habría cuatro respuestas distintas que un desconocido puede
      // distinguir. Preguntando las cuatro juntas, la fila aparece o no
      // aparece, y el que pide no puede saber cuál falló.
      //
      // `pacientes!inner` es lo que convierte al correo en FILTRO en vez de en
      // dato adjunto. Sin él la consulta sigue contestando, pero devuelve el
      // turno de cualquiera con el paciente en `null` — y este endpoint lo
      // cancelaría. Es el mismo `!inner` de `/mis-turnos`, y acá el precio de
      // olvidarlo no es leer de más: es APAGAR EL TURNO DE OTRO.
      //
      // Los otros dos van SIN `!inner` a propósito: `tratamiento_id` puede
      // estar vacío, y con `!inner` ese turno no volvería — el paciente no
      // podría cancelar un turno que existe.
      // ⚠ `!turnos_tratamiento_id_fkey` NO ES ADORNO Y NO SE PUEDE ACORTAR.
      // Desde la migración 20260827135537, `turnos` tiene DOS referencias a
      // `tratamientos` —`tratamiento_id` y `motivo_consulta_id`—, así que
      // `tratamientos ( nombre )` a secas es ambiguo: PostgREST no sabe cuál de
      // las dos seguir y corta con un error. El `!` nombra la relación por su
      // constraint. Falla ruidoso, no en silencio, pero falla.
      const turno = await ctx.supabaseAdmin
        .from( 'turnos' )
        .select( `
          id,
          inicio,
          duracion_min,
          paciente:pacientes!inner ( nombre, apellido ),
          profesional:profesionales ( nombre, apellido, email ),
          tratamiento:tratamientos!turnos_tratamiento_id_fkey ( nombre )
        ` )
        .eq( 'id', turnoId )
        .eq( 'activo', true )
        .eq( 'pacientes.email', correo )
        .gte( 'inicio', ahora )
        .maybeSingle()

      if ( turno.error ) {
        return falloDeBase()
      }

      if ( !turno.data ) {
        return noSePuedeCancelar()
      }

      // ── El apagado ────────────────────────────────────────────────────────
      //
      // 🔴 EL `.eq( 'activo', true )` DE ACÁ NO ES UNA COPIA DE ARRIBA, y es la
      // línea más fácil de borrar por "redundante". Entre la consulta y esta
      // escritura pasan milisegundos, y en ese hueco puede entrar el segundo
      // clic del mismo paciente: los dos pedidos vieron el turno activo. Con la
      // condición puesta, el segundo `update` no encuentra nada que apagar y
      // `apagado.data` viene vacío, así que no se manda un segundo lote de
      // correos de cancelación por el mismo turno.
      //
      // Es el mismo razonamiento que el 409 de `reservar`: mirar y escribir son
      // dos momentos distintos, y la condición tiene que viajar hasta la
      // escritura.
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

      // ── Los avisos ────────────────────────────────────────────────────────
      //
      // 🔴 LO QUE PASE ACÁ NO CAMBIA LA RESPUESTA. El turno YA está apagado. Si
      // esto devolviera 500, el paciente cancelaría de nuevo y recibiría el 403
      // de arriba, convencido de que la cancelación no entró — cuando entró.
      //
      // `enviarAvisos` no lanza nunca, así que no lleva `try`: ya trae el suyo.
      let nombreDelTratamiento = TRATAMIENTO_SIN_CARGAR

      if ( turno.data.tratamiento ) {
        nombreDelTratamiento = turno.data.tratamiento.nombre
      }

      await enviarAvisos( {
        turnoId: turno.data.id,
        inicio: turno.data.inicio,
        duracionMin: turno.data.duracion_min,
        tratamiento: nombreDelTratamiento,
        pacienteNombre: turno.data.paciente.nombre,
        pacienteApellido: turno.data.paciente.apellido,
        pacienteCorreo: correo,
        profesionalNombre: turno.data.profesional.nombre,
        profesionalApellido: turno.data.profesional.apellido,
        profesionalCorreo: turno.data.profesional.email,
        tieneObservaciones: false,
      },
      'cancelacion' )

      // Lo mínimo. El turno cancelado no vuelve con sus datos: el que canceló
      // ya los tenía en pantalla, y `GET /mis-turnos` es el que manda sobre qué
      // le queda.
      return Response.json(
        {
          id: apagado.data.id,
          cancelado: true,
        },
        { status: 200 },
      )
    },
  ),

}
