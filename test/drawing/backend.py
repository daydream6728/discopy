from pytest import raises

from discopy.drawing.backend import TikZ
from discopy.monoidal import Ty, Box


def test_draw_raises_on_relabeled_box(tmp_path):
    """ Drawing a relabeled box over an existing baseline raises. """
    x, y = Ty('x'), Ty('y')
    path = tmp_path / "box.svg"
    Box('f', x, y).draw(doctest=path, show=False)
    with raises(ValueError, match="Drawing differs"):
        Box('g', x, y).draw(doctest=path, show=False)


def test_tikz_wire_separates_its_style_keys():
    tikz = TikZ()
    tikz.draw_wire((0, 0), (1, 2), style="->")
    assert "->, looseness=" in tikz.edgelayer[-1]


def test_tikz_twist_in_an_xcolor_name(tmp_path):
    from discopy import ribbon
    path = tmp_path / "twist.tikz"
    ribbon.Diagram.twist(ribbon.Ty('x')).to_ribbons(colour='RoyalPurple')\
        .draw(path=str(path), to_tikz=True)
    tikz = path.read_text()
    assert "fill=RoyalPurple," in tikz
    assert "fill=RoyalPurple!60!black," in tikz


def test_tikzstyle_of_a_hexcode_has_no_hash(tmp_path):
    path = tmp_path / "box.tikz"
    Box('f', Ty('x'), Ty('x'), color='#336699').draw(
        path=str(path), to_tikz=True, use_tikzstyles=True)
    tikz, styles = path.read_text(), path.with_suffix(".tikzstyles")\
        .read_text()
    assert "style=336699_box" in tikz
    assert "\\tikzstyle{336699_box}" in styles
    assert "#" not in tikz + styles
