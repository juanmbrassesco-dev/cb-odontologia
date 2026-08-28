-- El turno pasa a recordar QUÉ SABE EL PACIENTE de él, al lado de lo que el turno ES.
--
-- `activo` dice si el turno está vivo o cancelado: es el HECHO.
-- `aviso_estado` dice qué es lo último que se le comunicó al paciente: es lo que
-- ÉL CREE. Son dos cosas distintas y por eso son dos columnas — un turno puede
-- estar cancelado y el paciente seguir creyendo que lo tiene, porque el correo
-- no salió. Comparar las dos es lo único que le permite a la repesca (fase 6)
-- descubrir qué aviso falta y mandarlo.
--
-- `aviso_at` es CUÁNDO se escribió esa marca. Parece decoración hasta que un
-- envío se muere por la mitad: un turno que quedó en 'enviando' hace más de diez
-- minutos es un envío muerto, y `aviso_at` es lo único que lo distingue de uno
-- que está saliendo en este momento.


alter table public.turnos
  add column aviso_estado text,
  add column aviso_at     timestamptz;


-- Los tres valores posibles, cerrados con la misma forma que el canal en la
-- migración 20260828135023.
--
-- 🔴 EL VACÍO NO ESTÁ EN LA LISTA Y SIN EMBARGO PASA. Un `check` no se viola
-- cuando la columna está vacía: sólo juzga los valores que hay. Acá eso es
-- exactamente lo que se quiere —vacío significa "no se le avisó nada todavía",
-- que es como nace cada turno—, pero conviene tenerlo escrito: es la clase de
-- detalle que se descubre tarde y por el lado malo.

alter table public.turnos
  add constraint turnos_aviso_estado_valido
  check (
    aviso_estado in ( 'enviando', 'reservado', 'cancelado' )
  );

comment on column public.turnos.aviso_estado is
  'Lo último que el paciente SABE de este turno: vacío (nada), enviando, reservado o cancelado. No es el estado del turno, que lo dice activo.';

comment on column public.turnos.aviso_at is
  'Cuándo se escribió aviso_estado. Un enviando con más de 10 minutos es un envío que se murió y se vuelve a tomar.';


-- 🔒 EL PERMISO CRECE CON LO QUE EL PORTERO HACE, NI UNA COLUMNA MÁS.
--
-- Hasta hoy la única columna que el portero modificaba era `activo`, y el grant
-- del paso F nombraba esa sola. A partir de ahora `cancelar` y la repesca
-- escriben también la marca, así que la lista pasa a nombrar tres. Sigue siendo
-- un grant ACOTADO POR COLUMNAS: una cuarta columna no se va a poder escribir
-- hasta que alguien la nombre acá.
--
-- Sin esta línea, el primer intento de marcar un aviso muere con un 42501 que
-- no nombra la causa por ningún lado — el mismo fallo mudo del 16-ago.

grant update ( activo, aviso_estado, aviso_at )
  on public.turnos
  to service_role;


-- 🔴 LOS TURNOS QUE YA EXISTEN NACEN CON LA MARCA VACÍA, Y ESO ES MENTIRA.
--
-- Vacío significa "no se le avisó nada", y a estos pacientes YA se les avisó
-- cuando reservaron. Sin este relleno, la primera corrida de la repesca lee la
-- tabla entera como pendiente y le manda un correo a TODOS los pacientes con
-- turno futuro. La repesca tiene que arrancar mirando sólo lo que pase de acá
-- en adelante.

update public.turnos
  set aviso_estado = 'reservado'
  where activo;


-- 🔴 SI CAMBIA UN DATO QUE EL CORREO NOMBRA, LO QUE EL PACIENTE SABE QUEDÓ VIEJO.
--
-- Los cinco datos son los que el correo le dijo: cuándo, cuánto dura, con quién,
-- de qué y para quién. Si Cecilia mueve el turno de hora o se lo pasa a otro
-- profesional, el correo que el paciente tiene en la casilla pasa a mentir, y
-- borrar la marca es la forma de dejar anotado "a esta persona hay que volver a
-- avisarle". Este trigger NO manda nada: sólo deja el pendiente escrito, y la
-- repesca lo levanta.
--
-- No alcanza con `inicio`: con eso solo quedaba abierto el caso de la
-- reasignación a otro profesional, donde el paciente llega a la hora correcta a
-- ver a alguien que no lo espera.
--
-- ⚠ `is distinct from` y no `<>`: `tratamiento_id` PUEDE ESTAR VACÍA, y en SQL
-- el vacío no es un valor sino un "no sé" — `<>` contra un vacío no contesta ni
-- sí ni no, y un `if` que recibe "no sé" no entra. O sea que con `<>` un turno
-- cargado a mano sin tratamiento y completado después NUNCA volvería a avisar.
-- `is distinct from` trata al vacío como un valor más y siempre contesta.
--
-- ⚠ EL TRIGGER NO SE DISPARA A SÍ MISMO, y esto no se "simplifica": cuando la
-- repesca escribe `aviso_estado`, las otras cinco columnas llegan en `new` con
-- el mismo valor que en `old` —un `update` que no las nombra no las cambia—,
-- así que ningún renglón da verdadero y la marca recién puesta sobrevive. Sin
-- esa propiedad, esto es un bucle de correos.

create function public.borrar_aviso_si_cambia_el_turno ()
  returns trigger
  language plpgsql
as $$
begin

  if new.inicio         is distinct from old.inicio
  or new.duracion_min   is distinct from old.duracion_min
  or new.profesional_id is distinct from old.profesional_id
  or new.tratamiento_id is distinct from old.tratamiento_id
  or new.paciente_id    is distinct from old.paciente_id
  then
    new.aviso_estado := null;
    new.aviso_at     := null;
  end if;

  return new;
end;
$$;


-- `before update` y no `after`: escribirle a `new` sólo cambia lo que se va a
-- guardar mientras la fila todavía no se guardó. Después ya es tarde y haría
-- falta un `update` aparte, que volvería a disparar el trigger.

create trigger turnos_borrar_aviso_al_cambiar
  before update on public.turnos
  for each row
  execute function public.borrar_aviso_si_cambia_el_turno ();


-- 🔒 Toda función nueva se queda sin `execute` para nadie, como manda
-- `herramientas/auditar-base-supabase.md` § 3.b. No la desactiva: un trigger
-- ejecuta su función sin mirar este permiso. Lo que cierra es que alguien la
-- llame por su cuenta.

revoke execute
  on function public.borrar_aviso_si_cambia_el_turno ()
  from public;
