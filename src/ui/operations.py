"""操作撤销栈相关定义（功能 ID 9）

将 Operation 和 OperationStack 独立出来，避免循环依赖。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from src.structures import Stack

__all__ = ["Operation", "OperationStack"]


@dataclass
class Operation:
    """可撤销的操作记录"""

    name: str                           # 操作名称（如"撤销挂单 l_001"）
    undo_fn: Callable[[], None]         # 撤销函数
    context: dict = field(default_factory=dict)  # 上下文数据（用于日志）


class OperationStack:
    """操作撤销栈，基于 Stack[Operation] 实现

    要求的数据结构演示点：
    - 后进先出（LIFO）语义：pop() 取最近 push 的操作
    - 容量上限与淘汰策略：FIFO 淘汰最旧操作
    """

    def __init__(self, max_size: int = 20) -> None:
        self._stack: Stack[Operation] = Stack(max_size=max_size)

    def push(self, op: Operation) -> None:
        """压栈，超限时淘汰最早的操作（FIFO 淘汰）"""
        self._stack.push(op)

    def pop(self) -> Operation | None:
        """弹栈，空栈返回 None"""
        return self._stack.pop()

    def can_undo(self) -> bool:
        """检查是否有可撤销的操作"""
        return not self._stack.is_empty()

    def __len__(self) -> int:
        return len(self._stack)
