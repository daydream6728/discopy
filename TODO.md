# TODO

> ok lets forget about quantum for now, as long as it duck-types.
> implement the other suggested changes

- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-17 10:00 `Generator.build` ties a built class to its level by the root: the level is a base only when the root is a subclass of the owner, and every class attribute of the root equal to the owner is lifted to the level (`Exp.ob`, `Functor.dom` and `cod`).
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-17 10:00 Declare the wire generator with `@generator` on every `Ty` that has one, `biclosed.Ty` included so that `biclosed.Wire` is used.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-17 10:00 Declare `exp_factory`, `over_factory` and `under_factory` on `biclosed.Ty`; `categorial.Over` and `Under` are built; `closed.Ty` aliases the three to its `Exp`.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-17 10:00 Declare `functor_factory` on every `Diagram` that defines a `Functor`; `pivotal.Functor` and `pregroup.Functor` are built.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-17 10:00 Declare the term generators on `biclosed.Diagram`, with `Ty.x_factory = Diagram.x_factory` at each level.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-17 10:00 Extend the exports test to type and functor generators; CHANGELOG, README, lint, tests, proptest.
