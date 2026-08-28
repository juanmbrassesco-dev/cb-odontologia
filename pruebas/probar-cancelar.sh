#!/bin/bash
#
# LA BATERÍA DE PRUEBAS DE `POST /cancelar` (etapa ④, paso D)
#
# Cada caso dice ANTES qué tiene que contestar, y después qué contestó. Si los
# dos renglones no coinciden, ahí está el bug: no hay nada que interpretar.
#
# 🔴 LAS FECHAS NO SE ESCRIBEN A MANO, SE LE PREGUNTAN AL SISTEMA — misma regla
# que `probar-reservar.sh` y por el mismo motivo: una fecha clavada le pone
# fecha de vencimiento al archivo, y una prueba que se pone en rojo sola es peor
# que no tenerla, porque manda a buscar un bug que no existe.
#
# 🔴 Y LO QUE ESTA BATERÍA CUIDA POR ENCIMA DE TODO ES QUE LAS CUATRO FORMAS DE
# FALLAR CONTESTEN IGUAL. El endpoint rechaza por cuatro motivos —el turno no
# existe, es de otro, ya está cancelado, ya pasó— y los cuatro tienen que dar
# **el mismo 403 con el mismo texto**. Si alguna vez difieren, cualquiera con
# una sesión válida manda turno_id 1, 2, 3… y el código de respuesta le va
# diciendo qué números existen y cuáles son suyos: eso es ENUMERACIÓN
# (enumeration). Los casos 5 a 8 existen para eso y sus textos se comparan.
#
# QUÉ NECESITA:
#   - el `.env` en la raíz del repo (claves del proyecto y usuario de prueba)
#   - `jq`
#   - la CLI de Supabase con el proyecto enlazado (para armar el escenario)
#
# CÓMO SE CORRE, parado en la raíz del repo:
#
#   bash pruebas/probar-cancelar.sh
#
# DEJA RASTRO: turnos y pacientes de prueba. El comando para borrarlos se
# imprime al final; no se ejecuta solo.
#
# ⏰ EL USUARIO DE PRUEBA es el mismo de `probar-reservar.sh`, con la misma
# fecha de vencimiento: se borra ANTES DE PRODUCCIÓN. El detalle de por qué esta
# batería no se arregla sola el día que exista el login de verdad está escrito
# en el encabezado de aquel archivo, y no se copia acá para no tener dos.

set -u

set -a
source .env
set +a

FUNCIONES="$SUPABASE_URL/functions/v1"

CONSULTA=1
PROFESIONAL=1

# La casilla del paciente ajeno. Va en un dominio reservado a propósito, para no
# meter el correo de nadie en un repo público.
CASILLA_AJENA='otra-casilla@example.com'


# ── Un par de ayudantes ──────────────────────────────────────────────────────

# `date` no se escribe igual en macOS y en Linux, y esto tiene que correr en las
# dos. Se intenta la forma de macOS y, si falla, la de Linux.
sumar_dias () {
  date -v"$1"d +%F 2>/dev/null || date -d "$1 days" +%F
}

# Una consulta a la base, con la salida siempre en la misma forma.
#
# 🔴 LOS DOS FLAGS SON OBLIGATORIOS. La CLI de Supabase contesta la MISMA
# consulta de tres maneras según quién la corra: tabla dibujada, JSON envuelto o
# JSON pelado. `--output-format json` saca la tabla y `--agent no` saca la
# detección de quién está del otro lado. El porqué completo, con las tres formas
# medidas, está en `probar-reservar.sh`.
consultar () {

  supabase db query --linked --output-format json --agent no "$1" \
  | jq 'if type == "array" then . else .rows end'
}

# Un `insert … returning id` del que hay que sacar el id, con la red puesta.
#
# 🔴 POR QUÉ NO SE ESCRIBE DERECHO `id=$( consultar … | jq … )`: el 25-ago-2026
# un insert así ANDABA —la fila quedaba creada— y el id viajaba VACÍO, así que
# el pedido salía roto y se leía como un endpoint que falla. Guardar la salida
# cruda antes de pasarla por `jq` es lo que permite mostrarla cuando algo no
# cierra, en vez de seguir con una variable en blanco.
#
# $1 = la consulta · $2 = para qué es, para el mensaje de error
id_de_insert () {

  local SALIDA
  local ID

  SALIDA=$( consultar "$1" )
  ID=$( echo "$SALIDA" | jq -r '.[0].id' 2>/dev/null )

  if [ "$ID" = "null" ] || [ -z "$ID" ]; then
    echo "❌ No se pudo armar $2, así que su caso no probaría nada." >&2
    echo "   Esto contestó la CLI, crudo:" >&2
    echo "$SALIDA" >&2
    exit 1
  fi

  echo "$ID"
}

# $1 = qué se prueba · $2 = qué tiene que dar · $3 = el cuerpo del pedido
#
# Guarda el cuerpo de la última respuesta en `ULTIMO_TEXTO`, que es lo que
# después permite comparar los textos de los casos 5 a 8 entre sí.
probar () {

  echo "───────────────────────────────────────────────────────────────"
  echo "▶ $1"
  echo "  esperado: $2"

  local RESPUESTA

  RESPUESTA=$(
    curl -s -w '\n%{http_code}' -X POST "$FUNCIONES/cancelar" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "$3"
  )

  ULTIMO_TEXTO=$( echo "$RESPUESTA" | sed '$d' )

  echo "  obtenido: $( echo "$RESPUESTA" | tail -1 )   $ULTIMO_TEXTO"
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


# ── El escenario, preguntado al sistema ──────────────────────────────────────
#
# Hacen falta TRES bloques libres distintos y uno en el pasado. Los tres libres
# los elige `GET /horarios-disponibles`, que ya sabe qué días trabaja la
# profesional, cuáles están tapados y cuál cae adentro de la ventana de 12
# horas. El del pasado no se puede reservar —el endpoint lo rechazaría, y con
# razón—, así que ése se escribe directo en la base.

HOY=$( date +%F )
HASTA=$( sumar_dias +40 )

grilla () {
  curl -s "$FUNCIONES/horarios-disponibles?profesional=$PROFESIONAL&tratamiento=$CONSULTA&desde=$HOY&hasta=$HASTA" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY"
}

LIBRES=$( grilla | jq -r '[ .dias[].bloques[] | select( .estado == "libre" ) | .inicio ]' )

HORA_FELIZ=$( echo "$LIBRES" | jq -r '.[0]' )
HORA_CANCELADO=$( echo "$LIBRES" | jq -r '.[1]' )
HORA_AJENO=$( echo "$LIBRES" | jq -r '.[2]' )

if [ "$HORA_AJENO" = "null" ]; then
  echo "❌ Hacen falta tres bloques libres y la grilla no los tiene."
  echo "   libres encontrados: $( echo "$LIBRES" | jq 'length' )"
  exit 1
fi

AYER="$( sumar_dias -1 )T09:00:00-03:00"

echo "✅ Escenario armado sin escribir una sola fecha a mano:"
echo "   el feliz       → $HORA_FELIZ"
echo "   ya cancelado   → $HORA_CANCELADO"
echo "   turno ajeno    → $HORA_AJENO"
echo "   ya pasado      → $AYER"
echo

# El paciente propio. Se crea a mano en vez de usar `paciente_nuevo` porque los
# cuatro turnos de abajo tienen que colgar del MISMO paciente, y `reservar` da
# de alta uno nuevo cada vez que se le manda `paciente_nuevo`.
MIO=$( id_de_insert \
  "insert into pacientes ( nombre, apellido, email ) values ( 'Ana', 'Zabala', '$PRUEBA_EMAIL' ) returning id;" \
  "el paciente propio" )

AJENO=$( id_de_insert \
  "insert into pacientes ( nombre, apellido, email ) values ( 'Carla', 'Mendez', '$CASILLA_AJENA' ) returning id;" \
  "el paciente ajeno" )

echo "  paciente propio = id $MIO · paciente ajeno = id $AJENO"

# Los dos turnos que NO se pueden crear por la web, escritos directo en la base.
# `canal` dice 'manual' porque es exactamente lo que serían: turnos cargados a
# mano por el consultorio. Decía 'panel' hasta el 28-ago-2026, y la migración
# `restringir_canal_de_turnos` lo dejó fuera de la lista de valores válidos: los
# dos inserts pasaron a fallar y con ellos cuatro casos de esta batería. Es el
# valor el que se corrige, no la migración — 'panel' y 'manual' nombraban lo
# mismo, y ahora hay un solo nombre.
TURNO_PASADO=$( id_de_insert \
  "insert into turnos ( paciente_id, profesional_id, tratamiento_id, inicio, duracion_min, canal )
   values ( $MIO, $PROFESIONAL, $CONSULTA, '$AYER', 30, 'manual' ) returning id;" \
  "el turno ya pasado" )

TURNO_AJENO=$( id_de_insert \
  "insert into turnos ( paciente_id, profesional_id, tratamiento_id, inicio, duracion_min, canal )
   values ( $AJENO, $PROFESIONAL, $CONSULTA, '$HORA_AJENO', 30, 'manual' ) returning id;" \
  "el turno ajeno" )

# 🔴 LA RED QUE FALTABA — puesta el 28-ago-2026, después de que la batería
# siguiera corriendo con el escenario roto.
#
# `id_de_insert` termina en `exit 1` cuando el insert falla, pero se la llama
# dentro de `$( … )`: ese `exit` mata al SUBSHELL, no a la batería. El resultado
# medido: los dos inserts fallaron, se imprimieron los dos ❌, y la corrida siguió
# igual con las variables vacías — los casos 6 y 8 mandaron un cuerpo sin id y
# contestaron "el cuerpo del pedido no es JSON válido", que no tiene nada que ver
# con lo que esos casos prueban. Una prueba que no corta cuando dice que corta
# manda a buscar el bug al lugar equivocado.

if [ -z "$TURNO_PASADO" ] || [ -z "$TURNO_AJENO" ]; then
  echo "❌ El escenario quedó incompleto y los casos 6, 8 y 9 no probarían nada."
  echo "   Mirá los errores de arriba: sin esos dos turnos no tiene sentido seguir."
  exit 1
fi


# Los dos que SÍ salen por la web, para que el camino feliz se pruebe entero.
reservar () {
  curl -s -X POST "$FUNCIONES/reservar" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{ \"profesional\": $PROFESIONAL, \"tratamiento\": $CONSULTA, \"inicio\": \"$1\", \"paciente_id\": $MIO }" \
  | jq -r '.id'
}

TURNO_FELIZ=$( reservar "$HORA_FELIZ" )
TURNO_CANCELADO=$( reservar "$HORA_CANCELADO" )

if [ "$TURNO_FELIZ" = "null" ] || [ "$TURNO_CANCELADO" = "null" ]; then
  echo "❌ No se pudieron reservar los dos turnos de prueba. Corré probar-reservar.sh primero."
  exit 1
fi

# Y éste se cancela YA, para que el caso 7 tenga qué encontrar apagado.
curl -s -o /dev/null -X POST "$FUNCIONES/cancelar" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{ \"turno_id\": $TURNO_CANCELADO }"

echo "  turnos: feliz=$TURNO_FELIZ · ya cancelado=$TURNO_CANCELADO · ajeno=$TURNO_AJENO · pasado=$TURNO_PASADO"
echo


# ── 1. La puerta ─────────────────────────────────────────────────────────────

echo "───────────────────────────────────────────────────────────────"
echo "▶ 1. Sin token"
echo "  esperado: 401"
curl -s -o /dev/null -w "  obtenido: %{http_code}\n\n" -X POST "$FUNCIONES/cancelar" \
  -H "Content-Type: application/json" \
  -d "{ \"turno_id\": $TURNO_FELIZ }"

echo "───────────────────────────────────────────────────────────────"
echo "▶ 2. Token inventado"
echo "  esperado: 401"
curl -s -o /dev/null -w "  obtenido: %{http_code}\n\n" -X POST "$FUNCIONES/cancelar" \
  -H "Authorization: Bearer esto-no-es-un-token" \
  -H "Content-Type: application/json" \
  -d "{ \"turno_id\": $TURNO_FELIZ }"


# ── 2. El pedido mal armado ──────────────────────────────────────────────────
#
# Estos dos SÍ contestan el motivo, y no filtran nada: "el cuerpo no es JSON" y
# "turno_id tiene que ser un número" no dicen una palabra sobre qué turnos
# existen. Lo que no puede distinguirse es POR CUÁL DE LOS CUATRO MOTIVOS se
# rechazó un turno_id bien formado, que es lo que prueban los casos 5 a 8.

probar "3. Cuerpo que no es JSON" \
  "400 — el cuerpo del pedido no es JSON válido" \
  "esto no es json"

probar "4. turno_id que no es un número" \
  "400 — turno_id tiene que ser un número" \
  '{ "turno_id": "hola" }'


# ── 3. Las cuatro formas de fallar, que tienen que ser INDISTINGUIBLES ───────

probar "5. Un id que no existe" \
  "403 — ese turno no se puede cancelar" \
  '{ "turno_id": 999999 }'

TEXTO_INEXISTENTE="$ULTIMO_TEXTO"

probar "6. Turno AJENO — existe, es de otro correo" \
  "403 y EL MISMO TEXTO del caso 5" \
  "{ \"turno_id\": $TURNO_AJENO }"

TEXTO_AJENO="$ULTIMO_TEXTO"

probar "7. Turno YA CANCELADO — es tuyo, pero está apagado" \
  "403 y EL MISMO TEXTO del caso 5" \
  "{ \"turno_id\": $TURNO_CANCELADO }"

TEXTO_CANCELADO="$ULTIMO_TEXTO"

probar "8. Turno YA PASADO — es tuyo y está activo, pero ya ocurrió" \
  "403 y EL MISMO TEXTO del caso 5" \
  "{ \"turno_id\": $TURNO_PASADO }"

TEXTO_PASADO="$ULTIMO_TEXTO"

echo "───────────────────────────────────────────────────────────────"
echo "▶ 9. LOS CUATRO TEXTOS, COMPARADOS ENTRE SÍ"
echo "  esperado: idénticos. Si difieren, hay enumeración"

if [ "$TEXTO_INEXISTENTE" = "$TEXTO_AJENO" ] \
   && [ "$TEXTO_INEXISTENTE" = "$TEXTO_CANCELADO" ] \
   && [ "$TEXTO_INEXISTENTE" = "$TEXTO_PASADO" ]; then
  echo "  obtenido: ✅ los cuatro dicen $TEXTO_INEXISTENTE"
else
  echo "  obtenido: ❌ NO son iguales"
  echo "    no existe  → $TEXTO_INEXISTENTE"
  echo "    ajeno      → $TEXTO_AJENO"
  echo "    cancelado  → $TEXTO_CANCELADO"
  echo "    pasado     → $TEXTO_PASADO"
fi
echo


# ── 4. El camino feliz, y el doble clic ──────────────────────────────────────

probar "10. LA CANCELACIÓN FELIZ" \
  "200 con el id y cancelado: true" \
  "{ \"turno_id\": $TURNO_FELIZ }"

probar "11. EL MISMO TURNO OTRA VEZ — el doble clic" \
  "403, el mismo texto de siempre. Es el costo aceptado de no distinguir" \
  "{ \"turno_id\": $TURNO_FELIZ }"


# ── 5. Las dos regresiones ───────────────────────────────────────────────────

echo "───────────────────────────────────────────────────────────────"
echo "▶ 12. REGRESIÓN — el bloque liberado, visto por /horarios-disponibles"
echo "  esperado: $HORA_FELIZ en 'libre'"

grilla | jq -c --arg h "$HORA_FELIZ" '.dias[].bloques[] | select( .inicio == $h )'
echo

echo "───────────────────────────────────────────────────────────────"
echo "▶ 13. REGRESIÓN — qué le queda al paciente en /mis-turnos"
echo "  esperado: NINGUNO de los cuatro turnos de prueba"

curl -s "$FUNCIONES/mis-turnos" -H "Authorization: Bearer $TOKEN" \
  | jq -c '[ .[] | { id, inicio } ]'
echo


# ── 6. Lo que quedó ──────────────────────────────────────────────────────────

echo "───────────────────────────────────────────────────────────────"
echo "▶ 14. Lo que quedó en la base"

consultar "select
             ( select count(*) from turnos ) as turnos,
             ( select count(*) from turnos where activo ) as turnos_activos,
             ( select count(*) from pacientes ) as pacientes;" \
  | jq -c '.'

echo
echo "⚠ Quedan DOS turnos activos y ninguno es un bug: el ajeno de Carla no se"
echo "  cancela nunca —justamente porque no es del que está conectado— y el"
echo "  pasado sigue activo porque acá nada se apaga solo al pasar la hora."
echo "  Los otros dos de los cuatro son los que esta batería apagó."
echo
echo "🔴 PARA LIMPIAR, cuando termines de mirar:"
echo "   supabase db query --linked \"delete from turnos; delete from pacientes;\""
