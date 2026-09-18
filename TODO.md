# TODO

> rename Generator to Factory, and introduce a `def subclass(cls, f)` and a `def classmethod(cls, f)` classmethods to be able to define e.g.
>
> * abstraction_factory = Factory.subclass(Abstraction)
> * @Factory.classmethod def application_factory(cls, func, args, left=False): return BA(args, func) if left else FA(func, args)

- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-18 09:00 `utils.Factory` replaces `Generator` and `generator`: `Factory.subclass(X)` builds a subclass of `X` for every level below, `Factory.classmethod(f)` is a factory that is behaviour; a factory assigned after its class is created finds its owner on first access.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-18 09:00 Migrate every `@generator` declaration to `Factory.subclass`, in the class body when the generator precedes it and after the generator's class otherwise; the callable factories of the free levels to `Factory.classmethod`.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-18 09:00 Docs, CHANGELOG, README, tests, lint, suite, proptest.
