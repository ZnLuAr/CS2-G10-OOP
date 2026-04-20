"""领域模型 / 实体类（统一入口）。

模块布局：

- ``player.py``      Player 玩家实体（dataclass + JSON 互转，业务方法待 owner 补）
- ``listing.py``     Listing 市场挂单
- ``transaction.py`` Transaction 成交记录
- ``item.py``        Item 抽象基类及 Weapon / Tool / Armor / Consumable / Misc 子类
                     ⚠️ 待 JIAFENG YE 实现，目前 Persistence 暂以 dict 承接 Item 数据
- ``inventory.py``   Inventory 背包（双向链表）
                     ⚠️ 待 XINGZHOU PENG 实现

字段定义见 docs/data-design.md。
"""

from __future__ import annotations

from .listing import (
    STATUS_ACTIVE,
    STATUS_CANCELLED,
    STATUS_SOLD,
    Listing,
)
from .player import Player
from .transaction import Transaction


__all__ = [
    "Player",
    "Listing",
    "STATUS_ACTIVE",
    "STATUS_SOLD",
    "STATUS_CANCELLED",
    "Transaction",
]
