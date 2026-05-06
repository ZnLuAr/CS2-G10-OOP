"""CatalogTree - 物品分类目录树结构

实现 docs/data-design.md §7 / §8.1 中 category 路径与 catalog.json 树的一一对应。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

__all__ = ["CatalogNode", "CatalogTree"]




@dataclass
class CatalogNode:
    """分类目录节点

    字段：
        key: 节点标识（如 "weapon", "sword"）
        label: 显示名称（如 "武器", "剑"）
        children: 子节点列表
    """

    key: str
    label: str
    children: list["CatalogNode"] = field(default_factory=list)

    @property
    def is_leaf(self) -> bool:
        """是否为叶子节点（无子节点）"""
        return not self.children


    def find_child(self, key: str) -> "CatalogNode | None":
        """在当前节点的直接子节点中查找"""
        for child in self.children:
            if child.key == key:
                return child
        return None


    def to_dict(self) -> dict[str, Any]:
        """序列化为 catalog.json 节点格式"""
        return {
            "key": self.key,
            "label": self.label,
            "children": [child.to_dict() for child in self.children],
        }




class CatalogTree:
    """分类目录树

    提供从 catalog.json 构建、按 key/路径查找、叶子分类枚举等功能。
    """

    def __init__(self, root: CatalogNode) -> None:
        self.root = root


    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CatalogTree":
        """
        从 catalog.json 格式构造树

        Args:
            data: catalog.json 内容，含 "root" 键或直接是 root 节点

        Returns:
            CatalogTree 实例
        """
        root_data = data.get("root", data)
        root = cls._build_node(root_data)
        return cls(root)


    @classmethod
    def _build_node(cls, data: dict[str, Any]) -> CatalogNode:
        """递归构造 CatalogNode"""
        if not isinstance(data, dict):
            raise ValueError(f"CatalogNode data must be dict, got {type(data).__name__}")
        if "key" not in data or "label" not in data:
            raise ValueError(f"CatalogNode missing required fields: {data!r}")
        children_data = data.get("children", [])
        if not isinstance(children_data, list):
            raise ValueError(f"CatalogNode children must be list: {data!r}")
        if not all(isinstance(child, dict) for child in children_data):
            raise ValueError(f"CatalogNode children must contain only dicts: {data!r}")
        children = [cls._build_node(child) for child in children_data]
        return CatalogNode(
            key=data["key"],
            label=data["label"],
            children=children,
        )


    def find_node(self, key: str) -> CatalogNode | None:
        """按 key 搜索任意节点（深度优先）"""
        return self._find_node_recursive(self.root, key)


    def _find_node_recursive(self, node: CatalogNode, key: str) -> CatalogNode | None:
        """递归查找节点"""
        if node.key == key:
            return node
        for child in node.children:
            found = self._find_node_recursive(child, key)
            if found is not None:
                return found
        return None

    def find_by_path(self, path: str) -> CatalogNode | None:
        """
        按根到叶路径逐级匹配

        Args:
            path: 如 "weapon.sword"、"misc"

        Returns:
            匹配的节点，或 None
        """
        if not path:
            return None
        parts = path.split(".")
        current = self.root
        # 处理 root 本身（path="root" 或 path=""）
        if parts[0] == "root" and len(parts) == 1:
            return self.root
        # 跳过 root 前缀（如果存在）
        if parts[0] == "root":
            parts = parts[1:]
        # 逐级匹配
        for part in parts:
            child = current.find_child(part)
            if child is None:
                return None
            current = child
        return current


    def get_leaf_categories(self) -> list[str]:
        """
        获取所有叶子分类的完整路径

        Returns:
            形如 ["weapon.sword", "tool.axe", "misc"] 的列表
        """
        leaves: list[str] = []
        self._collect_leaves(self.root, [], leaves)
        return leaves


    def _collect_leaves(
        self, node: CatalogNode, path_parts: list[str], result: list[str]
    ) -> None:
        """递归收集叶子节点路径"""
        current_path = path_parts + [node.key]
        # 跳过 root 本身
        display_path = ".".join(current_path[1:]) if current_path[0] == "root" else ".".join(current_path)
        if node.is_leaf:
            result.append(display_path)
        else:
            for child in node.children:
                self._collect_leaves(child, current_path, result)


    def to_dict(self) -> dict[str, Any]:
        """序列化为 catalog.json 格式"""
        return {"root": self.root.to_dict()}
