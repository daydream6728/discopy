# -*- coding: utf-8 -*-

from pytest import raises

from discopy import rigid, symmetric
from discopy.agentic import Agentic, Prompt
from discopy.utils import AxiomError

x, y, z = map(symmetric.Ty, "xyz")
D, P = Agentic[symmetric.Diagram], Prompt[symmetric.Diagram]
mix, ice, back = (symmetric.Box(name, dom, cod) for name, dom, cod in [
    ("mix", x, z), ("ice", z, y), ("back", y, x)])


def test_agentic():
    assert Agentic[symmetric.Diagram] is D
    assert issubclass(D, symmetric.Diagram) and P.factory is D
    assert Agentic[rigid.Diagram, rigid.Box] is not D


def test_lift_and_downgrade():
    assert type(D.lift(mix)) is D
    assert D.lift(mix).downgrade() == symmetric.Diagram(
        mix.inside, mix.dom, mix.cod)
    assert D.lift(mix).prompts == []
    with raises(AxiomError):
        P("do it", x, y).downgrade()


def test_prompts():
    p, q = P("do it", x, y), P("do it again", y, x)
    assert p.prompts == [p]
    assert (p >> q >> P("do it", x, y)).prompts == [p, q]


def test_rigid_prompt():
    p = Prompt[rigid.Diagram, rigid.Box]("say it", rigid.Ty('x'), rigid.Ty())
    assert p.l.z == -1 and p.r.z == 1


def step(text, dom, cod, tool=None):
    return {"text": text, "dom": dom, "cod": cod, "tool": tool}


def test_from_layers():
    layers = [[step("", ["x"], ["z"], "mix")], [step("finish", ["z"], ["y"])]]
    built = D.from_layers(x, layers, [mix])
    assert built == D.lift(mix) >> P("finish", z, y)
    assert isinstance(built, D) and built.prompts == [P("finish", z, y)]


def test_from_layers_parallel():
    layers = [[step("left", ["x"], ["z"]), step("right", ["y"], ["x"])]]
    assert D.from_layers(x @ y, layers)\
        == P("left", x, z) @ P("right", y, x)


def test_from_layers_does_not_compose():
    with raises(AxiomError):
        D.from_layers(x, [[step("", ["y"], ["x"], "back")]], [back])
