# TODO

> with your current implementation, can we display diagrams whose objects are predicates/compound entities? what i wanted is to not read through all the predicates as boxes but use types instead
>
> [answers to design questions] auto-coerce in composition, feature/owl style; math notation for compound wire labels.

- [x] constructs as objects: `instances`, `carrier` and everything on them accept
      compound class expressions
- [x] `label`, the math-notation printer, and `ob` reading it
- [x] `coercion` and auto-coercion in `Relation.then`, with `parallel` widening
- [x] `from_property` filters its pairs to the carriers of its boundary
- [x] `extension` defaults to the compound type, the anatomy one keyword away
- [WIP] @claude-allegories-2026-09-01 15:45 tests keeping 100% coverage, notebook
      retouch, changelog and sign-off
