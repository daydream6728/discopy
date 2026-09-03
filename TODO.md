# TODO

> i see. what i want is a way to translate any Relation to an equivalent Query
> that collapses coreflexives as types, without having to explicitly specify
> dom and cod. would this make sense?
>
> implement it.
>
> while you're at it, change the rulebook to display query equations instead
> of untyped relations
>
> wait, instead of building frobenius boxes, can you just make discopy.owl a
> full blown discopy layer with its own boxes etc...?

- [WIP] @claude-allegories-2026-09-03 12:30 `discopy.owl` becomes a full
      discopy layer: `Ob` wraps a predicate, `Ty`, `Box`, `Diagram` subclass
      `frobenius` with the factory pattern, and `ob`/`box`/`point`/
      `to_diagram` build them instead of raw frobenius
- [ ] `Relation.typed` reading boundary predicates off the picture, no
      explicit dom and cod
- [ ] the rule book displays typed query equations: class axioms at the
      subject's predicate
- [ ] tests at 100% coverage, a notebook cell, changelog and sign-off
