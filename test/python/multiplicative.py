# -*- coding: utf-8 -*-

from typing import List
from pytest import raises

from discopy.biclosed import *
from discopy.python import *


def test_Function():
    x, y, z = (complex, ), (bool, ), (float, )
    f = Function(dom=y, cod=exp(z, x),
                 inside=lambda y: lambda x: abs(x) ** 2 if y else 0)
    g = Function(dom=x + y, cod=z, inside=lambda x, y: f(y)(x))

    assert f.uncurry().curry()(True)(1j) == f(True)(1j)
    assert f.uncurry(left=False).curry(left=False)(True)(1j) == f(True)(1j)
    assert g.curry().uncurry()(1j, True) == g(1j, True)
    assert g.curry(left=False).uncurry(left=False)(1j, True) == g(1j, True)


def test_fixed_point():
    from math import sqrt
    phi = Function(lambda x=1: 1 + 1 / x, dom=(float,), cod=(float,)).fix()
    assert phi() == (1 + sqrt(5)) / 2


def test_trace():
    with raises(NotImplementedError):
        Function.id(int).trace(left=True)


def test_list_generic_in_function():
    func = Function(sum, List[int], int)
    assert func([1, 2, 3]) == 6


def test_copy_of_one_is_the_identity():
    """A single copy returns its argument, the way the identity does."""
    x = (int, )
    assert Function.copy(x, 1)(42) == Function.id(x)(42) == 42
    assert Function.copy(x, 0)(42) == ()
    assert Function.copy(x, 3)(42) == (42, 42, 42)
    assert Function.copy((int, str), 2)(42, "a") == (42, "a", 42, "a")
