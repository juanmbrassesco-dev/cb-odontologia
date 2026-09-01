"""Lee el KERNING de una tipografía: cuánto se acerca o se aleja cada par de letras.

Por qué existe este archivo. Una tipografía no sólo dice cuánto mide cada
letra: también trae una lista de PAREJAS que hay que corregir, porque puestas
una al lado de la otra con su ancho nominal quedan mal («AV» queda separada,
«To» queda floja). El navegador aplica esa lista sin avisar. Quien pase el
texto a contornos ignorándola dibuja el texto MÁS ANCHO, y el error se
acumula: la primera letra cae bien y la última cae lejos.

Medido en este proyecto el 31-ago-2026: «ODONTOLOGÍA» sin kerning salía
1,24 px más ancha que lo que dibujaba el navegador — invisible letra por
letra, evidente al final de la palabra.

La lista vive en la tabla GPOS y viene en dos formatos, los dos usados:
  · por PAREJA suelta (formato 1): «esta letra con esta otra, tanto».
  · por CLASES (formato 2): las letras se agrupan por forma —todas las
    redondas, todas las de asta vertical— y la corrección se declara entre
    grupos. Es el formato compacto, y el que usa Jost.
"""


def _subtabla(lookup):
    """El tipo 9 es un envase: la tabla real está adentro."""
    for st in lookup.SubTable:
        yield st.ExtSubTable if lookup.LookupType == 9 else st


def tabla_de_kerning(fuente):
    """Devuelve una función (glifo_a, glifo_b) → corrección en unidades de la
    tipografía. Si no hay kerning, devuelve una que siempre da cero."""
    if "GPOS" not in fuente:
        return lambda a, b: 0

    gpos = fuente["GPOS"].table
    indices = set()

    for registro in gpos.FeatureList.FeatureRecord:
        if registro.FeatureTag == "kern":
            indices.update(registro.Feature.LookupListIndex)

    parejas = {}

    for i in sorted(indices):
        lookup = gpos.LookupList.Lookup[i]

        for st in _subtabla(lookup):
            if getattr(st, "LookupType", lookup.LookupType) not in (2, 9):
                continue

            if st.Format == 1:
                for primero, conjunto in zip(st.Coverage.glyphs, st.PairSet):
                    for registro in conjunto.PairValueRecord:
                        valor = getattr(registro.Value1, "XAdvance", 0)
                        if valor:
                            parejas[(primero, registro.SecondGlyph)] = valor

            elif st.Format == 2:
                clases_1 = st.ClassDef1.classDefs
                clases_2 = st.ClassDef2.classDefs

                for primero in st.Coverage.glyphs:
                    c1 = clases_1.get(primero, 0)

                    for segundo, c2 in list(clases_2.items()) + [(None, 0)]:
                        if segundo is None:
                            continue
                        try:
                            registro = st.Class1Record[c1].Class2Record[c2]
                        except IndexError:
                            continue
                        valor = getattr(registro.Value1, "XAdvance", 0)
                        if valor:
                            parejas[(primero, segundo)] = valor

    return lambda a, b: parejas.get((a, b), 0)
