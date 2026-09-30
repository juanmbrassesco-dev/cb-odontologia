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


prepararElBoton( {

  contenedor: contenedorDelBoton,

  // ENTRÓ. De acá en adelante la pantalla de entrar ya no sirve para nada:
  // lo que sigue es preguntar para quién es el turno.
  alEntrar: async () => {

    const queHacer = prepararLaPantallaDeQuien( await pedirLosPacientes() );

    if ( queHacer === 'falló' ) {
      avisar( 'Entraste, pero no pudimos leer tus datos. Probá de nuevo, o escribinos por WhatsApp.' );
      return;
    }

    reemplazarPor( '#paso-quien' );
  },

  alFallar: () => {
    avisar( 'No pudimos entrar. Probá de nuevo, o escribinos por WhatsApp.' );
  }

} );
