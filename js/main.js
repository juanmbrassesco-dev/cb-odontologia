// CB Odontología y Estética — el JavaScript de la landing.
//
// Por ahora hace UNA sola cosa: abrir y cerrar el menú del teléfono. Todo lo
// demás de la página —los colores, los tamaños, qué se ve en cada ancho— lo
// resuelve el CSS solo, sin JavaScript de por medio. Eso es a propósito: lo
// que el navegador puede hacer sin código no se programa.


// Las dos piezas del menú. El botón vive adentro de la barra; el panel que se
// despliega vive AFUERA de ella, porque cae debajo y ocupa el ancho entero.
const boton = document.querySelector( '.menu-boton' );
const menu = document.querySelector( '#menu' );


boton.addEventListener( 'click', () => {

  // CÓMO ESTABA ANTES DE TOCAR NADA. Se pregunta primero porque después de
  // cambiarlo ya no se puede saber, y el nombre dice el TIEMPO PASADO a
  // propósito: guarda cómo venía, no lo que va a pasar.
  const estabaCerrado = menu.hidden;

  menu.hidden = !estabaCerrado;

  // Y lo mismo, dicho para quien no ve la pantalla: un lector de pantalla
  // anuncia "contraído" o "expandido" leyendo este atributo. Sin esta línea el
  // menú se abre igual, pero quien lo usa a ciegas no se entera.
  boton.setAttribute( 'aria-expanded', estabaCerrado );

} );
