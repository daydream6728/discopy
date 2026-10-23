# TODO

Prompt (toumix, 🌤️ Daylight 2026-10-22, verbatim):

> You have a $200 modal budget to make some improvement to our parser (English/Dutch/French/trilingual) you're free to try any techniques you can think of, the more abstract the better. First merge all of the generic parser code from lambek to discopy-next.

#277 was the first sentence's second half. This branch is the library half of the improvement,
rel-int/lambek#12, where decoding by search gained 6.0 points of exact term on English (rebank dev)
and 3.7 on French (TLGbank dev) over the cascade `Parser.forward`, on the same checkpoint.

- [WIP] @session_01KbBG77r4dz5RennpDkce2y-2026-10-23 07:50 **Parsing as search in proof-net space**:
  `products`, the lazy best-first enumeration of a product of sorted lists; `Linker.log_likelihood`,
  the log-probability of the links of a net after Sinkhorn normalisation; `Parser.search`, the
  correct proof net of highest joint score among the best sequents of the `k` best types of each word
- [ ] CHANGELOG, docs, pflake8, pylint, the suite
