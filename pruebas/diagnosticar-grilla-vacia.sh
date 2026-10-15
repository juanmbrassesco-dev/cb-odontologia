#!/usr/bin/env bash
#
# POR QUÉ EXISTE: los casos 19 y 44 de `probar-panel.sh` avisan que NO PUDIERON
# MEDIR porque ningún día entre +30 y +36 devuelve bloques. El script dice QUE
# pasa; esto dice POR QUÉ.
#
# 🔴 Y existe por un fallo de método del 15-oct-2026: se escribió una causa
# INFERIDA («la cuenta de soporte no tiene tramos») con la forma de una causa
# medida, y era falsa por dos lados. Esto mide en vez de suponer.
#
#     uso:  bash pruebas/diagnosticar-grilla-vacia.sh
#
# Lo que imprime por cada día: el día de la semana, cuántos bloques devuelve, y
# si vino `tapado_por` — que es lo que distingue «no atiende ese día» de «ese
# día está tapado por una ausencia».

set -u

source .env

FUNCIONES="$SUPABASE_URL/functions/v1"

TOKEN=$(
  curl -s "$SUPABASE_URL/auth/v1/token?grant_type=password" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
    -H 'Content-Type: application/json' \
    -d "{ \"email\": \"$SOPORTE_EMAIL\", \"password\": \"$SOPORTE_PASSWORD\" }" \
  | jq -r '.access_token'
)

if [ "$TOKEN" = "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ No se pudo pedir el token. Mirá SOPORTE_EMAIL / SOPORTE_PASSWORD en el .env."
  exit 1
fi

echo
echo "▶ LOS TRAMOS QUE TIENE CARGADOS CADA PROFESIONAL"
echo "  (1 = lunes … 7 = domingo; es lo que decide si un día tiene agenda)"
echo

supabase db query --linked --output csv \
  "select h.profesional_id, p.nombre, h.dia_semana, h.inicio, h.fin, h.activo
   from public.horarios_base h
   join public.profesionales p on p.id = h.profesional_id
   order by h.profesional_id, h.dia_semana;" 2>/dev/null

echo
echo "▶ LOS PRIMEROS CATORCE DÍAS DE LA VENTANA DEL CASO 19, uno por uno"
echo

for SALTO in $( seq 30 43 ); do

  DIA=$( date -v+${SALTO}d +%F 2>/dev/null || date -d "+$SALTO days" +%F )
  NOMBRE=$( date -v+${SALTO}d +%A 2>/dev/null || date -d "+$SALTO days" +%A )

  CUERPO=$(
    curl -s "$FUNCIONES/horarios-del-panel?fecha=$DIA&duracion=30&profesional=1" \
      -H "apikey: $SUPABASE_PUBLISHABLE_KEY" \
      -H "Authorization: Bearer $TOKEN"
  )

  CUANTOS=$( echo "$CUERPO" | jq -r '.bloques | length' 2>/dev/null )
  TAPADO=$( echo "$CUERPO" | jq -r '.tapado_por.descripcion // "—"' 2>/dev/null )

  printf '  %s  %-10s  bloques: %-4s  tapado_por: %s\n' \
    "$DIA" "$NOMBRE" "$CUANTOS" "$TAPADO"
done

echo
echo "  ✅ CÓMO SE LEE:"
echo "     · bloques > 0 en alguno  → el caso 19 debería haber medido, y el"
echo "       problema está en cómo CUENTA el script, no en los datos."
echo "     · todos en 0 CON tapado_por → hay una ausencia tapando esa semana."
echo "     · todos en 0 SIN tapado_por → Cecilia no atiende ninguno de esos"
echo "       días de la semana, y el caso tiene que mirar otro rango."
