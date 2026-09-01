# Brand audit

Measures a rendered logo against the brand manual it is supposed to reproduce,
and reports the deviation in fractions of a pixel.

Drawing a logo from a PDF brand manual is guesswork until something checks it.
These scripts replace the guess with a number. They found a wordmark that was
20% off, six published measurements taken from a mis-scaled crop, and a set of
text baselines that were half a pixel out — none of which were visible by eye.

No dependencies: pure Python, plus Chrome to render and `pdftoppm` to rasterize.

## The tools

| Script | What it answers |
|---|---|
| `leer_png.py` | Reads a PNG into rows of pixels. Everything else builds on it. |
| `restar_renders.py` | **Where** two renders differ. Subtracts them; black means they match. |
| `centro_de_masa.py` | **How much** they differ, to a hundredth of a pixel. |
| `medir_emblema_calibrado.py` | Measures the emblem against the manual, self-calibrating on the ring diameter. Also reports the arc's thickness profile. |

## How a measurement is run

```sh
# 1. Rasterize the page of the brand manual, writing down the parameters.
pdftoppm -png -r 1600 -f 5 -l 5 "brief.pdf" reference

# 2. Render our version at the same scale.
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --force-device-scale-factor=8 \
  --window-size=320,110 --screenshot=ours.png "file://$PWD/logo.html"

# 3. Ask where they differ, then how much.
python3 restar_renders.py reference.png ours.png diff.png
python3 centro_de_masa.py reference.png ours.png 8
```

## Three rules these tools were built around

**Validate the instrument against the source before trusting it as a judge.**
Run it on the manual itself: it has to return the manual's own numbers. Run it
twice on the same file: it has to return zero.

**A crop without its parameters is a measurement without a scale.** A PNG
labelled "400 dpi" that nobody verified cost a night of false numbers. Always
re-rasterize from the PDF with the parameters written down.

**Measure at more than one scale before correcting anything.** A pixel-grid
artefact shrinks as the grid gets finer; a real drawing error stays put. At 2x
a correct half-pixel correction looked like a regression, and was nearly
reverted; at 4x and 8x it was unmistakable.

## Not here

`medir_emblema.py`, the first version, is kept outside this folder and is not
used: it takes the scale by hand and a single pixel of antialiasing moves its
arc height by 7 px. It is preserved only as a record of why the calibrated one
exists.
