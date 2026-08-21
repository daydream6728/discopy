# TODO

> Make a discopy module that defines a parametric """category""" class Agentic[C: Category] which adds on top of any category a type of box containing prompts (holes). these boxes would define a `refine` method which calls to an actual LLM to generate a more precise discopy diagram (again in `Agentic[C]`, not necessarily in `C` this way it can still contain diagrams). diagrams in `Agentic[C]` then define a `plan` method which makes parallel llm calls to iteratively refine the current diagram until the diagram can be downgraded from `Agentic[C]` to `C`, i.e. when there are no remaining boxes.

- [x] The parametric construction: `Agentic[C]`, `Prompt`, `lift` and `downgrade`
- [x] Assembling an answer into a diagram: `from_step` and `from_layers`
- [x] Calling the model: `question` and `query`
- [x] Refinement and planning: `Prompt.refine`, `Diagram.refine`, `Diagram.plan`
- [x] Docs, changelog and a green CI
- [x] `lift_structure`, so that a plan can have swaps and copies in it
- [x] `structural`, so the plumbing is always available to an agent
