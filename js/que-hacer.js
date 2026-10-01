// LA PANTALLA ①.b — «¿qué querés hacer?».
//
// QUÉ HACE ESTE ARCHIVO, en una línea: decide si el que entró viene a reservar
// o a mirar los turnos que ya tiene.
//
// POR QUÉ EXISTE. Hasta el 1-oct-2026 entrar llevaba derecho a «¿para quién es
// el turno?», y **el que había entrado para ver un turno suyo no tenía adónde
// ir**: la única puerta a «mis turnos» era el enlace del correo. Lo encontró
// Juan probando el sitio publicado — reservó, y no pudo confirmar que el turno
// había quedado.
//
// 🔑 ES UNA PANTALLA SIN DATOS: no le pide nada al portero y no guarda nada.
// Sólo elige por cuál de los dos caminos sigue el flujo, así que es el archivo
// más corto del sitio y no tiene por qué crecer.


// EL «CONTINUAR» DE ESTA PANTALLA.
//
// ⚠️ LOS DOS CAMINOS NO SON SIMÉTRICOS Y CONVIENE SABERLO: reservar es un paso
// MÁS de este mismo flujo —se avanza y el «atrás» del teléfono devuelve acá—,
// mientras que «mis turnos» es OTRA PÁGINA. Al irse, la sesión de ésta se
// pierde: `mis-turnos.html` va a pedir entrar de nuevo.
//
// Eso no es un descuido: el token vive en memoria y en ningún lado más —no se
// guarda en el navegador—, que es la decisión de seguridad que este proyecto ya
// tomó. El costo es un toque más en la pantalla de Google, que normalmente ya
// tiene la cuenta elegida.
document.querySelector( '#que-hacer-continuar' ).addEventListener( 'click', async () => {

  const reservar = document.querySelector( '#que-reservar' ).checked;

  if ( !reservar ) {
    window.location.href = 'mis-turnos.html';
    return;
  }

  // PREPARA LA SIGUIENTE ANTES DE MOSTRARLA, que es el orden que usan todas
  // las pantallas de este flujo: primero se le pide al portero lo que la ②
  // necesita, y recién si eso salió bien se avanza.
  const queHacer = prepararLaPantallaDeQuien( await pedirLosPacientes() );

  if ( queHacer === 'falló' ) {
    console.error( 'No se pudo leer la lista de pacientes.' );
    return;
  }

  avanzarA( '#paso-quien' );
} );
