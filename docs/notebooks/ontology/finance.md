---
title: Finance
marimo-version: 0.23.14
pyproject: |
  requires-python = ">=3.11"
  dependencies = [
      "discopy @ git+https://github.com/daydream6728/discopy.git@feature/allegories",
  ]
---

```python {.marimo}
import marimo as mo
```

# Typed financial analysis

A financial analytics pipeline fails the way the Mars Climate Orbiter
did: not loudly, but by adding a number in euros to a number in dollars
and reporting the sum with a straight face. The unit of a number lives
in a column name, a convention, a colleague's memory — nowhere a machine
can check it.

This notebook makes units *predicates* of an [OWL
ontology](https://www.w3.org/TR/owl2-overview/) and lets two typecheckers
guard every step of a risk computation, before a single number flows:

- **HermiT**, a logical reasoner, proves the schema-level guarantees —
  every position has a definite currency, the currency buckets cannot
  overlap, and no position escapes them — and refuses any query that
  would launder one currency into another;
- **DisCoPy** composes the numeric plan as a string diagram whose wires
  are those same predicates, so a plan with a unit error cannot even be
  written down.

The companion [ontologies notebook](ontologies.html) explains the
categorical architecture — a category of relations split at its
predicates; here we put it to work.

```python {.marimo}
from owlready2 import (
    AllDifferent, FunctionalProperty, Nothing, OneOf, Thing, World)

from discopy import python
from discopy.owl import (
    Box, Functor, Id, Query, axioms, ob, reason, subsumes)
from discopy.utils import AxiomError
```

## A fund ontology where currencies are types

Ten lines of schema: portfolios hold positions, each position is in one
asset, each asset is denominated in one currency, and the currencies are
a *closed* enumeration of pairwise distinct individuals. The per-currency
classes are *defined* — HermiT will classify every position into its
bucket from the facts alone:

```python {.marimo}
world = World()
fund = world.get_ontology("http://discopy.org/fund.owl")
with fund:
    class Currency(Thing): pass
    class Asset(Thing): pass
    class Position(Thing): pass
    class Portfolio(Thing): pass
    class MonetaryAmount(Thing): pass
    class holds(Portfolio >> Position): pass
    class inAsset(Position >> Asset, FunctionalProperty): pass
    class denominatedIn(Asset >> Currency, FunctionalProperty): pass
    usd, eur, jpy = Currency("USD"), Currency("EUR"), Currency("JPY")
    _ = AllDifferent([usd, eur, jpy])
    Currency.equivalent_to.append(OneOf([usd, eur, jpy]))
    Asset.is_a.append(denominatedIn.some(Currency))
    Position.is_a.append(inAsset.some(Asset))

    class USDAsset(Asset):
        equivalent_to = [Asset & denominatedIn.value(usd)]
    class EURAsset(Asset):
        equivalent_to = [Asset & denominatedIn.value(eur)]
    class JPYAsset(Asset):
        equivalent_to = [Asset & denominatedIn.value(jpy)]
    class USDPosition(Position):
        equivalent_to = [Position & inAsset.some(USDAsset)]
    class EURPosition(Position):
        equivalent_to = [Position & inAsset.some(EURAsset)]
    class JPYPosition(Position):
        equivalent_to = [Position & inAsset.some(JPYAsset)]

    class USDAmount(MonetaryAmount): pass
    class EURAmount(MonetaryAmount): pass
    class JPYAmount(MonetaryAmount): pass

    class marketValue(Position >> float, FunctionalProperty): pass
    class volatility(Asset >> float, FunctionalProperty): pass
mo.md(f"**{len(list(fund.classes()))} classes**, "
      f"**{len(list(fund.properties()))} properties** — "
      "that is the whole schema.")
```

Now a toy multi-currency portfolio. Note that `marketValue` is a bare
number: its unit is not a column name, it is the *type* of the position
that carries it, which the ontology pins down:

```python {.marimo}
with fund:
    aapl, bund = USDAsset("aapl"), EURAsset("bund")
    toyota, nestle = JPYAsset("toyota"), EURAsset("nestle")
    for asset, sigma in ((aapl, .25), (bund, .06),
                         (toyota, .22), (nestle, .15)):
        asset.volatility = sigma
    macro = Portfolio("global_macro")
    positions = []
    for index, (asset, value) in enumerate(
            ((aapl, 4.2e6), (bund, 3.0e6),
             (toyota, 5.0e8), (nestle, 1.1e6))):
        position = Position(f"p{index}")
        position.inAsset, position.marketValue = asset, value
        positions.append(position)
    macro.holds = positions
reason(world)
buckets = {cls: sorted(cls.instances(), key=lambda one: one.name)
           for cls in (USDPosition, EURPosition, JPYPosition)}
mo.md("HermiT classifies every position into its currency bucket: "
      + ", ".join(
          f"**{cls.name}** = {{{', '.join(one.name for one in ones)}}}"
          for cls, ones in buckets.items()))
```

## Three theorems before any number flows

Each of the following is a statement about the *schema*, proved by
HermiT — not a scan of the data. Together they are exactly what a
unit-safe aggregation needs:

```python {.marimo}
definite = subsumes(Asset, denominatedIn.some(Currency), world)
no_mixing = subsumes(EURPosition & USDPosition, Nothing, world)
coverage = subsumes(
    Position, USDPosition | EURPosition | JPYPosition, world)
mo.md(f"""
| guarantee | statement | proved |
| --- | --- | --- |
| definite unit | every asset is denominated in some currency | **{definite}** |
| no mixing | a position cannot be in two currency buckets | **{no_mixing}** |
| no leakage | every position is in some currency bucket | **{coverage}** |
""")
```

The proofs lean on the schema in an instructive way: *no mixing* holds
because `denominatedIn` is functional and the currencies are declared
pairwise different; *no leakage* holds because `Currency` is a closed
enumeration. Delete either axiom and the corresponding proof — and only
that proof — fails.

## Queries that refuse to mix currencies

At the query level, the currency is the *type of the wire*. Asking for
the EUR leg of the portfolio is one typed composition — the codomain
annotation does the filtering, and the wire labels carry the audit:

```python {.marimo}
eur_leg = Query.from_property(holds, Portfolio, EURPosition)
retrieved = sorted(y.name for (_, ), (y, ) in eur_leg.relation.inside)
mo.vstack([eur_leg.to_diagram(),
           mo.md(f"`{eur_leg}` retrieves **{retrieved}**.")])
```

Composing that leg into a step typed for dollars owes a proof that a
euro position is a dollar position — and HermiT refuses it:

```python {.marimo}
with Query.no_reasoning:
    crooked = eur_leg >> Query.id((USDPosition, ), world)
try:
    crooked.validate()
    verdict = "validated?!"
except AxiomError as error:
    verdict = f"refused: **{error}**"
mo.md(f"The mixed pipeline is {verdict}")
```

## The case study: asset risk and FX risk, statically unit-checked

The numeric plan is a string diagram in the syntax layer of
`discopy.owl`: every wire is a predicate — a position bucket or a
monetary amount in a definite currency — and every box declares the unit
it consumes and the unit it produces. Per bucket, **asset risk** is the
sum of absolute volatility-weighted market values in the *local*
currency, converted to dollars only through an explicit conversion box;
**FX risk** is the net non-dollar exposure times the FX volatility of
its currency pair. (Toy numbers throughout: standalone volatilities, no
correlations, linear FX delta.)

```python {.marimo}
spot = {eur: 1.09, jpy: 0.0068}
fx_vol = {eur: .08, jpy: .11}
amount = {usd: USDAmount, eur: EURAmount, jpy: JPYAmount}
bucket_type = {usd: USDPosition, eur: EURPosition, jpy: JPYPosition}
risk = lambda ccy: Box(
    "asset risk", ob((bucket_type[ccy], )), ob((amount[ccy], )))
net = lambda ccy: Box(
    "net", ob((bucket_type[ccy], )), ob((amount[ccy], )))
to_usd = lambda ccy: Box(
    f"×{spot[ccy]}", ob((amount[ccy], )), ob((USDAmount, )),
    data=spot[ccy])
fx_risk = lambda ccy: Box(
    f"fx risk ×{fx_vol[ccy]}", ob((amount[ccy], )), ob((USDAmount, )),
    data=fx_vol[ccy] * spot[ccy])
add = lambda arity: Box(
    "+", ob(arity * (USDAmount, )), ob((USDAmount, )))

asset_plan = risk(usd) @ risk(eur) @ risk(jpy)\
    >> Id(ob((USDAmount, ))) @ to_usd(eur) @ to_usd(jpy) >> add(3)
fx_plan = net(eur) @ net(jpy) >> fx_risk(eur) @ fx_risk(jpy) >> add(2)
mo.hstack([asset_plan.foliation(), fx_plan.foliation()],
          justify="center")
```

A mis-wired plan is not a wrong number waiting to be noticed — it is a
composition error the moment it is written, because the wires disagree
on their predicate:

```python {.marimo}
try:
    risk(eur) >> to_usd(jpy)
    mistake = "composed?!"
except AxiomError:
    mistake = ("`risk(eur) >> to_usd(jpy)` raises `AxiomError`: "
               "an `EURAmount` wire cannot meet a `JPYAmount` box.")
mo.md(f"The wrong conversion cannot even be written: {mistake}")
```

Evaluation is a functor into Python functions — buckets flow in on
position wires, floats flow on amount wires, and each box is interpreted
by its unit-respecting formula:

```python {.marimo}
values = lambda cls: [
    (one.marketValue, one.inAsset.volatility) for one in buckets[cls]]
rule = lambda box: (
    (lambda *amounts: sum(amounts)) if box.name == "+"
    else (lambda leg: sum(abs(value) * sigma for value, sigma in leg))
    if box.name == "asset risk"
    else (lambda leg: sum(value for value, _ in leg))
    if box.name == "net"
    else (lambda number: abs(number) * box.data))
run = Functor(
    ob_map=lambda typ: (list, )
    if "Position" in typ.inside[0].name else (float, ),
    ar_map=rule, cod=python.Function)
asset_risk_usd = run(asset_plan)(
    values(USDPosition), values(EURPosition), values(JPYPosition))
fx_risk_usd = run(fx_plan)(values(EURPosition), values(JPYPosition))
mo.md(f"""
| metric | value | unit |
| --- | --- | --- |
| asset risk | {asset_risk_usd:,.0f} | `{asset_plan.cod}` |
| FX risk | {fx_risk_usd:,.0f} | `{fx_plan.cod}` |
""")
```

The unit column is not a caption — it is the codomain of the plan, read
off the diagram. Every intermediate number in the computation flowed on
a wire whose predicate names its currency, every conversion was an
explicit box, and the three theorems above guarantee the buckets that
fed the plan were disjoint and exhaustive.

## The fund's own rule book

Like any knowledge base loaded into `discopy.owl`, the fund compiles to
a rule book of equations between relations — including the bucket
definitions and disjointness that back the three theorems — with no
entailed counterexample:

```python {.marimo}
rule_book = axioms(world)
mo.vstack([
    mo.md(f"**{len(rule_book)}** rules, all holding: "
          f"**{all(rule_book)}**."),
    mo.accordion({f"{index}. {axiom}": mo.lazy(
        lambda axiom=axiom: axiom.equation)
        for index, axiom in enumerate(rule_book, 1)})])
```

## Where this goes

The schema above is deliberately tiny, but nothing in it is toy-shaped:
[FIBO](https://spec.edmcouncil.org/fibo/) already declares currencies,
monetary amounts and instruments at industry scale, and the
[ontologies notebook](ontologies.html) loads its ownership-and-control
modules into the same two-level category. Point the same machinery at a
real book of positions and the same three theorems — definite unit, no
mixing, no leakage — are one reasoner call each, before the first
number moves.
