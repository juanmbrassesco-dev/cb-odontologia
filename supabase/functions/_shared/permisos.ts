// QUIÉN PUEDE TOCAR QUÉ — la decisión de permisos del panel, en un solo lugar.
//
// Qué es: dado quién pide y de quién es la fila que quiere tocar, contesta si
// puede. Nada más: no lee la base, no arma respuestas, no sabe de HTTP.
//
// 🔴 POR QUÉ EXISTE, y es el motivo exacto de `quien-pide.ts`: el panel tiene
// DOS chequeos distintos y hasta hoy cada endpoint escribía el suyo a mano.
//
//   · de PROPIEDAD — «¿esta fila es tuya?» — `cancelar-del-panel`, `mover-turno`
//   · de NIVEL     — «¿sos admin?»        — `plantel-del-panel`, `alta-de-profesional`
//
// La etapa ⑤.5 es la primera que necesita LOS DOS EN LA MISMA PUERTA, porque
// `excepciones` guarda dos cosas con la misma forma: la ausencia de una persona
// —que es suya— y el cierre de toda la clínica —que no es de nadie—. Escribir
// esa mezcla con un `if` suelto adentro de cada endpoint deja la cerradura
// repartida en tres archivos, y una cerradura que está en dos de tres puertas
// no es una cerradura.
//
// 🔑 LA REGLA DE DISEÑO, LA MISMA DE `quien-pide.ts`: ningún endpoint decide
// permisos por su cuenta — todos preguntan acá. El día que los permisos tengan
// que volverse finos se toca este archivo, no los nueve.

import type { QuienPide } from './quien-pide.ts'


/**
 * ¿Puede quien pide tocar una fila que es de `profesionalIdDeLaFila`?
 *
 * `null` en ese parámetro significa **de la clínica**: una excepción sin
 * profesional tapa a todo el plantel.
 *
 * 🔴 DE QUIÉN ES LA FILA SALE DE LA FILA, NUNCA DEL PEDIDO. Quien llama a esta
 * función con un dato que viajó en el cuerpo del pedido está preguntando
 * «¿puedo tocar algo que ES MÍO PORQUE YO LO DIGO?», y la respuesta siempre va
 * a ser sí. En una ESCRITURA sobre una fila que ya existe, primero se LEE la
 * fila y recién después se pregunta acá — es el orden que ya usa `mover-turno`.
 */
export function puedeTocar(
  quien: QuienPide,
  profesionalIdDeLaFila: number | null,
): boolean {

  // Una fila de la clínica afecta al plantel entero, así que la pregunta no es
  // de quién es: es de NIVEL. Un profesional con sesión válida no puede cerrar
  // el consultorio.
  if ( profesionalIdDeLaFila === null ) {
    return quien.esAdmin
  }

  // Y si la fila es de alguien, puede tocarla ese alguien — o Cecilia, que
  // puede sobre cualquiera. Ese «o Cecilia» es el requisito que ella precisó el
  // 8-oct: que pueda tocar la agenda de otro es una CAPACIDAD, no el flujo
  // previsto.
  return quien.esAdmin || profesionalIdDeLaFila === quien.id
}
