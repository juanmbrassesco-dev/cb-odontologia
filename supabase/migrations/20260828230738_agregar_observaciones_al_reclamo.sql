-- LE FALTABA UN DATO AL RECLAMO: si el paciente escribió observaciones.
--
-- La migración 20260828230339 devolvía todo lo que el correo necesita menos
-- esto, y el aviso operativo lo usa: `avisos.ts` escribe un renglón avisándole
-- al consultorio que hay algo escrito. Sin el dato, un turno reenviado por la
-- repesca le llegaría a Cecilia SIN esa advertencia, y ella no tendría cómo
-- saber que el paciente dejó una nota.
--
-- ⚠ VIAJA EL SÍ/NO, NUNCA EL TEXTO. `turnos.observaciones_paciente` puede
-- contener datos de salud: el correo dice que hay algo escrito y dónde mirarlo,
-- no lo transcribe. Es la misma regla que ya aplican `reservar` y `cancelar`.
--
-- Va `drop` y no `create or replace` porque Postgres no deja cambiar el tipo de
-- retorno de una función existente, y agregar una columna al `returns table` lo
-- cambia. Se puede sin riesgo porque todavía no la llama nadie: la Edge Function
-- de la repesca no está escrita.

drop function public.reclamar_avisos_pendientes ( integer );


create function public.reclamar_avisos_pendientes ( tope integer )
  returns table (
    turno_id             bigint,
    turno_inicio         timestamptz,
    turno_duracion_min   integer,
    turno_activo         boolean,
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
        for update skip locked
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
  select r.id,
         r.inicio,
         r.duracion_min,
         r.activo,
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

revoke execute
  on function public.reclamar_avisos_pendientes ( integer )
  from public;

grant execute
  on function public.reclamar_avisos_pendientes ( integer )
  to service_role;
