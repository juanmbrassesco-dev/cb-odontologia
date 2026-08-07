-- Cierra la primera cerradura en `pacientes`, la única tabla con datos personales.
--
-- Se detectó el 7-ago-2026, al verificar la base tabla por tabla: el rol `anon`
-- —el navegador— tenía SELECT, INSERT, UPDATE y DELETE sobre `pacientes`. Son
-- los cuatro verbos que la API expone hacia afuera, y contradicen la regla del
-- proyecto: en el modelo portero-only, `anon` no tiene permiso en ninguna tabla.
-- No salió de ninguna migración de este repo; venía del panel, de cuando se creó
-- la tabla.
--
-- No había filtración: RLS está encendido y no hay ninguna policy escrita, así
-- que la segunda cerradura tapaba a la primera. El problema era estar sostenido
-- por una sola de las dos, justo acá.
--
-- Se quita TODO y no solo los cuatro verbos: `anon` no necesita nada sobre
-- ninguna tabla, y "no tiene ni un permiso" es una frase que se puede verificar
-- de un vistazo. Se incluye `authenticated` por el mismo motivo: un visitante
-- logueado tampoco le habla a la base, le habla al portero.
--
-- `service_role` queda intacto: es el portero, y es el único que entra.

revoke all on public.pacientes from anon;

revoke all on public.pacientes from authenticated;
