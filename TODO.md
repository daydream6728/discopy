# TODO

> i don't like it. every rule should be a rule, plain and simple.
> if a category overrides a rule, it should wrap the override with a
> @rule decorator as well.
> make declarations aware of inner decorators as well: at least for
> classmethods and abstractmethods.

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-25 Redesign
      `declarations`: unwrap inner decorators (classmethods,
      abstractmethods) in a loop, drop the `shadowed` special case so
      a plain method over a rule drops it like an axiom, and an
      override decorated `@rule` without a conclusion keeps the
      sequent of the declaration it overrides, one with a conclusion
      redeclares it
- [ ] Inventory every implementation that shadows a rule or
      generator and decorate it with `@rule`/`@generator`
- [ ] Give `Rule.__get__` an instance fast path and measure the
      composition benchmark, since `then` and `tensor` become rules
      on the hot path
- [ ] Respell the inapplicable sites without the `rule(...)` wrap,
      now that the attribute is a rule
- [ ] `ruff check`, `ty check`, pytest, fast + dev matrix, benchmark,
      CHANGELOG, close
