"""种子数据生成器（功能 ID 1）。

首次启动时若 data/ 下无业务文件则生成初始数据集：
- 玩家 ≥ 10
- 物品 ≥ 50
- 挂单 ≥ 20
- 完整的 Catalog 分类树

所有数据严格遵循 docs/data-design.md 的字段约定。
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from typing import Any

__all__ = ["generate_seed"]


_RARITIES = ["common", "uncommon", "rare", "epic", "legendary"]
_CLASSES = ["warrior", "archer", "mage", "summon", "none"]




# ---------------------------------------------------------------------------
# Items 示例定义
# ---------------------------------------------------------------------------

_ITEM_TEMPLATES: list[tuple[str, str, dict[str, Any]]] = [
    # weapon.sword
    ("weapon.sword", "短剑", {"attack": 25, "attack_speed": 1.6,
                              "durability_max": 80, "slot": "weapon"}),
    ("weapon.sword", "日耀喷发剑", {"attack": 105, "attack_speed": 1.3,
                              "durability_max": 120, "slot": "weapon"}),
    ("weapon.sword", "餓王剣「餓鬼十王の報い」", {"attack": 85, "attack_speed": 1.4,
                              "durability_max": 200, "slot": "weapon"}),
    # weapon.bow
    ("weapon.bow", "短弓", {"attack": 30, "attack_speed": 1.2,
                            "durability_max": 60, "slot": "weapon"}),
    ("weapon.bow", "恋人を射ち堕とす", {"attack": 500, "attack_speed": 1.0,
                            "durability_max": 100, "slot": "weapon"}),
    # weapon.spear
    ("weapon.spear", "铁矛", {"attack": 40, "attack_speed": 0.9,
                              "durability_max": 110, "slot": "weapon"}),
    ("weapon.spear", "风暴长矛", {"attack": 70, "attack_speed": 0.8,
                                  "durability_max": 180, "slot": "weapon"}),
    # weapon.hammer
    ("weapon.hammer", "血肉球", {"attack": 95, "attack_speed": 0.6,
                               "durability_max": 250, "slot": "weapon"}),
    # weapon.halberd
    ("weapon.halberd", "三叉戟", {"attack": 60, "attack_speed": 0.85,
                                  "durability_max": 160, "slot": "weapon"}),

    # tool.axe / pickaxe / shovel / hoe
    ("tool.axe", "木斧", {"efficiency": 1.0, "tier": 1, "durability_max": 60}),
    ("tool.axe", "铁斧", {"efficiency": 1.5, "tier": 3, "durability_max": 200}),
    ("tool.pickaxe", "石镐", {"efficiency": 1.2, "tier": 2, "durability_max": 100}),
    ("tool.pickaxe", "蘑菇爪", {"efficiency": 25, "tier": 3, "durability_max": 200}),
    ("tool.pickaxe", "钻石镐", {"efficiency": 2.5, "tier": 5, "durability_max": 500}),
    ("tool.shovel", "铁锹", {"efficiency": 1.3, "tier": 3, "durability_max": 180}),
    ("tool.hoe", "铁锄", {"efficiency": 1.2, "tier": 3, "durability_max": 150}),

    # armor.helmet / chestplate / greaves / boots / shield
    ("armor.helmet", "皮帽", {"defense": 3, "magic_resist": 1, "slot": "helmet",
                              "durability_max": 80}),
    ("armor.helmet", "神圣兜帽", {"defense": 1, "magic_resist": 2, "slot": "helmet",
                              "durability_max": 200}),
    ("armor.chestplate", "皮甲", {"defense": 6, "magic_resist": 2,
                                  "slot": "chestplate", "durability_max": 120}),
    ("armor.chestplate", "钯金盔甲", {"defense": 10, "magic_resist": 4,
                                  "slot": "chestplate", "durability_max": 300}),
    ("armor.greaves", "奥钢护胫", {"defense": 10, "magic_resist": 2,
                                 "slot": "greaves", "durability_max": 200}),
    ("armor.boots", "欧内的手", {"defense": 3, "magic_resist": 1,
                             "slot": "boots", "durability_max": 80}),
    ("armor.boots", "水晶刺客靴", {"defense": 10, "magic_resist": 2,
                             "slot": "boots", "durability_max": 180}),
    ("armor.shield", "克苏鲁护盾", {"defense": 2, "magic_resist": 0,
                              "slot": "shield", "durability_max": 100}),
    ("armor.shield", "十字章护盾", {"defense": 4, "magic_resist": 400,
                              "slot": "shield", "durability_max": 250}),

    # consumable.potion
    ("consumable.potion", "生命药水(小)", {"effect": "heal", "power": 100,
                                           "duration": 0, "stack_size_max": 16}),
    ("consumable.potion", "生命药水(中)", {"effect": "heal", "power": 300,
                                           "duration": 0, "stack_size_max": 8}),
    ("consumable.potion", "魔力药水", {"effect": "mana", "power": 150,
                                       "duration": 0, "stack_size_max": 16}),
    ("consumable.potion", "力量药剂", {"effect": "buff_attack", "power": 20,
                                       "duration": 30, "stack_size_max": 8}),

    # consumable.food
    ("consumable.food", "韭菜合子", {"effect": "heal", "power": 20, "duration": 0,
                                 "stack_size_max": 32, "nutrition": 30}),
    ("consumable.food", "鞋垫", {"effect": "heal", "power": 60, "duration": 0,
                                 "stack_size_max": 16, "nutrition": 60}),

    # consumable.magic
    ("consumable.magic", "火球卷轴", {"effect": "buff_attack", "power": 50,
                                      "duration": 0, "stack_size_max": 8,
                                      "mana_cost": 30}),
    ("consumable.magic", "空大魔术", {"effect": "none", "power": 0, "duration": 0,
                                      "stack_size_max": 4, "mana_cost": 50}),

    # consumable.material
    ("consumable.material", "铁锭", {"effect": "none", "power": 0, "duration": 0,
                                     "stack_size_max": 64}),
    ("consumable.material", "金锭", {"effect": "none", "power": 0, "duration": 0,
                                     "stack_size_max": 64}),
    ("consumable.material", "魔法粉尘", {"effect": "none", "power": 0,
                                         "duration": 0, "stack_size_max": 32}),

    # misc
    ("misc", "唢呐", {"stack_size_max": 99}),
    ("misc", "榔冰", {"stack_size_max": 64}),
    ("misc", "易拉罐", {"stack_size_max": 16}),
    ("misc", "一把米诺", {"stack_size_max": 8}),
]




# ---------------------------------------------------------------------------
# Catalog（与 data-design.md §8.1 一一对应）
# ---------------------------------------------------------------------------

def _build_catalog() -> dict[str, Any]:
    return {
        "root": {
            "key": "root",
            "label": "全部",
            "children": [
                {
                    "key": "weapon",
                    "label": "武器",
                    "children": [
                        {"key": k, "label": v, "children": []}
                        for k, v in [
                            ("sword", "剑"), ("bow", "弓弩"),
                            ("spear", "长矛"), ("hammer", "重锤"),
                            ("halberd", "长戟"),
                        ]
                    ],
                },
                {
                    "key": "tool",
                    "label": "工具",
                    "children": [
                        {"key": k, "label": v, "children": []}
                        for k, v in [
                            ("axe", "斧"), ("pickaxe", "镐"),
                            ("shovel", "锹"), ("hoe", "锄"),
                        ]
                    ],
                },
                {
                    "key": "armor",
                    "label": "装备",
                    "children": [
                        {"key": k, "label": v, "children": []}
                        for k, v in [
                            ("helmet", "头盔"), ("chestplate", "胸甲"),
                            ("greaves", "护胫"), ("boots", "靴子"),
                            ("shield", "盾牌"),
                        ]
                    ],
                },
                {
                    "key": "consumable",
                    "label": "消耗品",
                    "children": [
                        {"key": k, "label": v, "children": []}
                        for k, v in [
                            ("potion", "药水"), ("food", "食物"),
                            ("magic", "魔法物品"), ("material", "材料"),
                        ]
                    ],
                },
                {"key": "misc", "label": "杂项", "children": []},
            ],
        }
    }


def _is_stackable(category: str) -> bool:
    return category.startswith("consumable") or category == "misc"


def _has_durability(category: str) -> bool:
    return category.startswith(("weapon", "tool", "armor"))


def _has_equipped(category: str) -> bool:
    return category.startswith(("weapon", "armor"))


def _build_items() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    rng = random.Random(20260420)  # 固定种子，便于复现
    # 把模板复制 2 遍以便达到 ≥50 件，并随机化稀有度与基础价值
    pool = _ITEM_TEMPLATES + _ITEM_TEMPLATES[: max(0, 50 - len(_ITEM_TEMPLATES))]
    for idx, (category, name, stats_template) in enumerate(pool, start=1):
        rarity = rng.choice(_RARITIES)
        base_value = rng.randint(20, 2000)
        stats = dict(stats_template)
        if _has_durability(category):
            stats["durability"] = stats["durability_max"]
        if _has_equipped(category):
            stats["equipped"] = False
        if _is_stackable(category):
            stats["count"] = stats.get("stack_size_max", 1)
        items.append({
            "item_id": f"i_{idx:03d}",
            "name": name,
            "category": category,
            "rarity": rarity,
            "base_value": base_value,
            "stats": stats,
        })
    return items




# ---------------------------------------------------------------------------
# Players
# ---------------------------------------------------------------------------

_PLAYER_NAMES = [
    "Arthur", "Bryn", "Cedric", "Diana", "Eira",
    "Finn", "Gwen", "Hector", "Isolde", "Jorah",
    "Kael", "Lyra",
]


def _build_players(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rng = random.Random(20260420)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    players: list[dict[str, Any]] = []
    for idx, name in enumerate(_PLAYER_NAMES, start=1):
        # 每位玩家随机 0-5 件初始物品
        inventory: list[dict[str, Any]] = []
        sample = rng.sample(items, k=rng.randint(0, 5))
        for it in sample:
            slot = {"item_id": it["item_id"], "count": 1}
            if _is_stackable(it["category"]):
                slot["count"] = rng.randint(1, it["stats"]["stack_size_max"])
            inventory.append(slot)
        players.append({
            "player_id": f"p_{idx:03d}",
            "name": name,
            "gold": rng.randint(100, 5000),
            "level": rng.randint(1, 30),
            "class": rng.choice(_CLASSES),
            "inventory": inventory,
            "created_at": now,
        })
    return players




# ---------------------------------------------------------------------------
# Listings
# ---------------------------------------------------------------------------

def _build_listings(players: list[dict[str, Any]],
                    items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rng = random.Random(20260420)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    listings: list[dict[str, Any]] = []
    for idx in range(1, 26):  # 25 条挂单
        seller = rng.choice(players)
        item = rng.choice(items)
        listings.append({
            "listing_id": f"l_{idx:03d}",
            "seller_id": seller["player_id"],
            "item_id": item["item_id"],
            "count": 1,
            "price": rng.randint(50, 3000),
            "status": "active",
            "created_at": now,
            "closed_at": None,
        })
    return listings




# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def generate_seed() -> dict[str, Any]:
    """生成完整的初始数据集，返回 dict 供 Persistence 写入。

    返回结构::

        {
            "catalog":      {...},
            "items":        [...],
            "players":      [...],
            "listings":     [...],
            "transactions": [],
        }
    """
    catalog = _build_catalog()
    items = _build_items()
    players = _build_players(items)
    listings = _build_listings(players, items)
    return {
        "catalog": catalog,
        "items": items,
        "players": players,
        "listings": listings,
        "transactions": [],
    }
