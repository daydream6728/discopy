> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

Agent `grammar`, the bullets of #31 in `discopy/grammar/`:

- [x] B67: `thue.Word`, `categorial.Word` daggers keep `dom`/`cod`; `cfg.Word`/`Rule` and `thue.Rule` daggers crash; `categorial.Diagram.fc/bc` on non-atomic outer types; `cfg.Tree.from_nltk` drops every child after the first string (`fc`/`bc` already right on `main` since discopy/discopy#400, tested by `test/grammar/categorial.py::test_Diagram`)
- [x] B30: `grammar.cfg` unhashable and uncomparable; dependency leaves never become `Word`s; `cfg.Word` refuses drawing params
- [WIP] @session_01YCJQ3Xco3ydQ6AsdTtYJ5x-2026-10-22 16:00 B31: `pregroup.Diagram.normal_form` crashes on foliated and on left-whiskered diagrams
- [x] B86, grammar parts: rotated `pregroup.Word` through `to_tree`; `pregroup.Word.__repr__` without its factory prefix; `cfg.Tree`/`Rule`/`Id` reprs not evaluable; `Rule.__eq__` compares a tuple to `[]` (the rotated word already loads with its winding on `main`, since #113)
- [ ] `CHANGELOG.md`
