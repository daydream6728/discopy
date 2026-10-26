> test that the two implementations coincide, make sure you use good ideas from both and then port the from_diagram method from optyx to discopy next

— toumix, https://github.com/rel-int/discopy-next/pull/334#issuecomment-6370416775

- [x] check that `quantum.contextuality` (#283) and `optyx.contextuality` coincide: https://github.com/rel-int/discopy-next/pull/334#issuecomment-6405389584
- [x] port `from_diagram` to `quantum.contextuality.Model`, with per-party settings in `Scenario.bell`
- [x] keep `Model.deterministic` and a violation of zero on noncontextual models
- [x] remove `optyx.contextuality` and its test, keep the coincidence cases as tests of the one module
- [ ] CHANGELOG, pflake8, pylint, pytest
