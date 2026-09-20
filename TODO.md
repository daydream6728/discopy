# TODO

> In `discopy/pattern.py` at line 426:
> ```python
> class Unit(Pattern):
> ```
> type it: class Unit[C0, C1: ColouredMonoid](Pattern[C0, C1])
>
> In `discopy/pattern.py` at line 461:
> ```python
> class Tensor(Pattern):
> ```
> type it: class Tensor[C0, C1: ColouredMonoid](Pattern[C0, C1])
>
> In `discopy/pattern.py` at line 555:
> ```python
> class Delay(Pattern):
> ```
> type it: class Delay[C0, C1: DelayedMonoid](Pattern[C0, C1])
>
> In `discopy/pattern.py` at lines 615-622:
> ```python
> class Over:
>     """ The :class:`Exp` ``x << y``, ``Over[X, Y]`` in an annotation. """
>     def __class_getitem__(cls, item) -> Exp:
>         base, exponent = item
>         return Exp("<<", operand(base), operand(exponent))
>
>
> class Under:
> ```
> type them
>
> In `discopy/pattern.py` at line 732:
> ```python
> class Sequent:
> ```
> type it

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-20 13:30 Probe how ty
      reads a subscripted generic pattern class in `Annotated` metadata
      today, then type `Unit`, `Tensor`, `Delay` (and `Repeat`, `L`, `R`
      with them for coherence) as `Pattern[C0, C1]` subclasses, dropping
      the `level()` classmethods the bounds replace
- [ ] Type `Over` and `Under`, and `Sequent`
- [ ] `ty check`, `ruff check`, pytest, proptest fast profile, close
