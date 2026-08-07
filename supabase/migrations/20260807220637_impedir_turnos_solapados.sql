-- Dos pacientes no pueden quedarse con el mismo turno.
--
-- Un `if` en el endpoint no lo impide, y el motivo es el que importa:
-- PREGUNTAR y ESCRIBIR son dos pasos separados, y en el hueco entre uno y otro
-- entra el otro pedido. Dos personas reservando desde su celular preguntan
-- "¿libre las 11?" con milisegundos de diferencia, las dos reciben un "sí"
-- honesto —porque cuando preguntaron todavía estaba libre— y las dos escriben.
-- Poner otro `if`, o preguntar más rápido, no achica ese hueco: lo mueve.
--
-- La base es el único lugar donde las dos escrituras se cruzan de verdad, así
-- que es el único lugar donde se puede decidir quién queda afuera. Y como es una
-- restricción y no una función que alguien tiene que acordarse de llamar, la
-- aplica Postgres solo, en cada escritura, para siempre.


create extension if not exists btree_gist;

-- No es opcional y no se puede deducir del error. La restricción de más abajo
-- mezcla dos formas distintas de comparar —una igualdad sobre `profesional_id` y
-- un solapamiento sobre un rango de tiempo— y el índice GiST no sabe hacer la
-- primera hasta que este módulo se lo enseña. Sin esta línea, el `db push` falla
-- con un mensaje que no menciona la extensión por ningún lado.


create function public.fin_del_turno (
  inicio timestamptz,
  minutos integer
)
  returns timestamptz
  language sql
  immutable
  as $$
    select inicio + make_interval( mins => minutos )
  $$;

-- Esta función existe por una limitación del motor, no por el diseño.
--
-- El primer intento puso la cuenta directamente adentro de la restricción y
-- Postgres la rechazó:
--
--     ERROR: functions in index expression must be marked IMMUTABLE (42P17)
--
-- Un índice necesita que la cuenta dé SIEMPRE el mismo resultado; si cambiara,
-- quedaría apuntando a lugares equivocados sin avisar. Y sumarle un intervalo a
-- una fecha no siempre es determinista: un intervalo puede traer días o meses, y
-- sumar "un día" cruzando un cambio de horario de verano no es sumar 24 horas.
-- Postgres no revisa si en este caso solo se suman minutos — bloquea la
-- operación entera.
--
-- Declararla `immutable` es una promesa que hacemos nosotros, y acá es cierta:
-- `duracion_min` son siempre minutos enteros, nunca días ni meses, y sumarle
-- minutos a un instante absoluto no depende de ninguna zona horaria.
--
-- `language sql` dice en qué idioma está escrito el cuerpo, y los `$$` marcan
-- dónde empieza y dónde termina ese cuerpo — hacen de comillas, pero sin serlo,
-- para que adentro se puedan escribir comillas sin cerrar nada por accidente.


alter table public.turnos
  add constraint turnos_sin_solapar
  exclude using gist (
    profesional_id with =,
    tstzrange( inicio, public.fin_del_turno( inicio, duracion_min ) ) with &&
  )
  where ( activo );

-- "Para un mismo profesional, no pueden existir dos turnos activos cuyos tramos
-- de tiempo se pisen." Las tres partes de esa frase son, en orden, las tres
-- líneas de adentro.
--
-- `profesional_id with =` es la que hace que dos profesionales atendiendo a la
-- misma hora NO choquen: sus id son distintos, la condición no se cumple y la
-- fila entra. Es correcto a propósito — el consultorio tiene varias salas, y esa
-- simultaneidad es el funcionamiento normal, no un conflicto. Sin esta línea, un
-- turno de cualquier profesional le bloquearía ese horario a todo el plantel.
--
-- El fin del turno no se guarda en ninguna columna: se calcula. Guardarlo sería
-- un tercer dato capaz de contradecir a los otros dos.
--
-- `with &&` cubre de una los dos casos que parecían distintos: el turno
-- duplicado exacto y el de 90 minutos que se come el principio del siguiente.
-- Para la base son lo mismo — dos tramos que se pisan.
--
-- `where ( activo )` deja fuera de la regla a los turnos cancelados. Sin eso, un
-- turno dado de baja seguiría bloqueando su horario para siempre, porque en este
-- proyecto no se borran filas: se apaga el estado.
