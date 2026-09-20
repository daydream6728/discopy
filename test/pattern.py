""" The sequent patterns, their collection and their matching. """

from typing import Annotated, TypeVar

from pytest import raises

from discopy import feedback, rigid
from discopy.abc import (
    Category, ColouredMonoid, DelayedMonoid, FeedbackCategory, Pregroup,
    ResiduatedMonoid)
from discopy.monoidal import Ty
from discopy.pattern import (
    C0, C1, SELF, Adjoint, Atom, Delay, Exp, HomType, L, Over, R, Repeat,
    Sequent, Sort, Tensor, Under, Unit, Var, interpret, parse)


x, y, z = map(Ty, "xyz")
A, B = (Var(name, Sort(bound=ColouredMonoid)) for name in "AB")
M = Var("M", Sort(atomic=True, bound=ColouredMonoid))
X = Var("X", Sort(atomic=True, bound=Pregroup))
D = Var("D", Sort(bound=DelayedMonoid))
E = Var("E", Sort(bound=ResiduatedMonoid))
ONE = Unit(A.sort)


def test_subscripts():
    """ A pattern class subscripted with type parameters is the pattern. """
    def cups[V: Atom, N](
            cls, left: Annotated[C0, V], right: Annotated[C0, R[V]]
    ) -> Annotated[C1, Tensor[V, R[V]], Unit[C0]]:
        ...
    conclusion = interpret(
        cups.__annotations__["return"],
        {"V": Sort("C0", atomic=True, bound=Pregroup)})
    assert str(conclusion) == "C1[V @ V.r, Unit[C0]]"

    def spider[V: Atom, N, K](cls) -> Annotated[C1, Repeat[V, N], V]:
        ...
    assert str(interpret(
        spider.__annotations__["return"],
        {"V": Sort("C0", atomic=True), "N": Sort("Count")}))\
        == "C1[V ** N, V]"

    def wait[V: Atom, W](cls) -> Annotated[
            C1, Tensor[L[V], Delay[W]], Tensor[Over[V, W], Under[W, V]]]:
        ...
    assert str(interpret(
        wait.__annotations__["return"],
        {"V": Sort("C0", atomic=True), "W": Sort("C0")}))\
        == "C1[V.l @ W.d, (V << W) @ (W >> V)]"

    assert A @ M == Tensor((A, M)) and (E << M) == Exp("<<", E, M)
    assert Atom[Sort("C0")] == Sort("C0", atomic=True)
    assert Atom[TypeVar("C1")] == Sort("C1", atomic=True)
    assert Atom[TypeVar("C0", bound=Pregroup)].bound is Pregroup
    assert Atom[Pregroup].bound is Pregroup and Atom[Pregroup].atomic
    assert Atom[SELF.dom.ob] == Sort("Self.dom.ob", atomic=True)
    with raises(TypeError):
        Atom[A]
    with raises(TypeError):
        Tensor[A]
    with raises(TypeError):
        Repeat[A, 2]
    with raises(TypeError):
        interpret("A @ M", {})
    with raises(TypeError):
        interpret(1, {})
    with raises(AttributeError):
        A.__wrapped__


def test_parse():
    def then[A: C0, B: C0, C: C0](
            self: C1[A, B], other: C1[B, C]) -> C1[A, C]:
        ...
    sequent = parse(then)
    assert list(sequent.variables) == ["A", "B", "C"]
    assert list(sequent.premises) == ["self", "other"]
    assert str(sequent.conclusion) == "C1[A, C]"
    assert parse(then, conclusion=False).conclusion is None

    def law(cls, x: Atom[C0], n: int = 1, *args, **kwargs):
        ...
    assert list(parse(law, conclusion=False).premises) == ["x"]
    assert str(parse(lambda cls: None, conclusion=False)) == ""
    with raises(TypeError):
        parse(law)
    namespace = {}
    exec(compile(  # A module deferring its annotations states strings.
        "from __future__ import annotations\ndef eager(cls, f: int): ...",
        "<deferred>", "exec", dont_inherit=True), namespace)
    with raises(TypeError, match="__future__"):
        parse(namespace["eager"], conclusion=False)

    def unsorted[A: C1[A, A]](cls, f: A):
        ...
    with raises(TypeError):
        parse(unsorted, conclusion=False)
    assert str(FeedbackCategory.feedback_right.sequent) == (
        "A: C0, B: C0, M: Atom[C0] | self: C1[A @ M.d, B @ M] ⊢ C1[A, B]")
    assert FeedbackCategory.feedback_left.sequent.variables["M"].bound\
        is DelayedMonoid


def test_match():
    assert list(A.match(None)) == [({}, ())]
    assert [s for s, _ in (M @ A).match(x @ y)] == [{"M": x, "A": y}]
    assert list((M @ M).match(x)) == []
    assert list(ONE.match(x)) == []
    assert list((A @ A).match(x @ y)) == []
    assert [s for s, _ in (A @ A).match(x @ x)] == [{"A": x}]
    assert next(X.r.match(rigid.Ty("x").r))[0] == {"X": rigid.Ty("x")}
    subst, residuals = next((X << X).match(x))
    assert subst == {} and residuals == ((X << X, x), )
    subst, residuals = next(D.d.match(x))
    assert residuals == ((D.d, x), )


def test_instantiate():
    subst = {"A": x @ y, "M": z}
    assert (A @ M).instantiate(subst, Ty) == x @ y @ z
    assert ONE.instantiate(subst, Ty) == Ty()
    assert X.r.instantiate({"X": rigid.Ty("z")}, rigid.Ty) == rigid.Ty("z").r
    assert D.d.instantiate({"D": feedback.Ty("z")}, feedback.Ty)\
        == feedback.Ty("z").d
    assert HomType(A, M).instantiate(subst, Ty) == (x @ y, z)
    assert (A @ M).variables == ("A", "M") and (E << E).variables == ("E", "E")


def test_hom_match():
    hom = HomType(A @ B, A)
    assert [s for s, _ in hom.match((x @ y, x))] == [{"A": x, "B": y}]
    assert [s for s, _ in hom.match((None, x))] == [{"A": x}]
    assert list(hom.match((x @ y, y))) == []


def test_sequent_str():
    assert str(Sequent()) == ""
    assert str(Sequent({"A": Sort()}, {"f": HomType(A, A)}, HomType(A, A)))\
        == "A: C0 | f: C1[A, A] ⊢ C1[A, A]"
    assert str(Sequent(premises={"x": Sort("C0", atomic=True)}))\
        == "x: Atom[C0]"


def test_level():
    """ A pattern needs the level its known objects are bounded by. """
    assert Var.level() is Category and Tensor.level() is ColouredMonoid
    assert Adjoint.level() is Pregroup and Delay.level() is DelayedMonoid
    assert Exp.level() is ResiduatedMonoid and Unit.level() is ColouredMonoid
    assert X.l == Adjoint(X, "l") and X.r == Adjoint(X, "r")
    assert (X << X) == Exp("<<", X, X) and (E >> X) == Exp(">>", E, X)
    assert (X @ D).l == Adjoint(Tensor((X, D)), "l") and D.d == Delay(D)
    assert X.l.r.bound is Pregroup and Unit(X.sort).bound is Pregroup
    for build in (lambda: X.d, lambda: D.r, lambda: D >> D,
                  lambda: (A @ X).d, lambda: Adjoint(A, "r")):
        with raises(TypeError, match="needs a"):
            build()
    unknown = Var("U", Sort())
    assert (unknown @ A).bound is None  # Checked by parse, with the owner.

    def snake[U: Atom](cls, u: Annotated[C0, U]) -> Annotated[
            C1, Tensor[U, R[U]], Unit[C0]]:
        ...
    from discopy.abc import MonoidalCategory, RigidCategory
    with raises(TypeError, match="needs a"):
        parse(snake, owner=MonoidalCategory)
    assert parse(snake, owner=RigidCategory).conclusion is not None
    with raises(AttributeError):
        A.z
