# TODO

> i want to introduce static typing or at least some typing on morphism dom
> and cod, the purpose is to use them later on claude/proof-search-on-serde
> which for now makes use of unorthodox metaprogramming to interpret python
> annotations as sequent patterns to implement a systematic search strategy
> for free diagrams in any monoidal doctrine. however, this is using hacks
> and heavy metaprogramming i want to clean up. a byproduct of these sequent
> patterns is that they also encode the precise typing of generators, rules
> and axioms, so they also have the potential of eliminating a lot of manual
> `assert_iscomposable` or `assert_isparallel`, etc... by having a single
> mechanism for sequent matching with metavariables.
> [sketch of TwoCategory, TracedCategory, RigidCategory signatures]
> I am wondering whether we could make something compatible with
> typecheckers using typing.Annotated to emulate more properly the
> higher-kindedness of morphism types like `C1[X, Y]`. if not possible, the
> typecheckers need not to detect coherence violations statically, it would
> already be a win if the check was dynamically introduced by one of the
> decorators but at try to remove a bunch of manually inserted checks.
> on the other hand, i've been working on another branch
> claude/nifty-cray-b7mtqd which might also help with the typing of
> factories, the module gives away its responsibility to define its
> factories/generators to the Diagram class, i.e. instead of defining
> `Diagram.swap_factory = Swap` we now do `Swap = Diagram.Swap` but in any
> case every subclass of Diagram will generate its own Swap class,
> systematically.
> can you investigate both of these branch and come up with a radically new
> way to type discopy?
> without importing all the property testing work from the branch, your
> typing proposal should be compatible with this sequent with metavariable
> idea to represent generator/rule/axiom signatures. if necessary, create
> another branch off this one with both claude/proof-search-on-serde and
> claude/nifty-cray-b7mtqd merged and unified, then remove all hacks by
> using advanced python typing techniques that typecheckers like ty
> actually handle.

- [ ] Validate the design against ty: `Annotated[C1, dom, cod]` with
      metavariables as pattern objects in the metadata, statically the
      coarse `C1` typing, at runtime the sequent
- [ ] Merge `claude/proof-search-on-serde` into this branch and resolve
- [ ] Unify with `claude/nifty-cray-b7mtqd`: take the `Generator`
      descriptor mechanism so factories are typed nested classes
- [ ] Replace the eval-in-shadow-scope front end of `axioms` with the
      `Annotated` spelling: `annotated`, `metavariables`, `rule`,
      `generator` read type-parameter-faithful scopes, no `Level`
      impersonation of `C0`/`C1`/`C2`
- [ ] Respell the declarations of `abc` (and the modules that declare
      rules) in the statically-valid form
- [ ] Let sequent matching replace manual assertions where a generator
      declares its shape
- [ ] `ty check` green, `pflake8`, full pytest, CHANGELOG, report
