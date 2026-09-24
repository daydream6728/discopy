# TODO

> # Review of `claude/sequent-annotations`
>
> This branch is not ready to merge. The unit suite passes, but the
> full property matrix fails 31 cells. On top of that, every law
> marked as broken is never actually checked, and the new left-handed
> feedback has several confirmed bugs. [...] It should be split before
> anyone reviews it in depth. [...]
>
> Blocking
> 1. ~~Laws declared broken are never checked~~ its alright for now
> 2. Broken marks inherit too far down the hierarchy: braided's
>    `braid_naturality` reaches `symmetric` and below where the law
>    holds; traced's repr and serialisation marks switch them off for
>    every symmetric-level diagram; markov's real tree failure is
>    `Copy.__new__` rejecting `name`, recorded under the trace's
>    reason.
> 3. The 31 failing cells in the full matrix: `Ty.repr_transparency`
>    on rigid, pivotal, biclosed and pregroup (`rigid.Ty(dom=red,
>    cod=red)` prints as `rigid.Ty()`); Functor laws for tensor, hopf
>    and quantum.channel (relabelling targets frobenius.Ty even for a
>    Tensor codomain); `UnboundLocalError: 'layer'` at
>    monoidal.py:934 and `'Swap' object has no attribute 'is_mixed'`;
>    pickling of grammar.cfg.Algebra; ribbon.rotate_contravariance.
> 4. Left-handed Feedback bugs: left compares and hashes equal to
>    right; to_tree records neither left nor mem; feedback.Functor
>    passes left=True to Stream and para which raise TypeError;
>    feedback_left recurses on mem[1:] and raises AxiomError for
>    memories of length two or more.
>
> Should fix: parse should refuse a type variable outside the rule's
> parameters (KeyError at pattern.py:826); __str__ drops parentheses
> (`R[Tensor[A,B]]` prints `A @ B.r`); keyword-only premises applied
> positionally raise TypeError (search.py:93); the structure check
> skips bounded type parameters; Repeat breaks silently on a
> non-atomic base; Tensor[()] raises IndexError; a docstring promises
> `@` on patterns; Equivalence.dagger_involution is vacuous and
> Inverse defines __eq__ without __hash__.
>
> Minor: biclosed's failing reason cites #562 which is fixed;
> para.Closed.curry defaults left=False; cycle's misleading length
> error; undocumented renames (to_drawing functor=, quantum circuit
> exports); the fast profile claims the settings of dev but uses no
> database; style violations (nesting in generate, __post_init__
> pass, Rule.constant after the class, axioms.py telling readers to
> write laws into TODO.md).

- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-24 Run the full
      matrix under the dev profile on the current head to enumerate
      the failing cells as they stand
- [ ] Fix the left feedback: equality and hash read `left`, the tree
      records `left` and `mem`, the functor only passes `left` where
      the codomain takes it, and `feedback_left` handles memories of
      any length
- [ ] Stop the broken marks at the level they hold: re-enable
      `braid_naturality` on `symmetric`, declare markov's roundtrips
      under the copy's own reason
- [ ] Fix or classify every failing dev cell: the coloured empty
      `Ty` repr, the relabelling strategy on a non-endo functor,
      the `layer` UnboundLocalError and `Swap.is_mixed`,
      `grammar.cfg.Algebra` pickling, `ribbon.rotate_contravariance`
- [ ] The pattern and search fixes: refuse out-of-scope
      metavariables, parenthesise `__str__`, apply keyword-only
      premises by name, check the bounds of binders, reject
      `Tensor[()]` and a non-atomic `Repeat` base, drop the operator
      docstring
- [ ] `Equivalence.dagger_involution` declared by construction,
      `Inverse.__hash__`
- [ ] The minor round: the #562 reason, `para.Closed.curry` left
      default, the cycle error message, CHANGELOG entries for the
      renames, the fast-profile claim, the style violations
- [ ] `ty check`, `ruff check`, pytest, proptest fast + dev rerun of
      the fixed cells, CHANGELOG, close
