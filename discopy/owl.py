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
  named classes or compound class expressions, labelled the way a
  mathematician would write them -- and a morphism is a relation ``r``
  normalised to ``e ; r ; f`` between the coreflexives of its boundary.
  Composing two queries whose predicates do not meet asks the reasoner
  whether one predicate is subsumed by the other and inserts the verdict
  as a :class:`Coercion` in between -- a proof object, drawn as a box
  exactly where the predicate changes.

Everything is deductive and delegated through `owlapy`_: a :class:`World`
pairs an ontology with the reasoner that judges it -- `HermiT`_ by
default, through the bundled `owlapi`_ bridge, so complete reasoning
needs a Java runtime -- and the constructors read what it entails, never
what merely fails to be said. :func:`deduced` retrieves the entailed
members of a class expression, :func:`subsumes` decides the inclusion of
two predicates, :func:`consistent` checks the world and
:meth:`Relation.sparql` queries the asserted graph with `rdflib`.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    World
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

        preserve_list_order
        load
        reason
        consistent
        deduced
        subsumes
        declared
        instances
        carrier
        relations
        satisfying
        extension
        coercion
        parallel
        class_axioms
        property_axioms
        axioms
        label
        ob
        peel
        demorgan
        distinct
        schema
        box
        point
        individual_class
        to_diagram
        restriction_diagram
        combine

.. _owlapy: https://dice-group.github.io/owlapy/
.. _owlapi: https://owlcs.github.io/owlapi/
.. _HermiT: http://www.hermit-reasoner.com/

Example
-------
>>> world = World("http://discopy.org/kennel.owl#")
>>> Dog, Person = world.owl_class("Dog"), world.owl_class("Person")
>>> owns = world.owl_property("owns", Person, Dog)
>>> rex, ada = world.individual("rex", Dog), world.individual("ada", Person)
>>> world.relate(ada, owns, rex)
>>> web = Relation.from_property(owns, world)
>>> print(web)
owns : Thing -> Thing
>>> print(Query.from_property(owns, world))
owns : ('Person',) -> ('Dog',)
>>> assert Query.from_property(owns, world).relation <= web
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from itertools import product

import jpype
from owlapy.class_expression import (
    OWLClass, OWLClassExpression, OWLNothing, OWLObjectAllValuesFrom,
    OWLObjectCardinalityRestriction, OWLObjectComplementOf,
    OWLObjectExactCardinality, OWLObjectHasSelf, OWLObjectHasValue,
    OWLObjectIntersectionOf, OWLObjectMaxCardinality,
    OWLObjectMinCardinality, OWLObjectOneOf, OWLObjectSomeValuesFrom,
    OWLObjectUnionOf, OWLThing)
from owlapy.iri import IRI
from owlapy.owl_axiom import (
    OWLAsymmetricObjectPropertyAxiom, OWLClassAssertionAxiom,
    OWLDeclarationAxiom, OWLDisjointClassesAxiom,
    OWLEquivalentClassesAxiom, OWLEquivalentObjectPropertiesAxiom,
    OWLFunctionalObjectPropertyAxiom,
    OWLInverseFunctionalObjectPropertyAxiom,
    OWLInverseObjectPropertiesAxiom, OWLIrreflexiveObjectPropertyAxiom,
    OWLObjectPropertyAssertionAxiom, OWLObjectPropertyDomainAxiom,
    OWLObjectPropertyRangeAxiom, OWLReflexiveObjectPropertyAxiom,
    OWLSubClassOfAxiom, OWLSubObjectPropertyOfAxiom,
    OWLSubPropertyChainAxiom, OWLSymmetricObjectPropertyAxiom,
    OWLTransitiveObjectPropertyAxiom)
from owlapy.owl_individual import OWLNamedIndividual
from owlapy.owl_ontology import SyncOntology
from owlapy.owlapi_mapper import OWLAPIMapper
from owlapy.owl_property import OWLObjectInverseOf, OWLObjectProperty
from owlapy.owl_reasoner import SyncReasoner

from discopy import cat, frobenius, messages
from discopy.abc import DistributiveAllegory, SymmetricCategory
from discopy.utils import (
    AxiomError, assert_iscomposable, assert_isinstance, assert_isparallel,
    classproperty, factory, tuplify)


Thing = OWLThing
""" The one generating object, every individual's class. """

Nothing = OWLNothing
""" The empty class, what an unsatisfiable predicate is equivalent to. """

INCLUSION = "$\\sqsubseteq$"
""" The symbol of a 2-cell that is an inclusion, not an equation. """

NEGATION = "$\\neg$"
""" The drawing name of the bubble for a complement. """


def preserve_list_order():
    """
    Re-register `owlapy`_'s list mappers without their reversal:
    ``OWLAPIMapper`` reverses every list it maps, both from Python to
    Java and back, which keeps its own round trips looking consistent
    while the ontology holds -- and `HermiT`_ reasons with -- every
    property chain backwards, and a chain loaded from a file reads
    backwards in Python. Dropping the reversal on both sides keeps the
    round trips identical and puts
    ``SubObjectPropertyOf(ObjectPropertyChain(r, s), t)``, i.e.
    ``r ; s <= t``, the same way on both sides of the bridge.
    """
    array_list = jpype.JClass("java.util.ArrayList")

    def from_java(self, items):
        return [self.map_(item) for item in list(items)]

    def to_java(self, items):
        result = array_list()
        for item in items or ():
            result.add(self.map_(item))
        return result

    for kind in ("List", "Set", "LinkedHashSet", "ArrayList"):
        OWLAPIMapper.map_.register(
            jpype.JClass(f"java.util.{kind}"), from_java)
    for kind in (list, set, frozenset, tuple):
        OWLAPIMapper.map_.register(kind, to_java)


preserve_list_order()


def declared(entity, kind: type) -> bool:
    """
    Whether an entity is one an ontology declared rather than one of OWL's
    own vocabulary, i.e. whether it is worth talking about.

    Parameters:
        entity : The candidate.
        kind : The class it has to be, i.e. a class or a property.
    """
    return isinstance(entity, kind)\
        and not entity.iri.as_str().startswith("http://www.w3.org/2002/07/")


def name_of(entity) -> str:
    """
    The short name of an OWL entity, i.e. the last segment of its IRI.

    Parameters:
        entity : The `owlapy` class, property or individual.
    """
    return entity.iri.remainder


def iris(individuals: tuple) -> tuple[str, ...]:
    """
    The IRIs of a tuple of individuals, the sort key that keeps every
    relation deterministic.

    Parameters:
        individuals : The individuals.
    """
    return tuple(one.iri.as_str() for one in individuals)


class World:
    """
    An ontology together with the reasoner that judges it: the context a
    :class:`Relation` lives over. The reasoner is `HermiT`_ by default,
    reached through the `owlapi`_ bridge that `owlapy`_ bundles; set
    :attr:`engine` to another of its reasoners, e.g. ``"Pellet"`` or
    ``"ELK"``. The reasoner is built lazily and dropped -- along with
    :attr:`retrieved`, the memo of :func:`instances` -- whenever an
    axiom is added, so every question is answered about the current
    ontology.

    Parameters:
        iri : The base IRI new entities are named under, also the IRI of
            the ontology when nothing is loaded.

    Example
    -------
    >>> world = World("http://discopy.org/kennel.owl#")
    >>> Dog = world.owl_class("Dog")
    >>> rex = world.individual("rex", Dog)
    >>> assert world.find("Dog") == Dog and rex in instances(Dog, world)
    """
    engine = "HermiT"

    def __init__(self, iri: str = "http://discopy.org/world.owl#"):
        self.iri = iri
        self.ontology = SyncOntology(iri.rstrip("#/"), load=False)
        self.retrieved = {}
        self._reasoner, self._graph = None, None
        self._tbox, self._rbox, self._abox = None, None, None

    def add(self, *axioms):
        """
        Add axioms to the ontology, dropping the reasoner and the
        retrievals so the next question is answered about the new state.

        Parameters:
            axioms : The `owlapy` axioms to add.
        """
        self.ontology.add_axiom(list(axioms))
        self.retrieved = {}
        self._reasoner, self._graph = None, None
        self._tbox, self._rbox, self._abox = None, None, None

    @property
    def reasoner(self) -> SyncReasoner:
        """ The reasoner judging the current ontology, built lazily. """
        if self._reasoner is None:
            self._reasoner = SyncReasoner(self.ontology, reasoner=self.engine)
        return self._reasoner

    def owl_class(self, name: str) -> OWLClass:
        """
        Declare and return a named class under the world's base IRI.

        Parameters:
            name : The short name of the class.
        """
        result = OWLClass(IRI.create(self.iri + name))
        self.add(OWLDeclarationAxiom(result))
        return result

    def owl_property(self, name: str, dom: OWLClassExpression = None,
                     cod: OWLClassExpression = None) -> OWLObjectProperty:
        """
        Declare and return an object property under the world's base
        IRI, with optional ``rdfs:domain`` and ``rdfs:range``.

        Parameters:
            name : The short name of the property.
            dom : The domain class, if declared.
            cod : The range class, if declared.
        """
        result = OWLObjectProperty(IRI.create(self.iri + name))
        self.add(OWLDeclarationAxiom(result))
        if dom is not None:
            self.add(OWLObjectPropertyDomainAxiom(result, dom))
        if cod is not None:
            self.add(OWLObjectPropertyRangeAxiom(result, cod))
        return result

    def individual(self, name: str, cls: OWLClassExpression = None
                   ) -> OWLNamedIndividual:
        """
        Declare and return a named individual under the world's base
        IRI, with an optional class assertion.

        Parameters:
            name : The short name of the individual.
            cls : The class it is asserted to belong to, if any.
        """
        result = OWLNamedIndividual(IRI.create(self.iri + name))
        self.add(OWLDeclarationAxiom(result))
        if cls is not None:
            self.add(OWLClassAssertionAxiom(result, cls))
        return result

    def relate(self, subject, prop, *objects):
        """
        Assert that a property holds of a subject and some objects.

        Parameters:
            subject : The `owlapy` individual on the left.
            prop : The object property.
            objects : The individuals on the right.
        """
        self.add(*(OWLObjectPropertyAssertionAxiom(subject, prop, one)
                   for one in objects))

    def signature(self, java_name: str, wrap) -> tuple:
        """
        The entities of one kind in the signature of the ontology and
        its imports, sorted by IRI.

        Parameters:
            java_name : The `owlapi` accessor, e.g.
                ``"getClassesInSignature"``.
            wrap : The `owlapy` constructor wrapping each entity's IRI.
        """
        imports = jpype.JClass(
            "org.semanticweb.owlapi.model.parameters.Imports").INCLUDED
        entities = getattr(self.ontology.owlapi_ontology, java_name)(imports)
        return tuple(sorted(
            (wrap(IRI.create(str(one.getIRI()))) for one in entities),
            key=lambda one: one.iri.as_str()))

    def classes(self) -> tuple:
        """ The named classes of the world, imports included. """
        return self.signature("getClassesInSignature", OWLClass)

    def object_properties(self) -> tuple:
        """ The object properties of the world, imports included. """
        return tuple(
            prop for prop in self.signature(
                "getObjectPropertiesInSignature", OWLObjectProperty)
            if declared(prop, OWLObjectProperty))

    def individuals(self) -> tuple:
        """ The named individuals of the world, imports included. """
        return self.signature(
            "getIndividualsInSignature", OWLNamedIndividual)

    def find(self, fragment: str):
        """
        The first entity of the world whose IRI ends with a fragment --
        classes, then properties, then individuals.

        Parameters:
            fragment : The end of the IRI, e.g. the short name.
        """
        for entities in (self.classes(), self.object_properties(),
                         self.individuals()):
            for entity in entities:
                if entity.iri.as_str().endswith(fragment):
                    return entity
        return None

    def tbox(self) -> tuple:
        """
        The class schema of the world, imports included -- `owlapi`
        also files property domains, ranges and functionality here,
        while the rest of the property schema is the :meth:`rbox`.
        """
        if self._tbox is None:
            self._tbox = tuple(self.ontology.get_tbox_axioms())
        return self._tbox

    def rbox(self) -> tuple:
        """
        The role schema of the world, imports included: subproperties,
        inverses, chains and characteristics.
        """
        if self._rbox is None:
            self._rbox = tuple(self.ontology.get_rbox_axioms())
        return self._rbox

    def abox(self) -> tuple:
        """ The fact axioms of the world, imports included. """
        if self._abox is None:
            self._abox = tuple(self.ontology.get_abox_axioms())
        return self._abox

    def graph(self):
        """
        The asserted graph of the world as an `rdflib` graph, imports
        included -- what :meth:`Relation.sparql` queries.
        """
        if self._graph is None:
            import rdflib
            self._graph = rdflib.Graph()
            manager = self.ontology.owlapi_manager
            target_factory = jpype.JClass(
                "org.semanticweb.owlapi.io.StringDocumentTarget")
            rdf_format = jpype.JClass(
                "org.semanticweb.owlapi.formats.RDFXMLDocumentFormat")
            for onto in manager.ontologies().toArray():
                target = target_factory()
                manager.saveOntology(onto, rdf_format(), target)
                self._graph.parse(data=str(target), format="xml")
        return self._graph


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
    A wire is labelled by a predicate: a named class, a class expression
    or ``owl:Thing`` -- the split object of the Karoubi envelope that
    :class:`Query` presents, displayed by :func:`label`.

    Parameters:
        entity : The `owlapy` class or class expression, or the name of
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
    `owlapy` entities.

    Parameters:
        inside (tuple[Wire, ...]) : The predicates inside the type.
    """
    generator_factory = Wire


@factory
class Diagram(frobenius.Diagram):
    """
    A diagram is the syntax of a relation, read off the ontology's own:
    a property is a :class:`Box` between the predicates of its schema, a
    class expression the coreflexive that tests it, an individual a
    point -- intersection is composition, the complement is a
    :class:`Bubble`, a quantifier follows its property and discards.

    Parameters:
        inside (tuple[frobenius.Layer, ...]) : The layers of the diagram.
        dom (Ty) : The domain of the diagram, i.e. its input.
        cod (Ty) : The codomain of the diagram, i.e. its output.
    """
    ob = Ty


class Box(frobenius.Box, Diagram):
    """
    A box is a generator of the syntax, carrying the `owlapy` entity it
    denotes as ``data``: a property, a class or class expression tested
    on a wire, an individual, or the :class:`Coercion` that changes a
    predicate.

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
    A bubble around the syntax of a complement, which the allegory
    cannot evaluate -- OWL has no complement of a property -- so it is
    decoration on the coreflexive that the reasoner retrieves whole.
    """


class Functor(frobenius.Functor):
    """ A functor with the syntax of an ontology as domain. """
    dom = cod = Diagram


Diagram.cup_factory, Diagram.cap_factory = Cup, Cap
Diagram.swap_factory, Diagram.spider_factory = Swap, Spider
Diagram.permutation_factory = Permutation
Diagram.bubble_factory = Bubble
Id = Diagram.id


def meet_of(*exprs):
    """
    The intersection of some class expressions, one alone left as it is
    and nested intersections flattened.

    Parameters:
        exprs : The `owlapy` class expressions.
    """
    exprs = tuple(
        operand for expr in exprs for operand in (
            expr.operands() if isinstance(expr, OWLObjectIntersectionOf)
            else (expr, )))
    return exprs[0] if len(exprs) == 1 else OWLObjectIntersectionOf(exprs)


def peel(layer) -> dict | None:
    """
    The predicates a layer tests, by wire position -- ``None`` unless
    every box of the layer is a membership test on a single wire, i.e.
    carries a class or class expression as ``data``. A layer of tests is
    a coreflexive factor, which :meth:`Relation.typed` collapses into
    the types of its wires.

    Parameters:
        layer : The layer of a :class:`Diagram`.
    """
    result = {}
    for box, offset in layer.boxes_and_offsets:
        if not isinstance(box.data, OWLClassExpression)\
                or (len(box.dom), len(box.cod)) != (1, 1):
            return None
        result[offset] = box.data
    return result


def demorgan(dom: Ty, cod: Ty, *inside: Diagram) -> Diagram:
    """
    The picture of a union as its De Morgan dual: one complement bubble
    around the meet of the complemented pictures -- spiders around their
    tensor -- so that the complement is the only bubble of the
    dictionary.

    Parameters:
        dom : The domain of the pictures.
        cod : The codomain of the pictures.
        inside : The pictures to join.
    """
    return (Diagram.spiders(1, len(inside), dom) >> Id().tensor(*(
        one.bubble(drawing_name=NEGATION) for one in inside))
        >> Diagram.spiders(len(inside), 1, cod)
        ).bubble(drawing_name=NEGATION)


def distinct(arity: int, typ: Ty) -> Diagram:
    """
    The effect testing that some wires of one type are pairwise
    distinct: the cup holds of two wires exactly when they agree, so a
    pair is distinct under one complemented cup, and more wires are
    copied by spiders and routed so that every pair meets its own --
    the anatomy of a cardinality restriction, in place of an ad-hoc
    inequality box.

    Parameters:
        arity : The number of wires, at least two.
        typ : The type of each wire.
    """
    unequal = Diagram.cups(typ, typ).bubble(drawing_name=NEGATION)
    if arity == 2:
        return unequal
    partners = [[other for other in range(arity) if other != wire]
                for wire in range(arity)]
    source = {(wire, other): wire * (arity - 1) + partners[wire].index(other)
              for wire in range(arity) for other in partners[wire]}
    legs = [leg for left in range(arity) for right in range(left + 1, arity)
            for leg in ((left, right), (right, left))]
    copies = Id().tensor(*(arity * [Diagram.spiders(1, arity - 1, typ)]))
    return copies >> Diagram.permutation(
        [source[leg] for leg in legs], copies.cod) >> Id().tensor(*(
            (len(legs) // 2) * [unequal]))


def instances(cls, world: World) -> tuple:
    """
    The individuals a class or class expression provably holds of,
    sorted by IRI -- asked of the world's reasoner, so a complement, a
    universal or a cardinality holds of an individual only when it is
    entailed.

    Retrievals are kept in :attr:`World.retrieved` until the ontology
    changes, so asking the same expression twice costs one reasoner call.

    Parameters:
        cls : The `owlapy` class or class expression.
        world : The world whose ontology says what is entailed.
    """
    if cls not in world.retrieved:
        world.retrieved[cls] = world.individuals() if cls == Thing\
            else tuple(sorted(world.reasoner.instances(cls),
                              key=lambda one: one.iri.as_str()))
    return world.retrieved[cls]


def carrier(arity: int, world: World) -> tuple:
    """
    The tuples of individuals a boundary of a given arity can carry, i.e.
    the product of that many copies of the individuals of a world.

    Parameters:
        arity : The number of wires.
        world : The world whose individuals the wires carry.
    """
    return tuple(product(world.individuals(), repeat=arity))


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
        world : The world the relation lives over.

    The extension is stored sorted by IRIs, so that equal relations
    compare equal whatever order their pairs came in. What the extension
    *means* is deductive: the constructors read the atoms the reasoner
    entails and the algebra computes certain answers, sound for
    entailment. There is no complement and no greatest relation: OWL
    cannot say either of a property, which is why this is a
    :class:`DistributiveAllegory` and not a Boolean one.

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
            typed
            from_property
            from_individual
            sparql

    Example
    -------
    >>> world = World("http://discopy.org/kennel.owl#")
    >>> Dog, Person = world.owl_class("Dog"), world.owl_class("Person")
    >>> owns = world.owl_property("owns", Person, Dog)
    >>> rex, fido = (world.individual(name, Dog) for name in ("rex", "fido"))
    >>> ada, bob = (world.individual(name, Person) for name in ("ada", "bob"))
    >>> world.relate(ada, owns, rex)
    >>> world.relate(bob, owns, fido)
    >>> web = Relation.from_property(owns, world)
    >>> assert web.dagger().dagger() == web
    >>> assert web.meet(web) == web <= web.join(web.dagger() >> web)
    >>> assert Relation.id(1, world) >> web == web
    """
    inside: tuple
    dom: int
    cod: int
    world: World

    ob = int

    def __init__(self, inside, dom: int, cod: int, world: World):
        pairs = {(tuplify(xs), tuplify(ys)) for xs, ys in inside}
        for xs, ys in pairs:
            if (len(xs), len(ys)) != (dom, cod):
                raise AxiomError(messages.WRONG_ARITY.format(
                    (dom, cod), (xs, ys)))
        self.inside = tuple(sorted(
            pairs, key=lambda pair: iris(pair[0] + pair[1])))
        self.dom, self.cod = dom, cod
        self.world = world
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
    def id(cls, dom: int, world: World) -> Relation:
        """
        The identity relation, i.e. the diagonal on the tuples.

        Parameters:
            dom : The number of wires.
            world : The world whose individuals the wires carry.
        """
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
    def swap(cls, left: int, right: int, world: World) -> Relation:
        """
        The relation exchanging two boundaries.

        Parameters:
            left : The number of wires on the left.
            right : The number of wires on the right.
            world : The world whose individuals the wires carry.
        """
        result = cls([(xs + ys, ys + xs)
                      for xs in carrier(left, world)
                      for ys in carrier(right, world)],
                     left + right, right + left, world)
        result.diagram = Diagram.swap(
            ob(left * (Thing, )), ob(right * (Thing, )))
        return result

    @classmethod
    def permutation(cls, xs, doms, world: World) -> Relation:
        """
        The relation permuting some boundaries, with the same convention
        as :meth:`abc.SymmetricCategory.permutation`: the ``i``-th output
        is the ``xs[i]``-th input.

        Parameters:
            xs : A permutation of ``range(len(doms))``.
            doms : The arities to permute.
            world : The world whose individuals the wires carry.
        """
        xs, doms = list(xs), list(doms)
        if sorted(xs) != list(range(len(doms))):
            raise ValueError
        return cls([(sum(groups, ()), sum((groups[x] for x in xs), ()))
                    for groups in product(
                        *(carrier(one, world) for one in doms))],
                   sum(doms), sum(doms), world)

    @classmethod
    def spiders(cls, n_legs_in: int, n_legs_out: int, typ: int,
                world: World) -> Relation:
        """
        The spider relation, i.e. tuples of individuals repeated on every
        leg -- copying, comparing and forgetting them.

        Parameters:
            n_legs_in : The number of legs in.
            n_legs_out : The number of legs out.
            typ : The number of wires on each leg.
            world : The world whose individuals the wires carry.
        """
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
            world : The world whose individuals the wires carry.
        """
        return cls.spiders(1, n, typ, world)

    @classmethod
    def cups(cls, left: int, right: int, world: World) -> Relation:
        """
        The relation bending two boundaries into none; ``owl:Thing`` is
        self-dual so ``left`` and ``right`` must be equal.

        Parameters:
            left : The number of wires on the left.
            right : The same number of wires.
            world : The world whose individuals the wires carry.
        """
        if left != right:
            raise AxiomError(messages.NOT_ADJOINT.format(left, right))
        result = cls([(xs + xs, ()) for xs in carrier(left, world)],
                     left + right, 0, world)
        result.diagram = Diagram.cups(
            ob(left * (Thing, )), ob(right * (Thing, )))
        return result

    @classmethod
    def caps(cls, left: int, right: int, world: World) -> Relation:
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
            demorgan(typs[0], typs[1], *inside)
            if len(inside) > 1 else inside[0]), *diagrams)
        return result

    @classmethod
    def bottom(cls, dom: int, cod: int, world: World) -> Relation:
        """
        The empty relation between two boundaries.

        Parameters:
            dom : The number of input wires.
            cod : The number of output wires.
            world : The world the relation lives over.
        """
        result = cls((), dom, cod, world)
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
        collapsing to the identity on its predicates. The picture of the
        result draws the splitting: the peeled tests become the
        inclusions of the Karoubi envelope, between each typed boundary
        wire and the single-sorted middle.

        Example
        -------
        >>> world = World("http://discopy.org/kennel.owl#")
        >>> Dog, Person = world.owl_class("Dog"), world.owl_class("Person")
        >>> owns = world.owl_property("owns", Person, Dog)
        >>> rex = world.individual("rex", Dog)
        >>> ada = world.individual("ada", Person)
        >>> world.relate(ada, owns, rex)
        >>> web = Relation.from_property(owns, world)
        >>> person, dog = (extension(one, world) for one in (Person, Dog))
        >>> chain = (person >> web >> dog).typed()
        >>> print(chain)
        Query : ('Person',) -> ('Dog',)
        >>> assert chain.relation == person >> web >> dog
        >>> assert web.typed() == web.split((Thing, ), (Thing, ))
        >>> print(label((person >> person >> dog).typed().dom[0]))
        Person ⊓ Person ⊓ Dog
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
                    else meet_of(expr, cod_preds[offset])
        while layers:
            tests = peel(layers[0])
            if tests is None:
                break
            layers.pop(0)
            for offset, expr in tests.items():
                dom_preds[offset] = expr if offset not in dom_preds\
                    else meet_of(dom_preds[offset], expr)
        if not layers and self.diagram is not None:
            for offset in set(dom_preds) | set(cod_preds):
                both = [preds[offset] for preds in (dom_preds, cod_preds)
                        if offset in preds]
                dom_preds[offset] = cod_preds[offset] = meet_of(*both)
        dom = tuple(
            dom_preds.get(offset, Thing) for offset in range(self.dom))
        cod = tuple(
            cod_preds.get(offset, Thing) for offset in range(self.cod))
        result = Query(self, dom, cod, normalise=False)
        if self.diagram is None:
            return result
        if not layers:
            result.diagram = Id(ob(dom))
            return result
        include = lambda pred: Box(
            label(pred), ob((pred, )), ob(), data=pred)
        mid = Diagram(tuple(layers), layers[0].dom, layers[-1].cod)
        result.diagram = Id().tensor(*(
            include(dom_preds[offset]) if offset in dom_preds else Id(ob())
            for offset in range(self.dom))) >> mid >> Id().tensor(*(
                include(cod_preds[offset]).dagger()
                if offset in cod_preds else Id(ob())
                for offset in range(self.cod)))
        return result

    @classmethod
    def from_property(cls, prop, world: World) -> Relation:
        """
        The relation an OWL property holds of the individuals of a world:
        the raw single-sorted reading, every pair at arity one, deduced
        as in :func:`relations` -- see :meth:`Query.from_property` for
        the reading typed by the schema.

        Parameters:
            prop : The `owlapy` object property, or the inverse of one.
            world : The world whose ontology says what is entailed.
        """
        result = cls({(x, y) for x, ys in relations(prop, world).items()
                      for y in ys}, 1, 1, world)
        result.name = label(prop)
        result.diagram = box(prop, world, Thing, Thing)
        return result

    @classmethod
    def from_individual(cls, individual, world: World) -> Relation:
        """
        An individual as a point, i.e. the relation from the monoidal
        unit that holds of it alone.

        Parameters:
            individual : The `owlapy` individual.
            world : The world it lives in.
        """
        result = cls([((), (individual, ))], 0, 1, world)
        result.name = name_of(individual)
        result.diagram = point(individual, world, Thing)
        return result

    @classmethod
    def sparql(cls, query: str, dom: int, cod: int, world: World
               ) -> Relation:
        """
        The relation a SPARQL query defines, evaluated by `rdflib` on
        the asserted graph of the world -- the atoms as written, not the
        entailed ones, which is what the reasoner-backed constructors
        read. Each row is split into a pair after the first ``dom``
        variables.

        Parameters:
            query : The SPARQL query, with one variable per wire.
            dom : The number of input wires.
            cod : The number of output wires.
            world : The world to ask.
        """
        wrap = lambda term: OWLNamedIndividual(IRI.create(str(term)))
        return cls([(tuple(map(wrap, row[:dom])),
                     tuple(map(wrap, row[dom:])))
                    for row in world.graph().query(query)], dom, cod, world)

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
    classes or compound class expressions, each the :func:`label` of its
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

    Composing two queries whose predicates differ asks the reasoner for
    the subsumption between them, wire by wire, and inserts each verdict
    as a :class:`Coercion` -- so ``>>`` runs entailment queries, a
    deliberate exception to composition being pure, and
    :attr:`no_reasoning` is the way to opt out. :meth:`validate` then
    raises on every coercion whose subsumption failed or was never
    checked.

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
    >>> world = World("http://discopy.org/kennel.owl#")
    >>> Dog, Person = world.owl_class("Dog"), world.owl_class("Person")
    >>> owns_ = world.owl_property("owns", Person, Dog)
    >>> rex = world.individual("rex", Dog)
    >>> ada = world.individual("ada", Person)
    >>> world.relate(ada, owns_, rex)
    >>> owns = Query.from_property(owns_, world)
    >>> assert owns.relation.dom == owns.relation.cod == 1
    >>> assert Query.id(owns.dom, world) >> owns == owns
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
    def id(cls, dom: tuple, world: World) -> Query:
        """
        The identity on a split object, i.e. the coreflexive of its
        predicates.

        Parameters:
            dom : The tuple of predicates.
            world : The world whose ontology says what is entailed.
        """
        dom = tuplify(dom)
        result = cls(boundary(dom, world), dom, dom, normalise=False)
        result.diagram = Id(ob(dom))
        return result

    def then(self, *others: Query) -> Query:
        """
        Compose queries; where the predicates of the boundary differ,
        ask the reasoner for the subsumption between them and insert the
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
            demorgan(ob(self.dom), ob(self.cod), *inside)
            if len(inside) > 1 else inside[0]),
            self.diagram, *(other.diagram for other in others))
        return result

    @classmethod
    def bottom(cls, dom: tuple, cod: tuple, world: World) -> Query:
        """
        The empty query between two tuples of predicates.

        Parameters:
            dom : The tuple of predicates for the domain.
            cod : The tuple of predicates for the codomain.
            world : The world the query lives over.
        """
        dom, cod = map(tuplify, (dom, cod))
        result = cls(Relation.bottom(len(dom), len(cod), world),
                     dom, cod, normalise=False)
        result.diagram = Box("$\\bot$", ob(dom), ob(cod))
        return result

    @classmethod
    def spiders(cls, n_legs_in: int, n_legs_out: int, typ: tuple,
                world: World) -> Query:
        """
        The spiders on a tuple of predicates: the single-sorted spiders,
        normalised between the coreflexives of the boundary.

        Parameters:
            n_legs_in : The number of legs in.
            n_legs_out : The number of legs out.
            typ : The tuple of predicates on each leg.
            world : The world the spiders live over.
        """
        typ = tuplify(typ)
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
            world : The world the query lives over.
        """
        return cls.spiders(1, n, typ, world)

    @classmethod
    def swap(cls, left: tuple, right: tuple, world: World) -> Query:
        """
        The query exchanging two tuples of predicates.

        Parameters:
            left : The tuple of predicates on the left.
            right : The tuple of predicates on the right.
            world : The world the query lives over.
        """
        left, right = map(tuplify, (left, right))
        result = cls(Relation.swap(len(left), len(right), world),
                     left + right, right + left)
        result.diagram = Diagram.swap(ob(left), ob(right))
        return result

    @classmethod
    def permutation(cls, xs, doms, world: World) -> Query:
        """
        The query permuting some tuples of predicates, the ``i``-th
        output being the ``xs[i]``-th input.

        Parameters:
            xs : A permutation of ``range(len(doms))``.
            doms : The tuples of predicates to permute.
            world : The world the query lives over.
        """
        xs, doms = list(xs), [tuplify(dom) for dom in doms]
        dom = sum(doms, ())
        return cls(Relation.permutation(
            xs, [len(one) for one in doms], world),
            dom, sum((doms[x] for x in xs), ()))

    @classmethod
    def cups(cls, left: tuple, right: tuple, world: World) -> Query:
        """
        The query bending two boundaries into none; predicates are
        self-dual so ``left`` and ``right`` must be equal.

        Parameters:
            left : The tuple of predicates on the left.
            right : The same tuple of predicates.
            world : The world the query lives over.
        """
        left, right = map(tuplify, (left, right))
        if left != right:
            raise AxiomError(messages.NOT_ADJOINT.format(left, right))
        result = cls(Relation.cups(len(left), len(right), world),
                     left + right, ())
        result.diagram = Diagram.cups(ob(left), ob(right))
        return result

    @classmethod
    def caps(cls, left: tuple, right: tuple, world: World) -> Query:
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
        the reasoner refuted raises.

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
    def from_property(cls, prop, world: World, dom=None, cod=None) -> Query:
        """
        The query an OWL property defines, typed by what ``rdfs:domain``
        and ``rdfs:range`` declare: the raw relation of
        :meth:`Relation.from_property`, normalised between the
        coreflexives of the schema.

        Parameters:
            prop : The `owlapy` object property, or the inverse of one.
            world : The world whose ontology says what is entailed.
            dom : The predicate to read it at, its ``rdfs:domain`` when
                it declares exactly one and ``owl:Thing`` otherwise.
            cod : The predicate it lands in, likewise from ``rdfs:range``.
        """
        schema_dom, schema_cod = schema(prop, world)
        dom = schema_dom if dom is None else dom
        cod = schema_cod if cod is None else cod
        result = cls(Relation.from_property(prop, world), (dom, ), (cod, ))
        result.name = label(prop)
        result.diagram = box(prop, world, dom, cod)
        return result

    @classmethod
    def from_class(cls, entity, world: World, dom=None) -> Query:
        """
        The coreflexive query testing membership of a predicate, read at
        another one.

        Parameters:
            entity : The `owlapy` class or class expression.
            world : The world whose ontology says what is entailed.
            dom : The predicate to read it at, the expression itself by
                default -- in which case this is the identity on the
                split object, see :meth:`id`.
        """
        dom = entity if dom is None else dom
        result = cls(extension(entity, world), (dom, ), (dom, ))
        result.name = label(entity)
        result.diagram = to_diagram(entity, world, dom)
        return result

    @classmethod
    def from_individual(cls, individual, world: World, cod=None) -> Query:
        """
        An individual as a point, typed by its first named class.

        Parameters:
            individual : The `owlapy` individual.
            world : The world it lives in.
            cod : The predicate of the point, the individual's first
                named class by default.
        """
        cod = individual_class(individual, world) if cod is None else cod
        result = cls(
            Relation.from_individual(individual, world), (), (cod, ))
        result.name = name_of(individual)
        result.diagram = point(individual, world, cod)
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
    both, together with the reasoner's verdict on whether the source is
    subsumed by the target -- ``entailed`` is ``True`` for a free
    coercion, ``False`` for a filter and ``None`` when composed under
    :attr:`Query.no_reasoning`, to be settled by :meth:`Query.validate`.

    Parameters:
        source : The predicate to come from.
        target : The predicate to go to.
        world : The world whose ontology says what is entailed.
    """
    def __init__(self, source, target, world: World):
        self.source, self.target = source, target
        inside = extension(source, world).meet(extension(target, world))
        self.entailed = subsumes(source, target, world)\
            if type(self).reasoning else None
        super().__init__(inside, (source, ), (target, ), normalise=False)
        self.name = label(target)
        self.diagram = Box(
            label(target), ob((source, )), ob((target, )), data=self)


def coercion(source, target, world: World) -> Query:
    """
    The move between two predicates: the identity where they agree and a
    :class:`Coercion` otherwise, which is what :meth:`Query.then` puts
    between two queries that do not meet.

    Parameters:
        source : The predicate to come from.
        target : The predicate to go to.
        world : The world whose ontology says what is entailed.
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


def load(iri: str, path: str = None) -> World:
    """
    Load an ontology from its base IRI, together with its imports, into
    a fresh :class:`World`.

    Parameters:
        iri : The base IRI, i.e. the URL the ontology lives at.
        path : A local directory holding a copy of the ontology and its
            imports -- e.g. when the URL is unreachable or the loading
            should not depend on it. The directory is scanned by
            `owlapi`'s own ``AutoIRIMapper`` and an import that no file
            declares is stubbed silently, the way FIBO's OMG Commons
            annotation vocabularies are.

    Example
    -------
    >>> iri = ("https://spec.edmcouncil.org/fibo/ontology"
    ...        "/BE/OwnershipAndControl/OwnershipParties/")
    >>> world = load(iri)  # doctest: +SKIP
    >>> world = load(iri, path="test/fixtures/fibo")
    >>> name_of(world.find("UltimateConsolidation"))
    'UltimateConsolidation'
    """
    if path is not None and not os.path.isdir(path):
        raise FileNotFoundError(path)
    world = World(iri)
    manager = world.ontology.owlapi_manager
    if path is not None:
        mapper = jpype.JClass("org.semanticweb.owlapi.util.AutoIRIMapper")(
            jpype.JClass("java.io.File")(os.path.abspath(path)), True)
        manager.getIRIMappers().add(mapper)
        strategy = jpype.JClass(
            "org.semanticweb.owlapi.model.MissingImportHandlingStrategy")
        manager.setOntologyLoaderConfiguration(jpype.JClass(
            "org.semanticweb.owlapi.model.OWLOntologyLoaderConfiguration")()
            .setMissingImportHandlingStrategy(strategy.SILENT))
    world.ontology.owlapi_ontology = manager.loadOntology(
        jpype.JClass("org.semanticweb.owlapi.model.IRI").create(iri))
    return world


def reason(world: World):
    """
    Drop the world's reasoner and memos so the next question builds a
    fresh one -- reasoning itself is on demand: every retrieval and
    every proof asks the reasoner directly, and :meth:`World.add`
    already invalidates it, so calling this is only needed after
    mutating the ontology behind the world's back.

    Parameters:
        world : The world to reason about anew.
    """
    world.retrieved = {}
    world._reasoner, world._graph = None, None
    world._tbox, world._rbox, world._abox = None, None, None


def consistent(world: World) -> bool:
    """
    Whether the ontology of a world is consistent, by asking the
    reasoner.

    Parameters:
        world : The world to check.
    """
    return world.reasoner.has_consistent_ontology()


def deduced(exprs, world: World) -> list:
    """
    The individuals the reasoner can prove each class expression holds
    of, sorted by IRI. Each retrieval goes through
    :attr:`World.retrieved`, the memo of :func:`instances`, so a
    repeated expression is only ever asked once per world state.

    Parameters:
        exprs : The `owlapy` class expressions.
        world : The world whose ontology says what is entailed.

    Example
    -------
    >>> from owlapy.class_expression import OWLObjectComplementOf
    >>> from owlapy.owl_axiom import OWLDisjointClassesAxiom
    >>> world = World("http://discopy.org/kennel.owl#")
    >>> Dog, Person = world.owl_class("Dog"), world.owl_class("Person")
    >>> rex = world.individual("rex", Dog)
    >>> ada = world.individual("ada", Person)
    >>> deduced([OWLObjectComplementOf(Dog)], world)  # nothing provably not
    [()]
    >>> world.add(OWLDisjointClassesAxiom([Dog, Person]))
    >>> [[name_of(one) for one in found]
    ...  for found in deduced([OWLObjectComplementOf(Dog)], world)]
    [['ada']]
    """
    return [instances(expr, world) for expr in exprs]


def subsumes(left, right, world: World) -> bool:
    """
    Whether the ontology of a world entails that one predicate is
    subsumed by another, by asking the reasoner directly -- the proof
    object a :class:`Coercion` carries.

    Parameters:
        left : The predicate to be subsumed.
        right : The predicate to subsume it.
        world : The world whose ontology says what is entailed.

    Example
    -------
    >>> from owlapy.class_expression import OWLObjectSomeValuesFrom
    >>> world = World("http://discopy.org/kennel.owl#")
    >>> Dog, Person = world.owl_class("Dog"), world.owl_class("Person")
    >>> owns = world.owl_property("owns", Person, Dog)
    >>> world.add(OWLSubClassOfAxiom(
    ...     Person, OWLObjectSomeValuesFrom(owns, Dog)))
    >>> assert subsumes(Person, OWLObjectSomeValuesFrom(owns, Dog), world)
    >>> assert not subsumes(Dog, Person, world)
    >>> assert subsumes(Nothing, Dog, world)
    """
    return world.reasoner.is_entailed(OWLSubClassOfAxiom(left, right))


def relations(prop, world: World) -> dict:
    """
    The pairs an OWL property provably holds, grouped by subject -- the
    reasoner's property values, which follow subproperties, inverses
    and chains; an :class:`OWLObjectInverseOf <owlapy.owl_property.\
OWLObjectInverseOf>` groups its property the other way around.

    Parameters:
        prop : The `owlapy` object property, or the inverse of one.
        world : The world whose ontology says what is entailed.
    """
    if isinstance(prop, OWLObjectInverseOf):
        pairs = {}
        for x, ys in relations(prop.get_inverse(), world).items():
            for y in ys:
                pairs.setdefault(y, set()).add(x)
        return pairs
    result = {}
    for subject in world.individuals():
        values = set(world.reasoner.object_property_values(subject, prop))
        if values:
            result[subject] = values
    return result


def satisfying(expr, world: World) -> set:
    """
    The individuals a predicate provably holds of, by asking the
    reasoner: a complement, a universal or a cardinality holds of an
    individual only when the ontology entails it, never for want of
    information.

    Parameters:
        expr : The `owlapy` class or class expression.
        world : The world whose ontology says what is entailed.
    """
    return set(instances(expr, world))


def extension(expr, world: World) -> Relation:
    """
    A predicate as a coreflexive of the single-sorted category: the
    partial identity, at arity one, on the individuals :func:`satisfying`
    it -- the idempotent that :class:`Query` splits.

    Parameters:
        expr : The `owlapy` class or class expression.
        world : The world whose ontology says what is entailed.

    Example
    -------
    >>> from owlapy.class_expression import OWLObjectSomeValuesFrom
    >>> world = World("http://discopy.org/kennel.owl#")
    >>> Dog, Person = world.owl_class("Dog"), world.owl_class("Person")
    >>> owns = world.owl_property("owns", Person, Dog)
    >>> rex = world.individual("rex", Dog)
    >>> ada = world.individual("ada", Person)
    >>> bob = world.individual("bob", Person)
    >>> world.relate(ada, owns, rex)
    >>> dog_owners = extension(OWLObjectSomeValuesFrom(owns, Dog), world)
    >>> assert [name_of(x) for (x, ), _ in dog_owners.inside] == ["ada"]
    >>> assert dog_owners <= extension(Person, world)
    """
    return coreflexive(expr, satisfying(expr, world), world)


def coreflexive(expr, members, world: World) -> Relation:
    """
    The coreflexive of a predicate from members already retrieved --
    what :func:`extension` computes when it retrieves for itself.

    Parameters:
        expr : The `owlapy` class or class expression.
        members : The individuals the predicate provably holds of.
        world : The world they live in.
    """
    result = Relation([2 * ((one, ), ) for one in members], 1, 1, world)
    result.name = label(expr)
    result.diagram = to_diagram(expr, world, Thing)
    return result


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
    An OWL entity or class expression as a mathematician would write it
    on the board: intersection is :math:`\\sqcap`, union :math:`\\sqcup`,
    complement :math:`\\neg`, a quantifier follows its property, a
    cardinality precedes it and an inverse takes a converse breve.

    Parameters:
        entity : The `owlapy` entity or class expression.

    Example
    -------
    >>> from owlapy.class_expression import (
    ...     OWLObjectComplementOf, OWLObjectMinCardinality, OWLObjectOneOf,
    ...     OWLObjectSomeValuesFrom, OWLObjectUnionOf)
    >>> from owlapy.owl_property import OWLObjectInverseOf
    >>> world = World("http://discopy.org/kennel.owl#")
    >>> Dog, Person = world.owl_class("Dog"), world.owl_class("Person")
    >>> owns = world.owl_property("owns", Person, Dog)
    >>> rex = world.individual("rex", Dog)
    >>> print(label(OWLObjectIntersectionOf((Person, OWLObjectComplementOf(
    ...     OWLObjectUnionOf((OWLObjectSomeValuesFrom(owns, Dog),
    ...                       OWLObjectHasValue(owns, rex))))))))
    Person ⊓ ¬(∃owns.Dog ⊔ ∃owns.{rex})
    >>> print(label(OWLObjectMinCardinality(2, OWLObjectInverseOf(owns),
    ...             OWLObjectUnionOf((Person, Dog)))))
    ≥2 owns˘.(Person ⊔ Dog)
    """
    sub = lambda one: f"({label(one)})" if isinstance(
        one, (OWLObjectIntersectionOf, OWLObjectUnionOf)) else label(one)
    if entity == Thing:
        return "Thing"
    if entity == Nothing:
        return "Nothing"
    if isinstance(entity, (OWLClass, OWLObjectProperty, OWLNamedIndividual)):
        return name_of(entity)
    if isinstance(entity, OWLObjectInverseOf):
        return sub(entity.get_inverse()) + "˘"
    if isinstance(entity, OWLObjectIntersectionOf):
        return " ⊓ ".join(map(sub, entity.operands()))
    if isinstance(entity, OWLObjectUnionOf):
        return " ⊔ ".join(map(sub, entity.operands()))
    if isinstance(entity, OWLObjectComplementOf):
        return "¬" + sub(entity.get_operand())
    if isinstance(entity, OWLObjectOneOf):
        return "{" + ", ".join(sorted(
            name_of(one) for one in entity.operands())) + "}"
    if isinstance(entity, OWLObjectHasSelf):
        return f"∃{label(entity.get_property())}.Self"
    if isinstance(entity, OWLObjectHasValue):
        return f"∃{label(entity.get_property())}"\
            + ".{" + name_of(entity.get_filler()) + "}"
    if isinstance(entity, OWLObjectSomeValuesFrom):
        return f"∃{label(entity.get_property())}"\
            f".{sub(entity.get_filler())}"
    if isinstance(entity, OWLObjectAllValuesFrom):
        return f"∀{label(entity.get_property())}"\
            f".{sub(entity.get_filler())}"
    if isinstance(entity, OWLObjectCardinalityRestriction):
        symbol = {OWLObjectMinCardinality: "≥", OWLObjectMaxCardinality:
                  "≤", OWLObjectExactCardinality: "="}[type(entity)]
        return f"{symbol}{entity.get_cardinality()} "\
            f"{label(entity.get_property())}.{sub(entity.get_filler())}"
    return str(entity)


def ob(typ=None) -> Ty:
    """
    A tuple of OWL classes or class expressions as a type with one
    :class:`Wire` per predicate -- the predicates-as-types reading of a
    boundary.

    Parameters:
        typ : The predicate or tuple of predicates, ``owl:Thing`` by
            default.
    """
    typ = (Thing, ) if typ is None else tuplify(typ)
    return Ty(*map(Wire, typ))


def schema(prop, world: World) -> tuple:
    """
    What ``rdfs:domain`` and ``rdfs:range`` say an OWL property is
    defined on and lands in: the class when exactly one named one is
    declared and ``owl:Thing`` otherwise, swapped for an inverse.

    Parameters:
        prop : The `owlapy` object property, or the inverse of one.
        world : The world whose ontology declares the schema.
    """
    if isinstance(prop, OWLObjectInverseOf):
        return schema(prop.get_inverse(), world)[::-1]
    sides = {OWLObjectPropertyDomainAxiom: [],
             OWLObjectPropertyRangeAxiom: []}
    for axiom in world.tbox():
        if type(axiom) in sides\
                and axiom.get_property() == prop:
            sides[type(axiom)].append(axiom.get_domain() if isinstance(
                axiom, OWLObjectPropertyDomainAxiom) else axiom.get_range())
    only = lambda classes: classes[0]\
        if len(classes) == 1 and isinstance(classes[0], OWLClass)\
        and classes[0] != Thing else Thing
    return tuple(only(sides[kind]) for kind in sides)


def box(prop, world: World, dom=None, cod=None) -> Diagram:
    """
    An OWL property as a box between predicates, an inverse as the
    dagger of its box.

    Parameters:
        prop : The `owlapy` object property, or the inverse of one.
        world : The world whose ontology declares the schema.
        dom : The predicate to read it as defined on, its ``rdfs:domain``
            when it declares exactly one and ``owl:Thing`` otherwise.
        cod : The predicate it lands in, likewise from ``rdfs:range``.
    """
    if isinstance(prop, OWLObjectInverseOf):
        return box(prop.get_inverse(), world, cod, dom).dagger()
    schema_dom, schema_cod = schema(prop, world)
    dom = schema_dom if dom is None else dom
    cod = schema_cod if cod is None else cod
    return Box(name_of(prop), ob(dom), ob(cod), data=prop)


def individual_class(individual, world: World) -> OWLClass:
    """
    The first asserted named class of an individual by IRI, ``owl:Thing``
    when it has none.

    Parameters:
        individual : The `owlapy` individual.
        world : The world it lives in.
    """
    named = sorted(
        (axiom.get_class_expression() for axiom in world.abox()
         if isinstance(axiom, OWLClassAssertionAxiom)
         and axiom.get_individual() == individual
         and isinstance(axiom.get_class_expression(), OWLClass)),
        key=lambda one: one.iri.as_str())
    return named[0] if named else Thing


def point(individual, world: World, cod=None) -> Box:
    """
    An individual as a state, i.e. a box from the monoidal unit into its
    predicate.

    Parameters:
        individual : The `owlapy` individual.
        world : The world it lives in.
        cod : The predicate of the point, the individual's first named
            class by default.
    """
    cod = individual_class(individual, world) if cod is None else cod
    return Box(name_of(individual), Ty(), ob(cod), data=individual)


def to_diagram(source, world: World, dom=None) -> Diagram:
    """
    An OWL entity or class expression as a diagram, read off the syntax
    the ontology itself keeps: an individual is a :func:`point`, a
    property a :func:`box`, and a class expression the coreflexive that
    tests it -- intersection is composition, a quantifier follows its
    property and discards, the complement is the one bubble with union
    as its De Morgan dual.

    Parameters:
        source : The `owlapy` individual, property, class or class
            expression.
        world : The world whose ontology declares the schema.
        dom : The predicate a class expression is read at, itself for a
            named class and ``owl:Thing`` otherwise.

    Example
    -------
    >>> from owlapy.class_expression import (
    ...     OWLObjectComplementOf, OWLObjectSomeValuesFrom)
    >>> world = World("http://discopy.org/kennel.owl#")
    >>> Dog, Person = world.owl_class("Dog"), world.owl_class("Person")
    >>> owns = world.owl_property("owns", Person, Dog)
    >>> to_diagram(OWLObjectIntersectionOf((Person, OWLObjectComplementOf(
    ...     OWLObjectSomeValuesFrom(owns, Dog)))), world).draw(
    ...     doctest="docs/_static/owl/dogless-person.svg")

    .. image:: /_static/owl/dogless-person.svg
        :align: center
    """
    if isinstance(source, OWLNamedIndividual):
        return point(source, world)
    if isinstance(source, (OWLObjectProperty, OWLObjectInverseOf)):
        return box(source, world)
    if dom is None:
        dom = source if isinstance(source, OWLClass) else Thing
    typ = ob(dom)
    if source == Thing or source == dom:
        return Id(typ)
    if isinstance(source, OWLClass):
        return Box(name_of(source), typ, typ, data=source)
    if isinstance(source, OWLObjectIntersectionOf):
        return Id(typ).then(*(
            to_diagram(one, world, dom) for one in source.operands()))
    if isinstance(source, OWLObjectUnionOf):
        return Id(typ).then(*(
            to_diagram(one, world, dom).bubble(drawing_name=NEGATION)
            for one in source.operands())).bubble(drawing_name=NEGATION)
    if isinstance(source, OWLObjectComplementOf):
        return to_diagram(source.get_operand(), world, dom).bubble(
            drawing_name=NEGATION)
    if isinstance(source, OWLObjectOneOf):
        names = ", ".join(sorted(
            name_of(one) for one in source.operands()))
        return Box("{" + names + "}", typ, typ, data=source)
    if isinstance(source, (
            OWLObjectSomeValuesFrom, OWLObjectAllValuesFrom,
            OWLObjectHasValue, OWLObjectHasSelf,
            OWLObjectCardinalityRestriction)):
        return restriction_diagram(source, world, dom)
    raise NotImplementedError(messages.NOT_IN_DICTIONARY.format(source))


def restriction_diagram(source, world: World, dom) -> Diagram:
    """
    An OWL property restriction as a coreflexive diagram, the
    restriction case of :func:`to_diagram`: keep the wire, follow the
    property on a copy and ask the branch for the filler.

    Parameters:
        source : The `owlapy` restriction.
        world : The world whose ontology declares the schema.
        dom : The predicate the restriction is read at.
    """
    typ, prop = ob(dom), source.get_property()
    _, target = schema(prop, world)
    arrow, target_typ = box(prop, world, dom, target), ob(target)
    spiders = Diagram.spiders
    keep = lambda branch: spiders(1, 2, typ)\
        >> Id(typ) @ (branch >> spiders(1, 0, target_typ))
    if isinstance(source, OWLObjectHasSelf):
        return spiders(1, 2, typ)\
            >> box(prop, world, dom, dom) @ typ >> spiders(2, 1, typ)
    if isinstance(source, OWLObjectHasValue):
        value = source.get_filler()
        return spiders(1, 2, typ) >> Id(typ)\
            @ (box(prop, world, dom, individual_class(value, world))
               >> point(value, world).dagger())
    filler = to_diagram(source.get_filler(), world, target)
    if isinstance(source, OWLObjectSomeValuesFrom):
        return keep(arrow >> filler)
    if isinstance(source, OWLObjectAllValuesFrom):
        negated = filler.bubble(drawing_name=NEGATION)
        return keep(arrow >> negated).bubble(drawing_name=NEGATION)
    at_least = lambda n: Id(typ) if n == 0\
        else keep(arrow >> filler) if n == 1\
        else spiders(1, n + 1, typ) >> Id(typ) @ (
            Id().tensor(*(n * [arrow >> filler]))
            >> distinct(n, target_typ))
    cardinality = source.get_cardinality()
    if isinstance(source, OWLObjectMinCardinality):
        return at_least(cardinality)
    if isinstance(source, OWLObjectMaxCardinality):
        return at_least(cardinality + 1).bubble(drawing_name=NEGATION)
    assert_isinstance(source, OWLObjectExactCardinality)
    return at_least(cardinality) >> at_least(
        cardinality + 1).bubble(drawing_name=NEGATION)


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
        source : The `owlapy` axiom or entity it came from.

    Example
    -------
    >>> world = World("http://discopy.org/kennel.owl#")
    >>> Dog, Person = world.owl_class("Dog"), world.owl_class("Person")
    >>> owns = world.owl_property("owns", Person, Dog)
    >>> rex, toto = (world.individual(name, Dog) for name in ("rex", "toto"))
    >>> ada = world.individual("ada", Person)
    >>> world.relate(ada, owns, rex)
    >>> web = Relation.from_property(owns, world)
    >>> assert Axiom(web.dagger() >> web, extension(Dog, world))
    >>> assert not Axiom(extension(Dog, world), web.dagger() >> web)
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


def class_axioms(axiom, world: World) -> list[Axiom]:
    """
    One `owlapy` class axiom as :class:`Axiom` on relations over
    ``owl:Thing`` -- an inclusion for a subclass axiom, one equation per
    pair for an equivalence, one empty-intersection equation per pair
    for a disjointness -- or nothing when a side is outside the
    dictionary. The pictures read a subclass axiom at the subject's own
    predicate, the way a :class:`Query` would: the subject is a typed
    wire and the parent's anatomy is drawn on it, while the truth stays
    extensional over ``owl:Thing``.

    Parameters:
        axiom : The `owlapy` class axiom.
        world : The world it belongs to.
    """
    if isinstance(axiom, OWLSubClassOfAxiom):
        entity, parent = axiom.get_sub_class(), axiom.get_super_class()
        if not isinstance(entity, OWLClass) or parent == Thing\
                or not compilable(parent, world):
            return []
        left, right = extension(entity, world), extension(parent, world)
        left.diagram = Id(ob((entity, )))
        right.diagram = to_diagram(parent, world, entity)
        return [Axiom(left, right, source=axiom)]
    if isinstance(axiom, OWLEquivalentClassesAxiom):
        operands = list(axiom.class_expressions())
        if not all(compilable(one, world) for one in operands):
            return []
        named = [one for one in operands if isinstance(one, OWLClass)]
        subject = named[0] if named else None
        result = []
        for index, left in enumerate(operands):
            for right in operands[index + 1:]:
                sides = [extension(one, world) for one in (left, right)]
                if subject is not None:
                    for side, expr in zip(sides, (left, right)):
                        side.diagram = Id(ob((subject, )))\
                            if expr == subject\
                            else to_diagram(expr, world, subject)
                result.append(Axiom(*sides, symbol="=", source=axiom))
        return result
    if isinstance(axiom, OWLDisjointClassesAxiom):
        operands = list(axiom.class_expressions())
        if not all(compilable(one, world) for one in operands):
            return []
        bottom = Relation.bottom(1, 1, world)
        return [
            Axiom(extension(left, world).meet(extension(right, world)),
                  bottom, symbol="=", source=axiom)
            for index, left in enumerate(operands)
            for right in operands[index + 1:]]
    return []


def property_axioms(axiom, world: World) -> list[Axiom]:
    """
    One `owlapy` object property axiom as :class:`Axiom` on relations
    over ``owl:Thing``: the characteristics are the classical ones --
    an inverse is a converse, transitivity is a composite included in
    the relation, functionality is the converse composite under the
    identity -- and a domain or range bounds :meth:`Relation.domain` or
    :meth:`Relation.codomain`.

    Parameters:
        axiom : The `owlapy` object property axiom.
        world : The world it belongs to.
    """
    web = lambda prop: Relation.from_property(prop, world)
    named = lambda prop: isinstance(prop, OWLObjectProperty)
    if isinstance(axiom, OWLSubObjectPropertyOfAxiom):
        sub_property = axiom.get_sub_property()
        super_property = axiom.get_super_property()
        if not (named(sub_property) and named(super_property)):
            return []
        return [Axiom(web(sub_property), web(super_property), source=axiom)]
    if isinstance(axiom, OWLEquivalentObjectPropertiesAxiom):
        operands = list(axiom.properties())
        if not all(map(named, operands)):
            return []
        return [Axiom(web(left), web(right), symbol="=", source=axiom)
                for index, left in enumerate(operands)
                for right in operands[index + 1:]]
    if isinstance(axiom, OWLInverseObjectPropertiesAxiom):
        first = axiom.get_first_property()
        second = axiom.get_second_property()
        if not (named(first) and named(second)):
            return []
        return [Axiom(web(first).dagger(), web(second), symbol="=",
                      source=axiom)]
    if isinstance(axiom, OWLSubPropertyChainAxiom):
        steps = list(axiom.get_property_chain())
        if not all(map(named, steps)) or not named(
                axiom.get_super_property()):
            return []
        return [Axiom(
            Relation.id(1, world).then(*(web(step) for step in steps)),
            web(axiom.get_super_property()), source=axiom)]
    if isinstance(axiom, OWLObjectPropertyDomainAxiom):
        if not named(axiom.get_property()) or not isinstance(
                axiom.get_domain(), OWLClass):
            return []
        return [Axiom(web(axiom.get_property()).domain(),
                      extension(axiom.get_domain(), world), source=axiom)]
    if isinstance(axiom, OWLObjectPropertyRangeAxiom):
        if not named(axiom.get_property()) or not isinstance(
                axiom.get_range(), OWLClass):
            return []
        return [Axiom(web(axiom.get_property()).codomain(),
                      extension(axiom.get_range(), world), source=axiom)]
    characteristics = {
        OWLTransitiveObjectPropertyAxiom:
            lambda web: (web >> web, web, INCLUSION),
        OWLSymmetricObjectPropertyAxiom:
            lambda web: (web.dagger(), web, "="),
        OWLAsymmetricObjectPropertyAxiom: lambda web: (
            web.meet(web.dagger()), Relation.bottom(1, 1, world), "="),
        OWLReflexiveObjectPropertyAxiom:
            lambda web: (Relation.id(1, world), web, INCLUSION),
        OWLIrreflexiveObjectPropertyAxiom: lambda web: (
            web.meet(Relation.id(1, world)),
            Relation.bottom(1, 1, world), "="),
        OWLFunctionalObjectPropertyAxiom: lambda web: (
            web.dagger() >> web, Relation.id(1, world), INCLUSION),
        OWLInverseFunctionalObjectPropertyAxiom: lambda web: (
            web >> web.dagger(), Relation.id(1, world), INCLUSION)}
    if type(axiom) in characteristics and named(axiom.get_property()):
        left, right, symbol = characteristics[type(axiom)](
            web(axiom.get_property()))
        return [Axiom(left, right, symbol=symbol, source=axiom)]
    return []


def axioms(entity, world: World = None) -> list[Axiom]:
    """
    The rules of a loaded knowledge base, compiled to :class:`Axiom` --
    each a :class:`cat.Equation` between relations, whose
    :attr:`Axiom.equation` draws itself. A :class:`World` gives every
    rule its schema declares, imports included; a class or an object
    property gives the rules mentioning it. Every retrieval goes
    through :attr:`World.retrieved`, so a whole world compiles with one
    reasoner and one retrieval per predicate. SWRL rules are not
    compiled: FIBO's ownership-and-control modules declare none, and
    they wait on data properties.

    Parameters:
        entity : A :class:`World`, or an `owlapy` class or object
            property with the ``world`` argument.
        world : The world a class or property belongs to.

    Example
    -------
    >>> world = World("http://discopy.org/kennel.owl#")
    >>> Dog, Person = world.owl_class("Dog"), world.owl_class("Person")
    >>> owns = world.owl_property("owns", Person, Dog)
    >>> rex = world.individual("rex", Dog)
    >>> ada = world.individual("ada", Person)
    >>> world.relate(ada, owns, rex)
    >>> assert all(axioms(world))  # no entailed counterexample
    >>> assert len(axioms(Person, world)) == 1  # the domain of owns
    """
    if isinstance(entity, World):
        return [axiom
                for declared_axiom in entity.tbox() + entity.rbox()
                for axiom in class_axioms(declared_axiom, entity)
                + property_axioms(declared_axiom, entity)]
    assert_isinstance(
        entity, (OWLClass, OWLObjectProperty))
    return [axiom for axiom in axioms(world)
            if entity in axiom.source.signature()]


def compilable(expr, world: World) -> bool:
    """
    Whether a class expression is inside the dictionary, i.e. whether
    :func:`to_diagram` can draw it -- what :func:`axioms` checks before
    compiling a rule.

    Parameters:
        expr : The `owlapy` class or class expression.
        world : The world whose ontology declares the schema.
    """
    try:
        to_diagram(expr, world, Thing)
        return True
    except NotImplementedError:
        return False
