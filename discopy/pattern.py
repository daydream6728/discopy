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
                self: Annotated[C1, Hom[A, B]],
                other: Annotated[C1, Hom[C, D]]
        ) -> Annotated[C1, Hom[Tensor[A, C], Tensor[B, D]]]:
            ...

The signature typechecks as it reads and evaluates to the sequent it
states. Every annotation is an ``Annotated[T, pat]``: the coarse type
``T`` a typechecker reads and the one pattern ``pat`` the interpreter
builds. A metavariable is one of the method's own :pep:`695` type
parameters, its sort the bound — an object of ``C0`` when unbounded, an
:class:`Atom` or a :class:`Count` when declared — and a compound
pattern is a pattern class subscripted with the type parameters:
``Hom[A, B]`` is the :class:`Hom` between two boundaries, its level
the base of the ``Annotated`` carrying it, ``Tensor[X, R[X]]``
is the :class:`Tensor` of a variable with its right :class:`Adjoint`,
``Delay[M]`` a :class:`Delay`, ``Over[Z, Y]`` and ``Under[Y, Z]`` the
:class:`Exp` s, ``Repeat[X, N]`` a :class:`Repeat` and ``Unit[C0]`` the
:class:`Unit`. The module stating a declaration does *not* quote its
annotations, so each one is an object the interpreter builds when it is
read, lazily by :pep:`649` — the subscript of a pattern class *is* the
pattern — and :func:`parse` collects the sequent from
``__annotations__``, ``__type_params__``, ``__bound__`` and
``__metadata__`` without evaluating anything itself.

Each pattern class declares its :meth:`Pattern.level`, the least
structure the objects it stands in must have: a :class:`Tensor` needs a
:class:`abc.ColouredMonoid`, an :class:`Adjoint` a :class:`abc.Pregroup`,
a :class:`Delay` a :class:`abc.DelayedMonoid`. A variable's sort carries
the bound of the objects of the class stating the rule, ``C0: Pregroup``,
and a pattern refuses one bounded below what its shape needs — at
construction when the bound is known, at :func:`parse` with the class
stating the declaration otherwise. The levels are the classes of
:mod:`discopy.abc`, read lazily, so that this module imports it while it
imports this one.

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
    L
    R
    Delay
    Exp
    Over
    Under
    Repeat
    Hom
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
        interpret
        cell
        declarations
"""

import __future__
import inspect
import operator
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator
from dataclasses import KW_ONLY, dataclass, field, replace
from functools import reduce
from typing import Annotated, ClassVar, Self, TypeVar, get_origin

from discopy import abc
from discopy.utils import factory_name


type Substitution = dict[str, object]
type Residuals = tuple[tuple[Pattern, object], ...]
type Match = tuple[Substitution, Residuals]


@dataclass(frozen=True)
class Sort:
    """
    The sort of an object variable: the instances of the type its ``head``
    resolves to in the scope of a bound declaration, atomic or not, and
    the class of :mod:`discopy.abc` bounding them when known.

    >>> print(Sort("C0", atomic=True))
    Atom[C0]
    """

    head: str = "C0"
    atomic: bool = False
    bound: type | None = field(default=None, compare=False, repr=False)

    def resolve(self, scope: dict) -> type:
        """ The type the head stands for in the scope. """
        return scope[self.head]

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
    ``X`` an object with exactly one generator, and ``Atom[C0]`` in the
    metadata of an annotation stands for the same sort.

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


def operand(value) -> Pattern:
    """
    A pattern as the subscript of a pattern class: itself, or a type
    parameter as the variable of the sort its bound declares, so that
    ``Tensor[X, R[X]]`` in an annotation builds the pattern it reads as.
    """
    if isinstance(value, TypeVar):
        return Var.of(value)
    return pattern(value)


class Pattern[C0, C1: abc.Category](ABC):
    """
    A pattern for the objects of a category, with variables to instantiate,
    generic in the colours ``C0`` and objects ``C1`` of the monoid it
    stands in: the bound of ``C1`` is the :meth:`level` the pattern needs.

    Matching a value yields every substitution unifying the pattern with it,
    each with the residual equations it could not invert.

    A subclass named in annotations — :class:`Hom`, :class:`Unit`,
    :class:`Tensor`,
    :class:`Delay`, :class:`Repeat` and the fronts :class:`L`, :class:`R`,
    :class:`Over` and :class:`Under` — is instead generic in what its
    subscript takes, since a typechecker reads the subscript ``Tensor[A,
    C]`` as a specialisation: its type parameters are the operands the
    interpreter takes, and the level is its :meth:`level` classmethod
    where this class reads the bound of ``C1``.
    """
    def __post_init__(self):
        """
        Check the objects the pattern stands for are bounded by its
        :meth:`level` — when a bound is known: a pattern built from bare
        type parameters knows none until :func:`parse` reads it with the
        class stating it, which checks then; a variable or a hom adds no
        structure to its parts, which its level being a bare
        :class:`discopy.abc.Category` says.
        """
        bound, required = self.bound, self.level()
        if required is abc.Category:
            return
        if bound is not None and not issubclass(bound, required):
            raise TypeError(
                f"{self} needs a {required.__name__}, its objects "
                f"are bounded by {bound.__name__}.")

    @classmethod
    def level(cls) -> type[abc.Category]:
        """ The bound of ``C1``, the least structure the pattern needs. """
        return cls.__type_params__[  # ty: ignore[invalid-return-type]
            1].__bound__

    @property
    def parts(self) -> tuple[Pattern, ...]:
        """ The immediate sub-patterns, the fields holding one. """
        values = (
            getattr(self, name)
            for name in getattr(self, "__dataclass_fields__", ()))
        return tuple(
            part for value in values
            for part in (value if isinstance(value, tuple) else (value, ))
            if isinstance(part, Pattern))

    def walk(self) -> Iterator[Pattern]:
        """ The pattern and every sub-pattern below it. """
        yield self
        for part in self.parts:
            yield from part.walk()

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
        >>> for subst, _ in Tensor[A, B].match(x @ y):
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


C0, C1 = Sort("C0"), Sort("C1")
"""
The objects and the arrows of the category a declaration is bound to:
what the annotations of a module-level declaration name in their
metadata, where a method names the type parameters of its class. For a
functor category the objects are categories and the arrows functors.
"""

In0, In1, Out0, Out1 = (
    Sort("In0"), Sort("In1"), Sort("Out0"), Sort("Out1"))
"""
The objects and the arrows of the categories a functor maps from and
to, read off the ``dom`` and ``cod`` of the class a declaration is
bound to: the sorts of the two overloads of
:meth:`discopy.cat.Functor.__call__`, ``In0 -> Out0`` on objects and
``In1 -> Out1`` on arrows.
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
    sort: Sort | Hom

    @classmethod
    def of(cls, parameter: TypeVar) -> Var:
        """
        The variable a type parameter declares, of the sort its bound
        states, see :func:`sort_of`; the bound of the objects is attached
        when :func:`parse` reads the class stating the declaration.
        """
        return cls(parameter.__name__, sort_of(parameter, None))

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
class Unit[C0](Pattern):
    """
    The unit of a monoid of objects, ``Unit[C0]`` in an annotation.

    >>> Unit[Sort(bound=abc.ColouredMonoid)]
    Unit(sort=Sort(head='C0', atomic=False))
    """

    sort: Sort

    def __class_getitem__(cls, item):
        return cls(sort(item))

    @classmethod
    def level(cls) -> type[abc.Category]:
        return abc.ColouredMonoid

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
class Tensor[*Fs](Pattern):
    """
    The tensor of two or more patterns, flattened: ``Tensor[A, C]`` in an
    annotation.
    """

    factors: tuple[Pattern, ...]

    @classmethod
    def level(cls) -> type[abc.Category]:
        return abc.ColouredMonoid

    def __class_getitem__(cls, items):
        if not isinstance(items, tuple) or len(items) < 2:
            raise TypeError(f"A tensor takes two or more factors: {items!r}.")
        return cls(tuple(
            factor for item in items for factor in factors(operand(item))))

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
    The left or right adjoint ``X.l`` or ``X.r`` of a pattern — ``L[X]``
    or ``R[X]`` in an annotation — inverted by the adjoint on the other
    side when matching.
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
        base = f"({self.base})"\
            if isinstance(self.base, (Tensor, Repeat)) else str(self.base)
        return f"{base}.{self.side}"


class L[X]:
    """ The left :class:`Adjoint` of a pattern, ``L[X]`` for ``x.l``. """
    def __class_getitem__(cls, item) -> Adjoint:
        return Adjoint(operand(item), "l")


class R[X]:
    """ The right :class:`Adjoint` of a pattern, ``R[X]`` for ``x.r``. """
    def __class_getitem__(cls, item) -> Adjoint:
        return Adjoint(operand(item), "r")


@dataclass(frozen=True)
class Delay[M](Pattern):
    """
    The delay ``M.d`` of a pattern by one time step, ``Delay[M]`` in an
    annotation.
    """

    base: Pattern

    @classmethod
    def level(cls) -> type[abc.Category]:
        return abc.DelayedMonoid

    def __class_getitem__(cls, item):
        return cls(operand(item))

    @property
    def variables(self):
        return self.base.variables

    @property
    def bound(self):
        return self.base.bound

    def instantiate(self, subst, unit):
        return self.base.instantiate(subst, unit).d

    def __str__(self):
        base = f"({self.base})"\
            if isinstance(self.base, (Tensor, Repeat)) else str(self.base)
        return f"{base}.d"


@dataclass(frozen=True)
class Exp[C0, C1: abc.ResiduatedMonoid, S: str](Pattern[C0, C1]):
    """
    An exponential ``X << Y`` or ``X >> Y`` of two patterns —
    ``Over[X, Y]`` or ``Under[X, Y]`` in an annotation.
    """

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


class Over[X, Y]:
    """ The :class:`Exp` ``x << y``, ``Over[X, Y]`` in an annotation. """
    def __class_getitem__(cls, item) -> Exp:
        base, exponent = item
        return Exp("<<", operand(base), operand(exponent))


class Under[X, Y]:
    """ The :class:`Exp` ``x >> y``, ``Under[X, Y]`` in an annotation. """
    def __class_getitem__(cls, item) -> Exp:
        exponent, base = item
        return Exp(">>", operand(exponent), operand(base))


@dataclass(frozen=True)
class Repeat[X, N](Pattern):
    """
    An atomic pattern repeated a variable number of times,
    ``Repeat[X, N]`` in an annotation, for the legs of a spider:
    matching binds the count to the number of atoms and the base to the
    one atom they all equal.
    """

    base: Pattern
    count: Var

    @classmethod
    def level(cls) -> type[abc.Category]:
        return abc.ColouredMonoid

    def __class_getitem__(cls, item):
        base, count = item
        base, count = operand(base), operand(count)
        if not isinstance(count, Var):
            raise TypeError(f"Expected a Count variable, got {count!r}.")
        if not getattr(getattr(base, "sort", None), "atomic", False):
            raise TypeError(
                f"Repeat takes an atomic base, e.g. `X: Atom`, got {base!r}: "
                "matching cannot read a repeated compound back.")
        return cls(base, count)

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
class Hom[A, B](Pattern):
    """
    The type ``head[dom, cod]`` of the morphisms between two patterns,
    ``Hom[A, B]`` in an annotation, its level the base of the
    ``Annotated`` carrying it — matched against a goal: a pair of an
    optional domain and codomain.

    >>> from discopy.monoidal import Ty
    >>> A, B = (Var(n, Sort(bound=abc.ColouredMonoid)) for n in "AB")
    >>> hom = Hom(Tensor[A, B], A)
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

    def __class_getitem__(cls, item):
        dom, cod = item
        return cls(operand(dom), operand(cod))

    @classmethod
    def level(cls) -> type[abc.Category]:
        return abc.Category

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
class Sequent[C0, C1: abc.Category]:
    """
    Variables and their sorts, named premises and an optional conclusion.
    A premise is a :class:`Hom` to generate, a :class:`Sort` to
    generate, or a :class:`Pattern` to instantiate.

    >>> from discopy.abc import MonoidalCategory
    >>> print(MonoidalCategory.tensor.sequent)
    ... # doctest: +NORMALIZE_WHITESPACE
    A: C0, B: C0, C: C0, D: C0
    | self: C1[A, B], other: C1[C, D] ⊢ C1[A @ C, B @ D]
    """

    variables: dict[str, Sort | Hom[C0, C1]] = field(default_factory=dict)
    premises: dict[str, Pattern[C0, C1] | Sort] = field(default_factory=dict)
    conclusion: Hom[C0, C1] | None = None

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
    parameters = list(inspect.signature(function).parameters.values())
    if parameters and parameters[0].annotation is inspect.Parameter.empty:
        parameters = parameters[1:]
    return [
        parameter.name for parameter in parameters
        if parameter.default is inspect.Parameter.empty
        and parameter.kind not in (
            inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        and (not missing
             or parameter.annotation is inspect.Parameter.empty)]


def sort_of(parameter: TypeVar, level: type | None) -> Sort | Hom:
    """
    The sort a type parameter declares: an object of ``C0`` when
    unbounded, an :class:`Atom` or a :class:`Count` when the bound says
    so, the :class:`Hom` between two sibling variables for a bound
    ``A: Annotated[C1, Hom[X, Y]]``, and a class of :mod:`discopy.abc`
    for a rule
    stated outside a class. The ``level`` is the bound of the objects of
    the class stating the declaration, carried by every object sort.
    """
    try:
        bound = parameter.__bound__
    except RecursionError as error:
        raise TypeError(f"{parameter} bounds itself.") from error
    if bound is None:
        return Sort("C0", bound=level)
    if isinstance(bound, type) and issubclass(bound, Atom):
        return Sort("C0", atomic=True, bound=level)
    if isinstance(bound, type) and issubclass(bound, Count):
        return Sort("Count")
    if isinstance(bound, Sort):
        return replace(bound, bound=bound.bound or level)
    if get_origin(bound) is Annotated:
        (value, ) = bound.__metadata__
        if not isinstance(value, Hom):
            raise TypeError(
                f"{parameter} is bounded by {bound!r}, "
                "which carries no hom pattern.")
        boundary = Sort("C0", bound=level)
        dom, cod = (
            Var(part.name, boundary) if isinstance(part, Var) else part
            for part in (value.dom, value.cod))
        return Hom(dom, cod, head_of(bound.__origin__))
    if isinstance(bound, type) and issubclass(bound, abc.Category):
        return Sort(bound=bound)
    raise TypeError(
        f"{parameter} is bounded by {bound!r}, which is no sort.")


def head_of(base) -> str:
    """ The head a hom annotation names with its base, ``C1`` by default. """
    if isinstance(base, TypeVar):
        return base.__name__
    if isinstance(base, Sort):
        return base.head
    return "C1"


def interpret(annotation, sorts: dict[str, Sort | Hom]) -> Pattern | Sort:
    """
    The pattern or sort an annotation object carries, collected shallowly
    — nothing is evaluated, the interpreter built every part when the
    declaration was defined: a type parameter is the :class:`Var` of its
    sort, ``Self`` the sort of the terms, a pattern or a sort stands as
    itself, and an ``Annotated`` carries exactly one pattern, a
    :class:`Hom` taking its head from the base.

    >>> def cups[X: Atom](
    ...         cls, left: Annotated[C0, X], right: Annotated[C0, R[X]]
    ... ) -> Annotated[C1, Hom[Tensor[X, R[X]], Unit[C0]]]:
    ...     ...
    >>> sorts = {"X": Sort("C0", atomic=True, bound=abc.Pregroup)}
    >>> print(interpret(cups.__annotations__["return"], sorts))
    C1[X @ X.r, Unit[C0]]
    >>> interpret("X @ X.r", sorts)  # doctest: +ELLIPSIS
    Traceback (most recent call last):
     ...
    TypeError: A declaration is stated eagerly, ...
    """
    if isinstance(annotation, str):
        raise TypeError(
            "A declaration is stated eagerly, without `from __future__ "
            f"import annotations`, got the string {annotation!r}.")
    if annotation is Self:
        return Sort("Self")
    if isinstance(annotation, TypeVar):
        name = annotation.__name__
        if name in sorts:
            return Var(name, sorts[name])
        if name in ("Self", "C0", "C1"):
            return Sort(name)
        raise TypeError(
            f"{name} is not a type parameter of the declaration nor a "
            "sort in scope.")
    if isinstance(annotation, (Pattern, Sort)):
        return annotation
    if get_origin(annotation) is Annotated:
        try:
            (entry, ) = annotation.__metadata__
        except ValueError:
            raise TypeError(
                "An annotation carries exactly one pattern, got "
                f"{annotation!r}.") from None
        value = interpret(entry, sorts)
        if isinstance(value, Hom) and isinstance(
                annotation.__origin__, (TypeVar, Sort)):
            value = replace(value, head=head_of(annotation.__origin__))
        return value if isinstance(value, Sort) else pattern(value)
    raise TypeError(f"Cannot read a pattern from {annotation!r}.")


def parse(function: Callable, owner: type | None = None,
          conclusion: bool = True) -> Sequent:
    """
    The sequent a function states with its signature, collected from the
    annotation objects the interpreter built when it was defined: each
    type parameter a variable of the sort its bound declares — carrying
    the bound of the objects of the ``owner`` class stating it — each
    parameter without a default a premise, the return annotation the
    conclusion when asked for. An unannotated first parameter, ``cls``
    or ``self``, is skipped, and a pattern needing more structure than
    the owner's objects have is refused.

    >>> def then[A, B, C](
    ...         self: Annotated[C1, Hom[A, B]],
    ...         other: Annotated[C1, Hom[B, C]]
    ... ) -> Annotated[C1, Hom[A, C]]:
    ...     ...
    >>> print(parse(then))
    A: C0, B: C0, C: C0 | self: C1[A, B], other: C1[B, C] ⊢ C1[A, C]
    >>> print(parse(then, conclusion=False))
    A: C0, B: C0, C: C0 | self: C1[A, B], other: C1[B, C]
    """
    function = inspect.unwrap(function)
    if function.__code__.co_flags & __future__.annotations.compiler_flag:
        raise TypeError(
            f"{function.__module__} defers its annotations with `from "
            f"__future__ import annotations`, so {function.__name__} "
            "states strings where patterns are read.")
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

    def checked(value):
        if isinstance(value, Pattern) and level is not None:
            for node in value.walk():
                if isinstance(node, (Var, Hom)):
                    continue
                required = type(node).level()
                if not issubclass(level, required):
                    raise TypeError(
                        f"{node} needs a {required.__name__}, the objects "
                        f"of {function.__name__} are bounded by "
                        f"{level.__name__}.")
        return value

    for sort in sorts.values():
        if isinstance(sort, Hom):
            checked(sort)
    premises = {
        name: checked(interpret(annotations[name], sorts))
        for name in premises_of(function)}
    returns = checked(interpret(annotations["return"], sorts))\
        if conclusion and "return" in annotations else None
    if conclusion and not isinstance(returns, Hom):
        raise TypeError(f"{function.__name__} concludes no hom type.")
    if isinstance(returns, Hom):
        stated = {
            name for premise in premises.values()
            for name in getattr(premise, "variables", ())}
        stated |= {
            name for variable in stated
            for name in getattr(sorts.get(variable), "variables", ())}
        missing = set(returns.variables) - stated
        if missing:
            raise TypeError(
                f"{function.__name__} concludes on "
                f"{', '.join(sorted(missing))} that no premise states, "
                "e.g. a parameter whose default drops it.")
    return Sequent(
        sorts, premises, returns if isinstance(returns, Hom) else None)


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

    @property
    def __signature__(self):
        """ The signature of the function, so that a declaration
        introspects as the method it decorates. """
        return inspect.signature(self.function)

    def __repr__(self):
        if self.category is None:
            return f"{type(self).__name__}({self.name})"
        return f"{factory_name(self.category)}.{self.name}"

    def __str__(self):
        return f"{self.name}: {self.sequent}"

    def __hash__(self):
        return hash((self.function, self.category, self.name))

    def bind(self, category: type,
             owner: type | None = None) -> Self:
        """ Bind the declaration to a concrete category. """
        return replace(
            self, category=category, owner=self.owner or owner)

    @property
    def scope(self) -> dict:
        """
        What the heads of the sorts and homs stand for: the category for
        ``Self``, its objects and arrows for ``C0`` and ``C1``. A monoid,
        having no objects of its own, stands for both; a functor class,
        whose ``dom`` and ``cod`` are categories, also gives their
        objects and arrows as ``In0``, ``In1``, ``Out0`` and ``Out1``.
        """
        if self.category is None:
            raise TypeError(f"{self.name} is not bound to a class.")
        scope = {
            "Self": self.category,
            "C0": getattr(self.category, "ob", self.category),
            "C1": getattr(self.category, "ar", self.category)}
        dom, cod = (getattr(self.category, name, None)
                    for name in ("dom", "cod"))
        if isinstance(dom, type) and isinstance(cod, type):
            scope.update({
                "In0": getattr(dom, "ob", dom), "In1": dom,
                "Out0": getattr(cod, "ob", cod), "Out1": cod})
        return scope

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
            if not isinstance(sort, Hom)}
        for name, sort in self.sequent.variables.items():
            if isinstance(sort, Hom):
                dom, cod = sort.instantiate(subst, self.unit)
                subst[name] = cell(sort.resolve(self.scope), name, dom, cod)
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

        def draw_variable(name):
            sort = sorts[name]
            if not isinstance(sort, Hom):
                return draw(sort.strategy(self.scope, types), label=name)
            dom, cod = side(sort.dom), side(sort.cod)
            term = draw(
                hom(sort.resolve(self.scope), dom, cod), label=name)
            read_off(sort.dom, term.dom)
            read_off(sort.cod, term.cod)
            return term

        def bound(*names):
            for name in names:
                if name not in subst:
                    subst[name] = draw_variable(name)

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
                    and premise.resolve(self.scope) is self.scope["C1"]\
                    and issubclass(self.scope["C1"], abc.Category):
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


def concluding(function: Callable) -> bool:
    """
    Whether a function states a conclusion: a return annotation carrying
    a :class:`Hom` pattern. A rule without one implements the
    declaration it overrides, keeping its sequent.
    """
    returns = getattr(function, "__annotations__", {}).get("return")
    return any(
        isinstance(pattern, Hom)
        for pattern in getattr(returns, "__metadata__", ()))


def declarations[D: Declaration](cls: type, kind: type[D]) -> dict[str, D]:
    """
    The declarations of exactly a kind inherited by a class, bound to it
    and keyed by name, subclasses overriding bases — found under any
    inner decorator: a classmethod, a staticmethod or an abstract
    method. A declaration whose signature states no conclusion
    implements the one it overrides, keeping its sequent, and anything
    that is not a declaration assigned over an inherited one drops it,
    an implementation below the drop staying dropped.

    >>> from discopy.monoidal import Diagram
    >>> from discopy.search import Rule
    >>> list(declarations(Diagram, Rule))
    ['id', 'then', 'tensor']
    """
    result: dict[str, D] = {}
    dropped: set[str] = set()
    for base in reversed(cls.__mro__):
        for name, value in base.__dict__.items():
            while isinstance(value, (classmethod, staticmethod)):
                value = value.__func__
            if getattr(value, "__inapplicable__", None) is not None:
                result.pop(name, None)
                dropped.add(name)
            elif type(value) is not kind:
                if result.pop(name, None) is not None:
                    dropped.add(name)
            elif not kind.concludes or concluding(value.function):
                result[name] = value.bind(cls, owner=base)
                dropped.discard(name)
    return result
