# -*- coding: utf-8 -*-

"""
The free Markov category, i.e. a semicartesian category with a supply of
commutative comonoid, see :cite:t:`FritzLiang23`.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Diagram
    Box
    Swap
    Permutation
    Copy
    Feedback
    Trace
    FollowedBy
    Head
    Tail
    Functor


Axioms
------

>>> x = Ty('x')

>>> copy, delete = Copy(x), Copy(x, n=0)

Cocommutative comonoid
======================

>>> counitality = Equation(copy >> delete @ x, Id(x), copy >> x @ delete)
>>> coassociativity = Equation(copy >> copy @ x, copy >> x @ copy)
>>> cocommutativity = Equation(copy >> Swap(x, x), copy)
>>> assert counitality and coassociativity and cocommutativity
>>> Equation(counitality, coassociativity, cocommutativity, symbol='').draw(
...     doctest="docs/_static/frobenius/comonoid.svg")

.. image:: /_static/frobenius/comonoid.svg
    :align: center

Coherence
=========

>>> assert Equation(Diagram.copy(x @ x, n=0), delete @ delete)
>>> assert Equation(Diagram.copy(x @ x),
...     copy @ copy >> x @ Swap(x, x) @ x)

Note
----
Equality of Markov diagrams is computed by translation to hypergraph.
Copy boxes are translated to spiders, thus when they appear in the same
diagram as the merge boxes of :mod:`comarkov` they automatically satisfy
the :mod:`frobenius` axioms.
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, ClassVar

from discopy import symmetric, monoidal, feedback, cmap, hypergraph, messages
from discopy.abc import ComarkovCategory, MarkovCategory
from discopy.axioms import FUEL
from discopy.cat import factory
from discopy.feedback import (  # noqa: F401  pylint: disable=unused-import
    Wire, Ty)
from discopy.utils import (
    AxiomError, assert_isatomic, deprecated_alias, factory_name, from_tree)

if TYPE_CHECKING:
    from discopy import comarkov


Layer = symmetric.Layer


@factory
class Diagram(symmetric.Diagram, MarkovCategory):
    """
    A Markov diagram is a symmetric diagram with :class:`Copy` boxes.

    Parameters:
        inside(Layer) : The layers inside the diagram.
        dom (monoidal.Ty) : The domain of the diagram, i.e. its input.
        cod (monoidal.Ty) : The codomain of the diagram, i.e. its output.

    Note
    ----
    We can create arbitrary Markov diagrams with the standard notation for
    Python functions.

    >>> x = Ty('x')
    >>> f = Box('f', x, x)

    >>> copy_then_apply = Diagram.from_callable(x, x @ x)(
    ...     lambda x: (f(x), f(x)))

    >>> @Diagram.from_callable(x, x @ x)
    ... def apply_then_copy(x):
    ...     y = f(x)
    ...     return y, y

    >>> Equation(copy_then_apply, apply_then_copy, symbol="$\\\\neq$").draw(
    ...     doctest="docs/_static/markov/copy_and_apply.svg")

    .. image:: /_static/markov/copy_and_apply.svg

    Note
    ----
    A Markov diagram is a feedback diagram whose wires carry a time step, so
    that it is the syntax of streams, see :mod:`discopy.stream`.

    >>> x = Ty('x')
    >>> zero = Box('0', Ty(), x.head)
    >>> rand = Box('rand', Ty(), x)
    >>> plus = Box('+', x @ x, x)
    >>> walk = (rand.delay() @ x.delay() >> zero @ plus.delay()
    ...         >> FollowedBy(x) >> Copy(x)).feedback()
    >>> walk.draw(doctest="docs/_static/feedback/feedback-random-walk.svg")

    .. image:: /_static/feedback/feedback-random-walk.svg
        :align: center
    """
    copy_factory: ClassVar[type["Copy"]]
    discard_factory: ClassVar[type["Discard"]]

    @classmethod
    def sample(cls, *, dom=None, cod=None, fuel=FUEL):
        """
        Sample Markov diagrams through their quotient: a hypergraph drawn
        by :meth:`discopy.hypergraph.Hypergraph.strategy` with at most
        ``fuel + 1`` boxes, besides the one balancing box that may close its
        boundary, and the spiders that the category supports, i.e.
        copies and discards here and every spider in a hypergraph category,
        downgraded with :meth:`discopy.hypergraph.Hypergraph.to_diagram`.
        """
        category = hypergraph.Hypergraph[cls]  # ty: ignore[invalid-type-form]
        return category.strategy(
            dom=dom, cod=cod, max_leaves=fuel + 1).map(
                lambda graph: graph.to_diagram())

    @classmethod
    def spider_factory(cls, n_legs_in, n_legs_out, typ, phase=None):
        if phase is not None or n_legs_in != 1:
            raise ValueError(messages.NO_SUCH_SPIDER.format(
                factory_name(cls), "copies"))
        return cls.copy_factory(typ, n_legs_out)

    @classmethod
    def copy(cls, x: monoidal.Ty, n=2) -> Diagram:
        """
        Make :code:`n` copies of a given type :code:`x`.

        Parameters:
            x : The type to copy.
            n : The number of copies.
        """
        from discopy import frobenius
        return frobenius.Diagram.spiders.__func__(
            cls, 1, n, x)  # ty: ignore[invalid-argument-type]

    @classmethod
    def discard(cls, x: monoidal.Ty) -> Diagram:
        """
        The discard of a type :code:`x`, i.e. no copy of it at all.

        Parameters:
            x : The type to discard.
        """
        return cls.copy(x, 0)

    map_agreement = monoidal.Diagram.map_agreement.failing(
        messages.MAP_HAS_NO_SPIDERS)

    @classmethod
    def merge(cls, x: monoidal.Ty, n=2) -> Diagram | comarkov.Diagram:
        """
        Deprecated: a Markov diagram has no merge, see
        :meth:`discopy.comarkov.Diagram.merge`, which a diagram that is
        also comarkov, e.g. :class:`discopy.frobenius.Diagram`, inherits.

        Parameters:
            x : The type to merge.
            n : The number of copies.
        """
        if issubclass(cls, ComarkovCategory):
            return super().merge(x, n)
        warnings.warn(
            f"{factory_name(cls)}.merge is deprecated, "
            "use discopy.comarkov.Diagram.merge instead.",
            DeprecationWarning, stacklevel=2)
        from discopy import comarkov
        return comarkov.Diagram.merge(x, n)


class Box(symmetric.Box, Diagram):
    """
    A Markov box is a symmetric box in a Markov diagram.

    Parameters:
        name (str) : The name of the box.
        dom (monoidal.Ty) : The domain of the box, i.e. its input.
        cod (monoidal.Ty) : The codomain of the box, i.e. its output.
    """


class Permutation(symmetric.Permutation, Box):
    """
    A permutation in a Markov category.

    Parameters:
        dom (monoidal.Ty) : The domain, i.e. the wires to permute.
        perm : The permutation as a :class:`finset.Permutation` or a list.
    """


class Swap(Permutation, symmetric.Swap, Box):
    """
    Symmetric swap in a Markov diagram.

    Parameters:
        left (monoidal.Ty) : The type on the top left and bottom right.
        right (monoidal.Ty) : The type on the top right and bottom left.
    """


class Copy(Box):
    """
    The copy of an atomic type :code:`x` some :code:`n` number of times.

    Parameters:
        x : The type to copy.
        n : The number of copies.
    """
    def __init__(self, x: monoidal.Ty, n: int = 2):
        assert_isatomic(x, monoidal.Ty)
        name = f"Copy({x}" + ("" if n == 2 else f", {n}") + ")"
        Box.__init__(self, name, dom=x, cod=x ** n,
                     draw_as_spider=True, color="black", drawing_name="")

    def __new__(cls, x: monoidal.Ty, n: int = 2):
        return super().__new__(cls) if n else\
            cls.discard_factory.__new__(cls.discard_factory, x)

    def __getnewargs__(self):
        """
        The arguments of :meth:`__new__`, which a pickle needs.

        >>> from pickle import dumps, loads
        >>> x = Ty('x')
        >>> assert loads(dumps(Copy(x))) == Copy(x)
        >>> assert loads(dumps(Discard(x))) == Discard(x)
        """
        return self.dom, len(self.cod)

    def dagger(self) -> Diagram:
        """
        The merge of the same type, when the category is also comarkov.

        >>> from discopy import closed
        >>> closed.Copy(closed.Ty('x')).dagger()
        Traceback (most recent call last):
            ...
        discopy.utils.AxiomError: Copy(x) has no dagger: closed.Diagram \
is not a dagger category.
        """
        if not issubclass(self.ar, ComarkovCategory):
            raise AxiomError(messages.NOT_A_DAGGER.format(
                self, factory_name(self.ar)))
        return self.ar.merge_factory(self.dom, len(self.cod))

    def __repr__(self):
        return (
            factory_name(type(self)) + f"({repr(self.dom)}, {len(self.cod)})")

    @classmethod
    def from_tree(cls, tree: dict) -> Copy:
        return cls(from_tree(tree['dom']), len(from_tree(tree['cod'])))


class Discard(Copy):
    """
    The discard of an atomic type :code:`x`.

    Parameters:
        x : The type to discard.
    """
    def __init__(self, x: monoidal.Ty, n: int = 0):
        if n:
            raise ValueError(f"A discard has no copies, got n={n}.")
        super().__init__(x, 0)


class Sum(symmetric.Sum, Box):
    """
    A markov sum is a symmetric sum and a markov box.

    Parameters:
        terms (tuple[Diagram, ...]) : The terms of the formal sum.
        dom (Ty) : The domain of the formal sum.
        cod (Ty) : The codomain of the formal sum.
    """


class Functor(symmetric.Functor):
    """
    A Markov functor is a symmetric functor that preserves copies.

    Parameters:
        ob_map (Mapping[monoidal.Ty, monoidal.Ty]) :
            Map from :class:`monoidal.Ty` to :code:`cod.ob`.
        ar_map (Mapping[Box, Diagram]) : Map from :class:`Box` to :code:`cod`.
        cod (Category) :
            The codomain, :code:`Diagram` by default.

    Example
    -------

    We build a functor into python functions.

    >>> x = Ty('x')
    >>> add = Box('add', x @ x, x)
    >>> from discopy import python
    >>> F = Functor({x: int}, {add: lambda a, b: a + b},
    ...             cod=python.Function)
    >>> copy = Copy(x)
    >>> bialgebra_l = copy @ copy >> Id(x) @ Swap(x, x) @ Id(x) >> add @ add
    >>> bialgebra_r = add >> copy
    >>> assert F(bialgebra_l)(54, 46) == F(bialgebra_r)(54, 46)

    >>> Equation(bialgebra_l, bialgebra_r, symbol="=").draw(
    ...     doctest="docs/_static/markov/bialgebra.svg")

    .. image:: /_static/markov/bialgebra.svg
    """
    dom = cod = Diagram

    def __call__(self, other):
        if isinstance(other, Copy) and hasattr(self.cod, "copy"):
            return self.cod.copy(self(other.dom), len(other.cod))
        return super().__call__(other)


CMap = cmap.CMap[Diagram]

Feedback, Trace, FollowedBy, Head, Tail = feedback.generators(Diagram, Box)
Diagram.box_factory = Box
Diagram.functor_factory = Functor
Hypergraph = hypergraph.Hypergraph[Diagram]
Diagram.copy_factory = Copy
Diagram.swap_factory = Swap
Diagram.permutation_factory = Permutation
Diagram.discard_factory = Discard
Diagram.sum_factory = Sum
Id = Diagram.id


class Equation(symmetric.Equation):
    """ The :class:`symmetric.Equation` of Markov diagrams. """
    up_to = staticmethod(Diagram.to_hypergraph)


__getattr__ = deprecated_alias(__name__, {"Merge": "discopy.comarkov.Merge"})
