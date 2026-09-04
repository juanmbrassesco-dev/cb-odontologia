# Marcas ajenas — de dónde salen estos dos archivos

**No son nuestros y no se dibujan a mano.** Son los isotipos oficiales de Instagram y
WhatsApp, bajados el 4-sep-2026 del Brand Resource Center de Meta, que es el único lugar
del que sus propias reglas permiten sacarlos.

| archivo | origen exacto | versión |
|---|---|---|
| `instagram-glyph.svg` | `IG_brand_asset_pack_2023.zip` → `01 Static Glyph/03 Black Glyph/` | negra |
| `whatsapp-glyph.svg` | `WhatsApp-Brand-Resource-Center.zip` → `01_Glyph/01_Digital RGB/03_SVG/` | negra |

Los packs completos traen además la versión **verde** y la **blanca** de WhatsApp, y la
**degradada** y la **blanca** de Instagram. Se guardó la negra de cada uno porque es la que
sirve de base para colorear: es una silueta plana, sin color propio.

## Cómo se usan acá

`tools/construir-tableros.py` **lee estos archivos** y les cambia el relleno por
`currentColor`, así que el color lo pone el CSS y **el dibujo nunca se retoca**. Si mañana
Meta actualiza un isotipo, se reemplaza el archivo y listo.

## Lo que dicen sus reglas, y la decisión que tomamos

- **Instagram** permite llevar el pictograma a **cualquier color sólido**, mientras el resto
  del dibujo no cambie. Nuestro dorado entra sin discusión.
- **WhatsApp** dice lo contrario: *"you shouldn't modify any colors in our logos"*. Publica
  sus versiones —verde, blanca y negra— y espera que se use una de ésas.

🔴 **Se usan los dos en dorado, y es decisión de Juan del 4-sep-2026**, tomada con ese dato
sobre la mesa. Su criterio: es la misma empresa, y el uso repintado está en todos lados.
**Queda escrito con su costo al lado** para que no se re-discuta cada vez que alguien lo mire.

Las dos reglas que **no** se tocan, porque no cuestan nada: el dibujo no se deforma ni se
combina con otro logo, y "WhatsApp" se escribe con las dos mayúsculas y nunca como verbo.
