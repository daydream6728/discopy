# TODO

> In `test/rigid.py` at line 194:
> ```python
>     assert Diagram.Functor is Functor
> ```
> useless
>
> In `test/monoidal.py` at line 755:
> ```python
>     assert not issubclass(Ty, List) and Ty.Wire is Wire
> ```
> useless
>
> In `test/markov.py` at line 63:
> ```python
>     assert Diagram.Permutation is Permutation
> ```
> useless
>
> In `test/utils.py` at lines 181-182:
> ```python
>     class Step(symmetric.Box, Recipe):
>         pass
> ```
> what if we try using @Recipe.generates here instead?
>
> remove the useless tests i commented everywhere you detect similar ones
>
> In `test/utils.py` at line 207:
> ```python
>             if name.endswith("_factory") and isinstance(cls, type)\
> ```
> is this test still up to date?

- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-19 11:30 Remove every `A.Generator is Generator` that restates the binding of
      the module it reads: the three commented, and the same in `compact`,
      `symmetric` (twice) and `test_generator`/`test_generates`.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-19 11:30 Try `@Recipe.generates` in `test_generator_override`.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-19 11:30 `test_generator_exports` asserts nothing since the slot rename: its
      filter reads `_factory`, a name no slot has any more.
