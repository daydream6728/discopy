# TODO

> In `discopy/biclosed.py` at line 115: `exp_factory: ClassVar[Factory[..., "Exp"]] = Factory.subclass("Exp")` I would rather have subclass only take types, not str. Let's return to the previous design where factories were bound after defining the associated class, as long as you keep the classvar annotations and late-bind them, and confirm that this has no effect over inheritance, as in subclasses will normally inherit all late-bind factories
>
> In `discopy/balanced.py` at line 136: `twist_factory: ClassVar[Factory[..., "Twist"]] = Factory.subclass("Twist")` what are we missing to accurately type the ellipsis here? semi related: does factory need an extra parameter to say to which class it is bound to?

- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-18 17:00 `Factory.subclass` takes a class again, the declaration in the body is the `ClassVar` annotation alone and the binding goes back below the generator, with `Factory.locate` to find the owner.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-18 17:00 A test that a subclass inherits every late-bound factory, whichever class reads it first.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-18 17:00 Docs, lint, suite, proptest; answer what it would take to type the parameters and whether a factory needs its owner.
