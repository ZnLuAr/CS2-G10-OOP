from __future__ import annotations

from src.structures import PriceBST


def test_empty_range_query_returns_empty_list():
    tree = PriceBST()
    assert tree.range_query(1, 10) == []


def test_range_query_is_inclusive_and_sorted_by_price_order():
    tree = PriceBST()
    tree.insert(20, "b")
    tree.insert(10, "a")
    tree.insert(30, "c")

    assert tree.range_query(10, 20) == ["a", "b"]


def test_duplicate_prices_are_all_returned():
    tree = PriceBST()
    tree.insert(10, "a")
    tree.insert(10, "b")
    tree.insert(20, "c")

    assert tree.range_query(10, 10) == ["a", "b"]
