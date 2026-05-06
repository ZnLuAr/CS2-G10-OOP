"""按价格索引挂单的二叉搜索树。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class _PriceNode:
    price: int
    values: list[Any] = field(default_factory=list)
    left: "_PriceNode | None" = None
    right: "_PriceNode | None" = None


class PriceBST:
    def __init__(self) -> None:
        self.root: _PriceNode | None = None

    def insert(self, price: int, value: Any) -> None:
        if self.root is None:
            self.root = _PriceNode(price=price, values=[value])
            return
        self._insert(self.root, price, value)

    def range_query(self, min_price: int, max_price: int) -> list[Any]:
        result: list[Any] = []
        self._range_query(self.root, min_price, max_price, result)
        return result

    def _insert(self, node: _PriceNode, price: int, value: Any) -> None:
        if price == node.price:
            node.values.append(value)
        elif price < node.price:
            if node.left is None:
                node.left = _PriceNode(price=price, values=[value])
            else:
                self._insert(node.left, price, value)
        else:
            if node.right is None:
                node.right = _PriceNode(price=price, values=[value])
            else:
                self._insert(node.right, price, value)

    def _range_query(
        self,
        node: _PriceNode | None,
        min_price: int,
        max_price: int,
        result: list[Any],
    ) -> None:
        if node is None:
            return
        if min_price < node.price:
            self._range_query(node.left, min_price, max_price, result)
        if min_price <= node.price <= max_price:
            result.extend(node.values)
        if node.price < max_price:
            self._range_query(node.right, min_price, max_price, result)
