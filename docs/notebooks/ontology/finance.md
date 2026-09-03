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

# Typed financial analysis on FIBO

A financial analytics pipeline fails the way the Mars Climate Orbiter
did: not loudly, but by adding a number in euros to a number in dollars
and reporting the sum with a straight face. The unit of a number lives
in a column name, a convention, a colleague's memory — nowhere a machine
can check it.

The [Financial Industry Business Ontology](https://spec.edmcouncil.org/fibo/)
already fixed this on paper: its `FND/Accounting/CurrencyAmount` module
declares that *a monetary amount has exactly one currency*, and its
`FND/OwnershipAndControl/Ownership` module declares what a portfolio, a
holding and an acquisition price are. This notebook makes those axioms
*executable* — every wire of a risk computation is a FIBO predicate, and
two typecheckers guard every step before a single number flows:

- **HermiT**, a logical reasoner, proves the schema-level guarantees
  from FIBO's own axioms — a definite currency for every amount, no
  overlap between currency buckets, and no holding escaping the fund's
  mandate — and refuses any query that would launder one currency into
  another;
- **DisCoPy** composes the numeric plan as a string diagram whose wires
  are those same predicates, so a plan with a unit error cannot even be
  written down.

The companion [ontologies notebook](ontologies.html) explains the
categorical architecture — a category of relations split at its
predicates; here we put it to work.

```python {.marimo}
import os

from owlready2 import AllDifferent, Nothing, OneOf, World

from discopy import python
from discopy.owl import (
    Box, Functor, Id, Query, axioms, extension, label, load, ob, reason,
    subsumes)
from discopy.utils import AxiomError
```

## The right FIBO modules

`Ownership` pulls in its whole import closure, `CurrencyAmount`
included. Everything below — classes, properties and their axioms — is
FIBO's own; we define no schema of our own:

```python {.marimo}
FIBO = "https://spec.edmcouncil.org/fibo/ontology/"
FIXTURES = os.path.join(str(mo.notebook_dir() or "."),
                        "..", "..", "..", "test", "fixtures", "fibo")
world = World()
ownership = load(
    FIBO + "FND/OwnershipAndControl/Ownership/", world, path=FIXTURES)
find = lambda module, name: world.search_one(iri=f"*{module}/{name}")
Portfolio = find("Ownership", "Portfolio")
Holding = find("Ownership", "Holding")
hasAcquisitionPrice = find("Ownership", "hasAcquisitionPrice")
MonetaryAmount = find("CurrencyAmount", "MonetaryAmount")
MonetaryPrice = find("CurrencyAmount", "MonetaryPrice")
Currency = find("CurrencyAmount", "Currency")
ExchangeRate = find("CurrencyAmount", "ExchangeRate")
hasCurrency = find("CurrencyAmount", "hasCurrency")
comprises = find("Collections", "comprises")
isMemberOf = find("Collections", "isMemberOf")
mo.md(f"Loaded **{len(list(world.classes()))} classes** and "
      f"**{len(list(world.properties()))} properties** from "
      f"FIBO's foundations.")
```

Now the *data*: three currencies, two exchange rates — FIBO's
`ExchangeRate` carries its base currency, dealt currency and rate as
first-class structure, one euro being 1.09 dealt dollars — and a
portfolio of four holdings, each priced by a `MonetaryPrice` in its own
currency. The one axiom we state is about *our* portfolio, not about
finance: its mandate, that everything it comprises is a holding priced
in one of the three currencies. FIBO even polices the quotation
convention: `hasBaseCurrency` is inverse-functional, so our first
attempt, quoting both rates off the same base, made the world
inconsistent — the reasoner caught a modelling mistake before it could
become a pricing one.

```python {.marimo}
demo = world.get_ontology("http://discopy.org/portfolio.owl")
with demo:
    usd, eur, jpy = Currency("USD"), Currency("EUR"), Currency("JPY")
    _ = AllDifferent([usd, eur, jpy])
    eurusd, jpyusd = ExchangeRate("eurusd"), ExchangeRate("jpyusd")
    eurusd.hasBaseCurrency, eurusd.hasDealtCurrency = [eur], [usd]
    jpyusd.hasBaseCurrency, jpyusd.hasDealtCurrency = [jpy], [usd]
    eurusd.hasRateValue, jpyusd.hasRateValue = [1.09], [0.0068]
    holdings = []
    for name, value, ccy in (("aapl", 4.2e6, usd), ("bund", 3.0e6, eur),
                             ("toyota", 5.0e8, jpy),
                             ("nestle", 1.1e6, eur)):
        price = MonetaryPrice(name + "_price")
        price.hasCurrency, price.hasAmount = [ccy], [value]
        holding = Holding(name)
        holding.hasAcquisitionPrice = [price]
        holdings.append(holding)
    macro = Portfolio("global_macro")
    macro.comprises = holdings
    macro.is_a.append(comprises.only(Holding & hasAcquisitionPrice.some(
        MonetaryPrice & hasCurrency.some(OneOf([usd, eur, jpy])))))
reason(world)
mo.md(f"**{len(holdings)}** holdings, **2** exchange rates, "
      "**1** mandate — and HermiT has classified the lot.")
```

## Currency buckets are compound predicates

No bucket classes to declare: a bucket is a FIBO class construct, one
wire in the Karoubi envelope, and HermiT retrieves its members —

```python {.marimo}
priced = lambda ccy: MonetaryAmount & hasCurrency.value(ccy)
bucket = lambda ccy: Holding & hasAcquisitionPrice.some(priced(ccy))
members = {ccy: sorted(
    x.name for (x, ), _ in extension(bucket(ccy), world).inside)
    for ccy in (usd, eur, jpy)}
mo.vstack([
    extension(bucket(eur), world).to_diagram(),
    mo.md(" — ".join(f"**`{label(bucket(ccy))}`** = "
                     f"{{{', '.join(members[ccy])}}}"
                     for ccy in (usd, eur, jpy)))])
```

## Three theorems before any number flows

Each of the following is proved by HermiT from the loaded axioms — not
scanned off the data. The first is FIBO's own
`MonetaryAmount ⊑ =1 hasCurrency.Currency`; the second follows from that
cardinality plus the currencies being pairwise different; the third from
the portfolio's declared mandate:

```python {.marimo}
definite = subsumes(MonetaryAmount, hasCurrency.some(Currency), world)
no_mixing = subsumes(priced(eur) & priced(usd), Nothing, world)
coverage = subsumes(
    isMemberOf.some(OneOf([macro])),
    bucket(usd) | bucket(eur) | bucket(jpy), world)
mo.md(f"""
| guarantee | statement | proved by |
| --- | --- | --- |
| definite unit | every monetary amount has a currency | FIBO's cardinality axiom — **{definite}** |
| no mixing | no amount is priced in two currencies | cardinality + distinct currencies — **{no_mixing}** |
| no leakage | every holding of the fund is in a bucket | the fund's own mandate — **{coverage}** |
""")
```

## Queries that refuse to mix currencies

At the query level the bucket is the *type of the wire*: asking for the
EUR leg of the portfolio is one typed composition along FIBO's
`comprises`, with the codomain annotation doing the filtering —

```python {.marimo}
eur_leg = Query.from_property(comprises, Portfolio, bucket(eur))
retrieved = sorted(y.name for (_, ), (y, ) in eur_leg.relation.inside)
mo.vstack([eur_leg.to_diagram(),
           mo.md(f"the EUR leg retrieves **{retrieved}**.")])
```

Composing that leg into a step typed for the dollar bucket owes a proof
that a euro holding is a dollar holding — and HermiT refuses it:

```python {.marimo}
with Query.no_reasoning:
    crooked = eur_leg >> Query.id((bucket(usd), ), world)
try:
    crooked.validate()
    verdict = "validated?!"
except AxiomError as error:
    verdict = f"refused: **{error}**"
mo.md(f"The mixed pipeline is {verdict}")
```

## The case study: asset risk and FX risk, statically unit-checked

The numeric plan is a string diagram in the syntax layer of
`discopy.owl`: every wire is a FIBO predicate — a currency bucket or a
monetary amount in a definite currency — and every conversion box
denotes one of the portfolio's `ExchangeRate` individuals, carried as
its `data`. Per bucket, **asset risk** is the sum of absolute
volatility-weighted values in the *local* currency, converted to
dollars only through its rate box; **FX risk** is the net non-dollar
exposure times the FX volatility of its pair. (Toy numbers: standalone
volatilities, no correlations, linear FX delta.)

```python {.marimo}
risk = lambda ccy: Box(
    "asset risk", ob((bucket(ccy), )), ob((priced(ccy), )))
net = lambda ccy: Box("net", ob((bucket(ccy), )), ob((priced(ccy), )))
convert = lambda rate: Box(
    f"×{rate.hasRateValue.first()}",
    ob((priced(rate.hasBaseCurrency.first()), )),
    ob((priced(rate.hasDealtCurrency.first()), )), data=rate)
fx_vol = {eurusd: .08, jpyusd: .11}
fx_risk = lambda rate: Box(
    f"fx risk ×{fx_vol[rate]}",
    ob((priced(rate.hasBaseCurrency.first()), )),
    ob((priced(rate.hasDealtCurrency.first()), )), data=rate)
add = lambda arity: Box(
    "+", ob(arity * (priced(usd), )), ob((priced(usd), )))

asset_plan = risk(usd) @ risk(eur) @ risk(jpy)\
    >> Id(ob((priced(usd), ))) @ convert(eurusd) @ convert(jpyusd)\
    >> add(3)
fx_plan = net(eur) @ net(jpy) >> fx_risk(eurusd) @ fx_risk(jpyusd)\
    >> add(2)
mo.hstack([asset_plan.foliation(), fx_plan.foliation()],
          justify="center")
```

A mis-wired plan is not a wrong number waiting to be noticed — it is a
composition error the moment it is written, because the wires disagree
on their predicate:

```python {.marimo}
try:
    risk(eur) >> convert(jpyusd)
    mistake = "composed?!"
except AxiomError:
    mistake = ("`risk(eur) >> convert(jpyusd)` raises `AxiomError`: "
               "a euro-amount wire cannot meet the yen rate box.")
mo.md(f"The wrong conversion cannot even be written: {mistake}")
```

Evaluation is a functor into Python functions — buckets flow in on
holding wires, floats on amount wires, values and rates read off the
ontology's own individuals, volatilities from a market-data table:

```python {.marimo}
volatility = {"aapl": .25, "bund": .06, "toyota": .22, "nestle": .15}
values = lambda ccy: [
    (one.hasAcquisitionPrice.first().hasAmount.first(),
     volatility[one.name])
    for one in holdings if one.name in members[ccy]]
rule = lambda box: (
    (lambda *amounts: sum(amounts)) if box.name == "+"
    else (lambda leg: sum(abs(value) * sigma for value, sigma in leg))
    if box.name == "asset risk"
    else (lambda leg: sum(value for value, _ in leg))
    if box.name == "net"
    else (lambda number: abs(number)
          * fx_vol[box.data] * box.data.hasRateValue.first())
    if box.name.startswith("fx risk")
    else (lambda number: number * box.data.hasRateValue.first()))
run = Functor(
    ob_map=lambda typ: (list, )
    if typ.inside[0].name.startswith("Holding") else (float, ),
    ar_map=rule, cod=python.Function)
asset_risk_usd = run(asset_plan)(values(usd), values(eur), values(jpy))
fx_risk_usd = run(fx_plan)(values(eur), values(jpy))
mo.md(f"""
| metric | value | unit |
| --- | --- | --- |
| asset risk | {asset_risk_usd:,.0f} | `{asset_plan.cod}` |
| FX risk | {fx_risk_usd:,.0f} | `{fx_plan.cod}` |
""")
```

The unit column is not a caption — it is the codomain of the plan, read
off the diagram: a FIBO monetary amount whose currency is provably the
dollar. Every intermediate number flowed on a wire whose predicate names
its currency, every conversion was an `ExchangeRate` of the ontology,
and the three theorems above guarantee the buckets that fed the plan
were disjoint and exhaustive over the fund's mandate.

## The rule book, straight from FIBO

Like any knowledge base loaded into `discopy.owl`, the world compiles to
a rule book of equations between relations — FIBO's own axioms, the
cardinality that gave us definite units among them — with no entailed
counterexample:

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

Nothing above needed a schema of our own: the vocabulary, the definite-
unit axiom and the exchange-rate structure are FIBO's, maintained by the
EDM Council for the industry at large. What we added is a portfolio, its
mandate, and the discipline of running every query and every numeric
plan through wires typed by FIBO's predicates — so that the reasoner,
not a code review, is what stands between a euro and a dollar.
