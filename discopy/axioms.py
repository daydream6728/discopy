"""
Property-based testing of the axioms with `Hypothesis
<https://hypothesis.readthedocs.io>`_.

An :class:`Axiom` is an equation stated once on an abstract base class of
:mod:`discopy.abc` and inherited by every category below it, its signature a
sequent: its type parameters are variables, e.g. objects ``A: Obj[C0]``, its
parameters premises, e.g. a morphism ``f: Hom[C1, A, B]`` from ``A`` to
``B``, and its return annotation the type of its output, e.g. an equation
``Equation[Hom[C1, A, B]]``, which every value can be checked against, see
:func:`inhabits`. A :class:`Rule` is stated the same way, an operation of
the structure with a morphism as conclusion:
the terms of a free category are those its rules derive from boxes, see
:meth:`discopy.cat.Arrow.search`, and from symmetric categories on also
those of the combinatorial representation their equations compare by, see
:meth:`discopy.symmetric.Diagram.strategy`. Every strategy of a free category
honours any boundary it is asked for.

A law a category breaks is declared :meth:`Axiom.failing` where it breaks,
one that does not apply :meth:`Axiom.inapplicable`, and one that holds up to
a quotient or on a subspace :meth:`Axiom.modulo` and :meth:`Axiom.weaken`.
A :class:`Testable` category generates its own terms and
:meth:`Testable.matrix` lists every law of every such category, which the
suite in ``proptest/`` checks; CONTRIBUTING.md says how to run it. A
:class:`Serialisable` type states the laws of writing a term down and
reading it back.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Equation
    Declaration
    Axiom
    Rule
    AxiomFailure
    Count
    Tensor
    Unit
    L
    R
    Delay
    Over
    Under
    Repeat
    Testable
    Serialisable

.. admonition:: Functions

    .. autosummary::
        :template: function.rst
        :nosignatures:
        :toctree:

        axiom
        rule
        inhabits
"""

from __future__ import annotations

import __future__
import ast
import inspect
import pickle
import sys
from abc import ABC
from collections.abc import Callable
from copy import deepcopy
from dataclasses import KW_ONLY, dataclass, replace
from functools import cached_property, reduce, wraps
from operator import matmul
from typing import (
    TYPE_CHECKING, Annotated, Self, get_args, get_origin)

from discopy.utils import (
    AxiomError,
    classproperty,
    dumps,
    factory_name,
    from_tree,
    loads,
)

if TYPE_CHECKING:
    from hypothesis import strategies as st


GENERATORS = tuple("abcde")
"""
The names the generators of a free category are drawn from.

They are finitely many and shared, so a generated functor can name every one
of them: composing two functors keeps only the keys of the left-hand map, so
a functor that named just a few would compose to one defined nowhere else.
"""

MAX_COUNT = 3
""" The largest number a declaration quantifying over ``int`` is given. """

FUEL = 3
""" How deep the rules nest in a term of a free category, by default. """


class Equation[T]:
    """
    An equation is a list of ``terms`` to be compared up to a function
    ``up_to``, the identity by default.  Casting it to ``bool`` checks
    whether its terms are all equal up to that function.

    Parameters:
        terms : The terms of the equation.
        symbol : The symbol between each pair of terms, ``"="`` by default.
        symbols : The symbols between each pair of consecutive terms, one
            fewer than the terms, overriding ``symbol``.
        up_to : The function up to which ``bool(equation)`` compares its
            terms, overriding the subclass' :attr:`up_to` if given.

    Example
    -------
    The number of boxes inside an arrow is left unchanged by associativity,
    so we can compare arrows up to the function that counts them modulo 2:

    >>> from discopy.cat import Ob, Box, Equation
    >>> x = Ob('x')
    >>> f, g = Box('f', x, x), Box('g', x, x)
    >>> parity = lambda term: len(term.inside) % 2
    >>> assert not Equation(f, f >> g >> g)
    >>> assert Equation(f, f >> g >> g, up_to=parity)
    """
    up_to = None

    def __init__(self, *terms, symbol="=", symbols=None, up_to=None):
        self.terms = terms
        gaps = max(len(terms) - 1, 0)
        self.symbols = gaps * (symbol, ) if symbols is None\
            else tuple(symbols)
        if len(self.symbols) != gaps:
            raise ValueError(
                f"Expected {gaps} symbols between {len(terms)} terms, "
                f"got {len(self.symbols)}.")
        if up_to is not None:
            self.up_to = up_to

    def modulo(self, up_to: Callable) -> Equation:
        """
        The same equation compared up to the given function, rebinding
        :attr:`up_to`, whose name the attribute already takes.

        >>> from discopy.cat import Ob, Box, Equation
        >>> x = Ob('x')
        >>> f, g = Box('f', x, x), Box('g', x, x)
        >>> assert Equation(f >> g, g >> f).modulo(lambda _: True)
        """
        return type(self)(*self.terms, symbols=self.symbols, up_to=up_to)

    def checked(self) -> Equation:
        """
        The same equation with ``≠`` between two consecutive terms that
        differ up to :attr:`up_to`, i.e. the inequation it is when it fails.

        >>> from discopy.cat import Ob, Box, Equation
        >>> x = Ob('x')
        >>> f, g = Box('f', x, x), Box('g', x, x)
        >>> Equation(f, f, g).checked().symbols
        ('=', '$\\\\neq$')
        """
        symbols = (
            symbol if type(self)(left, right, up_to=self.up_to)
            else "$\\neq$" for symbol, left, right
            in zip(self.symbols, self.terms, self.terms[1:]))
        return type(self)(*self.terms, symbols=symbols, up_to=self.up_to)

    def __repr__(self):
        """
        >>> from discopy.cat import Ob, Box, Equation
        >>> Equation(Box('f', Ob('x'), Ob('x')))
        cat.Equation(cat.Box('f', cat.Ob('x'), cat.Ob('x')))
        """
        return factory_name(type(self))\
            + f"({', '.join(map(repr, self.terms))})"

    def __str__(self):
        return f"Equation({', '.join(map(str, self.terms))})"

    def __bool__(self):
        terms = self.terms if self.up_to is None\
            else list(map(self.up_to, self.terms))
        return all(term == terms[0] for term in terms)


class AxiomFailure(AxiomError):
    """
    A law declared broken, raised when the bound axiom is called: the
    reason is the message and :attr:`equation` is the law evaluated on the
    arguments, whose sides say how it failed.
    """

    def __init__(self, reason: str, equation):
        super().__init__(reason, equation)
        self.equation = equation


type Obj[Coarse] = Annotated[Coarse, "object"]
"""
The sort of the objects of type ``Coarse``, as the bound of a variable
``A: Obj[C0]`` of a declaration. A typechecker reads it as ``Coarse``.
"""

type Atom[Coarse] = Annotated[Coarse, "atom"]
""" The sort of the atomic objects, i.e. a single wire, ``X: Atom[C0]``. """

type Var[Coarse, Value] = Annotated[Coarse, Value]
"""
The premise standing for the value of an expression over the variables of a
declaration, e.g. ``x: Var[C0, X]`` for ``X: Obj[C0]``, ``mem: Var[C0,
Tensor[M, X]]`` or ``n: Var[int, N]`` for ``N: Count``. A typechecker reads
it as ``Coarse``.
"""

type Hom[Coarse, Dom, Cod] = Annotated[Coarse, Dom, Cod]
"""
The morphisms of type ``Coarse`` from ``Dom`` to ``Cod``, as a premise to
draw, e.g. ``f: Hom[C1, A, B]``, or the conclusion of a rule. A typechecker
reads it as ``Coarse``.
"""


class Count(int):
    """
    The sort of the numbers up to :data:`MAX_COUNT`, as the bound of a
    variable ``N: Count`` of a declaration, e.g. the legs of a spider.
    """


class Tensor[*Objects]:
    """
    The tensor of objects in a signature: ``Tensor[A, B]`` is a type for a
    typechecker and the object ``A @ B`` once the variables are drawn.

    >>> from discopy.monoidal import Ty
    >>> assert Tensor[Ty('x'), Ty('y')] == Ty('x', 'y')
    """
    def __class_getitem__(cls, objects):
        objects = objects if isinstance(objects, tuple) else (objects, )
        return reduce(matmul, objects)


class Unit[Coarse]:
    """
    The unit of a monoid of objects in a signature: ``Unit[C0]`` is the
    object ``C0()``.

    >>> from discopy.monoidal import Ty
    >>> assert Unit[Ty] == Ty()
    """
    def __class_getitem__(cls, ob):
        return ob()


class L[Object]:
    """ The left adjoint of an object in a signature, ``x.l``. """
    def __class_getitem__(cls, obj):
        return obj.l


class R[Object]:
    """ The right adjoint of an object in a signature, ``x.r``. """
    def __class_getitem__(cls, obj):
        return obj.r


class Delay[Object]:
    """
    The delay of an object by one time step in a signature, ``M.delay()``.

    >>> from discopy.feedback import Ty
    >>> assert Delay[Ty('x')] == Ty('x').delay()
    """
    def __class_getitem__(cls, obj):
        return obj.delay()


class Over[Base, Exponent]:
    """ The exponential on the left in a signature, ``base << exponent``. """
    def __class_getitem__(cls, sides):
        base, exponent = sides
        return base << exponent


class Under[Exponent, Base]:
    """ The exponential on the right in a signature, ``exponent >> base``. """
    def __class_getitem__(cls, sides):
        exponent, base = sides
        return exponent >> base


class Repeat[Object, N]:
    """
    An object repeated a number of times in a signature, ``x ** n``.

    >>> from discopy.monoidal import Ty
    >>> assert Repeat[Ty('x'), 2] == Ty('x', 'x')
    """
    def __class_getitem__(cls, args):
        obj, n = args
        return obj ** n


def inhabits(value, kind) -> bool:
    """
    Whether a value has an evaluated type of a sequent: a morphism of
    ``Hom[C, dom, cod]`` has that boundary, the value of ``Var[T, x]`` is
    ``x``, an equation of ``Equation[T]`` has terms of type ``T``, a tuple of
    ``tuple[T, ...]`` has its elements of these types and ``type[T]`` is a
    subclass of ``T``.

    >>> from discopy.monoidal import Ty, Box, Diagram
    >>> x, y = Ty('x'), Ty('y')
    >>> f = Box('f', x, y)
    >>> assert inhabits(f, Hom[Diagram, x, y])
    >>> assert not inhabits(f, Hom[Diagram, y, x])
    >>> assert inhabits(Equation(f, f), Equation[Hom[Diagram, x, y]])
    """
    origin, args = get_origin(kind), get_args(kind)
    if origin is Hom:
        return isinstance(value, args[0])\
            and (value.dom, value.cod) == args[1:]
    if origin is Var:
        return value == args[1]
    if origin is Equation:
        return all(inhabits(term, args[0]) for term in value.terms)
    if origin is tuple:
        return len(value) == len(args) and all(map(inhabits, value, args))
    if origin is type:
        return isinstance(value, type) and issubclass(value, args[0])
    return isinstance(value, kind)


@dataclass
class Declaration[**P, T](classmethod):
    """
    A declaration of a category, stated once on an abstract base class and
    inherited by every category below it: an :class:`Axiom` or a
    :class:`Rule`.

    The category is the class the declaration is bound to, e.g.
    :class:`discopy.cat.Arrow` for those of :class:`discopy.abc.Category`.
    Its function is a classmethod of it, implicitly: its first parameter is
    the category and the others are its arguments, drawn in order. Its
    signature is a sequent: each type parameter is a variable of the sort
    its bound states, ``A: Obj[C0]`` an object, ``X: Atom[C0]`` an atomic
    one and ``N: Count`` a number, each parameter a premise, ``f: Hom[C1, A,
    B]`` a morphism from ``A`` to ``B``, ``x: Var[C0, X]`` the value of an
    object expression and :data:`typing.Self` a term, and the return
    annotation the type of its output, see :meth:`output`. Object
    expressions are built by :class:`Tensor`, :class:`Unit`, :class:`L`,
    :class:`R`, :class:`Delay`, :class:`Over`, :class:`Under` and
    :class:`Repeat`. Every module stating a declaration needs ``from
    __future__ import annotations``, which keeps the annotations unevaluated
    until the variables are drawn: a function compiled without it is
    refused.

    Parameters:
        function : The function the declaration states, from the category and
            its arguments.
        category : The class the declaration is bound to, :obj:`None` until
            :meth:`bind` or the attribute access on a class binds it.
        name : The attribute the declaration is stored under, the name of the
            function by default.
        params : The parameters passed to the strategy of every morphism the
            declaration quantifies over, see :meth:`Axiom.weaken`.
    """

    function: Callable[P, T]
    _: KW_ONLY
    category: type = None  # ty: ignore[invalid-assignment]
    name: str = None  # ty: ignore[invalid-assignment]
    params: dict = None  # ty: ignore[invalid-assignment]

    def __post_init__(self):
        function = inspect.unwrap(self.function)
        deferred = __future__.annotations.compiler_flag
        if not function.__code__.co_flags & deferred:
            raise TypeError(
                f"{function.__module__} states {function.__name__} "
                "without `from __future__ import annotations`.")
        classmethod.__init__(self, self.function)
        self.name = self.name or self.function.__name__
        self.params = dict(self.params or {})
        self.__doc__ = self.function.__doc__

    def __repr__(self):
        """
        A bound declaration is the attribute of its category, e.g.
        ``cat.Arrow.unitality``; an unbound one wraps a function and has no
        transparent representation.
        """
        if self.category is None:
            return f"{type(self).__name__}({self.name})"
        return f"{factory_name(self.category)}.{self.name}"

    def __hash__(self):
        return hash((self.function, self.category, self.name))

    def bind(self, category: type[T]) -> Self:
        """ Bind the declaration to a concrete category. """
        return replace(self, category=category)

    def __get__(self, instance, owner: type[T]) -> Self:
        return self.bind(owner)

    @property
    def parameters(self) -> tuple[inspect.Parameter, ...]:
        """
        The parameters whose arguments are generated: all but the first,
        which is the category, and those with a default.
        """
        return tuple(
            parameter for parameter in tuple(
                inspect.signature(self.function).parameters.values())[1:]
            if parameter.default is inspect.Parameter.empty)

    def scope(self, variable: Callable, given: dict | None = None) -> dict:
        """
        The names a signature is evaluated with: the category as ``Self``
        and ``C1``, its objects as ``C0``, and then a value
        ``variable(name, sort)`` for each type parameter not ``given`` by
        name, the sort being its bound.
        """
        if self.category is None:
            raise TypeError(f"{self.name} is not bound to a class.")
        given, category = given or {}, self.category
        scope = {"Self": category, "C1": category,
                 "C0": getattr(category, "ob", category)}
        for parameter in inspect.unwrap(self.function).__type_params__:
            name = parameter.__name__
            scope[name] = given[name] if name in given\
                else variable(name, parameter.__bound__)
        return scope

    def evaluate(self, annotation: str, scope: dict):
        """ An annotation of the signature, evaluated in a scope. """
        function = inspect.unwrap(self.function)
        return eval(annotation, function.__globals__, scope)

    def instantiate(self, scope: dict, value: Callable) -> dict:
        """
        The arguments of the bound declaration: ``value(name, kind)`` for each
        of its :attr:`parameters`, their annotation evaluated in the scope.
        """
        return {
            parameter.name: value(
                parameter.name, self.evaluate(parameter.annotation, scope))
            for parameter in self.parameters}

    def output(self, scope: dict):
        """
        The type of the output of the declaration, its return annotation
        evaluated in the scope its arguments were drawn in, which the output
        :func:`inhabits`.
        """
        return self.evaluate(
            inspect.unwrap(self.function).__annotations__["return"], scope)

    def sequents(
            self, given: dict | None = None, **params
    ) -> st.SearchStrategy[tuple]:
        """
        Generate the scope and the arguments of the bound declaration: a
        variable of sort ``Obj`` from the strategy of ``category.ob``, of
        sort ``Atom`` of length one and of sort :class:`Count` a number up to
        :data:`MAX_COUNT`, then a premise ``Hom[C1, A, B]`` from the strategy
        of the category with its boundary and ``params``, a premise
        ``Var[T, x]`` the value ``x`` and :data:`typing.Self` a term.
        """
        from hypothesis import strategies as st

        @st.composite
        def sequents(draw):
            def variable(name, sort):
                if sort is Count:
                    return draw(st.integers(0, MAX_COUNT), label=name)
                length = {"min_length": 1, "max_length": 1}\
                    if get_origin(sort) is Atom else {}
                return draw(
                    self.category.ob.strategy(**length), label=name)

            def value(name, kind):
                if get_origin(kind) is Var:
                    return get_args(kind)[1]
                if get_origin(kind) is Hom:
                    _, dom, cod = get_args(kind)
                    strategy = self.category.strategy(
                        dom=dom, cod=cod, **params)
                else:
                    strategy = self.category.strategy()
                return draw(strategy, label=name)

            scope = self.scope(variable, given)
            return scope, self.instantiate(scope, value)

        return sequents()

    def arguments(
            self, given: dict | None = None, **params
    ) -> st.SearchStrategy[dict]:
        """ Generate the arguments of the bound declaration, see
        :meth:`sequents`. """
        return self.sequents(given, **params).map(lambda sequent: sequent[1])

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> T:
        if self.category is None:
            raise TypeError(f"{self.name} is not bound to a class.")
        return self.function(
            self.category,  # ty: ignore[invalid-argument-type]
            *args, **kwargs)


@dataclass(repr=False)
class Axiom[**P, T](Declaration[P, T]):
    """
    An axiom of a category: a :class:`Declaration` whose function states a
    law, from the category and its arguments to an :class:`Equation`, or to
    :obj:`NotImplemented` when the structure does not apply.

    Calling a bound axiom returns its own verdict: :obj:`NotImplemented`
    when the structure does not apply to the category, and the equation
    itself otherwise; a law declared broken raises an
    :class:`AxiomFailure` carrying that equation instead of returning it.

    A law is broken when *some* argument is a counterexample, not every one,
    so :attr:`broken` is declared by :meth:`failing` before any argument is
    generated — the property matrix marks such an axiom as an expected
    failure and lets the search find the counterexample.

    Parameters:
        broken : Whether the law is declared broken by :meth:`failing`.
    """

    _: KW_ONLY
    broken: bool = False

    __hash__ = Declaration.__hash__

    def modulo(self, up_to) -> Axiom[P, T]:
        """
        The same law with its equation compared up to a function, so that a
        category weakens an inherited axiom in one statement, e.g.
        ``CMap.dagger_contravariance = CompactCategory.dagger_contravariance
        .modulo(CMap.to_hypergraph)``.
        """
        @wraps(self.function)
        def equation(*args, **kwargs):
            return self.function(*args, **kwargs).modulo(up_to)
        return replace(self, function=equation)

    def failing(self, reason: str) -> Axiom[P, T]:
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

    def inapplicable(self, reason: str) -> Axiom[P, T]:
        """
        The same law declared not to apply to the category: it takes no
        argument and returns :obj:`NotImplemented`, with the reason as its
        documentation, e.g. ``trace_vanishing =
        TracedCategory.trace_vanishing.inapplicable("No trace.")``.
        """
        def law(_category):
            return NotImplemented
        law.__doc__ = reason
        return replace(self, function=law, params={}, broken=False)

    def weaken(self, **params) -> Axiom[P, T]:
        """
        The same law quantified over the morphisms the strategy of the
        category generates with the given parameters, e.g. the rigid
        diagrams of the underlying monoidal category
        ``RigidCategory.dagger_involution.weaken(within=MonoidalCategory)``,
        see :meth:`discopy.cat.Arrow.search`. Assigned to its own attribute
        beside a ``.failing`` declaration, it shows the matrix one expected
        failure and one green cell instead of one blanket expected failure.
        """
        return replace(self, params=dict(self.params, **params))

    def strategy(self) -> st.SearchStrategy[dict]:
        """
        Generate the arguments of the bound axiom, with the parameters
        :meth:`weaken` declared, see :meth:`Declaration.arguments`.
        """
        return self.arguments(**self.params)

    def canonical(self) -> Equation:
        """
        The law as a schema: its equation with an object named after each
        type parameter, a box named after each morphism, and two for each
        number, the equation a law declared broken raises included.

        >>> from discopy.cat import Arrow
        >>> print(Arrow.associativity.canonical())
        Equation(f >> g >> h, f >> g >> h)
        """
        def value(name, kind):
            if get_origin(kind) is Var:
                return get_args(kind)[1]
            dom, cod = get_args(kind)[1:] if get_origin(kind) is Hom\
                else (self.category.ob(name), ) * 2
            return self.category.box_factory(name, dom, cod)

        scope = self.scope(lambda name, sort: 2 if sort is Count
                           else self.category.ob(name))
        arguments = self.instantiate(scope, value)
        try:
            return self(**arguments)  # ty: ignore[invalid-return-type]
        except AxiomFailure as failure:
            return failure.equation

    def draw(self, **params):
        """
        Draw the :meth:`canonical` equation of the law, the parameters those
        of :meth:`discopy.monoidal.Equation.draw`. A law the category breaks
        on its canonical instance is drawn all the same, as the inequation it
        is there, see :meth:`Equation.checked`.

        >>> from discopy import biclosed
        >>> biclosed.Diagram.currying_left.draw(
        ...     doctest="docs/_static/biclosed/currying-left-failing.svg")

        .. image:: /_static/biclosed/currying-left-failing.svg
            :align: center
        """
        equation = self.canonical()
        if equation is NotImplemented:
            raise TypeError(f"{self} does not apply, so has nothing to draw.")
        return equation.checked().draw(**params)

    def falsify(self, **params) -> dict:
        """
        Search for a shrunk counterexample to the bound axiom: arguments for
        which the verdict fails — the equation is false, or the
        implementation refuses to build its terms — raising
        :class:`hypothesis.errors.NoSuchExample` when no counterexample is
        found. Keyword arguments are passed to :func:`hypothesis.find`.

        >>> from hypothesis import settings
        >>> from discopy.cat import Arrow
        >>> Arrow.associativity.falsify(
        ...     settings=settings(max_examples=10))  # doctest: +ELLIPSIS
        Traceback (most recent call last):
         ...
        hypothesis.errors.NoSuchExample: No examples found of condition ...
        """
        from hypothesis import find

        def refutes(arguments):
            try:
                verdict = self(**arguments)
            except AxiomFailure:
                return True
            return verdict is not NotImplemented and not verdict

        return find(self.strategy(), refutes, **params)


@dataclass(repr=False)
class Rule[**P, T](Declaration[P, T]):
    """
    An inference rule of a category: a :class:`Declaration` whose function
    concludes a morphism from its premises, the objects and morphisms it
    quantifies over, forwarding to the method that implements the operation,
    e.g. the cut ``def cut[A: Obj[C0], B: Obj[C0], C: Obj[C0]](cls, f:
    Hom[C1, A, B], g: Hom[C1, B, C]) -> Hom[C1, A, C]`` composes. Its return
    annotation ``Hom[C1, dom, cod]`` is the
    boundary of its conclusion, read by :meth:`strategy`, and never
    evaluated.

    >>> from discopy.cat import Arrow, Ob, Box
    >>> sorted(Arrow.rules)
    ['ax', 'cut']
    >>> f, g = Box('f', Ob('x'), Ob('y')), Box('g', Ob('y'), Ob('z'))
    >>> assert Arrow.cut(f, g) == f >> g
    """

    __hash__ = Declaration.__hash__

    @cached_property
    def conclusion(self) -> tuple[str | None, ...]:
        """
        The type parameter each side of the conclusion is, or :obj:`None`
        for a side that is not a variable.

        >>> from discopy.abc import MonoidalCategory
        >>> MonoidalCategory.cut.conclusion
        ('A', 'C')
        >>> MonoidalCategory.mix.conclusion
        (None, None)
        """
        function = inspect.unwrap(self.function)
        variables = {
            variable.__name__ for variable in function.__type_params__}
        annotation = function.__annotations__["return"]
        sides = ast.parse(annotation, mode="eval").body.slice.elts[1:]
        return tuple(
            side.id if isinstance(side, ast.Name) and side.id in variables
            else None for side in sides)

    @cached_property
    def is_recursive(self) -> bool:
        """
        Whether the rule has a morphism among its premises, i.e. a parameter
        annotated with ``Hom``.
        """
        return any(
            isinstance(premise, ast.Subscript) and premise.value.id == "Hom"
            for premise in (
                ast.parse(parameter.annotation, mode="eval").body
                for parameter in self.parameters))

    def given(self, dom=None, cod=None) -> dict:
        """
        The variables a goal from ``dom`` to ``cod`` binds: each side of the
        conclusion that is a variable takes the side of the goal, unless the
        variable is an :class:`Atom` and the side is not.

        >>> from discopy.abc import Category
        >>> from discopy.cat import Ob
        >>> Category.cut.given(Ob('x'), Ob('y'))
        {'A': cat.Ob('x'), 'C': cat.Ob('y')}
        """
        variables = {
            variable.__name__: variable
            for variable in inspect.unwrap(self.function).__type_params__}
        return {
            name: side for name, side in zip(self.conclusion, (dom, cod))
            if name is not None and side is not None
            and (get_origin(variables[name].__bound__) is not Atom
                 or len(side) == 1)}

    def strategy(
            self, dom=None, cod=None, **params) -> st.SearchStrategy[dict]:
        """
        Generate the premises of the rule for a conclusion from ``dom`` to
        ``cod``, see :meth:`Declaration.arguments`, the variables it binds
        :meth:`given` and the others drawn. The conclusion need not meet the
        goal on a side that is not a variable.
        """
        return self.arguments(self.given(dom, cod), **params)


def axiom[**P, T](
        equation: Callable[P, Equation[T]]) -> Axiom[P, Equation[T]]:
    """
    Decorate an equation as a categorical axiom: a classmethod of its
    category, implicitly, whose remaining parameters are generated.
    """
    return Axiom(equation)


def rule[**P, T](function: Callable[P, T]) -> Rule[P, T]:
    """
    Decorate an operation as an inference rule: a classmethod of its
    category, implicitly, from its premises to its conclusion.
    """
    return Rule(function)


class Testable[T](ABC):
    """
    A testable class states axioms, which its subclasses inherit along with
    the structure they axiomatise, and says how to generate the terms those
    axioms quantify over with :meth:`strategy`.

    A :class:`discopy.abc.Category` states the laws of a categorical
    structure, a :class:`Serialisable` those of writing a term down and
    reading it back, which is why the two meet here rather than in either.
    """

    @classmethod
    def strategy(cls, **params) -> st.SearchStrategy[T]:
        """
        Build a `search strategy
        <https://hypothesis.readthedocs.io/en/latest/data.html>`_ for the
        instances of ``cls``: implementing it is how a category enrols in
        the property matrix, see :meth:`enrolled`.

        An override that delegates to another strategy accepts
        ``**params``, pops the parameters it consumes and forwards the
        rest, so that a caller's bounds pass through unchanged. A terminal
        strategy instead declares exactly the parameters it implements: a
        constraint it cannot honour fails loudly as an unexpected keyword
        rather than being silently dropped.

        The default raises, deliberately not as an
        :func:`abc.abstractmethod`, which would make every category that has
        not implemented one uninstantiable rather than merely unchecked.

        >>> from discopy.abc import Nat
        >>> Nat.strategy()
        Traceback (most recent call last):
         ...
        NotImplementedError: No strategy implemented for abc.Nat.
        """
        raise NotImplementedError(
            f"No strategy implemented for {factory_name(cls)}.")

    @classmethod
    def declared[D: Declaration](cls, kind: type[D]) -> dict[str, D]:
        """
        The declarations of a kind inherited by ``cls``, by name, subclasses
        overriding bases, bound to ``cls``.

        Names are collected before they are filtered, so that assigning
        anything that is not a declaration over an inherited one drops it
        altogether, rather than restating it. Each declaration is named after
        the attribute it is stored under, so that a law weakened beside its
        failing declaration, e.g. ``dagger_involution_monoidal``, is a
        cell of its own in the matrix.
        """
        visible = {
            name: value
            for base in reversed(cls.__mro__)
            for name, value in base.__dict__.items()}
        return {name: replace(value.bind(cls), name=name)
                for name, value in visible.items()
                if isinstance(value, kind)}

    axioms = classproperty(lambda cls: cls.declared(Axiom))
    """ The axioms inherited by ``cls``, see :meth:`declared`. """

    rules = classproperty(lambda cls: cls.declared(Rule))
    """ The rules inherited by ``cls``, see :meth:`declared`. """

    @classmethod
    def subclasses(cls) -> tuple[type[Testable], ...]:
        """
        Every transitive subclass of ``cls``, ``cls`` itself included, once,
        in the order a breadth-first walk of the subclass graph meets it.

        >>> from discopy.cat import Arrow, Box
        >>> assert Arrow.subclasses()[0] is Arrow
        >>> assert Box in Arrow.subclasses()
        """
        found, queue = {cls: None}, [cls]
        while queue:
            for subclass in queue.pop(0).__subclasses__():
                if subclass not in found:
                    found[subclass] = None
                    queue.append(subclass)
        return tuple(found)

    @classmethod
    def enrolled(cls) -> tuple[type[Testable], ...]:
        """
        The categories the property matrix checks, by name: those that state
        laws, generate their terms and are their own ``ar``. A box inherits
        the strategy of the category it lives in, whose terms it is part of,
        rather than being a category of its own, and so does a type, which
        is checked as the boundary of the morphisms of its category.

        >>> from discopy.cat import Arrow, Box
        >>> from discopy.monoidal import Ty
        >>> assert Arrow in Testable.enrolled()
        >>> assert Box not in Testable.enrolled()
        >>> assert Ty not in Testable.enrolled()
        """
        from discopy.abc import ColouredMonoid

        def generates(testable):
            try:
                testable.strategy()
            except NotImplementedError:
                return False
            return True

        return tuple(sorted((
            testable for testable in cls.subclasses()
            if getattr(testable, "ar", None) is testable
            and not issubclass(testable, ColouredMonoid)
            and testable.axioms and generates(testable)), key=factory_name))

    @classmethod
    def matrix(cls, once: bool = False) -> list[Axiom]:
        """
        Every law of every :meth:`enrolled` category, bound to it, or only
        ``once`` per declaration of a law: bound to the enrolled category
        nearest the class declaring it, rather than to every category
        inheriting it. A category restating a law, broken, weakened or
        modulo a quotient, declares it anew and is the nearest to that.

        >>> from discopy.cat import Arrow
        >>> assert Arrow.unitality in Testable.matrix(once=True)
        """
        cells = [
            law for testable in cls.enrolled()
            for law in testable.axioms.values()]
        if not once:
            return cells
        nearest = {}
        for law in cells:
            distance, declaring = next(
                (i, base) for i, base in enumerate(law.category.__mro__)
                if law.name in vars(base))
            key = (declaring, law.name)
            if key not in nearest or distance < nearest[key][0]:
                nearest[key] = (distance, law)
        return sorted(
            (law for _, law in nearest.values()),
            key=lambda law: (factory_name(law.category), law.name))


no_strategy = Testable.__dict__["strategy"]
"""
The default :meth:`Testable.strategy`, under a name that can be assigned: a
category that would inherit a strategy for terms it cannot read back, e.g.
a pregroup diagram, declares ``strategy = no_strategy`` to stay out of the
matrix until it implements its own.
"""


class Serialisable[T](Testable[T]):
    """
    A type whose terms are written down and read back: by their
    representation, their pickle, their deep copy and their tree, each
    with the law that it is a roundtrip.
    """

    @classmethod
    def environment(cls) -> dict:
        """
        The namespace the representation of a term reads back in: the
        public names of the package, as ``from discopy import *`` binds
        them, so that a representation qualified by module such as
        ``cat.Box('f', cat.Ob('x'), cat.Ob('y'))`` evaluates, and then
        those of the module the type is defined in, so that one
        printing bare names such as ``Tensor[int]([0], dom=Dim(1),
        cod=Dim(1))`` evaluates too. The module comes second because a
        term prints the names its own module binds: ``Dim`` in
        ``discopy.tensor`` is the one a tensor is built from.

        The import is local because the package imports this module.
        """
        import discopy

        public = lambda namespace: {
            name: value for name, value in namespace.items()
            if not name.startswith("_")}
        module = sys.modules[cls.__module__]
        return dict(public(vars(discopy)), **public(vars(module)))

    @axiom
    def repr_transparency(cls, term: Self) -> Equation[Self]:
        """
        The representation of a term evaluates back to it, in the
        :meth:`environment` of its type.
        """
        return Equation(eval(repr(term), cls.environment()), term)

    @axiom
    def pickling(cls, term: Self) -> Equation[tuple[type[Self], Self]]:
        """
        A term loads back from its pickle, of the same class: the equation
        is between the pairs of a class and a term, since a subscript of a
        :class:`discopy.utils.NamedGeneric` is part of what a pickle keeps.
        """
        loaded = pickle.loads(pickle.dumps(term))
        return Equation((type(loaded), loaded), (type(term), term))

    @axiom
    def copying(cls, term: Self) -> Equation[tuple[type[Self], Self]]:
        """
        A term is equal to its deep copy, of the same class. Copying goes
        through the same protocol as :meth:`pickling` without the bytes, so
        a class whose reduction drops what its state needs breaks one law
        with the other.
        """
        copied = deepcopy(term)
        return Equation((type(copied), copied), (type(term), term))

    @axiom
    def serialisation(cls, term: Self) -> Equation[Self]:
        """
        A term decodes back from its tree and from the JSON of its tree.
        A type without a tree declares the law inapplicable.
        """
        return Equation(from_tree(term.to_tree()), loads(dumps(term)), term)
