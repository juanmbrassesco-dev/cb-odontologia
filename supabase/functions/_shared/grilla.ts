// LA GRILLA DE BLOQUES — el cálculo que comparten los dos canales.
//
// 🔴 POR QUÉ ESTE ARCHIVO EXISTE, y nació el 9-oct-2026. La grilla la piden
// DOS pantallas: la del paciente que reserva por la web y la del consultorio
// que carga un turno a mano. El cálculo es el mismo —qué tramos atiende ese
// profesional, qué días están tapados, qué ya está tomado— y las REGLAS DEL
// CANAL no lo son.
//
// Hasta hoy el cálculo vivía adentro de `horarios-disponibles`, pegado a las
// reglas de la web. Copiarlo para el panel habría dejado dos grillas que se
// desincronizan: la primera vez que alguien arregle un borde en una, la otra
// sigue contestando lo viejo y el error aparece como un turno que se pisa.
//
// 🔑 LO QUE QUEDA AFUERA, Y ES LA FRONTERA: acá NO se decide la duración, ni
// se valida la pareja profesional-tratamiento, ni se aplica el techo de dos
// meses. Eso es política de canal y la pone quien llama. Acá entra un número
// de minutos ya decidido y sale una grilla.

import type { SupabaseContext } from 'npm:@supabase/server@^1'

import type { Database } from './tipos-de-la-base.ts'

import {
  bloqueOcupado,
  bloquesDelTramo,
  desfaseDeSantaFe,
  diaSemanaISO,
  excepcionQueTapa,
  fueraDePlazo,
  listarDias,
  sumarDias,
  unificarBloques,
} from './disponibilidad.ts'


export type PedidoDeGrilla = {

  profesionalId: number

  // Cuánto dura el turno que se está buscando, en minutos. Es lo que decide si
  // un bloque se pisa con lo ya tomado: no alcanza con mirar la media hora del
  // bloque, porque una limpieza de 60 que empieza a las 12:00 se pisa con un
  // turno de las 12:30.
  //
  // 🔑 ENTRA POR PARÁMETRO Y NO SE DEDUCE DEL TRATAMIENTO. Es la diferencia de
  // fondo entre los dos canales: por la web la duración la decide el sistema
  // (`duracion_web_min`), y en el panel la elige quien atiende, porque la
  // ortodoncia de verdad dura 90 o 120.
  duracionMin: number

  desde: string
  hasta: string

  // El reloj entra de afuera, no se mira acá adentro: una función que consulta
  // la hora por su cuenta devuelve algo distinto cada vez y no se puede probar.
  ahora: Date

  // 🔒 EL PISO DE 12 HORAS ES UNA REGLA DEL FORMULARIO, NO DEL CONSULTORIO.
  // Existe para que un paciente no saque un turno para dentro de veinte
  // minutos; Cecilia tiene que poder agendar para esta tarde. Con esto en
  // `false`, ningún bloque sale como `fuera_de_plazo`.
  conPisoDeHoras: boolean

  // 🔒 SI EL DÍA TAPADO DICE POR QUÉ. Es una regla de CANAL, igual que el piso
  // de 12 horas, y por eso entra por parámetro en vez de decidirse acá adentro.
  //
  // 🔴 EL MOTIVO NO PUEDE VIAJAR AL PACIENTE. «Vacaciones de verano» o
  // «Congreso en Rosario» es información interna del consultorio: él tiene que
  // ver el día cerrado y nada más. Con esto en `false` el campo no se calcula,
  // así que el endpoint del paciente no tiene nada que acordarse de sacar —el
  // dato que no existe no se filtra por accidente.
  conMotivo?: boolean

  // 🔑 UN TURNO QUE NO CUENTA COMO OCUPADO, y existe por la pantalla de MOVER.
  // Al mover un turno la pregunta no es «qué horarios están libres» sino «qué
  // horarios habría si ESTE turno no existiera»: sin esto el turno se tapa a sí
  // mismo, y dejarlo a la misma hora con otra duración —el caso más común— no
  // se puede ni elegir.
  //
  // ⚠ OPCIONAL A PROPÓSITO. El camino del paciente no lo manda, así que para
  // él no cambia nada: `undefined` no agrega ningún filtro.
  exceptoTurnoId?: number
}


export type DiaDeLaGrilla = {
  fecha: string
  bloques: { inicio: string, estado: string }[]

  // Por qué está cerrado, cuando se pidió con `conMotivo` y hay una ausencia
  // que lo tapa. Un domingo NO lo lleva: ahí no hay ausencia ninguna, el día
  // simplemente no tiene agenda — y la distinción es justo la que la pantalla
  // necesita para decir algo útil.
  tapadoPor?: {
    descripcion: string
    esDeLaClinica: boolean
  }
}


/**
 * La grilla de bloques de un profesional, día por día.
 *
 * Devuelve la lista de días, o `'error-de-base'` si alguna consulta falló —
 * quien llama decide qué contestar, porque el texto del error de Postgres
 * nombra tablas y columnas y no puede viajar al navegador.
 */
export async function armarLaGrilla(
  ctx: SupabaseContext< Database >,
  pedido: PedidoDeGrilla,
): Promise< DiaDeLaGrilla[] | 'error-de-base' > {

  const { profesionalId, duracionMin, desde, hasta, ahora, exceptoTurnoId } = pedido

  // La agenda semanal entera, de una sola vez. Son pocas filas —siete, hoy— y
  // volver a preguntar por cada día del rango serían sesenta consultas para el
  // mismo dato.
  const agenda = await ctx.supabaseAdmin
    .from( 'horarios_base' )
    .select( 'dia_semana, inicio, fin, fin_maximo' )
    .eq( 'profesional_id', profesionalId )

    // 🔴 ESTA LÍNEA ES LO QUE HACE QUE `activo` SIRVA DE ALGO, y entró con la
    // etapa ⑤.5: sin ella, un tramo apagado desde el panel sigue ofreciendo
    // turnos y la columna es decoración. No falla con error — contesta mal.
    //
    // ⚠ TOCA LOS DOS CANALES, porque este cálculo lo comparten: el que reserva
    // por la web y el que carga a mano desde el panel. Por eso el día que se
    // cerró la rebanada C se corrió `probar-reservar.sh` entera, que es la
    // batería que mide que el camino del paciente no se rompió.
    .eq( 'activo', true )

    .order( 'dia_semana' )
    .order( 'inicio' )

  if ( agenda.error ) {
    return 'error-de-base'
  }

  // Las excepciones que pueden tapar un día de este profesional son de dos
  // dueños: las de la CLÍNICA, que no tienen profesional y tapan a todos
  // (feriados, cierres), y las de ÉL. Las de otro profesional no se piden.
  //
  // `activa` es el interruptor: una excepción terminada se apaga, no se borra.
  // Una fila borrada no deja rastro de por qué esa semana estuvo cerrada.
  //
  // El filtro se arma pegando el número del profesional adentro del texto, y
  // eso es seguro porque `profesionalId` es un `number` del tipo: lo que llega
  // es un número, no lo que haya escrito quien arma la dirección.
  const excepciones = await ctx.supabaseAdmin
    .from( 'excepciones' )
    .select(
      'tipo, fecha_desde, fecha_hasta, semana_del_mes, descripcion, profesional_id',
    )
    .eq( 'activa', true )
    .or( `profesional_id.is.null,profesional_id.eq.${ profesionalId }` )

  if ( excepciones.error ) {
    return 'error-de-base'
  }

  // Los turnos que ya tiene tomados este profesional en el rango.
  //
  // `activo` es el filtro que hace que un turno cancelado no ocupe nada: la
  // fila sigue existiendo —acá no se borra— pero el hueco vuelve entero a la
  // grilla (§ 9.3).
  //
  // El rango se pide con UN DÍA DE MARGEN para atrás. Un turno que arrancó el
  // día anterior y se estiró hasta hoy igual ocupa, y la consulta filtra por el
  // ARRANQUE. Hoy ningún tramo cruza la medianoche, así que no puede pasar; el
  // margen está para que la respuesta no dependa de eso.
  //
  // Se piden dos columnas y nada más. `observaciones_paciente` puede tener
  // datos de salud: lo que no se lee no se puede publicar por accidente.
  const primerDia = sumarDias( desde, -1 )
  const diaSiguiente = sumarDias( hasta, 1 )

  let consulta = ctx.supabaseAdmin
    .from( 'turnos' )
    .select( 'inicio, duracion_min' )
    .eq( 'profesional_id', profesionalId )
    .eq( 'activo', true )
    .gte( 'inicio', `${ primerDia }T00:00:00${ desfaseDeSantaFe( primerDia ) }` )
    .lt( 'inicio', `${ diaSiguiente }T00:00:00${ desfaseDeSantaFe( diaSiguiente ) }` )

  // 🔴 EL TURNO QUE SE ESTÁ MOVIENDO SE SACA ACÁ, EN LA CONSULTA, y no de la
  // lista después de leerla. La fila que nunca llegó no se puede olvidar de
  // descontar más abajo; la que llega y hay que ignorar, sí.
  //
  // Se filtra por una columna que el `select` no pide, y se puede: el filtro lo
  // aplica la base, no esta función.
  if ( exceptoTurnoId ) {
    consulta = consulta.neq( 'id', exceptoTurnoId )
  }

  const turnos = await consulta

  if ( turnos.error ) {
    return 'error-de-base'
  }

  return listarDias( desde, hasta ).map( ( fecha ) => {

    // Un día tapado no devuelve bloques, y es una distinción que hay que poder
    // ver: «acá no se atiende» no es lo mismo que «acá está todo tomado», que
    // sí devuelve sus bloques y se pinta distinto.
    const tapa = excepcionQueTapa( fecha, excepciones.data )

    if ( tapa ) {

      // Sin `conMotivo`, el día sale igual que antes: cerrado y sin explicar.
      // Es lo que ve el paciente.
      if ( !pedido.conMotivo ) {
        return {
          fecha: fecha,
          bloques: [],
        }
      }

      return {
        fecha: fecha,
        bloques: [],
        tapadoPor: {
          descripcion: tapa.descripcion,

          // 🔑 LA DISTINCIÓN NO ES UN ADORNO: si la ausencia es de la clínica no
          // sirve cambiar de profesional, y si es de una persona OTRA puede
          // atender ese día. Es lo que decide qué hacer con el pedido que se
          // está cargando.
          esDeLaClinica: tapa.profesional_id === null,
        },
      }
    }

    const desfase = desfaseDeSantaFe( fecha )
    const dia = diaSemanaISO( fecha )

    const tramosDelDia = agenda.data.filter(
      ( tramo ) => tramo.dia_semana === dia,
    )

    // El tramo entero entra a la función porque su `fin_maximo` es lo que
    // decide si el turno cabe: `fin` corta la grilla, el techo dice hasta
    // dónde puede terminar lo que arrancó adentro.
    const bloquesDelDia = unificarBloques(
      tramosDelDia.flatMap(
        ( tramo ) => bloquesDelTramo( fecha, tramo, duracionMin, desfase ),
      ),
    )

    // Ningún bloque se saca: se MARCA. Es la decisión del 6-ago — un día con
    // todo tomado tiene que verse distinto de un día en que no se atiende, y
    // esconder lo que no se puede reservar los deja iguales.
    //
    // 🔴 El ORDEN de estos tres `if` es la regla, no una casualidad: se informa
    // el motivo que quien mira NO puede destrabar. Decir «ocupado» en un bloque
    // que además ya venció insinúa que si alguien cancela se libera, y es
    // falso: aunque se libere, sigue siendo tarde.
    const bloques = bloquesDelDia.map( ( bloque ) => {

      if ( pedido.conPisoDeHoras && fueraDePlazo( bloque.inicio, ahora ) ) {
        return {
          inicio: bloque.inicio,
          estado: 'fuera_de_plazo',
        }
      }

      // `no_entra` ya viene decidido desde el tramo: es el único de los tres
      // que no depende de nada de afuera.
      if ( bloque.estado === 'no_entra' ) {
        return bloque
      }

      if ( bloqueOcupado( bloque.inicio, duracionMin, turnos.data ) ) {
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
}
