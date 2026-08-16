-- Los roles del navegador no tienen nada que hacer en ninguna tabla.
--
-- El modelo de acceso del proyecto es portero-only: el navegador nunca toca la
-- base, entra el backend con la llave maestra. Con esa regla escrita desde el
-- principio, `anon` y `authenticated` no deberían aparecer en ningún permiso.
--
-- Y aparecían: la auditoría del 16-ago-2026 los encontró con `truncate`,
-- `trigger` y `references` sobre SEIS de las siete tablas. La única limpia era
-- `pacientes`, porque el 7-ago se le hizo un `revoke` a mano — a esa tabla y
-- sólo a esa.
--
-- No los dio nadie: Supabase se los regala a cada tabla nueva del esquema
-- `public`. Por eso `pacientes` estaba bien y las otras seis no. No es que
-- alguien se equivocó seis veces; es que se arregló una sola vez.

revoke all privileges
  on
    public.pacientes,
    public.profesionales,
    public.tratamientos,
    public.profesional_tratamientos,
    public.horarios_base,
    public.excepciones,
    public.turnos
  from
    anon,
    authenticated;

-- `all privileges` es todos los verbos de una: `select`, `insert`, `update`,
-- `delete`, `truncate`, `references`, `trigger` y `maintain`. Se escribe así en
-- vez de nombrar los tres que la auditoría encontró porque la lista de lo que
-- Supabase regala puede cambiar con una versión nueva, y la intención de esta
-- migración no es "sacar estos tres": es "que no quede ninguno".
--
-- `pacientes` va en la lista aunque ya esté limpia. Un `revoke` sobre un permiso
-- que no existe no falla ni avisa: la base responde que salió bien y no hace
-- nada. Esa indiferencia es lo que permite escribir la lista completa sin
-- averiguar antes tabla por tabla qué tenía cada una — y deja el archivo
-- diciendo la verdad entera, que es "ninguna de las siete tablas queda con
-- permisos para el navegador".
--
-- ⚠ Y es también la trampa: como no falla, el "OK" de este comando NO prueba
-- que se haya quitado nada. Sale igual de bien si el permiso estaba que si no
-- estaba. La verificación es leer los permisos DESPUÉS, en
-- `information_schema.role_table_grants`, nunca confiar en que el comando
-- terminó sin error.
--
-- Se revoca también a `authenticated`, no sólo a `anon`, y no es por las dudas:
-- `authenticated` es el paciente que inició sesión desde su celular, o sea el
-- navegador otra vez. El panel de administración va a tener usuarios de verdad
-- (etapa ⑤), pero también va a entrar por el portero. Ningún rol del lado del
-- cliente necesita permisos propios.
--
-- Riesgo de romper algo: ninguno. `service_role` —el único rol que usa el
-- portero— no se toca en esta migración, y hoy no hay una sola línea de código
-- que entre a la base con `anon` o `authenticated`.
--
-- ⏳ Lo que esta migración NO cierra: la tabla que se cree MAÑANA vuelve a nacer
-- con el regalo puesto, porque acá se limpia lo que ya existe y no se cambia lo
-- que Supabase hace por defecto. Cerrar eso requiere `alter default privileges`
-- y se decide aparte, con la documentación delante.
