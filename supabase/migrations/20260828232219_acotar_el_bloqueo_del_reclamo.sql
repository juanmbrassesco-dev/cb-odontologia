-- EL RECLAMO TRABABA MÁS DE LO QUE NECESITABA, Y POR ESO NO FUNCIONABA.
--
-- `for update skip locked` a secas traba una fila de CADA tabla nombrada en el
-- `from` — acá, el turno y también el paciente. Y trabar una fila no es leerla:
-- Postgres exige permiso de ESCRITURA sobre la tabla trabada. El portero tiene
-- `select` e `insert` sobre `pacientes` y nada más, así que la función entera
-- moría con `42501: permission denied for table pacientes`.
--
-- 🔴 LA SALIDA NO ES DARLE EL PERMISO, ES TRABAR MENOS. Un `grant update` sobre
-- `pacientes` habría hecho andar esto y de paso le habría abierto al portero la
-- posibilidad de reescribir los datos de cualquier paciente, para conseguir algo
-- que no necesitaba. `for update of t` traba sólo los turnos, que son lo que se
-- reclama.
--
-- 🧭 CÓMO APARECIÓ, porque es la parte que vale: la función se había probado
-- entera y en verde CORRIENDO COMO DUEÑO DE LA BASE, que atraviesa cualquier
-- permiso. El fallo salió recién al llamarla como `service_role`, que es quien
-- la va a llamar de verdad. Un permiso que falta no se ve desde arriba.

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
