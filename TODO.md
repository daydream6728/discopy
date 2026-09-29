# TODO

> let's do it, goals as patterns with a shared substitution
> it should have been this way since the beginning! that was the
> whole point of patterns

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-29 Goals as
      patterns in `search`: each side a pattern, a type or `None` (a
      fresh variable), one shared substitution threaded through the
      attempts — a side instantiates for guidance once its variables
      are bound, unifies with the boundary of the built term to
      extend the substitution, and a failed unification rejects the
      attempt where a fully bound side still raises `AxiomError`
- [ ] Tests: an endomorphism goal `A ⊢ A`, a copy-shaped goal
      `A ⊢ A @ A`, sharing across the two sides, and a doctest on
      `search`
- [ ] Validate: ruff, ty, pytest, fast + dev matrix, CHANGELOG,
      close
