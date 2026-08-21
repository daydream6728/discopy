# -*- coding: utf-8 -*-

from shutil import which

from pytest import fixture, importorskip, mark, raises

importorskip("owlready2")

from owlready2 import (  # noqa: E402
    JAVA_EXE, ClassAtom, DataProperty, FunctionalProperty, Imp,
    InverseFunctionalProperty, PropertyChain, PropertyClass,
    ReflexiveProperty, SymmetricProperty, Thing, ThingClass,
    TransitiveProperty, World, sync_reasoner_hermit)

from discopy import frobenius  # noqa: E402
from discopy.python.owl import (  # noqa: E402
    INCLUSION, THING, Coercion, Diagram, Rule, atoms, box, coercion,
    conjunction, declared, deterministic, drawable, implication, membership,
    ob, parallel, predicates, reason, resolve, rules, subsumes, variable,
    variables)
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
        class barksAt(Dog >> Person): pass
        class knows(Person >> Person, SymmetricProperty): pass
        class descends(Dog >> Dog, TransitiveProperty): pass
        class sameAs(Dog >> Dog, ReflexiveProperty): pass
        class chip(Dog >> Person, FunctionalProperty): pass
        class tag(Dog >> Person, InverseFunctionalProperty): pass
        class ownedBy(Dog >> Person): pass
        class named(Dog >> str, DataProperty): pass
        class untyped(Thing >> Thing): pass
        owns.inverse_property = ownedBy
        Dog.is_a.append(barksAt.some(Person))
        Dog.is_a.append(barksAt.only(Person))
        Dog.is_a.append(chip.max(1, Person))
        Dog.is_a.append(tag.exactly(1, Person))
        Dog.is_a.append(owns.min(1, Dog))
        Dog.is_a.append(owns.min(2, Dog))  # no rule for a cardinality of two
        Dog.is_a.append(named.some(str))  # a datatype filler, so no rule
    return result


def test_declared(kennel):
    assert declared(kennel.Dog, ThingClass)
    assert not declared(Thing, ThingClass)  # owl:Thing says nothing
    assert not declared(TransitiveProperty, PropertyClass)
    assert not declared(kennel.Dog, PropertyClass)


def test_ob(kennel):
    assert ob(kennel.Dog) == frobenius.Ty("Dog")
    assert ob() == ob(Thing) == ob("not an entity") == THING


def test_box_is_typed_by_the_ontology(kennel):
    assert (box(kennel.owns).dom, box(kennel.owns).cod) == (
        ob(kennel.Person), ob(kennel.Dog))
    assert box(kennel.untyped).dom == box(kennel.untyped).cod == THING
    assert box(kennel.owns, THING, THING).dom == THING
    assert membership(kennel.Dog) == coercion(THING, ob(kennel.Dog))
    assert box(kennel.owns).data is kennel.owns


def test_coercion(kennel):
    assert coercion(THING, THING) == Diagram.id(THING)
    assert isinstance(coercion(THING, ob(kennel.Dog)), Coercion)


def test_then_coerces(kennel):
    owns, barks = box(kennel.owns), box(kennel.barksAt)
    assert (owns >> barks).coercions == []  # a dog is a dog
    crooked = barks >> barks
    assert [str(one.cod) for one in crooked.coercions] == ["Dog"]
    assert (owns >> owns).coercions[0].dom == ob(kennel.Dog)


def test_everywhere(kennel):
    owns = box(kennel.owns)
    assert owns.everywhere().dom == owns.everywhere().cod == THING
    state = conjunction([], [])
    assert state.everywhere() == state  # nothing to widen


def test_parallel(kennel):
    owns, knows = box(kennel.owns), box(kennel.knows)
    assert parallel(owns, owns) == (owns, owns)
    left, right = parallel(owns, knows)
    assert left.dom == right.dom == THING


@needs_java
def test_subsumes_and_validate(kennel):
    world, owns = kennel.world, box(kennel.owns)
    barks, chip = box(kennel.barksAt), box(kennel.chip)
    assert (owns >> barks).validate(world) == owns >> barks
    assert (barks >> owns).validate(world) == barks >> owns
    reason(world)
    assert subsumes(world, coercion(ob(kennel.Dog), ob(kennel.Animal)))
    assert subsumes(world, coercion(ob(kennel.Dog), THING))
    assert not subsumes(world, coercion(ob(kennel.Person), ob(kennel.Dog)))
    assert not subsumes(world, coercion(THING, frobenius.Ty("Nowhere")))
    with raises(AxiomError):
        (barks >> barks).validate(world)  # a person is not a dog
    assert (chip >> owns >> barks).coercions == []  # and this one is fine


def test_deterministic(kennel):
    single = deterministic(box(kennel.chip))
    assert not single  # it is an axiom, not a theorem of the free category
    assert single.terms[0].cod == ob(kennel.Person) ** 2


def among(rule, rulebook):
    """ Whether a rule is one of a list, as `Equation` has no `__eq__`. """
    return any((other.terms, other.symbols) == (rule.terms, rule.symbols)
               for other in rulebook)


def test_property_rules(kennel):
    knows, owns = box(kennel.knows), box(kennel.owns)
    descends, chip = box(kennel.descends), box(kennel.chip)
    assert among(Rule(knows, knows.transpose()), rules(kennel.knows))
    assert among(Rule(descends >> descends, descends, symbol=INCLUSION),
                 rules(kennel.descends))
    assert among(Rule(Diagram.id(ob(kennel.Dog)), box(kennel.sameAs),
                      symbol=INCLUSION), rules(kennel.sameAs))
    assert among(deterministic(chip), rules(kennel.chip))
    assert among(deterministic(box(kennel.tag).transpose()),
                 rules(kennel.tag))
    assert among(Rule(*parallel(owns.transpose(), box(kennel.ownedBy))),
                 rules(kennel.owns))


def test_property_rules_of_a_chain_and_a_parent(kennel):
    with kennel:
        class walks(kennel.Person >> kennel.Dog): pass
        class strolls(kennel.Person >> kennel.Dog): pass
        strolls.is_a.append(walks)
        walks.property_chain.append(
            PropertyChain([kennel.knows, kennel.owns]))
        walks.equivalent_to.append(strolls)
    assert among(Rule(*parallel(box(strolls), box(walks)), symbol=INCLUSION),
                 rules(strolls))
    assert among(Rule(*parallel(box(walks), box(strolls))), rules(walks))
    assert any(["knows", "owns"] == [step.name for step in rule.terms[0].boxes
                                     if step.data is not None]
               for rule in rules(walks))


def test_class_rules(kennel):
    dog, book = membership(kennel.Dog), rules(kennel.Dog)
    barks, person = box(kennel.barksAt), ob(kennel.Person)
    path = dog >> barks
    assert among(Rule(*parallel(dog >> Diagram.discard(dog.cod),
                                path >> Diagram.discard(person))), book)
    assert among(Rule(*parallel(path, path)), book)  # the universal
    assert among(deterministic(dog >> box(kennel.chip)), book)
    assert len(book) == 6  # some, only, max, exactly twice, min one


def test_rules_of_an_ontology(kennel):
    everything = rules(kennel)
    assert everything and all(isinstance(rule, Rule) for rule in everything)
    assert among(rules(kennel.knows)[0], everything)
    with raises(TypeError):
        rules("not an ontology")


def test_typing_makes_a_universal_free(kennel):
    """ `Dog barksAt only Person` says nothing once `barksAt` is typed by
    its range, which is what having predicates as objects buys. """
    universal, = [rule for rule in rules(kennel.Dog) if rule]
    assert universal.terms[0] == universal.terms[1]
    assert universal.terms[0].boxes[-1].data is kennel.barksAt


@fixture
def horn(kennel):
    with kennel:
        uncles, adults = Imp(), Imp()
    uncles.set_as_rule(
        "Dog(?x), owns(?y, ?x), barksAt(?x, ?z) -> knows(?y, ?z)")
    adults.set_as_rule("Dog(?x), named(?x, 'Rex') -> Dog(?x)")
    return kennel


def only_drawable(ontology):
    return next(rule for rule in ontology.rules() if drawable(rule))


def test_drawable(horn):
    assert not all(map(drawable, horn.rules()))  # a literal is not a wire
    assert drawable(only_drawable(horn))


def test_variable(horn):
    assert variable("x0", horn) is variable("x0", horn)
    assert variable("x0", horn) is not variable("x1", horn)


def test_predicates_type_the_variables(horn):
    rule = only_drawable(horn)
    order = variables([*rule.body, *rule.head])
    typed = predicates(rule.body, order)
    assert [str(one) for one in typed.values()] == ["Dog", "Thing", "Thing"]


def test_conjunction(horn):
    rule = only_drawable(horn)
    order = variables([*rule.body, *rule.head])
    body = conjunction(rule.body, order)
    assert body.dom == THING ** 0 and len(body.cod) == 3
    assert [step.name for step in body.boxes if not isinstance(
        step, (Coercion, frobenius.Spider, frobenius.Swap, frobenius.Cup,
               frobenius.Cap))] == ["owns", "barksAt"]  # Dog is a wire now


def test_conjunction_keeps_a_second_class_as_a_box(horn):
    order = [variable("x", horn)]
    both = [ClassAtom(namespace=horn), ClassAtom(namespace=horn)]
    for atom, entity in zip(both, (horn.Dog, horn.Animal)):
        atom.class_predicate, atom.arguments = entity, order
    assert conjunction(both, order).cod == THING  # two of them, so untyped
    assert len(conjunction(both, order).to_hypergraph().boxes) == 2


def test_implication_round_trip(horn):
    rule = implication(only_drawable(horn))
    assert rule.symbols[0] == INCLUSION and not rule
    written, = rule.swrl(horn)
    assert str(written) == (
        "Dog(?x0), owns(?x1, ?x0), barksAt(?x0, ?x2) -> knows(?x1, ?x2)")
    assert str(implication(written).swrl(horn)[0]) == str(written)


def test_an_equation_is_two_rules(horn):
    rule = only_drawable(horn)
    order = variables(rule.body)
    owns = conjunction([rule.body[1]], order)
    barks = conjunction([rule.body[2]], order)
    there, back = Rule(*parallel(owns, barks)).swrl(horn)
    assert str(there).split(" -> ")[1] == str(back).split(" -> ")[0]
    assert str(back).split(" -> ")[1] == str(there).split(" -> ")[0]


def test_atoms_needs_a_state(horn):
    with raises(ValueError):
        atoms(box(horn.owns), [], horn)


def test_resolve(horn):
    assert resolve(THING, horn) is None
    assert resolve(frobenius.Ty("Nowhere"), horn) is None
    assert resolve(ob(horn.Dog), horn) is horn.Dog


@needs_java
def test_reason(kennel):
    reason(kennel.world)
    assert issubclass(kennel.Dog, kennel.Animal)
    sync_reasoner_hermit(kennel.world, debug=0)  # the default is HermiT
