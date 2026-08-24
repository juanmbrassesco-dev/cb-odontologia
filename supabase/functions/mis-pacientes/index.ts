// Portero de CB Odontología — endpoint GET /mis-pacientes
//
// EL PRIMERO QUE EXIGE SESIÓN INICIADA. Los otros dos son públicos a
// conciencia; éste toca la única tabla con datos personales.
//
// Contesta una sola pregunta: ¿a qué pacientes puede pedirle turno el que
// está conectado? Un correo puede devolver VARIAS filas —una madre anota a
// sus hijos con su casilla (§ 9.8)—, así que la respuesta es una lista, no
// una ficha. Es lo que llena el desplegable "¿para quién es el turno?".
//
// 🔒 DEVUELVE TRES COLUMNAS Y NADA MÁS: id, nombre y apellido. Ni DNI, ni
// teléfono, ni fecha de nacimiento. No es que no hagan falta hoy: es que un
// dato que no sale no se puede filtrar por accidente mañana, cuando alguien
// arme otra pantalla con esta misma respuesta.
//
// 🔒 Y EL CORREO NO VIAJA EN EL PEDIDO: sale del token de la sesión. Si el
// pedido lo trajera, cualquiera escribiría el ajeno y leería sus pacientes.
// El portero no le pregunta al cliente quién es; se lo pregunta al token.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`, y la ausencia es la decisión: la
// plataforma exige un JWT válido por defecto, y los otros dos endpoints lo
// APAGAN con `verify_jwt = false`. Acá se lo deja prendido. Agregarle ese
// bloque a este archivo sería abrir la puerta, no configurarla.

import { withSupabase } from 'npm:@supabase/server@^1'

// Los tipos de la base entran por acá. No cambian NADA de lo que el endpoint
// hace: son para que TypeScript sepa qué columnas existen y avise en el editor
// cuando una consulta pide algo que no está.

import type { Database } from '../_shared/tipos-de-la-base.ts'

// Un fallo de la base se contesta SIN el detalle: el texto de Postgres nombra
// tablas, columnas y roles.
function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo leer la lista' },
    { status: 500 },
  )
}

export default {

  fetch: withSupabase< Database >(
    { auth: 'user' },
    async ( _req, ctx ) => {

      // De acá sale la identidad, y es el corazón del endpoint. `userClaims`
      // son los datos que vienen adentro del token, ya verificado por la
      // librería contra las claves del proyecto: no es lo que el cliente dice
      // ser, es lo que el sistema de cuentas firmó.
      const correo = ctx.userClaims?.email

      // Un token válido sin correo no debería existir con las cuentas que hay
      // hoy —sólo correo y contraseña, sin teléfono ni anónimos—, pero el tipo
      // dice que la casilla puede venir vacía y por eso se contesta en vez de
      // seguir. Sin correo no hay ancla, y sin ancla la consulta de abajo
      // devolvería la tabla entera.
      //
      // El mensaje es genérico a propósito. Antes decía "la sesión no trae
      // correo" y lo levantó Juan el 23-ago-2026: un error que describe el
      // estado interno del sistema es *divulgación de información*
      // (information disclosure), aunque acá el que lo lee ya tenga el token
      // en la mano y pueda leerlo solo. Lo que decide es otra cosa: esta rama
      // NO SE PUEDE ALCANZAR con la configuración de cuentas de hoy, así que
      // el texto descriptivo no le sirve a nadie para depurar y sí se copia y
      // pega a lugares donde el que lee no tiene nada.
      if ( !correo ) {
        return Response.json(
          { error: 'Sesión no válida' },
          { status: 403 },
        )
      }

      // ⚠ NO se mira `email_verified`, y NO es un olvido — se probó contra el
      // proyecto real el 23-ago-2026:
      //
      //   1. ese dato vive en `user_metadata`, que el propio usuario puede
      //      reescribir con un pedido a `/auth/v1/user`. Lo escrito aparece
      //      en el token siguiente. Un dato que el interesado edita no sirve
      //      para decidir si confiar en él.
      //   2. la garantía real está en el panel: con "Confirm email" prendido,
      //      una cuenta sin confirmar no llega a tener sesión, así que acá no
      //      entra nadie sin verificar.
      //
      // 🔴 Si alguna vez se apaga esa opción del panel, el ancla de este
      // endpoint se vuelve falsificable: cualquiera se registra con el correo
      // de otro y le ve los pacientes. El chequeo que haría falta entonces NO
      // es leer el token, es preguntarle al servidor de cuentas.

      const pacientes = await ctx.supabaseAdmin
        .from( 'pacientes' )
        .select( 'id, nombre, apellido' )
        .eq( 'email', correo )
        .order( 'apellido' )
        .order( 'nombre' )

      if ( pacientes.error ) {
        return falloDeBase()
      }

      // La lista vacía es una respuesta válida, no un error: es el paciente
      // que entra por primera vez. La pantalla que la reciba ofrece el alta.
      return Response.json( pacientes.data )
    },
  ),

}
