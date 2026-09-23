#!/bin/bash
#
# LA PRUEBA DEL `check` DEL CANAL (fase 4, B1)
#
# Verifica lo único que esa migración promete: que `turnos.canal` sólo acepta
# 'web' y 'manual'. Un `check` que no se prueba contra el valor que quiere
# prohibir no está verificado.
#
# 🔴 NO DEJA RASTRO, Y ESO ES DE DISEÑO: los tres casos usan a propósito un
# paciente y un profesional que NO existen. Postgres evalúa el `check` de la
# columna ANTES que las foreign keys, así que:
#
#   - si el canal es inválido, rebota por el CHECK  → la fila nunca se escribe
#   - si el canal es válido, pasa el check y rebota por la FOREIGN KEY
#
# O sea que el motivo del rechazo es la respuesta: `turnos_canal_valido` (23514)
# significa que el canal fue rechazado; un error de foreign key (23503) significa
# que el canal PASÓ. Ninguna fila entra, así que no hay nada que limpiar después.
#
# QUÉ NECESITA:
#   - el `.env` en la raíz del repo
#   - `jq`
#
# CÓMO SE CORRE, parado en la raíz del repo:
#
#   bash pruebas/probar-canal.sh

set -u

set -a
source .env
set +a

# La fecha no se escribe a mano: se le pregunta al sistema, misma regla que las
# otras dos baterías. Cualquier fecha sirve — la fila nunca llega a guardarse.
INICIO=$( date -u -v+3d '+%Y-%m-%dT%H:00:00Z' )

INEXISTENTE=999999999

probar () {
  local canal="$1"
  local esperado="$2"
  local titulo="$3"

  echo
  echo "── $titulo"
  echo "   canal enviado : '$canal'"
  echo "   ESPERADO      : $esperado"

  local respuesta
  respuesta=$( curl -s -X POST "$SUPABASE_URL/rest/v1/turnos" \
    -H "apikey: $SUPABASE_SECRET_KEY" \
    -H "Authorization: Bearer $SUPABASE_SECRET_KEY" \
    -H "Content-Type: application/json" \
    -d "{
          \"canal\": \"$canal\",
          \"inicio\": \"$INICIO\",
          \"paciente_id\": $INEXISTENTE,
          \"profesional_id\": $INEXISTENTE
        }" )

  local code
  code=$( echo "$respuesta" | jq -r '.code // "sin-code"' )
  local msg
  msg=$( echo "$respuesta" | jq -r '.message // "sin-message"' )

  echo "   OBTENIDO      : $code — $msg"
}

echo "════════════════════════════════════════════════════════════"
echo " EL CHECK DEL CANAL — ninguna fila se escribe en esta prueba"
echo "════════════════════════════════════════════════════════════"

probar "Web" \
  "23514, y el mensaje tiene que nombrar turnos_canal_valido" \
  "CASO 1 — la mayúscula rebota (es el caso que justifica la migración)"

probar "telefono" \
  "23514, y el mensaje tiene que nombrar turnos_canal_valido" \
  "CASO 2 — un canal que no está en la lista rebota"

probar "web" \
  "23503 (foreign key). Si sale 23514, el check está rechazando lo que debe aceptar" \
  "CASO 3 — el canal del portero PASA el check"

probar "manual" \
  "23503 (foreign key). Si sale 23514, el check está rechazando lo que debe aceptar" \
  "CASO 4 — el canal del consultorio PASA el check"

echo
echo "════════════════════════════════════════════════════════════"
echo " Los cuatro casos tienen que fallar. Lo que se lee es POR QUÉ:"
echo "   23514 = lo paró el check del canal"
echo "   23503 = el canal pasó, lo paró la foreign key inexistente"
echo "════════════════════════════════════════════════════════════"
