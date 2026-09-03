# TODO

> put the notebook in an `ontology` directory and make another one that
> instead focuses on financial analysis applications rather than business
> entities.
> think of how we could formulate complex financial queries and have them
> typechecked by hermiT.
> make a case study example computing the asset risk and fx risk over a
> multi-currency portfolio, in such a way that we can ensure that all
> currency/metric has a definite unit that can be checked statically

- [x] move `ontologies.md` into `docs/notebooks/ontology/`, keeping the
      export script, the docs and the fixture paths working
- [x] the `finance` notebook: a currency ontology where units are
      predicates, complex queries typechecked by HermiT, and the three
      static guarantees -- definite unit, no mixing, no leakage; found and
      fixed on the way: `subsumes` missed entailed subsumptions whose
      writeback `owlready2` drops, now an unsatisfiability probe
- [x] the case study: asset risk and FX risk over a multi-currency
      portfolio, every hand-off proved before a number flows
- [WIP] @claude-allegories-2026-09-03 16:30 changelog, validation and
      sign-off
