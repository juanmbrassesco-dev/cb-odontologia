// Portero de CB Odontología — endpoint público GET /tratamientos
//
// Pide la lista de tratamientos DOS veces, para ver la diferencia:
//   - con los permisos del visitante  -> el RLS lo frena
//   - con la llave maestra            -> el RLS lo deja pasar

import { withSupabase } from 'npm:@supabase/server@^1'

export default {
  fetch: withSupabase({ auth: 'none' }, async (req, ctx) => {

    // respeta el RLS: la tabla no tiene ninguna regla que permita leer
    const conRLS = await ctx.supabase.from('tratamientos').select('nombre')

    // llave maestra: atraviesa el RLS
    const sinRLS = await ctx.supabaseAdmin.from('tratamientos').select('nombre')

    return Response.json({ conRLS, sinRLS })
  }),
}
