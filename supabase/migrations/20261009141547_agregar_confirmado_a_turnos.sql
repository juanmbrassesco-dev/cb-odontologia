-- CUÁNDO EL PACIENTE CONFIRMÓ QUE SE ENTERÓ DE SU TURNO.
--
-- La forma se decidió el 25-ago-2026 y está escrita en la § 9.3 del documento
-- de estado; acá se construye tal cual, sin reabrirla.
--
-- 🔑 POR QUÉ NO VA EN `activo`, que es la pregunta que todos hacen primero.
-- `activo` contesta UNA sola cosa: ¿este turno ocupa el hueco? Un turno sin
-- confirmar OCUPA —si no, la web lo vendería dos veces—, así que nace con
-- `activo = true` igual que cualquier otro. Un tercer valor sobre `activo`
-- rompería esa columna; una columna aparte no toca nada.
--
-- 🔑 Y POR QUÉ UNA FECHA Y NO UN BOOLEAN: es la misma forma que
-- `profesionales.fecha_baja`. No es un estado, es un HECHO CON SU MOMENTO.
-- Vacía dice «todavía no contestó»; con fecha dice «confirmó, y cuándo».
-- Un boolean guardaría la mitad de eso por el mismo espacio.
--
-- ⚠ ANULABLE Y SIN `default`, Y LAS DOS COSAS SON LA DECISIÓN. Si llevara
-- `default now()`, los turnos que carga Cecilia a mano nacerían confirmados
-- solos y la columna no distinguiría nada: la escribe quien SABE que hubo
-- confirmación. `POST /reservar` la pone con la hora del momento —un turno web
-- está confirmado por construcción, lo hizo el paciente— y el turno del panel
-- la deja vacía hasta que alguien conteste.
--
-- 🔒 QUÉ PROBLEMA RESUELVE, con su nombre: un correo VÁLIDO PERO AJENO. Si
-- Cecilia tipea `juan@` donde iba `juana@`, la dirección existe, no rebota, y
-- ninguna validación de formato la caza. Lo único que lo delata es que nadie
-- conteste nunca. Verificar que alguien controla la casilla se llama DOUBLE
-- OPT-IN (doble aceptación).
--
-- ⬜ Lo que esta migración NO trae, y es a propósito: el flujo para confirmar
-- (el link del correo, la pantalla, el `grant update` de esta columna). Entra
-- en la etapa ⑤.3.b. La columna va primero para que los turnos que se carguen
-- desde hoy nazcan con el dato bien puesto: eso no se reconstruye después.

alter table public.turnos
  add column confirmado_en timestamptz;

comment on column public.turnos.confirmado_en is
  'Cuándo el paciente confirmó que se enteró del turno. Vacía = todavía no contestó. La escribe POST /reservar con la hora del momento; un turno cargado a mano nace vacío.';
