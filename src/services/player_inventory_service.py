"""PlayerInventoryService - 玩家背包业务服务

封装玩家背包的所有业务操作，包括：
- 查询背包内容（原始顺序/排序后）
- 添加/移除物品（管理员调试）
- 物品流转（上架、购买、撤销等场景）

职责边界：
- 本层处理：构造 Inventory 对象、操作、持久化保存
- CLI 层只负责：输入收集、调用服务、结果展示
- MarketService 后续通过本服务操作背包，不直接操作 Inventory
"""

from __future__ import annotations

from src.errors import (
    InvalidInputError,
    InventoryFullError,
    ItemNotFoundError,
    PlayerNotFoundError,
)
from src.services.inventory import Inventory
from src.services.persistence import Persistence, Repository

__all__ = ["PlayerInventoryService"]




class PlayerInventoryService:
    """
    玩家背包业务服务

    为 CLI 和 MarketService 提供统一的背包操作入口。
    所有操作自动处理：构造 Inventory → 执行操作 → 持久化保存
    """

    def __init__(self, repo: Repository, persistence: Persistence) -> None:
        self.repo = repo
        self.persistence = persistence


    # ========== 查询接口 ==========

    def get_inventory(self, player_id: str) -> Inventory:
        """
        获取玩家背包对象

        Args:
            player_id: 玩家 ID

        Returns:
            构造好的 Inventory 对象

        Raises:
            PlayerNotFoundError: 玩家不存在
        """
        player = self._get_player_or_raise(player_id)
        return self._build_inventory(player_id, player.inventory)


    def get_slots(self, player_id: str) -> list:
        """获取玩家背包槽位列表（按链表顺序）"""
        inventory = self.get_inventory(player_id)
        return inventory.slots()


    def get_sorted_view(self, player_id: str, key: str = "rarity") -> list:
        """
        获取排序后的背包槽位列表

        Args:
            player_id: 玩家 ID
            key: 排序键，目前仅支持 "rarity"

        Returns:
            排序后的槽位列表（不修改内部链表顺序）
        """
        inventory = self.get_inventory(player_id)
        return inventory.sorted_view(key=key)


    def get_capacity_info(self, player_id: str) -> dict:
        """
        获取背包容量信息

        Returns:
            {"capacity": int, "used": int, "remaining": int, "is_full": bool}
        """
        inventory = self.get_inventory(player_id)
        return {
            "capacity": inventory.capacity,
            "used": inventory.used(),
            "remaining": inventory.capacity - inventory.used(),
            "is_full": inventory.is_full(),
        }


    # ========== 管理操作（管理员调试） ==========

    def add_item(self, player_id: str, item_id: str, count: int = 1) -> None:
        """
        向玩家背包添加物品（管理员调试用）

        Args:
            player_id: 玩家 ID
            item_id: 物品 ID
            count: 添加数量，必须 > 0

        Raises:
            PlayerNotFoundError: 玩家不存在
            ItemNotFoundError: 物品不存在
            InvalidInputError: count <= 0
            InventoryFullError: 背包已满
        """
        if count <= 0:
            raise InvalidInputError(field="count", value=count)

        player = self._get_player_or_raise(player_id)
        item = self._get_item_or_raise(item_id)

        inventory = self._build_inventory(player_id, player.inventory)

        try:
            inventory.add(item, count=count)
            # 同步回 player 并保存
            player.inventory = inventory.to_inventory_data()
            self.persistence.save_players(self.repo)
        except InventoryFullError as e:
            # 补充上下文
            raise InventoryFullError(
                player_id=player_id,
                capacity=inventory.capacity,
                context={"item_id": item_id, "count": count, **e.context}
            ) from None


    def remove_item(self, player_id: str, item_id: str, count: int = 1) -> None:
        """
        从玩家背包移除物品

        Args:
            player_id: 玩家 ID
            item_id: 物品 ID
            count: 移除数量，必须 > 0

        Raises:
            PlayerNotFoundError: 玩家不存在
            ItemNotFoundError: 物品不存在于背包
            InvalidInputError: count <= 0 或数量不足
        """
        if count <= 0:
            raise InvalidInputError(field="count", value=count)

        player = self._get_player_or_raise(player_id)

        inventory = self._build_inventory(player_id, player.inventory)

        # Inventory.remove 内部已检查存在性和数量，无需重复检查
        inventory.remove(item_id, count=count)

        # 同步回 player 并保存
        player.inventory = inventory.to_inventory_data()
        self.persistence.save_players(self.repo)


    # ========== 业务流转接口（供 MarketService 调用） ==========

    def move_to_listing(self, player_id: str, item_id: str, count: int = 1) -> None:
        """
        物品从背包移到挂单（上架时调用）

        Args:
            player_id: 卖家 ID
            item_id: 物品 ID
            count: 数量（对于可堆叠物品可能 >1）

        Raises:
            PlayerNotFoundError: 玩家不存在
            ItemNotFoundError: 物品不在背包
            InvalidInputError: 数量不足
        """
        # 目前等价于 remove_item，后续可扩展挂单锁定逻辑
        self.remove_item(player_id, item_id, count)


    def move_from_listing(self, player_id: str, item_id: str, count: int = 1) -> None:
        """
        物品从挂单退回背包（撤销挂单时调用）

        Args:
            player_id: 卖家 ID
            item_id: 物品 ID
            count: 数量

        Raises:
            PlayerNotFoundError: 玩家不存在
            ItemNotFoundError: 物品不存在（系统中）
            InventoryFullError: 背包已满无法退回
        """
        self.add_item(player_id, item_id, count)


    def transfer_item(
        self,
        from_player_id: str,
        to_player_id: str,
        item_id: str,
        count: int = 1
    ) -> None:
        """
        物品从一个玩家转移到另一个玩家（交易时调用）

        原子操作：买家金币扣减和物品转移应在 MarketService 事务中完成，
        本方法只处理物品转移部分。

        Args:
            from_player_id: 卖家 ID
            to_player_id: 买家 ID
            item_id: 物品 ID
            count: 数量

        Raises:
            PlayerNotFoundError: 任一方玩家不存在
            ItemNotFoundError: 物品不在卖家背包
            InvalidInputError: 数量不足
            InventoryFullError: 买家背包已满
        """
        if count <= 0:
            raise InvalidInputError(field="count", value=count)

        from_player = self._get_player_or_raise(from_player_id)
        to_player = self._get_player_or_raise(to_player_id)
        item = self._get_item_or_raise(item_id)

        from_inventory = self._build_inventory(from_player_id, from_player.inventory)
        from_inventory.remove(item_id, count=count)

        if from_player_id == to_player_id:
            return

        to_inventory = self._build_inventory(to_player_id, to_player.inventory)
        try:
            to_inventory.add(item, count=count)
        except InventoryFullError as e:
            raise InventoryFullError(
                player_id=to_player_id,
                capacity=to_inventory.capacity,
                context={"item_id": item_id, "count": count, **e.context}
            ) from None

        from_player.inventory = from_inventory.to_inventory_data()
        to_player.inventory = to_inventory.to_inventory_data()
        self.persistence.save_players(self.repo)


    # ========== 内部方法 ==========

    def _get_player_or_raise(self, player_id: str):
        """获取玩家，不存在则抛异常"""
        player = self.repo.players.get(player_id)
        if player is None:
            raise PlayerNotFoundError(player_id=player_id)
        return player


    def _get_item_or_raise(self, item_id: str):
        """获取物品，不存在则抛异常"""
        item = self.repo.items.get(item_id)
        if item is None:
            raise ItemNotFoundError(item_id=item_id)
        return item


    def _build_inventory(self, player_id: str, data: list[dict]) -> Inventory:
        """从 player.inventory 数据构造 Inventory 对象"""
        return Inventory.from_inventory_data(
            owner_id=player_id,
            data=data,
            item_lookup=lambda iid: self.repo.items[iid]
        )
