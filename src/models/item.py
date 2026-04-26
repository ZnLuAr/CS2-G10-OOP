from abc import ABC, abstractmethod
from typing import Dict, Any


# ====================== Mixin 组合 ======================
class Durable(ABC):
    """耐久Mixin：武器/工具/装备"""
    durability: int
    durability_max: int

    def is_broken(self) -> bool:
        return self.durability <= 0

    def repair(self):
        self.durability = self.durability_max


class Equippable(ABC):
    """穿戴Mixin：武器/装备"""
    equipped: bool
    slot: str

    def equip(self):
        self.equipped = True

    def unequip(self):
        self.equipped = False


class Stackable(ABC):
    """堆叠Mixin：消耗品/杂项"""
    count: int
    stack_size_max: int

    def can_stack(self, add: int) -> bool:
        return self.count + add <= self.stack_size_max

    def add_stack(self, num: int) -> bool:
        if self.can_stack(num):
            self.count += num
            return True
        return False

    def remove_stack(self, num: int) -> bool:
        if self.count >= num:
            self.count -= num
            return True
        return False


# ====================== 抽象物品基类 ======================
class Item(ABC):
    def __init__(
        self,
        item_id: str,
        name: str,
        category: str,
        rarity: str,
        base_value: int,
        description: str = ""
    ):
        self.item_id = item_id
        self.name = name
        self.category = category
        self.rarity = rarity
        self.base_value = base_value
        self.description = description

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """返回该物品的stats字典（子类必须实现）"""
        pass

    @abstractmethod
    def describe(self) -> str:
        """多态描述"""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """序列化为可存JSON的字典"""
        return {
            "item_id": self.item_id,
            "name": self.name,
            "category": self.category,
            "rarity": self.rarity,
            "base_value": self.base_value,
            "description": self.description,
            "stats": self.get_stats()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Item":
        """从字典反序列化为对应子类Item（工厂方法）"""
        return ItemFactory.create_item(data)


# ====================== 武器大类 ======================
class Weapon(Item, Durable, Equippable, ABC):
    def __init__(
        self,
        item_id: str,
        name: str,
        sub_category: str,
        rarity: str,
        base_value: int,
        attack: int,
        attack_speed: float,
        durability_max: int,
        description: str = ""
    ):
        super().__init__(
            item_id=item_id,
            name=name,
            category=f"weapon.{sub_category}",
            rarity=rarity,
            base_value=base_value,
            description=description
        )
        self.attack = attack
        self.attack_speed = attack_speed
        self.durability_max = durability_max
        self.durability = durability_max
        self.equipped = False
        self.slot = "weapon"

    def get_stats(self) -> Dict[str, Any]:
        return {
            "attack": self.attack,
            "attack_speed": self.attack_speed,
            "durability": self.durability,
            "durability_max": self.durability_max,
            "equipped": self.equipped,
            "slot": self.slot
        }


    def describe(self) -> str:
        return f"【{self.rarity}】{self.name} | 攻击:{self.attack} 攻速:{self.attack_speed} 耐久:{self.durability}/{self.durability_max}"


class Sword(Weapon):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, attack: int, attack_speed: float, durability_max: int, description: str = ""):
        super().__init__(item_id, name, "sword", rarity, base_value, attack, attack_speed, durability_max, description)

class Bow(Weapon):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, attack: int, attack_speed: float, durability_max: int, description: str = ""):
        super().__init__(item_id, name, "bow", rarity, base_value, attack, attack_speed, durability_max, description)

class Spear(Weapon):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, attack: int, attack_speed: float, durability_max: int, description: str = ""):
        super().__init__(item_id, name, "spear", rarity, base_value, attack, attack_speed, durability_max, description)

class Hammer(Weapon):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, attack: int, attack_speed: float, durability_max: int, description: str = ""):
        super().__init__(item_id, name, "hammer", rarity, base_value, attack, attack_speed, durability_max, description)

class Halberd(Weapon):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, attack: int, attack_speed: float, durability_max: int, description: str = ""):
        super().__init__(item_id, name, "halberd", rarity, base_value, attack, attack_speed, durability_max, description)


# ====================== 工具大类 ======================
class Tool(Item, Durable, ABC):
    def __init__(
        self,
        item_id: str,
        name: str,
        sub_category: str,
        rarity: str,
        base_value: int,
        efficiency: float,
        tier: int,
        durability_max: int,
        description: str = ""
    ):
        super().__init__(
            item_id=item_id,
            name=name,
            category=f"tool.{sub_category}",
            rarity=rarity,
            base_value=base_value,
            description=description
        )
        self.efficiency = efficiency
        self.tier = tier
        self.durability_max = durability_max
        self.durability = durability_max

    def get_stats(self) -> Dict[str, Any]:
        return {
            "efficiency": self.efficiency,
            "tier": self.tier,
            "durability": self.durability,
            "durability_max": self.durability_max
        }

    def describe(self) -> str:
        return f"【{self.rarity}】{self.name} | 效率:{self.efficiency} 等级:{self.tier} 耐久:{self.durability}/{self.durability_max}"


class Axe(Tool):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, efficiency: float, tier: int, durability_max: int, description: str = ""):
        super().__init__(item_id, name, "axe", rarity, base_value, efficiency, tier, durability_max, description)

class Pickaxe(Tool):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, efficiency: float, tier: int, durability_max: int, description: str = ""):
        super().__init__(item_id, name, "pickaxe", rarity, base_value, efficiency, tier, durability_max, description)

class Shovel(Tool):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, efficiency: float, tier: int, durability_max: int, description: str = ""):
        super().__init__(item_id, name, "shovel", rarity, base_value, efficiency, tier, durability_max, description)

class Hoe(Tool):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, efficiency: float, tier: int, durability_max: int, description: str = ""):
        super().__init__(item_id, name, "hoe", rarity, base_value, efficiency, tier, durability_max, description)


# ====================== 装备大类 ======================
class Armor(Item, Durable, Equippable, ABC):
    def __init__(
        self,
        item_id: str,
        name: str,
        sub_category: str,
        rarity: str,
        base_value: int,
        defense: int,
        magic_resist: int,
        durability_max: int,
        description: str = ""
    ):
        super().__init__(
            item_id=item_id,
            name=name,
            category=f"armor.{sub_category}",
            rarity=rarity,
            base_value=base_value,
            description=description
        )
        self.defense = defense
        self.magic_resist = magic_resist
        self.durability_max = durability_max
        self.durability = durability_max
        self.equipped = False
        self.slot = sub_category

    def get_stats(self) -> Dict[str, Any]:
        return {
            "defense": self.defense,
            "magic_resist": self.magic_resist,
            "slot": self.slot,
            "durability": self.durability,
            "durability_max": self.durability_max,
            "equipped": self.equipped
        }

    def describe(self) -> str:
        return f"【{self.rarity}】{self.name} | 防御:{self.defense} 魔抗:{self.magic_resist} 耐久:{self.durability}/{self.durability_max}"


class Helmet(Armor):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, defense: int, magic_resist: int, durability_max: int, description: str = ""):
        super().__init__(item_id, name, "helmet", rarity, base_value, defense, magic_resist, durability_max, description)

class Chestplate(Armor):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, defense: int, magic_resist: int, durability_max: int, description: str = ""):
        super().__init__(item_id, name, "chestplate", rarity, base_value, defense, magic_resist, durability_max, description)

class Greaves(Armor):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, defense: int, magic_resist: int, durability_max: int, description: str = ""):
        super().__init__(item_id, name, "greaves", rarity, base_value, defense, magic_resist, durability_max, description)

class Boots(Armor):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, defense: int, magic_resist: int, durability_max: int, description: str = ""):
        super().__init__(item_id, name, "boots", rarity, base_value, defense, magic_resist, durability_max, description)

class Shield(Armor):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, defense: int, magic_resist: int, durability_max: int, description: str = ""):
        super().__init__(item_id, name, "shield", rarity, base_value, defense, magic_resist, durability_max, description)


# ====================== 消耗品大类 ======================
class Consumable(Item, Stackable, ABC):
    def __init__(
        self,
        item_id: str,
        name: str,
        sub_category: str,
        rarity: str,
        base_value: int,
        effect: str,
        power: int,
        duration: int,
        stack_size_max: int,
        count: int = 1,
        description: str = ""
    ):
        super().__init__(
            item_id=item_id,
            name=name,
            category=f"consumable.{sub_category}",
            rarity=rarity,
            base_value=base_value,
            description=description
        )
        self.effect = effect
        self.power = power
        self.duration = duration
        self.stack_size_max = stack_size_max
        self.count = count

    def get_stats(self) -> Dict[str, Any]:
        return {
            "effect": self.effect,
            "power": self.power,
            "duration": self.duration,
            "stack_size_max": self.stack_size_max,
            "count": self.count
        }

    def describe(self) -> str:
        return f"【{self.rarity}】{self.name} | {self.effect}+{self.power} 数量:{self.count}/{self.stack_size_max}"


class Potion(Consumable):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, effect: str, power: int, stack_size_max: int, count: int = 1, description: str = ""):
        super().__init__(item_id, name, "potion", rarity, base_value, effect, power, 0, stack_size_max, count, description)

class Food(Consumable):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, effect: str, power: int, duration: int, stack_size_max: int, count: int = 1, nutrition: int = 0, description: str = ""):
        super().__init__(item_id, name, "food", rarity, base_value, effect, power, duration, stack_size_max, count, description)
        self.nutrition = nutrition

    def get_stats(self) -> Dict[str, Any]:
        stats = super().get_stats()
        stats["nutrition"] = self.nutrition
        return stats

class Magic(Consumable):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, effect: str, power: int, duration: int, stack_size_max: int, count: int = 1, mana_cost: int = 0, description: str = ""):
        super().__init__(item_id, name, "magic", rarity, base_value, effect, power, duration, stack_size_max, count, description)
        self.mana_cost = mana_cost

    def get_stats(self) -> Dict[str, Any]:
        stats = super().get_stats()
        stats["mana_cost"] = self.mana_cost
        return stats

class Material(Consumable):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, stack_size_max: int, count: int = 1, description: str = ""):
        super().__init__(item_id, name, "material", rarity, base_value, "none", 0, 0, stack_size_max, count, description)


# ====================== 杂项大类 ======================
class Misc(Item, Stackable):
    def __init__(
        self,
        item_id: str,
        name: str,
        rarity: str,
        base_value: int,
        stack_size_max: int,
        count: int = 1,
        description: str = ""
    ):
        super().__init__(
            item_id=item_id,
            name=name,
            category="misc",
            rarity=rarity,
            base_value=base_value,
            description=description
        )
        self.stack_size_max = stack_size_max
        self.count = count

    def get_stats(self) -> Dict[str, Any]:
        return {
            "stack_size_max": self.stack_size_max,
            "count": self.count
        }

    def describe(self) -> str:
        return f"【{self.rarity}】{self.name} | 数量:{self.count}/{self.stack_size_max} | {self.description}"



class ItemFactory:
    @staticmethod
    def create_item(data: Dict) -> Item:
        cat = data.get("category", "")
        stats = data.get("stats", {})
        base = {
            "item_id": data["item_id"],
            "name": data["name"],
            "rarity": data["rarity"],
            "base_value": data["base_value"],
            "description": data.get("description", "")
        }

        if cat.startswith("weapon."):
            sub = cat.split(".")[1]
            args = [
                base["item_id"], base["name"], base["rarity"], base["base_value"],
                stats["attack"], stats["attack_speed"], stats["durability_max"],
                base["description"]
            ]
            if sub == "sword": return Sword(*args)
            if sub == "bow": return Bow(*args)
            if sub == "spear": return Spear(*args)
            if sub == "hammer": return Hammer(*args)
            if sub == "halberd": return Halberd(*args)

        elif cat.startswith("tool."):
            sub = cat.split(".")[1]
            args = [
                base["item_id"], base["name"], base["rarity"], base["base_value"],
                stats["efficiency"], stats["tier"], stats["durability_max"],
                base["description"]
            ]
            if sub == "axe": return Axe(*args)
            if sub == "pickaxe": return Pickaxe(*args)
            if sub == "shovel": return Shovel(*args)
            if sub == "hoe": return Hoe(*args)

        elif cat.startswith("armor."):
            sub = cat.split(".")[1]
            args = [
                base["item_id"], base["name"], base["rarity"], base["base_value"],
                stats["defense"], stats["magic_resist"], stats["durability_max"],
                base["description"]
            ]
            if sub == "helmet": return Helmet(*args)
            if sub == "chestplate": return Chestplate(*args)
            if sub == "greaves": return Greaves(*args)
            if sub == "boots": return Boots(*args)
            if sub == "shield": return Shield(*args)

        elif cat.startswith("consumable."):
            sub = cat.split(".")[1]
            if sub == "potion":
                return Potion(
                    base["item_id"], base["name"], base["rarity"], base["base_value"],
                    stats["effect"], stats["power"], stats["stack_size_max"], stats["count"],
                    base["description"]
                )
            if sub == "food":
                return Food(
                    base["item_id"], base["name"], base["rarity"], base["base_value"],
                    stats["effect"], stats["power"], stats["duration"],
                    stats["stack_size_max"], stats["count"], stats.get("nutrition", 0),
                    base["description"]
                )
            if sub == "magic":
                return Magic(
                    base["item_id"], base["name"], base["rarity"], base["base_value"],
                    stats["effect"], stats["power"], stats["duration"],
                    stats["stack_size_max"], stats["count"], stats.get("mana_cost", 0),
                    base["description"]
                )
            if sub == "material":
                return Material(
                    base["item_id"], base["name"], base["rarity"], base["base_value"],
                    stats["stack_size_max"], stats["count"], base["description"]
                )

        elif cat == "misc":
            return Misc(
                base["item_id"], base["name"], base["rarity"], base["base_value"],
                stats["stack_size_max"], stats["count"], base["description"]
            )

        raise ValueError(f"Unknown category: {cat}")