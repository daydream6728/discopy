"""
Sequent patterns and their matching: the language in which a category
states its rules, generators and axioms.

A sequent is the signature of a method on an abstract base class of
:mod:`discopy.abc`: its type parameters are the variables and their
sorts, its parameters the premises, its return annotation the conclusion.

.. code-block:: python

    class MonoidalCategory[C0: ColouredMonoid, C1: MonoidalCategory](
            Category[C0, C1]):
        @rule
        @abstractmethod
        def tensor[A, B, C, D](
                self: Hom[C1, A, B], other: Hom[C1, C, D]
        ) -> Annotated[C1, "A @ C", "B @ D"]:
            ...

The signature typechecks as it reads: a metavariable is one of the
method's own :pep:`695` type parameters, its sort the bound — an object
of ``C0`` when unbounded, an :class:`Atom` or a :class:`Count` when
declared — ``Hom[C1, A, B]`` types as a plain ``C1`` by substituting the
base of ``type Hom[C, A, B] = Annotated[C, A, B]``, and a pattern with
an operator on a type parameter is quoted in the metadata of a
``typing.Annotated``, which is no part of the type. The module stating
it defers its annotations with ``from __future__ import annotations``
and :func:`parse` evaluates each in an environment where the type
parameters are :class:`Var` s, ``C0``, ``C1`` and ``Self``
:class:`Sort` s and ``Hom`` and ``Annotated`` build the :class:`HomType`
between two boundaries: ``X @ X.r`` is a :class:`Tensor` of a variable
with its :class:`Adjoint`, ``M.d`` a :class:`Delay`, ``X << Y`` an
:class:`Exp`, ``X ** N`` a :class:`Repeat` and ``Unit[C0]`` the
:class:`Unit`.

A pattern is generic in the colours ``C0`` and the objects ``C1`` of the
monoid it stands in, and the bound of ``C1`` is the least structure the
pattern needs: a :class:`Tensor` needs a :class:`abc.ColouredMonoid`, an
:class:`Adjoint` a :class:`abc.Pregroup`, a :class:`Delay` a
:class:`abc.DelayedMonoid`. A variable's sort carries the bound of the
objects of the class stating the rule, ``C0: Pregroup``, and a pattern
refuses a variable whose sort is bounded below what it needs. Those
bounds are the classes of :mod:`discopy.abc`, evaluated lazily, so that
this module imports it while it imports this one.

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
    Adjoint
    Delay
    Exp
    Repeat
    HomType
    Sort
    Atom
    Count
    Sequent
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
from typing import (
    Annotated, ClassVar, TypeAliasType, TypeVar, get_args, get_origin)

from discopy import abc
from discopy.utils import factory_name


type Substitution = dict[str, object]
type Residuals = tuple[tuple["Pattern", object], ...]
type Match = tuple[Substitution, Residuals]

type Hom[C, A, B] = Annotated[C, A, B]
"""
The cells from ``A`` to ``B`` at the level ``C``, in the annotations of
a declaration: a use-site ``self: Hom[C1, A, B]`` types as a plain
``C1`` by substituting the base, so the law bodies typecheck on the
cells they compose, and evaluates to the :class:`HomType` from ``A`` to
``B``; a bound ``def tensor[X, Y, A: Hom[C1, X, Y]]`` declares a higher
metavariable between two boundaries, the telescope ``{A : C1 X Y}`` of
a dependently typed language, see :func:`parse`.
"""


@dataclass(frozen=True)
class Sort:
    """
    The sort of an object variable: the instances of the type its ``head``
    resolves to in the scope of a bound declaration, atomic or not, and
    the class of :mod:`discopy.abc` bounding them when known. An attribute
    of a sort is a longer head, ``Self.dom.ob``, and subscripting a sort
    with two patterns is the :class:`HomType` between them.

    >>> print(Sort("C0", atomic=True))
    Atom[C0]
    >>> Sort("Self").dom.ob
    Sort(head='Self.dom.ob', atomic=False)
    >>> X = Var('X', Sort(bound=abc.ColouredMonoid))
    >>> print(Sort("C1")[X, Unit[X.sort]])
    C1[X, Unit[C0]]
    """

    head: str = "C0"
    atomic: bool = False
    bound: type | None = field(default=None, compare=False, repr=False)

    def __getattr__(self, name: str) -> Sort:
        if name.startswith("_"):
            raise AttributeError(name)
        return Sort(f"{self.head}.{name}", self.atomic)

    def __getitem__(self, key) -> HomType:
        if not isinstance(key, tuple) or len(key) != 2:
            raise TypeError(f"Expected a domain and a codomain, got {key}.")
        dom, cod = key
        return HomType(pattern(dom), pattern(cod), self.head)

    def resolve(self, scope: dict) -> type:
        """ The type the head stands for, a path from a root of the scope. """
        root, *path = self.head.split(".")
        return reduce(getattr, path, scope[root])

    def strategy(self, scope: dict, types=None):
        """
        Generate an object of the sort, from ``types`` in place of the
        strategy of the objects ``C0`` when given; a :class:`Count` draws
        a small number.
        """
        from hypothesis import strategies as st

        if self.head == "Count":
            return st.integers(min_value=0, max_value=3)
        resolved = self.resolve(scope)
        base = types if types is not None and resolved is scope["C0"]\
            else resolved.strategy()
        return base.filter(lambda value: len(value) == 1)\
            if self.atomic else base

    def __str__(self):
        return f"Atom[{self.head}]" if self.atomic else self.head


class Atom:
    """
    The sort of atomic objects: the bound ``def cups[X: Atom]`` declares
    ``X`` an object with exactly one generator, and ``Atom[C0]`` in a
    quoted pattern stands for the same sort.

    >>> Atom[Sort("C0")]
    Sort(head='C0', atomic=True)
    """
    def __class_getitem__(cls, item):
        return replace(sort(item), atomic=True)


class Count:
    """
    The sort of small numbers: the bound ``def spiders[N: Count]``
    declares ``N`` a number of repetitions, see :class:`Repeat`.
    """


def sort(value) -> Sort:
    """
    A sort as written in a bound: itself, :class:`Atom` or :class:`Count`
    bare, a type parameter by name and bounded as it is, or a class of
    :mod:`discopy.abc` bounding the objects.
    """
    if isinstance(value, Sort):
        return value
    if isinstance(value, type) and issubclass(value, Atom):
        return Sort(atomic=True)
    if isinstance(value, type) and issubclass(value, Count):
        return Sort("Count")
    if isinstance(value, TypeVar):
        bound = value.__bound__
        return Sort(value.__name__,
                    bound=bound if isinstance(bound, type) else None)
    if isinstance(value, type) and issubclass(value, abc.Category):
        return Sort(bound=value)
    raise TypeError(f"Expected a sort, got {value!r}.")


def pattern(value) -> Pattern:
    """ A pattern as an operand, refusing anything else. """
    if not isinstance(value, Pattern):
        raise TypeError(f"Expected a pattern, got {value!r}.")
    return value


class Pattern[C0, C1: abc.Category](ABC):
    """
    A pattern for the objects of a category, with variables to instantiate,
    generic in the colours ``C0`` and objects ``C1`` of the monoid it
    stands in: the bound of ``C1`` is the :meth:`level` the pattern needs.

    Matching a value yields every substitution unifying the pattern with it,
    each with the residual equations it could not invert.
    """
    def __post_init__(self):
        """
        Check the objects the pattern stands for are bounded by its
        :meth:`level`; a variable or a hom adds no structure to its parts
        and skips the check.
        """
        bound, required = self.bound, self.level()
        if bound is None or not issubclass(bound, required):
            raise TypeError(f"{self} needs a {required.__name__}, its objects "
                            + ("are unbounded." if bound is None
                               else f"are bounded by {bound.__name__}."))

    @classmethod
    def level(cls) -> type[abc.Category]:
        """ The bound of ``C1``, the least structure the pattern needs. """
        return cls.__type_params__[1].__bound__

    @property
    @abstractmethod
    def variables(self) -> tuple[str, ...]:
        """ The names of the variables of the pattern, in order. """

    @property
    @abstractmethod
    def bound(self) -> type | None:
        """
        The class of :mod:`discopy.abc` bounding the objects the pattern
        stands for, :obj:`None` when none is known.
        """

    @abstractmethod
    def instantiate(self, subst: Substitution, unit: Callable) -> object:
        """
        The object the pattern stands for under a substitution.

        Parameters:
            subst : The values of the variables, by name.
            unit : The object type, called to build the unit.
        """

    def match(self, value, subst: Substitution | None = None,
              residuals: Residuals = ()) -> Iterator[Match]:
        """
        Unify the pattern with a value, or with anything at all when the
        value is :obj:`None`.

        >>> from discopy.monoidal import Ty
        >>> x, y = Ty('x'), Ty('y')
        >>> A, B = (Var(n, Sort(bound=abc.ColouredMonoid)) for n in "AB")
        >>> for subst, _ in (A @ B).match(x @ y):
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

    def __lshift__(self, other):
        return Exp("<<", self, pattern(other))

    def __rshift__(self, other):
        return Exp(">>", self, pattern(other))

    def __pow__(self, other):
        if not isinstance(other, Var):
            raise TypeError(f"Expected a Count variable, got {other!r}.")
        return Repeat(self, other)

    def __getattr__(self, name: str):
        if name in ("l", "r"):
            return Adjoint(self, name)
        if name == "d":
            return Delay(self)
        raise AttributeError(name)


C0, C1 = Sort("C0"), Sort("C1")
"""
The objects and arrows of the category a declaration is bound to, in the
environment its annotations are read in and in a module stating a rule on
a class with no type parameters of its own.
"""


def factors(value: Pattern) -> tuple:
    """ The factors of a pattern as a tensor: itself, unless it is one. """
    return value.factors if isinstance(value, Tensor) else (value, )


def common(*patterns: Pattern) -> type | None:
    """ The bound of the objects of patterns standing together, if all do. """
    bounds = [pattern.bound for pattern in patterns]
    return None if None in bounds else bounds[0]


@dataclass(frozen=True)
class Var[C0, C1: abc.Category](Pattern[C0, C1]):
    """ A variable of a given sort, or between the boundaries of a hom. """

    name: str
    sort: Sort | HomType

    def __post_init__(self):
        pass

    @property
    def variables(self):
        return (self.name, )

    @property
    def bound(self):
        return getattr(self.sort, "bound", None)

    def instantiate(self, subst, unit):
        return subst[self.name]

    def unify(self, value, subst, residuals):
        if self.name in subst:
            if subst[self.name] == value:
                yield subst, residuals
        elif not getattr(self.sort, "atomic", False) or len(value) == 1:
            yield dict(subst, **{self.name: value}), residuals

    def __str__(self):
        return self.name


@dataclass(frozen=True)
class Unit[C0, C1: abc.ColouredMonoid](Pattern[C0, C1]):
    """
    The unit of a monoid of objects, ``Unit[C0]`` in a quoted pattern.

    >>> Unit[Sort(bound=abc.ColouredMonoid)]
    Unit(sort=Sort(head='C0', atomic=False))
    """

    sort: Sort

    def __class_getitem__(cls, item):
        return cls(sort(item))

    variables = ()

    @property
    def bound(self):
        return self.sort.bound

    def instantiate(self, subst, unit):
        return unit()

    def unify(self, value, subst, residuals):
        if not len(value):
            yield subst, residuals

    def __str__(self):
        return f"Unit[{self.sort}]"


@dataclass(frozen=True)
class Tensor[C0, C1: abc.ColouredMonoid](Pattern[C0, C1]):
    """ The tensor of two or more patterns, flattened. """

    factors: tuple[Pattern, ...]

    @property
    def variables(self):
        return tuple(name for f in self.factors for name in f.variables)

    @property
    def bound(self):
        return common(*self.factors)

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
class Adjoint[C0, C1: abc.Pregroup, S: str](Pattern[C0, C1]):
    """
    The left or right adjoint ``X.l`` or ``X.r`` of a pattern, inverted by
    the adjoint on the other side when matching.
    """

    base: Pattern
    side: S

    INVERSE: ClassVar[dict] = {"l": "r", "r": "l"}

    @property
    def variables(self):
        return self.base.variables

    @property
    def bound(self):
        return self.base.bound

    def instantiate(self, subst, unit):
        return getattr(self.base.instantiate(subst, unit), self.side)

    def unify(self, value, subst, residuals):
        inverse = getattr(value, self.INVERSE[self.side])
        yield from self.base.unify(inverse, subst, residuals)

    def __str__(self):
        return f"{self.base}.{self.side}"


@dataclass(frozen=True)
class Delay[C0, C1: abc.DelayedMonoid](Pattern[C0, C1]):
    """ The delay ``M.d`` of a pattern by one time step. """

    base: Pattern

    @property
    def variables(self):
        return self.base.variables

    @property
    def bound(self):
        return self.base.bound

    def instantiate(self, subst, unit):
        return self.base.instantiate(subst, unit).d

    def __str__(self):
        return f"{self.base}.d"


@dataclass(frozen=True)
class Exp[C0, C1: abc.ResiduatedMonoid, S: str](Pattern[C0, C1]):
    """ An exponential ``X << Y`` or ``X >> Y`` of two patterns. """

    symbol: S
    left: Pattern
    right: Pattern

    OPERATORS: ClassVar[dict] = {"<<": operator.lshift, ">>": operator.rshift}

    @property
    def variables(self):
        return self.left.variables + self.right.variables

    @property
    def bound(self):
        return common(self.left, self.right)

    def instantiate(self, subst, unit):
        return self.OPERATORS[self.symbol](
            self.left.instantiate(subst, unit),
            self.right.instantiate(subst, unit))

    def __str__(self):
        return f"({self.left} {self.symbol} {self.right})"


@dataclass(frozen=True)
class Repeat[C0, C1: abc.ColouredMonoid](Pattern[C0, C1]):
    """
    An atomic pattern repeated a variable number of times, ``X ** N`` for
    the legs of a spider: matching binds the count to the number of atoms
    and the base to the one atom they all equal.
    """

    base: Pattern
    count: Var

    @property
    def variables(self):
        return self.base.variables + self.count.variables

    @property
    def bound(self):
        return self.base.bound

    def instantiate(self, subst, unit):
        return self.base.instantiate(subst, unit)\
            ** self.count.instantiate(subst, unit)

    def unify(self, value, subst, residuals):
        atoms = [value[i:i + 1] for i in range(len(value))]
        if any(atom != atoms[0] for atom in atoms[1:]):
            return
        for subst_, residuals_ in self.count.unify(
                len(atoms), subst, residuals):
            if atoms:
                yield from self.base.unify(atoms[0], subst_, residuals_)
            else:
                yield subst_, residuals_

    def __str__(self):
        return f"{self.base} ** {self.count}"


@dataclass(frozen=True)
class HomType[C0, C1: abc.Category, A: C0, B: C0](Pattern[C0, C1]):
    """
    The type ``head[dom, cod]`` of the morphisms between two patterns —
    what a ``Hom[C1, A, B]`` annotation evaluates to — matched against a
    goal: a pair of an optional domain and codomain.

    >>> from discopy.monoidal import Ty
    >>> A, B = (Var(n, Sort(bound=abc.ColouredMonoid)) for n in "AB")
    >>> hom = HomType(A @ B, A)
    >>> print(hom)
    C1[A @ B, A]
    >>> x, y = Ty('x'), Ty('y')
    >>> [(str(s['A']), str(s['B'])) for s, _ in hom.match((x @ y, x))]
    [('x', 'y')]
    >>> list(hom.match((x @ y, y)))
    []
    """

    dom: Pattern
    cod: Pattern
    head: str = "C1"

    def __post_init__(self):
        pass

    @property
    def variables(self):
        return self.dom.variables + self.cod.variables

    @property
    def bound(self):
        return common(self.dom, self.cod)

    def resolve(self, scope: dict) -> type:
        """ The type the head stands for, see :meth:`Sort.resolve`. """
        return Sort(self.head).resolve(scope)

    def instantiate(self, subst, unit) -> tuple:
        """ The domain and codomain under a substitution. """
        return (self.dom.instantiate(subst, unit),
                self.cod.instantiate(subst, unit))

    def unify(self, value, subst, residuals):
        dom, cod = value
        for subst_, residuals_ in self.dom.match(dom, subst, residuals):
            yield from self.cod.match(cod, subst_, residuals_)

    def __str__(self):
        return f"{self.head}[{self.dom}, {self.cod}]"


@dataclass(frozen=True)
class Sequent:
    """
    Variables and their sorts, named premises and an optional conclusion.
    A premise is a :class:`HomType` to generate, a :class:`Sort` to
    generate, or a :class:`Pattern` to instantiate.

    >>> from discopy.abc import MonoidalCategory
    >>> print(MonoidalCategory.tensor.sequent)
    ... # doctest: +NORMALIZE_WHITESPACE
    A: C0, B: C0, C: C0, D: C0
    | self: C1[A, B], other: C1[C, D] ⊢ C1[A @ C, B @ D]
    """

    variables: dict[str, Sort | HomType] = field(default_factory=dict)
    premises: dict[str, Pattern | Sort] = field(default_factory=dict)
    conclusion: HomType | None = None

    def __str__(self):
        context = ", ".join(f"{n}: {s}" for n, s in self.variables.items())
        premises = ", ".join(f"{n}: {p}" for n, p in self.premises.items())
        left = " | ".join(part for part in (context, premises) if part)
        right = "" if self.conclusion is None else f" ⊢ {self.conclusion}"
        return left + right


def premises_of(function: Callable, missing: bool = False) -> list[str]:
    """
    The names of the premises a function states: its parameters without a
    default, an unannotated first ``cls`` or ``self`` skipped — only the
    ones without an annotation when ``missing``.
    """
    signature = inspect.signature(function)
    parameters = list(signature.parameters.values())
    if parameters and parameters[0].annotation is inspect.Parameter.empty:
        parameters = parameters[1:]
    return [
        parameter.name for parameter in parameters
        if parameter.default is inspect.Parameter.empty
        and parameter.kind not in (
            inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        and (not missing
             or parameter.annotation is inspect.Parameter.empty)]


def sort_of(parameter: TypeVar, level: type | None) -> Sort | HomType:
    """
    The sort a type parameter declares: an object of ``C0`` when
    unbounded, an :class:`Atom` or a :class:`Count` when the bound says
    so, the :class:`HomType` between two sibling variables for a bound
    ``A: Hom[C1, X, Y]``, and a class of :mod:`discopy.abc` for a rule
    stated outside a class. The ``level`` is the bound of the objects of
    the class stating the declaration, carried by every object sort.
    """
    bound = parameter.__bound__
    if bound is None:
        return Sort("C0", bound=level)
    if isinstance(bound, type) and issubclass(bound, Atom):
        return Sort("C0", atomic=True, bound=level)
    if isinstance(bound, type) and issubclass(bound, Count):
        return Sort("Count")
    if isinstance(bound, Sort):
        return replace(bound, bound=bound.bound or level)
    origin = get_origin(bound)
    if isinstance(origin, TypeAliasType):
        substitution = dict(zip(origin.__type_params__, get_args(bound)))
        head, dom, cod = (substitution.get(item, item)
                          for item in get_args(origin.__value__))
        boundary = Sort("C0", bound=level)
        return HomType(
            Var(dom.__name__, boundary), Var(cod.__name__, boundary),
            getattr(head, "__name__", "C1"))
    if isinstance(bound, type) and issubclass(bound, abc.Category):
        return Sort(bound=bound)
    raise TypeError(
        f"{parameter} is bounded by {bound!r}, which is no sort.")


def read(annotation: str, sorts: dict[str, Sort | HomType],
         namespace: dict | None = None) -> Pattern | Sort:
    """
    Read a pattern or a sort from a deferred annotation, evaluated in the
    environment of the sequent over the namespace of the function: the
    metavariables are :class:`Var` s of the given sorts, ``C0``, ``C1``
    and ``Self`` sorts — the ``C0`` of the environment bounded as the
    variables of that sort are — ``Hom`` builds the :class:`HomType`
    between two patterns and ``Annotated`` reads its quoted metadata in
    the same environment.

    >>> sorts = {"X": Sort("C0", atomic=True, bound=abc.Pregroup)}
    >>> print(read('Annotated[C1, "X @ X.r", "Unit[C0]"]', sorts))
    C1[X @ X.r, Unit[C0]]
    >>> print(read('Hom[C1, X, X]', sorts))
    C1[X, X]
    >>> read('Atom[Self.dom.ob]', sorts)
    Sort(head='Self.dom.ob', atomic=True)
    >>> read("X * 2", sorts)
    Traceback (most recent call last):
     ...
    TypeError: Cannot read a pattern from X * 2.
    """
    level = next((
        sort.bound for sort in sorts.values()
        if getattr(sort, "head", None) == "C0"), None)
    environment = {
        "Atom": Atom, "Count": Count, "Unit": Unit, "Self": Sort("Self"),
        "C0": Sort("C0", bound=level), "C1": C1,
        **{name: Var(name, sort) for name, sort in sorts.items()}}

    def evaluate(item):
        if isinstance(item, str):
            item = eval(item, namespace or {}, environment)
        return item

    class AnnotatedForm:
        """ ``Annotated[...]`` in an annotation: quoted patterns. """
        def __class_getitem__(cls, item):
            base, *metadata = item if isinstance(item, tuple) else (item, )
            metadata = [evaluate(entry) for entry in metadata]
            if len(metadata) == 1:
                (value, ) = metadata
                return value if isinstance(value, Sort) else pattern(value)
            dom, cod = metadata
            base = evaluate(base)
            head = base.head if isinstance(base, Sort) else "C1"
            return HomType(pattern(dom), pattern(cod), head)

    class HomForm:
        """ ``Hom[C1, A, B]`` in an annotation: the hom type it aliases. """
        def __class_getitem__(cls, item):
            head, dom, cod = (evaluate(entry) for entry in item)
            return sort(head)[dom, cod]

    environment["Annotated"], environment["Hom"] = AnnotatedForm, HomForm
    try:
        value = evaluate(annotation)
        if not isinstance(value, (Sort, Pattern)):
            raise TypeError(f"Expected a pattern, got {value!r}.")
    except Exception as error:
        raise TypeError(
            f"Cannot read a pattern from {annotation}.") from error
    return value


def parse(function: Callable, owner: type | None = None,
          conclusion: bool = True) -> Sequent:
    """
    The sequent a function states with its signature, deferred with
    ``from __future__ import annotations``: each type parameter a
    variable of the sort its bound declares — carrying the bound of the
    objects of the ``owner`` class stating it — each parameter without a
    default a premise, the return annotation the conclusion when asked
    for. An unannotated first parameter, ``cls`` or ``self``, is skipped.

    >>> def then[A, B, C](
    ...         self: Hom[C1, A, B], other: Hom[C1, B, C]
    ... ) -> Hom[C1, A, C]:
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
    level = None
    if owner is not None:
        if getattr(owner, "__type_params__", ()):
            bound = owner.__type_params__[0].__bound__
            level = bound if isinstance(bound, type) else None
        else:
            level = getattr(owner, "ob", None)
            level = level if isinstance(level, type) else None
    sorts = {
        parameter.__name__: sort_of(parameter, level)
        for parameter in function.__type_params__}
    signature = inspect.signature(function)
    annotations = {
        name: parameter.annotation
        for name, parameter in signature.parameters.items()
        if parameter.annotation is not inspect.Parameter.empty}
    if signature.return_annotation is not inspect.Signature.empty:
        annotations["return"] = signature.return_annotation
    for name in premises_of(function, missing=True):
        raise TypeError(
            f"{function.__name__} states no pattern for {name}.")
    premises = premises_of(function)
    namespace = function.__globals__
    premises = {
        name: read(annotations[name], sorts, namespace)
        for name in premises}
    returns = read(annotations["return"], sorts, namespace)\
        if conclusion and "return" in annotations else None
    if conclusion and not isinstance(returns, HomType):
        raise TypeError(f"{function.__name__} concludes no hom type.")
    return Sequent(sorts, premises, returns)


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
        owner : The class declaring the sequent, whose objects bound the
            sorts of its variables; found when a class access binds it.

    >>> from discopy.abc import Category
    >>> Category.then
    abc.Category.then
    >>> print(Category.then.sequent)
    A: C0, B: C0, C: C0 | self: C1[A, B], other: C1[B, C] ⊢ C1[A, C]
    """

    function: Callable
    _: KW_ONLY
    category: type[T] | None = None
    name: str | None = None
    owner: type | None = None

    concludes: ClassVar[bool] = True
    """ Whether the return annotation is read as the conclusion. """

    def __post_init__(self):
        if isinstance(self.function, classmethod):
            raise TypeError(
                f"Decorate {self.function.__func__.__name__} inside "
                "classmethod, not outside.")
        self.name = self.name or self.function.__name__
        self.__doc__ = self.function.__doc__
        for name in premises_of(inspect.unwrap(self.function), missing=True):
            raise TypeError(f"{self.name} states no pattern for {name}.")

    @property
    def sequent(self) -> Sequent:
        """ The parsed signature, read lazily and cached, see :func:`parse`
        — lazily so that the sorts carry the bounds of the class stating
        the declaration, which does not exist when its body is decorated.
        """
        if "sequent" not in self.__dict__:
            self.__dict__["sequent"] = parse(
                self.function, self.owner or self.category,
                conclusion=self.concludes)
        return self.__dict__["sequent"]

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

    def bind(self, category: type[T],
             owner: type | None = None) -> Declaration[P, T]:
        """ Bind the declaration to a concrete category. """
        return replace(
            self, category=category, owner=self.owner or owner)

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
        object named after it — a count the number two — each premise a
        :func:`cell` named after its parameter, so that a declaration
        reads as a schema.

        >>> from discopy.abc import MonoidalCategory
        >>> from discopy.monoidal import Diagram
        >>> tensor = MonoidalCategory.tensor.bind(Diagram)
        >>> for name, box in tensor.canonical().items():
        ...     print(f"{name}: {box.dom} -> {box.cod}")
        self: A -> B
        other: C -> D
        """
        subst = {
            name: 2 if getattr(sort, "head", None) == "Count"
            else cell(sort.resolve(self.scope), name)
            for name, sort in self.sequent.variables.items()
            if not isinstance(sort, HomType)}
        for name, sort in self.sequent.variables.items():
            if isinstance(sort, HomType):
                dom, cod = sort.instantiate(subst, self.unit)
                subst[name] = cell(sort.resolve(self.scope), name, dom, cod)
        args = {}
        for name, premise in self.sequent.premises.items():
            if isinstance(premise, HomType):
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
        needs it — one bounded by a hom through ``hom`` itself — except
        one standing alone on a side of a hom, which is read off the term
        the search finds so that the goal guides the search. The residuals
        of a match are checked once every variable is bound, rejecting the
        example otherwise.

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

        def side(pattern):
            if isinstance(pattern, Var) and pattern.name not in subst:
                return None
            bound(*pattern.variables)
            return pattern.instantiate(subst, self.unit)

        def read_off(pattern, value):
            if isinstance(pattern, Var) and pattern.name not in subst:
                assume(not getattr(pattern.sort, "atomic", False)
                       or len(value) == 1)
                subst[pattern.name] = value

        def bound(*names):
            for name in names:
                if name in subst:
                    continue
                sort = sorts[name]
                if isinstance(sort, HomType):
                    dom, cod = side(sort.dom), side(sort.cod)
                    term = draw(
                        hom(sort.resolve(self.scope), dom, cod), label=name)
                    read_off(sort.dom, term.dom)
                    read_off(sort.cod, term.cod)
                    subst[name] = term
                else:
                    strategy = sort.strategy(self.scope, types)
                    subst[name] = draw(strategy, label=name)

        args = {}
        for name, premise in self.sequent.premises.items():
            if isinstance(premise, HomType):
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
    class with a ``Box``, between ``dom`` and ``cod`` or objects named
    ``x`` and ``y``, else an instance of the class of that name.

    >>> from discopy.monoidal import Box, Diagram, Ty
    >>> assert cell(Diagram, 'f') == Box('f', Ty('x'), Ty('y'))
    >>> assert cell(Ty, 'A') == Ty('A')
    """
    box = getattr(factory, "Box", None)
    if box is not None and isinstance(box, type):
        dom = factory.ob("x") if dom is None else dom
        cod = factory.ob("y") if cod is None else cod
        return box(name, dom, cod)
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
            if getattr(value, "__inapplicable__", None) is not None:
                result.pop(name, None)
            elif type(value) is kind:
                result[name] = value.bind(cls, owner=base)
            elif name in result and not shadowed:
                del result[name]
    return result
