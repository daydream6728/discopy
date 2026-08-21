# -*- coding: utf-8 -*-

"""
The 2-category of an OWL ontology.

An OWL property is a relation between individuals, not a function, and OWL
is single-sorted: a class is a unary predicate over one domain of
individuals rather than a sort of its own. Those two facts fix the shape of
this module, which is a 2-category:

* its **objects** are predicates, i.e. classes of an ontology, with
  :data:`THING` the one everything satisfies;
* its **morphisms** are queries, i.e. diagrams of properties in a hypergraph
  category, where the spiders are the variables a conjunctive query shares;
* its **2-morphisms** are :class:`Rule`, i.e. what the ontology says about
  those queries -- an inclusion or an equation between two of them, which is
  what a `SWRL`_ rule is and what an axiom compiles to.

Because the sort is one and the predicates are many, composing never fails:
:meth:`Diagram.then` inserts the :func:`coercion` between what comes out of
one query and what the next is defined on, and :meth:`Diagram.validate` is
where a reasoner is asked which of those coercions were free. A coercion
that is not free is a filter, which is the honest reading of `rdfs:domain`:
OWL makes it an entailment rather than a constraint, so feeding a property
something outside its domain is not an error, it says something.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Diagram
    Box
    Coercion
    Rule

.. admonition:: Functions

    .. autosummary::
        :template: function.rst
        :nosignatures:
        :toctree:

        ob
        box
        membership
        coercion
        rules
        reason
        subsumes
        declared
        deterministic
        conjunction
        implication
        atoms
        variable
        variables
        drawable

A `SWRL`_ rule is a Horn clause over atoms, i.e. a conjunctive query on each
side of an arrow, and a conjunctive query is a hypergraph -- its variables
are the wires, its atoms the boxes and the variables it shares the spiders.
A class atom is not a box but a *type*, which is what having predicates as
objects buys: :func:`implication` reads a rule as a 2-cell between the state
of its body and the state of its head, and :meth:`Rule.swrl` writes one
back, so a rule can be drawn, rewritten as a diagram and put where a
reasoner will run it.

.. _SWRL: https://www.w3.org/submissions/SWRL/
"""

from __future__ import annotations

from owlready2 import (
    EXACTLY, MAX, MIN, ONLY, SOME, ClassAtom, FunctionalProperty, Imp,
    IndividualPropertyAtom, InverseFunctionalProperty, Ontology,
    PropertyClass, ReflexiveProperty, SymmetricProperty,
    ThingClass, TransitiveProperty, Variable, World,
    sync_reasoner_hermit)
from owlready2.class_construct import Restriction

from discopy import frobenius, messages
from discopy.hypergraph import Hypergraph
from discopy.utils import AxiomError, assert_isinstance, factory


THING = frobenius.Ty("Thing")
""" ``owl:Thing``, the predicate every individual satisfies. """

INCLUSION = "$\\sqsubseteq$"
""" The symbol of a 2-cell that is an inclusion, not an equation. """

OWL = "http://www.w3.org/2002/07/owl#"
""" The namespace of OWL's own vocabulary, which says nothing on its own. """


def reason(world: World):
    """
    Run HermiT on a world so that what it entails can be read off it.

    Assign to this to use another reasoner or other options, e.g.
    ``ignore_unsupported_datatypes`` for the published ontologies whose
    annotations are outside the OWL 2 datatype map.

    Parameters:
        world : The world to reason about.
    """
    sync_reasoner_hermit(world, debug=0)


def declared(entity, kind: type) -> bool:
    """
    Whether an entity is one an ontology declared rather than one of OWL's
    own, i.e. whether it is worth a box or a wire.

    ``owl:Thing`` is every class and ``owl:TransitiveProperty`` is where
    `owlready2` keeps a characteristic, so both turn up as parents without
    being anything the ontology said.

    Parameters:
        entity : The candidate.
        kind : The class it has to be, i.e. a class or a property.
    """
    return isinstance(entity, kind) and not entity.iri.startswith(OWL)


def ob(entity: ThingClass = None) -> frobenius.Ty:
    """
    An OWL class as an object, i.e. the predicate its members satisfy.

    Parameters:
        entity : The class, ``owl:Thing`` by default.

    Example
    -------
    >>> from owlready2 import Thing, World
    >>> with World().get_ontology("http://discopy.org/owl.owl"):
    ...     class Person(Thing): pass
    >>> assert ob(Person) == frobenius.Ty("Person") and ob() == THING
    """
    return THING if not declared(entity, ThingClass)\
        else frobenius.Ty(entity.name)


@factory
class Diagram(frobenius.Diagram):
    """
    A query, i.e. a diagram of OWL properties between predicates.

    Composing never fails: OWL is single-sorted, so :meth:`then` inserts the
    :func:`coercion` between what one query lands in and what the next is
    defined on. :meth:`validate` is where a reasoner is asked which of those
    coercions were free.

    .. admonition:: Summary

        .. autosummary::

            then
            everywhere
            coercions
            validate
    """
    def then(self, *others: Diagram) -> Diagram:
        """
        Compose queries, coercing between them where their predicates
        differ.

        Parameters:
            others : The queries to compose in sequence.
        """
        result = self
        for other in others:
            assert_isinstance(other, Diagram)
            if result.cod != other.dom:
                result = frobenius.Diagram.then(
                    result, coercion(result.cod, other.dom))
            result = frobenius.Diagram.then(result, other)
        return result

    def everywhere(self) -> Diagram:
        """
        The query read as a relation on :data:`THING`, i.e. with a coercion
        on each wire at each end, which is what makes two of them parallel.
        """
        widen = lambda ty, into: Diagram.id(frobenius.Ty()).tensor(*[
            coercion(*(THING, ty[i:i + 1])[::1 if into else -1])
            for i in range(len(ty))])
        return widen(self.dom, True) >> self >> widen(self.cod, False)

    @property
    def coercions(self) -> list[Coercion]:
        """ The coercions inside a query, without repetition. """
        return list(dict.fromkeys(
            generator for generator in self.boxes
            if isinstance(generator, Coercion)))

    def validate(self, world: World) -> Diagram:
        """
        Check the coercions of a query against the ontologies of a world
        and return it.

        A coercion is free when the predicate it comes from is subsumed by
        the one it goes to, and a filter otherwise. Filtering is what OWL
        means by a domain, so this raises only on the coercions that lose
        something.

        Parameters:
            world : The world whose ontologies say what is subsumed.

        Raises:
            AxiomError : Whenever a coercion is not free.
        """
        reason(world)
        lossy = [one for one in self.coercions if not subsumes(world, one)]
        if lossy:
            raise AxiomError(" and ".join(
                f"{one.dom} is not {one.cod}" for one in lossy))
        return self


class Box(frobenius.Box, Diagram):
    """
    An OWL entity as a box between predicates, i.e. a generator of a query.

    A property is the relation it holds, from what ``rdfs:domain`` says it
    is defined on to what ``rdfs:range`` says it lands in. A class is the
    partial identity that tests membership, i.e. the coercion from
    :data:`THING` into itself as a predicate.
    """


class Coercion(Box):
    """
    The move between two predicates on the same individuals, i.e. what
    :meth:`Diagram.then` puts between two queries that do not meet.

    It is the identity where the two agree, an inclusion where the first is
    subsumed by the second, and a filter otherwise.
    """


class Spider(frobenius.Spider, Box):
    """ A variable, i.e. copying, comparing and forgetting individuals. """


class Swap(frobenius.Swap, Box):
    """ Two wires of individuals crossing. """


class Cup(frobenius.Cup, Box):
    """ Bending an input into an output, i.e. taking a converse. """


class Cap(frobenius.Cap, Box):
    """ Bending an output into an input. """


Diagram.spider_factory, Diagram.swap_factory = Spider, Swap
Diagram.cup_factory, Diagram.cap_factory = Cup, Cap


def box(entity: PropertyClass, dom: frobenius.Ty = None,
        cod: frobenius.Ty = None) -> Box:
    """
    An OWL property as a box, from what it is defined on to what it lands
    in.

    Parameters:
        entity : The `owlready2` property.
        dom : The predicate to read it as defined on, its ``rdfs:domain``
            when it declares exactly one and :data:`THING` otherwise.
        cod : The predicate it lands in, likewise from ``rdfs:range``.

    Example
    -------
    >>> from owlready2 import Thing, World
    >>> with World().get_ontology("http://discopy.org/owl.owl"):
    ...     class Person(Thing): pass
    ...     class Dog(Thing): pass
    ...     class owns(Person >> Dog): pass
    >>> print(box(owns), ":", box(owns).dom, "->", box(owns).cod)
    owns : Person -> Dog
    """
    only = lambda classes: ob(classes[0]) if len(classes) == 1 else THING
    return Box(entity.name, only(entity.domain) if dom is None else dom,
               only(entity.range) if cod is None else cod, data=entity)


def membership(entity: ThingClass) -> Box:
    """
    An OWL class as a box, i.e. the partial identity that tests membership,
    read as the coercion from :data:`THING` into the predicate.

    Parameters:
        entity : The `owlready2` class.
    """
    return coercion(THING, ob(entity))


def coercion(dom: frobenius.Ty, cod: frobenius.Ty) -> Diagram:
    """
    The move from one predicate to another, i.e. the identity where they
    agree and a :class:`Coercion` otherwise.

    Parameters:
        dom : The predicate to come from.
        cod : The predicate to go to.
    """
    return Diagram.id(dom) if dom == cod else Coercion(str(cod), dom, cod)


def subsumes(world: World, one: Coercion) -> bool:
    """
    Whether a coercion is free, i.e. whether the ontologies of a world
    entail that what it comes from is subsumed by what it goes to.

    The reasoner writes what it finds back into the class hierarchy, so the
    question is asked of `owlready2` afterwards; :func:`reason` is what puts
    it there and :meth:`Diagram.validate` is what calls it.

    Parameters:
        world : The world whose ontologies say what is subsumed.
        one : The coercion.
    """
    if one.cod == THING:
        return True  # everything is a thing
    classes = [world.search_one(iri=f"*{name}") for name in (one.dom, one.cod)]
    return all(map(bool, classes)) and issubclass(*classes)


class Rule(frobenius.Equation):
    """
    A 2-cell, i.e. what an ontology says about two parallel queries.

    An axiom of the schema and a `SWRL`_ rule are the same thing read at
    different sizes, so both compile to this: an inclusion when the symbol
    is :data:`INCLUSION`, an equation when it is ``"="``, and either way
    something a reasoner can be given back with :meth:`swrl`.

    Casting to ``bool`` compares the terms up to the axioms of a hypergraph
    category, i.e. it asks whether the rule says anything the notation did
    not already.

    Parameters:
        terms : The queries it relates.
        symbol : :data:`INCLUSION` or ``"="``.

    .. _SWRL: https://www.w3.org/submissions/SWRL/

    Example
    -------
    >>> from owlready2 import Thing, TransitiveProperty, World
    >>> with World().get_ontology("http://discopy.org/owl.owl"):
    ...     class Place(Thing): pass
    ...     class partOf(Place >> Place, TransitiveProperty): pass
    >>> transitivity, = rules(partOf)
    >>> print(*transitivity.terms, sep=" ⊑ ")
    partOf >> partOf ⊑ partOf
    >>> assert transitivity.symbols[0] == INCLUSION
    >>> assert not transitivity  # it is a rule, not a tautology
    """
    def swrl(self, ontology: Ontology) -> list[Imp]:
        """
        The rule as SWRL rules in an ontology, i.e. the inverse of
        :func:`implication`.

        An inclusion is one rule, from the query on the left to the one on
        the right. An equation is two, one each way.

        Parameters:
            ontology : The ontology to write them in.
        """
        result = []
        with ontology:
            for index, term in enumerate(self.terms[:-1]):
                other = self.terms[index + 1]
                pairs = [(term, other)] + (
                    [(other, term)] if self.symbols[index] == "=" else [])
                for body, head in pairs:
                    shared = [variable(f"x{position}", ontology)
                              for position in range(len(body.cod))]
                    rule = Imp(namespace=ontology)
                    rule.body = atoms(body, shared, ontology)
                    rule.head = atoms(head, shared, ontology)
                    result.append(rule)
        return result


def parallel(left: Diagram, right: Diagram) -> tuple:
    """
    Two queries as a parallel pair, read on :data:`THING` if the predicates
    they run between differ -- which is what a 2-cell between them needs.

    Parameters:
        left : One query.
        right : The other.
    """
    return (left, right) if (left.dom, left.cod) == (right.dom, right.cod)\
        else (left.everywhere(), right.everywhere())


def deterministic(query: Diagram) -> Rule:
    """
    The 2-cell saying a query has at most one value, i.e. that it commutes
    with copying.

    Following it and then copying gives the pairs `(y, y)`; copying and then
    following it twice gives every pair `(y, y')` of values. The two are the
    same query exactly when there was never more than one to begin with,
    which is what OWL calls a functional property.

    Parameters:
        query : The query to say it of.
    """
    return Rule(query >> Diagram.copy(query.cod),
                Diagram.copy(query.dom) >> query @ query)


def restriction_rules(entity: ThingClass,
                      restriction: Restriction) -> list[Rule]:
    """
    A class restriction as 2-cells, i.e. what an ontology says the members
    of a class do with one of their properties.

    An existential says the class discards no more than what following the
    property into the filler does, a universal says following the property
    lands in the filler whether we ask for it or not, and a cardinality of
    one says the property is :func:`deterministic` where the class holds.

    Parameters:
        entity : The class the restriction is on.
        restriction : The `owlready2` restriction.
    """
    if not declared(restriction.value, ThingClass) or not declared(
            restriction.property, PropertyClass):
        return []  # a datatype filler or a property from a module not loaded
    subject = membership(entity)
    path = subject >> box(restriction.property)
    into = path >> coercion(path.cod, ob(restriction.value))
    exists = Rule(*parallel(subject >> Diagram.discard(subject.cod),
                            into >> Diagram.discard(into.cod)))
    if restriction.type == SOME or (
            restriction.type == MIN and restriction.cardinality == 1):
        return [exists]
    if restriction.type == ONLY:
        return [Rule(*parallel(path, into))]
    if restriction.type == MAX and restriction.cardinality == 1:
        return [deterministic(path)]
    if restriction.type == EXACTLY and restriction.cardinality == 1:
        return [exists, deterministic(path)]
    return []


def class_rules(entity: ThingClass) -> list[Rule]:
    """
    What an ontology says about a class, as 2-cells.

    Being a subclass is not one of them any more: it is the
    :func:`coercion` between two predicates being free, which is structure
    rather than something said about a query.

    Parameters:
        entity : The `owlready2` class.
    """
    return [rule for restriction in entity.is_a
            if isinstance(restriction, Restriction)
            for rule in restriction_rules(entity, restriction)]


def property_rules(entity: PropertyClass) -> list[Rule]:
    """
    What an ontology says about a property, as 2-cells.

    Its characteristics are the classical ones: an inverse is a transpose,
    symmetry is being one's own transpose, transitivity is a composite
    included in the relation, and being functional is
    :func:`deterministic`. Its domain and range are not among them any
    more: they are what :func:`box` types it by.

    Parameters:
        entity : The `owlready2` property.
    """
    relation, result = box(entity), []
    result.extend(Rule(*parallel(relation, box(parent)), symbol=INCLUSION)
                  for parent in entity.is_a
                  if declared(parent, PropertyClass))
    if issubclass(entity, SymmetricProperty):
        result.append(Rule(*parallel(relation, relation.transpose())))
    if issubclass(entity, TransitiveProperty):
        result.append(Rule(*parallel(relation >> relation, relation),
                           symbol=INCLUSION))
    if issubclass(entity, ReflexiveProperty):
        result.append(Rule(*parallel(Diagram.id(relation.dom), relation),
                           symbol=INCLUSION))
    if issubclass(entity, FunctionalProperty):
        result.append(deterministic(relation))
    if issubclass(entity, InverseFunctionalProperty):
        result.append(deterministic(relation.transpose()))
    if entity.inverse_property is not None:
        result.append(Rule(*parallel(
            relation.transpose(), box(entity.inverse_property))))
    result.extend(Rule(*parallel(relation, box(other)))
                  for other in entity.equivalent_to
                  if declared(other, PropertyClass))
    result.extend(Rule(*parallel(
        Diagram.id(THING).then(*[box(link).everywhere()
                                 for link in chain.properties]),
        relation.everywhere()), symbol=INCLUSION)
        for chain in entity.get_property_chain())
    return result


def rules(entity) -> list[Rule]:
    """
    The 2-cells of an OWL entity, i.e. what an ontology says about the
    queries it can build.

    Parameters:
        entity : An `owlready2` ontology, class or property.

    Example
    -------
    >>> from owlready2 import Thing, SymmetricProperty, World
    >>> onto = World().get_ontology("http://discopy.org/owl.owl")
    >>> with onto:
    ...     class Person(Thing): pass
    ...     class knows(Person >> Person, SymmetricProperty): pass
    ...     Person.is_a.append(knows.some(Person))
    >>> for rule in rules(onto):
    ...     print(*rule.terms, sep=" ~ ")  # doctest: +ELLIPSIS
    Person >> Spider(1, 0, Person) ~ Person >> knows >> Spider(1, 0, Person)
    knows ~ Cap(Person, Person) @ Person >> Person @ knows @ Person >> Perso...
    Cap(Person, Person) @ Person >> Person @ knows @ Person >> Person @ Cup(...
    """
    if isinstance(entity, Ontology):
        return [rule for other in [*entity.classes(), *entity.properties()]
                for rule in rules(other)] + [
            implication(rule) for rule in entity.rules() if drawable(rule)]
    assert_isinstance(entity, (ThingClass, PropertyClass))
    return (class_rules if isinstance(entity, ThingClass)
            else property_rules)(entity)


def drawable(rule: Imp) -> bool:
    """
    Whether every atom of a SWRL rule is a box or a wire, i.e. a class or an
    object property applied to variables.

    Builtins, datatypes and constants are the atoms with nowhere to go: a
    literal is not an individual, so it is neither.

    Parameters:
        rule : The SWRL rule.
    """
    return all(
        isinstance(atom, (ClassAtom, IndividualPropertyAtom))
        and all(isinstance(argument, Variable) for argument in atom.arguments)
        for atom in [*rule.body, *rule.head])


def variable(name: str, ontology: Ontology) -> Variable:
    """
    The SWRL variable of a name, made if it is not there already.

    `owlready2` keeps variables as individuals of the ``urn:swrl#``
    namespace, so two rules that both talk about ``?x0`` talk about the same
    one and it can only be made once.

    Parameters:
        name : The name of the variable, without the question mark.
        ontology : The ontology to make it in.
    """
    return Variable(name, namespace=ontology.get_namespace("urn:swrl#"))


def variables(atoms: list) -> list:
    """
    The variables of a list of SWRL atoms, in the order they first appear.

    Parameters:
        atoms : The atoms.
    """
    return list(dict.fromkeys(
        argument for atom in atoms for argument in atom.arguments))


def predicates(atoms: list, order: list) -> dict:
    """
    The predicate each variable of a conjunction is typed by, i.e. its class
    atom when it has exactly one and :data:`THING` otherwise.

    Having predicates as objects is what makes a class atom a type rather
    than a box; a variable with two of them keeps both as boxes, since a
    wire carries one predicate.

    Parameters:
        atoms : The atoms of the conjunction.
        order : The variables, in order.
    """
    classes = {name: [atom.class_predicate for atom in atoms
                      if isinstance(atom, ClassAtom)
                      and atom.arguments[0] is name] for name in order}
    return {name: ob(found[0]) if len(found) == 1 else THING
            for name, found in classes.items()}


def conjunction(atoms: list, order: list) -> Diagram:
    """
    A conjunction of SWRL atoms as a state with one wire per variable.

    A conjunctive query is a hypergraph: the variables are its spiders, the
    property atoms are its boxes, and a variable two atoms share is the
    spider they are both wired to. A class atom is the *type* of its
    variable rather than a box of its own, unless the variable has more than
    one, in which case they stay boxes because a wire carries one predicate.

    Parameters:
        atoms : The atoms of the conjunction.
        order : The variables, i.e. the wires of the state in order.
    """
    typed = predicates(atoms, order)
    spider = {name: index for index, name in enumerate(order)}
    boxes, wires = [], []
    for atom in atoms:
        legs = [spider[argument] for argument in atom.arguments]
        entity = atom.class_predicate or atom.property_predicate
        if isinstance(entity, ThingClass)\
                and typed[atom.arguments[0]] != THING:
            continue  # it is the type of its wire, not a box on it
        boxes.append(box(entity, typed[atom.arguments[0]],
                         typed[atom.arguments[-1]])
                     if isinstance(entity, PropertyClass) else
                     Box(entity.name, *2 * (typed[atom.arguments[0]], ),
                         data=entity))
        wires.append(((legs[0], ), (legs[-1], )))
    return Hypergraph[Diagram](
        dom=THING ** 0, cod=frobenius.Ty().tensor(*typed.values()),
        boxes=tuple(boxes),
        wires=((), tuple(wires), tuple(range(len(order)))),
        spider_types=tuple(typed.values())).to_diagram()


def implication(rule: Imp) -> Rule:
    """
    A SWRL rule as a 2-cell between the states of its body and its head.

    Both sides are drawn on every variable of the rule, so that they are
    parallel and the inclusion says what the rule says: every assignment
    satisfying the body satisfies the head.

    Parameters:
        rule : The SWRL rule.

    Example
    -------
    >>> from owlready2 import Imp, Thing, World
    >>> onto = World().get_ontology("http://discopy.org/owl.owl")
    >>> with onto:
    ...     class Person(Thing): pass
    ...     class hasParent(Person >> Person): pass
    ...     class hasAncestor(Person >> Person): pass
    ...     imp = Imp()
    >>> _ = imp.set_as_rule(
    ...     "Person(?x), hasParent(?x, ?y) -> hasAncestor(?x, ?y)")
    >>> assert not implication(imp)  # it is a rule, not a tautology
    >>> written, = implication(imp).swrl(onto)
    >>> print(written)
    Person(?x0), hasParent(?x0, ?x1) -> hasAncestor(?x0, ?x1)
    """
    order = variables([*rule.body, *rule.head])
    body, head = (conjunction(list(side), order)
                  for side in (rule.body, rule.head))
    return Rule(*parallel(body, head), symbol=INCLUSION)


def atoms(state: Diagram, shared: list, ontology: Ontology) -> list:
    """
    The SWRL atoms of a state, i.e. the inverse of :func:`conjunction`.

    Reading a query back is reading its hypergraph. A coercion is not an
    atom -- it is the same individual seen at two predicates -- so the
    spiders it joins are one variable, the predicate each spider is typed by
    is a class atom about that variable, and every other box is an atom on
    the spiders its legs are wired to.

    Parameters:
        state : The query, whose domain must be empty.
        shared : The variables of its outputs, in order.
        ontology : The ontology to build the atoms in.
    """
    assert_isinstance(state, Diagram)
    if state.dom:
        raise ValueError(messages.WRONG_DOM.format(state.dom[:0], state.dom))
    graph, result = state.to_hypergraph(), []
    same = {spider: spider for spider in range(len(graph.spider_types))}

    def root(spider):
        while same[spider] != spider:
            spider = same[spider]
        return spider

    for generator, (dom, cod) in zip(graph.boxes, graph.wires[1]):
        if isinstance(generator, Coercion):
            same[root(cod[0])] = root(dom[0])
    names = {}
    for position, spider in enumerate(graph.wires[2]):
        names.setdefault(root(spider), shared[position])
    name = lambda spider: names.setdefault(
        root(spider), variable(f"v{root(spider)}", ontology))
    for spider, predicate in enumerate(graph.spider_types):
        entity = resolve(predicate, ontology)
        if entity is not None:
            result.append(atom(ClassAtom, entity, [name(spider)], ontology))
    for generator, (dom, cod) in zip(graph.boxes, graph.wires[1]):
        if isinstance(generator, Coercion):
            continue
        legs = [name(spider) for spider in (dom[0], cod[0])]
        kind = ClassAtom if isinstance(generator.data, ThingClass)\
            else IndividualPropertyAtom
        result.append(atom(
            kind, generator.data, legs[:1] if kind is ClassAtom else legs,
            ontology))
    return result


def resolve(name: frobenius.Ty, ontology: Ontology) -> ThingClass:
    """
    The class a predicate names, or ``None`` for :data:`THING` and for a
    name the world does not know.

    Parameters:
        name : The predicate.
        ontology : The ontology whose world to look it up in.
    """
    return None if name == THING else ontology.world.search_one(iri=f"*{name}")


def atom(kind: type, entity, arguments: list, ontology: Ontology):
    """
    One SWRL atom, i.e. a predicate applied to variables.

    Parameters:
        kind : The class of atom, e.g. `owlready2.ClassAtom`.
        entity : The class or property it is about, `None` for an equality.
        arguments : The variables it is applied to.
        ontology : The ontology to build it in.
    """
    result = kind(namespace=ontology)
    if kind is ClassAtom:
        result.class_predicate = entity
    elif kind is IndividualPropertyAtom:
        result.property_predicate = entity
    result.arguments = arguments
    return result
