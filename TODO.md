# TODO

> make it so that Hom can take either TypeVars or patterns, so we can
> write Hom(A, B) directly

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-29 `Hom` lifts a bare
      type parameter itself, respell every `Hom(Ob(A), Ob(B))` to
      `Hom(A, B)`, validate: sequents byte-identical, ruff, ty, pytest,
      fast matrix, CHANGELOG, close
