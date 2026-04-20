"""Transaction 数据模型（字段容器 + JSON 互转）。

字段定义见 docs/data-design.md §6。
``transactions.json`` 是 append-only，不允许覆盖既有记录。
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Transaction"]




@dataclass(frozen=True)
class Transaction:
    transaction_id: str
    listing_id: str
    buyer_id: str
    seller_id: str
    item_id: str
    count: int
    price: int
    total: int
    completed_at: str

    @classmethod
    def from_dict(cls, d: dict) -> "Transaction":
        return cls(
            transaction_id=d["transaction_id"],
            listing_id=d["listing_id"],
            buyer_id=d["buyer_id"],
            seller_id=d["seller_id"],
            item_id=d["item_id"],
            count=d["count"],
            price=d["price"],
            total=d["total"],
            completed_at=d["completed_at"],
        )

    def to_dict(self) -> dict:
        return {
            "transaction_id": self.transaction_id,
            "listing_id": self.listing_id,
            "buyer_id": self.buyer_id,
            "seller_id": self.seller_id,
            "item_id": self.item_id,
            "count": self.count,
            "price": self.price,
            "total": self.total,
            "completed_at": self.completed_at,
        }
