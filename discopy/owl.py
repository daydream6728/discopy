# -*- coding: utf-8 -*-

"""
The category of relations of an OWL ontology.

An OWL property denotes a relation between individuals and an OWL class
denotes a set of them, so a loaded ontology presents a category of finite
relations: a :class:`BooleanAllegory`, i.e. a locally posetal bicategory
whose 2-cells are the inclusions of relations, with converse, intersection,
union and complement. This module implements it directly on the extensions
that `owlready2`_ reads off a :class:`World <owlready2.namespace.World>`:

* its **objects** are tuples of OWL classes, with the empty tuple as
  monoidal unit and ``owl:Thing`` as the class of all individuals;
* its **morphisms** are :class:`Relation`, i.e. finite sets of pairs of
  tuples of individuals, composed by relational composition;
* its **2-morphisms** are the inclusions ``<=``, with :class:`Axiom`
  recording what an ontology says as a pair of parallel relations.

Everything an instance satisfies is closed-world with respect to the loaded
world; the open world is one :func:`reason` away, a `HermiT`_ invocation
that writes what the ontology entails back into the world, so the same
constructors read the entailed relations afterwards. Composition, meet,
join and complement are the set operations that define relations; anything
that deserves the name of a query or a proof is delegated, to the `SPARQL`_
engine of `owlready2`_ with :meth:`Relation.sparql` and to `HermiT`_ with
:func:`reason` and :func:`consistent`.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Relation
    Axiom

.. admonition:: Functions

    .. autosummary::
        :template: function.rst
        :nosignatures:
        :toctree:

        load
        reason
        consistent
        declared
        instances
        carrier
        relations
        satisfying
        restricted
        extension
        expr_world
        class_axioms
        property_axioms
        axioms
        label
        ob
        schema
        box
        point
        individual_class
        coercion
        parallel
        to_diagram
        restriction_diagram
        combine

.. _owlready2: https://owlready2.readthedocs.io/
.. _HermiT: http://www.hermit-reasoner.com/
.. _SPARQL: https://www.w3.org/TR/sparql11-query/

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
>>> owns = Relation.from_property(onto.owns)
>>> print(owns)
owns : ('Person',) -> ('Dog',)
>>> assert owns.dagger() >> owns <= Relation.id(Dog)  # ownership is single
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from itertools import product

from owlready2 import (
    EXACTLY, HAS_SELF, MAX, MIN, ONLY, SOME, VALUE, And, Inverse, Not,
    ObjectPropertyClass, OneOf, Ontology, Or,
    OwlReadyInconsistentOntologyError, Restriction, Thing, ThingClass, World,
    sync_reasoner_hermit)
from owlready2 import (
    AsymmetricProperty, FunctionalProperty, InverseFunctionalProperty,
    IrreflexiveProperty, ReflexiveProperty, SymmetricProperty,
    TransitiveProperty)
import owlready2

from discopy import cat, frobenius, messages
from discopy.abc import BooleanAllegory, SymmetricCategory
from discopy.utils import (
    AxiomError, assert_iscomposable, assert_isinstance, assert_isparallel,
    factory, tuplify)


OWL = "http://www.w3.org/2002/07/owl#"
""" The namespace of OWL's own vocabulary, which says nothing on its own. """

INCLUSION = "$\\sqsubseteq$"
""" The symbol of a 2-cell that is an inclusion, not an equation. """

NEGATION = "$\\neg$"
""" The drawing name of the bubble for a complement. """


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
    The individuals of an OWL class or class construct, sorted by IRI.

    A named class carries its own world and a construct finds one inside
    itself with :func:`expr_world`; ``owl:Thing`` belongs to every world
    at once, so its instances are read from the ``world`` given, the
    default world otherwise. A construct is read closed-world with
    :func:`satisfying`, which is what lets a compound class expression
    stand as an object, i.e. type a wire.

    Parameters:
        cls : The OWL class or class construct.
        world : The world to read ``owl:Thing`` from.
    """
    if isinstance(cls, ThingClass):
        generator = cls.instances(world=world) if world is not None\
            else cls.instances()
    else:
        generator = satisfying(cls, world or expr_world(cls))
    return tuple(sorted(generator, key=lambda one: one.iri))


def carrier(typ: tuple, world: World = None) -> tuple:
    """
    The product of the instances of a tuple of OWL classes, i.e. the set of
    tuples of individuals a wire of that type can carry.

    Parameters:
        typ : The tuple of OWL classes.
        world : The world to read ``owl:Thing`` from, resolved from the
            first named class of ``typ`` otherwise.
    """
    world = world or find_world(typ)
    return tuple(product(*(instances(cls, world) for cls in typ)))


def find_world(*typs: tuple) -> World:
    """
    The world of the first named class or class construct in some tuples
    of OWL classes, or ``None`` when there is nothing but ``owl:Thing``
    to ask.

    Parameters:
        typs : The tuples of OWL classes or class constructs.
    """
    for typ in typs:
        for cls in typ:
            world = expr_world(cls)
            if world is not None:
                return world
    return None


@factory
@dataclass
class Relation(BooleanAllegory, SymmetricCategory):
    """
    A finite relation between products of OWL classes, read off a loaded
    world.

    Parameters:
        inside : The extension, i.e. the pairs of tuples of individuals.
        dom : The domain, a tuple of OWL classes.
        cod : The codomain, a tuple of OWL classes.

    The extension is stored sorted by IRIs, so that equal relations compare
    equal whatever order their pairs came in. Membership of the individuals
    in the classes of the boundary is not checked: the constructors read
    them off the world, so it holds by construction.

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
            neg
            top
            bottom
            repeat
            from_property
            from_class
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
    >>> owns = Relation.from_property(onto.owns)
    >>> barks_at = owns.dagger() >> Relation.top((Person, ), (Person, ))
    >>> assert barks_at == Relation.top((Dog, ), (Person, ))
    >>> assert owns.meet(owns) == owns <= Relation.top((Person, ), (Dog, ))
    >>> assert owns.neg().neg() == owns
    """
    inside: tuple
    dom: tuple
    cod: tuple

    ob = tuple

    def __init__(self, inside, dom: tuple, cod: tuple):
        dom, cod = map(tuplify, (dom, cod))
        pairs = {(tuplify(xs), tuplify(ys)) for xs, ys in inside}
        for xs, ys in pairs:
            if (len(xs), len(ys)) != (len(dom), len(cod)):
                raise AxiomError(messages.WRONG_ARITY.format(
                    (len(dom), len(cod)), (xs, ys)))
        self.inside = tuple(sorted(
            pairs, key=lambda pair: iris(pair[0] + pair[1])))
        self.dom, self.cod = dom, cod
        self.diagram = None

    def __str__(self):
        name = getattr(self, "name", type(self).__name__)
        dom = tuple(map(label, self.dom))
        cod = tuple(map(label, self.cod))
        return f"{name} : {dom and str(dom) or '()'} "\
            f"-> {cod and str(cod) or '()'}"

    def __bool__(self):
        return bool(self.inside)

    def __le__(self, other) -> bool:
        assert_isinstance(other, Relation)
        assert_isparallel(self, other)
        return set(self.inside) <= set(other.inside)

    @classmethod
    def id(cls, dom: tuple = (), world: World = None) -> Relation:
        """
        The identity relation, i.e. the diagonal on the instances.

        Parameters:
            dom : The tuple of OWL classes.
            world : The world to read ``owl:Thing`` from.
        """
        dom = tuplify(dom)
        result = cls([(xs, xs) for xs in carrier(dom, world)], dom, dom)
        result.diagram = frobenius.Id(ob(dom))
        return result

    def then(self, *others: Relation) -> Relation:
        """
        The relational composition, i.e. pairs that share a middle.

        Composing across two different predicates never fails: OWL is
        single-sorted, so when the boundaries differ wire by wire the
        :func:`coercion` between them is inserted -- the join restricts
        to the individuals both predicates hold of, and the picture shows
        a coercion box exactly where the predicate changes.

        Parameters:
            others : The relations to compose in sequence.
        """
        result = self
        for other in others:
            assert_isinstance(other, Relation)
            if result.cod != other.dom\
                    and len(result.cod) == len(other.dom):
                other = type(self).id(()).tensor(*(
                    coercion(source, target) for source, target
                    in zip(result.cod, other.dom))).then(other)
            assert_iscomposable(result, other)
            targets = {}
            for ys, zs in other.inside:
                targets.setdefault(ys, []).append(zs)
            step = type(self)(
                {(xs, zs) for xs, ys in result.inside
                 for zs in targets.get(ys, ())}, result.dom, other.cod)
            step.diagram = combine(
                lambda left, right: left >> right,
                result.diagram, other.diagram)
            result = step
        return result

    def tensor(self, *others: Relation) -> Relation:
        """
        The product of relations, i.e. pairs of pairs.

        Parameters:
            others : The relations to tensor, tuples of OWL classes are
                taken as identities.
        """
        result = self
        for other in others:
            if not isinstance(other, Relation):
                other = type(self).id(other)
            step = type(self)(
                {(xs + xs_, ys + ys_)
                 for xs, ys in result.inside for xs_, ys_ in other.inside},
                result.dom + other.dom, result.cod + other.cod)
            step.diagram = combine(
                lambda left, right: left @ right,
                result.diagram, other.diagram)
            result = step
        return result

    __matmul__ = tensor
    __rmatmul__ = lambda self, other: type(self).id(other).tensor(self)

    def dagger(self) -> Relation:
        """ The converse relation, i.e. the pairs the other way around. """
        result = type(self)(
            [(ys, xs) for xs, ys in self.inside], self.cod, self.dom)
        result.diagram = combine(
            lambda diagram: diagram.dagger(), self.diagram)
        return result

    @classmethod
    def swap(cls, left: tuple, right: tuple, world: World = None) -> Relation:
        """
        The relation exchanging two tuples of OWL classes.

        Parameters:
            left : The tuple of OWL classes on the left.
            right : The tuple of OWL classes on the right.
            world : The world to read ``owl:Thing`` from.
        """
        left, right = map(tuplify, (left, right))
        world = world or find_world(left, right)
        result = cls([(xs + ys, ys + xs)
                      for xs in carrier(left, world)
                      for ys in carrier(right, world)],
                     left + right, right + left)
        result.diagram = frobenius.Diagram.swap(ob(left), ob(right))
        return result

    @classmethod
    def permutation(cls, xs, doms, world: World = None) -> Relation:
        """
        The relation permuting some tuples of OWL classes, with the same
        convention as :meth:`abc.SymmetricCategory.permutation`: the
        ``i``-th output is the ``xs[i]``-th input.

        Parameters:
            xs : A permutation of ``range(len(doms))``.
            doms : The tuples of OWL classes to permute.
            world : The world to read ``owl:Thing`` from.
        """
        xs, doms = list(xs), [tuplify(dom) for dom in doms]
        if sorted(xs) != list(range(len(doms))):
            raise ValueError
        dom = sum(doms, ())
        cod = sum((doms[x] for x in xs), ())
        world = world or find_world(dom)
        return cls([(sum(groups, ()), sum((groups[x] for x in xs), ()))
                    for groups in product(
                        *(carrier(one, world) for one in doms))], dom, cod)

    @classmethod
    def spiders(cls, n_legs_in: int, n_legs_out: int, typ: tuple,
                world: World = None) -> Relation:
        """
        The spider relation, i.e. tuples of individuals repeated on every
        leg -- copying, comparing and forgetting them.

        Parameters:
            n_legs_in : The number of legs in.
            n_legs_out : The number of legs out.
            typ : The tuple of OWL classes on each leg.
            world : The world to read ``owl:Thing`` from.
        """
        typ = tuplify(typ)
        result = cls([(n_legs_in * xs, n_legs_out * xs)
                      for xs in carrier(typ, world)],
                     n_legs_in * typ, n_legs_out * typ)
        result.diagram = frobenius.Diagram.spiders(
            n_legs_in, n_legs_out, ob(typ))
        return result

    @classmethod
    def copy(cls, typ: tuple, n: int = 2, world: World = None) -> Relation:
        """
        The relation copying every individual ``n`` times.

        Parameters:
            typ : The tuple of OWL classes to copy.
            n : The number of copies.
            world : The world to read ``owl:Thing`` from.
        """
        return cls.spiders(1, n, typ, world)

    @classmethod
    def cups(cls, left: tuple, right: tuple, world: World = None) -> Relation:
        """
        The relation bending two wires into none; OWL classes are self-dual
        so ``left`` and ``right`` must be equal.

        Parameters:
            left : The tuple of OWL classes on the left.
            right : The same tuple of OWL classes.
            world : The world to read ``owl:Thing`` from.
        """
        left, right = map(tuplify, (left, right))
        if left != right:
            raise AxiomError(messages.NOT_ADJOINT.format(left, right))
        result = cls([(xs + xs, ()) for xs in carrier(left, world)],
                     left + right, ())
        result.diagram = frobenius.Diagram.cups(ob(left), ob(right))
        return result

    @classmethod
    def caps(cls, left: tuple, right: tuple, world: World = None) -> Relation:
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
            pairs &= set(other.inside)
        result = type(self)(pairs, self.dom, self.cod)
        diagrams = (self.diagram, ) + tuple(
            other.diagram for other in others)
        result.diagram = combine(lambda *inside: (
            frobenius.Diagram.spiders(1, len(inside), ob(self.dom))
            >> frobenius.Id().tensor(*inside)
            >> frobenius.Diagram.spiders(len(inside), 1, ob(self.cod))
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
            pairs |= set(other.inside)
        result = type(self)(pairs, self.dom, self.cod)
        diagrams = (self.diagram, ) + tuple(
            other.diagram for other in others)
        result.diagram = combine(lambda *inside: (
            frobenius.Bubble(
                *inside, dom=ob(self.dom), cod=ob(self.cod),
                drawing_name="$\\vee$")
            if len(inside) > 1 else inside[0]), *diagrams)
        return result

    def neg(self, world: World = None) -> Relation:
        """
        The complement within the product of the carriers, called with
        ``~``. This is closed-world negation: what the world does not hold
        is taken to be false.

        Parameters:
            world : The world to read ``owl:Thing`` from.
        """
        result = type(self)(
            set(type(self).top(self.dom, self.cod, world).inside)
            - set(self.inside), self.dom, self.cod)
        result.diagram = combine(
            lambda diagram: diagram.bubble(drawing_name=NEGATION),
            self.diagram)
        return result

    @classmethod
    def top(cls, dom: tuple, cod: tuple, world: World = None) -> Relation:
        """
        The greatest relation between two tuples of OWL classes, relating
        every pair of tuples of instances.

        Parameters:
            dom : The domain.
            cod : The codomain.
            world : The world to read ``owl:Thing`` from.
        """
        dom, cod = map(tuplify, (dom, cod))
        world = world or find_world(dom, cod)
        result = cls(product(carrier(dom, world), carrier(cod, world)),
                     dom, cod)
        result.diagram = frobenius.Diagram.spiders(1, 0, ob(dom))\
            >> frobenius.Diagram.spiders(0, 1, ob(cod))
        return result

    @classmethod
    def bottom(cls, dom: tuple, cod: tuple) -> Relation:
        """
        The empty relation between two tuples of OWL classes.

        Parameters:
            dom : The domain.
            cod : The codomain.
        """
        dom, cod = map(tuplify, (dom, cod))
        result = cls((), dom, cod)
        result.diagram = frobenius.Box("$\\bot$", ob(dom), ob(cod))
        return result

    def domain(self) -> Relation:
        """
        The coreflexive relation on what a relation is actually defined on,
        i.e. the partial identity on the tuples with at least one value.
        """
        result = type(self)(
            [(xs, xs) for xs, _ in self.inside], self.dom, self.dom)
        result.diagram = combine(lambda diagram: (
            frobenius.Diagram.spiders(1, 2, ob(self.dom)) >> frobenius.Id(
                ob(self.dom)) @ (diagram >> frobenius.Diagram.spiders(
                    1, 0, ob(self.cod)))), self.diagram)
        return result

    def codomain(self) -> Relation:
        """ The :meth:`domain` of the converse relation. """
        return self.dagger().domain()

    def repeat(self) -> Relation:
        """
        The reflexive transitive closure of a relation on one type, i.e.
        the least reflexive and transitive relation above it.
        """
        if self.dom != self.cod:
            raise AxiomError(messages.NOT_ENDO.format(self))
        result = type(self).id(self.dom, find_world(self.dom)).join(self)
        while True:
            step = result.join(result >> result)
            if step == result:
                break
            result = step
        result.diagram = combine(
            lambda diagram: diagram.bubble(drawing_name="$\\ast$"),
            self.diagram)
        return result

    @classmethod
    def from_property(cls, prop, dom: tuple = None, cod: tuple = None
                      ) -> Relation:
        """
        The relation an OWL property holds, from what ``rdfs:domain`` says
        it is defined on to what ``rdfs:range`` says it lands in.

        The pairs are restricted to the carriers of the boundary, so that
        reading a property at a narrower predicate filters what it holds
        and the boundary stays honest; ``owl:Thing`` keeps everything.

        Parameters:
            prop : The `owlready2` property.
            dom : The domain to read it at, its ``rdfs:domain`` when it
                declares exactly one and ``owl:Thing`` otherwise.
            cod : The codomain, likewise from ``rdfs:range``.
        """
        schema_dom, schema_cod = schema(prop)
        dom = tuplify(schema_dom if dom is None else dom)
        cod = tuplify(schema_cod if cod is None else cod)
        source, target = (
            None if one is Thing else set(instances(one))
            for one in (dom[0], cod[0]))
        result = cls({(x, y) for x, y in prop.get_relations()
                      if (source is None or x in source)
                      and (target is None or y in target)}, dom, cod)
        result.name = prop.name
        result.diagram = frobenius.Box(prop.name, ob(dom), ob(cod))
        return result

    @classmethod
    def from_class(cls, entity: ThingClass, dom: tuple = None) -> Relation:
        """
        The coreflexive relation testing membership of an OWL class, i.e.
        the partial identity on its instances.

        Parameters:
            entity : The `owlready2` class.
            dom : The type to read it at, the class itself by default.
        """
        dom = (entity, ) if dom is None else tuplify(dom)
        result = cls([2 * ((one, ), ) for one in instances(entity)],
                     dom, dom)
        result.name = entity.name
        if len(dom) == 1:
            result.diagram = to_diagram(entity, dom[0])
        return result

    @classmethod
    def from_individual(cls, individual, cod: tuple = None) -> Relation:
        """
        An individual as a point, i.e. the relation from the monoidal unit
        that holds of it alone.

        Parameters:
            individual : The `owlready2` individual.
            cod : The type of the point, the first of the individual's
                named classes by default.
        """
        cod = tuplify(individual_class(individual) if cod is None else cod)
        result = cls([((), (individual, ))], (), cod)
        result.name = individual.name
        if len(cod) == 1:
            result.diagram = point(individual, cod[0])
        return result

    def to_diagram(self) -> "frobenius.Diagram":
        """
        The picture of a relation: the diagram of the syntax it was built
        from when there is one, and a box named after it otherwise --
        a relation is extensional, so a composite forgets its history
        unless every part carried a picture.
        """
        if self.diagram is not None:
            return self.diagram
        return frobenius.Box(
            getattr(self, "name", "?"), ob(self.dom), ob(self.cod))

    def draw(self, **params):
        """
        Draw the picture of a relation, see :meth:`to_diagram`.

        Parameters:
            params : Passed to :meth:`frobenius.Diagram.draw`.
        """
        return self.to_diagram().draw(**params)

    @classmethod
    def sparql(cls, query: str, dom: tuple, cod: tuple, world: World
               ) -> Relation:
        """
        The relation a SPARQL query defines, evaluated by the native engine
        of `owlready2`: each row is split into a pair after the first
        ``len(dom)`` variables.

        Parameters:
            query : The SPARQL query, with one variable per wire.
            dom : The domain, a tuple of OWL classes.
            cod : The codomain, a tuple of OWL classes.
            world : The world to ask.
        """
        dom, cod = map(tuplify, (dom, cod))
        return cls([(tuple(row[:len(dom)]), tuple(row[len(dom):]))
                    for row in world.sparql(query)], dom, cod)


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
    form a cycle.

    Parameters:
        path : The directory holding ``.rdf`` or ``.owl`` files.
        world : The world to load them into.
    """
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
    class membership, subsumption and, by default, property values.

    Assign to this to use another reasoner or other options.

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


def coercion(source, target, world: World = None) -> Relation:
    """
    The move between two predicates on the same individuals: the partial
    identity relating what satisfies both, drawn as a box named after
    where it goes -- and the identity where the two agree, which is what
    :meth:`Relation.then` puts between two relations that do not meet.

    Parameters:
        source : The predicate to come from.
        target : The predicate to go to.
        world : The world to read ``owl:Thing`` from.

    Example
    -------
    >>> from owlready2 import Thing, World
    >>> onto = World().get_ontology("http://discopy.org/kennel.owl")
    >>> with onto:
    ...     class Animal(Thing): pass
    ...     class Dog(Animal): pass
    ...     rex = Dog("rex")
    >>> assert coercion(onto.Dog, onto.Dog) == Relation.id(onto.Dog)
    >>> free = coercion(onto.Dog, onto.Animal)
    >>> assert free.domain() == Relation.id(onto.Dog)  # a dog is an animal
    """
    if source == target:
        return Relation.id((source, ), world)
    world = world or expr_world(source) or expr_world(target)
    inside = set(instances(source, world)) & set(instances(target, world))
    result = Relation([2 * ((one, ), ) for one in inside],
                      (source, ), (target, ))
    result.diagram = frobenius.Box(label(target), ob(source), ob(target))
    return result


def parallel(left: Relation, right: Relation) -> tuple:
    """
    Two relations as a parallel pair, widened to ``owl:Thing`` with
    coercions on each wire if their boundaries differ -- which is what an
    :class:`Axiom` between them needs.

    Parameters:
        left : One relation.
        right : The other.
    """
    if left.is_parallel(right):
        return left, right
    world = find_world(left.dom, left.cod, right.dom, right.cod)
    widen = lambda relation: (
        Relation.id(len(relation.dom) * (Thing, ), world) >> relation
        >> Relation.id(len(relation.cod) * (Thing, ), world))
    left, right = widen(left), widen(right)
    if not left.is_parallel(right):
        raise AxiomError(messages.NOT_PARALLEL.format(left, right))
    return left, right


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
            return f"∃{prop}.{{{entity.value.name}}}"
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


def ob(typ=None) -> frobenius.Ty:
    """
    A tuple of OWL classes or class constructs as a type with one wire
    per predicate, named by its :func:`label` -- the predicates-as-types
    reading of a boundary.

    Parameters:
        typ : The predicate or tuple of predicates, ``owl:Thing`` by
            default.
    """
    typ = (Thing, ) if typ is None else tuplify(typ)
    return frobenius.Ty(*map(label, typ))


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
        ) -> frobenius.Diagram:
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
    return frobenius.Box(prop.name, ob(dom), ob(cod))


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


def point(individual, cod: ThingClass = None) -> frobenius.Box:
    """
    An individual as a state, i.e. a box from the monoidal unit into its
    predicate.

    Parameters:
        individual : The `owlready2` individual.
        cod : The predicate of the point, the individual's first named
            class by default.
    """
    cod = individual_class(individual) if cod is None else cod
    return frobenius.Box(individual.name, frobenius.Ty(), ob(cod))


def to_diagram(source, dom: ThingClass = None) -> frobenius.Diagram:
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
        return frobenius.Id(typ)
    if isinstance(source, ThingClass):
        return frobenius.Box(source.name, typ, typ)
    if isinstance(source, And):
        return frobenius.Id(typ).then(*(
            to_diagram(one, dom) for one in source.Classes))
    if isinstance(source, Or):
        return frobenius.Bubble(
            *(to_diagram(one, dom) for one in source.Classes),
            dom=typ, cod=typ, drawing_name="$\\vee$")
    if isinstance(source, Not):
        return to_diagram(source.Class, dom).bubble(drawing_name=NEGATION)
    if isinstance(source, OneOf):
        names = ", ".join(one.name for one in source.instances)
        return frobenius.Box("{" + names + "}", typ, typ)
    if isinstance(source, Restriction):
        return restriction_diagram(source, dom)
    raise NotImplementedError(messages.NOT_IN_DICTIONARY.format(source))


def restriction_diagram(source: Restriction, dom: ThingClass
                        ) -> frobenius.Diagram:
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
    spiders = frobenius.Diagram.spiders
    keep = lambda branch: spiders(1, 2, typ)\
        >> frobenius.Id(typ) @ (branch >> spiders(1, 0, target_typ))
    if source.type == HAS_SELF:
        return spiders(1, 2, typ)\
            >> box(prop, dom, dom) @ typ >> spiders(2, 1, typ)
    if source.type == VALUE:
        return spiders(1, 2, typ) >> frobenius.Id(typ)\
            @ (box(prop, dom, individual_class(source.value))
               >> point(source.value).dagger())
    filler = to_diagram(source.value, target)
    if source.type == SOME:
        return keep(arrow >> filler)
    if source.type == ONLY:
        negated = filler.bubble(drawing_name=NEGATION)
        return keep(arrow >> negated).bubble(drawing_name=NEGATION)
    at_least = lambda n: frobenius.Id(typ) if n == 0\
        else keep(arrow >> filler) if n == 1\
        else spiders(1, n + 1, typ) >> frobenius.Id(typ) @ (
            frobenius.Id().tensor(*(n * [arrow >> filler]))
            >> frobenius.Box("$\\neq$", target_typ ** n, frobenius.Ty()))
    if source.type == MIN:
        return at_least(source.cardinality)
    if source.type == MAX:
        return at_least(source.cardinality + 1).bubble(
            drawing_name=NEGATION)
    assert source.type == EXACTLY
    return at_least(source.cardinality) >> at_least(
        source.cardinality + 1).bubble(drawing_name=NEGATION)


def relations(prop) -> dict:
    """
    The pairs an OWL property holds, grouped by subject; an
    :class:`Inverse <owlready2.class_construct.Inverse>` groups its
    property the other way around.

    Parameters:
        prop : The `owlready2` property, or the inverse of one.
    """
    if isinstance(prop, Inverse):
        pairs = ((y, x) for x, ys in relations(prop.property).items()
                 for y in ys)
    else:
        pairs = prop.get_relations()
    result = {}
    for x, y in pairs:
        result.setdefault(x, set()).add(y)
    return result


def satisfying(expr, world: World) -> set:
    """
    The individuals satisfying an OWL class construct, i.e. its extension
    in the closed world.

    A universal or a maximum cardinality quantifies over every individual,
    so an individual with no value at all satisfies both -- which is what
    the open world would not let one conclude, and precisely what makes
    this the *closed*-world reading.

    Parameters:
        expr : The `owlready2` class or class construct.
        world : The world whose individuals quantifiers range over.

    Raises:
        NotImplementedError : On a construct outside the dictionary,
            e.g. a datatype restriction.
    """
    if expr is Thing:
        return set(instances(Thing, world))
    if isinstance(expr, ThingClass):
        return set(instances(expr))
    if isinstance(expr, And):
        return set.intersection(
            *(satisfying(one, world) for one in expr.Classes))
    if isinstance(expr, Or):
        return set.union(*(satisfying(one, world) for one in expr.Classes))
    if isinstance(expr, Not):
        return satisfying(Thing, world) - satisfying(expr.Class, world)
    if isinstance(expr, OneOf):
        return set(expr.instances)
    if isinstance(expr, Restriction):
        return restricted(expr, world)
    raise NotImplementedError(messages.NOT_IN_DICTIONARY.format(expr))


def restricted(expr: Restriction, world: World) -> set:
    """
    The individuals satisfying an OWL property restriction, the
    :class:`Restriction <owlready2.class_construct.Restriction>` case of
    :func:`satisfying`.

    Parameters:
        expr : The `owlready2` restriction.
        world : The world whose individuals quantifiers range over.
    """
    if isinstance(expr.property, str):  # a reference left unresolved
        raise NotImplementedError(
            messages.NOT_IN_DICTIONARY.format(expr))
    pairs = relations(expr.property)
    if expr.type == HAS_SELF:
        return {x for x, ys in pairs.items() if x in ys}
    if expr.type == VALUE:
        return {x for x, ys in pairs.items() if expr.value in ys}
    filler = satisfying(expr.value, world)
    if expr.type == SOME:
        return {x for x, ys in pairs.items() if ys & filler}
    count = lambda x: len(pairs.get(x, set()) & filler)
    if expr.type == ONLY:
        return {x for x in satisfying(Thing, world)
                if pairs.get(x, set()) <= filler}
    if expr.type == MIN:
        return {x for x in satisfying(Thing, world)
                if count(x) >= expr.cardinality}
    if expr.type == MAX:
        return {x for x in satisfying(Thing, world)
                if count(x) <= expr.cardinality}
    assert expr.type == EXACTLY
    return {x for x in satisfying(Thing, world)
            if count(x) == expr.cardinality}


def extension(expr, dom: ThingClass = None, world: World = None) -> Relation:
    """
    An OWL class construct as a coreflexive relation, i.e. the partial
    identity on the individuals :func:`satisfying` it.

    Parameters:
        expr : The `owlready2` class or class construct.
        dom : The predicate to read it at, the construct itself by
            default -- an identity wire on the compound type; pass
            ``owl:Thing`` to see its anatomy as boxes and bubbles
            instead.
        world : The world whose individuals quantifiers range over,
            resolved from ``expr`` or ``dom`` otherwise.

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
    >>> assert dog_owners == Relation.id(dog_owners.dom)  # its own type
    >>> anatomy = extension(onto.owns.some(onto.Dog), dom=Thing)
    >>> assert anatomy <= extension(onto.Person, dom=Thing)
    """
    dom = expr if dom is None else dom
    world = world or expr_world(expr) or expr_world(dom)
    inside = satisfying(expr, world) & set(instances(dom, world))
    result = Relation([2 * ((one, ), ) for one in inside], dom, dom)
    result.diagram = to_diagram(expr, dom)
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


class Axiom(cat.Equation):
    """
    What an ontology says about some parallel relations: an inclusion when
    the symbol is :data:`INCLUSION`, an equation when it is ``"="``.

    Casting to ``bool`` checks whether the loaded world satisfies the
    axiom, which is decidable because the relations are finite; the open
    world satisfies it by construction once :func:`reason` has run.

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
    >>> owns = Relation.from_property(onto.owns)
    >>> assert Axiom(owns.dagger() >> owns, Relation.id(onto.Dog))
    >>> assert not Axiom(Relation.id(onto.Dog), owns.dagger() >> owns)
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


def class_axioms(entity: ThingClass) -> list[Axiom]:
    """
    What an ontology says about a class, as :class:`Axiom` on relations
    over ``owl:Thing``: one inclusion per superclass or restriction and
    one equation per equivalence, skipping what is outside the dictionary.

    Parameters:
        entity : The `owlready2` class.
    """
    world = entity.namespace.world
    left, result = extension(entity, Thing, world), []
    for parents, symbol in ((entity.is_a, INCLUSION),
                            (entity.equivalent_to, "=")):
        for parent in parents:
            if parent is Thing:
                continue
            try:
                right = extension(parent, Thing, world)
            except NotImplementedError:
                continue
            result.append(Axiom(
                left, right, symbol=symbol, source=(entity, parent)))
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
    at_thing = lambda prop: Relation.from_property(prop, Thing, Thing)
    relation, result = at_thing(entity), []
    identity = Relation.id(Thing, world)
    bottom = Relation.bottom((Thing, ), (Thing, ))
    source = entity
    result.extend(
        Axiom(relation, at_thing(parent), source=source)
        for parent in entity.is_a if declared(parent, ObjectPropertyClass))
    result.extend(
        Axiom(relation, at_thing(other), symbol="=", source=source)
        for other in entity.equivalent_to
        if declared(other, ObjectPropertyClass))
    if entity.inverse_property is not None:
        result.append(Axiom(relation.dagger(),
                            at_thing(entity.inverse_property),
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
        Axiom(identity.then(*map(at_thing, chain.properties)), relation,
              source=source)
        for chain in entity.get_property_chain()
        if all(isinstance(step, ObjectPropertyClass)
               for step in chain.properties))  # a step may be unresolved
    for classes, side in ((entity.domain, relation.domain()),
                          (entity.range, relation.codomain())):
        if len(classes) == 1 and declared(classes[0], ThingClass):
            result.append(Axiom(
                side, extension(classes[0], Thing, world), source=source))
    return result


def axioms(entity) -> list[Axiom]:
    """
    The axioms of an OWL entity, i.e. what an ontology says about the
    relations it presents, compiled to :class:`Axiom` -- including, for a
    whole ontology, one empty-intersection equation per pair of disjoint
    classes.

    Parameters:
        entity : An `owlready2` ontology, class or object property.

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
    >>> assert all(axioms(onto))  # the loaded world satisfies its schema
    """
    if isinstance(entity, Ontology):
        world = entity.world
        result = [axiom for cls in entity.classes()
                  for axiom in class_axioms(cls)]
        result += [axiom for prop in entity.object_properties()
                   for axiom in property_axioms(prop)]
        bottom = Relation.bottom((Thing, ), (Thing, ))
        result += [
            Axiom(extension(left, Thing, world).meet(
                extension(right, Thing, world)), bottom,
                symbol="=", source=disjoint)
            for disjoint in entity.disjoint_classes()
            for index, left in enumerate(disjoint.entities)
            for right in disjoint.entities[index + 1:]]
        return result
    if isinstance(entity, ThingClass):
        return class_axioms(entity)
    assert_isinstance(entity, ObjectPropertyClass)
    return property_axioms(entity)
