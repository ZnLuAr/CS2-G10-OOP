from src.structures.doubly_linked_list import DoublyLinkedList
from src.errors.backpack_errors import InventoryFullError

class InventorySlot:
    """背包槽位，存物品引用 + 数量 + 实例状态"""
    def __init__(self, item, count=1, instance_state=None):
        self.item = item            # Item 对象引用
        self.count = count
        self.instance_state = instance_state or {}

    def to_dict(self):
        """序列化为 Player.inventory 数组元素"""
        result = {"item_id": self.item.item_id, "count": self.count}
        if self.instance_state:
            result["instance_state"] = self.instance_state
        return result


class Backpack:
    MAX_CAPACITY = 50
    RARITY_ORDER = ["common", "uncommon", "rare", "epic", "legendary"]

    def __init__(self):
        self.slots = DoublyLinkedList()

    # 物品添加
    def add_item(self, item, count=1, instance_state=None):
        """
        向背包添加物品。
        - 可堆叠：先尝试合入既有同 item_id 的槽位，溢出部分新建槽位
        - 不可堆叠：直接新建槽位
        - 容量满且无法合堆叠时抛 InventoryFullError
        """
        remaining = count

        # 可堆叠物品：尝试合入既有槽位
        if hasattr(item, 'stackable') and item.stackable:
            cur = self.slots.head
            while cur and remaining > 0:
                slot = cur.data
                if slot.item.item_id == item.item_id:
                    max_stack = getattr(item, 'stack_size_max', 99)
                    space = max_stack - slot.count
                    if space > 0:
                        add_amount = min(space, remaining)
                        slot.count += add_amount
                        remaining -= add_amount
                cur = cur.next

        # 剩余数量新建槽位
        while remaining > 0:
            if self.slots.size >= self.MAX_CAPACITY:
                raise InventoryFullError(f"背包已满（{self.MAX_CAPACITY}格），无法继续添加")
            max_stack = getattr(item, 'stack_size_max', 1) if hasattr(item, 'stackable') and item.stackable else 1
            add_amount = min(max_stack, remaining)
            self.slots.add_tail(InventorySlot(item, add_amount, instance_state))
            remaining -= add_amount

    # 移除物品
    def remove_item(self, item_id, count=1):
        """
        按 item_id 移除指定数量的物品。
        - 数量不足时抛 ValueError
        - 物品不存在时抛 ValueError
        """
        remaining = count
        cur = self.slots.head
        while cur and remaining > 0:
            slot = cur.data
            if slot.item.item_id == item_id:
                if slot.count > remaining:
                    slot.count -= remaining
                    remaining = 0
                else:
                    remaining -= slot.count
                    next_node = cur.next
                    self.slots.remove_node(cur)
                    cur = next_node
                    continue
            cur = cur.next

        if remaining > 0:
            raise ValueError(f"背包中 {item_id} 数量不足，缺少 {remaining} 个")

    def remove_slot_node(self, node):
        """直接删除已知节点（O(1)，供市场挂单等外部调用）"""
        self.slots.remove_node(node)

    # 查找
    def find_item(self, item_id):
        """按 item_id 查找第一个匹配的节点，返回 Node 或 None"""
        return self.slots.find(lambda slot: slot.item.item_id == item_id)

    def find_by_predicate(self, predicate):
        """按自定义条件查找节点"""
        return self.slots.find(predicate)

    # 查看背包
    def show(self):
        """打印背包内容"""
        print("\n===== BACKPACK =====")
        if self.slots.is_empty():
            print("Empty")
        else:
            for i, slot in enumerate(self.slots, 1):
                item = slot.item
                print(f"{i}. {item.name} | {item.rarity} | x{slot.count}")
        print("====================\n")

    def to_display_list(self):
        """返回展示用的列表（不改变内部顺序）"""
        return list(self.slots)

    # 排序展示
    def sort_by_rarity(self, reverse=False):
        """
        返回按稀有度排序后的槽位列表。
        不改变背包内部存储顺序。
        """
        lst = list(self.slots)
        if len(lst) <= 1:
            return lst
        lst.sort(
            key=lambda slot: self.RARITY_ORDER.index(slot.item.rarity)
            if slot.item.rarity in self.RARITY_ORDER else 99,
            reverse=reverse
        )
        return lst

    # 辅助方法
    def is_empty(self):
        return self.slots.is_empty()

    def __len__(self):
        return self.slots.size

    def __iter__(self):
        return iter(self.slots)

    def clear(self):
        self.slots.clear()

    def to_json(self):
        """序列化为 JSON 兼容的列表"""
        return [slot.to_dict() for slot in self.slots]