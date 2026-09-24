---
title: FIBO, drawn
marimo-version: 0.23.16
pyproject: |-
  requires-python = ">=3.12"
  dependencies = [
      "marimo",
      "matplotlib",
      "discopy[semantic] @ git+https://github.com/daydream6728/discopy.git@codex/fibo-qudt-demo",
  ]
---
```python {.marimo hide_code="true"}
import marimo as mo
```

# FIBO, drawn

An ontology is usually met as a wall of RDF. But every axiom it states is
an equation — or an inclusion — between *relations*, and a relation has a
picture. This notebook loads the financial-instrument modules of the
[Financial Industry Business Ontology](https://spec.edmcouncil.org/fibo/)
and draws what they say about securities, credit and derivatives.

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
world = load(FIBO + "FBC/FinancialInstruments/FinancialInstruments/",
             path=FIXTURES)
classes = {name_of(one): one for one in world.classes()}
```

```python {.marimo hide_code="true"}
mo.hstack([
    mo.stat(label="Classes", value=f"{len(world.classes()):,}"),
    mo.stat(label="Object properties",
            value=f"{len(world.object_properties()):,}"),
    mo.stat(label="Axioms declared",
            value=f"{len(world.tbox()) + len(world.rbox()):,}"),
    mo.stat(label="World consistent", value=str(consistent(world))),
], widths="equal")
```

Loading `FinancialInstruments` pulls its whole import closure — debt and
equities, products and services, accounting, dates, the legal-entity and
ownership modules — from the offline copy in `test/fixtures/fibo`, so
this touches no network. The class schema comes from the TBox and the
role schema from the RBox: `owlapi` files subproperties, inverses, chains
and characteristics in the latter, which its TBox accessor omits, so both
are compiled.

Compiling *every* rule of a closure this size is minutes of reasoning for
a page nobody reads whole, so nothing is compiled up front: `axioms` is
asked for one entity at a time, filtering the declarations before it
compiles any, and each picture is drawn only when its row is opened.

```python {.marimo hide_code="true"}
def drawn(rules):
    """A lazy accordion: nothing is drawn until a row is opened."""
    return mo.accordion({
        f"{index}. {one}": mo.lazy(lambda one=one: one.equation)
        for index, one in enumerate(rules, 1)})


def rules_of(entity):
    """Every rule mentioning an entity, counted and drawn lazily."""
    rules = axioms(entity, world)
    return mo.vstack([
        mo.md(f"**{len(rules)}** rules, **{sum(map(bool, rules))}** "
              f"of them holding."),
        drawn(rules)])
```

## Every rule holds

An axiom's truth here is the *absence of an entailed counterexample*. A
schema loaded on its own has no individuals to contradict it, so a
consistent ontology entails itself and every rule reads `True`. That is
not a triviality: the same check run against a populated world is what
catches a fact the schema forbids, and it is the check the risk notebooks
lean on.

## One rule, up close

Before the wall of them, a single equation. FIBO defines a constituent of
a basket as whatever is a constituent *of* one — the two sides are the
same relation, one named and one spelled out:

```python {.marimo hide_code="true"}
_example = next(one for one in axioms(classes["Basket"], world)
                if "=" in one.symbols)
mo.vstack([mo.md(f"`{_example}`"), _example.equation])
```

## What an instrument is

The vocabulary the rest of this repository types its numbers by: what a
security is, what a debt instrument owes to whom, what makes a
derivative one, and what a credit facility commits. Open a row to compile
its rules — the reasoning happens then, not before.

```python {.marimo hide_code="true"}
INSTRUMENTS = {
    "Instruments": ["FinancialInstrument", "Security", "DebtInstrument",
                    "EquityInstrument", "PromissoryNote"],
    "Derivatives": ["DerivativeInstrument", "Option", "Future", "Underlier",
                    "Basket"],
    "Credit": ["CreditAgreement", "CreditFacility", "RevolvingLineOfCredit",
               "Debt", "InterestPayment", "FloatingInterestRate"],
    "Collateral": ["Collateral", "PhysicalCollateral", "SecurityAgreement"],
    "Exposure": ["FinancialExposure", "Position", "Holding"],
}

mo.accordion({
    f"**{group}** · {name}": mo.lazy(
        lambda name=name: rules_of(classes[name]))
    for group, names in INSTRUMENTS.items() for name in names})
```

```python {.marimo}
# rules_of(INSTRUMENTS["Future"])
axioms(classes["DerivativeInstrument"], world)[4].draw(path="cash-and-derivatives-instruments-are-disjoint.svg")
# axioms(classes["Future"], world)[0].draw(path="future-derivative.svg")
```

## Browse by entity

Any other class or property the closure declares, on the same terms: the
rules mentioning it, each drawn when you open it.

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
if chooser.value is None:
    _panel = mo.md("*Choose an entity above.*")
else:
    _chosen = entities[chooser.value]
    _panel = mo.vstack([
        mo.md(f"Rules mentioning `{label(_chosen)}` in their subject."),
        rules_of(_chosen)])
_panel
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