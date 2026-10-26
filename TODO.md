> P2: `Noise(x, -1)` is now silently accepted because `x ** -1` produces an empty domain and `if self.dom` passes. Validate the normalized count before constructing the box so negative counts still raise `ValueError`.
>
> P2: `Discard(x, -1)` is now silently accepted because `x ** -1` produces an empty codomain and `if self.cod` passes. Validate the normalized count before constructing the box so negative counts still raise `ValueError`.

(cubic-dev-ai, on comarkov.py:477 and markov.py:695)

- [ ] `Copy`, `Discard`, `Merge` and `Noise` raise `ValueError` on a negative count, tested
