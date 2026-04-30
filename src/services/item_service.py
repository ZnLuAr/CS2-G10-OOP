"""物品查询服务"""

from __future__ import annotations

from src.errors import InvalidInputError, ItemNotFoundError     # ..errors.validation
from src.services.persistence import Persistence, Repository
from src.models import Player     # ..models.player
from src.models import (
        Sword, Bow, Spear, Hammer, Halberd,
        Axe, Pickaxe, Shovel, Hoe,
        Helmet, Chestplate, Greaves, Boots, Shield,
        Potion, Food, Magic, Material, Misc, Item
    )     # ..models.item

__all__ = ["ItemService"]


def _ensure_item(obj) -> Item:
    if isinstance(obj, Item):
        return obj
    if isinstance(obj, dict):
        return Item.from_dict(obj)
    raise TypeError("Unknown item representation")


# 【类别 → 类】映射字典
category_to_class = {
    "weapon.sword": Sword,
    "weapon.bow": Bow,
    "weapon.spear": Spear,
    "weapon.hammer": Hammer,
    "weapon.halberd": Halberd,

    "tool.axe": Axe,
    "tool.pickaxe": Pickaxe,
    "tool.shovel": Shovel,
    "tool.hoe": Hoe,

    "armor.helmet": Helmet,
    "armor.chestplate": Chestplate,
    "armor.greaves": Greaves,
    "armor.boots": Boots,
    "armor.shield": Shield,

    "consumable.potion": Potion,
    "consumable.food": Food,
    "consumable.magic": Magic,
    "consumable.material": Material,

    "misc": Misc,
}


class ItemService:
    def __init__(self, repo: Repository, persistence: Persistence, player: Player) -> None:
        self.repo = repo
        self.persistence = persistence
        self.player = player

    def list_by_id(self, item_id: str) -> Item:
        item = self.repo.items.get(item_id)
        if item is None:
            raise ItemNotFoundError(item_id=item_id)
        return _ensure_item(item)

    def list_all(self, category_prefix: str | None = None) -> list[Item]:
        if category_prefix is None:
            return [_ensure_item(it) for it in self.repo.items.values()]
        return self.list_by_category(category_prefix)

    def list_catalog(self, node_key: str = "root") -> dict:
        if node_key == "root":
            root = self.repo.catalog.get("root")
            if root is None:
                raise InvalidInputError(field="node_key", value=node_key)
            return root

        found = self.find_catalog_node(self.repo.catalog.get("root", {}), node_key)
        if found is None:
            raise InvalidInputError(field="node_key", value=node_key)
        return found

    def list_by_category(self, category: str) -> list[Item]:
        result = []
        for it in self.repo.items.values():     # item:dict["item_id":{...}]
            if isinstance(it, dict):
                cat = it.get("category")
            else:
                raise ItemNotFoundError(item_id=category)
            if cat.startswith(category):     # prefix match
                result.append(_ensure_item(it))
        return result

    @staticmethod
    def create_item(payload: dict) -> Item:
        try:
            return Item.from_dict(payload)
        except Exception:
            raise InvalidInputError(field="payload", value=payload)

    def find_catalog_node(self, node: dict, node_key: str) -> dict | None:
        if not isinstance(node, dict):
            return None
        if node.get("key") == node_key:
            return node
        for child in node.get("children", []):
            found = self.find_catalog_node(child, node_key)
            if found is not None:
                return found
        return None
