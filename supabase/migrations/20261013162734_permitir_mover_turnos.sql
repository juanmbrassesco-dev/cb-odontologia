-- PERMITIR MOVER UN TURNO — etapa ⑤.4.
--
-- QUÉ HABILITA: que el portero pueda cambiarle a un turno la hora de arranque
-- y la duración.
--
-- ⚠️ LO QUE `turnos` YA TENÍA Y NO ES ESTO, porque se confunde fácil: desde el
-- 29-ago hay un `grant update ( activo, aviso_estado, aviso_at,
-- inicio_avisado )`. Con eso se puede CANCELAR un turno y marcar que se avisó
-- — nada más. Mover necesita escribir `inicio` y `duracion_min`, que no
-- estaban en ninguna lista.
--
-- 🔴 LAS DOS COLUMNAS VAN JUNTAS PORQUE SON LA MISMA DECISIÓN. Un turno ocupa
-- un TRAMO, no un instante: moverlo a las 15:00 con 90 minutos es otro tramo
-- que moverlo a las 15:00 con 30. La pantalla las manda juntas y el constraint
-- `turnos_sin_solapar` las mira juntas, así que separarlas en dos permisos
-- dejaría escribir media decisión.
--
-- 🔴 LO QUE SIGUE SIN PERMISO, Y ES DELIBERADO: `paciente_id`,
-- `profesional_id`, `tratamiento_id` y `obra_social_id`. Mover un turno de
-- hora es una cosa; pasárselo a OTRA PERSONA o a otro profesional es otra, y
-- un error en el endpoint de mover no puede terminar haciéndola — la base lo
-- rechaza. Si algún día hace falta reasignar, es su propia pantalla con su
-- propio permiso, y probablemente con su propio correo: al paciente hay que
-- decirle que lo atiende otro.
--
-- 🔑 `inicio_avisado` NO ENTRA ACÁ porque ya la tiene. Es la columna que hace
-- que el correo de cambio pueda nombrar la hora vieja: guarda qué se le
-- comunicó al paciente la última vez, y cuando difiere de `inicio`, el turno
-- se movió y él todavía no lo sabe.

grant update ( inicio, duracion_min )
  on public.turnos
  to service_role;
