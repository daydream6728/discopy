# TODO

> Read desire/EVENING.md and run a 🌙 Evening turn for tonight.

🌙 Evening's step 5 picks the next repo's oldest bug needing no decision.
[#229](https://github.com/rel-int/discopy-next/issues/229) is the one takeable item: `Matrix.prob_with_perceval`
answers a probability renormalised over the postselected outcomes, where `Matrix.prob`'s other
branch applies the Born rule to the amplitudes. The oracle is that other branch, so the fix chooses
nothing.

- [x] Reproduce on `main`: `Create(1, 1) >> BBS(0) >> Select(2, 0)` reads `1` where `prob()` reads `0.5`
- [x] Make `prob_with_perceval` undo perceval's renormalisation, per input state
- [x] A test that the two branches of `prob` agree on a postselection carrying part of the mass
- [x] `CHANGELOG.md` entry
- [x] `pflake8`, `pylint`, `ruff`, `ty`, the optyx suite and the per-file doctests
