"""物品查询服务"""

from __future__ import annotations

from src.errors import InvalidInputError, ItemNotFoundError
from src.services.persistence import Persistence, Repository

__all__ = ["ItemService"]




class ItemService:
    def __init__(self, repo: Repository, persistence: Persistence) -> None:
        self.repo = repo
        self.persistence = persistence

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
        for it in self.repo.items.values():
            if it.get("category", "").startswith(category):
                return it

    def create_item(self, payload: dict) -> dict:
        raise NotImplementedError("待 Item 多态层落地后实现")

    def delete_item(self, item_id: str) -> None:
        raise NotImplementedError("待 Item 多态层与引用校验完善后实现")

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
