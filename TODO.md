# TODO

> i want you to implement the following mathematical description in discopy, on a new branch (name it feature/allegories). you can deviate from the plan if justified. take inspiration from the existing work in the feature/owl branch. avoid implementing low level algorithms like querying and logical solvers yourself, instead make use of existing libraries and programs such as owlready2 or the hermiT solver.
>
> one should be able to load an ontology from a base url and represent ontological facts diagrammatically.
> while you implement this feature, co-develop in parallel a marimo notebook in notebooks/ that showcases all features in a non trivial demo on the official FIBO financial ontology by EDMCouncil.
> work until i can showcase these features in a real world context, such that we can show it to an investor who wants to improve AI agent safety and correctness, and have convincing arguments that ontologies are the right tool for the job.
>
> [on review] do we need to implement rel as a boolean tensor category? can we use owlready2 directly?
> we don't need free diagrams, owl is a semantic category describing owl relations from a loaded ontology.
> how is the categorical structure described? can you add Bicategory, Poset, etc... (do we need quantales?)

- [x] `discopy.abc`: `Poset`, `Lattice`, `BooleanAlgebra`, `DaggerCategory`,
      `Allegory`, `BooleanAllegory`
- [x] `discopy.owl.Relation`, the semantic category of an ontology's relations, with the
      `semantic` extra, `UNIMPORTABLE` and docs registration
- [x] `reason`, `consistent` and `load`, delegating to HermiT and `owlready2`
- [x] `extension`, the closed-world semantics of class constructs, and `Relation.sparql`
- [x] `Axiom` and `axioms`, compiling what an ontology says into checkable inclusions
- [x] drawing: `to_diagram` and friends, pictures derived from the ontology's own syntax
- [x] FIBO fixtures in `test/fixtures/fibo/` with a demo ABox
- [WIP] @claude-allegories-2026-09-01 13:00 the notebook `docs/notebooks/ontologies.md`,
      CI Java and `uv.lock`
- [ ] changelog, lint, coverage and sign-off
