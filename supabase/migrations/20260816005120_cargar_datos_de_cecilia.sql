-- La primera profesional del consultorio, con su agenda y sus tratamientos.
--
-- Va por migración y no a mano en el editor de tablas por decisión de Juan: son
-- diecinueve filas tipeadas, y siete de ellas son los horarios, que es el dato
-- del que depende TODO el cálculo de disponibilidad. Un 11:30 escrito como
-- 11:03 no falla con un error: devuelve huecos que no existen. Escrito acá,
-- queda revisable, versionado y repetible en cualquier base nueva.
--
-- Las tres cargas van juntas en una sola migración porque se revierten juntas:
-- una profesional sin horarios ni tratamientos no sirve para nada. La regla de
-- nombres del proyecto pide separar cuando hay una "y" — el criterio de fondo
-- es que se puedan leer y revertir por separado, y acá no se puede.

insert into public.profesionales ( nombre, apellido, email )
values ( 'Cecilia', 'Brassesco', 'cecilia@example.com' );

-- OJO: ese correo es de PRUEBA y hay que cambiarlo antes de producción.
--
-- `example.com` es un dominio reservado por norma (RFC 2606) para ejemplos y
-- documentación: nadie lo puede registrar, así que un mail escrito ahí no le
-- llega nunca a un desconocido. Por eso es el valor seguro para un repositorio
-- público.
--
-- No va acá el correo real de nadie. El de la profesional todavía no está
-- confirmado, y un correo personal en un repo público se queda en el historial
-- de git para siempre.
--
-- Se carga un valor provisional en vez de esperar el definitivo porque `email`
-- es un dato mutable: se cambia con un update de una línea. Esperarlo habría
-- dejado el sistema de turnos frenado por algo editable en un segundo. Y no
-- hace falta que funcione todavía: el primer mail se manda en la etapa ③.
--
-- Para encontrarlo el día que haya que cambiarlo:  git grep example.com

insert into public.profesional_tratamientos ( profesional_id, tratamiento_id )
select
  ( select id from public.profesionales where apellido = 'Brassesco' ),
  tratamientos.id
from
  public.tratamientos;

-- Hace todas las parejas de una vez: Cecilia con cada uno de los once
-- tratamientos de la tabla, ortodoncia incluida.
--
-- Se escriben así, y no con los números a mano, porque los `id` los inventa la
-- base. Ni el de Cecilia ni los de los tratamientos se conocen al escribir
-- este archivo, y si mañana se corre sobre una base nueva van a ser otros.
-- La consulta los busca en el momento.

insert into public.horarios_base ( profesional_id, dia_semana, inicio, fin )
values
  ( ( select id from public.profesionales where apellido = 'Brassesco' ), 1, '08:00', '14:00' ),
  ( ( select id from public.profesionales where apellido = 'Brassesco' ), 2, '11:00', '12:30' ),
  ( ( select id from public.profesionales where apellido = 'Brassesco' ), 2, '13:00', '17:00' ),
  ( ( select id from public.profesionales where apellido = 'Brassesco' ), 3, '08:00', '14:00' ),
  ( ( select id from public.profesionales where apellido = 'Brassesco' ), 4, '11:00', '12:30' ),
  ( ( select id from public.profesionales where apellido = 'Brassesco' ), 4, '13:00', '17:00' ),
  ( ( select id from public.profesionales where apellido = 'Brassesco' ), 5, '08:00', '14:00' );

-- Los siete tramos, en números ISO 8601: lunes 1, martes 2, miércoles 3,
-- jueves 4, viernes 5. Sábados y domingos no aparecen, y ésa es toda la
-- manera de decir que no atiende: el hueco es la ausencia de una fila, no una
-- fila que diga "cerrado".
--
-- El martes y el jueves llevan DOS filas cada uno porque corta al mediodía. El
-- almuerzo tampoco se modela: entre las 12:30 y las 13:00 simplemente no hay
-- tramo.
--
-- Se repite la búsqueda de Cecilia en cada renglón. Es prolijo de leer así
-- —una línea por tramo, con los días y las horas en columna— y el precio es
-- una consulta repetida siete veces sobre una tabla de una fila.
