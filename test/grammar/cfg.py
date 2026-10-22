from discopy.grammar.cfg import Tree, Rule, Word, Id, Ty

x = Ty('x')
f, w = Rule(x @ x, x, name='f'), Word('w', x)


def test_eq_and_hash():
    tree = f(f(w, w), Id(x))
    assert tree.cod == x and tree == f(f(w, w), Id(x)) and tree != 5
    assert {tree: 1, f: 2, w: 3}[f(f(w, w), Id(x))] == 1
    assert Tree(w) == w == Tree(w) and hash(Tree(w)) == hash(w)
    assert Word('w', x, draw_as_spider=True).draw_as_spider

