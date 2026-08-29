-- EL RECLAMO DEVUELVE TAMBIÉN LA HORA QUE SE LE AVISÓ AL PACIENTE.
--
-- Un renglón nuevo en lo que la función devuelve —`turno_inicio_avisado`— y
-- nada más: ni el `where`, ni el bloqueo, ni los `join` cambian una coma. Es la
-- columna que agregó la migración 20260829145613, puesta al alcance del correo.
--
-- 🔴 POR QUÉ TIENE QUE VIAJAR ACÁ Y NO SE CONSULTA DESPUÉS. Es la misma razón
-- por la que esta función devuelve los datos del correo en vez de los `id`: si
-- la repesca preguntara aparte, entre el reclamo y la pregunta el turno podría
-- cambiar y el correo saldría comparando contra un dato que ya no es el que se
-- reclamó. Lo que se reclama y lo que se manda tienen que salir de la misma
-- operación.
--
-- 🔑 Y LA CLAVE DE POR QUÉ ESTO FUNCIONA, que no se ve leyendo el `update`: el
-- reclamo escribe `aviso_estado` y `aviso_at`, NO `inicio_avisado`. Así que el
-- `returning *` la devuelve con el valor que tenía ANTES de este aviso, que es
-- justamente contra el que hay que comparar. Si el reclamo la tocara, la
-- comparación se perdería en el mismo instante en que se la necesita.
--
-- Con eso, `_shared/avisos.ts` decide solo cuál de los tres correos escribe:
--
--   vacía                      → nunca se le avisó nada  → "quedó agendado"
--   llena y distinta de inicio → se le avisó otra hora   → "cambió el horario"
--   llena e igual a inicio     → se le avisó esta hora,
--                                y el trigger borró la
--                                marca porque algo cambió → "hubo un cambio"
--
-- El tercer caso es el que levantó Juan el 29-ago-2026: si a un turno le cambian
-- el PROFESIONAL sin moverle la hora, el correo viejo pasa a mentir igual, y sin
-- este dato el aviso nuevo saldría con el mismo asunto que la reserva original
-- —el gestor de correo los agrupa y la paciente ni ve que llegó otro—.
--
-- ⚠ VA `drop` Y NO `create or replace` porque cambia el tipo de retorno, y
-- Postgres no lo permite. Mismo motivo y mismo procedimiento que las
-- migraciones 20260828230738 y 20260828232219: la función se reescribe entera.


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
