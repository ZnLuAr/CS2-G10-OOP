"""Listing 数据模型（字段容器 + JSON 互转）。

字段定义见 docs/data-design.md §5。
业务方法（状态转换、撤销逻辑等）由 ``services/market.py`` 负责人实现。
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["Listing", "STATUS_ACTIVE", "STATUS_SOLD", "STATUS_CANCELLED"]


STATUS_ACTIVE = "active"
STATUS_SOLD = "sold"
STATUS_CANCELLED = "cancelled"




@dataclass
class Listing:
    listing_id: str
    seller_id: str
    item_id: str
    count: int
    price: int
    status: str = STATUS_ACTIVE
    created_at: str = ""
    closed_at: str | None = None
    instance_state: dict | None = None        # 上架瞬间的实例状态快照

    @classmethod
    def from_dict(cls, d: dict) -> "Listing":
        return cls(
            listing_id=d["listing_id"],
            seller_id=d["seller_id"],
            item_id=d["item_id"],
            count=d["count"],
            price=d["price"],
            status=d.get("status", STATUS_ACTIVE),
            created_at=d.get("created_at", ""),
            closed_at=d.get("closed_at"),
            instance_state=d.get("instance_state"),
        )

    def to_dict(self) -> dict:
        out: dict = {
            "listing_id": self.listing_id,
            "seller_id": self.seller_id,
            "item_id": self.item_id,
            "count": self.count,
            "price": self.price,
            "status": self.status,
            "created_at": self.created_at,
            "closed_at": self.closed_at,
        }
        if self.instance_state is not None:
            out["instance_state"] = self.instance_state
        return out
