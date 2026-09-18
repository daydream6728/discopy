# TODO

> implement the method-scoped type parameters on the two constructors, the overloaded __get__, and __call__ as fallback

- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-18 11:00 `Factory[**P, T]` with `subclass[**Q, U]` and `classmethod[**Q, U]` returning `Factory[Q, U]`, the overloaded `__get__` returning `Callable[P, T]` and `__call__` taking `P` to `T`.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-18 11:00 Test both branches of `__call__`, check the signatures with pyright, run lint, suite and proptest.
