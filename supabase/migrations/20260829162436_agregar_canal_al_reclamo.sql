-- EL RECLAMO DEVUELVE TAMBIÉN CÓMO ENTRÓ EL TURNO.
--
-- Un renglón más en lo que la función devuelve —`turno_canal`— y nada más. Es
-- la columna `turnos.canal` que cerró la migración 20260828135023 en dos
-- valores, `web` y `manual`.
--
-- 🔴 QUÉ ARREGLA, con el caso concreto. El aviso operativo empezaba SIEMPRE con
-- «entró un turno nuevo por la web», también cuando el turno lo había cargado
-- Cecilia a mano en el Table Editor y el correo salía por la repesca. O sea que
-- el correo afirmaba un origen que no era.
--
-- 🧭 Lo levantó Juan el 29-ago-2026, y de paso corrigió una respuesta mía que
-- estaba mal: yo había dicho que el origen «no se podía distinguir». Se puede,
-- y la columna existía desde el día anterior — lo único que faltaba era traerla
-- hasta el correo. El dato estaba; la que falló fue la respuesta.
--
-- ⚠ VA `drop` Y NO `create or replace` porque cambia el tipo de retorno, y
-- Postgres no lo permite. Es la tercera vez que esta función se reescribe
-- entera por el mismo motivo; el procedimiento es el de siempre.
--
-- 🔴 Y EL ORDEN DE LAS DOS LISTAS SIGUE SIENDO POSICIONAL: `turno_canal` entra
-- entre `turno_activo` y `paciente_nombre` arriba, así que `r.canal` entra
-- exactamente en el mismo lugar abajo. No hay nombres que las emparejen.


drop function public.reclamar_avisos_pendientes ( integer );


create function public.reclamar_avisos_pendientes ( tope integer )
  returns table (
    turno_id             bigint,
    turno_inicio         timestamptz,
    -- Las dos horas van pegadas a propósito: la que el turno ES y la que el
    -- paciente CREE. Todo el sentido de la columna está en compararlas, así que
    -- separarlas en la lista sería esconder de qué se trata.
    turno_inicio_avisado timestamptz,
    turno_duracion_min   integer,
    turno_activo         boolean,
    -- Cómo entró el turno: 'web' o 'manual'. Es lo único que separa un aviso
    -- que puede decir «entró por la web» de uno que estaría mintiendo.
    turno_canal          text,
    paciente_nombre      text,
    paciente_apellido    text,
    paciente_email       text,
    profesional_nombre   text,
    profesional_apellido text,
    profesional_email    text,
    tratamiento_nombre   text,
    motivo_nombre        text,
    tiene_observaciones  boolean
  )
  language sql
as $$

  with reclamados as (

    update public.turnos
       set aviso_estado = 'enviando',
           aviso_at     = now()
     where id in (

       select t.id
         from public.turnos t
         join public.pacientes p
           on p.id = t.paciente_id

        -- ── A QUIÉN HAY QUE AVISARLE ────────────────────────────────────────
        --
        -- Compara lo que el turno ES (`activo`) contra lo que el paciente SABE
        -- (`aviso_estado`), y deja entrar sólo a los que no coinciden. Un
        -- `where` no dice a quién deja afuera: dice a quién deja entrar, así
        -- que todo lo que no está nombrado acá ya está excluido.
        --
        -- Los dos casos que NO figuran, y es a propósito: el turno activo que
        -- ya sabe `reservado`, y el cancelado del que nadie supo nunca —
        -- avisarle de una cancelación sería contarle de un turno que ignoraba.
        --
        -- El tercer renglón es el turno que cancelaron MIENTRAS le salía el
        -- primer correo: queda apagado con la marca trabada en `enviando`, y
        -- sin esta línea no lo levanta nadie nunca más.
        where t.inicio > now()
          and p.email is not null
          and (
                (     t.activo and t.aviso_estado is distinct from 'reservado' )
             or ( not t.activo and t.aviso_estado = 'reservado' )
             or ( not t.activo and t.aviso_estado = 'enviando'  )
              )

        -- ── LO QUE YA ESTÁ SALIENDO NO SE VUELVE A TOMAR ────────────────────
        --
        -- Salvo que lleve más de diez minutos ahí: eso ya no es un envío en
        -- curso, es un envío que se murió. Acá es donde `aviso_at` deja de ser
        -- decoración.
          and (
                t.aviso_estado is distinct from 'enviando'
             or t.aviso_at < now() - interval '10 minutes'
              )

        order by t.inicio
        limit tope

        -- 🔴 LO QUE HACE AL RECLAMO A PRUEBA DE CARRERAS. La segunda corrida
        -- SALTEA las filas que la primera ya tomó, en vez de esperarlas: dos
        -- corridas nunca se llevan el mismo turno y ninguna queda trabada.
        --
        -- ⚠ EL `of t` NO ES ADORNO: sin él, el bloqueo alcanza a TODAS las
        -- tablas del `from`, y trabar una fila exige permiso de ESCRITURA sobre
        -- ella. El portero no lo tiene sobre `pacientes` —ni debe tenerlo—, así
        -- que la función entera moría con un 42501. Se traban los turnos, que
        -- son los que se reclaman; `pacientes` sólo se lee.
        for update of t skip locked
     )

    returning *
  )

  -- Los datos del correo, ya con el turno reclamado. Las dos referencias a
  -- `tratamientos` son distintas —lo que se agenda y a qué vino— y en SQL se
  -- distinguen solas por el alias, sin nombrar ninguna constraint.
  --
  -- Van con `left join` porque las dos columnas pueden estar vacías: un turno
  -- cargado a mano puede no tener tratamiento, y el motivo sólo existe si la
  -- reserva entró por el sitio. Con un `join` a secas, esos turnos no volverían.
  --
  -- ⚠ EL ORDEN DE ESTA LISTA ES EL DE LA TABLA DE ARRIBA, columna por columna.
  -- No hay nombres que las emparejen: se emparejan por POSICIÓN, así que meter
  -- una en el medio de un lado obliga a meterla en el mismo lugar del otro.
  select r.id,
         r.inicio,
         r.inicio_avisado,
         r.duracion_min,
         r.activo,
         r.canal,
         p.nombre,
         p.apellido,
         p.email,
         pr.nombre,
         pr.apellido,
         pr.email,
         tr.nombre,
         mo.nombre,
         ( r.observaciones_paciente is not null )
    from reclamados r
    join public.pacientes p
      on p.id = r.paciente_id
    join public.profesionales pr
      on pr.id = r.profesional_id
    left join public.tratamientos tr
      on tr.id = r.tratamiento_id
    left join public.tratamientos mo
      on mo.id = r.motivo_consulta_id;

$$;


-- 🔒 A DIFERENCIA DE LOS TRIGGERS, ÉSTA SÍ SE LLAMA POR HTTP: es el caso exacto
-- que cubre `herramientas/auditar-base-supabase.md` § 3.b. Se le quita el
-- `execute` a todo el mundo y se le devuelve SOLO al portero, que es el único
-- que la invoca.
--
-- Y se vuelve a escribir porque la función se borró: los permisos se van con
-- ella. Una función recreada sin estas dos líneas queda ejecutable por
-- cualquiera y el portero sin poder llamarla.

revoke execute
  on function public.reclamar_avisos_pendientes ( integer )
  from public;

grant execute
  on function public.reclamar_avisos_pendientes ( integer )
  to service_role;
