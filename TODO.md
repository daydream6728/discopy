# TODO

cubic's review of this pull request, 2026-10-19, quoted:

> **5 issues found** across 15 files
> - CHANGELOG.md:895 — P3: This release note incorrectly says every `tensor` is variadic, although several category implementations remain binary. [...]
> - CHANGELOG.md:910 — P3: The explanation of the unary call is mathematically inaccurate: `f.tensor()` is a singleton tensor, not an empty product. [...]
> - discopy/matrix.py:210 — P2: The PyTorch backend only accepts two operands in `torch.result_type`, so any n-ary tensor with two or more `others` raises `TypeError`; fold promotion pairwise through a backend-neutral helper.
> - discopy/matrix.py:346 — P1: This mutates the array returned by `cls.zero`, but JAX backend arrays are immutable, so n-ary `Matrix.tensor` raises instead of producing the block-diagonal matrix. [...]
> - discopy/symmetric.py:597 — P3: `Permutation.tensor` makes long plumbing runs quadratic by repeatedly calling `pop(0)`. [...]

- [ ] `Matrix.promote` folds `result_type` pairwise, which PyTorch takes two at a time, with a test
- [ ] `Matrix.tensor` concatenates its blocks rather than writing into an array, which JAX refuses, with a test
- [ ] `Permutation.tensor` walks its operands by index
- [ ] `CHANGELOG.md`: which `tensor`s, and the unary call
