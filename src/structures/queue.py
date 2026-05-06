"""自实现 FIFO 队列。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class _QueueNode:
    value: Any
    next: "_QueueNode | None" = None


class Queue:
    def __init__(self) -> None:
        self._head: _QueueNode | None = None
        self._tail: _QueueNode | None = None
        self._size = 0

    def enqueue(self, value: Any) -> None:
        node = _QueueNode(value)
        if self._tail is None:
            self._head = node
            self._tail = node
        else:
            self._tail.next = node
            self._tail = node
        self._size += 1

    def dequeue(self) -> Any:
        if self._head is None:
            raise IndexError("dequeue from empty queue")
        node = self._head
        self._head = node.next
        if self._head is None:
            self._tail = None
        self._size -= 1
        return node.value

    def is_empty(self) -> bool:
        return self._size == 0

    def __len__(self) -> int:
        return self._size
