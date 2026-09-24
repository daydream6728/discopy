# FIBO fixtures

The import closure, within FIBO itself, of the four modules of
`BE/OwnershipAndControl` -- `OwnershipParties`, `ControlParties`,
`CorporateControl` and `CorporateOwnership` -- together with those of
`FBC/FinancialInstruments`, which brings the instrument vocabulary (securities
and their kinds, derivatives, options and futures, debt, credit agreements and
facilities, collateral, positions and exposure), and of `IND/Indicators`, which
brings what a quoted price, an end-of-day market rate and a volatility are,
and with them FIBO's statistics module `FND/Utilities/Analytics`. 42 files
copied verbatim from
[edmcouncil/fibo](https://github.com/edmcouncil/fibo) (`master`, September
2026), where the Financial Industry Business Ontology is published under the
[MIT License](https://github.com/edmcouncil/fibo/blob/master/LICENSE).

The canonical IRIs live at <https://spec.edmcouncil.org/fibo/ontology/>;
`discopy.owl.load` reads this directory instead when given its path, so the
tests and the notebook never touch the network. `discopy/FXRisk.rdf` is the
one file here that FIBO does not publish: an ontology whose whole content is
the import list the FX risk notebook loads, the way FIBO's own
`AboutFIBOProd.rdf` assembles a set of modules. Loading a published module
that imports both of the ones it needs would drag in vocabularies nothing
types a wire by, and every class of those is one more the reasoner carries
through every retrieval.

The modules also import the
[OMG Commons Ontology Library](https://www.omg.org/spec/Commons/), which OMG
serves from `www.omg.org` only: those imports are not copied here and
`discopy.owl.preload` stubs them as empty ontologies, which loses nothing the
tests rely on -- annotation properties and upper-level parents -- except for
the four minimal stand-ins under `Commons/`: the two datatypes the fixtures
range over, read as their closest OWL 2 datatype so that HermiT accepts
them, the date vocabulary those fixtures relate to one of them --
`ExplicitDate`, `hasObservedDateTime`, `hasDate` -- the collection
membership properties that make a `Portfolio`'s holdings queryable, and the
quantity vocabulary the fixtures state their own classes in terms of, so
that a monetary amount is read as the scalar quantity value FIBO says it is
and a statistic as a measure. A restriction on a Commons class that no
stand-in declares is dropped by the `owlapi` parser, which says so on the
standard error; the rule it belongs to is then one rule fewer, not a wrong
one.

A file that is not well-formed XML is skipped by `owlapi`'s IRI mapper
without a word and its import stubbed empty, which is indistinguishable from
not being here at all -- an `--` inside an XML comment is enough, and is how
the date stand-in went unread for as long as it did. `test/owl.py` parses
every file here to keep that from happening again.
