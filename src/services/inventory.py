"""
Inventory 服务骨架

当前阶段只提供接口边界；真正实现待双向链表背包结构落地
"""

from __future__ import annotations

__all__ = ["Inventory"]




class Inventory:
    CAPACITY: int = 50

    def __init__(self, owner_id: str) -> None:
        self.owner_id = owner_id

    def slots(self):
        raise NotImplementedError("待双向链表背包结构落地后实现")

    def find(self, item_id: str):
        raise NotImplementedError("待双向链表背包结构落地后实现")

    def is_full(self) -> bool:
        raise NotImplementedError("待双向链表背包结构落地后实现")

    def used(self) -> int:
        raise NotImplementedError("待双向链表背包结构落地后实现")

    def sorted_view(self, key: str = "rarity"):
        raise NotImplementedError("待双向链表背包结构落地后实现")

    def add(self, item, count: int = 1, instance_state: dict | None = None) -> None:
        raise NotImplementedError("待双向链表背包结构落地后实现")

    def remove(self, item_id: str, count: int = 1) -> None:
        raise NotImplementedError("待双向链表背包结构落地后实现")
