"""Player 数据模型（字段容器 + JSON 互转）。

字段定义见 docs/data-design.md §3。
本类目前只承载字段；业务方法（add_gold / spend_gold / 删除前校验等）
留待 ``services/player_service.py`` 的负责人实现。
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["Player"]




@dataclass
class Player:
    player_id: str
    name: str
    gold: int
    level: int
    klass: str                              # JSON 字段名为 'class'，Python 关键字回避
    inventory: list[dict] = field(default_factory=list)  # 暂为 dict 列表，等 InventorySlot 落地
    created_at: str = ""

    def add_gold(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("The number of gold(beryl) can not be negative")
        else:
            self.gold += amount

    def spend_gold(self, amount: int) -> None:
        if amount < 0:
            raise ValueError("The number of gold(beryl) can not be negative")
        else:
            if self.gold < amount:
                raise InsufficientGoldError
            else:
                self.gold -= amount

    def can_be_deleted(self) -> bool:
        if self.inventory:  # It still has items in bags :)
            return True
        else:
            return  False


    @classmethod
    def from_dict(cls, d: dict) -> "Player":
        return cls(
            player_id=d["player_id"],
            name=d["name"],
            gold=d["gold"],
            level=d["level"],
            klass=d["class"],
            inventory=list(d.get("inventory", [])),
            created_at=d.get("created_at", ""),
        )

    def to_dict(self) -> dict:
        return {
            "player_id": self.player_id,
            "name": self.name,
            "gold": self.gold,
            "level": self.level,
            "class": self.klass,
            "inventory": list(self.inventory),
            "created_at": self.created_at,
        }
