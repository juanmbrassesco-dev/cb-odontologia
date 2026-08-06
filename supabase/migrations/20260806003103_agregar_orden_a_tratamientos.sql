-- Orden de presentación de la lista de tratamientos.
--
-- El orden es un DATO del negocio, no una regla de código: Cecilia decide qué
-- ve primero el paciente y lo cambia desde el Table Editor, sin desplegar nada.
-- (La alternativa era ordenar en el portero y dejar "otros" escrito a mano en
-- el código: se rompía en silencio el día que se renombrara esa fila.)
--
-- Se numera de 10 en 10 para poder insertar un tratamiento nuevo en el medio
-- sin renumerar todos los demás.

alter table public.tratamientos
  add column orden int4;
