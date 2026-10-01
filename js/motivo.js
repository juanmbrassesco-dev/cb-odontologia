// LA PANTALLA ③ — «¿a qué venís?».
//
// QUÉ HACE ESTE ARCHIVO, en una línea: llena el desplegable de motivo con los
// tratamientos que da el portero, y guarda cuál se eligió.
//
// POR QUÉ LA LISTA NO ESTÁ ESCRITA EN EL HTML. Los catorce tratamientos viven
// en la tabla `tratamientos` de la base. Escribirlos también acá sería tener
// la misma lista en dos lados, y el día que Cecilia agregue uno cambiaría
// sólo uno de los dos — sin que nada avise.
//
// SE PIDE AL CARGAR LA PÁGINA, ANTES DE QUE NADIE ENTRE, y se puede porque
// `tratamientos` es público (`verify_jwt = false` en config.toml): son los
// mismos nombres que ya figuran en la grilla de la landing. Pedirlo recién al
// llegar a esta pantalla haría esperar al paciente en el medio del flujo.


const DIRECCION_DE_TRATAMIENTOS = SUPABASE_URL + '/functions/v1/tratamientos';


// EL TRATAMIENTO ELEGIDO, que es lo único que esta pantalla le deja al resto
// del flujo. Guarda el `id` y no el nombre: es lo que `POST /reservar` pide, y
// es lo que no cambia si algún día se le corrige el texto a un tratamiento.
let tratamientoElegido = null;


// Y SU NOMBRE, que es otro trabajo: el id es lo que entiende el portero y el
// nombre es lo que el paciente va a releer en la tarjeta de la pantalla ⑤.
// Guardarlo acá —y no volver a buscarlo allá— deja la lista de tratamientos
// viviendo en un solo archivo.
let nombreDelTratamiento = null;


/**
 * Le pide al portero la lista de tratamientos.
 *
 * Devuelve la lista, o `null` si el pedido falló. Quien llama decide qué
 * mostrar: este archivo no dibuja errores.
 */
async function pedirLosTratamientos() {

  const respuesta = await fetch(
    DIRECCION_DE_TRATAMIENTOS,
    {
      headers: {
        'apikey': SUPABASE_CLAVE_PUBLICA
      }
    }
  );

  if ( !respuesta.ok ) {
    console.error( 'No se pudieron leer los tratamientos. Estado:', respuesta.status );
    return null;
  }

  return await respuesta.json();
}


/**
 * Cuelga un tratamiento del desplegable.
 *
 * 🔴 EL NOMBRE SE ESCRIBE CON `textContent` Y NO PEGANDO HTML, por el mismo
 * motivo que en `quien.js`: es texto que escribió una persona en la base, y
 * pegado como HTML un nombre con `<script>` adentro se ejecutaría. Es la
 * defensa contra XSS (Cross-Site Scripting).
 */
function ponerUnTratamiento( desplegable, tratamiento ) {

  const opcion = document.createElement( 'option' );

  opcion.value = tratamiento.id;
  opcion.textContent = tratamiento.nombre;

  desplegable.appendChild( opcion );
}


/**
 * Llena el desplegable. Si el pedido falló, deja la pantalla como está: con su
 * única opción, la de «Elegí una opción», y sin nada que elegir.
 */
async function prepararLaPantallaDeMotivo() {

  const tratamientos = await pedirLosTratamientos();

  if ( tratamientos === null ) {
    return;
  }

  const desplegable = document.querySelector( '#motivo' );

  for ( const tratamiento of tratamientos ) {
    ponerUnTratamiento( desplegable, tratamiento );
  }
}


prepararLaPantallaDeMotivo();


// EL «CONTINUAR» DE ESTA PANTALLA.
//
// PREPARA LA SIGUIENTE ANTES DE MOSTRARLA, que es el mismo orden que usa
// `entrar.js`: primero se le pide al portero lo que la pantalla ④ necesita, y
// recién si eso salió bien se avanza. Al revés, el paciente vería una pantalla
// vacía llenarse delante suyo, o quedarse vacía si el pedido falla.
document.querySelector( '#motivo-continuar' ).addEventListener( 'click', async () => {

  const desplegable = document.querySelector( '#motivo' );

  // Sin elegir, el valor es la cadena vacía que trae la primera opción del
  // HTML. No se avanza y se devuelve el foco al desplegable: el mensaje de
  // error todavía no está diseñado, y un aviso inventado acá no pasaría por
  // el maquetado, que es donde se deciden estas cosas.
  if ( desplegable.value === '' ) {
    desplegable.focus();
    return;
  }

  tratamientoElegido = Number( desplegable.value );

  // `selectedOptions` es la lista de lo elegido —uno solo, porque el
  // desplegable no es múltiple—, así que el nombre sale de la opción misma y
  // no de volver a recorrer la lista buscando ese id.
  nombreDelTratamiento = desplegable.selectedOptions[ 0 ].textContent;

  // ⬜ SI FALLA, HOY NO SE LE DICE NADA AL PACIENTE, y es deuda declarada: esta
  // pantalla no tiene dónde escribir un aviso —la ① sí, con `#aviso-entrar`—.
  // No se inventa uno acá: el maquetado es donde se decide qué dice y dónde va.
  const profesionales = await pedirLosProfesionales( tratamientoElegido );

  if ( prepararLaPantallaDeDiaHora( profesionales ) === 'falló' ) {
    console.error( 'No se pudo preparar la pantalla de día y hora.' );
    return;
  }

  avanzarA( '#paso-dia-hora' );
} );


// EL «ATRÁS» DE ESTA PANTALLA.
//
// 🔑 NO ESCONDE NI MUESTRA NADA: le pide al navegador que retroceda un paso, y
// el resto lo hace solo el oyente de `popstate` que ya vive en `pasos.js`.
//
// El porqué es que así hay UNA sola manera de volver, no dos. Si este botón
// cambiara de pantalla por su cuenta, el historial se quedaría donde estaba y
// el «atrás» del teléfono empezaría a contar pasos distintos que este botón —
// dos mecanismos para lo mismo, que es de donde salen los bugs que nadie
// reproduce.
document.querySelector( '#motivo-atras' ).addEventListener( 'click', () => {
  history.back();
} );
