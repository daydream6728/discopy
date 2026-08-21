# -*- coding: utf-8 -*-

"""
The category of Python functions typed by an OWL ontology.

Objects are tuples of :class:`owlready2.ThingClass`, i.e. classes of an
ontology, so that type checking is OWL class membership. Morphisms are Python
functions taking an :class:`owlready2.World` as their first argument: the
world is the state in which individuals live and to which they are added, it
is threaded through composition rather than being a wire. Every call is
validated against the schema by a local HermiT invocation, so that a function
asserting data which contradicts the ontology raises
:class:`owlready2.OwlReadyInconsistentOntologyError`. Everything is
local: :mod:`owlready2` ships HermiT, whose invocation needs a Java
runtime.

The two functors relating this category to :mod:`discopy.python` are
:func:`lift`, which reads a Python function as an OWL function ignoring the
world, and :class:`Eval`, which evaluates an OWL function at a given world.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Function
    Query
    Eval

.. admonition:: Functions

    .. autosummary::
        :template: function.rst
        :nosignatures:
        :toctree:

        lift
        box
        rules
        declared
        deterministic
        conjunction
        implication
        atoms
        swrl
        variable
        variables

The schema itself can be read as syntax rather than as a type: :func:`rules`
compiles the axioms of an ontology into :class:`discopy.frobenius.Equation`,
i.e. a property becomes a box and what OWL says about it becomes an equation
between diagrams. Frobenius is the right home because an OWL property is a
relation, not a function, and the category of relations is a hypergraph
category whose spiders are copying and discarding.

That includes the rules an ontology carries itself: a `SWRL`_ rule is a Horn
clause over atoms, i.e. a conjunctive query on each side of an arrow, and a
conjunctive query is a hypergraph -- its variables are the wires, its atoms
the boxes and the variables it shares the spiders. :func:`implication` reads
one as an inclusion of states and :func:`swrl` writes one back, so a rule can
be drawn, rewritten as a diagram and put where a reasoner will run it.

.. _SWRL: https://www.w3.org/submissions/SWRL/
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass

from owlready2 import (
    EXACTLY, MAX, MIN, ONLY, SOME, ClassAtom, FunctionalProperty, Imp,
    IndividualPropertyAtom, InverseFunctionalProperty, Ontology,
    PropertyClass, ReflexiveProperty, SameIndividualAtom, SymmetricProperty,
    ThingClass, TransitiveProperty, Variable, World, sync_reasoner_hermit)
from owlready2.class_construct import Restriction

from discopy import frobenius, messages
from discopy.abc import MarkovCategory
from discopy.python import function, multiplicative
from discopy.python.multiplicative import Ty
from discopy.utils import (
    assert_iscomposable, assert_isinstance, classproperty, factory,
    untuplify)


@factory
class Function(function.Function, MarkovCategory):
    """
    Python function annotated with an OWL schema, i.e. a callable
    ``(world, *xs) -> ys`` from individuals to individuals.

    Parameters:
        inside : The callable inside the function, world as first argument.
        dom : The domain, i.e. a tuple of OWL classes.
        cod : The codomain, i.e. a tuple of OWL classes.

    Type checking is that of :class:`discopy.python.multiplicative.Function`,
    which the function delegates to via :meth:`eval`. Schema checking is one
    HermiT invocation per call, on the world as a whole, switched off with
    :attr:`no_reasoning`.

    .. admonition:: Summary

        .. autosummary::

            eval
            validate
            id
            then
            tensor
            swap
            copy
            discard

    Example
    -------
    >>> from owlready2 import AllDisjoint, Thing, World
    >>> world = World()
    >>> onto = world.get_ontology("http://discopy.org/owl.owl")
    >>> with onto:
    ...     class Person(Thing): pass
    ...     class Dog(Thing): pass
    ...     class owns(Person >> Dog): pass
    ...     _ = AllDisjoint([Person, Dog])
    >>> alice, rex = Person("alice"), Dog("rex")

    A generator is a Python function supplemented with an OWL signature.

    >>> def adopt_inside(world, person, dog):
    ...     person.owns.append(dog)
    ...     return person
    >>> adopt = Function(adopt_inside, (Person, Dog), Person)
    >>> name = Function(lambda world, x: x.name, Person, str)

    Composition threads the world through, HermiT runs once per call.

    >>> with Function.no_reasoning:
    ...     (adopt >> name)(world, alice, rex)
    'alice'
    >>> alice.owns
    [owl.rex]

    Asserting data that contradicts the schema is caught by HermiT.

    >>> from owlready2 import OwlReadyInconsistentOntologyError
    >>> confuse = Function(
    ...     lambda world, x: x.is_a.append(Dog) or x, Person, Person)
    >>> try:                                            # doctest: +EXTRA
    ...     confuse(world, alice)
    ... except OwlReadyInconsistentOntologyError:
    ...     print("Alice is not a dog.")
    Alice is not a dog.
    """
    reasoning = True

    @classproperty
    @contextmanager
    def no_reasoning(cls):
        """ Context manager for switching off the HermiT invocations. """
        tmp, cls.reasoning = cls.reasoning, False
        try:
            yield
        finally:
            cls.reasoning = tmp

    def eval(self, world: World) -> multiplicative.Function:
        """
        The image of the function under the evaluation functor at a world,
        i.e. the Python function that calls it on that world.

        Parameters:
            world : The world in which to evaluate the function.
        """
        return multiplicative.Function(
            lambda *xs: self.inside(world, *xs), self.dom, self.cod)

    @staticmethod
    def validate(world: World):
        """
        Check a world against the schema it is typed by, i.e. run HermiT on
        it. Assign to this to use another reasoner or other options, e.g.
        ``ignore_unsupported_datatypes`` for ontologies with annotations
        outside the OWL 2 datatype map.

        Parameters:
            world : The world to check.
        """
        sync_reasoner_hermit(world, debug=0)

    def __call__(self, world: World, *xs):
        result = self.eval(world)(*xs)
        if self.reasoning:
            self.validate(world)
        return result

    @classmethod
    def id(cls, dom: Ty = ()) -> Function:
        """
        The identity function on a tuple of OWL classes, it leaves the world
        untouched.

        Parameters:
            dom : The tuple of OWL classes on which to take the identity.
        """
        return lift(multiplicative.Function.id(dom))

    def then(self, other: Function) -> Function:
        """
        The sequential composition of two functions, called with ``>>``,
        i.e. the composite of their evaluations at every world.

        Parameters:
            other : The other function to compose in sequence.
        """
        assert_iscomposable(self, other)
        return Function(
            lambda world, *xs: (self.eval(world) >> other.eval(world))(*xs),
            self.dom, other.cod)

    def tensor(self, other: Function) -> Function:
        """
        The parallel composition of two functions, called with ``@``,
        i.e. the tensor of their evaluations at every world, the first
        happening before the second on the same world.

        Parameters:
            other : The other function to compose in parallel.
        """
        return Function(
            lambda world, *xs: (self.eval(world) @ other.eval(world))(*xs),
            self.dom + other.dom, self.cod + other.cod)

    @staticmethod
    def swap(x: Ty, y: Ty) -> Function:
        """
        The function swapping two tuples of OWL classes.

        Parameters:
            x : The tuple of OWL classes on the left.
            y : The tuple of OWL classes on the right.
        """
        return lift(multiplicative.Function.swap(x, y))

    @staticmethod
    def copy(x: Ty, n=2) -> Function:
        """
        The function making ``n`` copies of a tuple of OWL classes, i.e. of
        the individuals themselves rather than of the world.

        Parameters:
            x : The tuple of OWL classes to copy.
            n : The number of copies.
        """
        return lift(multiplicative.Function.copy(x, n))

    @staticmethod
    def discard(dom: Ty) -> Function:
        """
        The function discarding a tuple of OWL classes.

        Parameters:
            dom : The tuple of OWL classes to discard.
        """
        return Function.copy(dom, 0)


class Query(Function):
    """
    A :class:`Function` in the special case where its body is a SPARQL query
    on the world, i.e. its inputs are the parameters ``??1, ??2, ...`` of the
    query and its output is the first solution.

    Parameters:
        query : The SPARQL query to perform on the world.
        dom : The domain, i.e. a tuple of OWL classes for the parameters.
        cod : The codomain, i.e. a tuple of OWL classes for the columns.

    Example
    -------
    >>> from owlready2 import Thing, World
    >>> world = World()
    >>> onto = world.get_ontology("http://discopy.org/owl.owl")
    >>> with onto:
    ...     class Person(Thing): pass
    ...     class Dog(Thing): pass
    ...     class owns(Person >> Dog): pass
    >>> alice, rex = Person("alice"), Dog("rex")
    >>> alice.owns.append(rex)
    >>> dog_of = Query('''
    ...     PREFIX onto: <http://discopy.org/owl.owl#>
    ...     SELECT ?dog WHERE { ??1 onto:owns ?dog }''', Person, Dog)
    >>> with Function.no_reasoning:
    ...     dog_of(world, alice)
    owl.rex
    >>> print(Query('SELECT ?x { ?x a ?y }', (), Person))
    Query('SELECT ?x { ?x a ?y }', (), (owl.Person,))
    """
    def __init__(self, query: str, dom: Ty, cod: Ty):
        self.query = query
        super().__init__(self.solve, dom, cod)

    def __repr__(self):
        return f"Query({self.query!r}, {self.dom}, {self.cod})"

    def __eq__(self, other):
        return isinstance(other, Query) and (
            self.query, self.dom, self.cod) == (
                other.query, other.dom, other.cod)

    def solve(self, world: World, *xs):
        """
        The body of the query, i.e. the first solution of ``world.sparql``.

        Parameters:
            world : The world on which to perform the query.
            xs : The individuals to pass as parameters of the query.
        """
        for row in world.sparql(self.query, list(xs)):
            return untuplify(tuple(row))
        raise ValueError(f"No solution for {self.query}")


def lift(other: multiplicative.Function) -> Function:
    """
    The image of a Python function under the inclusion functor into OWL,
    i.e. the OWL function that ignores the world.

    Parameters:
        other : The Python function to lift.

    Example
    -------
    >>> from discopy.python import Function as Py
    >>> from owlready2 import Thing, World
    >>> world = World()
    >>> with world.get_ontology("http://discopy.org/owl.owl"):
    ...     class Person(Thing): pass
    >>> with Function.no_reasoning:
    ...     lift(Py.copy((Person, )))(world, Person("alice"))
    (owl.alice, owl.alice)
    """
    return Function(
        lambda world, *xs: other.inside(*xs), other.dom, other.cod)


@dataclass
class Eval:
    """
    The evaluation functor from OWL to Python at a given world, i.e. the
    identity on objects and :meth:`Function.eval` on morphisms.

    Parameters:
        world : The world at which to evaluate.

    Example
    -------
    >>> from owlready2 import Thing, World
    >>> world = World()
    >>> with world.get_ontology("http://discopy.org/owl.owl"):
    ...     class Person(Thing): pass
    >>> F, alice = Eval(world), Person("alice")
    >>> f = Function(lambda world, x: x.name, Person, str)
    >>> with Function.no_reasoning:
    ...     F((Person, )) == (Person, ) and F(f)(alice) == f(world, alice)
    True
    """
    world: World

    def __call__(self, other: Ty | Function) -> Ty | multiplicative.Function:
        return other if isinstance(other, tuple) else other.eval(self.world)


THING = frobenius.Ty("Thing")
""" The wire of :func:`rules`, i.e. the individuals an ontology is about. """

INCLUSION = "$\\sqsubseteq$"
""" The symbol of the rules that are an inclusion rather than an equation. """

OWL = "http://www.w3.org/2002/07/owl#"
""" The namespace of OWL's own vocabulary, which says nothing on its own. """


def declared(entity, kind: type) -> bool:
    """
    Whether an entity is one an ontology declared rather than one of OWL's
    own, i.e. whether it is worth a box.

    ``owl:Thing`` is every class and ``owl:TransitiveProperty`` is where
    `owlready2` keeps a characteristic, so both turn up as parents without
    being anything the ontology said.

    Parameters:
        entity : The candidate.
        kind : The class it has to be, i.e. a class or a property.
    """
    return isinstance(entity, kind) and not entity.iri.startswith(OWL)


def box(entity, ob: frobenius.Ty = THING) -> frobenius.Box:
    """
    An OWL entity as a box on the wire of individuals.

    A property is the relation it holds, a class is the partial identity
    that tests membership -- the same box either way, since a class is the
    relation that relates its members to themselves.

    Parameters:
        entity : The `owlready2` class or property.
        ob : The wire it is a relation on.

    Example
    -------
    >>> from owlready2 import Thing, World
    >>> with World().get_ontology("http://discopy.org/owl.owl"):
    ...     class Person(Thing): pass
    ...     class owns(Person >> Person): pass
    >>> print(box(owns), box(Person))
    owns Person
    """
    return frobenius.Box(entity.name, ob, ob, data=entity)


def deterministic(relation: frobenius.Diagram, ob: frobenius.Ty = THING
                  ) -> frobenius.Equation:
    """
    The equation saying a relation has at most one value, i.e. that it
    commutes with copying.

    Following the relation and then copying gives the pairs `(y, y)` for
    `y` a value of `x`; copying and then following it twice gives every
    pair `(y, y')` of values. The two are the same diagram exactly when
    there was never more than one to begin with, which is what OWL calls a
    functional property.

    Parameters:
        relation : The diagram to say it of.
        ob : The wire it is a relation on.
    """
    copy = frobenius.Diagram.copy(ob)
    return frobenius.Equation(relation >> copy, copy >> relation @ relation)


def restriction_rules(test: frobenius.Diagram, restriction: Restriction,
                      ob: frobenius.Ty = THING) -> list[frobenius.Equation]:
    """
    A class restriction as equations, i.e. what an ontology says the members
    of a class do with one of their properties.

    An existential says the class discards no more than what following the
    property into the filler does, a universal says following the property
    lands in the filler whether we ask for it or not, and a cardinality of
    one says the property is :func:`deterministic` where the class holds.

    Parameters:
        test : The diagram testing membership of the class.
        restriction : The `owlready2` restriction on it.
        ob : The wire it is a relation on.
    """
    if not declared(restriction.value, ThingClass) or not declared(
            restriction.property, PropertyClass):
        return []  # a datatype filler or a property from a module not loaded
    path = test >> box(restriction.property, ob)
    filler, discard = box(restriction.value, ob), frobenius.Diagram.discard(ob)
    exists = frobenius.Equation(
        test >> discard, path >> filler >> discard)
    if restriction.type == SOME or (
            restriction.type == MIN and restriction.cardinality == 1):
        return [exists]
    if restriction.type == ONLY:
        return [frobenius.Equation(path, path >> filler)]
    if restriction.type == MAX and restriction.cardinality == 1:
        return [deterministic(path, ob)]
    if restriction.type == EXACTLY and restriction.cardinality == 1:
        return [exists, deterministic(path, ob)]
    return []


def class_rules(entity: ThingClass, ob: frobenius.Ty = THING
                ) -> list[frobenius.Equation]:
    """
    What an ontology says about a class, as equations.

    Being a subclass is being oneself and then being the parent, i.e. the
    two tests in a row are the narrower one.

    Parameters:
        entity : The `owlready2` class.
        ob : The wire it is a relation on.
    """
    test, result = box(entity, ob), []
    for parent in entity.is_a:
        if declared(parent, ThingClass):
            result.append(frobenius.Equation(test >> box(parent, ob), test))
        elif isinstance(parent, Restriction):
            result.extend(restriction_rules(test, parent, ob))
    result.extend(frobenius.Equation(test, box(other, ob))
                  for other in entity.equivalent_to
                  if declared(other, ThingClass))
    return result


def property_rules(entity: PropertyClass, ob: frobenius.Ty = THING
                   ) -> list[frobenius.Equation]:
    """
    What an ontology says about a property, as equations.

    Its characteristics are the classical ones: an inverse is a transpose,
    symmetry is being one's own transpose, transitivity is a composite
    included in the relation, and being functional is
    :func:`deterministic`. A domain and a range are the classes the relation
    may be restricted to without losing anything.

    Parameters:
        entity : The `owlready2` property.
        ob : The wire it is a relation on.
    """
    relation, result = box(entity, ob), []
    result.extend(frobenius.Equation(relation, box(parent, ob),
                                     symbol=INCLUSION)
                  for parent in entity.is_a
                  if declared(parent, PropertyClass))
    if issubclass(entity, SymmetricProperty):
        result.append(frobenius.Equation(relation, relation.transpose()))
    if issubclass(entity, TransitiveProperty):
        result.append(frobenius.Equation(
            relation >> relation, relation, symbol=INCLUSION))
    if issubclass(entity, ReflexiveProperty):
        result.append(frobenius.Equation(
            frobenius.Diagram.id(ob), relation, symbol=INCLUSION))
    if issubclass(entity, FunctionalProperty):
        result.append(deterministic(relation, ob))
    if issubclass(entity, InverseFunctionalProperty):
        result.append(deterministic(relation.transpose(), ob))
    if entity.inverse_property is not None:
        result.append(frobenius.Equation(
            relation.transpose(), box(entity.inverse_property, ob)))
    result.extend(frobenius.Equation(relation, box(other, ob))
                  for other in entity.equivalent_to
                  if declared(other, PropertyClass))
    result.extend(frobenius.Equation(box(domain, ob) >> relation, relation)
                  for domain in entity.domain
                  if declared(domain, ThingClass))
    result.extend(frobenius.Equation(relation >> box(image, ob), relation)
                  for image in entity.range if declared(image, ThingClass))
    result.extend(frobenius.Equation(
        frobenius.Diagram.id(ob).then(
            *[box(link, ob) for link in chain.properties]),
        relation, symbol=INCLUSION) for chain in entity.get_property_chain())
    return result


def rules(entity, ob: frobenius.Ty = THING) -> list[frobenius.Equation]:
    """
    The axioms about an OWL entity as equations between diagrams.

    Parameters:
        entity : An `owlready2` ontology, class or property.
        ob : The wire its relations are on.

    Example
    -------
    >>> from owlready2 import Thing, TransitiveProperty, World
    >>> onto = World().get_ontology("http://discopy.org/owl.owl")
    >>> with onto:
    ...     class Place(Thing): pass
    ...     class partOf(Place >> Place, TransitiveProperty): pass
    >>> for rule in rules(partOf):
    ...     print(rule)
    Equation(partOf >> partOf, partOf)
    Equation(Place >> partOf, partOf)
    Equation(partOf >> Place, partOf)

    A rule that holds in the free hypergraph category is one the ontology
    did not need to say, which is what :meth:`frobenius.Equation.__bool__`
    reports:

    >>> transitivity, domain, image = rules(partOf)
    >>> assert not transitivity and not domain
    >>> assert bool(frobenius.Equation(box(partOf), box(partOf)))
    """
    if isinstance(entity, Ontology):
        return [rule for other in [*entity.classes(), *entity.properties()]
                for rule in rules(other, ob)] + [
            implication(rule, ob)
            for rule in entity.rules() if drawable(rule)]
    assert_isinstance(entity, (ThingClass, PropertyClass))
    return (class_rules if isinstance(entity, ThingClass)
            else property_rules)(entity, ob)


def drawable(rule: Imp) -> bool:
    """
    Whether every atom of a SWRL rule is a box on a wire, i.e. a class or an
    object property applied to variables.

    Builtins, datatypes and constants are the atoms with nowhere to go: a
    literal is not an individual, so it is not a wire of this category.

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


def conjunction(atoms: list, order: list, ob: frobenius.Ty = THING
                ) -> frobenius.Diagram:
    """
    A conjunction of SWRL atoms as a state with one wire per variable.

    A conjunctive query is a hypergraph: the variables are its spiders, the
    atoms are its boxes, and a variable two atoms share is the spider they
    are both wired to. An atom about one variable, i.e. a class, has both of
    its legs on the same spider, which is what makes it a test rather than a
    step.

    Parameters:
        atoms : The atoms of the conjunction.
        order : The variables, i.e. the wires of the state in order.
        ob : The wire they are relations on.
    """
    spider, wires = {name: i for i, name in enumerate(order)}, []
    for atom in atoms:
        legs = [spider[argument] for argument in atom.arguments]
        wires.append(((legs[0], ), (legs[-1], )))
    return frobenius.Hypergraph(
        dom=ob ** 0, cod=ob ** len(order),
        boxes=tuple(box(atom.class_predicate or atom.property_predicate, ob)
                    for atom in atoms),
        wires=((), tuple(wires), tuple(range(len(order)))),
        spider_types=len(order) * (ob, )).to_diagram()


def implication(rule: Imp, ob: frobenius.Ty = THING) -> frobenius.Equation:
    """
    A SWRL rule as an inclusion between the states of its body and its head.

    Both sides are drawn on every variable of the rule, so that they are
    parallel and the inclusion says what the rule says: every assignment
    satisfying the body satisfies the head.

    Parameters:
        rule : The SWRL rule.
        ob : The wire its relations are on.

    Example
    -------
    >>> from owlready2 import Imp, Thing, World
    >>> onto = World().get_ontology("http://discopy.org/owl.owl")
    >>> with onto:
    ...     class Person(Thing): pass
    ...     class hasParent(Person >> Person): pass
    ...     class hasAncestor(Person >> Person): pass
    ...     rule = Imp()
    >>> _ = rule.set_as_rule(
    ...     "hasParent(?x, ?y), hasAncestor(?y, ?z) -> hasAncestor(?x, ?z)")
    >>> assert not implication(rule)  # it is a rule, not a tautology
    >>> assert implication(rule).symbols[0] == INCLUSION
    """
    order = variables([*rule.body, *rule.head])
    return frobenius.Equation(
        conjunction(rule.body, order, ob),
        conjunction(rule.head, order, ob), symbol=INCLUSION)


def atoms(state: frobenius.Diagram, shared: list, ontology: Ontology) -> list:
    """
    The SWRL atoms of a state, i.e. the inverse of :func:`conjunction`.

    Reading a diagram back is reading its hypergraph: every spider is a
    variable, every box an atom on the spiders its legs are wired to. A
    class whose legs are on two different spiders is a test and an equality
    at once, so it comes back as two atoms.

    Parameters:
        state : The diagram, whose domain must be empty.
        shared : The variables of its outputs, in order.
        ontology : The ontology to build the atoms in.
    """
    assert_isinstance(state, frobenius.Diagram)
    if state.dom:
        raise ValueError(messages.WRONG_DOM.format(state.dom[:0], state.dom))
    graph, result = state.to_hypergraph(), []
    names = {}
    for position, spider in enumerate(graph.wires[2]):
        names.setdefault(spider, shared[position])
    for generator, (dom, cod) in zip(graph.boxes, graph.wires[1]):
        legs = [names.setdefault(spider, variable(f"v{spider}", ontology))
                for spider in (dom[0], cod[0])]
        if isinstance(generator.data, ThingClass):
            atom = ClassAtom(namespace=ontology)
            atom.class_predicate, atom.arguments = generator.data, legs[:1]
            result.append(atom)
            if dom[0] == cod[0]:
                continue
            atom = SameIndividualAtom(namespace=ontology)
        else:
            atom = IndividualPropertyAtom(namespace=ontology)
            atom.property_predicate = generator.data
        atom.arguments = legs
        result.append(atom)
    return result


def swrl(equation: frobenius.Equation, ontology: Ontology) -> list[Imp]:
    """
    An equation between states as SWRL rules in an ontology, i.e. the
    inverse of :func:`implication`.

    An inclusion is one rule, from the term on the left to the one on the
    right. An equation is two, one each way.

    Parameters:
        equation : The equation, whose terms are states with the same
            outputs, i.e. the same variables in the same order.
        ontology : The ontology to write the rules in.

    Example
    -------
    >>> from owlready2 import Imp, Thing, World
    >>> onto = World().get_ontology("http://discopy.org/owl.owl")
    >>> with onto:
    ...     class Person(Thing): pass
    ...     class hasParent(Person >> Person): pass
    ...     class hasAncestor(Person >> Person): pass
    ...     rule = Imp()
    >>> _ = rule.set_as_rule(
    ...     "Person(?x), hasParent(?x, ?y) -> hasAncestor(?x, ?y)")
    >>> written, = swrl(implication(rule), onto)
    >>> print(written)
    Person(?x0), hasParent(?x0, ?x1) -> hasAncestor(?x0, ?x1)
    """
    result = []
    with ontology:
        for index, term in enumerate(equation.terms[:-1]):
            other, symbol = equation.terms[index + 1], equation.symbols[index]
            pairs = [(term, other)] + (
                [(other, term)] if symbol == "=" else [])
            for body, head in pairs:
                shared = [variable(f"x{position}", ontology)
                          for position in range(len(body.cod))]
                rule = Imp(namespace=ontology)
                rule.body = atoms(body, shared, ontology)
                rule.head = atoms(head, shared, ontology)
                result.append(rule)
    return result
