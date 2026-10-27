"""
Unification of placeholder wires, which types a derivation of
:mod:`discopy.boltzmann` from the root down: each object variable of a rule
is first a fresh object of placeholders, the conclusion of each rule is
unified with the boundary it meets, adjoints and delays being offsets of a
wire and an exponential its base and exponent, and a placeholder no rule
determines is coloured from a palette the first time a term is built with
it.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Unifier
"""

from __future__ import annotations

import random as std_random

from discopy.abc import Nat
from discopy.utils import AxiomError

MISMATCH = (AxiomError, TypeError, ValueError, AttributeError, IndexError,
            NotImplementedError)
""" What a former raises on an object it does not apply to. """

PLACEHOLDERS = 10 ** 6
""" The first number of a placeholder wire, for objects that take no name,
e.g. a dimension, see :class:`Unifier`. """


def length(obj) -> int:
    """
    The number of wires of an object: none for the single object of a
    monoid, one for an object with no tensor.
    """
    if obj is None:
        return 0
    return len(obj) if hasattr(obj, "__len__") else 1


def atoms_of(obj) -> list:
    """ The objects of one cell of an object, itself if it has no tensor. """
    if not hasattr(obj, "__len__"):
        return [obj]
    return [obj[i:i + 1] for i in range(len(obj))]


def offset(atom) -> tuple[int, int]:
    """ The winding and the time step of the cell of an atom. """
    cell = atom.inside[0] if hasattr(atom, "inside") else atom
    return getattr(cell, "z", 0) or 0, getattr(cell, "time_step", 0) or 0


def shift(atom, winding: int, steps: int):
    """ An atom wound right ``winding`` times and delayed ``steps``. """
    for _ in range(abs(winding)):
        atom = atom.r if winding > 0 else atom.l
    return atom.delay(steps) if steps else atom


class Unifier:
    """
    A substitution of the placeholder wires of a derivation being typed:
    each object variable of a rule is first a fresh object of placeholders,
    see :meth:`fresh`, the conclusion of a rule is unified with the goal it
    meets, see :meth:`unify`, and a placeholder no rule determines is
    coloured uniformly from the ``palette`` the first time a term is built
    with it, see :meth:`resolve`. Adjoints and delays are offsets of a
    cell, an exponential the pair of its base and exponent.

    >>> from random import Random
    >>> from discopy.rigid import Ty, Diagram
    >>> x = Ty('x')
    >>> unifier = Unifier(Diagram, Random(0), (x, ), None)
    >>> left, right = unifier.fresh(x), unifier.fresh(x)
    >>> unifier.unify(left @ left.l, right @ x.l)
    >>> assert unifier.resolve(right) == x
    """
    def __init__(self, category: type, random: std_random.Random,
                 palette: tuple, generator):
        self.ob, self.random = category.typeparams()[0], random
        self.palette, self.generator = palette, generator
        self.bound: dict = {}

    @staticmethod
    def placeholder(atom):
        """
        The name of a placeholder atom, ``None`` for any other: its name if
        it starts with ``?``, or its number if it is one of the
        :data:`PLACEHOLDERS`, e.g. for a dimension.
        """
        cell = atom.inside[0] if hasattr(atom, "inside") else atom
        name = getattr(cell, "name", None)
        number = getattr(cell, "inside", (None, ))[:1]
        if hasattr(cell, "base"):
            return None
        if isinstance(name, str) and name.startswith("?"):
            return name
        if number and isinstance(number[0], int)\
                and number[0] >= PLACEHOLDERS:
            return number[0]
        return None

    def fresh(self, shadow):
        """ An object of the shape of a shadow, each cell a placeholder. """
        if shadow is None or isinstance(shadow, Nat):
            return shadow
        atoms = []
        for _ in range(length(shadow)):
            number = len(self.bound)
            try:
                atom = self.ob(f"?{number}")
            except MISMATCH:
                atom = self.ob(PLACEHOLDERS + number)
            name = self.placeholder(atom)
            if name is None or name in self.bound:
                raise ValueError(f"No placeholder for {atom}.")
            self.bound[name] = None
            atoms.append(atom)
        return atoms[0] if not hasattr(shadow, "tensor")\
            else type(shadow)().tensor(*atoms)

    def resolve(self, obj, colour: bool = True):
        """
        An object with each bound placeholder substituted, and each free one
        coloured from the palette when ``colour``.
        """
        if obj is None or isinstance(obj, (Nat, int)):
            return obj
        atoms = [self.resolve_atom(atom, colour) for atom in atoms_of(obj)]
        return atoms[0] if not hasattr(obj, "tensor")\
            else type(obj)().tensor(*atoms)

    def resolve_atom(self, atom, colour: bool):
        """ An atom resolved, see :meth:`resolve`. """
        cell = atom.inside[0] if hasattr(atom, "inside") else atom
        name = self.placeholder(atom)
        if hasattr(cell, "base"):
            base, exponent = (self.resolve(side, colour)
                              for side in (cell.base, cell.exponent))
            exp = exponent >> base if type(cell).__name__ == "Under"\
                else base << exponent
            return shift(exp, 0, offset(atom)[1])
        if name is None:
            return atom
        if self.bound[name] is None and colour:
            self.bound[name] = self.random.choice(self.palette)
        if self.bound[name] is None:
            return atom
        return shift(self.resolve(self.bound[name], colour), *offset(atom))

    def unify(self, left, right) -> None:
        """
        Bind placeholders so that two objects resolve to the same, raising
        :class:`discopy.utils.AxiomError` when they cannot.
        """
        left, right = (self.resolve(side, False) for side in (left, right))
        if left == right:
            return
        if length(left) != length(right):
            raise AxiomError(f"{left} and {right} do not unify.")
        for one, other in zip(atoms_of(left), atoms_of(right)):
            self.unify_atom(*(self.resolve(atom, False)
                              for atom in (one, other)))

    def unify_atom(self, one, other) -> None:
        """ Unify two objects of one cell, see :meth:`unify`. """
        if one == other:
            return
        for this, that in ((one, other), (other, one)):
            name = self.placeholder(this)
            if name is not None:
                value = shift(that, *(-n for n in offset(this)))
                if repr(name) in repr(value):
                    raise AxiomError(f"{this} occurs in {that}.")
                self.bound[name] = value
                return
        cells = [atom.inside[0] for atom in (one, other)]
        if all(hasattr(cell, "base") for cell in cells)\
                and type(cells[0]) is type(cells[1])\
                and offset(one) == offset(other):
            self.unify(cells[0].base, cells[1].base)
            self.unify(cells[0].exponent, cells[1].exponent)
            return
        raise AxiomError(f"{one} and {other} do not unify.")
