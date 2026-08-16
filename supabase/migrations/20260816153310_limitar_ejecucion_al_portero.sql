-- La función interna de la agenda deja de estar al alcance del navegador.
--
-- `fin_del_turno` existe por una limitación del motor: la restricción
-- anti-solapamiento necesita una función `immutable` para calcular dónde
-- termina cada turno (el porqué completo, en la migración 20260807220637). Es
-- una pieza interna del cálculo de la agenda, no un servicio para nadie.
--
-- Pero nació abierta. Postgres le da `execute` al pseudo-rol `public` —todos los
-- roles, presentes y futuros— a toda función nueva, y Supabase publica las
-- funciones del esquema `public` como endpoints REST. Las dos cosas juntas
-- significan que cualquiera con la clave pública del sitio, que por diseño viaja
-- en el navegador, podía llamarla.
--
-- Y podía de verdad: se comprobó el 16-ago-2026 contra el proyecto en
-- producción. Un POST a /rest/v1/rpc/fin_del_turno con la clave `anon` devolvió
-- HTTP 200 y la fecha calculada.
--
-- El daño que se evita es chico y conviene decirlo sin inflarlo: la función es
-- pura —suma minutos a una fecha— y no lee ni escribe una sola fila. Lo que se
-- cierra no es una fuga de datos, es superficie: un endpoint público de más y un
-- nombre interno del sistema publicado en el catálogo de la API.

revoke execute
  on function public.fin_del_turno ( timestamptz, integer )
  from public;

grant execute
  on function public.fin_del_turno ( timestamptz, integer )
  to service_role;

-- Las dos líneas van juntas y el orden importa, porque la primera sola ROMPE LA
-- RESERVA DE TURNOS.
--
-- Eso no se dedujo, se probó. Con sólo el `revoke`, insertar un turno como
-- `service_role` falla con:
--
--     ERROR: 42501: permission denied for function fin_del_turno
--
-- El motivo: la restricción tiene la función metida adentro de su índice, y ese
-- índice se evalúa en cada escritura con los permisos de quien está escribiendo,
-- no con los de quien creó la función. Sin `execute`, el portero no puede
-- guardar ningún turno. Con el `grant` de abajo puesto, el mismo insert entra.
--
-- Las dos pruebas se hicieron con `begin … rollback` sobre la base real, así que
-- no quedó ni un turno ni un paciente de prueba dado de alta.
--
-- Se nombran los tipos de los parámetros —`( timestamptz, integer )`— porque en
-- Postgres pueden convivir varias funciones con el mismo nombre y distinta
-- firma. Sin los tipos, la orden es ambigua el día que exista una segunda.
--
-- `anon` y `authenticated` no aparecen por ningún lado a propósito: no se les
-- revoca nada porque nunca tuvieron nada propio. Lo que los alcanzaba era el
-- `execute` a `public`, que los incluye a los dos y a cualquier rol que se cree
-- mañana. Quitar el permiso de la puerta grande es lo que cierra los tres casos.
--
-- ⏳ Vale para esta función, no para las que vengan: cada función nueva del
-- esquema `public` va a nacer con el mismo `execute` abierto. Cerrarlo de raíz
-- se puede —hay un `alter default privileges ... on functions`— y queda sin
-- hacer hoy porque no hay una segunda función que lo justifique.
