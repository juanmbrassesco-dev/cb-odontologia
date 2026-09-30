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

  const dato  = document.querySelector( '#profesional-dato' );
  const campo = document.querySelector( '#profesional-campo' );

  // ── UNO SOLO: no hay nada que preguntar ─────────────────────────────────
  //
  // Se muestra igual, como DATO y no como pregunta. El paciente tiene que
  // saber de quién es la agenda que está mirando; sin esta línea no se entera
  // hasta la pantalla de confirmar.
  if ( profesionales.length === 1 ) {

    profesionalElegido = profesionales[ 0 ].id;

    // `textContent` y no HTML pegado: es un nombre que escribió una persona en
    // la base. Misma defensa contra XSS que en `quien.js` y en `motivo.js`.
    dato.textContent =
      'Con ' + profesionales[ 0 ].nombre + ' ' + profesionales[ 0 ].apellido + '.';

    dato.hidden  = false;
    campo.hidden = true;

    return 'mostrar';
  }

  // ── DOS O MÁS: la pregunta ──────────────────────────────────────────────
  const desplegable = document.querySelector( '#profesional' );

  desplegable.textContent = '';

  for ( const profesional of profesionales ) {

    const opcion = document.createElement( 'option' );

    opcion.value = profesional.id;
    opcion.textContent = profesional.nombre + ' ' + profesional.apellido;

    desplegable.appendChild( opcion );
  }

  // El primero queda elegido: con el desplegable cerrado hay que mostrar algo,
  // y mostrar «Elegí una opción» obligaría a un toque que no decide nada
  // cuando el paciente no tiene preferencia.
  profesionalElegido = Number( desplegable.value );

  dato.hidden  = true;
  campo.hidden = false;

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
