-- La agenda pasa a decir de quién es.
--
-- `profesionales` ya existe, pero ninguna de las tablas de agenda la mira: hoy
-- `horarios_base` guarda "los martes de 11:00 a 12:30" sin decir de quién, y
-- `turnos` guarda un turno sin decir quién lo atiende. Mientras eso siga así,
-- `GET /horarios-disponibles` no se puede escribir: recibe un profesional y no
-- tiene contra qué filtrar.
--
-- Las tres columnas van juntas porque son la misma pregunta —¿de quién?—
-- contestada en las tres tablas que forman la agenda. Se verificó que las tres
-- están vacías, así que las obligatorias entran sin default y sin backfill: la
-- trampa del NOT NULL que apareció al construir `pacientes` no aplica acá.


alter table public.horarios_base
  add column profesional_id bigint
    not null
    references public.profesionales (id)
    on delete restrict;

-- Obligatoria: un tramo de agenda que no es de nadie no significa nada. Los 7
-- tramos que se carguen después pasan a ser, explícitamente, los de Cecilia.


alter table public.turnos
  add column profesional_id bigint
    not null
    references public.profesionales (id)
    on delete restrict;

-- Obligatoria por el mismo motivo, y además es la columna sobre la que se apoya
-- la restricción anti-solapamiento de la migración siguiente: sin saber de quién
-- es cada turno, la base no puede distinguir dos turnos que se pisan de dos
-- profesionales atendiendo en salas distintas a la misma hora, que es el
-- funcionamiento normal del consultorio.


alter table public.excepciones
  add column profesional_id bigint
    references public.profesionales (id)
    on delete restrict;

-- Ésta es la única OPCIONAL, y el vacío es información, no un dato faltante:
-- una excepción sin profesional tapa a TODA la clínica (un feriado, un cierre),
-- y con profesional es la ausencia de una sola persona. Poner NOT NULL obligaría
-- a repetir cada feriado una vez por cada profesional del plantel.


-- `on delete restrict` en las tres: si alguien intenta borrar un profesional que
-- todavía tiene agenda o turnos, la base lo frena en vez de arrastrarse las filas
-- que cuelgan de él. Es la regla del proyecto — no se borran filas, se apaga el
-- estado con `activo`.
