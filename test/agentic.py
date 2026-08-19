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
