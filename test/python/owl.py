# -*- coding: utf-8 -*-

from shutil import which

from pytest import fixture, importorskip, mark, raises

importorskip("owlready2")

from owlready2 import (
    JAVA_EXE, AllDisjoint, OwlReadyInconsistentOntologyError, Thing, World)

from discopy.python.owl import Eval, Function, Query, lift
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
