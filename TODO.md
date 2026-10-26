> Your issues, all in `discopy/optyx/channel.py` (and possibly `discopy/optyx/core/diagram.py`), ported from rel-int/optyx when optyx moved into `discopy.optyx`: rel-int/discopy-next #290 (channel.Swap.dagger returns self), #291 (empty channel Sum has no types), #244 (Channel.double broken for plain array kraus boxes: Box.conjugate returns a dagger; classical doubling mis-assembles when arities differ), #252 (doubling a Sum evaluates to zero), #234 (Channel.inflate drops env), #247 (Channel.from_callable raises "Expected monoidal.Box"). Reproduce each on origin/main first; an issue that no longer reproduces gets a comment saying on which commit it stopped, and is closed via the PR's description only if a test now pins it (otherwise just comment). Fix the rest in ONE PR, one commit per issue, a regression test per issue, `Closes #N` per issue on its own line.

- [x] #290: `channel.Swap.dagger` swaps its wires back
- [x] #291: the empty channel `Sum` keeps its types in `get_kraus` and `double`
- [ ] #244: no longer reproduces at the move (#276), pinned by `test_channel.py`: comment
- [ ] #252: no longer reproduces at the move (#276): pin with a test, comment
- [ ] #234: stopped at #332 (`3e6f3972`): pin with a test, comment
- [ ] #247: stopped at #331 (`a4c13265`): pin with a test, comment
