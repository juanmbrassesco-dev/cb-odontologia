-- Hasta acá `profesionales.email` cargaba DOS significados a la vez: "a dónde le
-- aviso" y, si el panel lo hubiera reusado, "con qué cuenta entra". Son dos datos
-- con ciclos de vida distintos: la dirección pública del consultorio puede cambiar
-- sin que cambie la cuenta de quien entra, y al revés.
--
-- El caso que lo volvió concreto: el 6-oct-2026 `email` quedó en
-- `contacto@cbodontologiayestetica.com.ar`, que es un REENVÍO de Cloudflare Email
-- Routing y no un buzón. Una dirección que no es buzón no es una cuenta de Google,
-- así que anclando el acceso ahí la única persona que no podría entrar al panel
-- sería la dueña del consultorio.
--
-- `unique` porque la cuenta identifica a UNA fila: si dos profesionales tuvieran
-- la misma, el portero no sabría a cuál de los dos le está abriendo.
--
-- ACEPTA NULO, y es la mitad que hace que esto funcione: un profesional que
-- alquila consultorio y no usa el panel se carga sin este dato. PostgreSQL permite
-- VARIOS nulos en una columna `unique` —dos nulos no se consideran iguales entre
-- sí—, así que la restricción no estorba a los que no tienen acceso.
--
-- El valor NO viaja en esta migración. Una migración aplicada es historia y no se
-- edita, así que un dato que puede cambiar no vive acá: la columna nace vacía y se
-- carga a mano. El valor queda anotado en la § 9.1.e del doc de estado, que es
-- privado.

alter table public.profesionales
  add column email_de_acceso text unique;
