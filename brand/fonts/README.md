# Fonts

The two typefaces of the brand, vendored so the logo can be rebuilt without a
network round-trip and so the print pack can convert them to outlines.

| File | Family | Where it is used |
|---|---|---|
| `Marcellus-Regular.ttf` | Marcellus | The `CB` initials, in all three versions |
| `Jost-var.ttf` | Jost (variable, weight 100–900) | Source file. Not used directly. |
| `Jost-Light-300.ttf` | Jost frozen at weight 300 | The name. This is the one the outlines come from. |

Both are licensed under the SIL Open Font License 1.1, included here as
`OFL-Marcellus.txt` and `OFL-Jost.txt`. Downloaded from `github.com/google/fonts`,
the upstream repository — not from a font aggregator.

Jost ships as a **variable** font: one file with weight as a dial. Outlines
cannot be extracted from it directly — it has to be pinned to weight 300 first,
otherwise there is no single shape to extract. `Jost-Light-300.ttf` is that
pinned instance, produced with `fontTools.varLib.instancer`; the variable file
is kept as the source it was cut from.
