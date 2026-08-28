#!/bin/bash
#
# LA BATERÍA DEL LÍMITE DE TURNOS (fase 4, B2)
#
# Verifica lo único que promete el trigger `turnos_limite_por_paciente`: que un
# paciente no puede tener más de DOS turnos web abiertos con el mismo profesional,
# y que los turnos que carga el consultorio NO cuentan para ese tope.
#
# 🔴 EL CASO 4 ES EL QUE MÁS IMPORTA Y ES EL MENOS OBVIO. Los tres primeros
# prueban que el límite existe; el cuarto prueba que NO se pasó de la raya. Un
# trigger que cuente también los turnos manuales dejaría sin poder reservar por la
# web a cualquier paciente de tratamiento largo —el que tiene controles cargados a
# mano—, y eso no fallaría con error: simplemente no podría sacar turno nunca.
#
# QUÉ NECESITA:
#   - el `.env` en la raíz del repo (claves y usuario de prueba)
#   - `jq` y la CLI de Supabase con el proyecto enlazado
#
# CÓMO SE CORRE, parado en la raíz del repo:
#
#   bash pruebas/probar-limite.sh
#
# DEJA RASTRO: turnos y un paciente de prueba. El comando para borrarlos se
# imprime al final; no se ejecuta solo.

set -u

set -a
source .env
set +a

FUNCIONES="$SUPABASE_URL/functions/v1"

CONSULTA=1
PROFESIONAL=1

consultar () {
  supabase db query --linked --output-format json --agent no "$1" \
  | jq 'if type == "array" then . else .rows end'
}

# $1 = qué se prueba · $2 = qué tiene que dar · $3 = el cuerpo del pedido
probar () {

  echo "───────────────────────────────────────────────────────────────"
  echo "▶ $1"
  echo "  esperado: $2"

  RESPUESTA=$(
    curl -s -w '\n%{http_code}' -X POST "$FUNCIONES/reservar" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "$3"
  )

  echo "  obtenido: $( echo "$RESPUESTA" | tail -1 )   $( echo "$RESPUESTA" | sed '$d' )"
  echo
}


# ── El token de la sesión de prueba ──────────────────────────────────────────

TOKEN=$(
  curl -s "$SUPABASE_URL/auth/v1/token?grant_type=password" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H "Content-Type: application/json" \
    -d "{ \"email\": \"$PRUEBA_EMAIL\", \"password\": \"$PRUEBA_PASSWORD\" }" \
  | jq -r '.access_token'
)

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ No se pudo obtener el token. Revisá PRUEBA_EMAIL / PRUEBA_PASSWORD en el .env"
  exit 1
fi

echo "✅ Token obtenido"


# ── El escenario: tres huecos libres, sin escribir una sola fecha a mano ─────

HOY=$( date +%F )
HASTA=$( date -u -v+40d '+%F' )

GRILLA=$(
  curl -s "$FUNCIONES/horarios-disponibles?profesional=$PROFESIONAL&tratamiento=$CONSULTA&desde=$HOY&hasta=$HASTA" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY"
)

LIBRES=$( echo "$GRILLA" | jq -r '[ .dias[].bloques[] | select( .estado == "libre" ) ][0:3] | .[].inicio' )

HORA_1=$( echo "$LIBRES" | sed -n 1p )
HORA_2=$( echo "$LIBRES" | sed -n 2p )
HORA_3=$( echo "$LIBRES" | sed -n 3p )

if [ -z "$HORA_3" ]; then
  echo "❌ La grilla no devolvió tres huecos libres. Sin escenario no hay prueba."
  exit 1
fi

echo "✅ Escenario armado: $HORA_1 · $HORA_2 · $HORA_3"
echo


# ── Los tres turnos web ──────────────────────────────────────────────────────

probar "1. Primer turno web" \
  "201 — el primero entra" \
  "{ \"profesional\": $PROFESIONAL, \"tratamiento\": $CONSULTA, \"inicio\": \"$HORA_1\", \"paciente_nuevo\": { \"nombre\": \"Tope\", \"apellido\": \"DePrueba\" } }"

PACIENTE=$( consultar "select id from pacientes order by id desc limit 1;" | jq -r '.[0].id' )
echo "  (el paciente de prueba quedó con id $PACIENTE)"
echo

probar "2. Segundo turno web" \
  "201 — dos es el tope, todavía entra" \
  "{ \"profesional\": $PROFESIONAL, \"tratamiento\": $CONSULTA, \"inicio\": \"$HORA_2\", \"paciente_id\": $PACIENTE }"

probar "3. Tercer turno web" \
  "409 — 'Ya tenés dos turnos con este profesional'" \
  "{ \"profesional\": $PROFESIONAL, \"tratamiento\": $CONSULTA, \"inicio\": \"$HORA_3\", \"paciente_id\": $PACIENTE }"


# ── El caso que prueba que el límite NO se pasó de la raya ───────────────────

echo "───────────────────────────────────────────────────────────────"
echo "▶ 4. El consultorio carga un turno a mano para ese mismo paciente"
echo "  esperado: entra. El tope es del formulario, no del consultorio."

SALIDA_MANUAL=$(
  consultar "insert into turnos ( paciente_id, profesional_id, inicio, canal, duracion_min )
             values ( $PACIENTE, $PROFESIONAL, now() + interval '35 days', 'manual', 30 )
             returning id, canal;" 2>&1
)

echo "  obtenido: $SALIDA_MANUAL"
echo


# ── Lo que quedó ─────────────────────────────────────────────────────────────

echo "───────────────────────────────────────────────────────────────"
echo "▶ 5. Lo que quedó en la base"

consultar "select canal, count(*) as cuantos from turnos group by canal order by canal;"

echo
echo "🔴 PARA LIMPIAR, cuando termines de mirar:"
echo "   supabase db query --linked \"delete from turnos; delete from pacientes;\""
