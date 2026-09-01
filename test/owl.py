# -*- coding: utf-8 -*-

from shutil import which

from pytest import fixture, importorskip, mark, raises

importorskip("owlready2")

from owlready2 import (  # noqa: E402
    JAVA_EXE, AllDisjoint, Thing, ThingClass, World)

from discopy.owl import (  # noqa: E402
    Relation, carrier, consistent, declared, find_world, instances, load,
    reason)
from discopy.utils import AxiomError  # noqa: E402


needs_java = mark.skipif(which(JAVA_EXE) is None, reason="HermiT needs Java.")


@fixture
def kennel():
    world = World()
    result = world.get_ontology("http://discopy.org/kennel.owl")
    with result:
        class Animal(Thing): pass
        class Dog(Animal): pass
        class Person(Thing): pass
        class owns(Person >> Dog): pass
        class knows(Person >> Person): pass
        rex, fido = Dog("rex"), Dog("fido")
        ada, bob = Person("ada"), Person("bob")
        ada.owns, bob.owns = [rex], [rex, fido]
        ada.knows = [bob]
    return result


def test_declared(kennel):
    assert declared(kennel.Dog, ThingClass)
    assert not declared(Thing, ThingClass)  # owl:Thing says nothing
    assert not declared(kennel.rex, ThingClass)


def test_instances_and_carrier(kennel):
    assert [one.name for one in instances(kennel.Dog)] == ["fido", "rex"]
    assert instances(Thing, kennel.world) == tuple(sorted(
        instances(kennel.Animal) + instances(kennel.Person),
        key=lambda one: one.iri))
    assert carrier((kennel.Person, kennel.Dog)) == tuple(
        (person, dog) for person in instances(kennel.Person)
        for dog in instances(kennel.Dog))
    assert carrier(()) == ((), )


def test_find_world(kennel):
    assert find_world((Thing, kennel.Dog)) is kennel.world
    assert find_world((Thing, ), (Thing, )) is None


def test_init_checks_arity(kennel):
    with raises(AxiomError):
        Relation([((kennel.rex, ), ())], kennel.Dog, kennel.Person)


def test_init_is_deterministic(kennel):
    pairs = [((kennel.ada, ), ()), ((kennel.bob, ), ())]
    assert Relation(pairs, kennel.Person, ())\
        == Relation(pairs[::-1], kennel.Person, ())


def test_str_and_bool(kennel):
    owns = Relation.from_property(kennel.owns)
    assert str(owns) == "owns : ('Person',) -> ('Dog',)"
    assert str(Relation.id(())) == "Relation : () -> ()"
    assert Relation.id(()) and not Relation.bottom((), ())


def test_id_then(kennel):
    owns = Relation.from_property(kennel.owns)
    assert Relation.id(kennel.Person) >> owns\
        == owns == owns >> Relation.id(kennel.Dog)
    knows = Relation.from_property(kennel.knows)
    assert (knows >> owns).inside == (((kennel.ada, ), (kennel.fido, )),
                                      ((kennel.ada, ), (kennel.rex, )))
    with raises(AxiomError):
        owns >> knows


def test_tensor_whiskers_objects(kennel):
    owns = Relation.from_property(kennel.owns)
    assert owns @ (kennel.Dog, ) == owns @ Relation.id(kennel.Dog)
    assert owns @ Relation.id(()) == owns


def test_dagger_is_involutive_and_contravariant(kennel):
    owns = Relation.from_property(kennel.owns)
    knows = Relation.from_property(kennel.knows)
    assert owns.dagger().dagger() == owns
    assert (knows >> owns).dagger() == owns.dagger() >> knows.dagger()


def test_swap_and_permutation(kennel):
    person, dog = (kennel.Person, ), (kennel.Dog, )
    swap = Relation.swap(person, dog)
    assert swap >> swap.dagger() == Relation.id(person + dog)
    assert Relation.permutation([1, 0], [person, dog]) == swap


def test_spiders(kennel):
    dog = (kennel.Dog, )
    assert Relation.spiders(1, 1, dog) == Relation.id(dog)
    copy = Relation.copy(dog)
    assert copy >> copy.dagger() == Relation.id(dog)  # special
    assert copy >> Relation.copy(dog, 0) @ dog == Relation.id(dog)  # unital


def test_cups_and_caps(kennel):
    dog = (kennel.Dog, )
    cup, cap = Relation.cups(dog, dog), Relation.caps(dog, dog)
    snake = cap @ dog >> dog @ cup
    assert snake == Relation.id(dog)
    with raises(AxiomError):
        Relation.cups(dog, (kennel.Person, ))


def test_lattice(kennel):
    owns = Relation.from_property(kennel.owns)
    top = Relation.top(owns.dom, owns.cod)
    bottom = Relation.bottom(owns.dom, owns.cod)
    assert owns.meet(top) == owns == owns.join(bottom)
    assert (owns & ~owns) == bottom and (owns | ~owns) == top
    assert bottom <= owns <= top and not top <= owns
    with raises(AxiomError):
        owns <= Relation.id(kennel.Person)
    with raises(AxiomError):
        owns.meet(Relation.id(kennel.Person))


def test_poset(kennel):
    owns = Relation.from_property(kennel.owns)
    top = Relation.top(owns.dom, owns.cod)
    assert owns < top and top > owns and top >= top


def test_modular_law(kennel):
    r = Relation.from_property(kennel.knows)
    s = Relation.from_property(kennel.owns)
    t = Relation.top(r.dom, s.cod)
    assert (r >> s).meet(t) <= r >> s.meet(r.dagger() >> t)


def test_neg_is_closed_world(kennel):
    knows = Relation.from_property(kennel.knows)
    strangers = knows.neg()
    assert ((kennel.bob, ), (kennel.ada, )) in strangers.inside
    assert knows.meet(strangers) == Relation.bottom(knows.dom, knows.cod)


def test_repeat(kennel):
    knows = Relation.from_property(kennel.knows)
    knows_someone_who = knows.repeat()
    assert Relation.id(kennel.Person) <= knows_someone_who
    assert knows_someone_who >> knows_someone_who == knows_someone_who
    with raises(AxiomError):
        Relation.from_property(kennel.owns).repeat()


def test_from_property_defaults(kennel):
    with kennel:
        class untyped(Thing >> Thing): pass
    assert Relation.from_property(untyped).dom == (Thing, )
    owns = Relation.from_property(kennel.owns, dom=Thing, cod=Thing)
    assert owns.dom == owns.cod == (Thing, )


def test_from_class(kennel):
    dogs = Relation.from_class(kennel.Dog)
    assert dogs == Relation.id(kennel.Dog)
    on_animals = Relation.from_class(kennel.Dog, dom=kennel.Animal)
    assert on_animals.dom == (kennel.Animal, )
    assert on_animals <= Relation.id(kennel.Animal)


def test_from_individual(kennel):
    rex = Relation.from_individual(kennel.rex)
    assert rex.cod == (kennel.Dog, )  # the first named direct class by IRI
    assert rex >> Relation.from_class(kennel.Dog) == rex
    with kennel:
        anonymous = Thing()
    assert Relation.from_individual(anonymous).cod == (Thing, )


def test_sparql(kennel):
    owns = Relation.sparql(
        "SELECT ?x ?y WHERE { ?x <http://discopy.org/kennel.owl#owns> ?y . }",
        kennel.Person, kennel.Dog, kennel.world)
    assert owns == Relation.from_property(kennel.owns)


def test_load(kennel, tmp_path):
    kennel.save(file=str(tmp_path / "kennel.owl"))
    copy = load("http://discopy.org/kennel.owl",
                world=World(), path=str(tmp_path))
    assert {one.name for one in copy.classes()}\
        == {one.name for one in kennel.classes()}
    again = load("http://discopy.org/kennel.owl",
                 world=World(), path=str(tmp_path))
    assert {one.name for one in again.individuals()}\
        == {one.name for one in kennel.individuals()}


@needs_java
def test_reason_classifies_individuals(kennel):
    with kennel:
        class DogOwner(Thing):
            equivalent_to = [kennel.Person & kennel.owns.some(kennel.Dog)]
    assert not Relation.from_class(DogOwner)  # not asserted
    reason(kennel.world)
    assert Relation.from_class(DogOwner, dom=kennel.Person)\
        == Relation.id(kennel.Person)  # but entailed: every person owns


@needs_java
def test_consistent(kennel):
    assert consistent(kennel.world)
    with kennel:
        AllDisjoint([kennel.Dog, kennel.Person])
        kennel.rex.is_a.append(kennel.Person)
    assert not consistent(kennel.world)
