# Review round: cubic on ffbaebe2

> P2 (discopy/utils.py:625): Malformed ndarray shapes can make `loads` raise after passing the product check. Catch `ValueError` and `OverflowError` around array construction and reshaping, then return `tree` for shapes NumPy cannot represent.

- [ ] `decode_numpy` leaves alone a shape numpy refuses, e.g. `[0, 10 ** 30]`
