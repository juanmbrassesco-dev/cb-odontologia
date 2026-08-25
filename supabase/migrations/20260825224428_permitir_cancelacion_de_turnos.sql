-- El portero pasa de anotar turnos a poder APAGARLOS.

-- Cancelar, en este proyecto, no es borrar: es poner `activo = false` en una fila
-- que ya existe (regla del CLAUDE.md de CB, y el porqué está en 9.3). Y modificar
-- una fila que ya existe es un `update`, no un `insert` — por eso el permiso de la
-- migración 20260822221903 no alcanza y hace falta éste.
--
-- Sin esta línea, `POST /cancelar` falla con:
--
--     ERROR: 42501: permission denied for table turnos
--
-- Es el error de la PRIMERA cerradura, el GRANT, y es ruidoso a propósito: corta
-- antes de llegar a RLS. La segunda cerradura, la de filas, no entra en juego
-- porque la llave maestra del portero la atraviesa.
--
-- Esta migración estaba ANUNCIADA desde el 22-ago-2026: la que dio el `insert`
-- dice, con todas las letras, que el `update` "va a entrar con SU migración, para
-- que cada permiso tenga escrito al lado el porqué que lo justifica". Acá está.

grant update ( activo )
  on public.turnos
  to service_role;

-- Se da `update` y nada más. Los otros dos verbos que entrarían en la misma línea
-- no entran, y por motivos distintos:
--
-- 1. `all` juntaría los cuatro de una y taparía la decisión. El día que alguien
--    quiera saber por qué el portero puede modificar turnos, tiene que encontrar
--    una línea que diga sólo eso.
--
-- 2. `delete` NO SE VA A DAR NUNCA. En este proyecto no se borran filas: se apaga
--    el estado `activo`. Borrar un turno pasado además rompería el registro de lo
--    que efectivamente ocurrió en el consultorio.
--
-- Y no hace falta tocar el `execute` de `fin_del_turno`: `service_role` ya lo
-- tiene desde la migración 20260816153310, y lo necesita también acá. La
-- restricción anti-solapamiento lleva `where (activo)`, así que apagar una fila
-- la hace re-evaluarse, y esa evaluación corre con los permisos de quien escribe.

-- 🔒 EL PARÉNTESIS ES LA PARTE QUE MÁS IMPORTA DE ESTA MIGRACIÓN, y por eso no se
-- borra "para simplificar". Un `grant update` a secas habilita modificar CUALQUIER
-- columna de la tabla; acotado a `( activo )`, el portero puede apagar un turno y
-- nada más. No puede correrle la hora, ni cambiarle el paciente, ni tocar las
-- observaciones.
--
-- Se eligió acotar por dos razones, y cada una alcanza sola:
--
-- 1. Es la regla del proyecto. El 22-ago-2026 se pudo dar `insert` y `update`
--    juntos y se dio sólo el `insert`, con el motivo escrito: el permiso entra con
--    la funcionalidad que lo usa. Dar hoy las columnas que va a necesitar ⑤ sería
--    romper esa misma regla por adelantado.
--
-- 2. Es una defensa que no depende de que el código esté bien. Si `POST /cancelar`
--    tuviera un bug y escribiera `inicio`, Postgres lo rechaza igual — el mismo
--    razonamiento por el que la restricción anti-solapamiento vive en la base y no
--    en un `if` del portero.
--
-- ⏰ LO QUE ESTO CUESTA, dicho acá para que nadie lo debuguee a ciegas: el día que
-- el panel ⑤ reprograme un turno —mover `inicio`, escribir `nota`— va a fallar con
-- un error de privilegios (`42501`) aunque el rol "ya tenga update". No es un bug:
-- es este paréntesis. Se destraba con OTRA migración que agregue esas columnas, no
-- editando ésta.
