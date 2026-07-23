# TODO

> Fix issue https://github.com/discopy/discopy/issues/461

- [ ] Factor the Graphviz DOT helpers of `CMap.to_dot` and the rendering
  logic of `CMap.draw` into a shared module `discopy.drawing.dot`.
- [ ] Add `Hypergraph.to_dot` with HTML-table nodes for boundaries and boxes
  (distinguished ports) and a second node style for spiders where all wires
  meet at one position, incident from the top for spider inputs and from the
  bottom for spider outputs.
- [ ] Replace the networkx spring-layout `Hypergraph.draw` with Graphviz
  rendering so the docs images are deterministic SVGs.
- [ ] Add docs and doctests, regenerate `docs/_static/hypergraph` images.
- [ ] Run `uv run pflake8 discopy` and `uv run coverage run -m pytest`.
