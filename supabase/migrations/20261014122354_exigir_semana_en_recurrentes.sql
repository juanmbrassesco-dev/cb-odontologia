-- EXIGIR LA SEMANA EN LAS RECURRENTES — etapa ⑤.5, rebanada A.
--
-- 🔴 QUÉ ARREGLA, Y LO ENCONTRÓ LA PRUEBA, NO LA LECTURA. La migración
-- `acotar_tipos_de_excepcion`, aplicada diez minutos antes que ésta, dejó
-- escrito que una excepción 'recurrente' sin `semana_del_mes` no se puede
-- guardar. **Y se podía: la fila entraba sin una queja.**
--
-- EL MOTIVO es la regla del vacío de SQL, que este proyecto ya tiene escrita en
-- la migración `agregar_fin_maximo_a_horarios` y en el glosario, al lado de
-- `is distinct from`: **comparar contra un valor ausente no da "falso", da "no
-- sé" — y un `check` sólo rechaza lo que da FALSO.**
--
-- Paso por paso, con la fila que entró ('recurrente', semana vacía):
--
--     tipo <> 'recurrente'                →  FALSO      (el tipo es ése)
--     semana_del_mes between 1 and 5      →  NO SÉ      (no hay número)
--     FALSO or NO SÉ                      →  NO SÉ      ← no es FALSO
--     el check acepta la fila
--
-- 🔑 POR QUÉ LA REGLA DE AL LADO SÍ FUNCIONABA, que es lo que hace entendible
-- la diferencia: `excepciones_unica_con_fecha` pregunta `fecha_desde is not
-- null`, y `is not null` **siempre** contesta sí o no — nunca "no sé". Las dos
-- reglas se leían igual y sólo una de las dos cerraba.
--
-- ⚠️ LA MIGRACIÓN ANTERIOR NO SE EDITA: una aplicada es historia. Se reemplaza
-- la regla acá, con su nombre, y el `drop` de abajo es la única forma de
-- cambiarle el contenido a una restricción que ya existe.
--
-- ✅ La fila real ('recurrente', semana 3) cumple la versión nueva: su semana
-- está cargada.


alter table public.excepciones
  drop constraint excepciones_recurrente_con_semana;


alter table public.excepciones
  add constraint excepciones_recurrente_con_semana
    check (
      tipo <> 'recurrente'
      or (
        semana_del_mes is not null
        and semana_del_mes between 1 and 5
      )
    );

-- El `is not null` de adentro es lo único que cambió, y es lo que convierte el
-- "no sé" en un NO: con la semana vacía, el paréntesis entero da FALSO, el `or`
-- da FALSO, y la base rechaza la fila.
--
-- El `between` se queda igual y sigue haciendo falta: tapa el 0, el 6 y el -3,
-- que son números cargados y mal.
