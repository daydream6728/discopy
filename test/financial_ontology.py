# -*- coding: utf-8 -*-

"""The predicates, the plans and the refusals of the FX risk notebook.

The notebook quotes a live feed; these tests quote :func:`market`, a
fixed snapshot, because a test that depends on what the market did today
is not a test. What is exercised is the machinery between the two: which
predicate retrieves which holding, which rate reaches which leg, and
which plans refuse to compose.
"""

import math
from datetime import datetime, timedelta
from shutil import which

import numpy as np
from pytest import approx, fixture, importorskip, raises, skip

importorskip("owlapy")

if which("java") is None:
    skip("owlapy's owlapi bridge needs Java.", allow_module_level=True)

from owlapy.class_expression import (  # noqa: E402
    OWLObjectHasValue, OWLObjectIntersectionOf, OWLObjectOneOf,
    OWLObjectSomeValuesFrom, OWLObjectUnionOf)

from discopy.owl import Nothing, label, subsumes  # noqa: E402
from discopy.utils import AxiomError  # noqa: E402
from docs.notebooks.financial_ontology import (  # noqa: E402
    SHARES, Market, Step, conversion, demo, exposure_plan, hedge,
    interpreter,
    netting, pairing, quotes, regroup, risk_box, risk_currency, select,
    shock, stress_plan)

DAYS = 40


def market() -> Market:
    """A fixed snapshot, shaped like one the feed would give.

    `uk_large` is quoted in pence, as `ISF.L` really is, so the hundred-
    fold trap the notebook shows is under test rather than in prose.
    """
    dates = tuple(datetime(2026, 8, 3) + timedelta(days=one)
                  for one in range(DAYS))
    wave = lambda base, amplitude, period: tuple(
        base * (1 + amplitude * math.sin(one / period))
        for one in range(DAYS))
    history = {"EUR": wave(1.15, .01, 6), "JPY": wave(.0064, .015, 5),
               "GBP": wave(1.34, .012, 7)}
    history["GBp"] = tuple(one / 100 for one in history["GBP"])
    return Market(
        asof=dates[-1], reporting="USD",
        spot={one: values[-1] for one, values in history.items()},
        prices={"us_equity": (768., "USD"), "europe_equity": (210., "EUR"),
                "europe_credit": (116., "EUR"), "japan_equity": (426., "JPY"),
                "uk_large": (1042., "GBp"), "uk_mid": (37., "GBP")},
        dates=dates, history=history, source="fixed quotes for the tests")


@fixture(scope="module")
def fund():
    return demo(market())


@fixture(scope="module")
def book(fund):
    """What the exposure plan takes: a portfolio and a date."""
    one, _ = fund
    return (one, one.market.asof)


def quarter(one):
    return one.during(datetime(2026, 7, 1), datetime(2026, 9, 30))


def test_the_feed_decides_the_units(fund):
    one, model = fund
    assert one.market.units() == ("EUR", "GBP", "GBp", "JPY", "USD")
    assert model.currencies == ("EUR", "GBP", "JPY")  # pence folds into GBP
    assert one.quoting("GBP") == ("GBP", "GBp")
    assert risk_currency("GBp") == "GBP" and risk_currency("USD") == "USD"


def test_priced_is_not_exposed(fund):
    """The hedge is priced in dollars and exposed to euros."""
    one, _ = fund
    assert one.names(one.bucket("EUR")) == [
        "europe_credit", "europe_equity"]
    assert one.names(one.exposed("EUR")) == [
        "europe_credit", "europe_equity", "existing_eur_hedge"]
    assert "existing_eur_hedge" in one.names(one.bucket("USD"))
    assert one.names(one.exposed("GBp")) == ["uk_large"]
    assert one.names(one.exposed("GBP")) == ["uk_mid"]


def test_every_number_comes_from_the_reasoner(fund):
    """Deltas follow hasFXDelta to hasAmount, in retrieval order."""
    one, _ = fund
    assert one.deltas("GBp") == [1042. * SHARES["uk_large"]]
    assert one.values("JPY") == [426. * SHARES["japan_equity"]]
    assert one.observed(one.world.find("uk_mid_price"), one.hasAmount)\
        == 37. * SHARES["uk_mid"]


def test_the_layout_does_not_depend_on_the_assets(fund):
    """The whole point: two portfolios, one diagram.

    A fund of four quoting units and a fund of two give the *same*
    picture, because what varies lives inside the collections rather
    than in the number of wires.
    """
    one, _ = fund
    smaller = market()
    smaller = Market(
        asof=smaller.asof, reporting=smaller.reporting,
        spot={key: value for key, value in smaller.spot.items()
              if key in ("EUR", "JPY")},
        prices={key: value for key, value in smaller.prices.items()
                if value[1] in ("EUR", "JPY", "USD")},
        dates=smaller.dates, history=smaller.history, source=smaller.source)
    other, _ = demo(smaller)
    assert other.market.units() == ("EUR", "JPY", "USD")
    mine, theirs = exposure_plan(one), exposure_plan(other)
    assert (mine.dom, mine.cod) == (theirs.dom, theirs.cod)
    assert [(box.name, box.dom, box.cod) for box in mine.boxes]\
        == [(box.name, box.dom, box.cod) for box in theirs.boxes]
    generators = [(left, right) for left, right
                  in zip(mine.boxes, theirs.boxes)
                  if isinstance(left.data, Step)]
    assert all(left.data != right.data       # only the closures differ
               for left, right in generators)
    assert all(left == right for left, right  # the plumbing is shared
               in zip(mine.boxes, theirs.boxes)
               if not isinstance(left.data, Step))


def test_every_box_has_a_fixed_arity(fund):
    one, model = fund
    plan = exposure_plan(one) >> risk_box(one, model)
    assert [(len(box.dom), len(box.cod)) for box in plan.boxes] == [
        (1, 2), (1, 1), (2, 1), (1, 1), (2, 1), (1, 1), (1, 1), (1, 3)]
    assert len(plan.dom) == 2 and len(plan.cod) == 3


def test_a_pence_holding_is_converted_at_the_pence_rate(fund, book):
    """The hundredfold trap: 150m pence is $2m, not $200m."""
    one, _ = fund
    bag = interpreter(one)(exposure_plan(one))(*book)
    pounds = one.market.spot["GBP"]
    assert bag["GBP"] == approx(
        1042. * SHARES["uk_large"] * pounds / 100
        + 37. * SHARES["uk_mid"] * pounds)


def test_the_plan_takes_only_a_portfolio_and_a_date(fund):
    one, _ = fund
    plan = exposure_plan(one)
    assert [label(wire.entity) for wire in plan.dom.inside] == [
        "Portfolio", "{" + one.market.asof.date().isoformat() + "}"]


def test_the_rate_is_an_input_not_a_coefficient(fund):
    """Quoting is its own box, so no rate is compiled into a conversion."""
    one, _ = fund
    boxes = {box.name: box for box in exposure_plan(one).boxes}
    assert boxes["×"].data.entity is None      # the converter denotes nothing
    assert boxes["quotes in USD"].data.entity is one.ExchangeRate
    assert all(not isinstance(box.name, float) and "×0" not in box.name
               and "×1" not in box.name for box in exposure_plan(one).boxes)


def test_another_date_gives_another_answer(fund):
    """The coefficient is read off the feed by the date flowing in."""
    one, _ = fund
    run, early = interpreter(one), one.market.dates[0]
    first = run(exposure_plan(one, when=one.on(early)))(one, early)
    assert first["EUR"] == approx(
        sum(one.deltas("EUR")) * one.market.rate("EUR", early))
    assert first["EUR"] != approx(
        run(exposure_plan(one))(one, one.market.asof)["EUR"])


def test_risk_components_sum_to_var(fund, book):
    one, model = fund
    run = interpreter(one)
    var, shortfall, components = run(
        exposure_plan(one) >> risk_box(one, model))(*book)
    assert sum(components.values()) == approx(var)
    assert set(components) == set(model.currencies)
    assert shortfall > var > 0
    assert run(exposure_plan(one) >> risk_box(one, type(model)(
        model.currencies, model.covariance, model.source,
        model.confidence, 4)))(*book)[0] == approx(2 * var)


def test_risk_of_no_exposure_is_zero(fund):
    one, model = fund
    var, shortfall, components = interpreter(one)(risk_box(one, model))(
        {one: 0. for one in model.currencies})
    assert (var, shortfall) == (0., 0.)
    assert set(components.values()) == {0.}


def test_stress_attributes_to_each_currency(fund, book):
    one, model = fund
    shocks = dict(zip(model.currencies, (-.05, -.08, -.06)))
    run = interpreter(one)
    bag = run(exposure_plan(one))(*book)
    assert run(exposure_plan(one) >> stress_plan(one, shocks))(*book)\
        == approx(sum(bag[one] * ratio for one, ratio in shocks.items()))


def test_a_hedge_only_touches_its_own_currency(fund, book):
    one, model = fund
    run = interpreter(one)
    bag = run(exposure_plan(one))(*book)
    hedged = run(exposure_plan(one) >> hedge(one, "JPY", .75))(*book)
    assert hedged["JPY"] == approx(.25 * bag["JPY"])
    assert hedged["EUR"] == approx(bag["EUR"])
    assert hedged["GBP"] == approx(bag["GBP"])


def test_the_window_is_the_same_plan_retyped(fund, book):
    """One diagram, a day or an interval, scalars or arrays."""
    one, model = fund
    run = interpreter(one)
    dates = one.market.dates[-20:]
    when = one.during(dates[0], dates[-1])
    var, shortfall, components = run(
        exposure_plan(one, when) >> risk_box(one, model, when))(
            one, np.array(dates))
    point, _, _ = run(exposure_plan(one) >> risk_box(one, model))(*book)
    assert var.shape == (len(dates), ) and shortfall.shape == var.shape
    assert var[-1] == approx(point)  # the window ends at the valuation date
    assert sum(components.values())[-1] == approx(point)


def test_a_mismatched_valuation_is_refuted(fund):
    """The guarantee a per-currency wire used to give, now an axiom.

    It holds for every unit the feed names, not only the ones a plan
    happened to wire up, which is what buys the fixed layout. Asked as
    a subsumption, so nothing is written into the world to ask it.
    """
    one, _ = fund
    mixed = lambda amount, quote: OWLObjectIntersectionOf((
        one.Valuation,
        OWLObjectSomeValuesFrom(one.hasExposure, OWLObjectHasValue(
            one.hasCurrency, one.money[amount])),
        OWLObjectSomeValuesFrom(one.hasQuotation, OWLObjectHasValue(
            one.hasBaseCurrency, one.money[quote]))))
    for amount, quote in (("EUR", "JPY"), ("GBP", "GBp"), ("GBp", "GBP"),
                          ("JPY", "USD")):
        assert subsumes(mixed(amount, quote), Nothing, one.world)
    for matched in ("EUR", "GBp", "JPY"):
        assert not subsumes(mixed(matched, matched), Nothing, one.world)


def test_the_stages_do_not_compose_out_of_order(fund):
    """Every collection wire says what it holds, so the order is forced."""
    one, model = fund
    for left, right in (
            (select(one), conversion(one)),        # holdings are not pairings
            (netting(one), risk_box(one, model)),  # unconverted is not risk
            (quotes(one), conversion(one)),        # rates are not pairings
            (netting(one), regroup(one)),          # local is not reporting
            (shock(one, {}), risk_box(one, model)),   # P&L is not exposure
            (conversion(one), pairing(one))):      # converted is not to pair
        with raises(AxiomError):
            left >> right


def test_mixing_dates_does_not_compose(fund):
    one, model = fund
    with raises(AxiomError):
        exposure_plan(one) >> risk_box(one, model, quarter(one))
    with raises(AxiomError):
        exposure_plan(one, quarter(one)) >> risk_box(one, model)


def test_a_missing_risk_factor_is_refused(fund):
    _, model = fund
    with raises(ValueError, match="One exposure per"):
        model.evaluate((1e6, 2e6))


def test_the_model_refuses_an_impossible_covariance(fund):
    _, model = fund
    build = lambda **kwargs: type(model)(**{
        "currencies": model.currencies, "covariance": model.covariance,
        "source": model.source, **kwargs})
    for covariance in (
            ((1., 2., 0.), (2., 1., 0.), (0., 0., 1.)),   # not PSD
            ((1., .1, 0.), (.2, 1., 0.), (0., 0., 1.)),   # not symmetric
            ((1., 0.), (0., 1.))):                        # wrong shape
        with raises(ValueError):
            build(covariance=covariance)
    for kwargs in ({"days": 0}, {"confidence": 1.}, {"source": " "},
                   {"currencies": ("EUR", "EUR", "EUR")}):
        with raises(ValueError):
            build(**kwargs)


def test_the_covariance_is_estimated_from_the_history(fund):
    one, model = fund
    matrix = np.asarray(model.covariance)
    assert matrix.shape == (3, 3)
    assert np.allclose(matrix, matrix.T, rtol=0, atol=1e-14)
    assert np.linalg.eigvalsh(matrix).min() >= -1e-14
    assert one.market.covariance("GBP")[0][0] == approx(
        one.market.covariance("GBp")[0][0])  # one return, two units


def test_the_reasoner_proves_the_schema(fund):
    one, _ = fund
    assert subsumes(one.MonetaryAmount, OWLObjectSomeValuesFrom(
        one.hasCurrency, one.Currency), one.world)
    assert subsumes(OWLObjectIntersectionOf(
        (one.priced("EUR"), one.priced("USD"))), Nothing, one.world)
    assert subsumes(OWLObjectIntersectionOf(
        (one.priced("GBP"), one.priced("GBp"))), Nothing, one.world)
    assert subsumes(OWLObjectSomeValuesFrom(
        one.isMemberOf, OWLObjectOneOf((one.portfolio, ))),
        OWLObjectUnionOf(tuple(map(one.bucket, one.market.units()))),
        one.world)


def test_the_reasoner_places_a_date_in_its_window(fund):
    one, _ = fund
    today = one.amount("FXExposure", "USD", to="EUR")
    window = lambda a, b: one.amount(
        "FXExposure", "USD", one.during(a, b), to="EUR")
    year = window(datetime(2026, 1, 1), datetime(2026, 12, 31))
    assert subsumes(today, window(
        datetime(2026, 8, 1), datetime(2026, 9, 30)), one.world)
    assert not subsumes(today, window(
        datetime(2026, 1, 1), datetime(2026, 6, 30)), one.world)
    assert subsumes(window(
        datetime(2026, 8, 1), datetime(2026, 9, 30)), year, one.world)
    assert not subsumes(year, window(
        datetime(2026, 8, 1), datetime(2026, 9, 30)), one.world)


def test_a_collection_wire_carries_a_keyed_bag(fund):
    one, model = fund
    run = interpreter(one)
    assert run(select(one)).dom == (type(one), )
    assert run(select(one)).cod == (dict, )
    assert run(risk_box(one, model)).cod == (float, float, dict)
    assert run(risk_box(one, model, quarter(one))).cod == (
        np.ndarray, np.ndarray, dict)
