# Cómo usar el logo — CB Odontología y Estética

Guía corta para saber **qué archivo mandar en cada caso**. Si tenés dudas, la
regla general está en la última sección.

---

## 1. Las cuatro versiones, y cuándo va cada una

| versión | cuándo se usa |
|---|---|
| **Wordmark** — `CB \| Odontología y Estética` | **La principal.** Sitio web, papelería, firma de correo, cartelería. Es la única que dice el nombre completo, así que es la que va donde alguien tiene que *enterarse* de quiénes somos. Es larga y baja: entra donde sobra ancho. |
| **Apilada** — el mismo contenido, en vertical | **La misma información, para cuando el ancho aprieta**: encabezado del sitio en el celular, firma de correo, tarjeta. Al ir el nombre debajo y no al lado, la palabra se queda con todo el ancho de la pieza y **se lee a tamaños donde el wordmark ya no**. No es una versión nueva: es la disposición que el manual de marca ya usaba en la señalética. |
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
| `cb-wordmark-1200` · `-2400` | encabezado del sitio, en pantalla ancha |
| `cb-apilado-600` · `-1200` | encabezado en el celular, y donde el ancho no alcance |
| `cb-emblema-512` · `-1024` | posteos de redes |

📌 **Las fotos de perfil van sobre marfil y no transparentes a propósito:**
WhatsApp e Instagram rellenan la transparencia con un fondo que elige la app, y
puede tocarte negro.

## 4. Dos reglas que no se negocian

**Espacio de reserva.** Alrededor del logo tiene que quedar un aire libre de por
lo menos **la altura de la letra "C"**. Nada entra ahí: ni texto, ni una foto,
ni el borde de la placa.

**Tamaño mínimo.** Medidos, no estimados.

🔑 **Lo que decide si algo se lee no es el alto de la letra: es el grosor de su
trazo.** Un trazo de menos de un píxel y medio no se puede dibujar entero — la
pantalla lo reparte entre dos píxeles a media tinta, y ahí el color se aclara
solo y la palabra se apaga. Por eso los números de abajo salen del trazo más
fino de cada pieza y no de su altura.

**Y el ancho no alcanza para saberlo: importa la DENSIDAD de la pantalla.** El
mismo logo en un celular moderno tiene el triple de píxeles que en un monitor
común. La columna que hay que mirar es la peor: la de densidad sencilla.

| pieza | monitor común | pantalla retina | celular moderno |
|---|---|---|---|
| **wordmark** | **300 px de ancho** | 150 px | 100 px |
| **apilada** | **240 px** | 120 px | 80 px |
| **emblema** | **160 px** | 80 px | 55 px |
| **submarca** | **96 px** | 48 px | 32 px |

⚠️ **El mínimo del wordmark estuvo mal cumplido hasta el 2-sep-2026, y el
número no tenía la culpa: el archivo sí.** El nombre estaba compuesto en un peso
de tipografía más liviano que el del manual de marca, así que a 300 px no
llegaba a leerse aunque la guía dijera 300. Corregido el peso, el número vuelve
a ser cierto. *Si algún día el logo se ve apagado a un tamaño que esta tabla
declara válido, el sospechoso es el archivo, no la tabla.*

⚠️ **El favicon del navegador es de 32 px, y a ese tamaño las iniciales NO se
leen: se ve un disco oscuro con una marca clara.** No es un defecto del archivo
— es que la letra tiene trazos finos y a 32 píxeles ese trazo no entra.
Comprobado: agrandar las letras dentro del disco tampoco lo arregla.

**Impreso, el mínimo depende de la TÉCNICA**: cada una tiene un grosor de línea
abajo del cual no reproduce, y el trazo más fino del logo tiene que llegarle.

**No hay una sola "medida segura": cada técnica tiene su mínimo de línea, y son
muy distintos entre sí.** Buscá la fila de la técnica y la columna de la pieza.

| técnica | su línea mínima | wordmark | apilada | emblema | submarca |
|---|---|---|---|---|---|
| **grabado** *(placa de bronce)* | 0,35 mm | 6,3 cm | 5,6 cm | 3,7 cm | 1,7 cm |
| **serigrafía** | 0,71 mm | 12,6 cm | 11,3 cm | 7,5 cm | 3,4 cm |
| **serigrafía invertida** *(claro sobre oscuro)* | 1,06 mm | 18,8 cm | 16,9 cm | 11,2 cm | 5,2 cm |
| **bordado** *(el ambo)* | 1,00 mm | 17,8 cm | 16,0 cm | 10,6 cm | **4,9 cm** |

🔴 **La consecuencia práctica más importante de esta tabla: en el ambo va la
submarca.** Un bordado de pecho mide unos 8,9 cm de ancho. El wordmark necesita
17,8 y el emblema 10,6 — no entran. **La submarca necesita 4,9 cm y entra
holgada.** La prueba del oficio, para comprobarlo sin instrumentos: reducilo a
8,9 cm en pantalla y si no leés cada letra, la máquina de bordar tampoco.

📌 **La submarca se mide distinto y por eso su número es más grande de lo que
parecería:** sus letras están **caladas**, así que lo que tiene que aguantar es
el hueco y no la tinta — y un hueco es más difícil que una línea, porque la
tinta se le mete desde los dos lados.

*Offset es la más fina de todas y perdona mucho más; el digital queda en el
medio. Si te confirman que la tirada es offset, estos números bajan bastante.*

⚠️ **Hasta el 2-sep-2026 esta guía decía que 11 cm era "la medida segura, la que
aguanta bordado, serigrafía y grabado".** No era cierto: a 11 cm el trazo del
nombre llega al grabado y no le alcanza ni a la serigrafía ni al bordado. Los
11 cm eran el número del grabado con las otras dos pegadas al lado sin haberlas
medido.

⚠️ **Antes de una tirada, preguntale a quien imprime cuál es su mínimo de línea.**
Estos números salen de los valores de referencia del oficio, no de su máquina.

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

📌 **La barra del wordmark es dorado `#B08D57`, el mismo de la tabla.** Hasta el
2-sep-2026 tenía un `#D9CBAA` que ninguna tabla del manual nombraba, y que era
además más pálido que la barra del emblema — dos barras distintas haciendo el
mismo trabajo. Ahora las dos son el mismo dorado.

🔴 **Los CMYK de esta tabla son una cuenta directa y NO están aprobados para
imprimir.** El color de pantalla y el de tinta no son lo mismo, y el dorado es
justo el que peor se porta al pasar a papel. **Antes de una tirada grande hay
que pedirle a la imprenta una prueba impresa y aprobar el dorado sobre el papel
real.** Si en algún momento se busca que el dorado *brille* de verdad, eso ya no
es CMYK: es tinta metálica o estampado con foil, y se cotiza aparte.

## 7. La regla general, si nada de esto aplica

**Ante la duda: PDF para papel, SVG para quien diseña, PNG para pantalla. Y si
el fondo es oscuro, la versión blanca.**
