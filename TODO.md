# TODO

> i don't like the standalone `inapplicable` function, can't we just
> define it for Rule just like there's already an `inapplicable`
> method on Axiom?

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-24 Define
      `Rule.inapplicable(reason)` returning a marked copy, like
      `Axiom.inapplicable`, and delete the standalone decorator —
      which mutates the function it wraps, so pregroup's mark on the
      shared `trace_left` leaked into `ribbon.Diagram` and dropped
      the trace rules of the whole ribbon-side tower, import-order
      dependent
- [ ] Respell the four sites: `CompactCategory.twist`, the traces of
      `quantum.circuit` and `grammar.pregroup`, the trace of
      `feedback`
- [ ] Verify the restored trace rules against the matrix, fixing or
      classifying what the wider search finds
- [ ] `ruff check`, `ty check`, pytest, fast + dev matrix,
      CHANGELOG, close
