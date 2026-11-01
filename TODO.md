# TODO

🌙 Evening's prompt for the night of 2026-11-01, verbatim:

> Read desire/EVENING.md and run a 🌙 Evening turn for tonight.

[next#426](https://github.com/rel-int/discopy-next/issues/426):
`optyx/core/zx.py`'s `Spider.grad` returns `π·θ′` times the spider shifted by
half a turn. A spider's array is `P₀ + exp(2πiθ)P₁`, whose derivative has no
`P₀` component, while the shifted spider has one, so the gradient is wrong at
**every** arity — a spurious `π` on the all-zero entry and `−π·θ′` where
`2πi·θ′·exp(2πiθ)` belongs. `discopy/quantum/zx.py`'s `Spider.grad` is the
same formula written correctly, as `1j·π·θ′` times the *difference* between
the spider and the half-turn shift, and it reproduces the numerical
derivative exactly. Cut on top of #425, both being in `core/zx.py`.

- [WIP] @session_01C7YfAR-2026-11-01 02:35 Port the sibling module's two-term
      form, docstring included, so that the two copies of this class say and
      do the same thing.
- [WIP] @session_01C7YfAR-2026-11-01 02:35 `test_zx.py::test_grad` pins the
      old formula structurally, in its own assertion and in its chain-rule
      case: both move to the corrected form.
- [WIP] @session_01C7YfAR-2026-11-01 02:35 Add the difference-quotient oracle
      `test/optyx/grad.py` already uses for the photonic gates, over `Z` and
      `X` at several arities and phases, the legless spider included, since a
      structural assertion cannot tell a right formula from a wrong one.
- [WIP] @session_01C7YfAR-2026-11-01 02:35 Run `test/optyx`, the wide suite,
      `pflake8`, `pylint`, `ruff`, the changed module's doctests, and
      `CHANGELOG.md`.
