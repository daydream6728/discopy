# TODO

> Port the contextuality module to discopy-next

The module is `optyx/contextuality.py` of [optyx#87](https://github.com/rel-int/optyx/pull/87), whose first commit [#334](https://github.com/rel-int/discopy-next/pull/334) already unified with `quantum.contextuality`; what follows is its later commits, written for these prompts:

> Can we differentiate through the contextual fraction? Eg find the parameters of a given physical setup that maximises the contextual fraction in an scenario

> Find a procedure that takes as input a CMap in optyx.interaction and learns local measurements on the nodes that maximise the contextual fraction

> The most important aspect is how you choose the scenario given a particular CMap, this should be generalisable beyond qubits to any physical system. So defining a notion of message passing scenario that generates contextual distributions. Keep the experiments to small networks, we are quantifying the contextuality of empirical models

- [x] `quantum.contextuality`: `Model.gradient`, the gradient of the contextual fraction with respect to the table as the dual solution of the linear program, and `ascend`, gradient ascent over the parameters of any function to a model with an adaptive step
- [x] `quantum.contextuality.Model.normalise`, conditioning a postselected model on its success when that has the same probability in every context
- [x] `optyx.contextuality.distributions` contracts the diagram once with its bit inputs open, and `Model.from_diagram` groups several output wires into one party's outcome
- [x] `optyx.contextuality`: `local_measurement` for a qubit, `dual_rail_measurement` for a pair of modes and `MessagePassingScenario`, the measurement scenario of a `CMap` for any physical system on its wires, with `learn`
- [WIP] @session_01XhK5oE7DUqFEBMsGrvpC1e-2026-10-27 10:10 tests, `CHANGELOG.md`, `pflake8`, `pylint`, `ruff`, `ty` and `coverage run -m pytest`
