# TODO

> my comment wasn't specific to finset.Function, but inherited rules
> in general. consider markov.Diagram.copy which doesn't annotate its
> parameters with a pattern. this `concluding` mechanism seems to be
> doing sketchy stuff that are hard to reason about. It should be as
> simple as that: markov.Diagram defines a copy rule, so d.copy
> should be markov.Diagram.copy, not abc.MarkovCategory.copy. if that
> implies re-annotating rules every time they are overridden, then so
> be it. simpify the mechanism as much as possible, remove all hacky
> if statements in declaration and pattern handling and make it as
> straightforward as possible

- [x] Remove `concluding` and the sequent fallback: `declarations`
      binds the latest rule in the MRO like ordinary Python attribute
      lookup, every rule parses its own signature
- [x] Re-annotate every overriding rule with its full sequent, a
      premise being a parameter that states a pattern whether or not
      it has a default
- [WIP] @session_01UrSNrBcfEnb46fFG9LYRPo-2026-09-28 Validate: ruff,
      ty, pytest, fast + dev matrix, benchmark spot check, CHANGELOG,
      close
