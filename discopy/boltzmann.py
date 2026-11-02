"""
Boltzmann samplers for the derivations of a free category of bounded width.

Instantiating the :attr:`discopy.cat.FreeCategory.rules` of a category at
every object of width at most ``width`` over a finite set of atoms gives a
context-free grammar: one nonterminal for each pair of objects ``(A, B)``,
the derivations from ``A`` to ``B``, and one production for each instance of
a rule whose premises and conclusion are all of bounded width, plus a fresh
generator for each pair. The size of a derivation is its number of nodes.

A `Boltzmann sampler <https://doi.org/10.1017/S0963548304006315>`_ draws a
derivation ``t`` with probability ``z ** |t| / V(z)``, where ``V`` is the
generating function of the grammar, computed by fixed-point iteration: two
derivations of the same size are equally likely and ``z`` tunes their
expected size, up to the singularity ``rho`` of ``V``, the critical
parameter, where the sizes are heavy-tailed.

Summary
-------

.. autosummary::
    :template: class.rst
    :nosignatures:
    :toctree:

    Production
    Grammar
"""

from __future__ import annotations

import inspect
import math
from dataclasses import dataclass, field
from functools import cache
from itertools import product
from typing import TYPE_CHECKING, Any, get_args, get_origin

import numpy as np

from discopy.testable import Atom, Hom, Obj, Var, substitute

if TYPE_CHECKING:
    from hypothesis import strategies as st


GENERATOR = "generator"
""" The kind of the production of a fresh generator. """


@dataclass(frozen=True)
class Production:
    """
    A production of a :class:`Grammar`: an instance of a rule, or a fresh
    generator if ``kind`` is :data:`GENERATOR`.

    Parameters:
        kind : The name of the rule, or :data:`GENERATOR`.
        lhs : The nonterminal it derives.
        children : The nonterminal of each morphism premise.
        premises : The name of each morphism premise.
        values : The values of the other premises, by name.
    """
    kind: str
    lhs: int
    children: tuple[int, ...] = ()
    premises: tuple[str, ...] = ()
    values: dict[str, Any] = field(default_factory=dict, hash=False)


@dataclass
class Grammar:
    """
    The derivations of a free category of bounded width as a context-free
    grammar, with a Boltzmann sampler, see :meth:`compile`.

    Parameters:
        category : The free category.
        types : The objects of bounded width.
        productions : The productions, those of each nonterminal in order of
            simplicity: the identity, then the generator, then the rules.
    """
    category: type
    types: tuple
    productions: tuple[Production, ...]
    tuned: dict = field(default_factory=dict, repr=False, compare=False)
    """ The parameter tuned to each size, root and bias, see :meth:`tune`. """

    @staticmethod
    @cache
    def compile(  # pylint: disable=too-many-locals  # one per part of a rule
            category: type, atoms: tuple, width: int,
            within: type | None = None,
            signature: tuple[tuple, ...] | None = None) -> Grammar:
        """
        Instantiate the applicable rules of ``category``, or those of
        ``within`` if given, at every object of width at most ``width`` over
        ``atoms``, each atomic variable at every atom and each number at
        every width. A rule with a premise that is neither a morphism nor a
        value, or an instance with an object of larger width, e.g. a delay,
        is left out. Given a ``signature``, i.e. the pairs of objects of the
        generators, the grammar only has generators of those types.

        >>> from discopy.monoidal import Diagram
        >>> grammar = Grammar.compile(Diagram, ("a", ), 1)
        >>> len(grammar.types), len(grammar.nonterminals)
        (2, 4)
        >>> sorted({p.kind for p in grammar.productions})
        ['ax', 'cut', 'generator', 'mix']
        """
        atoms = tuple(
            category.ob(x) if isinstance(x, str) else x for x in atoms)
        types = tuple(
            category.ob().tensor(*word) for n in range(width + 1)
            for word in product(atoms, repeat=n))
        index = {x: i for i, x in enumerate(types)}
        n_types = len(types)

        def nonterminal(hom):
            _, dom, cod = get_args(hom)
            if dom not in index or cod not in index:
                return None
            return index[dom] * n_types + index[cod]

        def domain(parameter):
            origin = get_origin(parameter.__bound__)
            if origin is Atom:
                return list(atoms)
            if origin is Obj:
                return list(types)
            return list(range(width + 1))

        productions = [
            Production(GENERATOR, index[x] * n_types + index[y])
            for x, y in product(types, repeat=2)
            if signature is None or (x, y) in signature]
        rules = (within or category).rules
        for name, rule in category.rules.items():
            if name not in rules or not rule.applicable:
                continue
            annotations, parameters = rule.annotations(), rule.parameters
            if any(get_origin(annotations[p.name]) not in (Hom, Var)
                   for p in parameters):
                continue
            variables = inspect.unwrap(rule.function).__type_params__
            outer = rule.scope(None, {v.__name__: None for v in variables})
            for values in product(*map(domain, variables)):
                scope = outer | dict(zip(variables, values))
                lhs = nonterminal(substitute(annotations["return"], scope))
                if lhs is None:
                    continue
                premises = {p.name: substitute(annotations[p.name], scope)
                            for p in parameters}
                homs = [p.name for p in parameters
                        if get_origin(premises[p.name]) is Hom]
                children = tuple(nonterminal(premises[p]) for p in homs)
                if None in children:
                    continue
                productions.append(Production(
                    name, lhs, children, tuple(homs), {
                        p: get_args(kind)[1] for p, kind in premises.items()
                        if p not in homs}))
        order = {"ax": 0, GENERATOR: 1}
        productions.sort(key=lambda p: (p.lhs, order.get(p.kind, 2)))
        return Grammar(category, types, tuple(productions))

    @property
    def nonterminals(self) -> list[tuple]:
        """ The pairs of objects each nonterminal derives. """
        return [(x, y) for x in self.types for y in self.types]

    def weights(self, z: float, bias: dict[str, float] | None = None
                ) -> np.ndarray:
        """
        The weight of each production, ``z`` for each node times the
        ``bias`` of its kind, e.g. ``{"generator": 2.}``, ``1`` by default.
        """
        bias = bias or {}
        return np.array([z * bias.get(p.kind, 1.) for p in self.productions])

    def values(self, z: float, bias: dict[str, float] | None = None,
               iterations: int = 100) -> np.ndarray | None:
        """
        The generating function of each nonterminal at ``z``, the least
        solution of the system of the grammar by Newton's method from zero,
        which converges monotonically below the singularity for a system of
        polynomials with positive coefficients (Esparza, Kiefer, Luttenberger
        2010), or :obj:`None` if it diverges, i.e. beyond the singularity.
        """
        n, weights = len(self.nonterminals), self.weights(z, bias)
        lhs = np.array([p.lhs for p in self.productions])
        children = np.array([
            p.children + (n, ) * (2 - len(p.children))
            for p in self.productions])
        current = np.zeros(n)
        for _ in range(iterations):
            extended = np.append(current, 1.)
            image = np.bincount(
                lhs, weights * extended[children].prod(axis=1), minlength=n)
            residual = image - current
            if np.abs(residual).max() <= 1e-12 * (1 + image.max()):
                return image
            jacobian = np.zeros((n, n + 1))
            for side, other in ((0, 1), (1, 0)):
                np.add.at(jacobian, (lhs, children[:, side]),
                          weights * extended[children[:, other]])
            try:
                step = np.linalg.solve(
                    np.eye(n) - jacobian[:, :n], residual)
            except np.linalg.LinAlgError:
                return None
            current = current + step
            if not np.all(np.isfinite(current)) or current.min() < 0\
                    or current.max() > 1e8:
                return None
        return None

    def singularity(self, bias: dict[str, float] | None = None) -> float:
        """ The critical parameter ``rho``, by bisection. """
        low, high = 0., 1.
        for _ in range(50):
            middle = (low + high) / 2
            low, high = (middle, high) if self.values(
                middle, bias) is not None else (low, middle)
        return low

    def expected_size(self, z: float, root: np.ndarray,
                      bias: dict[str, float] | None = None) -> float:
        """
        The expected number of nodes of a derivation from the nonterminals
        weighted by ``root``, i.e. ``z`` times the logarithmic derivative of
        their generating function.
        """
        step = z * 1e-6
        low, high = (self.values(x, bias) for x in (z - step, z + step))
        if low is None or high is None:
            return math.inf
        if root @ low == 0:
            return 0.
        return z * (math.log(root @ high) - math.log(root @ low)) / (2 * step)

    def tune(self, size: float, root: np.ndarray,
             bias: dict[str, float] | None = None) -> float:
        """
        The parameter whose expected size from ``root`` is ``size``, by
        bisection below the singularity, or just below it if ``size`` is
        infinite, i.e. critical sampling, computed once for each size, root
        and bias.
        """
        key = (size, root.tobytes(), tuple(sorted((bias or {}).items())))
        if key in self.tuned:
            return self.tuned[key]
        rho = self.singularity(bias)
        low, high = 0., rho * (1 - 1e-4)
        for _ in range(0 if math.isinf(size) else 40):
            middle = (low + high) / 2
            low, high = (middle, high) if self.expected_size(
                middle, root, bias) < size else (low, middle)
        self.tuned[key] = high if math.isinf(size) else low
        return self.tuned[key]

    def root(self, dom=None, cod=None) -> np.ndarray:
        """
        The indicator of the nonterminals a derivation from ``dom`` to
        ``cod`` starts from: all of them on a side not given or not of
        bounded width, which a generator then glues to the boundary.
        """
        return np.array([
            float((dom not in self.types or x == dom)
                  and (cod not in self.types or y == cod))
            for x, y in self.nonterminals])

    def strategy(  # pylint: disable=too-many-locals  # the sampler's tables
            self, dom=None, cod=None, size: float = 8.,
            max_nodes: int = 200, z: float | None = None,
            bias: dict[str, float] | None = None, exact: bool = False
            ) -> st.SearchStrategy:
        """
        Generate a term from ``dom`` to ``cod`` by the Boltzmann sampler of
        the grammar at ``z`` with the ``bias`` of each kind of production,
        ``z`` tuned to an expected ``size`` from any boundary if not given,
        once for the grammar rather than for each boundary, rejecting a
        derivation of more than ``max_nodes`` nodes.

        Each choice is a production drawn by a byte whose zero is the
        simplest, so that a term shrinks to the identity or a generator.
        Hypothesis draws neither bytes uniformly nor long sequences of them
        whole, so that the large terms the expected size counts are cut
        off: if ``exact``, the choices are drawn instead from a single
        random seed, as the Boltzmann distribution says, which no longer
        shrinks.
        """
        from hypothesis import strategies as st

        root = self.root(dom, cod)
        if root @ self.values(1e-3, bias) == 0:
            return st.nothing()
        z = self.tune(size, self.root(), bias) if z is None else z
        values = self.values(z, bias)
        extended = np.append(values, 1.)
        n = len(values)
        terms = self.weights(z, bias) * extended[np.array([
            p.children + (n, ) * (2 - len(p.children))
            for p in self.productions])].prod(axis=1)
        by_lhs = [[] for _ in range(n)]
        for i, p in enumerate(self.productions):
            by_lhs[p.lhs].append(i)
        resolution = 2 ** 8

        def pick(draw, weights, seed):
            x = seed.random() if exact\
                else draw(st.integers(0, resolution - 1)) / resolution
            cumulative = np.cumsum(weights)
            return int(np.searchsorted(
                cumulative, x * cumulative[-1], side="right"))

        @st.composite
        def terms_(draw):
            count = [0]
            seed = draw(st.randoms(use_true_random=True)) if exact else None

            def build(nonterminal):
                count[0] += 1
                if count[0] > max_nodes:
                    # pylint: disable-next=import-outside-toplevel  # too large
                    from hypothesis import reject
                    reject()
                candidates = by_lhs[nonterminal]
                production = self.productions[
                    candidates[pick(draw, terms[candidates], seed)]]
                children = [build(child) for child in production.children]
                if production.kind == GENERATOR:
                    x, y = self.nonterminals[nonterminal]
                    return draw(self.category.generators(dom=x, cod=y))
                rule = self.category.rules[production.kind]
                return rule(**production.values,
                            **dict(zip(production.premises, children)))

            term = build(pick(draw, root * values, seed))
            if dom is not None and term.dom != dom:
                term = draw(self.category.generators(
                    dom=dom, cod=term.dom)) >> term
            if cod is not None and term.cod != cod:
                term = term >> draw(self.category.generators(
                    dom=term.cod, cod=cod))
            return term

        return terms_()
