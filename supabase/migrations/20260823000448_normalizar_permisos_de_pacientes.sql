-- Los permisos de `pacientes` pasan a estar decididos, en vez de heredados.

-- Hallazgo del 22-ago-2026, mientras se verificaba el `grant insert` de `turnos`:
-- `service_role` tiene sobre `pacientes` los permisos de `insert`, `update` y
-- `delete`, y NINGUNA migración se los dio. Se comprobó buscando en las 18
-- migraciones del proyecto: los seis `grant` que existen son de otras tablas.
--
-- De dónde salieron: `pacientes` no se creó por migración sino desde el panel,
-- y nació con los permisos de fábrica puestos. Es el mismo mecanismo que el
-- 7-ago dejó a `anon` con permisos sobre esta misma tabla.
--
-- Qué tan grave es, sin inflarlo: NO es un agujero. `service_role` es la llave
-- del portero y no viaja al navegador. Lo que rompe es la disciplina del
-- proyecto, en dos puntos concretos:
--
--   1. Acá cada permiso tiene su porqué escrito al lado, y estos no tenían
--      ninguno. Un permiso sin motivo a la vista es un permiso que nadie se
--      anima a sacar después, porque nadie sabe qué rompe.
--   2. Hay un `delete` sobre pacientes, y en este proyecto no se borran filas:
--      se apaga el estado `activo`. Estaba prohibido por regla y habilitado
--      por olvido.

revoke all privileges
  on public.pacientes
  from service_role;

grant select, insert
  on public.pacientes
  to service_role;

-- Se revoca TODO y después se da lo que hace falta, en vez de quitar los tres
-- verbos por nombre. El motivo es el mismo que ya dejó escrito la migración
-- 20260816152403: una lista de verbos envejece —`maintain` no existía antes de
-- Postgres 17— y la intención no es "sacar estos tres", es "que no quede
-- ninguno que no hayamos elegido".
--
-- `select` porque el portero ya lee pacientes, e `insert` porque el alta de un
-- paciente nuevo es parte del endpoint que viene (etapa ③, paso C). Los dos
-- entran juntos con la funcionalidad que los usa.
--
-- `update` NO se da todavía, aunque se sepa que el panel (⑤) va a necesitarlo:
-- entra con su migración el día que exista la pantalla que edita un paciente.
-- `delete` no se va a dar nunca.
--
-- ⏳ Efecto de borde que conviene saber: después de esto `pacientes` queda MÁS
-- limpia que las otras seis tablas, que todavía conservan `truncate`, `trigger`
-- y `references` de fábrica para `service_role`. No es una inconsistencia que
-- haya que arreglar con prisa —son verbos que el portero no usa y que PostgREST
-- no expone—, pero queda dicho para que nadie lo descubra de nuevo dentro de
-- tres meses creyendo que encontró algo raro.
