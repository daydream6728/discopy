# TODO

> remove all idiosyncracies accumulated during the design of this
> branch and finalize the design. remove as many concepts and
> operations as possible, the only things we need is to generate a
> canonical equation for axioms, and generate diagrams efficiently
> from rules according to a goal pattern, all while making everything
> as typeable as possible in the cleanest way

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-23 14:00 Inventory
      every public concept and operation of `pattern`, `search` and
      `axioms` with its uses, keeping only what serves the two
      capabilities: the canonical equation of an axiom and the
      generation of diagrams from rules toward a goal pattern
- [ ] Remove what does not serve them, fold what remains into its
      simplest typed shape, and re-validate the sequents unchanged
- [ ] Consolidate the CHANGELOG entries into one description of the
      final design
- [ ] `ty check`, `ruff check`, pytest, proptest fast profile, close
