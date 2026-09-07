# TODO

> this task is about typechecking discopy using the ty typechecker
> do a first pass over the codebase and start annotating every function
> ignore some of the diagnostics when typechecking would require a substantial architectural change
> work until `ty check` succeeds then report and classify these problems along with a potential solution

- [ ] Install `ty` and get a baseline of diagnostics on `discopy/`
- [ ] Configure `ty` in `pyproject.toml` (paths, rules)
- [ ] First pass: add type annotations to functions across the codebase
- [ ] Suppress (with `# ty: ignore` or rule config) diagnostics that would need substantial architectural change
- [ ] Get `ty check` to succeed
- [ ] Report and classify the ignored problems along with potential solutions
- [ ] Run `pflake8 discopy` and `coverage run -m pytest`, update CHANGELOG.md
