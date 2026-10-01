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


// 🔴 SI YA ENTRÓ, NO SE LE PIDE ENTRAR DE NUEVO. La sesión sobrevive al salto
// entre las dos páginas del sitio desde el 1-oct-2026, así que el que vuelve
// acá desde «mis turnos» —o el que recarga— se saltea esta pantalla.
//
// `reemplazarPor` y no `avanzarA`: la pantalla de entrar no tiene por qué
// quedar en el historial de alguien que ya entró.
if ( haySesion() ) {
  reemplazarPor( '#paso-que-hacer' );
}


prepararElBoton( {

  contenedor: contenedorDelBoton,

  // ENTRÓ. De acá en adelante la pantalla de entrar ya no sirve para nada:
  // lo que sigue es preguntar A QUÉ VINO.
  //
  // 🔴 ANTES ESTO LLEVABA DERECHO A «¿para quién es el turno?», y por eso el
  // que entraba para mirar un turno suyo quedaba sin salida —lo encontró Juan
  // el 1-oct-2026 probando el sitio publicado—. La lista de pacientes ya no se
  // pide acá: la pide la pantalla nueva, y sólo si eligen reservar. **El que
  // viene a ver sus turnos ya no espera un pedido que no le sirve.**
  alEntrar: () => {
    reemplazarPor( '#paso-que-hacer' );
  },

  alFallar: () => {
    avisar( 'No pudimos entrar. Probá de nuevo, o escribinos por WhatsApp.' );
  }

} );
