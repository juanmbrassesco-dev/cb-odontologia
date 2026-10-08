// Portero de CB Odontología — endpoint GET /quien-soy
//
// EL PRIMER ENDPOINT DEL PANEL, y el más chico que existe: contesta si el que
// está conectado es personal de la clínica, y con qué nivel. Nada más.
//
// Tiene DOS trabajos, y los dos justifican que exista en vez de ser una línea
// adentro de otro endpoint:
//
//   1. el panel lo llama al abrir, para saber qué dibujar. Sin esto tendría
//      que adivinar el nivel del que entró, o pedir la agenda y deducirlo del
//      error — que es enterarse por el síntoma.
//   2. es el SUJETO DE PRUEBA de la cerradura. `quien-pide.ts` es una función
//      compartida y una función no se puede golpear con `curl`: la batería
//      necesita una puerta de verdad para medir el 401, el 403 y el 200.
//
// 🔒 NO DEVUELVE EL CORREO que vino en el token, ni ningún dato de la fila que
// no haga falta en pantalla. El que pregunta ya sabe quién es; lo que no sabe
// es qué puede hacer.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`, y la ausencia es la decisión — igual que
// en `mis-pacientes`: la plataforma exige un JWT válido por defecto, así que
// un pedido sin token muere ANTES de llegar acá y la respuesta es 401. Ese es
// el primer caso de la batería, y lo contesta la plataforma, no este archivo.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'


// Un fallo de la base se contesta SIN el detalle: el texto de Postgres nombra
// tablas, columnas y roles.
function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo verificar el acceso' },
    { status: 500 },
  )
}


export default {

  fetch: withSupabase< Database >(
    { auth: 'user' },
    async ( _req, ctx ) => {

      // La cerradura. `quien-pide.ts` levanta el error de base en vez de
      // devolver `null`, así que acá se separan los dos casos: lo que falla y
      // lo que no tiene permiso. Confundirlos manda a buscar el problema al
      // lugar equivocado.
      let quien

      try {
        quien = await quienPide( ctx )
      }
      catch {
        return falloDeBase()
      }

      // 🔴 403 Y NO 404: el que pide tiene una sesión válida, lo que no tiene
      // es permiso. Y el mensaje es genérico a propósito —no dice "no estás en
      // la tabla profesionales"—, porque un error que describe el estado
      // interno es divulgación de información (information disclosure).
      if ( !quien ) {
        return Response.json(
          { error: 'Sin acceso al panel' },
          { status: 403 },
        )
      }

      return Response.json( quien )
    },
  ),

}
