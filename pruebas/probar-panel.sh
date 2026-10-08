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
# falla más caro que hay. Se deja la salida cruda: dos renglones de más valen
# menos que un verde falso.
supabase db query --linked \
  "select nombre, es_admin from public.profesionales where email_de_acceso = '$SOPORTE_EMAIL';" \
  2>&1 | grep -iv "initialising\|boundary\|untrusted data"

echo
echo "   ✅ es_admin tiene que decir TRUE. Si dice false, el script se cortó"
echo "      antes de restaurarlo: el comando para arreglarlo está comentado"
echo "      arriba, en el bloque del caso 6."


# ── Qué mirar ────────────────────────────────────────────────────────────────

echo
echo "✅ EN VERDE ES: 401 · 403 · 200 · 200 · 400, en ese orden."
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
