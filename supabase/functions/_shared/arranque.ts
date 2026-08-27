// CON QUÉ ARRANCA UN TURNO — una sola regla, un solo lugar.
//
// Qué es: dado el tratamiento que el paciente ELIGIÓ en el sitio, contesta con
// qué se agenda ese turno — qué tratamiento, cómo se llama y cuántos minutos
// ocupa.
//
// La regla del consultorio, decidida el 6-ago-2026 (§ 6 del documento de
// estado), es una sola bifurcación:
//
//   consulta   → se agenda consulta, 30 minutos
//   limpieza   → se agenda limpieza, 60 minutos
//   los otros  → se agenda una CONSULTA de 30, y a qué vino queda anotado
//                aparte, en `turnos.motivo_consulta_id`
//
// O sea que la consulta es el ENVASE que el consultorio le pone adelante a
// todo lo que no se reserva solo. Nadie empieza una ortodoncia sin que la vean
// primero.
//
// 🔴 POR QUÉ VIVE EN `_shared/` Y NO ADENTRO DE UN ENDPOINT, que es el mismo
// motivo exacto de `parejas.ts`: la regla la necesitan LOS DOS —`reservar`
// para anotar el turno y `horarios-disponibles` para dibujar la grilla— y
// tiene que valer en los dos o no vale en ninguno. Si la grilla ofreciera
// bloques de 30 y el `POST` agendara 60, el paciente se enteraría al chocar
// contra un turno que se le pisa con el siguiente. Ese olvido no falla con
// error: contesta mal en silencio.
//
// 🔴 EL LÍMITE, ESCRITO ACÁ PARA QUE NADIE LO REUSE DE MÁS: esta regla vale
// para el canal `web` Y PARA NADA MÁS. Después de esa primera consulta de 30,
// Cecilia agenda la ortodoncia de verdad, que dura 90 o 120. Si el panel ⑤
// llamara a esta función tal cual, le convertiría ese turno en una consulta de
// 30 minutos.

import type { SupabaseContext } from 'npm:@supabase/server@^1'

import type { Database } from './tipos-de-la-base.ts'


// El nombre de la fila que hace de envase. Es un dato de la base del que
// depende este código, así que se escribe UNA vez y con nombre, en vez de
// quedar suelto adentro de la consulta.
const NOMBRE_DEL_ENVASE = 'consulta'


// Lo que hace falta saber del tratamiento elegido. Llega YA LEÍDO, no como
// `id`: los dos endpoints consultan esa fila igual para validar que existe, y
// pedirla de nuevo acá sería ir dos veces a la base en el mismo pedido.
export type TratamientoElegido = {
  id: number
  nombre: string
  duracion_web_min: number | null
}


// Lo que se agenda. Los tres datos viajan juntos porque se usan juntos: el
// `id` va al turno, el nombre al correo y los minutos a la grilla.
export type Arranque = {
  tratamientoId: number
  nombre: string
  duracionMin: number
}


export async function conQueArranca(
  ctx: SupabaseContext< Database >,
  elegido: TratamientoElegido,
): Promise< Arranque | null > {

  // Caso 1: el elegido se reserva solo por la web. Es su propio envase, y no
  // hay nada que preguntarle a la base.
  if ( elegido.duracion_web_min ) {
    return {
      tratamientoId: elegido.id,
      nombre: elegido.nombre,
      duracionMin: elegido.duracion_web_min,
    }
  }

  // Caso 2: no se reserva solo, así que el envase es la consulta.
  const envase = await ctx.supabaseAdmin
    .from( 'tratamientos' )
    .select( 'id, nombre, duracion_web_min' )
    .eq( 'nombre', NOMBRE_DEL_ENVASE )
    .maybeSingle()

  if ( envase.error ) {
    return null
  }

  // 🔴 LOS DOS CASOS, Y NO ALCANZA CON UNO. Que la fila no exista y que exista
  // con la duración vacía terminan igual de mal: sin envase no hay con qué
  // agendar. El `?.` cubre los dos en una sola pregunta: si `data` está vacío
  // no sigue la cadena y contesta `undefined`, que negado da verdadero.
  //
  // Y acá NO se devuelve un 30 por defecto, que es la tentación obvia. Un 30
  // inventado agendaría turnos contra un tratamiento que nadie verificó, y el
  // error aparecería semanas después como turnos pisados en la agenda de
  // Cecilia. Devolver `null` corta el pedido con un fallo de base: se rompe
  // ruidoso y del lado de no anotar nada.
  //
  // Se llega acá si alguien renombra, borra o vacía la fila `consulta` desde
  // el Table Editor. Es improbable y es exactamente por eso que hay que
  // escribirlo: nadie va a estar mirando cuando pase.
  if ( !envase.data?.duracion_web_min ) {
    return null
  }

  return {
    tratamientoId: envase.data.id,
    nombre: envase.data.nombre,
    duracionMin: envase.data.duracion_web_min,
  }
}
