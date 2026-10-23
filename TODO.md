# TODO

Prompt (toumix, 🌤️ Daylight 2026-10-22, verbatim):

> You have a $200 modal budget to make some improvement to our parser (English/Dutch/French/trilingual) you're free to try any techniques you can think of, the more abstract the better. First merge all of the generic parser code from lambek to discopy-next.

Answer (toumix, 2026-10-23, on toumix/memory#166, to rel-int/lambek#12's two proposals, the first being "port the fibre and the k-best linkings into discopy-next's `Parser.search`"), verbatim:

> both

- [x] `assignments`: Murty's ranking of the assignments of a square matrix, best first, lazily
- [x] `Sequent.linkings`: the best linkings of a sequent, the product of the rankings of its atom blocks, lazily
- [x] `Parser.search` takes `depth` (sequents enumerated; `width` counts those with a goal) and `links` (linkings tried per sequent), defaults leaving it as it is
- [x] tests against brute force, docs, `CHANGELOG.md`
