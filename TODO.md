# Review round: cubic on 789b0629

> P2 (test/cat.py:646): This broad `AxiomError` catch can hide broken dagger implementations, because it treats every failure as an intentional no-dagger case. Restrict the exception handling to the explicitly listed no-dagger classes, or assert the expected exception for those classes separately.
>
> P2 (discopy/closed.py:511): Undelayed timed boxes cannot be rebuilt because `Timed.__init__` never initializes `_time_step` for zero. Initialize `_time_step` for every `Timed` instance; the same issue affects `Coeval` and `Curry`.
>
> P2 (discopy/tensor.py:1169): Monoidal functors still erase custom `tensor.Bubble.func`: this new equality key makes `F(bubble)` differ from `bubble` because `monoidal.Functor.__call__` rebuilds the bubble without passing `func=other.func`. Preserve the function when constructing the codomain bubble.

- [ ] `test_every_box` lists the boxes with no dagger by reason instead of catching `AxiomError`
- [ ] answer the `Timed` thread: `feedback.Box._time_step = 0` covers time step zero
- [ ] `monoidal.Functor` passes a bubble the fields its codomain bubble also declares, e.g. `tensor.Bubble.func`
