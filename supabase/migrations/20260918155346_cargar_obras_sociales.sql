-- Las setenta obras sociales de Cecilia, más `Particular`.
--
-- La lista la pasó ella el 12-ago-2026 y vivía sólo como texto en el documento
-- de estado del proyecto. Entra TAL CUAL: no se depura, no se renombra y no se
-- saca ninguna fila, incluidas las dos que no son obras sociales en sentido
-- estricto -- `PREVENCION ART` y `Normas de Trabajo de Pre Pago` --. Es su
-- respuesta a una pregunta que ya se le hizo; corregirla por nuestra cuenta
-- sería inventar un dato del consultorio.
--
-- `Particular` es la primera fila y no es una obra social: es lo que hace que
-- un campo obligatorio no deje afuera a quien paga de su bolsillo. Si la
-- cobertura de alguien no está en esta lista, es porque el consultorio no
-- trabaja ese convenio, y la salida es Particular.
--
-- `entidad` agrupa quince filas bajo cinco títulos -- IAPOS, DOS, ARTE DE
-- CURAR, CORA y MEDIFE -- y en las otras cincuenta y seis repite el nombre.
-- `DOS MOTORES CZERWENY` queda como entidad propia a propósito: hay una fila
-- aparte, `TADEO CZERWENY`, que es una fábrica santafesina, así que colgarla
-- del grupo DOS sería afirmar algo que nadie verificó con Cecilia.
--
-- Va por migración y no a mano desde el panel porque es dato del consultorio
-- que el sistema necesita para funcionar: tiene que poder reconstruirse en una
-- base vacía sin que nadie recuerde haberlo tipeado.

insert into public.obras_sociales ( nombre, entidad ) values
  ( 'Particular', 'Particular' ),
  ( 'A.M.U.R.', 'A.M.U.R.' ),
  ( 'ACEITEROS - OSIAD Salud', 'ACEITEROS - OSIAD Salud' ),
  ( 'AMEP', 'AMEP' ),
  ( 'AMERICA SERVICIOS', 'AMERICA SERVICIOS' ),
  ( 'AMSTERDAM SALUD', 'AMSTERDAM SALUD' ),
  ( 'ARTE DE CURAR', 'ARTE DE CURAR' ),
  ( 'ARTE DE CURAR ORT, ORTOPEDIA, IMPL., CIRUGÍA', 'ARTE DE CURAR' ),
  ( 'ASOCIACIÓN DE TRABAJADORES DE FARMACIA', 'ASOCIACIÓN DE TRABAJADORES DE FARMACIA' ),
  ( 'ASOCIACIÓN MUTUAL ARGUS SALUD', 'ASOCIACIÓN MUTUAL ARGUS SALUD' ),
  ( 'ASOCIACIÓN UNIÓN TAMBEROS - MILKAUT', 'ASOCIACIÓN UNIÓN TAMBEROS - MILKAUT' ),
  ( 'ASSPE SALUD', 'ASSPE SALUD' ),
  ( 'AUTOMUTUAL', 'AUTOMUTUAL' ),
  ( 'AVALIAN', 'AVALIAN' ),
  ( 'BANCARIOS - OSBA (SIACO)', 'BANCARIOS - OSBA (SIACO)' ),
  ( 'BOUNOUS', 'BOUNOUS' ),
  ( 'CAJA FORENSE', 'CAJA FORENSE' ),
  ( 'CENTRO ASISTENCIAL (ASOCIACIÓN MEDICA DEPARTAMENTO CASTELLANOS)', 'CENTRO ASISTENCIAL (ASOCIACIÓN MEDICA DEPARTAMENTO CASTELLANOS)' ),
  ( 'CIENCIAS ECONÓMICAS', 'CIENCIAS ECONÓMICAS' ),
  ( 'COGAS', 'COGAS' ),
  ( 'COOPERATIVA TELEFÓNICA TOSTADO', 'COOPERATIVA TELEFÓNICA TOSTADO' ),
  ( 'CORA - ASOCIACIÓN ESCLESIÁSTICA SAN PEDRO', 'CORA' ),
  ( 'CORA - O.S.S. Seguros', 'CORA' ),
  ( 'DASUTeN', 'DASUTeN' ),
  ( 'DOCTHOS', 'DOCTHOS' ),
  ( 'DOS BASICO', 'DOS' ),
  ( 'DOS INTEGRAL', 'DOS' ),
  ( 'DOS INTEGRAL PLATINO - DOS INTEGRAL PLATINO (OS)', 'DOS' ),
  ( 'DOS MOTORES CZERWENY', 'DOS MOTORES CZERWENY' ),
  ( 'ELEVAR - O.S. PASTELEROS-CONFITEROS-PIZZEROS-HELADEROS Y ALFAJOREROS', 'ELEVAR - O.S. PASTELEROS-CONFITEROS-PIZZEROS-HELADEROS Y ALFAJOREROS' ),
  ( 'ENERGÍA SALUD (AGUA Y ENERGÍA)', 'ENERGÍA SALUD (AGUA Y ENERGÍA)' ),
  ( 'ENSALUD (Molineros)', 'ENSALUD (Molineros)' ),
  ( 'FE SALUD', 'FE SALUD' ),
  ( 'FEDERADA SALUD', 'FEDERADA SALUD' ),
  ( 'FUTBOLISTAS AGREMIADOS ARGENTINOS', 'FUTBOLISTAS AGREMIADOS ARGENTINOS' ),
  ( 'GALENO ARGENTINA', 'GALENO ARGENTINA' ),
  ( 'IAPOS', 'IAPOS' ),
  ( 'IAPOS CAPACIDADES DIFERENTES', 'IAPOS' ),
  ( 'IAPOS EMBARAZADAS', 'IAPOS' ),
  ( 'IAPOS IMAGENES exclusivo IMPLANTES', 'IAPOS' ),
  ( 'IAPOS IMPLANTES', 'IAPOS' ),
  ( 'IAPOS PRÓTESIS', 'IAPOS' ),
  ( 'INTEGRAL SALUD', 'INTEGRAL SALUD' ),
  ( 'JERARQUICOS SALUD', 'JERARQUICOS SALUD' ),
  ( 'LUZ Y FUERZA', 'LUZ Y FUERZA' ),
  ( 'MEDICUS', 'MEDICUS' ),
  ( 'MEDIFE', 'MEDIFE' ),
  ( 'MEDIFE ORTODONCIA Y ORTOPEDIA', 'MEDIFE' ),
  ( 'MEDYCIN', 'MEDYCIN' ),
  ( 'Normas de Trabajo de Pre Pago', 'Normas de Trabajo de Pre Pago' ),
  ( 'O DONT', 'O DONT' ),
  ( 'O.M.I.N.T.', 'O.M.I.N.T.' ),
  ( 'O.P.D.E.A.', 'O.P.D.E.A.' ),
  ( 'O.S. PERSONAL RECOLECCION - BARRIDO - LIMPIEZA', 'O.S. PERSONAL RECOLECCION - BARRIDO - LIMPIEZA' ),
  ( 'OSDE', 'OSDE' ),
  ( 'OSDOP (Sistema Complementario)', 'OSDOP (Sistema Complementario)' ),
  ( 'OSPICA', 'OSPICA' ),
  ( 'OSSACRA', 'OSSACRA' ),
  ( 'PERSONAL INDUSTRIA DEL CAUCHO', 'PERSONAL INDUSTRIA DEL CAUCHO' ),
  ( 'PREVENCION ART', 'PREVENCION ART' ),
  ( 'PREVENCION SALUD', 'PREVENCION SALUD' ),
  ( 'S.A.D.A.I.C.', 'S.A.D.A.I.C.' ),
  ( 'S.A.T. (Sindicato Argentino de Televisión)', 'S.A.T. (Sindicato Argentino de Televisión)' ),
  ( 'SANATORIO SANTA FE', 'SANATORIO SANTA FE' ),
  ( 'SANCOR', 'SANCOR' ),
  ( 'SUTIAGA', 'SUTIAGA' ),
  ( 'SWISS MEDICAL GROUP', 'SWISS MEDICAL GROUP' ),
  ( 'TADEO CZERWENY', 'TADEO CZERWENY' ),
  ( 'UENO (ex SANITAS SALUD) - OSMATA', 'UENO (ex SANITAS SALUD) - OSMATA' ),
  ( 'UNL', 'UNL' ),
  ( 'WILLIAM HOPE', 'WILLIAM HOPE' );
