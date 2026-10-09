// Portero de CB Odontología — endpoint GET /horarios-disponibles, PIDE SESIÓN
//
// Contesta una sola pregunta: qué bloques de media hora tiene ese profesional
// en ese rango de fechas.
//
// 🔒 ERA PÚBLICO Y DEJÓ DE SERLO el 24-sep-2026, por decisión de Juan. El
// encabezado decía "el paciente tiene que poder ver si hay turno ANTES de
// registrarse", y eso es lo que se cayó: la agenda de dos meses, servida sin
// sesión, deja reconstruir qué días y horas trabaja cada profesional y cuánto
// hueco libre tiene. Es divulgación de información (information disclosure)
// sin autenticar, y encima anónima.
//
// ⚠ No confundir con lo que el login SÍ da: atribución, no impedimento. Una
// cuenta de Google se crea en dos minutos. Lo que cambia es que el pedido
// tiene nombre y se le puede cortar a uno solo.
//
// ⚠ Son DOS cerraduras y hacen falta las dos: `auth: 'user'` acá abajo, y la
// ausencia de `verify_jwt = false` en `config.toml`. La segunda frena en la
// plataforma; la primera es la que se lee al abrir este archivo.
//
// PASO E de la etapa ②, el último: la grilla descuenta los días que tapan las
// `excepciones` (feriados, cierres, ausencias), marca `ocupado` lo que ya tiene
// turno y aplica la ventana de reserva — piso de 12 horas, techo de dos meses y
// la pregunta de si el tratamiento entra antes del cierre.
//
// Un bloque sale con uno de cuatro estados: `libre`, `ocupado`, `no_entra` (el
// tratamiento no cabe ahí) o `fuera_de_plazo` (falta menos que el margen de
// anticipación). La pantalla pinta los dos últimos con el mismo gris; el
// endpoint los distingue igual, porque distinguir cuesta cero y mezclar es
// irreversible.
//
// Nada de lo que sale de acá viene de `turnos`: son horas y un estado. Quién
// reservó qué no se publica.

import { withSupabase } from 'npm:@supabase/server@^1'

// Los tipos de la base entran por acá. No cambian NADA de lo que el endpoint
// hace: son para que TypeScript sepa qué columnas existen y avise en el editor
// cuando una consulta pide algo que no está.

import type { Database } from '../_shared/tipos-de-la-base.ts'

import {
  esFechaValida,
  listarDias,
  sumarMeses,
  fechaEnSantaFe,
  MESES_DE_HORIZONTE,
} from '../_shared/disponibilidad.ts'

import { estadoDeLaPareja } from '../_shared/parejas.ts'

import { conQueArranca } from '../_shared/arranque.ts'

import { armarLaGrilla } from '../_shared/grilla.ts'

// Techo de días por pedido. Dos meses de calendario más un resto, que es el
// horizonte máximo de reserva que fijó el consultorio. No es una regla de
// negocio: es un tope para que un pedido de diez años no ponga a la función a
// armar bloques hasta que se acabe el tiempo de ejecución.
const DIAS_MAXIMOS_POR_PEDIDO = 62

// Un pedido mal armado se contesta con el motivo: lo escribió quien está
// construyendo la pantalla y necesita saber qué corregir.
function pedidoInvalido( mensaje: string ): Response {

  return Response.json(
    { error: mensaje },
    { status: 400 },
  )
}

// Un fallo de la base se contesta SIN el detalle. El texto de Postgres nombra
// tablas, columnas y roles, y esto lo ve cualquiera.
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

      const url = new URL( req.url )

      const profesionalPedido = url.searchParams.get( 'profesional' )
      const tratamientoPedido = url.searchParams.get( 'tratamiento' )
      const desde = url.searchParams.get( 'desde' )
      const hasta = url.searchParams.get( 'hasta' )

      // ── Lo que se puede rechazar sin preguntarle nada a la base ──────────
      //
      // Se valida TODO del lado del servidor, incluso lo que la pantalla ya
      // va a validar. El navegador corre en la máquina del paciente y
      // cualquiera edita lo que manda: la validación del front es comodidad
      // para el que la usa bien, no una defensa.

      if ( !profesionalPedido || !tratamientoPedido || !desde || !hasta ) {
        return pedidoInvalido(
          'Faltan datos: profesional, tratamiento, desde y hasta',
        )
      }

      const profesionalId = Number( profesionalPedido )
      const tratamientoId = Number( tratamientoPedido )

      if ( !Number.isInteger( profesionalId ) || !Number.isInteger( tratamientoId ) ) {
        return pedidoInvalido( 'profesional y tratamiento tienen que ser números' )
      }

      if ( !esFechaValida( desde ) || !esFechaValida( hasta ) ) {
        return pedidoInvalido( 'Las fechas van en formato AAAA-MM-DD' )
      }

      if ( hasta < desde ) {
        return pedidoInvalido( 'La fecha "hasta" no puede ser anterior a "desde"' )
      }

      const diasPedidos = listarDias( desde, hasta )

      if ( diasPedidos.length > DIAS_MAXIMOS_POR_PEDIDO ) {
        return pedidoInvalido(
          `El rango no puede pasar de ${ DIAS_MAXIMOS_POR_PEDIDO } días`,
        )
      }

      // ── El techo de la ventana de reserva ────────────────────────────────
      //
      // El reloj se mira UNA sola vez y el instante viaja de mano en mano. Si
      // cada bloque preguntara la hora por su cuenta, dos bloques de la misma
      // respuesta podrían quedar calculados con relojes distintos.
      const ahora = new Date()

      const ultimoDiaReservable = sumarMeses(
        fechaEnSantaFe( ahora ),
        MESES_DE_HORIZONTE,
      )

      // Los días de más NO viajan, ni siquiera vacíos: el calendario no llega
      // hasta ahí. Es distinto de un día cerrado, que sí viaja con la lista de
      // bloques vacía.
      //
      // Las fechas se comparan como texto, y es correcto por lo mismo de
      // siempre: AAAA-MM-DD ordena igual alfabéticamente que en el almanaque.
      //
      // 🔑 EL RECORTE SE HACE SOBRE EL `hasta`, no sobre la lista ya armada:
      // el cálculo de la grilla vive en `_shared/grilla.ts` desde el
      // 9-oct-2026 y recibe un rango, no una lista de días. El resultado es el
      // mismo y el techo sigue siendo de este endpoint — el panel no lo tiene.
      const hastaReservable = hasta <= ultimoDiaReservable
        ? hasta
        : ultimoDiaReservable

      // ── Lo que hay que ir a preguntarle a la base ─────────────────────────
      //
      // Cinco consultas, todas de lectura, todas con la llave maestra: el
      // navegador no toca ninguna de estas tablas.

      const profesional = await ctx.supabaseAdmin
        .from( 'profesionales' )
        .select( 'id, activo' )
        .eq( 'id', profesionalId )
        .maybeSingle()

      if ( profesional.error ) {
        return falloDeBase()
      }

      // Un profesional dado de baja se contesta igual que uno inexistente, y
      // es deliberado: "existe pero no atiende más" es información del
      // consultorio y no hay motivo para publicarla.
      if ( !profesional.data || !profesional.data.activo ) {
        return pedidoInvalido( 'Ese profesional no está disponible' )
      }

      const tratamiento = await ctx.supabaseAdmin
        .from( 'tratamientos' )
        .select( 'id, nombre, duracion_web_min' )
        .eq( 'id', tratamientoId )
        .maybeSingle()

      if ( tratamiento.error ) {
        return falloDeBase()
      }

      if ( !tratamiento.data ) {
        return pedidoInvalido( 'Ese tratamiento no existe' )
      }

      // 🔴 ACÁ HABÍA UN 400 QUE YA NO EXISTE: hasta el 27-ago-2026, un
      // tratamiento sin `duracion_web_min` se rechazaba con "no se reserva por
      // la web". Ahora se convierte, y la grilla se dibuja con el largo de lo
      // que SE VA A AGENDAR, no con el del elegido.
      //
      // La regla vive en `_shared/arranque.ts` y la aplica también `reservar`.
      // Tiene que ser la misma en los dos: si acá se dibujaran bloques de 30 y
      // allá se agendaran 60, el paciente se enteraría al chocar contra el
      // turno siguiente, no al reservar.
      const arranque = await conQueArranca( ctx, tratamiento.data )

      if ( !arranque ) {
        return falloDeBase()
      }

      // La consulta vive en `_shared/parejas.ts`: la hacen los dos endpoints y
      // la condición `activo` tiene que valer en los dos o no vale en ninguno.
      const pareja = await estadoDeLaPareja(
        ctx,
        profesionalId,
        tratamientoId,
      )

      if ( pareja === 'error-de-base' ) {
        return falloDeBase()
      }

      if ( pareja === 'no-la-hace' ) {
        return pedidoInvalido( 'Ese profesional no hace ese tratamiento' )
      }

      // ── La grilla ─────────────────────────────────────────────────────────
      //
      // 🔑 EL CÁLCULO NO VIVE ACÁ DESDE EL 9-oct-2026: está en
      // `_shared/grilla.ts`, que lo comparte con el panel. Lo que queda en
      // este archivo es lo que SÍ es de este canal — la duración deducida del
      // tratamiento, la pareja profesional-tratamiento, el techo de dos meses
      // y el piso de doce horas.
      //
      // `conPisoDeHoras: true` es la regla del formulario: un paciente no saca
      // un turno para dentro de veinte minutos. El panel la apaga, porque
      // Cecilia sí tiene que poder agendar para esta tarde.
      const respuesta = await armarLaGrilla( ctx, {
        profesionalId: profesionalId,
        duracionMin: arranque.duracionMin,
        desde: desde,
        hasta: hastaReservable,
        ahora: ahora,
        conPisoDeHoras: true,
      } )

      if ( respuesta === 'error-de-base' ) {
        return falloDeBase()
      }

      // El día sin agenda viaja igual, con la lista vacía. Así la pantalla
      // distingue "ese día no atiende" de "ese día no vino en la respuesta",
      // que es la misma decisión del 6-ago sobre los bloques ocupados: se
      // muestran, no se esconden.
      // 🔑 VIAJAN LOS DOS TRATAMIENTOS, y la pantalla necesita los dos para
      // poder avisar ANTES de que el paciente confirme: "elegiste ortodoncia,
      // reservás una consulta de 30 minutos". Sin el par, o le miente el
      // nombre o le miente la duración.
      return Response.json( {
        profesional: profesionalId,
        tratamiento: tratamientoId,
        tratamiento_nombre: tratamiento.data.nombre,
        se_agenda: arranque.tratamientoId,
        se_agenda_nombre: arranque.nombre,
        duracion_min: arranque.duracionMin,
        dias: respuesta,
      } )
    },
  ),

}
