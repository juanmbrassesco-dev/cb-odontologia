-- Falta la limpieza, y es uno de los dos únicos tratamientos que el paciente
-- puede reservar por su cuenta.
--
-- La tabla se cargó el 5-ago-2026 con diez filas y ninguna era ésta. No se
-- notó hasta que Cecilia contestó qué se puede reservar por la web: la
-- consulta general de 30 minutos y la limpieza de 60. El resto de los
-- tratamientos sale de la consulta previa y los agenda el profesional.
--
-- Va en su propia migración, separada de la columna que marca lo reservable:
-- ésta agrega un DATO al catálogo y la otra cambia la FORMA de la tabla. Se
-- leen y se revierten por separado.

insert into public.tratamientos ( nombre, orden )
values ( 'limpieza', 15 );

-- El `orden` 15 la deja entre `consulta` (10) y `blanqueamiento` (20), que es
-- donde el paciente espera encontrarla.
--
-- Para esto se numeró de 10 en 10 el 6-ago-2026: entra una fila en el medio
-- sin tocar el orden de ninguna de las otras diez. Con la numeración natural
-- (1, 2, 3…) esta línea habría obligado a reescribir nueve filas.
--
-- El nombre va en minúscula porque así están las otras diez: la tabla guarda
-- el nombre crudo y la pantalla decide cómo mostrarlo.
