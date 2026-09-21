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
    OWLObjectIntersectionOf, OWLObjectOneOf, OWLObjectSomeValuesFrom,
    OWLObjectUnionOf)

from discopy.owl import Nothing, label, subsumes  # noqa: E402
from discopy.utils import AxiomError  # noqa: E402
from docs.notebooks.financial_ontology import (  # noqa: E402
    SHARES, Market, conversion, demo, exposure_plan, history_plan,
    interpreter, merge, netting, path, risk_box, risk_currency, stress_plan)

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
def legs(fund):
    one, model = fund
    return tuple(one.deltas(unit) for currency in model.currencies
                 for unit in one.quoting(currency))


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


def test_a_pence_leg_is_converted_at_the_pence_rate(fund):
    """The hundredfold trap: 150m pence is $2m, not $200m."""
    one, _ = fund
    pounds = one.market.spot["GBP"]
    assert interpreter(one)(netting(one, "GBp") >> conversion(one, "GBp"))(
        one.deltas("GBp")) == approx(
            1042. * SHARES["uk_large"] * pounds / 100)


def test_exposure_plan_converts_each_leg(fund, legs):
    one, model = fund
    plan = exposure_plan(one, *model.currencies)
    assert interpreter(one)(plan)(*legs) == approx(tuple(
        sum(sum(one.deltas(unit)) * one.market.spot[unit]
            for unit in one.quoting(currency))
        for currency in model.currencies))
    assert label(plan.cod.inside[0].entity).endswith("∃exposureTo.{EUR}")


def test_risk_components_sum_to_var(fund, legs):
    one, model = fund
    run = interpreter(one)
    plan = exposure_plan(one, *model.currencies) >> risk_box(one, model)
    var, shortfall, *components = run(plan)(*legs)
    assert sum(components) == approx(var)
    assert shortfall > var > 0
    assert run(exposure_plan(one, *model.currencies) >> risk_box(
        one, type(model)(model.currencies, model.covariance, model.source,
                         model.confidence, 4)))(*legs)[0] == approx(2 * var)


def test_risk_of_no_exposure_is_zero(fund):
    one, model = fund
    assert interpreter(one)(risk_box(one, model))(0., 0., 0.) == (0., ) * 5


def test_stress_attributes_to_each_currency(fund, legs):
    one, model = fund
    shocks = dict(zip(model.currencies, (-.05, -.08, -.06)))
    run = interpreter(one)
    plan = exposure_plan(one, *model.currencies)
    assert run(plan >> stress_plan(one, shocks))(*legs) == approx(sum(
        value * shocks[currency] for currency, value
        in zip(model.currencies, run(plan)(*legs))))


def test_the_window_plan_backtests_the_same_book(fund, legs):
    one, model = fund
    run = interpreter(one)
    dates, series = path(one, model, days=20)
    window = history_plan(one, model, dates[0], dates[-1], series)
    var, shortfall, *components = run(window)()
    point, _, *_ = run(exposure_plan(one, *model.currencies)
                       >> risk_box(one, model))(*legs)
    assert var.shape == (len(dates), ) and shortfall.shape == var.shape
    assert var[-1] == approx(point)  # the window ends at the valuation date
    assert sum(components)[-1] == approx(point)


def test_mixing_currencies_does_not_compose(fund):
    one, _ = fund
    with raises(AxiomError):
        netting(one, "EUR") >> conversion(one, "JPY")


def test_mixing_pence_and_pounds_does_not_compose(fund):
    one, _ = fund
    with raises(AxiomError):  # the pound rate on a pence amount
        netting(one, "GBp") >> conversion(one, "GBP")
    with raises(AxiomError):  # pence added straight into sterling exposure
        netting(one, "GBp") >> merge(one, "GBP", 1)


def test_mixing_dates_does_not_compose(fund):
    one, model = fund
    with raises(AxiomError):
        netting(one, "EUR") >> conversion(one, "EUR", quarter(one))
    with raises(AxiomError):
        exposure_plan(one, *model.currencies) >> risk_box(
            one, model, quarter(one))


def test_permuted_risk_factors_do_not_compose(fund):
    one, model = fund
    with raises(AxiomError):
        exposure_plan(one, "JPY", "EUR", "GBP") >> risk_box(one, model)


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


def test_a_window_wire_carries_an_array(fund):
    one, model = fund
    run = interpreter(one)
    assert run(risk_box(one, model)).cod == (float, ) * 5
    assert run(risk_box(one, model, quarter(one))).cod == (np.ndarray, ) * 5
    assert run(netting(one, "EUR")).dom == (list, )
