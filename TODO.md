# TODO

> now i want you to implement other property tests than axioms. axioms are deeply embedded into the
> source files, but we also need more ad hoc tests testing arbitrary boolean properties rather than
> structured equations. for example, i want you to create proptest/test_conversion.py to test
> roundtrips between diagrams, hypergraph and cmap, or any kind of property on methods like `.to_*`; and proptest/test_repr.py to test that all
> implementations of __repr__ can evaluate back to self in a fresh environment that has loaded `from
> discopy import *` (and possibly other recurring modules like `import numpy as np`). also create a proptest/test_pickle.py which tests serialization roundtrips; and so on...

- [ ] `proptest/test_conversion.py`: roundtrips between `Diagram`, `Hypergraph` and `CMap`
- [ ] `proptest/test_repr.py`: `eval(repr(x)) == x` in a fresh `from discopy import *` environment
- [ ] `proptest/test_pickle.py`: pickle roundtrips for every carrier
- [ ] CHANGELOG entry, `pflake8` and test runs green
