// LA DURACIÓN DE UN TURNO — la regla que comparten los endpoints que la
// escriben.
//
// 🔴 POR QUÉ VIVE ACÁ Y NO ADENTRO DE CADA ENDPOINT. Las tres constantes
// estaban escritas en `turno-del-panel`, y al construir `mover-turno` había
// que repetirlas. Dos copias de un número no fallan el día que se escriben:
// fallan el día que alguien cambia una — ahí cargar un turno y moverlo
// empiezan a aceptar duraciones distintas, y nada avisa. Es el mismo motivo
// por el que el 9-oct se extrajo `grilla.ts`: lo que se comparte no es el
// resultado, es el mecanismo.
//
// 🔑 EL BLOQUE DE 30 ES LA UNIDAD DE PRESENTACIÓN, no cómo la base guarda el
// dato. `turnos.duracion_min` guarda MINUTOS, que es la unidad estable; el
// bloque es como piensa Cecilia y por eso es lo que se valida de este lado.

export const DURACION_MINIMA = 30

export const DURACION_MAXIMA = 300

export const BLOQUE = 30


/** Si una duración en minutos es una que el consultorio pueda agendar. */
export function duracionValida( minutos: number ): boolean {

  return Number.isInteger( minutos )
    && minutos >= DURACION_MINIMA
    && minutos <= DURACION_MAXIMA
    && minutos % BLOQUE === 0
}


/** El texto del error, uno solo para los dos endpoints. */
export function porQueNoVale(): string {

  return `La duración va en bloques de ${ BLOQUE } minutos, `
    + `entre ${ DURACION_MINIMA } y ${ DURACION_MAXIMA }`
}
