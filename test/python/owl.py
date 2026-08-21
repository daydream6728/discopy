# -*- coding: utf-8 -*-

from shutil import which

from pytest import fixture, importorskip, mark, raises

importorskip("owlready2")

from owlready2 import (
    JAVA_EXE, AllDisjoint, FunctionalProperty, InverseFunctionalProperty,
    OwlReadyInconsistentOntologyError, PropertyChain, PropertyClass,
    ReflexiveProperty, SymmetricProperty, Thing, ThingClass,
    TransitiveProperty, World)

from discopy.frobenius import Diagram, Equation
from discopy.python.owl import (
    INCLUSION, THING, Eval, Function, Query, box, declared, deterministic,
    lift, rules)
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
