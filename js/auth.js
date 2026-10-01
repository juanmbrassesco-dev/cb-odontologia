// CB Odontología y Estética — entrar con Google.
//
// QUÉ HACE ESTE ARCHIVO, en una línea: consigue el permiso para hablar con el
// portero, y lo guarda mientras dure la pestaña.
//
// EL RECORRIDO SON TRES PASOS Y DOS INTERLOCUTORES:
//
//   ① Google dibuja su botón. El paciente lo toca, elige su cuenta, y Google
//      nos devuelve un PAPEL FIRMADO por él que dice quién es. Ese papel no
//      nos sirve para pedir turnos: lo firmó Google, no nuestro sistema.
//
//   ② Le llevamos ese papel a Supabase y lo CANJEAMOS. Supabase lo verifica
//      contra Google, y si está bien nos da uno propio.
//
//   ③ Ese segundo papel —el de Supabase— es el que abre las puertas del
//      portero. Se guarda en memoria y se acompaña en cada pedido.
//
// 🔴 EL PAPEL NO SE GUARDA EN NINGÚN LADO MÁS QUE EN MEMORIA, y es decisión
// tomada el 28-sep-2026. Guardado en el navegador (`localStorage`) lo puede
// leer cualquier JavaScript de la página, y este sitio dibuja texto que
// escriben personas: ahí una inyección de código (XSS, cross-site scripting)
// dejaría de ser una pantalla fea y pasaría a ser robo de sesión (session
// theft). El costo, aceptado: al cerrar la pestaña hay que entrar de nuevo.


// ─── LO QUE IDENTIFICA A CADA SERVICIO ───────────────────────────────────────
//
// 🔴 LOS TRES SON PÚBLICOS Y VAN A LA VISTA A PROPÓSITO. No son un descuido:
// el navegador de cualquiera que entre al sitio los lee igual. El que NO está
// acá ni puede estar es la llave maestra (`SECRET_KEY`), que vive sólo en el
// servidor y atraviesa todas las cerraduras.

const CLIENTE_DE_GOOGLE =
  '1017724457659-r3uj7a84f2lf27lavib3lv7jvtfak77o.apps.googleusercontent.com';

const SUPABASE_URL = 'https://jnktefjqtvqdrljqfpsj.supabase.co';

const SUPABASE_CLAVE_PUBLICA = 'sb_publishable_TSqUMMo4al7PR9CNncy6fw_GudBDQq2';


// ─── DONDE VIVE LA SESIÓN ────────────────────────────────────────────────────
//
// Arranca en `null`, que significa "todavía no entró nadie". Se llena al
// canjear el papel de Google.
//
// 🔴 Y DESDE EL 1-oct-2026 SOBREVIVE AL CAMBIO DE PÁGINA, que es una decisión
// de seguridad y no de comodidad. El motivo lo encontró Juan probando el sitio
// publicado: el sitio son DOS páginas —reservar y mis turnos—, y al pasar de
// una a la otra la sesión se perdía, **así que al paciente que acababa de
// entrar se le pedía entrar otra vez**. Para él no hay dos páginas: hay un
// sitio donde ya se identificó.
//
// POR QUÉ `sessionStorage` Y NO `localStorage`, que es la diferencia que
// importa: `sessionStorage` vive en ESTA pestaña y muere cuando se cierra;
// `localStorage` queda en el disco hasta que alguien lo borre. Con el segundo,
// el token de una paciente sobreviviría en una computadora compartida —un
// locutorio, la máquina del trabajo— días después de que se fue.
//
// ⚠️ LO QUE ESTO NO EMPEORA, y conviene decirlo para no sobreactuar el riesgo:
// contra un XSS (Cross-Site Scripting) guardar el token acá no es peor que
// tenerlo en una variable — el código atacante corre en la misma página y
// alcanza las dos. Lo que cambia es CUÁNTO dura, y por eso se eligió el que
// dura menos.
const DONDE_SE_GUARDA = 'cb.sesion';

let sesion = null;


/**
 * Guarda la sesión para que sobreviva al salto de una página a la otra.
 *
 * ⚠️ TODO ACCESO VA ADENTRO DE UN `try`: en una ventana privada, o con el
 * almacenamiento del sitio bloqueado, esto LANZA en vez de devolver vacío. Un
 * sitio que se cae por no poder guardar una comodidad está roto por la
 * comodidad.
 */
function guardarLaSesion() {
  try {
    sessionStorage.setItem( DONDE_SE_GUARDA, JSON.stringify( sesion ) );
  } catch ( falla ) {
    console.error( 'No se pudo guardar la sesión en esta pestaña:', falla );
  }
}


/**
 * Recupera la sesión guardada, si hay una y si todavía sirve.
 *
 * 🔑 SE MIRA EL VENCIMIENTO ACÁ Y NO SE CONFÍA EN QUE EL PORTERO LO RECHACE.
 * Rechazarlo lo rechaza igual —el token lo valida él, que es la defensa de
 * verdad— pero un token vencido manda al paciente a una pantalla que falla en
 * vez de a la que le pide entrar.
 */
function recuperarLaSesion() {

  let guardada = null;

  try {
    guardada = sessionStorage.getItem( DONDE_SE_GUARDA );
  } catch ( falla ) {
    return;
  }

  if ( guardada === null ) {
    return;
  }

  const candidata = JSON.parse( guardada );

  // `expires_at` viene en SEGUNDOS desde 1970 y `Date.now()` en milisegundos:
  // sin el /1000 la comparación da siempre que está vencida.
  const vencida = !candidata.expires_at || candidata.expires_at < Date.now() / 1000;

  if ( vencida ) {
    olvidarLaSesion();
    return;
  }

  sesion = candidata;
}


/** Borra la sesión guardada. La usa el vencimiento, y la va a usar un «salir». */
function olvidarLaSesion() {

  sesion = null;

  try {
    sessionStorage.removeItem( DONDE_SE_GUARDA );
  } catch ( falla ) {
    // Si no se puede borrar es porque tampoco se pudo guardar.
  }
}


recuperarLaSesion();


/**
 * El permiso para hablar con el portero, o `null` si nadie entró todavía.
 * Las otras pantallas preguntan por acá en vez de mirar la variable.
 */
function tokenDeLaSesion() {
  return sesion === null ? null : sesion.access_token;
}


/** Si hay alguien adentro. Lo preguntan las dos páginas al arrancar. */
function haySesion() {
  return sesion !== null;
}


/**
 * PASO ② — le lleva a Supabase el papel de Google y se trae el propio.
 *
 * Recibe el papel firmado por Google y devuelve `true` si el canje salió
 * bien. Si sale mal devuelve `false`: quien la llama decide qué mostrar.
 */
async function canjearElPapel( papelDeGoogle ) {

  const respuesta = await fetch(
    SUPABASE_URL + '/auth/v1/token?grant_type=id_token',
    {
      method: 'POST',

      headers: {
        // La clave pública dice A QUÉ PROYECTO de Supabase le hablamos. No
        // dice quién es el paciente: eso lo dice el papel de abajo.
        'apikey': SUPABASE_CLAVE_PUBLICA,
        'Content-Type': 'application/json'
      },

      // `JSON.stringify` convierte el objeto de JavaScript en el texto que
      // viaja por la red. Del otro lado se vuelve a armar.
      body: JSON.stringify( {
        provider: 'google',
        id_token: papelDeGoogle
      } )
    }
  );

  if ( !respuesta.ok ) {
    // No se imprime el cuerpo del error: puede traer datos del paciente.
    console.error( 'El canje falló. Estado:', respuesta.status );
    return false;
  }

  sesion = await respuesta.json();

  guardarLaSesion();

  return true;
}


/**
 * PASO ① — el enganche con Google.
 *
 * `alEntrar` es lo que la pantalla quiere que pase DESPUÉS de un login que
 * salió bien. Este archivo no sabe qué pantalla lo llamó ni qué tiene que
 * dibujar después, y por eso no lo decide.
 */
function prepararElBoton( { contenedor, alEntrar, alFallar } ) {

  google.accounts.id.initialize( {
    client_id: CLIENTE_DE_GOOGLE,

    // Google llama a esta función cuando el paciente terminó de elegir su
    // cuenta. El papel firmado viene adentro, en `credential`.
    callback: async ( respuestaDeGoogle ) => {

      const entro = await canjearElPapel( respuestaDeGoogle.credential );

      if ( entro ) {
        alEntrar();

      } else {
        alFallar();
      }
    }
  } );

  // EL BOTÓN LO DIBUJA GOOGLE Y NO NOSOTROS, y no es una preferencia: su
  // documentación dice que un botón propio no puede disparar el login porque
  // no hay función que llamar al tocarlo. Lo que sí se puede es elegir cómo
  // se ve, y estos cinco valores son los que lo dejan igual al que se aprobó
  // el 24-sep: blanco con filo, rectangular, el logo a la izquierda y el
  // rótulo «Continuar con Google».
  google.accounts.id.renderButton(
    contenedor,
    {
      type: 'standard',
      theme: 'outline',
      size: 'large',
      shape: 'rectangular',
      text: 'continue_with',
      logo_alignment: 'left',
      locale: 'es'
    }
  );
}
