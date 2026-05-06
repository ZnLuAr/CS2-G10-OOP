"""
自实现的基础数据结构。

预期模块：
- doubly_linked_list.py   双向链表（用于 Inventory）
- stack.py                栈（用于操作撤销 / 历史回溯）
- queue.py                队列（用于挂单处理 / 通知）
- tree.py                 通用树（用于物品分类层级）
- bst.py                  二叉搜索树（用于按价格索引挂单）
- hash_map.py             哈希表（用于 ID 查找 / 关键字索引）
- catalog_tree.py         物品分类目录树（CatalogTree + CatalogNode）
"""

from __future__ import annotations

from .catalog_tree import CatalogNode, CatalogTree
from .doubly_linked_list import DoublyLinkedList
from .price_bst import PriceBST
from .queue import Queue

__all__ = [
    "CatalogNode",
    "CatalogTree",
    "DoublyLinkedList",
    "PriceBST",
    "Queue",
]
