# -*- coding: utf-8 -*-

from shutil import which

from pytest import fixture, importorskip, mark, raises

importorskip("owlready2")

from owlready2 import (  # noqa: E402
    JAVA_EXE, AllDisjoint, AsymmetricProperty, FunctionalProperty, Inverse,
    InverseFunctionalProperty, IrreflexiveProperty, Not, OneOf,
    PropertyChain, ReflexiveProperty, Restriction, SymmetricProperty,
    Thing, ThingClass, TransitiveProperty, World)

from discopy import frobenius  # noqa: E402
from discopy.owl import (  # noqa: E402
    Axiom, Relation, axioms, box, carrier, class_axioms, combine,
    consistent, declared, expr_world, extension, find_world, instances,
    coercion, label, load, ob, parallel, point, property_axioms, reason,
    relations, satisfying, schema, to_diagram)
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
        class named(Dog >> str): pass
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
    assert not owns >> knows  # coerced through Dog ⊓ Person, which is empty
    with raises(AxiomError):
        owns >> Relation.id(())  # only an arity mismatch fails


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


def test_permutation_rejects(kennel):
    with raises(ValueError):
        Relation.permutation([0, 0], [(kennel.Dog, ), (kennel.Person, )])


def test_schema_of_an_inverse(kennel):
    assert schema(Inverse(kennel.owns)) == (kennel.Dog, kennel.Person)


def test_to_diagram_rejects(kennel):
    with raises(NotImplementedError):
        to_diagram(42, dom=Thing)


def test_preload_skips_a_file_without_ontology(kennel, tmp_path):
    (tmp_path / "notes.rdf").write_text("just a note, no owl:Ontology")
    kennel.save(file=str(tmp_path / "kennel.rdf"))
    copy = load("http://discopy.org/kennel.owl",
                world=World(), path=str(tmp_path))
    assert {one.name for one in copy.classes()}\
        == {one.name for one in kennel.classes()}


def test_preload_rejects_a_missing_directory(tmp_path):
    with raises(FileNotFoundError):
        load("http://x/a/", world=World(), path=str(tmp_path / "nowhere"))


def test_preload_rejects_cycles(tmp_path):
    for name, other in (("a", "b"), ("b", "a")):
        (tmp_path / f"{name}.rdf").write_text(
            f'<owl:Ontology rdf:about="http://x/{name}/">\n'
            f'<owl:imports rdf:resource="http://x/{other}/"/>')
    with raises(ValueError):
        load("http://x/a/", world=World(), path=str(tmp_path))


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


def test_relations(kennel):
    assert relations(kennel.owns) == {
        kennel.ada: {kennel.rex}, kennel.bob: {kennel.rex, kennel.fido}}
    assert relations(Inverse(kennel.owns)) == {
        kennel.rex: {kennel.ada, kennel.bob}, kennel.fido: {kennel.bob}}


def test_satisfying_boolean_constructs(kennel):
    world = kennel.world
    people, dogs = satisfying(kennel.Person, world), set(
        instances(kennel.Dog))
    assert satisfying(Thing, world) == people | dogs | {
        kennel.ada, kennel.bob, kennel.rex, kennel.fido}
    assert satisfying(kennel.Person & kennel.Animal, world) == set()
    assert satisfying(kennel.Person | kennel.Dog, world) == people | dogs
    assert satisfying(Not(kennel.Person), world)\
        == satisfying(Thing, world) - people
    assert satisfying(OneOf([kennel.rex]), world) == {kennel.rex}
    with raises(NotImplementedError):
        satisfying("not a construct", world)


def test_satisfying_restrictions(kennel):
    world, owns, dog = kennel.world, kennel.owns, kennel.Dog
    assert satisfying(owns.some(dog), world) == {kennel.ada, kennel.bob}
    assert satisfying(owns.value(kennel.fido), world) == {kennel.bob}
    assert satisfying(owns.min(2, dog), world) == {kennel.bob}
    assert satisfying(owns.max(1, dog), world)\
        == satisfying(Thing, world) - {kennel.bob}
    assert satisfying(owns.exactly(1, dog), world) == {kennel.ada}
    assert satisfying(owns.only(dog), world) == satisfying(Thing, world)
    assert satisfying(kennel.knows.has_self(), world) == set()
    with kennel:
        kennel.ada.knows.append(kennel.ada)
    assert satisfying(kennel.knows.has_self(), world) == {kennel.ada}
    with raises(NotImplementedError):
        satisfying(kennel.named.some(str), world)  # a datatype filler


def test_extension(kennel):
    assert extension(kennel.Dog) == Relation.id(kennel.Dog)
    hoarders = extension(kennel.owns.min(2, kennel.Dog), dom=kennel.Person)
    assert [x.name for (x, ), _ in hoarders.inside] == ["bob"]
    assert extension(Thing, world=kennel.world)\
        == Relation.id(Thing, kennel.world)


def test_expr_world(kennel):
    world = kennel.world
    assert expr_world(kennel.Dog) is world
    assert expr_world(kennel.Dog & Thing) is world
    assert expr_world(Not(kennel.Dog)) is world
    assert expr_world(OneOf([kennel.rex])) is world
    assert expr_world(kennel.owns.some(Thing)) is world
    assert expr_world(Inverse(kennel.owns).some(Thing)) is world
    assert expr_world(Thing) is None
    assert expr_world(OneOf([])) is None


def test_axiom(kennel):
    owns = Relation.from_property(kennel.owns)
    single = Axiom(owns >> owns.dagger(), Relation.id(kennel.Person))
    assert not single  # ada and bob share rex
    assert str(Axiom(owns, owns, symbol="=")).count("=") == 1
    assert "<=" in str(single)


def test_class_axioms(kennel):
    with kennel:
        class Pet(Thing): pass
        class Barker(Thing):
            equivalent_to = [kennel.Dog]
        kennel.Dog.is_a.append(Pet)
        kennel.Dog.is_a.append(kennel.knows.some(Thing))  # dogs know nobody
        kennel.Dog.is_a.append(kennel.named.some(str))  # not compiled
    book = class_axioms(kennel.Dog)
    sources = [axiom.source[1] for axiom in book]
    assert Pet in sources and kennel.Animal in sources
    assert not any(  # the datatype restriction is skipped
        "named" in str(source) for source in sources)
    broken = [axiom for axiom in book if not axiom]
    assert [axiom.source[1] for axiom in broken]\
        == [kennel.knows.some(Thing)]  # a named parent holds by search
    assert all(class_axioms(Barker))  # so does an equivalence


def test_property_axioms_characteristics(kennel):
    with kennel:
        class descends(kennel.Dog >> kennel.Dog, TransitiveProperty): pass
        class near(kennel.Dog >> kennel.Dog, SymmetricProperty): pass
        class above(kennel.Dog >> kennel.Dog, AsymmetricProperty): pass
        class sameAs(kennel.Dog >> kennel.Dog, ReflexiveProperty): pass
        class other(kennel.Dog >> kennel.Dog, IrreflexiveProperty): pass
        class chip(kennel.Dog >> kennel.Person, FunctionalProperty): pass
        class tag(kennel.Dog >> kennel.Person,
                  InverseFunctionalProperty): pass
    for prop in (descends, near, above, other, chip, tag):
        assert all(property_axioms(prop))  # empty relations satisfy these
    reflexivity, = [axiom for axiom in property_axioms(sameAs)
                    if len(axiom.terms[0].inside)]
    assert not reflexivity  # nothing is sameAs itself, closed world


def test_property_axioms_structure(kennel):
    with kennel:
        class ownedBy(kennel.Dog >> kennel.Person): pass
        class has(kennel.Person >> kennel.Dog): pass
        class walksWith(kennel.Person >> kennel.Dog): pass
        kennel.owns.is_a.append(has)
        kennel.owns.equivalent_to.append(has)
        ownedBy.inverse_property = kennel.owns
        walksWith.property_chain.append(
            PropertyChain([kennel.knows, kennel.owns]))
    for x, ys in relations(kennel.owns).items():
        for y in ys:
            x.has.append(y)
            y.ownedBy.append(x)
    assert all(property_axioms(kennel.owns))
    walks = property_axioms(walksWith)[0]  # the chain, then domain, range
    assert not walks  # ada knows bob who owns fido, but walks with nobody
    domain, range_ = [axiom for axiom in property_axioms(kennel.knows)
                      if axiom.source is kennel.knows][-2:]
    assert domain and range_


def test_axioms(kennel):
    with kennel:
        AllDisjoint([kennel.Dog, kennel.Person])
    book = axioms(kennel)
    assert all(book)  # the kennel is a model of its own schema
    assert any("=" in axiom.symbols for axiom in book)  # the disjointness
    assert [str(one) for one in axioms(kennel.Dog)]\
        == [str(one) for one in class_axioms(kennel.Dog)]
    assert len(axioms(kennel.owns)) == len(property_axioms(kennel.owns))
    with raises(TypeError):
        axioms("not an entity")


def test_ob_box_point(kennel):
    assert ob() == frobenius.Ty("Thing")
    assert ob((kennel.Person, kennel.Dog)) == frobenius.Ty("Person", "Dog")
    assert box(kennel.owns) == frobenius.Box(
        "owns", frobenius.Ty("Person"), frobenius.Ty("Dog"))
    assert box(Inverse(kennel.owns)) == box(kennel.owns).dagger()
    assert point(kennel.rex).cod == frobenius.Ty("Dog")


def test_to_diagram_constructs(kennel):
    dog, person, thing = kennel.Dog, kennel.Person, frobenius.Ty("Thing")
    assert to_diagram(kennel.rex) == point(kennel.rex)
    assert to_diagram(kennel.owns) == box(kennel.owns)
    assert to_diagram(dog) == frobenius.Id(frobenius.Ty("Dog"))
    assert to_diagram(dog, dom=Thing)\
        == frobenius.Box("Dog", thing, thing)
    assert to_diagram(dog & person, dom=Thing)\
        == to_diagram(dog, Thing) >> to_diagram(person, Thing)
    union = to_diagram(dog | person, dom=Thing)
    assert isinstance(union, frobenius.Bubble) and len(union.args) == 2
    negation = to_diagram(Not(dog), dom=Thing)
    assert isinstance(negation, frobenius.Bubble)
    assert to_diagram(OneOf([kennel.rex]), dom=Thing).name == "{rex}"
    with raises(NotImplementedError):
        to_diagram(kennel.named.some(str), dom=Thing)


def test_restriction_diagrams(kennel):
    owns, dog = kennel.owns, kennel.Dog
    for construct in (owns.some(dog), owns.only(dog),
                      owns.value(kennel.rex), owns.min(2, dog),
                      owns.max(1, dog), owns.exactly(1, dog),
                      kennel.knows.has_self(), owns.min(0, dog)):
        diagram = to_diagram(construct, dom=kennel.Person)
        typ = frobenius.Ty("Person")
        assert (diagram.dom, diagram.cod) == (typ, typ)


def test_relation_pictures(kennel):
    owns = Relation.from_property(kennel.owns)
    knows = Relation.from_property(kennel.knows)
    assert (knows >> owns).to_diagram()\
        == knows.to_diagram() >> owns.to_diagram()
    assert owns.dagger().to_diagram() == owns.to_diagram().dagger()
    assert (owns @ knows).to_diagram()\
        == owns.to_diagram() @ knows.to_diagram()
    assert isinstance(owns.neg().to_diagram(), frobenius.Bubble)
    assert isinstance(knows.repeat().to_diagram(), frobenius.Bubble)
    assert owns.meet(owns).to_diagram().boxes  # copy, both, merge
    assert isinstance(owns.join(owns.neg()).to_diagram(), frobenius.Bubble)
    assert owns.domain().to_diagram().cod == frobenius.Ty("Person")
    forgetful = Relation(owns.inside, owns.dom, owns.cod)  # no history
    assert forgetful.diagram is None
    assert forgetful.to_diagram() == frobenius.Box(
        "?", frobenius.Ty("Person"), frobenius.Ty("Dog"))
    assert (forgetful >> owns.dagger()).diagram is None
    assert combine(lambda x: x, None) is None


def test_axiom_draw(kennel, tmp_path):
    axioms(kennel.knows)[0].draw(path=str(tmp_path / "axiom.png"))
    extension(kennel.owns.some(kennel.Dog)).draw(
        path=str(tmp_path / "some.png"))


def test_label(kennel):
    dog, person, owns = kennel.Dog, kennel.Person, kennel.owns
    assert label(Thing) == "Thing" and label(dog) == "Dog"
    assert label(owns) == "owns" and label(kennel.rex) == "rex"
    assert label(Inverse(owns)) == "owns˘"
    assert label(person & Not(owns.some(dog) | owns.value(kennel.rex)))\
        == "Person ⊓ ¬(∃owns.Dog ⊔ ∃owns.{rex})"
    assert label(owns.only(OneOf([kennel.rex]))) == "∀owns.{rex}"
    assert label(kennel.knows.has_self()) == "∃knows.Self"
    assert label(owns.min(2, dog)) == "≥2 owns.Dog"
    assert label(owns.max(1, dog)) == "≤1 owns.Dog"
    assert label(owns.exactly(1, dog)) == "=1 owns.Dog"
    assert label(str) == "str" and label(42) == "42"


def test_constructs_as_objects(kennel):
    parents = kennel.owns.some(kennel.Dog)
    assert instances(parents) == (kennel.ada, kennel.bob)
    wire = Relation.id(parents)
    assert wire == extension(parents) and len(wire.inside) == 2
    assert wire.to_diagram() == frobenius.Id(frobenius.Ty("∃owns.Dog"))
    assert Relation.top(parents, parents).neg()\
        == Relation.bottom(parents, parents)
    assert Relation.spiders(1, 0, parents).dom == (parents, )
    assert find_world((parents, )) is kennel.world


def test_coercion(kennel):
    dog, animal, person = kennel.Dog, kennel.Animal, kennel.Person
    assert coercion(dog, dog) == Relation.id(dog)
    free = coercion(dog, animal)
    assert free.domain() == Relation.id(dog)  # a dog is an animal
    assert not coercion(dog, person)  # but not a person
    assert free.to_diagram() == frobenius.Box(
        "Animal", frobenius.Ty("Dog"), frobenius.Ty("Animal"))


def test_then_coerces(kennel):
    owns = Relation.from_property(kennel.owns)
    ada = Relation.from_individual(kennel.ada, kennel.Person)
    everyone = Relation.from_property(kennel.owns, Thing, Thing)
    coerced = ada >> everyone  # a coercion Person -> Thing is inserted
    assert coerced == ada >> coercion(kennel.Person, Thing) >> everyone
    assert set(coerced.inside) == {((), (kennel.rex, ))}
    assert "Thing" in [box.name for box in coerced.to_diagram().boxes]
    two_dogs = owns >> coercion(kennel.Dog, kennel.Animal)
    assert (ada >> owns >> two_dogs.dagger()).dom == ()  # auto-coerced


def test_from_property_filters_to_its_boundary(kennel):
    with kennel:
        kennel.rex.knows = [kennel.ada]  # a dog outside knows' domain
    at_schema = Relation.from_property(kennel.knows)
    assert ((kennel.rex, ), (kennel.ada, )) not in at_schema.inside
    at_thing = Relation.from_property(kennel.knows, Thing, Thing)
    assert ((kennel.rex, ), (kennel.ada, )) in at_thing.inside
    assert at_schema <= Relation.top(at_schema.dom, at_schema.cod)


def test_parallel(kennel):
    owns = Relation.from_property(kennel.owns)
    knows = Relation.from_property(kennel.knows)
    assert parallel(owns, owns) == (owns, owns)
    left, right = parallel(owns, knows)
    assert left.dom == right.dom == (Thing, )
    assert left == Relation.from_property(kennel.owns, Thing, Thing)
    with raises(AxiomError):
        parallel(owns, Relation.id(()))


FIBO = "https://spec.edmcouncil.org/fibo/ontology/"
FIXTURES = "test/fixtures/fibo"


def market_world():
    world = World()
    load(FIBO + "BE/OwnershipAndControl/CorporateControl/",
         world, path=FIXTURES)
    company = world.search_one(
        iri=FIBO + "BE/LegalEntities/LegalPersons/BusinessEntity")
    person = world.search_one(
        iri=FIBO + "BE/LegalEntities/LegalPersons"
        "/LegallyCompetentNaturalPerson")
    controls = world.search_one(iri=FIBO + "FND/Relations/Relations"
                                "/controls")
    demo = world.get_ontology("http://discopy.org/market.owl")
    with demo:
        alice = person("alice")
        holdings, bank, shell = map(
            company, ("acme_holdings", "acme_bank", "shell_co"))
        alice.controls = [holdings]
        holdings.controls = [bank]
        bank.controls = [shell]
    return world, demo, company, person, controls


@fixture(scope="module")
def market():
    return market_world()


def test_fibo_chain_axiom(market):
    world = market[0]
    owning = world.search_one(iri="*hasDirectOwningEntity")
    chain, = [axiom for axiom in property_axioms(owning)
              if len(axiom.terms[0].to_diagram().boxes) == 2]
    assert [box.name for box in chain.terms[0].to_diagram().boxes]\
        == ["hasDirectOwnership", "hasOwningEntity"]
    assert chain  # trivially, over an empty extension


def test_fibo_axioms_hold(market):
    world, demo, company, person, controls = market
    onto = world.get_ontology(
        FIBO + "BE/OwnershipAndControl/ControlParties/")
    assert all(axioms(onto))


def test_unresolved_restriction_is_outside_the_dictionary(market):
    world = market[0]
    stray = next(
        parent for onto in list(world.ontologies.values())
        for cls in onto.classes() for parent in cls.is_a
        if isinstance(parent, Restriction)
        and isinstance(parent.property, str))  # points into a stub
    with raises(NotImplementedError):
        to_diagram(stray, dom=Thing)


def test_market_control_chain(market):
    world, demo, company, person, controls = market
    web = Relation.from_property(controls, dom=Thing, cod=Thing)
    alice = Relation.from_individual(demo.alice, Thing)
    shell = Relation.from_individual(demo.shell_co, Thing)
    assert not alice >> web >> shell.dagger()  # not directly
    assert alice >> web.repeat() >> shell.dagger()  # but ultimately


def test_fibo_compound_type(market):
    world, demo, company, person, controls = market
    controllers = controls.some(Thing)
    wire = Relation.id(controllers)
    assert [x.name for (x, ), _ in wire.inside]\
        == ["acme_bank", "acme_holdings", "alice"]
    assert wire.to_diagram()\
        == frobenius.Id(frobenius.Ty("∃controls.Thing"))


@needs_java
def test_market_safety():
    world, demo, company, person, controls = market_world()  # a fresh one
    corporate_bodies = FIBO + "BE/LegalEntities/CorporateBodies/"
    for_profit = world.search_one(
        iri=corporate_bodies + "ForProfitCorporation")
    not_for_profit = world.search_one(
        iri=corporate_bodies + "NotForProfitCorporation")
    with demo:
        demo.shell_co.is_a.append(for_profit)
    assert consistent(world)  # so far so good
    with demo:
        demo.shell_co.is_a.append(not_for_profit)  # an agent's mistake
    assert not consistent(world)  # HermiT knows the two are disjoint


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
