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
      const turnos = await ctx.supabaseAdmin
        .from( 'turnos' )
        .select( `
          id,
          inicio,
          duracion_min,
          paciente:pacientes!inner ( id, nombre, apellido ),
          profesional:profesionales ( nombre, apellido ),
          tratamiento:tratamientos ( nombre )
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

      // La lista vacía es una respuesta válida, no un error: es el paciente que
      // no tiene turnos. La pantalla que la reciba dice "no tenés turnos
      // activos" y —esto lo pidió el caso de las dos cuentas de Google—
      // pregunta si no habrá reservado con otra casilla.
      return Response.json( turnos.data )
    },
  ),

}
