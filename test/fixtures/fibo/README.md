# FIBO fixtures

The import closure, within FIBO itself, of the four modules of
`BE/OwnershipAndControl` -- `OwnershipParties`, `ControlParties`,
`CorporateControl` and `CorporateOwnership` -- 29 files copied verbatim from
[edmcouncil/fibo](https://github.com/edmcouncil/fibo) (`master`, September
2026), where the Financial Industry Business Ontology is published under the
[MIT License](https://github.com/edmcouncil/fibo/blob/master/LICENSE).

The canonical IRIs live at <https://spec.edmcouncil.org/fibo/ontology/>;
`discopy.owl.load` reads this directory instead when given its path, so the
tests and the notebook never touch the network. The modules also import the
[OMG Commons Ontology Library](https://www.omg.org/spec/Commons/), which OMG
serves from `www.omg.org` only: those imports are not copied here and
`discopy.owl.preload` stubs them as empty ontologies, which loses nothing the
tests rely on -- annotation properties and upper-level parents.
