# TODO

cubic's review of this pull request, 2026-10-19, quoted:

> **1 issue found** across 7 files
> - CHANGELOG.md:1228 — P3: The "any dtype but `complex`" description is inaccurate: explicit built-in dtypes such as `int`, `float`, and `bool` already round-tripped through the old builtins-only resolver, while NumPy-inferred names such as `float64` were the failing case. [...]

- [ ] `CHANGELOG.md`: a dtype NumPy names, not every dtype but `complex`
