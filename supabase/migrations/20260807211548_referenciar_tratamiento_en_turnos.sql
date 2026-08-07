-- El turno deja de guardar el tratamiento como texto suelto y pasa a apuntar a
-- la tabla que ya lo tiene.
--
-- `turnos.tratamiento` era un `text` libre, escrito a mano en cada turno. Eso
-- admite "Blanqueamiento", "blanqueamiento" y "blanq." como tres tratamientos
-- distintos, y ninguno se puede cruzar con la tabla `tratamientos` ni con lo que
-- cada profesional sabe hacer. Guardar el `id` deja un solo nombre por
-- tratamiento, en un solo lugar.
--
-- El dato no agrega ningún paso al paciente: ya lo elige al reservar. Lo que
-- habilita es el aviso por email al profesional, que sin esto diría "turno el
-- martes 11:00" sin decir a qué viene la persona.
--
-- Va separada de la migración anterior porque contesta otra pregunta: aquélla
-- agrega el "¿de quién?" a la agenda; ésta cambia el "¿a qué viene?" de texto a
-- referencia. Son dos cambios con dos motivos, y separados se pueden leer —y
-- revertir— por separado.


alter table public.turnos
  drop column tratamiento;

-- Se puede borrar sin más porque la tabla está vacía (verificado antes de
-- aplicar). Con turnos reales adentro esto sería otra operación: habría que
-- crear la columna nueva, traducir cada texto a su `id` a mano, y recién
-- entonces borrar la vieja.


alter table public.turnos
  add column tratamiento_id bigint
    references public.tratamientos (id)
    on delete restrict;

-- Opcional a propósito. Un turno cargado por Cecilia desde el panel —o el que
-- entra por teléfono— puede no tener el tratamiento decidido todavía, y esa
-- falta no debería impedir agendar. Lo que el sistema no puede permitir es un
-- tratamiento INVENTADO, y de eso se ocupa la foreign key, no el NOT NULL.
--
-- `on delete restrict`: un tratamiento que ya figura en un turno no se borra.
-- Se saca de la grilla apagándolo, como todo lo demás en el proyecto.
