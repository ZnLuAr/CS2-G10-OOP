"""Stack 单元测试"""

import pytest

from src.structures import Stack


class TestStack:
    def test_lifo_semantics(self):
        """后进先出语义"""
        stack = Stack()
        stack.push("first")
        stack.push("second")
        stack.push("third")

        assert stack.pop() == "third"
        assert stack.pop() == "second"
        assert stack.pop() == "first"

    def test_empty_pop_returns_none(self):
        """空栈 pop 返回 None"""
        stack = Stack()
        assert stack.pop() is None

    def test_peek_does_not_remove(self):
        """peek 查看栈顶但不弹出"""
        stack = Stack()
        stack.push("value")
        assert stack.peek() == "value"
        assert stack.peek() == "value"
        assert len(stack) == 1

    def test_is_empty(self):
        """is_empty 正确反映栈状态"""
        stack = Stack()
        assert stack.is_empty()
        stack.push("value")
        assert not stack.is_empty()
        stack.pop()
        assert stack.is_empty()

    def test_len(self):
        """len 返回栈大小"""
        stack = Stack()
        assert len(stack) == 0
        stack.push("a")
        assert len(stack) == 1
        stack.push("b")
        assert len(stack) == 2
        stack.pop()
        assert len(stack) == 1

    def test_bool(self):
        """bool 转换"""
        stack = Stack()
        assert not stack
        stack.push("value")
        assert stack

    def test_clear(self):
        """clear 清空栈"""
        stack = Stack()
        stack.push("a")
        stack.push("b")
        stack.clear()
        assert len(stack) == 0
        assert stack.is_empty()
        assert stack.pop() is None

    def test_fifo_eviction_at_max_size(self):
        """超限时 FIFO 淘汰最旧元素"""
        stack = Stack(max_size=3)
        stack.push("first")
        stack.push("second")
        stack.push("third")
        stack.push("fourth")  # 应淘汰 first

        assert len(stack) == 3
        assert stack.pop() == "fourth"
        assert stack.pop() == "third"
        assert stack.pop() == "second"
        assert stack.pop() is None

    def test_max_size_one(self):
        """max_size=1 时只保留最新元素"""
        stack = Stack(max_size=1)
        stack.push("a")
        stack.push("b")
        assert len(stack) == 1
        assert stack.pop() == "b"

    def test_invalid_max_size_raises(self):
        """非法 max_size 抛异常"""
        with pytest.raises(ValueError):
            Stack(max_size=0)
        with pytest.raises(ValueError):
            Stack(max_size=-1)

    def test_none_max_size_unlimited(self):
        """max_size=None 时无容量限制"""
        stack = Stack(max_size=None)
        for i in range(100):
            stack.push(i)
        assert len(stack) == 100
