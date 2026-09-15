"""
Sequent patterns and their matching: the language in which a category
states its rules, generators and axioms.

A sequent is the signature of a method on an abstract base class of
:mod:`discopy.abc`: its type parameters are the variables and their
sorts, its parameters the premises, its return annotation the conclusion.

.. code-block:: python

    class MonoidalCategory[C0, C1](Category[C0, C1]):
        @rule
        @abstractmethod
        def tensor[A: C0, B: C0, C: C0, D: C0](
                self: C1[A, B], other: C1[C, D]) -> C1[A @ C, B @ D]:
            ...

The module stating it defers its annotations with ``from __future__
import annotations``, and :func:`parse` evaluates each in an environment
where the type parameters are :class:`Var` s, ``C0``, ``C1`` and ``Self``
:class:`Sort` s and ``Atom`` marks a sort atomic: ``C1[A, B]`` is a
:class:`Hom`, ``X @ X.r`` a :class:`Tensor` of a variable with its
:class:`Attr`, ``X << Y`` an :class:`Op`, ``1`` the :class:`Unit`, and
``L[X, Y]`` for a variable ``L: Bool`` the :class:`Choice` of one or the
other, e.g. the left or right evaluation. The bound of a type parameter
is its sort; a class's ``C0: Pregroup`` reaches
the sort as its bound, so that ``X.l`` and ``X.r`` are patterns of a
rigid category only, ``X << Y`` of a residuated one and ``M.d`` of one
with a delay: the abstract classes bound the patterns without being
imported here.

A conclusion is matched against a goal, a pair of an optional domain and
codomain, by unification over the free monoid of objects: a
:class:`Tensor` splits the goal at every position, a :class:`Var` binds
once, an adjoint ``X.r`` inverts to ``X``. What cannot be inverted, an
exponential or a delay, is a residual equation checked once every
variable is instantiated.

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
    Op
    Choice
    Sort
    Bool
    Hom
    Sequent
    Atom
    Declaration

.. admonition:: Functions

    .. autosummary::
        :template: function.rst
        :nosignatures:
        :toctree:

        parse
        read
        cell
        declarations
"""

from __future__ import annotations

import __future__
import inspect
import operator
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from dataclasses import KW_ONLY, dataclass, field, replace
from functools import reduce
from typing import TYPE_CHECKING, ClassVar, TypeVar

from discopy.utils import factory_name

if TYPE_CHECKING:
    from discopy import abc


class Atom:
    """
    The sort of atomic objects: ``Atom[C0]`` in a signature stands for the
    objects of ``C0`` with exactly one generator.

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
    if isinstance(value, type) and issubclass(value, Sort):
        return value()
    if isinstance(value, TypeVar):
        return Sort(value.__name__, bound=value.__bound__)
    raise TypeError(f"Expected a sort, got {value!r}.")


type Substitution = dict[str, object]
type Residuals = tuple[tuple["Pattern", object], ...]
type Match = tuple[Substitution, Residuals]


@dataclass(frozen=True)
class Sort:
    """
    The sort of an object variable: the instances of the type its ``head``
    resolves to in the scope of a bound declaration, atomic or not, and
    the class of :mod:`discopy.abc` bounding them when the sort is that of
    a bounded type parameter. An attribute of a sort is a longer head,
    ``Self.dom.ob``, and subscripting a sort with two patterns is the
    :class:`Hom` between them.

    >>> print(Sort("C0", atomic=True))
    Atom[C0]
    >>> Sort("Self").dom.ob
    Sort(head='Self.dom.ob', atomic=False)
    >>> print(Sort("C1")[Var('A', Sort()), 1])
    C1[A, 1]
    """

    head: str = "C0"
    atomic: bool = False
    bound: type[abc.ColouredMonoid] | None = field(
        default=None, compare=False, repr=False)

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


@dataclass(frozen=True)
class Bool(Sort):
    """
    The sort of a boolean variable ``L: Bool``, the :class:`Choice` between
    two patterns ``L[then, otherwise]``; canonically :obj:`True`.
    """

    head: str = "Bool"

    def resolve(self, scope: dict) -> type:
        return bool

    def strategy(self, scope: dict, types=None):
        from hypothesis import strategies as st

        return st.booleans()


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

    @property
    @abstractmethod
    def bound(self) -> type[abc.ColouredMonoid] | None:
        """
        The class of :mod:`discopy.abc` bounding the objects the pattern
        stands for, :obj:`None` when nothing does.
        """

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


C0, C1 = Sort("C0"), Sort("C1")
"""
The objects and arrows of the category a declaration is bound to, in the
environment its annotations are read in and in a module stating a rule on
a class with no type parameters of its own.
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


def member(bound: type | None, name: str, pattern: Pattern) -> None:
    """
    Check that the bound declares a member, e.g. ``l`` for a
    :class:`abc.Pregroup` or ``d`` for a :class:`abc.DelayedMonoid`: a
    pattern only does what the sort of its variables allows.

    >>> from discopy.abc import Pregroup
    >>> Var('X', Sort(bound=Pregroup)).l
    Attr(base=Var(name='X', sort=Sort(head='C0', atomic=False)), name='l')
    >>> Var('X', Sort()).l
    Traceback (most recent call last):
     ...
    TypeError: X has no l: its objects are unbounded.
    """
    if not hasattr(bound, name):
        objects = "unbounded" if bound is None\
            else f"bounded by {bound.__name__}"
        raise TypeError(f"{pattern} has no {name}: its objects are {objects}.")


@dataclass(frozen=True)
class Var(Pattern):
    """ A variable of a given sort. """

    name: str
    sort: Sort

    @property
    def variables(self):
        return (self.name, )

    @property
    def bound(self):
        return self.sort.bound

    def instantiate(self, subst, unit):
        return subst[self.name]

    def unify(self, value, subst, residuals):
        if self.name in subst:
            if subst[self.name] == value:
                yield subst, residuals
        elif not self.sort.atomic or len(value) == 1:
            yield dict(subst, **{self.name: value}), residuals

    def __getitem__(self, key):
        if not isinstance(self.sort, Bool):
            raise TypeError(f"{self} is no boolean to choose by.")
        then, otherwise = key
        return Choice(self, pattern(then), pattern(otherwise))

    def __str__(self):
        return self.name


@dataclass(frozen=True)
class Unit(Pattern):
    """ The monoidal unit, written ``1``. """

    variables = ()
    bound = None

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

    @property
    def bound(self):
        return next((
            f.bound for f in self.factors if f.bound is not None), None)

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
    An attribute of a pattern its bound declares, e.g. the adjoint ``X.r``,
    inverted by the adjoint on the other side when matching.
    """

    base: Pattern
    name: str

    INVERSE: ClassVar[dict] = {"l": "r", "r": "l"}

    def __post_init__(self):
        member(self.bound, self.name, self.base)

    @property
    def variables(self):
        return self.base.variables

    @property
    def bound(self):
        return self.base.bound

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
class Op(Pattern):
    """
    An exponential ``X << Y`` or ``X >> Y``, the ``over`` and ``under`` of
    a residuated monoid.
    """

    symbol: str
    left: Pattern
    right: Pattern

    OPERATORS: ClassVar[dict] = {
        "<<": (operator.lshift, "over"), ">>": (operator.rshift, "under")}

    def __post_init__(self):
        member(self.bound, self.OPERATORS[self.symbol][1], self.left)

    @property
    def variables(self):
        return self.left.variables + self.right.variables

    @property
    def bound(self):
        return self.left.bound or self.right.bound

    def instantiate(self, subst, unit):
        return self.OPERATORS[self.symbol][0](
            self.left.instantiate(subst, unit),
            self.right.instantiate(subst, unit))

    def __str__(self):
        return f"({self.left} {self.symbol} {self.right})"


@dataclass(frozen=True)
class Choice(Pattern):
    """
    The choice ``L[then, otherwise]`` of a pattern by a boolean variable,
    matching a value by either branch and binding the variable to which.
    """

    var: Var
    then: Pattern
    otherwise: Pattern

    @property
    def variables(self):
        return (self.var.name, ) + self.then.variables\
            + self.otherwise.variables

    @property
    def bound(self):
        return self.then.bound or self.otherwise.bound

    def instantiate(self, subst, unit):
        branch = self.then if subst[self.var.name] else self.otherwise
        return branch.instantiate(subst, unit)

    def unify(self, value, subst, residuals):
        for choice, branch in ((True, self.then), (False, self.otherwise)):
            for subst_, residuals_ in self.var.unify(choice, subst, residuals):
                yield from branch.unify(value, subst_, residuals_)

    def __str__(self):
        return f"{self.var}[{self.then}, {self.otherwise}]"


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
    Variables and their sorts, named premises and an optional conclusion.
    A premise is a :class:`Hom` to generate, a :class:`Sort` to generate,
    or a :class:`Pattern` to instantiate; those with a default are passed
    by keyword.

    >>> from discopy.abc import MonoidalCategory
    >>> print(MonoidalCategory.tensor.sequent)
    ... # doctest: +NORMALIZE_WHITESPACE
    A: C0, B: C0, C: C0, D: C0
    | self: C1[A, B], other: C1[C, D] ⊢ C1[A @ C, B @ D]
    """

    variables: dict[str, Sort] = field(default_factory=dict)
    premises: dict[str, Pattern | Sort | Hom] = field(default_factory=dict)
    conclusion: Hom | None = None
    keywords: frozenset[str] = frozenset()

    def __str__(self):
        context = ", ".join(f"{n}: {s}" for n, s in self.variables.items())
        premises = ", ".join(f"{n}: {p}" for n, p in self.premises.items())
        left = " | ".join(part for part in (context, premises) if part)
        right = "" if self.conclusion is None else f" ⊢ {self.conclusion}"
        return left + right


def read(annotation: str, sorts: dict[str, Sort],
         namespace: dict = None) -> Pattern | Sort | Hom:
    """
    Read a pattern, a sort or a hom from an annotation evaluated in the
    environment of the sequent, over the namespace of the function.

    >>> from discopy.abc import Pregroup
    >>> sorts = {"X": Sort("C0", atomic=True, bound=Pregroup)}
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
        "Atom": Atom, "Bool": Bool, "C0": C0, "C1": C1, "Self": Sort("Self"),
        **{name: Var(name, sort) for name, sort in sorts.items()}}
    try:
        value = eval(annotation, namespace or {}, environment)
    except Exception as error:
        raise TypeError(
            f"Cannot read a pattern from {annotation}.") from error
    return value if isinstance(value, (Sort, Hom)) else pattern(value)


def parse(function: Callable, conclusion: bool = True) -> Sequent:
    """
    The sequent a function states with its signature, deferred with
    ``from __future__ import annotations``: the bound of each type
    parameter the sort of a variable, each parameter without a default a
    premise — with one, only if annotated by a variable, e.g. ``left: L =
    True`` — the return annotation the conclusion when asked for. An
    unannotated first parameter, ``cls`` or ``self``, is skipped.

    >>> def then[A: C0, B: C0, C: C0](
    ...         self: C1[A, B], other: C1[B, C]) -> C1[A, C]:
    ...     ...
    >>> print(parse(then))
    A: C0, B: C0, C: C0 | self: C1[A, B], other: C1[B, C] ⊢ C1[A, C]
    >>> print(parse(then, conclusion=False))
    A: C0, B: C0, C: C0 | self: C1[A, B], other: C1[B, C]
    """
    function = inspect.unwrap(function)
    if not function.__code__.co_flags & __future__.annotations.compiler_flag:
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
    keywords = frozenset(
        parameter.name for parameter in parameters
        if parameter.default is not inspect.Parameter.empty
        and annotations.get(parameter.name) in sorts)
    namespace = function.__globals__
    premises = {
        name: read(annotations[name], sorts, namespace)
        for name in premises + sorted(keywords)}
    returns = read(annotations["return"], sorts, namespace)\
        if conclusion and "return" in annotations else None
    if conclusion and not isinstance(returns, Hom):
        raise TypeError(f"{function.__name__} concludes no hom type.")
    return Sequent(sorts, premises, returns, keywords)


@dataclass(repr=False)
class Declaration[**P, T]:
    """
    A sequent stated by a function on an abstract base class and inherited
    by every category below it: the base of the rules and generators of
    :mod:`discopy.search` and of the axioms of :mod:`discopy.axioms`.

    Parameters:
        function : The function stating the sequent as its signature; a
            classmethod is decorated inside ``classmethod``.
        category : The class the declaration is bound to, :obj:`None`
            until :meth:`bind` or the attribute access on a class binds it.
        name : The attribute the declaration is stored under, the name of
            the function by default.
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

    def bind(self, category: type[T]) -> Declaration[P, T]:
        """ Bind the declaration to a concrete category. """
        return replace(self, category=category)

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

    def canonical(self) -> dict:
        """
        The canonical arguments of the sequent, by name: each variable an
        object named after it, each premise a :func:`cell` named after its
        parameter, so that a declaration reads as a schema.

        >>> from discopy.abc import MonoidalCategory
        >>> from discopy.monoidal import Diagram
        >>> tensor = MonoidalCategory.tensor.bind(Diagram)
        >>> for name, box in tensor.canonical().items():
        ...     print(f"{name}: {box.dom} -> {box.cod}")
        self: A -> B
        other: C -> D
        """
        subst = {
            name: cell(sort.resolve(self.scope), name)
            for name, sort in self.sequent.variables.items()}
        args = {}
        for name, premise in self.sequent.premises.items():
            if isinstance(premise, Hom):
                dom, cod = premise.instantiate(subst, self.unit)
                args[name] = cell(premise.resolve(self.scope), name, dom, cod)
            elif isinstance(premise, Sort):
                args[name] = cell(premise.resolve(self.scope), name)
            else:
                args[name] = premise.instantiate(subst, self.unit)
        return args

    def generate(self, draw: Callable, hom: Callable, subst=None,
                 residuals: Residuals = (), types=None) -> tuple:
        """
        Draw the arguments of the sequent inside a composite strategy, by
        name and one premise at a time: a pattern is instantiated, a sort
        drawn, a hom drawn by ``hom(category, dom, cod)`` — a premise of
        the sort of the arrows, ``f: C1``, being the hom with both sides
        free. A variable is drawn from its sort the first time a premise
        needs it, except one standing alone on a side of a hom, which is
        read off the term the search finds so that the goal guides the
        search. The residuals of a match are checked once every variable
        is bound, rejecting the example otherwise.

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

        args = {}
        for name, premise in self.sequent.premises.items():
            if isinstance(premise, Hom):
                dom, cod = side(premise.dom), side(premise.cod)
                category = premise.resolve(self.scope)
                term = draw(hom(category, dom, cod), label=name)
                read_off(premise.dom, term.dom)
                read_off(premise.cod, term.cod)
                args[name] = term
            elif isinstance(premise, Sort)\
                    and premise.resolve(self.scope) is self.scope["C1"]:
                arrows = hom(self.scope["C1"], None, None)
                args[name] = draw(arrows, label=name)
            elif isinstance(premise, Sort):
                strategy = premise.strategy(self.scope, types)
                args[name] = draw(strategy, label=name)
            else:
                bound(*premise.variables)
                args[name] = premise.instantiate(subst, self.unit)
        for pattern, value in residuals:
            bound(*pattern.variables)
            assume(pattern.instantiate(subst, self.unit) == value)
        return subst, args


def cell(factory: type, name: str, dom=None, cod=None):
    """
    A cell of a class named after a parameter or a variable: a box of a
    class with a ``box_factory``, between ``dom`` and ``cod`` or objects
    named ``x`` and ``y``, else an instance of the class of that name.

    >>> from discopy.monoidal import Box, Diagram, Ty
    >>> assert cell(Diagram, 'f') == Box('f', Ty('x'), Ty('y'))
    >>> assert cell(Ty, 'A') == Ty('A')
    """
    if hasattr(factory, "box_factory"):
        dom = factory.ob("x") if dom is None else dom
        cod = factory.ob("y") if cod is None else cod
        return factory.box_factory(name, dom, cod)
    return factory(name)


def declarations[D: Declaration](cls: type, kind: type[D],
                                 shadowed: bool = True) -> dict[str, D]:
    """
    The declarations of exactly a kind inherited by a class, bound to it and
    keyed by name, subclasses overriding bases. A rule survives a plain
    method assigned over it, its implementation; an axiom does not, so
    assigning anything that is not an axiom over an inherited law drops it
    rather than restating it.

    >>> from discopy.monoidal import Diagram
    >>> from discopy.search import Rule
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
