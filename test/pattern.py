""" The sequent patterns, their reading and their matching. """

from __future__ import annotations

from typing import TypeVar

from pytest import raises

from discopy import feedback, rigid
from discopy.abc import (
    Category, ColouredMonoid, DelayedMonoid, FeedbackCategory, Pregroup,
    ResiduatedMonoid)
from discopy.monoidal import Ty
from discopy.pattern import (
    C0, C1, Adjoint, Atom, Delay, Exp, Hom, Sequent, Sort, Tensor, Unit,
    Var, parse, read)


x, y, z = map(Ty, "xyz")
A, B = (Var(name, Sort(bound=ColouredMonoid)) for name in "AB")
M = Var("M", Sort(atomic=True, bound=ColouredMonoid))
X = Var("X", Sort(atomic=True, bound=Pregroup))
D = Var("D", Sort(bound=DelayedMonoid))
E = Var("E", Sort(bound=ResiduatedMonoid))
ONE = Unit(A.sort)


def test_read():
    sorts = {"A": A.sort, "M": M.sort}
    assert read("A @ M", sorts) == Tensor((A, M))
    assert read("(A @ M) @ A", sorts) == Tensor((A, M, A))
    assert read("Unit[C0]", sorts) == ONE
    assert read("M.r", {"M": X.sort}) == Adjoint(Var("M", X.sort), "r")
    residuated = {"A": E.sort, "M": X.sort}
    assert read("(A @ M) << Unit[C0]", residuated) == Exp("<<", Tensor((
        Var("A", E.sort), Var("M", X.sort))), Unit(E.sort))
    assert read("C0", sorts) == Sort("C0")
    assert read("Atom[C0]", sorts) == Sort("C0", atomic=True)
    assert read("Self.dom.ob", sorts) == Sort("Self.dom.ob")
    assert read("Self.dom.ar[A, M]", sorts) == Hom(A, M, "Self.dom.ar")
    assert str(read("C1[A @ M.r, Unit[C0]]", {"A": A.sort, "M": X.sort}))\
        == "C1[A @ M.r, Unit[C0]]"
    assert A @ M == Tensor((A, M)) and (E << M) == Exp("<<", E, M)
    assert Atom[Sort("C0")] == Sort("C0", atomic=True)
    assert Atom[TypeVar("C1")] == Sort("C1", atomic=True)
    assert Atom[TypeVar("C0", bound=Pregroup)].bound is Pregroup
    assert Atom[Pregroup].bound is Pregroup and Atom[Pregroup].atomic
    for source in ("A ** 2", "C0 @ A", "C1[A]", "1 @ A"):
        with raises(TypeError):
            read(source, sorts)
    with raises(TypeError):
        Atom[A]
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
    namespace, source = {}, "def eager(cls, f: int): ..."
    exec(compile(source, "<eager>", "exec", dont_inherit=True), namespace)
    with raises(TypeError, match="__future__"):
        parse(namespace["eager"], conclusion=False)

    def unsorted[A: C1[A, A]](cls, f: A):
        ...
    with raises(TypeError):
        parse(unsorted, conclusion=False)
    assert str(parse(FeedbackCategory.feedback_right.function)) == (
        "X: C0, Y: C0, M: Atom[C0] | self: C1[X @ M.d, Y @ M] ⊢ C1[X, Y]")
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
    assert Hom(A, M).instantiate(subst, Ty) == (x @ y, z)
    assert (A @ M).variables == ("A", "M") and (E << E).variables == ("E", "E")


def test_hom_match():
    hom = Hom(A @ B, A)
    assert [s for s, _ in hom.match((x @ y, x))] == [{"A": x, "B": y}]
    assert [s for s, _ in hom.match((None, x))] == [{"A": x}]
    assert list(hom.match((x @ y, y))) == []


def test_sequent_str():
    assert str(Sequent()) == ""
    assert str(Sequent({"A": Sort()}, {"f": Hom(A, A)}, Hom(A, A)))\
        == "A: C0 | f: C1[A, A] ⊢ C1[A, A]"
    assert str(Sequent(premises={"x": Sort("C0", atomic=True)}))\
        == "x: Atom[C0]"


def test_level():
    """ A pattern needs the level its objects are bounded by. """
    assert Var.level() is Category and Tensor.level() is ColouredMonoid
    assert Adjoint.level() is Pregroup and Delay.level() is DelayedMonoid
    assert Exp.level() is ResiduatedMonoid and Unit.level() is ColouredMonoid
    assert X.l == Adjoint(X, "l") and X.r == Adjoint(X, "r")
    assert (X << X) == Exp("<<", X, X) and (E >> X) == Exp(">>", E, X)
    assert (X @ D).l == Adjoint(Tensor((X, D)), "l") and D.d == Delay(D)
    assert X.l.r.bound is Pregroup and Unit(X.sort).bound is Pregroup
    unbounded = Var("U", Sort())
    for build in (lambda: unbounded @ A, lambda: X.d, lambda: D.r,
                  lambda: Unit(unbounded.sort), lambda: unbounded << A,
                  lambda: D >> D, lambda: (A @ X).d, lambda: Adjoint(A, "r"),
                  lambda: Tensor((unbounded, ))):
        with raises(TypeError, match="needs a"):
            build()
    with raises(AttributeError):
        A.z
