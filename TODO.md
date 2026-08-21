# TODO

> make a new discopy semantic module python/owl.py that describes the subcategory of python functions whose types are enriched to be annotated with an OWL schema described by owlready2 and validated against the schema using hermiT invocations, everything being local, data added in a world state being passed around. its generators are python functions taking the world as an argument and supplemented with a owlready2 signature, we also have sparql queries which are just wrappers over python functions in the special case where the body of the function performs a sparql query. there is an evaluation functor thats sends OWL to the regular python category.

- [x] `discopy.python.owl.Function`, a Markov category of world-passing functions typed by OWL classes
- [x] HermiT validation on every call, with a `no_reasoning` switch
- [x] `discopy.python.owl.Query`, the special case of a SPARQL body
- [x] `discopy.python.owl.Eval`, the evaluation functor to `discopy.python`, and `lift` the other way
- [x] `owlready2` as a `semantic` extra, `--skip-extra` support, docs and changelog
- [x] `Function.validate`, the hook where a call meets the reasoner
- [x] `rules`, compiling OWL axioms into `frobenius.Equation`
- [x] `implication` and `swrl`, the round trip with the ontology's own
      SWRL rules
- [x] a domain of definition on each end of a relation, and
      `Diagram.validate` checking composites against it with HermiT
- [x] `Function.check`, holding inserted individuals to their codomain
- [x] tests and doctests, `pflake8 discopy` and `coverage run -m pytest`
