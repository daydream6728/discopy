> cubic's review 5619881008 of fa034519 on #282, five findings:
> 1. P1 discopy/cat.py:631: `lambdify` now sends matrices through `rsubs`/`rmap`, which rebuilds their flat entries as a column and changes an `m×n` payload's shape. Preserve the original matrix shape when mapping.
> 2. P2 discopy/monoidal.py:1896: This rebuild drops the bubble's `data` and `is_dagger`, so a functor image no longer carries them. Forward `data=other.data` and `is_dagger=other.is_dagger` in the `bubble` call, as `cat.Bubble.lambdify` and `dagger` already do.
> 3. P2 discopy/feedback.py:708: This override reaches `cat.Bubble.lambdify` for `Feedback` bubbles, which rebuilds them with `name=`, `method=`, `data=` and `is_dagger=` kwargs that `Feedback.__init__` does not accept. Substituting a symbol inside a feedback bubble (e.g. `Box('f', x @ y.delay(), z @ y, data=phi).feedback().subs(phi, 1)`) will likely raise TypeError.
> 4. P2 discopy/utils.py:612: Passing one pair as `rsubs(data, (var, expr))` now makes `dict(pairs)` raise `TypeError`; normalize it as one pair before building the dict.
> 5. P3 CHANGELOG.md:1572: `B88` is cited for three unrelated bugs in this changelog. Check the issue tracker and correct the IDs so each bullet points to its own bug.

- [x] merge `origin/main` (5e95a3f4)
- [x] 1: check ndarray, sympy `Matrix` and `Array` data keep their shape through `subs` and `lambdify`, with a test
- [ ] 2: forward a bubble's `data` and `is_dagger` through functors into free categories
- [ ] 3: `Feedback.subs`/`lambdify` rebuild through its own constructor
- [x] 4: `rsubs(data, (var, expr))` takes one pair, as it did on main
- [ ] 5: name which item of B88 each changelog bullet fixes
