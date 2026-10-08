-- El permiso del panel tiene DOS NIVELES de paquete fijo, no sub-permisos que se
-- prendan uno por uno: dar de alta a un profesional le habilita todo su nivel de
-- una vez. La matriz completa de quién puede qué vive en el plan de la fase ⑤.
--
-- `boolean` porque la pregunta que contesta esta columna tiene dos respuestas y no
-- hay una tercera: o manda sobre la agenda de todos, o sólo sobre la suya. Es el
-- mismo criterio con el que `activo` ya es boolean en esta tabla.
--
-- `not null` + `default false` van JUNTOS y por el mismo motivo: sin `default`, el
-- valor de fábrica de una columna en PostgreSQL es NULL, que es justo lo único que
-- `not null` prohíbe. Sobre una tabla que ya tiene filas, la instrucción entera
-- fallaría con `column … contains null values`.
--
-- Y el `default` es `false` porque el caso normal es NO ser admin: el que manda es
-- la excepción. Al revés —`default true`— cada profesional nuevo nacería con
-- acceso a los datos de todos los demás hasta que alguien se acordara de apagarlo,
-- y un permiso que hay que recordar quitar es un permiso que se queda puesto.

alter table public.profesionales
  add column es_admin boolean not null default false;
