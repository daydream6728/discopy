> Implement double-pushout rewriting for discopy.hypergraph following the theory from Bonchi et al.  using Lafont's interaction combinators as a test case.

(USER, live, 2026-10-22, attaching Bonchi et al., *String Diagram Rewrite Theory* I (2022) and II
(2021), and Lafont's Fig. 2, the interaction rules, and Fig. 11, a net reducing to a wiring.)

A `Hypergraph` is a cospan `dom -> G <- cod` of hypergraphs, so a rule `left => right` of two
parallel hypergraphs is the DPO span `left <- dom + cod -> right` (I, Remark 3.14). A match is a
hypergraph homomorphism `left -> G`, injective on boxes, with the gluing conditions: spiders merged
are interface spiders, and a spider deleted has no leg left outside the match, the boundary of `G`
included (I, Def. 3.16 and §3.4). A pushout complement is a context `C : left.cod @ G.dom ->
left.dom @ G.cod` such that plugging `left` into `C` gives `G` back; plugging `right` instead is the
rewrite. All pushout complements are enumerated (I, §4.5) over a hypergraph category; over any
other symmetric category, matches are convex and the context is the boundary complement, the unique
monogamous one (II, Defs. 23, 25, 26).

- [WIP] @session_01M8CWacKqbJVKPcDMd2m3AD-2026-10-22 15:10 `Hypergraph.match`: homomorphisms with the gluing conditions, convex for symmetric categories
- [ ] `Hypergraph.complements`: all pushout complements, the boundary complement for symmetric ones
- [ ] `Hypergraph.plug`, `rewrite`, `normalize`, `normal_form`
- [ ] interaction combinators: Lafont's six rules (Fig. 2) and the net of Fig. 11 normalising to a
  wiring, staying bijective at every step
- [ ] the examples of the papers: I, Ex. 3.21 with interface (17), and §4.5's five contexts; II,
  Ex. 4.1 (boundary complement) and Ex. 4.2 (non-convex match)
- [ ] docs: module summary, bibliography (part II, Lafont), `CHANGELOG.md`
- [ ] `pflake8`, `pylint` (raise `fail-under` if it rises), `coverage run -m pytest`
