# Archivos ajenos — qué hay acá y por qué

Esta carpeta guarda archivos que **no son nuestros**. Se separan del resto de `brand/`
justamente para que nadie los trate como parte de la identidad de CB: no se recolorean,
no se rehacen y no se versionan a mano.

## `googleg_standard_color_128dp.png`

- **Qué es:** el logotipo «G» de Google, en su versión oficial a color.
- **De dónde salió:** `https://www.gstatic.com/images/branding/googleg/1x/googleg_standard_color_128dp.png`,
  descargado el 2 de septiembre de 2026. **Sin modificar**: ni el tamaño, ni el color, ni el
  encuadre.
- **Para qué se usa:** el botón «Continuar con Google» de la pantalla de entrada, que es la única
  forma de iniciar sesión del sitio.
- **Bajo qué condiciones:** las
  [pautas de marca de Google Identity](https://developers.google.com/identity/branding-guidelines),
  que permiten usar el logotipo dentro del botón de inicio de sesión y **prohíben** alterarlo,
  usarlo suelto sin el botón, pasarlo a una sola tinta o ponerlo sobre un relleno que no sea uno
  de sus tres temas.
- **Marca registrada:** «Google» y su logotipo son marcas de Google LLC. **Nada de lo que se
  publique sobre CB los incluye como parte de su identidad**, y el archivo vive acá sólo para
  armar ese botón.

El tema elegido y el porqué de los descartes viven en `css/tokens.css`, bajo «colores ajenos».
