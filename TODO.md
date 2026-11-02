# Box 31 of #314: a feed-forward component applies its default action once per configuration

Autonomous 🌙 Evening round of 2026-11-02, under
[`daydream6728/desire`](https://github.com/daydream6728/desire)'s `EVENING.md`, step 5: *"in the
next repos, finish every item left"*, taking the next repo's bugs that need no decision. No human
prompt: the box is [#314](https://github.com/rel-int/discopy-next/issues/314)'s own, and perceval's
own semantics is its oracle.

> - [ ] in the feed-forward conversion, each configuration entry applies `default_action` when it
>   does not match, so the default is applied once per non-matching entry: with default
>   `PERM([1, 0])` and two identity configurations, `|1,1,0>` gives `(1,0,1)` in optyx and
>   `|1,1,0>` in perceval

- [ ] Reproduce it against this `main`, and find what makes it visible
- [ ] Exactly one action applies: the configuration's, or the default when none matches
- [ ] A test over a count of configurations that reads right as well as counts that read wrong
- [ ] `CHANGELOG.md`
- [ ] `pflake8`, `pylint`, `ruff`, `ty` and the optyx suite
