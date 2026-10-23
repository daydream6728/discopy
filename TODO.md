> Go through all the bugs that are reported in discopy-next issues (especially the ones in the full readings of the codebase e.g. https://github.com/rel-int/discopy-next/issues/31) and spawn subagents to fix all of the ones that don't require any design decisions from my side.

- [ ] #142: recognise the identity, per https://github.com/rel-int/discopy-next/issues/142#issuecomment-6349440334: `Functor.id` is built from one shared function and `then` drops an identity on either side, so both unit laws hold
