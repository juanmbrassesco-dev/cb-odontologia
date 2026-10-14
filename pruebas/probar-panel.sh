#!/usr/bin/env bash
#
# BATERÍA DE LA CERRADURA DEL PANEL — etapa ⑤.0
#
# Qué mide: que la puerta del panel distinga TRES situaciones distintas. No
# mide qué hace el panel: mide quién entra.
#
#   1. nadie            → 401   (lo rechaza la plataforma, antes de la función)
#   2. un paciente      → 403   ← el caso que justifica la etapa entera
#   3. el personal      → 200
#
# 🔑 EL DEL MEDIO ES EL QUE VALE. Un 403 ahí es la prueba de que un paciente
# logueado —con un token tan válido como el de Cecilia— no entra al panel. Sin
# ese caso esta batería no mide nada: el 401 lo da la plataforma sola y el 200
# lo daría también una puerta sin cerradura.
#
# Qué golpea: `GET /quien-soy`, que es el endpoint más chico que usa
# `_shared/quien-pide.ts`. Una función compartida no se puede golpear con
# `curl`, así que la prueba necesita una puerta de verdad.
#
# Qué hace falta en el `.env`:
#   - PRUEBA_EMAIL / PRUEBA_PASSWORD      el paciente de prueba (caso 2)
#   - SOPORTE_EMAIL / SOPORTE_PASSWORD    el admin de soporte  (caso 3)
#
# 🔴 POR QUÉ EL CASO 3 NO USA LA CUENTA DE CECILIA: ella entra con Google, así
# que no tiene contraseña en Supabase Auth y su token no se puede pedir con
# `grant_type=password`. El admin de soporte existe exactamente para esto —
# probar el panel sin depender de que ella esté.
#
# ⏰ Y tiene final: esa cuenta se borra ANTES DE PRODUCCIÓN. Es una credencial
# de larga vida (long-lived credential) viva en el mismo proyecto que guarda
# datos de salud.

set -u

set -a
source .env
set +a

FUNCIONES="$SUPABASE_URL/functions/v1"


# ── Las dos credenciales, chequeadas antes de empezar ────────────────────────
#
# Sin esto, un `.env` incompleto hace que el caso 3 falle con 403 y se lea como
# "la cerradura está mal", que es el diagnóstico equivocado.

if [ -z "${SOPORTE_EMAIL:-}" ] || [ -z "${SOPORTE_PASSWORD:-}" ]; then
  echo "❌ Faltan SOPORTE_EMAIL / SOPORTE_PASSWORD en el .env."
  echo "   Son los de la cuenta del admin de soporte: la misma dirección que"
  echo "   está cargada en profesionales.email_de_acceso, con contraseña."
  exit 1
fi


# ── Pedir un token ───────────────────────────────────────────────────────────

token_de() {

  curl -s "$SUPABASE_URL/auth/v1/token?grant_type=password" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H 'Content-Type: application/json' \
    -d "{ \"email\": \"$1\", \"password\": \"$2\" }" \
  | jq -r '.access_token'
}


TOKEN_PACIENTE=$( token_de "$PRUEBA_EMAIL" "$PRUEBA_PASSWORD" )

if [ "$TOKEN_PACIENTE" = "null" ] || [ -z "$TOKEN_PACIENTE" ]; then
  echo "❌ No se pudo obtener el token del paciente. Revisá PRUEBA_EMAIL / PRUEBA_PASSWORD."
  exit 1
fi

TOKEN_SOPORTE=$( token_de "$SOPORTE_EMAIL" "$SOPORTE_PASSWORD" )

if [ "$TOKEN_SOPORTE" = "null" ] || [ -z "$TOKEN_SOPORTE" ]; then
  echo "❌ No se pudo obtener el token de soporte. ¿Existe esa cuenta en Auth?"
  exit 1
fi


# ── Los tres casos ───────────────────────────────────────────────────────────

echo
echo "▶ 1. Sin token — tiene que dar 401"
echo "     (lo contesta la PLATAFORMA, no el código: quien-soy no lleva"
echo "      bloque en config.toml, así que verify_jwt queda prendido)"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  "$FUNCIONES/quien-soy" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY"

echo
echo "▶ 2. Token de un PACIENTE — tiene que dar 403   ← el caso que importa"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  "$FUNCIONES/quien-soy" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_PACIENTE"

echo
echo "▶ 3. Token del ADMIN DE SOPORTE — tiene que dar 200"

RESPUESTA=$(
  curl -s -w '\n%{http_code}' \
    "$FUNCIONES/quien-soy" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE"
)

CODIGO=$( echo "$RESPUESTA" | tail -1 )
CUERPO=$( echo "$RESPUESTA" | sed '$d' )

echo "   obtenido: $CODIGO"
echo "   cuerpo:   $CUERPO"


# ── La agenda del día ────────────────────────────────────────────────────────

HOY=$( date +%F )

echo
echo "▶ 4. La agenda de hoy, como ADMIN — 200"

AGENDA=$(
  curl -s -w '\n%{http_code}' \
    "$FUNCIONES/agenda-del-dia?fecha=$HOY" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE"
)

echo "   obtenido: $( echo "$AGENDA" | tail -1 )"
echo "   cuerpo:   $( echo "$AGENDA" | sed '$d' | head -c 300 )"

echo
echo "▶ 5. Sin fecha — 400"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  "$FUNCIONES/agenda-del-dia" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE"


# ── 6. EL CASO IDOR, y es el que mide la regla que escribimos ────────────────
#
# Un no-admin que manda `?profesional_id=` de OTRO tiene que recibir SU propia
# agenda, no la del otro. Para probarlo hace falta un no-admin, y la cuenta de
# soporte es admin: se le baja el permiso, se mide, y se le devuelve.
#
# 🔴 SI ESTE SCRIPT SE CORTA EN EL MEDIO, la cuenta queda sin es_admin. El
# comando para devolverlo está escrito abajo y es el mismo que corre solo:
#
#   supabase db query --linked "update public.profesionales set es_admin = true
#   where email_de_acceso = '$SOPORTE_EMAIL';"

echo
echo "▶ 6. IDOR: un NO-admin pidiendo la agenda de otro"
echo "     (se le baja es_admin a la cuenta de soporte y se le devuelve al final)"

supabase db query --linked \
  "update public.profesionales set es_admin = false where email_de_acceso = '$SOPORTE_EMAIL';" \
  > /dev/null 2>&1

# El token viejo sigue sirviendo: el permiso se lee de la BASE en cada pedido,
# no del token. Que esto funcione sin volver a loguearse ES la prueba de que la
# revocación es inmediata, que es el motivo por el que el rol no viaja firmado.
AJENA=$(
  curl -s \
    "$FUNCIONES/agenda-del-dia?fecha=$HOY&profesional_id=1" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE"
)

supabase db query --linked \
  "update public.profesionales set es_admin = true where email_de_acceso = '$SOPORTE_EMAIL';" \
  > /dev/null 2>&1

echo "   cuerpo:   $( echo "$AJENA" | head -c 300 )"

echo
echo "   ✅ Tiene que decir \"esAdmin\": false Y no traer NI UN turno del"
echo "      profesional 1. Si trae turnos ajenos, el parámetro se obedeció sin"
echo "      preguntar quién pide: eso es IDOR."

echo
echo "▶ es_admin restaurado — la salida va CRUDA, a propósito:"

# 🔴 Acá había un `grep -o '"es_admin": [a-z]*'` y NO IMPRIMIÓ NADA en la
# terminal de Juan, aunque la restauración sí había ocurrido. El motivo es que
# `supabase db query` NO devuelve el mismo formato en las dos máquinas: en una
# contesta JSON y en la otra una tabla, así que un grep que busca `"es_admin":
# true` encuentra cero.
#
# Era un chequeo que no chequeaba y no avisaba de que no chequeaba — el modo de
# falla más caro que hay.
#
# ✅ LA SALIDA: `--output csv`, que es la ÚNICA forma estable. El CLI tiene tres
# formatos y elige solo; con csv contesta lo mismo en cualquier máquina. Volvió
# a morder una tercera vez el mismo día, en el caso 8 de más abajo, que se
# declaró «no medible» con el turno a la vista dos pruebas más arriba.
supabase db query --linked --output csv \
  "select nombre, es_admin from public.profesionales where email_de_acceso = '$SOPORTE_EMAIL';" \
  2>/dev/null | tail -2

echo
echo "   ✅ es_admin tiene que decir TRUE. Si dice false, el script se cortó"
echo "      antes de restaurarlo: el comando para arreglarlo está comentado"
echo "      arriba, en el bloque del caso 6."


# ── 7 y 8. CANCELAR DESDE EL PANEL ───────────────────────────────────────────
#
# 🔴 EL CASO 8 ES EL QUE IMPORTA Y ES EL IDOR DE ESCRITURA: un profesional que
# NO es admin mandando el id de un turno que no es suyo. Si eso cancela, el
# paciente de otro se entera por el correo de cancelación.

echo
echo "▶ 7. Cancelar un turno que no existe — 403, no 404"
echo "     (el id inventado se contesta igual que el ajeno: dos respuestas"
echo "      distintas le dirían al que prueba ids cuáles existen)"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/cancelar-del-panel" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE" \
  -H 'Content-Type: application/json' \
  -d '{ "turno_id": 999999 }'

echo
echo "▶ 8. IDOR de ESCRITURA: un NO-admin cancelando un turno ajeno"
echo "     (se le baja es_admin a la cuenta de soporte y se le devuelve al final)"

supabase db query --linked \
  "update public.profesionales set es_admin = false where email_de_acceso = '$SOPORTE_EMAIL';" \
  > /dev/null 2>&1

# El turno activo más próximo, que es de Cecilia y NO de la cuenta de soporte.
#
# 🔴 TERCER INTENTO DE ESTE RENGLÓN, y las dos veces anteriores fallaron igual:
# el caso se saltó solo con el turno 428 activo y a la vista dos pruebas más
# arriba. Primero por buscar JSON donde el CLI contestaba una tabla; después
# por tomar la última línea con `tail -1`, que agarra una línea vacía si la
# salida termina con una.
#
# ✅ LO QUE QUEDA: `--output csv` para que el formato no dependa de la máquina,
# y `grep '^[0-9]+$'` para quedarse con el renglón que ES un número, haya
# encabezado, líneas vacías o avisos del CLI alrededor.
SALIDA_AJENO=$(
  supabase db query --linked --output csv \
    "select id from public.turnos where activo = true order by inicio desc limit 1;" \
    2>/dev/null
)

AJENO=$( echo "$SALIDA_AJENO" | grep -oE '^[0-9]+$' | tail -1 )

echo "   turno ajeno elegido: ${AJENO:-ninguno}"

if [ -n "$AJENO" ]; then

  curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
    -X POST "$FUNCIONES/cancelar-del-panel" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE" \
    -H 'Content-Type: application/json' \
    -d "{ \"turno_id\": $AJENO }"

else
  echo "   ❌ NO SE PUDO MEDIR EL CASO MÁS IMPORTANTE DE ESTA BATERÍA."
  echo "      No es un aviso: es una prueba que no corrió, y una prueba que no"
  echo "      corre se lee como verde. La salida cruda del CLI, para arreglarlo:"
  echo "$SALIDA_AJENO" | sed 's/^/      | /'
fi

supabase db query --linked \
  "update public.profesionales set es_admin = true where email_de_acceso = '$SOPORTE_EMAIL';" \
  > /dev/null 2>&1

echo
echo "   🔴 TIENE QUE DAR 403. Si da 200, el turno se canceló y la paciente"
echo "      recibió el correo: eso es el IDOR de escritura, y no se sigue"
echo "      construyendo nada arriba de eso."

echo
echo "▶ ¿sigue activo el turno ajeno? (tiene que decir TRUE)"

supabase db query --linked --output csv \
  "select id, activo from public.turnos where id = ${AJENO:-0};" \
  2>/dev/null | tail -2


# ── 9 a 11. EL BUSCADOR DE PACIENTES ─────────────────────────────────────────

echo
echo "▶ 9. Buscar pacientes sin token — 401"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  "$FUNCIONES/buscar-pacientes?q=bra" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY"

echo
echo "▶ 10. Buscar pacientes como PACIENTE — 403"
echo "      (un paciente no puede listar la tabla de pacientes)"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  "$FUNCIONES/buscar-pacientes?q=bra" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_PACIENTE"

# 🔴 EL CASO 11 ES EL DE SEGURIDAD DE ESTE ENDPOINT, y no se parece a los
# otros: no mide quién entra, mide QUÉ SE PUEDE ESCRIBIR ADENTRO del filtro.
#
# El `.or( … )` de PostgREST recibe los filtros como un solo texto separado por
# comas. Si el término de búsqueda viaja ahí con una coma adentro, deja de ser
# un valor y pasa a ser un SEPARADOR: el que busca escribe filtros propios. Es
# la misma familia que una inyección SQL, sobre la sintaxis de PostgREST.
#
# `id.gte.0` matchea TODAS las filas. Si el saneado no estuviera, esta llamada
# devolvería la tabla de pacientes entera hasta el tope de 20.

echo
echo "▶ 11. INYECCIÓN DE FILTRO: un término con una coma y un filtro adentro"

INYECCION=$(
  curl -s -G \
    "$FUNCIONES/buscar-pacientes" \
    --data-urlencode "q=zzz,id.gte.0" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE"
)

echo "   cuerpo:   $( echo "$INYECCION" | head -c 200 )"
echo

# 🔴 ESTE `if` LO PAGÓ UNA CORRIDA ENTERA, el 9-oct-2026. El endpoint contestó
# `{"error":"No se pudo buscar"}` —porque la migración del RPC no se había
# aplicado— y el renglón de abajo seguía diciendo «tiene que venir la lista
# vacía», que es verdad y no era lo que había pasado.
#
# Un error y una lista vacía se leen parecido de un vistazo y significan cosas
# OPUESTAS: una es la defensa funcionando, la otra es el endpoint roto. El
# chequeo tiene que decir cuál de las dos.
if echo "$INYECCION" | grep -q '"error"'; then

  echo "   ❌ ESTO NO ES UNA LISTA VACÍA: EL ENDPOINT CONTESTÓ UN ERROR."
  echo "      Lo más probable es que falte aplicar una migración —el portero"
  echo "      llama a una función de la base que todavía no existe—. Corré"
  echo "      'supabase db push' y volvé a probar. Este caso NO se midió."

else

  echo "   ✅ Tiene que venir la lista VACÍA. La coma se saneó, así que el"
  echo "      término quedó en 'zzz id.gte.0' y no coincide con nadie. Si trae"
  echo "      pacientes, el filtro se obedeció: eso es inyección de filtro."

fi


# ── 12 a 14. EL ALTA DE PACIENTE Y EL TURNO A MANO ───────────────────────────

echo
echo "▶ 12. Alta de paciente con los dos correos DISTINTOS — 400"
echo "      (es la defensa contra el correo válido pero ajeno)"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/paciente-del-panel" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE" \
  -H 'Content-Type: application/json' \
  -d '{ "nombre": "Prueba", "apellido": "Bateria", "email": "juana@ejemplo.test", "email_repetido": "juan@ejemplo.test" }'

# El paciente de la batería se crea SIN CORREO a propósito: así el turno del
# caso 14 no dispara ningún aviso y la casilla de prueba no se llena de correos
# en cada corrida. De paso prueba que una ficha sin correo es válida.
echo
echo "▶ 13. Alta de un paciente SIN correo — 201"
echo "      (Cecilia carga gente que sólo dejó un teléfono; es un caso real)"

ALTA=$(
  curl -s -w '\n%{http_code}' \
    -X POST "$FUNCIONES/paciente-del-panel" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE" \
    -H 'Content-Type: application/json' \
    -d '{ "nombre": "Sin Correo", "apellido": "Bateria", "telefono": "3420000000" }'
)

echo "   obtenido: $( echo "$ALTA" | tail -1 )"

PACIENTE_ID=$(
  echo "$ALTA" | sed '$d' | grep -oE '"id":[0-9]+' | head -1 | grep -oE '[0-9]+'
)

echo "   paciente creado: ${PACIENTE_ID:-ninguno}"

# 🔴 EL CASO 14 ES EL IDOR DE ESCRITURA DE ESTE ENDPOINT, y es peor que el de
# la agenda: no lee la agenda de otro, le LLENA la agenda a otro.
#
# Un no-admin manda `profesional_id` de otra persona. La regla dice que ese
# campo se ignora y el turno se crea a su nombre. Lo que se mide es el
# `profesional` de la RESPUESTA: tiene que ser el id de la cuenta de soporte,
# nunca el 1 que se mandó.

echo
echo "▶ 14. IDOR de ESCRITURA: un NO-admin cargando un turno a nombre de otro"

supabase db query --linked \
  "update public.profesionales set es_admin = false where email_de_acceso = '$SOPORTE_EMAIL';" \
  > /dev/null 2>&1

SOPORTE_ID=$(
  supabase db query --linked --output csv \
    "select id from public.profesionales where email_de_acceso = '$SOPORTE_EMAIL';" \
    2>/dev/null | grep -oE '^[0-9]+$' | tail -1
)

# Una fecha lejana y fija: no se pisa con nada real y la corrida de mañana cae
# en el mismo lugar, así que el choque 23P01 sería una señal de que el turno
# anterior no se apagó.
LEJOS=$( date -v+400d +%F 2>/dev/null || date -d '+400 days' +%F )

PARTICULAR=$(
  supabase db query --linked --output csv \
    "select id from public.obras_sociales where nombre = 'Particular';" \
    2>/dev/null | grep -oE '^[0-9]+$' | tail -1
)

TRATAMIENTO=$(
  supabase db query --linked --output csv \
    "select id from public.tratamientos limit 1;" \
    2>/dev/null | grep -oE '^[0-9]+$' | tail -1
)

if [ -n "$PACIENTE_ID" ] && [ -n "$PARTICULAR" ] && [ -n "$TRATAMIENTO" ]; then

  TURNO=$(
    curl -s -w '\n%{http_code}' \
      -X POST "$FUNCIONES/turno-del-panel" \
      -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
      -H "Authorization: Bearer $TOKEN_SOPORTE" \
      -H 'Content-Type: application/json' \
      -d "{ \"paciente_id\": $PACIENTE_ID,
            \"profesional_id\": 1,
            \"tratamiento_id\": $TRATAMIENTO,
            \"obra_social_id\": $PARTICULAR,
            \"duracion_min\": 30,
            \"inicio\": \"${LEJOS}T14:00:00-03:00\" }"
  )

  echo "   obtenido: $( echo "$TURNO" | tail -1 )"
  echo "   cuerpo:   $( echo "$TURNO" | sed '$d' | head -c 300 )"
  echo
  echo "   🔴 Tiene que dar 201 Y el \"profesional\" de la respuesta tiene que"
  echo "      ser $SOPORTE_ID, NO el 1 que se mandó. Si dice 1, el campo se"
  echo "      obedeció sin preguntar quién pide: eso es el IDOR de escritura."

  TURNO_ID=$(
    echo "$TURNO" | sed '$d' | grep -oE '"id":[0-9]+' | head -1 | grep -oE '[0-9]+'
  )

else
  echo "   ❌ NO SE PUDO MEDIR: falta el paciente, la cobertura o el"
  echo "      tratamiento. Una prueba que no corre se lee como verde."
fi

supabase db query --linked \
  "update public.profesionales set es_admin = true where email_de_acceso = '$SOPORTE_EMAIL';" \
  > /dev/null 2>&1

# El turno de la batería se APAGA, no se borra: es la regla del proyecto. Y se
# apaga con `aviso_estado` vacío, así que la repesca no manda ninguna
# cancelación — nadie se enteró nunca de ese turno.
if [ -n "${TURNO_ID:-}" ]; then

  supabase db query --linked \
    "update public.turnos set activo = false where id = $TURNO_ID;" \
    > /dev/null 2>&1

  echo
  echo "   turno de prueba $TURNO_ID apagado (no borrado)"
fi

echo
echo "▶ 15. Duración fuera de los bloques de 30 — 400"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/turno-del-panel" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE" \
  -H 'Content-Type: application/json' \
  -d "{ \"paciente_id\": ${PACIENTE_ID:-1},
        \"tratamiento_id\": ${TRATAMIENTO:-1},
        \"obra_social_id\": ${PARTICULAR:-1},
        \"duracion_min\": 45,
        \"inicio\": \"${LEJOS}T16:00:00-03:00\" }"


# ── 16 a 19. LA GRILLA DE HORAS DEL PANEL ────────────────────────────────────

echo
echo "▶ 16. La grilla sin token — 401"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  "$FUNCIONES/horarios-del-panel?fecha=$HOY&duracion=30" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY"

echo
echo "▶ 17. La grilla como PACIENTE — 403"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  "$FUNCIONES/horarios-del-panel?fecha=$HOY&duracion=30" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_PACIENTE"

echo
echo "▶ 18. La grilla con una duración fuera de los bloques de 30 — 400"
echo "      (el mismo tope que valida turno-del-panel, y a propósito está en"
echo "       los dos: una duración absurda armaría una grilla absurda)"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  "$FUNCIONES/horarios-del-panel?fecha=$HOY&duracion=45" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE"

# 🔴 EL CASO 19 ES EL QUE JUSTIFICA QUE ESTE ENDPOINT EXISTA, y no se mide por
# el código de respuesta: se mide comparando DOS respuestas.
#
# La misma fecha, el mismo profesional, dos duraciones. Si los bloques libres
# salen iguales, la duración no se está usando para nada — que es exactamente
# el bug que esta etapa vino a arreglar: un hueco de media hora no sirve para
# una ortodoncia de tres horas.

echo
echo "▶ 19. La MISMA fecha con dos duraciones — tienen que dar distinto"

# 🔴 DOS COSAS QUE LA PRIMERA VERSIÓN DE ESTE CASO HIZO MAL, y las dos lo
# dejaron en «0 de 0» — o sea, sin medir nada:
#
#   1. Preguntaba por la agenda de la CUENTA DE SOPORTE, que no tiene ninguna
#      cargada en `horarios_base`. Se pregunta por la de Cecilia, con
#      `?profesional=1`, y eso sólo lo puede hacer un admin: de paso queda
#      probado que el parámetro SÍ se obedece cuando quien pide lo es.
#   2. Clavaba un día a 30 vista, que puede caer domingo. Ahora se prueban
#      varios hasta dar con uno que tenga agenda.
#
# ⚠ Lo que salvó al caso fue el aviso que tenía escrito abajo. Sin esa línea,
# «0 de 0» se habría leído como verde.
DIA_GRILLA=""

for SALTO in 30 31 32 33 34 35 36; do

  CANDIDATO=$( date -v+${SALTO}d +%F 2>/dev/null || date -d "+$SALTO days" +%F )

  CUANTOS=$(
    curl -s \
      "$FUNCIONES/horarios-del-panel?fecha=$CANDIDATO&duracion=30&profesional=1" \
      -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
      -H "Authorization: Bearer $TOKEN_SOPORTE" \
      | grep -o '"inicio"' | wc -l | tr -d ' '
  )

  if [ "$CUANTOS" != "0" ]; then
    DIA_GRILLA="$CANDIDATO"
    break
  fi
done

if [ -z "$DIA_GRILLA" ]; then

  echo "   ❌ NO SE PUDO MEDIR: ningún día de la semana probada tiene agenda."
  echo "      Una prueba que no corre se lee como verde."

else

  echo "   día con agenda encontrado: $DIA_GRILLA"
  echo

  for DURA in 30 180; do

    CUERPO=$(
      curl -s \
        "$FUNCIONES/horarios-del-panel?fecha=$DIA_GRILLA&duracion=$DURA&profesional=1" \
        -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
        -H "Authorization: Bearer $TOKEN_SOPORTE"
    )

    LIBRES=$( echo "$CUERPO" | grep -o '"libre"' | wc -l | tr -d ' ' )
    TOTAL=$(  echo "$CUERPO" | grep -o '"inicio"' | wc -l | tr -d ' ' )

    echo "   duración $DURA min → $LIBRES libre(s) de $TOTAL bloque(s)"
  done

  echo
  echo "   ✅ Los dos números de LIBRES tienen que ser DISTINTOS, y el de 180"
  echo "      menor. Si son iguales, la duración no llegó al cálculo."
fi


# ── 20. BUSCAR POR NOMBRE Y APELLIDO JUNTOS ──────────────────────────────────
# ── 19.b LA GRILLA SIN ?profesional= — el bug del 13-oct, del lado del vecino ─
#
# 🔴 QUÉ MIDE, y no lo medía ninguno de los cuatro casos de la grilla: que un
# ADMIN que NO manda el parámetro reciba SU PROPIA agenda. `Number( null )` da
# CERO, así que antes del arreglo la respuesta venía con `"profesional": 0` —
# una agenda vacía, sin error, para un profesional que no existe.
#
# 🔑 POR QUÉ ESTE CASO SÍ SE PUEDE MEDIR Y EL PRIMER INTENTO NO: comparar la
# grilla «sin parámetro» contra la grilla «con un 0» da lo mismo en los dos
# mundos, porque las dos caen en el default. Lo que distingue es que la
# respuesta DICE de quién es la grilla, en el campo `profesional`.

echo
echo "▶ 19.b La grilla como ADMIN sin ?profesional= — tiene que decir SU id"

DIA_PROPIO=$( date -v+30d +%F 2>/dev/null || date -d "+30 days" +%F )

DE_QUIEN=$(
  curl -s \
    "$FUNCIONES/horarios-del-panel?fecha=$DIA_PROPIO&duracion=30" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE" \
  | jq -r '.profesional' 2>/dev/null
)

DE_QUIEN_CERO=$(
  curl -s \
    "$FUNCIONES/horarios-del-panel?fecha=$DIA_PROPIO&duracion=30&profesional=0" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE" \
  | jq -r '.profesional' 2>/dev/null
)

printf '   sin parámetro → profesional %s\n' "$DE_QUIEN"
printf '   con un 0      → profesional %s\n' "$DE_QUIEN_CERO"

echo
echo "   🔴 LOS DOS tienen que traer el id de la CUENTA DE SOPORTE (el que"
echo "      imprimió el caso 3), nunca un 0. Un 0 ahí es el bug del 13-oct:"
echo "      el default seguro no se aplicó y la grilla es de nadie."


#
# 🔴 EL CASO QUE FALTABA, Y NO LO ENCONTRÓ NINGUNA PRUEBA: lo encontró Juan
# usando el panel. El buscador comparaba el término contra cada columna POR
# SEPARADO, así que «rafa b» no coincidía con nadie aunque «rafa» sí.
#
# Y el síntoma era peor que un cero: la pantalla abre el alta de ficha cuando
# no hay coincidencias, así que al terminar de escribir el apellido los
# resultados desaparecían y salía el formulario para crear un paciente que ya
# existía — el agujero exacto que el buscador existe para tapar.
#
# Las ocho pruebas anteriores del buscador medían PERMISOS —quién puede
# buscar— y ninguna medía QUÉ ENCUENTRA. Son dos preguntas distintas.

echo
echo "▶ 20. El mismo paciente, buscado de tres maneras"

NOMBRE_REAL=$(
  supabase db query --linked --output csv \
    "select nombre from public.pacientes where nombre is not null and apellido is not null order by id desc limit 1;" \
    2>/dev/null | tail -1 | tr -d '\r'
)

APELLIDO_REAL=$(
  supabase db query --linked --output csv \
    "select apellido from public.pacientes where nombre is not null and apellido is not null order by id desc limit 1;" \
    2>/dev/null | tail -1 | tr -d '\r'
)

if [ -z "$NOMBRE_REAL" ] || [ -z "$APELLIDO_REAL" ]; then

  echo "   ❌ NO SE PUDO MEDIR: no hay un paciente con nombre y apellido."

else

  echo "   paciente elegido: $NOMBRE_REAL $APELLIDO_REAL"
  echo

  for Q in "$NOMBRE_REAL" "$NOMBRE_REAL $APELLIDO_REAL" "$APELLIDO_REAL $NOMBRE_REAL"; do

    RESPUESTA_BUSQUEDA=$(
      curl -s -G "$FUNCIONES/buscar-pacientes" \
        --data-urlencode "q=$Q" \
        -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
        -H "Authorization: Bearer $TOKEN_SOPORTE"
    )

    # Mismo motivo que el `if` del caso 11: contando `"id"`, un error contesta
    # CERO y se lee igual que «no encontró a nadie».
    if echo "$RESPUESTA_BUSQUEDA" | grep -q '"error"'; then
      printf '   q="%s" → ❌ EL ENDPOINT FALLÓ: %s\n' "$Q" "$RESPUESTA_BUSQUEDA"
      continue
    fi

    CUANTOS=$( echo "$RESPUESTA_BUSQUEDA" | grep -o '"id"' | wc -l | tr -d ' ' )

    printf '   q="%s" → %s resultado(s)\n' "$Q" "$CUANTOS"
  done

  echo
  echo "   🔴 LOS TRES tienen que traer al menos UNO. Un cero en el segundo o"
  echo "      el tercero es el bug del 9-oct: buscar «nombre apellido» junto"
  echo "      no encontraba a nadie, y la pantalla ofrecía crear la ficha de"
  echo "      alguien que ya estaba en la base."
fi


# ── 21 a 27. LA SOLAPA DEL PLANTEL Y LA LUPA — etapa ⑤.6, rebanada A ─────────
#
# 🔴 LO QUE ESTOS CASOS MIDEN Y NINGUNO DE LOS 20 ANTERIORES MIDE: el chequeo de
# NIVEL. Hasta acá la pregunta del panel era «¿este turno es tuyo?»
# (propiedad); estos dos endpoints preguntan «¿sos admin?». Un profesional con
# sesión válida tiene que recibir 403 AUNQUE PIDA SU PROPIA FILA.
#
# 🔴 Y EL 26 ES EL MÁS CARO DE TODA LA BATERÍA: `turnos-del-profesional` es el
# único endpoint del proyecto que devuelve `observaciones_paciente`, que puede
# traer datos de salud. Si ese caso da 200, cualquier profesional logueado lee
# el motivo de consulta de los pacientes de todos los demás.

echo
echo "▶ 21. El plantel sin token — 401"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  "$FUNCIONES/plantel-del-panel" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY"

echo
echo "▶ 22. El plantel como PACIENTE — 403"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  "$FUNCIONES/plantel-del-panel" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_PACIENTE"

echo
echo "▶ 23. El plantel como ADMIN — 200"

PLANTEL=$(
  curl -s -w '\n%{http_code}' \
    "$FUNCIONES/plantel-del-panel" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE"
)

CODIGO_PLANTEL=$( echo "$PLANTEL" | tail -1 )
CUERPO_PLANTEL=$( echo "$PLANTEL" | sed '$d' )

echo "   obtenido: $CODIGO_PLANTEL"
echo "   cuerpo:   $( echo "$CUERPO_PLANTEL" | head -c 400 )"

echo
echo "   ✅ Tienen que venir TODOS, los de baja incluidos, y cada fila con su"
echo "      turnosPendientes. Es la diferencia con profesionales-del-panel,"
echo "      que filtra activo = true."

echo
echo "▶ 24. La lupa sin ?profesional= — 400"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  "$FUNCIONES/turnos-del-profesional" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE"

echo
echo "▶ 24.b La lupa con ?profesional=0 — 400"
echo "       (los id de la base arrancan en 1: un 0 es un pedido mal"
echo "        formado, no un profesional que no está)"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  "$FUNCIONES/turnos-del-profesional?profesional=0" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE"

echo
echo "▶ 25. La lupa como ADMIN — 200, y el conteo tiene que COINCIDIR"

PRIMERO=$( echo "$CUERPO_PLANTEL" | jq -r '.plantel[0].id' 2>/dev/null )
ESPERADOS=$( echo "$CUERPO_PLANTEL" | jq -r '.plantel[0].turnosPendientes' 2>/dev/null )

if [ -z "$PRIMERO" ] || [ "$PRIMERO" = "null" ]; then
  echo "   ⚠ No se pudo leer un id del plantel: el caso 23 no devolvió filas."
else

  LUPA=$(
    curl -s -w '\n%{http_code}' \
      "$FUNCIONES/turnos-del-profesional?profesional=$PRIMERO" \
      -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
      -H "Authorization: Bearer $TOKEN_SOPORTE"
  )

  echo "   obtenido: $( echo "$LUPA" | tail -1 )"

  TRAIDOS=$( echo "$LUPA" | sed '$d' | jq -r '.turnos | length' 2>/dev/null )

  printf '   profesional %s → el plantel dice %s, la lupa trae %s\n' \
    "$PRIMERO" "$ESPERADOS" "$TRAIDOS"

  echo
  echo "   🔴 LOS DOS NÚMEROS TIENEN QUE SER IGUALES. Si no, los dos filtros se"
  echo "      desincronizaron y la lupa desmiente a la fila que se clickeó para"
  echo "      abrirla — una pantalla que se contradice sola, sin dar error."
fi


# ── 26 y 27. LOS DOS DE NIVEL, con es_admin bajado una sola vez ──────────────
#
# 🔴 SI EL SCRIPT SE CORTA ACÁ, la cuenta queda sin es_admin. El comando para
# devolverlo es el mismo que corre solo cinco líneas más abajo:
#
#   supabase db query --linked "update public.profesionales set es_admin = true
#   where email_de_acceso = '$SOPORTE_EMAIL';"

echo
echo "▶ 26 y 27. Los dos endpoints como NO-admin — los dos tienen que dar 403"

supabase db query --linked \
  "update public.profesionales set es_admin = false where email_de_acceso = '$SOPORTE_EMAIL';" \
  > /dev/null 2>&1

echo "   26. el plantel:"

curl -s -o /dev/null -w "       obtenido: %{http_code}\n" \
  "$FUNCIONES/plantel-del-panel" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE"

echo "   27. la lupa (la que trae observaciones_paciente):"

curl -s -o /dev/null -w "       obtenido: %{http_code}\n" \
  "$FUNCIONES/turnos-del-profesional?profesional=$PRIMERO" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE"

supabase db query --linked \
  "update public.profesionales set es_admin = true where email_de_acceso = '$SOPORTE_EMAIL';" \
  > /dev/null 2>&1

echo
echo "▶ es_admin restaurado — la salida va CRUDA y en csv, por el motivo del caso 6:"

supabase db query --linked --output csv \
  "select nombre, es_admin from public.profesionales where email_de_acceso = '$SOPORTE_EMAIL';" \
  2>/dev/null | tail -2

echo
echo "   ✅ es_admin tiene que decir TRUE. Si dice false, el script se cortó"
echo "      antes de restaurarlo: el comando está comentado arriba."


# ── 28 a 35. EL ALTA Y LA BAJA — etapa ⑤.6, rebanada B ───────────────────────
#
# 🔴 ESTOS DOS ENDPOINTS ESCRIBEN, así que lo que miden estos casos no es que
# anden: es que NO anden para quien no corresponde. El de alta es la puerta más
# cara de toda la fase — quien puede dar de alta puede crearse una fila con
# es_admin y repartirse permisos.
#
# ⏰ La fila que crea el caso 31 se BORRA al final de este bloque. Es la única
# de toda la batería que se limpia sola, y se puede: un profesional recién
# creado no tiene turnos, así que la foreign key `restrict` no lo retiene.

CORREO_BATERIA="bateria-$( date +%s )@ejemplo.invalido"

echo
echo "▶ 28. Alta sin token — 401"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/alta-de-profesional" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H 'Content-Type: application/json' \
  -d '{ "nombre": "x", "apellido": "x", "email": "x@x.com" }'

echo
echo "▶ 29. Alta como PACIENTE — 403"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/alta-de-profesional" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_PACIENTE" \
  -H 'Content-Type: application/json' \
  -d '{ "nombre": "x", "apellido": "x", "email": "x@x.com" }'

echo
echo "▶ 30. Alta sin el correo — 400"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/alta-de-profesional" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE" \
  -H 'Content-Type: application/json' \
  -d '{ "nombre": "Sin", "apellido": "Correo" }'

echo
echo "▶ 31. Alta como ADMIN — 201"

ALTA=$(
  curl -s -w '\n%{http_code}' \
    -X POST "$FUNCIONES/alta-de-profesional" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE" \
    -H 'Content-Type: application/json' \
    -d "{ \"nombre\": \"Batería\", \"apellido\": \"De Prueba\",
          \"email\": \"$CORREO_BATERIA\" }"
)

echo "   obtenido: $( echo "$ALTA" | tail -1 )"

NUEVO_ID=$( echo "$ALTA" | sed '$d' | jq -r '.alta.id' 2>/dev/null )

echo "   profesional creado: $NUEVO_ID"

# 🔴 EL CUERPO SE IMPRIME, y esto se arregló el 13-oct apenas se corrió la
# batería: el aviso de abajo decía «el cuerpo tiene que traer es_admin: false»
# y el cuerpo NO SE MOSTRABA. Era un chequeo que no chequeaba y no avisaba de
# que no chequeaba — el mismo modo de falla que ya mordió tres veces en el
# caso 6, con el formato de `supabase db query`.
echo "   cuerpo:   $( echo "$ALTA" | sed '$d' | head -c 200 )"

echo
echo "   ✅ El cuerpo tiene que traer \"es_admin\": false aunque no se haya"
echo "      mandado: el alta nace SIN permisos de administrador."

echo
echo "▶ 32. El MISMO correo otra vez — 409, no 500"
echo "      (choca contra el unique de la tabla: nadie se equivocó)"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/alta-de-profesional" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE" \
  -H 'Content-Type: application/json' \
  -d "{ \"nombre\": \"Otro\", \"apellido\": \"Igual\",
        \"email\": \"$CORREO_BATERIA\" }"

echo
echo "▶ 33. BAJA DE SÍ MISMO — 409   ← el caso que evita el bloqueo total"
echo "      (un admin que se apaga pierde el panel en el pedido siguiente,"
echo "       y si era el único no queda quien pueda devolvérselo)"

AUTOBAJA=$(
  curl -s -w '\n%{http_code}' \
    -X POST "$FUNCIONES/baja-de-profesional" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE" \
    -H 'Content-Type: application/json' \
    -d '{ "profesional_id": 16 }'
)

echo "   obtenido: $( echo "$AUTOBAJA" | tail -1 )"
echo "   cuerpo:   $( echo "$AUTOBAJA" | sed '$d' | head -c 200 )"

echo
echo "   🔴 TIENE QUE DAR 409. Si da 200, la cuenta de soporte quedó apagada"
echo "      y el resto de esta batería va a dar 403 de acá en adelante."

echo
echo "▶ 34. Baja del profesional de prueba, como ADMIN — 200"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/baja-de-profesional" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE" \
  -H 'Content-Type: application/json' \
  -d "{ \"profesional_id\": $NUEVO_ID }"

echo
echo "▶ 35. Baja como NO-admin — 403   ← el que justifica el chequeo de nivel"

supabase db query --linked \
  "update public.profesionales set es_admin = false where email_de_acceso = '$SOPORTE_EMAIL';" \
  > /dev/null 2>&1

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/baja-de-profesional" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE" \
  -H 'Content-Type: application/json' \
  -d "{ \"profesional_id\": $NUEVO_ID, \"activo\": true }"

echo "   35.b el alta, también como NO-admin — 403:"

curl -s -o /dev/null -w "       obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/alta-de-profesional" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE" \
  -H 'Content-Type: application/json' \
  -d '{ "nombre": "No", "apellido": "Debería", "email": "no@ejemplo.invalido" }'

supabase db query --linked \
  "update public.profesionales set es_admin = true where email_de_acceso = '$SOPORTE_EMAIL';" \
  > /dev/null 2>&1

# ── 36 a 43. LOS TRATAMIENTOS DE CADA UNO — etapa ⑤.6, rebanada C ────────────
#
# 🔴 QUÉ MIDE ESTE BLOQUE Y NO MIDE NINGÚN OTRO: el interruptor de tratamientos
# es el ÚNICO permiso del panel que rompe la simetría — un profesional no puede
# apagar NI EL SUYO PROPIO. En todo lo demás cada uno manda sobre lo suyo. El
# caso 41 es el que prueba que esa excepción está escrita en el portero y no
# sólo en la pantalla.
#
# 🔑 SE TRABAJA SOBRE EL PROFESIONAL DE PRUEBA, no sobre Cecilia, y el motivo
# es que esto ESCRIBE: apagarle un tratamiento a ella lo sacaría del sitio real
# hasta que alguien lo volviera a prender.

echo
echo "▶ 36. Sus tratamientos sin token — 401"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  "$FUNCIONES/tratamientos-del-profesional?profesional=$NUEVO_ID" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY"

echo
echo "▶ 37. Sus tratamientos como PACIENTE — 403"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  "$FUNCIONES/tratamientos-del-profesional?profesional=$NUEVO_ID" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_PACIENTE"

echo
echo "▶ 38. Sus tratamientos como ADMIN — 200, y el CATÁLOGO ENTERO"

CUALES=$(
  curl -s -w '\n%{http_code}' \
    "$FUNCIONES/tratamientos-del-profesional?profesional=$NUEVO_ID" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE"
)

echo "   obtenido: $( echo "$CUALES" | tail -1 )"

CUANTOS_HAY=$( echo "$CUALES" | sed '$d' | jq -r '.tratamientos | length' 2>/dev/null )
CUANTOS_HACE=$( echo "$CUALES" | sed '$d' | jq -r '[ .tratamientos[] | select( .loHace ) ] | length' 2>/dev/null )

printf '   catálogo: %s tratamiento(s) · los hace: %s\n' "$CUANTOS_HAY" "$CUANTOS_HACE"

echo
echo "   🔴 El catálogo tiene que venir ENTERO y «los hace» tiene que ser 0:"
echo "      un profesional recién dado de alta no tiene ninguna pareja, así"
echo "      que no aparece para reservar con nadie. Ese es el estado que esta"
echo "      pantalla existe para arreglar."

# El primer tratamiento del catálogo, para prenderlo y apagarlo.
UN_TRATAMIENTO=$( echo "$CUALES" | sed '$d' | jq -r '.tratamientos[0].id' 2>/dev/null )

echo
echo "▶ 39. Prender un tratamiento — 200, y CREA la pareja"
echo "      (no existía: prenderlo necesita un insert, no un update)"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/pareja-del-panel" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE" \
  -H 'Content-Type: application/json' \
  -d "{ \"profesional_id\": $NUEVO_ID, \"tratamiento_id\": $UN_TRATAMIENTO,
        \"activo\": true }"

echo
echo "▶ 40. Volver a pedirlo — tiene que decir que ahora lo hace"

AHORA=$(
  curl -s "$FUNCIONES/tratamientos-del-profesional?profesional=$NUEVO_ID" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE" \
  | jq -r '[ .tratamientos[] | select( .loHace ) ] | length' 2>/dev/null
)

echo "   los hace ahora: $AHORA"

echo
echo "   🔴 TIENE QUE SER 1. Si sigue en 0, el pedido contestó 200 y no"
echo "      escribió nada — el modo de falla que no se ve."

echo
echo "▶ 41. El interruptor como NO-admin — 403   ← la excepción del panel"
echo "      (es el único permiso que un profesional NO tiene ni sobre lo suyo)"

supabase db query --linked \
  "update public.profesionales set es_admin = false where email_de_acceso = '$SOPORTE_EMAIL';" \
  > /dev/null 2>&1

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/pareja-del-panel" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE" \
  -H 'Content-Type: application/json' \
  -d "{ \"profesional_id\": $NUEVO_ID, \"tratamiento_id\": $UN_TRATAMIENTO,
        \"activo\": false }"

echo "   41.b la lectura, también como NO-admin — 403:"

curl -s -o /dev/null -w "       obtenido: %{http_code}\n" \
  "$FUNCIONES/tratamientos-del-profesional?profesional=$NUEVO_ID" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE"

supabase db query --linked \
  "update public.profesionales set es_admin = true where email_de_acceso = '$SOPORTE_EMAIL';" \
  > /dev/null 2>&1

echo
echo "▶ 42. Apagarlo, ya como ADMIN — 200, y ahora SÍ es un update"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/pareja-del-panel" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE" \
  -H 'Content-Type: application/json' \
  -d "{ \"profesional_id\": $NUEVO_ID, \"tratamiento_id\": $UN_TRATAMIENTO,
        \"activo\": false }"

echo
echo "▶ 43. Sin tratamiento_id — 400"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/pareja-del-panel" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE" \
  -H 'Content-Type: application/json' \
  -d "{ \"profesional_id\": $NUEVO_ID, \"activo\": true }"


echo
echo "▶ limpieza: se borra el profesional de prueba y se restaura es_admin"

# 🔴 LAS PAREJAS SE BORRAN PRIMERO, y no es un detalle de orden: la fila de
# `profesional_tratamientos` apunta al profesional con `on delete restrict`, así
# que la base RECHAZA borrarlo mientras tenga una. Es la misma protección que
# obliga a apagar en vez de borrar en todo el proyecto, funcionando.
supabase db query --linked --output csv \
  "delete from public.profesional_tratamientos
     where profesional_id in (
       select id from public.profesionales where email like 'bateria-%' );
   delete from public.profesionales where email like 'bateria-%';
   select nombre, es_admin from public.profesionales where email_de_acceso = '$SOPORTE_EMAIL';" \
  2>/dev/null | tail -2

echo
echo "   ✅ Tiene que decir TRUE, y la fila de prueba ya no está."


# ── 44 a 51. MOVER UN TURNO DE HORA — etapa ⑤.4 ──────────────────────────────
#
# 🔴 TRES CASOS SON LOS QUE VALEN, y los otros cinco son la forma:
#   · el 44 mide `?excepto=`, que es lo que hace usable la pantalla: el turno
#     que se está moviendo NO tiene que contarse a sí mismo como ocupado.
#   · el 50 mide el 409 del constraint `turnos_sin_solapar`, que es la defensa
#     contra pisar un turno existente. Tiene que dar 409 y NO 500.
#   · el 51 es el IDOR de ESCRITURA, el mismo del caso 8 pero sobre mover: un
#     profesional que manda el id de un turno ajeno no puede cambiarle la hora.
#
# Los dos turnos de prueba se crean acá —A el que se mueve, B el obstáculo— en
# la misma fecha lejana que usa el caso 14, y al final se APAGAN, no se borran.

echo
echo "── 44 a 51 · MOVER UN TURNO ────────────────────────────────────────"

crear_turno_de_prueba() {

  curl -s \
    -X POST "$FUNCIONES/turno-del-panel" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE" \
    -H 'Content-Type: application/json' \
    -d "{ \"paciente_id\": ${PACIENTE_ID:-1},
          \"tratamiento_id\": ${TRATAMIENTO:-1},
          \"obra_social_id\": ${PARTICULAR:-1},
          \"duracion_min\": 30,
          \"inicio\": \"${LEJOS}T$1:00-03:00\" }" \
    | grep -oE '"id":[0-9]+' | head -1 | grep -oE '[0-9]+'
}

# Sin `profesional_id`: así los dos turnos quedan a nombre de la cuenta de
# soporte, que es la que después los mueve. Un turno ajeno daría 403 y el caso
# 49 mediría la propiedad en vez del movimiento.
MOVER_A=$( crear_turno_de_prueba '14:00' )

MOVER_B=$( crear_turno_de_prueba '16:00' )

echo "   turno A (el que se mueve): ${MOVER_A:-ninguno}"
echo "   turno B (el obstáculo):    ${MOVER_B:-ninguno}"

if [ -z "${MOVER_A:-}" ] || [ -z "${MOVER_B:-}" ]; then
  echo "   ❌ NO SE PUDIERON CREAR LOS DOS TURNOS DE PRUEBA, así que los ocho"
  echo "      casos de abajo no miden nada. Una prueba que no corre se lee"
  echo "      como verde: esto es un ROJO."
fi

# ── 44. La grilla con y sin `?excepto=` ──────────────────────────────────────
#
# 🔑 QUÉ MIDE, Y NO LO MEDÍA NINGUNO DE LOS CINCO CASOS DE LA GRILLA: que el
# turno que se está moviendo deje de contar como ocupado cuando se lo nombra.
# Sin esto, la pantalla de mover no puede dejar un turno a la misma hora con
# otra duración — el turno se tapa a sí mismo.
#
# Se lee por el CUERPO y no por el código: los dos pedidos dan 200. Lo que
# tiene que cambiar es CUÁNTOS bloques salen libres.
#
# 🔴 POR QUÉ ESTE CASO NO USA LOS TURNOS A Y B, Y ES EL MISMO ERROR QUE YA
# DEJÓ AL CASO 19 EN «0 de 0» la primera vez: la CUENTA DE SOPORTE NO TIENE
# AGENDA en `horarios_base`, así que cualquier día suyo devuelve cero bloques y
# los dos conteos salen iguales — en 0. Eso no es rojo ni verde: es no medir.
# Y la fecha lejana que usan los otros casos tampoco sirve, porque está más
# allá de los días que la búsqueda del 19 recorre.
#
# ✅ LO QUE SE HACE EN SU LUGAR: se reusa `$DIA_GRILLA` —el día con agenda que
# el caso 19 ya encontró— sobre la agenda de CECILIA (`?profesional=1`, que un
# admin puede pedir), se carga un turno de prueba en el primer bloque LIBRE de
# ese día, y se cuenta. El turno se apaga enseguida.

echo
echo "▶ 44. La grilla de un día CON AGENDA, sin y con ?excepto= — 200 las dos"

if [ -z "${DIA_GRILLA:-}" ]; then

  echo "   ❌ NO SE PUDO MEDIR: el caso 19 no encontró ningún día con agenda,"
  echo "      así que no hay dónde poner el turno de prueba."

else

  GRILLA_ANTES=$(
    curl -s "$FUNCIONES/horarios-del-panel?fecha=$DIA_GRILLA&duracion=30&profesional=1" \
      -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
      -H "Authorization: Bearer $TOKEN_SOPORTE"
  )

  # El primer bloque libre, tal cual lo manda el portero —con su desfase—. Se
  # saca del JSON y no se arma a mano: una hora inventada puede caer fuera de
  # la agenda y el turno se crearía donde la grilla no lo muestra.
  HORA_LIBRE=$(
    echo "$GRILLA_ANTES" \
      | grep -o '"inicio":"[^"]*","estado":"libre"' \
      | head -1 \
      | sed 's/"inicio":"//; s/","estado":"libre"//'
  )

  echo "   día con agenda: $DIA_GRILLA · primer bloque libre: ${HORA_LIBRE:-ninguno}"

  if [ -z "$HORA_LIBRE" ]; then

    echo "   ❌ NO SE PUDO MEDIR: ese día no tiene ni un bloque libre."

  else

    # A nombre de CECILIA (profesional 1), que es de quien es la agenda que se
    # está mirando. El paciente es el de la batería, que no tiene correo: así
    # este turno no le manda un aviso a nadie.
    GRILLA_TURNO=$(
      curl -s \
        -X POST "$FUNCIONES/turno-del-panel" \
        -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
        -H "Authorization: Bearer $TOKEN_SOPORTE" \
        -H 'Content-Type: application/json' \
        -d "{ \"paciente_id\": ${PACIENTE_ID:-1},
              \"profesional_id\": 1,
              \"tratamiento_id\": ${TRATAMIENTO:-1},
              \"obra_social_id\": ${PARTICULAR:-1},
              \"duracion_min\": 30,
              \"inicio\": \"$HORA_LIBRE\" }" \
        | grep -oE '"id":[0-9]+' | head -1 | grep -oE '[0-9]+'
    )

    echo "   turno de prueba cargado en ese bloque: ${GRILLA_TURNO:-ninguno}"

    if [ -z "${GRILLA_TURNO:-}" ]; then

      echo "   ❌ NO SE PUDO MEDIR: el turno de prueba no se creó."

    else

      LIBRES_SIN=$(
        curl -s "$FUNCIONES/horarios-del-panel?fecha=$DIA_GRILLA&duracion=30&profesional=1" \
          -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
          -H "Authorization: Bearer $TOKEN_SOPORTE" \
          | grep -o '"estado":"libre"' | wc -l | tr -d ' '
      )

      LIBRES_CON=$(
        curl -s "$FUNCIONES/horarios-del-panel?fecha=$DIA_GRILLA&duracion=30&profesional=1&excepto=$GRILLA_TURNO" \
          -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
          -H "Authorization: Bearer $TOKEN_SOPORTE" \
          | grep -o '"estado":"libre"' | wc -l | tr -d ' '
      )

      echo
      echo "   bloques libres SIN excepto: $LIBRES_SIN"
      echo "   bloques libres CON excepto: $LIBRES_CON"
      echo
      echo "   🔴 CON tiene que ser MAYOR que SIN — y eso es el turno dejando"
      echo "      de taparse a sí mismo. Si son IGUALES, el parámetro no se"
      echo "      obedece y la pantalla de mover no sirve."
      echo "   ⚠ Si los dos dan 0, el caso no midió: avisá antes de leerlo"
      echo "      como verde."

      supabase db query --linked \
        "update public.turnos set activo = false where id = $GRILLA_TURNO;" \
        > /dev/null 2>&1

      echo
      echo "   turno de prueba $GRILLA_TURNO apagado (no borrado)"
    fi
  fi
fi

# ── 45 a 48. La forma ────────────────────────────────────────────────────────

echo
echo "▶ 45. Mover sin token — 401   (lo contesta la plataforma)"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/mover-turno" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H 'Content-Type: application/json' \
  -d '{ "turno_id": 1, "inicio": "2027-01-01T10:00:00-03:00", "duracion_min": 30 }'

echo
echo "▶ 46. Mover como PACIENTE — 403   ← la cerradura del panel"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/mover-turno" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_PACIENTE" \
  -H 'Content-Type: application/json' \
  -d '{ "turno_id": 1, "inicio": "2027-01-01T10:00:00-03:00", "duracion_min": 30 }'

echo
echo "▶ 47. Sin turno_id — 400"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/mover-turno" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE" \
  -H 'Content-Type: application/json' \
  -d '{ "inicio": "2027-01-01T10:00:00-03:00", "duracion_min": 30 }'

echo
echo "▶ 48. Duración fuera de los bloques de 30 — 400"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/mover-turno" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE" \
  -H 'Content-Type: application/json' \
  -d "{ \"turno_id\": ${MOVER_A:-1}, \"inicio\": \"${LEJOS}T15:00:00-03:00\", \"duracion_min\": 45 }"

# ── 49. El movimiento que SÍ entra ───────────────────────────────────────────

echo
echo "▶ 49. Mover el turno A de las 14:00 a las 15:00 — 200"

if [ -n "${MOVER_A:-}" ]; then

  curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
    -X POST "$FUNCIONES/mover-turno" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE" \
    -H 'Content-Type: application/json' \
    -d "{ \"turno_id\": $MOVER_A, \"inicio\": \"${LEJOS}T15:00:00-03:00\", \"duracion_min\": 60 }"

  # 🔑 SE PREGUNTA A LA BASE Y NO SE LE CREE A LA RESPUESTA. Un 200 dice que el
  # portero contestó bien, no que la fila quedó cambiada.
  echo
  echo "▶ ¿qué hora tiene ahora el turno A? (tiene que decir 15:00 y 60)"

  supabase db query --linked --output csv \
    "select to_char( inicio at time zone 'America/Argentina/Cordoba', 'HH24:MI' ) as hora,
            duracion_min
       from public.turnos where id = $MOVER_A;" \
    2>/dev/null | tail -2
fi

# ── 50. EL 409 DEL CONSTRAINT ────────────────────────────────────────────────
#
# 🔴 LO QUE SE MIDE ACÁ NO ES QUE FALLE: es que falle BIEN. 409 significa «ese
# horario está tomado» y es información para quien atiende; un 500 significaría
# que el error se escapó sin que nadie lo tradujera, y la pantalla no tendría
# qué decirle.

echo
echo "▶ 50. Mover el turno A ENCIMA del turno B — 409, no 500   ← el que vale"

if [ -n "${MOVER_A:-}" ] && [ -n "${MOVER_B:-}" ]; then

  CHOQUE=$(
    curl -s -w '\n%{http_code}' \
      -X POST "$FUNCIONES/mover-turno" \
      -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
      -H "Authorization: Bearer $TOKEN_SOPORTE" \
      -H 'Content-Type: application/json' \
      -d "{ \"turno_id\": $MOVER_A, \"inicio\": \"${LEJOS}T16:00:00-03:00\", \"duracion_min\": 30 }"
  )

  echo "   obtenido: $( echo "$CHOQUE" | tail -1 )"
  echo "   cuerpo:   $( echo "$CHOQUE" | sed '$d' | head -c 200 )"
  echo
  echo "   🔴 Tiene que decir 409 Y traer \"codigo\": \"HORARIO_OCUPADO\". Ese"
  echo "      código es lo que la pantalla usa para decirlo con sus palabras en"
  echo "      vez de mostrar un error genérico."

  echo
  echo "▶ ¿se quedó el turno A donde estaba? (tiene que decir 15:00)"

  supabase db query --linked --output csv \
    "select to_char( inicio at time zone 'America/Argentina/Cordoba', 'HH24:MI' ) as hora
       from public.turnos where id = $MOVER_A;" \
    2>/dev/null | tail -2
fi

# ── 51. EL IDOR DE ESCRITURA ─────────────────────────────────────────────────

echo
echo "▶ 51. IDOR de ESCRITURA: un NO-admin moviendo un turno ajeno — 403"
echo "      (se le baja es_admin a la cuenta de soporte y se le devuelve al final)"

supabase db query --linked \
  "update public.profesionales set es_admin = false where email_de_acceso = '$SOPORTE_EMAIL';" \
  > /dev/null 2>&1

# Un turno activo que NO sea de la cuenta de soporte ni los dos de esta prueba.
SALIDA_AJENO_MOVER=$(
  supabase db query --linked --output csv \
    "select id from public.turnos
       where activo = true
         and profesional_id <> ${SOPORTE_ID:-0}
       order by inicio desc limit 1;" \
    2>/dev/null
)

AJENO_MOVER=$( echo "$SALIDA_AJENO_MOVER" | grep -oE '^[0-9]+$' | tail -1 )

echo "   turno ajeno elegido: ${AJENO_MOVER:-ninguno}"

if [ -n "$AJENO_MOVER" ]; then

  HORA_ANTES=$(
    supabase db query --linked --output csv \
      "select to_char( inicio at time zone 'America/Argentina/Cordoba', 'HH24:MI' )
         from public.turnos where id = $AJENO_MOVER;" \
      2>/dev/null | tail -1
  )

  curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
    -X POST "$FUNCIONES/mover-turno" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE" \
    -H 'Content-Type: application/json' \
    -d "{ \"turno_id\": $AJENO_MOVER, \"inicio\": \"${LEJOS}T19:00:00-03:00\", \"duracion_min\": 30 }"

  echo
  echo "   🔴 TIENE QUE DAR 403. Si da 200, el turno de otro profesional se"
  echo "      movió y a su paciente le llegó un correo diciendo que su turno"
  echo "      cambió de hora: eso es el IDOR de escritura."

  echo
  echo "▶ ¿quedó el turno ajeno en su hora? (antes decía $HORA_ANTES)"

  supabase db query --linked --output csv \
    "select to_char( inicio at time zone 'America/Argentina/Cordoba', 'HH24:MI' ) as hora
       from public.turnos where id = $AJENO_MOVER;" \
    2>/dev/null | tail -2

else
  echo "   ❌ NO SE PUDO MEDIR EL CASO MÁS IMPORTANTE DE ESTE BLOQUE: no hay"
  echo "      ningún turno activo de otro profesional."
fi

supabase db query --linked \
  "update public.profesionales set es_admin = true where email_de_acceso = '$SOPORTE_EMAIL';" \
  > /dev/null 2>&1



# ── 52 a 64. LAS AUSENCIAS — etapa ⑤.5, rebanada A ───────────────────────────
#
# 🔴 QUÉ MIDEN ESTOS CASOS Y NINGUNO DE LOS 51 ANTERIORES MIDE: la tabla
# `excepciones` guarda DOS cosas con la misma forma —la ausencia de una persona,
# que es suya, y el cierre de toda la clínica, que no es de nadie— y por eso es
# la primera puerta del panel donde conviven el chequeo de PROPIEDAD y el de
# NIVEL. El caso 62 es el que mide esa mezcla.
#
# 🔴 Y EL 59 ES EL QUE JUSTIFICA LA ETAPA, y no se lee por el código sino por el
# CUERPO: cargar una ausencia sobre un día que ya tiene turnos tiene que
# DEVOLVER esos turnos. Si vuelve lista vacía, Cecilia se va de vacaciones sin
# saber a quién llamar, que es exactamente el agujero que la etapa viene a
# tapar.

echo
echo "▶ 52. Las ausencias sin token — 401"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  "$FUNCIONES/ausencias-del-panel" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY"

echo
echo "▶ 53. Las ausencias como PACIENTE — 403"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  "$FUNCIONES/ausencias-del-panel" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_PACIENTE"

echo
echo "▶ 54. Las ausencias como ADMIN — 200"

AUSENCIAS=$(
  curl -s -w '\n%{http_code}' \
    "$FUNCIONES/ausencias-del-panel" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE"
)

echo "   obtenido: $( echo "$AUSENCIAS" | tail -1 )"
echo "   cuerpo:   $( echo "$AUSENCIAS" | sed '$d' | head -c 400 )"

echo
echo "   ✅ semanasDelMes tiene que traer CINCO entradas, cada una con las dos"
echo "      próximas fechas que tapa. Si viene vacía, la pantalla no puede"
echo "      mostrar qué significa «la tercera semana»."
echo
echo "   ⚠ Y 'ausencias' VIENE VACÍA, que acá es lo correcto: la recurrente de"
echo "      la tercera semana es del profesional 1 y esta cuenta es la 16. Lo"
echo "      que se pide sin parámetro son LAS PROPIAS más las de la clínica."

echo
echo "▶ 54.b Las de OTRO profesional, como ADMIN — 200 y ahí SÍ aparece"

AJENAS=$(
  curl -s -w '\n%{http_code}' \
    "$FUNCIONES/ausencias-del-panel?profesional=1" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE"
)

echo "   obtenido: $( echo "$AJENAS" | tail -1 )"
echo "   recurrentes que trae: $( echo "$AJENAS" | sed '$d' | jq -r '[ .ausencias[] | select( .tipo == "recurrente" ) ] | length' 2>/dev/null )"

echo
echo "   🔴 TIENE QUE TRAER AL MENOS UNA: es la tercera semana de Cecilia, la"
echo "      única fila que la tabla tenía antes de esta etapa. Un 0 acá"
echo "      significa que el ?profesional= de un admin no se obedece, y"
echo "      entonces Cecilia no puede ver ni tocar la agenda de nadie."

echo
echo "▶ 55. Cargar una ausencia sin token — 401"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/cargar-ausencia" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "descripcion": "x", "tipo": "unica", "alcance": "propio", "fecha_desde": "2027-01-11" }'

echo
echo "▶ 56. Cargar una ausencia como PACIENTE — 403"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/cargar-ausencia" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_PACIENTE" \
  -H "Content-Type: application/json" \
  -d '{ "descripcion": "x", "tipo": "unica", "alcance": "propio", "fecha_desde": "2027-01-11" }'

echo
echo "▶ 57. Sin descripción — 400"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/cargar-ausencia" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE" \
  -H "Content-Type: application/json" \
  -d '{ "descripcion": "   ", "tipo": "unica", "alcance": "propio", "fecha_desde": "2027-01-11" }'

echo "   ✅ Tres espacios, no vacío: es el caso que not null NO cubre y que"
echo "      cierra el check excepciones_descripcion_con_texto."

echo
echo "▶ 58. Fechas al revés — 400"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/cargar-ausencia" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE" \
  -H "Content-Type: application/json" \
  -d '{ "descripcion": "Vacaciones al reves", "tipo": "unica", "alcance": "propio", "fecha_desde": "2027-01-30", "fecha_hasta": "2027-01-20" }'

echo "   ✅ Dos dígitos invertidos al tipear. Sin esta regla la fila entra y no"
echo "      tapa NI UN DÍA, sin error y sin aviso."


# ── 59. EL CASO QUE JUSTIFICA LA ETAPA ───────────────────────────────────────
#
# Se carga la ausencia SOBRE EL DÍA DE UN TURNO QUE YA EXISTE, y lo que se mide
# es el cuerpo: tiene que devolver ese turno con el teléfono del paciente.

DIA_CON_TURNO=$(
  supabase db query --linked --output csv \
    "select to_char( t.inicio at time zone 'America/Argentina/Cordoba', 'YYYY-MM-DD' ) as dia
       from public.turnos t
      where t.activo = true
        and t.inicio >= now()
      order by t.inicio
      limit 1;" \
    2>/dev/null | tail -1 | tr -d '"\r'
)

echo
echo "▶ 59. Una ausencia SOBRE un día con turnos — 201 y la lista de a quién llamar"

if [ -n "$DIA_CON_TURNO" ] && [ "$DIA_CON_TURNO" != "dia" ]; then

  echo "   (el día elegido, que tiene al menos un turno activo: $DIA_CON_TURNO)"

  CARGADA=$(
    curl -s -w '\n%{http_code}' \
      -X POST "$FUNCIONES/cargar-ausencia" \
      -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
      -H "Authorization: Bearer $TOKEN_SOPORTE" \
      -H "Content-Type: application/json" \
      -d "{ \"descripcion\": \"PRUEBA de la bateria - se borra al final\", \"tipo\": \"unica\", \"alcance\": \"clinica\", \"fecha_desde\": \"$DIA_CON_TURNO\" }"
  )

  echo "   obtenido: $( echo "$CARGADA" | tail -1 )"
  echo "   cuerpo:   $( echo "$CARGADA" | sed '$d' | head -c 500 )"

  AUSENCIA_DE_PRUEBA=$( echo "$CARGADA" | sed '$d' | jq -r '.ausencia.id' 2>/dev/null )

  CUANTOS_TAPADOS=$( echo "$CARGADA" | sed '$d' | jq -r '.turnosTapados | length' 2>/dev/null )

  echo
  echo "   🔴 turnosTapados tiene que traer AL MENOS UNO (trajo: ${CUANTOS_TAPADOS:-?})."
  echo "      Un 0 acá es el agujero que esta etapa viene a tapar: la ausencia"
  echo "      se guardó y nadie sabe a quién hay que llamar."

else
  echo "   ❌ NO SE PUDO MEDIR: no hay ningún turno activo a futuro en la base."
fi


# ── 60 y 61. PRENDER Y APAGAR ────────────────────────────────────────────────

echo
echo "▶ 60. Apagar la ausencia recién creada — 200, y la lista va VACÍA"

if [ -n "${AUSENCIA_DE_PRUEBA:-}" ] && [ "$AUSENCIA_DE_PRUEBA" != "null" ]; then

  APAGADA=$(
    curl -s -w '\n%{http_code}' \
      -X POST "$FUNCIONES/estado-de-ausencia" \
      -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
      -H "Authorization: Bearer $TOKEN_SOPORTE" \
      -H "Content-Type: application/json" \
      -d "{ \"id\": $AUSENCIA_DE_PRUEBA, \"activa\": false }"
  )

  echo "   obtenido: $( echo "$APAGADA" | tail -1 )"
  echo "   cuerpo:   $( echo "$APAGADA" | sed '$d' | head -c 200 )"

  echo "   ✅ Apagar DESTAPA, así que no hay a quién avisar: turnosTapados va []."

  echo
  echo "▶ 61. Volver a prenderla — 200, y los turnos tapados VUELVEN"

  PRENDIDA=$(
    curl -s -w '\n%{http_code}' \
      -X POST "$FUNCIONES/estado-de-ausencia" \
      -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
      -H "Authorization: Bearer $TOKEN_SOPORTE" \
      -H "Content-Type: application/json" \
      -d "{ \"id\": $AUSENCIA_DE_PRUEBA, \"activa\": true }"
  )

  echo "   obtenido: $( echo "$PRENDIDA" | tail -1 )"
  echo "   tapados:  $( echo "$PRENDIDA" | sed '$d' | jq -r '.turnosTapados | length' 2>/dev/null )"

  echo "   🔴 Este es el caso que la primera versión del plan no tenía: sin un"
  echo "      endpoint que PRENDA, una ausencia apagada por error sólo se"
  echo "      recupera desde el Table Editor."

else
  echo "   ❌ NO SE PUDO MEDIR: el caso 59 no devolvió el id de la ausencia."
fi

echo
echo "▶ 62. Un id que no existe — 403 (no 404)"

curl -s -o /dev/null -w "   obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/estado-de-ausencia" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE" \
  -H "Content-Type: application/json" \
  -d '{ "id": 999999, "activa": false }'

echo "   ✅ 403 y no 404 a propósito: distinguir «no existe» de «no es tuya»"
echo "      le dice a quien prueba ids al azar cuáles existen."


# ── 63 y 64. EL CHEQUEO DE NIVEL — los dos casos más caros del bloque ────────

echo
echo "▶ 63 y 64. Como NO-ADMIN — los dos tienen que dar 403"
echo "     (se le baja es_admin a la cuenta de soporte y se le devuelve al final)"

supabase db query --linked \
  "update public.profesionales set es_admin = false where email_de_acceso = '$SOPORTE_EMAIL';" \
  > /dev/null 2>&1

echo
echo "   63. cargar un cierre de CLÍNICA siendo un profesional cualquiera:"

curl -s -o /dev/null -w "       obtenido: %{http_code}\n" \
  -X POST "$FUNCIONES/cargar-ausencia" \
  -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
  -H "Authorization: Bearer $TOKEN_SOPORTE" \
  -H "Content-Type: application/json" \
  -d '{ "descripcion": "Cierro el consultorio", "tipo": "unica", "alcance": "clinica", "fecha_desde": "2027-01-11" }'

echo
echo "       🔴 ÉSTE ES EL HUECO QUE LA AUDITORÍA DEL PLAN DE LA FASE HABÍA"
echo "          MARCADO: una fila sin profesional_id tapa a TODO el plantel. Si"
echo "          da 201, cualquier profesional logueado cierra la clínica."

echo
echo "   64. apagar el cierre de clínica que cargó la admin:"

if [ -n "${AUSENCIA_DE_PRUEBA:-}" ] && [ "$AUSENCIA_DE_PRUEBA" != "null" ]; then

  curl -s -o /dev/null -w "       obtenido: %{http_code}\n" \
    -X POST "$FUNCIONES/estado-de-ausencia" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Authorization: Bearer $TOKEN_SOPORTE" \
    -H "Content-Type: application/json" \
    -d "{ \"id\": $AUSENCIA_DE_PRUEBA, \"activa\": false }"

  echo
  echo "       🔴 Y ÉSTE ES EL OTRO LADO DE LA MISMA PUERTA: destapar un feriado"
  echo "          también es de nivel. Si da 200, un profesional vuelve a abrir"
  echo "          un día que la clínica cerró."

else
  echo "       ❌ no se pudo medir: no hay ausencia de prueba."
fi

supabase db query --linked \
  "update public.profesionales set es_admin = true where email_de_acceso = '$SOPORTE_EMAIL';" \
  > /dev/null 2>&1

# La ausencia de prueba SE BORRA, y acá sí se puede: nada la apunta con una
# foreign key y es una fila que inventó la batería, no un dato del consultorio.
# Es el mismo criterio que el profesional de prueba del caso 31.
if [ -n "${AUSENCIA_DE_PRUEBA:-}" ] && [ "$AUSENCIA_DE_PRUEBA" != "null" ]; then

  supabase db query --linked \
    "delete from public.excepciones where id = $AUSENCIA_DE_PRUEBA;" \
    > /dev/null 2>&1

  echo
  echo "   ausencia de prueba $AUSENCIA_DE_PRUEBA borrada"
fi



# ── 65 y 66. EL MOTIVO DE UN DÍA CERRADO — etapa ⑤.5, pedido de Juan ─────────
#
# 🔴 QUÉ MIDEN, Y SON DOS CARAS DE LA MISMA DECISIÓN. Un día tapado por una
# ausencia devuelve CERO BLOQUES, igual que un domingo, así que de la lista
# vacía no se puede deducir por qué: quien carga un turno a mano necesita saber
# si no se atiende, si está todo tomado o si la profesional está de vacaciones.
#
# 🔒 Y EL MOTIVO ES SÓLO DEL LADO DEL PANEL. «Vacaciones de verano» es
# información interna del consultorio; el paciente ve el día cerrado y nada
# más. El caso 66 es el que lo mide, y por eso pega contra el OTRO endpoint con
# el token del PACIENTE.

echo
echo "▶ 65 y 66. Un día tapado por una ausencia, visto por los dos canales"

# El día se saca de la base y no se escribe a mano: una fecha fija vence y el
# caso pasa a medir nada sin avisar.
DIA_TAPADO=$(
  supabase db query --linked --output csv \
    "select fecha_desde::text as dia
       from public.excepciones
      where activa = true
        and tipo = 'unica'
        and fecha_desde is not null
        and fecha_desde >= current_date
      order by fecha_desde
      limit 1;" \
    2>/dev/null | tail -1 | tr -d '"\r'
)

if [ -n "$DIA_TAPADO" ] && [ "$DIA_TAPADO" != "dia" ]; then

  echo "   (el día tapado que había cargado: $DIA_TAPADO)"

  echo
  echo "   65. el PANEL — tiene que traer tapado_por con su descripción:"

  PANEL_TAPADO=$(
    curl -s \
      "$FUNCIONES/horarios-del-panel?fecha=$DIA_TAPADO&duracion=30" \
      -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
      -H "Authorization: Bearer $TOKEN_SOPORTE"
  )

  echo "       $( echo "$PANEL_TAPADO" | head -c 300 )"

  echo
  echo "       🔴 bloques tiene que venir VACÍO y tapado_por CON la descripción."
  echo "          Sin ese campo, la pantalla dice «ese día no se atiende» y"
  echo "          quien atiende el teléfono no sabe qué ofrecerle a la paciente."

  echo
  echo "   66. el PACIENTE, el mismo día — NO puede traer tapado_por:"

  PACIENTE_TAPADO=$(
    curl -s \
      "$FUNCIONES/horarios-disponibles?profesional=1&tratamiento=1&desde=$DIA_TAPADO&hasta=$DIA_TAPADO" \
      -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
      -H "Authorization: Bearer $TOKEN_PACIENTE"
  )

  echo "       $( echo "$PACIENTE_TAPADO" | head -c 300 )"

  if echo "$PACIENTE_TAPADO" | grep -q "tapado_por\|tapadoPor\|descripcion"; then
    echo
    echo "       🔴 PARÁ: el motivo de la ausencia viajó al canal del PACIENTE."
    echo "          Es information disclosure (divulgación de información): el"
    echo "          nombre de la ausencia es interno del consultorio."
  else
    echo
    echo "       ✅ El motivo NO viajó, que es lo que tiene que pasar. Y no es"
    echo "          que se filtre al salir: el canal del paciente no manda"
    echo "          conMotivo, así que el campo ni se calcula."
  fi

else
  echo "   ❌ NO SE PUDO MEDIR: no hay ninguna ausencia de fecha activa a futuro."
fi


# Los dos turnos de prueba se APAGAN, no se borran — la regla del proyecto. Y
# con `aviso_estado` vacío, así que la repesca no le manda ninguna cancelación
# a nadie.
for TURNO_DE_PRUEBA in "${MOVER_A:-}" "${MOVER_B:-}"; do

  if [ -n "$TURNO_DE_PRUEBA" ]; then

    supabase db query --linked \
      "update public.turnos set activo = false where id = $TURNO_DE_PRUEBA;" \
      > /dev/null 2>&1

    echo
    echo "   turno de prueba $TURNO_DE_PRUEBA apagado (no borrado)"
  fi
done


# ── Qué mirar ────────────────────────────────────────────────────────────────

echo
echo "✅ EN VERDE ES: 401 · 403 · 200 · 200 · 400 · 403 · 403 · 401 · 403 · 400 · 201 · 201 · 400 ·"
echo "   401 · 403 · 400 · 401 · 403 · 200 · 400 · 400 · 200 · 403 · 403 ·"
echo "   401 · 403 · 400 · 201 · 409 · 409 · 200 · 403 · 403 ·"
echo "   401 · 403 · 200 · 200 · 403 · 403 · 200 · 400 ·"
echo "   401 · 403 · 400 · 400 · 200 · 409 · 403 ·"
echo "   401 · 403 · 200 · 401 · 403 · 400 · 400 · 201 · 200 · 200 · 403 · 403 · 403,"
echo "   en ese orden."
echo "   Y SIETE casos se leen por el CUERPO, no por el código: el 11 (lista vacía),"
echo "   el 14 (el profesional de la respuesta), el 19 (dos conteos distintos),"
echo "   el 19.b (la grilla tiene que decir el id del que pide, nunca 0),"
echo "   el 20 (los tres tienen que encontrar a alguien) y el 25 (los dos conteos"
echo "   IGUALES: el del plantel y el de la lupa) y el 44 (más bloques libres CON"
echo "   ?excepto= que sin él: si son iguales, el parámetro no se obedece)."
echo "   Y TRES casos más de la ⑤.5 se leen por el CUERPO: el 54 (semanasDelMes"
echo "   con sus cinco entradas), el 54.b (al menos UNA recurrente con"
echo "   ?profesional=1), el 59 (turnosTapados con AL MENOS UNO) y el 61"
echo "   (al volver a prender, los tapados VUELVEN)."
echo "   Y los DOS últimos también: el 65 (tapado_por con su descripción en el"
echo "   panel) y el 66 (el mismo día, por el canal del paciente, SIN motivo)."
echo
echo "   Y el cuerpo del caso 3 tiene que traer \"esAdmin\": true. Si trae"
echo "   false, la fila existe pero el update del es_admin no entró: la puerta"
echo "   abre y los permisos quedaron cortos. No falla, contesta mal."
echo
echo "🔴 SI EL CASO 2 DA 200, PARÁ TODO: significa que un paciente cualquiera"
echo "   entra al panel. Es A01 (Broken Access Control) y no se sigue"
echo "   construyendo nada arriba de eso."
echo
echo "⚠ Si el 3 da 403, mirá primero el .env y la fila de la base ANTES de"
echo "  tocar quien-pide.ts: el modo de falla más probable es que el correo de"
echo "  SOPORTE_EMAIL no coincida con el email_de_acceso cargado."
