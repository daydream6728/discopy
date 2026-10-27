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

**Colours.** A derivation is then coloured from the root down, see
:meth:`Specification.evaluate`: the variables of a rule that its conclusion
determines are read off the boundary asked of it, see :func:`match`, and the
others, e.g. the middle object of a cut, are drawn wire by wire from a
palette, uniformly. A derivation whose conclusion cannot meet the boundary
asked of it, e.g. a cup ``x @ x.r -> Ty()`` asked for ``x @ y -> Ty()``, is
rejected, so that the terms are drawn from the Boltzmann distribution of the
shapes, coloured uniformly, conditioned on being well-typed.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Production
    Specification
    Colouring

.. admonition:: Functions

    .. autosummary::
        :template: function.rst
        :nosignatures:
        :toctree:

        wire
        shapes
        match
        compile
"""

from __future__ import annotations

import inspect
import math
import random as std_random
from dataclasses import dataclass, field
from functools import cached_property, lru_cache
from itertools import product
from operator import index
from types import NoneType
from typing import TYPE_CHECKING, Any, TypeVar, get_args, get_origin

from discopy import monoidal
from discopy.abc import Nat
from discopy.axioms import (
    GENERATORS, Atom, Declaration, Delay, Hom, L, Obj, R, Repeat, Tensor,
    Unit, Var, substitute)
from discopy.grammar import cfg
from discopy.utils import AxiomError

if TYPE_CHECKING:
    import numpy
    from hypothesis import strategies as st

NUMBERS = 3
""" The numbers a variable ``N: Nat`` of a rule ranges over, from zero. """

SIZE = 4
""" The expected size of a derivation, by default. """

WIDTH = 2
""" The most wires on either side of a morphism of a derivation, by default.
"""

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
        data : The weight, a monomial in the parameters.
        shadow : The value of each variable of the rule in the instance,
            an object of as many wires as it is given, all of one colour.
    """
    # pylint: disable-next=too-many-arguments  # a rule and its shadow
    def __init__(self, dom: monoidal.Ty, cod: monoidal.Ty, name: str, *,
                 data=None, shadow: dict | None = None):
        super().__init__(dom, cod, name=name, data=data)
        self.shadow = dict(shadow or {})


def wire(category: type):
    """
    The object of one wire the shapes of a category are drawn with: named
    after the first of :data:`discopy.axioms.GENERATORS` when its objects
    take a name, the least of its generators otherwise, e.g. a dimension.

    >>> from discopy.monoidal import Ty, Diagram
    >>> assert wire(Diagram) == Ty('a')
    >>> from discopy.neural.network import Network
    >>> assert len(wire(Network)) == 1
    """
    ob = category.typeparams()[0]
    try:
        return ob(GENERATORS[0])
    except MISMATCH:
        # pylint: disable-next=import-outside-toplevel  # off the package
        from hypothesis import find, settings
        return find(generators(ob), lambda _: True,
                    settings=settings(database=None))


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
        if max(map(max, shape)) <= width:
            yield scope, shape[0], shape[1:]


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
        if rule.applicable and name in (within or category).rules)
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


def match(pattern, obj, scope: dict, shadow: dict) -> None:
    """
    Bind the variables of a pattern, an object expression of a rule, so that
    it substitutes to the object ``obj`` in the ``scope``, inverting each
    former: a tensor splits by the number of wires its factors have in the
    ``shadow`` scope, an adjoint is undone by the other adjoint and a delay
    by a delay back. An expression with no inverse, e.g. an exponential,
    binds nothing, the conclusion being checked against the goal once the
    other variables are drawn.

    >>> from discopy.rigid import Ty
    >>> X = TypeVar("X")
    >>> scope = {}
    >>> match(Tensor[X, L[X]], Ty('x') @ Ty('x').l, scope,
    ...       {X: Ty('a')})
    >>> assert scope == {X: Ty('x')}
    """
    if isinstance(pattern, TypeVar):
        scope.setdefault(pattern, obj)
        return
    origin, args = get_origin(pattern), get_args(pattern)
    if origin is Tensor:
        start = 0
        for arg in args:
            stop = start + length(substitute(arg, shadow))
            match(arg, obj[start:stop], scope, shadow)
            start = stop
    elif origin in (L, R):
        match(args[0], obj.r if origin is L else obj.l, scope, shadow)
    elif origin is Delay:
        match(args[1], obj.delay(-1), scope, shadow)
    elif origin is Repeat and index(substitute(args[1], shadow)):
        match(args[0], obj[:length(substitute(args[0], shadow))],
              scope, shadow)
    elif origin not in (Unit, Repeat):
        return


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
            coefficients.append(float(production.data.subs(
                {p: 1 for p in self.parameters})))
        return coefficients, exponents

    def logarithms(self) -> tuple[tuple, tuple, list]:
        """
        The system in log-space, :math:`t_s \\geq \\log \\sum_r \\exp(\\theta
        \\cdot m_r + \\sum_p t_p)`: the logarithm of each parameter, that of
        each sort and the right-hand side of each sort, a :func:`LogSumExp`.
        """
        # pylint: disable-next=import-outside-toplevel
        import sympy
        thetas = tuple(sympy.Symbol(f"log_{p}") for p in self.parameters)
        logs = {sort: sympy.Symbol(f"t[{sort}]") for sort in self.sorts}
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

    def probabilities(self, params: dict) -> dict:
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
        choices: dict = {sort: ([], []) for sort in self.sorts}
        for production, term, sort in zip(
                self.productions, terms, conclusions):
            choices[production.cod][0].append(production)
            choices[production.cod][1].append(float(term / values[sort]))
        self.cache[key] = choices
        return choices

    def sample(self, random: std_random.Random, params: dict,
               sort: monoidal.Ty | None = None,
               max_size: int | None = None) -> cfg.Tree | None:
        """
        A derivation of a sort, the root by default, drawn exactly from the
        Boltzmann distribution at the parameters given a source of uniform
        randomness, or ``None`` as soon as it grows past ``max_size``.
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
                branches = built[len(built) - arity:]
                del built[len(built) - arity:]
                built.append(production(*branches) if arity else production)
                continue
            size += 1
            if max_size is not None and size > max_size:
                return None
            productions, probabilities = choices[sort_]
            production = choose(productions, probabilities, random.random())
            stack.append((sort_, production))
            stack += [(monoidal.Ty(wire), None)
                      for wire in reversed(production.dom.inside)]
        return built[0]

    def palette(self, *goal) -> tuple:
        """
        The atoms of the boundary asked for, from which the wires no boundary
        determines are coloured, besides those drawn by
        :meth:`strategy`.
        """
        ob = self.category.typeparams()[0]
        if ob is NoneType:
            return (None, )
        return tuple(dict.fromkeys(
            obj[i:i + 1] if hasattr(obj, "__len__") else obj
            for obj in goal if obj is not None
            for i in range(length(obj))))

    def kinds(self, production: Production, dom, cod,
              colouring: Colouring) -> dict | None:
        """
        The premises of the rule of a production concluding ``dom -> cod``,
        by name, or ``None`` when it cannot: the variables its conclusion
        determines are matched against the boundary, see :func:`match`, and
        the others coloured by the ``colouring``.
        """
        rule = self.category.rules[production.name]
        annotations = rule.annotations()
        scope: dict = {}
        try:
            for pattern, side in zip(
                    boundary(annotations["return"]), (dom, cod)):
                match(pattern, side, scope, production.shadow)
            scope = {**production.shadow, **{
                variable: scope[variable] if variable in scope
                else colouring.colour(production.shadow[variable])
                for variable in inspect.unwrap(rule.function).__type_params__}}
            if boundary(rule.output(scope)) != (dom, cod):
                return None
            return {parameter.name: substitute(
                annotations[parameter.name], scope)
                for parameter in rule.parameters}
        except MISMATCH:
            return None

    def evaluate(self, tree: cfg.Tree, dom, cod, colouring: Colouring):
        """
        The term a derivation denotes from ``dom`` to ``cod``, coloured from
        the root down, or ``None`` when it cannot meet that boundary: the
        rule of its root is applied to its :meth:`kinds` of premises, a
        morphism premise the term of the branch evaluated at the boundary
        it asks for, and a generator is drawn by the ``colouring``.
        """
        production, branches = tree.root, iter(tree.branches)
        assert isinstance(production, Production)
        if production.name == "any":
            return self.evaluate(next(branches), dom, cod, colouring)
        if production.name == "box":
            return colouring.generator(dom, cod)
        kinds = self.kinds(production, dom, cod, colouring)
        if kinds is None:
            return None
        arguments = {}
        for name, kind in kinds.items():
            arguments[name] = get_args(kind)[1] if get_origin(kind) is Var\
                else self.evaluate(next(branches), *boundary(kind), colouring)
            if arguments[name] is None:
                return None
        return self.category.rules[production.name](**arguments)

    def strategy(  # pylint: disable=too-many-arguments  # a boundary, bounds
            self, dom=None, cod=None, *, size: float = SIZE,
            max_size: int | None = None, exact: bool = True,
            **marks) -> st.SearchStrategy:
        """
        The :mod:`hypothesis` strategy of the terms from ``dom`` to ``cod``,
        any if ``None``, Boltzmann sampled at the parameters :meth:`tune`
        gives the root, of at most ``max_size`` nodes, ten times the expected
        size by default: a derivation of the shape of the boundary is drawn
        and coloured, see :meth:`evaluate`, again until one is well-typed.
        The generators are drawn by the ``generators`` of the category, the
        colours of its wires from the atoms of the boundary and those of
        one or two wires drawn by the ``generators`` of its objects.

        Parameters:
            dom : The domain, any if ``None``.
            cod : The codomain, any if ``None``.
            size : The expected size of a derivation of the root.
            max_size : The size past which a derivation is rejected.
            exact : Whether to draw from :func:`hypothesis.strategies.randoms`
                with ``use_true_random``, i.e. from the Boltzmann
                distribution exactly, or from the choices of Hypothesis,
                which shrink to the first production of each sort.
            marks : The expected applications of the rules, by name.

        >>> from hypothesis import find
        >>> from discopy.monoidal import Ty, Diagram
        >>> x, y = Ty('x'), Ty('y')
        >>> spec = compile(Diagram)
        >>> term = find(spec.strategy(x, x @ y), lambda f: len(f) > 1)
        >>> assert (term.dom, term.cod) == (x, x @ y)
        """
        # pylint: disable-next=import-outside-toplevel
        from hypothesis import reject, strategies as st
        params = self.tune(size, **marks)
        max_size = max_size or int(10 * size)
        shape = tuple(None if side is None else length(side)
                      for side in (dom, cod))
        sort = self.root if len(self.shapes) == 1 else self.shapes.get(shape)
        if sort is None:
            raise ValueError(f"No sort of shape {shape} in {self}.")

        ob = self.category.typeparams()[0]

        @st.composite
        def terms(draw):
            random = draw(st.randoms(use_true_random=exact))
            palette = self.palette(dom, cod)
            if ob is not NoneType:
                palette += tuple(draw(generators(ob), label="colour")
                                 for _ in range(2 - min(1, len(palette))))
            for _ in range(100):
                tree = self.sample(random, params, sort, max_size)
                if tree is None:
                    continue
                colouring = Colouring(random, palette, lambda x, y: draw(
                    self.category.generators(dom=x, cod=y)))
                dom_, cod_ = (side if side is not None else colouring.colour(
                    shadow) for side, shadow in zip(
                        (dom, cod), self.sides(tree)))
                term = self.evaluate(tree, dom_, cod_, colouring)
                if term is not None:
                    return term
            return reject()

        return terms()

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


def choose(productions: list, probabilities: list, draw: float):
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


@dataclass
class Colouring:
    """
    How the wires and boxes of a derivation are drawn as it is evaluated:
    each wire no boundary determines uniformly from a ``palette`` by a source
    of randomness ``random``, each box by the ``generator`` of a boundary.
    """
    random: std_random.Random
    palette: tuple
    generator: Any

    def colour(self, shadow):
        """ An object of the shape of a shadow, its wires drawn uniformly. """
        if shadow is None or isinstance(shadow, Nat):
            return shadow
        atoms = [self.random.choice(self.palette)
                 for _ in range(length(shadow))]
        if not hasattr(shadow, "tensor"):
            return atoms[0]
        return type(shadow)().tensor(*atoms)


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
