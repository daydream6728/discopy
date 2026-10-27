"""
Boltzmann sampling of the terms of a free category, from its rules.

The :class:`discopy.axioms.Rule` declarations of a free category are a
sequent calculus, and they are compiled in two steps: first the *shape* of a
derivation, then the *colours* of its wires.

**Shapes.** Every object variable of a rule is given a number of wires, at
most a ``width``, and every instance whose premises and conclusion have at
most that many wires on each side is a :class:`Production` of a
context-free grammar, see :func:`compile`. Its sorts are the shapes
``m → n`` of the morphisms with ``m`` inputs and ``n`` outputs, and each sort
has one more production, the generator, a box with that shape, so that every
sort is inhabited. A derivation is a :class:`discopy.grammar.cfg.Tree` of
productions.

Each production carries a weight as data, a monomial in :mod:`sympy` symbols:
``z`` marks the size of a derivation, its number of nodes, and ``u_rule`` the
applications of each rule. The generating function of a sort ``s`` is the
least solution of the system, see :meth:`Specification.system`

.. math::

    T_s = \\sum_{r : \\dots \\to s} w_r \\prod_{p \\in \\mathrm{dom}(r)} T_p

and the Boltzmann distribution draws a derivation with the product of the
weights of its nodes over :math:`T_s`, i.e. the root by
:math:`w_r \\prod_p T_p / T_s` then each premise from its own sort, see
:meth:`Specification.sample`. It is uniform on the derivations of a given
size and shape, which are not the diagrams up to the equations of the
category: a diagram is drawn once per derivation of it.

As diagrams, the equation of a sort is ``T_s = sum((T_p @ ... @ T_q) >> r)``
with a state ``T_s`` for each sort, its symbol as data: the *sampling
diagram* of the sort, see :meth:`Specification.diagrams`. Its parameters are
tuned by a convex program in log-space, see :meth:`Specification.tune`.

**Colours.** A derivation is then typed from the root down, see
:meth:`Specification.derive`: each object variable of a rule is a fresh
object of placeholder wires, the conclusion of each rule is unified with the
boundary asked of it, adjoints and delays being offsets of a wire, see
:class:`Unifier`, and the wires no rule determines are coloured uniformly
from a palette as the term is built. A derivation whose conclusion cannot
meet the boundary asked of it, e.g. a cup ``x @ x.r -> Ty()`` asked for
``x @ y -> Ty()``, is rejected, so that the terms are drawn from the
Boltzmann distribution of the shapes, coloured uniformly, conditioned on
being well-typed.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Production
    Specification
    Unifier

.. admonition:: Functions

    .. autosummary::
        :template: function.rst
        :nosignatures:
        :toctree:

        wire
        shapes
        compile
"""

from __future__ import annotations

import inspect
import math
import random as std_random
from dataclasses import dataclass, field
from functools import cached_property, lru_cache
from itertools import product
from types import NoneType
from typing import TYPE_CHECKING, Any, get_args, get_origin

from discopy import monoidal
from discopy.abc import Nat
from discopy.axioms import (
    GENERATORS, Atom, Declaration, Hom, Obj, Var, substitute)
from discopy.grammar import cfg
from discopy.utils import AxiomError, factory_name

if TYPE_CHECKING:
    import numpy
    from hypothesis import strategies as st

NUMBERS = 3
""" The numbers a variable ``N: Nat`` of a rule ranges over, from zero. """

SIZE = 4
""" The least size of a derivation drawn by default, see
:meth:`Specification.strategy`. """

BOXES = .4
"""
The share of generators among the nodes of a derivation, by default: a
uniform derivation is mostly structure, e.g. the traces of a swap, which
tuning the expected number of generators near the singularity redresses,
see :meth:`Specification.strategy`.
"""

SINGULAR = 1000
"""
The expected size the parameters of a strategy are tuned to: close enough
to the singularity of the generating function that the distribution is
nearly uniform on the derivations of each size, so that conditioning on a
window of sizes draws them nearly uniformly, see
:meth:`Specification.strategy`.
"""

WIDTH = 2
""" The most wires on either side of a morphism of a derivation, by default.
"""

MAX_WIDTH = 8
"""
The widest grammar compiled for a boundary: the instances of a rule grow
with a power of the width, e.g. a mix with its fourth, so a boundary wider
than that is met by a generator on either side, see
:meth:`Specification.strategy`.
"""

PLACEHOLDERS = 10 ** 6
""" The first number of a placeholder wire, for objects that take no name,
e.g. a dimension, see :class:`Unifier`. """

MISMATCH = (AxiomError, TypeError, ValueError, AttributeError, IndexError,
            NotImplementedError)
""" What a former raises on an object it does not apply to. """


def length(obj) -> int:
    """
    The number of wires of an object: none for the single object of a
    monoid, one for an object with no tensor.
    """
    if obj is None:
        return 0
    return len(obj) if hasattr(obj, "__len__") else 1


class Production(cfg.Rule):
    """
    A production of the grammar of a free category: an instance of one of its
    rules, from the sorts of its premises to the sort of its conclusion, or a
    generator, with a weight as ``data``.

    Parameters:
        dom : The sorts of the morphism premises.
        cod : The sort of the conclusion.
        name : The name of the rule, ``"box"`` for a generator and
            ``"any"`` for the choice of a shape.
        shadow : The value of each variable of the rule in the instance,
            an object of as many wires as it is given, all of one colour.
        params : Those of :class:`discopy.grammar.cfg.Rule`, its ``data``
            the weight, a monomial in the parameters.

    The shadow is how the grammar instantiates the rule rather than a field
    of the box: a production rebuilt from its fields, e.g. its dagger, has
    none.
    """
    def __init__(self, dom: monoidal.Ty, cod: monoidal.Ty, name: str, *,
                 shadow: dict | None = None, **params):
        super().__init__(dom, cod, name=name, **params)
        self.shadow = dict(shadow or {})


def wire(category: type):
    """
    The object of one wire the shapes of a category are drawn with: named
    after the first of :data:`discopy.axioms.GENERATORS` when its objects
    take a name, numbered two otherwise, e.g. a dimension.

    >>> from discopy.monoidal import Ty, Diagram
    >>> assert wire(Diagram) == Ty('a')
    >>> from discopy.neural.network import Dims, Network
    >>> assert wire(Network) == Dims(2)
    """
    ob = category.typeparams()[0]
    for name in (GENERATORS[0], 2):
        try:
            return ob(name)
        except MISMATCH:
            continue
    raise NotImplementedError(f"No wire of {factory_name(category)}.")


def generators(ob: type) -> st.SearchStrategy:
    """ The strategy of the objects of one wire of a category. """
    return getattr(ob, "generators", ob.strategy)()


def shapes(category: type, width: int = WIDTH) -> tuple:
    """
    The objects the variables of a rule range over when compiling the shapes
    of a category: the tensors of at most ``width`` copies of one
    :func:`wire`, the wire itself when its objects have no tensor and the
    single object of a monoid.

    >>> from discopy.monoidal import Ty, Diagram
    >>> assert shapes(Diagram, 2) == (Ty(), Ty('a'), Ty('a', 'a'))
    """
    ob = category.typeparams()[0]
    if ob is NoneType:
        return (None, )
    if not hasattr(ob, "tensor"):
        return (wire(category), )
    return tuple(wire(category) ** n for n in range(width + 1))


def ranges(sort, objects: tuple) -> tuple:
    """ The values a variable of a rule of the given sort ranges over. """
    if get_origin(sort) is Obj:
        return objects
    if get_origin(sort) is Atom:
        return tuple(obj for obj in objects if length(obj) <= 1)[-1:]
    if isinstance(sort, type) and issubclass(sort, Nat):
        return tuple(map(sort, range(NUMBERS + 1)))
    raise NotImplementedError(f"No values for the sort {sort}.")


def boundary(kind) -> tuple[Any, Any]:
    """ The domain and codomain of a morphism sort ``Hom[C1, dom, cod]``. """
    _, dom, cod = get_args(kind)
    return dom, cod


def instances(rule: Declaration, objects: tuple, width: int):
    """
    The instances of a rule whose morphisms have at most ``width`` wires on
    either side, as pairs of a scope, the value of each variable, and the
    shapes of its conclusion and of its morphism premises.
    """
    variables = inspect.unwrap(rule.function).__type_params__
    annotations = rule.annotations()
    base = rule.scope(lambda name, sort: sort)
    domains = [ranges(base[variable], objects) for variable in variables]
    for assignment in product(*domains):
        scope = {**base, **dict(zip(variables, assignment))}
        try:
            kinds = [substitute(annotations[parameter.name], scope)
                     for parameter in rule.parameters]
            sides = [boundary(rule.output(scope))] + [
                boundary(kind) for kind in kinds if get_origin(kind) is Hom]
        except MISMATCH:
            continue
        if any(get_origin(kind) not in (Hom, Var) for kind in kinds):
            raise NotImplementedError(f"{rule} has a premise of no sort.")
        shape = [tuple(map(length, side)) for side in sides]
        if max(map(max, shape)) <= width and not vanishes(kinds, shape):
            yield scope, shape[0], shape[1:]


def vanishes(kinds: list, shape: list) -> bool:
    """
    Whether an instance of a rule wraps a premise of its own shape around
    an empty object, e.g. the trace or the feedback of no wire: admissible
    by vanishing, it would only nest the premise in a bubble.
    """
    empty = any(get_origin(kind) is Var and get_args(kind)[1] is not None
                and not isinstance(get_args(kind)[1], int)
                and length(get_args(kind)[1]) == 0 for kind in kinds)
    return empty and shape[0] in shape[1:]


def sort_name(category: type, shape: tuple) -> str:
    """ The name of the sort of the morphisms of a shape, ``?`` if unknown. """
    if len(shapes(category)) == 1:
        return "Hom"
    return " → ".join("?" if side is None else str(side) for side in shape)


@lru_cache(maxsize=None)
def compile(  # pylint: disable=redefined-builtin  # compiles a grammar
        category: type, *, within: type | None = None,
        width: int = WIDTH) -> Specification:
    """
    The specification of the shapes of the derivations of a free category,
    from the rules of ``within``, the category itself by default, of at most
    ``width`` wires on either side, its root the sort of unknown shape.

    >>> from discopy.cat import Arrow
    >>> print(compile(Arrow))
    Specification(root=Hom, productions=3)
    >>> from discopy.monoidal import Diagram
    >>> print(compile(Diagram))
    Specification(root=? → ?, productions=102)
    """
    # pylint: disable-next=import-outside-toplevel  # an optional dependency
    import sympy

    objects = shapes(category, width)
    names = ["box"] + sorted(
        name for name, rule in category.rules.items()
        if rule.applicable and rule.derivation is None
        and name in (within or category).rules)
    z = sympy.Symbol("z", positive=True)
    marks = {name: sympy.Symbol(f"u_{name}", positive=True) for name in names}
    sorts: dict[tuple, monoidal.Ty] = {
        shape: monoidal.Ty(sort_name(category, shape))
        for shape in product(*2 * [sorted(set(map(length, objects)))])}
    productions = [Production(
        monoidal.Ty(), sort, "box", data=z * marks["box"])
                   for sort in sorts.values()]
    for name in names[1:]:
        for scope, conclusion, premises in instances(
                category.rules[name], objects, width):
            productions.append(Production(
                monoidal.Ty().tensor(*(sorts[shape] for shape in premises)),
                sorts[conclusion], name, data=z * marks[name], shadow=scope))
    if len(sorts) > 1:
        productions += unions(category, sorts)
    root = sorts[(None, None)] if len(sorts) > 1 else next(
        iter(sorts.values()))
    return Specification(
        category, root, tuple(productions), z, tuple(marks.values()), sorts)


def unions(category: type, sorts: dict) -> list[Production]:
    """
    The sorts of the shapes with a side unknown, ``None``, added to
    ``sorts``, and their productions: the choice of a sort with that side.
    """
    # pylint: disable-next=import-outside-toplevel  # an optional dependency
    import sympy
    known = list(sorts)
    lengths = sorted({side for shape in known for side in shape})
    productions = []
    for shape in product(*2 * [[None, *lengths]]):
        if None not in shape:
            continue
        sorts[shape] = monoidal.Ty(sort_name(category, shape))
        productions += [
            Production(sorts[given], sorts[shape], "any",
                       data=sympy.Integer(1))
            for given in known if all(
                side in (None, value) for side, value in zip(shape, given))]
    return productions


@dataclass(frozen=True, eq=False)
class Specification:
    """
    The weighted grammar of the shapes of the derivations of a free
    category, see :func:`compile`, from which its terms are Boltzmann
    sampled.

    Parameters:
        category : The free category the derivations denote terms of.
        root : The sort of the derivations sampled by default.
        productions : The productions of the grammar.
        size : The symbol marking the size of a derivation.
        marks : The symbol marking each rule, ``u_box`` for the generators.
        shapes : The sort of each shape, ``None`` for an unknown side.
    """
    category: type
    root: monoidal.Ty
    productions: tuple[Production, ...]
    size: Any
    marks: tuple = ()
    shapes: dict = field(default_factory=dict)
    cache: dict = field(default_factory=dict, repr=False)

    def __str__(self):
        return f"Specification(root={self.root}, " \
               f"productions={len(self.productions)})"

    @cached_property
    def sorts(self) -> tuple[monoidal.Ty, ...]:
        """ The sorts of the grammar, the root last. """
        return tuple(dict.fromkeys(
            [production.cod for production in self.productions
             if production.cod != self.root] + [self.root]))

    @cached_property
    def symbols(self) -> dict:
        """ The unknown :math:`T_s` of each sort, a :mod:`sympy` symbol. """
        # pylint: disable-next=import-outside-toplevel
        import sympy
        return {sort: sympy.Symbol(f"T[{sort}]", positive=True)
                for sort in self.sorts}

    @property
    def parameters(self) -> tuple:
        """ The parameters of the weights: the size, then the marks. """
        return (self.size, *self.marks)

    def state(self, sort: monoidal.Ty) -> monoidal.Box:
        """ The state :math:`T_s` sampling a sort, its symbol as data. """
        return monoidal.Box("T", monoidal.Ty(), sort, data=self.symbols[sort])

    def diagrams(self, sort: monoidal.Ty | None = None) -> monoidal.Equation:
        """
        The sampling diagram of a sort, the root by default: its state is the
        sum of each production that concludes it after the states of its
        premises.

        >>> from discopy.cat import Arrow
        >>> compile(Arrow).diagrams().draw(
        ...     doctest="docs/_static/boltzmann/arrows.svg")

        .. image:: /_static/boltzmann/arrows.svg
            :align: center
        """
        sort = self.root if sort is None else sort
        terms = [(
            monoidal.Diagram.id().tensor(*map(self.state, production.dom))
            >> production.to_diagram()).foliation()
            for production in self.productions if production.cod == sort]
        return monoidal.Equation(
            self.state(sort), *terms,
            symbols=("=", ) + (len(terms) - 1) * ("+", ))

    def system(self) -> dict:
        """
        The equation of the generating function of each sort, read off its
        sampling diagram: each term is the product of the data of its boxes.

        >>> from discopy.cat import Arrow
        >>> spec = compile(Arrow)
        >>> print(spec.system()[spec.symbols[spec.root]])
        T[Hom]**2*u_cut*z + u_ax*z + u_box*z
        """
        # pylint: disable-next=import-outside-toplevel
        import sympy
        return {self.symbols[sort]: sympy.Add(*(
            sympy.Mul(*(box.data for box in term.boxes))
            for term in self.diagrams(sort).terms[1:]))
            for sort in self.sorts}

    @cached_property
    def monomials(self) -> tuple[list, list]:
        """
        The coefficient of each weight and its exponent in each parameter.
        """
        coefficients, exponents = [], []
        for production in self.productions:
            powers = production.data.as_powers_dict()
            exponents.append([powers.get(p, 0) for p in self.parameters])
            coefficients.append(float(production.data.as_coeff_Mul()[0]))
        return coefficients, exponents

    def logarithms(self) -> tuple[tuple, tuple, list]:
        """
        The system in log-space, :math:`t_s \\geq \\log \\sum_r \\exp(\\theta
        \\cdot m_r + \\sum_p t_p)`: the logarithm of each parameter, that of
        each sort, ``t_i`` for the ``i``-th of the :attr:`sorts`, so that
        :func:`sympy.lambdify` reads them as identifiers, and the right-hand
        side of each sort, a :func:`LogSumExp`.
        """
        # pylint: disable-next=import-outside-toplevel
        import sympy
        thetas = tuple(sympy.Symbol(f"log_{p}") for p in self.parameters)
        logs = {sort: sympy.Symbol(f"t_{i}")
                for i, sort in enumerate(self.sorts)}
        coefficients, exponents = self.monomials
        terms: dict = {sort: [] for sort in self.sorts}
        for production, coefficient, exponent in zip(
                self.productions, coefficients, exponents):
            terms[production.cod].append(sympy.Add(
                sympy.log(coefficient),
                *(k * theta for k, theta in zip(exponent, thetas)),
                *(logs[monoidal.Ty(wire)] for wire in production.dom.inside)))
        return thetas, tuple(logs.values()), [
            LogSumExp()(*terms[sort]) for sort in self.sorts]

    def tune(self, size: float = SIZE, **marks: float) -> dict:
        """
        The parameters whose Boltzmann distribution on the root has the given
        expected size, and the given expected applications of the rules
        named as keywords, the other marks being one: the optimum of the
        convex program of `Bendkowski, Bodini and Dovgal (2018)
        <https://arxiv.org/abs/1708.01212>`_,

        .. math::

            \\min t_{root} - \\nu \\cdot \\theta \\quad \\text{s.t.} \\quad
            t_s \\geq \\log \\sum_r \\exp(\\theta \\cdot m_r + \\sum_p t_p)

        whose constraints :func:`sympy.lambdify` turns into :mod:`cvxpy`
        expressions, :func:`LogSumExp` being :func:`cvxpy.log_sum_exp`.

        >>> from discopy.monoidal import Diagram
        >>> spec = compile(Diagram)
        >>> params = spec.tune(size=5, cut=1)
        >>> assert abs(spec.expectation(params) - 5) < 1e-3
        >>> assert abs(spec.expectation(params, "cut") - 1) < 1e-3
        """
        # pylint: disable-next=import-outside-toplevel
        import cvxpy
        # pylint: disable-next=import-outside-toplevel
        import sympy
        key = ("tune", size, tuple(sorted(marks.items())))
        if key in self.cache:
            return self.cache[key]
        thetas, logs, rhs = self.logarithms()
        names = ["z"] + [str(mark).removeprefix("u_") for mark in self.marks]
        targets = {0: size} | {
            i: marks[name] for i, name in enumerate(names) if name in marks}
        theta, t = cvxpy.Variable(len(thetas)), cvxpy.Variable(len(logs))
        right = sympy.lambdify(thetas + logs, rhs, modules=[{
            "LogSumExp": lambda *xs: cvxpy.log_sum_exp(cvxpy.hstack(xs)),
            "log": math.log}])(
                *(theta[i] for i in range(len(thetas))),
                *(t[i] for i in range(len(logs))))
        problem = cvxpy.Problem(
            cvxpy.Minimize(t[len(logs) - 1] - sum(
                nu * theta[i] for i, nu in targets.items())),
            [t[i] >= expression for i, expression in enumerate(right)] + [
                theta[i] == 0 for i in range(len(thetas))
                if i not in targets])
        problem.solve(solver=cvxpy.CLARABEL)
        if theta.value is None:
            raise ValueError(f"No parameters tune {self} to {key[1:]}.")
        self.cache[key] = dict(zip(self.parameters, map(
            math.exp, theta.value)))
        return self.cache[key]

    def arrays(self, params: dict) -> tuple:
        """
        The numeric weight of each production, the index of the sort of its
        conclusion and those of its premises, padded with the index of the
        constant one, after the last sort.
        """
        # pylint: disable-next=import-outside-toplevel
        import numpy
        index_of = {sort: i for i, sort in enumerate(self.sorts)}
        coefficients, exponents = self.monomials
        weights = numpy.array(coefficients) * numpy.prod(
            numpy.array([[params[p] for p in self.parameters]],
                        dtype=float) ** numpy.array(exponents, dtype=float),
            axis=1)
        arity = max(len(production.dom) for production in self.productions)
        premises = numpy.full((len(self.productions), arity), len(index_of))
        for i, production in enumerate(self.productions):
            premises[i, :len(production.dom)] = [
                index_of[monoidal.Ty(wire)] for wire in production.dom.inside]
        conclusions = numpy.array([
            index_of[production.cod] for production in self.productions])
        return weights, conclusions, premises

    def oracle(self, params: dict, tolerance: float = 1e-12,
               iterations: int = 100_000) -> numpy.ndarray:
        """
        The value of the generating function of each sort at the parameters,
        the limit of the iteration of the system from zero, raising
        ``ValueError`` when it diverges, i.e. past the singularity.
        """
        # pylint: disable-next=import-outside-toplevel
        import numpy
        weights, conclusions, premises = self.arrays(params)
        values = numpy.zeros(len(self.sorts) + 1)
        values[-1] = 1
        for _ in range(iterations):
            new = numpy.bincount(
                conclusions, weights * numpy.prod(values[premises], axis=1),
                minlength=len(self.sorts))
            if not numpy.all(numpy.isfinite(new)) or new.max() > 1e12:
                raise ValueError(f"{self} diverges at {params}.")
            done = numpy.max(numpy.abs(new - values[:-1]))\
                <= tolerance * (1 + new.max())
            values[:-1] = new
            if done:
                return values[:-1]
        raise ValueError(f"{self} does not converge at {params}.")

    def expectation(self, params: dict, mark: str = "z") -> float:
        """
        The expected number of nodes of a derivation of the root, or of the
        applications of the rule named ``mark``, at the parameters: the
        logarithmic derivative of the generating function in that parameter,
        a check of :meth:`tune`.
        """
        # pylint: disable-next=import-outside-toplevel
        import numpy
        symbol = next(p for p in self.parameters
                      if str(p) in (mark, f"u_{mark}"))
        epsilon = 1e-7
        shifted = {**params, symbol: params[symbol] * (1 + epsilon)}
        return float(numpy.log(self.oracle(shifted)[-1] / self.oracle(
            params)[-1]) / math.log1p(epsilon))

    def probabilities(
            self, params: dict) -> dict[monoidal.Ty, tuple[list, list]]:
        """
        The productions of each sort with the probability of drawing each,
        :math:`w_r \\prod_p T_p / T_s`, computed once for each parameters.
        """
        # pylint: disable-next=import-outside-toplevel
        import numpy
        key = ("probabilities", tuple(sorted(
            (str(k), v) for k, v in params.items())))
        if key in self.cache:
            return self.cache[key]
        values = numpy.append(self.oracle(params), 1)
        weights, conclusions, premises = self.arrays(params)
        terms = weights * numpy.prod(values[premises], axis=1)
        choices: dict[monoidal.Ty, tuple[list, list]] = {
            sort: ([], []) for sort in self.sorts}
        for production, term, sort in zip(
                self.productions, terms, conclusions):
            choices[production.cod][0].append(production)
            choices[production.cod][1].append(float(term / values[sort]))
        self.cache[key] = choices
        return choices

    def sample(  # pylint: disable=too-many-arguments  # a window of sizes
            self, random: std_random.Random, params: dict, *,
            sort: monoidal.Ty | None = None, max_size: int | None = None,
            min_size: int = 0) -> cfg.Tree | None:
        """
        A derivation of a sort, the root by default, drawn exactly from the
        Boltzmann distribution at the parameters given a source of uniform
        randomness, or ``None`` as soon as it grows past ``max_size``, or
        when it ends short of ``min_size``: anticipated rejection, which
        conditions the distribution on that window of sizes.
        Each choice is that of the first production whose cumulative
        probability exceeds a uniform draw, the generators first, so that a
        draw that shrinks to zero shrinks the derivation to a single box.

        >>> from random import Random
        >>> from discopy.cat import Arrow
        >>> spec = compile(Arrow)
        >>> print(spec.sample(Random(6), spec.tune(size=5)))
        cut(cut(ax, box), box)
        """
        choices = self.probabilities(params)
        size, stack, built = 0, [(sort or self.root, None)], []
        while stack:
            sort_, production = stack.pop()
            if production is not None:
                arity = len(production.dom)
                built[len(built) - arity:] = [production(
                    *built[len(built) - arity:]) if arity else production]
                continue
            size += 1
            if max_size is not None and size > max_size:
                return None
            production = choose(*choices[sort_], random.random())
            stack.append((sort_, production))
            stack += [(monoidal.Ty(premise), None)
                      for premise in reversed(production.dom.inside)]
        return built[0] if size >= min_size else None

    def palette(self, *goal, draw=None) -> tuple:
        """
        The atoms of the boundary asked for, from which the wires no rule
        determines are coloured, and with a hypothesis ``draw`` those of one
        or two more wires drawn by the ``generators`` of the objects, so that
        a wire may take a colour the boundary does not have.
        """
        ob = self.category.typeparams()[0]
        if ob is NoneType:
            return (None, )
        atoms = tuple(dict.fromkeys(
            atom for obj in goal if obj is not None for atom in atoms_of(obj)))
        if draw is not None:
            atoms += tuple(draw(generators(ob), label="colour")
                           for _ in range(2 - min(1, len(atoms))))
        return atoms

    def premises(self, production: Production, dom, cod,
                 unifier: Unifier) -> dict | None:
        """
        The premises of the rule of a production concluding ``dom -> cod``,
        by name, its variables fresh placeholders and its conclusion unified
        with the boundary, or ``None`` when it does not unify.
        """
        rule = self.category.rules[production.name]
        annotations = rule.annotations()
        scope = {**production.shadow, **{
            variable: unifier.fresh(production.shadow[variable])
            for variable in inspect.unwrap(rule.function).__type_params__}}
        try:
            for side, goal in zip(boundary(rule.output(scope)), (dom, cod)):
                unifier.unify(side, goal)
            return {parameter.name: substitute(
                annotations[parameter.name], scope)
                for parameter in rule.parameters}
        except MISMATCH:
            return None

    def derive(self, tree: cfg.Tree, dom, cod, unifier: Unifier):
        """
        Type a derivation from ``dom`` to ``cod``, from the root down, and
        return how to build the term it denotes once every wire is coloured,
        or ``None`` when it cannot meet that boundary: each object variable
        of a rule is a fresh object of placeholders of the shape of its
        shadow, its conclusion is unified with the boundary, see
        :class:`Unifier`, and each morphism premise derived at the boundary
        it asks for in turn.
        """
        production, branches = tree.root, iter(tree.branches)
        assert isinstance(production, Production)
        if production.name == "any":
            return self.derive(next(branches), dom, cod, unifier)
        if production.name == "box":
            return lambda: unifier.generator(
                unifier.resolve(dom), unifier.resolve(cod))
        rule = self.category.rules[production.name]
        kinds = self.premises(production, dom, cod, unifier)
        if kinds is None:
            return None
        builders = {}
        for name, kind in kinds.items():
            builders[name] = (lambda value=get_args(kind)[1]:
                              unifier.resolve(value))\
                if get_origin(kind) is Var else self.derive(
                    next(branches), *boundary(kind), unifier)
            if builders[name] is None:
                return None
        return lambda: rule(**{
            name: build() for name, build in builders.items()})

    def strategy(  # pylint: disable=too-many-arguments  # a boundary, bounds
            self, dom=None, cod=None, *, size: int = SIZE, exact: bool = True,
            attempts: int = 1000, **marks) -> st.SearchStrategy:
        """
        The :mod:`hypothesis` strategy of the terms from ``dom`` to ``cod``,
        any if ``None``, whose derivations have between ``size`` and
        ``2 * size + 1`` nodes: the approximate-size Boltzmann sampler at the
        parameters :meth:`tune` gives near the singularity, see
        :data:`SINGULAR`, a derivation of the shape of the boundary drawn,
        conditioned on that window by anticipated rejection, and typed, see
        :meth:`derive`, again until one is well-typed. A side wider
        than the grammar is met by a generator from or to its first wires,
        those of the widest shape. The generators are drawn by the
        ``generators`` of the category, the colours of the wires no rule
        determines from the :meth:`palette`, uniformly.

        Parameters:
            dom : The domain, any if ``None``.
            cod : The codomain, any if ``None``.
            size : The least size of a derivation, half the largest.
            exact : Whether to draw from :func:`hypothesis.strategies.randoms`
                with ``use_true_random``, i.e. from the Boltzmann
                distribution exactly, or from the choices of Hypothesis,
                which shrink to the first production of each sort.
            attempts : How many derivations are drawn before the example
                is rejected.
            marks : The expected applications of the rules near the
                singularity, by name, the generators a share :data:`BOXES`
                of the nodes by default, when that tunes.

        >>> from hypothesis import find
        >>> from discopy.monoidal import Ty, Diagram
        >>> x, y = Ty('x'), Ty('y')
        >>> spec = compile(Diagram)
        >>> term = find(spec.strategy(x, x @ y), lambda f: len(f) > 1)
        >>> assert (term.dom, term.cod) == (x, x @ y)
        """
        # pylint: disable-next=import-outside-toplevel
        from hypothesis import reject, strategies as st
        try:
            params = self.tune(SINGULAR, **{"box": BOXES * SINGULAR} | marks)
        except ValueError:
            params = self.tune(SINGULAR, **marks)
        min_size, max_size = size, 2 * size + 1
        inner, sort = self.clip(dom, cod)

        @st.composite
        def terms(draw):
            random = draw(st.randoms(use_true_random=exact))
            palette = self.palette(dom, cod, draw=draw)
            for _ in range(attempts):
                tree = self.sample(random, params, sort=sort,
                                   max_size=max_size, min_size=min_size)
                if tree is None:
                    continue
                unifier = Unifier(self.category, random, palette, lambda x, y:
                                  draw(self.category.generators(dom=x, cod=y)))
                dom_, cod_ = (side if side is not None else unifier.fresh(
                    shadow) for side, shadow in zip(inner, self.sides(tree)))
                build = self.derive(tree, dom_, cod_, unifier)
                if build is None:
                    continue
                term = build()
                if dom is not None and dom != term.dom:
                    term = unifier.generator(dom, term.dom) >> term
                if cod is not None and cod != term.cod:
                    term = term >> unifier.generator(term.cod, cod)
                return term
            return reject()

        return terms()

    def clip(self, dom, cod) -> tuple[tuple, monoidal.Ty]:
        """
        A boundary clipped to the widest shape of the grammar, and the sort
        of its shape, see :meth:`strategy`.
        """
        widest = max(side for shape in self.shapes for side in shape
                     if side is not None) if len(self.shapes) > 1 else None
        inner = tuple(
            side[:widest] if widest is not None and side is not None
            and length(side) > widest else side for side in (dom, cod))
        shape = tuple(None if side is None else length(side)
                      for side in inner)
        sort = self.root if len(self.shapes) == 1 else self.shapes.get(shape)
        if sort is None:
            raise ValueError(f"No sort of shape {shape} in {self}.")
        return inner, sort

    def sides(self, tree: cfg.Tree) -> tuple:
        """
        Objects of one colour of the shape of the conclusion of a derivation,
        for the sides of a boundary that is not asked for.
        """
        while tree.root.name == "any":
            tree = tree.branches[0]
        shape = next(shape for shape, sort in self.shapes.items()
                     if sort == tree.cod and None not in shape)
        objects = shapes(self.category, max(shape))
        return tuple(objects[min(n, len(objects) - 1)] for n in shape)


def choose(productions: list, probabilities: list, draw: float, /):
    """
    The first production whose cumulative probability exceeds a uniform
    draw, the last one if rounding leaves the draw past them all.

    >>> choose(["box", "ax", "cut"], [.5, .25, .25], .6)
    'ax'
    """
    total = 0.
    for production, probability in zip(productions, probabilities):
        total += probability
        if draw < total:
            return production
    return productions[-1]


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
            count = len(self.bound)
            try:
                atom = self.ob(f"?{count}")
            except MISMATCH:
                atom = self.ob(PLACEHOLDERS + count)
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


@lru_cache(maxsize=None)
def LogSumExp() -> type:  # pylint: disable=invalid-name  # a sympy function
    """
    The :mod:`sympy` function :math:`\\log \\sum_i \\exp(x_i)`, unevaluated,
    which :func:`sympy.lambdify` prints by name, so that a module may give
    it a meaning, e.g. :func:`cvxpy.log_sum_exp`.
    """
    # pylint: disable-next=import-outside-toplevel
    import sympy
    return type("LogSumExp", (sympy.Function, ), {})
