# TODO

> In `discopy/ribbon.py` at line 213 (before changes): `z = 0` explain to me again why this got removed here and lifted to the parent level? was this only for minimizing diff of was it for correctness?
>
> In `discopy/symmetric.py` at line 269: `braid_factory = classproperty(lambda cls: cls.swap_factory)` should be a Factory too
>
> In `discopy/symmetric.py` at line 270: `layer_factory = Layer` should be a Factory.subclass
>
> In `discopy/utils.py` at lines 719-720: `def __set_name__` what is __set_name__? when is this called? are you using this as a class definition hook? is there a better way?
>
> In `discopy/rigid.py` at line 814: `Diagram.cap_factory = Factory.subclass(Cap)` why not define this directly in Diagram? can we do forward references? id rather avoid reordering every declaration
>
> In `discopy/cat.py` at lines 184-186: `Note ---- Subclasses are assumed to have an arrow factory ``ar`` whose` what was the difference between ar and generator_factory before this branch? im afraid we are conflating two different things, how do you justify it?
>
> also, define all the `ClassVar`s for the factories

- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-18 14:00 `Factory.subclass` takes a forward reference resolved in the owner's module, so every factory is declared in the class body and `locate` goes.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-18 14:00 `Factory.alias` for `symmetric.braid_factory` and `closed.over_factory`/`under_factory`.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-18 14:00 `layer_factory = Factory.subclass("Layer")` with the built layers exported.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-18 14:00 A `ClassVar[Factory[..., Root]]` annotation on every factory declaration.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-18 14:00 Check whether `rigid.Box.z = 0` is load-bearing by removing it, answer the questions on `__set_name__` and on `ar` versus `generator_factory`.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-18 14:00 Docs, lint, suite, proptest.
