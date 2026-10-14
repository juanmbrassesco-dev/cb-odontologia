-- APAGAR UN TRAMO DE LA AGENDA SEMANAL — etapa ⑤.5, rebanada C.
--
-- QUÉ HABILITA: que un tramo de atención —«los viernes de 8 a 14»— se pueda
-- SACAR de la agenda sin borrar la fila.
--
-- 🔴 POR QUÉ UNA COLUMNA Y NO UN `delete`, y es la decisión que tomó Juan el
-- 14-oct-2026 con el costo de las dos opciones sobre la mesa. El borrado era
-- técnicamente seguro —`horarios_base` es una de las dos únicas tablas de las
-- siete que nadie apunta con una foreign key—, y aun así pierde:
--
--   · Rompe el no-hagas duro del proyecto, que dice apagar el estado y no
--     borrar la fila. El mismo criterio que ya rige en `excepciones` (`activa`),
--     en `profesionales` (`activo`) y en `profesional_tratamientos`.
--   · Y habilita un caso REAL que el borrado no cubre: «en verano no atiendo
--     los viernes». Con `activo` se apaga en diciembre y se vuelve a prender en
--     marzo; borrando, hay que recargar el tramo entero con su hora de cierre y
--     su `fin_maximo` a mano, y lo que se recarga a mano se recarga distinto.
--
-- ⚠️ EL COSTO ACEPTADO, dicho: la pantalla tiene que mostrar los tramos
-- apagados —si los escondiera, la columna no serviría para volver a prenderlos—
-- y eso suma renglones a una lista que ya tiene siete días.
--
-- 🔑 Y LA COLUMNA NO HACE NADA SOLA: el cálculo de la grilla tiene que
-- filtrarla. Sin ese filtro, un tramo apagado sigue ofreciendo turnos y la
-- migración es decoración. Va en `_shared/grilla.ts`, en el mismo commit.


alter table public.horarios_base
  add column activo boolean
    not null
    default true;

-- `default true` y `not null` van juntas por lo que ya está escrito en el
-- glosario, al lado de `default`: sin un valor por defecto, PostgreSQL le pone
-- `null` a las filas que ya existen —justo lo único que `not null` prohíbe— y
-- el `alter table` entero falla con `column … contains null values`.
--
-- Las 7 filas de la agenda de Cecilia quedan en `true`: su agenda sigue igual.
