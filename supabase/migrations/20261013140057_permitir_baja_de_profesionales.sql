-- PERMITIR LA BAJA DE PROFESIONALES — etapa ⑤.6, rebanada B.
--
-- QUÉ HABILITA: que el portero pueda APAGAR una fila de `profesionales`
-- escribiendo `activo = false` y la fecha en que pasó.
--
-- 🔴 DAR DE BAJA ES APAGAR, NUNCA BORRAR, y acá no es una preferencia de
-- estilo: los turnos pasados apuntan al profesional con una foreign key
-- `restrict`, así que la base RECHAZARÍA el `delete`. Y si se forzara, se
-- llevaría puesto el historial de todo lo que esa persona atendió. Por eso
-- esta migración no da `delete` y no lo va a dar nunca.
--
-- 🔴 SON EXACTAMENTE DOS COLUMNAS, y la lista corta es la protección. Con un
-- `grant update on public.profesionales` a secas, el endpoint que da de baja
-- quedaría habilitado a escribir TAMBIÉN `es_admin` y `email_de_acceso` — o
-- sea, a convertir a cualquiera en administrador o a cambiarle la cuenta con
-- la que entra. Un error de programación en ese endpoint pasaría de "no se dio
-- de baja" a "se repartieron permisos". El `grant` por columna es lo que hace
-- que ese error ni siquiera sea posible: la base lo rechaza.
--
-- 🔑 `fecha_baja` VIAJA CON `activo` porque las dos las escribe una sola
-- acción. `activo` dice si sigue; `fecha_baja` dice desde cuándo no. Separarlas
-- permitiría apagar a alguien sin dejar constancia de cuándo, que es
-- justamente lo que la columna existe para evitar.
--
-- ⚠️ ESTO NO HABILITA EL ALTA: volver a prender a alguien escribe las mismas
-- dos columnas, así que ya queda cubierto por este permiso. Lo que NO queda
-- cubierto, y es a propósito, es editar el nombre o el correo de alguien que
-- ya está cargado: eso es otra pantalla y va a necesitar su propio grant.

grant update ( activo, fecha_baja )
  on public.profesionales
  to service_role;
