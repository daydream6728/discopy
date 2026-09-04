# -*- coding: utf-8 -*-

"""
Shapes as computads, sampling as Kleisli morphisms, derivation as a functor.

A shape is a finitely presented category: generating objects, and generating
boxes whose ``dom`` and ``cod`` are words over them, written in the free
category of the doctrine the shape needs — plain :mod:`discopy.monoidal`
types for a composable pair, :meth:`discopy.feedback.Ob.delay` in the words
of a feedback shape, exponentials in those of a currying one. An instance of
a shape in a carrier is a :class:`Model`, i.e. a functor from the shape to
the carrier: the boundary conditions the old testing classes checked in
``__new__`` are exactly the typing of that functor, stated once in
:meth:`Model.__init__`.

Sampling is effectful, so it lives in the Kleisli category of the
``SearchStrategy`` monad: :class:`Sample`, a Markov category whose arrows
take values and return a search strategy of values — ``st.just`` is the
unit, ``flatmap`` the bind and ``st.tuples`` the strength, lawful up to
distribution, which is all sampling needs. Deriving the search strategy of
a shape happens in two stages, the way ``STYLE.md`` prescribes that diagram
composition stays pure while functor application may be effectful:

- :meth:`Shape.sampling` builds a :class:`discopy.markov.Diagram`, the
  *plan*: one :class:`DrawOb` per generating object not bound to a
  parameter, copies wiring each object into every word that mentions it,
  one :class:`DrawAr` per free generating box with its boundaries as
  inputs, a :class:`Pure` box per derived cell, and a final :class:`Pure`
  packing the images into a :class:`Model`. The plan is an ordinary
  diagram: ``shape.sampling().draw()`` shows the sampler.
- :func:`sampler` is a :class:`discopy.markov.Functor` into :class:`Sample`
  evaluating the plan to a Kleisli morphism, whose application to the bound
  parameters is the ``SearchStrategy`` of models.

Every arrow is drawn with fully determined boundaries, so the derived
strategies do no rejection filtering outside the sorts of the generators.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Sample
    Shape
    Model
    DrawOb
    DrawAr
    Pure

.. admonition:: Functions

    .. autosummary::
        :template: function.rst
        :nosignatures:
        :toctree:

        sampler
        send
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Mapping
from functools import partial
from typing import TYPE_CHECKING

from discopy import markov, monoidal
from discopy.abc import Category, MarkovCategory
from discopy.utils import (
    AxiomError, assert_iscomposable, assert_isinstance, factory, tuplify,
    untuplify)

if TYPE_CHECKING:
    from hypothesis import strategies as st


Ty = tuple[type, ...]
""" Kleisli arrows have tuples of types as input and output. """


@factory
class Sample(MarkovCategory):
    """
    The Kleisli category of the ``SearchStrategy`` monad: a morphism takes
    values in ``dom`` and returns a search strategy of values in ``cod``.

    Parameters:
        inside : A callable from ``dom`` values to a ``SearchStrategy`` of
            ``cod`` values, untuplified like a
            :class:`discopy.python.Function`.
        dom : The tuple of input types.
        cod : The tuple of output types.

    Example
    -------
    >>> from hypothesis import strategies as st, find
    >>> dice = Sample(lambda: st.integers(1, 6), (), (int, ))
    >>> add = Sample.pure(lambda x, y: x + y, (int, int), (int, ))
    >>> pair = Sample.copy((int, ), 2) >> add
    >>> assert find((dice >> pair)(), lambda n: n % 2 == 0) == 2
    """
    inside: Callable
    dom: Ty
    cod: Ty

    ob = Ty

    def __init__(self, inside: Callable, dom: Ty, cod: Ty):
        self.inside, self.dom, self.cod = inside, tuplify(dom), tuplify(cod)

    def __call__(self, *xs) -> "st.SearchStrategy":
        return self.inside(*xs)

    @classmethod
    def pure(cls, function: Callable, dom: Ty, cod: Ty) -> Sample:
        """ The unit of the monad, embedding a deterministic function. """
        from hypothesis import strategies as st

        return cls(lambda *xs: st.just(function(*xs)), dom, cod)

    @classmethod
    def id(cls, dom: Ty = ()) -> Sample:
        return cls.pure(lambda *xs: untuplify(xs), dom, dom)

    def then(self, other: Sample) -> Sample:
        """ Kleisli composition, i.e. ``flatmap``. """
        assert_isinstance(other, type(self))
        assert_iscomposable(self, other)
        return type(self)(
            lambda *xs: self(*xs).flatmap(
                lambda ys: other(*tuplify(ys))), self.dom, other.cod)

    def tensor(self, other: Sample) -> Sample:
        """ Independent sampling, i.e. the strength ``st.tuples``. """
        from hypothesis import strategies as st

        def inside(*xs):
            left, right = xs[:len(self.dom)], xs[len(self.dom):]
            return st.tuples(self(*left), other(*right)).map(
                lambda pair: untuplify(tuplify(pair[0]) + tuplify(pair[1])))
        return type(self)(inside, self.dom + other.dom, self.cod + other.cod)

    @classmethod
    def swap(cls, x: Ty, y: Ty) -> Sample:
        return cls.pure(
            lambda *xs: untuplify(xs[len(x):] + xs[:len(x)]), x + y, y + x)

    braid = swap

    @classmethod
    def permutation(cls, xs, doms) -> Sample:
        """ Permute blocks of values, deterministically. """
        doms, xs = list(map(tuplify, doms)), list(xs)
        offsets = [0]
        for dom in doms:
            offsets.append(offsets[-1] + len(dom))

        def inside(*args):
            blocks = [args[offsets[i]:offsets[i + 1]]
                      for i in range(len(doms))]
            return untuplify(sum((blocks[i] for i in xs), ()))

        return cls.pure(
            inside, sum(doms, ()), sum((doms[i] for i in xs), ()))

    @classmethod
    def copy(cls, x: Ty, n: int = 2) -> Sample:
        """ Share a drawn value, i.e. the commutative comonoid. """
        return cls.pure(lambda *xs: untuplify(n * xs), x, n * x)

    @classmethod
    def discard(cls, x: Ty) -> Sample:
        return cls.copy(x, 0)


OB, AR, MODEL = markov.Ty("ob"), markov.Ty("ar"), markov.Ty("model")
""" The wire types of a sampling plan: carrier objects, arrows, models. """


def names(word) -> list[str]:
    """
    The generating objects a word mentions, by name, in occurrence order
    with multiplicity, through whatever structure decorates them: a tensor,
    an exponential, a rotation or a delay.
    """
    from discopy import biclosed

    if isinstance(word, biclosed.Exp):
        return names(word.base) + names(word.exponent)
    if hasattr(word, "inside"):
        return [name for obj in word.inside for name in names(obj)]
    return [word.name]


def send(word, images: Mapping[str, object], carrier):
    """
    The image of a presentation word under an assignment of its atoms,
    carrying over whatever the word does to them: an exponential in a
    closed word, a rotation in a rigid one, a delay in a feedback one.
    """
    from discopy import biclosed

    if isinstance(word, biclosed.Exp):
        base, exponent = (
            send(side, images, carrier)
            for side in (word.base, word.exponent))
        return base << exponent if isinstance(word, biclosed.Over)\
            else exponent >> base
    if hasattr(word, "inside"):
        values = [send(obj, images, carrier) for obj in word.inside]
        if len(values) == 1:
            return values[0]
        return carrier.ob().tensor(*values)
    image = images[word.name]
    turns = getattr(word, "z", 0)
    for _ in range(abs(turns)):
        image = image.l if turns < 0 else image.r
    steps = getattr(word, "time_step", 0)
    return image.delay(steps) if steps else image


def infer(word, boundary, images: dict) -> None:
    """
    Read the image of a word's single unknown atom off a boundary, slicing
    out the lengths of the known ones — how a replayed counterexample gets
    the objects its exposed arrows do not name.
    """
    from discopy import biclosed

    if not hasattr(word, "inside") or any(
            isinstance(atom, biclosed.Exp) for atom in word.inside):
        return
    atoms = list(word.inside)
    unknown = [i for i, atom in enumerate(atoms)
               if atom.name not in images]
    if len(unknown) != 1:
        return
    index = unknown[0]
    atom = atoms[index]
    if getattr(atom, "z", 0) or getattr(atom, "time_step", 0):
        return
    if len(atoms) == 1:
        images[atom.name] = boundary
        return
    before = sum(len(images[a.name]) for a in atoms[:index])
    after = sum(len(images[a.name]) for a in atoms[index + 1:])
    images[atom.name] = boundary[before:len(boundary) - after]


class Pure(markov.Box):
    """
    A deterministic box in a sampling plan: the image under the unit of the
    monad of a function of the carrier and the box's input values.
    """
    def __init__(self, name: str, function: Callable,
                 dom: markov.Ty, cod: markov.Ty):
        self.function = function
        super().__init__(name, dom, cod)


class DrawOb(markov.Box):
    """ Draw a carrier object, with the params of the generator's sort. """
    def __init__(self, name: str, sort: Mapping | None = None):
        self.sort = dict(sort or {})
        super().__init__(f"draw({name})", markov.Ty(), OB)


class DrawAr(markov.Box):
    """
    Draw a carrier arrow between the objects it takes as input, with the
    params of the generator's sort; ``sides`` says which of its boundaries
    are constrained, both by default.
    """
    def __init__(self, name: str, sort: Mapping | None = None,
                 sides: tuple[str, ...] = ("dom", "cod")):
        self.sort, self.sides = dict(sort or {}), tuple(sides)
        super().__init__(f"draw({name})", OB ** len(self.sides), AR)


def sampler(carrier, ob_factory=None, **draw_params) -> markov.Functor:
    """
    The functor evaluating a sampling plan in the Kleisli category: draws
    become the carrier's primitive strategies, :class:`Pure` boxes go
    through the unit of the monad.

    Parameters:
        carrier : The class whose instances are sampled.
        ob_factory : The class objects are drawn from, ``carrier.ob`` by
            default.
        draw_params : Extra params passed to every arrow draw.
    """
    ob_factory = carrier.ob if ob_factory is None else ob_factory

    def ar_map(box):
        if isinstance(box, DrawOb):
            return lambda: ob_factory.strategy(**box.sort)
        if isinstance(box, DrawAr):
            params = dict(draw_params, **box.sort)
            return lambda *boundaries: carrier.strategy(
                **dict(zip(box.sides, boundaries)), **params)
        assert_isinstance(box, Pure)
        return Sample.pure(
            partial(box.function, carrier),
            len(box.dom) * (object, ), len(box.cod) * (object, ))
    return markov.Functor(
        ob_map=lambda _: object, ar_map=ar_map, cod=Sample)


class Model:
    """
    An instance of a shape in a carrier, i.e. a functor from the shape: an
    image for each generating object and box, whose typing against the
    shape's words is the one validation every old testing class stated in
    its own ``__new__``.

    A model unpacks like the tuple it replaces, yielding the images of the
    shape's ``exposed`` generators in order.
    """
    def __init__(self, shape: Shape, carrier,
                 obs: Mapping[str, object], ars: Mapping[str, object]):
        self.shape, self.carrier = shape, carrier
        self.obs, self.ars = dict(obs), dict(ars)
        for box in shape.boxes:
            image = self.ars[box.name]
            expected = tuple(
                send(word, self.obs, carrier)
                for word in (box.dom, box.cod))
            if (image.dom, image.cod) != expected:
                raise AxiomError(
                    f"The image of {box.name} has boundary "
                    f"{image.dom, image.cod}, expected {expected}.")

    def __getitem__(self, key):
        """ The image of a generator by name, or of a word. """
        if not isinstance(key, str):
            return send(key, self.obs, self.carrier)
        return self.ars[key] if key in self.ars else self.obs[key]

    def __iter__(self):
        return iter(self[key] for key in self.shape.exposed)

    @property
    def value(self):
        """ The single exposed image of a one-generator shape. """
        image, = self
        return image

    def __eq__(self, other):
        return isinstance(other, Model) and (
            self.shape, self.carrier, self.obs, self.ars) == (
                other.shape, other.carrier, other.obs, other.ars)

    def __repr__(self):
        return f"Model({self.shape!r}, {self.carrier.__name__}, "\
            f"obs={self.obs!r}, ars={self.ars!r})"

    @property
    def functor(self):
        """ The model as the carrier's own functor from the shape. """
        return self.carrier.functor_factory(
            ob_map=lambda atom: send(atom, self.obs, self.carrier),
            ar_map=lambda box: self.ars[box.name], cod=self.carrier)


class Shape:
    """
    A finitely presented category: generating boxes whose ``dom`` and
    ``cod`` are words over generating objects, written in the free category
    of the doctrine the shape needs.

    Parameters:
        boxes : The generating boxes.
        obs : Extra generating objects mentioned by no word.
        exposed : The generator names a :class:`Model` unpacks, the box
            names in order by default.
        params : Strategy param names, each bound to the generating
            objects it gives a value to.
        sorts : Draw params per generator name, e.g. ``min_length`` for an
            object or ``min_leaves`` for a box.
        derived : Functions ``(carrier, obs) -> arrow`` for the boxes whose
            image is computed rather than drawn.
    """
    def __init__(self, boxes, obs=(), exposed=None,
                 params=None, sorts=None, derived=None):
        self.boxes = tuple(boxes)
        self.params = dict(params or {})
        self.sorts = dict(sorts or {})
        self.derived = dict(derived or {})
        mentioned = [
            name for box in self.boxes
            for name in names(box.dom) + names(box.cod)]
        extra = [name for ob in obs for name in names(ob)]
        self.obs = tuple(dict.fromkeys(mentioned + extra))
        self.exposed = tuple(
            box.name for box in self.boxes
        ) if exposed is None else tuple(exposed)

    def __eq__(self, other):
        return isinstance(other, Shape) and (
            self.boxes, self.obs, self.exposed) == (
                other.boxes, other.obs, other.exposed)

    def __repr__(self):
        return f"Shape({list(self.boxes)!r})"

    def __getitem__(self, carrier) -> Sampled:
        """
        Instantiate the shape at a carrier, as an axiom annotation like
        ``ComposablePair[C1]`` resolves it — the carrier is the last
        subscript, matching ``TraceSuperposing[C0, C1]``.
        """
        carrier = carrier[-1] if isinstance(carrier, tuple) else carrier
        return Sampled(self, carrier)

    def __call__(self, *values) -> Model:
        """
        A model from the images of the exposed generators, the remaining
        objects read off the boundaries of the given arrows — the way a
        recorded counterexample replays.
        """
        box_names = {box.name for box in self.boxes}
        obs, ars = {}, {}
        for key, value in zip(self.exposed, values, strict=True):
            if not isinstance(key, str):
                atoms = names(key)
                if len(atoms) != len(value):
                    raise ValueError(
                        f"Cannot split {value} over the word {key}.")
                obs.update({
                    name: value[i:i + 1]
                    for i, name in enumerate(atoms)})
            elif key in box_names:
                ars[key] = value
            else:
                obs[key] = value
        for box in self.boxes:
            if box.name not in ars:
                raise ValueError(f"Missing the image of {box.name}.")
        for _ in range(2):
            for box in self.boxes:
                image = ars[box.name]
                for word, boundary in (
                        (box.dom, image.dom), (box.cod, image.cod)):
                    infer(word, boundary, obs)
        missing = [name for name in self.obs if name not in obs]
        if missing:
            raise AxiomError(
                f"Cannot infer the images of {missing} "
                "from the given boundaries.")
        carrier = next(
            (type(value).ar for value in values
             if isinstance(value, Category)), type(values[0]))
        return Model(self, carrier, obs, ars)

    @classmethod
    def grid(cls, n_rows: int, n_columns: int) -> Shape:
        """
        The pasting-diagram shape: a rectangular grid of cells composable
        along the columns, ``f[i][j]`` from ``x[i][j]`` to ``x[i + 1][j]``,
        with ``dom`` and ``cod`` params binding every column's boundary.
        """
        boxes = tuple(
            monoidal.Box(
                f"f{i}{j}",
                monoidal.Ty(f"x{i}{j}"), monoidal.Ty(f"x{i + 1}{j}"))
            for i in range(n_rows) for j in range(n_columns))
        params = {
            "dom": tuple(f"x0{j}" for j in range(n_columns)),
            "cod": tuple(f"x{n_rows}{j}" for j in range(n_columns))}
        return cls(boxes, params=params)

    def sampling(self, bound: tuple[str, ...] = ()) -> markov.Diagram:
        """
        The sampling plan of the shape: a pure :class:`discopy.markov`
        diagram drawing each generator with its boundaries determined,
        taking the ``bound`` objects as inputs instead of drawing them.
        """
        drawn = [name for name in self.obs if name not in bound]
        plan = markov.Id(OB ** len(bound))
        for name in drawn:
            plan @= DrawOb(name, self.sorts.get(name))
        current = list(bound) + drawn
        if current != list(self.obs):
            plan >>= markov.Diagram.permutation(
                [current.index(name) for name in self.obs],
                OB ** len(self.obs))

        groups = []
        for box in self.boxes:
            if box.name in self.derived:
                groups.append((list(self.obs), Pure(
                    box.name, self._derive(box.name),
                    OB ** len(self.obs), AR)))
            else:
                for side, word in (("dom", box.dom), ("cod", box.cod)):
                    groups.append((names(word), Pure(
                        f"{box.name}.{side}", self._word(word),
                        OB ** len(names(word)), OB)))
        groups.append((list(self.obs), None))

        demand = [name for group, _ in groups for name in group]
        counts = [demand.count(name) for name in self.obs]
        copies = markov.Id(markov.Ty())
        for count in counts:
            copies @= markov.Id(OB) if count == 1\
                else markov.Copy(OB, count)
        plan >>= copies

        pools = {name: deque() for name in self.obs}
        position = 0
        for name, count in zip(self.obs, counts):
            for _ in range(count):
                pools[name].append(position)
                position += 1
        plan >>= markov.Diagram.permutation(
            [pools[name].popleft() for name in demand],
            OB ** len(demand))

        layer = markov.Id(markov.Ty())
        for group, box in groups:
            layer @= markov.Id(OB ** len(group)) if box is None else box
        plan >>= layer

        layer = markov.Id(markov.Ty())
        for box in self.boxes:
            layer @= markov.Id(AR) if box.name in self.derived\
                else DrawAr(box.name, self.sorts.get(box.name))
        plan >>= layer @ markov.Id(OB ** len(self.obs))

        return plan >> Pure(
            "model", self._pack,
            AR ** len(self.boxes) @ OB ** len(self.obs), MODEL)

    def chain_sampling(self, bound: tuple[str, ...] = ()) -> markov.Diagram:
        """
        The sampling plan of a chain of composable boxes, drawing each
        arrow with the boundary projected off the one before rather than
        drawing the objects first — for carriers whose objects have no
        strategy of their own, e.g. the functors of ``Cat``, whose objects
        are categories.
        """
        atoms = [names(self.boxes[0].dom)[0]] + [
            names(box.cod)[0] for box in self.boxes]
        if any(
                names(box.dom) + names(box.cod) != atoms[i:i + 2]
                for i, box in enumerate(self.boxes)):
            raise NotImplementedError(
                "Projected sampling is only derived for chains.")
        plan = markov.Id(OB ** len(bound))
        n_arrows = 0
        for i, box in enumerate(self.boxes):
            sides = tuple(
                side for side, atom in (
                    ("dom", atoms[i]), ("cod", atoms[i + 1]))
                if atom in bound or side == "dom" and i > 0)
            step = DrawAr(box.name, self.sorts.get(box.name), sides)
            trailing = len(plan.cod) - n_arrows - len(step.dom)
            plan >>= markov.Id(AR ** n_arrows) @ step\
                @ markov.Id(OB ** trailing)
            n_arrows += 1
            if i < len(self.boxes) - 1:
                plan >>= markov.Id(AR ** (n_arrows - 1)) @ Pure(
                    f"{box.name}.cod", lambda carrier, arrow: (
                        arrow, arrow.cod), AR, AR @ OB)\
                    @ markov.Id(OB ** (len(plan.cod) - n_arrows))
        return plan >> Pure(
            "model", self._pack_projected, AR ** len(self.boxes), MODEL)

    def _pack_projected(self, carrier, *arrows):
        ars = dict(zip((box.name for box in self.boxes), arrows))
        obs: dict = {}
        for _ in range(2):
            for box in self.boxes:
                image = ars[box.name]
                infer(box.dom, image.dom, obs)
                infer(box.cod, image.cod, obs)
        return Model(self, carrier, obs, ars)

    def _word(self, word) -> Callable:
        group = names(word)

        def function(carrier, *values):
            return send(word, dict(zip(group, values)), carrier)
        return function

    def _derive(self, name: str) -> Callable:
        def function(carrier, *values):
            return self.derived[name](
                carrier, dict(zip(self.obs, values)))
        return function

    def _pack(self, carrier, *values):
        ars = dict(zip((box.name for box in self.boxes), values))
        obs = dict(zip(self.obs, values[len(self.boxes):]))
        return Model(self, carrier, obs, ars)

    def strategy(self, carrier, **params) -> "st.SearchStrategy[Model]":
        """
        The derived search strategy for models of the shape in the carrier:
        the :func:`sampler` functor applied to the :meth:`sampling` plan,
        then to the values of the bound params. Params the shape does not
        declare are passed to every arrow draw. A shape with no boxes is
        instantiated at the object factory itself, e.g. ``Atomic[C0]``.
        """
        bound, values = [], []
        for key in self.params:
            value = params.pop(key, None)
            if value is not None:
                for name in self.params[key]:
                    bound.append(name)
                    values.append(value)
        ob_factory = carrier if not self.boxes else carrier.ob
        plan = self.chain_sampling(tuple(bound))\
            if self.boxes and not hasattr(ob_factory, "strategy")\
            else self.sampling(tuple(bound))
        return sampler(carrier, ob_factory=ob_factory, **params)(
            plan)(*values)


class Sampled:
    """
    A shape instantiated at a carrier, with the params its subspace
    annotations have accumulated: what an axiom annotation resolves to.
    """
    def __init__(self, shape, carrier, params: Mapping | None = None):
        self.shape, self.carrier = shape, carrier
        self.params = dict(params or {})

    def __repr__(self):
        return f"{self.shape!r}[{self.carrier.__name__}]"

    def strategy(self, **params) -> "st.SearchStrategy[Model]":
        """ The derived strategy of the shape in the carrier. """
        return self.shape.strategy(
            self.carrier, **dict(self.params, **params))


class Refined:
    """
    A subspace annotation adding draw params to the shape it subscripts,
    e.g. ``BoundaryConnected[Bifunctor[C1]]``.
    """
    def __init__(self, **params):
        self.params = params

    def __getitem__(self, inner: Sampled) -> Sampled:
        return Sampled(
            inner.shape, inner.carrier, dict(inner.params, **self.params))


BoundaryConnected = Refined(boundary_connected=True)


class Padded:
    """
    A grid shape sampled one active row at a time, the others identities:
    the degeneracy inserting identity rows, applied to the model after
    sampling rather than built into the plan.
    """
    def __init__(self, n_rows: int, n_columns: int):
        self.n_rows, self.n_columns = n_rows, n_columns
        self.row = Shape.grid(1, n_columns)
        self.full = Shape.grid(n_rows, n_columns)

    __getitem__ = Shape.__getitem__

    def __call__(self, *values) -> Model:
        """ A model of the full grid, replayed without padding. """
        return self.full(*values)

    def strategy(self, carrier, **params) -> "st.SearchStrategy[Model]":
        """ Sample a single row and a position to insert it at. """
        from hypothesis import strategies as st

        def pad(args):
            active, model = args
            obs, ars = {}, {}
            for j in range(self.n_columns):
                source, target = model[f"x0{j}"], model[f"x1{j}"]
                for i in range(self.n_rows + 1):
                    obs[f"x{i}{j}"] = source if i <= active else target
                for i in range(self.n_rows):
                    ars[f"f{i}{j}"] = model[f"f0{j}"] if i == active\
                        else carrier.id(obs[f"x{i}{j}"])
            return Model(self.full, carrier, obs, ars)

        return st.tuples(
            st.integers(min_value=0, max_value=self.n_rows - 1),
            self.row.strategy(carrier, **params)).map(pad)


def sorted_object(**sort) -> Shape:
    """ The shape of a single generating object of the given sort. """
    return Shape((), obs=(monoidal.Ty("x"), ),
                 exposed=("x", ), sorts={"x": sort})


ComposablePair = Shape.grid(2, 1)
ComposableTriple = Shape.grid(3, 1)
HorizontalPair = Shape.grid(1, 2)
Bifunctor = Padded(2, 2)

Atomic = sorted_object(min_length=1, max_length=1)
NonEmpty = sorted_object(min_length=1)
Small = sorted_object(max_length=1)

TraceSuperposing = Shape(
    boxes=(monoidal.Box("traced", monoidal.Ty("u"), monoidal.Ty("u")), ),
    obs=(monoidal.Ty("a"), ),
    exposed=("traced", "a"),
    sorts={"u": dict(min_length=1, max_length=1)},
    derived={"traced": lambda carrier, obs: carrier.id(obs["u"])})

TraceNaturalityLeft = Shape(
    boxes=(
        monoidal.Box(
            "traced", monoidal.Ty("u", "b"), monoidal.Ty("u", "a")),
        monoidal.Box("sliding", monoidal.Ty("a"), monoidal.Ty("b"))),
    exposed=("traced", "u", "sliding"),
    sorts={"u": dict(min_length=1),
           "traced": dict(min_leaves=1), "sliding": dict(min_leaves=1)})

TraceNaturalityRight = Shape(
    boxes=(
        monoidal.Box(
            "traced", monoidal.Ty("b", "u"), monoidal.Ty("a", "u")),
        monoidal.Box("sliding", monoidal.Ty("a"), monoidal.Ty("b"))),
    exposed=("traced", "u", "sliding"),
    sorts={"u": dict(min_length=1),
           "traced": dict(min_leaves=1), "sliding": dict(min_leaves=1)})

TraceDinaturalityLeft = Shape(
    boxes=(
        monoidal.Box(
            "traced", monoidal.Ty("s", "p"), monoidal.Ty("t", "q")),
        monoidal.Box("sliding", monoidal.Ty("t"), monoidal.Ty("s"))),
    exposed=("traced", "sliding"),
    sorts={"s": dict(min_length=1), "t": dict(min_length=1),
           "traced": dict(min_leaves=1), "sliding": dict(min_leaves=1)})

TraceDinaturalityRight = Shape(
    boxes=(
        monoidal.Box(
            "traced", monoidal.Ty("p", "s"), monoidal.Ty("q", "t")),
        monoidal.Box("sliding", monoidal.Ty("t"), monoidal.Ty("s"))),
    exposed=("traced", "sliding"),
    sorts={"s": dict(min_length=1), "t": dict(min_length=1),
           "traced": dict(min_leaves=1), "sliding": dict(min_leaves=1)})


def currying(left: bool) -> Shape:
    """
    The shape of an evaluation morphism: two atomic objects and the
    derived cell evaluating the exponential of one by the other. The words
    are biclosed so that the exponential keeps its handedness, whatever
    the carrier reads it as: an :class:`discopy.closed.Exp` or the
    adjoints of a rigid type.
    """
    from discopy import biclosed

    base, exponent = biclosed.Ty("base"), biclosed.Ty("exponent")
    dom = (base << exponent) @ exponent if left\
        else exponent @ (exponent >> base)
    return Shape(
        boxes=(biclosed.Box("arrow", dom, base), ),
        exposed=("arrow", "base", "exponent"),
        sorts={"base": dict(min_length=1, max_length=1),
               "exponent": dict(min_length=1, max_length=1)},
        derived={"arrow": lambda carrier, obs: carrier.ev(
            obs["base"], obs["exponent"], left=left)})


LeftCurrying = currying(left=True)
RightCurrying = currying(left=False)


def feedback_shapes() -> tuple[Shape, Shape, Shape]:
    """ The vanishing, joining and homogeneous-memory feedback shapes. """
    from discopy import feedback

    def joining(memory: feedback.Ty) -> Shape:
        obj = feedback.Ty("o")
        return Shape(
            boxes=(feedback.Box(
                "arrow", obj @ memory.delay(), obj @ memory), ),
            exposed=("arrow", memory),
            sorts={name: dict(min_length=1, max_length=1)
                   for name in names(memory)})

    vanishing = Shape(
        boxes=(feedback.Box(
            "arrow", feedback.Ty("x"), feedback.Ty("y")), ),
        exposed=("arrow", feedback.Ty()))
    memory = feedback.Ty("m1") @ feedback.Ty("m2")
    homogeneous = feedback.Ty("m") @ feedback.Ty("m")
    return vanishing, joining(memory), joining(homogeneous)


FeedbackVanishing, FeedbackJoining, HomogeneousMemory = feedback_shapes()


def catalog() -> dict:
    """
    The shapes by name, for evaluating axiom annotations: the scope
    :meth:`discopy.testing.Axiom.strategy` injects beside ``C0, C1``.
    """
    return {
        name: value for name, value in globals().items()
        if isinstance(value, (Shape, Padded, Refined))}
