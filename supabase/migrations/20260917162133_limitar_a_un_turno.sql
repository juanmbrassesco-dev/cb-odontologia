-- Un paciente no puede tener MÁS DE UN turno web abierto con el mismo profesional.

-- Cambia la regla del 28-ago-2026, que permitía dos. El motivo es de agenda y no
-- técnico: un paciente que TODAVÍA NO FUE al turno que ya tiene no debería poder
-- ocupar un segundo lugar con ese mismo profesional. (Decisión de Juan, 2-sep-2026.)
--
-- 🔴 LA MIGRACIÓN VIEJA NO SE TOCA — una migración aplicada es historia. Esta
-- reemplaza el CUERPO de la función con `create or replace`, y por eso abajo no
-- hay ningún `create trigger`: el trigger apunta a la función por su NOMBRE, así
-- que al cambiarle el cuerpo sigue enganchado solo. Un `drop` + `create` se lo
-- llevaría puesto y la regla quedaría escrita en la base sin nadie que la
-- dispare — que es el peor de los dos mundos: no falla, deja pasar.
--
-- 🔑 LO QUE NO CAMBIA, y es la mitad que hace a la regla: el conteo ya filtraba
-- `inicio > now()`, o sea que sólo pesan los turnos cuya hora todavía no llegó.
-- El cupo se libera cuando PASA LA HORA DE INICIO del turno anterior — no cuando
-- el turno termina, y no sólo si el paciente lo cancela. Eso ya estaba construido
-- desde el 28-ago: acá cambian un número y un texto.


create or replace function public.limitar_turnos_por_paciente ()
  returns trigger
  language plpgsql
as $$
declare
  ya_tiene integer;
begin

  -- ① LA GUARDA — sin cambios.
  --
  -- El límite es del FORMULARIO, no del consultorio: Cecilia tiene que poder
  -- darle un turno más a quien lo necesite desde el panel.

  if new.canal <> 'web' then
    return new;
  end if;


  -- ② LA CERRADURA — sin cambios. No se toca.
  --
  -- Pone en fila los pedidos de ESE paciente para que dos reservas simultáneas
  -- no cuenten las dos "no tiene ninguno" y entren las dos. Se suelta sola
  -- cuando termina la transacción del insert.

  perform pg_advisory_xact_lock(
    hashtext( 'limite_turnos' ),
    new.paciente_id::int
  );


  -- ③ EL CONTEO — sin cambios. Los cinco filtros siguen siendo los mismos, y
  -- `inicio > now()` es el que libera el cupo al pasar la hora de inicio.

  select count(*)
    into ya_tiene
    from public.turnos
   where paciente_id = new.paciente_id
     and profesional_id = new.profesional_id
     and canal = 'web'
     and activo
     and inicio > now();


  -- ④ EL RECHAZO — ACÁ ESTÁ EL CAMBIO, y es todo el cambio.
  --
  -- Antes decía `>= 2`. Ahora alcanza con que tenga UNO.
  --
  -- El `>` sigue sin sobrar aunque el conteo nunca debería pasar de uno: es una
  -- guarda. Si alguna vez entrara una fila de más por otro camino, un `= 1`
  -- fallaría la igualdad y el límite dejaría de aplicarse justo cuando más falta
  -- hace. El `>=` no cuesta nada y no tiene ese modo de falla.
  --
  -- El código CB001 NO cambia: es el que la Edge Function `reservar` traduce a
  -- un 409 con texto para la pantalla. El texto de acá no lo ve el paciente.

  if ya_tiene >= 1 then
    raise exception 'ya tiene un turno con este profesional'
      using errcode = 'CB001';
  end if;


  return new;
end;
$$;


-- 🔒 PERMISOS. `create or replace` CONSERVA los permisos de la función que
-- reemplaza, así que en teoría el `revoke` del 28-ago sigue en pie. Se repite
-- igual: cuesta nada, no rompe nada si ya estaba, y deja la garantía escrita en
-- la misma migración que toca la función en vez de a ocho migraciones de acá.

revoke execute
  on function public.limitar_turnos_por_paciente ()
  from public;
