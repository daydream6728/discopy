import operator
import pytest
from pytest import mark

torch = pytest.importorskip("torch")
import torch.nn as nn

from discopy.markov import Diagram, Hypergraph
from discopy.pytorch import from_torch, C, P, T, Add, Copy, InitParam, Linear, Placeholder, Swap


# --- Models for Testing ---
class Identity(nn.Module):
    def forward(self, x):
        return x

class ResidualBlock(nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = nn.Linear(128, 128)

    def forward(self, x):
        return operator.add(x, self.linear(x))

class SimpleMHA(nn.Module):
    def __init__(self):
        super().__init__()
        self.attention = nn.MultiheadAttention(embed_dim=256, num_heads=8)

    def forward(self, query, key, value):
        return self.attention(query, key, value)[0]


# --- Tests ---
def test_from_torch_identity():
    """Test a pure pass-through model."""
    diagram = from_torch(Identity(), as_hypergraph=False)
    assert isinstance(diagram, Diagram)
    assert len(diagram.boxes) == 1

def test_from_torch_attention():
    """Test multiple inputs and shared parameter generation."""
    diagram = from_torch(SimpleMHA(), as_hypergraph=False)
    assert isinstance(diagram, Diagram)
    assert len(diagram.boxes) > 0
    assert diagram.dom.name == "C"

def test_from_torch_hypergraph_direct():
    """Verify hypergraph generation with no simplification works."""
    hypergraph = from_torch(ResidualBlock(), as_hypergraph=True, simplify=False)
    assert isinstance(hypergraph, Hypergraph)
    assert len(hypergraph.boxes) > 0

def test_from_torch_hypergraph_simplify():
    """
    Verify that the hypergraph is correctly simplified.

    This also actss as a regression test, as hypergraph simplification was found to
    loop indefinitely in this situation.
    """
    hypergraph = from_torch(ResidualBlock(), as_hypergraph=True)
    assert hypergraph.to_diagram() == Copy(C) >> (Placeholder('x') @ C) >> (Copy(T) @ C) >> (T @ T @ InitParam('param_linear')) >> (T @ Swap(T, P)) >> (Linear('linear') @ T) >> Swap(T, T) >> Add('add')
