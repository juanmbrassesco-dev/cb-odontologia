#!/bin/bash
#
# LA BATERÍA DE PRUEBAS DE `POST /reservar` (etapa ③, paso D)
#
# Cada caso dice ANTES qué tiene que contestar, y después qué contestó. Si los
# dos renglones no coinciden, ahí está el bug: no hay nada que interpretar.
#
# 🔴 LAS FECHAS NO SE ESCRIBEN A MANO, SE LE PREGUNTAN AL SISTEMA. La primera
# versión de este archivo las tenía clavadas ("el martes 1 de septiembre a las
# 15:00") y eso le ponía fecha de vencimiento adentro: pasado ese día, la
# reserva feliz cae en el pasado y contesta 400. Una prueba que se pone en rojo
# sola es peor que no tenerla, porque manda a buscar un bug que no existe.
#
# Así que el escenario sale de `GET /horarios-disponibles`, que es el endpoint
# que YA sabe qué días trabaja la profesional, cuáles están tapados y qué
# bloques entran. De paso, evita copiar esas reglas acá: dos copias de la misma
# regla se desincronizan siempre.
#
# QUÉ NECESITA:
#   - el `.env` en la raíz del repo (claves del proyecto y usuario de prueba)
#   - `jq`
#   - la CLI de Supabase con el proyecto enlazado (para los casos 14 y 18)
#
# CÓMO SE CORRE, parado en la raíz del repo:
#
#   bash pruebas/probar-reservar.sh
#
# DEJA RASTRO: un turno y varios pacientes de prueba. El comando para borrarlos
# se imprime al final; no se ejecuta solo.

# 🔴 EL USUARIO DE PRUEBA NO ES EL LOGIN DE LOS PACIENTES, Y POR ESO ESTA
# BATERÍA NO SE ARREGLA SOLA. El token sale más abajo con `grant_type=password`,
# o sea correo y contraseña. La identidad del paciente en la web va a ser cuenta
# de Google (sección 6 del doc de estado) y Google NO tiene ese flujo: el día que
# exista el login de verdad, esto sigue necesitando SU PROPIA cuenta de correo y
# contraseña, con un correo aparte del de cualquier paciente. Los dos proveedores
# conviven en el mismo proyecto de Supabase; lo único que hay que sostener es esa
# cuenta y el `.env` apuntándole.
#
# Lo que NO hay que hacer es pegar a mano un token sacado de una sesión real:
# vence, y entonces la batería se pone en rojo sola — exactamente lo que el
# comentario de las fechas, más arriba, dice que no puede pasar.
#
# ⏰ Y tiene final: esa cuenta se borra ANTES DE PRODUCCIÓN. Es una credencial de
# larga vida (long-lived credential) viva en el mismo proyecto que va a guardar
# datos de salud.

set -u

set -a
source .env
set +a

FUNCIONES="$SUPABASE_URL/functions/v1"

# Los dos tratamientos que se reservan por la web. Son ids de la base real.
CONSULTA=1
LIMPIEZA=11

PROFESIONAL=1


# ── Un par de ayudantes ──────────────────────────────────────────────────────

# `date` no se escribe igual en macOS y en Linux, y esto tiene que correr en las
# dos. Se intenta la forma de macOS y, si falla, la de Linux.
sumar_dias () {
  date -v"$1"d +%F 2>/dev/null || date -d "$1 days" +%F
}

# Qué día de la semana es una fecha, numerado como la base: lunes 1 … domingo 7.
dia_de_semana () {
  date -j -f %Y-%m-%d "$1" +%u 2>/dev/null || date -d "$1" +%u
}

# Una consulta a la base, con la salida siempre en la misma forma.
#
# 🔴 LOS DOS FLAGS SON OBLIGATORIOS Y CADA UNO TAPA UN AGUJERO DISTINTO. La CLI
# de Supabase contesta la MISMA consulta de tres maneras según quién la corra, y
# las tres se vieron el 25-ago-2026 sobre esta misma línea:
#
#   sin flags                     → una tabla dibujada con caracteres (┌─┐│└─┘)
#   --output-format json          → JSON, pero envuelto en un objeto con `rows`
#                                   si la corre un agente, y pelado si la corre
#                                   una persona
#   + --agent no                  → siempre el array de filas pelado
#
# `--output-format json` saca la tabla; `--agent no` saca la detección de quién
# está del otro lado. Sin los dos, este script anda en una terminal y falla en
# la otra — que fue exactamente lo que pasó, dos veces seguidas.
#
# El `if type == "array"` de abajo es la red por si la CLI vuelve a cambiar de
# forma: venga pelado o venga envuelto, de acá sale el array de filas.
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


# ── El escenario, preguntado al sistema ──────────────────────────────────────

HOY=$( date +%F )
HASTA=$( sumar_dias +40 )

grilla () {
  curl -s "$FUNCIONES/horarios-disponibles?profesional=$PROFESIONAL&tratamiento=$1&desde=$HOY&hasta=$HASTA" \
    -H "apikey: $SUPABASE_PUBLISHABLE_KEY"
}

GRILLA_CONSULTA=$( grilla $CONSULTA )
GRILLA_LIMPIEZA=$( grilla $LIMPIEZA )

# El primer hueco reservable de verdad. Ya pasó la ventana de 12 horas y el
# techo de dos meses: el endpoint lo marcó `libre`, no lo marcamos nosotros.
HORA_LIBRE=$( echo "$GRILLA_CONSULTA" | jq -r '[ .dias[].bloques[] | select( .estado == "libre" ) ][0].inicio' )
DIA_LIBRE=$( echo "$HORA_LIBRE" | cut -c1-10 )

# 🔴 UN SEGUNDO HUECO, Y ES NUEVO DESDE EL 27-ago-2026. La prueba 7 dejó de
# rechazar y ahora RESERVA de verdad: si usara el mismo bloque que la 15, le
# ocuparía el hueco a la reserva feliz y la 15 daría 409 sin que nada esté roto.
HORA_DERIVADA=$( echo "$GRILLA_CONSULTA" | jq -r '[ .dias[].bloques[] | select( .estado == "libre" ) ][1].inicio' )

# Un bloque donde la limpieza de 60 minutos NO entra antes del cierre. También
# lo decide el endpoint.
HORA_NO_ENTRA=$( echo "$GRILLA_LIMPIEZA" | jq -r '[ .dias[].bloques[] | select( .estado == "no_entra" ) ][0].inicio' )

# Un día TAPADO por una excepción. Se reconoce así: no tiene ningún bloque, pero
# ese mismo día de la semana sí trabaja en otra fecha del rango. Un sábado
# también viene sin bloques y NO está tapado — está fuera de la agenda, que es
# otra cosa y contesta otro error.
DIAS_QUE_TRABAJA=$(
  echo "$GRILLA_CONSULTA" \
  | jq -r '.dias[] | select( .bloques | length > 0 ) | .fecha'
)

SEMANA_QUE_TRABAJA=""

for FECHA in $DIAS_QUE_TRABAJA; do
  SEMANA_QUE_TRABAJA="$SEMANA_QUE_TRABAJA $( dia_de_semana "$FECHA" )"
done

DIA_TAPADO=""

for FECHA in $( echo "$GRILLA_CONSULTA" | jq -r '.dias[] | select( .bloques | length == 0 ) | .fecha' ); do

  if [ -z "$DIA_TAPADO" ] && [[ " $SEMANA_QUE_TRABAJA " == *" $( dia_de_semana "$FECHA" ) "* ]]; then
    DIA_TAPADO="$FECHA"
  fi
done

if [ "$HORA_LIBRE" = "null" ] || [ "$HORA_DERIVADA" = "null" ] || [ -z "$DIA_TAPADO" ] || [ "$HORA_NO_ENTRA" = "null" ]; then
  echo "❌ No se pudo armar el escenario desde /horarios-disponibles."
  echo "   libre=$HORA_LIBRE · derivada=$HORA_DERIVADA · no_entra=$HORA_NO_ENTRA · tapado=$DIA_TAPADO"
  exit 1
fi

# Una hora que no existe en ninguna agenda, sobre el ÚLTIMO día trabajado del
# rango. El día tiene que ser lejano a propósito: si se usara el primero, el
# pedido caería adentro de las 12 horas de anticipación y el endpoint contestaría
# ESO en vez de lo que este caso quiere probar. El orden de los chequeos importa,
# y acá se paga.
#
# ⚠ Las 06:00 se eligen porque la profesional arranca a las 08:00 en su tramo más
# temprano. Si algún día se carga un tramo que empiece antes, este caso deja de
# probar lo que dice.
DIA_LEJANO=$( echo "$DIAS_QUE_TRABAJA" | tail -1 )
HORA_SIN_AGENDA="${DIA_LEJANO}T06:00:00-03:00"
HORA_PASADA="$( sumar_dias -1 )T09:00:00-03:00"
HORA_LEJANA="$( sumar_dias +100 )T15:00:00-03:00"

echo "✅ Escenario armado sin escribir una sola fecha a mano:"
echo "   reserva feliz  → $HORA_LIBRE"
echo "   no entra       → $HORA_NO_ENTRA"
echo "   día tapado     → $DIA_TAPADO"
echo


# ── 1. La puerta ─────────────────────────────────────────────────────────────

echo "───────────────────────────────────────────────────────────────"
echo "▶ 1. Sin token"
echo "  esperado: 401"
curl -s -o /dev/null -w "  obtenido: %{http_code}\n\n" -X POST "$FUNCIONES/reservar" \
  -H "Content-Type: application/json" \
  -d '{}'


# ── 2. Los rechazos, todos con sesión válida ─────────────────────────────────

probar "2. Cuerpo que no es JSON" \
  "400 — el cuerpo del pedido no es JSON válido" \
  'esto no es json'

probar "3. Falta el paciente" \
  "400 — mandá paciente_id o paciente_nuevo" \
  "{ \"profesional\": $PROFESIONAL, \"tratamiento\": $CONSULTA, \"inicio\": \"$HORA_LIBRE\" }"

probar "4. Vienen los DOS pacientes" \
  "400 — uno de los dos, no los dos" \
  "{ \"profesional\": $PROFESIONAL, \"tratamiento\": $CONSULTA, \"inicio\": \"$HORA_LIBRE\", \"paciente_id\": 1, \"paciente_nuevo\": { \"nombre\": \"A\", \"apellido\": \"B\" } }"

probar "5. inicio SIN desfase horario" \
  "400 — inicio va con fecha, hora y desfase" \
  "{ \"profesional\": $PROFESIONAL, \"tratamiento\": $CONSULTA, \"inicio\": \"${DIA_LIBRE}T15:00:00\", \"paciente_nuevo\": { \"nombre\": \"Ana\", \"apellido\": \"Zabala\" } }"

probar "6. Profesional que no existe" \
  "400 — ese profesional no está disponible" \
  "{ \"profesional\": 99, \"tratamiento\": $CONSULTA, \"inicio\": \"$HORA_LIBRE\", \"paciente_nuevo\": { \"nombre\": \"Ana\", \"apellido\": \"Zabala\" } }"

# 🔴 ESTA PRUEBA CAMBIÓ DE SIGNIFICADO EL 27-ago-2026, Y NO SE BORRÓ.
#
# Hasta ese día esperaba un `400 — ese tratamiento no se reserva por la web`.
# Ese rechazo dejó de existir: ahora el tratamiento SE CONVIERTE. El paciente
# que entra por cualquiera de los nueve consigue turno, y lo que se agenda es
# la consulta de 30 que el consultorio le pone adelante a todo.
#
# Se conserva porque sigue cubriendo el mismo riesgo, del otro lado: antes
# vigilaba que no entrara, ahora vigila que entre BIEN — con la duración del
# envase, no la del elegido.
probar "7. Tratamiento que NO se reserva solo — AHORA SE CONVIERTE" \
  "201 — se agenda una consulta de 30, no el tratamiento elegido" \
  "{ \"profesional\": $PROFESIONAL, \"tratamiento\": 2, \"inicio\": \"$HORA_DERIVADA\", \"paciente_nuevo\": { \"nombre\": \"Ana\", \"apellido\": \"Zabala\" } }"

# Y la respuesta sola no alcanza: dice lo que el endpoint contestó, no lo que
# la base guardó. Las dos columnas se leen de la fila recién escrita.
echo "───────────────────────────────────────────────────────────────"
echo "▶ 7.b LO QUE QUEDÓ GUARDADO, leído de la base"
echo "  esperado: tratamiento_id=$CONSULTA (el envase) · motivo_consulta_id=2 (lo elegido) · duracion_min=30"
consultar "select tratamiento_id, motivo_consulta_id, duracion_min
           from turnos order by id desc limit 1;" | jq -c '.[0]'
echo

probar "8. Más allá de los 2 meses" \
  "400 — todavía no se puede reservar tan lejos" \
  "{ \"profesional\": $PROFESIONAL, \"tratamiento\": $CONSULTA, \"inicio\": \"$HORA_LEJANA\", \"paciente_nuevo\": { \"nombre\": \"Ana\", \"apellido\": \"Zabala\" } }"

probar "9. Ayer" \
  "400 — hay que sacarlo con 12 horas de anticipación" \
  "{ \"profesional\": $PROFESIONAL, \"tratamiento\": $CONSULTA, \"inicio\": \"$HORA_PASADA\", \"paciente_nuevo\": { \"nombre\": \"Ana\", \"apellido\": \"Zabala\" } }"

probar "10. Día tapado por una excepción ($DIA_TAPADO)" \
  "400 — ese día el consultorio no atiende" \
  "{ \"profesional\": $PROFESIONAL, \"tratamiento\": $CONSULTA, \"inicio\": \"${DIA_TAPADO}T09:00:00-03:00\", \"paciente_nuevo\": { \"nombre\": \"Ana\", \"apellido\": \"Zabala\" } }"

probar "11. Una hora que no está en la agenda de ese día" \
  "400 — ese horario no está en la agenda de ese día" \
  "{ \"profesional\": $PROFESIONAL, \"tratamiento\": $CONSULTA, \"inicio\": \"$HORA_SIN_AGENDA\", \"paciente_nuevo\": { \"nombre\": \"Ana\", \"apellido\": \"Zabala\" } }"

probar "12. Limpieza en un bloque donde no entra antes del cierre" \
  "400 — ese tratamiento no entra en ese horario" \
  "{ \"profesional\": $PROFESIONAL, \"tratamiento\": $LIMPIEZA, \"inicio\": \"$HORA_NO_ENTRA\", \"paciente_nuevo\": { \"nombre\": \"Ana\", \"apellido\": \"Zabala\" } }"

probar "13. paciente_id que NO existe" \
  "403 — ese paciente no está disponible" \
  "{ \"profesional\": $PROFESIONAL, \"tratamiento\": $CONSULTA, \"inicio\": \"$HORA_LIBRE\", \"paciente_id\": 999999 }"


# ── 3. El paciente ajeno, que es el corazón de la regla de enumeración ───────

echo "───────────────────────────────────────────────────────────────"
echo "▶ Cargando un paciente de OTRA casilla, para el caso 14…"

# La consulta va por `consultar`, que es donde está explicado por qué la salida
# de la CLI necesita dos flags para ser siempre la misma.
#
# Lo de acá es la misma red que el token allá arriba: la salida se guarda ANTES
# de pasarla por `jq`, el id se verifica, y si algo salió mal se muestra crudo.
# El 25-ago-2026 el `insert` andaba —el paciente quedaba creado— pero el id no
# se podía leer, viajaba VACÍO, y el pedido salía roto: se leía como un endpoint
# que falla cuando el roto era este script. El caso 14 es la prueba de
# ENUMERACIÓN DE PACIENTES (patient enumeration) y que se saltee en silencio es
# exactamente lo que no puede pasar.
SALIDA_AJENO=$(
  consultar "insert into pacientes ( nombre, apellido, email ) values ( 'Carla', 'Mendez', 'otra-casilla@example.com' ) returning id;"
)

AJENO=$( echo "$SALIDA_AJENO" | jq -r '.[0].id' 2>/dev/null )

if [ "$AJENO" = "null" ] || [ -z "$AJENO" ]; then
  echo "❌ No se pudo dar de alta el paciente ajeno, así que el caso 14 no prueba nada."
  echo "   Esto es lo que contestó la CLI, crudo:"
  echo "$SALIDA_AJENO"
  exit 1
fi

echo "  paciente ajeno = id $AJENO"
echo

probar "14. paciente_id AJENO — existe, pero es de otro correo" \
  "403 y EL MISMO TEXTO del caso 13. Si difiere, hay enumeración" \
  "{ \"profesional\": $PROFESIONAL, \"tratamiento\": $CONSULTA, \"inicio\": \"$HORA_LIBRE\", \"paciente_id\": $AJENO }"


# ── 4. La reserva, y el choque ───────────────────────────────────────────────

probar "15. LA RESERVA FELIZ" \
  "201 con id, inicio y duracion_min 30" \
  "{ \"profesional\": $PROFESIONAL, \"tratamiento\": $CONSULTA, \"inicio\": \"$HORA_LIBRE\", \"paciente_nuevo\": { \"nombre\": \"Ana\", \"apellido\": \"Zabala\", \"telefono\": \"342-1234567\" }, \"observaciones\": \"prueba automatizada\" }"

probar "16. EL MISMO BLOQUE OTRA VEZ" \
  "409 — esa hora se acaba de ocupar" \
  "{ \"profesional\": $PROFESIONAL, \"tratamiento\": $CONSULTA, \"inicio\": \"$HORA_LIBRE\", \"paciente_nuevo\": { \"nombre\": \"Ana\", \"apellido\": \"Zabala\" } }"


# ── 5. La regresión: ② y ③ tienen que hablar del mismo estado ────────────────

echo "───────────────────────────────────────────────────────────────"
echo "▶ 17. REGRESIÓN — el bloque recién reservado, visto por /horarios-disponibles"
echo "  esperado: $HORA_LIBRE en 'ocupado'"

grilla $CONSULTA | jq -c --arg h "$HORA_LIBRE" '.dias[].bloques[] | select( .inicio == $h )'

echo
echo "───────────────────────────────────────────────────────────────"
echo "▶ 18. Lo que quedó en la base"

# Va por `consultar` igual que el caso 14, por el mismo motivo explicado allá.
# Acá NO se corta la corrida: es el resumen del final, no una prueba.
SALIDA_CUENTAS=$(
  consultar "select ( select count(*) from turnos ) as turnos, ( select count(*) from pacientes ) as pacientes;"
)

echo "$SALIDA_CUENTAS" | jq -c '.' 2>/dev/null \
  || { echo "  ⚠ La CLI no contestó JSON. Crudo:"; echo "$SALIDA_CUENTAS"; }

echo
echo "⚠ Los pacientes van a ser MÁS que los turnos, y no es un bug: el caso 16"
echo "  da de alta al paciente y recién después choca con el 409. Es el costo"
echo "  aceptado de no deduplicar en el portero."
echo
echo "🔴 PARA LIMPIAR, cuando termines de mirar:"
echo "   supabase db query --linked \"delete from turnos; delete from pacientes;\""
