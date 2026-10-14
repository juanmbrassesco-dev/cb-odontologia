-- EXIGIR UNA DESCRIPCIÓN DE VERDAD — etapa ⑤.5, rebanada A.
--
-- QUÉ ARREGLA, y salió de auditar las cuatro reglas anteriores: `descripcion`
-- es `not null`, y eso **no impide guardar una cadena vacía ni tres espacios**.
-- `not null` prohíbe la ausencia del dato, no su inutilidad.
--
-- 🔑 POR QUÉ ESTA COLUMNA Y NO OTRA: es lo ÚNICO que después explica por qué un
-- día está cerrado. La fila que existe hoy lo dice entero —«Tercera semana de
-- cada mes: la profesional no atiende»— y por eso, meses después, se entiende
-- qué significa. Con la descripción en blanco, la lista del panel muestra
-- renglones que tapan días y no dicen por qué, y el único camino para
-- averiguarlo es leer `fecha_desde` y adivinar.
--
-- ⚠️ Y VA EN LA BASE AUNQUE EL ENDPOINT TAMBIÉN LA VALIDE, que es el principio
-- que este proyecto ya tiene escrito en el `check` de `dia_semana`: **que el
-- panel muestre un campo obligatorio no es una defensa, porque nada obliga a
-- pasar por el panel para escribir en la base.**
--
-- ✅ La fila real la cumple de sobra.


alter table public.excepciones
  add constraint excepciones_descripcion_con_texto
    check ( length( trim( descripcion ) ) > 0 );

-- El `trim` es la mitad que importa: sin él, tres espacios pasan la regla
-- —tienen largo 3— y en pantalla se ven exactamente igual que el vacío.
