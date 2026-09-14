"""
Sequent patterns, their matching and the search for diagrams by rules.

A rule of a category is stated once on an abstract base class of
:mod:`discopy.abc`, as a method whose signature is a sequent: its type
parameters are the variables and their sorts, its parameters the premises
and its return annotation the conclusion. The tensor of a monoidal
category is the rule ``f: C1[A, B], g: C1[C, D] ⊢ C1[A @ C, B @ D]``, the
cups of a rigid category the generator ``x: X, y: X.r ⊢ C1[X @ X.r, 1]``
for an atomic ``X``, and an axiom is a sequent with no conclusion: its
premises are the arguments generated for a property test.

.. code-block:: python

    class MonoidalCategory[C0, C1](Category[C0, C1]):
        @rule
        @abstractmethod
        def tensor[A: C0, B: C0, C: C0, D: C0](
                self: C1[A, B], other: C1[C, D]) -> C1[A @ C, B @ D]:
            ...

        @axiom
        def bifunctoriality[
                A: C0, B: C0, C: C0, D: C0, E: C0, F: C0](
                cls, f: C1[A, B], g: C1[C, D], h: C1[B, E], k: C1[D, F]):
            return cls.equation_factory(
                f @ g >> h @ k, (f >> h) @ (g >> k))

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Pattern
    Var
    Unit
    Tensor
    Attr
    Call
    Op
    Sort
    Hom
    Sequent
    Atom
    Rule
    Generator
    Axiom
    AxiomFailure

.. admonition:: Functions

    .. autosummary::
        :template: function.rst
        :nosignatures:
        :toctree:

        rule
        generator
        axiom
        parse
        read
        declarations
        search

Reading a signature
-------------------

A module stating a rule defers its annotations with ``from __future__
import annotations``, so that :func:`parse` finds each as the expression
it is written as and evaluates it in the environment of the sequent, see
:func:`read`: the type parameters are :class:`Var` s, ``C0``, ``C1`` and
``Self`` are :class:`Sort` s and ``Atom`` marks a sort atomic. The
patterns carry the operators, so that Python reads the expression:
``C1[A, B]`` subscripts a sort into a :class:`Hom`, ``X @ X.r`` is the
:class:`Tensor` of a variable with its :class:`Attr`, ``M.delay()`` a
:class:`Call`, ``X << Y`` an :class:`Op` and ``1`` the :class:`Unit`.
The bound of a type parameter is its sort, evaluated as Python does:
``C0`` for any object — the type parameter of the class, or the
:data:`C0` of this module in a class that has none — ``Atom[C0]`` for
one with a single generator. The head of a sort or a hom is resolved
only once the rule is bound to a category, in the :attr:`Rule.scope`
where ``Self`` is the category and ``C0``, ``C1`` its objects and
arrows.

Matching
--------

A conclusion is matched against a goal, a pair of an optional domain and
codomain, by unification over the free monoid of objects: a
:class:`Tensor` splits the goal at every position, a :class:`Var` binds
once and compares afterwards, an adjoint ``X.r`` inverts to ``X`` as the
left adjoint of the goal. What cannot be inverted, an exponential
``X << Y`` or a delay ``M.delay()``, is kept as a residual equation and
checked once every variable is instantiated. A match is a substitution
together with its residuals.

Search
------

:func:`search` builds a term of a goal type by choosing, at each step, a
free box, a :class:`Generator` whose conclusion matches the goal, or a
:class:`Rule` whose conclusion matches and whose premises are searched
recursively with one less unit of depth. A category tunes the search by
declaring its rules and generators: a level of :mod:`discopy.abc` adds
the structure it axiomatises, a concrete diagram class may add more.
"""

from __future__ import annotations

import __future__
import inspect
import operator
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from dataclasses import KW_ONLY, dataclass, field, replace
from functools import reduce, wraps
from types import MethodType
from typing import TYPE_CHECKING, ClassVar, TypeVar
from typing import Self as _Self

from discopy.utils import AxiomError, factory_name

if TYPE_CHECKING:
    from hypothesis import strategies as st


class Atom:
    """
    The sort of atomic objects: ``Atom[C0]`` in a signature stands for the
    objects of ``C0`` with exactly one generator, whether ``C0`` is a sort
    or the type parameter of the class stating the rule.

    >>> Atom[Sort("C0")]
    Sort(head='C0', atomic=True)
    >>> Atom[TypeVar("C1")]
    Sort(head='C1', atomic=True)
    """
    def __class_getitem__(cls, item):
        return replace(sort(item), atomic=True)


def sort(value) -> Sort:
    """ A sort as written in a bound: itself, or a type parameter by name. """
    if isinstance(value, Sort):
        return value
    if isinstance(value, TypeVar):
        return Sort(value.__name__)
    raise TypeError(f"Expected a sort, got {value!r}.")


type Substitution = dict[str, object]
type Residuals = tuple[tuple["Pattern", object], ...]
type Match = tuple[Substitution, Residuals]


@dataclass(frozen=True)
class Sort:
    """
    The sort of an object variable: the instances of the type its ``head``
    resolves to in the scope of a bound rule, atomic or not. An attribute
    of a sort is a longer head, ``Self.dom.ob``, and subscripting a sort
    with two patterns is the :class:`Hom` between them.

    >>> print(Sort("C0", atomic=True))
    Atom[C0]
    >>> Sort("Self").dom.ob
    Sort(head='Self.dom.ob', atomic=False)
    >>> print(Sort("C1")[Var('A', Sort()), 1])
    C1[A, 1]
    """

    head: str = "C0"
    atomic: bool = False

    def __getattr__(self, name: str) -> Sort:
        if name.startswith("_"):
            raise AttributeError(name)
        return Sort(f"{self.head}.{name}", self.atomic)

    def __getitem__(self, key):
        if not isinstance(key, tuple) or len(key) != 2:
            raise TypeError(f"Expected a domain and a codomain, got {key}.")
        dom, cod = key
        return Hom(pattern(dom), pattern(cod), self.head)

    def resolve(self, scope: dict) -> type:
        """ The type the head stands for, a path from a root of the scope. """
        root, *path = self.head.split(".")
        return reduce(getattr, path, scope[root])

    def strategy(self, scope: dict, types=None):
        """
        Generate an object of the sort, from ``types`` in place of the
        strategy of the objects ``C0`` when given.
        """
        resolved = self.resolve(scope)
        base = types if types is not None and resolved is scope["C0"]\
            else resolved.strategy()
        return base.filter(lambda value: len(value) == 1)\
            if self.atomic else base

    def __str__(self):
        return f"Atom[{self.head}]" if self.atomic else self.head


class Pattern(ABC):
    """
    A pattern for the objects of a category, with variables to instantiate.

    Matching a value yields every substitution unifying the pattern with it,
    each with the residual equations it could not invert.
    """
    @property
    @abstractmethod
    def variables(self) -> tuple[str, ...]:
        """ The names of the variables of the pattern, in order. """

    @abstractmethod
    def instantiate(self, subst: Substitution, unit: Callable) -> object:
        """
        The object the pattern stands for under a substitution.

        Parameters:
            subst : The values of the variables, by name.
            unit : The object type, called to build the unit.
        """

    def match(self, value, subst: Substitution = None,
              residuals: Residuals = ()) -> Iterator[Match]:
        """
        Unify the pattern with a value, or with anything at all when the
        value is :obj:`None`.

        >>> from discopy.monoidal import Ty
        >>> x, y = Ty('x'), Ty('y')
        >>> A, B = Var('A', Sort()), Var('B', Sort())
        >>> for subst, _ in Tensor((A, B)).match(x @ y):
        ...     print(subst['A'], '|', subst['B'])
        Ty() | x @ y
        x | y
        x @ y | Ty()
        """
        subst = {} if subst is None else subst
        if value is None:
            yield subst, residuals
        else:
            yield from self.unify(value, subst, residuals)

    def unify(self, value, subst: Substitution,
              residuals: Residuals) -> Iterator[Match]:
        """
        Unify the pattern with a concrete value; by default the equation is
        kept as a residual, checked once the variables are instantiated.
        """
        yield subst, residuals + ((self, value), )

    def __matmul__(self, other):
        return Tensor(factors(self) + factors(pattern(other)))

    def __rmatmul__(self, other):
        return Tensor(factors(pattern(other)) + factors(self))

    def __lshift__(self, other):
        return Op("<<", self, pattern(other))

    def __rlshift__(self, other):
        return Op("<<", pattern(other), self)

    def __rshift__(self, other):
        return Op(">>", self, pattern(other))

    def __rrshift__(self, other):
        return Op(">>", pattern(other), self)

    def __getattr__(self, name: str):
        if name.startswith("_"):
            raise AttributeError(name)
        return Attr(self, name)


C0, C1, Self = Sort("C0"), Sort("C1"), Sort("Self")
"""
The objects and arrows of the category a rule is bound to, and the
category itself, in the environment its annotations are read in — and
in a module stating a rule on a class with no type parameters of its own.
"""


def pattern(value) -> Pattern:
    """ A pattern as an operand: itself, or the unit for the literal ``1``. """
    if isinstance(value, Pattern):
        return value
    if isinstance(value, int) and value == 1:
        return Unit()
    raise TypeError(f"Expected a pattern, got {value!r}.")


def factors(value: Pattern) -> tuple:
    """ The factors of a pattern as a tensor: itself, unless it is one. """
    return value.factors if isinstance(value, Tensor) else (value, )


@dataclass(frozen=True)
class Var(Pattern):
    """ A variable of a given sort. """

    name: str
    sort: Sort

    @property
    def variables(self):
        return (self.name, )

    def instantiate(self, subst, unit):
        return subst[self.name]

    def unify(self, value, subst, residuals):
        if self.name in subst:
            if subst[self.name] == value:
                yield subst, residuals
        elif not self.sort.atomic or len(value) == 1:
            yield dict(subst, **{self.name: value}), residuals

    def __str__(self):
        return self.name


@dataclass(frozen=True)
class Unit(Pattern):
    """ The monoidal unit, written ``1``. """

    variables = ()

    def instantiate(self, subst, unit):
        return unit()

    def unify(self, value, subst, residuals):
        if not len(value):
            yield subst, residuals

    def __str__(self):
        return "1"


@dataclass(frozen=True)
class Tensor(Pattern):
    """ The tensor of two or more patterns, flattened. """

    factors: tuple[Pattern, ...]

    @property
    def variables(self):
        return tuple(name for f in self.factors for name in f.variables)

    def instantiate(self, subst, unit):
        return reduce(operator.matmul, (
            factor.instantiate(subst, unit) for factor in self.factors))

    def unify(self, value, subst, residuals):
        yield from self.split(self.factors, value, subst, residuals)

    @classmethod
    def split(cls, factors, value, subst, residuals) -> Iterator[Match]:
        """ Unify the factors with the prefixes of a value, in turn. """
        if not factors:
            if not len(value):
                yield subst, residuals
            return
        head, *tail = factors
        for n in range(len(value) + 1):
            for subst_, residuals_ in head.unify(value[:n], subst, residuals):
                yield from cls.split(tail, value[n:], subst_, residuals_)

    def __str__(self):
        return " @ ".join(map(str, self.factors))


@dataclass(frozen=True)
class Attr(Pattern):
    """
    An attribute of a pattern, e.g. the adjoint ``X.r`` of a variable,
    inverted by the adjoint on the other side when matching.
    """

    base: Pattern
    name: str

    INVERSE: ClassVar[dict] = {"l": "r", "r": "l"}

    @property
    def variables(self):
        return self.base.variables

    def __call__(self, *args):
        return Call(self.base, self.name, args)

    def instantiate(self, subst, unit):
        return getattr(self.base.instantiate(subst, unit), self.name)

    def unify(self, value, subst, residuals):
        if self.name in self.INVERSE:
            inverse = getattr(value, self.INVERSE[self.name])
            yield from self.base.unify(inverse, subst, residuals)
        else:
            yield from super().unify(value, subst, residuals)

    def __str__(self):
        return f"{self.base}.{self.name}"


@dataclass(frozen=True)
class Call(Pattern):
    """ A method of a pattern called on constants, e.g. ``M.delay()``. """

    base: Pattern
    name: str
    args: tuple = ()

    @property
    def variables(self):
        return self.base.variables

    def instantiate(self, subst, unit):
        method = getattr(self.base.instantiate(subst, unit), self.name)
        return method(*self.args)

    def __str__(self):
        return f"{self.base}.{self.name}({', '.join(map(repr, self.args))})"


@dataclass(frozen=True)
class Op(Pattern):
    """ A binary operator between patterns, ``X << Y`` or ``X >> Y``. """

    symbol: str
    left: Pattern
    right: Pattern

    OPERATORS: ClassVar[dict] = {
        "<<": operator.lshift, ">>": operator.rshift}

    @property
    def variables(self):
        return self.left.variables + self.right.variables

    def instantiate(self, subst, unit):
        return self.OPERATORS[self.symbol](
            self.left.instantiate(subst, unit),
            self.right.instantiate(subst, unit))

    def __str__(self):
        return f"({self.left} {self.symbol} {self.right})"


@dataclass(frozen=True)
class Hom:
    """
    The type ``head[dom, cod]`` of the morphisms between two patterns.

    >>> from discopy.monoidal import Ty
    >>> A, B = Var('A', Sort()), Var('B', Sort())
    >>> hom = Hom(Tensor((A, B)), A)
    >>> print(hom)
    C1[A @ B, A]
    >>> x, y = Ty('x'), Ty('y')
    >>> [(str(s['A']), str(s['B'])) for s, _ in hom.match(x @ y, x)]
    [('x', 'y')]
    >>> list(hom.match(x @ y, y))
    []
    """

    dom: Pattern
    cod: Pattern
    head: str = "C1"

    @property
    def variables(self):
        return self.dom.variables + self.cod.variables

    def resolve(self, scope: dict) -> type:
        """ The type the head stands for, see :meth:`Sort.resolve`. """
        return Sort(self.head).resolve(scope)

    def instantiate(self, subst, unit) -> tuple:
        """ The domain and codomain under a substitution. """
        return (self.dom.instantiate(subst, unit),
                self.cod.instantiate(subst, unit))

    def match(self, dom=None, cod=None) -> Iterator[Match]:
        """ Unify with a goal, either side of which may be free. """
        for subst, residuals in self.dom.match(dom):
            yield from self.cod.match(cod, subst, residuals)

    def __str__(self):
        return f"{self.head}[{self.dom}, {self.cod}]"


@dataclass(frozen=True)
class Sequent:
    """
    A sequent: variables and their sorts, named premises and an optional
    conclusion. A premise is a :class:`Hom` to generate, a :class:`Sort` to
    generate, or a :class:`Pattern` to instantiate.

    >>> from discopy.abc import MonoidalCategory
    >>> print(MonoidalCategory.tensor.sequent)
    ... # doctest: +NORMALIZE_WHITESPACE
    A: C0, B: C0, C: C0, D: C0
    | self: C1[A, B], other: C1[C, D] ⊢ C1[A @ C, B @ D]
    """

    variables: dict[str, Sort] = field(default_factory=dict)
    premises: dict[str, Pattern | Sort | Hom] = field(default_factory=dict)
    conclusion: Hom | None = None

    def __str__(self):
        context = ", ".join(f"{n}: {s}" for n, s in self.variables.items())
        premises = ", ".join(f"{n}: {p}" for n, p in self.premises.items())
        left = " | ".join(part for part in (context, premises) if part)
        right = "" if self.conclusion is None else f" ⊢ {self.conclusion}"
        return left + right


def read(annotation: str, sorts: dict[str, Sort],
         namespace: dict = None) -> Pattern | Sort | Hom:
    """
    Read a pattern, a sort or a hom from an annotation, evaluated in the
    environment of the sequent: the variables in scope by name, ``C0``,
    ``C1`` and ``Self`` as sorts, ``Atom`` marking a sort atomic, over
    the namespace of the function stating it.

    >>> sorts = {"X": Sort("C0", atomic=True)}
    >>> print(read("C1[X @ X.r, 1]", sorts))
    C1[X @ X.r, 1]
    >>> read("Atom[Self.dom.ob]", sorts)
    Sort(head='Self.dom.ob', atomic=True)
    >>> read("X ** 2", sorts)
    Traceback (most recent call last):
     ...
    TypeError: Cannot read a pattern from X ** 2.
    """
    environment = {
        "Atom": Atom, "C0": C0, "C1": C1, "Self": Self,
        **{name: Var(name, sort) for name, sort in sorts.items()}}
    try:
        value = eval(annotation, dict(namespace or {}), environment)
    except Exception as error:
        raise TypeError(
            f"Cannot read a pattern from {annotation}.") from error
    return value if isinstance(value, (Sort, Hom)) else pattern(value)


def parse(function: Callable, conclusion: bool = True) -> Sequent:
    """
    Read the sequent a function states with its signature: the bound of
    each type parameter is the sort of a variable, the annotation of each
    parameter without a default a premise, the return annotation the
    conclusion. An unannotated first parameter is the receiver, ``cls`` or
    ``self``, and is skipped.

    Parameters:
        function : The function, stated under ``from __future__ import
            annotations``: :class:`Rule` refuses one compiled without it.
        conclusion : Whether to read the return annotation.

    >>> def then[A: C0, B: C0, C: C0](
    ...         self: C1[A, B], other: C1[B, C]) -> C1[A, C]:
    ...     ...
    >>> print(parse(then))
    A: C0, B: C0, C: C0 | self: C1[A, B], other: C1[B, C] ⊢ C1[A, C]
    >>> print(parse(then, conclusion=False))
    A: C0, B: C0, C: C0 | self: C1[A, B], other: C1[B, C]
    """
    function = inspect.unwrap(function)
    deferred = __future__.annotations.compiler_flag
    if not function.__code__.co_flags & deferred:
        raise TypeError(
            f"{function.__module__} states {function.__name__} without "
            "`from __future__ import annotations`.")
    sorts = {
        parameter.__name__: Sort() if parameter.__bound__ is None
        else sort(parameter.__bound__)
        for parameter in function.__type_params__}
    signature = inspect.signature(function)
    annotations = {
        name: parameter.annotation
        for name, parameter in signature.parameters.items()
        if parameter.annotation is not inspect.Parameter.empty}
    if signature.return_annotation is not inspect.Signature.empty:
        annotations["return"] = signature.return_annotation
    parameters = list(signature.parameters.values())
    if parameters and parameters[0].name not in annotations:
        parameters = parameters[1:]
    premises = [
        parameter.name for parameter in parameters
        if parameter.default is inspect.Parameter.empty
        and parameter.kind not in (
            inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)]
    for name in premises:
        if name not in annotations:
            raise TypeError(
                f"{function.__name__} states no pattern for {name}.")
    namespace = function.__globals__
    premises = {
        name: read(annotations[name], sorts, namespace) for name in premises}
    returns = read(annotations["return"], sorts, namespace)\
        if conclusion and "return" in annotations else None
    if conclusion and not isinstance(returns, Hom):
        raise TypeError(f"{function.__name__} concludes no hom type.")
    return Sequent(sorts, premises, returns)


@dataclass(repr=False)
class Rule[**P, T]:
    """
    An inference rule of a category, stated once on an abstract base class
    as a method whose signature :func:`parse` reads as a :class:`Sequent`,
    and inherited by every category below it.

    The declaration and the implementation are decoupled by name: the
    :attr:`sequent` is read from the declaration in :mod:`discopy.abc`
    while :func:`search` calls the attribute of the same name on the
    category, which a concrete class may override with its own method.
    Accessed on a class, a rule binds to it; accessed on an instance, it
    behaves as the method it decorates.

    Parameters:
        function : The function stating the rule, with the sequent as its
            signature; a classmethod is decorated inside ``classmethod``.
        category : The class the rule is bound to, :obj:`None` until
            :meth:`bind` or the attribute access on a class binds it.
        name : The attribute the rule is stored under, the name of the
            function by default.
        sequent : The parsed signature, read from the function by default.

    >>> from discopy.abc import Category
    >>> Category.then
    abc.Category.then
    >>> print(Category.then.sequent)
    A: C0, B: C0, C: C0 | self: C1[A, B], other: C1[B, C] ⊢ C1[A, C]
    """

    function: Callable
    _: KW_ONLY
    category: type[T] = None
    name: str = None
    sequent: Sequent = None

    concludes: ClassVar[bool] = True
    """ Whether the return annotation is read as the conclusion. """

    def __post_init__(self):
        if isinstance(self.function, classmethod):
            raise TypeError(
                f"Decorate {self.function.__func__.__name__} inside "
                "classmethod, not outside.")
        self.name = self.name or self.function.__name__
        if self.sequent is None:
            self.sequent = parse(self.function, conclusion=self.concludes)
        self.__doc__ = self.function.__doc__

    @property
    def __isabstractmethod__(self):
        return getattr(self.function, "__isabstractmethod__", False)

    def __repr__(self):
        if self.category is None:
            return f"{type(self).__name__}({self.name})"
        return f"{factory_name(self.category)}.{self.name}"

    def __str__(self):
        return f"{self.name}: {self.sequent}"

    def __hash__(self):
        return hash((self.function, self.category, self.name))

    def bind(self, category: type[T]) -> _Self:
        """ Bind the rule to a concrete category. """
        return replace(self, category=category)

    def __get__(self, instance, owner: type[T]):
        bound = self.bind(owner)
        return bound if instance is None else MethodType(bound, instance)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        return self.function(*args, **kwargs)

    @property
    def scope(self) -> dict:
        """
        What the heads of the sorts and homs stand for: the category for
        ``Self``, its objects and arrows for ``C0`` and ``C1``. A monoid,
        having no objects of its own, stands for both; the category a
        functor maps from is reachable as ``Self.dom``.
        """
        if self.category is None:
            raise TypeError(f"{self.name} is not bound to a class.")
        return {
            "Self": self.category,
            "C0": getattr(self.category, "ob", self.category),
            "C1": getattr(self.category, "ar", self.category)}

    @property
    def unit(self) -> Callable:
        """ The object type of the category, called to build the unit. """
        return self.scope["C0"]

    def match(self, dom=None, cod=None) -> Iterator[Match]:
        """ Unify the conclusion with a goal. """
        return self.sequent.conclusion.match(dom, cod)

    def generate(self, draw: Callable, hom: Callable, subst=None,
                 residuals: Residuals = (), types=None) -> tuple:
        """
        Draw the arguments of the rule inside a composite strategy, one
        premise at a time: a pattern is instantiated, a sort drawn, a hom
        drawn by ``hom(category, dom, cod)``. A variable is drawn from its
        sort the first time a premise needs it — except a variable standing
        alone on one side of a hom, which is left free for the search and
        read off the term it finds, so that the search is guided by the
        goal rather than by a draw. The residuals of a match are checked
        once every variable is bound, rejecting the example otherwise.

        Parameters:
            draw : The draw function of a
                :func:`hypothesis.strategies.composite`.
            hom : A function from a category, a domain and a codomain to a
                strategy for the morphisms of that type, either boundary
                free when :obj:`None`.
            subst : The variables already bound by a match.
            residuals : The equations a match could not invert.
            types : A strategy for the objects, overriding that of ``C0``.
        """
        from hypothesis import assume

        subst = dict(subst or {})
        sorts = self.sequent.variables

        def bound(*names):
            for name in names:
                if name not in subst:
                    strategy = sorts[name].strategy(self.scope, types)
                    subst[name] = draw(strategy, label=name)

        def side(pattern):
            if isinstance(pattern, Var) and pattern.name not in subst:
                return None
            bound(*pattern.variables)
            return pattern.instantiate(subst, self.unit)

        def read_off(pattern, value):
            if isinstance(pattern, Var) and pattern.name not in subst:
                assume(not pattern.sort.atomic or len(value) == 1)
                subst[pattern.name] = value

        args = []
        for name, premise in self.sequent.premises.items():
            if isinstance(premise, Hom):
                dom, cod = side(premise.dom), side(premise.cod)
                category = premise.resolve(self.scope)
                term = draw(hom(category, dom, cod), label=name)
                read_off(premise.dom, term.dom)
                read_off(premise.cod, term.cod)
                args.append(term)
            elif isinstance(premise, Sort):
                strategy = premise.strategy(self.scope, types)
                args.append(draw(strategy, label=name))
            else:
                bound(*premise.variables)
                args.append(premise.instantiate(subst, self.unit))
        for pattern, value in residuals:
            bound(*pattern.variables)
            assume(pattern.instantiate(subst, self.unit) == value)
        return subst, tuple(args)


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


class AxiomFailure(AxiomError):
    """
    A law declared broken, raised when the bound axiom is called: the
    reason is the message and :attr:`equation` is the law evaluated on the
    arguments, which a recorded counterexample must falsify.
    """

    def __init__(self, reason: str, equation):
        super().__init__(reason, equation)
        self.equation = equation


@dataclass(repr=False)
class Axiom[**P, T](Rule[P, T]):
    """
    An axiom of a category: a sequent with no conclusion, whose premises
    are the arguments of a property test, generated from their patterns.

    The category is the class the axiom is bound to, e.g.
    :class:`discopy.cat.Arrow` for the axioms of
    :class:`discopy.abc.Category`. The axiom is a classmethod of it,
    implicitly: its first parameter is the category and the remaining ones
    are generated from their annotations — an object for the typing of
    identities, three composable arrows for the associativity of
    composition, a term of the category itself for
    :meth:`discopy.axioms.Strategy.transparency`.

    Calling a bound axiom returns its own verdict: :obj:`NotImplemented`
    when the structure does not apply to the category, and the equation
    itself otherwise; a law declared broken raises an
    :class:`AxiomFailure` carrying that equation instead of returning it.

    A law is broken when *some* argument is a counterexample, not every one,
    so :attr:`broken` is declared by :meth:`failing` before any argument is
    generated — the property matrix marks such an axiom as an expected
    failure and lets the search find the counterexample.

    Parameters:
        function : The function stating the law, from the category and the
            generated arguments to an :class:`discopy.axioms.Equation`, or
            to :obj:`NotImplemented` when the structure does not apply.
        params : The parameters :meth:`weaken` passes to the strategy of
            every hom premise, restricting the law to a subspace.
        broken : Whether the law is declared broken by :meth:`failing`.
    """

    _: KW_ONLY
    params: dict = field(default_factory=dict)
    broken: bool = False

    concludes = False

    __hash__ = Rule.__hash__

    def __get__(self, instance, owner: type) -> _Self:
        return self.bind(owner)

    def modulo(self, up_to) -> _Self:
        """
        The same law with its equation compared up to a function, so that a
        category weakens an inherited axiom in one statement, e.g. a diagram
        compares the interchange law up to its normal form:
        ``Diagram.bifunctoriality = MonoidalCategory.bifunctoriality.modulo(
        Diagram.normal_form)``.
        """
        @wraps(self.function)
        def equation(*args, **kwargs):
            return self.function(*args, **kwargs).modulo(up_to)
        return replace(self, function=equation)

    def failing(self, reason: str) -> _Self:
        """
        The same law declared broken: calling it raises an
        :class:`AxiomFailure` with the reason as message and the equation
        evaluated on the arguments, e.g. ``braid_naturality =
        BraidedCategory.braid_naturality.failing("A free braid is a box.")``.
        """
        @wraps(self.function)
        def equation(*args, **kwargs):
            raise AxiomFailure(reason, self.function(*args, **kwargs))
        equation.__doc__ = reason
        return replace(self, function=equation, broken=True)

    def inapplicable(self, reason: str) -> _Self:
        """
        The same law declared not to apply to the category: it takes no
        argument and returns :obj:`NotImplemented`, with the reason as its
        documentation, e.g. ``trace_vanishing =
        TracedCategory.trace_vanishing.inapplicable("No trace.")``.
        """
        def law(cls):
            return NotImplemented
        law.__doc__ = reason
        return replace(
            self, function=law, sequent=Sequent(), params={}, broken=False)

    def weaken(self, **params) -> _Self:
        """
        The same law quantified over the subspace the given parameters cut
        out of the strategy of each hom premise, e.g.
        ``bifunctoriality.weaken(boundary_connected=True)`` on a diagram
        category compares the interchange law on the diagrams its normal
        form is defined for. Assigned to its own attribute beside a
        ``.failing`` declaration, it shows the matrix one expected failure
        and one green cell instead of one blanket expected failure.
        """
        return replace(self, params=dict(self.params, **params))

    @property
    def parameters(self) -> tuple[inspect.Parameter, ...]:
        """
        The parameters whose arguments the property matrix generates: all
        but the first, which is the category.
        """
        return tuple(
            inspect.signature(self.function).parameters.values())[1:]

    def strategy(self, **params) -> st.SearchStrategy:
        """
        Generate the arguments the bound axiom expects: one per parameter,
        from its pattern in the :attr:`scope` of the category. Keyword
        arguments are passed to the strategy of each hom premise, after
        those :meth:`weaken` declared.
        """
        from hypothesis import strategies as st

        if self.category is None:
            raise TypeError(f"{self.name} is not bound to a class.")
        params = dict(self.params, **params)

        def hom(category, dom, cod):
            return category.strategy(dom=dom, cod=cod, **params)

        @st.composite
        def arguments(draw):
            return self.generate(draw, hom)[1]

        return arguments()

    def falsify(self, **params) -> tuple:
        """
        Search for a shrunk counterexample to the bound axiom: arguments for
        which the verdict fails — the equation is false, or the
        implementation refuses to build its terms — raising
        :class:`hypothesis.errors.NoSuchExample` when no counterexample is
        found. Keyword arguments are passed to :func:`hypothesis.find`.

        >>> from discopy.cat import Arrow
        >>> Arrow.associativity.falsify()  # doctest: +ELLIPSIS
        Traceback (most recent call last):
         ...
        hypothesis.errors.NoSuchExample: No examples found of condition ...
        """
        from hypothesis import find

        def refutes(args):
            try:
                verdict = self(*args)
            except AxiomFailure:
                return True
            return verdict is not NotImplemented and not verdict

        return find(self.strategy(), refutes, **params)

    def arguments(self, *args: P.args, **kwargs: P.kwargs) -> dict:
        """ Bind the arguments to the :attr:`parameters` of the axiom. """
        if self.category is None:
            raise TypeError(f"{self.name} is not bound to a class.")
        bound = inspect.Signature(self.parameters).bind(*args, **kwargs)
        bound.apply_defaults()
        return dict(bound.arguments)

    def __call__(self, *args: P.args, **kwargs: P.kwargs):
        return self.function(self.category, **self.arguments(*args, **kwargs))


def rule[**P, T](function: Callable[P, T]) -> Rule[P, T]:
    """ Decorate a method as an inference rule, its signature the sequent. """
    return Rule(function)


def generator[**P, T](function: Callable[P, T]) -> Generator[P, T]:
    """ Decorate a method as a logical constant, its signature the sequent. """
    return Generator(function)


def axiom[**P, T](function: Callable[P, T]) -> Axiom[P, T]:
    """
    Decorate an equation as a categorical axiom: a classmethod of its
    category, implicitly, whose remaining parameters are generated.
    """
    return Axiom(function)


def declarations[R: Rule](cls: type, kind: type[R],
                          shadowed: bool = True) -> dict[str, R]:
    """
    The declarations of exactly a kind inherited by a class, bound to it and
    keyed by name, subclasses overriding bases. A :class:`Rule` survives a
    plain method assigned over it, which is its implementation; an
    :class:`Axiom` does not, so assigning anything that is not an axiom over
    an inherited law drops it altogether rather than restating it.

    Parameters:
        cls : The class, e.g. :class:`discopy.monoidal.Diagram`.
        kind : :class:`Rule`, :class:`Generator` or :class:`Axiom`.
        shadowed : Whether a plain override keeps the declaration.

    >>> from discopy.monoidal import Diagram
    >>> list(declarations(Diagram, Rule))
    ['then', 'tensor']
    """
    result = {}
    for base in reversed(cls.__mro__):
        for name, value in base.__dict__.items():
            value = value.__func__ if isinstance(value, classmethod) else value
            if type(value) is kind:
                result[name] = value.bind(cls)
            elif name in result and not shadowed:
                del result[name]
    return result


def search(category: type, free: Callable, *, dom=None, cod=None,
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
