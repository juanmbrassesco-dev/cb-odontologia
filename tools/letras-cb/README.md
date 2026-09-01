# CB initials

The logo does not use the typeface as it comes. Its **C** is narrower and its
**B** wider than the originals, by the same amount, so that both measure the
same and the gold rule lands exactly on the circle's axis.

Stroke weights were not touched. Only the middle band of each letter was
stretched — the part where the strokes run horizontally, so widening it does not
thicken them. Measured before and after: **0.0% change on every stem.**

**This is why the logo can no longer be rebuilt by typing the letters.** This
folder is the source; without it the drawing cannot be regenerated.

## What is here

| file | what it is |
|---|---|
| `cb-inicial-c.ttf` · `cb-inicial-b.ttf` | the typeface with that one letter corrected. Derived from Marcellus, whose OFL licence permits modification — **they are not distributed as fonts, nor under the original name** |
| `base-aro-y-luna.svg` | the ring and the smile come from here; neither changed |
| `piezas.py` | places each letter, the rule and the name |
| `componer.py` | runs it and writes the SVGs into `salida/` |

## Rebuilding the pack

```sh
/opt/homebrew/opt/fonttools/libexec/bin/python3 componer.py
```

The white versions, the PDFs, the EPSs and the PNGs are then produced from
`salida/` with the scripts in `tools/print-pack/`.

## The numbers this has to hold

- the `C` and the `B` both measure **1094 units** (they were 1264 and 924)
- the gold rule sits **on the ring's axis** — deviation 0.00
- the gap between the initials and the rule in the wordmark is **8.05% of the
  total width**, the same it was before

## Licence

Marcellus is published under the SIL Open Font License, which explicitly permits
modification. `OFL-original.txt` is that licence, kept with the files it applies
to. **"Marcellus" is a Reserved Font Name, so the derived files carry a
different one — `CB Inicial C` and `CB Inicial B`.**
