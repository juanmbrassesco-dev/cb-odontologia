-- El turno pasa a decir bajo qué cobertura se sacó.
--
-- La tabla `obras_sociales` ya existe con sus setenta y una filas, pero nada la
-- apuntaba todavía. Esta columna es la que hace que la cobertura sea un dato DEL
-- TURNO: el consultorio necesita saber, antes de atender, bajo qué concepto
-- viene cada paciente.
--
-- Vive acá y no en `pacientes` por una razón que conviene poder reconstruir: en
-- `pacientes` la columna describiría la cobertura de HOY, y el día que alguien
-- cambie de obra social los turnos viejos pasarían a mentir sobre bajo qué
-- concepto se sacaron. El turno tiene que poder decirlo siempre.
--
-- `on delete restrict`, como en las otras cuatro referencias de esta tabla: un
-- convenio que se cae se apaga con `activa`, no se borra. Borrarlo dejaría
-- turnos apuntando a una fila que ya no existe.

alter table public.turnos
  add column obra_social_id bigint
    constraint turnos_obra_social_id_fkey
      references public.obras_sociales ( id )
      on delete restrict;


-- ANULABLE DE FORMA TEMPORAL, y hay que decirlo fuerte porque al lado hay una
-- columna que se ve igual y no lo es: el vacío de `motivo_consulta_id` es
-- permanente y significa "el paciente no eligió"; el vacío de esta columna no
-- significa nada, es una migración que todavía no se escribió.
--
-- El campo es obligatorio en el formulario del paciente. No nace `not null`
-- porque `POST /reservar` todavía no manda el dato, y ponerlo hoy haría fallar
-- toda reserva nueva y las cuatro baterías con ella. Se agrega en cuanto el
-- portero mande el campo, y sale barato: `turnos` tiene cero filas, y un
-- `not null` sobre una tabla con filas nulas hace fallar el `alter table`
-- entero.

comment on column public.turnos.obra_social_id is
  'Cobertura con la que se sacó el turno. Obligatoria en el formulario; anulable en la base hasta que POST /reservar la mande.';
