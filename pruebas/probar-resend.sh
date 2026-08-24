#!/bin/bash
#
# DIAGNÓSTICO DEL PROVEEDOR DE CORREO — le habla a Resend DIRECTO, sin pasar por
# el portero.
#
# Para qué existe: cuando un correo no llega hay DOS preguntas metidas en una,
# "¿está mal mi código?" y "¿me rechaza el proveedor?", y mientras estén juntas
# no se puede arreglar ninguna. Este archivo contesta la segunda sola. Si acá
# sale todo bien, el problema es nuestro; si acá falla, el proveedor te dice el
# motivo con todas las letras.
#
# 🔒 LA CLAVE NO SE ESCRIBE ACÁ NI SE IMPRIME. Sale del `.env`, que está en el
# `.gitignore`. El script se la pasa a `curl` y nunca la muestra en pantalla.
#
# QUÉ NECESITA en el `.env` de la raíz:
#   RESEND_API_KEY=re_...
#
# CÓMO SE CORRE, parado en la raíz del repo:
#
#   bash pruebas/probar-resend.sh

set -u

set -a
source .env
set +a

if [ -z "${RESEND_API_KEY:-}" ]
then
  echo "🔴 Falta RESEND_API_KEY en el .env — agregala y volvé a correr esto."
  exit 1
fi

# La casilla de pruebas sale del `.env` y NO tiene valor por defecto: es una
# dirección de una persona, y este repositorio es público.
DESTINO="${CORREO_DE_PRUEBA:-}"

if [ -z "$DESTINO" ]
then
  echo "🔴 Falta CORREO_DE_PRUEBA en el .env — es la casilla que recibe todo."
  exit 1
fi
AJENO="no-existe-a-proposito@example.com"
REMITENTE="CB Odontología <onboarding@resend.dev>"

# $1 = qué se prueba · $2 = qué tiene que dar · $3 = la dirección · $4 = el cuerpo
probar () {

  echo ""
  echo "───────────────────────────────────────────────────────────────"
  echo "▶ $1"
  echo "  esperado: $2"

  RESPUESTA=$(
    curl -s -w $'\n''HTTP %{http_code}' \
      -X POST "$3" \
      -H "Authorization: Bearer $RESEND_API_KEY" \
      -H 'Content-Type: application/json' \
      -d "$4"
  )

  echo "  obtenido:"
  echo "$RESPUESTA" | sed 's/^/    /'
}


# ── 1. Un correo suelto a la casilla dueña de la cuenta ──────────────────────
#
# Es el caso más simple que existe. Si esto falla, no hace falta seguir: o la
# clave está mal, o la cuenta no puede mandar nada.

probar \
  "1. Un correo, a la casilla dueña de la cuenta" \
  "200 con un id" \
  "https://api.resend.com/emails" \
  "{
     \"from\": \"$REMITENTE\",
     \"to\": [ \"$DESTINO\" ],
     \"subject\": \"Prueba 1 — un correo suelto\",
     \"text\": \"Si leés esto, la clave sirve y el proveedor entrega a esta casilla.\"
   }"


# ── 2. El MISMO correo, pero a una dirección que no es la de la cuenta ───────
#
# Acá se mide la restricción de la que hablamos: mientras el dominio no esté
# verificado, el proveedor sólo entrega a la casilla dueña. Si esto da 403, la
# regla está confirmada sobre tu cuenta y no sobre la documentación.

probar \
  "2. Un correo, a OTRA dirección (la restricción)" \
  "403 si la restricción existe · 200 si no" \
  "https://api.resend.com/emails" \
  "{
     \"from\": \"$REMITENTE\",
     \"to\": [ \"$AJENO\" ],
     \"subject\": \"Prueba 2 — dirección ajena\",
     \"text\": \"Esta no tendría que salir.\"
   }"


# ── 3. El LOTE, que es lo que usa el portero ─────────────────────────────────
#
# Dos mensajes distintos en un solo pedido, los dos a la casilla dueña. Es
# exactamente la forma que arma `_shared/avisos.ts`. Si 1 anda y 3 no, el
# problema es la dirección de lote o la forma del cuerpo, no la clave.

probar \
  "3. Un LOTE de dos mensajes, los dos a la casilla dueña" \
  "200 con dos ids" \
  "https://api.resend.com/emails/batch" \
  "[
     {
       \"from\": \"$REMITENTE\",
       \"to\": [ \"$DESTINO\" ],
       \"subject\": \"Prueba 3a — lote, primero\",
       \"text\": \"Primero del lote.\"
     },
     {
       \"from\": \"$REMITENTE\",
       \"to\": [ \"$DESTINO\" ],
       \"subject\": \"Prueba 3b — lote, segundo\",
       \"text\": \"Segundo del lote.\"
     }
   ]"

echo ""
echo "───────────────────────────────────────────────────────────────"
echo "Qué mirar: el número de HTTP de cada una y, si hay error, el texto"
echo "que devuelve el proveedor. Ahí está el motivo escrito."
echo ""
