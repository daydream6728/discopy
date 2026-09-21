# -*- coding: utf-8 -*-

"""FX risk typed by FIBO's own predicates.

Every wire of the numeric plans below is a FIBO class expression saying
what a number measures, in which currency and on which date. DisCoPy
checks composition before a number flows and HermiT decides every
predicate change, so a plan that mixes currencies or dates cannot be
written down at all.

Numbers stay numbers. The ontology holds what is *observed* -- holdings,
prices, exchange rates, valuation dates -- and NumPy holds what is
*computed* -- covariances, quantiles, attributions. A description logic
has no arithmetic, so no result is ever written back as an individual;
the wire is the contract between the two halves.

The only schema authored here is what FIBO does not say: what a number
measures (`MarketValue`, `VaR`, ...) and which currency a dollar amount
is exposed to. Everything else -- monetary amounts, their definite
currency, exchange rates, portfolios, holdings, as-of dates -- is FIBO's
own, read from the offline fixtures in ``test/fixtures/fibo``.

Quotes are real. :func:`fetch` pulls spot rates, instrument prices and a
year of daily history from Yahoo Finance, and the covariance is estimated
from those returns rather than invented. Only the share counts are made
up, because a fund's positions are not public. A :class:`Market` is an
argument everywhere, so the notebook can pass a live fetch while the
tests pass fixed quotes: the feed decides the numbers, never the code.

One thing the feed decides is the *unit*. `ISF.L` is quoted in `GBp`,
pence rather than pounds, so a plan that reads 1042 GBp as 1042 GBP is
wrong by a factor of a hundred. Pence is a quoting unit of its own here,
with its own `ExchangeRate`, and the conversion is a box in the diagram
like any other.
"""

import os
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from statistics import NormalDist

import numpy as np
from owlapy.class_expression import (
    OWLDataSomeValuesFrom, OWLDatatypeRestriction, OWLFacetRestriction,
    OWLObjectAllValuesFrom, OWLObjectHasValue, OWLObjectIntersectionOf,
    OWLObjectSomeValuesFrom, OWLObjectUnionOf)
from owlapy.iri import IRI
from owlapy.owl_axiom import (
    OWLClassAssertionAxiom, OWLDataPropertyAssertionAxiom,
    OWLDeclarationAxiom, OWLDifferentIndividualsAxiom,
    OWLObjectPropertyDomainAxiom, OWLObjectPropertyRangeAxiom,
    OWLSubClassOfAxiom)
from owlapy.owl_literal import DateTimeOWLDatatype, OWLLiteral
from owlapy.owl_property import OWLObjectProperty
from owlapy.vocab import OWLFacet

from discopy import python
from discopy.owl import (
    Box, Functor, Id, Relation, instances, load, name_of, ob)

FIBO = "https://spec.edmcouncil.org/fibo/ontology/"
FIXTURES = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir,
    "test", "fixtures", "fibo")
KINDS = ("MarketValue", "FXExposure", "PnL", "VaR", "ExpectedShortfall",
         "ComponentVaR")
PAIRS = {"EUR": "EURUSD=X", "JPY": "JPYUSD=X", "GBP": "GBPUSD=X"}
""" The FX pairs quoting one foreign unit in the reporting currency. """

TICKERS = {"us_equity": "SPY", "europe_equity": "EXS1.DE",
           "europe_credit": "IEAC.AS", "japan_equity": "1306.T",
           "uk_large": "ISF.L", "uk_mid": "VMID.L"}
""" The instruments the demonstration fund holds, priced by the feed. """

SHARES = {"us_equity": 5200, "europe_equity": 14250,
          "europe_credit": 17200, "japan_equity": 1173000,
          "uk_large": 144000, "uk_mid": -13400}
""" How many of each -- the one thing here that is made up. """


def risk_currency(unit: str) -> str:
    """The currency a quoting unit belongs to.

    A minor unit is written like its major one with the last letter in
    lower case -- `ISF.L` is quoted in `GBp`, pence -- so upper-casing
    the code names the currency whose risk it carries.
    """
    return unit.upper()


@dataclass(frozen=True)
class Market:
    """One dated snapshot of quotes, and the history behind it.

    Parameters:
        asof : The date the quotes close on.
        reporting : The currency every plan reports in.
        spot : Reporting currency per one unit, for each quoting unit.
        prices : The price and quoting unit of each instrument.
        dates : The days of the history, oldest first.
        history : The daily spot of each unit over those days.
        source : Where the quotes came from.
    """

    asof: datetime
    reporting: str
    spot: dict
    prices: dict
    dates: tuple
    history: dict
    source: str

    def units(self) -> tuple:
        """Every quoting unit, the reporting currency included."""
        return tuple(sorted({self.reporting, *self.spot} | {
            unit for _, unit in self.prices.values()}))

    def currencies(self) -> tuple:
        """The foreign currencies carrying risk, minor units folded in."""
        return tuple(sorted({
            risk_currency(one) for one in self.units()} - {self.reporting}))

    def covariance(self, *currencies: str) -> tuple:
        """The daily return covariance of some currencies, as estimated.

        Log returns of the spot history, which is what the Gaussian
        model of :class:`RiskModel` assumes; the matrix is symmetric and
        positive semidefinite by construction.
        """
        returns = np.diff(np.log(np.array(
            [self.history[one] for one in currencies], dtype=float)), axis=1)
        return tuple(map(tuple, np.atleast_2d(np.cov(returns))))


def fetch(reporting: str = "USD", years: int = 1) -> Market:
    """Real quotes from Yahoo Finance, through `yfinance`.

    One download for every symbol, forward-filled across the holidays
    that differ between Frankfurt, Tokyo, London and New York, and the
    quoting unit of each instrument read off the feed rather than
    assumed -- `ISF.L` comes back in pence.

    Parameters:
        reporting : The currency to quote everything in.
        years : How much daily history to estimate the covariance from.
    """
    import yfinance
    symbols = list(PAIRS.values()) + list(TICKERS.values())
    close = yfinance.download(
        symbols, period=f"{years}y", interval="1d", progress=False,
        auto_adjust=True)["Close"].ffill().dropna()
    if close.empty:
        raise RuntimeError("Yahoo Finance returned no quotes.")
    unit_of = {name: yfinance.Ticker(symbol).fast_info["currency"]
               for name, symbol in TICKERS.items()}
    spot = {one: float(close[symbol].iloc[-1])
            for one, symbol in PAIRS.items()}
    history = {one: tuple(map(float, close[symbol]))
               for one, symbol in PAIRS.items()}
    minor = {one for one in unit_of.values()
             if one not in spot and one != reporting}
    for unit in minor:
        if risk_currency(unit) not in spot:
            raise RuntimeError(f"No quote for {unit}.")
        spot[unit] = spot[risk_currency(unit)] / 100
        history[unit] = tuple(
            one / 100 for one in history[risk_currency(unit)])
    return Market(
        asof=close.index[-1].to_pydatetime(), reporting=reporting,
        spot=spot, dates=tuple(
            one.to_pydatetime() for one in close.index),
        prices={name: (float(close[TICKERS[name]].iloc[-1]), unit_of[name])
                for name in TICKERS},
        history=history, source="Yahoo Finance daily close, via yfinance")


class Fund:
    """A portfolio of dated FIBO amounts, and the world that judges it.

    Loading `Ownership` pulls its whole import closure, `CurrencyAmount`
    and the Commons dates included. On top of it this declares the two
    things FIBO leaves open: a class per metric kind, and `exposureTo`,
    the currency a reporting-currency amount is exposed to.
    """

    def __init__(self, market: Market):
        self.market = market
        self.asof, self.reporting = market.asof, market.reporting
        self.world = load(
            FIBO + "FND/OwnershipAndControl/Ownership/", path=FIXTURES)
        find = self.world.find
        self.MonetaryAmount = find("CurrencyAmount/MonetaryAmount")
        self.MonetaryPrice = find("CurrencyAmount/MonetaryPrice")
        self.Currency = find("CurrencyAmount/Currency")
        self.ExchangeRate = find("CurrencyAmount/ExchangeRate")
        self.hasCurrency = find("CurrencyAmount/hasCurrency")
        self.hasBaseCurrency = find("CurrencyAmount/hasBaseCurrency")
        self.hasDealtCurrency = find("CurrencyAmount/hasDealtCurrency")
        self.hasRateValue = find("CurrencyAmount/hasRateValue")
        self.hasAmount = find("CurrencyAmount/hasAmount")
        self.Portfolio = find("Ownership/Portfolio")
        self.Holding = find("Ownership/Holding")
        self.hasAcquisitionPrice = find("Ownership/hasAcquisitionPrice")
        self.comprises = find("Collections/comprises")
        self.isMemberOf = find("Collections/isMemberOf")
        self.hasAsOfDate = find("FinancialDates/hasAsOfDate")
        self.ExplicitDate = find("DatesAndTimes/ExplicitDate")
        self.hasObservedDateTime = find("DatesAndTimes/hasObservedDateTime")
        self.kind = {name: self.world.owl_class(name) for name in KINDS}
        self.world.add(*(OWLSubClassOfAxiom(one, self.MonetaryAmount)
                         for one in self.kind.values()))
        self.exposureTo = OWLObjectProperty(
            IRI.create(self.world.iri + "exposureTo"))
        self.hasFXDelta = OWLObjectProperty(
            IRI.create(self.world.iri + "hasFXDelta"))
        self.world.add(
            OWLDeclarationAxiom(self.exposureTo),
            OWLObjectPropertyRangeAxiom(self.exposureTo, self.Currency),
            OWLDeclarationAxiom(self.hasFXDelta),
            OWLObjectPropertyDomainAxiom(self.hasFXDelta, self.Holding),
            OWLObjectPropertyRangeAxiom(
                self.hasFXDelta, self.kind["FXExposure"]))
        self.money = {unit: self.world.individual(unit, self.Currency)
                      for unit in market.units()}
        self.world.add(
            OWLDifferentIndividualsAxiom(list(self.money.values())))
        self.portfolio = self.world.individual("fund", self.Portfolio)
        self.dates, self.rates, self.holdings = {}, {}, {}
        for unit, value in sorted(market.spot.items()):
            self.quote(unit, value, market.source)

    def day(self, moment: datetime):
        """The `ExplicitDate` individual of a moment, observed as such."""
        name = moment.date().isoformat()
        if name not in self.dates:
            self.dates[name] = self.world.individual(name, self.ExplicitDate)
            self.world.add(OWLDataPropertyAssertionAxiom(
                self.dates[name], self.hasObservedDateTime,
                OWLLiteral(moment)))
        return self.dates[name]

    def on(self, moment: datetime):
        """The predicate of an observation dated to one day."""
        return OWLObjectHasValue(self.hasAsOfDate, self.day(moment))

    def during(self, start: datetime, end: datetime):
        """The predicate of an observation dated inside a window."""
        return OWLObjectSomeValuesFrom(
            self.hasAsOfDate, OWLObjectIntersectionOf((
                self.ExplicitDate, OWLDataSomeValuesFrom(
                    self.hasObservedDateTime, OWLDatatypeRestriction(
                        DateTimeOWLDatatype, (
                            OWLFacetRestriction(
                                OWLFacet.MIN_INCLUSIVE, OWLLiteral(start)),
                            OWLFacetRestriction(
                                OWLFacet.MAX_INCLUSIVE, OWLLiteral(end))))))))

    def priced(self, currency: str):
        """A monetary amount in one currency, FIBO's own construct."""
        return OWLObjectIntersectionOf((
            self.MonetaryAmount,
            OWLObjectHasValue(self.hasCurrency, self.money[currency])))

    def bucket(self, currency: str):
        """A holding whose acquisition price is in one currency."""
        return OWLObjectIntersectionOf((
            self.Holding, OWLObjectSomeValuesFrom(
                self.hasAcquisitionPrice, self.priced(currency))))

    def exposed(self, currency: str):
        """A holding whose FX delta is in one currency.

        Not the same predicate as :meth:`bucket`: a hedge is priced at
        nothing in the reporting currency and carries a large delta in
        the currency it hedges, so netting by price would lose it.
        """
        return OWLObjectIntersectionOf((
            self.Holding, OWLObjectSomeValuesFrom(
                self.hasFXDelta, OWLObjectHasValue(
                    self.hasCurrency, self.money[currency]))))

    def amount(self, metric: str, currency: str, when=None, to: str = None):
        """What a number measures, in which currency, when, exposed to what.

        Parameters:
            metric : The metric kind, one of :data:`KINDS`.
            currency : The currency of the amount itself.
            when : The date predicate, :meth:`on` the valuation date by
                default, :meth:`during` a window for a series.
            to : The currency the amount is exposed to, if any.
        """
        when = self.on(self.asof) if when is None else when
        inside = (self.kind[metric],
                  OWLObjectHasValue(self.hasCurrency, self.money[currency]),
                  when)
        if to is not None:
            inside += (OWLObjectHasValue(self.exposureTo, self.money[to]), )
        return OWLObjectIntersectionOf(inside)

    def hold(self, name: str, unit: str, value: float, delta: float,
             source: str, exposure_to: str = None):
        """Add a holding: a priced position and its local FX delta.

        A local delta is dV/dS with S the reporting currency per local
        unit. For the linear positions here it equals the local market
        value; a derivative's delta is a pricing-model input and is
        never inferred from its market value: a hedge is priced at
        nothing and still carries one, in the currency it hedges, which
        is what ``exposure_to`` says.
        """
        exposure_to = unit if exposure_to is None else exposure_to
        price = self.world.individual(name + "_price", self.MonetaryPrice)
        self.world.relate(price, self.hasCurrency, self.money[unit])
        self.world.add(OWLDataPropertyAssertionAxiom(
            price, self.hasAmount, OWLLiteral(Decimal(str(value)))))
        exposure = self.world.individual(
            name + "_delta", self.kind["FXExposure"])
        self.world.relate(
            exposure, self.hasCurrency, self.money[exposure_to])
        self.world.relate(exposure, self.hasAsOfDate, self.day(self.asof))
        self.world.add(OWLDataPropertyAssertionAxiom(
            exposure, self.hasAmount, OWLLiteral(Decimal(str(delta)))))
        holding = self.world.individual(name, self.Holding)
        self.world.relate(holding, self.hasAcquisitionPrice, price)
        self.world.relate(holding, self.hasFXDelta, exposure)
        self.world.relate(self.portfolio, self.comprises, holding)
        self.holdings[name] = source
        return holding

    def quote(self, base: str, value: float, source: str):
        """Add an `ExchangeRate`: reporting currency per one base unit."""
        rate = self.world.individual(base + self.reporting, self.ExchangeRate)
        self.world.relate(rate, self.hasBaseCurrency, self.money[base])
        self.world.relate(
            rate, self.hasDealtCurrency, self.money[self.reporting])
        self.world.add(OWLDataPropertyAssertionAxiom(
            rate, self.hasRateValue, OWLLiteral(Decimal(str(value)))))
        self.rates[base] = (rate, float(value), source)
        return rate

    def mandate(self):
        """Declare that the fund holds nothing outside its quoting units."""
        self.world.add(OWLClassAssertionAxiom(
            self.portfolio, OWLObjectAllValuesFrom(
                self.comprises, OWLObjectUnionOf(
                    tuple(map(self.bucket, self.market.units()))))))

    def quoting(self, currency: str) -> tuple:
        """The quoting units whose risk is that of one currency.

        Pounds and pence are two units of one risk, so the pound leg of
        a plan has two branches that meet once both are converted.
        """
        return tuple(one for one in self.market.units()
                     if risk_currency(one) == currency)

    def members(self, predicate) -> tuple:
        """The individuals HermiT retrieves for a predicate."""
        return instances(predicate, self.world)

    def names(self, predicate) -> list:
        """The short names of the individuals a predicate retrieves."""
        return [name_of(one) for one in self.members(predicate)]

    def observed(self, individual, prop) -> float:
        """The one value the reasoner entails for a data property."""
        value, = self.world.reasoner.data_property_values(individual, prop)
        return float(value.to_python())

    def amounts(self, prop, predicate) -> list:
        """Follow a property from every member of a predicate to a number.

        Every step is a reasoner call: which holdings the predicate
        retrieves, which amount each relates to, and what that amount is
        worth. Nothing here is read out of Python state.
        """
        related = dict(
            (x, y) for (x, ), (y, ) in Relation.from_property(
                prop, self.world).inside)
        return [self.observed(related[one], self.hasAmount)
                for one in self.members(predicate)]

    def deltas(self, currency: str) -> list:
        """The FX deltas of the holdings exposed to one currency."""
        return self.amounts(self.hasFXDelta, self.exposed(currency))

    def values(self, currency: str) -> list:
        """The acquisition prices of the holdings priced in one currency."""
        return self.amounts(self.hasAcquisitionPrice, self.bucket(currency))


@dataclass(frozen=True)
class Step:
    """What a box means: the function it runs, the individual it denotes."""

    run: object
    entity: object = None


def netting(fund: Fund, unit: str, when=None) -> Box:
    """Net the FX deltas of a quoting unit into one dated amount."""
    return Box(
        "net", ob((fund.exposed(unit), )),
        ob((fund.amount("FXExposure", unit, when), )),
        data=Step(lambda deltas: float(sum(deltas))))


def conversion(fund: Fund, unit: str, when=None) -> Box:
    """One `ExchangeRate` of the ontology, carried as the box's data.

    The result is a reporting-currency amount of exposure to the
    *currency* of the unit, so a pence leg and a pound leg land on the
    same predicate and can then be added.
    """
    rate, value, _ = fund.rates[unit]
    return Box(
        f"×{value:.6g}", ob((fund.amount("FXExposure", unit, when), )),
        ob((fund.amount("FXExposure", fund.reporting, when,
                        to=risk_currency(unit)), )),
        data=Step(lambda amount: amount * value, rate))


def merge(fund: Fund, currency: str, arity: int, when=None) -> Box:
    """Add the reporting-currency exposures of one currency's units."""
    wire = fund.amount("FXExposure", fund.reporting, when, to=currency)
    return Box("+", ob(arity * (wire, )), ob((wire, )),
               data=Step(lambda *xs: sum(xs)))


def exposure_plan(fund: Fund, *currencies: str, when=None):
    """Net each quoting unit, convert it, then merge the units of one risk.

    Pounds and pence are netted apart, being different predicates, and
    meet only once both have become reporting-currency amounts of
    sterling exposure.
    """
    legs = []
    for currency in currencies:
        units = fund.quoting(currency)
        leg = Id().tensor(*(netting(fund, one, when)
                            >> conversion(fund, one, when) for one in units))
        legs.append(leg if len(units) == 1
                    else leg >> merge(fund, currency, len(units), when))
    return Id().tensor(*legs)


def risk_box(fund: Fund, model: "RiskModel", when=None) -> Box:
    """Covariance FX risk: the same box on a day or over a window."""
    exposure = tuple(
        fund.amount("FXExposure", fund.reporting, when, to=one)
        for one in model.currencies)
    component = tuple(
        fund.amount("ComponentVaR", fund.reporting, when, to=one)
        for one in model.currencies)
    return Box(
        f"VaR {model.confidence:.0%} · {model.days}d", ob(exposure),
        ob((fund.amount("VaR", fund.reporting, when),
            fund.amount("ExpectedShortfall", fund.reporting, when))
           + component),
        data=Step(lambda *xs: model.evaluate(xs)))


def shock(fund: Fund, currency: str, ratio: float) -> Box:
    """A first-order scenario move in the reporting currency per unit."""
    return Box(
        f"{ratio:+.0%}",
        ob((fund.amount("FXExposure", fund.reporting, to=currency), )),
        ob((fund.amount("PnL", fund.reporting, to=currency), )),
        data=Step(lambda amount: amount * ratio))


def total(fund: Fund, *currencies: str) -> Box:
    """Sum the scenario contributions, which share one currency and date."""
    return Box(
        "+", ob(tuple(fund.amount("PnL", fund.reporting, to=one)
                      for one in currencies)),
        ob((fund.amount("PnL", fund.reporting), )),
        data=Step(lambda *xs: float(sum(xs))))


def stress_plan(fund: Fund, shocks: dict):
    """Shock each exposure, then add what is now commensurable."""
    return Id().tensor(*(
        shock(fund, one, ratio) for one, ratio in shocks.items()
    )) >> total(fund, *shocks)


def history(fund: Fund, currency: str, start, end, series) -> Box:
    """A dated series of reporting-currency exposure to one currency."""
    return Box(
        f"{currency} history", ob(()),
        ob((fund.amount("FXExposure", fund.reporting,
                        fund.during(start, end), to=currency), )),
        data=Step(lambda: np.asarray(series, dtype=float)))


def history_plan(fund: Fund, model: "RiskModel", start, end, series: dict):
    """The risk plan retyped from one day to a window: same shape, arrays."""
    return Id().tensor(*(
        history(fund, one, start, end, series[one])
        for one in model.currencies
    )) >> risk_box(fund, model, fund.during(start, end))


def interpreter(fund: Fund) -> Functor:
    """Evaluate a plan: predicates to carriers, boxes to Python functions.

    A wire carries a list when it is a bucket of holdings, an array when
    its date is a window rather than a day, and a float otherwise.
    """
    def carrier(wire):
        inside = tuple(wire.entity.operands()) if isinstance(
            wire.entity, OWLObjectIntersectionOf) else (wire.entity, )
        if fund.Holding in inside:
            return list
        return np.ndarray if any(
            isinstance(one, OWLObjectSomeValuesFrom)
            and one.get_property() == fund.hasAsOfDate
            for one in inside) else float
    return Functor(ob_map=lambda typ: tuple(map(carrier, typ.inside)),
                   ar_map=lambda box: box.data.run, cod=python.Function)


@dataclass(frozen=True)
class RiskModel:
    """Dated daily simple-return covariance, in named currency order.

    Zero mean, Gaussian returns, fixed linear deltas and iid time
    scaling. Component VaR is the Euler allocation, so it sums to the
    total and is negative for a diversifier; it is a covariance-aware
    contribution, not a standalone loss.
    """

    currencies: tuple
    covariance: tuple
    source: str
    confidence: float = .99
    days: int = 1

    def __post_init__(self):
        matrix = np.asarray(self.covariance, dtype=float)
        if not self.currencies or len(set(self.currencies)) != len(
                self.currencies):
            raise ValueError("Risk factors must be distinct currencies.")
        if (matrix.shape != (len(self.currencies), ) * 2
                or not np.isfinite(matrix).all()
                or not np.allclose(matrix, matrix.T, rtol=0, atol=1e-14)
                or np.linalg.eigvalsh(matrix).min() < -1e-14):
            raise ValueError("Covariance must be finite, symmetric and PSD.")
        if not .5 < self.confidence < 1 or type(self.days) is not int\
                or self.days < 1 or not self.source.strip():
            raise ValueError("Invalid confidence, horizon or model source.")

    def evaluate(self, exposures) -> tuple:
        """Value at risk, expected shortfall and the Euler components.

        One row per date, so the same model reads a day or a window; a
        single date comes back as floats rather than arrays of one.
        """
        rows = np.atleast_2d(np.stack(
            [np.asarray(one, dtype=float) for one in exposures], axis=-1))
        if rows.shape[-1] != len(self.currencies):
            raise ValueError("One exposure per declared risk factor.")
        covariance = np.asarray(self.covariance, dtype=float) * self.days
        sigma = np.sqrt(np.maximum(0., np.einsum(
            "ij,jk,ik->i", rows, covariance, rows)))
        normal = NormalDist()
        z = normal.inv_cdf(self.confidence)
        safe = np.where(sigma > 0, sigma, 1.)
        components = z * rows * (rows @ covariance) / safe[:, None]
        result = (z * sigma, sigma * normal.pdf(z) / (1 - self.confidence)
                  ) + tuple(components.T)
        return tuple(one[0] if one.shape == (1, ) else one for one in result)


def demo(market: Market = None) -> tuple:
    """A fund of real instruments at real prices, in made-up size.

    The quotes, the exchange rates and the covariance are whatever the
    feed says on the day; only :data:`SHARES`, the cash balance and the
    size of the euro hedge are invented, because a fund's positions are
    not public. The hedge is priced at nothing and carries a euro delta,
    so it shows up in the currency it is exposed to and not in the one
    it is priced in.

    Parameters:
        market : The quotes to build on, a live :func:`fetch` by default.
    """
    market = fetch() if market is None else market
    fund = Fund(market)
    for name, shares in SHARES.items():
        price, unit = market.prices[name]
        fund.hold(name, unit, price * shares, price * shares, market.source)
    fund.hold("usd_cash", market.reporting, 1.82e6, 1.82e6,
              "Synthetic cash balance")
    euro = sum(price * SHARES[name] for name, (price, unit)
               in market.prices.items() if unit == "EUR")
    fund.hold("existing_eur_hedge", market.reporting, 0., -.6 * euro,
              "Synthetic spot-delta overlay", exposure_to="EUR")
    fund.mandate()
    currencies = market.currencies()
    return fund, RiskModel(
        currencies, market.covariance(*currencies),
        f"Daily log-return covariance, {len(market.dates)} days, "
        f"{market.source}")


def path(fund: Fund, model: RiskModel, days: int = 65) -> tuple:
    """The fund's reporting-currency exposure on each of the last days.

    The positions are held at today's size and the exchange rates are
    the real ones of those days, so the window plan is a backtest of
    the current book rather than a simulation.
    """
    market, series = fund.market, {}
    for currency in model.currencies:
        series[currency] = sum(
            sum(fund.deltas(unit))
            * np.array(market.history[unit][-days:], dtype=float)
            for unit in fund.quoting(currency))
    return market.dates[-days:], series
