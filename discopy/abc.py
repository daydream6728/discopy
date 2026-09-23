"""
The abstract base classes for categories.

These mirror the concrete hierarchy of :mod:`discopy` modules: each class adds
the characteristic generator of its categorical structure as an
:func:`abc.abstractmethod`, e.g. :class:`BraidedCategory` is a
:class:`MonoidalCategory` with an abstract :meth:`BraidedCategory.braid`.

.. raw:: html
    :file: api/architecture.html

Software dependencies between modules go top-to-bottom, left-to-right and
forgetful functors between categories go the other way.

Each class also declares its :func:`discopy.axioms.axiom` equations, which
every free category inherits along with the structure they axiomatise:
:class:`Category` states the unitality and associativity of composition,
the typing of its identities and composites, and the involution and
contravariance of its dagger; a :class:`ColouredMonoid` inherits them as
the unitality and associativity of its product, its composition. The
structural methods carry their own :func:`discopy.search.rule` or
:func:`discopy.search.generator`, from which
:meth:`discopy.monoidal.Diagram.strategy` searches for the diagrams the
laws quantify over: a level of the hierarchy declares its structure here
and inherits the search as is.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Category
    ColouredMonoid
    Monoid
    Nat
    MonoidalCategory
    PRO
    TracedCategory
    ResiduatedMonoid
    BiclosedCategory
    Pregroup
    RigidCategory
    PivotalCategory
    BraidedCategory
    PROB
    SymmetricCategory
    PROP
    MarkovCategory
    ClosedCategory
    DelayedMonoid
    FeedbackCategory
    BalancedCategory
    RibbonCategory
    CompactCategory
    HypergraphCategory
    NamedGeneric
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from types import NoneType
from typing import Annotated, ClassVar, Self, TYPE_CHECKING

from discopy.axioms import (  # noqa: F401
    C0, C1, Atom, Axiom, Count, Delay, Equation, Generator, Hom, L, Over,
    R, Repeat, Rule, Serialisable, Tensor, Testable, Under, Unit, axiom,
    declarations, generator, inapplicable, rule)
from discopy.utils import (  # noqa: F401
    NamedGeneric, classproperty, factory_name)


class Category[C0, C1: Category](Testable, ABC):
    """
    A category is a class with two class variables ``ob, ar``, two attributes
    ``dom, cod`` and two methods ``id, then``.

    This base class also implements syntactic sugar :code:`>>` and :code:`<<`
    for forward and backward composition with the method :code:`then`.

    Example
    -------
    >>> class List(list, Category):
    ...     ob, dom, cod = type(None), None, None
    ...     def then(self, other):
    ...         return self + other
    >>> assert List([1, 2]) >> List([3]) == List([1, 2, 3])
    >>> assert List([3]) << List([1, 2]) == List([1, 2, 3])
    """
    ob: ClassVar[type]
    factory: ClassVar[type]
    dom: C0
    cod: C0

    #: Backward-compatible alias for :attr:`factory`, since types are
    #: themselves the objects of diagrams.
    ar = classproperty(lambda cls: getattr(cls, "factory", cls))

    #: The equation up to which the axioms of the category compare, with
    #: strict equality by default. A category that quotients its equations
    #: binds its own, e.g. by hypergraph isomorphism from symmetric
    #: categories on, and :meth:`discopy.axioms.Axiom.modulo` weakens it
    #: further.
    Equation: ClassVar[type[Equation]] = Equation

    @classproperty
    def rules(cls: type) -> dict[str, Rule]:
        """
        The inference rules inherited by ``cls``, by name: the rule each
        structural method carries, see :func:`discopy.search.rule`, bound
        to ``cls`` and owned by the class declaring it. A rule survives
        the plain method implementing it, which the search calls by that
        name; one decorated with :func:`discopy.search.inapplicable` is
        dropped.
        """
        return declarations(cls, Rule)

    @classproperty
    def generators(cls: type) -> dict[str, Generator]:
        """
        The logical constants inherited by ``cls``, by name: the rules
        the search builds in one step, see
        :func:`discopy.search.generator`. A class adjusts the set by
        assigning a dictionary of rules instead,
        :meth:`discopy.search.Rule.constant` giving the rule of one given
        box, so that its strategy draws from a fixed vocabulary, e.g. the
        words of a pregroup grammar or the gates of a circuit.

        >>> from hypothesis import find
        >>> from discopy.axioms import Rule
        >>> from discopy.grammar import pregroup
        >>> n, s = pregroup.Ty('n'), pregroup.Ty('s')
        >>> Alice, sleeps = pregroup.Word('Alice', n), pregroup.Word(
        ...     'sleeps', n.r @ s)
        >>> class Sentence(pregroup.Diagram):
        ...     generators = {
        ...         "cups": pregroup.Diagram.generators["cups"],
        ...         **{w.name: Rule.constant(w) for w in (Alice, sleeps)}}
        >>> print(find(Sentence.strategy(), bool).foliation())
        Alice @ sleeps >> Cup(n, n.r) @ s
        """
        return declarations(cls, Generator)

    @classmethod
    @generator
    @abstractmethod
    def id[A](cls, dom: Annotated[C0, A]) -> Annotated[C1, Hom[A, A]]:
        """
        Identity morphism on an object :code:`dom: C0`, to be instantiated:
        as a rule, ``x ⊢ x`` with no box is the identity.

        Parameters:
            dom (C0) : The domain of an identity is also its codomain.
        """

    @rule
    @abstractmethod
    def then[A, B, C](
            self: Annotated[C1, Hom[A, B]],
            other: Annotated[C1, Hom[B, C]]) -> Annotated[C1, Hom[A, C]]:
        """
        Sequential composition, to be instantiated: the rule composes two
        morphisms, an implementation may take ``n >= 1`` of them.

        Parameters:
            other : The other morphism to compose sequentially.
        """

    def is_composable(self, other: C1) -> bool:
        """
        Whether two morphisms are composable, i.e. the codomain of the first is
        the domain of the second.

        Parameters:
            other : The other morphism.
        """
        return self.cod == other.dom

    def is_parallel(self, other: Category) -> bool:
        """
        Whether two morphisms are parallel, i.e. they have the same
        domain and codomain.

        Parameters:
            other : The other morphism.
        """
        return (self.dom, self.cod) == (other.dom, other.cod)

    @axiom
    def unitality(
            cls, f: C1) -> Equation[C1]:
        """ Left and right unitality of composition. """
        return cls.Equation(cls.id(f.dom).then(f), f, f.then(cls.id(f.cod)))

    @axiom
    def associativity[A, B, C, D](
            cls, f: Annotated[C1, Hom[A, B]], g: Annotated[C1, Hom[B, C]],
            h: Annotated[C1, Hom[C, D]]) -> Equation[C1]:
        """ Associativity of composition. """
        return cls.Equation(f.then(g).then(h), f.then(g.then(h)))

    @axiom
    def identity_typing(
            cls, x: C0) -> Equation[C0]:
        """ Typing of identity morphisms. """
        identity = cls.id(x)
        return cls.ob.Equation(identity.dom, x, identity.cod)

    @axiom
    def composition_dom_typing[A, B, C](
            cls, f: Annotated[C1, Hom[A, B]],
            g: Annotated[C1, Hom[B, C]]) -> Equation[C0]:
        """ Domain typing of composition. """
        return cls.ob.Equation(f.then(g).dom, f.dom)

    @axiom
    def composition_cod_typing[A, B, C](
            cls, f: Annotated[C1, Hom[A, B]],
            g: Annotated[C1, Hom[B, C]]) -> Equation[C0]:
        """ Codomain typing of composition. """
        return cls.ob.Equation(f.then(g).cod, g.cod)

    @axiom
    def dagger_involution(
            cls, f: C1) -> Equation[C1]:
        """ The dagger is involutive. """
        return cls.Equation(f.dagger().dagger(), f)

    @axiom
    def dagger_contravariance[A, B, C](
            cls, f: Annotated[C1, Hom[A, B]],
            g: Annotated[C1, Hom[B, C]]) -> Equation[C1]:
        """ The dagger reverses composition. """
        return cls.Equation(f.then(g).dagger(), g.dagger().then(f.dagger()))

    __rshift__ = __llshift__ = lambda self, other: self.then(other)
    __lshift__ = __lrshift__ = lambda self, other: other.then(self)


class ColouredMonoid[C0, C1: ColouredMonoid](Category[C0, C1]):
    """
    A coloured monoid is a category whose sequential composition ``then`` is
    given by a monoidal ``tensor``, with the objects ``C0`` (its colours) as
    the boundaries of its morphisms.

    An ordinary :obj:`Monoid` is the special case with a single, trivial
    colour, i.e. :class:`type(None)`. We do not enforce this so
    that e.g. :class:`monoidal.Ty` can take colours as objects.
    """
    if TYPE_CHECKING:
        def __len__(self) -> int:
            """ The number of generating objects inside, assumed free. """

        def __getitem__(self, key) -> Self:
            """ The slices of a free monoid, assumed to stay inside it. """

    @classmethod
    def id(cls, dom: C0 | None = None) -> C1:
        """The monoidal unit, i.e. the empty tensor ``cls()``."""
        return cls()  # ty: ignore[invalid-return-type]

    @classmethod
    def unit(cls, colour: C0 | None = None) -> C0 | C1:
        """
        The unit at a colour, i.e. the identity on it.

        It need not be an element of the monoid, which is why it may land in
        ``C0``: the layers of :class:`monoidal.Layer` are closed under
        ``tensor`` but the empty one is a type rather than a layer.
        """
        return cls.id(colour)

    @abstractmethod
    def tensor(self, *objects: C1) -> C1:
        """ The n-ary product of a monoid for ``n > 0``. """

    def then(self, *others: C1) -> C1:
        """Sequential composition, given by the monoid product."""
        return self.tensor(*others)

    @classmethod
    def cast(cls, atoms) -> C1:
        """
        The element of a tuple of atoms, or of a single atom; an element of
        the monoid is unchanged.

        Parameters:
            atoms : An element, a tuple of atoms or a single atom.

        >>> assert Nat.cast(2) == Nat(2) == Nat.cast(Nat(2))
        """
        if isinstance(atoms, cls):
            return atoms
        if isinstance(atoms, tuple):
            return cls(*atoms)  # ty: ignore[invalid-return-type]
        return cls(  # ty: ignore[invalid-return-type]
            atoms)  # ty: ignore[too-many-positional-arguments]

    @classmethod
    def whisker(cls, other: C0 | C1) -> C1:
        """
        Do nothing if ``other`` is already a morphism else apply :meth:`id`.

        Parameters:
            other : The object or morphism to be tensored on the left or right.
        """
        return (
            other if isinstance(other, cls)  # ty: ignore[invalid-return-type]
            else cls.id(other))  # ty: ignore[invalid-argument-type]

    def __matmul__(self, other):
        return self.tensor(other)

    def __rmatmul__(self, other):
        return self.whisker(other).tensor(self)


class Monoid[C1: Monoid](ColouredMonoid[NoneType, C1]):
    """ A monoid is a coloured monoid with a single, trivial colour. """


@dataclass
class Nat(Monoid["Nat"]):
    """
    ``Nat`` is the free monoid on one generator, i.e. the natural numbers
    with addition as tensor. It is also a sequence over its unary encoding:
    :meth:`__len__` gives back the natural number itself and slicing reads
    it off as a sequence of ``1``'s, e.g. ``Nat(3)[:1] == Nat(1)``.

    Parameters:
        n : The natural number.
    """
    n: int = 0

    def tensor(self, *others: Nat) -> Nat:
        if any(not isinstance(other, Nat) for other in others):
            return NotImplemented  # This allows whiskering on the left.
        return type(self)(self.n + sum(other.n for other in others))

    def __len__(self) -> int:
        return self.n

    def __index__(self) -> int:
        return self.n

    def __str__(self) -> str:
        return str(self.n)

    def __getitem__(self, key: int | slice) -> Nat:
        """
        Slicing a natural number reads it off as a sequence of ``1``'s.

        Parameters:
            key : An integer or a slice.
        """
        if isinstance(key, slice):
            return type(self)(len(range(self.n)[key]))
        if key >= self.n or key < -self.n:
            raise IndexError
        return type(self)(1)


class MonoidalCategory[C0: ColouredMonoid, C1: MonoidalCategory](
        Category[C0, C1]):
    """
    A monoidal category is a :class:`Category` with a method :code:`tensor`
    for both its objects and its morphisms.

    This base class also implements syntactic sugar :code:`@` for whiskering.
    """
    @rule
    @abstractmethod
    def tensor[A, B, C, D](
            self: Annotated[C1, Hom[A, B]], other: Annotated[C1, Hom[C, D]]
    ) -> Annotated[C1, Hom[Tensor[A, C], Tensor[B, D]]]:
        """
        Parallel composition, to be instantiated: the rule tensors two
        morphisms, an implementation may take ``n >= 0`` of them.

        Parameters:
            other : The other morphism to compose in parallel.
        """

    @classmethod
    def whisker(cls, other: C0 | C1) -> C1:
        """
        Do nothing if ``other`` is already a morphism else apply :meth:`id`.

        Parameters:
            other : The object or morphism to be tensored on the left or right.
        """
        return (other if isinstance(  # ty: ignore[invalid-return-type]
            other, MonoidalCategory) else cls.id(other))

    def __matmul__(self, other):
        return self.tensor(self.whisker(other))

    def __rmatmul__(self, other):
        return self.whisker(other).tensor(self)

    @axiom
    def bifunctoriality[A, B, C, D, U, V](
            cls, f: Annotated[C1, Hom[A, B]], g: Annotated[C1, Hom[C, D]],
            h: Annotated[C1, Hom[B, U]],
            k: Annotated[C1, Hom[D, V]]) -> Equation[C1]:
        """ Bifunctoriality of the tensor. """
        return cls.Equation(
            f @ g >> h @ k, (f >> h) @ (g >> k))

    @axiom
    def tensor_unitality(
            cls, x: C0, y: C0) -> Equation[C1]:
        """ Preservation of identities by tensor. """
        return cls.Equation(
            cls.id(x) @ cls.id(y), cls.id(x @ y))

    @axiom
    def tensor_dom_typing(
            cls, f: C1, g: C1) -> Equation[C0]:
        """ Domain typing of tensor. """
        return cls.ob.Equation((f @ g).dom, f.dom @ g.dom)

    @axiom
    def tensor_cod_typing(
            cls, f: C1, g: C1) -> Equation[C0]:
        """ Codomain typing of tensor. """
        return cls.ob.Equation((f @ g).cod, f.cod @ g.cod)

    @axiom
    def dagger_monoidality(
            cls, f: C1, g: C1) -> Equation[C1]:
        """ The dagger distributes over the tensor. """
        return cls.Equation((f @ g).dagger(), f.dagger() @ g.dagger())


class PRO[C1: PRO](MonoidalCategory[Nat, C1]):
    """
    A PRO is a :class:`MonoidalCategory` whose objects are the natural
    numbers :class:`Nat`, i.e. the free monoidal category on one generator.
    """


class TracedCategory[C0: ColouredMonoid, C1: TracedCategory](
        MonoidalCategory[C0, C1]):
    """
    A traced category is a :class:`MonoidalCategory` with methods
    :code:`trace_left` and :code:`trace_right` for the partial trace of a
    morphism over some objects on either side.
    """
    @rule
    @abstractmethod
    def trace_left[A, B, M: Atom](
            self: Annotated[C1, Hom[Tensor[M, A], Tensor[M, B]]], n: int = 1
    ) -> Annotated[C1, Hom[A, B]]:
        """
        The trace of ``n`` wires on the left, to be instantiated: as a
        rule, one wire.

        Parameters:
            n : The number of objects to trace over.
        """

    @rule
    @abstractmethod
    def trace_right[A, B, M: Atom](
            self: Annotated[C1, Hom[Tensor[A, M], Tensor[B, M]]], n: int = 1
    ) -> Annotated[C1, Hom[A, B]]:
        """
        The trace of ``n`` wires on the right, to be instantiated: as a
        rule, one wire.

        Parameters:
            n : The number of objects to trace over.
        """

    def trace(self, n: int = 1, left: bool = False) -> C1:
        """
        The trace of a morphism on either side, :meth:`trace_left` or
        :meth:`trace_right`. Tracing no object at all is the identity, i.e.
        the vanishing axiom ``f.trace(0) == f``, see `nLab
        <https://ncatlab.org/nlab/show/traced+monoidal+category>`_.

        Parameters:
            n : The number of objects to trace over.
            left : Whether to trace the wires on the left or right.
        """
        return self.trace_left(n) if left else self.trace_right(n)

    @axiom
    def trace_vanishing(
            cls, f: C1) -> Equation[C1]:
        """ Vanishing of a trace over the unit. """
        return cls.Equation(
            f.trace(0), f, f.trace(0, left=True))

    @axiom
    def trace_superposing_left[A, B, M: Atom](
            cls, f: Annotated[C1, Hom[Tensor[M, A], Tensor[M, B]]],
            x: C0) -> Equation[C1]:
        """ Left-oriented superposing. """
        return cls.Equation(
            (f @ x).trace(left=True), f.trace(left=True) @ x)

    @axiom
    def trace_superposing_right[A, B, M: Atom](
            cls, f: Annotated[C1, Hom[Tensor[A, M], Tensor[B, M]]],
            x: C0) -> Equation[C1]:
        """ Right-oriented superposing. """
        return cls.Equation(
            (x @ f).trace(), x @ f.trace())

    @axiom
    def trace_naturality_left[M: Atom, X, A, B](
            cls, x: Annotated[C0, Tensor[M, X]],
            f: Annotated[C1, Hom[Tensor[M, X, B], Tensor[M, X, A]]],
            g: Annotated[C1, Hom[A, B]]) -> Equation[C1]:
        """ Left-oriented trace naturality. """
        return cls.Equation(
            (x @ g).then(f).then(x @ g).trace(len(x), left=True),
            g.then(f.trace(len(x), left=True)).then(g))

    @axiom
    def trace_naturality_right[M: Atom, X, A, B](
            cls, x: Annotated[C0, Tensor[M, X]],
            f: Annotated[C1, Hom[Tensor[B, M, X], Tensor[A, M, X]]],
            g: Annotated[C1, Hom[A, B]]) -> Equation[C1]:
        """ Right-oriented trace naturality. """
        return cls.Equation(
            (g @ x).then(f).then(g @ x).trace(len(x)),
            g.then(f.trace(len(x))).then(g))

    @axiom
    def trace_dinaturality_left[M: Atom, N: Atom, S, T, A, B](
            cls, f: Annotated[C1, Hom[Tensor[M, S, A], Tensor[N, T, B]]],
            g: Annotated[C1, Hom[Tensor[N, T], Tensor[M, S]]]) -> Equation[C1]:
        """ Left-oriented trace dinaturality. """
        source, target = g.cod, g.dom
        base, cobase = f.dom[len(source):], f.cod[len(target):]
        return cls.Equation(
            f.then(g @ cobase).trace(len(source), left=True),
            (g @ base).then(f).trace(len(target), left=True))

    @axiom
    def trace_dinaturality_right[M: Atom, N: Atom, S, T, A, B](
            cls, f: Annotated[C1, Hom[Tensor[A, M, S], Tensor[B, N, T]]],
            g: Annotated[C1, Hom[Tensor[N, T], Tensor[M, S]]]) -> Equation[C1]:
        """ Right-oriented trace dinaturality. """
        source, target = g.cod, g.dom
        base = f.dom[:-len(source)] if len(source) else f.dom
        cobase = f.cod[:-len(target)] if len(target) else f.cod
        return cls.Equation(
            f.then(cobase @ g).trace(len(source)),
            (base @ g).then(f).trace(len(target)))


class ResiduatedMonoid[C0, C1: ResiduatedMonoid](ColouredMonoid[C0, C1]):
    """
    A monoid is residuated when it comes with methods ``over`` and ``under``
    with syntactic sugar ``<<`` and ``>>``.

    We also assume the exponential objects can be recognised and taken apart,
    see :class:`biclosed.Exp`.
    """
    if TYPE_CHECKING:
        @property
        def is_exp(self) -> bool:
            """ Whether this is an exponential object. """

        @property
        def base(self) -> Self:
            """ The base of an exponential object. """

        @property
        def exponent(self) -> Self:
            """ The exponent of an exponential object. """

    @abstractmethod
    def over(self, other: C1) -> C1:
        """ The right-to-left exponential object ``self`` to the ``other``. """

    @abstractmethod
    def under(self, other: C1) -> C1:
        """ The left-to-right exponential object ``self`` to the ``other``. """

    def __lshift__(self, other):
        return self.over(other)

    def __rshift__(self, other):
        return other.under(self)


class BiclosedCategory[C0: ResiduatedMonoid, C1: BiclosedCategory](
        MonoidalCategory[C0, C1]):
    """
    A biclosed category is a :class:`MonoidalCategory` with methods for the
    evaluation and currying of morphisms on either side.

    We also assume the type for objects comes with methods for left and right
    exponentials :code`x << y` and :code`x >> y`.
    """
    @classmethod
    @generator
    @abstractmethod
    def ev_left[Y: Atom, E: Atom](
            cls, base: Annotated[C0, Y], exponent: Annotated[C0, E]
    ) -> Annotated[C1, Hom[Tensor[Over[Y, E], E], Y]]:
        """
        The left evaluation of an exponential type, to be instantiated:
        as a rule, ``(y << e) @ e ⊢ y``.

        Parameters:
            base : The base of the exponential type.
            exponent : The exponent of the exponential type.
        """

    @classmethod
    @generator
    @abstractmethod
    def ev_right[Y: Atom, E: Atom](
            cls, base: Annotated[C0, Y], exponent: Annotated[C0, E]
    ) -> Annotated[C1, Hom[Tensor[E, Under[E, Y]], Y]]:
        """
        The right evaluation of an exponential type, to be instantiated:
        as a rule, ``e @ (e >> y) ⊢ y``.

        Parameters:
            base : The base of the exponential type.
            exponent : The exponent of the exponential type.
        """

    @classmethod
    def ev(cls, base: C0, exponent: C0, left: bool = True) -> C1:
        """
        The evaluation of an exponential type on either side,
        :meth:`ev_left` or :meth:`ev_right`.

        Parameters:
            base : The base of the exponential type.
            exponent : The exponent of the exponential type.
            left : Whether to take the left or right evaluation.
        """
        return (cls.ev_left if left else cls.ev_right)(base, exponent)

    @rule
    @abstractmethod
    def curry_left[X, Y: Atom, Z](
            self: Annotated[C1, Hom[Tensor[X, Y], Z]], n: int = 1
    ) -> Annotated[C1, Hom[X, Over[Z, Y]]]:
        """
        The currying of ``n`` objects on the left, to be instantiated: as
        a rule, one object.

        Parameters:
            n : The number of objects to curry.
        """

    @rule
    @abstractmethod
    def curry_right[Y: Atom, X, Z](
            self: Annotated[C1, Hom[Tensor[Y, X], Z]], n: int = 1
    ) -> Annotated[C1, Hom[X, Under[Y, Z]]]:
        """
        The currying of ``n`` objects on the right, to be instantiated: as
        a rule, one object.

        Parameters:
            n : The number of objects to curry.
        """

    def curry(self, n: int = 1, left: bool = True) -> C1:
        """
        The currying of a morphism on either side, :meth:`curry_left` or
        :meth:`curry_right`.

        Parameters:
            n : The number of objects to curry.
            left : Whether to curry on the left or right.
        """
        return self.curry_left(n) if left else self.curry_right(n)

    def base_and_exponent(self, n: int, left: bool) -> tuple[C0, C0]:
        """
        The base and exponent that :meth:`uncurry` evaluates, read off the
        exponential object in the codomain.

        Parameters:
            n : The number of objects to uncurry.
            left : Whether to uncurry on the left or right.
        """
        if not self.cod.is_exp:
            raise ValueError
        base, exponent = self.cod.base, self.cod.exponent
        if n < len(exponent):
            raise ValueError
        return base, exponent

    def uncurry(self, n: int = 1, left: bool = True) -> C1:
        """
        Uncurry a morphism by composing it with :meth:`ev`, assuming its
        codomain is an exponential object. If the exponent has less than
        ``n`` objects, we uncurry the remaining ones in turn.

        Parameters:
            n : The number of objects to uncurry.
            left : Whether to uncurry on the left or right.
        """
        if n < 0:
            raise ValueError
        if not n:
            return self  # ty: ignore[invalid-return-type]
        base, exponent = self.base_and_exponent(n, left)
        result = self @ exponent >> self.ev(base, exponent, True) if left\
            else exponent @ self >> self.ev(base, exponent, False)
        return result.uncurry(n - len(exponent), left)

    @classmethod
    def uncurry_composition(
            cls, f: C1, base: C0, exponent: C0, left: bool) -> C1:
        """
        Curry ``f`` then evaluate it back, i.e. whisker the currying with
        ``exponent`` and compose with :meth:`ev`, the roundtrip that
        :meth:`currying_left` and :meth:`currying_right` state equal to
        ``f``.

        Parameters:
            f : The morphism to curry and evaluate back.
            base : The base of the exponential, i.e. the codomain of ``f``.
            exponent : The objects curried out of the domain of ``f``.
            left : Whether to curry on the left or right.
        """
        curried = f.curry(left=left)
        ev = cls.ev(base, exponent, left)
        return (curried @ exponent).then(ev) if left\
            else (exponent @ curried).then(ev)

    @axiom
    def currying_left[A, X: Atom, E: Atom](
            cls, f: Annotated[C1, Hom[Tensor[A, E], X]],
            base: Annotated[C0, X],
            exponent: Annotated[C0, E]) -> Equation[C1]:
        """ Left currying followed by evaluation. """
        return cls.Equation(
            cls.uncurry_composition(f, base, exponent, left=True), f)

    @axiom
    def currying_right[A, X: Atom, E: Atom](
            cls, f: Annotated[C1, Hom[Tensor[E, A], X]],
            base: Annotated[C0, X],
            exponent: Annotated[C0, E]) -> Equation[C1]:
        """ Right currying followed by evaluation. """
        return cls.Equation(
            cls.uncurry_composition(f, base, exponent, left=False), f)


class Pregroup[C0, C1: Pregroup](ResiduatedMonoid[C0, C1]):
    """
    A pregroup is a residuated monoid where the left and right exponentials are
    given by tensoring with the chosen left and right duals for each object.
    """
    @property
    @abstractmethod
    def l(self) -> C1:
        """ The left adjoint, to be instantiated. """

    @property
    @abstractmethod
    def r(self) -> C1:
        """ The right adjoint, to be instantiated. """

    def over(self, other: C1) -> C1:
        return self @ other.l

    def under(self, other: C1) -> C1:
        return other.r @ self

    @axiom
    def adjunction(
            cls, x: C1) -> Equation[C1]:
        """ The left and right adjoints are mutually inverse. """
        return cls.Equation(x.l.r, x, x.r.l)


class RigidCategory[C0: Pregroup, C1: RigidCategory](BiclosedCategory[C0, C1]):
    """
    A rigid category is a :class:`BiclosedCategory` with a :class:`Pregroup` as
    object type and methods for :code:`cups` and :code:`caps`.
    """
    @classmethod
    @generator
    @abstractmethod
    def cups[X: Atom](
            cls, left: Annotated[C0, X], right: Annotated[C0, R[X]]
    ) -> Annotated[C1, Hom[Tensor[X, R[X]], Unit[C0]]]:
        """
        The cups witnessing :code:`right` as the adjoint of :code:`left`:
        as a rule, ``x @ x.r ⊢ 1`` is a cup, ``x.l @ x`` included.

        Parameters:
            left : The left-hand side of the cups.
            right : Its adjoint, i.e. the right-hand side of the cups.
        """

    @classmethod
    @generator
    @abstractmethod
    def caps[X: Atom](
            cls, left: Annotated[C0, X], right: Annotated[C0, L[X]]
    ) -> Annotated[C1, Hom[Unit[C0], Tensor[X, L[X]]]]:
        """
        The caps witnessing :code:`right` as the adjoint of :code:`left`:
        as a rule, ``1 ⊢ x @ x.l`` is a cap, ``x.r @ x`` included.

        Parameters:
            left : The left-hand side of the caps.
            right : Its adjoint, i.e. the right-hand side of the caps.
        """

    @classmethod
    def ev_left(cls, base: C0, exponent: C0) -> C1:
        """ The left evaluation of a rigid morphism is obtained using cups. """
        return base @ cls.cups(exponent.l, exponent)

    @classmethod
    def ev_right(cls, base: C0, exponent: C0) -> C1:
        """ The right evaluation of a rigid morphism, using cups. """
        return cls.cups(exponent, exponent.r) @ base

    def curry_left(self, n: int = 1) -> C1:
        """ The left curry of a rigid morphism is obtained using caps. """
        if n < 0 or n > len(self.dom):
            raise ValueError
        if not n:
            return self  # ty: ignore[invalid-return-type]
        base, exponent = self.dom[:-n], self.dom[-n:]
        return base @ self.caps(exponent, exponent.l) >> self @ exponent.l

    def curry_right(self, n: int = 1) -> C1:
        """ The right curry of a rigid morphism is obtained using caps. """
        if n < 0 or n > len(self.dom):
            raise ValueError
        if not n:
            return self  # ty: ignore[invalid-return-type]
        base, exponent = self.dom[n:], self.dom[:n]
        return self.caps(exponent.r, exponent) @ base >> exponent.r @ self

    def base_and_exponent(self, n: int, left: bool) -> tuple[C0, C0]:
        """
        Contrary to :meth:`BiclosedCategory.base_and_exponent`, a pregroup has
        no exponential object to read the exponent off the codomain: it is the
        ``n`` objects at the end resp. the start of the codomain, dualised.

        Parameters:
            n : The number of objects to uncurry.
            left : Whether to uncurry on the left or right.
        """
        if n > len(self.cod):
            raise ValueError
        if left:
            return self.cod[:-n], self.cod[-n:].r
        return self.cod[n:], self.cod[:n].l

    def transpose(self, left: bool = False) -> C1:
        """
        The transpose of a morphism, i.e. its composition with cups and caps.

        Parameters:
            left : Whether to transpose left or right.

        Example
        -------
        >>> from discopy.monoidal import Equation
        >>> from discopy.rigid import Ty, Box
        >>> x, y = map(Ty, "xy")
        >>> f = Box('f', x, y)
        >>> Equation(f.transpose(left=True), f, f.transpose(),
        ...     symbols=("$\\\\mapsfrom$", "$\\\\mapsto$")).draw(
        ...         figsize=(8, 3), doctest="docs/_static/rigid/transpose.svg")

        .. image:: /_static/rigid/transpose.svg
        """
        if left:
            return self.cod.l @ self.caps(self.dom, self.dom.l)\
                >> self.cod.l @ self @ self.dom.l\
                >> self.cups(self.cod.l, self.cod) @ self.dom.l
        return self.caps(self.dom.r, self.dom) @ self.cod.r\
            >> self.dom.r @ self @ self.cod.r\
            >> self.dom.r @ self.cups(self.cod, self.cod.r)

    @axiom
    def snake_equations(
            cls, x: C0) -> Equation[C1]:
        """ The two snake equations. """
        snake_r = (cls.id(x) @ cls.caps(x.r, x)).then(
            cls.cups(x, x.r) @ cls.id(x))
        snake_l = (cls.caps(x, x.l) @ cls.id(x)).then(
            cls.id(x) @ cls.cups(x.l, x))
        return cls.Equation(snake_r, cls.id(x), snake_l)

    @axiom
    def caps_coherence[M: Atom, N: Atom, X, Y](
            cls, x: Annotated[C0, Tensor[M, X]],
            y: Annotated[C0, Tensor[N, Y]]) -> Equation[C1]:
        """ Monoidal coherence of caps. """
        return cls.Equation(
            cls.caps(x @ y, (x @ y).l),
            cls.caps(x, x.l).then(x @ cls.caps(y, y.l) @ x.l))

    @axiom
    def rotate_contravariance[A, B, C](
            cls, f: Annotated[C1, Hom[A, B]],
            g: Annotated[C1, Hom[B, C]]) -> Equation[C1]:
        """ Rotation reverses composition. """
        return cls.Equation(
            f.then(g).rotate(), g.rotate().then(f.rotate()))


class PivotalCategory[C0: Pregroup, C1: PivotalCategory](
        RigidCategory[C0, C1], TracedCategory[C0, C1]):
    """
    A pivotal category is a :class:`RigidCategory` where the left and right
    adjoints coincide, hence it is also a :class:`TracedCategory`.
    """

    @axiom
    def self_dual(
            cls, x: C0) -> Equation[C0]:
        """ Equality of left and right adjoints. """
        return cls.ob.Equation(x.r, x.l)

    @axiom
    def pivotality(
            cls, f: C1) -> Equation[C1]:
        """ Equality of left and right transposes. """
        dom, cod = f.dom, f.cod
        left_transpose = (cod.l @ cls.caps(dom, dom.l)).then(
            cod.l @ f @ dom.l).then(cls.cups(cod.l, cod) @ dom.l)
        right_transpose = (cls.caps(dom.r, dom) @ cod.r).then(
            dom.r @ f @ cod.r).then(dom.r @ cls.cups(cod, cod.r))
        return cls.Equation(left_transpose, right_transpose)


class BraidedCategory[C0: ColouredMonoid, C1: BraidedCategory](
        MonoidalCategory[C0, C1]):
    """
    A braided category is a :class:`MonoidalCategory` with a method
    :code:`braid` for the natural isomorphism :code:`x @ y -> y @ x`.
    """
    @classmethod
    @generator
    @abstractmethod
    def braid[X: Atom, Y: Atom](
            cls, left: Annotated[C0, X], right: Annotated[C0, Y]
    ) -> Annotated[C1, Hom[Tensor[X, Y], Tensor[Y, X]]]:
        """
        The braid of two objects, to be instantiated: as a rule, ``x @ y
        ⊢ y @ x`` is a braid over.

        Parameters:
            left : The object on the left of the braid.
            right : The object on the right of the braid.
        """

    @classmethod
    @generator
    def braid_inverse[X: Atom, Y: Atom](
            cls, left: Annotated[C0, X], right: Annotated[C0, Y]
    ) -> Annotated[C1, Hom[Tensor[Y, X], Tensor[X, Y]]]:
        """
        The inverse of the braid of two objects, crossing the other way.

        Parameters:
            left : The object on the left of the braid.
            right : The object on the right of the braid.
        """
        return cls.braid(left, right).dagger()

    @axiom
    def hexagon_left[X: Atom, Y: Atom, Z: Atom](
            cls, x: Annotated[C0, X], y: Annotated[C0, Y],
            z: Annotated[C0, Z]) -> Equation[C1]:
        """ The left hexagon equation. """
        return cls.Equation(
            cls.braid(x, y @ z),
            (cls.braid(x, y) @ z).then(y @ cls.braid(x, z)))

    @axiom
    def hexagon_right[X: Atom, Y: Atom, Z: Atom](
            cls, x: Annotated[C0, X], y: Annotated[C0, Y],
            z: Annotated[C0, Z]) -> Equation[C1]:
        """ The right hexagon equation. """
        return cls.Equation(
            cls.braid(x @ y, z),
            (x @ cls.braid(y, z)).then(cls.braid(x, z) @ y))

    @axiom
    def braid_naturality(
            cls, f: C1, g: C1) -> Equation[C1]:
        """ Naturality of the braid. """
        return cls.Equation(
            f @ g >> cls.braid(f.cod, g.cod),
            cls.braid(f.dom, g.dom) >> g @ f)


class PROB[C1: PROB](PRO[C1], BraidedCategory[Nat, C1]):
    """
    A PROB is a :class:`BraidedCategory` whose objects are the natural
    numbers :class:`Nat`, i.e. the free braided category on one generator.
    """


class SymmetricCategory[C0: ColouredMonoid, C1: SymmetricCategory](
        BraidedCategory[C0, C1]):
    """
    A symmetric category is a :class:`BraidedCategory` where the braid is its
    own inverse called :code:`swap` for the symmetry :code:`x @ y -> y @ x`.
    """
    @classmethod
    @generator
    @abstractmethod
    def swap[X: Atom, Y: Atom](
            cls, left: Annotated[C0, X], right: Annotated[C0, Y]
    ) -> Annotated[C1, Hom[Tensor[X, Y], Tensor[Y, X]]]:
        """
        The swap of two objects, to be instantiated: as a rule, ``x @ y ⊢
        y @ x`` is a swap.

        Parameters:
            left : The object on the left of the swap.
            right : The object on the right of the swap.
        """

    @classmethod
    def permutation(cls, xs: Sequence[int], doms: Sequence[C0]) -> C1:
        """ Compose swaps to permute the atomic objects in ``dom``. """
        xs, doms = list(xs), list(doms)
        if list(range(len(doms))) != sorted(xs):
            raise ValueError
        tensor = lambda objects: cls.ob().tensor(*objects)
        result, done = cls.id(tensor(doms)), cls.ob()
        while xs != list(range(len(xs))):
            i = xs[0]
            left, head = tensor(doms[:i]), tensor(doms[i:i + 1])
            result >>= done @ cls.swap(left, head) @ tensor(doms[i + 1:])
            done, doms = done @ head, doms[:i] + doms[i + 1:]
            xs = [x - 1 if x > i else x for x in xs[1:]]
        return result

    @classmethod
    def braid(cls, left: C0, right: C0) -> C1:
        return cls.swap(left, right)

    @axiom
    def swap_inverse(
            cls, x: C0, y: C0) -> Equation[C1]:
        """ Involutivity of the swap. """
        return cls.Equation(
            cls.swap(x, y).then(cls.swap(y, x)), cls.id(x @ y))


class PROP[C1: PROP](PROB[C1], SymmetricCategory[Nat, C1]):
    """
    A PROP is a :class:`SymmetricCategory` whose objects are the natural
    numbers :class:`Nat`, i.e. the free symmetric category on one generator.
    """


class MarkovCategory[C0: ColouredMonoid, C1: MarkovCategory](
        SymmetricCategory[C0, C1]):
    """
    A Markov category is a :class:`SymmetricCategory` with methods
    :code:`copy` and :code:`merge` for the supply of commutative comonoids.
    """
    @classmethod
    @generator
    @abstractmethod
    def copy[X: Atom, N: Count](
            cls, x: Annotated[C0, X], n: Annotated[int, N]
    ) -> Annotated[C1, Hom[X, Repeat[X, N]]]:
        """
        Make :code:`n` copies of a given object :code:`x`: as a rule,
        ``x ⊢ x @ .. @ x`` is a copy, none or up to three drawn.

        Parameters:
            x : The object to copy.
            n : The number of copies, two by default in implementations.
        """

    @classmethod
    @generator
    def merge[X: Atom, N: Count](
            cls, x: Annotated[C0, X], n: Annotated[int, N]
    ) -> Annotated[C1, Hom[Repeat[X, N], X]]:
        """
        Merge :code:`n` copies of a given object :code:`x`, the dagger of
        :meth:`copy`.

        Parameters:
            x : The object to merge.
            n : The number of copies, two by default in implementations.
        """
        return cls.copy(x, n).dagger()

    @axiom
    def copy_counitality(
            cls, x: C0) -> Equation[C1]:
        """ Counitality of copying. """
        copy, discard = cls.copy(x), cls.copy(x, n=0)
        return cls.Equation(
            copy.then(discard @ x), cls.id(x),
            copy.then(x @ discard))

    @axiom
    def copy_coassociativity(
            cls, x: C0) -> Equation[C1]:
        """ Coassociativity of copying. """
        copy = cls.copy(x)
        return cls.Equation(
            copy.then(copy @ x), copy.then(x @ copy))

    @axiom
    def copy_cocommutativity(
            cls, x: C0) -> Equation[C1]:
        """ Cocommutativity of copying. """
        copy = cls.copy(x)
        return cls.Equation(copy.then(cls.swap(x, x)), copy)

    @axiom
    def discard_coherence(
            cls, x: C0) -> Equation[C1]:
        """ Monoidal coherence of discarding. """
        return cls.Equation(
            cls.copy(x @ x, n=0),
            cls.copy(x, n=0) @ cls.copy(x, n=0))

    @axiom
    def copy_monoidal_coherence(
            cls, x: C0) -> Equation[C1]:
        """ Monoidal coherence of copying. """
        return cls.Equation(
            cls.copy(x @ x),
            (cls.copy(x) @ cls.copy(x)).then(
                x @ cls.swap(x, x) @ x))


class ClosedCategory[C0: ResiduatedMonoid, C1: ClosedCategory](
        BiclosedCategory[C0, C1], MarkovCategory[C0, C1]):
    """
    A closed category is a symmetric :class:`BiclosedCategory`. We also assume
    it comes with copy and discard so it is also a :class:`MarkovCategory`.
    """


class DelayedMonoid[C0, C1: DelayedMonoid](ColouredMonoid[C0, C1]):
    """
    A delayed monoid is a coloured monoid with a :meth:`delay` endomorphism,
    the objects of a :class:`FeedbackCategory`: the memory it feeds back
    is one time step later on the way in, shortened to :attr:`d`.
    """
    @abstractmethod
    def delay(self, n_steps: int = 1) -> C1:
        """
        The delay of an object by some time steps, to be instantiated.

        Parameters:
            n_steps : The number of time steps to delay.
        """

    @property
    def d(self) -> C1:
        """ Syntactic sugar for :meth:`delay` by one time step. """
        return self.delay()


class FeedbackCategory[C0: DelayedMonoid, C1: FeedbackCategory](
        MarkovCategory[C0, C1]):
    """
    A feedback category is a :class:`MarkovCategory` whose objects are a
    :class:`DelayedMonoid`, with a :code:`delay` endofunctor and a
    :code:`feedback` operator.
    """
    @abstractmethod
    def delay(self, n_steps: int = 1) -> C1:
        """
        The delay endofunctor applied to a morphism.

        Parameters:
            n_steps : The number of time steps to delay.
        """

    @rule
    @abstractmethod
    def feedback_left[A, B, M: Atom](
            self: Annotated[C1, Hom[Tensor[Delay[M], A], Tensor[M, B]]],
            dom: C0 | None = None, cod: C0 | None = None,
            mem: C0 | None = None) -> Annotated[C1, Hom[A, B]]:
        """
        The feedback of the memory on the left, to be instantiated: as a
        rule, one wire of memory.

        Parameters:
            dom : The domain of the feedback.
            cod : The codomain of the feedback.
            mem : The memory type to feed back.
        """

    @rule
    @abstractmethod
    def feedback_right[A, B, M: Atom](
            self: Annotated[C1, Hom[Tensor[A, Delay[M]], Tensor[B, M]]],
            dom: C0 | None = None, cod: C0 | None = None,
            mem: C0 | None = None) -> Annotated[C1, Hom[A, B]]:
        """
        The feedback of the memory on the right, to be instantiated: as a
        rule, one wire of memory.

        Parameters:
            dom : The domain of the feedback.
            cod : The codomain of the feedback.
            mem : The memory type to feed back.
        """

    def feedback(self, dom: C0 | None = None, cod: C0 | None = None,
                 mem: C0 | None = None, left: bool = False) -> C1:
        """
        The feedback operator on either side, :meth:`feedback_left` or
        :meth:`feedback_right`.

        Parameters:
            dom : The domain of the feedback.
            cod : The codomain of the feedback.
            mem : The memory type to feed back.
            left : Whether the memory is on the left or right.
        """
        side = self.feedback_left if left else self.feedback_right
        return side(dom, cod, mem)

    @axiom
    def feedback_vanishing(
            cls, f: C1) -> Equation[C1]:
        """ Vanishing of feedback over the unit. """
        return cls.Equation(f.feedback(mem=cls.ob()), f)

    @axiom
    def feedback_joining[X, M: Atom, N: Atom](
            cls, f: Annotated[C1, Hom[
                Tensor[X, Delay[Tensor[M, N]]], Tensor[X, M, N]]]
    ) -> Equation[C1]:
        """ Joining nested feedback loops. """
        return cls.Equation(
            f.feedback(mem=f.cod[-2:]), f.feedback().feedback())

    dagger_involution = Category.dagger_involution.inapplicable(
        "The delay of a feedback category is not reversible.")

    dagger_contravariance = Category.dagger_contravariance.inapplicable(
        "The delay of a feedback category is not reversible.")

    dagger_monoidality = MonoidalCategory.dagger_monoidality.inapplicable(
        "The delay of a feedback category is not reversible.")


class BalancedCategory[C0: ColouredMonoid, C1: BalancedCategory](
        BraidedCategory[C0, C1], TracedCategory[C0, C1]):
    """
    A balanced category is a :class:`BraidedCategory` and a
    :class:`TracedCategory` with a method :code:`twist` for the natural
    automorphism :code:`x -> x`.
    """
    @classmethod
    @generator
    @abstractmethod
    def twist[X: Atom](
            cls, dom: Annotated[C0, X]) -> Annotated[C1, Hom[X, X]]:
        """
        The twist on an object, to be instantiated. As a rule, ``x ⊢ x``
        is a twist.

        Parameters:
            dom : The object on which to take the twist.
        """

    @axiom
    def balanced_twist[X: Atom, Y: Atom](
            cls, x: Annotated[C0, X],
            y: Annotated[C0, Y]) -> Equation[C1]:
        """ Compatibility of the twist and braid. """
        return cls.Equation(
            cls.twist(x @ y),
            cls.braid(x, y).then(
                cls.twist(y) @ cls.twist(x)).then(
                    cls.braid(y, x)))


class RibbonCategory[C0: Pregroup, C1: RibbonCategory](
        PivotalCategory[C0, C1], BalancedCategory[C0, C1]):
    """
    A ribbon category is a :class:`PivotalCategory` which is also a
    :class:`BalancedCategory`, i.e. where diagrams can draw knots and links.
    """

    @axiom
    def twist_as_trace[X: Atom](
            cls, x: Annotated[C0, X]) -> Equation[C1]:
        """ The twist as both orientations of a traced braid. """
        braid = cls.braid(x, x)
        return cls.Equation(
            braid.trace(left=True), cls.twist(x), braid.trace())


class CompactCategory[C0: Pregroup, C1: CompactCategory](
        RibbonCategory[C0, C1], SymmetricCategory[C0, C1]):
    """
    A compact category is a :class:`RibbonCategory` which is also a
    :class:`SymmetricCategory`, i.e. with cups, caps and swaps and where
    the twist is the identity.
    """
    @classmethod
    @inapplicable("The twist is the identity.")
    def twist(cls, dom: C0) -> C1:
        return cls.id(dom)

    @axiom
    def reidemeister_1_cap(
            cls, x: C0) -> Equation[C1]:
        """ Reidemeister move 1 for caps. """
        return cls.Equation(
            cls.caps(x, x.r).then(cls.swap(x, x.r)),
            cls.caps(x.r, x))

    @axiom
    def reidemeister_1_cup(
            cls, x: C0) -> Equation[C1]:
        """ Reidemeister move 1 for cups. """
        return cls.Equation(
            cls.swap(x, x.r).then(cls.cups(x.r, x)),
            cls.cups(x, x.r))


class HypergraphCategory[C0: Pregroup, C1: HypergraphCategory](
        CompactCategory[C0, C1], MarkovCategory[C0, C1]):
    """
    A hypergraph category is a symmetric category with a supply of spiders,
    i.e. special commutative Frobenius algebras on each objects.

    This makes it both a :class:`CompactCategory` and a :class:`MarkovCategory`
    """
    @classmethod
    @generator
    @abstractmethod
    def spiders[X: Atom, M: Count, N: Count](
            cls, n_legs_in: Annotated[int, M],
            n_legs_out: Annotated[int, N],
            typ: Annotated[C0, X]
    ) -> Annotated[C1, Hom[Repeat[X, M], Repeat[X, N]]]:
        """
        The spiders on a given type with ``n_legs_in`` and ``n_legs_out``:
        as a rule, ``x @ .. @ x ⊢ x @ .. @ x`` is a spider, on up to three
        legs a side drawn.

        Parameters:
            n_legs_in : The number of legs in for each spider.
            n_legs_out : The number of legs out for each spider.
            typ : The type of the spiders.
        """
