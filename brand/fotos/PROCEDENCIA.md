# Fotos de ejemplo

**Ninguna de estas fotos es la foto del sitio.** Son de banco y están acá para
que la maqueta se pueda mirar con contenido real en vez de con un rectángulo
gris. **Se reemplazan por fotos propias antes de publicar.**

| archivo | autor | fuente | licencia |
|---|---|---|---|
| `hero-ejemplo.jpg` | Brooke Balentine (@brookebalentine) | Unsplash, `xSEFkIAopxA` | Unsplash License |
| `nosotros-ejemplo.jpg` | Jonathan Borba (@jonathanborba) | Unsplash, `ctrQhye5SWs` | Unsplash License |
| `antes-ejemplo.jpg` | Ozkan Guner (@dentistozkanguner) | Unsplash, `Uyv7g3kroJM` | Unsplash License |
| `despues-ejemplo.jpg` | Tony Litvyak (@justatony) | Unsplash, `glPVwPr1FKo` | Unsplash License |
| `entrar-ejemplo.jpg` | Amy Vosters (@amyvosters) | Unsplash, `pxOQ-P97sA8` | Unsplash License |

⚠️ **Unsplash tiene DOS licencias y la diferencia no se ve en la foto.** Las que
publica **Getty Images** —y cualquiera marcada `plus`— son **Unsplash+**, de
suscripción paga: **no entran acá**. Al elegir `nosotros-ejemplo.jpg` la mitad
de las candidatas buenas eran de ésas y se descartaron por eso, no por la
imagen. *El dato se verifica en la ficha de la foto: `plus: true`.*

**Qué permite la Unsplash License:** usar la foto gratis, incluso con fines
comerciales, sin pedir permiso y sin atribución obligatoria. Lo que prohíbe es
vender copias sin modificar y armar con ellas un servicio que compita con
Unsplash. **Redistribuirla como parte de este proyecto está permitido**, y la
atribución va igual porque cuesta un renglón.

🔴 **LO QUE LA LICENCIA NO CUBRE, y hay que resolver antes de producción:** la
persona que aparece es identificable, y **la licencia de la foto no es lo mismo
que el permiso de esa persona**. Para publicidad de un servicio de salud hace
falta autorización de imagen. **Para una maqueta interna no hace falta; para el
sitio en el aire, sí.** Es un motivo más para que las fotos propias existan
antes de noviembre — cómo se sacan está en `brand/COMO-SACAR-LAS-FOTOS.md`.

---

## 📐 `nosotros-ejemplo.jpg` VIENE RECORTADO, y eso es a propósito *(11-sep-2026)*

El original de Unsplash es **5464 × 8192** (2:3). Acá vive recortado y reducido
a **900 × 1125**, que es **4:5 exacto** — la misma proporción del hueco que le
da el bloque «Nosotros». **Por qué se recorta el archivo en vez de dejar que lo
recorte el navegador:** con `object-fit: cover` el recorte lo decide el
navegador, siempre por el centro; recortándolo antes, **lo que se aprueba en el
tablero es exactamente lo que se ve**, y el encuadre —cara en el tercio de
arriba, corte por el antebrazo y no por las manos— es una decisión y no una
casualidad.

**Los cuatro bordes, medidos contra el marfil `#FAF7F2`:** arriba **11,82** ·
abajo **4,78** · izquierda **9,53** · derecha **15,36**. **Los cuatro pasan el
piso de 3,0**, así que esta foto no se disuelve contra la página por ningún
lado. *(La del hero da **2,92 abajo** y por eso existe el filo de 1 px del
bloque. El filo se queda igual: es una regla, no un arreglo — las fotos
definitivas las va a cargar Cecilia y un filo que aparece «cuando hace falta»
obliga a medir cada foto nueva.)*

⚠️ **LO QUE ESTA FOTO NO RESUELVE: no muestra el consultorio.** El fondo es
liso. Sirve para juzgar encuadre, peso y jerarquía del bloque; **no** para
juzgar si «Nosotros» transmite el lugar. Eso se contesta con el retrato real.

---

## 🔴 EL PAR «ANTES / DESPUÉS» ES DE DOS BOCAS DISTINTAS, Y NO SE PUBLICA

`antes-ejemplo.jpg` y `despues-ejemplo.jpg` **no son la misma persona ni el
mismo tratamiento**: son dos fotos de banco sin relación entre sí, puestas una
al lado de la otra para poder decidir **tamaño, proporción y aire** de la
sección Prueba. *Lo decidió Juan el 8-sep-2026, con el criterio de que para
juzgar la forma alcanza — y alcanza.*

**Por qué esto es más fuerte que "reemplazar por fotos propias", que es lo que
pide el resto de este archivo:** el **Código Argentino de Ética y Deontología
Dental**, en su **Art. 53**, dice que el odontólogo no puede avalar documentos
o informes *"que reflejen resultados de actuaciones profesionales que no haya
efectuado y comprobado personalmente"*. Un par antes/después publicado **es
exactamente eso**. Y el **Art. 49.3** pide que la publicidad no pueda *"dar
lugar a falsas esperanzas"*.

**En criollo: el hero con una cara de banco es un ambiente y se puede discutir;
este par publicado sería un resultado clínico fabricado.** Al desplegar van
casos propios de Cecilia, con su autorización de imagen, **o la sección va sin
el par** — que por eso se maquetó de modo que se sostenga sin él.

⚠️ **Y falta el dato que manda:** en Santa Fe el régimen de anuncios lo dicta el
**Colegio de Odontólogos por Ley 3950**, la consulta está hecha y **no
contestó**. El código de la AOA es el marco de la profesión, no el reglamento
local.

**Fuente:** Código Argentino de Ética y Deontología Dental, arts. 49 a 53 —
`legisalud.gov.ar/pdf/aoa.pdf` *(bajado y leído el 8-sep-2026; el sitio tiene
el certificado vencido y hay que forzarlo con `curl -k`)*.


---

## 🪑 `entrar-ejemplo.jpg` — POR QUÉ ES UN LUGAR Y NO UNA PERSONA *(24-sep-2026)*

Es la foto de la **pantalla ① de `reservar.html`**, y la pidió Juan: *«buscá
alguna de archivo más descriptiva, tipo una recepción, una recepcionista o algo
por el estilo»*.

**Se eligió una SALA DE ESPERA y no una recepcionista, y el motivo no es
estético:** una persona en un rol promete **personal que este consultorio puede
no tener**. Si el ejemplo muestra una recepcionista y Cecilia atiende sola, la
foto propia no puede ocupar el lugar del ejemplo y hay que rediseñar la pieza.
**Un ejemplo sirve si la definitiva puede reemplazarlo sin tocar nada.**

**Y lo que la evidencia agrega, que empuja en la misma dirección:** lo que
genera confianza en un sitio de salud son **fotos reales del lugar y del
equipo**; el banco genérico es justamente lo que se recomienda reemplazar. Eso
no invalida usarlo como ejemplo — invalida publicarlo.

**Viene RECORTADA a 16/9 en el archivo** (1200 × 675), igual que
`nosotros-ejemplo.jpg` y por el mismo motivo: el encuadre es una decisión, no
lo que le toque al navegador. El original de Unsplash es vertical (2400 × 2808)
y el recorte toma la franja de abajo — el olivo, la fila de sillas y la pared.

⚠️ **DOS LIMITACIONES DECLARADAS, para que nadie las descubra tarde:**
1. **El cartel de la pared está en INGLÉS** *(«SMILE LIKE YOU MEAN IT — THE
   KILLERS»)*. A 390 px queda ilegible y no molesta; **en pantalla grande se
   lee**, y un cartel en inglés de una banda de rock no es lo que diría la sala
   de espera de un consultorio en Santa Fe. **Es una razón más para que la foto
   propia exista, no un detalle a maquillar.**
2. **El borde de ARRIBA de la foto es pared casi blanca contra el marfil de la
   barra.** Hoy no se disuelve porque **el encabezado tiene su línea dorada de
   1 px**, que es la que las separa. *Si esa línea se saca, este borde hay que
   volver a mirarlo.*

**Qué tiene que mostrar la foto DEFINITIVA:** la sala de espera o la entrada
reales, con luz cálida y sin equipamiento clínico a la vista — el paciente que
llega a esta pantalla ya decidió, y lo que necesita ver es **dónde va a ir**,
no el sillón. *Entra al brief de fotos junto con las otras.*
