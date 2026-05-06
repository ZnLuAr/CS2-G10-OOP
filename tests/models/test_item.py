"""Item 模型层次结构测试

覆盖所有 18 个具体子类的创建、序列化、属性访问。
"""

from __future__ import annotations

import pytest

from src.models import (
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
from src.errors import SerializationError


# ========== 工厂路由测试 ==========

class TestFromDictRouting:
    """测试 Item.from_dict 根据 category 正确路由到子类"""

    def test_weapon_sword(self):
        data = {
            "item_id": "i_test",
            "name": "测试剑",
            "category": "weapon.sword",
            "rarity": "rare",
            "base_value": 100,
            "stats": {"attack": 25, "attack_speed": 1.2, "durability_max": 80},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Sword)
        assert isinstance(item, Weapon)
        assert item.category == "weapon.sword"

    def test_weapon_bow(self):
        data = {
            "item_id": "i_bow",
            "name": "测试弓",
            "category": "weapon.bow",
            "rarity": "common",
            "base_value": 50,
            "stats": {"attack": 15, "attack_speed": 1.0, "durability_max": 60},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Bow)
        assert isinstance(item, Weapon)

    def test_weapon_spear(self):
        data = {
            "item_id": "i_spear",
            "name": "测试矛",
            "category": "weapon.spear",
            "rarity": "common",
            "base_value": 80,
            "stats": {"attack": 20, "attack_speed": 0.9, "durability_max": 100},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Spear)

    def test_weapon_hammer(self):
        data = {
            "item_id": "i_hammer",
            "name": "测试锤",
            "category": "weapon.hammer",
            "rarity": "epic",
            "base_value": 200,
            "stats": {"attack": 40, "attack_speed": 0.7, "durability_max": 150},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Hammer)

    def test_weapon_halberd(self):
        data = {
            "item_id": "i_halberd",
            "name": "测试戟",
            "category": "weapon.halberd",
            "rarity": "rare",
            "base_value": 150,
            "stats": {"attack": 35, "attack_speed": 0.8, "durability_max": 120},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Halberd)

    def test_tool_axe(self):
        data = {
            "item_id": "i_axe",
            "name": "测试斧",
            "category": "tool.axe",
            "rarity": "common",
            "base_value": 30,
            "stats": {"efficiency": 5, "tier": 1, "durability_max": 50},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Axe)
        assert isinstance(item, Tool)

    def test_tool_pickaxe(self):
        data = {
            "item_id": "i_pickaxe",
            "name": "测试镐",
            "category": "tool.pickaxe",
            "rarity": "common",
            "base_value": 40,
            "stats": {"efficiency": 6, "tier": 1, "durability_max": 60},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Pickaxe)

    def test_tool_shovel(self):
        data = {
            "item_id": "i_shovel",
            "name": "测试锹",
            "category": "tool.shovel",
            "rarity": "common",
            "base_value": 20,
            "stats": {"efficiency": 4, "tier": 1, "durability_max": 40},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Shovel)

    def test_tool_hoe(self):
        data = {
            "item_id": "i_hoe",
            "name": "测试锄",
            "category": "tool.hoe",
            "rarity": "common",
            "base_value": 25,
            "stats": {"efficiency": 4, "tier": 1, "durability_max": 45},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Hoe)

    def test_armor_helmet(self):
        data = {
            "item_id": "i_helmet",
            "name": "测试头盔",
            "category": "armor.helmet",
            "rarity": "rare",
            "base_value": 80,
            "stats": {"defense": 10, "magic_resist": 5, "durability_max": 60},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Helmet)
        assert isinstance(item, Armor)

    def test_armor_chestplate(self):
        data = {
            "item_id": "i_chestplate",
            "name": "测试胸甲",
            "category": "armor.chestplate",
            "rarity": "rare",
            "base_value": 120,
            "stats": {"defense": 15, "magic_resist": 8, "durability_max": 80},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Chestplate)

    def test_armor_greaves(self):
        data = {
            "item_id": "i_greaves",
            "name": "测试护胫",
            "category": "armor.greaves",
            "rarity": "uncommon",
            "base_value": 60,
            "stats": {"defense": 8, "magic_resist": 4, "durability_max": 50},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Greaves)

    def test_armor_boots(self):
        data = {
            "item_id": "i_boots",
            "name": "测试靴子",
            "category": "armor.boots",
            "rarity": "uncommon",
            "base_value": 50,
            "stats": {"defense": 6, "magic_resist": 3, "durability_max": 45},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Boots)

    def test_armor_shield(self):
        data = {
            "item_id": "i_shield",
            "name": "测试盾牌",
            "category": "armor.shield",
            "rarity": "rare",
            "base_value": 90,
            "stats": {"defense": 12, "magic_resist": 6, "durability_max": 70},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Shield)

    def test_consumable_potion(self):
        data = {
            "item_id": "i_potion",
            "name": "测试药水",
            "category": "consumable.potion",
            "rarity": "common",
            "base_value": 10,
            "stats": {"effect": "heal", "power": 20, "stack_size_max": 20, "count": 1},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Potion)
        assert isinstance(item, Consumable)

    def test_consumable_food(self):
        data = {
            "item_id": "i_food",
            "name": "测试食物",
            "category": "consumable.food",
            "rarity": "common",
            "base_value": 5,
            "stats": {"effect": "hunger", "power": 10, "duration": 30, "stack_size_max": 20, "count": 1, "nutrition": 5},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Food)

    def test_consumable_magic(self):
        data = {
            "item_id": "i_magic",
            "name": "测试魔法",
            "category": "consumable.magic",
            "rarity": "rare",
            "base_value": 50,
            "stats": {"effect": "fireball", "power": 30, "duration": 5, "stack_size_max": 10, "count": 1, "mana_cost": 20},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Magic)

    def test_consumable_material(self):
        data = {
            "item_id": "i_material",
            "name": "测试材料",
            "category": "consumable.material",
            "rarity": "common",
            "base_value": 2,
            "stats": {"stack_size_max": 99, "count": 1},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Material)

    def test_misc(self):
        data = {
            "item_id": "i_misc",
            "name": "测试杂项",
            "category": "misc",
            "rarity": "common",
            "base_value": 1,
            "stats": {"stack_size_max": 99, "count": 1},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Misc)

    def test_unknown_category_raises(self):
        data = {
            "item_id": "i_unknown",
            "name": "未知",
            "category": "unknown.category",
            "rarity": "common",
            "base_value": 1,
            "stats": {},
        }
        with pytest.raises((SerializationError, ValueError)):
            Item.from_dict(data)


# ========== Mixin 属性测试 ==========

class TestMixinProperties:
    """测试 Mixin 层的属性访问"""

    def test_weapon_is_durable_and_equippable(self):
        """Weapon 继承 Durable 和 Equippable"""
        data = {
            "item_id": "i_sword",
            "name": "测试剑",
            "category": "weapon.sword",
            "rarity": "common",
            "base_value": 100,
            "stats": {"attack": 20, "attack_speed": 1.0, "durability_max": 100},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Durable)
        assert isinstance(item, Equippable)
        # durability 初始化为 durability_max
        assert item.durability == 100
        assert item.durability_max == 100
        # equipped 默认为 False, slot 为 "weapon"
        assert item.equipped is False
        assert item.slot == "weapon"

    def test_armor_is_durable_and_equippable(self):
        """Armor 继承 Durable 和 Equippable"""
        data = {
            "item_id": "i_helmet",
            "name": "测试头盔",
            "category": "armor.helmet",
            "rarity": "common",
            "base_value": 50,
            "stats": {"defense": 10, "magic_resist": 5, "durability_max": 60},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Durable)
        assert isinstance(item, Equippable)
        assert item.slot == "helmet"

    def test_consumable_is_stackable(self):
        """Consumable 继承 Stackable"""
        data = {
            "item_id": "i_potion",
            "name": "测试药水",
            "category": "consumable.potion",
            "rarity": "common",
            "base_value": 10,
            "stats": {"effect": "heal", "power": 20, "stack_size_max": 20, "count": 1},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Stackable)
        assert item.stack_size_max == 20

    def test_misc_is_stackable(self):
        """Misc 继承 Stackable"""
        data = {
            "item_id": "i_misc",
            "name": "测试杂项",
            "category": "misc",
            "rarity": "common",
            "base_value": 1,
            "stats": {"stack_size_max": 99, "count": 10},
        }
        item = Item.from_dict(data)
        assert isinstance(item, Stackable)
        assert item.stack_size_max == 99

    def test_all_items_have_usage_requirement_defaults(self):
        """所有 Item 对象都有使用门槛属性，避免动态属性不一致"""
        data = {
            "item_id": "i_misc",
            "name": "测试杂项",
            "category": "misc",
            "rarity": "common",
            "base_value": 1,
            "stats": {"stack_size_max": 99, "count": 10},
        }
        item = Item.from_dict(data)
        assert item.level_req == 0
        assert item.class_req == []


# ========== 序列化/反序列化往返测试 ==========

class TestRoundTrip:
    """测试 to_dict / from_dict 往返保持数据"""

    def test_weapon_roundtrip(self):
        """Weapon 序列化/反序列化往返"""
        original_data = {
            "item_id": "i_sword",
            "name": "测试剑",
            "category": "weapon.sword",
            "rarity": "rare",
            "base_value": 100,
            "description": "测试描述",
            "stats": {
                "attack": 25,
                "attack_speed": 1.2,
                "durability": 42,
                "durability_max": 80,
                "equipped": True,
                "slot": "weapon",
                "level_req": 7,
                "class_req": ["warrior"],
            },
        }
        item = Item.from_dict(original_data)
        assert isinstance(item, Sword)

        data = item.to_dict()
        restored = Item.from_dict(data)
        assert isinstance(restored, Sword)
        assert restored.name == item.name
        assert restored.category == item.category
        assert restored.rarity == item.rarity
        assert restored.base_value == item.base_value
        assert restored.attack == 25
        assert restored.durability == 42
        assert restored.equipped is True
        assert restored.level_req == 7
        assert restored.class_req == ["warrior"]
        assert data["stats"] == original_data["stats"]

    def test_consumable_roundtrip(self):
        """Consumable 序列化/反序列化往返"""
        original_data = {
            "item_id": "i_potion",
            "name": "测试药水",
            "category": "consumable.potion",
            "rarity": "common",
            "base_value": 10,
            "stats": {"effect": "heal", "power": 20, "duration": 15, "stack_size_max": 20, "count": 1},
        }
        item = Item.from_dict(original_data)
        assert isinstance(item, Potion)

        data = item.to_dict()
        restored = Item.from_dict(data)
        assert isinstance(restored, Potion)
        assert restored.name == item.name
        assert restored.effect == "heal"
        assert restored.duration == 15
        assert restored.stackable is True
        assert data["stats"] == original_data["stats"]

    def test_misc_roundtrip(self):
        """Misc 序列化/反序列化往返"""
        original_data = {
            "item_id": "i_misc",
            "name": "测试杂项",
            "category": "misc",
            "rarity": "common",
            "base_value": 1,
            "stats": {"stack_size_max": 99, "count": 5},
        }
        item = Item.from_dict(original_data)
        assert isinstance(item, Misc)

        data = item.to_dict()
        restored = Item.from_dict(data)
        assert isinstance(restored, Misc)
        assert restored.name == item.name
        assert restored.count == 5


# ========== describe() 多态测试 ==========

class TestDescribe:
    """测试 describe() 方法输出关键字段"""

    def test_weapon_describe_contains_attack(self):
        data = {
            "item_id": "i_sword",
            "name": "测试剑",
            "category": "weapon.sword",
            "rarity": "rare",
            "base_value": 100,
            "stats": {"attack": 25, "attack_speed": 1.2, "durability_max": 80},
        }
        item = Item.from_dict(data)
        desc = item.describe()
        # 中文或英文输出都可以
        assert "攻击:25" in desc or "ATK:25" in desc

    def test_armor_describe_contains_defense(self):
        data = {
            "item_id": "i_helmet",
            "name": "测试头盔",
            "category": "armor.helmet",
            "rarity": "common",
            "base_value": 50,
            "stats": {"defense": 10, "magic_resist": 5, "durability_max": 60},
        }
        item = Item.from_dict(data)
        desc = item.describe()
        assert "防御:10" in desc or "DEF:10" in desc

    def test_consumable_describe_contains_effect(self):
        data = {
            "item_id": "i_potion",
            "name": "测试药水",
            "category": "consumable.potion",
            "rarity": "common",
            "base_value": 10,
            "stats": {"effect": "heal", "power": 20, "stack_size_max": 20, "count": 1},
        }
        item = Item.from_dict(data)
        desc = item.describe()
        assert "heal" in desc or "PWR:20" in desc

    def test_tool_describe_contains_efficiency(self):
        data = {
            "item_id": "i_axe",
            "name": "测试斧",
            "category": "tool.axe",
            "rarity": "common",
            "base_value": 30,
            "stats": {"efficiency": 5, "tier": 1, "durability_max": 50},
        }
        item = Item.from_dict(data)
        desc = item.describe()
        assert "效率:5" in desc or "Eff:5" in desc

    def test_misc_describe_contains_count(self):
        data = {
            "item_id": "i_misc",
            "name": "测试杂项",
            "category": "misc",
            "rarity": "common",
            "base_value": 1,
            "stats": {"stack_size_max": 99, "count": 5},
        }
        item = Item.from_dict(data)
        desc = item.describe()
        assert "数量:5" in desc or "Count:5" in desc
