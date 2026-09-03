# -*- coding: utf-8 -*-

"""
The category of relations of an OWL ontology, split at its predicates.

An OWL property denotes a relation between individuals and an OWL class
denotes a predicate over one domain of individuals, so a loaded ontology
presents two categories, one on top of the other:

* :class:`Relation` is the underlying **single-sorted** category: its one
  generating object is ``owl:Thing``, its objects are arities ``n`` read
  as ``Thing ** n``, and its morphisms are finite relations between tuples
  of individuals, composed by relational composition. It is a
  :class:`DistributiveAllegory`: converse, meet, join and bottom -- but no
  complement and no top, because OWL cannot say either of a property.
  A predicate lives here as a **coreflexive** ``e <= id(1)``, which is
  what :func:`extension` returns.
* :class:`Query` is the **Karoubi envelope** of :class:`Relation`,
  restricted to the coreflexives: its objects are tuples of predicates --
  named classes or compound class constructs, labelled the way a
  mathematician would write them -- and a morphism is a relation ``r``
  normalised to ``e ; r ; f`` between the coreflexives of its boundary.
  Composing two queries whose predicates do not meet asks `HermiT`_
  whether one predicate is subsumed by the other and inserts the verdict
  as a :class:`Coercion` in between -- a proof object, drawn as a box
  exactly where the predicate changes.

Everything is deductive: :func:`reason` writes what the ontology entails
back into the world, the constructors read the entailed atoms, the algebra
computes certain answers, and retrieval of a class construct classifies a
scratch defined class with `HermiT`_ (:func:`deduced`), so a complement, a
universal or a cardinality holds of an individual only when it is
*provably* so. Querying and proving are delegated: :meth:`Relation.sparql`
to `owlready2`_'s native SPARQL engine, :func:`reason`,
:func:`consistent`, :func:`deduced` and :func:`subsumes` to `HermiT`_.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Wire
    Ty
    Diagram
    Box
    Cup
    Cap
    Permutation
    Swap
    Spider
    Bubble
    Functor
    Relation
    Query
    Coercion
    Axiom

.. admonition:: Functions

    .. autosummary::
        :template: function.rst
        :nosignatures:
        :toctree:

        load
        preload
        reason
        consistent
        deduced
        dismiss
        subsumes
        declared
        instances
        carrier
        relations
        satisfying
        extension
        expr_world
        coercion
        parallel
        class_axioms
        property_axioms
        disjoint_axioms
        constructs_of
        axioms
        label
        ob
        peel
        schema
        box
        point
        individual_class
        to_diagram
        restriction_diagram
        combine

.. _owlready2: https://owlready2.readthedocs.io/
.. _HermiT: http://www.hermit-reasoner.com/

Example
-------
>>> from owlready2 import Thing, World
>>> onto = World().get_ontology("http://discopy.org/kennel.owl")
>>> with onto:
...     class Dog(Thing): pass
...     class Person(Thing): pass
...     class owns(Person >> Dog): pass
...     rex, ada = Dog("rex"), Person("ada")
...     ada.owns = [rex]
>>> web = Relation.from_property(onto.owns)
>>> print(web)
owns : Thing -> Thing
>>> print(Query.from_property(onto.owns))
owns : ('Person',) -> ('Dog',)
>>> assert Query.from_property(onto.owns).relation <= web
"""

from __future__ import annotations

import os
import re
from contextlib import contextmanager
from dataclasses import dataclass
from itertools import product
from types import new_class

from owlready2 import (
    EXACTLY, HAS_SELF, MAX, MIN, ONLY, SOME, VALUE, And, ClassConstruct,
    Inverse, Not, ObjectPropertyClass, OneOf, Ontology, Or,
    OwlReadyInconsistentOntologyError, Restriction, Thing, ThingClass, World,
    destroy_entity, sync_reasoner_hermit)
from owlready2 import (
    AsymmetricProperty, FunctionalProperty, InverseFunctionalProperty,
    IrreflexiveProperty, ReflexiveProperty, SymmetricProperty,
    TransitiveProperty)
from owlready2.base import owl_equivalentclass
import owlready2

from discopy import cat, frobenius, messages
from discopy.abc import DistributiveAllegory, SymmetricCategory
from discopy.utils import (
    AxiomError, assert_iscomposable, assert_isinstance, assert_isparallel,
    classproperty, factory, tuplify)


OWL = "http://www.w3.org/2002/07/owl#"
""" The namespace of OWL's own vocabulary, which says nothing on its own. """

INCLUSION = "$\\sqsubseteq$"
""" The symbol of a 2-cell that is an inclusion, not an equation. """

NEGATION = "$\\neg$"
""" The drawing name of the bubble for a complement. """

SCRATCH = "http://discopy.org/scratch.owl"
""" The ontology where :func:`deduced` puts its scratch defined classes. """


def declared(entity, kind: type) -> bool:
    """
    Whether an entity is one an ontology declared rather than one of OWL's
    own, i.e. whether it is worth talking about.

    ``owl:Thing`` is every class and ``owl:TransitiveProperty`` is where
    `owlready2` keeps a characteristic, so both turn up as parents without
    being anything the ontology said.

    Parameters:
        entity : The candidate.
        kind : The class it has to be, i.e. a class or a property.
    """
    return isinstance(entity, kind) and not entity.iri.startswith(OWL)


def iris(individuals: tuple) -> tuple[str, ...]:
    """
    The IRIs of a tuple of individuals, the sort key that keeps every
    relation deterministic.

    Parameters:
        individuals : The individuals.
    """
    return tuple(individual.iri for individual in individuals)


def instances(cls, world: World = None) -> tuple:
    """
    The individuals of an OWL class or class construct, sorted by IRI:
    what is materialised for a named class -- the entailed members once
    :func:`reason` has run -- and what `HermiT` :func:`deduced` for a
    construct.

    Parameters:
        cls : The OWL class or class construct.
        world : The world to read ``owl:Thing`` from, resolved with
            :func:`expr_world` otherwise.
    """
    if isinstance(cls, ThingClass):
        generator = cls.instances(world=world) if world is not None\
            else cls.instances()
        return tuple(sorted(generator, key=lambda one: one.iri))
    return deduced([cls], world or expr_world(cls))[0]


def carrier(arity: int, world: World) -> tuple:
    """
    The tuples of individuals a boundary of a given arity can carry, i.e.
    the product of that many copies of the individuals of a world.

    Parameters:
        arity : The number of wires.
        world : The world whose individuals the wires carry.
    """
    return tuple(product(instances(Thing, world), repeat=arity))


def pairs_world(pairs) -> World:
    """
    The world of the first individual in some pairs of tuples, or the
    default world when there is none to ask.

    Parameters:
        pairs : The pairs of tuples of individuals.
    """
    for xs, ys in pairs:
        for individual in xs + ys:
            return individual.namespace.world
    return owlready2.default_world


def assert_isworld(left, right):
    """
    Raise :class:`AxiomError` when two relations live over different
    worlds, i.e. in different categories.

    Parameters:
        left : One relation.
        right : The other.
    """
    if left.world is not right.world:
        raise AxiomError(messages.DIFFERENT_WORLDS.format(left, right))


class Wire(frobenius.Wire):
    """
    A wire is labelled by a predicate: a named class, a class construct
    or ``owl:Thing`` -- the split object of the Karoubi envelope that
    :class:`Query` presents, displayed by :func:`label`.

    Parameters:
        entity : The `owlready2` class or class construct, or the name of
            one when a diagram is rebuilt from its syntax alone.
        z : The winding number, see :class:`rigid.Wire`.
    """
    def __init__(self, entity=Thing, z: int = 0):
        self.entity = entity
        name = entity if isinstance(entity, str) else label(entity)
        super().__init__(name, z)


@factory
class Ty(frobenius.Ty):
    """
    A type is a tuple of predicates, one :class:`Wire` each -- the
    objects of the Karoubi envelope; :func:`ob` builds one from raw
    `owlready2` entities.

    Parameters:
        inside (tuple[Wire, ...]) : The predicates inside the type.
    """
    generator_factory = Wire


@factory
class Diagram(frobenius.Diagram):
    """
    A diagram is the syntax of a relation, read off the ontology's own:
    a property is a :class:`Box` between the predicates of its schema, a
    class construct the coreflexive that tests it, an individual a point
    -- intersection is composition, union and complement are
    :class:`Bubble`, a quantifier follows its property and discards.

    Parameters:
        inside (tuple[frobenius.Layer, ...]) : The layers of the diagram.
        dom (Ty) : The domain of the diagram, i.e. its input.
        cod (Ty) : The codomain of the diagram, i.e. its output.
    """
    ob = Ty


class Box(frobenius.Box, Diagram):
    """
    A box is a generator of the syntax, carrying the `owlready2` entity
    it denotes as ``data``: a property, a class or class construct
    tested on a wire, an individual, or the :class:`Coercion` that
    changes a predicate.

    Parameters:
        name : The name of the box.
        dom : The domain of the box, i.e. its input.
        cod : The codomain of the box, i.e. its output.
    """


class Cup(frobenius.Cup, Box):
    """ A cup is a frobenius cup between predicate wires. """


class Cap(frobenius.Cap, Box):
    """ A cap is a frobenius cap between predicate wires. """


class Permutation(frobenius.Permutation, Box):
    """ A permutation of predicate wires. """


class Swap(Permutation, frobenius.Swap, Box):
    """ A swap of two predicate wires. """


class Spider(frobenius.Spider, Box):
    """ A spider on a predicate wire, i.e. copying and discarding. """


class Bubble(frobenius.Bubble, Box):
    """
    A bubble around the syntax of a union or a complement, which the
    allegory cannot evaluate -- OWL has no complement of a property --
    so it is decoration on the coreflexive that HermiT retrieves whole.
    """


class Functor(frobenius.Functor):
    """ A functor with the syntax of an ontology as domain. """
    dom = cod = Diagram


Diagram.cup_factory, Diagram.cap_factory = Cup, Cap
Diagram.swap_factory, Diagram.spider_factory = Swap, Spider
Diagram.permutation_factory = Permutation
Diagram.bubble_factory = Bubble
Id = Diagram.id


def peel(layer) -> dict | None:
    """
    The predicates a layer tests, by wire position -- ``None`` unless
    every box of the layer is a membership test on a single wire, i.e.
    carries a class or class construct as ``data``. A layer of tests is
    a coreflexive factor, which :meth:`Relation.typed` collapses into
    the types of its wires.

    Parameters:
        layer : The layer of a :class:`Diagram`.
    """
    result = {}
    for box, offset in layer.boxes_and_offsets:
        if not isinstance(box.data, (ThingClass, ClassConstruct))\
                or (len(box.dom), len(box.cod)) != (1, 1):
            return None
        result[offset] = box.data
    return result


@factory
@dataclass
class Relation(DistributiveAllegory, SymmetricCategory):
    """
    A finite relation over the individuals of a world, in the
    single-sorted category generated by ``owl:Thing``: the objects are
    arities and every wire carries an individual.

    Parameters:
        inside : The extension, i.e. the pairs of tuples of individuals.
        dom : The number of input wires.
        cod : The number of output wires.
        world : The world the relation lives over, resolved from the first
            individual of ``inside`` and the default world otherwise.

    The extension is stored sorted by IRIs, so that equal relations
    compare equal whatever order their pairs came in. What the extension
    *means* is deductive: the constructors read the atoms a world holds --
    the entailed ones once :func:`reason` has run -- and the algebra
    computes certain answers, sound for entailment. There is no complement
    and no greatest relation: OWL cannot say either of a property, which
    is why this is a :class:`DistributiveAllegory` and not a Boolean one.

    .. admonition:: Summary

        .. autosummary::

            id
            then
            tensor
            dagger
            swap
            spiders
            cups
            caps
            meet
            join
            bottom
            domain
            repeat
            split
            from_property
            from_individual
            sparql

    Example
    -------
    >>> from owlready2 import Thing, World
    >>> onto = World().get_ontology("http://discopy.org/kennel.owl")
    >>> with onto:
    ...     class Dog(Thing): pass
    ...     class Person(Thing): pass
    ...     class owns(Person >> Dog): pass
    ...     rex, fido = Dog("rex"), Dog("fido")
    ...     ada, bob = Person("ada"), Person("bob")
    ...     ada.owns, bob.owns = [rex], [fido]
    >>> web = Relation.from_property(onto.owns)
    >>> assert web.dagger().dagger() == web
    >>> assert web.meet(web) == web <= web.join(web.dagger() >> web)
    >>> assert Relation.id(1, onto.world) >> web == web
    """
    inside: tuple
    dom: int
    cod: int
    world: World

    ob = int

    def __init__(self, inside, dom: int, cod: int, world: World = None):
        pairs = {(tuplify(xs), tuplify(ys)) for xs, ys in inside}
        for xs, ys in pairs:
            if (len(xs), len(ys)) != (dom, cod):
                raise AxiomError(messages.WRONG_ARITY.format(
                    (dom, cod), (xs, ys)))
        self.inside = tuple(sorted(
            pairs, key=lambda pair: iris(pair[0] + pair[1])))
        self.dom, self.cod = dom, cod
        self.world = world or pairs_world(self.inside)
        self.diagram = None

    def __str__(self):
        name = getattr(self, "name", type(self).__name__)
        power = lambda arity: "()" if arity == 0\
            else "Thing" if arity == 1 else f"Thing ** {arity}"
        return f"{name} : {power(self.dom)} -> {power(self.cod)}"

    def __bool__(self):
        return bool(self.inside)

    def __le__(self, other) -> bool:
        assert_isinstance(other, Relation)
        assert_isparallel(self, other)
        assert_isworld(self, other)
        return set(self.inside) <= set(other.inside)

    @classmethod
    def id(cls, dom: int = 0, world: World = None) -> Relation:
        """
        The identity relation, i.e. the diagonal on the tuples.

        Parameters:
            dom : The number of wires.
            world : The world, the default world otherwise.
        """
        world = world or owlready2.default_world
        result = cls([(xs, xs) for xs in carrier(dom, world)],
                     dom, dom, world)
        result.diagram = Id(ob(dom * (Thing, )))
        return result

    def then(self, *others: Relation) -> Relation:
        """
        The relational composition, i.e. pairs that share a middle.

        Parameters:
            others : The relations to compose in sequence.
        """
        result = self
        for other in others:
            assert_isinstance(other, Relation)
            assert_iscomposable(result, other)
            assert_isworld(result, other)
            targets = {}
            for ys, zs in other.inside:
                targets.setdefault(ys, []).append(zs)
            step = self.factory(
                {(xs, zs) for xs, ys in result.inside
                 for zs in targets.get(ys, ())},
                result.dom, other.cod, result.world)
            step.diagram = combine(
                lambda left, right: left >> right,
                result.diagram, other.diagram)
            result = step
        return result

    def tensor(self, *others: Relation) -> Relation:
        """
        The product of relations, i.e. pairs of pairs.

        Parameters:
            others : The relations to tensor.
        """
        result = self
        for other in others:
            assert_isinstance(other, Relation)
            assert_isworld(result, other)
            step = self.factory(
                {(xs + xs_, ys + ys_)
                 for xs, ys in result.inside for xs_, ys_ in other.inside},
                result.dom + other.dom, result.cod + other.cod,
                result.world)
            step.diagram = combine(
                lambda left, right: left @ right,
                result.diagram, other.diagram)
            result = step
        return result

    __matmul__ = tensor

    def dagger(self) -> Relation:
        """ The converse relation, i.e. the pairs the other way around. """
        result = self.factory(
            [(ys, xs) for xs, ys in self.inside],
            self.cod, self.dom, self.world)
        result.diagram = combine(
            lambda diagram: diagram.dagger(), self.diagram)
        return result

    @classmethod
    def swap(cls, left: int, right: int, world: World = None) -> Relation:
        """
        The relation exchanging two boundaries.

        Parameters:
            left : The number of wires on the left.
            right : The number of wires on the right.
            world : The world, the default world otherwise.
        """
        world = world or owlready2.default_world
        result = cls([(xs + ys, ys + xs)
                      for xs in carrier(left, world)
                      for ys in carrier(right, world)],
                     left + right, right + left, world)
        result.diagram = Diagram.swap(
            ob(left * (Thing, )), ob(right * (Thing, )))
        return result

    @classmethod
    def permutation(cls, xs, doms, world: World = None) -> Relation:
        """
        The relation permuting some boundaries, with the same convention
        as :meth:`abc.SymmetricCategory.permutation`: the ``i``-th output
        is the ``xs[i]``-th input.

        Parameters:
            xs : A permutation of ``range(len(doms))``.
            doms : The arities to permute.
            world : The world, the default world otherwise.
        """
        xs, doms = list(xs), list(doms)
        if sorted(xs) != list(range(len(doms))):
            raise ValueError
        world = world or owlready2.default_world
        return cls([(sum(groups, ()), sum((groups[x] for x in xs), ()))
                    for groups in product(
                        *(carrier(one, world) for one in doms))],
                   sum(doms), sum(doms), world)

    @classmethod
    def spiders(cls, n_legs_in: int, n_legs_out: int, typ: int,
                world: World = None) -> Relation:
        """
        The spider relation, i.e. tuples of individuals repeated on every
        leg -- copying, comparing and forgetting them.

        Parameters:
            n_legs_in : The number of legs in.
            n_legs_out : The number of legs out.
            typ : The number of wires on each leg.
            world : The world, the default world otherwise.
        """
        world = world or owlready2.default_world
        result = cls([(n_legs_in * xs, n_legs_out * xs)
                      for xs in carrier(typ, world)],
                     n_legs_in * typ, n_legs_out * typ, world)
        result.diagram = Diagram.spiders(
            n_legs_in, n_legs_out, ob(typ * (Thing, )))
        return result

    @classmethod
    def copy(cls, typ: int, n: int = 2, world: World = None) -> Relation:
        """
        The relation copying every individual ``n`` times.

        Parameters:
            typ : The number of wires to copy.
            n : The number of copies.
            world : The world, the default world otherwise.
        """
        return cls.spiders(1, n, typ, world)

    @classmethod
    def cups(cls, left: int, right: int, world: World = None) -> Relation:
        """
        The relation bending two boundaries into none; ``owl:Thing`` is
        self-dual so ``left`` and ``right`` must be equal.

        Parameters:
            left : The number of wires on the left.
            right : The same number of wires.
            world : The world, the default world otherwise.
        """
        if left != right:
            raise AxiomError(messages.NOT_ADJOINT.format(left, right))
        world = world or owlready2.default_world
        result = cls([(xs + xs, ()) for xs in carrier(left, world)],
                     left + right, 0, world)
        result.diagram = Diagram.cups(
            ob(left * (Thing, )), ob(right * (Thing, )))
        return result

    @classmethod
    def caps(cls, left: int, right: int, world: World = None) -> Relation:
        """ The dagger of :meth:`cups`. """
        return cls.cups(left, right, world).dagger()

    def meet(self, *others: Relation) -> Relation:
        """
        The intersection of parallel relations, called with ``&``.

        Parameters:
            others : The other relations.
        """
        pairs = set(self.inside)
        for other in others:
            assert_isinstance(other, Relation)
            assert_isparallel(self, other)
            assert_isworld(self, other)
            pairs &= set(other.inside)
        result = self.factory(pairs, self.dom, self.cod, self.world)
        diagrams = (self.diagram, ) + tuple(
            other.diagram for other in others)
        typs = ob(self.dom * (Thing, )), ob(self.cod * (Thing, ))
        result.diagram = combine(lambda *inside: (
            Diagram.spiders(1, len(inside), typs[0])
            >> Id().tensor(*inside)
            >> Diagram.spiders(len(inside), 1, typs[1])
            if len(inside) > 1 else inside[0]), *diagrams)
        return result

    def join(self, *others: Relation) -> Relation:
        """
        The union of parallel relations, called with ``|``.

        Parameters:
            others : The other relations.
        """
        pairs = set(self.inside)
        for other in others:
            assert_isinstance(other, Relation)
            assert_isparallel(self, other)
            assert_isworld(self, other)
            pairs |= set(other.inside)
        result = self.factory(pairs, self.dom, self.cod, self.world)
        diagrams = (self.diagram, ) + tuple(
            other.diagram for other in others)
        typs = ob(self.dom * (Thing, )), ob(self.cod * (Thing, ))
        result.diagram = combine(lambda *inside: (
            Bubble(
                *inside, dom=typs[0], cod=typs[1], drawing_name="$\\vee$")
            if len(inside) > 1 else inside[0]), *diagrams)
        return result

    @classmethod
    def bottom(cls, dom: int, cod: int, world: World = None) -> Relation:
        """
        The empty relation between two boundaries.

        Parameters:
            dom : The number of input wires.
            cod : The number of output wires.
            world : The world, the default world otherwise.
        """
        result = cls((), dom, cod, world or owlready2.default_world)
        result.diagram = Box(
            "$\\bot$", ob(dom * (Thing, )), ob(cod * (Thing, )))
        return result

    def domain(self) -> Relation:
        """
        The coreflexive relation on what a relation is actually defined
        on, i.e. the partial identity on the tuples with at least one
        value.
        """
        result = self.factory(
            [(xs, xs) for xs, _ in self.inside],
            self.dom, self.dom, self.world)
        typs = ob(self.dom * (Thing, )), ob(self.cod * (Thing, ))
        result.diagram = combine(lambda diagram: (
            Diagram.spiders(1, 2, typs[0]) >> Id(
                typs[0]) @ (diagram >> Diagram.spiders(
                    1, 0, typs[1]))), self.diagram)
        return result

    def codomain(self) -> Relation:
        """ The :meth:`domain` of the converse relation. """
        return self.dagger().domain()

    def repeat(self) -> Relation:
        """
        The reflexive transitive closure of a relation on one boundary,
        i.e. the least reflexive and transitive relation above it.
        """
        if self.dom != self.cod:
            raise AxiomError(messages.NOT_ENDO.format(self))
        result = self.factory.id(self.dom, self.world).join(self)
        while True:
            step = result.join(result >> result)
            if step == result:
                break
            result = step
        result.diagram = combine(
            lambda diagram: diagram.bubble(drawing_name="$\\ast$"),
            self.diagram)
        return result

    def split(self, dom: tuple, cod: tuple) -> Query:
        """
        The relation as a morphism of the Karoubi envelope, between the
        predicates given -- normalised between their coreflexives, see
        :class:`Query`.

        Parameters:
            dom : The tuple of predicates for the domain.
            cod : The tuple of predicates for the codomain.
        """
        return Query(self, dom, cod)

    def typed(self) -> Query:
        """
        The relation as a morphism of the Karoubi envelope, its boundary
        predicates read off its picture rather than given: a leading or
        trailing membership test is a coreflexive factor, collapsed into
        the type of its wire -- stacked tests meet -- and a wire with no
        test stays at ``owl:Thing``. The picture certifies the factors,
        so no normalisation and no reasoning is needed; a relation
        without a picture is typed at ``owl:Thing`` throughout, and a
        picture that is nothing but tests types both boundaries at once,
        collapsing to the identity on its predicates.

        Example
        -------
        >>> from owlready2 import Thing, World
        >>> onto = World().get_ontology("http://discopy.org/kennel.owl")
        >>> with onto:
        ...     class Dog(Thing): pass
        ...     class Person(Thing): pass
        ...     class owns(Person >> Dog): pass
        ...     rex, ada = Dog("rex"), Person("ada")
        ...     ada.owns = [rex]
        >>> web = Relation.from_property(onto.owns)
        >>> person, dog = map(extension, (onto.Person, onto.Dog))
        >>> chain = (person >> web >> dog).typed()
        >>> print(chain)
        Query : ('Person',) -> ('Dog',)
        >>> assert chain.relation == person >> web >> dog
        >>> assert web.typed() == web.split((Thing, ), (Thing, ))
        >>> print(label((person >> person >> dog).typed().dom[0]))
        Person ⊓ (Person ⊓ Dog)
        """
        layers = [] if self.diagram is None else list(self.diagram.inside)
        dom_preds, cod_preds = {}, {}
        while layers:
            tests = peel(layers[-1])
            if tests is None:
                break
            layers.pop()
            for offset, expr in tests.items():
                cod_preds[offset] = expr if offset not in cod_preds\
                    else expr & cod_preds[offset]
        while layers:
            tests = peel(layers[0])
            if tests is None:
                break
            layers.pop(0)
            for offset, expr in tests.items():
                dom_preds[offset] = expr if offset not in dom_preds\
                    else dom_preds[offset] & expr
        if not layers and self.diagram is not None:
            for offset in set(dom_preds) | set(cod_preds):
                both = [preds[offset] for preds in (dom_preds, cod_preds)
                        if offset in preds]
                dom_preds[offset] = cod_preds[offset]\
                    = both[0] if len(both) == 1 else both[0] & both[1]
        dom = tuple(
            dom_preds.get(offset, Thing) for offset in range(self.dom))
        cod = tuple(
            cod_preds.get(offset, Thing) for offset in range(self.cod))
        result = Query(self, dom, cod, normalise=False)
        if not layers and self.diagram is not None:
            result.diagram = Id(ob(dom))
        return result

    @classmethod
    def from_property(cls, prop, world: World = None) -> Relation:
        """
        The relation an OWL property holds of the individuals of a world:
        the raw single-sorted reading, every pair at arity one, deduced
        as in :func:`relations` -- see :meth:`Query.from_property` for
        the reading typed by the schema.

        Parameters:
            prop : The `owlready2` property.
            world : The world, the property's own otherwise.
        """
        world = world or prop.namespace.world
        result = cls({(x, y) for x, ys in relations(prop).items()
                      for y in ys}, 1, 1, world)
        result.name = prop.name
        result.diagram = box(prop, Thing, Thing)
        return result

    @classmethod
    def from_individual(cls, individual) -> Relation:
        """
        An individual as a point, i.e. the relation from the monoidal
        unit that holds of it alone.

        Parameters:
            individual : The `owlready2` individual.
        """
        result = cls([((), (individual, ))], 0, 1,
                     individual.namespace.world)
        result.name = individual.name
        result.diagram = point(individual, Thing)
        return result

    @classmethod
    def sparql(cls, query: str, dom: int, cod: int, world: World
               ) -> Relation:
        """
        The relation a SPARQL query defines, evaluated by the native
        engine of `owlready2` on the materialised graph -- run
        :func:`reason` first to query the entailed one. Each row is split
        into a pair after the first ``dom`` variables.

        Parameters:
            query : The SPARQL query, with one variable per wire.
            dom : The number of input wires.
            cod : The number of output wires.
            world : The world to ask.
        """
        return cls([(tuple(row[:dom]), tuple(row[dom:]))
                    for row in world.sparql(query)], dom, cod, world)

    def to_diagram(self) -> "Diagram":
        """
        The picture of a relation: the diagram of the syntax it was built
        from when there is one, and a box named after it otherwise -- a
        relation is extensional, so a composite forgets its history
        unless every part carried a picture.
        """
        if self.diagram is not None:
            return self.diagram
        return Box(
            getattr(self, "name", "?"),
            ob(self.dom * (Thing, )), ob(self.cod * (Thing, )))

    def draw(self, **params):
        """
        Draw the picture of a relation, see :meth:`to_diagram`.

        Parameters:
            params : Passed to :meth:`Diagram.draw`.
        """
        return self.to_diagram().draw(**params)


@factory
@dataclass
class Query(DistributiveAllegory, SymmetricCategory):
    """
    A morphism of the Karoubi envelope of :class:`Relation`, split at the
    coreflexives: the boundaries are tuples of predicates -- named OWL
    classes or compound class constructs, each the :func:`label` of its
    wire -- and the relation ``inside`` is normalised to ``e ; inside ;
    f`` between the coreflexives of the boundary, so that it only relates
    individuals the predicates provably hold of.

    Parameters:
        inside : The underlying :class:`Relation`, at the boundary
            arities.
        dom : The tuple of predicates for the domain.
        cod : The tuple of predicates for the codomain.
        normalise : Whether to normalise between the boundary
            coreflexives; the internal call sites pass ``False`` when the
            invariant already holds.

    Composing two queries whose predicates differ asks `HermiT` for the
    subsumption between them, wire by wire, and inserts each verdict as a
    :class:`Coercion` -- so ``>>`` runs entailment queries, a deliberate
    exception to composition being pure, and :attr:`no_reasoning` is the
    way to opt out. :meth:`validate` then raises on every coercion whose
    subsumption failed or was never checked.

    .. admonition:: Summary

        .. autosummary::

            id
            then
            tensor
            dagger
            meet
            join
            bottom
            spiders
            swap
            cups
            caps
            domain
            repeat
            relation
            at_thing
            validate
            from_property
            from_class
            from_individual

    Example
    -------
    >>> from owlready2 import Thing, World
    >>> onto = World().get_ontology("http://discopy.org/kennel.owl")
    >>> with onto:
    ...     class Dog(Thing): pass
    ...     class Person(Thing): pass
    ...     class owns(Person >> Dog): pass
    ...     rex, ada = Dog("rex"), Person("ada")
    ...     ada.owns = [rex]
    >>> owns = Query.from_property(onto.owns)
    >>> assert owns.relation.dom == owns.relation.cod == 1
    >>> assert Query.id(owns.dom) >> owns == owns
    >>> assert owns.at_thing() == owns.relation.split((Thing, ), (Thing, ))
    """
    inside: Relation
    dom: tuple
    cod: tuple

    reasoning = True

    def __init__(self, inside: Relation, dom: tuple, cod: tuple,
                 normalise: bool = True):
        assert_isinstance(inside, Relation)
        dom, cod = map(tuplify, (dom, cod))
        if (len(dom), len(cod)) != (inside.dom, inside.cod):
            raise AxiomError(messages.WRONG_ARITY.format(
                (inside.dom, inside.cod), (dom, cod)))
        if normalise:
            inside = boundary(dom, inside.world) >> inside\
                >> boundary(cod, inside.world)
        self.inside, self.dom, self.cod = inside, dom, cod
        self.diagram = None

    @property
    def relation(self) -> Relation:
        """ The underlying single-sorted relation, i.e. ``inside``. """
        return self.inside

    @property
    def world(self) -> World:
        """ The world the underlying relation lives over. """
        return self.inside.world

    @classproperty
    @contextmanager
    def no_reasoning(cls):
        """
        A context manager under which composition skips the entailment
        queries: the coercions it inserts carry ``entailed=None``, to be
        checked by :meth:`validate` later.
        """
        tmp, cls.reasoning = cls.reasoning, False
        try:
            yield
        finally:
            cls.reasoning = tmp

    def __str__(self):
        name = getattr(self, "name", type(self).__name__)
        dom = tuple(map(label, self.dom))
        cod = tuple(map(label, self.cod))
        return f"{name} : {dom and str(dom) or '()'} "\
            f"-> {cod and str(cod) or '()'}"

    def __bool__(self):
        return bool(self.inside)

    def __le__(self, other) -> bool:
        assert_isinstance(other, Query)
        assert_isparallel(self, other)
        return self.inside <= other.inside

    @classmethod
    def id(cls, dom: tuple = (), world: World = None) -> Query:
        """
        The identity on a split object, i.e. the coreflexive of its
        predicates.

        Parameters:
            dom : The tuple of predicates.
            world : The world, resolved from the predicates otherwise.
        """
        dom = tuplify(dom)
        world = world or find_world(dom) or owlready2.default_world
        result = cls(boundary(dom, world), dom, dom, normalise=False)
        result.diagram = Id(ob(dom))
        return result

    def then(self, *others: Query) -> Query:
        """
        Compose queries; where the predicates of the boundary differ,
        ask `HermiT` for the subsumption between them and insert the
        verdict as a :class:`Coercion` in between.

        Parameters:
            others : The queries to compose in sequence.
        """
        result = self
        for other in others:
            assert_isinstance(other, Query)
            if result.cod != other.dom:
                if len(result.cod) != len(other.dom):
                    assert_iscomposable(result, other)
                middle = self.factory.id((), result.world).tensor(*(
                    coercion(source, target, result.world)
                    for source, target in zip(result.cod, other.dom)))
                other = middle.then(other) if middle.cod != other.dom\
                    else _compose(middle, other)
            result = _compose(result, other)
        return result

    def tensor(self, *others: Query) -> Query:
        """
        The product of queries, concatenating their predicates.

        Parameters:
            others : The queries to tensor.
        """
        result = self
        for other in others:
            assert_isinstance(other, Query)
            step = self.factory(
                result.inside @ other.inside,
                result.dom + other.dom, result.cod + other.cod,
                normalise=False)
            step.diagram = combine(
                lambda left, right: left @ right,
                result.diagram, other.diagram)
            result = step
        return result

    __matmul__ = tensor

    def dagger(self) -> Query:
        """ The converse query, with the boundaries swapped. """
        result = self.factory(
            self.inside.dagger(), self.cod, self.dom, normalise=False)
        result.diagram = combine(
            lambda diagram: diagram.dagger(), self.diagram)
        return result

    def meet(self, *others: Query) -> Query:
        """
        The intersection of parallel queries, called with ``&``.

        Parameters:
            others : The other queries.
        """
        for other in others:
            assert_isinstance(other, Query)
            assert_isparallel(self, other)
        result = self.factory(
            self.inside.meet(*(other.inside for other in others)),
            self.dom, self.cod, normalise=False)
        result.diagram = combine(lambda *inside: (
            Diagram.spiders(1, len(inside), ob(self.dom))
            >> Id().tensor(*inside)
            >> Diagram.spiders(len(inside), 1, ob(self.cod))
            if len(inside) > 1 else inside[0]),
            self.diagram, *(other.diagram for other in others))
        return result

    def join(self, *others: Query) -> Query:
        """
        The union of parallel queries, called with ``|``.

        Parameters:
            others : The other queries.
        """
        for other in others:
            assert_isinstance(other, Query)
            assert_isparallel(self, other)
        result = self.factory(
            self.inside.join(*(other.inside for other in others)),
            self.dom, self.cod, normalise=False)
        result.diagram = combine(lambda *inside: (
            Bubble(*inside, dom=ob(self.dom), cod=ob(self.cod),
                   drawing_name="$\\vee$")
            if len(inside) > 1 else inside[0]),
            self.diagram, *(other.diagram for other in others))
        return result

    @classmethod
    def bottom(cls, dom: tuple, cod: tuple, world: World = None) -> Query:
        """
        The empty query between two tuples of predicates.

        Parameters:
            dom : The tuple of predicates for the domain.
            cod : The tuple of predicates for the codomain.
            world : The world, resolved from the predicates otherwise.
        """
        dom, cod = map(tuplify, (dom, cod))
        world = world or find_world(dom, cod) or owlready2.default_world
        result = cls(Relation.bottom(len(dom), len(cod), world),
                     dom, cod, normalise=False)
        result.diagram = Box("$\\bot$", ob(dom), ob(cod))
        return result

    @classmethod
    def spiders(cls, n_legs_in: int, n_legs_out: int, typ: tuple,
                world: World = None) -> Query:
        """
        The spiders on a tuple of predicates: the single-sorted spiders,
        normalised between the coreflexives of the boundary.

        Parameters:
            n_legs_in : The number of legs in.
            n_legs_out : The number of legs out.
            typ : The tuple of predicates on each leg.
            world : The world, resolved from the predicates otherwise.
        """
        typ = tuplify(typ)
        world = world or find_world(typ) or owlready2.default_world
        result = cls(
            Relation.spiders(n_legs_in, n_legs_out, len(typ), world),
            n_legs_in * typ, n_legs_out * typ)
        result.diagram = Diagram.spiders(
            n_legs_in, n_legs_out, ob(typ))
        return result

    @classmethod
    def copy(cls, typ: tuple, n: int = 2, world: World = None) -> Query:
        """
        The query copying every individual ``n`` times.

        Parameters:
            typ : The tuple of predicates to copy.
            n : The number of copies.
            world : The world, resolved from the predicates otherwise.
        """
        return cls.spiders(1, n, typ, world)

    @classmethod
    def swap(cls, left: tuple, right: tuple, world: World = None) -> Query:
        """
        The query exchanging two tuples of predicates.

        Parameters:
            left : The tuple of predicates on the left.
            right : The tuple of predicates on the right.
            world : The world, resolved from the predicates otherwise.
        """
        left, right = map(tuplify, (left, right))
        world = world or find_world(left, right) or owlready2.default_world
        result = cls(Relation.swap(len(left), len(right), world),
                     left + right, right + left)
        result.diagram = Diagram.swap(ob(left), ob(right))
        return result

    @classmethod
    def permutation(cls, xs, doms, world: World = None) -> Query:
        """
        The query permuting some tuples of predicates, the ``i``-th
        output being the ``xs[i]``-th input.

        Parameters:
            xs : A permutation of ``range(len(doms))``.
            doms : The tuples of predicates to permute.
            world : The world, resolved from the predicates otherwise.
        """
        xs, doms = list(xs), [tuplify(dom) for dom in doms]
        dom = sum(doms, ())
        world = world or find_world(dom) or owlready2.default_world
        return cls(Relation.permutation(
            xs, [len(one) for one in doms], world),
            dom, sum((doms[x] for x in xs), ()))

    @classmethod
    def cups(cls, left: tuple, right: tuple, world: World = None) -> Query:
        """
        The query bending two boundaries into none; predicates are
        self-dual so ``left`` and ``right`` must be equal.

        Parameters:
            left : The tuple of predicates on the left.
            right : The same tuple of predicates.
            world : The world, resolved from the predicates otherwise.
        """
        left, right = map(tuplify, (left, right))
        if left != right:
            raise AxiomError(messages.NOT_ADJOINT.format(left, right))
        world = world or find_world(left) or owlready2.default_world
        result = cls(Relation.cups(len(left), len(right), world),
                     left + right, ())
        result.diagram = Diagram.cups(ob(left), ob(right))
        return result

    @classmethod
    def caps(cls, left: tuple, right: tuple, world: World = None) -> Query:
        """ The dagger of :meth:`cups`. """
        return cls.cups(left, right, world).dagger()

    def domain(self) -> Query:
        """
        The coreflexive query on what a query is actually defined on.
        """
        result = self.factory(
            self.inside.domain(), self.dom, self.dom, normalise=False)
        result.diagram = combine(lambda diagram: (
            Diagram.spiders(1, 2, ob(self.dom)) >> Id(
                ob(self.dom)) @ (diagram >> Diagram.spiders(
                    1, 0, ob(self.cod)))), self.diagram)
        return result

    def codomain(self) -> Query:
        """ The :meth:`domain` of the converse query. """
        return self.dagger().domain()

    def repeat(self) -> Query:
        """
        The reflexive transitive closure of a query on one boundary,
        relative to the coreflexive of its predicates.
        """
        if self.dom != self.cod:
            raise AxiomError(messages.NOT_ENDO.format(self))
        result = self.factory.id(self.dom, self.world).join(self)
        while True:
            step = result.join(result >> result)
            if step == result:
                break
            result = step
        result.diagram = combine(
            lambda diagram: diagram.bubble(drawing_name="$\\ast$"),
            self.diagram)
        return result

    def at_thing(self) -> Query:
        """
        The query widened to ``owl:Thing`` on every wire -- the
        conversion back down to the single-sorted reading, as a query.
        """
        result = self.factory(
            self.inside, len(self.dom) * (Thing, ),
            len(self.cod) * (Thing, ), normalise=False)
        result.diagram = self.diagram
        return result

    @property
    def coercions(self) -> list:
        """ The coercions inside a query, without repetition. """
        return list({
            id(one.data): one.data
            for one in getattr(self.to_diagram(), "boxes", [])
            if isinstance(one.data, Coercion)}.values())

    def validate(self) -> Query:
        """
        Check the proof objects of the coercions inside a query and
        return it: a coercion never checked -- composed under
        :attr:`no_reasoning` -- is checked now, and one whose subsumption
        `HermiT` refuted raises.

        Raises:
            AxiomError : Whenever a coercion is not entailed.
        """
        lossy = []
        for one in self.coercions:
            if one.entailed is None:
                one.entailed = subsumes(one.source, one.target, one.world)
            if not one.entailed:
                lossy.append(one)
        if lossy:
            raise AxiomError(" and ".join(
                f"{label(one.source)} is not {label(one.target)}"
                for one in lossy))
        return self

    @classmethod
    def from_property(cls, prop, dom=None, cod=None) -> Query:
        """
        The query an OWL property defines, typed by what ``rdfs:domain``
        and ``rdfs:range`` declare: the raw relation of
        :meth:`Relation.from_property`, normalised between the
        coreflexives of the schema.

        Parameters:
            prop : The `owlready2` property.
            dom : The predicate to read it at, its ``rdfs:domain`` when
                it declares exactly one and ``owl:Thing`` otherwise.
            cod : The predicate it lands in, likewise from ``rdfs:range``.
        """
        schema_dom, schema_cod = schema(prop)
        dom = schema_dom if dom is None else dom
        cod = schema_cod if cod is None else cod
        result = cls(Relation.from_property(prop), (dom, ), (cod, ))
        result.name = prop.name
        result.diagram = box(prop, dom, cod)
        return result

    @classmethod
    def from_class(cls, entity, dom=None) -> Query:
        """
        The coreflexive query testing membership of a predicate, read at
        another one.

        Parameters:
            entity : The `owlready2` class or class construct.
            dom : The predicate to read it at, the construct itself by
                default -- in which case this is the identity on the
                split object, see :meth:`id`.
        """
        dom = entity if dom is None else dom
        world = expr_world(entity) or expr_world(dom)\
            or owlready2.default_world
        result = cls(extension(entity, world), (dom, ), (dom, ))
        result.name = label(entity)
        result.diagram = to_diagram(entity, dom)
        return result

    @classmethod
    def from_individual(cls, individual, cod=None) -> Query:
        """
        An individual as a point, typed by its first named class.

        Parameters:
            individual : The `owlready2` individual.
            cod : The predicate of the point, the individual's first
                named class by default.
        """
        cod = individual_class(individual) if cod is None else cod
        result = cls(Relation.from_individual(individual), (), (cod, ))
        result.name = individual.name
        result.diagram = point(individual, cod)
        return result

    def to_diagram(self) -> "Diagram":
        """
        The picture of a query, with every wire labelled by its
        predicate; a box named after it when the history is forgotten.
        """
        if self.diagram is not None:
            return self.diagram
        return Box(
            getattr(self, "name", "?"), ob(self.dom), ob(self.cod))

    def draw(self, **params):
        """
        Draw the picture of a query, see :meth:`to_diagram`.

        Parameters:
            params : Passed to :meth:`Diagram.draw`.
        """
        return self.to_diagram().draw(**params)


def _compose(left: Query, right: Query) -> Query:
    """ Strict composition of two queries with matching boundaries. """
    result = left.factory(
        left.inside >> right.inside, left.dom, right.cod, normalise=False)
    result.diagram = combine(
        lambda one, other: one >> other, left.diagram, right.diagram)
    return result


def boundary(preds: tuple, world: World) -> Relation:
    """
    The coreflexive of a tuple of predicates, i.e. the tensor of their
    :func:`extension` -- the identity of the split object they present.

    Parameters:
        preds : The tuple of predicates.
        world : The world whose individuals they hold of.
    """
    return Relation.id(0, world).tensor(*(
        extension(pred, world) for pred in preds))


class Coercion(Query):
    """
    The move between two predicates on the same individuals, carrying a
    proof object: the partial identity relating what provably satisfies
    both, together with `HermiT`'s verdict on whether the source is
    subsumed by the target -- ``entailed`` is ``True`` for a free
    coercion, ``False`` for a filter and ``None`` when composed under
    :attr:`Query.no_reasoning`, to be settled by :meth:`Query.validate`.

    Parameters:
        source : The predicate to come from.
        target : The predicate to go to.
        world : The world, resolved from the predicates otherwise.
    """
    def __init__(self, source, target, world: World = None):
        self.source, self.target = source, target
        world = world or expr_world(source) or expr_world(target)\
            or owlready2.default_world
        inside = extension(source, world).meet(extension(target, world))
        self.entailed = subsumes(source, target, world)\
            if type(self).reasoning else None
        super().__init__(inside, (source, ), (target, ), normalise=False)
        self.name = label(target)
        self.diagram = Box(
            label(target), ob((source, )), ob((target, )), data=self)


def coercion(source, target, world: World = None) -> Query:
    """
    The move between two predicates: the identity where they agree and a
    :class:`Coercion` otherwise, which is what :meth:`Query.then` puts
    between two queries that do not meet.

    Parameters:
        source : The predicate to come from.
        target : The predicate to go to.
        world : The world, resolved from the predicates otherwise.
    """
    if source == target:
        return Query.id((source, ), world)
    return Coercion(source, target, world)


def parallel(left: Query, right: Query) -> tuple:
    """
    Two queries as a parallel pair, widened to ``owl:Thing`` on every
    wire if their boundaries differ -- which is what an :class:`Axiom`
    between them needs.

    Parameters:
        left : One query.
        right : The other.
    """
    if left.is_parallel(right):
        return left, right
    left, right = left.at_thing(), right.at_thing()
    if not left.is_parallel(right):
        raise AxiomError(messages.NOT_PARALLEL.format(left, right))
    return left, right


def load(iri: str, world: World = None, path: str = None) -> Ontology:
    """
    Load an ontology from its base IRI, together with its imports.

    Parameters:
        iri : The base IRI, i.e. the URL the ontology lives at.
        world : The world to load it into, the default world otherwise.
        path : A local directory holding a copy of the ontology and its
            imports, see :func:`preload` -- e.g. when the URL is
            unreachable or the loading should not depend on it.

    Example
    -------
    >>> iri = ("https://spec.edmcouncil.org/fibo/ontology"
    ...        "/BE/OwnershipAndControl/OwnershipParties/")
    >>> onto = load(iri)  # doctest: +SKIP
    >>> from owlready2 import World
    >>> onto = load(iri, World(), path="test/fixtures/fibo")
    >>> onto.UltimateConsolidation
    OwnershipParties.UltimateConsolidation
    """
    world = world or owlready2.default_world
    if path is not None:
        preload(path, world)
    return world.get_ontology(iri).load()


def preload(path: str, world: World):
    """
    Load every ontology file under a directory into a world, offline: the
    files are read in dependency order, so an import between two of them
    never asks the network, and an import that no file declares -- say,
    an annotation vocabulary -- is stubbed as an empty ontology.

    The declared IRI and the imports of each file are read off its
    ``owl:Ontology`` element; the imports between the files must not
    form a cycle. A missing directory raises rather than falling back
    to the network, so a mistyped path fails here and not wherever the
    live ontologies first disagree with the copy.

    Parameters:
        path : The directory holding ``.rdf`` or ``.owl`` files.
        world : The world to load them into.
    """
    if not os.path.isdir(path):
        raise FileNotFoundError(path)
    files, imports = {}, {}
    for root, _, names in sorted(os.walk(path)):
        for name in sorted(names):
            if not name.endswith((".rdf", ".owl")):
                continue
            full = os.path.join(root, name)
            with open(full, encoding="utf-8") as handle:
                text = handle.read()
            match = re.search(r'<owl:Ontology rdf:about="([^"]+)"', text)
            if match is None:
                continue
            files[match.group(1)] = full
            imports[match.group(1)] = re.findall(
                r'<owl:imports rdf:resource="([^"]+)"', text)
    external = {dep for deps in imports.values() for dep in deps}\
        - set(files)
    for iri in sorted(external):
        world.get_ontology(iri).loaded = True
    remaining = dict(imports)
    while remaining:
        ready = [iri for iri, deps in sorted(remaining.items())
                 if all(dep not in remaining for dep in deps)]
        if not ready:
            raise ValueError(messages.CYCLIC_IMPORTS.format(
                ", ".join(sorted(remaining))))
        for iri in ready:
            world.get_ontology(
                "file://" + os.path.abspath(files[iri])).load()
            del remaining[iri]


def reason(world: World, infer_property_values: bool = True):
    """
    Run `HermiT` on a world so that what it entails can be read off it:
    class membership, subsumption and, by default, property values. This
    is the semantics of the module -- the constructors read what
    reasoning materialised, and nothing is concluded from absence.

    Assign to this to use another reasoner or other options. Note that
    HermiT accepts only the datatypes of the OWL 2 map, while published
    ontologies can range over others -- e.g. ``rdf:langString`` in the
    OMG Commons that FIBO imports -- so reasoning about them wants a
    curated copy, the way ``test/fixtures/fibo`` stands in for the
    modules that trip HermiT.

    Parameters:
        world : The world to reason about.
        infer_property_values : Whether to write entailed property values
            back into the world, so that :meth:`Relation.from_property`
            reads the entailed relation.
    """
    sync_reasoner_hermit(
        world, debug=0, infer_property_values=infer_property_values)


def consistent(world: World) -> bool:
    """
    Whether the ontologies of a world are consistent, by asking `HermiT`.

    Note that reasoning writes what it finds back into the world, and that
    an inconsistent world is left as it was.

    Parameters:
        world : The world to check.
    """
    try:
        reason(world)
        return True
    except OwlReadyInconsistentOntologyError:
        return False


BATCH = 32
"""
How many scratch defined classes :func:`deduced` gives one `HermiT` run:
classification cost grows quickly with the number of defined classes, so
a large batch is cut into runs of this size.
"""

fresh = iter(range(10 ** 12)).__next__
"""
The next number that no scratch defined class of this process has worn
yet: recreating a destroyed entity under the same IRI resurrects stale
state that the reasoner's write-back then cannot resolve.
"""


def deduced(exprs, world: World) -> list:
    """
    The individuals `HermiT` can prove each class construct holds of,
    sorted by IRI: one scratch defined class per construct, equivalent to
    it, classified by a run of :func:`reason` shared with up to
    :data:`BATCH` others and destroyed again -- so a batch costs a few
    reasoner calls, not one per construct.

    Parameters:
        exprs : The `owlready2` class constructs.
        world : The world whose ontologies say what is entailed.

    Example
    -------
    >>> from owlready2 import AllDisjoint, Not, Thing, World
    >>> onto = World().get_ontology("http://discopy.org/kennel.owl")
    >>> with onto:
    ...     class Dog(Thing): pass
    ...     class Person(Thing): pass
    ...     rex, ada = Dog("rex"), Person("ada")
    >>> deduced([Not(onto.Dog)], onto.world)  # nothing is provably not
    [()]
    >>> with onto:
    ...     _ = AllDisjoint([onto.Dog, onto.Person])
    >>> deduced([Not(onto.Dog)], onto.world)
    [(kennel.ada,)]
    """
    exprs = list(exprs)
    if len(exprs) > BATCH:
        return [found for start in range(0, len(exprs), BATCH)
                for found in deduced(exprs[start:start + BATCH], world)]
    scratch = world.get_ontology(SCRATCH)
    temps = []
    with scratch:
        for expr in exprs:
            temp = new_class(f"Deduced{fresh()}", (Thing, ))
            # A construct can only belong to one class, so clone it.
            temp.equivalent_to = [expr.__deepcopy__()]
            temps.append(temp)
    reason(world)
    results = [tuple(sorted(temp.instances(), key=lambda one: one.iri))
               for temp in temps]
    for temp in temps:
        dismiss(temp, world)
    return results


def dismiss(temp: ThingClass, world: World):
    """
    Destroy a scratch defined class, first dropping every equivalence
    triple about it across the world: the reasoner writes what it entails
    into an ontology of its own, and `owlready2` trips over destroying an
    entity still equivalent to a class construct.

    Parameters:
        temp : The scratch defined class.
        world : The world it was classified in.
    """
    for onto in list(world.ontologies.values()):
        onto._del_obj_triple_spo(temp.storid, owl_equivalentclass, None)
        onto._del_obj_triple_spo(None, owl_equivalentclass, temp.storid)
    destroy_entity(temp)


def subsumes(left, right, world: World) -> bool:
    """
    Whether the ontologies of a world entail that one predicate is
    subsumed by another, by asking `HermiT` -- the proof object a
    :class:`Coercion` carries. A construct is classified through a
    scratch defined class the way :func:`deduced` does.

    Parameters:
        left : The predicate to be subsumed.
        right : The predicate to subsume it.
        world : The world whose ontologies say what is entailed.

    Example
    -------
    >>> from owlready2 import Thing, World
    >>> onto = World().get_ontology("http://discopy.org/kennel.owl")
    >>> with onto:
    ...     class Dog(Thing): pass
    ...     class Person(Thing): pass
    ...     class owns(Person >> Dog): pass
    >>> assert subsumes(onto.Person & onto.owns.some(onto.Dog),
    ...                 onto.Person, onto.world)
    >>> assert not subsumes(onto.Person,
    ...                     onto.Person & onto.owns.some(onto.Dog),
    ...                     onto.world)
    """
    scratch, sides, temps = world.get_ontology(SCRATCH), [], []
    with scratch:
        for expr in (left, right):
            if expr is Thing or declared(expr, ThingClass):
                sides.append(expr)
            else:
                temp = new_class(f"Subsumed{fresh()}", (Thing, ))
                # A construct can only belong to one class, so clone it.
                temp.equivalent_to = [expr.__deepcopy__()]
                sides.append(temp)
                temps.append(temp)
    reason(world)
    result = issubclass(sides[0], sides[1])
    for temp in temps:
        dismiss(temp, world)
    return result


def relations(prop) -> dict:
    """
    The pairs an OWL property holds, grouped by subject: its own and
    those of the subproperties below it, which every pair entails but
    `owlready2` does not materialise upward; an
    :class:`Inverse <owlready2.class_construct.Inverse>` groups its
    property the other way around.

    Parameters:
        prop : The `owlready2` property, or the inverse of one.
    """
    if isinstance(prop, Inverse):
        pairs = ((y, x) for x, ys in relations(prop.property).items()
                 for y in ys)
    else:
        pairs = (pair for sub in prop.descendants()
                 for pair in sub.get_relations())
    result = {}
    for x, y in pairs:
        result.setdefault(x, set()).add(y)
    return result


def satisfying(expr, world: World) -> set:
    """
    The individuals a predicate provably holds of: the materialised
    members of a named class -- the entailed ones once :func:`reason` has
    run -- and what `HermiT` :func:`deduced` for a construct. A
    complement, a universal or a cardinality holds of an individual only
    when the ontology entails it, never for want of information.

    Parameters:
        expr : The `owlready2` class or class construct.
        world : The world whose ontologies say what is entailed.
    """
    if expr is Thing:
        return set(instances(Thing, world))
    if isinstance(expr, ThingClass):
        return set(instances(expr))
    return set(deduced([expr], world)[0])


def extension(expr, world: World = None) -> Relation:
    """
    A predicate as a coreflexive of the single-sorted category: the
    partial identity, at arity one, on the individuals :func:`satisfying`
    it -- the idempotent that :class:`Query` splits.

    Parameters:
        expr : The `owlready2` class or class construct.
        world : The world, resolved from ``expr`` otherwise.

    Example
    -------
    >>> from owlready2 import Thing, World
    >>> onto = World().get_ontology("http://discopy.org/kennel.owl")
    >>> with onto:
    ...     class Dog(Thing): pass
    ...     class Person(Thing): pass
    ...     class owns(Person >> Dog): pass
    ...     rex, ada, bob = Dog("rex"), Person("ada"), Person("bob")
    ...     ada.owns = [rex]
    >>> dog_owners = extension(onto.owns.some(onto.Dog))
    >>> assert [x.name for (x, ), _ in dog_owners.inside] == ["ada"]
    >>> assert dog_owners <= extension(onto.Person)
    """
    world = world or expr_world(expr) or owlready2.default_world
    result = Relation(
        [2 * ((one, ), ) for one in satisfying(expr, world)], 1, 1, world)
    result.name = label(expr)
    result.diagram = to_diagram(expr, Thing)
    return result


def expr_world(expr) -> World:
    """
    The world of the first named class or property inside an OWL class
    construct, or ``None`` for ``owl:Thing`` alone.

    Parameters:
        expr : The `owlready2` class or class construct.
    """
    if declared(expr, ThingClass):
        return expr.namespace.world
    if isinstance(expr, (And, Or)):
        return next((world for one in expr.Classes
                     for world in [expr_world(one)] if world), None)
    if isinstance(expr, Not):
        return expr_world(expr.Class)
    if isinstance(expr, OneOf):
        return next((one.namespace.world for one in expr.instances), None)
    if isinstance(expr, Restriction):
        prop = expr.property
        prop = prop.property if isinstance(prop, Inverse) else prop
        return None if isinstance(prop, str) else prop.namespace.world
    return None


def find_world(*typs: tuple) -> World:
    """
    The world of the first named class or property in some tuples of
    predicates, or ``None`` when there is nothing but ``owl:Thing`` to
    ask.

    Parameters:
        typs : The tuples of predicates.
    """
    for typ in typs:
        for pred in typ:
            world = expr_world(pred)
            if world is not None:
                return world
    return None


def combine(operation, *diagrams):
    """
    Apply an operation to some pictures, or give up: ``None`` -- a
    relation whose history is forgotten -- whenever one of them is.

    Parameters:
        operation : The operation on diagrams.
        diagrams : The pictures, possibly ``None``.
    """
    return None if any(one is None for one in diagrams)\
        else operation(*diagrams)


def label(entity) -> str:
    """
    An OWL entity or class construct as a mathematician would write it on
    the board: intersection is :math:`\\sqcap`, union :math:`\\sqcup`,
    complement :math:`\\neg`, a quantifier follows its property, a
    cardinality precedes it and an inverse takes a converse breve.

    Parameters:
        entity : The `owlready2` entity or class construct.

    Example
    -------
    >>> from owlready2 import Thing, World
    >>> onto = World().get_ontology("http://discopy.org/kennel.owl")
    >>> with onto:
    ...     class Dog(Thing): pass
    ...     class Person(Thing): pass
    ...     class owns(Person >> Dog): pass
    ...     rex = Dog("rex")
    >>> print(label(Person & Not(owns.some(Dog) | owns.value(rex))))
    Person ⊓ ¬(∃owns.Dog ⊔ ∃owns.{rex})
    >>> print(label(Inverse(owns).min(2, Person | Dog)))
    ≥2 owns˘.(Person ⊔ Dog)
    """
    sub = lambda one: f"({label(one)})"\
        if isinstance(one, (And, Or)) else label(one)
    if entity is Thing:
        return "Thing"
    if isinstance(entity, (ThingClass, Thing)) or declared(
            entity, owlready2.PropertyClass):
        return entity.name
    if isinstance(entity, Inverse):
        return sub(entity.property) + "˘"
    if isinstance(entity, And):
        return " ⊓ ".join(map(sub, entity.Classes))
    if isinstance(entity, Or):
        return " ⊔ ".join(map(sub, entity.Classes))
    if isinstance(entity, Not):
        return "¬" + sub(entity.Class)
    if isinstance(entity, OneOf):
        return "{" + ", ".join(one.name for one in entity.instances) + "}"
    if isinstance(entity, Restriction):
        prop = label(entity.property)
        if entity.type == HAS_SELF:
            return f"∃{prop}.Self"
        if entity.type == VALUE:
            value = getattr(entity.value, "name", str(entity.value))
            return f"∃{prop}.{{{value}}}"
        filler = sub(entity.value)
        if entity.type == SOME:
            return f"∃{prop}.{filler}"
        if entity.type == ONLY:
            return f"∀{prop}.{filler}"
        symbol = {MIN: "≥", MAX: "≤", EXACTLY: "="}[entity.type]
        return f"{symbol}{entity.cardinality} {prop}.{filler}"
    if isinstance(entity, type):
        return entity.__name__
    return str(entity)


def ob(typ=None) -> Ty:
    """
    A tuple of OWL classes or class constructs as a type with one
    :class:`Wire` per predicate -- the predicates-as-types reading of a
    boundary.

    Parameters:
        typ : The predicate or tuple of predicates, ``owl:Thing`` by
            default.
    """
    typ = (Thing, ) if typ is None else tuplify(typ)
    return Ty(*map(Wire, typ))


def schema(prop) -> tuple:
    """
    What ``rdfs:domain`` and ``rdfs:range`` say an OWL property is
    defined on and lands in: the class when there is exactly one named
    one and ``owl:Thing`` otherwise, swapped for an inverse.

    Parameters:
        prop : The `owlready2` property, or the inverse of one.
    """
    if isinstance(prop, Inverse):
        return schema(prop.property)[::-1]
    only = lambda classes: \
        classes[0] if len(classes) == 1 and declared(
            classes[0], ThingClass) else Thing
    return only(prop.domain), only(prop.range)


def box(prop, dom: ThingClass = None, cod: ThingClass = None
        ) -> Diagram:
    """
    An OWL property as a box between predicates, an inverse as the dagger
    of its box.

    Parameters:
        prop : The `owlready2` property, or the inverse of one.
        dom : The predicate to read it as defined on, its ``rdfs:domain``
            when it declares exactly one and ``owl:Thing`` otherwise.
        cod : The predicate it lands in, likewise from ``rdfs:range``.
    """
    if isinstance(prop, Inverse):
        return box(prop.property, cod, dom).dagger()
    schema_dom, schema_cod = schema(prop)
    dom = schema_dom if dom is None else dom
    cod = schema_cod if cod is None else cod
    return Box(prop.name, ob(dom), ob(cod), data=prop)


def individual_class(individual) -> ThingClass:
    """
    The first named class of an individual by IRI, ``owl:Thing`` when it
    has none.

    Parameters:
        individual : The `owlready2` individual.
    """
    named = sorted((one for one in individual.is_a
                    if declared(one, ThingClass)),
                   key=lambda one: one.iri)
    return named[0] if named else Thing


def point(individual, cod: ThingClass = None) -> Box:
    """
    An individual as a state, i.e. a box from the monoidal unit into its
    predicate.

    Parameters:
        individual : The `owlready2` individual.
        cod : The predicate of the point, the individual's first named
            class by default.
    """
    cod = individual_class(individual) if cod is None else cod
    return Box(individual.name, Ty(), ob(cod), data=individual)


def to_diagram(source, dom: ThingClass = None) -> Diagram:
    """
    An OWL entity or class construct as a diagram, read off the syntax
    the ontology itself keeps: an individual is a :func:`point`, a
    property a :func:`box`, and a class construct the coreflexive that
    tests it -- intersection is composition, union and complement are
    bubbles, a quantifier follows its property and discards.

    Parameters:
        source : The `owlready2` individual, property, class or class
            construct.
        dom : The predicate a class construct is read at, itself for a
            named class and ``owl:Thing`` otherwise.

    Example
    -------
    >>> from owlready2 import Thing, World
    >>> onto = World().get_ontology("http://discopy.org/kennel.owl")
    >>> with onto:
    ...     class Dog(Thing): pass
    ...     class Person(Thing): pass
    ...     class owns(Person >> Dog): pass
    >>> to_diagram(onto.Person & Not(onto.owns.some(onto.Dog))).draw(
    ...     doctest="docs/_static/owl/dogless-person.svg")

    .. image:: /_static/owl/dogless-person.svg
        :align: center
    """
    if isinstance(source, Thing):
        return point(source)
    if isinstance(source, (ObjectPropertyClass, Inverse)):
        return box(source)
    if dom is None:
        dom = source if declared(source, ThingClass) else Thing
    typ = ob(dom)
    if source is Thing or source is dom:
        return Id(typ)
    if isinstance(source, ThingClass):
        return Box(source.name, typ, typ, data=source)
    if isinstance(source, And):
        return Id(typ).then(*(
            to_diagram(one, dom) for one in source.Classes))
    if isinstance(source, Or):
        return Bubble(
            *(to_diagram(one, dom) for one in source.Classes),
            dom=typ, cod=typ, drawing_name="$\\vee$")
    if isinstance(source, Not):
        return to_diagram(source.Class, dom).bubble(drawing_name=NEGATION)
    if isinstance(source, OneOf):
        names = ", ".join(one.name for one in source.instances)
        return Box("{" + names + "}", typ, typ, data=source)
    if isinstance(source, Restriction):
        return restriction_diagram(source, dom)
    raise NotImplementedError(messages.NOT_IN_DICTIONARY.format(source))


def restriction_diagram(source: Restriction, dom: ThingClass
                        ) -> Diagram:
    """
    An OWL property restriction as a coreflexive diagram, the
    :class:`Restriction <owlready2.class_construct.Restriction>` case of
    :func:`to_diagram`: keep the wire, follow the property on a copy and
    ask the branch for the filler.

    Parameters:
        source : The `owlready2` restriction.
        dom : The predicate the restriction is read at.
    """
    typ, prop = ob(dom), source.property
    if isinstance(prop, str):  # a reference left unresolved
        raise NotImplementedError(messages.NOT_IN_DICTIONARY.format(source))
    _, target = schema(prop)
    arrow, target_typ = box(prop, dom, target), ob(target)
    spiders = Diagram.spiders
    keep = lambda branch: spiders(1, 2, typ)\
        >> Id(typ) @ (branch >> spiders(1, 0, target_typ))
    if source.type == HAS_SELF:
        return spiders(1, 2, typ)\
            >> box(prop, dom, dom) @ typ >> spiders(2, 1, typ)
    if source.type == VALUE:
        if not isinstance(source.value, Thing):  # a literal, not a point
            raise NotImplementedError(
                messages.NOT_IN_DICTIONARY.format(source))
        return spiders(1, 2, typ) >> Id(typ)\
            @ (box(prop, dom, individual_class(source.value))
               >> point(source.value).dagger())
    filler = to_diagram(source.value, target)
    if source.type == SOME:
        return keep(arrow >> filler)
    if source.type == ONLY:
        negated = filler.bubble(drawing_name=NEGATION)
        return keep(arrow >> negated).bubble(drawing_name=NEGATION)
    at_least = lambda n: Id(typ) if n == 0\
        else keep(arrow >> filler) if n == 1\
        else spiders(1, n + 1, typ) >> Id(typ) @ (
            Id().tensor(*(n * [arrow >> filler]))
            >> Box("$\\neq$", target_typ ** n, Ty()))
    if source.type == MIN:
        return at_least(source.cardinality)
    if source.type == MAX:
        return at_least(source.cardinality + 1).bubble(
            drawing_name=NEGATION)
    assert source.type == EXACTLY
    return at_least(source.cardinality) >> at_least(
        source.cardinality + 1).bubble(drawing_name=NEGATION)


class Axiom(cat.Equation):
    """
    What an ontology says about some parallel relations: an inclusion
    when the symbol is :data:`INCLUSION`, an equation when it is ``"="``.

    Casting to ``bool`` checks the inclusion of the entailed extensions:
    ``False`` is a sound refutation -- the world entails a concrete
    counterexample pair -- while ``True`` says no entailed counterexample
    exists, which is necessary for the axiom to be entailed but not
    sufficient; :func:`subsumes` asks the exact question of two
    predicates.

    Parameters:
        terms : The relations it relates.
        symbol : :data:`INCLUSION` or ``"="``.
        source : The `owlready2` entity or construct it came from.

    Example
    -------
    >>> from owlready2 import Thing, World
    >>> onto = World().get_ontology("http://discopy.org/kennel.owl")
    >>> with onto:
    ...     class Dog(Thing): pass
    ...     class Person(Thing): pass
    ...     class owns(Person >> Dog): pass
    ...     rex, toto = Dog("rex"), Dog("toto")
    ...     ada = Person("ada")
    ...     ada.owns = [rex]
    >>> web = Relation.from_property(onto.owns)
    >>> assert Axiom(web.dagger() >> web, extension(onto.Dog))
    >>> assert not Axiom(extension(onto.Dog), web.dagger() >> web)
    """
    def __init__(self, *terms: Relation, symbol: str = INCLUSION,
                 symbols=None, source=None):
        super().__init__(*terms, symbol=symbol, symbols=symbols)
        self.source = source

    def __bool__(self):
        return all(
            left <= right if symbol == INCLUSION else left == right
            for left, right, symbol
            in zip(self.terms, self.terms[1:], self.symbols))

    def __str__(self):
        symbols = ["<=" if one == INCLUSION else one for one in self.symbols]
        return " ".join(sum(
            ([str(term), symbol]
             for term, symbol in zip(self.terms, symbols)),
            [])[:-1])

    @property
    def equation(self) -> frobenius.Equation:
        """
        The pictures of the terms with the symbol in between, an
        :class:`frobenius.Equation` that knows how to display itself, see
        :meth:`Relation.to_diagram`.
        """
        return frobenius.Equation(
            *(term.to_diagram() for term in self.terms),
            symbols=self.symbols)

    def draw(self, **params):
        """
        Draw the pictures of the terms with the symbol in between, see
        :attr:`equation`.

        Parameters:
            params : Passed to :meth:`frobenius.Equation.draw`.
        """
        return self.equation.draw(**params)


def coreflexive(expr, members: tuple, world: World) -> Relation:
    """
    The coreflexive of a predicate from members already retrieved, e.g.
    by a batched :func:`deduced` -- what :func:`extension` computes when
    it retrieves for itself.

    Parameters:
        expr : The `owlready2` class or class construct.
        members : The individuals the predicate provably holds of.
        world : The world they live in.
    """
    result = Relation([2 * ((one, ), ) for one in members], 1, 1, world)
    result.name = label(expr)
    result.diagram = to_diagram(expr, Thing)
    return result


def class_axioms(entity: ThingClass, retrieved: dict = None) -> list[Axiom]:
    """
    What an ontology says about a class, as :class:`Axiom` on relations
    over ``owl:Thing``: one inclusion per superclass or restriction and
    one equation per equivalence, skipping what is outside the
    dictionary and the scratch classes a reasoner run may have written
    back among the parents, which are never rules of the knowledge base.

    Parameters:
        entity : The `owlready2` class.
        retrieved : Members per construct already retrieved by a batched
            :func:`deduced`, so that :func:`axioms` runs `HermiT` once
            per ontology rather than once per construct.
    """
    world = entity.namespace.world
    lookup = lambda expr: (
        extension(expr, world) if retrieved is None
        or isinstance(expr, ThingClass)
        else coreflexive(expr, retrieved[id(expr)], world))
    left, result = extension(entity, world), []
    for parents, symbol in ((entity.is_a, INCLUSION),
                            (entity.equivalent_to, "=")):
        for parent in parents:
            if isinstance(parent, ThingClass):
                if parent is Thing or parent.iri.startswith(SCRATCH):
                    continue
            elif not compilable(parent):
                continue
            result.append(Axiom(
                left, lookup(parent), symbol=symbol,
                source=(entity, parent)))
    return result


def property_axioms(entity: ObjectPropertyClass) -> list[Axiom]:
    """
    What an ontology says about an object property, as :class:`Axiom` on
    relations over ``owl:Thing``: its characteristics are the classical
    ones -- an inverse is a converse, transitivity is a composite included
    in the relation, functionality is the converse composite under the
    identity -- and its domain and range bound its :meth:`Relation.domain`
    and :meth:`Relation.codomain`.

    Parameters:
        entity : The `owlready2` object property.
    """
    world = entity.namespace.world
    relation, result = Relation.from_property(entity, world), []
    identity = Relation.id(1, world)
    bottom = Relation.bottom(1, 1, world)
    source = entity
    result.extend(
        Axiom(relation, Relation.from_property(parent, world),
              source=source)
        for parent in entity.is_a if declared(parent, ObjectPropertyClass))
    result.extend(
        Axiom(relation, Relation.from_property(other, world),
              symbol="=", source=source)
        for other in entity.equivalent_to
        if declared(other, ObjectPropertyClass))
    if entity.inverse_property is not None:
        result.append(Axiom(
            relation.dagger(),
            Relation.from_property(entity.inverse_property, world),
            symbol="=", source=source))
    characteristics = (
        (TransitiveProperty, relation >> relation, relation, INCLUSION),
        (SymmetricProperty, relation.dagger(), relation, "="),
        (AsymmetricProperty,
         relation.meet(relation.dagger()), bottom, "="),
        (ReflexiveProperty, identity, relation, INCLUSION),
        (IrreflexiveProperty, relation.meet(identity), bottom, "="),
        (FunctionalProperty,
         relation.dagger() >> relation, identity, INCLUSION),
        (InverseFunctionalProperty,
         relation >> relation.dagger(), identity, INCLUSION))
    result.extend(
        Axiom(left, right, symbol=symbol, source=source)
        for characteristic, left, right, symbol in characteristics
        if issubclass(entity, characteristic))
    result.extend(
        Axiom(identity.then(*(
            Relation.from_property(step, world)
            for step in chain.properties)), relation, source=source)
        for chain in entity.get_property_chain()
        if all(isinstance(step, ObjectPropertyClass)
               for step in chain.properties))  # a step may be unresolved
    for classes, side in ((entity.domain, relation.domain()),
                          (entity.range, relation.codomain())):
        if len(classes) == 1 and declared(classes[0], ThingClass):
            result.append(Axiom(
                side, extension(classes[0], world), source=source))
    return result


def disjoint_axioms(ontology: Ontology, retrieved: dict = None)\
        -> list[Axiom]:
    """
    The disjointness declarations of an ontology, as one
    empty-intersection equation per pair of disjoint classes, skipping
    the pairs with a member outside the dictionary.

    Parameters:
        ontology : The `owlready2` ontology.
        retrieved : Members per construct already retrieved by a batched
            :func:`deduced`, see :func:`class_axioms`.
    """
    world = ontology.world
    lookup = lambda expr: (
        extension(expr, world)
        if retrieved is None or isinstance(expr, ThingClass)
        else coreflexive(expr, retrieved[id(expr)], world))
    bottom = Relation.bottom(1, 1, world)
    return [
        Axiom(lookup(left).meet(lookup(right)), bottom,
              symbol="=", source=disjoint)
        for disjoint in ontology.disjoint_classes()
        for index, left in enumerate(disjoint.entities)
        for right in disjoint.entities[index + 1:]
        if (isinstance(left, ThingClass) or compilable(left))
        and (isinstance(right, ThingClass) or compilable(right))]


def constructs_of(ontology: Ontology) -> list:
    """
    The class constructs an ontology's axioms mention -- the parents and
    equivalents of its classes and the members of its disjointness
    declarations -- filtered to the :func:`compilable` ones, i.e. what
    :func:`axioms` sends to a batched :func:`deduced`.

    Parameters:
        ontology : The `owlready2` ontology.
    """
    result = [
        parent for cls in ontology.classes()
        for parents in (cls.is_a, cls.equivalent_to)
        for parent in parents
        if parent is not Thing
        and not isinstance(parent, ThingClass) and compilable(parent)]
    result += [
        one for disjoint in ontology.disjoint_classes()
        for one in disjoint.entities
        if not isinstance(one, ThingClass) and compilable(one)]
    return result


def axioms(entity, retrieved: dict = None) -> list[Axiom]:
    """
    The rules of a loaded knowledge base, compiled to :class:`Axiom` --
    each a :class:`cat.Equation` between relations, whose
    :attr:`Axiom.equation` draws itself. An entity gives what the
    ontology says about it, an ontology every rule it declares --
    including one empty-intersection equation per pair of disjoint
    classes -- and a whole :class:`World <owlready2.namespace.World>`
    the rules of every ontology loaded into it, each class and property
    compiled once however many modules mention it. The class constructs
    are retrieved by one batched :func:`deduced`, so a whole world costs
    a few `HermiT` runs, not one per rule. SWRL rules are not compiled:
    FIBO's ownership-and-control modules declare none, and they wait on
    data properties.

    Parameters:
        entity : An `owlready2` world, ontology, class or object
            property.
        retrieved : Members per construct already retrieved by a batched
            :func:`deduced`, the way the world branch hands them to the
            ontology branch.

    Example
    -------
    >>> from owlready2 import Thing, World
    >>> onto = World().get_ontology("http://discopy.org/kennel.owl")
    >>> with onto:
    ...     class Dog(Thing): pass
    ...     class Person(Thing): pass
    ...     class owns(Person >> Dog): pass
    ...     rex, ada = Dog("rex"), Person("ada")
    ...     ada.owns = [rex]
    >>> assert all(axioms(onto))  # no entailed counterexample
    >>> assert len(axioms(onto.world)) == len(axioms(onto))
    """
    if isinstance(entity, World):
        ontologies = [
            onto for iri, onto in entity.ontologies.items()
            if iri.startswith("http")
            and not iri.startswith((SCRATCH, "http://inferrences/"))]
        constructs = list({id(construct): construct
                           for onto in ontologies
                           for construct in constructs_of(onto)}.values())
        members = deduced(constructs, entity) if constructs else []
        retrieved = {id(expr): found
                     for expr, found in zip(constructs, members)}
        classes = {cls.iri: cls
                   for onto in ontologies for cls in onto.classes()}
        properties = {
            prop.iri: prop
            for onto in ontologies for prop in onto.object_properties()}
        result = [axiom for cls in classes.values()
                  for axiom in class_axioms(cls, retrieved)]
        result += [axiom for prop in properties.values()
                   for axiom in property_axioms(prop)]
        result += [axiom for onto in ontologies
                   for axiom in disjoint_axioms(onto, retrieved)]
        return result
    if isinstance(entity, Ontology):
        world = entity.world
        if retrieved is None:
            constructs = constructs_of(entity)
            members = deduced(constructs, world) if constructs else []
            retrieved = {id(expr): found
                         for expr, found in zip(constructs, members)}
        result = [axiom for cls in entity.classes()
                  for axiom in class_axioms(cls, retrieved)]
        result += [axiom for prop in entity.object_properties()
                   for axiom in property_axioms(prop)]
        return result + disjoint_axioms(entity, retrieved)
    if isinstance(entity, ThingClass):
        return class_axioms(entity)
    assert_isinstance(entity, ObjectPropertyClass)
    return property_axioms(entity)


def compilable(expr) -> bool:
    """
    Whether a class construct is inside the dictionary, i.e. whether
    :func:`to_diagram` can draw it -- what :func:`axioms` checks before
    sending it to a batched :func:`deduced`.

    Parameters:
        expr : The `owlready2` class or class construct.
    """
    try:
        to_diagram(expr, Thing)
        return True
    except NotImplementedError:
        return False
