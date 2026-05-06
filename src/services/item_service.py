"""ItemService - 物品查询与管理服务

实现 docs/services-interface.md §7 的 ItemService 接口。
- 查询：get_by_id, list_all, browse_catalog, items_in_category
- 管理：create_item, delete_item（管理员）
"""

from __future__ import annotations

from src.errors import (
    BusinessRuleError,
    InvalidInputError,
    ItemNotFoundError,
    SerializationError,
)
from src.models import Item
from src.services.persistence import Persistence, Repository
from src.services.logger import log
from src.structures import CatalogNode

__all__ = ["ItemService"]


# 合法的稀有度值
VALID_RARITIES = {"common", "uncommon", "rare", "epic", "legendary"}




class ItemService:
    def __init__(self, repo: Repository, persistence: Persistence) -> None:
        self.repo = repo
        self.persistence = persistence

    # ========== 查询接口 ==========

    def get_by_id(self, item_id: str) -> Item:
        """根据 ID 获取物品

        Args:
            item_id: 物品 ID

        Returns:
            Item 对象

        Raises:
            ItemNotFoundError: 物品不存在
        """
        item = self.repo.items.get(item_id)
        if item is None:
            raise ItemNotFoundError(item_id=item_id)
        return item


    def list_all(self, category_prefix: str | None = None) -> list[Item]:
        """列出所有物品，可选按分类前缀过滤

        Args:
            category_prefix: 分类前缀（如 "weapon" 匹配 weapon.sword）

        Returns:
            Item 对象列表
        """
        if category_prefix is None:
            return list(self.repo.items.values())
        return self.items_in_category(category_prefix)


    def browse_catalog(self, node_key: str = "root") -> CatalogNode:
        """浏览分类目录

        Args:
            node_key: 节点 key（默认 root）

        Returns:
            CatalogNode 对象

        Raises:
            InvalidInputError: 节点不存在
        """
        if self.repo.catalog is None:
            raise InvalidInputError(field="node_key", value=node_key)

        if node_key == "root":
            return self.repo.catalog.root

        node = self.repo.catalog.find_node(node_key)
        if node is None:
            raise InvalidInputError(field="node_key", value=node_key)
        return node


    def items_in_category(self, category: str) -> list[Item]:
        """获取指定分类下的所有物品（前缀匹配）

        Args:
            category: 分类路径前缀（如 "weapon", "weapon.sword"）

        Returns:
            Item 对象列表
        """
        if self.repo.catalog is None or self.repo.catalog.find_by_path(category) is None:
            raise InvalidInputError(field="category", value=category)

        if category == "root":
            return list(self.repo.items.values())

        result = []
        prefix = f"{category}."
        for item in self.repo.items.values():
            if item.category == category or item.category.startswith(prefix):
                result.append(item)
        return result


    # ========== 管理接口（管理员） ==========

    def create_item(self, payload: dict) -> Item:
        """创建新物品

        Args:
            payload: 物品数据，必须包含：
                - name: 物品名称
                - category: 分类路径（如 "weapon.sword"）
                - rarity: 稀有度
                - base_value: 基础价值（>=0）
                - stats: 扩展属性字典
                - description: 描述（可选）

        Returns:
            创建的 Item 对象

        Raises:
            InvalidInputError: 字段缺失或非法
            SerializationError: 构造失败
        """
        required = ["name", "category", "rarity", "base_value", "stats"]
        for field in required:
            if field not in payload:
                raise InvalidInputError(field=field, value=None)

        name = payload["name"]
        category = payload["category"]
        rarity = payload["rarity"]
        base_value = payload["base_value"]
        stats = payload["stats"]
        description = payload.get("description", "")

        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 40:
            raise InvalidInputError(field="name", value=name)
        if not isinstance(category, str):
            raise InvalidInputError(field="category", value=category)
        if not isinstance(stats, dict):
            raise InvalidInputError(field="stats", value=stats)
        if not isinstance(description, str) or len(description) > 200:
            raise InvalidInputError(field="description", value=description)

        if self.repo.catalog is None:
            raise InvalidInputError(field="category", value=category)
        category_node = self.repo.catalog.find_by_path(category)
        if category_node is None or not category_node.is_leaf:
            raise InvalidInputError(field="category", value=category)

        if rarity not in VALID_RARITIES:
            raise InvalidInputError(field="rarity", value=rarity)

        if not isinstance(base_value, int) or isinstance(base_value, bool) or base_value < 0:
            raise InvalidInputError(field="base_value", value=base_value)

        preview_payload = {
            "item_id": "i_preview",
            "name": name.strip(),
            "category": category,
            "rarity": rarity,
            "base_value": base_value,
            "description": description,
            "stats": stats,
        }

        item = Item.from_dict(preview_payload)

        item.item_id = self.persistence.next_item_id()
        self.repo.items[item.item_id] = item
        self.persistence.save_items(self.repo)

        log.info("item_service", "item_created", item_id=item.item_id, name=item.name)
        return item


    def delete_item(self, item_id: str) -> None:
        """删除物品

        Args:
            item_id: 物品 ID

        Raises:
            ItemNotFoundError: 物品不存在
            BusinessRuleError: 物品仍被引用（玩家背包或活跃挂单）
        """
        # 检查存在性
        if item_id not in self.repo.items:
            raise ItemNotFoundError(item_id=item_id)

        item = self.repo.items[item_id]

        # 检查玩家背包引用
        for player in self.repo.players.values():
            for slot in player.inventory:
                if slot.get("item_id") == item_id:
                    raise BusinessRuleError(
                        action="delete_item",
                        reason=f"item is held by player {player.player_id}",
                        context={"item_id": item_id, "player_id": player.player_id},
                    )

        # 检查活跃挂单引用
        for listing in self.repo.listings.values():
            if listing.item_id == item_id and listing.status == "active":
                raise BusinessRuleError(
                    action="delete_item",
                    reason=f"item is in active listing {listing.listing_id}",
                    context={"item_id": item_id, "listing_id": listing.listing_id},
                )

        # 执行删除
        del self.repo.items[item_id]
        self.persistence.save_items(self.repo)

        log.info("item_service", "item_deleted", item_id=item_id, name=item.name)
