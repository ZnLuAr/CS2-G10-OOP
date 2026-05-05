"""Item 模型层次结构

完整实现 docs/data-design.md §8 的物品设计：
- 抽象基类 Item
- Mixin: Durable, Equippable, Stackable
- 18 个具体子类

字段与 seed 数据 (data/items.json) 保持兼容。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from src.errors import SerializationError

__all__ = [
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


# ========== Mixin 层 ==========

class Durable:
    """可耐久 Mixin（Weapon, Tool, Armor）"""

    @property
    def durability(self) -> int:
        return getattr(self, "_stats", {}).get("durability", 0)

    @property
    def durability_max(self) -> int:
        return getattr(self, "_stats", {}).get("durability_max", 0)


class Equippable:
    """可装备 Mixin（Weapon, Armor）"""

    @property
    def equipped(self) -> bool:
        return getattr(self, "_stats", {}).get("equipped", False)

    @property
    def slot(self) -> str:
        return getattr(self, "_stats", {}).get("slot", "")

    @property
    def level_req(self) -> int:
        return getattr(self, "_stats", {}).get("level_req", 0)

    @property
    def class_req(self) -> list[str]:
        cr = getattr(self, "_stats", {}).get("class_req", [])
        if isinstance(cr, str):
            return [cr]
        return list(cr) if cr else []


class Stackable:
    """可堆叠 Mixin（Consumable, Misc）"""

    @property
    def stackable(self) -> bool:
        return True

    @property
    def stack_size_max(self) -> int:
        return getattr(self, "_stats", {}).get("stack_size_max", 1)


# ========== 抽象基类 ==========

@dataclass
class Item(ABC):
    """物品抽象基类

    字段（来自 data-design.md §8.3.1）：
        item_id: 唯一标识
        name: 显示名称
        category: 分类路径（如 "weapon.sword"）
        rarity: 稀有度（common/uncommon/rare/epic/legendary）
        base_value: 基础价值
        description: 描述（可选）
        stats: 扩展属性字典（子类通过 property 暴露）
    """

    item_id: str
    name: str
    category: str
    rarity: str
    base_value: int
    description: str = ""
    stats: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # 内部保留 stats 引用供 Mixin property 访问
        self._stats = self.stats

    @abstractmethod
    def describe(self) -> str:
        """返回物品描述字符串（多态实现）"""
        raise NotImplementedError

    def to_dict(self) -> dict[str, Any]:
        """序列化为 items.json 格式"""
        return {
            "item_id": self.item_id,
            "name": self.name,
            "category": self.category,
            "rarity": self.rarity,
            "base_value": self.base_value,
            "description": self.description,
            "stats": dict(self.stats),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Item":
        """根据 category 路由到对应子类"""
        category = data.get("category", "")
        item_id = data.get("item_id", "")
        name = data.get("name", "")
        rarity = data.get("rarity", "common")
        base_value = data.get("base_value", 0)
        description = data.get("description", "")
        stats = data.get("stats", {})

        factory = _CATEGORY_ROUTER.get(category)
        if factory is None:
            raise SerializationError(f"Unknown item category: {category}")

        return factory(item_id, name, rarity, base_value, description, stats)


# ========== Weapon 分支 ==========

@dataclass
class Weapon(Item, Durable, Equippable):
    """武器基类（Durable + Equippable）"""

    @property
    def attack(self) -> int:
        return self.stats.get("attack", 0)

    @property
    def attack_speed(self) -> float:
        return self.stats.get("attack_speed", 1.0)

    def describe(self) -> str:
        return f"[{self.rarity}] {self.name} (ATK:{self.attack}, SPD:{self.attack_speed}, DUR:{self.durability}/{self.durability_max})"


@dataclass
class Sword(Weapon):
    """剑"""

    category: str = field(init=False, default="weapon.sword")


@dataclass
class Bow(Weapon):
    """弓弩"""

    category: str = field(init=False, default="weapon.bow")


@dataclass
class Spear(Weapon):
    """长矛"""

    category: str = field(init=False, default="weapon.spear")


@dataclass
class Hammer(Weapon):
    """重锤"""

    category: str = field(init=False, default="weapon.hammer")


@dataclass
class Halberd(Weapon):
    """长戟"""

    category: str = field(init=False, default="weapon.halberd")


# ========== Tool 分支 ==========

@dataclass
class Tool(Item, Durable):
    """工具基类（仅 Durable，不可装备）"""

    @property
    def efficiency(self) -> int:
        return self.stats.get("efficiency", 0)

    @property
    def tier(self) -> int:
        return self.stats.get("tier", 1)

    def describe(self) -> str:
        return f"[{self.rarity}] {self.name} (Eff:{self.efficiency}, Tier:{self.tier}, DUR:{self.durability}/{self.durability_max})"


@dataclass
class Axe(Tool):
    """斧"""

    category: str = field(init=False, default="tool.axe")


@dataclass
class Pickaxe(Tool):
    """镐"""

    category: str = field(init=False, default="tool.pickaxe")


@dataclass
class Shovel(Tool):
    """锹"""

    category: str = field(init=False, default="tool.shovel")


@dataclass
class Hoe(Tool):
    """锄"""

    category: str = field(init=False, default="tool.hoe")


# ========== Armor 分支 ==========

@dataclass
class Armor(Item, Durable, Equippable):
    """装备基类（Durable + Equippable）"""

    @property
    def defense(self) -> int:
        return self.stats.get("defense", 0)

    @property
    def magic_resist(self) -> int:
        return self.stats.get("magic_resist", 0)

    def describe(self) -> str:
        return f"[{self.rarity}] {self.name} (DEF:{self.defense}, MRES:{self.magic_resist}, DUR:{self.durability}/{self.durability_max})"


@dataclass
class Helmet(Armor):
    """头盔"""

    category: str = field(init=False, default="armor.helmet")


@dataclass
class Chestplate(Armor):
    """胸甲"""

    category: str = field(init=False, default="armor.chestplate")


@dataclass
class Greaves(Armor):
    """护胫"""

    category: str = field(init=False, default="armor.greaves")


@dataclass
class Boots(Armor):
    """靴子"""

    category: str = field(init=False, default="armor.boots")


@dataclass
class Shield(Armor):
    """盾牌"""

    category: str = field(init=False, default="armor.shield")


# ========== Consumable 分支 ==========

@dataclass
class Consumable(Item, Stackable):
    """消耗品基类（Stackable）"""

    @property
    def effect(self) -> str:
        return self.stats.get("effect", "")

    @property
    def power(self) -> int:
        return self.stats.get("power", 0)

    @property
    def duration(self) -> int:
        return self.stats.get("duration", 0)

    def describe(self) -> str:
        extra = ""
        if "nutrition" in self.stats:
            extra = f", NUT:{self.stats['nutrition']}"
        if "mana_cost" in self.stats:
            extra = f", MANA:{self.stats['mana_cost']}"
        return f"[{self.rarity}] {self.name} ({self.effect}, PWR:{self.power}, DUR:{self.duration}s, MaxStack:{self.stack_size_max}{extra})"


@dataclass
class Potion(Consumable):
    """药水"""

    category: str = field(init=False, default="consumable.potion")


@dataclass
class Food(Consumable):
    """食物"""

    category: str = field(init=False, default="consumable.food")


@dataclass
class Magic(Consumable):
    """魔法物品"""

    category: str = field(init=False, default="consumable.magic")


@dataclass
class Material(Consumable):
    """材料"""

    category: str = field(init=False, default="consumable.material")


# ========== Misc 分支 ==========

@dataclass
class Misc(Item, Stackable):
    """杂项（Stackable）"""

    # Misc 的 count 是 seed 数据默认值，运行时 InventorySlot.count 独立管理
    @property
    def count(self) -> int:
        return self.stats.get("count", 1)

    def describe(self) -> str:
        return f"[{self.rarity}] {self.name} (Count:{self.count}, MaxStack:{self.stack_size_max})"

    category: str = field(init=False, default="misc")


# ========== 工厂路由表 ==========

_CATEGORY_ROUTER: dict[str, callable] = {
    "weapon.sword": lambda i, n, r, bv, d, s: Sword(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
    "weapon.bow": lambda i, n, r, bv, d, s: Bow(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
    "weapon.spear": lambda i, n, r, bv, d, s: Spear(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
    "weapon.hammer": lambda i, n, r, bv, d, s: Hammer(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
    "weapon.halberd": lambda i, n, r, bv, d, s: Halberd(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
    "tool.axe": lambda i, n, r, bv, d, s: Axe(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
    "tool.pickaxe": lambda i, n, r, bv, d, s: Pickaxe(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
    "tool.shovel": lambda i, n, r, bv, d, s: Shovel(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
    "tool.hoe": lambda i, n, r, bv, d, s: Hoe(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
    "armor.helmet": lambda i, n, r, bv, d, s: Helmet(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
    "armor.chestplate": lambda i, n, r, bv, d, s: Chestplate(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
    "armor.greaves": lambda i, n, r, bv, d, s: Greaves(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
    "armor.boots": lambda i, n, r, bv, d, s: Boots(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
    "armor.shield": lambda i, n, r, bv, d, s: Shield(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
    "consumable.potion": lambda i, n, r, bv, d, s: Potion(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
    "consumable.food": lambda i, n, r, bv, d, s: Food(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
    "consumable.magic": lambda i, n, r, bv, d, s: Magic(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
    "consumable.material": lambda i, n, r, bv, d, s: Material(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
    "misc": lambda i, n, r, bv, d, s: Misc(item_id=i, name=n, rarity=r, base_value=bv, description=d, stats=s),
}
