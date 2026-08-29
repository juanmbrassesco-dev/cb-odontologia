-- EL TURNO PASA A RECORDAR QUÉ HORA SE LE COMUNICÓ AL PACIENTE.
--
-- `aviso_estado` guarda QUÉ sabe el paciente —nada, reservado o cancelado—.
-- Esta columna guarda CUÁNDO le dijimos que era. Son dos preguntas distintas y
-- por eso son dos columnas.
--
-- 🔴 PARA QUÉ, con el caso concreto. Cecilia mueve un turno de hora desde el
-- Table Editor. El trigger de la migración 20260828204527 borra `aviso_estado`
-- —lo que el paciente creía dejó de ser cierto— y la repesca manda un correo
-- nuevo que dice "tu turno quedó agendado, 3/9 a las 09:00". En la casilla del
-- paciente hay OTRO correo que dice "29/8 a las 06:00", y ninguno de los dos
-- dice que uno reemplaza al otro: lee dos turnos, no un cambio, y se presenta
-- al viejo.
--
-- Con esta columna el correo puede nombrar la hora que reemplaza. Es UN dato y
-- ninguna lógica nueva: no hace falta saber si el turno nació o se movió —que
-- era mi propuesta y estaba mirando el problema equivocado—, alcanza con
-- recordar la última hora avisada y compararla con la actual.
--
-- 🔴 Y EL TRIGGER NO LA TOCA, que es lo único que hace que sirva. El trigger
-- corre `before update`, o sea en el único instante en que las dos horas
-- existen a la vez. Si ahí la borrara, la hora vieja desaparecería para siempre
-- y la repesca —que llega segundos después— sólo podría nombrar la nueva, que
-- es el correo mudo que tenemos hoy. `aviso_estado` se borra porque DEJÓ DE SER
-- CIERTO; esta columna no se borra porque nunca deja de serlo: la hora que se
-- le dijo sigue siendo la que se le dijo.
--
-- (Lo pidió Juan el 28-ago-2026; el detalle y las dos alternativas descartadas,
-- en 13.15 del doc de estado.)


alter table public.turnos
  add column inicio_avisado timestamptz;


comment on column public.turnos.inicio_avisado is
  'Qué hora se le comunicó al paciente la última vez. Vacía si nunca se le avisó nada. No es la hora del turno, que la dice inicio: cuando las dos difieren, el turno se movió y el paciente todavía no lo sabe.';


-- 🔴 LOS TURNOS QUE YA EXISTEN NACEN CON LA COLUMNA VACÍA, Y ESO ES MENTIRA.
--
-- Mismo relleno y mismo motivo que el de `aviso_estado` en la migración
-- 20260828204527: a esta gente YA se le dijo su hora cuando reservó, y su
-- correo la nombra. Sin esta línea, el día que a alguno le muevan el turno el
-- correo nuevo saldría sin poder nombrar lo que reemplaza — que es justamente
-- el caso que esta columna viene a cubrir.
--
-- Sólo los activos, igual que allá: de un turno ya cancelado no va a salir
-- ningún correo más, así que no hay nada que comparar.
--
-- ⚠ ESTE `update` DISPARA EL TRIGGER Y NO PASA NADA, y conviene saber por qué:
-- el trigger sólo borra la marca si cambió alguno de los cinco datos que el
-- correo nombra, y acá no cambia ninguno —`inicio` llega en `new` con el mismo
-- valor que en `old`, porque un `update` que no la nombra no la cambia—. Es la
-- misma propiedad por la que la repesca no se dispara a sí misma.

update public.turnos
  set inicio_avisado = inicio
  where activo;


-- 🔒 EL PERMISO CRECE CON LO QUE EL PORTERO HACE, NI UNA COLUMNA MÁS.
--
-- Eran tres columnas desde la migración 20260828204527; ahora son cuatro,
-- porque `reservar`, `cancelar` y la repesca escriben también la hora avisada.
-- Sigue siendo un grant ACOTADO POR COLUMNAS: una quinta no se va a poder
-- escribir hasta que alguien la nombre acá.
--
-- Se repiten las cuatro y no se agrega sólo la nueva: los permisos de columna
-- se suman, así que las dos formas funcionan, pero ésta deja la lista completa
-- a la vista en el archivo más nuevo. La otra obliga a leer dos migraciones
-- para saber qué puede escribir el portero.

grant update ( activo, aviso_estado, aviso_at, inicio_avisado )
  on public.turnos
  to service_role;
