import numpy as np
from hypothesis import given, settings, strategies as st
from pytest import raises

from discopy import symmetric
from discopy.ehypergraph import EHypergraph, Markov
from discopy.hypergraph import Hypergraph
from discopy.markov import Ty, Box, Copy, Diagram, Functor
from discopy.tensor import Dim, Tensor
from discopy.utils import AxiomError

x = Ty('x')
f, g = Box('f', x, x), Box('g', x, x)
sample = Box('sample', x, x, is_deterministic=False)
condition = Box('condition', x, Ty(), is_affine=False)
score = Box('score', x, Ty(), is_deterministic=False, is_affine=False)


def test_samples_are_independent():
    assert len(set(Markov.from_diagram(Copy(x) >> f @ f).classes)) == 2
    assert len(set(Markov.from_diagram(Copy(x) >> f @ g).classes)) == 3
    assert len(set(Markov.from_diagram(
        Copy(x) >> sample @ sample).classes)) == 3
    graph = Markov.from_diagram(sample)
    assert len(graph.add(sample, (0, ))[0].graph.boxes) == 2
    assert Markov.from_diagram(f).add(f, (0, ))[1] == (1, )


def test_category_has_flags():
    with raises(AxiomError):
        EHypergraph[symmetric.Diagram].from_diagram(symmetric.Box('f', x, x))


def test_effects_are_kept():
    hard = Markov.from_diagram(Copy(x, 3) >> condition @ condition @ x)
    assert hard.roots() == (0, ) and hard.extract().boxes == (condition, )
    soft = Markov.from_diagram(Copy(x, 3) >> score @ score @ x)
    assert soft.roots() == (0, 1) and soft.extract().boxes == (score, score)
    unread = Markov.from_diagram(f >> condition)
    assert unread.extract().boxes == (f, condition) and unread.cost() == 3
    assert Markov.from_diagram(f >> Diagram.discard(x)).extract().boxes == ()


def test_rewrite_refusals():
    graph = Markov.from_diagram(sample >> f)
    merge = Hypergraph[Diagram](x @ x, x, (), ((0, 0), (), (0, )))
    cyclic = Markov.from_diagram(f).merge(0, 1)
    with raises(AxiomError):
        cyclic.rewrite((0, ), (), (1, ), Box('c', Ty(), x).to_hypergraph())
    for region, dom, cod, rhs in [
            ((0, ), (0, ), (1, ), f.to_hypergraph()),
            ((1, ), (1, ), (2, ), sample.to_hypergraph()),
            ((1, ), (0, ), (2, ), g.to_hypergraph()),
            ((1, ), (1, ), (2, ), Box('h', x @ x, x).to_hypergraph()),
            ((1, ), (1, 1), (2, ), merge)]:
        with raises(AxiomError):
            graph.rewrite(region, dom, cod, rhs)


def test_rewrite_glues():
    graph = Markov.from_diagram(f >> g)
    rewritten = graph.rewrite(
        (0, 1), (0, ), (2, ), Diagram.id(x).to_hypergraph())
    assert len(rewritten.graph.boxes) == 2 and rewritten.classes == (0, 1, 0)
    assert rewritten.extract() == Diagram.id(x).to_hypergraph()
    assert len(rewritten.sections()) == 1


def find(alike: dict, box: Box) -> Box:
    """ The representative of a box, as the union-find ``alike`` says. """
    while box in alike:
        box = alike[box]
    return box


def model(seed: int, alike: dict) -> Functor:
    """
    A random functor into tensors with a dimension two for each wire, which
    interprets two boxes alike when ``alike`` relates them: a deterministic
    box is a function, partial when it is not affine, any other a random
    matrix, stochastic when affine.
    """
    rng, table = np.random.default_rng(seed), {}

    def array(box):
        rows, columns = 2 ** len(box.dom), 2 ** len(box.cod)
        if box.is_deterministic:
            return np.eye(columns)[rng.integers(columns, size=rows)] * (
                1 if box.is_affine else rng.integers(2, size=(rows, 1)))
        matrix = rng.random((rows, columns))
        return matrix / matrix.sum(axis=1, keepdims=True)\
            if box.is_affine else matrix

    def ar_map(box):
        return Tensor[float](
            table.setdefault(find(alike, box), array(box)),
            Dim(*len(box.dom) * (2, )), Dim(*len(box.cod) * (2, )))

    return Functor(ob_map=lambda _: Dim(2), ar_map=ar_map, cod=Tensor[float])


@settings(max_examples=50, deadline=None)
@given(st.data())
def test_sections_evaluate_as_the_diagram(data):
    diagram = data.draw(Markov.strategy(
        effects=True, max_merges=0)).graph.to_diagram()
    if data.draw(st.booleans()):
        diagram = Diagram.copy(diagram.dom) >> diagram @ diagram
    graph = Markov(Hypergraph[Diagram].from_diagram(diagram))
    boxes, rewritten, alike = graph.graph.boxes, graph, {}
    pairs = st.tuples(st.integers(0, 9), st.integers(0, 9))
    for i, j in data.draw(st.lists(pairs, max_size=3)) if boxes else ():
        i, j = i % len(boxes), j % len(boxes)
        if boxes[i].is_cartesian and boxes[j].is_cartesian and (
                boxes[i].dom, boxes[i].cod) == (boxes[j].dom, boxes[j].cod):
            rewritten = rewritten.rewrite(
                (i, ), *graph.graph.box_wires[i], boxes[j].to_hypergraph())
            if find(alike, boxes[i]) != find(alike, boxes[j]):
                alike[find(alike, boxes[i])] = find(alike, boxes[j])
    functor = model(data.draw(st.integers(0, 2 ** 32 - 1)), alike)
    expected = functor(diagram).array
    for section in rewritten.rebuild().sections():
        assert np.allclose(functor(section.to_diagram()).array, expected)
