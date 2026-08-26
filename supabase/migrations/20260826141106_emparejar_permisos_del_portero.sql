-- Higiene: al portero se le deja SÓLO lo que sus endpoints usan.
--
-- Esta migración no agrega funcionalidad — no hay nada que ande después que no
-- anduviera antes. Cierra una asimetría medida el 25-ago-2026: `pacientes`
-- recibió un `revoke all` antes de sus verbos y quedó con dos permisos exactos,
-- mientras las otras seis tablas conservaban los que Supabase le da a
-- `service_role` al crear la tabla. Dos formas distintas de haber llegado al
-- mismo lugar, y quien compare tabla contra tabla lo ve.
--
-- Por qué no es prolijidad: `TRUNCATE` vacía una tabla entera de un saque, y
-- este proyecto tiene un no-hagas duro —no se borran filas, se apaga el estado
-- `activo`—. Dejarle a la llave maestra la vía más rápida de violar esa regla
-- contradice la regla. Es el mismo razonamiento que se le aplicó a `anon` el
-- 16-ago-2026, ahora aplicado al portero.
--
-- VA ÚLTIMA a propósito, después de que la etapa ④ estuviera cerrada y probada:
-- si algo se rompe de acá en adelante, se sabe que fue este `revoke` y no la
-- cancelación.

revoke all privileges
  on
    public.profesionales,
    public.tratamientos,
    public.profesional_tratamientos,
    public.horarios_base,
    public.excepciones,
    public.turnos
  from service_role;

-- Se escribe `all` y NO la lista de verbos que había que sacar, aunque los
-- cuatro estén identificados. El motivo se midió el 26-ago-2026 y es el hallazgo
-- que justifica esta migración entera:
--
-- El permiso crudo de las seis tablas era `service_role=rDxtm` — SELECT (r),
-- TRUNCATE (D), REFERENCES (x), TRIGGER (t) y MAINTAIN (m). Son CUATRO verbos de
-- más, no tres. `MAINTAIN` existe desde Postgres 17 (esta base corre 17.6) y NO
-- APARECE en `information_schema.role_table_grants`, que es la consulta con la
-- que se audita: una lista escrita a mano lo habría dejado puesto y el
-- emparejado habría sido falso sin que nadie lo notara.
--
-- La intención no es "sacar estos cuatro", es "que no quede ninguno que no se
-- use". Una lista de verbos envejece con cada versión de Postgres; `all`, no.

grant select
  on
    public.profesionales,
    public.tratamientos,
    public.profesional_tratamientos,
    public.horarios_base,
    public.excepciones,
    public.turnos
  to service_role;

-- Las seis leen: `GET /tratamientos`, `GET /horarios-disponibles`,
-- `GET /mis-turnos`, `POST /reservar` y `POST /cancelar` consultan entre todas
-- ellas. `pacientes` no está en esta lista porque no perdió nada: ya tenía
-- exactamente `select` e `insert` y esta migración no la toca.

grant insert            on public.turnos to service_role;
grant update ( activo ) on public.turnos to service_role;

-- 🔴 ESTAS DOS LÍNEAS NO SON UNA REPETICIÓN Y NO SE BORRAN.
--
-- Se leen como duplicados de las migraciones 20260822221903 (el `insert` que
-- necesita `POST /reservar`) y 20260825224428 (el `update ( activo )` que
-- necesita `POST /cancelar`), y no lo son: el `revoke all` de arriba se lleva
-- puesto TODO lo que esas dos dieron. Sin estas dos líneas, esta migración
-- rompe la reserva y la cancelación con un `42501` que no nombra la causa por
-- ningún lado — que es exactamente como ya rompió una escritura en este
-- proyecto el 16-ago (`fin_del_turno`, migración 20260816153310).
--
-- El paréntesis de `( activo )` se mantiene con el mismo alcance que tenía: el
-- portero puede apagar un turno y nada más. El porqué completo está escrito en
-- la migración 20260825224428 y no se repite acá.
--
-- ⚠ Y hay una razón por la que esto es fácil de pasar por alto al auditar:
-- `update ( activo )` es un permiso DE COLUMNA. No figura en
-- `information_schema.role_table_grants` —la consulta 3 de la herramienta de
-- auditoría— sino en `role_column_grants`. Quien verifique esta migración con
-- la consulta de siempre va a ver `turnos │ INSERT, SELECT` y va a concluir que
-- falta el `update`. No falta: está una consulta más abajo.
--
-- La canilla de los permisos por defecto ya está cerrada desde el 16-ago
-- (migración 20260816152403, `alter default privileges ... revoke all ... from
-- anon, authenticated, service_role`), así que una tabla nueva nace limpia y
-- esta migración no se va a tener que repetir.
