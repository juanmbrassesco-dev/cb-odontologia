-- El portero pasa de mirar la agenda a escribir en ella.

-- Hasta hoy `turnos` tenía un solo permiso para `service_role`: `select`. Con eso
-- alcanzaba, porque los dos endpoints que existen sólo leen. `POST /reservar` es
-- el primero que anota una fila, y sin esta línea falla con:
--
--     ERROR: 42501: permission denied for table turnos
--
-- Ese es el error de la PRIMERA cerradura, el GRANT, y es el ruidoso a propósito:
-- corta antes de llegar siquiera a RLS. La segunda cerradura, la de filas, no
-- entra en juego acá porque la llave maestra del portero la atraviesa.

grant insert
  on public.turnos
  to service_role;

-- Se da `insert` y NADA MÁS, aunque en la misma línea entraran los cuatro verbos.
--
-- `update` y `delete` no se adelantan: la cancelación (④) va a necesitar el
-- `update` y va a entrar con SU migración, para que cada permiso tenga escrito al
-- lado el porqué que lo justifica. Un `grant` sin motivo a la vista es un permiso
-- que nadie se anima a sacar después, porque nadie sabe qué rompe.
--
-- `delete` no se va a dar nunca: en este proyecto no se borran filas, se apaga el
-- estado `activo` (regla del CLAUDE.md de CB).

-- Dos cosas que NO hacen falta, y conviene decirlas para que nadie las agregue
-- "por las dudas" en la próxima migración:
--
-- 1. No hay `grant` sobre la secuencia del `id`. Las siete tablas usan columnas
--    *identity* (`generated always as identity`), y ahí el número lo pone el motor
--    como parte del propio `insert`: no hay una secuencia que el rol tenga que
--    tocar por su cuenta. Con `serial` —la forma vieja— sí habría hecho falta.
--
-- 2. No se toca el `execute` sobre `fin_del_turno`. Ya lo tiene `service_role`
--    desde la migración 20260816153310, y ES IMPRESCINDIBLE PARA ESTE INSERT: la
--    restricción anti-solapamiento evalúa esa función en cada escritura, con los
--    permisos de quien escribe. Si alguien la revoca, la reserva deja de andar.
