# TODO

> in daydream6728/discopy:feature/owl+agentic: merge the two branches

Both prompts, verbatim, are the ones the merged branches were written for.

## `feature/owl`

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
- [x] the 2-category: predicates as objects, queries as morphisms,
      `Rule` as the 2-cells, and coercion where they do not meet
- [ ] move the world-passing `Function` half to the wiki's toolbox.py
- [x] tests and doctests, `pflake8 discopy` and `coverage run -m pytest`

## `feature/agentic`

> Make a discopy module that defines a parametric """category""" class Agentic[C: Category] which adds on top of any category a type of box containing prompts (holes). these boxes would define a `refine` method which calls to an actual LLM to generate a more precise discopy diagram (again in `Agentic[C]`, not necessarily in `C` this way it can still contain diagrams). diagrams in `Agentic[C]` then define a `plan` method which makes parallel llm calls to iteratively refine the current diagram until the diagram can be downgraded from `Agentic[C]` to `C`, i.e. when there are no remaining boxes.

- [x] The parametric construction: `Agentic[C]`, `Prompt`, `lift` and `downgrade`
- [x] Assembling an answer into a diagram: `from_step` and `from_layers`
- [x] Calling the model: `question` and `query`
- [x] Refinement and planning: `Prompt.refine`, `Diagram.refine`, `Diagram.plan`
- [x] Docs, changelog and a green CI
- [x] `lift_structure`, so that a plan can have swaps and copies in it
- [x] `structural`, so the plumbing is always available to an agent

## The merge

- [x] `semantic` and `llm` extras side by side, one `uv.lock` over both
- [x] `pflake8 discopy` and `coverage run -m pytest` green on the merge
