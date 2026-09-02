---
title: Ontologies
marimo-version: 0.23.14
pyproject: |
  requires-python = ">=3.11"
  dependencies = [
      "discopy @ git+https://github.com/daydream6728/discopy.git@feature/allegories",
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

`discopy.owl.load` takes the IRI an ontology lives at and pulls it in with
all its imports, using [owlready2](https://owlready2.readthedocs.io/):

```python
from discopy.owl import load
corporate_control = load("https://spec.edmcouncil.org/fibo/ontology"
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

from owlready2 import Not, Thing, World

from discopy.owl import (
    Query, Relation, axioms, consistent, extension, load, reason, subsumes)

FIBO = "https://spec.edmcouncil.org/fibo/ontology/"
FIXTURES = os.path.join(str(mo.notebook_dir() or "."),
                        "..", "..", "test", "fixtures", "fibo")
world = World()
corporate_control = load(
    FIBO + "BE/OwnershipAndControl/CorporateControl/",
    world, path=FIXTURES)
modules = [key for key in world.ontologies if key.startswith("http")]
mo.md(f"Loaded **{len(list(world.classes()))} classes** and "
      f"**{len(list(world.properties()))} properties** "
      f"from {len(modules)} ontology modules.")
```

## What the ontology says, as pictures

FIBO's vocabulary of ownership and control comes with axioms. Take
`hasDirectOwningEntity`: the ontology says that following an ownership
record to its owning entity *is* a way of having a direct owning entity —
a property chain, i.e. an inclusion between a composite relation and a
named one. DisCoPy compiles every axiom to a pair of relations and draws
it:

```python {.marimo}
owning_entity = world.search_one(iri="*hasDirectOwningEntity")
chain_axiom = next(
    axiom for axiom in axioms(owning_entity)
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
controls = world.search_one(iri=FIBO + "FND/Relations/Relations/controls")
for_profit = world.search_one(
    iri=FIBO + "BE/LegalEntities/CorporateBodies/ForProfitCorporation")
expression = controls.some(Thing) & Not(for_profit)
mo.hstack([Query.from_class(expression, dom=Thing).to_diagram(),
           Query.from_class(expression).to_diagram()])
```

## A small world of companies

Now some facts for the axioms to bite on: a person and three companies in
a chain of control, the kind of structure a compliance team unravels every
day. After asserting them we `reason` once, so that everything read from
now on is what the ontology *entails*, not merely what was typed in.

```python {.marimo}
business_entity = world.search_one(
    iri=FIBO + "BE/LegalEntities/LegalPersons/BusinessEntity")
natural_person = world.search_one(
    iri=FIBO + "BE/LegalEntities/LegalPersons"
    "/LegallyCompetentNaturalPerson")
market = world.get_ontology("http://discopy.org/market.owl")
with market:
    alice = natural_person("alice")
    holdings, bank, shell = map(
        business_entity, ("acme_holdings", "acme_bank", "shell_co"))
    alice.controls = [holdings]
    holdings.controls = [bank]
    bank.controls = [shell]
    shell.is_a.append(for_profit)
reason(world)
facts = mo.hstack([
    Query.from_individual(subject)
    >> Query.from_property(controls, subject.is_a[0], business_entity)
    >> Query.from_individual(target, business_entity).dagger()
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
chain = (Query.from_individual(alice)
         >> Query.from_property(controls, natural_person, business_entity)
         >> Query.from_property(controls, business_entity, business_entity)
         >> Query.from_property(controls, business_entity, business_entity)
         >> Query.from_individual(shell, business_entity).dagger())
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
sloppy = (Query.from_property(controls, natural_person, business_entity)
          >> Query.from_property(controls, natural_person, business_entity))
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
alice_point = Relation.from_individual(alice)
shell_point = Relation.from_individual(shell)
directly = bool(alice_point >> web >> shell_point.dagger())
ultimately = bool(alice_point >> web.repeat() >> shell_point.dagger())
mo.md(f"Does alice control shell_co directly? **{directly}**. "
      f"Ultimately, through the chain? **{ultimately}**.")
```

The same relation is available to anything that speaks SPARQL, evaluated
by owlready2's native engine on the materialised graph — the two agree by
construction:

```python {.marimo}
sparql_web = Relation.sparql(
    "SELECT ?x ?y WHERE { ?x <" + controls.iri + "> ?y . }",
    1, 1, world)
mo.md(f"SPARQL and the property extension agree: "
      f"**{sparql_web == web}**.")
```

And every axiom of the ontology compiles to a decidable check on these
finite relations: ``bool(axiom)`` asks whether the world entails a
*counterexample*. A consistent ontology entails none of its own — the
schema entails itself — so the interesting questions are about
candidates:

```python {.marimo}
rule_book = axioms(world.get_ontology(
    FIBO + "BE/OwnershipAndControl/ControlParties/"))
candidate = subsumes(
    business_entity & controls.some(Thing), business_entity, world)
converse = subsumes(
    business_entity, business_entity & controls.some(Thing), world)
mo.md(f"All **{len(rule_book)}** compiled axioms of ControlParties hold "
      f"— no entailed counterexample. And HermiT decides candidates "
      f"exactly: a controlling business entity is a business entity "
      f"(**{candidate}**), but not conversely (**{converse}**).")
```

## What the open world will not let you conclude

Deduction cuts both ways: it also *refuses* conclusions. Nothing in our
market is provably **not** a for-profit corporation — being a natural
person does not prove it, absence of paperwork does not prove it — and
nobody provably controls at most one thing, because nothing rules out
control edges we have not heard of:

```python {.marimo}
provably_not = extension(Not(for_profit), world)
bounded = extension(controls.max(1, Thing), world)
mo.md(f"Individuals provably ¬ForProfitCorporation: "
      f"**{[str(x.name) for (x, ), _ in provably_not.inside]}** — "
      f"provably controlling at most one thing: "
      f"**{[str(x.name) for (x, ), _ in bounded.inside]}**. "
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
not_for_profit = world.search_one(
    iri=FIBO + "BE/LegalEntities/CorporateBodies/NotForProfitCorporation")
with market:
    shell.is_a.append(not_for_profit)
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
