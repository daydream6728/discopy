# FIBO fixtures

The import closure, within FIBO itself, of the four modules of
`BE/OwnershipAndControl` -- `OwnershipParties`, `ControlParties`,
`CorporateControl` and `CorporateOwnership` -- together with that of
`FBC/FinancialInstruments`, which brings the instrument vocabulary: securities
and their kinds, derivatives, options and futures, debt, credit agreements and
facilities, collateral, positions and exposure. 41 files copied verbatim from
[edmcouncil/fibo](https://github.com/edmcouncil/fibo) (`master`, September
2026), where the Financial Industry Business Ontology is published under the
[MIT License](https://github.com/edmcouncil/fibo/blob/master/LICENSE).

The canonical IRIs live at <https://spec.edmcouncil.org/fibo/ontology/>;
`discopy.owl.load` reads this directory instead when given its path, so the
tests and the notebook never touch the network. The modules also import the
[OMG Commons Ontology Library](https://www.omg.org/spec/Commons/), which OMG
serves from `www.omg.org` only: those imports are not copied here and
`discopy.owl.preload` stubs them as empty ontologies, which loses nothing the
tests rely on -- annotation properties and upper-level parents -- except for
the three minimal stand-ins under `Commons/`: the two datatypes the fixtures
range over, read as their closest OWL 2 datatype so that HermiT accepts
them, the date vocabulary those fixtures relate to one of them --
`ExplicitDate`, `hasObservedDateTime`, `hasDate` -- and the collection
membership properties that make a `Portfolio`'s holdings queryable. A
restriction on a Commons class that no stand-in declares is dropped by the
`owlapi` parser, which says so on the standard error; the rule it belongs to
is then one rule fewer, not a wrong one.
