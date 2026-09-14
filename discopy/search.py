"""
The search for diagrams by the rules and generators of their category.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Rule
    Generator

.. admonition:: Functions

    .. autosummary::
        :template: function.rst
        :nosignatures:
        :toctree:

        rule
        generator
        search

A :class:`Rule` is a :class:`discopy.pattern.Declaration` with a
conclusion, an inference rule; a :class:`Generator` a rule with no hom
among its premises, a logical constant. :func:`search` builds a term of a
goal type by choosing, at each step, a free box, a generator whose
conclusion matches the goal, or a rule whose conclusion matches and whose
premises are searched recursively with one less unit of depth. A category
tunes the search by declaring its rules and generators: a level of
:mod:`discopy.abc` adds the structure it axiomatises, a concrete diagram
class may add more.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from types import MethodType
from typing import TYPE_CHECKING

from discopy.pattern import Declaration, Hom, Match, declarations
from discopy.utils import AxiomError

if TYPE_CHECKING:
    from hypothesis import strategies as st

    from discopy import abc


@dataclass(repr=False)
class Rule[**P, T](Declaration[P, T]):
    """
    An inference rule of a category: a :class:`discopy.pattern.Declaration`
    with a conclusion, stated once on an abstract base class and inherited
    by every category below it.

    The declaration and the implementation are decoupled by name: the
    sequent is read from the declaration in :mod:`discopy.abc` while
    :func:`search` calls the attribute of the same name on the category,
    which a concrete class may override with its own method. Accessed on a
    class, a rule binds to it; accessed on an instance, it behaves as the
    method it decorates.

    >>> from discopy.abc import Category
    >>> print(Category.then)
    then: A: C0, B: C0, C: C0 | self: C1[A, B], other: C1[B, C] ⊢ C1[A, C]
    """

    __hash__ = Declaration.__hash__

    def __get__(self, instance, owner: type[T]):
        bound = self.bind(owner)
        return bound if instance is None else MethodType(bound, instance)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        return self.function(*args, **kwargs)

    def match(self, dom=None, cod=None) -> Iterator[Match]:
        """ Unify the conclusion with a goal. """
        return self.sequent.conclusion.match(dom, cod)

    def canonical(self) -> T:
        """
        The rule applied to its canonical arguments, so that it reads as a
        schema: the term its implementation builds on a box per premise.

        >>> from discopy.abc import MonoidalCategory
        >>> from discopy.monoidal import Diagram
        >>> print(MonoidalCategory.tensor.bind(Diagram).canonical())
        self @ C >> B @ other
        """
        return getattr(self.category, self.name)(*super().canonical())


class Generator(Rule):
    """
    A logical constant: a rule with no hom among its premises, so that the
    search builds it in one step, e.g. the cups of a rigid category.

    >>> from discopy.abc import RigidCategory
    >>> print(RigidCategory.generators["cups"])
    cups: X: Atom[C0] | left: X, right: X.r ⊢ C1[X @ X.r, 1]
    """
    def __post_init__(self):
        super().__post_init__()
        for name, premise in self.sequent.premises.items():
            if isinstance(premise, Hom):
                raise TypeError(
                    f"A generator takes no hom premise, got {name}.")


def rule[**P, T](function: Callable[P, T]) -> Rule[P, T]:
    """ Decorate a method as an inference rule, its signature the sequent. """
    return Rule(function)


def generator[**P, T](function: Callable[P, T]) -> Generator[P, T]:
    """ Decorate a method as a logical constant, its signature the sequent. """
    return Generator(function)


def search(category: type[abc.Category], free: Callable, *, dom=None, cod=None,
           types=None, max_depth: int = 3) -> st.SearchStrategy:
    """
    Generate a term of a category by its rules: a goal ``dom -> cod``,
    either side free when :obj:`None`, is built as a free box, a
    :class:`Generator` whose conclusion matches, or below the depth bound a
    :class:`Rule` whose conclusion matches and whose premises are searched
    recursively. A term the rule builds outside its declared conclusion is
    an :class:`discopy.utils.AxiomError`: the declaration lies.

    Parameters:
        category : The class with the rules and generators, e.g.
            :class:`discopy.monoidal.Diagram`.
        free : A strategy factory ``free(dom=, cod=, types=)`` for a free
            generator of the category, e.g. the strategy of its boxes.
        dom : The domain of the goal, if any.
        cod : The codomain of the goal, if any.
        types : A strategy for the objects, overriding that of ``C0``.
        max_depth : The number of nested rules a term may apply.

    >>> from hypothesis import find
    >>> from discopy.monoidal import Ty, Diagram, Box
    >>> x, y = Ty('x'), Ty('y')
    >>> term = find(search(Diagram, Box.strategy, dom=x, cod=y),
    ...             lambda term: len(term.boxes) > 1)
    >>> assert (term.dom, term.cod) == (x, y) and len(term.boxes) > 1
    """
    from hypothesis import strategies as st

    generators = tuple(declarations(category, Generator).values())
    rules = tuple(declarations(category, Rule).values())

    def matching(candidates, dom, cod) -> list:
        matches = [(rule, list(rule.match(dom, cod))) for rule in candidates]
        return [(rule, found) for rule, found in matches if found]

    @st.composite
    def terms(draw, dom, cod, depth):
        leaves = [None] + matching(generators, dom, cod)
        branches = matching(rules, dom, cod) if depth else []
        candidates = branches if branches and draw(st.booleans()) else leaves
        choice = draw(st.sampled_from(candidates))
        if choice is None:
            return draw(free(dom=dom, cod=cod, types=types))
        rule, found = choice
        subst, residuals = draw(st.sampled_from(found))
        _, args = rule.generate(
            draw, lambda _, dom, cod: terms(dom, cod, depth - 1),
            subst=subst, residuals=residuals, types=types)
        result = getattr(category, rule.name)(*args)
        if dom is not None and result.dom != dom\
                or cod is not None and result.cod != cod:
            raise AxiomError(
                f"{rule} concludes {rule.sequent.conclusion} but built "
                f"{result.dom} -> {result.cod}.")
        return result

    return terms(dom, cod, max_depth)
