-- El correo del paciente es el ANCLA de su identidad (§ 9.8): el portero busca
-- por él para saber a quién puede pedirle turno el que está conectado.
--
-- El problema es que los dos lados de esa comparación no se escriben en el
-- mismo lugar. El correo de la SESIÓN lo normaliza Supabase Auth: se probó el
-- 23-ago-2026 entrando con el correo en mayúsculas y el token vino en
-- minúsculas igual. El correo de la TABLA lo carga Cecilia a mano desde el
-- Table Editor, y ahí no lo normaliza nadie.
--
-- Si ella tipea `Maria@Gmail.com`, la búsqueda por `maria@gmail.com` no
-- encuentra nada y el endpoint devuelve una LISTA VACIA, que es una respuesta
-- válida: se lee como "paciente nuevo", no como error. Es el modo de falla
-- caro, el que no avisa.
--
-- Se NORMALIZA en vez de RECHAZAR porque acá no hay ambigüedad: `Maria@Gmail.com`
-- y `maria@gmail.com` son la misma casilla, así que pasar a minúsculas no pierde
-- información. Un `check` sería lo correcto si los dos valores pudieran
-- significar cosas distintas, y no es el caso. Además, del otro lado del `check`
-- hay una persona que no puede interpretar un error de Postgres.

create or replace function public.email_en_minusculas()
returns trigger
language plpgsql
as $$
begin

  new.email = lower( new.email );

  return new;

end;
$$;

-- Las dos líneas van JUNTAS, y el porqué está en `auditar-base-supabase.md` § 3.b:
-- Postgres le da `execute` al pseudo-rol `public` a toda función nueva, y eso es
-- lo que hay que sacar. Revocar a secas puede romper la escritura, así que el
-- permiso se le devuelve al único rol que escribe en esta base.
revoke execute on function public.email_en_minusculas() from public;
grant execute on function public.email_en_minusculas() to service_role;

-- `before` y no `after`: el disparador tiene que corregir el valor ANTES de que
-- la fila se guarde. Un `after` vería el correo ya escrito y llegaría tarde.
--
-- `update` además de `insert` porque el agujero no se cierra en el alta: una
-- corrección posterior desde el Table Editor lo reabriría igual.
create trigger pacientes_email_en_minusculas
before insert or update on public.pacientes
for each row
execute function public.email_en_minusculas();
