-- ACOTAR LOS TIPOS DE EXCEPCIÓN — etapa ⑤.5, rebanada A.
--
-- QUÉ HABILITA: que el panel pueda escribir en `excepciones` sin que una fila
-- mal armada se guarde y no haga nada.
--
-- 🔴 POR QUÉ ESTA MIGRACIÓN VA ANTES DEL `grant`, y no es prolijidad. La
-- columna `tipo` es `not null` y hasta hoy NO tenía ninguna regla: acepta
-- 'unica', 'recurrente', 'vacaciones', 'Unica' y 'cualquier cosa' por igual. Y
-- `tapaEsteDia( )` —en `_shared/disponibilidad.ts`— termina diciendo que un
-- tipo que no conoce SE IGNORA, a propósito: tapar de más le cancela el turno a
-- alguien real, ignorar de más deja un día abierto que la profesional ve y
-- arregla.
--
-- Mientras la única fila la escribía una migración, eso era inofensivo. Desde
-- que lo escribe una pantalla, el silencio significa exactamente lo que esta
-- etapa viene a evitar: **la ausencia quedó cargada, la base la aceptó, y el
-- sistema sigue ofreciendo los turnos de las vacaciones.** Nadie se entera
-- hasta que un paciente viaja al consultorio al vacío.
--
-- 🔑 LAS TRES REGLAS SON UNA SOLA COSA —"que una fila de `excepciones`
-- signifique algo"— y por eso van juntas en una migración. Las tres se apoyan
-- en el mismo hecho: cada `tipo` se lee con columnas DISTINTAS, así que una
-- fila a la que le falta la columna de su tipo no es un dato incompleto, es un
-- dato que no se puede leer.
--
-- ✅ LAS CUMPLE LA FILA QUE YA EXISTE (la tercera semana de Cecilia:
-- 'recurrente', semana 3, sin fechas), así que entran sin tocar un solo dato.


alter table public.excepciones
  add constraint excepciones_tipo_valido
    check ( tipo in ( 'unica', 'recurrente' ) );

-- Los dos valores que el código sabe leer, y ninguno más. Compara texto
-- EXACTO: 'Unica' con mayúscula queda afuera, que es lo que se busca — dos
-- escrituras distintas del mismo tipo serían dos tipos para la base y uno solo
-- para la persona que lo cargó.


alter table public.excepciones
  add constraint excepciones_unica_con_fecha
    check (
      tipo <> 'unica'
      or fecha_desde is not null
    );

-- Una excepción de un solo día o de un rango SIN fecha de arranque no dice
-- nada: `tapaEsteDia( )` lo primero que hace es mirar `fecha_desde` y, si está
-- vacía, devolver que no tapa.
--
-- 🔑 LA FORMA DE ESTA REGLA ES LA QUE HAY QUE LEER DOS VECES, porque dice algo
-- más angosto de lo que parece: NO exige que toda fila tenga `fecha_desde`.
-- Exige que la tengan las de tipo 'unica'. Una fila 'recurrente' pasa por la
-- primera mitad y la segunda ni se mira.


alter table public.excepciones
  add constraint excepciones_recurrente_con_semana
    check (
      tipo <> 'recurrente'
      or semana_del_mes between 1 and 5
    );

-- El espejo de la anterior: una regla que se repite se lee por su semana del
-- mes, así que sin ese número tampoco se puede leer.
--
-- ⚠️ EL TOPE ES 5 Y NO 4, y conviene no re-razonarlo: la semana N es la fila
-- del almanaque que contiene el día `7N − 6`, o sea el 1, el 8, el 15, el 22 y
-- el 29. **El 29 existe todos los meses**, así que la quinta semana es una
-- semana real y dejarla afuera prohibiría una ausencia posible.
