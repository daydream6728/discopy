---
title: FIBO, drawn
marimo-version: 0.23.16
pyproject: |-
  requires-python = ">=3.12"
  dependencies = [
      "marimo",
      "matplotlib",
      "discopy[semantic]",
  ]
---

```python {.marimo hide_code="true"}
import marimo as mo
```

# FIBO, drawn

An ontology is usually met as a wall of RDF. But every axiom it states is
an equation — or an inclusion — between *relations*, and a relation has a
picture. This notebook loads the
[Financial Industry Business Ontology](https://spec.edmcouncil.org/fibo/)
and draws the lot.

Nothing here is authored: every rule below is FIBO's own, compiled from
the axioms in the files. The pictures are read off the same syntax — an
intersection is composition, a quantifier follows its property and
discards, a complement is a bubble — so what you see is the axiom, not an
illustration of it.

```python {.marimo}
import os

from discopy.owl import axioms, consistent, label, load, name_of

FIBO = "https://spec.edmcouncil.org/fibo/ontology/"
FIXTURES = os.path.join(str(mo.notebook_dir() or "."),
                        "..", "..", "..", "test", "fixtures", "fibo")
world = load(FIBO + "FND/OwnershipAndControl/Ownership/", path=FIXTURES)
book = axioms(world)
```

```python {.marimo hide_code="true"}
mo.hstack([
    mo.stat(label="Classes", value=f"{len(world.classes()):,}"),
    mo.stat(label="Object properties",
            value=f"{len(world.object_properties()):,}"),
    mo.stat(label="Axioms declared",
            value=f"{len(world.tbox()) + len(world.rbox()):,}"),
    mo.stat(label="Rules compiled", value=f"{len(book):,}"),
], widths="equal")
```

Loading `Ownership` pulls its whole import closure — accounting, dates,
relations, the legal-entity modules — from the offline copy in
`test/fixtures/fibo`, so this touches no network. The class schema comes
from the TBox and the role schema from the RBox: `owlapi` files
subproperties, inverses, chains and characteristics in the latter, which
its TBox accessor omits, so both are compiled.

## Every rule holds

An axiom's truth here is the *absence of an entailed counterexample*. A
schema loaded on its own has no individuals to contradict it, so a
consistent ontology entails itself and every rule reads `True`. That is
not a triviality: the same check run against a populated world is what
catches a fact the schema forbids, and it is the check the risk notebooks
lean on.

```python {.marimo hide_code="true"}
_equations = sum(1 for _one in book if "=" in _one.symbols)
mo.vstack([
    mo.hstack([
        mo.stat(label="World consistent", value=str(consistent(world))),
        mo.stat(label="Rules holding",
                value=f"{sum(map(bool, book)):,} / {len(book):,}"),
        mo.stat(label="Equations", value=f"{_equations:,}"),
        mo.stat(label="Inclusions", value=f"{len(book) - _equations:,}"),
    ], widths="equal"),
    mo.md("An equation is a definition — the two sides are the same "
          "relation. An inclusion is a constraint: everything on the left "
          "is on the right. Every rule here carries a picture, because a "
          "construct the drawing dictionary cannot compile is one the "
          "compiler declines to emit a rule for in the first place."),
])
```

## One rule, up close

Before the wall of them, a single equation. FIBO defines a reference
document as a document that something refers to; the two sides of the
equation are the same relation, one named and one spelled out:

```python {.marimo hide_code="true"}
_example = next(one for one in book if "=" in one.symbols)
mo.vstack([mo.md(f"`{_example}`"), _example.equation])
```

## Browse by entity

Pick any class or property the ontology declares and read what it says
about it. Each equation is drawn only when you open it.

```python {.marimo hide_code="true"}
entities = sorted(
    list(world.classes()) + list(world.object_properties()),
    key=name_of)
chooser = mo.ui.dropdown(
    options={f"{name_of(one)}  ·  {one.iri.as_str().split('/')[-2]}": index
             for index, one in enumerate(entities)},
    value=None, label="Entity")
chooser
```

```python {.marimo hide_code="true"}
def drawn(rules):
    """A lazy accordion: nothing is drawn until a row is opened."""
    return mo.accordion({
        f"{index}. {one}": mo.lazy(lambda one=one: one.equation)
        for index, one in enumerate(rules, 1)})


if chooser.value is None:
    _panel = mo.md("*Choose an entity above.*")
else:
    _chosen = entities[chooser.value]
    _rules = [one for one in book if _chosen in one.source.signature()]
    _panel = mo.vstack([
        mo.md(f"**{len(_rules)}** rules mention "
              f"`{label(_chosen)}` in their subject."),
        drawn(_rules)])
_panel
```

## The whole rule book

All of it, twenty-five at a time. The accordion is lazy, so opening a row
is what compiles its picture — which is the only reason a page of
FIBO's axioms renders at all.

```python {.marimo hide_code="true"}
page = mo.ui.number(start=1, stop=(len(book) + 24) // 25, value=1,
                    label="Page of 25")
page
```

```python {.marimo hide_code="true"}
_first = (page.value - 1) * 25
mo.vstack([
    mo.md(f"Rules **{_first + 1}–{min(_first + 25, len(book))}** "
          f"of **{len(book):,}**."),
    drawn(book[_first:_first + 25])])
```

## What this is good for

A vocabulary you can read is a vocabulary you can argue with. The FX risk
notebook types every wire of a numeric plan by one of these predicates,
and the guarantees it leans on — that a monetary amount has exactly one
currency, that an exchange rate carries a base and a dealt currency — are
rules on this page, maintained by the EDM Council rather than by us.

## Run it yourself

From the repository root:

```sh
uv run --group all marimo edit docs/notebooks/finance/fibo.md
uv run --group all python docs/export_notebooks.py fibo
```

Reasoning needs a Java runtime; the fixtures are read offline.
