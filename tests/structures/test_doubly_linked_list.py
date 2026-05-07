"""DoublyLinkedList 单元测试"""

import pytest

from src.structures import DoublyLinkedList


class TestDoublyLinkedList:
    def test_add_tail_and_iteration(self):
        """尾部添加并按顺序迭代"""
        dll = DoublyLinkedList()
        dll.add_tail("first")
        dll.add_tail("second")
        dll.add_tail("third")

        items = list(dll)
        assert items == ["first", "second", "third"]

    def test_to_list(self):
        """to_list 返回快照列表"""
        dll = DoublyLinkedList()
        dll.add_tail("a")
        dll.add_tail("b")

        lst = dll.to_list()
        assert lst == ["a", "b"]

    def test_len(self):
        """len 返回节点数"""
        dll = DoublyLinkedList()
        assert len(dll) == 0
        dll.add_tail("a")
        assert len(dll) == 1
        dll.add_tail("b")
        assert len(dll) == 2

    def test_is_empty(self):
        """is_empty 正确反映状态"""
        dll = DoublyLinkedList()
        assert dll.is_empty()
        dll.add_tail("value")
        assert not dll.is_empty()

    def test_find_with_predicate(self):
        """find 按谓词查找节点"""
        dll = DoublyLinkedList()
        dll.add_tail({"id": 1, "name": "alice"})
        dll.add_tail({"id": 2, "name": "bob"})

        node = dll.find(lambda x: x["id"] == 2)
        assert node is not None
        assert node.data["name"] == "bob"

    def test_find_nonexistent_returns_none(self):
        """find 找不到返回 None"""
        dll = DoublyLinkedList()
        dll.add_tail("a")
        node = dll.find(lambda x: x == "missing")
        assert node is None

    def test_remove_node(self):
        """remove_node 删除已知节点"""
        dll = DoublyLinkedList()
        dll.add_tail("a")
        node_b = dll.add_tail("b")
        dll.add_tail("c")

        dll.remove_node(node_b)
        assert list(dll) == ["a", "c"]
        assert len(dll) == 2

    def test_remove_head_node(self):
        """删除头节点"""
        dll = DoublyLinkedList()
        node_a = dll.add_tail("a")
        dll.add_tail("b")

        dll.remove_node(node_a)
        assert list(dll) == ["b"]

    def test_remove_tail_node(self):
        """删除尾节点"""
        dll = DoublyLinkedList()
        dll.add_tail("a")
        node_b = dll.add_tail("b")

        dll.remove_node(node_b)
        assert list(dll) == ["a"]

    def test_remove_only_node(self):
        """删除唯一节点后链表为空"""
        dll = DoublyLinkedList()
        node = dll.add_tail("only")
        dll.remove_node(node)

        assert dll.is_empty()
        assert len(dll) == 0

    def test_clear(self):
        """clear 清空链表"""
        dll = DoublyLinkedList()
        dll.add_tail("a")
        dll.add_tail("b")
        dll.clear()

        assert dll.is_empty()
        assert len(dll) == 0
        assert list(dll) == []

    def test_iteration_order_preserved(self):
        """迭代顺序与添加顺序一致"""
        dll = DoublyLinkedList()
        for i in range(10):
            dll.add_tail(i)

        assert list(dll) == list(range(10))

    def test_add_tail_returns_node(self):
        """add_tail 返回新节点"""
        dll = DoublyLinkedList()
        node = dll.add_tail("value")

        assert node is not None
        assert node.data == "value"
