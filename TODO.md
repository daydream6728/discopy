# TODO

Round 4: review of cubic-dev-ai on f5293a9, 2026-10-15, its summary quoted verbatim.

> **18 issues found** across 96 files

- [ ] P1 pyproject.toml: requires-python >=3.12 while the code relies on 3.14 (r4281421257)
- [ ] P2 para.py:209: restore the `category` annotation of `lift` (r4281421265)
- [ ] P2 test/symmetric.py:420: assert that foliation preserves the diagram (r4281421290)
- [ ] P2 markov.py:135: the box bound omits the balancing box (r4281421302)
- [ ] P2 feedback.py:383: the box bound omits the balancing box (r4281421328)
- [ ] P2 axioms.py:424: `inhabits` mishandles `tuple[T, ...]` (r4281421345)
- [ ] P2 utils.py:313: `is_discopy_class` matches `discopy_ext` (r4281421353)
- [ ] P2 hypergraph.py:965: the tree drops `offsets` (r4281421364)
- [ ] P2 drawing/backend.py:292: a `bytes` path is taken for a file (r4281421373)
- [ ] P3 CHANGELOG.md:12: incomplete sentence (r4281421383)
- [ ] P3 CONTRIBUTING.md:122: pull requests do not upload the database (r4281421416)
- [ ] P3 grammar/categorial.py:316: duplicate `map` methods (r4281421432)
- [ ] P3 grammar/pregroup.py:269: declare `spider_factory` as a `ClassVar` (r4281421436)
- [ ] P3 traced.py:241: `left` repr with `!r` (r4281421448)
- [ ] P3 stream.py:415: default `box_factory` only when `None` (r4281421465)
- [ ] P3 matrix.py:468: `array2string` with a `separator` (r4281421480)
- [ ] P3 grammar/abstract.py:304: `Merge` in the autosummary (r4281421493)
- [ ] P3 CONTRIBUTING.md:82: unclear sentence on `.pylintrc` (r4281421497)
