# TODO

> i want to start extracting the DAG roots one by one as a separate PR, make me a plan to decide in which order to proceed.

> go with 1-fixes first, but keep 2-typing as one for now. the 1000 loc diff rule shouldn't be taken too literally.

- [x] cut the root `1-fixes` of the split of #1 off `main`: the bugs its property matrix found, each with its regression test
- [x] flake8, ruff, pylint, ty, the unit suite and the `pr` matrix on the node
- [ ] CI green on the pull request
- [ ] every review thread resolved or waiting on a human
