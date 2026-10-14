-- VALIDAR EL RANGO DE FECHAS DE UNA EXCEPCIÓN — etapa ⑤.5, rebanada A.
--
-- QUÉ HABILITA: que una ausencia cargada al revés no se guarde.
--
-- 🔴 EL MODO DE FALLA ES EL MISMO QUE EL DE LA MIGRACIÓN ANTERIOR, y por eso
-- esta regla existe: una ausencia del 30 al 20 de octubre —dos dígitos
-- invertidos al tipear— hace que `tapaEsteDia( )` no tape NI UN SOLO DÍA. La
-- condición que mira es `fecha >= fecha_desde and fecha <= fecha_hasta`, y con
-- el rango al revés no hay ninguna fecha que cumpla las dos.
--
-- La fila entra, la base no se queja, la pantalla la muestra en la lista, y
-- Cecilia se va de vacaciones creyendo que lo cargó.
--
-- 🔑 VA APARTE DE LA ANTERIOR, Y ES LA REGLA DE NOMBRES DEL PROYECTO
-- FUNCIONANDO: aquélla acota QUÉ TIPOS existen, ésta valida UN RANGO. Si
-- entraran juntas habría que llamarlas "acotar tipos y validar fechas", y la
-- "y" es la señal de que son dos migraciones.
--
-- ✅ La fila que ya existe no tiene fechas cargadas, así que pasa por el primer
-- renglón de la condición y entra sin tocarse.


alter table public.excepciones
  add constraint excepciones_rango_valido
    check (
      fecha_hasta is null
      or fecha_desde is null
      or fecha_hasta >= fecha_desde
    );

-- Los dos primeros renglones NO son prolijidad defensiva, son lo que deja
-- pasar a las filas legítimas:
--
--   · `fecha_hasta` vacía es un feriado de un día, o una ausencia sin fecha de
--     fin: las dos son válidas y no tienen nada que comparar.
--   · `fecha_desde` vacía es una recurrente, que no se lee por fechas.
--
-- Recién cuando las dos están cargadas hay una comparación posible, y ahí sí
-- se exige el orden del almanaque.
--
-- 🔑 EL `>=` Y NO EL `>`: desde y hasta el MISMO día es el feriado escrito con
-- las dos columnas, que es una carga razonable y tapa un día. Con `>` la base
-- rechazaría una fila que significa exactamente lo mismo que dejar
-- `fecha_hasta` vacía.
