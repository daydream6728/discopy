from discopy import cat, grammar, monoidal
from discopy.grammar.thue import Rule, Word, Ty
from discopy.utils import dumps, loads


def test_dagger():
    n, s = Ty('n'), Ty('s')
    rule, word = Rule(n @ n, s, name='r'), Word('a', n, data=42)
    assert (rule[::-1].dom, rule[::-1].cod) == (s, n @ n)
    assert (word[::-1].dom, word[::-1].cod) == (n, Ty())
    for box in (rule, word):
        assert box[::-1][::-1] == box != box[::-1]
        assert (box >> box[::-1]).cod == box.dom
        for x in (box, box[::-1]):
            assert eval(repr(x), dict(
                cat=cat, monoidal=monoidal, grammar=grammar)) == x
            assert loads(dumps(x)) == x
