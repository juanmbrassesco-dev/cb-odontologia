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


# ── Qué mirar ────────────────────────────────────────────────────────────────

echo
echo "✅ EN VERDE ES: 401 · 403 · 200 · 200 · 400 · 403 · 403 · 401 · 403 · 400 · 201 · 201 · 400 ·"
echo "   401 · 403 · 400, en ese orden."
echo "   Y CUATRO casos se leen por el CUERPO, no por el código: el 11 (lista vacía),"
echo "   el 14 (el profesional de la respuesta), el 19 (dos conteos distintos) y"
echo "   el 20 (los tres tienen que encontrar a alguien)."
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
