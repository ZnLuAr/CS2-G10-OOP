"""物品查询服务"""

from __future__ import annotations

from src.errors import InvalidInputError, ItemNotFoundError     # ..errors.validation
from persistence import Persistence, Repository
from src.models import Player     # ..models.player
from src.item import (
        Sword, Bow, Spear, Hammer, Halberd,
        Axe, Pickaxe, Shovel, Hoe,
        Helmet, Chestplate, Greaves, Boots, Shield,
        Potion, Food, Magic, Material, Misc, Item
    )     # ..models.item

__all__ = ["ItemService"]


class ItemService:
    def __init__(self, repo: Repository, persistence: Persistence, player: Player, item: Item) -> None:
        self.repo = repo
        self.persistence = persistence
        self.player = player
        self.item = item

    def get_by_id(self, item_id: str) -> dict:
        item = self.repo.items.get(item_id)
        if item is None:
            raise ItemNotFoundError(item_id=item_id)
        return item

    def list_all(self, category_prefix: str | None = None) -> list[dict]:
        if category_prefix is None:
            return list(self.repo.items.values())
        return self.items_in_category(category_prefix)

    def browse_catalog(self, node_key: str = "root") -> dict:
        if node_key == "root":
            root = self.repo.catalog.get("root")
            if root is None:
                raise InvalidInputError(field="node_key", value=node_key)
            return root

        found = self._find_catalog_node(self.repo.catalog.get("root", {}), node_key)
        if found is None:
            raise InvalidInputError(field="node_key", value=node_key)
        return found

    def items_in_category(self, category: str) -> list[dict]:
        return [
            it
            for it in self.repo.items.values()
            if it.get("category", "").startswith(category)
        ]

    def create_item(self, payload: dict) -> Item:
        return self.item.from_dict(payload)

    def delete_item(self, item_id: str) -> None:
        to_remove_idx = None
        for idx, item_data in enumerate(self.player.inventory):
            if item_data["item_id"] == item_id:
                to_remove_idx = idx
                break

        if to_remove_idx is None:
            raise ItemNotFoundError(item_id=item_id)
        if Player.can_be_deleted(self.player) is None:
            raise ValueError("item still exist")
        del self.player.inventory[to_remove_idx]

    def _find_catalog_node(self, node: dict, node_key: str) -> dict | None:
        if not isinstance(node, dict):
            return None
        if node.get("key") == node_key:
            return node
        for child in node.get("children", []):
            found = self._find_catalog_node(child, node_key)
            if found is not None:
                return found
        return None
