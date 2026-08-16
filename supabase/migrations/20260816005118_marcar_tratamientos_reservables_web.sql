-- Qué puede reservar el paciente por la web, y cuánto dura, pasa a ser un dato
-- de la base.
--
-- Hasta hoy `tratamientos` era una lista de nombres y nadie contestaba dos
-- preguntas que el sitio necesita: cuáles de los once se le muestran al
-- paciente, y cuánto espacio se le reserva en la agenda si elige uno.
--
-- No pueden vivir en el navegador. El navegador corre en la máquina del
-- paciente y cualquiera edita lo que manda: si la duración viajara en el
-- pedido, se podría reservar una limpieza de 5 minutos (entra donde no cabe y
-- pisa el turno siguiente) o una consulta de 4 horas (tapa la mañana entera).
-- El portero recibe el tratamiento y busca acá la duración; no la recibe.
--
-- Tampoco conviene en el código del portero, aunque ahí sí sería seguro: la
-- lista de reservables quedaría en un archivo y los nombres en la base, o sea
-- dos fuentes para el mismo hecho, y cambiar la limpieza a 45 minutos exigiría
-- desplegar en vez de editar una fila.

alter table public.tratamientos
  add column duracion_web_min integer
    check ( duracion_web_min > 0 and duracion_web_min % 30 = 0 );

-- La columna es OPCIONAL a propósito: vacía significa "este tratamiento no se
-- reserva por la web". Vacío no es cero — un 0 sería una duración, diría "dura
-- cero minutos", que es falso, y además metería la fila en la grilla como si
-- fuera reservable.
--
-- Por eso es UNA columna y no dos. Con `reservable_web` por un lado y la
-- duración por otro existiría un estado imposible —reservable que sí, duración
-- vacía— que habría que prohibir con otra regla. Así ese estado no se puede
-- ni escribir.
--
-- Lleva `web` en el nombre porque la duración REAL de un tratamiento la sigue
-- decidiendo el profesional turno por turno con criterio clínico. Esta columna
-- no dice cuánto dura una limpieza: dice cuánto espacio reserva el sistema
-- cuando la pide un paciente. `turnos.duracion_min` es la otra, y confundirlas
-- desarma la agenda.
--
-- El `check` protege la grilla de media hora sobre la que está construido todo
-- el cálculo de disponibilidad. Una duración de 45 no encaja en ningún bloque
-- y el endpoint la acomodaría mal en silencio; así la base la rechaza de
-- entrada. Si algún día el consultorio necesita medias horas partidas, esta
-- línea es el lugar donde la suposición está escrita.

update public.tratamientos
  set duracion_web_min = 30
  where nombre = 'consulta';

update public.tratamientos
  set duracion_web_min = 60
  where nombre = 'limpieza';

-- Las otras nueve filas quedan vacías, que es exactamente lo que se quiere
-- decir de ellas. No hace falta escribirlas.
--
-- La lista de reservables es CERRADA por regla del consultorio, no un estado
-- transitorio: los demás tratamientos salen de la consulta previa y los asigna
-- el profesional desde su panel.
