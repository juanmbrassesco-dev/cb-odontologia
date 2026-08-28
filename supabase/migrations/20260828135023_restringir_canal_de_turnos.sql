-- `turnos.canal` deja de ser texto libre: pasa a aceptar sólo dos valores.

-- Hasta hoy la columna acepta cualquier texto. `reservar` escribe siempre 'web'
-- y todo lo demás lo tipea una persona, así que nada impide que algún día entre
-- 'Web', 'WEB' o 'pagina'.
--
-- Eso importa por lo que viene atrás: el límite de turnos por paciente decide si
-- actúa leyendo `canal = 'web'`, y compara texto EXACTO. Un 'Web' con mayúscula
-- no rompería nada de forma visible — el turno entraría igual y el límite
-- quedaría apagado para esa fila, sin fallar con error y sin que nadie se entere.
--
-- Se aplica sin riesgo porque la tabla está hoy en cero filas, verificado con
-- `select distinct canal from turnos` antes de escribir esto: un check que choca
-- con una fila que ya existe no se aplica a medias, voltea el alter entero.


alter table public.turnos
  add constraint turnos_canal_valido
    check (
      canal in ( 'web', 'manual' )
    );


-- DOS valores y no cuatro. El porqué queda escrito porque una lista corta se lee
-- como un olvido:
--
--   'web'    → lo escribe el sistema, desde el formulario del sitio.
--   'manual' → lo carga una persona en el consultorio, venga el pedido por
--              teléfono, por WhatsApp o del paciente que está enfrente.
--
-- `telefono` no entra porque el sistema no puede distinguirlo de un manual: el
-- turno lo teclea alguien igual, y pedirle a esa persona que además declare de
-- dónde vino es trabajo manual con riesgo de error, para un dato que ya sabe.
--
-- `whatsapp` no entra TODAVÍA: va a tener sentido el día que exista el bot y sea
-- el bot el que escriba la fila. Un valor reservado para el futuro contamina la
-- lista y se empieza a usar antes de significar lo que va a significar. Agregarlo
-- ese día cuesta una migración de dos líneas; el `check` es barato de ampliar.


comment on column public.turnos.canal is
  'Cómo entró el turno al sistema. Valores válidos: web, manual.';


-- El comentario no controla nada y la base nunca lo lee para decidir. Existe
-- porque el error de un check nombra la constraint y no lista ni un valor, así
-- que sin esto quien carga un turno a mano tendría que equivocarse primero para
-- enterarse de qué puede escribir. El Table Editor lo muestra al lado del campo,
-- antes de escribir.


-- ✅ PERMISOS: no hace falta ninguno. Un `check` no es un objeto que se ejecute
-- ni una tabla que se lea: es una regla que la base aplica sola en cada escritura,
-- con los permisos que ya tenga quien escribe. Y `comment on column` es
-- documentación, no un privilegio nuevo para nadie.
