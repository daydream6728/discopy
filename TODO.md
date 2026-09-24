# TODO

> In `discopy/symmetric.py` at lines 732-747:
> ```python
> @axiom
> def symmetric(
>         cls, functor: Annotated[Any, SELF],
>         x: Annotated[Ty, Atom[SELF.dom.ob]],
>         y: Annotated[Ty, Atom[SELF.dom.ob]]) -> Equation:
>     """ A symmetric functor preserves the swap. """
>     return functor.cod.Equation(
>         functor(functor.dom.swap(x, y)),
>         functor.cod.swap(functor(x), functor(y)))
>
>
> Diagram.Functor.symmetric = symmetric
> del symmetric
> ```
> don't do this, the axioms must be defined in their appropriate class.
> don't make functors automatically inherit, in practice there would
> always be one more axiom ensuring that the extra structure at each
> level's dom is mapped to the same generator at the same level's cod.
>
> don't introduce SELF, instead introduce for functors four extra
> variables on top of C0 and C1 (which for functor is basically C0:
> Category (or Diagram) and C1: Functor): In0, In1, Out0, Out1, and
> define def Functor.__call__ with two overloads In0 -> Out0 and
> In1 -> Out1

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-24 Introduce the
      sorts `In0`, `In1`, `Out0`, `Out1` read off the functor's `dom`
      and `cod`, remove `SELF` and the sort attribute chaining
- [ ] Declare `Functor.__call__` with the two overloads
      `In0 -> Out0` and `In1 -> Out1`
- [ ] Move the `braided` and `symmetric` functor axioms into their
      class bodies
- [ ] Respell the `Equivalence` laws on `In0` and `In1`
- [ ] `ruff check`, `ty check`, pytest, fast + dev functor cells,
      CHANGELOG, close
