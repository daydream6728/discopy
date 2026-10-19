# TODO

cubic's review of this pull request, 2026-10-19, quoted:

> **3 issues found** across 5 files
> - discopy/cat.py:940 — P2: The decorator drops the named `other` argument, so `F.then(other=G)` and `alpha.then(other=beta)` silently return the left operand without composing. [...]
> - CHANGELOG.md:714 — P3: `Every then` overstates the scope: this PR updates six implementations, while other morphism APIs such as `Matrix.then` and `Stream.then` remain binary. [...]
> - CHANGELOG.md:2062 — P3: The old `Permutation.then` did not iterate `self` through the `Sequence` protocol; it used `for i in range(len(self))` and `self[i]`. [...]

- [ ] `utils.unbiased` passes keyword operands to the binary method rather than dropping them, with a test
- [ ] `CHANGELOG.md`: six `then`s, not every one, and the binary ones named
- [ ] `CHANGELOG.md`: the old `Permutation.then` re-cast `other`, not `self`
