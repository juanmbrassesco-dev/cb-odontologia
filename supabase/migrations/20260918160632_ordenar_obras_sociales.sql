-- `Particular` tiene que salir primera en el desplegable del paciente.
--
-- Alfabéticamente cae en el medio, entre `OSSACRA` y `PERSONAL INDUSTRIA DEL
-- CAUCHO`, y ahí no cumple su función: es la salida para quien no tiene obra
-- social, así que tiene que estar donde se la ve sin buscar.
--
-- La columna existe para que el orden lo mande la base y no el código, que es
-- lo que ya hace `tratamientos` con su propia columna `orden`. La alternativa
-- -- que el endpoint moviera la fila al frente en JavaScript -- cuesta tres
-- líneas y ninguna migración, pero dejaría dos formas distintas de ordenar un
-- catálogo en el mismo proyecto.
--
-- `default 1` es lo que hace que las setenta y una filas ya cargadas no haya
-- que tocarlas: todas nacen en 1 y sólo una se mueve. Sin el `default`, un
-- `not null` sobre una tabla con filas hace fallar el `alter table` entero.

alter table public.obras_sociales
  add column orden integer not null default 1;

update public.obras_sociales
  set orden = 0
  where nombre = 'Particular';


-- El resto empata en 1 a propósito: no hay un orden preferido entre setenta
-- convenios, y el desempate lo hace el endpoint pidiendo después por `entidad`
-- y por `nombre`. Si algún día el consultorio quiere subir alguno, se le cambia
-- el número y no se toca una línea de código.

comment on column public.obras_sociales.orden is
  'Menor sale antes. Particular va en 0; el resto empata en 1 y desempata alfabéticamente.';
