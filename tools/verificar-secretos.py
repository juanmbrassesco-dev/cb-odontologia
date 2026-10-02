#!/usr/bin/env python3
"""Compara los secretos que el código ESPERA con los que están CARGADOS.

🔴 POR QUÉ EXISTE, y no es una idea de prolijidad: en este proyecto un secreto
que falta NO ROMPE NADA. El código lee el entorno con `delEntorno( … )`, que
devuelve `null` cuando no está, y cada lugar decide seguir sin ese dato. El
resultado es un correo más corto, un renglón que no aparece, un enlace que no
se escribe — y NINGÚN error en ningún registro.

Eso se llama FALLA ABIERTA (fail-open): ante la duda el sistema sigue, en vez
de frenar. La contraria es FALLA CERRADA (fail-closed), que rompe ruidosamente.
Acá la falla abierta está elegida a propósito —un turno se reserva igual aunque
el correo salga incompleto— y el precio es que nadie se entera.

EL 2-OCT-2026 SE ENCONTRARON DOS ASÍ, DE CASUALIDAD, buscando otra cosa:
`URL_MIS_TURNOS` —el correo de reserva no decía dónde cancelar— y
`WHATSAPP_DEL_CONSULTORIO` —el pie no ofrecía WhatsApp aunque el sitio sí—.
Los dos llevaban días puestos así, con el sitio publicado.

QUÉ HACE: lee las funciones, junta todos los nombres de entorno que piden, le
pregunta al CLI cuáles están cargados y los cruza.

QUÉ NO HACE, Y HAY QUE SABERLO: **no lee el VALOR de ningún secreto** —el CLI
sólo devuelve un hash— así que no puede decir si un valor está bien escrito.
Dice si está o no está. Un `URL_MIS_TURNOS` cargado con una dirección vieja
pasa este chequeo en verde.

CÓMO SE USA, desde la raíz del repo:

    python3 tools/verificar-secretos.py

Termina en 0 si no falta ninguno obligatorio, y en 1 si falta alguno — así
puede frenar algo automático el día que haga falta.
"""

import json
import re
import subprocess
import sys
from pathlib import Path


RAIZ = Path( __file__ ).resolve().parent.parent

FUNCIONES = RAIZ / "supabase" / "functions"


# LOS QUE PUEDEN FALTAR, CADA UNO CON SU MOTIVO ESCRITO.
#
# 🔑 ESTA LISTA ES LA MITAD ÚTIL DE LA HERRAMIENTA. Sin ella, el chequeo
# cantaría en rojo algo que está bien y se empezaría a ignorar — que es como
# muere un chequeo. Un secreto entra acá sólo con el motivo al lado.
PUEDEN_FALTAR = {
    "CORREO_REMITENTE":
        "sin él se usa `onboarding@resend.dev`, que es lo correcto hasta que el "
        "dominio esté verificado en Resend. Se carga con el mismo trámite de NIC.",

    "CORREO_DE_PRUEBA":
        "es el que REDIRIGE los tres avisos a la casilla de prueba. Hoy tiene que "
        "estar; se borra el día que el dominio quede verificado.",
}


# LOS QUE PONE SUPABASE SOLA. Aparecen en el entorno de toda función desplegada
# y no son nuestros: no se cargan a mano y no se pueden borrar.
LOS_PONE_SUPABASE = {
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_DB_URL",
    "SUPABASE_JWKS",
    "SUPABASE_PUBLISHABLE_KEYS",
    "SUPABASE_SECRET_KEYS",
}


# Las dos formas de pedir una variable de entorno que hay en este repo:
# `delEntorno( 'X' )`, que es nuestra, y `Deno.env.get( 'X' )`, que es la del
# lenguaje. Las comillas pueden ser simples o dobles.
PEDIDOS = re.compile(
    r"""(?:delEntorno|Deno\.env\.get)\s*\(\s*['"]([A-Z0-9_]+)['"]\s*\)"""
)

# 🔴 Y LA FORMA QUE ESTE CHEQUEO NO PUEDE RESOLVER: pedir el entorno con una
# VARIABLE adentro —`Deno.env.get( nombre )`—. Ahí el nombre se decide mientras
# el programa corre, así que leyendo el archivo no se sabe cuál es.
#
# No se ignora en silencio: se cuenta al final. Un chequeo que no avisa dónde
# es ciego vale menos que no tenerlo, porque deja creer que miró todo.
PEDIDOS_DINAMICOS = re.compile(
    r"""(?:delEntorno|Deno\.env\.get)\s*\(\s*(?!['"])([A-Za-z_][A-Za-z0-9_]*)\s*\)"""
)


def leer_el_codigo():
    """Devuelve (esperados, dinámicos): qué nombres pide el código y dónde no se puede saber."""

    esperados = {}
    dinamicos = []

    for archivo in sorted( FUNCIONES.rglob( "*.ts" ) ):

        texto = archivo.read_text( encoding = "utf-8" )
        donde = archivo.relative_to( RAIZ )

        for nombre in PEDIDOS.findall( texto ):
            esperados.setdefault( nombre, set() ).add( str( donde ) )

        renglones = texto.split( "\n" )

        for numero, contenido in enumerate( renglones, start = 1 ):

            encontrado = PEDIDOS_DINAMICOS.search( contenido )

            if not encontrado:
                continue

            # 🔴 NO TODA LECTURA DINÁMICA ES UN PUNTO CIEGO, y la primera
            # versión de este chequeo las cantaba todas. Las dos que hay en este
            # repo son la DEFINICIÓN de los lectores —`function delEntorno(
            # nombre: string ) { … Deno.env.get( nombre ) }`—: ahí el nombre es
            # el parámetro, y los usos de verdad, los que importan, están todos
            # escritos con el nombre a la vista.
            #
            # Señalarlas igual no es ser prudente: es gastar la atención de
            # quien lo lea en dos líneas que no se pueden arreglar, y enseñarle
            # a saltear la sección entera el día que aparezca una de verdad.
            if es_la_definicion_de_un_lector( renglones, numero, encontrado.group( 1 ) ):
                continue

            dinamicos.append( f"{ donde }:{ numero }" )

    return esperados, dinamicos


def es_la_definicion_de_un_lector( renglones, numero, argumento ):
    """Si esa lectura usa el PARÁMETRO de la función que la contiene.

    Se mira hacia arriba hasta diez renglones buscando una firma que reciba ese
    mismo nombre. Diez alcanza para cualquier lector de este repo y no tanto
    como para agarrar la función de al lado.
    """
    desde = max( 0, numero - 10 )

    firma = re.compile( r"function\s+\w+\s*\(\s*" + re.escape( argumento ) + r"\s*:" )

    return any( firma.search( renglon ) for renglon in renglones[ desde : numero ] )


def pedir_los_cargados():
    """Los nombres que el proyecto tiene cargados. `None` si el CLI no contestó."""

    try:
        salida = subprocess.run(
            [ "supabase", "secrets", "list", "--output", "json" ],
            capture_output = True,
            text = True,
            timeout = 60,
        )

    except FileNotFoundError:
        print( "✗ No está el CLI de Supabase. Se instala con: brew install supabase/tap/supabase" )
        return None

    except subprocess.TimeoutExpired:
        print( "✗ El CLI de Supabase no contestó en 60 segundos." )
        return None

    if salida.returncode != 0:
        print( "✗ El CLI de Supabase falló. Lo que dijo:" )
        print( "    " + ( salida.stderr.strip() or "nada" ) )
        print( "  Si es de sesión: supabase login · y después: supabase link" )
        return None

    try:
        datos = json.loads( salida.stdout )

    except json.JSONDecodeError:
        print( "✗ El CLI contestó algo que no es JSON. Primeros caracteres:" )
        print( "    " + salida.stdout[ : 120 ] )
        return None

    # ⚠️ EL CLI CONTESTA DE DOS FORMAS Y HAY QUE ACEPTAR LAS DOS: con
    # `--output json` devuelve la LISTA pelada, y sin el flag —cuando la salida
    # no es una terminal— devuelve `{ "secrets": [ … ] }`. La primera versión de
    # este archivo daba por sentada la segunda y se cayó con un `TypeError`.
    filas = datos[ "secrets" ] if isinstance( datos, dict ) else datos

    # 🔑 NO SE GUARDA NI SE IMPRIME NINGÚN VALOR, sólo los nombres. El CLI
    # devuelve el valor hasheado, pero un hash de un secreto sigue siendo algo
    # que no tiene por qué aparecer en la pantalla de nadie.
    return { secreto[ "name" ] for secreto in filas }


def main():

    esperados, dinamicos = leer_el_codigo()

    cargados = pedir_los_cargados()

    if cargados is None:
        return 1

    nuestros = { n: d for n, d in esperados.items() if n not in LOS_PONE_SUPABASE }

    faltan_de_verdad = []

    print( "LO QUE EL CÓDIGO PIDE" )
    print()

    for nombre in sorted( nuestros ):

        if nombre in cargados:
            print( f"  ✓ { nombre }" )
            continue

        if nombre in PUEDEN_FALTAR:
            print( f"  ⏱ { nombre } — no está, y está bien:" )
            print( f"      { PUEDEN_FALTAR[ nombre ] }" )
            continue

        faltan_de_verdad.append( nombre )

        print( f"  ✗ { nombre } — NO ESTÁ CARGADO" )
        print( f"      lo pide: { ', '.join( sorted( esperados[ nombre ] ) ) }" )
        print( f"      se carga con: supabase secrets set { nombre }=<EL VALOR>" )

    sobran = sorted( cargados - set( nuestros ) - LOS_PONE_SUPABASE )

    if sobran:
        print()
        print( "CARGADOS QUE NINGUNA FUNCIÓN PIDE" )
        print( "  (no es un error: puede ser de algo que se sacó, o de otra herramienta)" )
        print()

        for nombre in sobran:
            print( f"  ? { nombre }" )

    if dinamicos:
        print()
        print( "DONDE ESTE CHEQUEO ES CIEGO" )
        print( "  El nombre se arma mientras el programa corre, así que leyendo" )
        print( "  el archivo no se puede saber cuál es. Hay que mirarlo a mano:" )
        print()

        for donde in dinamicos:
            print( f"  · { donde }" )

    print()

    if faltan_de_verdad:
        print( f"✗ FALTAN { len( faltan_de_verdad ) }: { ', '.join( faltan_de_verdad ) }" )
        print( "  🔑 Ninguno de ésos va a dar error en ningún registro: el mensaje" )
        print( "     sale más corto y nadie se entera. Por eso existe este chequeo." )
        return 1

    print( "✓ No falta ningún secreto obligatorio." )
    print( "  ⚠ Lo que esto NO dice: si el VALOR de cada uno es el correcto." )
    return 0


if __name__ == "__main__":
    sys.exit( main() )
