"""
The search for diagrams by the rules and generators of their category: a
:class:`Rule` is a :class:`discopy.pattern.Declaration` with a conclusion,
a :class:`Generator` a rule with no hom among its premises, and
:func:`search` builds a term of a goal type by choosing at each step a
free box, a generator whose conclusion matches the goal, or a rule whose
conclusion matches and whose premises are searched recursively.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Rule
    Generator
    Constant

.. admonition:: Functions

    .. autosummary::
        :template: function.rst
        :nosignatures:
        :toctree:

        rule
        generator
        inapplicable
        search
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from types import MethodType
from typing import TYPE_CHECKING

from discopy.pattern import (
    Declaration, HomType, Match, Sequent, Sort, Substitution, parse)
from discopy.utils import AxiomError

if TYPE_CHECKING:
    from hypothesis import strategies as st

    from discopy import abc


class DeadEnd(Exception):
    """
    A goal no rule or generator of the category closes within the depth:
    :func:`search` retries the goal a bounded number of times before
    rejecting the whole example.
    """


@dataclass(repr=False)
class Rule[**P, T](Declaration[P, T]):
    """
    An inference rule of a category, a :class:`discopy.pattern.Declaration`
    with a conclusion. The sequent is read from the declaration in
    :mod:`discopy.abc` while :func:`search` calls the attribute of the same
    name on the category, which a concrete class overrides with its own
    method. Accessed on a class, a rule binds to it; on an instance, it
    behaves as the method it decorates.

    >>> from discopy.abc import Category
    >>> print(Category.then)
    then: A: C0, B: C0, C: C0 | self: C1[A, B], other: C1[B, C] ⊢ C1[A, C]
    """

    __hash__ = Declaration.__hash__

    def __get__(self, instance, owner: type):
        declaring = next((
            base for base in owner.__mro__
            if self.is_declared(base.__dict__.get(self.name or ""))),
            None)
        bound = self.bind(owner, owner=declaring)
        return bound if instance is None else MethodType(bound, instance)

    def is_declared(self, value) -> bool:
        """ Whether a class attribute is this very declaration. """
        value = getattr(value, "__func__", value)
        return value is self

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        return self.function(*args, **kwargs)

    def match(self, dom=None, cod=None) -> Iterator[Match]:
        """ Unify the conclusion with a goal. """
        return self.sequent.conclusion.match((dom, cod))

    def apply(self, arguments: dict) -> T:
        """ The implementation of the rule on the category, applied. """
        return getattr(self.category, self.name or "")(
            *arguments.values())

    def check(self, /, *args: P.args, **kwargs: P.kwargs) -> Substitution:
        """
        Match the arguments of the rule's method against the patterns its
        declaration states, the one mechanism behind the manual shape
        assertions: binding the metavariables on success and raising
        :class:`discopy.utils.AxiomError` on a mismatch.

        >>> from discopy.rigid import Diagram, Ty
        >>> x = Ty('x')
        >>> assert Diagram.generators["cups"].check(x, x.r) == {"X": x}
        >>> Diagram.generators["cups"].check(x, x.l)  # doctest: +ELLIPSIS
        Traceback (most recent call last):
         ...
        discopy.utils.AxiomError: cups does not accept ...
        """
        sequent = self.sequent
        parameters = [
            inspect.Parameter(name, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            for name in sequent.premises]
        values = inspect.Signature(parameters).bind(*args, **kwargs).arguments

        def matches(premises, subst, residuals):
            if not premises:
                for pattern, value in residuals:
                    if pattern.instantiate(subst, self.unit) != value:
                        return
                yield subst
                return
            (name, premise), *rest = premises
            value = values[name]
            if isinstance(premise, HomType):
                found = premise.match((value.dom, value.cod), subst,
                                      residuals)
            elif isinstance(premise, Sort):
                found = iter([(subst, residuals)])
            else:
                found = premise.match(value, subst, residuals)
            for subst_, residuals_ in found:
                yield from matches(rest, subst_, residuals_)

        premises = list(sequent.premises.items())
        for subst in matches(premises, {}, ()):
            return subst
        mismatch = ", ".join(
            f"{name}={values[name]!r}" for name in sequent.premises)
        raise AxiomError(f"{self.name} does not accept {mismatch}.")


class Generator(Rule):
    """
    A logical constant: a rule with no hom among its premises, so that the
    search builds it in one step, e.g. the cups of a rigid category.

    >>> from discopy.abc import RigidCategory
    >>> print(RigidCategory.generators["cups"])
    cups: X: Atom[C0] | left: X, right: X.r ⊢ C1[X @ X.r, Unit[C0]]
    """

    __hash__ = Declaration.__hash__

    def __post_init__(self):
        super().__post_init__()
        try:
            sequent = parse(self.function)
        except TypeError:
            return  # Validated lazily, once the owner bounds the sorts.
        self.validate(sequent)

    @staticmethod
    def validate(sequent: Sequent) -> None:
        """ Refuse a premise the search would have to prove. """
        for name, premise in sequent.premises.items():
            if isinstance(premise, HomType):
                raise TypeError(
                    f"A generator takes no hom premise, got {name}.")

    @property
    def sequent(self) -> Sequent:
        sequent = Declaration.sequent.fget(self)
        self.validate(sequent)
        return sequent


@dataclass(repr=False)
class Constant(Generator):
    """
    The rule of one given box: it applies exactly to the sequent of the
    box and builds it, so that a category generated by a fixed vocabulary
    — the words of a grammar, the gates of a circuit — assigns a
    dictionary of these to its ``generators``.

    >>> from discopy.grammar import pregroup
    >>> n = pregroup.Ty('n')
    >>> rule = Rule.constant(pregroup.Word('Alice', n))
    >>> assert rule.apply({}) == pregroup.Word('Alice', n)
    """

    __hash__ = Declaration.__hash__

    def __post_init__(self):
        self.name = self.name or str(self.function)
        self.__doc__ = f"The constant {self.name}."

    @property
    def sequent(self) -> Sequent:
        return Sequent()

    def match(self, dom=None, cod=None) -> Iterator[Match]:
        box = self.function
        if dom in (None, box.dom) and cod in (None, box.cod):
            yield {}, ()

    def generate(self, draw, hom, subst=None, residuals=(), types=None):
        return dict(subst or {}), {}

    def apply(self, arguments: dict):
        return self.function


def rule[**P, T](function: Callable[P, T]) -> Rule[P, T]:
    """ Decorate a method as an inference rule, its signature the sequent. """
    return Rule(function)


def generator[**P, T](function: Callable[P, T]) -> Generator:
    """ Decorate a method as a logical constant, its signature the sequent. """
    return Generator(function)


def constant(box) -> Constant:
    """ The rule of one given box, see :class:`Constant`. """
    return Constant(box)


Rule.constant = staticmethod(constant)


def inapplicable(reason: str) -> Callable:
    """
    Decorate a method to drop the rule it would otherwise inherit: the
    method still runs, but :func:`discopy.pattern.declarations` leaves it
    out of the rules and generators of the class, with the reason as its
    record.
    """
    def decorate(method: Callable) -> Callable:
        inner = method.__func__ if isinstance(method, classmethod)\
            else method
        inner.__inapplicable__ = reason
        return method
    return decorate


def search(category: type[abc.Category], free: Callable | None = None, *,
           dom=None, cod=None, types=None,
           max_depth: int = 3) -> st.SearchStrategy:
    """
    Generate a term of a category by its rules: a goal ``dom -> cod``,
    either side free when :obj:`None`, is built as a free box, a
    :class:`Generator` whose conclusion matches, or below the depth bound a
    :class:`Rule` whose conclusion matches and whose premises are searched
    recursively. A term built outside the declared conclusion is an
    :class:`discopy.utils.AxiomError`: the declaration lies.

    Parameters:
        category : The class with the rules and generators.
        free : A strategy factory ``free(dom=, cod=, types=)`` for the free
            generator of the category, e.g. the strategy of its boxes, or
            :obj:`None` for a category generated by a fixed vocabulary,
            whose search fills only the sequents its generators derive.
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
    from hypothesis import assume, strategies as st

    generators = tuple(category.generators.values())
    rules = tuple(category.rules.values())

    def matching(candidates, dom, cod) -> list:
        matches = [(rule, list(rule.match(dom, cod))) for rule in candidates]
        return [(rule, found) for rule, found in matches if found]

    @st.composite
    def attempt(draw, dom, cod, depth):
        leaves = ([] if free is None else [None])\
            + matching(generators, dom, cod)
        branches = matching(rules, dom, cod) if depth else []
        candidates = branches if branches\
            and (not leaves or draw(st.booleans())) else leaves
        if not candidates:
            raise DeadEnd(f"{dom} -> {cod}")
        choice = draw(st.sampled_from(candidates))
        if choice is None:
            assert free is not None
            return draw(free(dom=dom, cod=cod, types=types))
        rule, found = choice
        subst, residuals = draw(st.sampled_from(found))
        _, args = rule.generate(
            draw, lambda _, dom, cod: terms(dom, cod, depth - 1),
            subst=subst, residuals=residuals, types=types)
        result = rule.apply(args)
        if dom is not None and result.dom != dom\
                or cod is not None and result.cod != cod:
            raise AxiomError(
                f"{rule} concludes {rule.sequent.conclusion} but built "
                f"{result.dom} -> {result.cod}.")
        return result

    @st.composite
    def terms(draw, dom, cod, depth, tries: int = 8):
        for _ in range(tries):
            try:
                return draw(attempt(dom, cod, depth))
            except DeadEnd:
                continue
        raise DeadEnd(f"{dom} -> {cod}")

    @st.composite
    def goals(draw, dom, cod, depth):
        try:
            return draw(terms(dom, cod, depth))
        except DeadEnd:
            assume(False)

    return goals(dom, cod, max_depth)
