// Portero de CB Odontología — endpoint público GET /horarios-disponibles
//
// Contesta una sola pregunta: qué bloques de media hora tiene ese profesional
// en ese rango de fechas. Público a conciencia, igual que /tratamientos: el
// paciente tiene que poder ver si hay turno ANTES de registrarse.
//
// PASO D de la etapa ②: la grilla descuenta los días que tapan las
// `excepciones` (feriados, cierres, ausencias) y marca `ocupado` lo que ya
// tiene turno. Todavía no aplica la ventana de reserva (paso E), así que un
// bloque de ayer sigue saliendo `libre`. Cada paso se despliega y se prueba
// antes del siguiente.
//
// Nada de lo que sale de acá viene de `turnos`: son horas y un estado. Quién
// reservó qué no se publica.

import { withSupabase } from 'npm:@supabase/server@^1'

import {
  esFechaValida,
  listarDias,
  diaSemanaISO,
  desfaseDeSantaFe,
  bloquesDelTramo,
  diaTapado,
  sumarDias,
  bloqueOcupado,
  unificarBloques,
} from '../_shared/disponibilidad.ts'

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

  fetch: withSupabase(
    { auth: 'none' },
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

      const dias = listarDias( desde, hasta )

      if ( dias.length > DIAS_MAXIMOS_POR_PEDIDO ) {
        return pedidoInvalido(
          `El rango no puede pasar de ${ DIAS_MAXIMOS_POR_PEDIDO } días`,
        )
      }

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
        .select( 'id, duracion_web_min' )
        .eq( 'id', tratamientoId )
        .maybeSingle()

      if ( tratamiento.error ) {
        return falloDeBase()
      }

      if ( !tratamiento.data ) {
        return pedidoInvalido( 'Ese tratamiento no existe' )
      }

      // `duracion_web_min` vacío significa "no se reserva por la web": lo
      // agenda el profesional después de la consulta previa. No es un error de
      // datos, es la regla del consultorio, y por eso se contesta 400 y no 500.
      if ( !tratamiento.data.duracion_web_min ) {
        return pedidoInvalido( 'Ese tratamiento no se reserva por la web' )
      }

      const pareja = await ctx.supabaseAdmin
        .from( 'profesional_tratamientos' )
        .select( 'id' )
        .eq( 'profesional_id', profesionalId )
        .eq( 'tratamiento_id', tratamientoId )
        .maybeSingle()

      if ( pareja.error ) {
        return falloDeBase()
      }

      if ( !pareja.data ) {
        return pedidoInvalido( 'Ese profesional no hace ese tratamiento' )
      }

      // La agenda semanal entera, de una sola vez. Son pocas filas —siete, hoy—
      // y volver a preguntar por cada día del rango serían sesenta consultas
      // para el mismo dato.
      const agenda = await ctx.supabaseAdmin
        .from( 'horarios_base' )
        .select( 'dia_semana, inicio, fin' )
        .eq( 'profesional_id', profesionalId )
        .order( 'dia_semana' )
        .order( 'inicio' )

      if ( agenda.error ) {
        return falloDeBase()
      }

      // Las excepciones que pueden tapar un día de este profesional son de dos
      // dueños: las de la CLÍNICA, que no tienen profesional y tapan a todos
      // (feriados, cierres), y las de ÉL. Las de otro profesional no se piden.
      //
      // `activa` es el interruptor: una excepción terminada se apaga, no se
      // borra. Una fila borrada no deja rastro de por qué esa semana estuvo
      // cerrada durante meses.
      //
      // El filtro se arma pegando el número del profesional adentro del texto,
      // y eso es seguro acá porque `profesionalId` ya pasó por `Number.isInteger`
      // más arriba: lo que llega es un número, no lo que haya escrito el que
      // arma la dirección.
      const excepciones = await ctx.supabaseAdmin
        .from( 'excepciones' )
        .select( 'tipo, fecha_desde, fecha_hasta, semana_del_mes' )
        .eq( 'activa', true )
        .or( `profesional_id.is.null,profesional_id.eq.${ profesionalId }` )

      if ( excepciones.error ) {
        return falloDeBase()
      }

      // Los turnos que ya tiene tomados este profesional en el rango.
      //
      // `activo` es el filtro que hace que un turno cancelado no ocupe nada: la
      // fila sigue existiendo —acá no se borra— pero el hueco vuelve entero a
      // la grilla (§ 9.3).
      //
      // El rango se pide con UN DÍA DE MARGEN para atrás. Un turno que arrancó
      // el día anterior y se estiró hasta hoy igual ocupa, y la consulta filtra
      // por el ARRANQUE. Hoy ningún tramo cruza la medianoche, así que no puede
      // pasar; el margen está para que la respuesta no dependa de eso.
      //
      // Se piden dos columnas y nada más. `observaciones_paciente` puede tener
      // datos de salud: lo que no se lee no se puede publicar por accidente.
      const primerDia = sumarDias( desde, -1 )
      const diaSiguiente = sumarDias( hasta, 1 )

      const turnos = await ctx.supabaseAdmin
        .from( 'turnos' )
        .select( 'inicio, duracion_min' )
        .eq( 'profesional_id', profesionalId )
        .eq( 'activo', true )
        .gte( 'inicio', `${ primerDia }T00:00:00${ desfaseDeSantaFe( primerDia ) }` )
        .lt( 'inicio', `${ diaSiguiente }T00:00:00${ desfaseDeSantaFe( diaSiguiente ) }` )

      if ( turnos.error ) {
        return falloDeBase()
      }

      // ── La grilla ─────────────────────────────────────────────────────────

      // Cuánto dura el turno que se está buscando. Es lo que decide si un
      // bloque se pisa con lo ya tomado: no alcanza con mirar la media hora del
      // bloque, porque una limpieza de 60 minutos que empieza a las 12:00 se
      // pisa con un turno de las 12:30.
      const duracion = tratamiento.data.duracion_web_min

      const respuesta = dias.map( ( fecha ) => {

        // Un día tapado no devuelve bloques, y es una distinción que el
        // paciente necesita ver: "acá no se atiende" no es lo mismo que "acá
        // está todo tomado", que sí devuelve sus bloques y se pinta rojo.
        if ( diaTapado( fecha, excepciones.data ) ) {
          return {
            fecha: fecha,
            bloques: [],
          }
        }

        const desfase = desfaseDeSantaFe( fecha )
        const dia = diaSemanaISO( fecha )

        const tramosDelDia = agenda.data.filter(
          ( tramo ) => tramo.dia_semana === dia,
        )

        const bloquesDelDia = unificarBloques(
          tramosDelDia.flatMap(
            ( tramo ) => bloquesDelTramo( fecha, tramo.inicio, tramo.fin, desfase ),
          ),
        )

        // El bloque ocupado se MARCA, no se saca. Es la decisión del 6-ago: un
        // día con todo tomado tiene que verse distinto de un día en que no se
        // atiende, y esconder los rojos los deja iguales.
        const bloques = bloquesDelDia.map( ( bloque ) => {

          if ( bloqueOcupado( bloque.inicio, duracion, turnos.data ) ) {
            return {
              inicio: bloque.inicio,
              estado: 'ocupado',
            }
          }

          return bloque
        } )

        return {
          fecha: fecha,
          bloques: bloques,
        }
      } )

      // El día sin agenda viaja igual, con la lista vacía. Así la pantalla
      // distingue "ese día no atiende" de "ese día no vino en la respuesta",
      // que es la misma decisión del 6-ago sobre los bloques ocupados: se
      // muestran, no se esconden.
      return Response.json( {
        profesional: profesionalId,
        tratamiento: tratamientoId,
        duracion_min: tratamiento.data.duracion_web_min,
        dias: respuesta,
      } )
    },
  ),

}
