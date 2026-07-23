# TODO

> Fix issue https://github.com/discopy/discopy/issues/461

- [WIP] @cd8fa3-2026-07-23 10:45 Factor the Graphviz DOT helpers of `CMap.to_dot` and the rendering
  logic of `CMap.draw` into a shared module `discopy.drawing.dot`.
- [WIP] @cd8fa3-2026-07-23 10:45 Add `Hypergraph.to_dot` with HTML-table nodes for boundaries and boxes
  (distinguished ports) and a second node style for spiders where all wires
  meet at one position, incident from the top for spider inputs and from the
  bottom for spider outputs.
- [WIP] @cd8fa3-2026-07-23 10:45 Replace the networkx spring-layout `Hypergraph.draw` with Graphviz
  rendering so the docs images are deterministic SVGs.
- [WIP] @cd8fa3-2026-07-23 10:45 Add docs and doctests, regenerate `docs/_static/hypergraph` images.
- [WIP] @cd8fa3-2026-07-23 10:45 Run `uv run pflake8 discopy` and `uv run coverage run -m pytest`.
