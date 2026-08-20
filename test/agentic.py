# -*- coding: utf-8 -*-

import sys
from types import SimpleNamespace as N

from pytest import raises

from discopy import markov, rigid, symmetric
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


def test_from_layers_identity_step():
    layers = [[step("", ["x"], ["z"], "mix"), step("", ["y"], ["y"])],
              [step("", ["z"], ["y"], "ice"), step("", ["y"], ["x"], "back")]]
    assert D.from_layers(x @ y, layers, [mix, ice, back])\
        == D.lift(mix) @ y >> D.lift(ice) @ D.lift(back)


def test_from_layers_does_not_compose():
    with raises(AxiomError):
        D.from_layers(x, [[step("", ["y"], ["x"], "back")]], [back])


def stub(answers):
    """ A client answering one list of layers per task, recording calls. """
    calls = []

    def create(**params):
        calls.append(params)
        task = params["messages"][0]["content"].splitlines()[0]
        return N(content=[N(type="text"), N(
            type="tool_use", input={"layers": answers[task]})])
    return N(messages=N(create=create), calls=calls)


def test_question():
    assert P("do it", x, y).question([mix]) == (
        "Task: do it\nTypes: ['x'] -> ['y']\nTool mix: ['x'] -> ['z']")


def test_query():
    layers = [[step("", ["x"], ["z"], "mix")]]
    client = stub({"Task: do it": layers})
    assert P("do it", x, y).query([mix], client=client) == layers
    params, = client.calls
    assert params["tool_choice"] == {"type": "tool", "name": "refine"}
    assert params["model"] == P.model and params["tools"] == [P.schema]


def test_query_no_refinement():
    client = N(messages=N(create=lambda **params: N(content=[N(
        type="text")])))
    with raises(ValueError):
        P("do it", x, y).query(client=client)


def test_query_default_client(monkeypatch):
    layers = [[step("", ["x"], ["z"], "mix")]]
    client = stub({"Task: do it": layers})
    monkeypatch.setitem(sys.modules, "anthropic", N(Anthropic=lambda: client))
    assert P("do it", x, z).query([mix]) == layers


def test_refine():
    client = stub({"Task: do it": [
        [step("", ["x"], ["z"], "mix")], [step("finish", ["z"], ["y"])]]})
    assert P("do it", x, y).refine([mix], client=client)\
        == D.lift(mix) >> P("finish", z, y)


def test_refine_wrong_cod():
    client = stub({"Task: do it": [[step("", ["x"], ["z"], "mix")]]})
    with raises(AxiomError):
        P("do it", x, y).refine([mix], client=client)


def test_diagram_refine_is_parallel():
    p, q = P("do it", x, y), P("do it again", y, x)
    diagram = p >> q >> P("do it", x, y)
    client = stub({
        "Task: do it": [[step("", ["x"], ["z"], "mix")],
                        [step("finish", ["z"], ["y"])]],
        "Task: do it again": [[step("", ["y"], ["x"], "back")]]})
    image = diagram.refine(tools=[mix, back], client=client)
    assert len(client.calls) == 2  # one call per prompt up to repetition
    assert image.prompts == [P("finish", z, y)]
    assert D.lift(mix).refine() == D.lift(mix)  # no prompt, no call


def test_plan():
    diagram = P("do it", x, y) >> P("do it again", y, x)
    client = stub({
        "Task: do it": [[step("", ["x"], ["z"], "mix")],
                        [step("", ["z"], ["y"], "ice")]],
        "Task: do it again": [[step("", ["y"], ["x"], "back")]]})
    result = diagram.plan(tools=[mix, ice, back], client=client)
    assert type(result) is symmetric.Diagram
    assert result == mix >> ice >> back


def test_plan_did_not_end():
    client = stub({"Task: do it": [[step("do it", ["x"], ["y"])]]})
    with raises(AxiomError):
        P("do it", x, y).plan(max_rounds=3, tools=[], client=client)
    assert len(client.calls) == 3


M = Agentic[markov.Diagram]
a, b = markov.Ty("a"), markov.Ty("b")
f, copy = markov.Box("f", a, b), markov.Copy(a)


def test_lift_structure():
    assert issubclass(M.copy_factory, markov.Copy) and issubclass(M.copy_factory, M)
    assert isinstance(M.copy(a, 3), M) and isinstance(M.swap(a, b), M)
    assert M.braid_factory is M.swap_factory  # still reads swap_factory
    assert not issubclass(M.layer_factory, M)  # a layer is not a diagram


def test_plan_with_plumbing():
    """ Refining a diagram with a copy in it, i.e. what needs the lifting. """
    client = stub({
        "Task: do it twice": [
            [step("", ["a"], ["a", "a"], "Copy(a)")],
            [step("both of them", ["a", "a"], ["b", "b"])]],
        "Task: both of them": [
            [step("", ["a"], ["b"], "f"), step("", ["a"], ["b"], "f")]]})
    task = Prompt[markov.Diagram]("do it twice", a, b @ b)
    halfway = task.refine(tools=[f, copy], client=client)
    assert isinstance(halfway.boxes[0], markov.Copy)
    assert halfway.prompts == [Prompt[markov.Diagram]("both of them", a @ a, b @ b)]
    plan = task.plan(tools=[f, copy], client=client)  # refines past the copy
    assert type(plan) is markov.Diagram and plan == copy >> f @ f
    assert {type(box) for box in plan.boxes} == {markov.Box, markov.Copy}
