// Portero de CB Odontología — endpoint POST /alta-de-profesional
//
// Registra a alguien nuevo en el plantel. Sólo admin.
//
// 🔴 ES DE NIVEL, NO DE PROPIEDAD: no hay nada que sea "de uno" acá. Un
// profesional con sesión válida recibe 403, y la razón no es de pantalla —
// quien puede dar de alta puede crearse una fila con `es_admin: true` y
// repartirse permisos. Es la puerta más cara de toda la fase.
//
// 🔒 `email_de_acceso` ES LA COLUMNA POR LA QUE SE ENTRA, y no es la misma que
// `email`. Aquélla es a dónde se le avisan sus turnos; ésta es la cuenta de
// Google con la que entra al panel. El 6-oct `profesionales.email` quedó en un
// reenvío —`contacto@…`, que no es un buzón de Google—, y por eso son dos
// columnas: si fueran una, Cecilia no podría entrar.
//
// ⚠ VIENE OPCIONAL A PROPÓSITO: se puede cargar a alguien que todavía no tiene
// cuenta —existe en la agenda, se le pueden asignar turnos— y completarla
// después. Lo que no se puede es que entre al panel sin ella.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y
// acá se lo deja prendido.
//
// ✅ MIGRACIÓN: `permitir_alta_de_profesionales`, que da el `insert` por
// columnas. `id`, `created_at` y `activo` quedan fuera a propósito — los pone
// la base, y un alta que pudiera escribir `activo` podría nacer apagada.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'


// El código que Postgres devuelve cuando una fila choca contra un `unique`.
// Vale para los DOS de esta tabla: `email` y `email_de_acceso`.
const YA_EXISTE = '23505'


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo dar de alta' },
    { status: 500 },
  )
}


function sinAcceso(): Response {

  return Response.json(
    { error: 'Sin acceso a esta solapa' },
    { status: 403 },
  )
}


// Un texto que llegó del pedido, limpio y sin espacios de sobra. Devuelve
// cadena vacía si no vino o si no es texto: el que valida es el `if`, no esto.
function textoDelPedido( valor: unknown ): string {

  if ( typeof valor !== 'string' ) {
    return ''
  }

  return valor.trim()
}


export default {

  fetch: withSupabase< Database >(
    { auth: 'user' },
    async ( req, ctx ) => {

      // ── 1. La cerradura ───────────────────────────────────────────────────

      let quien

      try {
        quien = await quienPide( ctx )
      }
      catch {
        return falloDeBase()
      }

      if ( !quien ) {
        return sinAcceso()
      }

      if ( !quien.esAdmin ) {
        return sinAcceso()
      }

      // ── 2. El pedido ──────────────────────────────────────────────────────

      let cuerpo

      try {
        cuerpo = await req.json()
      }
      catch {
        return Response.json(
          { error: 'El pedido no trae un cuerpo JSON' },
          { status: 400 },
        )
      }

      const nombre = textoDelPedido( cuerpo.nombre )
      const apellido = textoDelPedido( cuerpo.apellido )
      const email = textoDelPedido( cuerpo.email )

      if ( !nombre || !apellido ) {
        return Response.json(
          { error: 'Faltan el nombre o el apellido' },
          { status: 400 },
        )
      }

      // 🔑 EL CORREO ES OBLIGATORIO ACÁ Y OPCIONAL EN `pacientes`, y la
      // diferencia está escrita en la migración que creó la tabla: es el canal
      // por el que se le avisan sus turnos. Un profesional sin correo no se
      // entera de nada de lo que le agendan.
      if ( !email ) {
        return Response.json(
          { error: 'Falta el correo' },
          { status: 400 },
        )
      }

      // 🔒 LA CUENTA DE ACCESO SE GUARDA EN MINÚSCULAS, y no hace falta
      // bajarla acá: lo hace un disparador de la base, de la migración del
      // 8-oct. Se nombra para que nadie lo agregue dos veces.
      const acceso = textoDelPedido( cuerpo.email_de_acceso )

      // 🔴 `es_admin` SE LEE COMO BOOLEAN ESTRICTO, nunca como "lo que venga".
      // Con `Boolean( cuerpo.es_admin )` un `"false"` de texto —que es lo que
      // manda un formulario mal armado— daría `true`, y eso reparte permisos
      // de administrador por un error de tipeo.
      const esAdmin = cuerpo.es_admin === true

      // ── 3. El alta ────────────────────────────────────────────────────────

      const nuevo = await ctx.supabaseAdmin
        .from( 'profesionales' )
        .insert( {
          nombre: nombre,
          apellido: apellido,
          email: email,

          // Vacío se guarda como NULO y no como cadena vacía: la columna es
          // `unique`, y dos filas con '' chocarían entre ellas. Nulo no choca
          // con nulo.
          email_de_acceso: acceso || null,

          es_admin: esAdmin,
        } )
        .select( 'id, nombre, apellido, es_admin' )
        .single()

      if ( nuevo.error ) {

        // 🔑 EL CHOQUE CONTRA EL `unique` NO ES UN ERROR DEL SISTEMA: es una
        // persona que ya está cargada. Se contesta 409 y no 500, porque nadie
        // se equivocó — y el texto dice cuál de los dos correos chocó, que es
        // lo único que permite arreglarlo.
        if ( nuevo.error.code === YA_EXISTE ) {

          return Response.json(
            {
              error: 'Ya hay alguien cargado con ese correo',
              detalle: nuevo.error.message,
            },
            { status: 409 },
          )
        }

        console.error( 'No se pudo dar de alta:', nuevo.error )

        return falloDeBase()
      }

      return Response.json( { alta: nuevo.data }, { status: 201 } )
    },
  ),

}
