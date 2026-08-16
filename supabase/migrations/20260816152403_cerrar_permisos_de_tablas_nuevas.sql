-- Una tabla nueva nace sin permisos para nadie.
--
-- La migración anterior limpió las siete tablas que existen hoy. No alcanza:
-- Postgres tiene una lista de "permisos por defecto" que se aplica sola a cada
-- tabla que se crea, y esa lista seguía repartiendo `truncate`, `references`,
-- `trigger` y `maintain` a los tres roles. La octava tabla habría nacido sucia
-- y nadie se habría enterado hasta la próxima auditoría.
--
-- Lo de hoy limpiaba el piso; esto cierra la canilla.

alter default privileges
  for role postgres
  in schema public
  revoke all
    on tables
    from
      anon,
      authenticated,
      service_role;

-- `for role postgres` NO elige a quién se le quita, sino QUIÉN crea la tabla.
-- Los permisos por defecto son una propiedad del creador: Postgres mira quién
-- está creando y aplica la lista de ese rol, sin heredar la de nadie más. En
-- este proyecto las tablas las crea `postgres`, tanto por migración como desde
-- el editor visual de Supabase — se verificó mirando las siete que ya existen.
-- A quién se le quita lo dice el `from` de abajo.
--
-- `service_role` va en la lista aunque sea el rol del portero, y es a propósito.
-- El proyecto ya habilita cada tabla a mano, con su `grant` escrito y
-- versionado; el regalo por defecto no le suma nada de lo que ya tiene. Lo que
-- cambia es qué pasa cuando alguien crea una tabla y se olvida del grant: hoy
-- funcionaría sola, y a partir de acá el portero falla con un `42501` bien
-- ruidoso. Un permiso de más pasa inadvertido; uno de menos avisa. Eso es lo que
-- se está comprando.
--
-- Sólo se tocan las TABLAS. Las secuencias creadas por `postgres` en este
-- esquema ya no le dan nada a los roles del navegador —verificado en
-- `pg_default_acl` antes de escribir esto—, así que revocarlas sería escribir
-- una línea que no hace nada y da la impresión de que hacía falta.
--
-- ⚠ Esta migración NO es la que recomienda la documentación de Supabase. La de
-- ellos revoca cuatro verbos por nombre —`select, insert, update, delete`— y por
-- eso deja afuera los cuatro que este proyecto encontró. Acá se dice `all` para
-- que la regla sea "ninguno" y no una lista que hay que mantener cuando Postgres
-- agregue un verbo nuevo. `maintain` es exactamente ese caso: no existía antes
-- de Postgres 17.
--
-- ⏳ Queda un frente que esta migración no toca: las FUNCIONES del esquema
-- `public` nacen con el `execute` abierto a todo el mundo, y hoy hay una,
-- `fin_del_turno`. Se decide aparte porque hay que probar antes si revocarla
-- rompe la restricción anti-solapamiento, que la evalúa en cada escritura.
