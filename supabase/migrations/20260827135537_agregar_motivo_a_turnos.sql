-- El turno pasa a guardar A QUÉ VINO el paciente, además de qué se le agenda.

-- `turnos.tratamiento_id` dice lo que el consultorio hace en ese turno. Hasta hoy
-- eso alcanzaba, porque las dos cosas eran la misma. Dejan de serlo cuando la
-- reserva entra por la web: de los once tratamientos, sólo consulta y limpieza se
-- reservan solos, y los otros nueve se agendan como una consulta de 30 minutos.
--
-- Sin esta columna, el paciente que entra por "ortodoncia" llega a la agenda como
-- una consulta más y Cecilia se sienta enfrente sin saber por qué vino.
--
-- Va en el TURNO y no en el paciente porque el motivo ENVEJECE. En el paciente hay
-- un solo valor y la segunda reserva pisa la primera: se leería "ortodoncia" sin
-- saber si se dijo la semana pasada o hace catorce meses, que es justo lo que se
-- quiere evitar antes de ofrecerle un tratamiento a alguien.


alter table public.turnos
  add column motivo_consulta_id bigint
    constraint turnos_motivo_consulta_id_fkey
      references public.tratamientos ( id )
      on delete restrict;


-- OPCIONAL a propósito, y la regla es sin excepciones: guarda LA ELECCIÓN DEL
-- PACIENTE POR LA WEB, y sólo eso. Se llena siempre que el turno venga del
-- formulario —aunque coincida con lo agendado, como pasa con la limpieza— y queda
-- vacía en los turnos que carga el consultorio, donde no hubo elección de nadie.
-- Así, al leer la columna, el vacío nunca es ambiguo: significa "no eligió", nunca
-- "eligió lo mismo".
--
-- `bigint` no se eligió por el tamaño del número: TIENE que coincidir con el tipo
-- de la columna a la que apunta, y `tratamientos.id` es `bigint`. Con otro tipo, la
-- base rechaza la migración entera.
--
-- `on delete restrict`: un tratamiento que ya figura como motivo de un turno no se
-- borra. Se saca de la grilla apagándolo, como todo lo demás en el proyecto.


-- 🔑 POR QUÉ ESTA FOREIGN KEY LLEVA NOMBRE A MANO Y LAS TRES DE AL LADO NO.
--
-- Las otras tres de `turnos` (`paciente_id`, `profesional_id`, `tratamiento_id`) se
-- escribieron sin nombrar la constraint, y Postgres les puso uno solo siguiendo su
-- convención. Alcanzaba porque cada una apuntaba a una tabla distinta.
--
-- Con ésta, `turnos` pasa a tener DOS referencias a `tratamientos`. A partir de acá,
-- cualquier consulta que cruce las dos tablas es ambigua —hay dos caminos posibles y
-- hay que decir por cuál—, y el camino se nombra por el nombre de la constraint. Un
-- nombre puesto a mano es predecible; el que genera Postgres solo hay que ir a
-- buscarlo a la base cada vez.
--
-- ⚠ Y esto ROMPE dos consultas que hoy andan, las dos de la etapa ④, que está
-- cerrada y probada:
--
--     mis-turnos/index.ts   → tratamiento:tratamientos ( nombre )
--     cancelar/index.ts     → tratamiento:tratamientos ( nombre )
--
-- Las dos pasan a nombrar la relación (`tratamientos!turnos_tratamiento_id_fkey`).
-- Falla ruidoso —PostgREST avisa que encontró más de una relación posible— pero
-- falla, así que las dos baterías se corren enteras detrás de esta migración.
--
-- El nombre de la constraint vieja no se supuso: se leyó de la base antes de escribir
-- esto (`turnos_tratamiento_id_fkey`). La convención acertó, pero la convención no es
-- el dato.


-- ✅ PERMISOS: no hace falta ninguno, y conviene dejar escrito por qué.
--
-- El `grant insert on public.turnos` de la migración 20260822221903 se dio A NIVEL DE
-- TABLA, sin lista de columnas, así que cubre cualquier columna que se agregue
-- después — ésta incluida.
--
-- No habría pasado lo mismo con un `update`: el de la migración 20260825224428 está
-- acotado a `( activo )`, y una columna que no esté nombrada ahí adentro no se puede
-- escribir nunca. Por eso esta columna, que se llena con el `insert` de la reserva,
-- nace cubierta, y las que la fase 5 va a llenar con un `update` van a necesitar su
-- propia migración de permisos.
