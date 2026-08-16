-- La regla más investigada del proyecto, que hasta hoy no existía como dato:
-- la tercera semana de cada mes la profesional no atiende.
--
-- `excepciones` tenía CERO filas. La regla estaba cerrada en el documento de
-- estado y en la cabeza de todos, y el cálculo de disponibilidad la habría
-- ignorado sin decir nada: habría ofrecido una semana entera de turnos que no
-- existen, con pacientes reales del otro lado.

insert into public.excepciones ( descripcion, tipo, semana_del_mes, activa, profesional_id )
values (
  'Tercera semana de cada mes: la profesional no atiende.',
  'recurrente',
  3,
  true,
  ( select id from public.profesionales where apellido = 'Brassesco' )
);

-- `fecha_desde` y `fecha_hasta` quedan vacías, y eso dice algo preciso: la
-- regla no tiene fecha de fin. Cecilia confirmó el 15-ago que todavía no sabe
-- hasta cuándo se ausenta. El día que lo sepa, esto es un update de una línea;
-- mientras tanto, vacío es la verdad.
--
-- `activa = true` es lo que la apaga cuando termine. Acá tampoco se borran
-- filas: se apaga el estado, como en el resto del proyecto. Una excepción
-- borrada no deja rastro de por qué esa semana estuvo cerrada durante meses.
--
-- Qué significa exactamente `semana_del_mes = 3`, porque "la tercera semana"
-- en castellano es ambiguo y el endpoint necesita una sola respuesta:
--
--   Es la semana del almanaque que contiene el día 15.
--
-- La cuenta general es `7N − 6`: N=1 → día 1, N=2 → día 8, N=3 → día 15,
-- N=4 → día 22. Para el caso de Cecilia da exactamente lo que ella describió.
-- La generalización a las otras semanas es una derivación nuestra, no algo que
-- ella haya dicho: si algún día aparece una excepción con N distinto de 3, esta
-- interpretación se confirma antes de usarla.
--
-- Se escribe acá y no sólo en el código del portero porque es el significado
-- del DATO. Quien abra la tabla dentro de un año va a ver un 3, y el 3 no dice
-- desde qué día se cuenta.
