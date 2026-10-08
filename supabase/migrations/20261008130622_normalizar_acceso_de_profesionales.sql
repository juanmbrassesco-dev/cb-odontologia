-- El mismo agujero que `normalizar_email_de_pacientes` cerró para `pacientes`, y
-- acá muerde más fuerte: los dos lados de la comparación no se escriben en el
-- mismo lugar. El correo de la SESIÓN lo normaliza Supabase Auth —probado el
-- 23-ago-2026 entrando con mayúsculas: el token vino en minúsculas igual— y
-- `email_de_acceso` lo tipea una persona a mano.
--
-- Cargado como `Ana@Gmail.com`, la búsqueda por `ana@gmail.com` no
-- encuentra nada. Y acá el vacío no se lee como "paciente nuevo" sino como "no es
-- profesional": el portero contesta 403 y la dueña del consultorio queda afuera
-- sin un solo error en pantalla.
--
-- Se NORMALIZA en vez de RECHAZAR por lo mismo que en `pacientes`: `Ana@Gmail.com`
-- y `ana@gmail.com` son la misma cuenta, así que pasar a minúsculas no pierde
-- información.
--
-- POR QUÉ UNA FUNCIÓN HERMANA Y NO SE GENERALIZA `email_en_minusculas()`: esa
-- función escribe sobre `new.email` por nombre fijo. Generalizarla para que reciba
-- el nombre de la columna obliga a SQL dinámico y a borrar y recrear el trigger de
-- `pacientes`, que es historia ya aplicada: más riesgo sobre una tabla que anda,
-- por ahorrar seis líneas. Convendría la versión genérica el día que sean cinco o
-- seis columnas en tablas distintas pidiendo lo mismo.
--
-- `profesionales.email` queda SIN normalizar a propósito, y no es un olvido: no es
-- ancla de ningún login, así que su modo de falla es un aviso que sale raro, no una
-- persona que no puede entrar. Si alguna vez se normaliza, va en su propia
-- migración.

create or replace function public.acceso_en_minusculas()
returns trigger
language plpgsql
as $$
begin

  new.email_de_acceso = lower( new.email_de_acceso );

  return new;

end;
$$;

-- Las dos líneas van JUNTAS, igual que en `normalizar_email_de_pacientes`:
-- PostgreSQL le da `execute` al pseudo-rol `public` a toda función nueva, y eso es
-- lo que hay que sacar. Revocar a secas puede romper la escritura, así que el
-- permiso se le devuelve al único rol que escribe en esta base.
revoke execute on function public.acceso_en_minusculas() from public;
grant execute on function public.acceso_en_minusculas() to service_role;

-- `before` y no `after`: el disparador tiene que corregir el valor ANTES de que la
-- fila se guarde. Un `after` la vería ya escrita y llegaría tarde.
--
-- `update` además de `insert` porque el agujero no se cierra en el alta: una
-- corrección posterior desde el Table Editor lo reabriría igual.
create trigger profesionales_acceso_en_minusculas
before insert or update on public.profesionales
for each row
execute function public.acceso_en_minusculas();
