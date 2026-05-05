"""双向链表实现

用于 Inventory 等需要保持插入顺序且频繁增删的场景。
"""

from __future__ import annotations

__all__ = ["Node", "DoublyLinkedList"]




class Node:
    """链表节点"""
    def __init__(self, data):
        self.data = data
        self.prev: Node | None = None
        self.next: Node | None = None




class DoublyLinkedList:
    """双向链表，支持 O(1) 头尾插入和已知节点删除"""

    def __init__(self):
        self.head: Node | None = None
        self.tail: Node | None = None
        self.size: int = 0


    def add_tail(self, data) -> Node:
        """在尾部添加节点，返回创建的节点"""
        node = Node(data)
        if not self.tail:
            self.head = node
            self.tail = node
        else:
            self.tail.next = node
            node.prev = self.tail
            self.tail = node
        self.size += 1
        return node


    def remove_node(self, node: Node) -> None:
        """删除已知节点（O(1)）"""
        if node is None:
            raise ValueError("Cannot remove None node")


        if node.prev:
            node.prev.next = node.next
        else:
            self.head = node.next

        if node.next:
            node.next.prev = node.prev
        else:
            self.tail = node.prev

        self.size -= 1


    def to_list(self):
        """转换为 Python 列表"""
        res = []
        cur = self.head
        while cur:
            res.append(cur.data)
            cur = cur.next
        return res


    def clear(self) -> None:
        """清空链表"""
        self.head = None
        self.tail = None
        self.size = 0


    def is_empty(self) -> bool:
        """判断链表是否为空"""
        return self.size == 0


    def __iter__(self):
        """支持迭代，方便遍历"""
        cur = self.head
        while cur:
            yield cur.data
            cur = cur.next


    def __len__(self) -> int:
        """支持链表能够被 len() 调用"""
        return self.size


    def find(self, predicate) -> Node | None:
        """按条件查找节点，返回第一个匹配的 Node 或 None"""
        cur = self.head
        while cur:
            if predicate(cur.data):
                return cur
            cur = cur.next
        return None
