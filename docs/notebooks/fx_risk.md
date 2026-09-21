---
title: A fund's FX risk, typed by FIBO
marimo-version: 0.23.16
pyproject: |-
  requires-python = ">=3.12"
  dependencies = [
      "marimo",
      "numpy",
      "matplotlib",
      "yfinance",
      "owlapy==1.6.6",
  ]
---
```python {.marimo hide_code="true"}
import marimo as mo
```

# A fund's FX risk, typed by FIBO

A financial analytics pipeline fails the way the Mars Climate Orbiter did:
not loudly, but by adding a number in euros to a number in dollars and
reporting the sum with a straight face. The unit of a number lives in a
column name, a convention, a colleague's memory — nowhere a machine can
check it. The valuation *date* is worse: nothing at all marks yesterday's
exposure as stale.

This is not a hypothetical. Every quote below is pulled live from Yahoo
Finance, and one of the instruments in the book, the FTSE 100 tracker
`ISF.L`, is quoted in **pence, not pounds** — a feed that says `1042` means
£10.42. Read it as pounds and the position is wrong by a factor of a
hundred. Nothing in a float says which one it is.

The [Financial Industry Business Ontology](https://spec.edmcouncil.org/fibo/)
fixed this on paper. Its `FND/Accounting/CurrencyAmount` module declares
that *a monetary amount has exactly one currency*; `FND/OwnershipAndControl`
declares what a portfolio and a holding are; `FND/DatesAndTimes` declares
what it means for an observation to be as of a date. This notebook makes
those axioms executable: **every wire of every calculation below is a FIBO
class expression** saying what a number measures, in which unit, on which
date — and two checkers guard every step before a number flows.

- **DisCoPy** composes each plan as a string diagram over those predicates,
  so pence added to pounds, or a euro amount valued at the yen rate, is a
  composition error the moment it is written rather than a wrong number
  waiting to be noticed.
- **HermiT** proves the schema-level guarantees from FIBO's own axioms — a
  definite currency, disjoint unit buckets, no holding outside the fund's
  mandate — and decides every change of predicate, including whether one
  valuation window lies inside another.

Numbers stay numbers: the ontology holds what is *observed*, NumPy holds
what is *computed*, and a description logic has no arithmetic, so nothing
computed is written back. Prices, exchange rates and the covariance are
real and as of the last close. Only the **share counts** are invented — a
fund's positions are not public.

```python {.marimo}
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from owlapy.class_expression import (
    OWLObjectIntersectionOf, OWLObjectOneOf, OWLObjectSomeValuesFrom,
    OWLObjectUnionOf)

sys.path.insert(0, str(mo.notebook_dir() or Path.cwd()))
from financial_ontology import (
    SHARES, conversion, demo, exposure_plan, fetch, history_plan,
    interpreter, merge, netting, path, risk_box, risk_currency, stress_plan)
from discopy.owl import Nothing, label, subsumes
from discopy.utils import AxiomError
```

```python {.marimo}
market = fetch()
fund, model = demo(market)
run = interpreter(fund)
legs = tuple(fund.deltas(unit) for currency in model.currencies
             for unit in fund.quoting(currency))
```

```python {.marimo hide_code="true"}
def table(headers, rows):
    return mo.md(
        "| " + " | ".join(headers) + " |\n| "
        + " | ".join(["---"] * len(headers)) + " |\n"
        + "\n".join("| " + " | ".join(map(str, row)) + " |" for row in rows))
```

```python {.marimo hide_code="true"}
mo.callout(
    f"Quotes as of **{market.asof:%d %B %Y}**, {market.source}, with "
    f"**{len(market.dates)}** daily closes behind the covariance. Re-run "
    "this notebook and every number changes with the market.", kind="info")
```

## 1 · The vocabulary is FIBO's, almost all of it

Loading `Ownership` pulls its whole import closure — `CurrencyAmount`, the
financial dates, the Commons collections — from an offline copy, so the
*schema* never touches the network even though the *quotes* do. Two things
FIBO deliberately leaves open are declared on top: a class per **metric
kind**, because FIBO says a number is a monetary amount but not whether it
is a market value or a value at risk, and two properties saying which
currency a dollar amount is **exposed to** and which FX delta a holding
carries.

```python {.marimo hide_code="true"}
mo.md(f"""
Loaded **{len(fund.world.classes())} classes** and
**{len(fund.world.object_properties())} object properties**, then declared
**{len(fund.kind)} metric kinds** and **2 properties** of our own. The feed
named **{len(market.units())} quoting units** — `{"`, `".join(
    market.units())}` — of which **{len(model.currencies)}** carry risk,
pence folding into pounds. A wire looks like this:

> `{label(fund.amount("FXExposure", "GBp"))}`

— one *pence*-denominated FX exposure, as of one day.
""")
```

## 2 · Pence are not pounds, and priced is not exposed

Two distinctions the feed forces on us, both invisible to a float.

The first is the unit. `ISF.L` reports in `GBp`; `VMID.L`, a London listing
of the same market, reports in `GBP`. They are separate predicates here,
netted apart, and they meet only after each has been converted at *its own*
rate.

The second is what a currency exposure even means. The fund runs a euro
hedge: an overlay priced at **nothing** in dollars that carries a large
negative euro delta. Net by the currency a position is *priced* in and the
hedge lands in the dollar bucket and its euro exposure vanishes from the
report.

```python {.marimo hide_code="true"}
mo.vstack([
    table(["Predicate", "Members"],
          [[f"`{label(fund.bucket('EUR'))}`",
            ", ".join(fund.names(fund.bucket("EUR")))],
           [f"`{label(fund.exposed('EUR'))}`",
            ", ".join(fund.names(fund.exposed("EUR")))]]),
    table(["Holding", "Quoted in", "Price", "Shares", "Market value",
           "FX delta"],
          [[name, unit, f"{price:,.2f}", f"{SHARES.get(name, 0):,}",
            f"{value:,.0f} {unit}", f"{delta:,.0f} {exposure}"]
           for unit in market.units()
           for name, value in zip(fund.names(fund.bucket(unit)),
                                  fund.values(unit))
           for price in [dict(
               (one, quote) for one, (quote, _) in market.prices.items()
           ).get(name, 1.)]
           for exposure, delta in [next(
               ((one, amount) for one in market.units()
                for other, amount in zip(fund.names(fund.exposed(one)),
                                         fund.deltas(one))
                if other == name), ("—", 0.))]])])
```

Every number in that table came out of the ontology: HermiT retrieved the
members of each predicate, followed `hasAcquisitionPrice` or `hasFXDelta`
to the amount, and read `hasAmount` off it. Nothing was kept in Python.

## 3 · Six things proved before a number moves

Each is a question put to HermiT, not a scan of the data. The first four
are FIBO's own cardinality axiom and what follows from it — including that
nothing is priced in pounds *and* pence. The last two are about **dates**,
and they are what lets the same plan be read over a day or over a quarter.

```python {.marimo hide_code="true"}
_today = fund.amount("FXExposure", "USD", to="EUR")
_window = lambda a, b: fund.amount(
    "FXExposure", "USD", fund.during(a, b), to="EUR")
_start = market.dates[0]
_inside = _window(_start, market.asof)
_year = _window(datetime(market.asof.year, 1, 1),
                datetime(market.asof.year, 12, 31))
_before = _window(datetime(_start.year - 1, 1, 1),
                  datetime(_start.year - 1, 12, 31))
table(["Guarantee", "Statement", "Proved"], [
    ["definite unit", "every monetary amount has a currency",
     subsumes(fund.MonetaryAmount, OWLObjectSomeValuesFrom(
         fund.hasCurrency, fund.Currency), fund.world)],
    ["no mixing", "no amount is priced in two currencies",
     subsumes(OWLObjectIntersectionOf(
         (fund.priced("EUR"), fund.priced("USD"))), Nothing, fund.world)],
    ["no pence as pounds", "no amount is priced in both GBP and GBp",
     subsumes(OWLObjectIntersectionOf(
         (fund.priced("GBP"), fund.priced("GBp"))), Nothing, fund.world)],
    ["no leakage", "every holding of the fund is in a unit bucket",
     subsumes(OWLObjectSomeValuesFrom(
         fund.isMemberOf, OWLObjectOneOf((fund.portfolio, ))),
         OWLObjectUnionOf(tuple(map(fund.bucket, market.units()))),
         fund.world)],
    ["a day lies in its window",
     f"{market.asof:%d %b %Y} ⊑ {_start:%d %b %Y}–{market.asof:%d %b %Y}",
     subsumes(_today, _inside, fund.world)],
    ["a window lies in its year",
     f"{_start:%d %b}–{market.asof:%d %b} ⊑ {market.asof.year}",
     subsumes(_inside, _year, fund.world)],
    ["and not in a year it falls outside",
     f"{market.asof:%d %b %Y} ⊑ {_start.year - 1}",
     subsumes(_today, _before, fund.world)],
])
```

## 4 · The exposure plan

Net each quoting unit **in its own unit**, convert it at **its own observed
rate**, and only then add. Each conversion box carries the FIBO
`ExchangeRate` individual it denotes, and the wire below it records that
the result is a dollar amount of exposure to that *currency* — which is
what lets the pound and pence branches meet at a `+` box, and nowhere
earlier.

```python {.marimo hide_code="true"}
exposure_plan(fund, *model.currencies).foliation()
```

```python {.marimo hide_code="true"}
exposure = run(exposure_plan(fund, *model.currencies))(*legs)
nav = sum(sum(fund.values(unit)) * (
    1. if unit == market.reporting else market.spot[unit])
    for unit in market.units())
mo.hstack([
    mo.stat(label="Portfolio NAV", value=f"${nav / 1e6:,.1f}m"),
    *(mo.stat(label=f"Net {one} exposure", value=f"${value / 1e6:,.2f}m")
      for one, value in zip(model.currencies, exposure))], widths="equal")
```

## 5 · The risk plan

One box, five outputs, each on its own predicate: a value at risk and an
expected shortfall in dollars, and one Euler component per factor tagged
with the currency it belongs to. For zero-mean Gaussian returns
$\mathrm{VaR}_\alpha = z_\alpha\sqrt{e^{T}\Sigma e}$, expected shortfall is
$\phi(z_\alpha)\sqrt{e^{T}\Sigma e}/(1-\alpha)$ and component VaR is
$z_\alpha e_c(\Sigma e)_c/\sqrt{e^{T}\Sigma e}$, so the components sum to
the total. $\Sigma$ is estimated from the daily log returns of the spot
history above — no invented volatilities, no invented correlations.

```python {.marimo hide_code="true"}
plan = exposure_plan(fund, *model.currencies) >> risk_box(fund, model)
plan.foliation()
```

```python {.marimo hide_code="true"}
var, shortfall, *components = run(plan)(*legs)
assert abs(sum(components) - var) < 1e-6
mo.vstack([
    mo.hstack([
        mo.stat(label="1-day FX VaR · 99%", value=f"${var:,.0f}"),
        mo.stat(label="1-day expected shortfall · 99%",
                value=f"${shortfall:,.0f}"),
        mo.stat(label="VaR / NAV", value=f"{100 * var / nav:.2f}%")],
        widths="equal"),
    table(["Factor", "Daily volatility", "Component VaR"],
          [[one, f"{100 * np.sqrt(model.covariance[index][index]):.2f}%",
            f"${value:,.0f}"]
           for index, (one, value) in enumerate(
               zip(model.currencies, components))])])
```

The unit of that number is not a caption: it is the codomain of the plan,
read off the diagram — a dollar value at risk, as of the last close.

## 6 · Plans that cannot be written down

Each of the following is a well-intentioned mistake, and two of them are
the ones that cost real money. None produces a wrong number, because none
composes:

```python {.marimo hide_code="true"}
def refused(what, build):
    try:
        build()
    except (AxiomError, ValueError) as error:
        return [what, "refused", f"`{str(error).split(':')[-1].strip()[:84]}`"]
    raise AssertionError(f"accepted: {what}")


table(["Mistake", "Verdict", "Reason"], [
    refused("value a pence holding at the pound rate (100× too big)",
            lambda: netting(fund, "GBp") >> conversion(fund, "GBP")),
    refused("add pence straight into sterling exposure",
            lambda: netting(fund, "GBp") >> merge(fund, "GBP", 1)),
    refused("convert a euro amount at the yen rate",
            lambda: netting(fund, "EUR") >> conversion(fund, "JPY")),
    refused("value today's netting with a rate dated to last year",
            lambda: netting(fund, "EUR") >> conversion(
                fund, "EUR", fund.during(
                    datetime(market.asof.year - 1, 1, 1),
                    datetime(market.asof.year - 1, 12, 31)))),
    refused("feed the risk model its factors in the wrong order",
            lambda: exposure_plan(fund, "JPY", "EUR", "GBP")
            >> risk_box(fund, model)),
    refused("read a day's exposure as if it covered the window",
            lambda: exposure_plan(fund, *model.currencies) >> risk_box(
                fund, model, fund.during(market.dates[0], market.asof))),
    refused("drop a risk factor the fund is exposed to",
            lambda: model.evaluate(exposure[:2])),
])
```

The first two are the hundredfold error, caught by the wire rather than by
a reviewer. The fourth and sixth are the ones a unit checker alone would
miss: every currency agrees and only the **dates** disagree.

## 7 · Stress the portfolio

Shocks are percentage changes in dollars per foreign unit, so a negative
shock is a foreign depreciation. Each contribution stays on its own
`exposureTo` wire until the `+` box, which can only be reached by three
amounts that already agree on currency, metric and date.

```python {.marimo hide_code="true"}
eur_shock = mo.ui.slider(-20, 20, value=-5, label="EUR shock (%)",
                         show_value=True)
jpy_shock = mo.ui.slider(-20, 20, value=-8, label="JPY shock (%)",
                         show_value=True)
gbp_shock = mo.ui.slider(-20, 20, value=-6, label="GBP shock (%)",
                         show_value=True)
mo.hstack([eur_shock, jpy_shock, gbp_shock], widths="equal")
```

```python {.marimo hide_code="true"}
shocks = dict(zip(model.currencies, (
    eur_shock.value / 100, gbp_shock.value / 100, jpy_shock.value / 100)))
scenario = exposure_plan(fund, *model.currencies) >> stress_plan(
    fund, shocks)
pnl = run(scenario)(*legs)
mo.vstack([stress_plan(fund, shocks).foliation(), mo.hstack([
    mo.stat(label="Scenario P&L", value=f"${pnl:,.0f}"),
    mo.stat(label="P&L / NAV", value=f"{100 * pnl / nav:.2f}%"),
    table(["Currency", "Contribution"],
          [[one, f"${value * shocks[one]:,.0f}"]
           for one, value in zip(model.currencies, exposure)])],
    widths="equal")])
```

## 8 · A hedge, and the same plan backtested over the window

Hedging is a change to the inputs, not to the plan: scale the yen delta and
re-run the identical diagram. And because a valuation date is a predicate
like any other, the *window* version is the same diagram with its wires
retyped from one day to an interval — every number becomes an array, and
HermiT's proof that today lies inside the window is what licenses reading
one as the other. The positions are held at today's size and the exchange
rates are the real ones of each day, so the series is a backtest of the
current book rather than a simulation.

```python {.marimo hide_code="true"}
hedge = mo.ui.slider(0, 100, step=5, value=75, show_value=True,
                     label="Hedge the remaining JPY exposure (%)")
hedge
```

```python {.marimo hide_code="true"}
hedged = tuple(
    [value * (1 - hedge.value / 100) for value in leg]
    if risk_currency(unit) == "JPY" else leg
    for leg, unit in zip(legs, [
        unit for currency in model.currencies
        for unit in fund.quoting(currency)]))
hedged_var, _, *hedged_components = run(plan)(*hedged)
dates, series = path(fund, model)
window = history_plan(fund, model, dates[0], dates[-1], series)
var_series, _, *component_series = run(window)()
assert abs(var_series[-1] - var) < 1e-6  # the window ends at the last close
mo.hstack([
    mo.stat(label="FX VaR after the hedge", value=f"${hedged_var:,.0f}"),
    mo.stat(label="VaR reduction",
            value=f"{100 * (1 - hedged_var / var):.1f}%"),
    mo.stat(label="Backtest window", value=f"{len(dates)} trading days")],
    widths="equal")
```

```python {.marimo hide_code="true"}
_figure, _axes = plt.subplots(1, 2, figsize=(13, 4), layout="constrained")
_axes[0].plot(dates, var_series, color="#17395c", label="1-day 99% VaR")
_axes[0].stackplot(dates, np.abs(component_series), alpha=.25,
                   labels=list(model.currencies))
_axes[0].set(title="VaR ⊓ ∃hasCurrency.{USD} ⊓ ∃hasAsOfDate.(window)")
_axes[0].legend(frameon=False, fontsize=8, loc="upper left")
_axes[0].tick_params(axis="x", labelrotation=30)
_y = range(len(model.currencies))
_axes[1].barh([one + .18 for one in _y], components, height=.32,
              color="#17395c", label="Current")
_axes[1].barh([one - .18 for one in _y], hedged_components, height=.32,
              color="#18a999", label="After the hedge")
_axes[1].set(yticks=list(_y), yticklabels=list(model.currencies),
             title="Component VaR · USD")
_axes[1].legend(frameon=False)
for _one in _axes:
    _one.spines[["top", "right"]].set_visible(False)
    _one.grid(axis="x", alpha=.15)
    _one.set_axisbelow(True)
_figure
```

The left panel is the codomain of the window plan plotted directly: a value
at risk, in dollars, dated inside the backtest window. The right panel is
the Euler decomposition before and after the overlay — the other components
*rise* as their share of the smaller total grows, which is the covariance
effect a standalone-volatility report hides.

## What this does and does not certify

The wires certify **meaning, unit and date**, and the reasoner certifies the
schema they rest on. They certify nothing about the market data, the
pricing model or the investment judgement. FX translation risk only, with
fixed linear deltas: no equity, credit, rates, liquidity or option risk.
VaR is a quantile, not a maximum loss; normal returns understate tails;
multi-day scaling is iid square-root-of-time. The covariance is a sample
estimate over one window of history, not a forecast. The hedge is an
idealised zero-cost spot overlay, not a forward valuation with carry.

```python {.marimo hide_code="true"}
mo.callout(
    f"Quotes are real, as of {market.asof:%d %B %Y}. The share counts, the "
    "cash balance and the size of the euro hedge are invented, because a "
    "fund's positions are not public. Nothing here is an order, a "
    "recommendation or investment advice.", kind="warn")
```

## Run it yourself

From the repository root:

```sh
uv run --group all marimo edit docs/notebooks/fx_risk.md
uv run --group all python docs/export_notebooks.py fx_risk
uv run --group all pytest test/financial_ontology.py
```

Reasoning needs a Java runtime, the quotes need a network, and the FIBO
fixtures under `test/fixtures/fibo` are read offline. The tests quote a
fixed snapshot instead of the feed, so they stay deterministic. Keep
`financial_ontology.py` beside this notebook.
