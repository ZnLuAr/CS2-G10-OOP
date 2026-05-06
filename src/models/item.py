from abc import ABC, abstractmethod
from typing import Dict, Any
from src.errors import InventoryFullError, SerializationError




def _copy_class_req(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    raise TypeError("class_req must be a list")




# ====================== Mixin 组合 ======================
class Durable:
    """耐久Mixin：武器/工具/装备"""
    durability: int
    durability_max: int

    def is_broken(self) -> bool:
        return self.durability <= 0

    def repair(self):
        self.durability = self.durability_max




class Equippable:
    """穿戴Mixin：武器/装备"""
    equipped: bool
    slot: str
    level_req: int
    class_req: list[str]


    def equip(self):
        self.equipped = True


    def unequip(self):
        self.equipped = False




class Stackable:
    """堆叠Mixin：消耗品/杂项"""
    count: int
    stack_size_max: int


    @property
    def stackable(self) -> bool:
        return True


    def can_stack(self, add: int) -> bool:
        return self.count + add <= self.stack_size_max


    def add_stack(self, num: int) -> bool:
        if self.can_stack(num):
            self.count += num
            return True
        raise InventoryFullError(
            player_id="item_stack",
            capacity=self.stack_size_max,
            context={"field": "num", "value": num},
        )


    def remove_stack(self, num: int) -> bool:
        if self.count >= num:
            self.count -= num
            return True
        return False




# ====================== 抽象物品基类 ======================
class Item(ABC):
    def __init__(
        self,
        *,
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
        self.level_req = 0
        self.class_req: list[str] = []


    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """返回该物品的stats字典（子类必须实现）"""
        pass


    @property
    def stackable(self) -> bool:
        return isinstance(self, Stackable)


    @property
    def stats(self) -> dict[str, Any]:
        return self.get_stats()


    @abstractmethod
    def describe(self) -> str:
        """多态描述"""
        pass


    def to_dict(self) -> dict[str, Any]:
        """序列化为可存JSON的字典"""
        result ={
            "item_id": self.item_id,
            "name": self.name,
            "category": self.category,
            "rarity": self.rarity,
            "base_value": self.base_value,
            "stats": self.get_stats()
        }
        if self.description is not None:
            result["description"] = self.description

        return result


    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Item":
        """从字典反序列化为对应子类Item（工厂方法）"""
        try:
            return ItemFactory.create_item(data)
        except (KeyError, TypeError, ValueError) as e:
            raise SerializationError(entity="Item", raw=data) from e




# ====================== 武器大类 ======================
class Weapon(Item, Durable, Equippable):
    def __init__(
        self,
        *,
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
        self.level_req = 0
        self.class_req: list[str] = []

    def get_stats(self) -> dict[str, Any]:
        return {
            "attack": self.attack,
            "attack_speed": self.attack_speed,
            "durability": self.durability,
            "durability_max": self.durability_max,
            "equipped": self.equipped,
            "slot": self.slot,
            "level_req": self.level_req,
            "class_req": list(self.class_req)
        }

    def describe(self) -> str:
        return f"【{self.rarity}】{self.name} | 攻击:{self.attack} 攻速:{self.attack_speed} 耐久:{self.durability}/{self.durability_max}"


class Sword(Weapon):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, attack: int, attack_speed: float, durability_max: int, description: str = ""):
        super().__init__(
            item_id=item_id,
            name=name,
            sub_category="sword",
            rarity=rarity,
            base_value=base_value,
            attack=attack,
            attack_speed=attack_speed,
            durability_max=durability_max,
            description=description
        )


class Bow(Weapon):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, attack: int, attack_speed: float, durability_max: int, description: str = ""):
        super().__init__(
            item_id=item_id,
            name=name,
            sub_category="bow",
            rarity=rarity,
            base_value=base_value,
            attack=attack,
            attack_speed=attack_speed,
            durability_max=durability_max,
            description=description
        )


class Spear(Weapon):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, attack: int, attack_speed: float, durability_max: int, description: str = ""):
        super().__init__(
            item_id=item_id,
            name=name,
            sub_category="spear",
            rarity=rarity,
            base_value=base_value,
            attack=attack,
            attack_speed=attack_speed,
            durability_max=durability_max,
            description=description
        )


class Hammer(Weapon):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, attack: int, attack_speed: float, durability_max: int, description: str = ""):
        super().__init__(
            item_id=item_id,
            name=name,
            sub_category="hammer",
            rarity=rarity,
            base_value=base_value,
            attack=attack,
            attack_speed=attack_speed,
            durability_max=durability_max,
            description=description
        )


class Halberd(Weapon):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, attack: int, attack_speed: float, durability_max: int, description: str = ""):
        super().__init__(
            item_id=item_id,
            name=name,
            sub_category="halberd",
            rarity=rarity,
            base_value=base_value,
            attack=attack,
            attack_speed=attack_speed,
            durability_max=durability_max,
            description=description
        )




# ====================== 工具大类 ======================
class Tool(Item, Durable):
    def __init__(
        self,
        *,
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
        self.level_req = 0
        self.class_req: list[str] = []

    def get_stats(self) -> dict[str, Any]:
        return {
            "efficiency": self.efficiency,
            "tier": self.tier,
            "durability": self.durability,
            "durability_max": self.durability_max,
            "level_req": self.level_req,
            "class_req": list(self.class_req)
        }

    def describe(self) -> str:
        return f"【{self.rarity}】{self.name} | 效率:{self.efficiency} 等级:{self.tier} 耐久:{self.durability}/{self.durability_max}"


class Axe(Tool):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, efficiency: float, tier: int, durability_max: int, description: str = ""):
        super().__init__(
            item_id=item_id,
            name=name,
            sub_category="axe",
            rarity=rarity,
            base_value=base_value,
            efficiency=efficiency,
            tier=tier,
            durability_max=durability_max,
            description=description
        )


class Pickaxe(Tool):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, efficiency: float, tier: int, durability_max: int, description: str = ""):
        super().__init__(
            item_id=item_id,
            name=name,
            sub_category="pickaxe",
            rarity=rarity,
            base_value=base_value,
            efficiency=efficiency,
            tier=tier,
            durability_max=durability_max,
            description=description
        )


class Shovel(Tool):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, efficiency: float, tier: int, durability_max: int, description: str = ""):
        super().__init__(
            item_id=item_id,
            name=name,
            sub_category="shovel",
            rarity=rarity,
            base_value=base_value,
            efficiency=efficiency,
            tier=tier,
            durability_max=durability_max,
            description=description
        )


class Hoe(Tool):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, efficiency: float, tier: int, durability_max: int, description: str = ""):
        super().__init__(
            item_id=item_id,
            name=name,
            sub_category="hoe",
            rarity=rarity,
            base_value=base_value,
            efficiency=efficiency,
            tier=tier,
            durability_max=durability_max,
            description=description
        )




# ====================== 装备大类 ======================
class Armor(Item, Durable, Equippable):
    def __init__(
        self,
        *,
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
        self.level_req = 0
        self.class_req: list[str] = []

    def get_stats(self) -> dict[str, Any]:
        return {
            "defense": self.defense,
            "magic_resist": self.magic_resist,
            "slot": self.slot,
            "durability": self.durability,
            "durability_max": self.durability_max,
            "equipped": self.equipped,
            "level_req": self.level_req,
            "class_req": list(self.class_req)
        }

    def describe(self) -> str:
        return f"【{self.rarity}】{self.name} | 防御:{self.defense} 魔抗:{self.magic_resist} 耐久:{self.durability}/{self.durability_max}"


class Helmet(Armor):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, defense: int, magic_resist: int, durability_max: int, description: str = ""):
        super().__init__(
            item_id=item_id,
            name=name,
            sub_category="helmet",
            rarity=rarity,
            base_value=base_value,
            defense=defense,
            magic_resist=magic_resist,
            durability_max=durability_max,
            description=description
        )


class Chestplate(Armor):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, defense: int, magic_resist: int, durability_max: int, description: str = ""):
        super().__init__(
            item_id=item_id,
            name=name,
            sub_category="chestplate",
            rarity=rarity,
            base_value=base_value,
            defense=defense,
            magic_resist=magic_resist,
            durability_max=durability_max,
            description=description
        )


class Greaves(Armor):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, defense: int, magic_resist: int, durability_max: int, description: str = ""):
        super().__init__(
            item_id=item_id,
            name=name,
            sub_category="greaves",
            rarity=rarity,
            base_value=base_value,
            defense=defense,
            magic_resist=magic_resist,
            durability_max=durability_max,
            description=description
        )


class Boots(Armor):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, defense: int, magic_resist: int, durability_max: int, description: str = ""):
        super().__init__(
            item_id=item_id,
            name=name,
            sub_category="boots",
            rarity=rarity,
            base_value=base_value,
            defense=defense,
            magic_resist=magic_resist,
            durability_max=durability_max,
            description=description
        )


class Shield(Armor):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, defense: int, magic_resist: int, durability_max: int, description: str = ""):
        super().__init__(
            item_id=item_id,
            name=name,
            sub_category="shield",
            rarity=rarity,
            base_value=base_value,
            defense=defense,
            magic_resist=magic_resist,
            durability_max=durability_max,
            description=description
        )




# ====================== 消耗品大类 ======================
class Consumable(Item, Stackable):
    def __init__(
        self,
        *,
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

    def get_stats(self) -> dict[str, Any]:
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
        super().__init__(
            item_id=item_id,
            name=name,
            sub_category="potion",
            rarity=rarity,
            base_value=base_value,
            effect=effect,
            power=power,
            duration=0,
            stack_size_max=stack_size_max,
            count=count,
            description=description
        )


class Food(Consumable):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, effect: str, power: int, duration: int, stack_size_max: int, count: int = 1, nutrition: int = 0, description: str = ""):
        super().__init__(
            item_id=item_id,
            name=name,
            sub_category="food",
            rarity=rarity,
            base_value=base_value,
            effect=effect,
            power=power,
            duration=duration,
            stack_size_max=stack_size_max,
            count=count,
            description=description
        )
        self.nutrition = nutrition

    def get_stats(self) -> dict[str, Any]:
        stats = super().get_stats()
        stats["nutrition"] = self.nutrition
        return stats


class Magic(Consumable):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, effect: str, power: int, duration: int, stack_size_max: int, count: int = 1, mana_cost: int = 0, description: str = ""):
        super().__init__(
            item_id=item_id,
            name=name,
            sub_category="magic",
            rarity=rarity,
            base_value=base_value,
            effect=effect,
            power=power,
            duration=duration,
            stack_size_max=stack_size_max,
            count=count,
            description=description
        )
        self.mana_cost = mana_cost

    def get_stats(self) -> dict[str, Any]:
        stats = super().get_stats()
        stats["mana_cost"] = self.mana_cost
        return stats


class Material(Consumable):
    def __init__(self, item_id: str, name: str, rarity: str, base_value: int, stack_size_max: int, count: int = 1, description: str = ""):
        super().__init__(
            item_id=item_id,
            name=name,
            sub_category="material",
            rarity=rarity,
            base_value=base_value,
            effect="none",
            power=0,
            duration=0,
            stack_size_max=stack_size_max,
            count=count,
            description=description
        )




# ====================== 杂项大类 ======================
class Misc(Item, Stackable):
    def __init__(
        self,
        *,
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

    def get_stats(self) -> dict[str, Any]:
        return {
            "stack_size_max": self.stack_size_max,
            "count": self.count
        }

    def describe(self) -> str:
        return f"【{self.rarity}】{self.name} | 数量:{self.count}/{self.stack_size_max} | {self.description}"


class ItemFactory:
    @staticmethod
    def _apply_usage_requirements(item: Item, stats: dict[str, Any]) -> None:
        level_req = stats.get("level_req", 0)
        if not isinstance(level_req, int):
            raise TypeError("level_req must be an int")
        item.level_req = level_req
        item.class_req = _copy_class_req(stats.get("class_req", []))

    @staticmethod
    def _apply_durability(item: Durable, stats: dict[str, Any]) -> None:
        durability = stats.get("durability")
        item.durability = item.durability_max if durability is None else durability

    @staticmethod
    def _apply_equipment(item: Equippable, stats: dict[str, Any], default_slot: str) -> None:
        item.equipped = stats.get("equipped", False)
        item.slot = stats.get("slot", default_slot)

    @staticmethod
    def create_item(data: Dict) -> Item:
        cat = data.get("category", "")
        stats = data.get("stats", {})
        if not isinstance(stats, dict):
            raise TypeError("stats must be a dict")
        base = {
            "item_id": data["item_id"],
            "name": data["name"],
            "rarity": data["rarity"],
            "base_value": data["base_value"],
            "description": data.get("description", "")
        }

        if cat.startswith("weapon."):
            sub = cat.split(".")[1]
            args = {
                "item_id": base["item_id"],
                "name": base["name"],
                "rarity": base["rarity"],
                "base_value": base["base_value"],
                "attack": stats["attack"],
                "attack_speed": stats["attack_speed"],
                "durability_max": stats["durability_max"],
                "description": base["description"]
            }
            classes = {
                "sword": Sword,
                "bow": Bow,
                "spear": Spear,
                "hammer": Hammer,
                "halberd": Halberd,
            }
            cls = classes.get(sub)
            if cls is not None:
                item = cls(**args)
                ItemFactory._apply_durability(item, stats)
                ItemFactory._apply_equipment(item, stats, "weapon")
                ItemFactory._apply_usage_requirements(item, stats)
                return item

        if cat.startswith("tool."):
            sub = cat.split(".")[1]
            args = {
                "item_id": base["item_id"],
                "name": base["name"],
                "rarity": base["rarity"],
                "base_value": base["base_value"],
                "efficiency": stats["efficiency"],
                "tier": stats["tier"],
                "durability_max": stats["durability_max"],
                "description": base["description"]
            }
            classes = {
                "axe": Axe,
                "pickaxe": Pickaxe,
                "shovel": Shovel,
                "hoe": Hoe,
            }
            cls = classes.get(sub)
            if cls is not None:
                item = cls(**args)
                ItemFactory._apply_durability(item, stats)
                ItemFactory._apply_usage_requirements(item, stats)
                return item

        if cat.startswith("armor."):
            sub = cat.split(".")[1]
            args = {
                "item_id": base["item_id"],
                "name": base["name"],
                "rarity": base["rarity"],
                "base_value": base["base_value"],
                "defense": stats["defense"],
                "magic_resist": stats["magic_resist"],
                "durability_max": stats["durability_max"],
                "description": base["description"]
            }
            classes = {
                "helmet": Helmet,
                "chestplate": Chestplate,
                "greaves": Greaves,
                "boots": Boots,
                "shield": Shield,
            }
            cls = classes.get(sub)
            if cls is not None:
                item = cls(**args)
                ItemFactory._apply_durability(item, stats)
                ItemFactory._apply_equipment(item, stats, sub)
                ItemFactory._apply_usage_requirements(item, stats)
                return item

        if cat == "consumable.potion":
            item = Potion(
                item_id=base["item_id"],
                name=base["name"],
                rarity=base["rarity"],
                base_value=base["base_value"],
                effect=stats["effect"],
                power=stats["power"],
                stack_size_max=stats["stack_size_max"],
                count=stats.get("count", 1),
                description=base["description"],
            )
            item.duration = stats.get("duration", item.duration)
            return item

        if cat == "consumable.food":
            return Food(
                item_id=base["item_id"],
                name=base["name"],
                rarity=base["rarity"],
                base_value=base["base_value"],
                effect=stats["effect"],
                power=stats["power"],
                duration=stats["duration"],
                stack_size_max=stats["stack_size_max"],
                count=stats.get("count", 1),
                nutrition=stats.get("nutrition", 0),
                description=base["description"],
            )

        if cat == "consumable.magic":
            return Magic(
                item_id=base["item_id"],
                name=base["name"],
                rarity=base["rarity"],
                base_value=base["base_value"],
                effect=stats["effect"],
                power=stats["power"],
                duration=stats["duration"],
                stack_size_max=stats["stack_size_max"],
                count=stats.get("count", 1),
                mana_cost=stats.get("mana_cost", 0),
                description=base["description"],
            )

        if cat == "consumable.material":
            item = Material(
                item_id=base["item_id"],
                name=base["name"],
                rarity=base["rarity"],
                base_value=base["base_value"],
                stack_size_max=stats["stack_size_max"],
                count=stats.get("count", 1),
                description=base["description"],
            )
            item.effect = stats.get("effect", item.effect)
            item.power = stats.get("power", item.power)
            item.duration = stats.get("duration", item.duration)
            return item

        if cat == "misc":
            return Misc(
                item_id=base["item_id"],
                name=base["name"],
                rarity=base["rarity"],
                base_value=base["base_value"],
                stack_size_max=stats["stack_size_max"],
                count=stats.get("count", 1),
                description=base["description"],
            )

        raise ValueError(f"Unknown category: {cat}")
