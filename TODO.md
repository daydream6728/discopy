# TODO

PLEASE IMPLEMENT THIS PLAN:
# Unified Drawing API with `Graphviz(Backend)`

## Summary

Add `Graphviz(Backend)` beside `TikZ` and `Matplotlib`. Allocate every DOT node identifier before rendering, including identifiers shared across composition boundaries. Tensor and composition then only concatenate graph content; no variable unification, substitution, or public DOT data model is needed.

Use the Python `graphviz` package to construct nodes, edges, attributes, and subgraphs and to obtain DOT or rendered bytes.

## Public API

Export:

```python
BackendName = Literal["tikz", "matplotlib", "graphviz"]
OutputFormat = Literal["tex", "png", "svg", "dot"]
```

Use the common static drawing signature:

```python
draw(
    path: str | os.PathLike[str] | None = None,
    *,
    backend: BackendName | None = None,
    format: OutputFormat | None = None,
    show: bool | None = None,
    compare: bool = False,
    tol: float = 0,
    **backend_params,
) -> str | None
```

| Backend | Inputs | Formats |
|---|---|---|
| Matplotlib | Diagram/Drawing/Equation | `png`, `svg` |
| TikZ | Diagram/Drawing/Equation | `tex` |
| Graphviz | Diagram/Drawing/Equation, CMap, Hypergraph | `dot`, `png`, `svg` |

- Infer `.tex` as TikZ and `.dot` as Graphviz. Ambiguous `.png`/`.svg` defaults to Matplotlib for plane drawings and Graphviz for CMap/Hypergraph.
- Pathless Matplotlib displays, pathless TikZ returns TeX, and pathless Graphviz returns DOT.
- Only Matplotlib accepts `show=True`.
- Remove `to_tikz` and migrate primary `.tikz` outputs to `.tex`, retaining optional `<stem>.tikzstyles`.
- Leave `to_gif` and PennyLane’s specialized drawer unchanged.

## Implementation Changes

- Add `graphviz>=0.21` as a core dependency and update the lockfile. Keep the system Graphviz executable as an external runtime requirement for PNG/SVG rendering.
- Extend `Backend` with an overridable graph-level rendering entry point:
  - Matplotlib and TikZ retain the existing primitive drawing sequence.
  - `Graphviz` overrides it and builds a `graphviz.Graph` directly.
- Implement `Graphviz(Backend)` with:
  - an internal `graphviz.Graph`;
  - ordered input/output node-name metadata;
  - an optional sparse position mapping;
  - `id`, `from_box`, `tensor`, `then`, `to_dot`, and `output` helpers.
- Allocate names in a deterministic prepass:
  - Diagram: enumerate boundaries, layers, boxes, and ports, assigning the same name to both sides of every composed wire.
  - Drawing: enumerate its existing nodes and edges.
  - CMap/Hypergraph: derive names from stable port, box, spider, and loop indices.
  - Tensor occurrences receive distinct names during the prepass; composition boundaries intentionally receive identical names.
- Define the DOT algebra:
  - `tensor` adds both operands as anonymous subgraphs and concatenates their boundary metadata.
  - `then` verifies corresponding output/input names are already identical, adds both graph bodies, and retains only the external boundaries.
  - No renaming or variable substitution occurs inside either operation.
- Use `Graph.node()`, `Graph.edge()`, `Graph.attr()`, and `Graph.subgraph()` rather than hand-building DOT strings. Use `.source` for DOT and `.pipe(format=..., engine=...)` for PNG/SVG bytes; these are supported by the package’s public API. [Python graphviz API](https://graphviz.readthedocs.io/en/stable/api.html)
- Omit `pos` attributes by default so Graphviz computes the layout. When explicit positions are supplied, add them as DOT position hints without requiring positions for every node.
- Preserve Graphviz-specific options including `engine`, `seed`, `graph_attr`, and `port_indices`.
- Refactor CMap and Hypergraph output through `Graphviz`:
  - emit existing HTML boundary and box labels through the package API;
  - connect known port/spider identifiers directly;
  - retain scalar loops and parallel edges;
  - remove direct subprocess and handwritten escaping logic.
- Add a shared output coordinator for format validation, source returns, saving, and comparison:
  - create a missing baseline;
  - otherwise render temporarily without modifying it;
  - compare TeX/SVG/DOT and TikZ companions byte-for-byte;
  - compare PNG pixels by RMS using `tol`;
  - reject comparison without a path, negative tolerance, and nonzero tolerance for non-PNG output.
- Reuse the useful comparison and Graphviz layout work from `e4ed8612` and `acfef5ad`, replacing their handwritten DOT/subprocess paths with `Graphviz(Backend)`.

## Test Plan

- Test deterministic preallocation for identities, sequential composition, tensor products, equations, CMaps, and Hypergraphs.
- Verify tensor concatenates two anonymous subgraphs without collisions.
- Verify composition requires matching preassigned boundary names and performs no rewriting.
- Test DOT construction through package methods, stable `.source`, and PNG/SVG `.pipe()` output.
- Cover absent, partial, and complete position mappings, including successful automatic layout with no positions.
- Test all backend/format inference and rejection cases, pathless source output, `show` restrictions, `PathLike` paths, and missing Graphviz executable errors.
- Test baseline creation, exact source/vector comparison, TikZ companions, PNG tolerance, mismatch preservation, and temporary cleanup.
- Migrate TikZ baselines to `.tex`, regenerate affected Graphviz SVGs, update docs/doctests, then run `pflake8` and the full coverage suite.

## Assumptions

- `Graphviz` is the only new public backend class; no public variable or DOT AST classes are added.
- Globally unique and intentionally shared node identifiers are established before fragment construction.
- Matplotlib/TikZ remain unsupported for CMap and Hypergraph.
- Positions are optional rendering hints; automatic Graphviz layout is the default.
- Implementation follows the repository’s `TODO.md` mutex protocol.

- [WIP] @019f8fa6-06a2-76d0-9beb-5590ad8fc3c7-2026-07-23 18:44 Implement the unified drawing API and Graphviz backend.
- [ ] Add and migrate tests, baselines, and documentation.
- [ ] Run lint and the full coverage suite.
