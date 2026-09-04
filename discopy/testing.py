"""Data structures and strategies for property tests."""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from functools import wraps
from typing import TypeVar, TYPE_CHECKING

from discopy.utils import AxiomError

if TYPE_CHECKING:
    from hypothesis import strategies as st


C0 = TypeVar("C0")
C1 = TypeVar("C1")
"""
The object and arrow types of the carrier an axiom is bound to.

An axiom annotates its arguments with these rather than with the concrete
types of the module it is written in, so that a subclass inherits the
override with its own types: :func:`proptest.strategies.arguments` rebinds
both names to ``carrier.ob`` and ``carrier.ar`` when it evaluates the
annotations. This is also why every module stating an axiom needs
``from __future__ import annotations``, which keeps them unevaluated.
"""


GENERATORS = tuple("abcde")
"""
The names the generators of a free category are drawn from.

They are finitely many and shared, so a generated functor can name every one
of them: composing two functors keeps only the keys of the left-hand map, so
a functor that named just a few would compose to one defined nowhere else.
"""


class Strategy[T](ABC):
    """
    A type with a canonical property-test strategy.
    Using ``hypothesis``, we can get the default search strategy dispatch
    through any object that defines a method called ``draw``, but this
    would conflict with our existing ``draw`` methods, so we do it manually
    with this custom trait.
    """

    @classmethod
    @abstractmethod
    def strategy(cls, **params) -> "st.SearchStrategy[T]":  # pragma: no cover
        """Build a strategy for instances of ``cls``."""


class Natural(int, Strategy["Natural"]):
    """ A non-negative integer with tensor given by addition. """

    def __new__(cls, value=0):
        if not isinstance(value, int) or value < 0:
            raise ValueError("Expected a non-negative integer.")
        return super().__new__(cls, value)

    def __matmul__(self, other):
        return type(self)(self + other) if isinstance(other, int)\
            else NotImplemented

    __rmatmul__ = __matmul__
    __len__ = lambda self: int(self)

    @classmethod
    def equation_factory(cls, *terms):
        """ Construct an equation between natural numbers. """
        from discopy.cat import Equation

        return Equation(*terms)

    @classmethod
    def strategy(cls, *, max_size=3):
        """Generate non-negative integers."""
        from hypothesis import strategies as st

        return st.one_of(
            st.just(1),
            st.integers(min_value=0, max_value=max_size)).map(cls)


@dataclass(frozen=True, eq=False)
class Relabelling(Mapping):
    """
    A map on the generators of a free category, sending the atoms it names to
    a chosen object and every other one to itself.

    It is a :class:`Mapping` rather than a closure so that functors built
    from it can be composed and compared, which is what makes the axioms of
    ``Cat`` itself checkable: :meth:`discopy.utils.MappingOrCallable.then`
    composes by iterating the keys of the left-hand map, and equality
    compares the wrapped maps. Iterating yields only the atoms it renames,
    while looking one up is total, so a functor built from it applies to any
    diagram and still composes to something comparable.
    """
    images: tuple[tuple[object, object], ...] = ()

    def __getitem__(self, atom):
        """
        The image of an atomic object, carrying over whatever the atom does:
        a rotation in a rigid category, a delay in a feedback one.
        """
        wire, = getattr(atom, "inside", (atom, ))
        for key, image in self.images:
            other, = getattr(key, "inside", (key, ))
            if other.name == wire.name:
                break
        else:
            return atom
        turns = getattr(wire, "z", 0)
        for _ in range(abs(turns)):
            image = image.l if turns < 0 else image.r
        steps = getattr(wire, "time_step", 0)
        return image.delay(steps) if steps else image

    def __iter__(self):
        return iter([key for key, _ in self.images])

    def __len__(self):
        return len(self.images)

    def __bool__(self):
        """ A relabelling is total, even when it renames nothing. """
        return True

    def send(self, typ):
        """ The image of an object, atom by atom. """
        if not hasattr(typ, "inside"):
            return self[typ]
        return type(typ)().tensor(*(
            self[typ[i:i + 1]] for i in range(len(typ))))


@dataclass(frozen=True, eq=False)
class Relabelled(Mapping):
    """
    Send each box to one of the same name on the relabelled boundary.

    Boxes cannot be enumerated, so this iterates empty and two of them
    compare equal as mappings do. That is what lets a functor built from a
    :class:`Relabelling` be the unit of its own composition on the right.
    """
    objects: Relabelling

    def __getitem__(self, box):
        return type(box)(
            box.name, self.objects.send(box.dom), self.objects.send(box.cod))

    def __iter__(self):
        return iter([])

    def __len__(self):
        return 0

    def __bool__(self):
        """ A relabelling is total, even though it enumerates nothing. """
        return True


class Axiom[T]:
    """
    A categorical law, stated either of a carrier or of one of its elements.

    An axiom whose first parameter is ``cls`` is a law of the category: it is
    bound to the carrier and its remaining arguments are generated. One whose
    first parameter is ``self`` is a law of an element, e.g. a functor, so the
    element is generated too and the law reads as a method on it.

    Calling a bound axiom returns its own verdict: :obj:`NotImplemented` when
    the structure does not apply to the carrier, an
    :class:`discopy.utils.AxiomError` wrapping the equation when the law is
    known to be broken, and the equation itself otherwise.

    A law is broken when *some* argument is a counterexample, not every one,
    so :attr:`broken` is declared by :meth:`failing` before any argument is
    generated — the property matrix marks such an axiom as an expected
    failure and lets the search find the counterexample.
    """

    def __init__(self, equation, *, carrier=None, name=None, subspaces=None,
                 broken=False):
        function = equation.__func__ if isinstance(equation, classmethod)\
            else equation
        self.equation = function
        self.signature = inspect.signature(function)
        self.receiver = next(iter(self.signature.parameters), None)
        self.carrier = carrier
        self.name = self.__name__ = name or function.__name__
        self.broken = broken
        self.subspaces = dict(subspaces or {})
        self.__doc__ = function.__doc__

    def __repr__(self):
        return f"Axiom({self.name})"

    def __set_name__(self, owner, name):
        """
        Take the name of the attribute the axiom is assigned to, so that an
        override built with :meth:`modulo`, :meth:`failing` or
        :meth:`inapplicable` needs no name of its own.
        """
        self.name = self.__name__ = name

    @property
    def is_method(self) -> bool:
        """ Whether the law is stated of an element rather than a carrier. """
        return self.receiver == "self"

    def bind(self, carrier: type[T]) -> Axiom[T]:
        """ Bind the axiom to a concrete carrier. """
        return type(self)(
            self.equation, carrier=carrier, name=self.name,
            subspaces=self.subspaces, broken=self.broken)

    def __get__(self, instance, owner: type[T]) -> Axiom[T]:
        return self.bind(owner)

    def modulo(self, up_to) -> Axiom[T]:
        """
        The same law with its equation compared up to a function, so that a
        carrier weakens an inherited axiom in one statement, e.g.
        ``bifunctoriality = MonoidalCategory.bifunctoriality.modulo(
        normal_form)``.
        """
        @wraps(self.equation)
        def equation(*args, **kwargs):
            return self.equation(*args, **kwargs).modulo(up_to)
        return type(self)(equation, broken=self.broken)

    def failing(self, reason: str) -> Axiom[T]:
        """
        The same law declared broken, its equation wrapped in an
        :class:`discopy.utils.AxiomError` with the reason as message and
        documentation, e.g. ``braid_naturality =
        BraidedCategory.braid_naturality.failing("A free braid is a box.")``.
        """
        @wraps(self.equation)
        def equation(*args, **kwargs):
            return AxiomError(reason, self.equation(*args, **kwargs))
        equation.__doc__ = reason
        return type(self)(equation, broken=True)

    def inapplicable(self, reason: str) -> Axiom[T]:
        """
        The same law declared not to apply to the carrier: it takes no
        argument and returns :obj:`NotImplemented`, with the reason as its
        documentation, e.g. ``trace_vanishing =
        TracedCategory.trace_vanishing.inapplicable("No trace.")``.
        """
        def law(cls):
            return NotImplemented
        law.__name__, law.__doc__ = self.name, reason
        return type(self)(law)

    def weaken(self, **subspaces) -> Axiom[T]:
        """
        The same law quantified over a subspace of the named arguments,
        e.g. ``bifunctoriality_connected =
        MonoidalCategory.bifunctoriality.weaken(
        square=BoundaryConnected[Bifunctor[C1]])``: each named parameter
        is generated from its subspace strategy, whose wrapper validates
        membership on construction — so a recorded counterexample replays
        honestly — and is unwrapped before the body reads it. Assigned to
        its own attribute beside a ``.failing`` declaration, it shows the
        matrix one expected failure and one green cell instead of one
        blanket expected failure.
        """
        result = type(self)(
            self.equation, name=self.name,
            subspaces=dict(self.subspaces, **subspaces), broken=self.broken)
        return result

    def strategy(self) -> "st.SearchStrategy":
        """
        Generate the arguments the bound axiom expects.

        ``C0`` and ``C1`` resolve to the objects and arrows of the carrier,
        or of the carrier's domain for a law of an element: the arguments a
        functor is applied to live in the category it maps from, and its
        codomain is reachable as ``self.cod`` from the body.
        """
        from hypothesis import strategies as st

        from discopy import shape

        function = inspect.unwrap(self.equation)
        source = self.carrier.dom if self.is_method else self.carrier
        scope = dict(shape.catalog(), C0=source.ob, C1=source.ar)
        annotations = inspect.get_annotations(
            function, globals=function.__globals__, locals=scope,
            eval_str=True)
        annotations[self.receiver] = self.carrier
        annotations.update({
            name: substitute(annotation, scope)
            for name, annotation in self.subspaces.items()})
        required = (
            parameter for parameter in self.parameters
            if parameter.default is inspect.Parameter.empty)
        return st.tuples(*(
            resolve(annotations[parameter.name]) for parameter in required))

    def falsify(self, **params) -> tuple:
        """
        Search for a shrunk counterexample to the bound axiom: arguments for
        which the verdict fails — the equation is false, or the
        implementation refuses to build its terms — raising
        :class:`hypothesis.errors.NoSuchExample` when no counterexample is
        found. Keyword arguments are passed to :func:`hypothesis.find`.

        >>> from discopy.cat import Functor
        >>> Functor.unitality.falsify()  # doctest: +ELLIPSIS
        (cat.Functor(ob_map=..., ar_map=...),)
        >>> Functor.associativity.falsify()  # doctest: +ELLIPSIS
        Traceback (most recent call last):
         ...
        hypothesis.errors.NoSuchExample: No examples found of condition ...
        """
        from hypothesis import find

        if self.carrier is None:
            raise TypeError(f"{self.name} is not bound to a class.")

        def refutes(args):
            try:
                verdict = self(*args)
            except Exception:
                return True
            return verdict is not NotImplemented and not holds(verdict)

        return find(self.strategy(), refutes, **params)

    @property
    def parameters(self) -> tuple[inspect.Parameter, ...]:
        """
        The parameters whose arguments the property matrix generates.

        For a law of an element that includes the element itself, so an axiom
        that takes none states its verdict before anything is generated.
        """
        explicit = tuple(self.signature.parameters.values())[1:]
        if not self.is_method:
            return explicit
        receiver = inspect.Parameter(
            self.receiver, inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=self.carrier)
        return (receiver, ) + explicit

    def __call__(self, *args, **kwargs):
        if self.carrier is None:
            raise TypeError(f"{self.name} is not bound to a class.")
        signature = self.signature.replace(parameters=self.parameters)
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        arguments = dict(bound.arguments)
        if self.is_method:
            return self.equation(**arguments)
        return self.equation(
            **{self.receiver: self.carrier, **arguments})


def axiom(equation) -> Axiom:
    """ Decorate an equation as an inherited categorical axiom. """
    return Axiom(equation)


def resolve(annotation, **params) -> "st.SearchStrategy":
    """ Resolve the strategy implemented by an annotated type or shape. """
    from discopy import shape

    if isinstance(annotation, shape.Sampled):
        return annotation.strategy(**params)
    if not isinstance(annotation, type)\
            or not issubclass(annotation, Strategy):
        raise TypeError(
            f"Expected a Strategy annotation, got {annotation!r}.")
    return annotation.strategy(**params)


def substitute(annotation: str, scope: dict):
    """
    Evaluate a subspace annotation in the shape catalog and the scope
    binding :obj:`C0` and :obj:`C1` — lazily, so that a module can weaken
    an axiom without importing :mod:`discopy.shape` at import time.
    """
    from discopy import shape

    return eval(annotation, dict(shape.catalog(), **scope))


def assert_axioms(*carriers) -> None:
    """
    Check every axiom of each carrier on a single generated example, a dry
    run of the property tests in ``proptest/``.

    An axiom that does not apply is skipped, a broken one is only required
    to state its :class:`discopy.utils.AxiomError` — one example need not
    be a counterexample — and any other law must hold.
    """
    from hypothesis import Phase, find, settings

    single_shot = settings(
        max_examples=1, phases=(Phase.generate, ), database=None)
    for carrier in carriers:
        for axiom in carrier.axioms:
            if not axiom.parameters and axiom() is NotImplemented:
                continue
            args = find(
                axiom.strategy(), lambda value: True, settings=single_shot)
            try:
                verdict = axiom(*args)
            except AxiomError:
                assert axiom.broken, axiom
                continue
            if axiom.broken:
                assert isinstance(verdict, AxiomError), axiom
            else:
                assert holds(verdict), axiom


def assert_strategy_finds(carrier, *structures) -> None:
    """
    Check that the strategy of an arrow carrier generates a term containing
    a box of each of the given structural classes.
    """
    from hypothesis import find

    for structure in structures:
        find(carrier.strategy(), lambda term: any(
            isinstance(box, structure)
            for box in getattr(term, "boxes", term.inside)))


def assert_verdict(axiom: Axiom, verdict) -> None:
    """
    Assert the verdict a bound axiom returned for some arguments.

    An :class:`discopy.utils.AxiomError` wraps the equation of a law that is
    known to be broken — as its last argument, after an optional reason —
    and carries none at all when the implementation refused to build its
    terms. Either way the equation is asserted: it is :attr:`Axiom.broken`
    that tells the runner to expect the failure.
    """
    assert holds(verdict)


def holds(verdict) -> bool:
    """
    Whether a verdict asserts, unwrapping the equation a broken law carries
    as the last argument of its :class:`discopy.utils.AxiomError`.
    """
    if isinstance(verdict, AxiomError):
        verdict = verdict.args[-1] if verdict.args else False
    return bool(verdict)


def declared_axioms(cls) -> dict[str, Axiom]:
    """
    The axioms a class declares, by name, subclasses overriding bases.

    Names are collected before they are filtered, so that assigning anything
    that is not an axiom over an inherited one drops it altogether, rather
    than restating it.
    """
    visible = {
        name: value
        for base in reversed(cls.__mro__)
        for name, value in base.__dict__.items()}
    return {name: value for name, value in visible.items()
            if isinstance(value, Axiom)}
