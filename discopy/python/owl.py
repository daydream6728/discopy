# -*- coding: utf-8 -*-

"""
The category of Python functions typed by an OWL ontology.

Objects are tuples of :class:`owlready2.ThingClass`, i.e. classes of an
ontology, so that type checking is OWL class membership. Morphisms are Python
functions taking an :class:`owlready2.World` as their first argument: the
world is the state in which individuals live and to which they are added, it
is threaded through composition rather than being a wire. Every call is
validated against the schema by a local HermiT invocation, so that a function
asserting data which contradicts the ontology raises
:class:`owlready2.OwlReadyInconsistentOntologyError`. Everything is
local: :mod:`owlready2` ships HermiT, whose invocation needs a Java
runtime.

The two functors relating this category to :mod:`discopy.python` are
:func:`lift`, which reads a Python function as an OWL function ignoring the
world, and :class:`Eval`, which evaluates an OWL function at a given world.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Function
    Query
    Eval

.. admonition:: Functions

    .. autosummary::
        :template: function.rst
        :nosignatures:
        :toctree:

        lift
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass

from owlready2 import World, sync_reasoner_hermit

from discopy.abc import MarkovCategory
from discopy.python import function, multiplicative
from discopy.python.multiplicative import Ty
from discopy.utils import (
    assert_iscomposable, classproperty, factory, untuplify)


@factory
class Function(function.Function, MarkovCategory):
    """
    Python function annotated with an OWL schema, i.e. a callable
    ``(world, *xs) -> ys`` from individuals to individuals.

    Parameters:
        inside : The callable inside the function, world as first argument.
        dom : The domain, i.e. a tuple of OWL classes.
        cod : The codomain, i.e. a tuple of OWL classes.

    Type checking is that of :class:`discopy.python.multiplicative.Function`,
    which the function delegates to via :meth:`eval`. Schema checking is one
    HermiT invocation per call, on the world as a whole, switched off with
    :attr:`no_reasoning`.

    .. admonition:: Summary

        .. autosummary::

            eval
            validate
            id
            then
            tensor
            swap
            copy
            discard

    Example
    -------
    >>> from owlready2 import AllDisjoint, Thing, World
    >>> world = World()
    >>> onto = world.get_ontology("http://discopy.org/owl.owl")
    >>> with onto:
    ...     class Person(Thing): pass
    ...     class Dog(Thing): pass
    ...     class owns(Person >> Dog): pass
    ...     _ = AllDisjoint([Person, Dog])
    >>> alice, rex = Person("alice"), Dog("rex")

    A generator is a Python function supplemented with an OWL signature.

    >>> def adopt_inside(world, person, dog):
    ...     person.owns.append(dog)
    ...     return person
    >>> adopt = Function(adopt_inside, (Person, Dog), Person)
    >>> name = Function(lambda world, x: x.name, Person, str)

    Composition threads the world through, HermiT runs once per call.

    >>> with Function.no_reasoning:
    ...     (adopt >> name)(world, alice, rex)
    'alice'
    >>> alice.owns
    [owl.rex]

    Asserting data that contradicts the schema is caught by HermiT.

    >>> from owlready2 import OwlReadyInconsistentOntologyError
    >>> confuse = Function(
    ...     lambda world, x: x.is_a.append(Dog) or x, Person, Person)
    >>> try:                                            # doctest: +EXTRA
    ...     confuse(world, alice)
    ... except OwlReadyInconsistentOntologyError:
    ...     print("Alice is not a dog.")
    Alice is not a dog.
    """
    reasoning = True

    @classproperty
    @contextmanager
    def no_reasoning(cls):
        """ Context manager for switching off the HermiT invocations. """
        tmp, cls.reasoning = cls.reasoning, False
        try:
            yield
        finally:
            cls.reasoning = tmp

    def eval(self, world: World) -> multiplicative.Function:
        """
        The image of the function under the evaluation functor at a world,
        i.e. the Python function that calls it on that world.

        Parameters:
            world : The world in which to evaluate the function.
        """
        return multiplicative.Function(
            lambda *xs: self.inside(world, *xs), self.dom, self.cod)

    @staticmethod
    def validate(world: World):
        """
        Check a world against the schema it is typed by, i.e. run HermiT on
        it. Assign to this to use another reasoner or other options, e.g.
        ``ignore_unsupported_datatypes`` for ontologies with annotations
        outside the OWL 2 datatype map.

        Parameters:
            world : The world to check.
        """
        sync_reasoner_hermit(world, debug=0)

    def __call__(self, world: World, *xs):
        result = self.eval(world)(*xs)
        if self.reasoning:
            self.validate(world)
        return result

    @classmethod
    def id(cls, dom: Ty = ()) -> Function:
        """
        The identity function on a tuple of OWL classes, it leaves the world
        untouched.

        Parameters:
            dom : The tuple of OWL classes on which to take the identity.
        """
        return lift(multiplicative.Function.id(dom))

    def then(self, other: Function) -> Function:
        """
        The sequential composition of two functions, called with ``>>``,
        i.e. the composite of their evaluations at every world.

        Parameters:
            other : The other function to compose in sequence.
        """
        assert_iscomposable(self, other)
        return Function(
            lambda world, *xs: (self.eval(world) >> other.eval(world))(*xs),
            self.dom, other.cod)

    def tensor(self, other: Function) -> Function:
        """
        The parallel composition of two functions, called with ``@``,
        i.e. the tensor of their evaluations at every world, the first
        happening before the second on the same world.

        Parameters:
            other : The other function to compose in parallel.
        """
        return Function(
            lambda world, *xs: (self.eval(world) @ other.eval(world))(*xs),
            self.dom + other.dom, self.cod + other.cod)

    @staticmethod
    def swap(x: Ty, y: Ty) -> Function:
        """
        The function swapping two tuples of OWL classes.

        Parameters:
            x : The tuple of OWL classes on the left.
            y : The tuple of OWL classes on the right.
        """
        return lift(multiplicative.Function.swap(x, y))

    @staticmethod
    def copy(x: Ty, n=2) -> Function:
        """
        The function making ``n`` copies of a tuple of OWL classes, i.e. of
        the individuals themselves rather than of the world.

        Parameters:
            x : The tuple of OWL classes to copy.
            n : The number of copies.
        """
        return lift(multiplicative.Function.copy(x, n))

    @staticmethod
    def discard(dom: Ty) -> Function:
        """
        The function discarding a tuple of OWL classes.

        Parameters:
            dom : The tuple of OWL classes to discard.
        """
        return Function.copy(dom, 0)


class Query(Function):
    """
    A :class:`Function` in the special case where its body is a SPARQL query
    on the world, i.e. its inputs are the parameters ``??1, ??2, ...`` of the
    query and its output is the first solution.

    Parameters:
        query : The SPARQL query to perform on the world.
        dom : The domain, i.e. a tuple of OWL classes for the parameters.
        cod : The codomain, i.e. a tuple of OWL classes for the columns.

    Example
    -------
    >>> from owlready2 import Thing, World
    >>> world = World()
    >>> onto = world.get_ontology("http://discopy.org/owl.owl")
    >>> with onto:
    ...     class Person(Thing): pass
    ...     class Dog(Thing): pass
    ...     class owns(Person >> Dog): pass
    >>> alice, rex = Person("alice"), Dog("rex")
    >>> alice.owns.append(rex)
    >>> dog_of = Query('''
    ...     PREFIX onto: <http://discopy.org/owl.owl#>
    ...     SELECT ?dog WHERE { ??1 onto:owns ?dog }''', Person, Dog)
    >>> with Function.no_reasoning:
    ...     dog_of(world, alice)
    owl.rex
    >>> print(Query('SELECT ?x { ?x a ?y }', (), Person))
    Query('SELECT ?x { ?x a ?y }', (), (owl.Person,))
    """
    def __init__(self, query: str, dom: Ty, cod: Ty):
        self.query = query
        super().__init__(self.solve, dom, cod)

    def __repr__(self):
        return f"Query({self.query!r}, {self.dom}, {self.cod})"

    def __eq__(self, other):
        return isinstance(other, Query) and (
            self.query, self.dom, self.cod) == (
                other.query, other.dom, other.cod)

    def solve(self, world: World, *xs):
        """
        The body of the query, i.e. the first solution of ``world.sparql``.

        Parameters:
            world : The world on which to perform the query.
            xs : The individuals to pass as parameters of the query.
        """
        for row in world.sparql(self.query, list(xs)):
            return untuplify(tuple(row))
        raise ValueError(f"No solution for {self.query}")


def lift(other: multiplicative.Function) -> Function:
    """
    The image of a Python function under the inclusion functor into OWL,
    i.e. the OWL function that ignores the world.

    Parameters:
        other : The Python function to lift.

    Example
    -------
    >>> from discopy.python import Function as Py
    >>> from owlready2 import Thing, World
    >>> world = World()
    >>> with world.get_ontology("http://discopy.org/owl.owl"):
    ...     class Person(Thing): pass
    >>> with Function.no_reasoning:
    ...     lift(Py.copy((Person, )))(world, Person("alice"))
    (owl.alice, owl.alice)
    """
    return Function(
        lambda world, *xs: other.inside(*xs), other.dom, other.cod)


@dataclass
class Eval:
    """
    The evaluation functor from OWL to Python at a given world, i.e. the
    identity on objects and :meth:`Function.eval` on morphisms.

    Parameters:
        world : The world at which to evaluate.

    Example
    -------
    >>> from owlready2 import Thing, World
    >>> world = World()
    >>> with world.get_ontology("http://discopy.org/owl.owl"):
    ...     class Person(Thing): pass
    >>> F, alice = Eval(world), Person("alice")
    >>> f = Function(lambda world, x: x.name, Person, str)
    >>> with Function.no_reasoning:
    ...     F((Person, )) == (Person, ) and F(f)(alice) == f(world, alice)
    True
    """
    world: World

    def __call__(self, other: Ty | Function) -> Ty | multiplicative.Function:
        return other if isinstance(other, tuple) else other.eval(self.world)
