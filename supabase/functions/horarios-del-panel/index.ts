// Portero de CB Odontología — endpoint GET /horarios-del-panel
//
//   ?profesional=1&fecha=2026-10-15&duracion=90&excepto=428
//
// `excepto` es opcional y lo manda SÓLO la pantalla de mover: dice qué turno no
// cuenta como ocupado. Ver el bloque 2.b de abajo.
//
// La misma grilla que ve el paciente, con las reglas del CONSULTORIO.
//
// 🔴 POR QUÉ NO ES `GET /horarios-disponibles` CON UN PARÁMETRO MÁS. Aquél
// aplica cuatro reglas que son del FORMULARIO y no del consultorio, y las
// cuatro están mal acá:
//
//   1. La duración la DEDUCE del tratamiento (`duracion_web_min`). Acá la
//      elige quien atiende: la ortodoncia de verdad dura 90 o 120, no los 30
//      de la consulta en que la web la convierte.
//   2. Piso de DOCE HORAS de anticipación. Cecilia tiene que poder agendar
//      para esta tarde — el piso existe para que un paciente no saque un
//      turno para dentro de veinte minutos.
//   3. Rechaza si el profesional no hace ese tratamiento. En el panel el
//      consultorio es la autoridad sobre quién hace qué.
//   4. Techo de dos meses. Un control se agenda a seis.
//
// Meterle un `modo=panel` a aquel endpoint habría sido más corto y es peor:
// es el camino crítico del paciente, y un `if` mal puesto cambia en silencio
// lo que ve quien reserva. **El cálculo sí se comparte** — vive en
// `_shared/grilla.ts` y lo llaman los dos.
//
// 🔑 ESTE DEVUELVE UN SOLO DÍA, no un rango, y es a propósito: el panel está
// organizado por día de punta a punta —la agenda se navega así— y quien
// atiende ya sabe qué día quiere. Lo que no sabe es QUÉ ENTRA ese día.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y
// acá se lo deja prendido.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'

import { armarLaGrilla } from '../_shared/grilla.ts'

import { esFechaValida } from '../_shared/disponibilidad.ts'


// Los mismos topes que valida `turno-del-panel`. Están escritos en los dos
// lados a propósito: la grilla se dibuja con lo que se pida, y pedir una
// duración absurda armaría una grilla absurda en vez de rebotar.
const DURACION_MINIMA = 30
const DURACION_MAXIMA = 300
const BLOQUE          = 30


function pedidoInvalido( mensaje: string ): Response {

  return Response.json(
    { error: mensaje },
    { status: 400 },
  )
}


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

      // ── 2. El pedido ──────────────────────────────────────────────────────

      const url = new URL( req.url )

      const fecha = url.searchParams.get( 'fecha' )

      if ( !fecha || !esFechaValida( fecha ) ) {
        return pedidoInvalido( 'Falta la fecha, o no tiene la forma AAAA-MM-DD' )
      }

      const duracion = Number( url.searchParams.get( 'duracion' ) )

      if (
        !Number.isInteger( duracion )
        || duracion < DURACION_MINIMA
        || duracion > DURACION_MAXIMA
        || duracion % BLOQUE !== 0
      ) {
        return pedidoInvalido(
          `La duración va en bloques de ${ BLOQUE } minutos, `
          + `entre ${ DURACION_MINIMA } y ${ DURACION_MAXIMA }`,
        )
      }

      // 🔒 LA MISMA REGLA DE IDOR QUE EL RESTO DEL PANEL: si quien pide no es
      // admin, el parámetro se IGNORA y la grilla es la suya. Sin esto, un
      // profesional cualquiera leería la agenda libre y ocupada de otro — que
      // es exactamente lo que `horarios-disponibles` dejó de publicar el
      // 24-sep cuando se le puso sesión.
      // 🔴 EL PEDIDO SE GUARDA CRUDO ANTES DE CONVERTIRLO, y lo que lo
      // justifica es un bug medido el 13-oct-2026 en `turnos-del-profesional`
      // —el caso 24 de la batería— que estaba igual acá:
      //
      // `searchParams.get( … )` devuelve `null` cuando el parámetro no vino, y
      // `Number( null )` NO da NaN: DA CERO. Un `Number.isInteger( … )` solo
      // contesta `true`, así que un ADMIN que llamaba sin `?profesional=`
      // armaba la grilla del profesional 0 —que no existe— y recibía una
      // agenda vacía en lugar de la suya. El código pretendía caer en
      // `quien.id` y no caía.
      //
      // ⚠ NO ERA UN AGUJERO DE PERMISOS: un no-admin caía igual en su propio
      // id, porque lo tapa el `quien.esAdmin` de abajo. Lo que hacía era
      // contestarle mal al admin, sin dar error.
      //
      // 🔑 Y EL ORDEN DE ABAJO ES EL ARREGLO, no un cambio de estilo: la
      // variable ARRANCA en la agenda propia y sólo se mueve si el pedido pasa
      // las tres condiciones. Un valor raro no desvía nada: cae en el default,
      // que es el seguro.
      const crudo = url.searchParams.get( 'profesional' )

      const pedido = Number( crudo )

      let profesionalId = quien.id

      if (
        quien.esAdmin
        && crudo
        && Number.isInteger( pedido )
        && pedido >= 1
      ) {
        profesionalId = pedido
      }

      // ── 2.b El turno que no cuenta como ocupado ───────────────────────────
      //
      // 🔑 LO MANDA LA PANTALLA DE MOVER, y sin él esa pantalla no sirve: el
      // turno que se está moviendo es uno de los turnos activos del
      // profesional, así que se tapa a sí mismo. Dejarlo a la misma hora con
      // otra duración —el caso más común— no se podría ni elegir.
      //
      // ⚠ NO ES UN HUECO DE PERMISOS, y conviene tenerlo medido para no
      // volver a razonarlo: lo único que este parámetro puede hacer es dejar de
      // contar un turno DEL MISMO PROFESIONAL cuya agenda quien pide ya tiene
      // derecho a ver —la consulta filtra por `profesional_id` antes—, así que
      // el id de un turno ajeno no saca nada de la lista. Y si alguien destapa
      // un bloque que en realidad está tomado, el movimiento lo rebota el
      // constraint de la base con 409. No hay information disclosure
      // (divulgación de información) ni permiso ganado por acá.
      //
      // Un valor que no sea un número entero ≥ 1 se ignora: el default es NO
      // excluir nada, que es el seguro.
      const exceptoCrudo = Number( url.searchParams.get( 'excepto' ) )

      const excepto = Number.isInteger( exceptoCrudo ) && exceptoCrudo >= 1
        ? exceptoCrudo
        : undefined

      // ── 3. La grilla ──────────────────────────────────────────────────────

      const dias = await armarLaGrilla( ctx, {
        profesionalId: profesionalId,
        duracionMin: duracion,
        desde: fecha,
        hasta: fecha,
        ahora: new Date(),

        // Acá está la diferencia con el canal del paciente, en una línea.
        conPisoDeHoras: false,

        exceptoTurnoId: excepto,
      } )

      if ( dias === 'error-de-base' ) {
        return falloDeBase()
      }

      // El día sin agenda viaja igual, con la lista vacía: así la pantalla
      // distingue «ese día no se atiende» de «ese día no vino en la
      // respuesta».
      return Response.json( {
        fecha: fecha,
        profesional: profesionalId,
        duracion_min: duracion,
        bloques: dias[ 0 ] ? dias[ 0 ].bloques : [],
      } )
    },
  ),

}
