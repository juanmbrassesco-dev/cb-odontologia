// LA PANTALLA ⑤ — «¿confirmamos?» — y la pantalla que da la noticia.
//
// QUÉ HACE ESTE ARCHIVO, en una línea: junta lo que eligieron las cuatro
// pantallas anteriores, le pide al portero que cree el turno, y según lo que
// conteste manda al paciente a una de cuatro noticias.
//
// LAS DOS PANTALLAS VIVEN EN EL MISMO ARCHIVO a propósito: la de mensaje no
// tiene vida propia —nadie llega ahí por su cuenta—, existe para contar cómo
// salió esto. Separarlas en dos archivos sería partir una sola conversación.
//
// 🔑 ACÁ NO SE VALIDA NADA QUE EL PORTERO NO VUELVA A VALIDAR. Todo lo que
// este archivo revisa antes de mandar —que haya cobertura elegida, que el
// texto no sea larguísimo— el portero lo revisa igual, porque cualquiera puede
// armar el pedido a mano sin pasar por esta pantalla. Lo de acá es COMODIDAD:
// le ahorra al paciente un viaje para que le digan algo que ya se sabía. La
// defensa está del otro lado.


const DIRECCION_DE_OBRAS_SOCIALES = SUPABASE_URL + '/functions/v1/obras-sociales';

const DIRECCION_DE_RESERVAR = SUPABASE_URL + '/functions/v1/reservar';


// ══════════════════════════════════════════════════════════════════════
// LA COBERTURA
// ══════════════════════════════════════════════════════════════════════

/**
 * Le pide al portero las obras sociales.
 *
 * Devuelve la lista, o `null` si el pedido falló. Quien llama decide qué
 * mostrar: este archivo no dibuja errores acá.
 *
 * SE PIDE AL CARGAR LA PÁGINA, como los tratamientos y por el mismo motivo:
 * son 71 filas y el endpoint es público. Pedirlas recién al llegar a esta
 * pantalla haría esperar al paciente con el turno ya elegido.
 */
async function pedirLasObrasSociales() {

  const respuesta = await fetch(
    DIRECCION_DE_OBRAS_SOCIALES,
    {
      headers: {
        'apikey': SUPABASE_CLAVE_PUBLICA
      }
    }
  );

  if ( !respuesta.ok ) {
    console.error( 'No se pudieron leer las obras sociales. Estado:', respuesta.status );
    return null;
  }

  return await respuesta.json();
}


/**
 * Cuenta cuántas filas tiene cada entidad.
 *
 * Hace falta para saber qué se agrupa y qué no: una entidad con un solo plan
 * no es un grupo, es una opción, y meterla en un `<optgroup>` de un solo hijo
 * agrega un título que no ordena nada.
 */
function cuantasPorEntidad( obras ) {

  const cuenta = {};

  for ( const obra of obras ) {
    cuenta[ obra.entidad ] = ( cuenta[ obra.entidad ] || 0 ) + 1;
  }

  return cuenta;
}


/**
 * Cuelga las 71 opciones del desplegable, agrupadas por entidad.
 *
 * 🔴 EL ORDEN NO SE TOCA ACÁ: viene resuelto por la columna `orden` de la base
 * —`Particular` primera— y las filas de una misma entidad ya llegan juntas.
 * Reordenar en el front sería tener la decisión del orden en dos lados.
 *
 * LOS NOMBRES VAN CON `textContent`, igual que en `quien.js` y en `motivo.js`:
 * son textos que escribió una persona en la base, y pegados como HTML un
 * nombre con `<script>` adentro se ejecutaría. Es la defensa contra XSS
 * (Cross-Site Scripting).
 */
function ponerLasCoberturas( obras ) {

  const desplegable = document.querySelector( '#cobertura' );
  const cuenta = cuantasPorEntidad( obras );

  // DOS VARIABLES PARA DOS COSAS DISTINTAS: el NOMBRE de la entidad que está
  // abierta —que es con lo que se compara— y el ELEMENTO al que hay que
  // colgarle los hijos. Con una sola, la comparación es entre un elemento y un
  // texto: nunca da verdadero, y se abre un grupo por fila.
  let entidadAbierta = null;
  let grupoAbierto = null;

  // Se recorre UNA vez y se va abriendo y cerrando el grupo, porque las filas
  // de una misma entidad ya llegan juntas. Agrupar primero en un objeto y
  // dibujar después rearma una estructura que la base ya entregó ordenada.
  for ( const obra of obras ) {

    const agrupa = cuenta[ obra.entidad ] > 1;

    const opcion = document.createElement( 'option' );

    opcion.value = obra.id;
    opcion.textContent = obra.nombre;

    if ( !agrupa ) {

      // Una entidad con un solo plan no es un grupo: es una opción suelta, y
      // cuelga del desplegable. Se cierra lo que hubiera abierto.
      entidadAbierta = null;
      grupoAbierto = null;

      desplegable.appendChild( opcion );
      continue;
    }

    if ( entidadAbierta !== obra.entidad ) {

      entidadAbierta = obra.entidad;

      grupoAbierto = document.createElement( 'optgroup' );

      // `label` es lo que el desplegable muestra como título del grupo, y va
      // como propiedad y no con `textContent`: un `<optgroup>` no tiene texto
      // propio, sus hijos son las opciones.
      grupoAbierto.label = obra.entidad;

      desplegable.appendChild( grupoAbierto );
    }

    grupoAbierto.appendChild( opcion );
  }
}


/**
 * Llena el desplegable de cobertura. Si el pedido falló, la pantalla se queda
 * con su única opción —«Elegí una opción»— y el paciente no puede confirmar:
 * la cobertura es obligatoria, así que un desplegable vacío frena la reserva
 * en vez de dejar pasar un turno sin ese dato.
 */
async function prepararLasCoberturas() {

  const obras = await pedirLasObrasSociales();

  if ( obras === null ) {
    return;
  }

  ponerLasCoberturas( obras );
}


prepararLasCoberturas();


// ══════════════════════════════════════════════════════════════════════
// LA TARJETA — EL RESUMEN DE LO QUE SE ESTÁ POR CREAR
// ══════════════════════════════════════════════════════════════════════

/**
 * Escribe en la tarjeta lo que eligieron las cuatro pantallas anteriores.
 *
 * La llama el «Continuar» de la ④, antes de mostrar esta pantalla: así el
 * paciente nunca ve la tarjeta vacía llenarse delante suyo.
 *
 * 🔑 NO PIDE NADA AL PORTERO. Todo lo que muestra ya está en memoria, elegido
 * por el paciente — y el único dato que no eligió él, la lista de coberturas,
 * se pidió al cargar la página. Por eso esta función es inmediata y no `async`.
 */
function prepararLaPantallaDeConfirmar() {

  // La hora sale del texto que mandó el portero —'…T15:30:00-03:00'— y NO se
  // convierte a fecha para volver a escribirla: el dato ya viene con el
  // desfase de acá, y pasarlo por `new Date()` es abrir la puerta a que se
  // corra una hora sin que nadie lo note. Es la misma decisión que en la
  // grilla de horas.
  const hora = horaElegida.slice( 11, 16 );

  document.querySelector( '#confirmar-cuando' ).textContent =
    diaEnPalabras( diaElegido ) + ', ' + hora;

  // «Consulta con Cecilia Duarte». El tratamiento es el que el paciente eligió
  // en la ③ y no «consulta»: eso último es lo que el turno ES para la agenda
  // —treinta minutos—, y acá la tarjeta está para que él reconozca lo que pidió.
  document.querySelector( '#confirmar-que' ).textContent =
    nombreDelTratamiento + ' con ' + nombreDelProfesional;

  document.querySelector( '#confirmar-quien' ).textContent =
    'Paciente: ' + pacienteElegido.nombre;
}


// ══════════════════════════════════════════════════════════════════════
// LA PANTALLA QUE DA LA NOTICIA
// ══════════════════════════════════════════════════════════════════════

/**
 * Muestra la pantalla de mensaje con un título, un cuerpo y UNA acción.
 *
 * `accion` es `{ rotulo, clase, hacer }`, o `null` para el único estado cuyo
 * botón no es nuestro: el de Google.
 *
 * 🔴 SE LLEGA CON `reemplazarPor` Y NO CON `avanzarA`, y es la diferencia que
 * evita un turno duplicado: la entrada del historial que ocupaba la pantalla ⑤
 * se PISA, así que el «atrás» del teléfono no devuelve al paciente a un
 * formulario lleno con un botón que vuelve a reservar.
 */
function darLaNoticia( { titulo, cuerpo, accion, accion2 } ) {

  document.querySelector( '#mensaje-titulo' ).textContent = titulo;
  document.querySelector( '#mensaje-cuerpo' ).textContent = cuerpo;

  const boton = document.querySelector( '#mensaje-accion' );
  const segundo = document.querySelector( '#mensaje-accion-2' );
  const hueco = document.querySelector( '#mensaje-google' );

  // EL SEGUNDO BOTÓN ES LA EXCEPCIÓN, NO LA REGLA: arranca escondido en cada
  // noticia y sólo lo enciende la que lo trae. Sin este apagado, el botón de
  // una noticia anterior quedaría puesto en la siguiente.
  segundo.hidden = true;

  if ( accion2 ) {
    segundo.hidden = false;
    segundo.textContent = accion2.rotulo;
    segundo.className = 'btn ' + accion2.clase;
    segundo.onclick = accion2.hacer;
  }

  if ( accion === null ) {

    // EL ESTADO DE LA SESIÓN VENCIDA. Su acción es el botón de Google, que lo
    // dibuja su biblioteca adentro del hueco: no hay uno nuestro que mostrar.
    // El porqué está escrito en `js/auth.js` — no hay función que llamar al
    // tocar un botón propio.
    boton.hidden = true;
    hueco.hidden = false;

    prepararElBoton( {
      contenedor: hueco,

      // Entró de nuevo: vuelve a la ⑤ con todo lo que había elegido, que sigue
      // en memoria. No se reserva solo — el paciente toca «Confirmar turno»,
      // que es la acción que él no llegó a completar.
      alEntrar: () => {
        reemplazarPor( '#paso-confirmar' );
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

    // El formato del botón lo dice el estado: el único que va con el
    // secundario es el del tope, porque «Ver mis turnos» no es lo que el sitio
    // empuja — es la salida de un camino que no se puede seguir.
    boton.className = 'btn ' + accion.clase;

    // `onclick` y no `addEventListener`: este botón cambia de trabajo con cada
    // noticia, y `onclick` REEMPLAZA al anterior. Con `addEventListener` se
    // irían apilando y el segundo mensaje de la sesión haría las dos cosas.
    boton.onclick = accion.hacer;
  }

  reemplazarPor( '#paso-mensaje' );
}


// Las cuatro noticias, con los textos tal cual se aprobaron en la pieza 5.
//
// 🔴 CUATRO CAUSAS DISTINTAS COMPARTEN EL TEXTO DE `falloGenerico` —alguien
// tomó la hora primero, se cumplieron las 12 horas de anticipación mientras
// elegía, Cecilia tapó ese día, se dio de baja el profesional—. Ninguna la
// puede arreglar el paciente sabiendo cuál fue, y todas se resuelven igual:
// volver a la agenda, que ya viene actualizada. Y NO se le dice que alguien
// llegó primero —decisión de Juan—: no hace falta revelarlo, irrita, y un
// paciente irritado abandona.
const NOTICIAS = {

  reservado: {
    titulo: 'Tu turno quedó reservado',
    cuerpo: 'Te mandamos un correo con los datos. Si no te llega, podés verlo '
      + 'y cancelarlo desde tus turnos, entrando con la misma cuenta.',
    accion: {
      rotulo: 'Volver al inicio',
      clase: 'btn-1',
      hacer: () => { window.location.href = 'index.html'; }
    },

    // 🔴 EL SEGUNDO BOTÓN, pedido por Juan el 1-oct-2026 probando el sitio
    // publicado: **reservó y no tenía cómo comprobar que el turno había
    // quedado.** El cuerpo de esta noticia ya le prometía que podía verlo
    // «desde tus turnos», y no había ninguna puerta.
    //
    // ⚠️ Va de secundario: la acción que el sitio empuja sigue siendo cerrar el
    // flujo. Ver los turnos es comprobar algo que ya se le dijo.
    accion2: {
      rotulo: 'Ir a mis turnos',
      clase: 'btn-2',
      hacer: () => { window.location.href = 'mis-turnos.html'; }
    }
  },

  // 🔑 EL ÚNICO QUE NO VUELVE A LA AGENDA, y por eso tiene noticia propia:
  // mandarlo a elegir otro horario es mandarlo a fallar de nuevo. El texto no
  // dice CUÁNTOS turnos, así que siguió siendo válido cuando el portero pasó
  // de dos a uno.
  limite: {
    titulo: 'Ya tenés un turno con este profesional',
    cuerpo: 'Para sacar otro, cancelá el que tenés y volvé a intentar.',
    accion: {
      rotulo: 'Ver mis turnos',
      clase: 'btn-2',
      hacer: () => { window.location.href = 'mis-turnos.html'; }
    }
  },

  sesionVencida: {
    titulo: 'Se cerró tu sesión',
    cuerpo: 'Entrá otra vez y terminá de reservar tu turno.',
    accion: null
  },

  falloGenerico: {
    titulo: 'Perdón, no pudimos reservar tu turno',
    cuerpo: 'Algo no salió como esperábamos. Intentalo de nuevo.',
    accion: {
      rotulo: 'Volver a la agenda',
      clase: 'btn-1',
      hacer: async () => {
        await recargarLaAgenda();
        reemplazarPor( '#paso-dia-hora' );
      }
    }
  }
};


// ══════════════════════════════════════════════════════════════════════
// RESERVAR
// ══════════════════════════════════════════════════════════════════════

/**
 * Arma el cuerpo del pedido.
 *
 * ⚠️ `paciente_id` O `paciente_nuevo`, UNO de los dos y nunca los dos: el
 * portero rechaza el pedido que trae los dos. Por eso la pantalla ② no guarda
 * dos campos sino UNO ya resuelto, y acá se desarma adentro del cuerpo con
 * `...`, que copia lo que haya.
 *
 * LA COBERTURA VIAJA COMO `id` y no como nombre, por lo mismo que el
 * tratamiento: el id no cambia si algún día se le corrige el texto a una obra
 * social.
 */
function cuerpoDelPedido() {

  const observaciones = document.querySelector( '#observaciones' ).value.trim();

  const cuerpo = {
    profesional: profesionalElegido,
    tratamiento: tratamientoElegido,
    obra_social: Number( document.querySelector( '#cobertura' ).value ),
    inicio: horaElegida,
    ...pacienteElegido.pedido
  };

  // El campo es opcional: vacío NO viaja. Mandar una cadena vacía guardaría
  // una observación que dice nada, y el portero tendría que distinguir «no
  // escribió» de «escribió nada».
  if ( observaciones !== '' ) {
    cuerpo.observaciones = observaciones;
  }

  return cuerpo;
}


/**
 * Qué noticia corresponde a lo que contestó el portero.
 *
 * 🔴 LOS DOS 409 SE DISTINGUEN POR `codigo` Y NO POR EL TEXTO DEL ERROR. El
 * portero manda `limite_alcanzado` o `hora_tomada`, y los dos van a lugares
 * distintos: el del tope a «mis turnos», el del choque de vuelta a la agenda.
 * Mirar el texto funcionaría hoy y mandaría al paciente al lugar equivocado el
 * día que alguien mejore una frase, sin que nada avise.
 *
 * EL 403 TAMBIÉN TIENE DOS CAUSAS —sesión no válida, y un `paciente_id` que no
 * es tuyo— y acá se tratan IGUAL, como sesión vencida. El segundo caso no lo
 * puede producir esta pantalla: el id sale de la lista que el portero mismo
 * devolvió para esta sesión. Si llegara, la salida honesta es la misma: volver
 * a entrar.
 */
function noticiaSegunLaRespuesta( estado, contenido ) {

  if ( estado === 201 ) {
    return NOTICIAS.reservado;
  }

  if ( estado === 409 && contenido.codigo === 'limite_alcanzado' ) {
    return NOTICIAS.limite;
  }

  if ( estado === 403 ) {
    return NOTICIAS.sesionVencida;
  }

  return NOTICIAS.falloGenerico;
}


/**
 * Le pide al portero que cree el turno y cuenta cómo salió.
 *
 * ⚠️ EL BOTÓN SE APAGA MIENTRAS VIAJA EL PEDIDO, y no es cosmética: dos clics
 * rápidos son dos pedidos, y el segundo crea un turno o rebota con el tope.
 * El ancho no se mueve al cambiar el rótulo porque el botón lleva las dos
 * palabras apiladas y la que no se ve sostiene la medida.
 */
async function reservar() {

  const boton = document.querySelector( '#confirmar-reservar' );
  const rotulo = boton.querySelector( 'span' );

  boton.disabled = true;
  rotulo.textContent = 'Reservando…';

  let estado = 0;
  let contenido = {};

  try {

    const respuesta = await fetch(
      DIRECCION_DE_RESERVAR,
      {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_CLAVE_PUBLICA,
          'Authorization': 'Bearer ' + tokenDeLaSesion(),
          'Content-Type': 'application/json'
        },

        // `JSON.stringify( … )` convierte el objeto en el texto que viaja. El
        // campo se llama `body` porque es lo que LLEVA el pedido, no lo que
        // vuelve.
        body: JSON.stringify( cuerpoDelPedido() )
      }
    );

    estado = respuesta.status;
    contenido = await respuesta.json();

  } catch ( falla ) {

    // ACÁ NO SE CAE NADA: un `fetch` sólo lanza si el pedido no llegó a salir
    // —sin red, o el servidor cortó—. Sin este `try` la pantalla se queda
    // muda, con el botón apagado y nada que leer, que es la peor de las
    // noticias posibles: ninguna.
    console.error( 'El pedido de reserva no llegó a salir:', falla );
  }

  if ( estado !== 201 ) {
    console.error( 'No se pudo reservar. Estado:', estado, contenido.error );
  }

  // El botón vuelve a su rótulo ANTES de cambiar de pantalla: si el paciente
  // vuelve a la ⑤ —porque se le venció la sesión y entró de nuevo—, lo tiene
  // que encontrar como estaba y no apagado y diciendo «Reservando…».
  boton.disabled = false;
  rotulo.textContent = 'Confirmar turno';

  darLaNoticia( noticiaSegunLaRespuesta( estado, contenido ) );
}


// EL «CONFIRMAR TURNO».
//
// La cobertura es el único control de esta pantalla, y su falta no avanza: el
// desplegable arranca en la opción vacía del HTML. Mismo criterio que las otras
// tres pantallas — se devuelve el foco a lo que falta tocar y no se inventa un
// aviso.
document.querySelector( '#confirmar-reservar' ).addEventListener( 'click', () => {

  const cobertura = document.querySelector( '#cobertura' );

  if ( cobertura.value === '' ) {
    cobertura.focus();
    return;
  }

  reservar();
} );


// EL «ATRÁS» DE ESTA PANTALLA. Igual que en la ③ y la ④: le pide al navegador
// que retroceda y el resto lo hace el oyente de `popstate` de `pasos.js`. UNA
// sola manera de volver.
document.querySelector( '#confirmar-atras' ).addEventListener( 'click', () => {
  history.back();
} );
