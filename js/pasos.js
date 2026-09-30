// EL FLUJO DE RESERVA — qué pantalla está a la vista.
//
// QUÉ HACE ESTE ARCHIVO, en una línea: muestra una pantalla, esconde la que
// estaba, y le anota al navegador que hubo un cambio de paso.
//
// Las seis pantallas del flujo viven todas en `reservar.html` —decisión del
// 28-sep-2026— y se muestra una sola por vez. Este archivo es el único que
// toca eso: `entrar.js` y `quien.js` le piden una pantalla y no saben cómo la
// hace aparecer.
//
// POR QUÉ EL HISTORIAL ES PROBLEMA NUESTRO Y NO DEL NAVEGADOR. Para el
// navegador `reservar.html` es UNA hoja, porque las seis pantallas son una
// sola página. Sin lo de abajo, su botón «atrás» no vuelve un paso: se va de
// `reservar.html` a la landing, y como el turno a medio armar y la sesión
// viven en memoria, se pierden los dos.
//
// LA URL NO CAMBIA en ningún momento. Se podría hacer que cambie, y no se
// hace: obligaría al servidor a contestar una dirección por paso. Lo que se
// guarda es sólo el nombre de la pantalla.


// LA PANTALLA QUE ESTÁ A LA VISTA AHORA. Arranca siendo la de entrar, que es
// la única que en el HTML no lleva `hidden`.
//
// Se guarda en vez de buscarla cada vez porque para esconder a la anterior hay
// que saber CUÁL era. La alternativa —recorrer las seis y esconderlas todas—
// hace el mismo trabajo seis veces para lograr lo mismo.
let pantallaALaVista = document.querySelector( '#paso-entrar' );


/**
 * Muestra la pantalla que se le pide y esconde la que estaba.
 *
 * `cual` es el id con el `#` adelante, como en CSS: '#paso-quien'.
 *
 * NO TOCA EL HISTORIAL: hace sólo el cambio visible. Por eso la usan las dos
 * funciones de abajo y también el aviso del «atrás», que necesita cambiar de
 * pantalla SIN anotar nada.
 */
function mostrarPantalla( cual ) {

  // Primero se esconde la vieja y recién después se muestra la nueva. Al revés
  // habría un instante con las dos puestas.
  pantallaALaVista.hidden = true;

  pantallaALaVista = document.querySelector( cual );

  pantallaALaVista.hidden = false;
}


/**
 * AVANZA UN PASO: cambia lo que se ve y le APILA al navegador una entrada
 * nueva, para que su «atrás» tenga a dónde volver.
 *
 * La usan las pantallas del flujo que todavía no están escritas —③ ④ ⑤—. Hoy
 * no tiene quien la llame; se escribe junto con su pareja porque las dos son
 * la misma decisión.
 */
function avanzarA( cual ) {

  mostrarPantalla( cual );

  // El objeto es NUESTRO y lo elegimos nosotros: es lo que el navegador nos va
  // a devolver cuando vuelva a esta entrada. Guardamos lo mínimo que hace
  // falta para rearmar la pantalla.
  //
  // El segundo argumento es un resto histórico que los navegadores ignoran.
  history.pushState( { pantalla: cual }, '' );
}


/**
 * REEMPLAZA EL PASO ACTUAL: cambia lo que se ve y PISA la entrada del
 * historial en vez de apilar una nueva.
 *
 * Es lo que usa la pantalla «entrar» al terminar: volver al login después de
 * haber entrado no tiene sentido, así que esa entrada no queda en el
 * historial. Consecuencia buscada: desde la pantalla ② el «atrás» sale al
 * sitio.
 */
function reemplazarPor( cual ) {

  mostrarPantalla( cual );

  history.replaceState( { pantalla: cual }, '' );
}


// EL «ATRÁS» DEL NAVEGADOR —el de la barra y el del teléfono— NO ES NUESTRO y
// no se puede interceptar. Lo único que se puede hacer es pedirle al navegador
// que nos AVISE cuando alguien lo apriete, y eso es `popstate`.
window.addEventListener( 'popstate', ( evento ) => {

  // `evento.state` es el objeto que guardamos al apilar la entrada a la que el
  // navegador acaba de volver. Si viene vacío, esa entrada no es nuestra y no
  // hay pantalla que rearmar.
  if ( evento.state === null ) {
    return;
  }

  // `mostrarPantalla` y no `avanzarA`: acá el historial ya se movió solo. Si
  // apiláramos una entrada, el «atrás» crearía pasos en vez de deshacerlos.
  mostrarPantalla( evento.state.pantalla );
} );
