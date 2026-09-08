# TODO

> alright lets forget about uploading the notebooks, they wont work on
> marimohub because of the hermit dependency anyway.
> switch to OWLAPY
>
> save this branch as feature/allegory-owlready2
> make a new branch feature/allegory-owlapy replacing owlready2 with owlapy
> as our main owl driver

- [x] investigate owlapy hands-on: reasoners available without a Java
      runtime, FIBO fixture parsing, instance retrieval, subsumption and
      consistency -- verdict: complete reasoning is `SyncReasoner` (bundled
      owlapi jars, still needs a JVM) with a real `is_entailed` /
      `is_satisfiable` / `has_consistent_ontology` API; the pure-Python
      `RDFLibReasoner` retrieves the existential fragment correctly but is
      closed-world on complements and universals and decides no entailment
- [x] port `discopy.owl` to owlapy: `World` wraps `SyncOntology` with a
      lazy `SyncReasoner`, the oracle calls become direct reasoner calls
      -- no scratch classes, no writeback -- and the dictionary reads
      owlapy class expressions; retrievals and the tbox are memoised on
      the world, dropped on `add`
- [x] port the offline FIBO loading onto owlapi IRI mappers: `load`
      returns a fresh `World`, `preload` is gone
- [WIP] @claude-allegories-2026-09-08 12:00 port the tests and both
      notebooks, update the `semantic` extra
- [ ] changelog, validation and sign-off
