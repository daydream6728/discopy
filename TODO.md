# TODO

> i don't like it. every rule should be a rule, plain and simple.
> if a category overrides a rule, it should wrap the override with a
> @rule decorator as well.
> make declarations aware of inner decorators as well: at least for
> classmethods and abstractmethods.

> why distinguish rules from generators? the name generator is already
> reserved to atomic diagram boxes like Swap, Cup and Cap. the plural
> (or sometimes just lowercase version) like swap, cups and caps are
> just rules with no hom premisse, why do we need to handle them
> differently in the first place, can't they be rules too?

> in fact, do we even need swap, cups, caps, etc... to be rules at all
> since their can already be sampled by generators? (in the box sense)

- [x] Redesign `declarations`: unwrap inner decorators (classmethods,
      abstractmethods) in a loop, drop the `shadowed` special case so
      a plain method over a rule drops it like an axiom, and an
      override decorated `@rule` without a conclusion keeps the
      sequent of the declaration it overrides, one with a conclusion
      redeclares it
- [x] Unify `Generator` into `Rule`: delete the class and the
      `@generator` decorator, derive `Category.generators` as the
      rules with no hom premise (`Rule.recursive`), keep the
      structural rules as rules since the sequent is the search
      interface and `id`, `cycle`, `braid_inverse`, the pivotal trace
      and the vocabulary constants have no box class to sample from
- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-25 Inventory every
      implementation that shadows a rule and decorate it with `@rule`
- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-25 Give
      `Rule.__get__` an instance fast path and measure the
      composition benchmark, since `then` and `tensor` become rules
      on the hot path
- [x] Respell the inapplicable sites without the `rule(...)` wrap,
      now that the attribute is a rule
- [ ] `ruff check`, `ty check`, pytest, fast + dev matrix, benchmark,
      CHANGELOG, close
