// Portero de CB Odontología — endpoint GET /mis-turnos
//
// La pantalla desde la que el paciente cancela. Contesta una sola pregunta:
// ¿qué turnos por venir tiene el que está conectado?
//
// 🔒 EXIGE SESIÓN INICIADA, igual que `/mis-pacientes`, y por eso tampoco lleva
// bloque en `config.toml`: la plataforma pide un JWT válido por defecto y acá no
// se lo apaga. Agregarle ese bloque sería abrir la puerta, no configurarla.
//
// 🔒 Y EL CORREO NO VIAJA EN EL PEDIDO: sale del token de la sesión. Si el
// pedido lo trajera, cualquiera escribiría el ajeno y leería sus turnos.
//
// ⚠ UN CORREO PUEDE TENER VARIOS PACIENTES (§ 9.8): una madre anota a sus hijos
// con su casilla. No es un caso borde, es el caso normal, y por eso cada turno
// viaja CON EL NOMBRE de a quién pertenece. La pantalla lo muestra en cada
// renglón y lo repite en la confirmación de cancelar — decidido el 25-ago-2026,
// para que nadie cancele el turno del hijo creyendo que cancela el suyo.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

// Un fallo de la base se contesta SIN el detalle: el texto de Postgres nombra
// tablas, columnas y roles, y esto lo ve cualquiera.
function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudieron leer los turnos' },
    { status: 500 },
  )
}

export default {

  fetch: withSupabase< Database >(
    { auth: 'user' },
    async ( _req, ctx ) => {

      // La identidad sale del token, ya verificado por la librería contra las
      // claves del proyecto: no es lo que el cliente dice ser, es lo que el
      // sistema de cuentas firmó. Mismo razonamiento que `/mis-pacientes`.
      const correo = ctx.userClaims?.email

      // Mensaje genérico a propósito: un error que describe el estado interno
      // del sistema es divulgación de información (information disclosure).
      if ( !correo ) {
        return Response.json(
          { error: 'Sesión no válida' },
          { status: 403 },
        )
      }

      // El reloj se mira UNA vez y el instante viaja de ahí en más, igual que en
      // `horarios-disponibles` y en `reservar`.
      const ahora = new Date().toISOString()

      // ── La consulta ───────────────────────────────────────────────────────
      //
      // Trae los turnos y, colgado de cada uno, los datos de las tablas con las
      // que ese turno está emparentado. Es UNA sola ida a la base, no cuatro.
      //
      // 🔴 `!inner` NO ES DECORACIÓN: es lo que convierte a `pacientes` de dato
      // adjunto en FILTRO. Sin él, un turno cuyo paciente no coincide con el
      // correo vendría igual, con el paciente en `null`. Con él, ese turno no
      // vuelve. Es la diferencia entre "traeme el turno y de paso su paciente" y
      // "traeme sólo los turnos cuyo paciente cumple esto".
      //
      // Los otros dos van SIN `!inner` a propósito: `tratamiento_id` puede estar
      // vacío —un turno que Cecilia cargó a mano sin tratamiento asignado—, y
      // con `!inner` ese turno desaparecería de la lista. El paciente dejaría de
      // ver un turno que existe, y no fallaría con error.
      // ⚠ `!turnos_tratamiento_id_fkey` NO ES ADORNO Y NO SE PUEDE ACORTAR.
      // Desde la migración 20260827135537, `turnos` tiene DOS referencias a
      // `tratamientos` —`tratamiento_id` y `motivo_consulta_id`—, así que
      // `tratamientos ( nombre )` a secas es ambiguo: PostgREST no sabe cuál de
      // las dos seguir y corta con un error. El `!` nombra la relación por su
      // constraint. Falla ruidoso, no en silencio, pero falla.
      const turnos = await ctx.supabaseAdmin
        .from( 'turnos' )
        .select( `
          id,
          inicio,
          duracion_min,
          paciente:pacientes!inner ( id, nombre, apellido ),
          profesional:profesionales ( nombre, apellido ),
          tratamiento:tratamientos!turnos_tratamiento_id_fkey ( nombre ),
          motivo:tratamientos!turnos_motivo_consulta_id_fkey ( nombre )
        ` )
        .eq( 'pacientes.email', correo )
        .eq( 'activo', true )
        .gte( 'inicio', ahora )
        .order( 'inicio' )

      if ( turnos.error ) {
        return falloDeBase()
      }

      // 🔴 `.gte( 'inicio', ahora )` TAMPOCO ES COSMÉTICO, y conviene decir qué
      // pasa si alguien lo saca "porque total filtra el front":
      //
      //   1. aparecerían los turnos YA ATENDIDOS, que siguen con `activo = true`
      //      —en este proyecto nada se apaga solo al pasar la hora—;
      //   2. y el paciente podría "cancelar" algo que ya ocurrió, dejando la
      //      base diciendo que no pasó.
      //
      // Además la § 6 ya decidió que NO HAY HISTORIAL: el paciente ve lo que
      // tiene por delante, nada más.

      // 🔒 LO QUE NO SALE, y no es un olvido: `observaciones_paciente` puede
      // traer datos de salud y no está en el `select`. Tampoco sale el correo
      // del paciente —es el mismo de la sesión, no agrega nada— ni su DNI, ni su
      // teléfono. Un dato que no sale no se puede filtrar por accidente mañana,
      // cuando alguien arme otra pantalla con esta misma respuesta.

      // 🔴 POR QUÉ EL MOTIVO SÍ SALE ACÁ, si en el correo se decidió que NO.
      // La diferencia no es el dato, es el CANAL: acá es el propio paciente
      // mirando su propio turno con la sesión iniciada, no un mensaje viajando
      // a un buzón que se puede reenviar.
      //
      // Y el problema que resuelve es concreto: el paciente pide ORTODONCIA,
      // el sistema le agenda una CONSULTA de 30, y en su pantalla lee
      // "consulta" a secas. Va a creer que se equivocó y va a reservar de
      // nuevo — dos huecos ocupados por una sola persona.
      //
      // La comparación se hace ACÁ y no en la pantalla, por dos motivos: la
      // regla queda escrita una sola vez, y lo que no difiere ni siquiera sale
      // de la base.
      const conMotivo = turnos.data.map(
        ( turno ) => {

          const seAgenda = turno.tratamiento?.nombre
          const vinoPor = turno.motivo?.nombre

          // Coinciden: el que pidió una limpieza se agendó una limpieza. El
          // motivo se apaga y el turno sale con `motivo: null`, igual que uno
          // que nunca lo tuvo.
          if ( vinoPor === seAgenda ) {
            return {
              ...turno,
              motivo: null,
            }
          }

          return turno
        },
      )

      // La lista vacía es una respuesta válida, no un error: es el paciente que
      // no tiene turnos. La pantalla que la reciba dice "no tenés turnos
      // activos" y —esto lo pidió el caso de las dos cuentas de Google—
      // pregunta si no habrá reservado con otra casilla.
      return Response.json( conMotivo )
    },
  ),

}
