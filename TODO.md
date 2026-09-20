# TODO

> i don't want any eval or parsing, is it possible to make Pattern
> inherit from type or even from Annotated in such a way that the only
> parsing required is only shallow and collects a signature as a whole
> from annotations without ever having to transform the types into
> patterns or cheating by evaluating in a ad hoc environment?

> yes, respell it this way

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-20 02:10 Inventory
      every parsed declaration and quoted pattern, and the modules whose
      annotations must become eager
- [ ] Respell `discopy/pattern.py`: patterns built by `__class_getitem__`
      at annotation evaluation, `parse` a shallow walk of
      `__annotations__`, `__type_params__`, `__bound__`, `__metadata__`
      and `__args__` — no `read`, no environment, no quoted operators
- [ ] Respell `discopy/abc.py` and the other declaring modules with
      eager annotations and subscripted pattern classes
- [ ] `ty check` green, `pflake8`, pytest, proptest fast profile,
      CHANGELOG
