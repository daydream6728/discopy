# -*- coding: utf-8 -*-

""" Diagrams with prompts as holes. """

from __future__ import annotations

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


class Prompt:
    """
    A box with a task in natural language as its name, i.e. a hole in an
    agentic diagram, to be filled by :meth:`refine`.

    Parameters:
        name : The task to perform, i.e. the prompt itself.
        dom : The domain of the prompt, i.e. its input.
        cod : The codomain of the prompt, i.e. its output.
    """
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
