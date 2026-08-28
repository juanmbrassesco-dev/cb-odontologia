-- Un paciente no puede tener más de dos turnos web abiertos con el mismo profesional.

-- El límite es del FORMULARIO, no del consultorio: Cecilia tiene que poder darle
-- un tercer turno a quien lo necesite. Por eso el canal manda dos veces — en la
-- guarda, que deja pasar de largo todo lo que no sea web, y en el conteo, que
-- tampoco suma los turnos cargados a mano. Lo segundo no repite a lo primero: un
-- paciente de ortodoncia tiene controles que le carga ella, y si contaran, con
-- dos controles agendados quedaría sin poder reservar nada por el sitio.
--
-- Y va en la BASE y no en el portero por la carrera: dos pedidos simultáneos del
-- mismo paciente leerían los dos "hay uno" y entrarían los dos. Es el mismo
-- razonamiento por el que la doble reserva se impide con la restricción de
-- exclusión y no con un `if`.


create function public.limitar_turnos_por_paciente ()
  returns trigger
  language plpgsql
as $$
declare
  ya_tiene integer;
begin

  -- ────────────────────────────────────────────────────────────────
  -- ① LA GUARDA
  --
  -- En castellano: si el canal de la fila que quiere entrar es distinto
  -- de 'web', dejala pasar y no hagas nada más.
  --
  -- Tres líneas. Lo que está adentro del `if` va corrido a la derecha.
  -- ────────────────────────────────────────────────────────────────

  if new.canal <> 'web' then
    return new;
  end if;


  -- ────────────────────────────────────────────────────────────────
  -- ② LA CERRADURA — ya escrita. No se toca.
  --
  -- Pone en fila los pedidos de ESE paciente para que dos reservas
  -- simultáneas no cuenten las dos "hay 1" y entren las dos. Se suelta
  -- sola cuando termina la transacción del insert.
  --
  -- Van DOS claves y no el `paciente_id` pelado porque el espacio de
  -- estas cerraduras es global a la base: con una sola clave, el
  -- paciente 7 compartiría cerradura con cualquier otra cosa que algún
  -- día bloquee por el número 7. La primera clave es el espacio de
  -- nombres; la segunda, la persona.
  -- ────────────────────────────────────────────────────────────────

  perform pg_advisory_xact_lock(
    hashtext( 'limite_turnos' ),
    new.paciente_id::int
  );


  -- ────────────────────────────────────────────────────────────────
  -- ③ EL CONTEO Y EL RECHAZO
  --
  -- Cuenta los turnos que ese paciente ya tiene con ese profesional y,
  -- si son dos o más, aborta. El conteo es el que decide, así que lo
  -- que importa de verdad son los cinco filtros del `where`: cada uno
  -- saca de la cuenta algo que no debe pesar.
  -- ────────────────────────────────────────────────────────────────

  select count(*)
    into ya_tiene
    from public.turnos
   where paciente_id = new.paciente_id
     and profesional_id = new.profesional_id
     and canal = 'web'
     and activo
     and inicio > now();

  if ya_tiene >= 2 then
    raise exception 'ya tiene dos turnos con este profesional'
      using errcode = 'CB001';
  end if;


  return new;
end;
$$;


-- El trigger es lo que engancha la función a la tabla. `before insert` importa:
-- corre ANTES de que la fila se escriba, que es lo único que permite impedirla.

create trigger turnos_limite_por_paciente
  before insert on public.turnos
  for each row
  execute function public.limitar_turnos_por_paciente ();


-- 🔒 PERMISOS, como manda `herramientas/auditar-base-supabase.md` § 3.b: toda
-- función nueva se queda sin `execute` para nadie. No la desactiva — un trigger
-- ejecuta su función sin chequear ese permiso. Lo que cierra es que alguien la
-- llame por su cuenta.

revoke execute
  on function public.limitar_turnos_por_paciente ()
  from public;
