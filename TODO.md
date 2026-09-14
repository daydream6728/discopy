# TODO

> this conversation is intended to reflect on the possible ways to implement good search strategies for diagrams.
> i want to be able to specify the following in discopy.abc:
>
> ```
> class TwoCategory(Category):
>     @rule
>     @abstractmethod
>     @unbiased
>     def tensor[
>             X: C0, Y: C0, Z: C0,
>             A: C1[X, Y], B: C1[X, Y],
>             C: C1[Y, Z], D: C1[Y, Z]
>         ](
>             self: C2[A, B], other: C2[C, D]
>         ) -> C2[A @ C, B @ D]:
>         raise NotImplementedError
>
>     @axiom
>     def bifunctoriality[
>             X: C0, Y: C0, Z: C0,
>             A: C1[X, Y], B: C1[X, Y], U: C1[X, Y],
>             C: C1[Y, Z], D: C1[Y, Z], V: C1[Y, Z]
>         ](
>             cls, f: C2[A, B], g: C2[C, D], h: C2[B, U], k: C2[D, V]
>         ) -> Equation[C2[A @ C, U @ V]]:
>         """ Bifunctoriality of the tensor. """
>         return cls.equation_factory(
>             f @ g >> h @ k, (f >> h) @ (g >> k))
>
> class MonoidalCategory[C0: ColouredMonoid, C1: MonoidalCategory](
>         TwoCategory[Colour, C0, C1]):
>     ...
>
> class TracedCategory[C0, C1](MonoidalCategory[C0, C1]):
>     @rule
>     @abstractmethod
>     def trace_left[
>         A: C0, B: C0, M: Atom[C0]
>     ](
>         self: C1[M @ A, M @ B],
>         n: int = 1
>     ) -> C1[A, B]:
>         raise NotImplementedError
>
> class RigidCategory[C0: Pregroup, C1: RigidCategory](BiclosedCategory[C0, C1]):
>     """
>     A rigid category is a :class:`BiclosedCategory` with a :class:`Pregroup` as
>     object type and methods for :code:`cups` and :code:`caps`.
>     """
>     @classmethod
>     @generator
>     @abstractmethod
>     def cups[X: Atom[C0]](cls, left: X, right: X.r) -> C1[X @ X.r, 1]:
>         """
>         The cups witnessing :code:`right` as the adjoint of :code:`left`:
>         as a rule, ``x @ x.r ⊢`` is a cup, ``x.l @ x`` included.
>
>         Parameters:
>             left : The left-hand side of the cups.
>             right : Its adjoint, i.e. the right-hand side of the cups.
>         """
>
> ```
>
> where axioms are property test using hypothesis, generators are logical constants and rules are inference rules
> re-implement the property testing infrastructure and search strategies for monoidal diagrams completely to be able to express these.
> implement a discopy.search module that implements:
>
> * an intrinsically typed data inductive structure to represent sequent patterns and matching over it, along with a way to parse one from a function signature
> * the new @rule and @generator decorators and an updated version of @axiom that reads the pattern
> * in monoidal.diagram, implement an extensible search strategy that diagram subclasses with more structure can tune modularly, making use of generators and rules
> * do not implement the TwoCategory/MonoidalCategory split, it was purely informative and simply motivates the higher dimensional matching that we ultimately want, for now you should focus on 1D diagrams.

- [WIP] @7663789e-2026-09-14 15:24 `discopy.search`: typed sequent patterns, matching, parsing from a signature
- [WIP] @7663789e-2026-09-14 15:24 `@rule`, `@generator` and the pattern-reading `@axiom`
- [ ] Rewrite the `abc` axioms as sequents, declare the rules and generators
- [ ] `monoidal.Diagram.strategy` as a rule-based search, subclass overrides removed
- [ ] Tests, records, docs and changelog; `pflake8` and `pytest` green
