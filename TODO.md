# Review round: cubic on 8248fc19

> P2 (discopy/cat.py:1323): This makes serialization asymmetric: equations with non-string symbols still produce trees, but `loads(dumps(equation))` now raises `TypeError`. Validate symbols in `to_tree` before writing them, or accept every value that the encoder writes.
>
> P2 (discopy/utils.py:737): Malformed SymPy nodes with correctly typed arguments can still make `loads` raise; validate constructor arity or catch constructor errors and return the original tree.
>
> P2 (discopy/utils.py:726): `decode_sympy` accepts an impossible `sympy.Integer` shape containing `q` and decodes it as a Rational. Match the Integer and Rational factories to the exact field sets emitted by `encode_sympy`, leaving malformed nodes unchanged.

- [ ] `Equation.to_tree` raises on a symbol that is not a string
- [ ] `decode_sympy` leaves a function node alone when its constructor refuses the args
- [ ] `decode_sympy` reads `Integer` as `{factory, p}` and `Rational` as `{factory, p, q}` with `q > 1`
