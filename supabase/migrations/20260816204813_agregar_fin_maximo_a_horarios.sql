-- Hasta qué hora se puede ESTIRAR un turno que no entra completo antes del
-- cierre, tramo por tramo.
--
-- El caso real: Cecilia cierra los lunes a las 14:00, pero si un turno de 60
-- minutos arranca a las 13:30 lo atiende igual y termina 14:30. Sin este dato
-- el sistema tendría que elegir entre dos errores: cortar la agenda a las 14:00
-- y perder un turno que ella sí toma, o dejar que cualquier tratamiento se
-- estire sin techo y ofrecer las 13:30 para algo de dos horas.
--
-- Es un TECHO, no agenda nueva. Un turno no puede EMPEZAR después del `fin`:
-- `fin_maximo` sólo permite que uno que empezó a horario termine más tarde.
-- La diferencia importa — si se leyera como agenda, los lunes se ofrecería un
-- turno a las 14:00, que no existe.

alter table public.horarios_base
  add column fin_maximo time;

-- OPCIONAL a propósito, mismo idioma que `duracion_web_min` en `tratamientos`:
-- vacío significa "este tramo no se estira", no "se estira cero minutos".
-- El tramo de martes y jueves de 13:00 a 17:00 queda vacío porque después no
-- hay nada que empuje: es el último del día y ahí Cecilia se va.

alter table public.horarios_base
  add constraint horarios_base_fin_maximo_valido
    check ( fin_maximo > fin );

-- Que nadie escriba un techo ANTERIOR al cierre. Un `fin_maximo` de 13:00 en un
-- tramo que termina a las 14:00 no da un error: le acorta el día a la
-- profesional en silencio, que es la clase de bug que se descubre cuando un
-- paciente se queja de que no consigue turno.
--
-- El vacío sigue entrando: en SQL, comparar contra un valor ausente no da
-- "falso", da "no sé", y un `check` sólo rechaza lo que da falso. Por eso una
-- columna opcional y una regla sobre ella conviven sin excepciones escritas.

alter table public.horarios_base
  add constraint horarios_base_tramo_valido
    check ( fin > inicio );

-- Esta regla la tabla no la tenía, y no es teórica: un tramo cargado al revés
-- —`18:00` a `09:00`— hoy entraría sin quejarse y devolvería cero bloques. Un
-- día entero desaparecido de la agenda, sin un solo error en pantalla.
--
-- Las 7 filas actuales la cumplen, así que entra sin tocar un solo dato.

update public.horarios_base
  set fin_maximo = '14:30'
  where profesional_id = ( select id from public.profesionales where apellido = 'Brassesco' )
    and fin = '14:00';

update public.horarios_base
  set fin_maximo = '13:00'
  where profesional_id = ( select id from public.profesionales where apellido = 'Brassesco' )
    and fin = '12:30';

-- Tres filas en el primero (lunes, miércoles y viernes de 8:00 a 14:00) y dos
-- en el segundo (martes y jueves de 11:00 a 12:30). Los dos tramos de la tarde
-- quedan vacíos.
--
-- El `where` acota por profesional aunque hoy haya una sola: la tabla es
-- multi-profesional por diseño desde el 6-ago, y un `update` que no la nombra
-- pisaría los horarios de cualquiera que se cargue después en una base nueva.
-- El `id` no se escribe a mano porque lo inventa la base — mismo motivo que en
-- `cargar_datos_de_cecilia`.
--
-- Se filtra por hora de cierre y no por día de la semana porque la regla de
-- Cecilia es sobre el tramo, no sobre el día: los que terminan a las 14:00 se
-- estiran media hora, el corto del mediodía se estira hasta las 13:00 porque a
-- esa hora empieza el siguiente. Escrito por día, agregar un tramo nuevo
-- obligaría a recordar esta migración; escrito así, la regla se lee sola.
