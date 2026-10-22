# TODO

> Move all of the optyx work into discopy-next, keep the license, make sure you keep the attribution of commits, copy all the open issues and pull requests adding giodefelice-agents as assignee. I had planned for him to do it (prompt attached) but I got some spare tokens so I'll do it myself instead.

toumix, 2026-10-22, interactive; the attached prompt is quoted in #225. optyx's `pytket-pyzx`
needs pyzx ≥ 0.9, against the `quantum` extra's `pyzx == 0.7.3`, so the `optyx` extra cannot sit
in the `all` group until discopy reads pyzx 0.10. That is a change to discopy, so it goes first,
on its own.

- [x] `quantum` pins pyzx 0.10.7
- [x] `zx.Diagram.to_pyzx` gives pyzx exact `Fraction` phases, which pyzx 0.10 requires
- [x] `test/fixtures/zx-graph.json` says which boundary is which in the way pyzx 0.10 reads
- [x] CHANGELOG under `Changed`
