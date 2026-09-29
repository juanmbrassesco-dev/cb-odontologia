// La pantalla «entrar» — el pegamento entre `auth.js` y este HTML.
//
// `auth.js` sabe hablar con Google y con Supabase, y NO sabe qué pantalla lo
// llamó. Este archivo es el que sabe: le dice dónde dibujar el botón y qué
// hacer cuando el paciente entró.


const contenedorDelBoton = document.querySelector( '#boton-google' );
const aviso = document.querySelector( '#aviso-entrar' );


prepararElBoton( {

  contenedor: contenedorDelBoton,

  // ⏱ PROVISORIO — hasta que exista el paso ② («¿para quién es el turno?»).
  // Hoy la rebanada termina acá: se prueba que el recorrido completo anda
  // —Google firma, Supabase canjea, la página se entera— y lo que sigue se
  // construye sobre esto.
  alEntrar: () => {
    aviso.hidden = false;
    aviso.textContent = 'Entraste. El paso siguiente todavía no está construido.';
  },

  alFallar: () => {
    aviso.hidden = false;
    aviso.textContent =
      'No pudimos entrar. Probá de nuevo, o escribinos por WhatsApp.';
  }

} );
