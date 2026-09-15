""" The sequent patterns, their reading and their matching. """

from __future__ import annotations

from typing import TypeVar

from pytest import raises

from discopy import feedback, rigid
from discopy.abc import (
    DelayedMonoid, FeedbackCategory, Pregroup, ResiduatedMonoid)
from discopy.monoidal import Ty
from discopy.pattern import (
    C0, C1, Atom, Attr, Bool, Choice, Hom, Op, Sequent, Sort, Tensor, Unit,
    Var, parse, read)


x, y, z = map(Ty, "xyz")
A, B = Var("A", Sort()), Var("B", Sort())
M = Var("M", Sort(atomic=True))
X = Var("X", Sort(atomic=True, bound=Pregroup))
D = Var("D", Sort(bound=DelayedMonoid))
L = Var("L", Bool())


def test_read():
    sorts = {"A": Sort(), "M": Sort(atomic=True)}
    assert read("A @ M", sorts) == Tensor((A, M))
    assert read("(A @ M) @ A", sorts) == Tensor((A, M, A))
    assert read("1", sorts) == Unit()
    rigid = {"M": Sort(atomic=True, bound=Pregroup)}
    assert read("M.r", rigid) == Attr(Var("M", rigid["M"]), "r")
    residuated = {"A": Sort(bound=ResiduatedMonoid), **rigid}
    assert read("(A @ M) << 1", residuated) == Op("<<", Tensor((
        Var("A", residuated["A"]), Var("M", rigid["M"]))), Unit())
    assert read("C0", sorts) == Sort("C0")
    assert read("Atom[C0]", sorts) == Sort("C0", atomic=True)
    assert read("Self.dom.ob", sorts) == Sort("Self.dom.ob")
    assert read("Self.dom.ar[A, M]", sorts) == Hom(A, M, "Self.dom.ar")
    assert A @ M == Tensor((A, M)) and 1 @ A == Tensor((Unit(), A))
    assert Atom[Sort("C0")] == Sort("C0", atomic=True)
    assert Atom[TypeVar("C1")] == Sort("C1", atomic=True)
    assert Atom[TypeVar("C0", bound=Pregroup)].bound is Pregroup
    with raises(TypeError):
        Atom[A]
    with raises(AttributeError):
        A.__wrapped__
    assert str(read("C1[A @ M.r, 1]", {"A": Sort(), **rigid}))\
        == "C1[A @ M.r, 1]"
    with raises(TypeError):
        read("A ** 2", sorts)
    with raises(TypeError):
        read("C0 @ A", sorts)
    with raises(TypeError):
        read("C1[A]", sorts)


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

    def unsorted[A: C1[A, A]](cls, f: A):
        ...
    with raises(TypeError):
        parse(unsorted, conclusion=False)
    assert str(parse(FeedbackCategory.feedback.function)) == (
        "X: C0, Y: C0, M: Atom[C0] | self: C1[X @ M.d, Y @ M] ⊢ C1[X, Y]")
    assert FeedbackCategory.feedback.sequent.variables["M"].bound\
        is DelayedMonoid
    namespace, source = {}, "def eager(cls, f: int): ..."
    exec(compile(source, "<eager>", "exec", dont_inherit=True), namespace)
    with raises(TypeError, match="__future__"):
        parse(namespace["eager"], conclusion=False)


def test_match():
    assert list(A.match(None)) == [({}, ())]
    assert [s for s, _ in Tensor((M, A)).match(x @ y)] == [
        {"M": x, "A": y}]
    assert list(Tensor((M, M)).match(x)) == []
    assert list(Unit().match(x)) == []
    assert list(Tensor((A, A)).match(x @ y)) == []
    assert [s for s, _ in Tensor((A, A)).match(x @ x)] == [{"A": x}]
    assert next(X.r.match(rigid.Ty("x").r))[0] == {"X": rigid.Ty("x")}
    subst, residuals = next((X << X).match(x))
    assert subst == {} and residuals == ((X << X, x), )
    subst, residuals = next(D.d.match(x))
    assert residuals == ((D.d, x), )


def test_instantiate():
    subst = {"A": x @ y, "M": z}
    assert Tensor((A, M)).instantiate(subst, Ty) == x @ y @ z
    assert Unit().instantiate(subst, Ty) == Ty()
    assert X.r.instantiate({"X": rigid.Ty("z")}, rigid.Ty) == rigid.Ty("z").r
    assert D.d.instantiate({"D": feedback.Ty("z")}, feedback.Ty)\
        == feedback.Ty("z").d
    assert Hom(A, M).instantiate(subst, Ty) == (x @ y, z)
    assert Tensor((A, M)).variables == ("A", "M")
    assert (X << M).variables == ("X", "M")


def test_hom_match():
    hom = Hom(Tensor((A, B)), A)
    assert [s for s, _ in hom.match(x @ y, x)] == [{"A": x, "B": y}]
    assert [s for s, _ in hom.match(None, x)] == [{"A": x}]
    assert list(hom.match(x @ y, y)) == []


def test_sequent_str():
    assert str(Sequent()) == ""
    assert str(Sequent({"A": Sort()}, {"f": Hom(A, A)}, Hom(A, A)))\
        == "A: C0 | f: C1[A, A] ⊢ C1[A, A]"
    assert str(Sequent(premises={"x": Sort("C0", atomic=True)}))\
        == "x: Atom[C0]"


def test_member():
    """ A pattern only does what the bound of its sort allows. """
    assert X.l == Attr(X, "l") and X.r == Attr(X, "r")
    assert (X << X) == Op("<<", X, X) and (1 >> X) == Op(">>", Unit(), X)
    assert (1 >> X).bound is Pregroup and (X << 1) == Op("<<", X, Unit())
    assert (X @ D).l == Attr(Tensor((X, D)), "l") and D.d == Attr(D, "d")
    assert X.l.r.bound is Pregroup and Unit().bound is None
    for pattern, name in ((A, "l"), (X, "d"), (D, "r"), (Unit(), "l")):
        with raises(TypeError, match=f"no {name}"):
            getattr(pattern, name)
    with raises(TypeError, match="no over"):
        A << M
    with raises(TypeError, match="no under"):
        D >> D
    with raises(TypeError, match="no d"):
        (A @ X).d
    with raises(TypeError, match="no r"):
        Attr(A, "r")


def test_choice():
    """ A boolean variable chooses between two patterns. """
    choice = L[A @ M, M @ A]
    assert choice == Choice(L, A @ M, M @ A)
    assert str(choice) == "L[A @ M, M @ A]"
    assert choice.variables == ("L", "A", "M", "M", "A")
    assert choice.instantiate({"L": True, "A": x @ y, "M": z}, Ty) == x @ y @ z
    assert choice.instantiate({"L": False, "A": x, "M": z}, Ty) == z @ x
    assert [s for s, _ in choice.match(x @ y)] == [
        {"L": True, "A": x, "M": y}, {"L": False, "M": x, "A": y}]
    assert [s for s, _ in choice.match(x @ y, {"L": False})]\
        == [{"L": False, "M": x, "A": y}]
    assert read("L[X, 1]", {"L": Bool(), "X": X.sort}) == L[X, 1]
    with raises(TypeError):
        A[X, 1]

    def ev[X: Atom[C0], Y: Atom[C0], L: Bool](
            cls, base: X, exponent: Y, left: L = True) -> C1[L[X @ Y, Y], X]:
        ...
    sequent = parse(ev)
    assert list(sequent.premises) == ["base", "exponent", "left"]
    assert sequent.keywords == {"left"}
    assert sequent.variables["L"] == Bool()
