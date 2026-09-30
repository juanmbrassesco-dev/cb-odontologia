// LA PANTALLA ② — «¿para quién es el turno?».
//
// QUÉ HACE ESTE ARCHIVO, en una línea: le pregunta al portero qué pacientes
// figuran bajo el correo del que entró, y arma la pantalla según cuántos sean.
//
// LOS TRES CASOS QUE PUEDE CONTESTAR EL PORTERO, y cada uno es otra pantalla:
//
//   · NINGUNO → el que reserva por primera vez. No hay lista: van los dos
//     campos solos, y la pregunta cambia a «¿Cómo te llamás?».
//   · UNO     → no se muestra nada. No hay nada que preguntar, así que el paso
//     se saltea y se avisa hacia afuera quién es.
//   · VARIOS  → la lista, que es el caso que se maquetó.


// De acá salen los pacientes. `SUPABASE_URL` y `SUPABASE_CLAVE_PUBLICA` las
// declara `js/auth.js`, que se carga antes.
const DIRECCION_DE_MIS_PACIENTES = SUPABASE_URL + '/functions/v1/mis-pacientes';


/**
 * Le pide al portero la lista de pacientes del correo que entró.
 *
 * Devuelve la lista, o `null` si el pedido falló. Quien llama decide qué
 * mostrar: este archivo no dibuja errores.
 */
async function pedirLosPacientes() {

  const respuesta = await fetch(
    DIRECCION_DE_MIS_PACIENTES,
    {
      headers: {
        // La clave pública dice a qué proyecto de Supabase le hablamos; el
        // token dice quién es el paciente. El portero saca el correo del
        // token, nunca del pedido — por eso acá no viaja ningún correo.
        'apikey': SUPABASE_CLAVE_PUBLICA,
        'Authorization': 'Bearer ' + tokenDeLaSesion()
      }
    }
  );

  if ( !respuesta.ok ) {
    console.error( 'No se pudo leer la lista. Estado:', respuesta.status );
    return null;
  }

  return await respuesta.json();
}


/**
 * Arma UNA fila de la lista: el <label> con su radio adentro.
 *
 * 🔴 EL NOMBRE SE ESCRIBE CON `textContent` Y NO PEGANDO HTML, y no es estilo:
 * es la defensa contra XSS (Cross-Site Scripting). Un nombre de la base es
 * texto que escribió una persona; pegado como HTML, un nombre que trajera
 * `<script>` se ejecutaría en la página. `textContent` lo pone como letras y
 * nunca como código.
 */
function filaDePaciente( paciente, esLaPrimera ) {

  const fila = document.createElement( 'label' );
  fila.className = 'opcion';

  const marca = document.createElement( 'input' );
  marca.type  = 'radio';
  marca.name  = 'paciente';
  marca.value = paciente.id;

  // La primera viene elegida, como en el maquetado aprobado. Con un solo
  // paciente eso es lo que convierte la pantalla en una confirmación: no hay
  // nada que decidir, sólo seguir.
  marca.checked = esLaPrimera;

  const nombre = document.createElement( 'span' );
  nombre.className   = 'nombre';
  nombre.textContent = paciente.nombre + ' ' + paciente.apellido;

  fila.append( marca, nombre );

  return fila;
}


/**
 * Deja la pantalla ② lista para mostrarse, y dice qué pasó.
 *
 * Contesta una de estas tres palabras, y quien llama hace algo distinto con
 * cada una. Son tres y no un `true`/`false` porque «no hay que mostrarla»
 * significa dos cosas opuestas: seguir de largo, o frenar y avisar.
 *
 *   'mostrar' → hay algo para preguntar: la lista, o los campos del que entra
 *               por primera vez.
 *   'falló'   → no se pudo leer la lista. Hay que avisarle a la persona.
 *
 * 🔴 YA NO EXISTE UN CASO «SALTEAR», y hasta el 29-sep-2026 existía: con un
 * solo paciente la pantalla no se mostraba, citando el maquetado —«mostrar una
 * lista de un elemento es pedirle a alguien que elija entre una cosa»—.
 *
 * Lo abrió Juan queriendo probar justamente ese caso, y el argumento se cae
 * solo: la lista de un paciente NO tiene un elemento, tiene dos —esa persona y
 * «es para otra persona»—. Salteándola, la madre que se registró sola y ahora
 * quiere anotar a su hijo **no tiene ninguna otra pantalla donde hacerlo**.
 *
 * El costo que se paga, y se paga a conciencia: el que reserva para sí mismo
 * toca «Continuar» una vez más. No elige nada — su fila viene ya marcada.
 *
 * RECIBE la lista en vez de pedirla, y eso no es un detalle: así se la puede
 * correr con una lista inventada y mirar los tres casos sin entrar con Google
 * ni tocar la base. Es lo que hace `pruebas/pantalla-quien.html`.
 */
function prepararLaPantallaDeQuien( pacientes ) {

  if ( pacientes === null ) {
    return 'falló';
  }

  const opciones = document.querySelector( '#quien-opciones' );
  const otra     = document.querySelector( '#quien-otra' );
  const alta     = document.querySelector( '#quien-alta' );

  // ── EL QUE ENTRA POR PRIMERA VEZ ──────────────────────────────────────────
  //
  // Sin lista y sin la opción «es para otra persona»: no hay ninguna otra. Los
  // campos quedan a la vista desde el arranque, y sin la clase que les dibuja
  // el filo y la sangría — ese filo existe para mostrar que la caja COLGABA de
  // una opción de la lista, y acá no hay lista de la que colgar.
  if ( pacientes.length === 0 ) {

    document.querySelector( '#quien-titulo' ).textContent = '¿Cómo te llamás?';

    document.querySelector( '#quien-ayuda' ).textContent =
      'Es la primera vez que reservás con este correo. Con esto queda tu turno a tu nombre.';

    otra.closest( '.opcion' ).hidden = true;

    alta.classList.remove( 'alta-abierta' );
    alta.hidden = false;

    document.querySelector( '#quien-alta-ayuda' ).hidden = true;

    return 'mostrar';
  }

  // ── HAY GENTE: LA LISTA ───────────────────────────────────────────────────
  //
  // La ayuda del maquetado dice «con tu correo figura más de una persona», y
  // con una sola eso es falso. Un texto que afirma algo que la pantalla
  // desmiente es peor que no tener texto.
  if ( pacientes.length === 1 ) {
    document.querySelector( '#quien-ayuda' ).textContent =
      'Si el turno es para otra persona, agregala acá abajo.';
  }

  // Las filas van ANTES de «Es para otra persona», que ya está escrita en el
  // HTML y tiene que quedar última: es una salida, no una persona.
  for ( const paciente of pacientes ) {

    const esLaPrimera = paciente === pacientes[ 0 ];

    opciones.insertBefore(
      filaDePaciente( paciente, esLaPrimera ),
      otra.closest( '.opcion' )
    );
  }

  // LOS CAMPOS SE ABREN Y SE CIERRAN CON LA ELECCIÓN.
  //
  // El evento es 'change' y no 'click': en un grupo de radios, elegir uno
  // APAGA al que estaba, y ese otro no recibe ningún clic. Con 'click' los
  // campos se abrirían y no se cerrarían nunca más.
  //
  // El oyente va sobre la lista entera y no sobre cada radio: el evento sube
  // desde el que se tocó hasta ella, y ahí se pregunta cuál quedó elegido.
  //
  // 🔴 Y VIVE ACÁ ADENTRO, NO AL CARGAR EL ARCHIVO — lo cazó Juan el
  // 29-sep-2026: «me escondió la barra para poner el nombre». Puesto afuera,
  // corría también para el que entra por primera vez, y ahí hace daño: los dos
  // campos de texto están DENTRO de `#quien-opciones`, un campo de texto
  // dispara 'change' al salir de él, el evento subía hasta acá, y como en ese
  // caso «es para otra persona» ni siquiera existe, la respuesta era «no está
  // elegida» y los campos se escondían mientras escribía.
  //
  // 🔑 Sin lista no hay nada que abrir ni cerrar. El oyente sólo tiene sentido
  // donde hay una lista de la que la caja cuelgue.
  opciones.addEventListener( 'change', () => {
    alta.hidden = !otra.checked;
  } );

  return 'mostrar';
}
