> `from_diagram` is giodefelice-agents' code from optyx, under Apache-2.0 [...] `discopy/quantum` is BSD-3. Moving it into `quantum.contextuality` relicenses it, which #225's prompt rules out: "Do not relicense anything."

> [`from_diagram`] reads `EvalResult.prob_dist`, which divides each context by its total whenever the total is not 1 [...] So a postselected or heralded diagram silently becomes the model conditioned on success.

— https://github.com/rel-int/discopy-next/pull/334#issuecomment-6405668128 and #issuecomment-6405668769

- [WIP] @session_01TLABkoqqKvrHxjA3QkrnH9-2026-10-26 01:00 keep the evaluation of the diagram in `discopy/optyx` (Apache-2.0) as `optyx.contextuality.distributions`, called by `quantum.contextuality.Model.from_diagram`; its example and test in optyx
- [WIP] @session_01TLABkoqqKvrHxjA3QkrnH9-2026-10-26 01:00 `prob_dist(normalise=False)` read by `distributions`, so a diagram that is not a channel fails `assert_compatible`
