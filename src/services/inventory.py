"""Inventory 服务实现

基于双向链表的背包管理，支持：
- 槽位管理（插入顺序保持）
- 物品堆叠（考虑 stackable 和 stack_size_max）
- 按稀有度排序展示（不改变内部顺序）
- 与 Player.inventory list[dict] 的双向转换
"""

from __future__ import annotations

from src.errors import InvalidInputError, ItemNotFoundError, InventoryFullError
from src.structures.doubly_linked_list import DoublyLinkedList

__all__ = ["Inventory", "InventorySlot"]



def _get_attr(item, attr: str, default=None):
    if isinstance(item, dict):
        return item.get(attr, default)
    return getattr(item, attr, default)


def _item_id(item) -> str:
    if isinstance(item, dict):
        return item["item_id"]
    return item.item_id




class InventorySlot:
    """
    背包槽位

    字段：
        item: 物品对象或 dict（需支持 .item_id, .name, .rarity, .stackable, .stack_size_max）
        count: 当前数量
        instance_state: 实例状态 dict（独立副本）
    """

    def __init__(self, item, count: int = 1, instance_state: dict | None = None):
        self.item = item
        self.count = count
        # 复制 dict 避免多个槽位共享引用
        self.instance_state = dict(instance_state) if instance_state else {}

    def to_dict(self) -> dict:
        """序列化为 Player.inventory 数组元素格式"""
        result = {"item_id": self._item_id(), "count": self.count}
        if self.instance_state:
            result["instance_state"] = dict(self.instance_state)
        return result

    def _item_id(self) -> str:
        """统一获取 item_id（支持 Item 对象或 dict）"""
        return _item_id(self.item)

    def get_display_name(self) -> str:
        """获取用于 CLI 展示的物品名"""
        return _get_attr(self.item, "name", self._item_id())

    def get_rarity(self) -> str:
        """获取用于 CLI 展示和排序的稀有度"""
        return _get_attr(self.item, "rarity", "unknown")




class Inventory:
    """
    玩家背包实现

    使用双向链表保持物品添加顺序，支持 O(1) 尾部插入和已知节点删除。
    对外提供文档约定的接口方法。
    """

    CAPACITY: int = 50
    RARITY_ORDER: list[str] = ["common", "uncommon", "rare", "epic", "legendary"]

    def __init__(self, owner_id: str, capacity: int | None = None) -> None:
        self.owner_id: str = owner_id
        self.capacity: int = capacity if capacity is not None else self.CAPACITY
        self._slots: DoublyLinkedList = DoublyLinkedList()


    # ========== 查询接口 ==========

    def slots(self) -> list[InventorySlot]:
        """返回槽位列表（按链表顺序，不改变内部存储）"""
        return list(self._slots)


    def find(self, item_id: str) -> InventorySlot | None:
        """按 item_id 查找第一个匹配的槽位"""
        for slot in self._slots:
            if slot._item_id() == item_id:
                return slot
        return None


    def find_by_state(self, item_id: str, instance_state: dict | None) -> InventorySlot | None:
        """按 item_id 和 instance_state 查找匹配的槽位

        Args:
            item_id: 物品 ID
            instance_state: 实例状态 dict，None 表示无状态

        Returns:
            第一个匹配的槽位，或 None
        """
        target_state = instance_state or {}
        for slot in self._slots:
            if slot._item_id() == item_id and slot.instance_state == target_state:
                return slot
        return None


    def is_full(self) -> bool:
        """检查背包是否已满"""
        return len(self._slots) >= self.capacity


    def used(self) -> int:
        """返回已使用槽位数"""
        return len(self._slots)


    def sorted_view(self, key: str = "rarity") -> list[InventorySlot]:
        """
        返回排序后的槽位列表（不改变内部链表顺序）

        Args:
            key: 排序键，目前仅支持 "rarity"（按稀有度）

        Returns:
            新的列表，内部链表顺序保持不变
        """
        if key != "rarity":
            raise InvalidInputError(field="key", value=key)

        lst = list(self._slots)
        if len(lst) <= 1:
            return lst

        def _rarity_key(slot):
            r = slot.get_rarity()
            try:
                return self.RARITY_ORDER.index(r)
            except ValueError:
                return 99  # 未知稀有度排最后

        lst.sort(key=_rarity_key)
        return lst


    # ========== 修改接口 ==========

    def add(self, item, count: int = 1, instance_state: dict | None = None) -> None:
        """
        向背包添加物品

        Args:
            item: 物品对象（需有 .item_id, .name, .rarity, .stackable, .stack_size_max）
                  或 dict 格式的物品数据
            count: 添加数量，必须 > 0
            instance_state: 实例状态，可堆叠合并时也会比较此字段

        Raises:
            InvalidInputError: count <= 0
            InventoryFullError: 背包已满且无法继续合堆叠
        """
        if count <= 0:
            raise InvalidInputError(field="count", value=count)

        remaining = count

        # 统一获取物品属性（支持对象或 dict）
        stackable = _get_attr(item, "stackable", False)
        stack_size_max = _get_attr(item, "stack_size_max", 1) if stackable else 1
        # 防止无效 stack_size_max 导致死循环
        if stackable and (not isinstance(stack_size_max, int) or stack_size_max <= 0):
            stack_size_max = 1

        # 可堆叠物品：尝试合入既有槽位（需满足 item_id 相同且 instance_state 相同）
        if stackable:
            for slot in self._slots:
                if self._can_merge(slot, item, instance_state, stack_size_max):
                    space = stack_size_max - slot.count
                    if space > 0:
                        add_amount = min(space, remaining)
                        slot.count += add_amount
                        remaining -= add_amount
                        if remaining == 0:
                            return

        # 剩余数量需要新建槽位
        while remaining > 0:
            if len(self._slots) >= self.capacity:
                raise InventoryFullError(
                    player_id=self.owner_id,
                    capacity=self.capacity,
                    context={"remaining_to_add": remaining}
                )

            add_amount = min(stack_size_max, remaining) if stackable else 1
            # 创建槽位时复制 instance_state，避免引用共享
            self._slots.add_tail(InventorySlot(item, add_amount, dict(instance_state) if instance_state else None))
            remaining -= add_amount


    def remove(self, item_id: str, count: int = 1) -> None:
        """
        从背包移除指定数量的物品

        Args:
            item_id: 要移除的物品 ID
            count: 移除数量，必须 > 0

        Raises:
            InvalidInputError: count <= 0
            ItemNotFoundError: 物品不存在
            InvalidInputError: 数量不足（操作前检查，保证原子性）
        """
        if count <= 0:
            raise InvalidInputError(field="count", value=count)

        # 先统计总数，确保原子性（不足时直接抛异常，不修改任何状态）
        total = self._count_item(item_id)
        if total == 0:
            raise ItemNotFoundError(item_id=item_id)
        if total < count:
            raise InvalidInputError(
                field="count",
                value=count,
                context={"available": total, "requested": count, "item_id": item_id}
            )

        # 确认足够后执行删除
        remaining = count
        cur = self._slots.head
        while cur and remaining > 0:
            slot = cur.data
            next_node = cur.next

            if slot._item_id() == item_id:
                if slot.count > remaining:
                    slot.count -= remaining
                    remaining = 0
                else:
                    remaining -= slot.count
                    self._slots.remove_node(cur)

            cur = next_node


    def remove_by_state(self, item_id: str, instance_state: dict | None, count: int = 1) -> None:
        """
        从背包移除指定数量、特定 instance_state 的物品

        与 remove() 的区别：此方法精确匹配 item_id + instance_state，
        只移除具有特定状态的物品（如特定强化等级、附魔属性等）

        Args:
            item_id: 要移除的物品 ID
            instance_state: 实例状态 dict，None 表示无状态
            count: 移除数量，必须 > 0

        Raises:
            InvalidInputError: count <= 0
            ItemNotFoundError: 不存在匹配 item_id + state 的槽位
            InvalidInputError: 数量不足（操作前检查，保证原子性）
        """
        if count <= 0:
            raise InvalidInputError(field="count", value=count)

        target_state = instance_state or {}

        # 先查找匹配的槽位（只匹配第一个）
        target_slot = None
        for slot in self._slots:
            if slot._item_id() == item_id and slot.instance_state == target_state:
                target_slot = slot
                break

        if target_slot is None:
            raise ItemNotFoundError(item_id=item_id)

        if target_slot.count < count:
            raise InvalidInputError(
                field="count",
                value=count,
                context={"available": target_slot.count, "requested": count, "item_id": item_id}
            )

        # 原子性执行删除
        if target_slot.count > count:
            target_slot.count -= count
        else:
            # 需要找到 node 来删除
            cur = self._slots.head
            while cur:
                if cur.data is target_slot:
                    self._slots.remove_node(cur)
                    break
                cur = cur.next


    # ========== 序列化/反序列化 ==========

    @classmethod
    def from_inventory_data(
        cls,
        owner_id: str,
        data: list[dict],
        item_lookup: callable,
        capacity: int | None = None
    ) -> Inventory:
        """
        从 Player.inventory 列表构造 Inventory

        Args:
            owner_id: 玩家 ID
            data: Player.inventory 的 list[dict] 格式
            item_lookup: 函数，接收 item_id 返回物品对象（Item 或 dict）
            capacity: 背包容量上限，默认使用 CAPACITY

        Returns:
            构造好的 Inventory 实例
        """
        inventory = cls(owner_id=owner_id, capacity=capacity)
        for slot_data in data:
            item_id = slot_data.get("item_id")
            if not item_id:
                continue
            try:
                item = item_lookup(item_id)
            except (KeyError, ItemNotFoundError):
                # 物品不存在时跳过（数据完整性问题已在 persistence 层警告）
                continue
            count = slot_data.get("count", 1)
            instance_state = slot_data.get("instance_state")
            # 使用内部 _add_to_slot 直接添加，绕过容量检查（持久化数据已占用槽位）
            inventory._force_add_slot(item, count, instance_state)
        return inventory


    def to_inventory_data(self) -> list[dict]:
        """转换为 Player.inventory 列表格式，用于持久化"""
        return [slot.to_dict() for slot in self._slots]


    # ========== 内部方法 ==========

    def _count_item(self, item_id: str) -> int:
        """统计指定 item_id 的总数量（只读）"""
        total = 0
        for slot in self._slots:
            if slot._item_id() == item_id:
                total += slot.count
        return total


    def _can_merge(self, slot: InventorySlot, item, instance_state, stack_size_max: int) -> bool:
        """判断槽位是否可以合并新物品"""
        # item_id 必须相同
        if slot._item_id() != _item_id(item):
            return False
        # instance_state 必须相同
        slot_state = slot.instance_state or {}
        new_state = instance_state or {}
        if slot_state != new_state:
            return False
        # 还有空间
        return slot.count < stack_size_max


    def _force_add_slot(self, item, count: int, instance_state: dict | None) -> None:
        """内部方法：强制添加槽位（用于从持久化数据恢复，绕过容量检查）"""
        self._slots.add_tail(InventorySlot(item, count, dict(instance_state) if instance_state else None))


    # ========== 兼容/辅助方法 ==========


    def __len__(self) -> int:
        return len(self._slots)


    def __iter__(self):
        return iter(self._slots)


    def is_empty(self) -> bool:
        return self._slots.is_empty()


    def clear(self) -> None:
        """清空背包（调试用）"""
        self._slots.clear()
