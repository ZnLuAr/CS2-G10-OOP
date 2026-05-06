from __future__ import annotations

import pytest

from src.structures import Queue


def test_queue_fifo_order():
    queue = Queue()
    queue.enqueue("first")
    queue.enqueue("second")
    queue.enqueue("third")

    assert len(queue) == 3
    assert queue.dequeue() == "first"
    assert queue.dequeue() == "second"
    assert queue.dequeue() == "third"
    assert queue.is_empty()


def test_empty_dequeue_raises():
    queue = Queue()

    with pytest.raises(IndexError):
        queue.dequeue()


def test_enqueue_after_emptying_queue():
    queue = Queue()
    queue.enqueue("a")
    assert queue.dequeue() == "a"
    queue.enqueue("b")
    assert queue.dequeue() == "b"
