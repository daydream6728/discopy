# TODO

> start phase 2 on this branch

Phase 2 of the approved purification plan: cheap ad-hoc properties and the
unit tests they subsume.

- [ ] `proptest/test_serialisation.py`: `from_tree(to_tree(x)) == x` and `loads(dumps(x)) == x` over the carriers
- [ ] `proptest/test_eq_hash.py`: whiskering by the unit preserves equality and hash
- [ ] `proptest/test_normal_form.py`: `normal_form` and `foliation` are idempotent and preserve the diagram
- [ ] `proptest/test_structure.py`: every structural factory of a diagram carrier builds boxes of that carrier
- [ ] `test_conversion.py` sections: `decode(*encode())` and permutation inverse/`to_swaps`
- [ ] Delete the unit tests these subsume, guardrail green after each batch
- [ ] CHANGELOG and CONTRIBUTING updated
