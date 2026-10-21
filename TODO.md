> Let's take care of the rich display PR now that Alessandro resigned https://github.com/discopy/discopy/pull/466

(toumix, live, 2026-10-21; ported here rather than finished upstream, toumix's answer to the question.)

- [x] merge discopy/discopy#466's head into this branch, conflicts resolved, `uv.lock` regenerated
- [ ] no widget cache on the diagram: it never hit (`hasattr(self, "__widget_cache")` is name-mangled away) and stored a widget in `__dict__`, so a displayed diagram no longer pickled (toumix's and the style review's `cached_property` threads)
- [ ] `_repr_mimebundle_` without `anywidget` installed: the SVG and the PNG, where it raised `ImportError`; with it, the widget view only, not the widget's `text/plain`
- [ ] `discopy.drawing.widget` imports `anywidget` like `neural.torch` imports `torch`, with no stub class, and is not imported by `discopy.drawing`; `DiagramWidget` has a docstring
- [ ] tested examples (toumix's thread): `to_widget`'s doctest checks `widget.svg` under `+EXTRA`
- [ ] answer the `to_svg` vs `draw` thread
- [ ] lint, tests, CHANGELOG
