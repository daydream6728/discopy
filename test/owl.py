# -*- coding: utf-8 -*-

from shutil import which
from types import SimpleNamespace

from pytest import fixture, importorskip, raises, skip

importorskip("owlapy")

if which("java") is None:
    skip("owlapy's owlapi bridge needs Java.", allow_module_level=True)

from owlapy.class_expression import (  # noqa: E402
    OWLClass, OWLDataSomeValuesFrom, OWLObjectAllValuesFrom,
    OWLObjectComplementOf, OWLObjectExactCardinality, OWLObjectHasSelf,
    OWLObjectHasValue, OWLObjectIntersectionOf, OWLObjectMaxCardinality,
    OWLObjectMinCardinality, OWLObjectOneOf, OWLObjectSomeValuesFrom,
    OWLObjectUnionOf)
from owlapy.iri import IRI  # noqa: E402
from owlapy.owl_axiom import (  # noqa: E402
    OWLAsymmetricObjectPropertyAxiom, OWLClassAssertionAxiom,
    OWLDeclarationAxiom, OWLDisjointClassesAxiom, OWLEquivalentClassesAxiom,
    OWLEquivalentObjectPropertiesAxiom, OWLFunctionalObjectPropertyAxiom,
    OWLInverseFunctionalObjectPropertyAxiom,
    OWLInverseObjectPropertiesAxiom, OWLIrreflexiveObjectPropertyAxiom,
    OWLReflexiveObjectPropertyAxiom, OWLSubClassOfAxiom,
    OWLSubObjectPropertyOfAxiom, OWLSubPropertyChainAxiom,
    OWLSymmetricObjectPropertyAxiom, OWLTransitiveObjectPropertyAxiom)
from owlapy.owl_datatype import OWLDatatype  # noqa: E402
from owlapy.owl_property import (  # noqa: E402
    OWLDataProperty, OWLObjectInverseOf)
from owlapy.vocab import XSDVocabulary  # noqa: E402

from discopy.owl import (  # noqa: E402
    Axiom, Box, Bubble, Coercion, Id, Nothing, Query, Relation, Thing, Ty,
    Wire, World, axioms, boundary, box, carrier, class_axioms, coercion,
    combine, compilable, consistent, declared, deduced, extension,
    individual_class, instances, label, load, name_of, ob, parallel, point,
    property_axioms, reason, relations, satisfying, schema, subsumes,
    to_diagram)
from discopy.utils import AxiomError  # noqa: E402


@fixture
def kennel():
    world = World("http://discopy.org/kennel.owl#")
    animal, dog, person = map(world.owl_class, ("Animal", "Dog", "Person"))
    world.add(OWLSubClassOfAxiom(dog, animal))
    owns = world.owl_property("owns", person, dog)
    knows = world.owl_property("knows", person, person)
    named = OWLDataProperty(IRI.create(world.iri + "named"))
    world.add(OWLDeclarationAxiom(named))
    rex, fido = (world.individual(name, dog) for name in ("rex", "fido"))
    ada, bob = (world.individual(name, person) for name in ("ada", "bob"))
    world.relate(ada, owns, rex)
    world.relate(bob, owns, rex, fido)
    world.relate(ada, knows, bob)
    return SimpleNamespace(
        world=world, Animal=animal, Dog=dog, Person=person,
        owns=owns, knows=knows, named=named,
        rex=rex, fido=fido, ada=ada, bob=bob)


def string_of_dogs(kennel):
    """ A datatype restriction, which the dictionary cannot draw. """
    return OWLDataSomeValuesFrom(
        kennel.named, OWLDatatype(XSDVocabulary.STRING.iri))


def test_world_enumerates_its_signature(kennel):
    world = kennel.world
    assert [name_of(one) for one in world.classes()]\
        == ["Animal", "Dog", "Person"]
    assert [name_of(one) for one in world.object_properties()]\
        == ["knows", "owns"]
    assert [name_of(one) for one in world.data_properties()] == ["named"]
    assert len(world.individuals()) == 4
    assert world.find("Dog") == kennel.Dog
    assert world.find("owns") == kennel.owns
    assert world.find("named") == kennel.named
    assert world.find("rex") == kennel.rex
    assert world.find("Unicorn") is None
    assert any(isinstance(one, OWLSubClassOfAxiom) for one in world.tbox())
    assert any(isinstance(one, OWLClassAssertionAxiom)
               for one in world.abox())


def test_declared(kennel):
    assert declared(kennel.Dog, OWLClass)
    assert not declared(Thing, OWLClass)  # owl:Thing says nothing
    assert not declared(kennel.rex, OWLClass)


def test_instances_and_carrier(kennel):
    world = kennel.world
    assert [name_of(one) for one in instances(kennel.Dog, world)]\
        == ["fido", "rex"]
    everyone = instances(Thing, world)
    assert len(everyone) == 4
    assert carrier(2, world) == tuple(
        (x, y) for x in everyone for y in everyone)
    assert carrier(0, world) == ((), )


def test_instances_are_memoised(kennel):
    world = kennel.world
    quiet = instances(kennel.Person, world)
    world.ontology.add_axiom(  # behind the world's back
        OWLClassAssertionAxiom(kennel.rex, kennel.Person))
    assert instances(kennel.Person, world) == quiet  # the stale memo
    reason(world)
    assert kennel.rex in instances(kennel.Person, world)


def test_init_checks_arity(kennel):
    with raises(AxiomError):
        Relation([((kennel.rex, ), ())], 1, 1, kennel.world)


def test_init_is_deterministic(kennel):
    pairs = [((kennel.ada, ), ()), ((kennel.bob, ), ())]
    assert Relation(pairs, 1, 0, kennel.world)\
        == Relation(pairs[::-1], 1, 0, kennel.world)


def test_str_and_bool(kennel):
    web = Relation.from_property(kennel.owns, kennel.world)
    assert str(web) == "owns : Thing -> Thing"
    assert str(Relation.id(0, kennel.world)) == "Relation : () -> ()"
    assert str(Relation.id(2, kennel.world))\
        == "Relation : Thing ** 2 -> Thing ** 2"
    assert Relation.id(0, kennel.world)
    assert not Relation.bottom(0, 0, kennel.world)


def test_id_then(kennel):
    web = Relation.from_property(kennel.owns, kennel.world)
    identity = Relation.id(1, kennel.world)
    assert identity >> web == web == web >> identity
    knows = Relation.from_property(kennel.knows, kennel.world)
    assert (knows >> web).inside == (((kennel.ada, ), (kennel.fido, )),
                                     ((kennel.ada, ), (kennel.rex, )))
    with raises(AxiomError):
        web >> Relation.id(2, kennel.world)
    with raises(AxiomError):
        web >> Relation.id(1, World())  # a different world


def test_tensor_and_dagger(kennel):
    web = Relation.from_property(kennel.owns, kennel.world)
    knows = Relation.from_property(kennel.knows, kennel.world)
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
    web = Relation.from_property(kennel.owns, kennel.world)
    knows = Relation.from_property(kennel.knows, kennel.world)
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
    r = Relation.from_property(kennel.knows, kennel.world)
    s = Relation.from_property(kennel.owns, kennel.world)
    t = r >> s >> s.dagger() >> s
    assert (r >> s).meet(t) <= r >> s.meet(r.dagger() >> t)


def test_domain_and_repeat(kennel):
    web = Relation.from_property(kennel.owns, kennel.world)
    assert web.domain() <= Relation.id(1, kennel.world)
    assert web.codomain() == web.dagger().domain()
    knows = Relation.from_property(kennel.knows, kennel.world)
    closure = knows.repeat()
    assert Relation.id(1, kennel.world) <= closure
    assert closure >> closure == closure
    with raises(AxiomError):
        Relation.from_individual(kennel.rex, kennel.world).repeat()


def test_sparql(kennel):
    web = Relation.sparql(
        "SELECT ?x ?y WHERE { ?x <http://discopy.org/kennel.owl#owns> ?y . }",
        1, 1, kennel.world)
    assert web == Relation.from_property(kennel.owns, kennel.world)


def test_pictures(kennel):
    web = Relation.from_property(kennel.owns, kennel.world)
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
    web = Relation.from_property(kennel.owns, kennel.world)
    with raises(AxiomError):
        Query(web, (kennel.Person, ), (kennel.Dog, kennel.Dog))
    typed = Query(web, (kennel.Person, ), (kennel.Dog, ))
    assert typed.inside == web  # the schema boundary keeps every pair
    assert typed.relation == typed.inside and typed.world is kennel.world
    forgetful = Query(Relation(web.inside, 1, 1, kennel.world),
                      (kennel.Person, ), (kennel.Dog, ))
    assert forgetful.to_diagram().name == "?"  # no history to draw


def test_query_normalises(kennel):
    web = Relation.from_property(kennel.owns, kennel.world)
    at_dogs = Query(web, (kennel.Dog, ), (kennel.Dog, ))
    assert not at_dogs.inside  # no dog owns anything
    assert boundary((kennel.Dog, ), kennel.world)\
        == extension(kennel.Dog, kennel.world).meet(
            extension(kennel.Dog, kennel.world))


def test_query_id_and_conversions(kennel):
    dogs = Query.id((kennel.Dog, ), kennel.world)
    assert dogs.inside == extension(kennel.Dog, kennel.world)
    assert dogs.at_thing() == dogs.inside.split((Thing, ), (Thing, ))
    assert Query.id((), kennel.world).inside == Relation.id(0, kennel.world)
    web = Query.from_property(kennel.owns, kennel.world)
    assert Query.id(web.dom, kennel.world) >> web == web
    assert web == web >> Query.id(web.cod, kennel.world)


def test_query_str_and_bool(kennel):
    web = Query.from_property(kennel.owns, kennel.world)
    assert str(web) == "owns : ('Person',) -> ('Dog',)"
    assert str(Query.id((), kennel.world)) == "Query : () -> ()"
    assert web and not Query.bottom(web.dom, web.cod, kennel.world)


def test_query_algebra(kennel):
    web = Query.from_property(kennel.owns, kennel.world)
    assert web.dagger().dagger() == web
    assert (web @ web).dom == 2 * web.dom
    assert web.meet(web) == web == web.join(
        Query.bottom(web.dom, web.cod, kennel.world))
    assert Query.bottom(web.dom, web.cod, kennel.world) <= web
    assert web.domain() <= Query.id(web.dom, kennel.world)
    assert web.codomain() == web.dagger().domain()
    with raises(AxiomError):
        web.meet(web.dagger())
    carl = kennel.world.individual("carl", kennel.Person)
    kennel.world.relate(kennel.bob, kennel.knows, carl)
    knows = Query.from_property(kennel.knows, kennel.world)
    closure = knows.repeat()
    assert Query.id(knows.dom, kennel.world) <= closure
    assert closure == closure >> closure
    with raises(AxiomError):
        web.repeat()


def test_query_structure(kennel):
    world = kennel.world
    person, dog = (kennel.Person, ), (kennel.Dog, )
    assert Query.spiders(1, 1, person, world) == Query.id(person, world)
    copy = Query.copy(person, world=world)
    assert copy >> copy.dagger() == Query.id(person, world)
    swap = Query.swap(person, dog, world)
    assert swap >> swap.dagger() == Query.id(person + dog, world)
    assert Query.permutation([1, 0], [person, dog], world) == swap
    cup, cap = Query.cups(dog, dog, world), Query.caps(dog, dog, world)
    assert cap @ Query.id(dog, world) >> Query.id(dog, world) @ cup\
        == Query.id(dog, world)
    with raises(AxiomError):
        Query.cups(dog, person, world)


def test_query_composition_strict(kennel):
    web = Query.from_property(kennel.owns, kennel.world)
    knows = Query.from_property(kennel.knows, kennel.world)
    assert (knows >> web).dom == knows.dom and (knows >> web).cod == web.cod
    with raises(AxiomError):
        web >> Query.id((), kennel.world)  # an arity mismatch still raises


def test_query_composition_coerces(kennel):
    web = Query.from_property(kennel.owns, kennel.world)
    with Query.no_reasoning:
        crooked = web >> web  # a dog is not a person
        one, = crooked.coercions
    assert isinstance(one, Coercion) and one.entailed is None
    assert (one.source, one.target) == (kennel.Dog, kennel.Person)
    assert not crooked  # no owned dog is an owner
    assert Query.reasoning  # the switch is restored


def test_coercion(kennel):
    with Query.no_reasoning:
        assert coercion(kennel.Dog, kennel.Dog, kennel.world)\
            == Query.id((kennel.Dog, ), kennel.world)
        free = coercion(kennel.Dog, kennel.Animal, kennel.world)
    assert free.inside == extension(kennel.Dog, kennel.world)  # dogs are


def test_subsumes_below_a_construct(kennel):
    world = kennel.world
    owns_a_dog = OWLObjectSomeValuesFrom(kennel.owns, kennel.Dog)
    world.add(OWLSubClassOfAxiom(kennel.Person, owns_a_dog),
              OWLDisjointClassesAxiom([kennel.Dog, kennel.Person]))
    assert subsumes(kennel.Person, owns_a_dog, world)
    assert subsumes(OWLObjectIntersectionOf(
        (kennel.Dog, kennel.Person)), Nothing, world)
    assert not subsumes(kennel.Dog, owns_a_dog, world)


def test_karoubi_splitting(kennel):
    with Query.no_reasoning:
        include = coercion(kennel.Dog, Thing, kennel.world)
        project = coercion(Thing, kennel.Dog, kennel.world)
    assert include >> project == Query.id((kennel.Dog, ), kennel.world)
    assert project >> include\
        == extension(kennel.Dog, kennel.world).split((Thing, ), (Thing, ))


def test_typed(kennel):
    web = Relation.from_property(kennel.owns, kennel.world)
    person, dog = (extension(one, kennel.world)
                   for one in (kennel.Person, kennel.Dog))
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
    web = Relation.from_property(kennel.owns, kennel.world)
    doubled = web @ web
    doubled.diagram = doubled.to_diagram() >> wide
    assert doubled.typed().cod == (Thing, Thing)  # not a single-wire test
    assert web.repeat().typed().dom == (Thing, )  # a bubble has no data


def test_parallel(kennel):
    web = Query.from_property(kennel.owns, kennel.world)
    knows = Query.from_property(kennel.knows, kennel.world)
    assert parallel(web, web) == (web, web)
    left, right = parallel(web, knows)
    assert left.dom == right.dom == (Thing, )
    with raises(AxiomError):
        parallel(web, Query.id((), kennel.world))


def test_validate(kennel):
    with Query.no_reasoning:
        free = coercion(kennel.Dog, kennel.Animal, kennel.world)
        crooked = Query.from_property(kennel.owns, kennel.world)\
            >> Query.from_property(kennel.owns, kennel.world)
    assert free.validate() == free and free.coercions[0].entailed
    with raises(AxiomError):
        crooked.validate()  # a dog is not a person


def test_coercion_carries_its_proof(kennel):
    assert coercion(
        kennel.Dog, kennel.Animal, kennel.world).coercions[0].entailed
    assert not coercion(
        kennel.Person, kennel.Dog, kennel.world).coercions[0].entailed


def test_deduced(kennel):
    world = kennel.world
    quiet, = deduced([OWLObjectComplementOf(kennel.Person)], world)
    assert quiet == ()  # nothing is provably not a person yet
    world.add(OWLDisjointClassesAxiom([kennel.Animal, kennel.Person]))
    loud, bounded = deduced(
        [OWLObjectComplementOf(kennel.Person),
         OWLObjectMaxCardinality(1, kennel.owns, kennel.Dog)], world)
    assert {name_of(one) for one in loud} == {"fido", "rex"}
    assert {name_of(one) for one in bounded} == {"fido", "rex"}  # dogs don't
    assert instances(OWLObjectComplementOf(kennel.Person), world) == loud


def test_subsumes(kennel):
    world = kennel.world
    owner = OWLObjectIntersectionOf(
        (kennel.Person, OWLObjectSomeValuesFrom(kennel.owns, kennel.Dog)))
    assert subsumes(owner, kennel.Person, world)
    assert not subsumes(kennel.Person, owner, world)
    assert subsumes(kennel.Dog, kennel.Animal, world)
    assert subsumes(kennel.Dog, Thing, world)


def test_satisfying_is_deductive(kennel):
    world = kennel.world
    assert satisfying(kennel.Person, world) == {kennel.ada, kennel.bob}
    assert satisfying(Thing, world) == set(instances(Thing, world))
    assert satisfying(
        OWLObjectSomeValuesFrom(kennel.owns, kennel.Dog), world)\
        == {kennel.ada, kennel.bob}
    assert satisfying(
        OWLObjectAllValuesFrom(kennel.owns, kennel.Dog), world)\
        == set(instances(Thing, world))  # entailed by the declared range
    world.add(OWLDisjointClassesAxiom([kennel.Animal, kennel.Person]))
    assert satisfying(
        OWLObjectMaxCardinality(1, kennel.owns, kennel.Dog), world)\
        == {kennel.fido, kennel.rex}  # only the dogs provably own so few


def test_extension_of_a_construct(kennel):
    dog_owners = extension(
        OWLObjectSomeValuesFrom(kennel.owns, kennel.Dog), kennel.world)
    assert dog_owners <= extension(kennel.Person, kennel.world)
    assert dog_owners.name == "∃owns.Dog"
    assert extension(Thing, kennel.world) == Relation.id(1, kennel.world)


def test_query_from_class_of_a_construct(kennel):
    owner = OWLObjectIntersectionOf(
        (kennel.Person, OWLObjectSomeValuesFrom(kennel.owns, kennel.Dog)))
    typed = Query.from_class(owner, kennel.world)
    assert typed == Query.id((owner, ), kennel.world)
    anatomy = Query.from_class(owner, kennel.world, dom=Thing)
    assert anatomy.inside == typed.inside
    assert len(anatomy.to_diagram().boxes) > 0


def test_query_from_individual(kennel):
    rex = Query.from_individual(kennel.rex, kennel.world)
    assert rex.cod == (kennel.Dog, )  # the first named class by IRI
    assert rex >> Query.id((kennel.Dog, ), kennel.world) == rex
    stray = kennel.world.individual("stray")  # no class assertion
    assert Query.from_individual(stray, kennel.world).cod == (Thing, )
    assert individual_class(stray, kennel.world) is Thing


def test_axiom(kennel):
    web = Relation.from_property(kennel.owns, kennel.world)
    single = Axiom(web >> web.dagger(), Relation.id(1, kennel.world))
    assert not single  # ada and bob share rex: an entailed counterexample
    assert str(Axiom(web, web, symbol="=")).count("=") == 1
    assert "<=" in str(single)


def test_axiom_draw(kennel, tmp_path):
    axioms(kennel.knows, kennel.world)[0].draw(
        path=str(tmp_path / "axiom.png"))
    extension(kennel.Dog, kennel.world).draw(
        path=str(tmp_path / "class.png"))
    Query.from_property(kennel.owns, kennel.world).draw(
        path=str(tmp_path / "query.png"))


def test_class_axioms(kennel):
    world = kennel.world
    pet = world.owl_class("Pet")
    parent = OWLSubClassOfAxiom(kennel.Dog, pet)
    world.add(parent)
    assert all(class_axioms(parent, world))  # asserted, hence entailed
    equivalence = OWLEquivalentClassesAxiom(
        [world.owl_class("Barker"), kennel.Dog])
    world.add(equivalence)
    assert all(class_axioms(equivalence, world))
    assert class_axioms(  # the datatype restriction is outside
        OWLSubClassOfAxiom(kennel.Dog, string_of_dogs(kennel)), world) == []
    assert class_axioms(  # so is a construct as the subject
        OWLSubClassOfAxiom(
            OWLObjectComplementOf(kennel.Dog), pet), world) == []
    assert class_axioms(  # and owl:Thing as the parent says nothing
        OWLSubClassOfAxiom(kennel.Dog, Thing), world) == []


def test_class_axioms_of_a_construct_parent(kennel):
    axiom = OWLSubClassOfAxiom(
        kennel.Dog, OWLObjectSomeValuesFrom(kennel.knows, Thing))
    kennel.world.add(axiom)
    assert all(class_axioms(axiom, kennel.world))  # the schema entails
    # itself: asserting it is what makes every dog provably know someone


def test_candidate_axiom_refuted(kennel):
    candidate = Axiom(
        extension(kennel.Person, kennel.world),
        extension(OWLObjectSomeValuesFrom(
            kennel.knows, Thing), kennel.world))
    assert not candidate  # bob is an entailed counterexample: a person
    assert ((kennel.bob, ), (kennel.bob, ))\
        in set(candidate.terms[0].inside) - set(candidate.terms[1].inside)


def test_property_axioms_characteristics(kennel):
    world = kennel.world
    characteristics = [
        kind(world.owl_property(name, kennel.Dog, kennel.Dog))
        for name, kind in (
            ("descends", OWLTransitiveObjectPropertyAxiom),
            ("near", OWLSymmetricObjectPropertyAxiom),
            ("above", OWLAsymmetricObjectPropertyAxiom),
            ("sameAs", OWLReflexiveObjectPropertyAxiom),
            ("other", OWLIrreflexiveObjectPropertyAxiom),
            ("chip", OWLFunctionalObjectPropertyAxiom),
            ("tag", OWLInverseFunctionalObjectPropertyAxiom))]
    world.add(*characteristics)
    for axiom in characteristics:
        one, = property_axioms(axiom, world)
        assert one  # the reasoner derives what each characteristic entails


def test_property_axioms_structure(kennel):
    world = kennel.world
    has = world.owl_property("has", kennel.Person, kennel.Dog)
    owned_by = world.owl_property("ownedBy", kennel.Dog, kennel.Person)
    walks_with = world.owl_property("walksWith", kennel.Person, kennel.Dog)
    structure = [
        OWLSubObjectPropertyOfAxiom(kennel.owns, has),
        OWLEquivalentObjectPropertiesAxiom([kennel.owns, has]),
        OWLInverseObjectPropertiesAxiom(owned_by, kennel.owns),
        OWLSubPropertyChainAxiom([kennel.knows, kennel.owns], walks_with)]
    world.add(*structure)
    for axiom in structure:  # the reasoner follows each declaration
        assert all(property_axioms(axiom, world))
    chain, = property_axioms(structure[-1], world)
    assert [one.name for one in chain.terms[0].to_diagram().boxes]\
        == ["knows", "owns"]  # in this order: ada walks with bob's dogs
    domain, range_ = (
        property_axioms(axiom, world)[0] for axiom in world.tbox()
        if getattr(axiom, "get_property", lambda: None)() == kennel.knows)
    assert domain and range_


def test_axioms_outside_the_dictionary_are_skipped(kennel):
    world, dog = kennel.world, kennel.Dog
    inverse = OWLObjectInverseOf(kennel.owns)
    assert class_axioms(OWLEquivalentClassesAxiom(
        [dog, string_of_dogs(kennel)]), world) == []
    assert class_axioms(OWLDisjointClassesAxiom(
        [dog, string_of_dogs(kennel)]), world) == []
    assert property_axioms(OWLSubObjectPropertyOfAxiom(
        inverse, kennel.owns), world) == []
    assert property_axioms(OWLEquivalentObjectPropertiesAxiom(
        [inverse, kennel.owns]), world) == []
    assert property_axioms(OWLInverseObjectPropertiesAxiom(
        inverse, kennel.owns), world) == []
    assert property_axioms(OWLSubPropertyChainAxiom(
        [inverse], kennel.owns), world) == []


def test_relations_of_an_inverse(kennel):
    assert relations(OWLObjectInverseOf(kennel.owns), kennel.world) == {
        kennel.rex: {kennel.ada, kennel.bob}, kennel.fido: {kennel.bob}}


def test_axioms(kennel):
    world = kennel.world
    world.add(
        OWLDisjointClassesAxiom([kennel.Dog, kennel.Person]),
        OWLDisjointClassesAxiom([
            kennel.Animal,
            OWLObjectSomeValuesFrom(kennel.owns, kennel.Dog)]),
        OWLSubClassOfAxiom(kennel.Person, OWLObjectAllValuesFrom(
            kennel.knows, kennel.Person)),
        OWLSubClassOfAxiom(kennel.Dog, string_of_dogs(kennel)))
    book = axioms(world)
    assert any("=" in axiom.symbols for axiom in book)  # the disjointness
    assert all(book)  # a consistent schema entails itself
    for axiom in axioms(kennel.Dog, world):
        assert kennel.Dog in axiom.source.signature()
    assert len(axioms(kennel.owns, world)) >= 2  # its domain and range
    with raises(TypeError):
        axioms("not an entity", world)


def test_compilable(kennel):
    assert compilable(
        OWLObjectSomeValuesFrom(kennel.owns, kennel.Dog), kennel.world)
    assert not compilable(string_of_dogs(kennel), kennel.world)


def test_label_ob_box_point(kennel):
    world, rex = kennel.world, kennel.rex
    owns, dog, person = kennel.owns, kennel.Dog, kennel.Person
    assert label(OWLObjectIntersectionOf((person, OWLObjectComplementOf(
        OWLObjectUnionOf((OWLObjectSomeValuesFrom(owns, dog),
                          OWLObjectHasValue(owns, rex)))))))\
        == "Person ⊓ ¬(∃owns.Dog ⊔ ∃owns.{rex})"
    assert label(OWLObjectMinCardinality(
        2, OWLObjectInverseOf(owns), OWLObjectUnionOf((person, dog))))\
        == "≥2 owns˘.(Person ⊔ Dog)"
    assert label(OWLObjectExactCardinality(1, owns, dog)) == "=1 owns.Dog"
    assert label(OWLObjectAllValuesFrom(owns, dog)) == "∀owns.Dog"
    assert label(OWLObjectHasSelf(kennel.knows)) == "∃knows.Self"
    assert label(OWLObjectOneOf((rex, ))) == "{rex}"
    assert label(Nothing) == "Nothing"
    assert label(42) == "42"
    assert ob() == Ty("Thing") and ob().inside[0].entity is Thing
    assert ob((person, OWLObjectSomeValuesFrom(owns, dog)))\
        == Ty("Person", "∃owns.Dog")
    assert box(owns, world) == Box(
        "owns", Ty("Person"), Ty("Dog"), data=owns)
    assert box(OWLObjectInverseOf(owns), world) == box(owns, world).dagger()
    assert schema(OWLObjectInverseOf(owns), world) == (dog, person)
    assert point(rex, world).cod == Ty("Dog")
    assert point(rex, world).data is rex


def test_to_diagram_constructs(kennel):
    world, thing = kennel.world, Ty("Thing")
    dog, person = kennel.Dog, kennel.Person
    assert to_diagram(kennel.rex, world) == point(kennel.rex, world)
    assert to_diagram(kennel.owns, world) == box(kennel.owns, world)
    assert to_diagram(dog, world) == Id(Ty(Wire(dog)))
    assert to_diagram(dog, world, dom=Thing)\
        == Box("Dog", thing, thing, data=dog)
    assert to_diagram(
        OWLObjectIntersectionOf((dog, person)), world, dom=Thing)\
        == to_diagram(dog, world, Thing) >> to_diagram(person, world, Thing)
    union = to_diagram(OWLObjectUnionOf((dog, person)), world, dom=Thing)
    assert isinstance(union, Bubble) and len(union.args) == 1
    negated, = union.args  # the De Morgan dual: one bubble per class
    assert sum(isinstance(one, Bubble) for one in negated.boxes) == 2
    assert isinstance(
        to_diagram(OWLObjectComplementOf(dog), world, dom=Thing), Bubble)
    assert to_diagram(
        OWLObjectOneOf((kennel.rex, )), world, dom=Thing).name == "{rex}"
    with raises(NotImplementedError):
        to_diagram(string_of_dogs(kennel), world, dom=Thing)
    with raises(NotImplementedError):
        to_diagram(42, world, dom=Thing)


def test_restriction_diagrams(kennel):
    world, owns, dog = kennel.world, kennel.owns, kennel.Dog
    for construct in (
            OWLObjectSomeValuesFrom(owns, dog),
            OWLObjectAllValuesFrom(owns, dog),
            OWLObjectHasValue(owns, kennel.rex),
            OWLObjectMinCardinality(2, owns, dog),
            OWLObjectMinCardinality(3, owns, dog),
            OWLObjectMaxCardinality(1, owns, dog),
            OWLObjectExactCardinality(1, owns, dog),
            OWLObjectHasSelf(kennel.knows),
            OWLObjectMinCardinality(0, owns, dog)):
        diagram = to_diagram(construct, world, dom=kennel.Person)
        typ = Ty("Person")
        assert (diagram.dom, diagram.cod) == (typ, typ)


def test_load_rejects_a_missing_directory(tmp_path):
    with raises(FileNotFoundError):
        load("http://x/a/", path=str(tmp_path / "nowhere"))


def test_consistent(kennel):
    assert consistent(kennel.world)
    kennel.world.add(
        OWLDisjointClassesAxiom([kennel.Dog, kennel.Person]),
        OWLClassAssertionAxiom(kennel.rex, kennel.Person))
    assert not consistent(kennel.world)


FIBO = "https://spec.edmcouncil.org/fibo/ontology/"
FIXTURES = "test/fixtures/fibo"


def market_world():
    world = load(
        FIBO + "BE/OwnershipAndControl/CorporateControl/", path=FIXTURES)
    company = world.find("LegalPersons/BusinessEntity")
    person = world.find("LegallyCompetentNaturalPerson")
    controls = world.find("Relations/controls")
    alice = world.individual("alice", person)
    holdings, bank, shell = (
        world.individual(name, company)
        for name in ("acme_holdings", "acme_bank", "shell_co"))
    world.relate(alice, controls, holdings)
    world.relate(holdings, controls, bank)
    world.relate(bank, controls, shell)
    demo = SimpleNamespace(
        alice=alice, holdings=holdings, bank=bank, shell_co=shell)
    return world, demo, company, person, controls


@fixture(scope="module")
def market():
    return market_world()


def test_fibo_chain_axiom(market):
    world = market[0]
    owning = world.find("hasDirectOwningEntity")
    declaration, = [
        axiom for axiom in world.rbox()
        if isinstance(axiom, OWLSubPropertyChainAxiom)
        and axiom.get_super_property() == owning]
    chain, = property_axioms(declaration, world)
    assert [one.name for one in chain.terms[0].to_diagram().boxes]\
        == ["hasDirectOwnership", "hasOwningEntity"]
    assert chain  # trivially, over an empty extension


def test_market_control_chain(market):
    world, demo, company, person, controls = market
    web = Relation.from_property(controls, world)
    alice = Relation.from_individual(demo.alice, world)
    shell = Relation.from_individual(demo.shell_co, world)
    assert not alice >> web >> shell.dagger()  # not directly
    assert alice >> web.repeat() >> shell.dagger()  # but ultimately


def test_market_typed_chain(market):
    world, demo, company, person, controls = market
    with Query.no_reasoning:
        chain = (
            Query.from_individual(demo.alice, world, person)
            >> Query.from_property(controls, world, person, company)
            >> Query.from_property(controls, world, company, company)
            >> Query.from_property(controls, world, company, company)
            >> Query.from_individual(
                demo.shell_co, world, company).dagger())
    assert chain and not chain.coercions  # the predicates all meet
    boxes = chain.to_diagram().boxes
    assert [one.name for one in boxes[1:-1]] == 3 * ["controls"]


def test_market_validates_a_typed_chain(market):
    world, demo, company, person, controls = market
    with Query.no_reasoning:
        sloppy = (Query.from_property(controls, world, person, company)
                  >> Query.from_property(controls, world, person, company))
    one, = sloppy.coercions
    assert (one.source, one.target) == (company, person)
    with raises(AxiomError):
        sloppy.validate()  # a company is not a natural person


def test_fixtures_resolve_the_currency_module():
    world = load(FIBO + "FND/OwnershipAndControl/Ownership/", path=FIXTURES)
    for fragment in (
            "CurrencyAmount/MonetaryAmount", "CurrencyAmount/Currency",
            "Ownership/Portfolio", "Collections/comprises"):
        assert world.find(fragment) is not None


def test_the_whole_rule_book(market):
    world = market[0]
    book = axioms(world)  # every loaded module, one memoised compile
    assert len(book) > 500 and all(book)


def test_market_safety():
    world, demo, company, person, controls = market_world()  # a fresh one
    for_profit = world.find("ForProfitCorporation")
    not_for_profit = world.find("NotForProfitCorporation")
    world.add(OWLClassAssertionAxiom(demo.shell_co, for_profit))
    assert consistent(world)  # so far so good
    world.add(  # an agent's mistake
        OWLClassAssertionAxiom(demo.shell_co, not_for_profit))
    assert not consistent(world)  # HermiT knows the two are disjoint
