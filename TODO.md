# TODO

> In `discopy/markov.py` at lines 216-217: `def dagger(self) -> Copy: return self.Copy(self.cod, len(self.dom))` why cant we return a Merge here too?
>
> can you guarantee that the construction of factories is cached and that it won't introduce slowdowns in our algorithms

- [x] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-19 09:00 The dagger of a merge is a copy by definition, and the round trip holds: `Discard(x).dagger()` is `Merge(x, 0)` and back.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-19 09:00 Reading a generator costs 260 ns against 47 ns on `main`, and `Diagram.swap` is 21% slower. Cache on the class as it is read, so that a hit is one dictionary lookup.
- [ ] Measure the benchmark suite against `main` on this runner.
