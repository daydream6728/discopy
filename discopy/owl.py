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
        extension
        axioms

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

from dataclasses import dataclass
from itertools import product

from owlready2 import (
    Ontology, OwlReadyInconsistentOntologyError, Thing, ThingClass, World,
    sync_reasoner_hermit)
import owlready2

from discopy import messages
from discopy.abc import BooleanAllegory, SymmetricCategory
from discopy.utils import (
    AxiomError, assert_iscomposable, assert_isinstance, assert_isparallel,
    factory, tuplify)


OWL = "http://www.w3.org/2002/07/owl#"
""" The namespace of OWL's own vocabulary, which says nothing on its own. """

INCLUSION = "$\\sqsubseteq$"
""" The symbol of a 2-cell that is an inclusion, not an equation. """


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


def instances(cls: ThingClass, world: World = None) -> tuple:
    """
    The individuals of an OWL class, sorted by IRI.

    A named class carries its own world; ``owl:Thing`` belongs to every
    world at once, so its instances are read from the ``world`` given,
    the default world otherwise.

    Parameters:
        cls : The OWL class.
        world : The world to read ``owl:Thing`` from.
    """
    generator = cls.instances(world=world) if world is not None\
        else cls.instances()
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
    The world of the first named class in some tuples of OWL classes, or
    ``None`` when there is nothing but ``owl:Thing`` to ask.

    Parameters:
        typs : The tuples of OWL classes.
    """
    for typ in typs:
        for cls in typ:
            if declared(cls, ThingClass):
                return cls.namespace.world
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

    def __str__(self):
        name = getattr(self, "name", type(self).__name__)
        dom = tuple(cls.name for cls in self.dom)
        cod = tuple(cls.name for cls in self.cod)
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
        return cls([(xs, xs) for xs in carrier(dom, world)], dom, dom)

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
            targets = {}
            for ys, zs in other.inside:
                targets.setdefault(ys, []).append(zs)
            result = type(self)(
                {(xs, zs) for xs, ys in result.inside
                 for zs in targets.get(ys, ())}, result.dom, other.cod)
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
            result = type(self)(
                {(xs + xs_, ys + ys_)
                 for xs, ys in result.inside for xs_, ys_ in other.inside},
                result.dom + other.dom, result.cod + other.cod)
        return result

    __matmul__ = tensor
    __rmatmul__ = lambda self, other: type(self).id(other).tensor(self)

    def dagger(self) -> Relation:
        """ The converse relation, i.e. the pairs the other way around. """
        return type(self)(
            [(ys, xs) for xs, ys in self.inside], self.cod, self.dom)

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
        return cls([(xs + ys, ys + xs)
                    for xs in carrier(left, world)
                    for ys in carrier(right, world)],
                   left + right, right + left)

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
        return cls([(n_legs_in * xs, n_legs_out * xs)
                    for xs in carrier(typ, world)],
                   n_legs_in * typ, n_legs_out * typ)

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
        return cls([(xs + xs, ()) for xs in carrier(left, world)],
                   left + right, ())

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
        return type(self)(pairs, self.dom, self.cod)

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
        return type(self)(pairs, self.dom, self.cod)

    def neg(self, world: World = None) -> Relation:
        """
        The complement within the product of the carriers, called with
        ``~``. This is closed-world negation: what the world does not hold
        is taken to be false.

        Parameters:
            world : The world to read ``owl:Thing`` from.
        """
        return type(self)(
            set(type(self).top(self.dom, self.cod, world).inside)
            - set(self.inside), self.dom, self.cod)

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
        return cls(product(carrier(dom, world), carrier(cod, world)),
                   dom, cod)

    @classmethod
    def bottom(cls, dom: tuple, cod: tuple) -> Relation:
        """
        The empty relation between two tuples of OWL classes.

        Parameters:
            dom : The domain.
            cod : The codomain.
        """
        return cls((), dom, cod)

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
                return result
            result = step

    @classmethod
    def from_property(cls, prop, dom: tuple = None, cod: tuple = None
                      ) -> Relation:
        """
        The relation an OWL property holds, from what ``rdfs:domain`` says
        it is defined on to what ``rdfs:range`` says it lands in.

        Parameters:
            prop : The `owlready2` property.
            dom : The domain to read it at, its ``rdfs:domain`` when it
                declares exactly one and ``owl:Thing`` otherwise.
            cod : The codomain, likewise from ``rdfs:range``.
        """
        only = lambda classes: \
            classes[0] if len(classes) == 1 and declared(
                classes[0], ThingClass) else Thing
        dom = tuplify(only(prop.domain) if dom is None else dom)
        cod = tuplify(only(prop.range) if cod is None else cod)
        result = cls(set(prop.get_relations()), dom, cod)
        result.name = prop.name
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
        if cod is None:
            named = sorted(
                (one for one in individual.is_a
                 if declared(one, ThingClass)), key=lambda one: one.iri)
            cod = (named[0] if named else Thing, )
        result = cls([((), (individual, ))], (), tuplify(cod))
        result.name = individual.name
        return result

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
        path : A local directory to resolve the IRI and its imports in
            first, e.g. a checked-out copy when the URL is unreachable.

    Example
    -------
    >>> onto = load("http://www.lesfleursdunormal.fr/static/_downloads"
    ...             "/pizza_onto.owl")  # doctest: +SKIP
    """
    if path is not None and path not in owlready2.onto_path:
        owlready2.onto_path.append(path)
    world = world or owlready2.default_world
    return world.get_ontology(iri).load()


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
