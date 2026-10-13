-- PERMITIR CREAR UNA PAREJA PROFESIONAL-TRATAMIENTO — etapa ⑤.6, rebanada C.
--
-- QUÉ HABILITA: que el portero pueda escribir una fila nueva en
-- `profesional_tratamientos`, o sea declarar que tal profesional hace tal
-- tratamiento.
--
-- 🔑 POR QUÉ HACE FALTA CREAR Y NO ALCANZA CON PRENDER Y APAGAR. Las once
-- parejas que hay hoy las cargaron dos migraciones, a mano. Alguien dado de
-- alta desde el panel —que ya se puede, desde la rebanada B— NO TIENE NINGUNA:
-- su fila existe, pero no hace ningún tratamiento, así que no aparece para
-- reservar con nadie. Sin este permiso, cada profesional nuevo habría que
-- completarlo por el Table Editor, que es justo lo que este panel evita.
--
-- 🔴 EL GRANT ES POR COLUMNAS, igual que en `profesionales` y por el mismo
-- motivo: `id` lo pone la base y `activo` tiene `default true`. Una pareja
-- nueva nace encendida —se crea porque alguien va a hacer ese tratamiento— y
-- apagarla es el otro permiso, el de la migración de al lado.
--
-- ⚠️ NO HAY RIESGO DE DUPLICADOS Y NO ES PORQUE EL CÓDIGO SEA CUIDADOSO: la
-- tabla tiene `unique (profesional_id, tratamiento_id)` desde que se creó. Un
-- doble clic choca contra esa restricción y la base contesta 23505. El código
-- la traduce; lo que no puede es crear la fila repetida.

grant insert ( profesional_id, tratamiento_id )
  on public.profesional_tratamientos
  to service_role;
