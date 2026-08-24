-- La pareja profesional-tratamiento pasa a poder apagarse.
--
-- El catálogo de `tratamientos` no se apaga nunca: una limpieza sigue
-- existiendo como tratamiento aunque hoy no la haga nadie. Lo que sí deja de
-- estar disponible es que TAL profesional lo haga, y eso no es una propiedad
-- del tratamiento ni una del profesional: es de la pareja. Por eso la columna
-- va acá y no en `tratamientos`.
--
-- Se apaga en lugar de borrarse, como en el resto del proyecto. Borrar la fila
-- dejaría turnos ya atendidos describiendo una combinación —este profesional,
-- este tratamiento— que la base ya no reconocería como válida, y una regla sin
-- excepciones (nunca se borra, se apaga) es más barata de sostener que una con
-- excepciones.

alter table public.profesional_tratamientos
  add column activo boolean
    not null
    default true;

-- El valor por defecto no es decoración y no se puede quitar: la tabla ya
-- tiene once filas cargadas. Sin él, esas once quedarían en null —que es
-- exactamente lo que `not null` prohíbe— y Postgres rechaza el `alter table`
-- completo, sin aplicar nada. Sobre una tabla vacía la columna obligatoria
-- entra sola, que fue el caso de `20260807211547`; éste no lo es.
--
-- Y `true` es el valor correcto, no sólo el que destraba la migración: al dar
-- de alta un profesional se cargan las parejas de lo que hace, así que lo
-- normal es que nazcan activas. Apagar después las pocas que dejen de
-- ofrecerse cuesta menos que activar una por una las de cada alta.
--
-- Quién lee la columna: hoy, las dos consultas que validan la pareja antes de
-- reservar (`reservar` y `horarios-disponibles`), que ya contestan "Ese
-- profesional no hace ese tratamiento" y sirven igual para una pareja apagada.
-- Más adelante, el endpoint que le lista al paciente qué profesionales hacen
-- el tratamiento que eligió.
