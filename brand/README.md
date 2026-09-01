# Brand

The logo of CB Odontología y Estética, as code.

| Path | What it is |
|---|---|
| `COMO-USAR-EL-LOGO.md` | **The client-facing guide** — which file to send in each situation, clear space, minimum size, what not to do. In Spanish, because it is written for the person using the logo, not for this repository's readers. |
| `logo/curvas/*.svg` | **The logo. These are the files you hand out** — web, print, anywhere. Text is outlined, so they depend on nothing. Generated; never hand-edited. |
| `logo/eps/*.eps` | The same, as EPS. Handed over only because some print shops still ask for it first. |
| `logo/pdf/*.pdf` | The same three as vector PDF, page sized to the artwork to the last hundredth of a millimetre. **What a print shop asks for.** |
| `logo/png/*.png` | Screen raster, named by pixel width. For where a vector will not go — a favicon, an avatar, an email signature. Not the print file. |
| `logo/*.svg` | The **editable source**, with live text. Not a second version of the logo and not for distribution: edit here, then regenerate. |
| `logo-cb-vector.html` | The three of them on one page, with the reasoning behind every coordinate. Start here. |
| `logo-cb.html` | The earlier CSS build. Kept as the reference the vector version is measured against — deleting it would mean losing the judge. |
| `fonts/` | Marcellus and Jost, vendored with their licenses. |

Every piece exists in two variants: full colour, and **all white** (`-blanco`),
for dark backgrounds and photos. The white one is not optional — the gold
emblem disappears on the brand's own graphite, which is measured, not guessed.
On the white submark the letters are knocked out of the disc rather than
painted white, or the piece would be a blank circle.

## Status

The three versions are measured against the brand manual and closed. The
vector build reproduces the CSS one to within 0.03 px.

**One logo file, outlined — the standard, and it is the right call.** A logo
that asks the viewer for a typeface can show up in Georgia the day a font CDN
fails, and a wrong logo that renders cleanly is worse than no logo at all. The
outlined files depend on nothing.

Measured while getting there, and worth knowing rather than acting on: a browser
thickens small live text and does not thicken vector paths, so outlines carry
about 14% less ink at 2x and 3% less at 8x. It is a rasterizing artefact that
shrinks with resolution, invisible in print and marginal on screen — not a
reason to ship two files. If it ever mattered, the fix would be to adjust the
drawing, not to keep a second logo alive.

Colours are HEX, which is screen colour. A print shop works in CMYK or Pantone,
and `#B08D57` is the one that behaves worst in ink. That conversion is decided
with the supplier, with a printed proof in hand — not here.

## Sizes

| piece | page = artwork |
|---|---|
| emblem | 50.271 × 50.271 mm |
| wordmark | 65.694 × 10.629 mm |
| submark | 25.400 × 25.400 mm |

The page is the artwork, with nothing around it. That matters more than it
looks: a layout program scales a placed PDF by its **page**, so any invisible
margin inside the file turns into a size error — ask for 50 mm and get 49.8.
Here there is no margin to turn into anything. Being vector, these sizes are a
reference and not a limit.

The PNGs are sized in **pixels, by where they are used**, because that is the
only unit a screen has: a favicon is 32 px, an Instagram avatar is 1000, a
header logo is 1200. Asking a screen file to hold an exact millimetre size is
asking the wrong question — millimetres are the PDF's job, and there they are
exact.

| file | used for |
|---|---|
| `cb-submarca-32` | favicon |
| `cb-submarca-180` | apple-touch icon |
| `cb-submarca-640-avatar`, `-1000-avatar` | WhatsApp and Instagram. On ivory, because those apps flatten transparency against a background you do not choose |
| `cb-wordmark-600` | email signature, documents |
| `cb-wordmark-1200`, `-2400` | site header at 2x and 4x |
| `cb-emblema-512`, `-1024` | social posts |

## How it was verified

With `tools/brand-audit`. The numbers, and what each of them caught, are in that
folder's README.
