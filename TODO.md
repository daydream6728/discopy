# TODO

> remove the closed world model and only use deductive reasoning with hermiT
>
> [on review] extend the plan with a proper way to construct the karoubi envelope.
> clearly separate the underlying single-sorted category of relations from the class
> that can represent diagrams whose types can be any predicate, and give conversions
> between them. in the latter, allow sequential composition to run HermiT entailment
> queries and insert the resulting proof object as a coercion in-between.

- [x] `abc.DistributiveAllegory`, with `BooleanAllegory` re-based on it
- [x] Layer 0: `Relation` single-sorted (`ob = int`, explicit world), `neg` and `top`
      removed, `deduced`, `subsumes` and the deductive `satisfying`/`extension`
- [x] Layer 1: `Query`, the Karoubi envelope — normalization, `Coercion` proof objects
      in `then`, `no_reasoning`, `validate`, conversions and constructors
- [x] axioms over Layer 0, tests reworked at 100% coverage
- [x] the notebook on one deductive semantics, with the proof-carrying coercions
- [WIP] @claude-allegories-2026-09-02 14:15 changelog, lint, `--skip-extra`,
      notebook check and sign-off
