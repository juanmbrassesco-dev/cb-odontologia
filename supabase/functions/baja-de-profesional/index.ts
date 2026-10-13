// Portero de CB Odontología — endpoint POST /baja-de-profesional
//
// Apaga a alguien del plantel, o lo vuelve a prender. Sólo admin.
//
// 🔴 APAGAR, NUNCA BORRAR. Los turnos pasados apuntan al profesional con una
// foreign key `restrict`: la base rechazaría el `delete`, y forzarlo se
// llevaría puesto el historial de todo lo que esa persona atendió. Por eso
// esta etapa no tiene un endpoint de borrado y no lo va a tener.
//
// 🔴 LO QUE ESTO NO HACE, Y HAY QUE SABERLO ANTES DE USARLO: apagar a alguien
// NO cancela sus turnos futuros ni le avisa a ningún paciente. Si renuncia con
// seis turnos reservados, quedan seis personas que van a viajar al consultorio
// a ver a alguien que no está. Se resuelven por teléfono, con la lista que
// devuelve `GET /turnos-del-profesional`.
//
// ⚠ Y ESO ES UNA DECISIÓN, no una limitación: cancelar en lote dispararía
// seis correos de «te cancelamos el turno» sin ofrecer uno nuevo, que es
// peor que la llamada. La solución es de Juan, 6-ago-2026.
//
// 🔑 EL MISMO ENDPOINT PRENDE Y APAGA, y por eso recibe `activo` en vez de ser
// dos puertas. Volver a prender a alguien escribe exactamente las mismas dos
// columnas con otros valores; separarlos sería duplicar la cerradura y el
// chequeo para cambiar un boolean.
//
// ⚠ NO LLEVA BLOQUE EN `config.toml`: la plataforma exige JWT por defecto y
// acá se lo deja prendido.
//
// ✅ MIGRACIÓN: `permitir_baja_de_profesionales`, que da el `update` sobre
// EXACTAMENTE `activo` y `fecha_baja`. Sin `es_admin` ni `email_de_acceso`: un
// error acá no puede repartir permisos de administrador, porque la base lo
// rechaza antes.

import { withSupabase } from 'npm:@supabase/server@^1'

import type { Database } from '../_shared/tipos-de-la-base.ts'

import { quienPide } from '../_shared/quien-pide.ts'


function falloDeBase(): Response {

  return Response.json(
    { error: 'No se pudo cambiar el estado' },
    { status: 500 },
  )
}


function sinAcceso(): Response {

  return Response.json(
    { error: 'Sin acceso a esta solapa' },
    { status: 403 },
  )
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

      const profesionalId = Number( cuerpo.profesional_id )

      // La presencia se chequea antes de convertir, por lo mismo que cazó el
      // caso 24: `Number( null )` da CERO, no NaN.
      if (
        cuerpo.profesional_id === undefined
        || cuerpo.profesional_id === null
        || !Number.isInteger( profesionalId )
        || profesionalId < 1
      ) {
        return Response.json(
          { error: 'Falta profesional_id, o no es un número entero válido' },
          { status: 400 },
        )
      }

      // 🔑 `activo` LLEGA COMO BOOLEAN ESTRICTO. Si no viene, se asume que la
      // acción es APAGAR, que es la que tiene nombre propio en la pantalla.
      const prender = cuerpo.activo === true

      // ── 3. LA LÍNEA QUE EVITA EL BLOQUEO TOTAL ────────────────────────────
      //
      // 🔴 NADIE SE PUEDE APAGAR A SÍ MISMO, y no es una cortesía: la cerradura
      // del panel busca la fila con `activo = true`, así que un admin que se
      // apaga pierde el acceso EN EL PEDIDO SIGUIENTE. Si además era el único
      // admin, ya no queda nadie que pueda volver a prenderlo desde el panel —
      // hay que entrar al Table Editor de Supabase, que es exactamente lo que
      // este panel existe para evitar.
      //
      // Se contesta 409 y no 403: no es un permiso que falte, es una acción que
      // no tiene sentido. Y el texto lo dice, porque el que la intenta no está
      // atacando nada.
      if ( !prender && profesionalId === quien.id ) {

        return Response.json(
          {
            error: 'No podés darte de baja a vos mismo',
            detalle: 'Perderías el acceso al panel y nadie podría'
              + ' devolvértelo desde acá.',
          },
          { status: 409 },
        )
      }

      // ── 4. El cambio de estado ────────────────────────────────────────────
      //
      // 🔑 LAS DOS COLUMNAS VIAJAN JUNTAS porque las escribe una sola acción:
      // `activo` dice si sigue y `fecha_baja` desde cuándo no. Al volver a
      // prender, la fecha se limpia — si quedara puesta, la fila diría «en
      // actividad» y «de baja el 12 de agosto» a la vez.
      //
      // ⚠ Esto PISA la baja anterior, y es la consecuencia aceptada de que la
      // tabla guarde un estado y no una historia. Si algún día importa el ir y
      // venir de alguien que se va y vuelve, el camino limpio es una tabla de
      // eventos — está escrito en la migración que creó `profesionales`.
      const cambiado = await ctx.supabaseAdmin
        .from( 'profesionales' )
        .update( {
          activo: prender,
          fecha_baja: prender ? null : new Date().toISOString(),
        } )
        .eq( 'id', profesionalId )

        // 🔴 EL `.eq( 'activo', … )` NO ES UNA COPIA DEL FILTRO DE ARRIBA: es
        // lo que hace que el segundo clic no haga nada. Sin él, apagar dos
        // veces reescribe `fecha_baja` con el momento del segundo clic y la
        // fila miente sobre cuándo se fue.
        .eq( 'activo', !prender )
        .select( 'id, nombre, apellido, activo, fecha_baja' )
        .maybeSingle()

      if ( cambiado.error ) {
        console.error( 'No se pudo cambiar el estado:', cambiado.error )
        return falloDeBase()
      }

      // Sin fila: o el id no existe, o ya estaba en el estado que se pidió. Las
      // dos se contestan igual —no hay nada que hacer— y con 200, porque el
      // mundo ya está como el que pidió quería que estuviera.
      if ( !cambiado.data ) {

        return Response.json( {
          cambiado: null,
          yaEstaba: true,
        } )
      }

      return Response.json( {
        cambiado: cambiado.data,
        yaEstaba: false,
      } )
    },
  ),

}
