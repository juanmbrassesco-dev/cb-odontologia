-- La cobertura deja de poder faltar.
--
-- La columna nació anulable hace un rato, y era temporal: `POST /reservar`
-- todavía no mandaba el dato, así que exigirlo entonces habría hecho fallar
-- toda reserva nueva. Ahora lo manda, lo valida contra la tabla y lo guarda.
--
-- Quién defiende la regla, que es lo que decide esta migración: hasta ahora la
-- obligatoriedad vivía SÓLO en el portero, y el portero es código que se puede
-- cambiar de un despliegue a otro. Acá pasa a vivir en la base, que es el mismo
-- criterio que el proyecto ya aplicó con el `check` del canal y con las dos
-- cerraduras de permisos: el front no es una defensa, y el backend tampoco es
-- la última.
--
-- ⚠ LO QUE ESTO DECIDE SOBRE EL CONSULTORIO, y se decidió sabiéndolo (Juan,
-- 18-sep-2026): un turno cargado a mano TAMBIÉN va a exigir cobertura. Si
-- Cecilia agenda a alguien que en ese momento no sabe con qué viene, carga
-- `Particular`. En la práctica el caso existe; en la lógica del sistema no se
-- contempla. El costo aceptado es que `Particular` pasa a significar dos cosas
-- -- "paga de su bolsillo" y "no se sabía al cargar" -- y desde el dato no se
-- distinguen. Es barato hoy y lo pagaría un informe futuro, no la atención.
--
-- Entra sin dolor SÓLO porque `turnos` está vacía: se verificó antes de
-- escribir esta migración (cero filas, cero nulos). Sobre una tabla con filas
-- en null, la base rechaza el `alter table` entero y no lo aplica a medias.

alter table public.turnos
  alter column obra_social_id set not null;

comment on column public.turnos.obra_social_id is
  'Cobertura con la que se sacó el turno. Obligatoria en la base desde el 18-sep-2026: si no se sabe, va Particular.';
