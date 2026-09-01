---
title: Ontologies
marimo-version: 0.23.14
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

This notebook reads an ontology as what it mathematically is: a **category
of relations** — an allegory, in the sense of Freyd & Scedrov — where

- every OWL class and property is a *finite relation* between individuals,
- composition, intersection, union and complement are the set operations
  that define relations, so checking an axiom is deciding an inclusion,
- every relation draws itself as a *string diagram*, and
- the open world is one [HermiT](http://www.hermit-reasoner.com/) call
  away.

One object, three faces: pictures for humans, relational algebra for
runtime monitors, description logic for auditors. That is the pitch — the
rest of the notebook is the demo, on FIBO itself.
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
    Relation, axioms, box, consistent, extension, load, point, to_diagram)

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
*coreflexive* relation — a predicate read as a partial identity. Read on
`owl:Thing`, it shows its anatomy: the class test composed with a
quantifier and a complement bubble. Read at its own type, the whole
predicate is one wire, labeled the way a mathematician would write it —
compound entities are objects too:

```python {.marimo}
controls = world.search_one(iri=FIBO + "FND/Relations/Relations/controls")
for_profit = world.search_one(
    iri=FIBO + "BE/LegalEntities/CorporateBodies/ForProfitCorporation")
expression = controls.some(Thing) & Not(for_profit)
mo.hstack([
    extension(expression, dom=Thing, world=world).to_diagram(),
    extension(expression, world=world).to_diagram()])
```

## A small world of companies

Now some facts for the axioms to bite on: a person and three companies in
a chain of control, the kind of structure a compliance team unravels every
day.

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
facts = mo.hstack([
    point(subject, natural_person if subject is alice else business_entity)
    >> box(controls, natural_person if subject is alice
           else business_entity, business_entity)
    >> point(target, business_entity).dagger()
    for subject, target in [
        (alice, holdings), (holdings, bank), (bank, shell)]])
facts
```

Each column is one asserted fact, read top to bottom: a point, a property,
a co-point — `controls(alice, acme_holdings)` and so on.
<!---->
Because predicates are types, the whole chain of control composes as one
diagram with every wire labeled by its FIBO class — no membership boxes
to read through. Where two predicates do not meet, composition inserts
the coercion between them automatically, so a boundary change is always
visible as a box:

```python {.marimo}
person_controls = Relation.from_property(
    controls, natural_person, business_entity)
company_controls = Relation.from_property(
    controls, business_entity, business_entity)
control_chain = (
    Relation.from_individual(alice, natural_person)
    >> person_controls >> company_controls >> company_controls
    >> Relation.from_individual(shell, business_entity).dagger())
mo.hstack([control_chain.to_diagram(),
           mo.md("The scalar this diagram evaluates to is the truth "
                 f"value of the chain: **{bool(control_chain)}**.")])
```

## Closed world: relations as a runtime monitor

Reading the `controls` property off the loaded world gives a finite
relation. Composition is relational composition, so "who ultimately
controls whom" is the reflexive transitive closure — no query language,
just the algebra:

```python {.marimo}
web = Relation.from_property(controls, dom=Thing, cod=Thing)
alice_point = Relation.from_individual(alice, Thing)
shell_point = Relation.from_individual(shell, Thing)
directly = bool(alice_point >> web >> shell_point.dagger())
ultimately = bool(alice_point >> web.repeat() >> shell_point.dagger())
mo.md(f"Does alice control shell_co directly? **{directly}**. "
      f"Ultimately, through the chain? **{ultimately}**.")
```

The same extension is available to anything that speaks SPARQL, evaluated
by owlready2's native engine — the two agree by construction:

```python {.marimo}
sparql_web = Relation.sparql(
    "SELECT ?x ?y WHERE { ?x <" + controls.iri + "> ?y . }",
    Thing, Thing, world)
mo.md(f"SPARQL and the property extension agree: "
      f"**{sparql_web == Relation.from_property(controls)}**.")
```

And every axiom of the ontology is now a *decidable* check on finite
relations — a runtime monitor that costs set operations, not a theorem
prover:

```python {.marimo}
rule_book = axioms(world.get_ontology(
    FIBO + "BE/OwnershipAndControl/ControlParties/"))
mo.md(f"The loaded world satisfies **{sum(map(bool, rule_book))} of "
      f"{len(rule_book)}** compiled axioms of the ControlParties module.")
```

Class expressions evaluate closed-world too: "controls at least two
things" holds of nobody in our little market, and DisCoPy computes it by
counting, not by proving:

```python {.marimo}
hoarders = extension(controls.min(2, Thing), dom=Thing, world=world)
controllers = extension(controls.some(Thing), dom=Thing, world=world)
mo.md(f"Individuals controlling something: "
      f"**{[str(x.name) for (x, ), _ in controllers.inside]}** — "
      f"controlling at least two things: "
      f"**{[str(x.name) for (x, ), _ in hoarders.inside]}**.")
```

## Open world: the reasoner as an audit trail

Closed-world checks are fast, but they only see what is written. The open
world is where an ontology earns its keep: HermiT checks that the facts
*could be true* of any world satisfying all of FIBO's axioms — including
the ones nobody thought to monitor.

Our world is consistent so far:

```python {.marimo}
ok_before = consistent(world)
mo.md(f"HermiT says the market is consistent: **{ok_before}**.")
```

Now an AI agent, optimising a tax position, proposes to reclassify
`shell_co` as a not-for-profit corporation. The assertion itself looks
harmless — it is one triple:

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
  standard and checkable. The same `Relation` objects give a cheap
  closed-world monitor for every action and an open-world proof when it
  counts.
- **The math keeps everyone honest.** Relations form an allegory: the
  laws of composition, converse, intersection and complement are theorems
  about the implementation (`discopy.abc` states them, the test suite
  checks them). Diagrams are not illustrations — they *are* the terms.
- **Nothing here is bespoke.** FIBO is maintained by the EDM Council;
  reasoning is delegated to HermiT; queries to SPARQL. DisCoPy is the
  thin categorical interface that makes them compose — and draw.

Next steps: data properties and literals as extra generating objects,
richer SPARQL round trips, and the Karoubi splitting that makes every
class an object of its own.
