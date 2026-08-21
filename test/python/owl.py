# -*- coding: utf-8 -*-

from shutil import which

from pytest import fixture, importorskip, mark, raises

importorskip("owlready2")

from owlready2 import (
    JAVA_EXE, AllDisjoint, ClassAtom, FunctionalProperty, Imp,
    IndividualPropertyAtom, InverseFunctionalProperty,
    OwlReadyInconsistentOntologyError, PropertyChain, PropertyClass,
    DataProperty, ReflexiveProperty, SameIndividualAtom,
    SymmetricProperty, Thing,
    ThingClass, TransitiveProperty, World)

from discopy.frobenius import Equation
from discopy.utils import AxiomError
from discopy.hypergraph import Hypergraph
from discopy.python.owl import (
    INCLUSION, THING, Diagram, Eval, Function, Query, atoms, box,
    conjunction, declared, deterministic, drawable, implication, lift,
    assertions, meets, rules, source, subsumes, swrl, target, unmet,
    variable, variables)
from discopy.python import Function as Py


needs_java = mark.skipif(which(JAVA_EXE) is None, reason="HermiT needs Java.")


@fixture
def onto():
    world = World()
    result = world.get_ontology("http://discopy.org/test.owl")
    with result:
        class Person(Thing): pass
        class Dog(Thing): pass
        class owns(Person >> Dog): pass
        AllDisjoint([Person, Dog])
    return result


def test_symmetric_monoidal(onto):
    Person, Dog, world = onto.Person, onto.Dog, onto.world
    alice, rex = Person("alice"), Dog("rex")
    name = Function(lambda world, x: x.name, Person, str)
    bark = Function(lambda world, x: "woof", Dog, str)
    with Function.no_reasoning:
        assert (Function.id(Person) >> name)(world, alice) == "alice"
        assert (name @ bark)(world, alice, rex) == ("alice", "woof")
        assert (Function.swap((Person, ), (Dog, )) >> bark @ name)(
            world, alice, rex) == ("woof", "alice")
        assert (Function.copy((Person, )) >> name @ name)(
            world, alice) == ("alice", "alice")
        assert (name @ Function.discard((Dog, )))(world, alice, rex) == "alice"


def test_no_reasoning_restores(onto):
    with raises(ValueError):
        with Function.no_reasoning:
            raise ValueError
    assert Function.reasoning


@needs_java
def test_hermit_validates_the_schema(onto):
    Person, Dog, world = onto.Person, onto.Dog, onto.world
    adopt = Function(
        lambda world, x, y: x.owns.append(y) or x, (Person, Dog), Person)
    assert adopt(world, Person("alice"), Dog("rex")).name == "alice"
    confuse = Function(
        lambda world, x: x.is_a.append(Dog) or x, Person, Person)
    with raises(OwlReadyInconsistentOntologyError):
        confuse(world, Person("bob"))


def test_query(onto):
    Person, Dog, world = onto.Person, onto.Dog, onto.world
    alice, rex = Person("alice"), Dog("rex")
    alice.owns.append(rex)
    owners = Query(
        "SELECT ?x WHERE { ?x <http://discopy.org/test.owl#owns> ?y }",
        (), Person)
    strays = Query(
        "SELECT ?x WHERE { ?x a <http://discopy.org/test.owl#Dog> ."
        " ?x <http://discopy.org/test.owl#owns> ?y }", (), Dog)
    with Function.no_reasoning:
        assert owners(world) == alice
        with raises(ValueError):
            strays(world)
    assert eval(repr(owners), dict(Query=Query, test=onto)) == owners


def test_eval_is_functorial(onto):
    Person, world = onto.Person, onto.world
    alice, F = Person("alice"), Eval(world)
    name = Function(lambda world, x: x.name, Person, str)
    shout = lift(Py(str.upper, str, str))
    with Function.no_reasoning:
        assert F((Person, )) == (Person, )
        assert F(name >> shout)(alice) == (F(name) >> F(shout))(alice)


@fixture
def rulebook():
    world = World()
    result = world.get_ontology("http://discopy.org/rules.owl")
    with result:
        class Place(Thing): pass
        class Person(Thing): pass
        class Citizen(Person): pass
        class partOf(Place >> Place, TransitiveProperty): pass
        class contains(Place >> Place): pass
        class knows(Person >> Person, SymmetricProperty): pass
        class livesIn(Person >> Place, FunctionalProperty): pass
        class capitalOf(Place >> Place, InverseFunctionalProperty): pass
        class isIn(Place >> Place, ReflexiveProperty): pass
        class hasParent(Person >> Person): pass
        class hasUncle(Person >> Person): pass
        contains.inverse_property = partOf
        hasUncle.property_chain.append(PropertyChain([hasParent, knows]))
        Citizen.is_a.append(livesIn.some(Place))
        Citizen.is_a.append(knows.only(Person))
        Citizen.is_a.append(livesIn.max(1, Place))
        Citizen.is_a.append(livesIn.exactly(1, Place))
        Citizen.is_a.append(hasParent.min(1, Person))
        Citizen.is_a.append(hasParent.min(2, Person))  # no rule for it
        Citizen.is_a.append(livesIn.some(str))  # a datatype, so no rule
    return result


def among(rule, rulebook):
    """ Whether a rule is one of a list, as `Equation` has no `__eq__`. """
    return any((other.terms, other.symbols) == (rule.terms, rule.symbols)
               for other in rulebook)


def test_box(rulebook):
    assert box(rulebook.knows) == box(rulebook.knows)
    assert box(rulebook.knows) != box(rulebook.contains)
    assert box(rulebook.knows).data is rulebook.knows
    assert box(rulebook.Place).dom == box(rulebook.Place).cod == THING


def test_declared(rulebook):
    assert declared(rulebook.Place, ThingClass)
    assert not declared(Thing, ThingClass)  # owl:Thing says nothing
    assert not declared(TransitiveProperty, PropertyClass)
    assert not declared(rulebook.Place, PropertyClass)


def test_deterministic(rulebook):
    single = deterministic(box(rulebook.livesIn))
    assert not single  # it is an axiom, not a theorem of the free category
    assert single.terms[0].cod == single.terms[1].cod == THING @ THING


def test_property_rules(rulebook):
    partOf, contains = box(rulebook.partOf), box(rulebook.contains)
    knows, livesIn = box(rulebook.knows), box(rulebook.livesIn)
    assert among(Equation(partOf >> partOf, partOf, symbol=INCLUSION),
                 rules(rulebook.partOf))
    assert among(Equation(knows, knows.transpose()), rules(rulebook.knows))
    assert among(Equation(contains.transpose(), partOf),
                 rules(rulebook.contains))
    assert among(deterministic(livesIn), rules(rulebook.livesIn))
    assert among(deterministic(box(rulebook.capitalOf).transpose()),
                 rules(rulebook.capitalOf))
    assert among(Equation(Diagram.id(THING), box(rulebook.isIn),
                          symbol=INCLUSION), rules(rulebook.isIn))
    assert among(Equation(box(rulebook.hasParent) >> knows,
                          box(rulebook.hasUncle), symbol=INCLUSION),
                 rules(rulebook.hasUncle))
    assert among(Equation(box(rulebook.Person) >> livesIn, livesIn),
                 rules(rulebook.livesIn))
    assert among(Equation(livesIn >> box(rulebook.Place), livesIn),
                 rules(rulebook.livesIn))


def test_class_rules(rulebook):
    citizen, person = box(rulebook.Citizen), box(rulebook.Person)
    livesIn, place = box(rulebook.livesIn), box(rulebook.Place)
    discard, book = Diagram.discard(THING), rules(rulebook.Citizen)
    assert among(Equation(citizen >> person, citizen), book)
    assert among(Equation(citizen >> discard,
                          citizen >> livesIn >> place >> discard), book)
    assert among(Equation(citizen >> box(rulebook.knows),
                          citizen >> box(rulebook.knows) >> person), book)
    assert among(deterministic(citizen >> livesIn), book)
    assert among(Equation(citizen >> discard,
                          citizen >> box(rulebook.hasParent) >> person
                          >> discard), book)


def test_equivalent_rules(rulebook):
    with rulebook:
        class Resident(Thing): pass
        class residesIn(rulebook.Person >> rulebook.Place): pass
    Resident.equivalent_to.append(rulebook.Citizen)
    residesIn.equivalent_to.append(rulebook.livesIn)
    assert among(Equation(box(Resident), box(rulebook.Citizen)),
                 rules(Resident))
    assert among(Equation(box(residesIn), box(rulebook.livesIn)),
                 rules(residesIn))


def test_rules_of_an_ontology(rulebook):
    everything = rules(rulebook)
    assert everything and all(
        isinstance(rule, Equation) for rule in everything)
    assert not any(rule for rule in everything)  # none of them are free
    assert among(rules(rulebook.knows)[0], everything)
    with raises(TypeError):
        rules("not an ontology")


@fixture
def horn():
    world = World()
    result = world.get_ontology("http://discopy.org/horn.owl")
    with result:
        class Person(Thing): pass
        class hasParent(Person >> Person): pass
        class hasBrother(Person >> Person): pass
        class hasUncle(Person >> Person): pass
        class hasAge(Person >> int, DataProperty): pass
        uncles, adults = Imp(), Imp()
    uncles.set_as_rule(
        "hasParent(?x, ?y), hasBrother(?y, ?z) -> hasUncle(?x, ?z)")
    adults.set_as_rule("Person(?x), hasAge(?x, 18) -> Person(?x)")
    return result


def state(ontology, *wired):
    """ A state with one box per (entity, source, target) triple. """
    spiders = 1 + max(leg for _, *legs in wired for leg in legs)
    return Hypergraph[Diagram](
        dom=THING ** 0, cod=THING ** spiders,
        boxes=tuple(box(entity) for entity, *_ in wired),
        wires=((), tuple(((source, ), (target, )) for _, source, target
                         in wired), tuple(range(spiders))),
        spider_types=spiders * (THING, )).to_diagram()


def test_drawable(horn):
    uncles, adults = sorted(horn.rules(), key=drawable, reverse=True)
    assert drawable(uncles) and "hasUncle" in str(uncles)
    assert not drawable(adults)  # a literal is not an individual


def test_variable(horn):
    assert variable("x0", horn) is variable("x0", horn)
    assert variable("x0", horn) is not variable("x1", horn)


def test_conjunction(horn):
    uncles = next(rule for rule in horn.rules() if drawable(rule))
    order = variables(uncles.body)
    assert [name.name for name in order] == ["x", "y", "z"]
    body = conjunction(uncles.body, order)
    assert body.dom == THING ** 0 and body.cod == THING ** 3
    assert set(body.to_hypergraph().boxes) == {
        box(horn.hasParent), box(horn.hasBrother)}


def test_conjunction_of_a_class_is_a_loop(horn):
    order = [variable("x", horn)]
    atom = ClassAtom(namespace=horn)
    atom.class_predicate, atom.arguments = horn.Person, order
    graph = conjunction([atom], order).to_hypergraph()
    assert graph.wires[1] == (((0, ), (0, )), )  # both legs, one spider


def test_implication(horn):
    rule = implication(next(r for r in horn.rules() if drawable(r)))
    assert rule.symbols[0] == INCLUSION and not rule
    assert all(term.dom == THING ** 0 for term in rule.terms)
    assert rule.terms[0].cod == rule.terms[1].cod == THING ** 3


def test_swrl_round_trip(horn):
    uncles = next(rule for rule in horn.rules() if drawable(rule))
    written, = swrl(implication(uncles), horn)
    assert str(written) == (
        "hasParent(?x0, ?x1), hasBrother(?x1, ?x2) -> hasUncle(?x0, ?x2)")
    assert str(swrl(implication(written), horn)[0]) == str(written)


def test_swrl_of_an_equation_is_two_rules(horn):
    parent = state(horn, (horn.hasParent, 0, 1))
    uncle = state(horn, (horn.hasUncle, 0, 1))
    there, back = swrl(Equation(parent, uncle), horn)
    assert str(there) == "hasParent(?x0, ?x1) -> hasUncle(?x0, ?x1)"
    assert str(back) == "hasUncle(?x0, ?x1) -> hasParent(?x0, ?x1)"


def test_swrl_of_a_class_across_two_wires(horn):
    across = state(horn, (horn.Person, 0, 1))
    rule, = swrl(Equation(across, across, symbol=INCLUSION), horn)
    assert [type(atom).__name__ for atom in rule.body] == [
        "ClassAtom", "SameIndividualAtom"]


def test_atoms_needs_a_state(horn):
    with raises(ValueError):
        atoms(box(horn.hasParent), [], horn)


def test_rules_includes_the_ontologys_own(horn):
    uncles = next(rule for rule in horn.rules() if drawable(rule))
    assert implication(uncles).terms in [
        rule.terms for rule in rules(horn)]


@fixture
def kennel():
    world = World()
    result = world.get_ontology("http://discopy.org/kennel.owl")
    with result:
        class Person(Thing): pass
        class Dog(Thing): pass
        class owns(Person >> Dog): pass  # noqa: F811
        class barksAt(Dog >> Person): pass
        class hasName(Dog >> str, DataProperty, FunctionalProperty): pass
        Dog.is_a.append(barksAt.some(Person))
        Dog.is_a.append(hasName.exactly(1, str))
    return result


def test_source_and_target(kennel):
    assert source(box(kennel.owns)) == [kennel.Person]
    assert target(box(kennel.owns)) == [kennel.Dog]
    assert source(box(kennel.Dog)) == []  # a test is defined on everything
    assert target(box(kennel.Dog)) == [kennel.Dog]


@needs_java
def test_subsumes(kennel):
    world = kennel.world
    assert subsumes(world, [kennel.Dog], [])  # everything is a Thing
    assert subsumes(world, [kennel.Dog], [kennel.Dog])
    assert not subsumes(world, [kennel.Dog], [kennel.Person])


@needs_java
def test_validate_a_diagram(kennel):
    world, owns = kennel.world, box(kennel.owns)
    barks = box(kennel.barksAt)
    assert (owns >> barks).validate(world) == owns >> barks
    assert (box(kennel.Person) >> owns).incoherent(world) == []
    with raises(AxiomError):
        (barks >> barks).validate(world)  # a person is not a dog
    with raises(AxiomError):
        (box(kennel.Dog) >> owns).validate(world)


def test_assertions(kennel):
    with kennel:
        rex, alice = kennel.Dog("rex"), kennel.Person("alice")
    rex.hasName = "Rex"  # functional, so not a list
    rex.barksAt.append(alice)
    assert assertions(rex, kennel.hasName) == ["Rex"]
    assert assertions(rex, kennel.barksAt) == [alice]
    assert assertions(alice, kennel.owns) == []


def test_meets(kennel):
    with kennel:
        rex, alice = kennel.Dog("rex"), kennel.Person("alice")
    assert not meets([], kennel.barksAt.some(kennel.Person))
    assert meets([alice], kennel.barksAt.some(kennel.Person))
    assert not meets([alice], kennel.barksAt.min(2, kennel.Person))
    assert meets([alice], kennel.barksAt.max(1, kennel.Person))
    assert meets([alice], kennel.barksAt.exactly(1, kennel.Person))
    assert not meets([rex], kennel.barksAt.only(kennel.Person))
    assert meets([alice], kennel.barksAt.value(alice))  # nothing to count


def test_unmet_and_check(kennel):
    with kennel:
        rex = kennel.Dog("rex")
    assert len(unmet(rex, kennel.Dog)) == 2  # no name, barks at nobody
    with raises(AxiomError):
        Function.check(rex, kennel.Dog)
    Function.check(rex, str)  # not a class, so nothing to meet
    Function.check("rex", kennel.Dog)  # not an individual either


@needs_java
def test_a_function_checks_what_it_inserts(kennel):
    world = kennel.world

    def inside(state, name):
        with kennel:
            return kennel.Dog(name)

    adopt = Function(inside, str, kennel.Dog)
    with raises(AxiomError):
        adopt(world, "fido")  # a dog with no name and nobody to bark at

    def complete(state, name):
        with kennel:
            dog, owner = kennel.Dog(name), kennel.Person(f"{name}-owner")
        dog.hasName, dog.barksAt = name.title(), [owner]
        return dog

    assert Function(complete, str, kennel.Dog)(world, "rex").hasName == "Rex"


def test_assertions_walk_the_property_hierarchy(kennel):
    with kennel:
        class knows(kennel.Person >> Thing): pass
        class owns(kennel.Person >> kennel.Dog): pass
        owns.is_a.append(knows)
        alice, rex = kennel.Person("alice"), kennel.Dog("rex")
    alice.owns.append(rex)
    assert assertions(alice, knows) == [rex]  # what it owns, it knows


def test_unmet_leaves_an_unresolved_filler_alone(kennel):
    with kennel:
        class hasVet(kennel.Dog >> Thing): pass
        fido = kennel.Dog("fido")
    kennel.Dog.is_a.append(hasVet.some("http://elsewhere.org#Vet"))
    fido.hasName, fido.barksAt = "Fido", [kennel.Person("bob")]
    assert unmet(fido, kennel.Dog) == []
