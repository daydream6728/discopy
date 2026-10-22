from pytest import importorskip

from discopy import cat, grammar, monoidal
from discopy.grammar.cfg import Tree, Rule, Word, Id, Ty

x = Ty('x')
f, w = Rule(x @ x, x, name='f'), Word('w', x)


def test_eq_and_hash():
    tree = f(f(w, w), Id(x))
    assert tree.cod == x and tree == f(f(w, w), Id(x)) and tree != 5
    assert {tree: 1, f: 2, w: 3}[f(f(w, w), Id(x))] == 1
    assert Tree(w) == w == Tree(w) and hash(Tree(w)) == hash(w)
    spider = Word('w', x, draw_as_spider=True, color='red')
    assert spider.to_diagram().draw_as_spider
    assert f(spider, spider).to_diagram().boxes[0].color == 'red'


def test_repr():
    namespace = dict(cat=cat, monoidal=monoidal, grammar=grammar)
    for tree in (f, f[::-1], w, Id(x), f(w, w), f(f(w, w), w)):
        assert eval(repr(tree), dict(namespace)) == tree


def test_dagger():
    assert (f[::-1].dom, f[::-1].cod) == (x, x @ x)
    assert (w[::-1].dom, w[::-1].cod) == (x, Ty())
    assert f[::-1][::-1] == f != f[::-1] and w[::-1][::-1] == w
    assert Id(x)[::-1] == Id(x) and str(f[::-1]) == "f[::-1]"
    assert f[::-1].to_diagram() == f.to_diagram()[::-1]


def test_from_nltk():
    nltk = importorskip("nltk")
    tree = Tree.from_nltk(nltk.Tree.fromstring("(S (NP I) (VP saw (NP him)))"))
    vp, np = Ty('VP'), Ty('NP')
    assert tree.branches[1] == Rule(vp @ np, vp, name='VP')(
        Word('saw', vp), Word('him', np))
    assert str(Tree.from_nltk(nltk.Tree.fromstring("(NP the big dog)")))\
        == "NP(the, big, dog)"
