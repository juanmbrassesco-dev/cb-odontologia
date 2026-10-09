// Portero de CB Odontología — endpoint POST /paciente-del-panel
//
// El alta de ficha EN EL ACTO (§ 9.4): Cecilia va a cargar un turno de alguien
// que no está en la base y crea la ficha ahí mismo, sin salir del flujo.
//
// 🔴 POR QUÉ ES UN ENDPOINT PROPIO Y NO PARTE DEL TURNO. Son dos cosas, y la
// regla del proyecto es «una cosa, un trabajo». Lo concreto: si el turno choca
// con otro y la base lo rechaza con un 409, la ficha ya creada NO es basura —
// Cecilia la quería igual y va a volver a intentar el turno. Metidos en el
// mismo endpoint habría que decidir si se deshace el alta, y la respuesta
// correcta sería «no», o sea código para no hacer nada.
//
// 🔒 EL CORREO SE PIDE DOS VECES, Y ES LA ÚNICA DEFENSA QUE HAY ACÁ.
//
// En `POST /reservar` el correo sale del token de la sesión: lo puso Google,
// nadie lo tipeó. Acá lo tipea Cecilia escuchando un teléfono, y una letra de
// más produce una dirección que EXISTE, no rebota y pasa cualquier validación
// de formato — `juan@` donde iba `juana@`. A partir de ahí los avisos de esa
// persona le llegan a un desconocido, y nadie se entera nunca.
//
// Repetirlo no lo resuelve del todo —se puede tipear mal dos veces igual—,
// pero cuesta un campo y ataca el error real, que es el dedo, no el formato.
// La otra mitad del problema la cubre el DOUBLE OPT-IN (doble aceptación) de
// la etapa ⑤.3.b: hasta que el paciente conteste, `turnos.confirmado_en` queda
// vacío y el panel puede mostrarlo.
//
// ⚠ EL CORREO PUEDE FALTAR, y no es un descuido: `pacientes.email` acepta nulo
// porque Cecilia carga gente que sólo dejó un teléfono. Un paciente sin correo
// es una ficha válida — lo que no tiene es aviso, y el sistema no lo disimula.
//
// 🔑 LAS MINÚSCULAS NO SE HACEN ACÁ: las baja el disparador de la base. Hacerlo
// en los dos lados invita a que un día coincidan menos.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y
// acá se lo deja prendido.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'

import { esFechaValida } from '../_shared/disponibilidad.ts'

import {
  LARGO_MAXIMO_CORREO,
  LARGO_MAXIMO_DNI,
  LARGO_MAXIMO_NOMBRE,
  LARGO_MAXIMO_TELEFONO,
  textoLimpio,
} from '../_shared/texto.ts'


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo crear la ficha' },
    { status: 500 },
  )
}


function pedidoInvalido( detalle: string ): Response {

  return Response.json(
    { error: detalle },
    { status: 400 },
  )
}


// La comprobación más floja que sirve: algo, un arroba, algo con un punto.
//
// 🔑 A PROPÓSITO NO ES UNA EXPRESIÓN EXHAUSTIVA. Las direcciones válidas según
// la norma incluyen cosas que ninguna regex corta valida bien, y cada intento
// de cubrirlas termina rechazando correos reales — que es el peor error
// posible acá: dejar a un paciente afuera por un apellido con tilde o un
// dominio raro. Lo que de verdad verifica una dirección es que alguien
// conteste, y de eso se encarga el doble opt-in.
function pareceCorreo( valor: string ): boolean {

  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test( valor )
}


export default {

  fetch: withSupabase< Database >(
    { auth: 'user' },
    async ( req, ctx ) => {

      if ( req.method !== 'POST' ) {
        return Response.json(
          { error: 'Este endpoint sólo acepta POST' },
          { status: 405 },
        )
      }

      // ── 1. La cerradura, antes de mirar el cuerpo ─────────────────────────

      let quien

      try {
        quien = await quienPide( ctx )
      }
      catch {
        return falloDeBase()
      }

      if ( !quien ) {
        return Response.json(
          { error: 'Sin acceso al panel' },
          { status: 403 },
        )
      }

      // ── 2. El cuerpo ──────────────────────────────────────────────────────

      let cuerpo

      try {
        cuerpo = await req.json()
      }
      catch {
        return pedidoInvalido( 'El cuerpo del pedido no es JSON válido' )
      }

      const nombre = textoLimpio( cuerpo.nombre, LARGO_MAXIMO_NOMBRE )

      if ( !nombre ) {
        return pedidoInvalido( 'El nombre es obligatorio' )
      }

      const apellido = textoLimpio( cuerpo.apellido, LARGO_MAXIMO_NOMBRE )

      if ( !apellido ) {
        return pedidoInvalido( 'El apellido es obligatorio' )
      }

      // ── 3. El correo, con su repetición ───────────────────────────────────

      let correo: string | null = null

      // `cuerpo.email` vacío o ausente significa «esta persona no dejó correo»,
      // que es un caso real y previsto. Lo que no se acepta es un correo a
      // medias: si vino algo, tiene que ser válido y estar repetido.
      const correoCrudo = textoLimpio( cuerpo.email, LARGO_MAXIMO_CORREO )

      if ( correoCrudo ) {

        if ( !pareceCorreo( correoCrudo ) ) {
          return pedidoInvalido( 'El correo no tiene forma de correo' )
        }

        const repetido = textoLimpio(
          cuerpo.email_repetido,
          LARGO_MAXIMO_CORREO,
        )

        // La comparación va en minúsculas de los dos lados: que alguien escriba
        // la segunda vez con una mayúscula distinta NO es un error de tipeo, y
        // rebotarlo sería inventar un problema. La base guarda en minúsculas
        // igual, por el disparador.
        if (
          !repetido
          || repetido.toLowerCase() !== correoCrudo.toLowerCase()
        ) {
          return pedidoInvalido( 'Los dos correos no coinciden' )
        }

        correo = correoCrudo
      }

      // ── 4. Lo opcional ────────────────────────────────────────────────────

      let telefono: string | null = null

      if ( cuerpo.telefono !== undefined && cuerpo.telefono !== '' ) {

        telefono = textoLimpio( cuerpo.telefono, LARGO_MAXIMO_TELEFONO )

        if ( !telefono ) {
          return pedidoInvalido( 'El teléfono no es válido' )
        }
      }

      let dni: string | null = null

      if ( cuerpo.dni !== undefined && cuerpo.dni !== '' ) {

        dni = textoLimpio( cuerpo.dni, LARGO_MAXIMO_DNI )

        if ( !dni ) {
          return pedidoInvalido( 'El DNI no es válido' )
        }
      }

      let fechaNacimiento: string | null = null

      if (
        cuerpo.fecha_nacimiento !== undefined
        && cuerpo.fecha_nacimiento !== ''
      ) {

        if (
          typeof cuerpo.fecha_nacimiento !== 'string'
          || !esFechaValida( cuerpo.fecha_nacimiento )
        ) {
          return pedidoInvalido(
            'La fecha de nacimiento va en formato AAAA-MM-DD',
          )
        }

        fechaNacimiento = cuerpo.fecha_nacimiento
      }

      // ── 5. El alta ────────────────────────────────────────────────────────
      //
      // 🔑 NO SE DEDUPLICA ACÁ, y es la misma decisión del 23-ago-2026 que
      // tomó `reservar`: fundir en una sola ficha a dos personas que comparten
      // casilla y apellido —una madre y su hijo— es un error que NO falla con
      // error, y se descubre tarde. La deduplicación vive en la mano de
      // Cecilia, con el buscador que corre ANTES de llegar acá.

      const alta = await ctx.supabaseAdmin
        .from( 'pacientes' )
        .insert( {
          nombre: nombre,
          apellido: apellido,
          email: correo,
          telefono: telefono,
          dni: dni,
          fecha_nacimiento: fechaNacimiento,
        } )
        .select( 'id, nombre, apellido, email, telefono' )
        .single()

      if ( alta.error ) {
        return falloDeBase()
      }

      return Response.json( { paciente: alta.data }, { status: 201 } )
    },
  ),

}
