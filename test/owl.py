# -*- coding: utf-8 -*-

from shutil import which

from pytest import fixture, importorskip, mark, raises

importorskip("owlready2")

from owlready2 import (  # noqa: E402
    JAVA_EXE, AllDisjoint, AsymmetricProperty, FunctionalProperty, Inverse,
    InverseFunctionalProperty, IrreflexiveProperty, Not, Nothing, OneOf,
    PropertyChain, ReflexiveProperty, Restriction, SymmetricProperty,
    Thing, ThingClass, TransitiveProperty, World)
import owlready2  # noqa: E402

from discopy.owl import (  # noqa: E402
    SCRATCH, Axiom, Box, Bubble, Coercion, Id, Query, Relation, Ty, Wire,
    axioms, boundary, box,
    carrier, class_axioms, coercion, combine, compilable, consistent,
    declared, deduced, expr_world, extension, find_world, individual_class,
    instances, label, load, ob, pairs_world, parallel, point,
    property_axioms, reason, relations, satisfying, schema, subsumes,
    to_diagram)
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
    everyone = instances(Thing, kennel.world)
    assert len(everyone) == 4
    assert carrier(2, kennel.world) == tuple(
        (x, y) for x in everyone for y in everyone)
    assert carrier(0, kennel.world) == ((), )


def test_worlds(kennel):
    assert pairs_world([((kennel.rex, ), ())]) is kennel.world
    assert pairs_world([]) is owlready2.default_world
    assert find_world((Thing, kennel.Dog)) is kennel.world
    assert find_world((Thing, ), (Thing, )) is None
    assert expr_world(Thing) is None
    assert expr_world(OneOf([])) is None
    assert expr_world(Not(kennel.Dog)) is kennel.world
    assert expr_world(Inverse(kennel.owns).some(Thing)) is kennel.world


def test_init_checks_arity(kennel):
    with raises(AxiomError):
        Relation([((kennel.rex, ), ())], 1, 1, kennel.world)


def test_init_is_deterministic(kennel):
    pairs = [((kennel.ada, ), ()), ((kennel.bob, ), ())]
    assert Relation(pairs, 1, 0, kennel.world)\
        == Relation(pairs[::-1], 1, 0, kennel.world)


def test_str_and_bool(kennel):
    web = Relation.from_property(kennel.owns)
    assert str(web) == "owns : Thing -> Thing"
    assert str(Relation.id(0, kennel.world)) == "Relation : () -> ()"
    assert str(Relation.id(2, kennel.world))\
        == "Relation : Thing ** 2 -> Thing ** 2"
    assert Relation.id(0, kennel.world)
    assert not Relation.bottom(0, 0, kennel.world)


def test_id_then(kennel):
    web = Relation.from_property(kennel.owns)
    identity = Relation.id(1, kennel.world)
    assert identity >> web == web == web >> identity
    knows = Relation.from_property(kennel.knows)
    assert (knows >> web).inside == (((kennel.ada, ), (kennel.fido, )),
                                     ((kennel.ada, ), (kennel.rex, )))
    with raises(AxiomError):
        web >> Relation.id(2, kennel.world)
    with raises(AxiomError):
        web >> Relation.id(1, World())  # a different world


def test_tensor_and_dagger(kennel):
    web = Relation.from_property(kennel.owns)
    knows = Relation.from_property(kennel.knows)
    assert (web @ knows).dom == 2
    assert web.dagger().dagger() == web
    assert (knows >> web).dagger() == web.dagger() >> knows.dagger()
    with raises(AxiomError):
        web @ Relation.id(1, World())


def test_swap_and_permutation(kennel):
    world = kennel.world
    swap = Relation.swap(1, 1, world)
    assert swap >> swap.dagger() == Relation.id(2, world)
    assert Relation.permutation([1, 0], [1, 1], world) == swap
    with raises(ValueError):
        Relation.permutation([0, 0], [1, 1], world)


def test_spiders(kennel):
    world = kennel.world
    assert Relation.spiders(1, 1, 1, world) == Relation.id(1, world)
    copy = Relation.copy(1, 2, world)
    assert copy >> copy.dagger() == Relation.id(1, world)  # special
    assert copy >> Relation.copy(1, 0, world) @ Relation.id(1, world)\
        == Relation.id(1, world)  # unital


def test_cups_and_caps(kennel):
    world = kennel.world
    cup, cap = Relation.cups(1, 1, world), Relation.caps(1, 1, world)
    snake = cap @ Relation.id(1, world) >> Relation.id(1, world) @ cup
    assert snake == Relation.id(1, world)
    with raises(AxiomError):
        Relation.cups(1, 2, world)


def test_lattice_and_poset(kennel):
    web = Relation.from_property(kennel.owns)
    knows = Relation.from_property(kennel.knows)
    bottom = Relation.bottom(1, 1, kennel.world)
    assert web.meet(web) == web == web.join(bottom)
    assert (web & web.join(knows)) == web
    assert bottom <= web <= (web | knows)
    assert web < web.join(knows) and web.join(knows) > web
    assert web >= web and not web <= bottom
    with raises(AxiomError):
        web <= Relation.id(2, kennel.world)
    with raises(AxiomError):
        web.meet(Relation.id(1, World()))
    with raises(AxiomError):
        web.join(Relation.id(2, kennel.world))


def test_modular_law(kennel):
    r = Relation.from_property(kennel.knows)
    s = Relation.from_property(kennel.owns)
    t = r >> s >> s.dagger() >> s
    assert (r >> s).meet(t) <= r >> s.meet(r.dagger() >> t)


def test_domain_and_repeat(kennel):
    web = Relation.from_property(kennel.owns)
    assert web.domain() <= Relation.id(1, kennel.world)
    assert web.codomain() == web.dagger().domain()
    knows = Relation.from_property(kennel.knows)
    closure = knows.repeat()
    assert Relation.id(1, kennel.world) <= closure
    assert closure >> closure == closure
    with raises(AxiomError):
        Relation.from_individual(kennel.rex).repeat()


def test_sparql(kennel):
    web = Relation.sparql(
        "SELECT ?x ?y WHERE { ?x <http://discopy.org/kennel.owl#owns> ?y . }",
        1, 1, kennel.world)
    assert web == Relation.from_property(kennel.owns)


def test_pictures(kennel):
    web = Relation.from_property(kennel.owns)
    assert web.to_diagram() == Box(
        "owns", Ty("Thing"), Ty("Thing"), data=kennel.owns)
    forgetful = Relation(web.inside, 1, 1, kennel.world)
    assert forgetful.diagram is None
    assert forgetful.to_diagram().name == "?"
    assert (forgetful >> web).diagram is None
    assert combine(lambda x: x, None) is None
    assert isinstance(web.repeat().to_diagram(), Bubble)
    assert isinstance(
        web.join(web.dagger() >> web >> web.dagger()).to_diagram(),
        Bubble)
    assert web.meet(web >> web.dagger() >> web).to_diagram().boxes
    assert web.domain().to_diagram().dom == Ty("Thing")


def test_query_init(kennel):
    web = Relation.from_property(kennel.owns)
    with raises(AxiomError):
        Query(web, (kennel.Person, ), (kennel.Dog, kennel.Dog))
    typed = Query(web, (kennel.Person, ), (kennel.Dog, ))
    assert typed.inside == web  # the schema boundary keeps every pair
    assert typed.relation == typed.inside and typed.world is kennel.world
    forgetful = Query(Relation(web.inside, 1, 1, kennel.world),
                      (kennel.Person, ), (kennel.Dog, ))
    assert forgetful.to_diagram().name == "?"  # no history to draw


def test_query_normalises(kennel):
    web = Relation.from_property(kennel.owns)
    at_dogs = Query(web, (kennel.Dog, ), (kennel.Dog, ))
    assert not at_dogs.inside  # no dog owns anything
    assert boundary((kennel.Dog, ), kennel.world)\
        == extension(kennel.Dog).meet(extension(kennel.Dog))


def test_query_id_and_conversions(kennel):
    dogs = Query.id((kennel.Dog, ))
    assert dogs.inside == extension(kennel.Dog)
    assert dogs.at_thing() == dogs.inside.split((Thing, ), (Thing, ))
    assert Query.id((), kennel.world).inside == Relation.id(0, kennel.world)
    web = Query.from_property(kennel.owns)
    assert Query.id(web.dom) >> web == web == web >> Query.id(web.cod)


def test_query_str_and_bool(kennel):
    web = Query.from_property(kennel.owns)
    assert str(web) == "owns : ('Person',) -> ('Dog',)"
    assert str(Query.id((), kennel.world)) == "Query : () -> ()"
    assert web and not Query.bottom(web.dom, web.cod)


def test_query_algebra(kennel):
    web = Query.from_property(kennel.owns)
    assert web.dagger().dagger() == web
    assert (web @ web).dom == 2 * web.dom
    assert web.meet(web) == web == web.join(
        Query.bottom(web.dom, web.cod))
    assert Query.bottom(web.dom, web.cod) <= web
    assert web.domain() <= Query.id(web.dom)
    assert web.codomain() == web.dagger().domain()
    with raises(AxiomError):
        web.meet(web.dagger())
    with kennel:
        carl = kennel.Person("carl")
        kennel.bob.knows = [carl]  # so that the closure takes a step
    knows = Query.from_property(kennel.knows)
    closure = knows.repeat()
    assert Query.id(knows.dom) <= closure == closure >> closure
    with raises(AxiomError):
        web.repeat()


def test_query_structure(kennel):
    person = (kennel.Person, )
    dog = (kennel.Dog, )
    assert Query.spiders(1, 1, person) == Query.id(person)
    copy = Query.copy(person)
    assert copy >> copy.dagger() == Query.id(person)
    swap = Query.swap(person, dog)
    assert swap >> swap.dagger() == Query.id(person + dog)
    assert Query.permutation([1, 0], [person, dog]) == swap
    cup, cap = Query.cups(dog, dog), Query.caps(dog, dog)
    assert cap @ Query.id(dog) >> Query.id(dog) @ cup == Query.id(dog)
    with raises(AxiomError):
        Query.cups(dog, person)


def test_query_composition_strict(kennel):
    web = Query.from_property(kennel.owns)
    knows = Query.from_property(kennel.knows)
    assert (knows >> web).dom == knows.dom and (knows >> web).cod == web.cod
    with raises(AxiomError):
        web >> Query.id((), kennel.world)  # an arity mismatch still raises


def test_query_composition_coerces(kennel):
    web = Query.from_property(kennel.owns)
    with Query.no_reasoning:
        crooked = web >> web  # a dog is not a person
        one, = crooked.coercions
    assert isinstance(one, Coercion) and one.entailed is None
    assert (one.source, one.target) == (kennel.Dog, kennel.Person)
    assert not crooked  # no owned dog is an owner
    assert Query.reasoning  # the switch is restored


def test_coercion(kennel):
    with Query.no_reasoning:
        assert coercion(kennel.Dog, kennel.Dog) == Query.id((kennel.Dog, ))
        free = coercion(kennel.Dog, kennel.Animal)
    assert free.inside == extension(kennel.Dog)  # a dog is an animal


@needs_java
def test_subsumes_writes_back_reliably(kennel):
    world = kennel.world
    with kennel:
        kennel.Person.is_a.append(kennel.owns.some(kennel.Dog))
        _ = AllDisjoint([kennel.Dog, kennel.Person])
    # a named class below a construct, which issubclass used to miss
    assert subsumes(kennel.Person, kennel.owns.some(kennel.Dog), world)
    assert subsumes(kennel.Dog & kennel.Person, Nothing, world)
    assert not subsumes(kennel.Dog, kennel.owns.some(kennel.Dog), world)


def test_karoubi_splitting(kennel):
    with Query.no_reasoning:
        include = coercion(kennel.Dog, Thing)
        project = coercion(Thing, kennel.Dog)
    assert include >> project == Query.id((kennel.Dog, ))
    assert project >> include\
        == extension(kennel.Dog).split((Thing, ), (Thing, ))


def test_typed(kennel):
    web = Relation.from_property(kennel.owns)
    person, dog = extension(kennel.Person), extension(kennel.Dog)
    chain = (person >> web >> dog).typed()
    assert (chain.dom, chain.cod) == ((kennel.Person, ), (kennel.Dog, ))
    assert chain.relation == person >> web >> dog
    backwards = (person >> web >> dog).dagger().typed()
    assert (backwards.dom, backwards.cod)\
        == ((kennel.Dog, ), (kennel.Person, ))
    whiskered = (web @ dog).typed()
    assert (whiskered.dom, whiskered.cod)\
        == ((Thing, Thing), (Thing, kennel.Dog))
    both = (dog @ person).typed()  # nothing but tests: an identity
    assert both.dom == both.cod == (kennel.Dog, kennel.Person)
    assert both.to_diagram() == Id(ob(both.dom))
    forgetful = Relation(web.inside, 1, 1, kennel.world)
    assert forgetful.typed() == web.split((Thing, ), (Thing, ))


def test_peel_keeps_wide_and_dataless_boxes(kennel):
    wide = Box("wide", ob(2 * (Thing, )), ob(2 * (Thing, )),
               data=kennel.Dog)
    web = Relation.from_property(kennel.owns)
    doubled = web @ web
    doubled.diagram = doubled.to_diagram() >> wide
    assert doubled.typed().cod == (Thing, Thing)  # not a single-wire test
    assert web.repeat().typed().dom == (Thing, )  # a bubble has no data


def test_parallel(kennel):
    web = Query.from_property(kennel.owns)
    knows = Query.from_property(kennel.knows)
    assert parallel(web, web) == (web, web)
    left, right = parallel(web, knows)
    assert left.dom == right.dom == (Thing, )
    with raises(AxiomError):
        parallel(web, Query.id((), kennel.world))


@needs_java
def test_validate(kennel):
    with Query.no_reasoning:
        free = coercion(kennel.Dog, kennel.Animal)
        crooked = Query.from_property(kennel.owns)\
            >> Query.from_property(kennel.owns)
    assert free.validate() == free and free.coercions[0].entailed
    with raises(AxiomError):
        crooked.validate()  # a dog is not a person


@needs_java
def test_coercion_carries_its_proof(kennel):
    assert coercion(kennel.Dog, kennel.Animal).coercions[0].entailed
    assert not coercion(kennel.Person, kennel.Dog).coercions[0].entailed


@needs_java
def test_deduced(kennel):
    quiet, = deduced([Not(kennel.Person)], kennel.world)
    assert quiet == ()  # nothing is provably not a person yet
    with kennel:
        AllDisjoint([kennel.Animal, kennel.Person])
    loud, bounded = deduced(
        [Not(kennel.Person), kennel.owns.max(1, kennel.Dog)], kennel.world)
    assert {one.name for one in loud} == {"fido", "rex"}
    assert {one.name for one in bounded} == {"fido", "rex"}  # dogs own not
    scratch = kennel.world.get_ontology(SCRATCH)
    assert not list(scratch.classes())  # the scratch classes are destroyed
    assert instances(Not(kennel.Person), kennel.world) == loud


@needs_java
def test_subsumes(kennel):
    owner = kennel.Person & kennel.owns.some(kennel.Dog)
    assert subsumes(owner, kennel.Person, kennel.world)
    assert not subsumes(kennel.Person, owner, kennel.world)
    assert subsumes(kennel.Dog, kennel.Animal, kennel.world)
    assert subsumes(kennel.Dog, Thing, kennel.world)
    scratch = kennel.world.get_ontology(SCRATCH)
    assert not list(scratch.classes())


@needs_java
def test_satisfying_is_deductive(kennel):
    world = kennel.world
    assert satisfying(kennel.Person, world) == {kennel.ada, kennel.bob}
    assert satisfying(Thing, world) == set(instances(Thing, world))
    assert satisfying(kennel.owns.some(kennel.Dog), world)\
        == {kennel.ada, kennel.bob}
    assert satisfying(kennel.owns.only(kennel.Dog), world)\
        == set(instances(Thing, world))  # entailed by the declared range
    with kennel:
        AllDisjoint([kennel.Animal, kennel.Person])
    assert satisfying(kennel.owns.max(1, kennel.Dog), world)\
        == {kennel.fido, kennel.rex}  # only the dogs provably own so few


@needs_java
def test_extension_of_a_construct(kennel):
    dog_owners = extension(kennel.owns.some(kennel.Dog))
    assert dog_owners <= extension(kennel.Person)
    assert dog_owners.name == "∃owns.Dog"
    assert extension(Thing, kennel.world)\
        == Relation.id(1, kennel.world)


@needs_java
def test_query_from_class_of_a_construct(kennel):
    owner = kennel.Person & kennel.owns.some(kennel.Dog)
    typed = Query.from_class(owner)
    assert typed == Query.id((owner, ))
    anatomy = Query.from_class(owner, dom=Thing)
    assert anatomy.inside == typed.inside
    assert len(anatomy.to_diagram().boxes) > 0


def test_query_from_individual(kennel):
    rex = Query.from_individual(kennel.rex)
    assert rex.cod == (kennel.Dog, )  # the first named direct class by IRI
    assert rex >> Query.id((kennel.Dog, )) == rex
    with kennel:
        anonymous = Thing()
    assert Query.from_individual(anonymous).cod == (Thing, )
    assert individual_class(anonymous) is Thing


def test_axiom(kennel):
    web = Relation.from_property(kennel.owns)
    single = Axiom(web >> web.dagger(), Relation.id(1, kennel.world))
    assert not single  # ada and bob share rex: an entailed counterexample
    assert str(Axiom(web, web, symbol="=")).count("=") == 1
    assert "<=" in str(single)


def test_axiom_draw(kennel, tmp_path):
    axioms(kennel.knows)[0].draw(path=str(tmp_path / "axiom.png"))
    extension(kennel.Dog).draw(path=str(tmp_path / "class.png"))
    Query.from_property(kennel.owns).draw(path=str(tmp_path / "query.png"))


def test_class_axioms(kennel):
    with kennel:
        class Pet(Thing): pass
        class Barker(Thing):
            equivalent_to = [kennel.Dog]
        kennel.Dog.is_a.append(Pet)
        kennel.Dog.is_a.append(kennel.named.some(str))  # not compiled
    book = class_axioms(kennel.Dog)
    sources = [axiom.source[1] for axiom in book]
    assert Pet in sources and kennel.Animal in sources
    assert not any(  # the datatype restriction is skipped
        "named" in str(source) for source in sources)
    assert all(book)  # named parents hold by search
    assert all(class_axioms(Barker))  # so does an equivalence


@needs_java
def test_class_axioms_of_a_construct_parent(kennel):
    with kennel:
        kennel.Dog.is_a.append(kennel.knows.some(Thing))
    assert all(class_axioms(kennel.Dog))  # the schema entails itself:
    # asserting the axiom is what makes every dog provably know someone


@needs_java
def test_candidate_axiom_refuted(kennel):
    candidate = Axiom(extension(kennel.Person),
                      extension(kennel.knows.some(Thing)))
    assert not candidate  # bob is an entailed counterexample: a person
    assert ((kennel.bob, ), (kennel.bob, ))\
        in set(candidate.terms[0].inside) - set(candidate.terms[1].inside)


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
    assert not reflexivity  # nothing is provably sameAs itself


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
    domain, range_ = property_axioms(kennel.knows)[-2:]
    assert domain and range_


def test_relations_of_an_inverse(kennel):
    assert relations(Inverse(kennel.owns)) == {
        kennel.rex: {kennel.ada, kennel.bob}, kennel.fido: {kennel.bob}}


@needs_java
def test_axioms(kennel):
    with kennel:
        AllDisjoint([kennel.Dog, kennel.Person])
        AllDisjoint([kennel.Animal, kennel.owns.some(kennel.Dog)])
        kennel.Person.is_a.append(kennel.knows.only(kennel.Person))
        kennel.Dog.is_a.append(kennel.named.some(str))  # not compiled
    book = axioms(kennel)
    assert any("=" in axiom.symbols for axiom in book)  # the disjointness
    assert all(book)  # a consistent schema entails itself
    assert [str(one) for one in axioms(kennel.world)]\
        == [str(one) for one in book]  # scratch and inferences skipped
    assert [str(one) for one in axioms(kennel.Dog)]\
        == [str(one) for one in class_axioms(kennel.Dog)]
    assert len(axioms(kennel.owns)) == len(property_axioms(kennel.owns))
    with raises(TypeError):
        axioms("not an entity")


def test_class_axioms_skip_a_scratch_parent(kennel):
    scratch = kennel.world.get_ontology(SCRATCH)
    with scratch:
        class Leaked(Thing): pass
    kennel.Dog.is_a.append(Leaked)  # a reasoner write-back would do this
    sources = [axiom.source[1] for axiom in class_axioms(kennel.Dog)]
    assert Leaked not in sources and kennel.Animal in sources


def test_compilable(kennel):
    assert compilable(kennel.owns.some(kennel.Dog))
    assert not compilable(kennel.named.some(str))


def test_label_ob_box_point(kennel):
    rex, owns, dog = kennel.rex, kennel.owns, kennel.Dog
    assert label(kennel.Person & Not(owns.some(dog) | owns.value(rex)))\
        == "Person ⊓ ¬(∃owns.Dog ⊔ ∃owns.{rex})"
    assert label(Inverse(owns).min(2, kennel.Person | dog))\
        == "≥2 owns˘.(Person ⊔ Dog)"
    assert label(owns.exactly(1, dog)) == "=1 owns.Dog"
    assert label(owns.only(dog)) == "∀owns.Dog"
    assert label(kennel.knows.has_self()) == "∃knows.Self"
    assert label(OneOf([rex])) == "{rex}"
    assert label(kennel.named.value("Rex")) == "∃named.{Rex}"
    assert label(str) == "str" and label(42) == "42"
    assert ob() == Ty("Thing") and ob().inside[0].entity is Thing
    assert ob((kennel.Person, owns.some(dog)))\
        == Ty("Person", "∃owns.Dog")
    assert box(owns) == Box(
        "owns", Ty("Person"), Ty("Dog"), data=owns)
    assert box(Inverse(owns)) == box(owns).dagger()
    assert schema(Inverse(owns)) == (dog, kennel.Person)
    assert point(rex).cod == Ty("Dog") and point(rex).data is rex


def test_to_diagram_constructs(kennel):
    dog, person, thing = kennel.Dog, kennel.Person, Ty("Thing")
    assert to_diagram(kennel.rex) == point(kennel.rex)
    assert to_diagram(kennel.owns) == box(kennel.owns)
    assert to_diagram(dog) == Id(Ty(Wire(dog)))
    assert to_diagram(dog, dom=Thing)\
        == Box("Dog", thing, thing, data=dog)
    assert to_diagram(dog & person, dom=Thing)\
        == to_diagram(dog, Thing) >> to_diagram(person, Thing)
    union = to_diagram(dog | person, dom=Thing)
    assert isinstance(union, Bubble) and len(union.args) == 1
    negated, = union.args  # the De Morgan dual: one bubble per class
    assert sum(isinstance(one, Bubble) for one in negated.boxes) == 2
    assert isinstance(to_diagram(Not(dog), dom=Thing), Bubble)
    assert to_diagram(OneOf([kennel.rex]), dom=Thing).name == "{rex}"
    with raises(NotImplementedError):
        to_diagram(kennel.named.some(str), dom=Thing)
    with raises(NotImplementedError):
        to_diagram(kennel.named.value(True), dom=Thing)  # a literal
    with raises(NotImplementedError):
        to_diagram(42, dom=Thing)


def test_restriction_diagrams(kennel):
    owns, dog = kennel.owns, kennel.Dog
    for construct in (owns.some(dog), owns.only(dog),
                      owns.value(kennel.rex), owns.min(2, dog),
                      owns.min(3, dog), owns.max(1, dog),
                      owns.exactly(1, dog), kennel.knows.has_self(),
                      owns.min(0, dog)):
        diagram = to_diagram(construct, dom=kennel.Person)
        typ = Ty("Person")
        assert (diagram.dom, diagram.cod) == (typ, typ)


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
    assert {one.name for one in copy.individuals()}\
        == {one.name for one in kennel.individuals()}


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
    assert [one.name for one in chain.terms[0].to_diagram().boxes]\
        == ["hasDirectOwnership", "hasOwningEntity"]
    assert chain  # trivially, over an empty extension


def test_market_control_chain(market):
    world, demo, company, person, controls = market
    web = Relation.from_property(controls, world)
    alice = Relation.from_individual(demo.alice)
    shell = Relation.from_individual(demo.shell_co)
    assert not alice >> web >> shell.dagger()  # not directly
    assert alice >> web.repeat() >> shell.dagger()  # but ultimately


def test_market_typed_chain(market):
    world, demo, company, person, controls = market
    with Query.no_reasoning:
        chain = (Query.from_individual(demo.alice, person)
                 >> Query.from_property(controls, person, company)
                 >> Query.from_property(controls, company, company)
                 >> Query.from_property(controls, company, company)
                 >> Query.from_individual(demo.shell_co, company).dagger())
    assert chain and not chain.coercions  # the predicates all meet
    boxes = chain.to_diagram().boxes
    assert [one.name for one in boxes[1:-1]] == 3 * ["controls"]


@needs_java
def test_market_validates_a_typed_chain(market):
    world, demo, company, person, controls = market
    with Query.no_reasoning:
        sloppy = (Query.from_property(controls, person, company)
                  >> Query.from_property(controls, person, company))
    one, = sloppy.coercions
    assert (one.source, one.target) == (company, person)
    with raises(AxiomError):
        sloppy.validate()  # a company is not a natural person


def test_unresolved_restriction_is_outside_the_dictionary(market):
    world = market[0]
    stray = next(
        parent for onto in list(world.ontologies.values())
        for cls in onto.classes() for parent in cls.is_a
        if isinstance(parent, Restriction)
        and isinstance(parent.property, str))  # points into a stub
    with raises(NotImplementedError):
        to_diagram(stray, dom=Thing)


@needs_java
def test_fibo_axioms_hold():
    world, demo, company, person, controls = market_world()
    onto = world.get_ontology(
        FIBO + "BE/OwnershipAndControl/ControlParties/")
    assert all(axioms(onto))  # no entailed counterexample


def test_fixtures_resolve_the_currency_module():
    world = World()
    load(FIBO + "FND/OwnershipAndControl/Ownership/", world, path=FIXTURES)
    for iri in ("*CurrencyAmount/MonetaryAmount", "*CurrencyAmount/Currency",
                "*Ownership/Portfolio", "*Collections/comprises"):
        assert world.search_one(iri=iri) is not None


@needs_java
def test_the_whole_rule_book():
    world = market_world()[0]
    book = axioms(world)  # every loaded module, one batched deduction
    assert len(book) > 500 and all(book)


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
    assert not Relation(  # not asserted
        [2 * ((one, ), ) for one in DogOwner.instances()],
        1, 1, kennel.world)
    reason(kennel.world)
    assert extension(DogOwner) == extension(kennel.Person)


@needs_java
def test_consistent(kennel):
    assert consistent(kennel.world)
    with kennel:
        AllDisjoint([kennel.Dog, kennel.Person])
        kennel.rex.is_a.append(kennel.Person)
    assert not consistent(kennel.world)
