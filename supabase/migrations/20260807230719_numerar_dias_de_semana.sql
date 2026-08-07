-- El día de la semana pasa de texto a número, con el estándar ISO 8601.
--
--     lunes 1 · martes 2 · miércoles 3 · jueves 4 · viernes 5 · sábado 6 · domingo 7
--
-- La columna era `text` y la tabla nunca tuvo datos, así que nadie había
-- decidido qué se escribía adentro: "martes", "Martes", "mar" y "2" eran todos
-- igual de válidos para la base.
--
-- Se elige número, y ISO 8601 entre las dos convenciones que existen, por un
-- motivo concreto: cuando el sistema pregunte "¿qué horarios hay el martes 15 de
-- septiembre?", Postgres le va a sacar el día de la semana a esa fecha con
-- `extract( isodow from … )`, que devuelve exactamente esta numeración. Guardando
-- texto habría que traducir en los dos sentidos, en cada consulta, y ahí es donde
-- aparece el clásico "¿el domingo es 0 o es 7?".
--
-- La otra convención —`dow`, con domingo 0 y sábado 6— se descartó justamente
-- por ese 0: obliga a recordar que la semana arranca en domingo, que no es como
-- se piensa una agenda de consultorio.
--
-- Lo que se guarda y lo que se muestra son cosas distintas: el paciente nunca ve
-- un número. La traducción a "martes" se escribe una sola vez, al pintar la
-- pantalla, y de ahí para adentro nadie más se entera.


alter table public.horarios_base
  alter column dia_semana type smallint
  using dia_semana::smallint;

-- `smallint` y no `integer`: el rango va de 1 a 7 y no va a crecer nunca.
--
-- El `using` le dice a Postgres CÓMO convertir lo que ya había, porque de texto
-- a número no hay traducción automática. Acá no convierte nada —la tabla está
-- vacía— pero la instrucción lo exige igual.


alter table public.horarios_base
  add constraint horarios_base_dia_semana_valido
  check ( dia_semana between 1 and 7 );

-- La segunda mitad, y es la que de verdad protege: sin esto, la columna acepta
-- un 0, un 8 o un -3 sin decir nada, y el error recién aparecería mucho después,
-- como un día de atención que no le figura a nadie.
--
-- Quién escribe esta columna es la pregunta que decide para qué sirve: NO la
-- escribe el paciente, ni por la web ni por el bot de WhatsApp. `horarios_base`
-- es configuración del consultorio, y la cargan Cecilia o el panel de admin. La
-- restricción protege de una carga a mano mal tipeada, de un bug en ese panel el
-- día que exista, y de una migración futura mal escrita.
--
-- Vale el mismo principio que la restricción anti-solapamiento: que el panel
-- muestre un desplegable con siete opciones no es una defensa, porque nada
-- obliga a pasar por el panel para escribir en la base.
