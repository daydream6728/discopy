import random

import numpy as np
import pytest

from discopy.quantum import graphlike as G
from discopy.quantum.zx import Z, X, H, Diagram


def circuit(qubits: int, depth: int, seed: int) -> list[Diagram]:
    """ The layers of a random circuit of Hadamards, CNOTs and Ts. """
    rng = random.Random(seed)
    layers = []
    for _ in range(depth):
        i = rng.randrange(qubits)
        gate = rng.choice(["H", "phase", "CNOT"]) if qubits > 1\
            else rng.choice(["H", "phase"])
        if gate == "H":
            layer = Diagram.id(i) @ H @ Diagram.id(qubits - i - 1)
        elif gate == "phase":
            phase = rng.randrange(1, 8) / 8
            layer = Diagram.id(i) @ Z(1, 1, phase)\
                @ Diagram.id(qubits - i - 1)
        else:
            i = rng.randrange(qubits - 1)
            layer = Diagram.id(i) @ (Z(1, 2) @ Diagram.id(1)
                                     >> Diagram.id(1) @ X(2, 1))\
                @ Diagram.id(qubits - i - 2)
        layers.append(layer)
    return layers


def matrix(layers: list[Diagram]) -> np.ndarray:
    """ The matrix of a circuit, the product of those of its layers. """
    size = 2 ** len(layers[0].dom)
    result = np.eye(size)
    for layer in layers:
        result = result @ np.asarray(layer.eval().array).reshape(size, size)
    return result


def tensor(graph) -> np.ndarray:
    """
    The tensor of a graph-like hypergraph, an index for each spider: a
    Hadamard is a matrix on two, a phase a vector on one, and a boundary
    port an identity to a fresh index.
    """
    spiders = graph.n_spiders
    operands = []
    for box, (dom, cod) in zip(graph.boxes, graph.box_wires):
        if box is H:
            operands += [np.array([[1, 1], [1, -1]]), list(dom + cod)]
        else:
            operands += [np.array([1, np.exp(2j * np.pi * box.phase)]),
                         list(dom)]
    ports = graph.dom_wires + graph.cod_wires
    for i, spider in enumerate(ports):
        operands += [np.eye(2), [spider, spiders + i]]
    for spider in range(spiders):
        operands += [np.ones(2), [spider]]
    return np.einsum(*operands, list(range(spiders, spiders + len(ports))),
                     optimize=True)


def proportional(left, right) -> bool:
    left, right = (np.asarray(x).flatten() for x in (left, right))
    k = np.argmax(abs(left))
    return abs(right[k]) > 1e-9 and np.allclose(
        left / left[k], right / right[k])


def checked(rules):
    """ The rules, each step checked as a match and as an equation. """
    def wrap(rule):
        def result(rewriter, spider):
            found = rule(rewriter, spider)
            if found is None:
                return None
            left, right, match = found
            spiders, boxes = match
            assert left.is_parallel(right)
            assert rewriter.glues(left, match)
            for i, j in enumerate(boxes):
                assert rewriter.boxes[j] == left.boxes[i]
                assert rewriter.box_wires[j] == tuple(tuple(
                    spiders[s] for s in wires)
                    for wires in left.box_wires[i])
            if len(left.dom) <= 12:
                assert proportional(tensor(left), tensor(right))
            return found
        return result
    return [([wrap(rule) for rule in level], anchors)
            for level, anchors in rules]


@pytest.mark.parametrize("seed", range(24))
def test_full_reduce_is_sound(seed):
    layers = circuit(2 + seed % 3, 8 + seed, seed)
    graph = G.from_diagram(Diagram.id(len(layers[0].dom)).then(*layers))
    assert proportional(tensor(graph), matrix(layers))
    rewriter = G.Simplifier(graph)
    G.reduce(rewriter, checked(G.RULES))
    result = rewriter.to_hypergraph()
    assert proportional(tensor(result), matrix(layers))
    rewriter = G.Simplifier(result)
    for level, _ in G.RULES:
        for rule in level:
            for spider in range(result.n_spiders):
                assert rule(rewriter, spider) is None


def test_full_reduce_example():
    diagram = Z(1, 1, .125) >> H >> H >> Z(1, 1, .125)
    assert str(G.full_reduce(G.from_diagram(diagram)))\
        == "Z(1, 2) >> Z(1, 0, 1/4) @ Nat(1)"


def test_from_diagram_errors():
    from discopy.quantum.zx import Y
    with pytest.raises(ValueError):
        G.from_diagram(Y(1, 1, .5))


@pytest.mark.parametrize("seed", range(6))
def test_pyzx(seed):
    zx = pytest.importorskip("pyzx")
    random.seed(seed)
    graph = zx.generate.CNOT_HAD_PHASE_circuit(4, 60).to_graph()
    ours = G.from_pyzx(graph)
    assert zx.compare_tensors(G.to_pyzx(ours), graph, preserve_scalar=False)
    result = G.full_reduce(ours)
    assert zx.compare_tensors(G.to_pyzx(result), graph, False)
    zx.full_reduce(graph)
    (spiders, _, tcount), (pyzx_spiders, _, pyzx_tcount) = (
        G.size(result), G.size(graph))
    assert tcount == pyzx_tcount and abs(spiders - pyzx_spiders) <= 1
