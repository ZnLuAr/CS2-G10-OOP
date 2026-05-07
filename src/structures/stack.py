"""自实现栈（LIFO）

使用链表节点实现，避免简单包装 Python list。
支持可选容量上限，超限时淘汰最旧元素（FIFO 淘汰）。
"""

from __future__ import annotations
from typing import Any, Optional

__all__ = ["Stack"]


class _StackNode:
    """栈节点（单向链表）"""
    def __init__(self, value: Any, next_node: Optional[_StackNode] = None):
        self.value = value
        self.next = next_node


class Stack:
    """自实现栈（LIFO）

    支持可选容量上限，超限时淘汰最旧元素（FIFO 淘汰）。
    """

    def __init__(self, max_size: Optional[int] = None):
        if max_size is not None and max_size <= 0:
            raise ValueError("max_size must be positive")
        self._top: Optional[_StackNode] = None
        self._bottom: Optional[_StackNode] = None
        self._size = 0
        self._max_size = max_size

    def push(self, value: Any) -> None:
        """压栈，超限时淘汰最旧元素"""
        new_node = _StackNode(value, self._top)
        self._top = new_node

        if self._size == 0:
            self._bottom = new_node

        self._size += 1

        # 超限时淘汰最旧元素（FIFO 淘汰）
        if self._max_size is not None and self._size > self._max_size:
            self._remove_bottom()

    def pop(self) -> Optional[Any]:
        """弹栈，空栈返回 None"""
        if self._top is None:
            return None

        value = self._top.value
        self._top = self._top.next
        self._size -= 1

        if self._size == 0:
            self._bottom = None

        return value

    def peek(self) -> Optional[Any]:
        """查看栈顶元素但不弹出"""
        return self._top.value if self._top else None

    def is_empty(self) -> bool:
        """检查栈是否为空"""
        return self._size == 0

    def clear(self) -> None:
        """清空栈"""
        self._top = None
        self._bottom = None
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def __bool__(self) -> bool:
        return self._size > 0

    def _remove_bottom(self) -> None:
        """移除栈底元素（用于容量淘汰）"""
        if self._size <= 1:
            self._top = None
            self._bottom = None
            self._size = 0
            return

        # 遍历到倒数第二个节点
        current = self._top
        while current and current.next and current.next != self._bottom:
            current = current.next

        if current:
            current.next = None
            self._bottom = current

        self._size -= 1
