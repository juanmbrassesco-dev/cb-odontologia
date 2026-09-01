# Cómo usar el logo — CB Odontología y Estética

Guía corta para saber **qué archivo mandar en cada caso**. Si tenés dudas, la
regla general está en la última sección.

---

## 1. Las tres versiones, y cuándo va cada una

| versión | cuándo se usa |
|---|---|
| **Wordmark** — `CB \| Odontología y Estética` | **La principal.** Sitio web, papelería, firma de correo, cartelería. Es la única que dice el nombre completo, así que es la que va donde alguien tiene que *enterarse* de quiénes somos. |
| **Emblema** — el círculo con las iniciales y la sonrisa | **Secundaria.** Redes sociales, sellos, detalles. Va donde el nombre ya se sabe o está escrito al lado. |
| **Submarca** — el disco con `CB` | **El ícono.** Favicon del navegador, foto de perfil de WhatsApp e Instagram. Va donde el espacio es cuadrado y chico. |

📌 **Las iniciales no son la tipografía tal cual.** Están dibujadas a partir de
ella: la `C` va más angosta y la `B` más ancha, en la misma medida, para que las
dos midan lo mismo y la rayita dorada caiga justo en el centro del círculo. Los
grosores de trazo quedaron intactos. **Por eso el logo no se puede rehacer
escribiendo las letras — hay que usar estos archivos.** La fuente para
regenerarlo vive en `tools/letras-cb/`.

## 2. Las dos variantes de color

| variante | sobre qué fondo |
|---|---|
| **De color** *(la normal)* | Fondos **claros**: blanco, marfil, gris muy claro, una foto clara. |
| **Blanca** *(termina en `-blanco`)* | Fondos **oscuros** o **fotos**. |

⚠️ **El emblema dorado sobre fondo oscuro DESAPARECE.** Está medido, no es una
impresión. Sobre oscuro va la versión blanca, siempre.

## 3. Qué archivo mandar

| si te lo pide… | mandale |
|---|---|
| **una imprenta o un cartelero** | el **PDF** (`logo/pdf/`). Si te dice que no lo abre, el **EPS** (`logo/eps/`). |
| **una diseñadora, una agencia** | el **SVG** (`logo/curvas/`). Es el mismo dibujo, editable. |
| **una web, un sistema, una plantilla** | el **PNG** del tamaño que corresponda (`logo/png/`). |
| **un documento de Word, una presentación** | el **PNG** de 1200. |

**Los PNG están nombrados por su ancho en píxeles**, y cada uno tiene su uso:

| archivo | para qué |
|---|---|
| `cb-submarca-32` | favicon (el iconito de la pestaña del navegador) |
| `cb-submarca-180` | ícono al guardar el sitio en un iPhone |
| `cb-submarca-640-avatar` · `-1000-avatar` | foto de perfil de WhatsApp e Instagram |
| `cb-wordmark-600` | firma de correo |
| `cb-wordmark-1200` · `-2400` | encabezado del sitio |
| `cb-emblema-512` · `-1024` | posteos de redes |

📌 **Las fotos de perfil van sobre marfil y no transparentes a propósito:**
WhatsApp e Instagram rellenan la transparencia con un fondo que elige la app, y
puede tocarte negro.

## 4. Dos reglas que no se negocian

**Espacio de reserva.** Alrededor del logo tiene que quedar un aire libre de por
lo menos **la altura de la letra "C"**. Nada entra ahí: ni texto, ni una foto,
ni el borde de la placa.

**Tamaño mínimo.** Medidos, no estimados:

| pieza | en pantalla | por qué |
|---|---|---|
| **wordmark** | **300 px de ancho** | a 150 px la mayúscula del nombre mide 6,9 px y deja de leerse |
| **submarca** | **96 px** | más chico, el trazo fino de las letras cae a 1 píxel |

⚠️ **El favicon del navegador es de 32 px, y a ese tamaño las iniciales NO se
leen: se ve un disco oscuro con una marca clara.** No es un defecto del archivo
— es que la letra tiene trazos finos y a 32 píxeles ese trazo no entra.
Comprobado: agrandar las letras dentro del disco tampoco lo arregla.

*(Los mínimos impresos, en milímetros, están por revisar con el mismo método.)*

## 5. Qué NO hacer

- **No lo estires ni lo achates.** Si lo agrandás, agarrá una esquina.
- **No le cambies los colores** ni lo pongas en un dorado "parecido".
- **No lo rehagas escribiendo el texto a mano**: las letras del archivo son
  dibujos y ya no dependen de tener la tipografía instalada. Reescribirlo con
  otra tipografía es otro logo.
- **No le agregues sombras, contornos ni brillos.**
- **No lo pongas sobre un fondo que no lo deje leer** — para eso está la versión
  blanca.

## 6. Los colores

| | HEX *(pantalla)* | CMYK *(orientativo)* |
|---|---|---|
| dorado | `#B08D57` | C0 M20 Y51 K31 |
| dorado claro | `#E4D6BC` | C0 M6 Y18 K11 |
| grafito | `#33322F` | C0 M2 Y8 K80 |
| gris del nombre | `#615E58` | C0 M4 Y10 K62 |
| marfil *(fondo)* | `#FAF7F2` | C0 M1 Y3 K2 |

🔴 **Los CMYK de esta tabla son una cuenta directa y NO están aprobados para
imprimir.** El color de pantalla y el de tinta no son lo mismo, y el dorado es
justo el que peor se porta al pasar a papel. **Antes de una tirada grande hay
que pedirle a la imprenta una prueba impresa y aprobar el dorado sobre el papel
real.** Si en algún momento se busca que el dorado *brille* de verdad, eso ya no
es CMYK: es tinta metálica o estampado con foil, y se cotiza aparte.

## 7. La regla general, si nada de esto aplica

**Ante la duda: PDF para papel, SVG para quien diseña, PNG para pantalla. Y si
el fondo es oscuro, la versión blanca.**
