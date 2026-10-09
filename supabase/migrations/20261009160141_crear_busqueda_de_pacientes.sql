-- BUSCAR UN PACIENTE POR NOMBRE Y APELLIDO JUNTOS.
--
-- 🔴 QUÉ ARREGLA, Y SE MIDIÓ ANTES DE ESCRIBIR ESTO. Lo levantó Juan probando
-- el panel el 9-oct-2026: «aparece un momento, desaparece, no te deja
-- clickearlo». Medido contra el portero real:
--
--     q = "rafa"      → 1 resultado
--     q = "rafa b"    → 0 resultados      ← acá se rompía
--     q = "rafa bra"  → 0 resultados
--
-- El buscador comparaba el término contra CADA COLUMNA POR SEPARADO, así que
-- «rafa b» no coincidía con nadie: nadie tiene ese texto adentro de su nombre
-- NI adentro de su apellido. Y el síntoma era peor que un cero, porque la
-- pantalla abre el alta de ficha cuando no hay coincidencias: los resultados
-- buenos desaparecían y aparecía el formulario para crear un paciente que YA
-- EXISTÍA. O sea, el agujero que el buscador existe para tapar.
--
-- 🔑 POR QUÉ UNA FUNCIÓN DE LA BASE Y NO UN FILTRO MÁS COMPLICADO EN EL
-- PORTERO. Los filtros de PostgREST comparan columnas contra valores y no
-- saben concatenar: `nombre || ' ' || apellido` no se puede expresar desde
-- ahí. Acá sí, y en una línea.
--
-- 🔒 Y SE LLEVA PUESTA UNA CLASE ENTERA DE AGUJERO, DE REGALO. El filtro que
-- reemplaza se armaba PEGANDO el término adentro de un texto —
-- `nombre.ilike.%ana%,apellido.ilike.%ana%`—, y una coma ahí deja de ser un
-- valor y pasa a ser un separador: INYECCIÓN DE FILTRO (filter injection).
-- El portero la tapaba sacándole al término las comas y los paréntesis.
-- Una función recibe el término como PARÁMETRO, y un parámetro no se puede
-- confundir con la consulta que lo lleva. *El saneado del portero se queda
-- igual: los comodines `%` y `_` siguen siendo comodines acá adentro, y
-- además una defensa que ya está probada no se saca porque apareció otra.*
--
-- Los DOS ÓRDENES —«nombre apellido» y «apellido nombre»— porque el
-- consultorio escribe de las dos maneras según de dónde venga el dato: del
-- teléfono sale «Rafa Brassesco» y de una ficha vieja, «Brassesco Rafa».
--
-- `stable` es una PROMESA al motor: esta función no escribe nada y, dentro de
-- una misma consulta, con los mismos argumentos devuelve lo mismo. No es
-- decoración — es lo que le permite a Postgres llamarla una sola vez.


create function public.buscar_pacientes( termino text )
  returns table (
    id       bigint,
    nombre   text,
    apellido text,
    email    text,
    telefono text
  )
  language sql
  stable
as $$

  select p.id,
         p.nombre,
         p.apellido,
         p.email,
         p.telefono
    from public.pacientes p
   where ( p.nombre || ' ' || p.apellido ) ilike '%' || termino || '%'
      or ( p.apellido || ' ' || p.nombre ) ilike '%' || termino || '%'
      or p.email ilike '%' || termino || '%'

   order by p.apellido,
            p.nombre

   -- El tope vive acá y no en el portero: si lo pusiera el que llama, cada
   -- pantalla nueva tendría que acordarse de ponerlo, y la que se olvide se
   -- trae la tabla entera.
   limit 20;

$$;


-- 🔒 SE LLAMA POR HTTP, así que lleva el mismo tratamiento que
-- `reclamar_avisos_pendientes`: se le quita el `execute` a todo el mundo y se
-- le devuelve SOLO al portero.
--
-- ⚠ Y no es opcional: `create function` le da `execute` a `public` POR
-- DEFECTO. Una función nueva sin estas dos líneas nace ejecutable por
-- cualquiera — es un valor por defecto inseguro (insecure default), y acá
-- expondría la tabla con los datos personales.

revoke execute
  on function public.buscar_pacientes ( text )
  from public;

grant execute
  on function public.buscar_pacientes ( text )
  to service_role;
