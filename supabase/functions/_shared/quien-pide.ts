// QUIÉN PIDE — la cerradura del panel, una sola vez y en un solo lugar.
//
// Qué es: dado un pedido ya autenticado, contesta si el que lo manda es
// personal de la clínica, y con qué nivel. Devuelve sus datos o `null`.
//
// 🔴 POR QUÉ HACE FALTA, medido contra el código y no supuesto. Los endpoints
// del paciente usan `auth: 'user'`, que significa "trae un papel firmado
// válido" Y NADA MÁS. Cualquiera se crea una cuenta de Google en dos minutos y
// tiene un token tan válido como el de Cecilia. Si el panel se construyera con
// esa misma cerradura, cualquier paciente logueado vería la agenda del día con
// los nombres de todos los demás. Eso es A01: Broken Access Control.
//
// 🔴 POR QUÉ VIVE EN `_shared/` Y NO ADENTRO DE UN ENDPOINT, que es el mismo
// motivo exacto de `arranque.ts` y `parejas.ts`: la necesitan TODOS los
// endpoints del panel y tiene que valer en todos o no vale en ninguno. Una
// cerradura que está en ocho de nueve puertas no es una cerradura.
//
// 🔴 Y LA REGLA DE DISEÑO QUE HAY QUE RESPETAR AL ESCRIBIR CADA ENDPOINT:
// ninguno lee `es_admin` por su cuenta — todos preguntan por esta función. El
// día que los permisos tengan que volverse finos se toca este archivo, no los
// nueve. El que lo lea directo es el que después no se encuentra.
//
// 🔒 EL CORREO SALE DEL TOKEN, NUNCA DEL PEDIDO. Es la misma regla que ya
// sostiene `mis-pacientes`: el portero no le pregunta al cliente quién es, se
// lo pregunta al papel que el sistema de cuentas firmó.

import type { SupabaseContext } from 'npm:@supabase/server@^1'

import type { Database } from './tipos-de-la-base.ts'


// Lo que el panel necesita saber del que pide. Los cuatro datos viajan juntos
// porque se usan juntos: el `id` filtra la agenda, el nombre se muestra en
// pantalla y `esAdmin` decide qué puede hacer.
export type QuienPide = {
  id: number
  nombre: string
  apellido: string
  esAdmin: boolean
}


export async function quienPide(
  ctx: SupabaseContext< Database >,
): Promise< QuienPide | null > {

  // `userClaims` son los datos de adentro del token, ya verificado por la
  // librería contra las claves del proyecto.
  const correo = ctx.userClaims?.email

  // Un token válido sin correo no debería existir con las cuentas de hoy, pero
  // el tipo dice que la casilla puede venir vacía. Sin correo no hay a quién
  // buscar, y la consulta de abajo sin filtro devolvería la tabla entera.
  if ( !correo ) {
    return null
  }

  // La fila se busca por `email_de_acceso`, NO por `email`: aquélla es "a
  // dónde le aviso" y hoy guarda un reenvío, que no es una cuenta de Google.
  //
  // `activo = true` va en la consulta y no en un `if` posterior a propósito:
  // así dar de baja a un profesional lo echa del panel en el pedido siguiente,
  // sin ningún paso extra que alguien tenga que acordarse de hacer.
  const fila = await ctx.supabaseAdmin
    .from( 'profesionales' )
    .select( 'id, nombre, apellido, es_admin' )
    .eq( 'email_de_acceso', correo )
    .eq( 'activo', true )
    .maybeSingle()

  // Un error de base NO se puede confundir con "no es profesional": si la
  // consulta falló, no sabemos quién pide. Devolver `null` acá haría que el
  // endpoint contestara 403 y el que lo lea busque el problema en los
  // permisos, que es el lugar equivocado.
  if ( fila.error ) {
    throw fila.error
  }

  // Sin fila, el que pide no es personal de la clínica. No es un error: es la
  // respuesta, y el endpoint la convierte en 403.
  if ( !fila.data ) {
    return null
  }

  // El renombre de `es_admin` a `esAdmin` es a propósito y marca la frontera:
  // de acá para arriba el código habla en camelCase, como el resto del JS del
  // proyecto; `es_admin` es el nombre de la COLUMNA y se queda del lado de la
  // base.
  return {
    id: fila.data.id,
    nombre: fila.data.nombre,
    apellido: fila.data.apellido,
    esAdmin: fila.data.es_admin,
  }

}
