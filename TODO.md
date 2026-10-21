> yes go ahead on both, refactoring via Stream sounds especially meaningful, Daphne confirmed the bias is a bit more general so let's also implement that, but first can you explain what this bias is about?

(toumix, 2026-10-21, interactive; answering daydream6728's review of
[discopy/discopy#813](https://github.com/discopy/discopy/pull/813), and daydream6728 on Slack:
> I'd say it's better to have the bias, but maybe making it optional; it's more general, and then we can choose whether we want it or not (depending on the problem and the interpretation of the result, the bias may not make sense, but in general it doesn't hurt)
)

- [WIP] @session_01KnHakJ3PdxvbpCKGgzGeJt-2026-10-21 10:20 `Reservoir.stream` and `Reservoir.encoding`: the reservoir as a `Stream[Circuit]` feeding back its memory, `run` walking its slices
- [ ] optional readout bias, on by default and unpenalised by the ridge term, in `run`, `fit` and `predict`
- [ ] tests, CHANGELOG, then carry the change into discopy/discopy#813
