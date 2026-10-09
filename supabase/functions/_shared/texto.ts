// Lo que escribió una persona, saneado — compartido por los endpoints que
// reciben un formulario.
//
// 🔴 POR QUÉ VIVE ACÁ Y NO ADENTRO DE UN ENDPOINT. Nació dentro de `reservar`,
// que era el único que recibía datos tipeados. Con el panel son tres —el alta
// de paciente, el turno a mano y lo que venga— y dos copias de una validación
// no fallan: se desincronizan. Una sube el tope de un campo, la otra no, y el
// mismo nombre entra por una puerta y rebota por la otra sin que nada avise.
//
// La regla que aplica: cuando el mismo mecanismo hace falta dos veces, se
// unifica el MECANISMO, no se igualan los dos resultados a mano.

// Los topes son de la BASE, no de la pantalla: `pacientes.nombre` es un
// `varchar` y un texto más largo lo rechaza el motor con un error feo. Acá se
// rechaza antes, con un mensaje que se entiende.
export const LARGO_MAXIMO_NOMBRE        = 60
export const LARGO_MAXIMO_TELEFONO      = 30
export const LARGO_MAXIMO_DNI           = 20
export const LARGO_MAXIMO_OBSERVACIONES = 500
export const LARGO_MAXIMO_CORREO        = 255


// Un texto que escribió una persona, o `null` si no sirve.
//
// Las tres preguntas son distintas y las tres hacen falta: que sea un texto y
// no un número ni una lista disfrazada, que no esté vacío después de sacarle
// los espacios (' ' no es un apellido), y que no pase del tope.
export function textoLimpio(
  valor: unknown,
  largoMaximo: number,
): string | null {

  if ( typeof valor !== 'string' ) {
    return null
  }

  const limpio = valor.trim()

  if ( limpio.length === 0 ) {
    return null
  }

  if ( limpio.length > largoMaximo ) {
    return null
  }

  return limpio
}
