-- Habilita la tabla `tratamientos` SOLO para el portero (service_role).
--
-- Modelo portero-only: el navegador (rol `anon`) NO recibe permiso, ni acá ni
-- en ninguna otra tabla. Si algún día `anon` necesita leer algo, es señal de
-- que se rompió el modelo, no de que falta un grant.
--
-- Hace falta porque Supabase ya no expone automáticamente las tablas nuevas a
-- los roles del Data API: cada tabla se habilita a mano, a propósito.

grant select on public.tratamientos to service_role;
