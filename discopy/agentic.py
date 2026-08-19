# -*- coding: utf-8 -*-

"""
Diagrams with prompts as holes, i.e. planning as diagram refinement.

Given an underlying `category` C, an agentic diagram is a diagram in C where
some of the boxes are a :class:`Prompt`, i.e. a hole labelled by a task in
natural language. Thus :class:`Agentic` is the free C-category on the
prompts, it comes with:

* an inclusion :meth:`Diagram.lift` from C, i.e. any diagram is agentic,
* its partial inverse :meth:`Diagram.downgrade`, defined on the diagrams
  with no prompt left,
* a refinement :meth:`Prompt.refine`, which calls a large language model to
  replace one prompt by an agentic diagram of tools and finer prompts,
* its extension :meth:`Diagram.refine`, the functor which refines every
  prompt in parallel and is the identity on the boxes of C,
* the iteration :meth:`Diagram.plan`, which refines until no prompt is left
  then downgrades the result to C.

Refinement lands in `Agentic[C]` rather than in C so that a plan can be made
of subplans, i.e. it need not bottom out in one step. It bottoms out when the
model answers with `tools`, i.e. boxes of C.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Diagram
    Prompt
    Agentic

Example
-------

The tools are the boxes of the underlying category, here a recipe:

>>> from discopy.symmetric import Ty, Box, Diagram as D
>>> egg, flour, batter, cake = map(Ty, ("egg", "flour", "batter", "cake"))
>>> mix, bake = Box("mix", egg @ flour, batter), Box("bake", batter, cake)
>>> task = Prompt[D]("make a cake", egg @ flour, cake)

We stub the language model with a client answering a fixed list of layers,
so that this example stays offline and deterministic:

>>> from types import SimpleNamespace as N
>>> def stub(*answers):
...     answers = iter(answers)
...     create = lambda **params: N(content=[
...         N(type="tool_use", input={"layers": next(answers)})])
...     return N(messages=N(create=create))
>>> step = lambda text, dom, cod, tool=None: {
...     "text": text, "dom": dom, "cod": cod, "tool": tool}

The first answer refines the task into a prompt and a tool, the second one
refines the remaining prompt into a tool, so that the plan takes two rounds:

>>> client = stub(
...     [[step("mix the ingredients", ["egg", "flour"], ["batter"])],
...      [step("", ["batter"], ["cake"], "bake")]],
...     [[step("", ["egg", "flour"], ["batter"], "mix")]])
>>> plan = task.plan(tools=[mix, bake], client=client)
>>> assert plan == mix >> bake and isinstance(plan, D)

>>> from discopy.monoidal import Equation
>>> Equation(task, plan, symbol="$\\\\mapsto$").draw(
...     doctest="docs/_static/agentic/plan.svg")

.. image:: /_static/agentic/plan.svg
    :align: center
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from functools import reduce

from discopy import messages, monoidal
from discopy.utils import (
    AxiomError, assert_isinstance, factory, factory_name)


class Diagram:
    """
    The methods that :class:`Agentic` adds to the diagrams of an underlying
    `category`, i.e. the interface of the free category on the prompts.

    .. admonition:: Summary

        .. autosummary::

            prompts
            lift
            downgrade
            from_step
            from_layers
            refine
            plan
    """
    category = monoidal.Diagram
    prompt_factory = None

    @property
    def prompts(self) -> list[Prompt]:
        """ The prompts inside a diagram, without repetition. """
        return list(dict.fromkeys(
            box for box in self.boxes
            if isinstance(box, self.prompt_factory)))

    @classmethod
    def lift(cls, diagram: category) -> Diagram:
        """
        A diagram of the underlying category as an agentic diagram with no
        prompt, i.e. the inclusion functor.

        Parameters:
            diagram : The diagram to lift.
        """
        assert_isinstance(diagram, cls.category)
        return cls(diagram.inside, diagram.dom, diagram.cod)

    def downgrade(self) -> category:
        """
        An agentic diagram with no prompt as a diagram of the underlying
        category, i.e. the partial inverse of :meth:`lift`.

        Raises:
            AxiomError : Whenever there are prompts left to refine.
        """
        if self.prompts:
            raise AxiomError(messages.PROMPTS_TO_REFINE.format(self))
        return self.category(self.inside, self.dom, self.cod)

    @classmethod
    def from_step(cls, step: dict, toolbox: dict) -> Diagram:
        """
        One step of an answer as a box, i.e. a tool if it has a `"tool"` name
        in `toolbox` and a prompt with types `"dom"` and `"cod"` otherwise.

        Parameters:
            step : The step, i.e. its `"text"`, `"dom"`, `"cod"` and `"tool"`.
            toolbox : The tools available, indexed by name.
        """
        if step.get("tool"):
            return cls.lift(toolbox[step["tool"]])
        return cls.prompt_factory(
            step["text"], cls.ob(*step["dom"]), cls.ob(*step["cod"]))

    @classmethod
    def from_layers(cls, dom, layers: list[list[dict]], tools=()) -> Diagram:
        """
        The diagram with one layer of parallel steps for each answer layer,
        i.e. the inverse of :meth:`monoidal.Diagram.foliation`.

        Parameters:
            dom : The domain of the diagram.
            layers : The layers of steps, as answered by the model.
            tools : The boxes of the underlying category to choose from.

        Raises:
            AxiomError : Whenever two consecutive layers do not compose.
        """
        toolbox = {tool.name: tool for tool in tools}
        return reduce(lambda result, layer: result >> reduce(
            lambda f, g: f @ g,
            [cls.from_step(step, toolbox) for step in layer]),
            layers, cls.id(dom))

    def refine(self, **params) -> Diagram:
        """
        One round of refinement, i.e. the functor which sends every prompt to
        :meth:`Prompt.refine` and every other box to itself. The calls to the
        model are made in parallel, once for each prompt up to repetition.

        Parameters:
            params : Passed on to :meth:`Prompt.refine`.
        """
        prompts = self.prompts
        if not prompts:
            return self
        with ThreadPoolExecutor(len(prompts)) as executor:
            images = executor.map(
                lambda prompt: prompt.refine(**params), prompts)
        ar_map = dict(zip(prompts, images))
        return self.functor_factory(
            ob_map=lambda x: x, ar_map=lambda box: ar_map.get(box, box),
            dom=self.factory, cod=self.factory)(self)

    def plan(self, max_rounds: int = 8, **params) -> category:
        """
        Refine a diagram until there is no prompt left, then downgrade it to
        the underlying category.

        Parameters:
            max_rounds : The maximum number of rounds of refinement.
            params : Passed on to :meth:`refine`.

        Raises:
            AxiomError : Whenever there are prompts left after `max_rounds`.
        """
        diagram = self
        for _ in range(max_rounds):
            if not diagram.prompts:
                return diagram.downgrade()
            diagram = diagram.refine(**params)
        raise AxiomError(
            messages.PLAN_DID_NOT_END.format(diagram, max_rounds))


class Prompt:
    """
    A box with a task in natural language as its name, i.e. a hole in an
    agentic diagram, to be filled by :meth:`refine`.

    Parameters:
        name : The task to perform, i.e. the prompt itself.
        dom : The domain of the prompt, i.e. its input.
        cod : The codomain of the prompt, i.e. its output.

    .. admonition:: Summary

        .. autosummary::

            question
            query
            refine
    """
    model = "claude-opus-5"
    max_tokens = 16000
    instructions = (
        "You are refining a string diagram, i.e. a plan whose boxes are"
        " tasks with typed inputs and outputs. Break the task you are given"
        " into layers of parallel steps, using one of the tools available"
        " whenever it does the job and a finer task otherwise, with an empty"
        " tool name. The inputs of the first layer must be the inputs of the"
        " task, the outputs of the last layer its outputs, and the outputs"
        " of each layer the inputs of the next one, in order and with"
        " repetition.")
    schema = {
        "name": "refine",
        "description": "Refine a task into layers of parallel steps.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["layers"],
            "properties": {"layers": {
                "type": "array",
                "description": "The layers of the refined diagram.",
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["text", "dom", "cod", "tool"],
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "The task of the step, empty"
                                               " if it is a tool."},
                            "dom": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Its input types."},
                            "cod": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Its output types."},
                            "tool": {
                                "type": "string",
                                "description": "The name of the tool, empty"
                                               " if the step is a task."
                            }}}}}}}}

    def question(self, tools=()) -> str:
        """
        The message sent to the model, i.e. the task, its types and the tools.

        Parameters:
            tools : The boxes of the underlying category to choose from.
        """
        types = lambda box: (
            f"{[str(x) for x in box.dom]} -> {[str(x) for x in box.cod]}")
        return "\n".join([f"Task: {self.name}", f"Types: {types(self)}"]
                         + [f"Tool {tool.name}: {types(tool)}"
                            for tool in tools])

    def query(self, tools=(), client=None, model: str = None
              ) -> list[list[dict]]:
        """
        Ask a large language model for the layers refining a prompt, i.e. the
        only call with a side effect in this module.

        Parameters:
            tools : The boxes of the underlying category to choose from.
            client : An `anthropic.Anthropic` client, the default needs the
                environment variable `ANTHROPIC_API_KEY`.
            model : The name of the model, :attr:`model` by default.

        Raises:
            ValueError : Whenever the model answers with no refinement.
        """
        if client is None:
            from anthropic import Anthropic
            client = Anthropic()
        answer = client.messages.create(
            model=model or self.model, max_tokens=self.max_tokens,
            system=self.instructions, tools=[self.schema],
            tool_choice={"type": "tool", "name": self.schema["name"]},
            messages=[{"role": "user", "content": self.question(tools)}])
        for block in answer.content:
            if block.type == "tool_use":
                return block.input["layers"]
        raise ValueError(messages.NO_REFINEMENT.format(answer))

    def refine(self, tools=(), **params) -> Diagram:
        """
        Call :meth:`query` then assemble the answer into an agentic diagram
        with the same domain and codomain, i.e. one step of planning.

        Parameters:
            tools : The boxes of the underlying category to choose from.
            params : Passed on to :meth:`query`.

        Raises:
            AxiomError : Whenever the answer does not have the right types,
                i.e. two consecutive layers or the last one do not compose.
        """
        image = self.factory.from_layers(
            self.dom, self.query(tools, **params), tools)
        if image.cod != self.cod:
            raise AxiomError(messages.WRONG_COD.format(self.cod, image.cod))
        return image

    def __class_getitem__(cls, values) -> type:
        return Agentic[values].prompt_factory


class Agentic:
    """
    The free `category` on the prompts, i.e. `Agentic[category]` is a
    subclass of `category` where boxes can also be a :class:`Prompt`.

    Parameters:
        category : The underlying category, i.e. a `Diagram` subclass.
        box : Its class of boxes, `monoidal.Box` by default, which the
            prompts subclass, e.g. `rigid.Box` for prompts with adjoints.

    Example
    -------
    >>> from discopy import rigid, symmetric
    >>> assert Agentic[symmetric.Diagram] is Agentic[symmetric.Diagram]
    >>> assert issubclass(Agentic[symmetric.Diagram], symmetric.Diagram)
    >>> assert Prompt[symmetric.Diagram].factory is Agentic[symmetric.Diagram]
    >>> Prompt[rigid.Diagram, rigid.Box]('say it', rigid.Ty(), rigid.Ty())
    agentic.Prompt[rigid.Diagram, rigid.Box]('say it', rigid.Ty(), rigid.Ty())
    """
    cache = dict()

    def __class_getitem__(cls, values) -> type:
        values = values if isinstance(values, tuple) else (values, )
        category, box = values if len(values) == 2\
            else (values[0], monoidal.Box)
        if (category, box) not in cls.cache:
            name = f"[{', '.join(map(factory_name, values))}]"
            diagram = factory(type("Agentic" + name, (Diagram, category), {
                "category": category, "__module__": cls.__module__}))
            diagram.prompt_factory = type(
                "Prompt" + name, (Prompt, box, diagram),
                {"__module__": cls.__module__})
            cls.cache[category, box] = diagram
        return cls.cache[category, box]
