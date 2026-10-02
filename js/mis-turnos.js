// LA PANTALLA ⑥ — «mis turnos».
//
// QUÉ HACE ESTE ARCHIVO, en una línea: muestra los turnos que el paciente
// tiene por delante y lo deja cancelar uno.
//
// POR QUÉ ESTA PÁGINA ARRANCA PIDIENDO ENTRAR Y `reservar.html` TAMBIÉN: acá
// se llega desde el enlace del correo, sin sesión. Las dos páginas comparten
// `auth.js` —el que habla con Google— y cada una decide qué hacer después de
// un login que salió bien. Este archivo es ese «después» para esta página.
//
// 🔑 LO QUE SE MUESTRA NO ES «TODOS LOS TURNOS»: son los FUTUROS y ACTIVOS del
// correo con el que entró. Eso lo decide el portero, no esta pantalla — acá no
// se filtra nada, y por eso no hay forma de que la pantalla muestre de más.


const DIRECCION_DE_MIS_TURNOS = SUPABASE_URL + '/functions/v1/mis-turnos';

const DIRECCION_DE_CANCELAR = SUPABASE_URL + '/functions/v1/cancelar';


// EL TURNO QUE EL CARTEL ESTÁ PREGUNTANDO SI SE CANCELA, o `null` si el cartel
// está cerrado.
//
// 🔴 CANCELAR PREGUNTA ANTES, Y LA PREGUNTA LA HACE UN CARTEL FLOTANTE —lo
// pidió Juan el 2-oct-2026—. Hasta ese día preguntaba el mismo botón cambiando
// de rótulo a «¿Seguro? Sí, cancelar», y lo cortó: «no está bueno que se
// transforme el botón». El motivo es medible: si el MISMO PÍXEL cambia de
// significado, dos toques rápidos cancelan sin que nadie lea nada.
//
// Y la pregunta no es una formalidad: cancelar NO SE DESHACE. Libera el
// horario, que alguien puede tomar en el minuto siguiente, y dispara los tres
// correos.
//
// 🔑 SE GUARDA EL TURNO ENTERO Y NO SÓLO SU `id` porque el cartel tiene que
// DECIR CUÁL: flota encima de la lista y tapa la tarjeta que el paciente acaba
// de tocar.
let turnoDelCartel = null;


const cartel = document.querySelector( '#cartel-cancelar' );


// ══════════════════════════════════════════════════════════════════════
// PEDIR Y DIBUJAR
// ══════════════════════════════════════════════════════════════════════

/**
 * Le pide al portero los turnos del correo que entró.
 *
 * Devuelve la lista —que puede venir VACÍA, y eso no es un error: es el
 * paciente que no tiene turnos— o `null` si el pedido falló.
 */
async function pedirLosTurnos() {

  const respuesta = await fetch(
    DIRECCION_DE_MIS_TURNOS,
    {
      headers: {
        // La clave pública dice a qué proyecto le hablamos; el token dice
        // quién es el paciente. El portero saca el correo del token, nunca del
        // pedido — por eso acá no viaja ningún correo.
        'apikey': SUPABASE_CLAVE_PUBLICA,
        'Authorization': 'Bearer ' + tokenDeLaSesion()
      }
    }
  );

  if ( !respuesta.ok ) {
    console.error( 'No se pudieron leer los turnos. Estado:', respuesta.status );
    return null;
  }

  return await respuesta.json();
}


/**
 * Qué dice la segunda línea de la tarjeta: «Consulta con Cecilia Brassesco».
 *
 * 🔑 EL MOTIVO MANDA SOBRE EL TRATAMIENTO CUANDO SON DISTINTOS, y el portero ya
 * hizo esa comparación: manda `motivo: null` cuando coinciden. El caso que lo
 * pide es concreto — el paciente pidió ORTODONCIA, el sistema le agendó una
 * CONSULTA de 30, y si en su pantalla lee «consulta» a secas va a creer que se
 * equivocó y va a reservar de nuevo.
 */
function queDiceElTurno( turno ) {

  const nombre = turno.motivo ? turno.motivo.nombre : turno.tratamiento.nombre;

  return nombre + ' con ' + turno.profesional.nombre + ' ' + turno.profesional.apellido;
}


/**
 * Arma UNA tarjeta, con su botón de cancelar.
 *
 * 🔴 TODO LO QUE VIENE DE LA BASE SE ESCRIBE CON `textContent` y nunca pegando
 * HTML: son nombres que escribió una persona, y pegados como HTML un nombre
 * con `<script>` adentro se ejecutaría. Es la defensa contra XSS
 * (Cross-Site Scripting), la misma de las otras pantallas.
 *
 * LA CLASE `con-accion` NO ES DECORACIÓN: es la que pone la tarjeta EN FILA de
 * 768 para arriba —datos a la izquierda, botón a la derecha—. La tarjeta de la
 * pantalla ⑤ no la lleva porque no tiene botón.
 */
function tarjetaDeTurno( turno ) {

  const tarjeta = document.createElement( 'div' );
  tarjeta.className = 'turno con-accion';

  const datos = document.createElement( 'div' );
  datos.className = 'datos';

  const cuando = document.createElement( 'h3' );
  cuando.textContent = turnoEnPalabras( turno.inicio );

  const que = document.createElement( 'p' );
  que.className = 'que';
  que.textContent = queDiceElTurno( turno );

  const quien = document.createElement( 'p' );
  quien.className = 'quien';
  quien.textContent = 'Paciente: ' + turno.paciente.nombre + ' ' + turno.paciente.apellido;

  datos.append( cuando, que, quien );

  // LA COBERTURA SÓLO SI VINO. Es dato de control y no lo que el paciente vino
  // a mirar, así que va en el renglón más callado de la tarjeta — y si el turno
  // no la tiene, no se escribe un renglón que diga «Cobertura: ».
  if ( turno.obra_social ) {

    const cobertura = document.createElement( 'p' );
    cobertura.className = 'cobertura';
    cobertura.textContent = 'Cobertura: ' + turno.obra_social.nombre;

    datos.appendChild( cobertura );
  }

  tarjeta.append( datos, botonDeCancelar( turno ) );

  return tarjeta;
}


/** El botón de cancelar de una tarjeta. No cancela: abre el cartel. */
function botonDeCancelar( turno ) {

  const boton = document.createElement( 'button' );

  boton.type = 'button';
  boton.className = 'btn btn-2';
  boton.textContent = 'Cancelar turno';

  boton.addEventListener( 'click', () => {
    abrirElCartel( turno );
  } );

  return boton;
}


// ══════════════════════════════════════════════════════════════════════
// EL CARTEL QUE PREGUNTA
// ══════════════════════════════════════════════════════════════════════

/**
 * Abre el cartel preguntando por ESTE turno.
 *
 * Los dos renglones del medio se escriben con las MISMAS funciones que la
 * tarjeta —`turnoEnPalabras` y `queDiceElTurno`—, así que el cartel no puede
 * decir una hora distinta de la que el paciente leyó un segundo antes.
 *
 * 🔑 `showModal()` Y NO `show()`: la versión «modal» es la que trae el fondo
 * oscurecido, el foco atrapado adentro y la tecla Escape. Con `show()` el
 * cartel se dibuja igual y la página de atrás sigue respondiendo — que es
 * justo lo que no queremos mientras hay una pregunta sin contestar.
 */
function abrirElCartel( turno ) {

  turnoDelCartel = turno;

  document.querySelector( '#cartel-cuando' ).textContent = turnoEnPalabras( turno.inicio );
  document.querySelector( '#cartel-que' ).textContent = queDiceElTurno( turno );

  cartel.showModal();
}


// LAS TRES SALIDAS SIN CANCELAR PASAN POR `close()`: el botón «No», la tecla
// Escape y el toque en el fondo oscuro. Por eso el turno guardado se borra en
// el evento `close` y no adentro del botón — así no queda un turno «elegido»
// esperando a nadie si el cartel se cerró por cualquiera de los otros dos
// caminos.
cartel.addEventListener( 'close', () => {
  turnoDelCartel = null;
} );


document.querySelector( '#cartel-no' ).addEventListener( 'click', () => {
  cartel.close();
} );


document.querySelector( '#cartel-si' ).addEventListener( 'click', () => {

  // El turno se agarra ANTES de cerrar, porque cerrar es lo que lo borra.
  const turnoId = turnoDelCartel.id;

  cartel.close();

  cancelar( turnoId );
} );


// 🔑 TOCAR EL FONDO OSCURO CIERRA, y el navegador no lo hace solo: lo que
// cuenta ese toque como propio es el `<dialog>`, así que el clic llega con el
// cartel como destino. Un clic adentro llega con destino el botón o la caja —
// nunca el cartel—, y por eso la comparación alcanza para distinguirlos.
cartel.addEventListener( 'click', ( evento ) => {

  if ( evento.target === cartel ) {
    cartel.close();
  }
} );


/**
 * Dibuja la pantalla con lo que haya: la lista, o el aviso de que no hay nada.
 *
 * 🔑 LA LISTA VACÍA NO ES UN ERROR y por eso tiene su propio estado dibujado:
 * es el paciente que no tiene turnos. El que falló es `null`, que es otra cosa
 * y la maneja quien llama.
 */
function dibujarLosTurnos( turnos ) {

  const lista = document.querySelector( '#turnos-lista' );
  const vacio = document.querySelector( '#turnos-vacio' );

  lista.textContent = '';

  const hay = turnos.length > 0;

  lista.hidden = !hay;
  vacio.hidden = hay;

  for ( const turno of turnos ) {
    lista.appendChild( tarjetaDeTurno( turno ) );
  }
}


/**
 * Pide la lista y la muestra. Devuelve 'falló' si el portero no contestó.
 *
 * La usan las tres entradas a esta pantalla: el login, el «Ver mis turnos» de
 * una noticia, y la vuelta después de cancelar. Las tres necesitan lo mismo
 * —datos frescos— y por eso ninguna reusa lo que ya estaba en pantalla: lo que
 * se acaba de cancelar tiene que desaparecer de la lista.
 */
async function mostrarLosTurnos() {

  const turnos = await pedirLosTurnos();

  if ( turnos === null ) {
    return 'falló';
  }

  dibujarLosTurnos( turnos );

  return 'mostrar';
}


// ══════════════════════════════════════════════════════════════════════
// LA PANTALLA QUE DA LA NOTICIA
// ══════════════════════════════════════════════════════════════════════

/**
 * Muestra la pantalla de mensaje con un título, un cuerpo y UNA acción.
 *
 * Es la misma pieza 5 que usa `reservar.html`, con los mismos tres huecos. El
 * código está escrito dos veces —acá y en `confirmar.js`— y es a propósito:
 * son dos PÁGINAS distintas, así que compartirlo obligaría a cargar en cada
 * una el archivo entero de la otra. Lo que sí es una sola cosa es el DIBUJO,
 * que vive en la pieza `mensaje` de `css/styles.css`.
 */
function darLaNoticia( { titulo, cuerpo, accion } ) {

  document.querySelector( '#mensaje-titulo' ).textContent = titulo;
  document.querySelector( '#mensaje-cuerpo' ).textContent = cuerpo;

  const boton = document.querySelector( '#mensaje-accion' );
  const hueco = document.querySelector( '#mensaje-google' );

  if ( accion === null ) {

    // EL ESTADO DE LA SESIÓN VENCIDA. Su acción es el botón de Google, que lo
    // dibuja su biblioteca adentro del hueco: no hay uno nuestro que mostrar.
    boton.hidden = true;
    hueco.hidden = false;

    prepararElBoton( {
      contenedor: hueco,

      alEntrar: async () => {
        await mostrarLosTurnos();
        reemplazarPor( '#paso-turnos' );
      },

      alFallar: () => {
        document.querySelector( '#mensaje-cuerpo' ).textContent =
          'No pudimos entrar. Probá de nuevo, o escribinos por WhatsApp.';
      }
    } );

  } else {

    hueco.hidden = true;
    boton.hidden = false;

    boton.textContent = accion.rotulo;
    boton.className = 'btn ' + accion.clase;

    // `onclick` y no `addEventListener`: este botón cambia de trabajo con cada
    // noticia, y `onclick` REEMPLAZA al anterior en vez de apilarse.
    boton.onclick = accion.hacer;
  }

  reemplazarPor( '#paso-mensaje' );
}


/** Vuelve a la lista con los turnos recién pedidos. */
async function volverALaLista() {

  await mostrarLosTurnos();

  reemplazarPor( '#paso-turnos' );
}


const NOTICIAS = {

  // El texto aprobado en la pieza 5. Cierra sin pedir explicaciones y deja
  // abierta la puerta de volver, que es lo que el consultorio quiere.
  cancelado: {
    titulo: 'Tu turno quedó cancelado',
    cuerpo: 'Te mandamos un correo con el detalle. Podés reservar otro cuando quieras.',
    accion: {
      rotulo: 'Volver al inicio',
      clase: 'btn-1',
      hacer: () => { window.location.href = 'index.html'; }
    }
  },

  sesionVencida: {
    titulo: 'Se cerró tu sesión',
    cuerpo: 'Entrá otra vez para ver tus turnos.',
    accion: null
  },

  // TEXTO NUEVO —la pieza 5 tiene el error de RESERVAR y no el de cancelar—,
  // aprobado por Juan el 1-oct-2026.
  //
  // 🔴 NO DICE LA CAUSA, Y ESA ES LA DECISIÓN. La primera versión arriesgaba
  // «puede que ya esté cancelado, o que la hora haya pasado»: acierta casi
  // siempre y MIENTE cuando el fallo es de la base o de la red, que es una de
  // las cuatro causas. Un texto que explica algo que no ocurrió hace dudar de
  // lo que el paciente ve después en su lista.
  //
  // Es además el criterio que ya estaba aprobado para el fallo al RESERVAR
  // —cuatro causas, un solo texto, ninguna nombrada— y la acción es lo único
  // que el paciente puede hacer: volver a mirar cómo quedaron sus turnos.
  noSePudo: {
    titulo: 'No pudimos cancelar tu turno',
    cuerpo: 'Algo no salió como esperábamos. '
      + 'Mirá tus turnos para ver cómo quedaron.',
    accion: {
      rotulo: 'Ver mis turnos',
      clase: 'btn-1',
      hacer: volverALaLista
    }
  }
};


// ══════════════════════════════════════════════════════════════════════
// CANCELAR
// ══════════════════════════════════════════════════════════════════════

/**
 * Cancela un turno y cuenta cómo salió.
 *
 * 🔴 LOS DOS 403 SE DISTINGUEN POR `codigo` Y NO POR EL TEXTO: `sesion_invalida`
 * manda a entrar de nuevo, y `no_cancelable` a mirar la lista, que está vieja.
 * Son dos salidas opuestas, y hasta que el portero mandó el código lo único que
 * las separaba era la redacción del error.
 */
async function cancelar( turnoId ) {

  let estado = 0;
  let contenido = {};

  try {

    const respuesta = await fetch(
      DIRECCION_DE_CANCELAR,
      {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_CLAVE_PUBLICA,
          'Authorization': 'Bearer ' + tokenDeLaSesion(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify( { turno_id: turnoId } )
      }
    );

    estado = respuesta.status;
    contenido = await respuesta.json();

  } catch ( falla ) {

    // Un `fetch` sólo lanza si el pedido no llegó a salir —sin red, o el
    // servidor cortó—. Sin este `try` la pantalla se queda muda, que es la peor
    // noticia posible: ninguna.
    console.error( 'El pedido de cancelación no llegó a salir:', falla );
  }

  if ( estado === 200 ) {
    darLaNoticia( NOTICIAS.cancelado );
    return;
  }

  console.error( 'No se pudo cancelar. Estado:', estado, contenido.error );

  if ( estado === 403 && contenido.codigo === 'sesion_invalida' ) {
    darLaNoticia( NOTICIAS.sesionVencida );
    return;
  }

  darLaNoticia( NOTICIAS.noSePudo );
}


// ══════════════════════════════════════════════════════════════════════
// EL ARRANQUE
// ══════════════════════════════════════════════════════════════════════

// Es el pegamento de esta página, el mismo papel que `entrar.js` cumple en
// `reservar.html`: `auth.js` sabe hablar con Google y no sabe qué pantalla lo
// llamó; acá se le dice dónde dibujar el botón y qué hacer cuando entró.
const aviso = document.querySelector( '#aviso-entrar' );


// 🔴 SI YA ENTRÓ EN ESTA PESTAÑA, LA LISTA SALE DIRECTO. Es el arreglo del
// error que encontró Juan el 1-oct-2026 probando el sitio publicado: elegía
// «ver mis turnos» recién entrado y esta página le pedía entrar otra vez.
// **Para el paciente no hay dos páginas: hay un sitio donde ya se identificó.**
//
// 🔑 SE CAMBIA DE PANTALLA ANTES DE QUE LLEGUEN LOS DATOS, a propósito: si se
// esperara la respuesta, el paciente vería asomar la pantalla de entrar y
// desaparecer. Lo que ve mientras tanto es el título «Mis turnos» y nada más
// —la lista y el aviso de vacío arrancan los dos escondidos—, que es la
// verdad: todavía no sabemos cuántos turnos tiene.
if ( haySesion() ) {

  reemplazarPor( '#paso-turnos' );

  mostrarLosTurnos().then( ( queHacer ) => {

    if ( queHacer === 'falló' ) {
      darLaNoticia( NOTICIAS.sesionVencida );
    }
  } );
}


prepararElBoton( {

  contenedor: document.querySelector( '#boton-google' ),

  alEntrar: async () => {

    if ( await mostrarLosTurnos() === 'falló' ) {
      aviso.hidden = false;
      aviso.textContent =
        'Entraste, pero no pudimos leer tus turnos. Probá de nuevo, o escribinos por WhatsApp.';
      return;
    }

    // `reemplazarPor` y no `avanzarA`: volver al login después de haber entrado
    // no tiene sentido, así que esa entrada no queda en el historial.
    reemplazarPor( '#paso-turnos' );
  },

  alFallar: () => {
    aviso.hidden = false;
    aviso.textContent = 'No pudimos entrar. Probá de nuevo, o escribinos por WhatsApp.';
  }

} );
