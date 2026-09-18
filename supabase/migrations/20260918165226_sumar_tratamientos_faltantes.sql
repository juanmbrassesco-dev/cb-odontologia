-- Los tres tratamientos que Cecilia hace y el sistema no conocía.
--
-- Aparecieron de rebote: al pedirle la lista para el letrero de fachada nombró
-- tres que no estaban ni en la tabla ni en el sitio. No es que se hubieran
-- borrado, nunca se cargaron.
--
-- `ortopedia` va pegada a `ortodoncia` en el orden porque son el par natural:
-- una mueve los dientes, la otra guía el crecimiento de los maxilares. Quien
-- busca una suele estar mirando la otra.
--
-- Los tres van con `duracion_web_min` en NULL, y eso NO significa que no se
-- puedan elegir por la web -- la confusión ya se leyó mal dos veces. Significa
-- que no tienen duración propia: el paciente los elige como MOTIVO, entra como
-- consulta de 30 minutos, y el profesional reasigna turnos más largos después
-- de verlo. El único con duración propia además de la consulta es `limpieza`.
--
-- `ATM` va en mayúscula porque es una sigla (articulación temporomandibular),
-- no una palabra; el resto de la tabla está en minúscula porque son nombres
-- comunes. Y `prótesis` va a secas: el detalle que dio Cecilia -- fija,
-- removible, sobre implantes -- es material del sitio, no de un desplegable.

insert into public.tratamientos ( nombre, orden, duracion_web_min ) values
  ( 'ortopedia'      ,  85, null ),
  ( 'prótesis'       ,  95, null ),
  ( 'ATM y bruxismo' , 100, null );


-- 🔴 LA SEGUNDA MITAD, y sin ella los tres no existen para el paciente: un
-- tratamiento que no está emparejado con ningún profesional no lo puede hacer
-- nadie. El paciente lo elegiría como motivo, el sistema buscaría quién lo
-- hace, no encontraría a nadie, y el turno no se podría reservar.
--
-- Va en la misma migración porque es el mismo hecho: "el consultorio ofrece
-- esto". Partirlo en dos dejaría un estado intermedio donde el tratamiento
-- figura y no se puede reservar.
--
-- Se empareja con TODOS los profesionales activos y no con el id 1 a mano: hoy
-- hay uno solo, pero un id clavado envejece en silencio el día que entre el
-- segundo -- y el modelo se reabrió en agosto justamente porque había un
-- supuesto de "una sola profesional" que no estaba escrito en ninguna tabla.

insert into public.profesional_tratamientos ( profesional_id, tratamiento_id )
select p.id, t.id
  from public.profesionales p
  cross join public.tratamientos t
  where p.activo
    and t.nombre in ( 'ortopedia', 'prótesis', 'ATM y bruxismo' );
