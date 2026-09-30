# -*- coding: utf-8 -*-

"""
The delooping of a monoidal category: the two-category with one
0-cell, the objects as 1-cells and the arrows as 2-cells, where the
horizontal composition is the tensor and the interchange law is
:meth:`discopy.abc.MonoidalCategory.bifunctoriality`.

``Deloop[C]`` is parameterised by the monoidal category ``C`` the way
:class:`discopy.hypergraph.Hypergraph` is by the category it hosts: a
2-cell wraps an arrow of ``C`` and a :class:`Cell` wraps an object, so
that the operators of the two-category read off the pattern language —
1-cells compose with ``>>`` — while everything is computed by ``C``.
Its search delegates to the strategy of ``C`` and its equations to the
:class:`Equation` of ``C``, so the laws of
:class:`discopy.abc.TwoCategory` are checked on every monoidal level
by the same terms and quotients that check its monoidal laws.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Cell
    Deloop
"""

from dataclasses import dataclass
from typing import Annotated

from discopy import (
    balanced, biclosed, braided, closed, compact, feedback, frobenius,
    markov, monoidal, pivotal, ribbon, rigid, symmetric, traced)
from discopy.abc import TwoCategory
from discopy.pattern import Compose, Hom, Ob
from discopy.search import rule
from discopy.utils import (
    NamedGeneric, assert_isinstance, classproperty, unbiased)


@dataclass(frozen=True)
class Cell[category](NamedGeneric):
    """
    A 1-cell of a delooping: an object of the category, composing by
    its tensor along the one 0-cell.

    Parameters:
        inside : The object of the category.

    >>> from discopy.monoidal import Ty
    >>> x, y = Monoidal.ob(Ty('x')), Monoidal.ob(Ty('y'))
    >>> assert x >> y == Monoidal.ob(Ty('x') @ Ty('y'))
    >>> assert len(x >> y) == 2 and (x >> y)[:1] == x
    """

    inside: monoidal.Ty

    def __post_init__(self):
        if self.category is not None:
            assert_isinstance(self.inside, self.category.ob)

    def __rshift__(self, other: Cell) -> Cell:
        assert_isinstance(other, type(self))
        return type(self)(self.inside @ other.inside)

    def __len__(self):
        return len(self.inside)

    def __getitem__(self, key) -> Cell:
        return type(self)(self.inside[key])

    @classmethod
    def strategy(cls, **params):
        """ The objects of the category, wrapped. """
        if cls.category is None:
            raise NotImplementedError(
                f"No search strategy implemented for {cls.__name__}")
        return cls.category.ob.strategy(**params).map(cls)

    @classproperty
    def Equation(cls):  # noqa: N802
        """ The equations of the category's objects, on those inside. """
        equation = cls.category.ob.Equation

        def build(*terms, **params):
            return equation(*(term.inside for term in terms), **params)
        return build


@dataclass(frozen=True)
class Deloop[category](NamedGeneric, TwoCategory):
    """
    A 2-cell of a delooping: an arrow of the category, composed
    vertically by its composition and horizontally by its tensor.

    Parameters:
        inside : The arrow of the category.

    >>> from discopy.monoidal import Ty, Box
    >>> f = Box('f', Ty('x'), Ty('y'))
    >>> a = Monoidal(f)
    >>> b = Monoidal(Box('g', Ty('y'), Ty('x')))
    >>> assert a.dom == Monoidal.ob(Ty('x'))
    >>> assert a.compose(a).inside == f @ f
    >>> assert Monoidal.interchange(a, b, a, b)
    """

    inside: monoidal.Diagram

    def __post_init__(self):
        if self.category is not None:
            assert_isinstance(self.inside, self.category)

    @classproperty
    def ob(cls) -> type:  # ty: ignore[invalid-attribute-override]
        """ The 1-cells, the objects of the category wrapped. """
        return Cell[cls.category]

    @property
    def dom(self) -> Cell:
        """ The 1-cell the 2-cell goes from. """
        return type(self).ob(self.inside.dom)

    @property
    def cod(self) -> Cell:
        """ The 1-cell the 2-cell goes to. """
        return type(self).ob(self.inside.cod)

    @classmethod
    @rule
    def id[F](cls, dom: Annotated[Cell, Ob(F)]
              ) -> Annotated[Deloop, Hom(F, F)]:
        """ The identity 2-cell on a 1-cell. """
        return cls(cls.category.id(dom.inside))

    @rule
    @unbiased
    def then[F, G, H](
            self: Annotated[Deloop, Hom(F, G)],
            other: Annotated[Deloop, Hom(G, H)]
    ) -> Annotated[Deloop, Hom(F, H)]:
        """ The vertical composition along a shared 1-cell. """
        assert_isinstance(other, type(self))
        return type(self)(self.inside >> other.inside)

    def __rshift__(self, other: Deloop) -> Deloop:
        return self.then(other)

    @rule
    def compose[F, G, H, K](
            self: Annotated[Deloop, Hom(F, G)],
            other: Annotated[Deloop, Hom(H, K)]
    ) -> Annotated[Deloop, Hom(
            Compose(Ob(F), Ob(H)), Compose(Ob(G), Ob(K)))]:
        """ The horizontal composition along the one 0-cell. """
        assert_isinstance(other, type(self))
        return type(self)(self.inside @ other.inside)

    @classproperty
    def Equation(cls):  # noqa: N802  # ty: ignore[invalid-attribute-override]
        """ The equations of the category, on the arrows inside. """
        equation = cls.category.Equation

        def build(*terms, **params):
            return equation(*(term.inside for term in terms), **params)
        return build

    @classmethod
    def strategy(cls, *, dom: Cell | None = None, cod: Cell | None = None,
                 **params):
        """ The strategy of the category, wrapped, its goal unwrapped. """
        if cls.category is None:
            raise NotImplementedError(
                f"No search strategy implemented for {cls.__name__}")
        goal = tuple(
            None if side is None else side.inside for side in (dom, cod))
        return cls.category.strategy(
            dom=goal[0], cod=goal[1], **params).map(cls)

    interchange = TwoCategory.interchange.modulo(
        monoidal.Diagram.normal_form).weaken(boundary_connected=True)


class Monoidal(Deloop):
    """ The delooping of :class:`discopy.monoidal.Diagram`. """
    category = monoidal.Diagram


class Braided(Deloop):
    """ The delooping of :class:`discopy.braided.Diagram`. """
    category = braided.Diagram


class Balanced(Deloop):
    """ The delooping of :class:`discopy.balanced.Diagram`. """
    category = balanced.Diagram


class Symmetric(Deloop):
    """ The delooping of :class:`discopy.symmetric.Diagram`. """
    category = symmetric.Diagram
    interchange = TwoCategory.interchange


class Markov(Deloop):
    """ The delooping of :class:`discopy.markov.Diagram`. """
    category = markov.Diagram
    interchange = TwoCategory.interchange


class Traced(Deloop):
    """ The delooping of :class:`discopy.traced.Diagram`. """
    category = traced.Diagram


class Closed(Deloop):
    """ The delooping of :class:`discopy.closed.Diagram`. """
    category = closed.Diagram
    interchange = TwoCategory.interchange


class Biclosed(Deloop):
    """ The delooping of :class:`discopy.biclosed.Diagram`. """
    category = biclosed.Diagram


class Rigid(Deloop):
    """ The delooping of :class:`discopy.rigid.Diagram`. """
    category = rigid.Diagram


class Pivotal(Deloop):
    """ The delooping of :class:`discopy.pivotal.Diagram`. """
    category = pivotal.Diagram


class Ribbon(Deloop):
    """ The delooping of :class:`discopy.ribbon.Diagram`. """
    category = ribbon.Diagram


class Compact(Deloop):
    """ The delooping of :class:`discopy.compact.Diagram`. """
    category = compact.Diagram
    interchange = TwoCategory.interchange


class Frobenius(Deloop):
    """ The delooping of :class:`discopy.frobenius.Diagram`. """
    category = frobenius.Diagram
    interchange = TwoCategory.interchange


class Feedback(Deloop):
    """ The delooping of :class:`discopy.feedback.Diagram`. """
    category = feedback.Diagram
    interchange = TwoCategory.interchange
