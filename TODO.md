# TODO

> `move`'s `target > source` branch in `from_pyzx` looks dead, in `quantum.zx` and `optyx.core.zx`
>
> `Diagram.from_pyzx` defines a closure `move(scan, source, target)` with three branches — `target < source`, `target > source`, `target == source`. [...] Neither caller reached it, and both look structurally unable to [...]
>
> What would settle it: either an argument that the two callers cannot produce `target > source` — in which case delete the branch and let `move` be a two-case function — or a graph that reaches it, in which case it wants a test, since nothing covers it today.
>
> The same closure, with the same three branches, is in `discopy/quantum/zx.py` and in its copy in `discopy/optyx/core/zx.py`.

(rel-int/discopy-next#361)

- [ ] argue both callers give `target <= source`
- [ ] delete the branch in `quantum.zx` and `optyx.core.zx`
- [ ] fuzz the round trip before and after
- [ ] test boundaries and spider inputs in odd orders, both copies
- [ ] changelog line
