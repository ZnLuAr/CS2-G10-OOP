"""领域模型 / 实体类（统一入口）。

模块布局：

- ``player.py``      Player 玩家实体（dataclass + JSON 互转，业务方法待 owner 补）
- ``listing.py``     Listing 市场挂单
- ``transaction.py`` Transaction 成交记录
- ``item.py``        Item 抽象基类及 Weapon / Tool / Armor / Consumable / Misc 子类
- ``inventory.py``   Inventory 背包（双向链表）

字段定义见 docs/data-design.md。
"""

from __future__ import annotations

from .item import (
    Armor,
    Axe,
    Boots,
    Bow,
    Chestplate,
    Consumable,
    Durable,
    Equippable,
    Food,
    Greaves,
    Halberd,
    Hammer,
    Helmet,
    Hoe,
    Item,
    Magic,
    Material,
    Misc,
    Pickaxe,
    Potion,
    Shield,
    Shovel,
    Spear,
    Stackable,
    Sword,
    Tool,
    Weapon,
)
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
    # Item models
    "Item",
    "Durable",
    "Equippable",
    "Stackable",
    "Weapon",
    "Sword",
    "Bow",
    "Spear",
    "Hammer",
    "Halberd",
    "Tool",
    "Axe",
    "Pickaxe",
    "Shovel",
    "Hoe",
    "Armor",
    "Helmet",
    "Chestplate",
    "Greaves",
    "Boots",
    "Shield",
    "Consumable",
    "Potion",
    "Food",
    "Magic",
    "Material",
    "Misc",
]
