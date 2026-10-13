-- PERMITIR PRENDER Y APAGAR UNA PAREJA — etapa ⑤.6, rebanada C.
--
-- QUÉ HABILITA: que el portero pueda escribir `profesional_tratamientos.activo`
-- — o sea que Cecilia decida qué tratamientos ofrece cada uno, sin tocar la
-- base a mano.
--
-- 🔑 POR QUÉ SE APAGA LA PAREJA Y NO EL TRATAMIENTO. El catálogo de
-- `tratamientos` no se apaga nunca: una limpieza sigue existiendo aunque hoy
-- no la haga nadie. Lo que deja de estar disponible es que TAL profesional lo
-- haga, y eso no es una propiedad del tratamiento ni del profesional: es de la
-- pareja. El porqué completo está en la migración que creó la columna.
--
-- 🔴 ES UNA SOLA COLUMNA, Y ESA ES LA PROTECCIÓN. Con un `grant update` sobre
-- la tabla entera, este endpoint quedaría habilitado a reescribir también
-- `profesional_id` y `tratamiento_id` — o sea a MUDAR una pareja existente a
-- otra persona. Un error ahí no apagaría un tratamiento: le pasaría el
-- tratamiento de alguien a otro, en silencio y sin que nada falle. Nombrando
-- la columna, la base rechaza esa escritura aunque el código la intente.
--
-- ⚠️ ESTE PERMISO ES DE CECILIA Y NO DE CADA PROFESIONAL, y eso NO lo decide
-- esta migración: el `grant` es del portero, que es uno solo. Quién puede
-- pedirlo se verifica en la Edge Function, contra `es_admin`. La regla de
-- negocio —ella es la referente de la clínica y decide cómo se hacen las
-- cosas— está escrita en la § 6 del documento de estado, y rompe a propósito
-- la simetría del resto del panel: un profesional no puede apagar ni el suyo.

grant update ( activo )
  on public.profesional_tratamientos
  to service_role;
