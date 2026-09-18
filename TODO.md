# TODO

> * fix the ty_factory one too
> * why do these quantum/tk.py methods even need those extra parameters? can't we just use e.g. cls.Box instead of box_factory=symmetric.Box?
> * don't implement anything yet on that front, but once you're done with the fix and the question above, also investigate how we could automate the implementation of Functor.__call__, by having an automatic way to map one generator from the functor's domain category to the same generator on the codomain category

- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-19 15:05 `docs/notebooks/diagrams.md` sets `ty_factory`, which is not an
      attribute: the objects of a category are its `ob`.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-19 15:05 `quantum/tk.py`'s `unit_factory` is a pytket register, not one of
      ours; `stream.Stream.sequence`'s `box_factory` is ours and should
      read `cls.category.Box`.
- [WIP] @session_01S8HY2Chfnczvn5kcoTY9wE-2026-09-19 15:05 Investigate automating `Functor.__call__` over the generators.
      Design only, no implementation.
