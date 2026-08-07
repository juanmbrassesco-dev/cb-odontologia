-- El portero todavía no puede leer la agenda.
--
-- `tratamientos`, `profesionales` y `profesional_tratamientos` ya le abrieron la
-- puerta a `service_role`, pero las tres tablas que forman la agenda quedaron
-- afuera. Sin esto, el endpoint que sigue —`GET /horarios-disponibles`— falla con
-- un `42501 permission denied`, que es el error ruidoso de la primera cerradura:
-- el GRANT se pide por tabla, una por una, y no se hereda de las vecinas.


grant select on public.horarios_base to service_role;

grant select on public.excepciones to service_role;

grant select on public.turnos to service_role;


-- Solo SELECT, y solo a `service_role`.
--
-- El GRANT es por verbo, no por tabla: esto habilita leer y nada más. Escribir un
-- turno va a necesitar su propio `grant insert`, y se da cuando exista el endpoint
-- que reserva, no antes — un permiso que nadie usa es superficie de ataque sin
-- contraparte.
--
-- A `anon` no se le da nada, nunca: el navegador no toca la base. Es el modelo
-- portero-only, y la única vez que esta regla se rompió en el proyecto fue por el
-- Data API prendido a mano sobre `pacientes`, corregido el 7-ago-2026.
