// La pantalla «entrar» — el pegamento entre `auth.js` y este HTML.
//
// `auth.js` sabe hablar con Google y con Supabase, y NO sabe qué pantalla lo
// llamó. Este archivo es el que sabe: le dice dónde dibujar el botón y qué
// hacer cuando el paciente entró.


const contenedorDelBoton = document.querySelector( '#boton-google' );
const aviso = document.querySelector( '#aviso-entrar' );


/** Escribe un aviso debajo del botón. Es lo único que esta pantalla dibuja. */
function avisar( texto ) {
  aviso.hidden = false;
  aviso.textContent = texto;
}


/** Lo que pasa cuando hay sesión: se arma la ② y se muestra. */
async function seguirConLaReserva() {

  if ( prepararLaPantallaDeQuien( await pedirLosPacientes() ) === 'falló' ) {
    avisar( 'Entraste, pero no pudimos leer tus datos. Probá de nuevo, o escribinos por WhatsApp.' );
    return;
  }

  reemplazarPor( '#paso-quien' );
}


// 🔴 SI YA ENTRÓ, NO SE LE PIDE ENTRAR DE NUEVO. La sesión sobrevive al salto
// entre las dos páginas del sitio, así que el que vuelve acá desde «mis
// turnos» —o el que recarga— se saltea esta pantalla.
if ( haySesion() ) {
  seguirConLaReserva();
}


prepararElBoton( {

  contenedor: contenedorDelBoton,

  // ENTRÓ. De acá en adelante la pantalla de entrar ya no sirve para nada:
  // lo que sigue es preguntar para quién es el turno.
  //
  // ⚠️ ACÁ NO SE PREGUNTA «¿qué querés hacer?», y es una decisión que se tomó y
  // se dio vuelta el mismo día: esta página es SÓLO para reservar. **La puerta
  // a «mis turnos» vive en el encabezado del sitio, antes de entrar**, porque
  // obligar a identificarse para recién ahí ofrecer la opción es al revés de
  // como lo busca una persona. *Lo levantó Juan el 1-oct-2026.*
  alEntrar: seguirConLaReserva,

  alFallar: () => {
    avisar( 'No pudimos entrar. Probá de nuevo, o escribinos por WhatsApp.' );
  }

} );
