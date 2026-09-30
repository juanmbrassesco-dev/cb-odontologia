// EL FLUJO DE RESERVA — qué pantalla está a la vista.
//
// QUÉ HACE ESTE ARCHIVO, en una línea: muestra una pantalla y esconde la que
// estaba.
//
// Las seis pantallas del flujo viven todas en `reservar.html` —decisión del
// 28-sep-2026— y se muestra una sola por vez. Este archivo es el único que
// toca eso: `entrar.js` y `quien.js` le piden una pantalla y no saben cómo la
// hace aparecer.
//
// ⏱ LO QUE TODAVÍA NO ESTÁ ACÁ, y es la mitad que falta: anotar cada paso en
// el HISTORIAL del navegador. Sin eso, el botón «atrás» del teléfono no vuelve
// un paso: se va de `reservar.html` a la landing, y como el turno a medio armar
// y la sesión viven en memoria, se pierden los dos. Es lo que sigue.


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
 */
function mostrarPantalla( cual ) {

  // Primero se esconde la vieja y recién después se muestra la nueva. Al revés
  // habría un instante con las dos puestas.
  pantallaALaVista.hidden = true;

  pantallaALaVista = document.querySelector( cual );

  pantallaALaVista.hidden = false;
}
