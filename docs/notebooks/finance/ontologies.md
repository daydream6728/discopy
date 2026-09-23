---
title: Ontologies
marimo-version: 0.23.14
pyproject: |
  requires-python = ">=3.11"
  dependencies = [
      "discopy[semantic] @ git+https://github.com/daydream6728/discopy.git@feature/allegory-owlapy",
  ]
---

```python {.marimo}
import marimo as mo
```

# Ontologies as guardrails for AI agents

An AI agent that moves money, signs contracts or files reports acts on a
world model it cannot show you. When that model is wrong, it fails
silently: the action goes through, and nobody learns anything until an
auditor does.

An [OWL ontology](https://www.w3.org/TR/owl2-overview/) is the opposite of
a hidden world model: it is an explicit, machine-checkable contract about
what exists and what is possible, written by the people who know. The
[Financial Industry Business Ontology](https://spec.edmcouncil.org/fibo/)
(FIBO) is two decades of that consensus for finance, maintained by the EDM
Council and used across the industry.

This notebook reads an ontology as what it mathematically is: two
categories, one split on top of the other, with
[HermiT](http://www.hermit-reasoner.com/) as the only judge of truth.

- `Relation` is the **single-sorted category of relations**: one
  generating object, `owl:Thing`; objects are arities; morphisms are
  finite relations between tuples of individuals — an *allegory* in the
  sense of Freyd & Scedrov, with converse, intersection and union but no
  complement, because OWL cannot say the complement of a property.
- `Query` is its **Karoubi envelope**, split at the predicates: wires are
  typed by OWL classes — compound expressions included, written the way a
  mathematician would — and composing two queries whose predicates do not
  meet asks HermiT whether one is subsumed by the other, inserting the
  verdict as a **coercion**: a proof object, drawn as a box exactly where
  the predicate changes.

Everything is deductive. Nothing is concluded from absence: a complement,
a universal or a cardinality holds of an individual only when the
ontology *entails* it. That is the pitch — pictures for humans, algebra
for machines, proofs for auditors — and the rest of the notebook is the
demo, on FIBO itself.
<!---->
## Loading FIBO from its base URL

`discopy.owl.load` takes the IRI an ontology lives at and pulls it in
with all its imports, through [owlapy](https://dice-group.github.io/owlapy/)
and the [owlapi](https://owlcs.github.io/owlapi/) bridge it bundles —
the same stack HermiT itself runs on:

```python
from discopy.owl import load
world = load("https://spec.edmcouncil.org/fibo/ontology"
             "/BE/OwnershipAndControl/CorporateControl/")
```

Here we load the same modules from the copy checked into DisCoPy's test
fixtures, so this notebook runs offline and reproducibly — and it is not
only about the network: HermiT accepts exactly the datatypes of the OWL 2
map, while the live OMG Commons modules that FIBO imports range over
`rdf:langString`, which is outside it, so reasoning about the live copy
fails where the curated one works.

```python {.marimo}
import os

from owlapy.class_expression import (
    OWLObjectComplementOf, OWLObjectIntersectionOf, OWLObjectMaxCardinality,
    OWLObjectSomeValuesFrom)
from owlapy.owl_axiom import OWLClassAssertionAxiom

from discopy.owl import (
    Query, Relation, Thing, axioms, consistent, extension, individual_class,
    load, name_of, subsumes)

FIBO = "https://spec.edmcouncil.org/fibo/ontology/"
FIXTURES = os.path.join(str(mo.notebook_dir() or "."),
                        "..", "..", "..", "test", "fixtures", "fibo")
world = load(
    FIBO + "BE/OwnershipAndControl/CorporateControl/", path=FIXTURES)
mo.md(f"Loaded **{len(world.classes())} classes** and "
      f"**{len(world.object_properties())} properties**, "
      "imports included.")
```

## What the ontology says, as pictures

FIBO's vocabulary of ownership and control comes with axioms. Take
`hasDirectOwningEntity`: the ontology says that following an ownership
record to its owning entity *is* a way of having a direct owning entity —
a property chain, i.e. an inclusion between a composite relation and a
named one. DisCoPy compiles every axiom to a pair of relations and draws
it:

```python {.marimo}
owning_entity = world.find("hasDirectOwningEntity")
chain_axiom = next(
    axiom for axiom in axioms(owning_entity, world)
    if len(axiom.terms[0].to_diagram().boxes) == 2)
chain_axiom.equation
```

Class expressions draw too, and they can be read at two altitudes. "A
party that controls something but is not a for-profit corporation" is a
predicate; read on `owl:Thing`, its picture shows its anatomy — the class
test composed with a quantifier and a complement bubble — while read at
its own type, the whole predicate is one wire of the split category,
labelled the way a mathematician would write it. Both readings are the
*same* coreflexive relation, and computing it already calls HermiT: its
members are the individuals *provably* satisfying the expression.

```python {.marimo}
controls = world.find("Relations/controls")
for_profit = world.find("ForProfitCorporation")
expression = OWLObjectIntersectionOf((
    OWLObjectSomeValuesFrom(controls, Thing),
    OWLObjectComplementOf(for_profit)))
mo.hstack([Query.from_class(expression, world, dom=Thing).to_diagram(),
           Query.from_class(expression, world).to_diagram()])
```

## A small world of companies

Now some facts for the axioms to bite on: a person and three companies in
a chain of control, the kind of structure a compliance team unravels every
day. Adding them drops the world's reasoner, so everything read from now
on is what the *new* ontology entails, not merely what was typed in.

```python {.marimo}
business_entity = world.find("LegalPersons/BusinessEntity")
natural_person = world.find("LegallyCompetentNaturalPerson")
alice = world.individual("alice", natural_person)
holdings, bank, shell = (
    world.individual(name, business_entity)
    for name in ("acme_holdings", "acme_bank", "shell_co"))
world.relate(alice, controls, holdings)
world.relate(holdings, controls, bank)
world.relate(bank, controls, shell)
world.add(OWLClassAssertionAxiom(shell, for_profit))
facts = mo.hstack([
    Query.from_individual(subject, world)
    >> Query.from_property(
        controls, world, individual_class(subject, world), business_entity)
    >> Query.from_individual(target, world, business_entity).dagger()
    for subject, target in [
        (alice, holdings), (holdings, bank), (bank, shell)]])
facts
```

Each column is one entailed fact, read top to bottom: a point, a property,
a co-point — `controls(alice, acme_holdings)` and so on. Because the
predicates of consecutive boundaries meet, no coercion was needed; the
whole chain of control composes as one diagram of the split category, and
the scalar it evaluates to is its truth value:

```python {.marimo}
chain = (
    Query.from_individual(alice, world)
    >> Query.from_property(
        controls, world, natural_person, business_entity)
    >> Query.from_property(
        controls, world, business_entity, business_entity)
    >> Query.from_property(
        controls, world, business_entity, business_entity)
    >> Query.from_individual(shell, world, business_entity).dagger())
mo.hstack([chain.to_diagram(),
           mo.md("The chain of control holds: "
                 f"**{bool(chain)}** — and it has "
                 f"**{len(chain.coercions)}** coercions: every hand-off "
                 "stayed within its predicate.")])
```

## Composition that runs the reasoner

Now the sloppy version: an agent wires the second hop as if the
controller were still a natural person. The predicates of the boundary
do not meet, so composition asks HermiT whether `BusinessEntity` is
subsumed by `LegallyCompetentNaturalPerson` — and inserts the verdict as
a coercion box exactly where the hand-off happens:

```python {.marimo}
sloppy = (
    Query.from_property(controls, world, natural_person, business_entity)
    >> Query.from_property(
        controls, world, natural_person, business_entity))
proof, = sloppy.coercions
try:
    sloppy.validate()
    verdict = "validated"
except Exception as error:
    verdict = f"**rejected**: {error}"
mo.hstack([sloppy.to_diagram(),
           mo.md("HermiT's proof object says the coercion is entailed: "
                 f"**{proof.entailed}**, so `validate()` {verdict}.")])
```

The box in the middle is not decoration: it is where a proof was owed,
and the proof failed. A well-typed pipeline of agent tools carries its
own audit trail — every predicate change is visible and certified, or
visibly *not*.
<!---->
## Certain answers from entailed facts

Underneath every query sits the single-sorted relation over the entailed
atoms. Composition is relational composition, so "who ultimately controls
whom" is the reflexive transitive closure — algebra, not a query
language, and sound for entailment because every atom it starts from is
entailed:

```python {.marimo}
web = Relation.from_property(controls, world)
alice_point = Relation.from_individual(alice, world)
shell_point = Relation.from_individual(shell, world)
directly = bool(alice_point >> web >> shell_point.dagger())
ultimately = bool(alice_point >> web.repeat() >> shell_point.dagger())
mo.md(f"Does alice control shell_co directly? **{directly}**. "
      f"Ultimately, through the chain? **{ultimately}**.")
```

The asserted graph is available to anything that speaks SPARQL, evaluated
by [rdflib](https://rdflib.readthedocs.io/) — and on `controls`, whose
atoms are all asserted, it agrees with the entailed extension:

```python {.marimo}
sparql_web = Relation.sparql(
    "SELECT ?x ?y WHERE { ?x <" + controls.iri.as_str() + "> ?y . }",
    1, 1, world)
mo.md(f"SPARQL and the property extension agree: "
      f"**{sparql_web == web}**.")
```

And the two altitudes convert into each other without bookkeeping:
`typed()` translates any single-sorted relation back up to a query,
reading the boundary predicates off its own picture — a membership test
composed at either end is a coreflexive factor, collapsed into the type
of its wire, so nobody has to spell out `dom` and `cod`:

```python {.marimo}
fenced = extension(business_entity, world) >> web\
    >> extension(business_entity, world)
collapsed = fenced.typed()
mo.hstack([fenced.to_diagram(), collapsed.to_diagram()],
          justify="center")
```

```python {.marimo}
mo.md(f"The tests became types: `{collapsed}` — "
      f"and nothing extensional changed: "
      f"**{collapsed.relation == fenced}**.")
```

HermiT also decides candidate rules exactly, not just the declared ones:

```python {.marimo}
controlling = OWLObjectIntersectionOf((
    business_entity, OWLObjectSomeValuesFrom(controls, Thing)))
candidate = subsumes(controlling, business_entity, world)
converse = subsumes(business_entity, controlling, world)
mo.md(f"A controlling business entity is a business entity "
      f"(**{candidate}**), but not conversely (**{converse}**).")
```

## The whole rule book

Every axiom of the knowledge base compiles to a decidable check on these
finite relations: ``bool(axiom)`` asks whether the world entails a
*counterexample*, and a consistent ontology entails none of its own — the
schema entails itself. `axioms(world)` compiles the rules of **every**
loaded FIBO module at once, class and property axioms alike, with one
reasoner and one memoised retrieval per predicate:

```python {.marimo}
rule_book = axioms(world)
mo.md(f"The rule book of the loaded knowledge base: "
      f"**{len(rule_book)}** axioms, each a `discopy` `Equation` — "
      f"and every one holds: **{all(rule_book)}**.")
```

Each rule draws itself from the ontology's own syntax: intersection is
composition, a quantifier follows its property, complement is the one
bubble with union as its De Morgan dual — and
a class axiom is read at its subject's own predicate, the subject a
typed wire with the parent's anatomy drawn on it, the way a query would
read it. Two showpieces — a bilateral agreement has *exactly two* party
roles, and an affiliate is *either* a majority controlling party *or* a
controlled one — then the whole book, every rule expandable:

```python {.marimo}
showpieces = [rule for rule in rule_book
              if "=2 hasPartyRole" in str(rule)
              or "⊔ ControlledParty" in str(rule)]
mo.vstack(
    [rule.equation for rule in showpieces]
    + [mo.accordion({
        f"{index}. {rule}": mo.lazy(lambda rule=rule: rule.equation)
        for index, rule in enumerate(rule_book, 1)})])
```

## What the open world will not let you conclude

Deduction cuts both ways: it also *refuses* conclusions. Nothing in our
market is provably **not** a for-profit corporation — being a natural
person does not prove it, absence of paperwork does not prove it — and
nobody provably controls at most one thing, because nothing rules out
control edges we have not heard of:

```python {.marimo}
provably_not = extension(OWLObjectComplementOf(for_profit), world)
bounded = extension(OWLObjectMaxCardinality(1, controls, Thing), world)
mo.md(f"Individuals provably ¬ForProfitCorporation: "
      f"**{[name_of(x) for (x, ), _ in provably_not.inside]}** — "
      f"provably controlling at most one thing: "
      f"**{[name_of(x) for (x, ), _ in bounded.inside]}**. "
      "The open world answers *unknown*, and DisCoPy will not launder "
      "*unknown* into *false*.")
```

## Open world = safety

The reasoner earns its keep when an agent acts. Suppose one, optimising a
tax position, proposes to reclassify `shell_co` as a not-for-profit
corporation. The assertion itself looks harmless — it is one triple:

```python {.marimo}
ok_before = consistent(world)
mo.md(f"HermiT says the market is consistent: **{ok_before}**.")
```

```python {.marimo}
assert ok_before
not_for_profit = world.find("NotForProfitCorporation")
world.add(OWLClassAssertionAxiom(shell, not_for_profit))
ok_after = consistent(world)
mo.md(f"HermiT says the market is still consistent: **{ok_after}** — "
      "FIBO declares for-profit and not-for-profit corporations "
      "disjoint, so the agent's proposal is rejected *before* it acts, "
      "with the violated axiom as the audit trail.")
```

The guardrail did not come from a prompt, a fine-tune or a heuristic: it
came from a published industry standard, and it is enforced by a theorem
prover with twenty years of tooling behind it.
<!---->
## Why this matters

- **Agent safety is a semantics problem.** An agent's action is safe
  relative to a world model; an ontology makes that model explicit,
  standard and checkable, and deduction never mistakes missing data for
  evidence. Consistency rejects bad writes; subsumption certifies every
  hand-off between tools.
- **The math keeps everyone honest.** The relations form a distributive
  allegory, its Karoubi envelope splits every predicate into a type, and
  the coercions carry the proofs — `discopy.abc` states the laws, the
  test suite checks them. Diagrams are not illustrations: they *are* the
  terms, and the box where a predicate changes is exactly where a proof
  is owed.
- **Nothing here is bespoke.** FIBO is maintained by the EDM Council;
  proving is delegated to HermiT; querying to SPARQL. DisCoPy is the thin
  categorical interface that makes them compose — and draw.

Next steps: data properties and literals as extra generating objects,
richer SPARQL round trips, and tabulations — reifying any relation as a
split object of its own.
