import marimo

__generated_with = "0.23.16"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import io
    import random
    import statistics
    import sys

    import marimo as mo
    import matplotlib.pyplot as plt

    sys.path.insert(0, str(mo.notebook_dir()))

    from discopy.boltzmann import Grammar
    from experiments import (
        DOCTRINES, SAMPLERS, Size, alphabet, coherent_shape, diagram_class,
        doctrines, sample, shape)
    return (DOCTRINES, Grammar, SAMPLERS, Size, alphabet, coherent_shape,
            diagram_class, io, mo, plt, random, doctrines, sample, shape,
            statistics)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Sampling playground

    Choose a doctrine, a sampler and its parameters, draw a batch of diagrams
    and see what the distribution looks like: the sizes of what was drawn,
    what Hypothesis gave up on, and a gallery of diagrams. The samplers are
    those of `presentation.md`; a draw runs Hypothesis's generate phase, as
    the property matrix does, from the given seed.
    """)
    return


@app.cell(hide_code=True)
def _(mo, doctrines):
    doctrine = mo.ui.dropdown(
        doctrines(), value="symmetric", label="doctrine")
    doctrine
    return (doctrine,)


@app.cell(hide_code=True)
def _(SAMPLERS, diagram_class, doctrine, mo):
    category = diagram_class(doctrine.value)
    available = [name for name in SAMPLERS
                 if hasattr(category, f"strategy_{name}")]
    sampler = mo.ui.dropdown(
        available, value="syntactic_baseline", label="sampler")
    boundary = mo.ui.radio(
        ["free", "fixed"], value="free", label="boundary", inline=True)
    dom = mo.ui.text(value="a @ b", label="dom")
    cod = mo.ui.text(value="b @ a", label="cod")
    atoms = mo.ui.text(value="a b", label="atoms")
    fuel = mo.ui.slider(0, 6, value=3, label="fuel", show_value=True)
    size = mo.ui.dropdown(
        ["2", "4", "8", "16", "32", "critical"], value="8",
        label="expected nodes (2c, 2bc)")
    exact = mo.ui.checkbox(label="exact, from one seed (2c, 2bc)")
    count = mo.ui.slider(
        10, 1000, step=10, value=200, label="diagrams", show_value=True)
    seed = mo.ui.number(0, 10 ** 6, value=0, label="seed")
    gallery = mo.ui.dropdown(
        ["first", "largest", "random"], value="first", label="gallery")
    drawn = mo.ui.slider(0, 24, value=8, label="drawings", show_value=True)
    run = mo.ui.run_button(label="sample")
    mo.vstack([
        mo.hstack([sampler, boundary, dom, cod, atoms], justify="start"),
        mo.hstack([fuel, size, exact], justify="start"),
        mo.hstack([count, seed, gallery, drawn, run], justify="start"),
    ])
    return (atoms, boundary, category, cod, count, dom, drawn, exact, fuel,
            gallery, run, sampler, seed, size)


@app.cell(hide_code=True)
def _(
    Grammar, alphabet, atoms, boundary, category, cod, count, dom, exact,
    fuel, mo, run, sample, sampler, seed, size,
):
    mo.stop(not run.value, mo.md("*Press **sample** to draw.*"))

    def parse(text):
        names = [name.strip() for name in text.split("@") if name.strip()]
        return category.ob(*names)

    bounds = {} if boundary.value == "free" else {
        "dom": parse(dom.value), "cod": parse(cod.value)}
    if sampler.value.startswith("syntactic_grammatical"):
        grammar = Grammar.compile(
            category, category.grammar_atoms, category.grammar_width,
            without=category.admissible
            if sampler.value.endswith("admissible") else ())
        strategy = grammar.strategy(
            **bounds, exact=exact.value, size=float(
                "inf" if size.value == "critical" else size.value))
    else:
        strategy = getattr(category, f"strategy_{sampler.value}")(
            fuel=fuel.value, **bounds)
    with alphabet(tuple(atoms.value.split()) or ("a", "b")):
        diagrams, cases, gave_up, seconds = sample(
            strategy, count.value, seed=int(seed.value))
    return cases, diagrams, gave_up, seconds


@app.cell(hide_code=True)
def _(
    Size, cases, coherent_shape, diagrams, gave_up, mo, seconds, shape,
    statistics,
):
    sizes = [Size.of(d) for d in diagrams]

    def stat(label, value):
        return mo.stat(value=value, label=label, bordered=True)

    def average(key):
        values = [getattr(s, key) for s in sizes]
        return f"{statistics.mean(values):.1f}" if values else "–"

    mo.hstack([
        stat("valid", f"{len(diagrams)} / {cases}"),
        stat("rejected", gave_up.get("rejected", 0)),
        stat("overruns", gave_up.get("overrun", 0)),
        stat("per second", f"{len(diagrams) / seconds:.0f}"),
        stat("distinct", len(set(map(shape, diagrams)))),
        stat("up to coherence", len(set(map(coherent_shape, diagrams)))),
        stat("mean boxes", average("boxes")),
        stat("mean crossings", average("crossings")),
    ], wrap=True)
    return (sizes,)


@app.cell(hide_code=True)
def _(plt, sizes):
    figure, axes = plt.subplots(1, 5, figsize=(13, 2.4))
    for ax, key in zip(axes, (
            "boxes", "layers", "width", "crossings", "structural")):
        values = [getattr(s, key) for s in sizes]
        ax.hist(values, bins=range(0, max(values, default=0) + 2),
                color="#4c72b0", align="left")
        ax.set_title(key, fontsize=9)
    axes[0].set_ylabel("diagrams", fontsize=9)
    figure.tight_layout()
    figure
    return


@app.cell(hide_code=True)
def _(Size, diagrams, drawn, gallery, io, mo, random, seed):
    if gallery.value == "largest":
        chosen = sorted(diagrams, key=lambda d: -Size.of(d).boxes)
    elif gallery.value == "random":
        chosen = random.Random(int(seed.value)).sample(
            diagrams, len(diagrams))
    else:
        chosen = diagrams
    chosen = chosen[:drawn.value]

    def svg(diagram):
        buffer = io.StringIO()
        diagram.draw(path=buffer, format="svg", draw_box_labels=False,
                     figsize=(2.5, 2.5))
        return mo.Html(buffer.getvalue())

    def card(diagram):
        measured = Size.of(diagram)
        caption = mo.md(
            f"`{diagram.dom}` → `{diagram.cod}`, {measured.boxes} boxes, "
            f"{measured.layers} layers")
        try:
            picture = svg(diagram)
        except Exception as error:  # noqa: BLE001  a drawing may fail
            picture = mo.md(f"*cannot draw: {type(error).__name__}*")
        return mo.vstack([picture, caption], align="center")

    mo.hstack([card(d) for d in chosen], wrap=True, justify="start")
    return


if __name__ == "__main__":
    app.run()
