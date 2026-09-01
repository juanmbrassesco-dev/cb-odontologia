# Print pack

Turns the logo into files a print shop can use.

A print shop does not receive a browser. It receives a PDF or an SVG, and there
is no CSS in either — only shapes with coordinates. And it will not have your
typefaces installed: an SVG whose letters are still letters silently renders in
Georgia and Arial on a machine without them. That is not a failure, it is worse
— it looks fine and it is the wrong logo.

## `svg_a_curvas.py`

Replaces every `<text>` in an SVG with a `<path>` of outlines. After it runs the
file mentions no typeface at all.

```sh
/opt/homebrew/opt/fonttools/libexec/bin/python3 svg_a_curvas.py in.svg out.svg
```

Run it with the fonttools interpreter, not the bare `python3` — Homebrew keeps
`fontTools` inside its own environment.

**It is a one-way door: outlines freeze the drawing.** Convert only once the
shapes are final; to change anything, edit the source SVG and convert again.
Never hand-edit the output.

## `svg_a_pdf.py`

Prints an outlined SVG to a vector PDF whose page is the artwork, nothing more.

```sh
python3 svg_a_pdf.py logo.svg logo.pdf
```

Two things it handles that are not obvious:

**The box the artwork came in was not the artwork.** The wordmark's canvas was
inherited from a CSS text line, and a text line is taller than its letters: it
reserves room above for accents and below for descenders. `CB` has neither, so
that room stayed empty — 1.7 mm above and 2.2 mm below, invisible and unequal.
Place that PDF centred in a space and the logo sits half a millimetre high.
`svg_a_curvas.py --recortar` trims the canvas to the ink; this script then sizes
the page to what is left.

**Chrome cannot be used to print it.** It snaps the page size to a grid of its
own and comes back up to 0.7 px off — larger, or smaller, which crops the
artwork. The unit makes no difference: pt, px, mm and in all return the same
number, and asking for less does not help. Nor can CSS centre the surplus: the
page is laid out at the requested size and the extra is appended outside that
box, so neither `padding` nor flex moves it.

So this script uses `rsvg-convert` (`brew install librsvg`), which writes the
page at exactly the size the SVG declares. Chrome was the tool already on the
machine; that is a reason to reach for it first, never a reason to hand over a
file that is off. **It verifies its own output and refuses to write a PDF whose
page came back a different size.** Measured at 1200 dpi, all three pieces now
have zero air on all four sides.

## `svg_a_png.py`

Rasterises an outlined SVG at 300 dpi, transparent or on ivory.

```sh
python3 svg_a_png.py logo.svg logo.png [--fondo]
```

It writes the physical size into the file (`pHYs`). Skip that and a PNG is a
grid of pixels with no idea how big it should print, which leaves whoever
receives it guessing — the one thing this pack exists to prevent.

**A PNG cannot hold the exact size, and that is the format, not sloppiness.**
300 dpi across 50.271 mm is 593.75 pixels, and a pixel does not split. Rounding
puts the printed size within half a pixel — 0.04 mm — of the PDF. Pixels are
kept square and the declared resolution is a flat 300; stretching one axis to
make the arithmetic close would give an exact size and rectangular pixels, and
those confuse half the layout programs. **Which is why the print file is the
PDF and this is the convenience raster.**

## `kerning.py`

Reads the kerning pairs out of the font's GPOS table, which is the part that
naive text-to-outline conversion gets wrong.

A font carries more than the width of each letter: it carries a list of pairs
that need correcting, because side by side at their nominal widths they look
wrong. The browser applies that list silently; a converter that ignores it draws
the text wider, and **the error accumulates** — the first letter lands right and
the last one lands far away. Measured here: `ODONTOLOGÍA` came out 1.24 px too
wide, invisible letter by letter and obvious by the end of the word. With
kerning applied, the difference is 0.006 px.

## Verifying the result

Never assume the conversion was faithful. Render both versions and compare them
with `tools/brand-audit` — ink bounds first, centre of mass second, and at more
than one scale.

Expect one difference that is not an error: **outlines draw thinner than text**.
A browser thickens small live text so it reads better and does not thicken
vector paths. Comparing the same SVG before and after conversion, outlines carry
0.86 of the ink at 2x and 0.97 at 8x — it shrinks with resolution, so it is a
rasterizing artefact and not a drawing one. Do not let it talk you into shipping
two logos: the outlined file is the logo.
