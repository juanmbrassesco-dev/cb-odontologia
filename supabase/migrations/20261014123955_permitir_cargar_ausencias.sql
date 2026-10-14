-- PERMITIR CARGAR Y APAGAR AUSENCIAS — etapa ⑤.5, rebanada A.
--
-- QUÉ HABILITA: que el portero pueda ESCRIBIR en `excepciones`. Hasta hoy la
-- tabla tenía `grant select` y nada más —puesto el 7-ago con la etapa ①—, así
-- que cargar una ausencia significaba entrar al Table Editor de Supabase.
--
-- 🔑 POR QUÉ ESTE PERMISO ENTRA AHORA Y NO ANTES: es la regla del proyecto que
-- ya se cumplió con `turnos` —el `insert` llegó con la etapa ③ y el `update`
-- con la ④—. **El permiso entra con la funcionalidad que lo usa, nunca por
-- adelantado.**
--
-- 🔴 `activa` QUEDA FUERA DEL `insert`, A PROPÓSITO. La columna tiene `default
-- true`, así que la pone la base: una ausencia nace tapando, que es para lo que
-- se carga. Si el portero pudiera escribirla, un alta podría nacer APAGADA —una
-- fila que está en la lista, parece cargada y no tapa nada—. Es el mismo
-- criterio escrito en `permitir_alta_de_profesionales`, donde `activo` también
-- quedó afuera.
--
-- 🔴 Y EL `update` ES DE UNA SOLA COLUMNA, igual que en `permitir_apagar_parejas`.
-- Con un `grant update` sobre la tabla entera, el endpoint que prende y apaga
-- quedaría habilitado a reescribir también `profesional_id`, `fecha_desde` o
-- `tipo` — o sea a MUDAR la ausencia de una persona a otra, o a correrle las
-- fechas. Un error ahí no apagaría nada: le cambiaría las vacaciones a otro, en
-- silencio y sin que nada falle. Nombrando la columna, **la base rechaza esa
-- escritura aunque el código la intente**.
--
-- ⚠️ NO HAY `delete`, y es la regla del proyecto: no se borran filas, se apaga
-- el estado. Una excepción borrada no deja rastro de por qué esa semana estuvo
-- cerrada durante meses.


grant insert (
    descripcion,
    tipo,
    fecha_desde,
    fecha_hasta,
    semana_del_mes,
    profesional_id
  )
  on public.excepciones
  to service_role;


grant update ( activa )
  on public.excepciones
  to service_role;
