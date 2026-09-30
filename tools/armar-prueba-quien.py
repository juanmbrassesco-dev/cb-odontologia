#!/usr/bin/env python3
"""Arma `pruebas/pantalla-quien.html`: los tres casos de la pantalla ②.

POR QUÉ EXISTE: la pantalla «¿para quién es el turno?» se comporta de tres
maneras según cuántos pacientes devuelva el portero para ese correo, y **un
correo real sólo puede mostrar uno de los tres**. Sin esto, dos de los tres
casos no se pueden mirar nunca — ni siquiera entrando con Google.

EL MARKUP NO SE COPIA: se recorta de `reservar.html` cada vez que se corre. Una
copia a mano se separaría del original el primer día que alguien lo toque, y
entonces la prueba estaría probando una pantalla que ya no existe.

CÓMO SE USA, desde la raíz del repo:

    python3 tools/armar-prueba-quien.py

Y después, con el servidor levantado:

    http://localhost:8000/pruebas/pantalla-quien.html?caso=ninguno
    http://localhost:8000/pruebas/pantalla-quien.html?caso=uno
    http://localhost:8000/pruebas/pantalla-quien.html?caso=varios
"""

from pathlib import Path


RAIZ = Path( __file__ ).resolve().parent.parent

PAGINA  = RAIZ / "reservar.html"
DESTINO = RAIZ / "pruebas" / "pantalla-quien.html"

# La prueba vive una carpeta más adentro que el sitio, así que sus rutas suben.
SUBIR = "../"


def recortar_la_pantalla():
    """La <section> de la pantalla ②, tal cual está en `reservar.html`.

    🔴 SE BUSCA POR EL `id`, NO POR LAS CLASES, y esto se arregló el
    30-sep-2026 después de que se rompiera. Antes buscaba la línea entera
    —`<section class="quien" id="paso-quien"`— y el día que la pantalla sumó
    una segunda clase (`class="paso quien"`) este archivo dejó de encontrarla.

    El `id` es lo que NO cambia: es el que `js/pasos.js` usa para mostrar y
    esconder los pasos, así que cambiarlo rompería el flujo entero y nadie lo
    va a tocar de pasada. Las clases son de presentación y se mueven solas.
    """
    pagina = PAGINA.read_text( encoding = "utf-8" )

    ancla    = pagina.index( 'id="paso-quien"' )
    arranque = pagina.rindex( "<section", 0, ancla )
    cierre   = pagina.index( "</section>", arranque ) + len( "</section>" )

    # Sin `hidden`: acá la pantalla es lo único que hay, y arranca a la vista.
    return pagina[ arranque : cierre ].replace( " hidden>", ">", 1 )


CUERPO_JS = r'''
  const CASOS = {
    ninguno: [],
    uno:     [ { id: 1, nombre: 'Laura', apellido: 'Giménez' } ],
    varios: [
      { id: 1, nombre: 'Laura', apellido: 'Giménez' },
      { id: 2, nombre: 'Sofía', apellido: 'Giménez' },
      { id: 3, nombre: 'Tomás', apellido: 'Giménez' }
    ]
  };

  const cual = new URLSearchParams( location.search ).get( 'caso' ) || 'varios';

  const queHacer = prepararLaPantallaDeQuien( CASOS[ cual ] );

  function seVe( selector ) {
    const elemento = document.querySelector( selector );
    if ( elemento === null ) {
      return 'NO EXISTE';
    }

    if ( getComputedStyle( elemento ).display === 'none' ) {
      return 'escondido';
    }

    return 'A LA VISTA';
  }

  // ── EL BUG QUE CAZÓ JUAN: escribir en el campo escondía los campos ────────
  //
  // Un <input type="text"> dispara 'change' al salir de él. Acá se simula ese
  // evento y se vuelve a mirar si los campos siguen puestos.
  let despuesDeEscribir = '(no aplica: los campos no estaban a la vista)';

  const campoNombre = document.querySelector( '#nombre' );

  if ( getComputedStyle( document.querySelector( '#quien-alta' ) ).display !== 'none' ) {
    campoNombre.value = 'Mariana';
    campoNombre.dispatchEvent( new Event( 'change', { bubbles: true } ) );
    despuesDeEscribir = seVe( '#quien-alta' );
  }

  document.querySelector( '#resultado' ).textContent =
    'CASO: ' + cual + '\n' +
    'resultado: ' + queHacer + '\n' +
    'titulo: ' + document.querySelector( '#quien-titulo' ).textContent + '\n' +
    'filas de personas: ' + document.querySelectorAll( '.opcion:not(.otra)' ).length + '\n' +
    'opcion «otra»: ' + seVe( '.opcion.otra' ) + '\n' +
    'campos nombre/apellido: ' + seVe( '#quien-alta' ) + '\n' +
    'campos DESPUÉS de escribir un nombre: ' + despuesDeEscribir + '\n' +
    '\n— con la LISTA, tocando «es para otra persona» —\n' +
    tocandoOtra() + '\n' +
    '\n[control del instrumento] con el oyente VIEJO puesto, escribir deja los campos: ' + control();


  // ── EL CAMINO COMPLETO CUANDO SÍ HAY LISTA ────────────────────────────────
  function tocandoOtra() {

    const otra = document.querySelector( '#quien-otra' );

    if ( getComputedStyle( otra.closest( '.opcion' ) ).display === 'none' ) {
      return '(no aplica: no hay lista en este caso)';
    }

    otra.checked = true;
    otra.dispatchEvent( new Event( 'change', { bubbles: true } ) );

    let salida = 'al tocarla, los campos quedan: ' + seVe( '#quien-alta' );

    const campo = document.querySelector( '#nombre' );
    campo.value = 'Mariana';
    campo.dispatchEvent( new Event( 'change', { bubbles: true } ) );

    salida += '\ny después de escribir: ' + seVe( '#quien-alta' );

    // Y si se arrepiente y elige a una persona de la lista, se cierran.
    const primera = document.querySelector( '.opcion:not(.otra) input' );

    if ( primera === null ) {
      salida += '\nal elegir a una persona de la lista: (no hay ninguna en este caso)';

    } else {
      primera.checked = true;
      primera.dispatchEvent( new Event( 'change', { bubbles: true } ) );

      salida += '\nal elegir a una persona de la lista: ' + seVe( '#quien-alta' );
    }

    return salida;
  }


  // ── ¿ESTA PRUEBA DETECTA EL BUG VIEJO? ────────────────────────────────────
  //
  // Una prueba que daría verde con el bug puesto no prueba nada. Acá se vuelve
  // a poner el oyente como estaba —afuera, corriendo siempre— y se escribe en
  // el campo. Si la prueba sirve, los campos TIENEN que esconderse.
  //
  // Va en el caso del que entra POR PRIMERA VEZ y no en el de la lista, y esa
  // es la corrección: con lista, «es para otra persona» queda elegida mientras
  // los campos están abiertos, así que el oyente viejo contestaba «sí» y no
  // escondía nada. El bug sólo se manifiesta donde esa opción no existe.
  function control() {

    if ( cual !== 'ninguno' ) {
      return '(el bug viejo sólo se manifiesta en el caso «ninguno»)';
    }

    document.querySelector( '#quien-opciones' ).addEventListener( 'change', () => {
      document.querySelector( '#quien-alta' ).hidden =
        !document.querySelector( '#quien-otra' ).checked;
    } );

    campoNombre.dispatchEvent( new Event( 'change', { bubbles: true } ) );

    const quedo = seVe( '#quien-alta' );

    if ( quedo === 'escondido' ) {
      return 'escondido — ✅ la prueba SÍ detecta el bug';
    }

    return quedo + ' — 🔴 la prueba NO detecta el bug: no sirve como control';
  }
'''


PAGINA_DE_PRUEBA = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Prueba · pantalla ¿para quién es el turno?</title>
  <link rel="stylesheet" href="{subir}css/styles.css">
  <style>
    /* ANDAMIAJE DE LA PRUEBA, no del sitio: el informe de abajo y el aviso de
       arriba no existen en `reservar.html`. */
    .aviso-de-prueba {{
      margin: 0;
      padding: 10px 16px;
      background: #33322F;
      color: #FFF;
      font: 500 13px/1.4 system-ui, sans-serif;
    }}
    .aviso-de-prueba a {{ color: #FFF; }}
    #resultado {{
      margin: 24px 16px;
      padding: 14px;
      border: 1px solid #CFCAC0;
      border-radius: 3px;
      background: #FFF;
      font: 13px/1.6 ui-monospace, Menlo, monospace;
      white-space: pre-wrap;
    }}
  </style>
</head>
<body>

<p class="aviso-de-prueba">PRUEBA — no es el sitio. Casos:
  <a href="?caso=ninguno">ninguno</a> ·
  <a href="?caso=uno">uno</a> ·
  <a href="?caso=varios">varios</a>
</p>

<main>
{pantalla}
</main>

<pre id="resultado"></pre>

<script src="{subir}js/quien.js"></script>
<script>{js}</script>
</body>
</html>
"""


def main():
    DESTINO.parent.mkdir( exist_ok = True )

    DESTINO.write_text(
        PAGINA_DE_PRUEBA.format(
            subir    = SUBIR,
            pantalla = recortar_la_pantalla(),
            js       = CUERPO_JS,
        ),
        encoding = "utf-8",
    )

    print( f"\u2713 {DESTINO.relative_to( RAIZ )}" )


if __name__ == "__main__":
    main()
