// LA PANTALLA ④ — «¿qué día y a qué hora?».
//
// QUÉ HACE HOY ESTE ARCHIVO, en una línea: resuelve CON QUIÉN es el turno.
//
// ⏱ LO QUE FALTA ACÁ ADENTRO: el almanaque y la grilla de horarios. Van a
// colgar del profesional elegido, porque `GET /horarios-disponibles` EXIGE uno
// —no acepta varios—: la agenda es por profesional por diseño del portero.


const DIRECCION_DE_PROFESIONALES = SUPABASE_URL + '/functions/v1/profesionales';


// CON QUIÉN ES EL TURNO. Guarda el `id`, que es lo que pide `POST /reservar`.
let profesionalElegido = null;


/**
 * Le pide al portero quiénes hacen ese tratamiento.
 *
 * Devuelve la lista, o `null` si el pedido falló. Quien llama decide qué
 * mostrar: este archivo no dibuja errores.
 */
async function pedirLosProfesionales( tratamiento ) {

  const respuesta = await fetch(
    DIRECCION_DE_PROFESIONALES + '?tratamiento=' + tratamiento,
    {
      headers: {
        'apikey': SUPABASE_CLAVE_PUBLICA
      }
    }
  );

  if ( !respuesta.ok ) {
    console.error( 'No se pudo leer los profesionales. Estado:', respuesta.status );
    return null;
  }

  return await respuesta.json();
}


/**
 * Arma la pantalla según CUÁNTOS profesionales hagan el tratamiento elegido.
 *
 * Devuelve 'mostrar' o 'falló', igual que `prepararLaPantallaDeQuien`: la
 * pantalla que llama decide si avanza o si avisa.
 *
 * 🔑 LA FORMA LA DECIDEN LOS DATOS, NO UNA BANDERA NUESTRA. El día que Cecilia
 * sume a alguien, el portero devuelve dos filas y la pregunta aparece sola. No
 * hay nada que acordarse de encender.
 *
 * RECIBE la lista en vez de pedirla, por el mismo motivo escrito en `quien.js`:
 * así se la puede correr con una lista inventada y mirar los dos casos sin
 * tocar la base. Hoy la base tiene UNA sola profesional, así que el caso de dos
 * no se podría probar de ninguna otra forma.
 */
function prepararLaPantallaDeDiaHora( profesionales ) {

  if ( profesionales === null || profesionales.length === 0 ) {
    return 'falló';
  }

  // EL DESPLEGABLE VA SIEMPRE, haya uno o haya cinco —decidido por Juan el
  // 30-sep-2026—. Con una sola profesional queda un desplegable de una opción,
  // que parece de más y no lo es: es el MISMO control en los dos casos, así
  // que el día que Cecilia sume a alguien no cambia la pantalla, cambia lo que
  // el control tiene adentro. Una pantalla que se transforma según los datos
  // es una pantalla que hay que probar dos veces y acordarse de las dos.
  const desplegable = document.querySelector( '#profesional' );

  desplegable.textContent = '';

  for ( const profesional of profesionales ) {

    const opcion = document.createElement( 'option' );

    opcion.value = profesional.id;

    // `textContent` y no HTML pegado: es un nombre que escribió una persona en
    // la base. Misma defensa contra XSS que en `quien.js` y en `motivo.js`.
    opcion.textContent = profesional.nombre + ' ' + profesional.apellido;

    desplegable.appendChild( opcion );
  }

  // El primero queda elegido: con el desplegable cerrado hay que mostrar algo,
  // y «Elegí una opción» obligaría a un toque que no decide nada cuando el
  // paciente no tiene preferencia — y con una sola profesional, a un toque que
  // no decide nada nunca.
  profesionalElegido = Number( desplegable.value );

  return 'mostrar';
}


// CAMBIAR DE PROFESIONAL CAMBIA LA AGENDA. Hoy sólo se guarda la elección;
// cuando el almanaque exista, acá es donde se vuelve a dibujar.
document.querySelector( '#profesional' ).addEventListener( 'change', ( evento ) => {
  profesionalElegido = Number( evento.target.value );
} );


document.querySelector( '#dia-hora-atras' ).addEventListener( 'click', () => {
  history.back();
} );
