-- PERMITIR EDITAR LA AGENDA SEMANAL — etapa ⑤.5, rebanada C.
--
-- QUÉ HABILITA: que el portero pueda escribir en `horarios_base`. Hasta hoy la
-- tabla tenía `grant select` y nada más —puesto el 7-ago con la etapa ①—, así
-- que cambiar los días y horarios de atención significaba entrar al Table
-- Editor de Supabase.
--
-- 🔑 EL PERMISO ENTRA CON LA FUNCIONALIDAD QUE LO USA, que es la regla del
-- proyecto y ya se cumplió con `turnos` y con `excepciones`.
--
-- 🔴 `activo` QUEDA FUERA DEL `insert`, igual que en `permitir_cargar_ausencias`
-- y por el mismo motivo: lo pone la base con su `default true`, así que un tramo
-- nace atendiendo. Si el endpoint pudiera escribirlo, un tramo podría nacer
-- APAGADO — una fila que está en la lista, parece cargada, y no ofrece ni un
-- turno.
--
-- 🔴 Y EL `update` ES DE UNA SOLA COLUMNA. Con un `grant update` sobre la tabla
-- entera, el endpoint que prende y apaga quedaría habilitado a reescribir
-- `inicio`, `fin`, `fin_maximo` o `dia_semana` — o sea a MUDAR un tramo de día o
-- a correrle el horario—. Un error ahí no apagaría nada: le cambiaría los días
-- de atención a alguien, en silencio y sin que nada falle. **Nombrando la
-- columna, la base rechaza esa escritura aunque el código la intente.**
--
-- ⚠️ NO HAY `delete`: no se borran filas, se apaga el estado. El porqué completo
-- está en la migración de la columna.
--
-- ⚠️ Y NO HACE FALTA TOCAR LOS TRES `check` QUE LA TABLA YA TIENE
-- —`dia_semana` entre 1 y 7, `fin > inicio`, `fin_maximo > fin`—: siguen
-- valiendo igual para una fila que escribe el panel, que es justo para lo que se
-- escribieron. *El comentario de `agregar_fin_maximo_a_horarios` lo dice con
-- todas las letras: protegen de una carga a mano mal tipeada Y de un bug en el
-- panel de admin el día que exista. Ese día es hoy.*


grant insert (
    profesional_id,
    dia_semana,
    inicio,
    fin,
    fin_maximo
  )
  on public.horarios_base
  to service_role;


grant update ( activo )
  on public.horarios_base
  to service_role;
