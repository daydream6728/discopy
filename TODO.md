# TODO

Prompt (toumix, 🌤️ Daylight 2026-10-22, verbatim):

> You have a $200 modal budget to make some improvement to our parser (English/Dutch/French/trilingual) you're free to try any techniques you can think of, the more abstract the better. First merge all of the generic parser code from lambek to discopy-next.

This branch is the first sentence's second half: what rel-int/lambek still holds that is
generic, rewritten on `grammar.abstract`, `grammar.proofnet`, `grammar.neural` and
`grammar.categorial`. The core of lambek#8 (tagger, Sinkhorn linker, Hungarian decoding,
geometry of interaction, sequentialisation) is already here since #51; lambek#1's lambda
calculus is `closed.BohmTree` since #442. Datasets, readers, training runs and results stay
in lambek.

- [WIP] @session_01KbBG77r4dz5RennpDkce2y-2026-10-22 18:40 **Goal inference by the count invariant** (lambek#8 `decode.decode_sentence`,
  `french.formula_balance`): the signed count of the atoms of a type, and the sequent of
  some words whose goal is the smallest type with their count; `Parser` infers the goal
  when none is given
- [WIP] @session_01KbBG77r4dz5RennpDkce2y-2026-10-22 18:40 **Decoding within a sub-signature** (lambek#8 `Tagger.constrain`, its per-language
  inventory masks): `Tagger.beam` and `Tagger.loss` restricted to some atoms
- [WIP] @session_01KbBG77r4dz5RennpDkce2y-2026-10-22 18:40 **Label smoothing over the symbols allowed** (lambek#8 `Tagger.forward`)
- [ ] **lambek#8's switching regressions as tests of `ProofNet.to_term`**
  (`test_proofnets.py`: the disconnected cycle, the stuck par, the crossed identity)
- [ ] **A chart parser for categorial grammars** (lambek#2 `CYK`, lambek#8 `chart.Chart`):
  the k best terms of a sentence from the scored types of its words, by CKY over the
  combinators, with Eisner's normal form against spurious ambiguity
- [ ] CHANGELOG, docs, pflake8, pylint, the suite
