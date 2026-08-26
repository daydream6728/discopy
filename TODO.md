# TODO

> in a new branch, investigate the unit test suite and planify a great purification. classify tests in different categories, extract common patterns that could be property-tested. for now the coverage is only computed for the unit test suite. i want you to quantify the advantage of the property testing suite by running the coverage on the property testing suite only just to try. once you have identified blind spots and classified them, come up with a plan of to integrate new property tests and ramp up the coverage score obtained by proptest/ alone. list all tests that could be subsumed by the unit testing suite and try to maximize LOC removal in test/.

Phase 1 of the approved purification plan: pure deletion of unit tests already
subsumed by the property matrix, `test_repr.py` and `test_conversion.py`.

- [ ] Delete the subsumed tests of `test/cmap.py`
- [ ] Delete the subsumed tests of `test/monoidal.py`
- [ ] Delete the subsumed tests of `test/symmetric.py`
- [ ] Delete the subsumed bits of `test/cat.py`, `test/traced.py`, `test/compact.py` and the hand-rolled `eval(repr)`, functor-preservation, whiskering and snake examples across `test/`
- [ ] Guardrail: unit gate >= 98%, no module drops, subsuming proptest cells pass; record proptest-alone baseline
- [ ] CHANGELOG entry
