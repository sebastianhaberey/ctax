from unittest import TestCase

from src.EqualityUtils import equals, calculate_hash


class Foo:
    """
    Some class with a list of other classes
    """

    def __init__(self, value, values=None) -> None:
        self.value = value
        self.values = values

    def get_equality_relevant_items(self):
        items = [self.value]
        if self.values is not None:
            items.extend(self.values)
        return items

    def __eq__(self, other):
        return equals(self, other)

    def __hash__(self):
        return calculate_hash(self)


class RelaxedFoo:
    """
    Some class with a list of other classes where the order does not matter.
    """

    def __init__(self, value, values=None) -> None:
        self.value = value
        self.values = values

    def get_equality_relevant_items(self):
        items = [self.value]
        if self.values is not None:
            items.extend(self.values)
        return items

    def __eq__(self, other):
        return equals(self, other, relaxed_order=True)

    def __hash__(self):
        return calculate_hash(self, relaxed_order=True)


class TestEqualityUtils(TestCase):

    def test_equals(self):
        foo1 = Foo(2, [Foo(3), Foo(5)])
        foo2 = Foo(2, [Foo(3), Foo(5)])

        self.assertEqual(foo1, foo2)

    def test_equals_not_equal(self):
        foo1 = Foo(2, [Foo(3), Foo(5)])
        foo2 = Foo(3, [Foo(3), Foo(5)])

        self.assertNotEqual(foo1, foo2)

    def test_equals_not_equal_strict_order(self):
        foo1 = Foo(2, [Foo(3), Foo(5)])
        foo2 = Foo(2, [Foo(5), Foo(3)])

        self.assertNotEqual(foo1, foo2)

    def test_equals_relaxed_order(self):
        foo1 = RelaxedFoo(2, [RelaxedFoo(3), RelaxedFoo(5)])
        foo2 = RelaxedFoo(2, [RelaxedFoo(5), RelaxedFoo(3)])

        self.assertEqual(foo1, foo2)

    def test_hash(self):
        foo1 = Foo(2, [Foo(3), Foo(5)])
        foo2 = Foo(2, [Foo(3), Foo(5)])

        self.assertEqual(foo1.__hash__(), foo2.__hash__())

    def test_hash_not_equal(self):
        foo1 = Foo(2, [Foo(3), Foo(5)])
        foo2 = Foo(3, [Foo(3), Foo(5)])

        self.assertNotEqual(foo1.__hash__(), foo2.__hash__())

    def test_hash_not_equal_strict_order(self):
        foo1 = Foo(2, [Foo(3), Foo(5)])
        foo2 = Foo(2, [Foo(5), Foo(3)])

        self.assertNotEqual(foo1.__hash__(), foo2.__hash__())

    def test_hash_relaxed_order(self):
        foo1 = RelaxedFoo(2, [RelaxedFoo(3), RelaxedFoo(5)])
        foo2 = RelaxedFoo(2, [RelaxedFoo(5), RelaxedFoo(3)])

        self.assertEqual(foo1.__hash__(), foo2.__hash__())
