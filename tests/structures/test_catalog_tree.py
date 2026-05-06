"""CatalogTree 测试"""

from __future__ import annotations

import pytest

from src.structures.catalog_tree import CatalogNode, CatalogTree


@pytest.fixture
def sample_catalog_dict():
    """样本 catalog.json 格式"""
    return {
        "root": {
            "key": "root",
            "label": "全部",
            "children": [
                {
                    "key": "weapon",
                    "label": "武器",
                    "children": [
                        {"key": "sword", "label": "剑", "children": []},
                        {"key": "bow", "label": "弓弩", "children": []},
                    ]
                },
                {
                    "key": "tool",
                    "label": "工具",
                    "children": [
                        {"key": "axe", "label": "斧", "children": []},
                    ]
                },
                {"key": "misc", "label": "杂项", "children": []},
            ]
        }
    }


class TestFromDict:
    """测试从字典构造"""

    def test_from_dict_with_root_wrapper(self, sample_catalog_dict):
        tree = CatalogTree.from_dict(sample_catalog_dict)
        assert tree.root.key == "root"
        assert tree.root.label == "全部"

    def test_from_dict_without_root_wrapper(self):
        data = {"key": "root", "label": "全部", "children": []}
        tree = CatalogTree.from_dict(data)
        assert tree.root.key == "root"


class TestFindNode:
    """测试按 key 查找节点"""

    def test_find_root(self, sample_catalog_dict):
        tree = CatalogTree.from_dict(sample_catalog_dict)
        node = tree.find_node("root")
        assert node is not None
        assert node.key == "root"

    def test_find_deep_node(self, sample_catalog_dict):
        tree = CatalogTree.from_dict(sample_catalog_dict)
        node = tree.find_node("sword")
        assert node is not None
        assert node.key == "sword"
        assert node.label == "剑"

    def test_find_nonexistent_returns_none(self, sample_catalog_dict):
        tree = CatalogTree.from_dict(sample_catalog_dict)
        node = tree.find_node("nonexistent")
        assert node is None


class TestFindByPath:
    """测试按路径查找"""

    def test_find_weapon_sword(self, sample_catalog_dict):
        tree = CatalogTree.from_dict(sample_catalog_dict)
        node = tree.find_by_path("weapon.sword")
        assert node is not None
        assert node.key == "sword"

    def test_find_tool_axe(self, sample_catalog_dict):
        tree = CatalogTree.from_dict(sample_catalog_dict)
        node = tree.find_by_path("tool.axe")
        assert node is not None
        assert node.key == "axe"

    def test_find_misc_direct(self, sample_catalog_dict):
        tree = CatalogTree.from_dict(sample_catalog_dict)
        node = tree.find_by_path("misc")
        assert node is not None
        assert node.key == "misc"
        assert node.is_leaf

    def test_find_with_root_prefix(self, sample_catalog_dict):
        tree = CatalogTree.from_dict(sample_catalog_dict)
        node = tree.find_by_path("root.weapon.sword")
        assert node is not None
        assert node.key == "sword"

    def test_find_nonexistent_path_returns_none(self, sample_catalog_dict):
        tree = CatalogTree.from_dict(sample_catalog_dict)
        node = tree.find_by_path("weapon.nonexistent")
        assert node is None

    def test_find_empty_path_returns_none(self, sample_catalog_dict):
        tree = CatalogTree.from_dict(sample_catalog_dict)
        node = tree.find_by_path("")
        assert node is None


class TestGetLeafCategories:
    """测试获取叶子分类"""

    def test_get_leaf_categories(self, sample_catalog_dict):
        tree = CatalogTree.from_dict(sample_catalog_dict)
        leaves = tree.get_leaf_categories()
        assert "weapon.sword" in leaves
        assert "weapon.bow" in leaves
        assert "tool.axe" in leaves
        assert "misc" in leaves
        assert "weapon" not in leaves  # 非叶子
        assert "root" not in leaves

    def test_all_leaves_are_leaf_nodes(self, sample_catalog_dict):
        tree = CatalogTree.from_dict(sample_catalog_dict)
        leaves = tree.get_leaf_categories()
        for leaf_path in leaves:
            node = tree.find_by_path(leaf_path)
            assert node is not None
            assert node.is_leaf


class TestToDict:
    """测试序列化"""

    def test_roundtrip(self, sample_catalog_dict):
        tree = CatalogTree.from_dict(sample_catalog_dict)
        result = tree.to_dict()
        assert result == sample_catalog_dict
        tree2 = CatalogTree.from_dict(result)
        assert tree2.root.key == tree.root.key
        assert len(tree2.root.children) == len(tree.root.children)


class TestMalformedData:
    """测试目录坏数据显式失败"""

    def test_missing_required_fields_raises(self):
        with pytest.raises(ValueError):
            CatalogTree.from_dict({"root": {"key": "root", "children": []}})

    def test_children_must_be_list(self):
        with pytest.raises(ValueError):
            CatalogTree.from_dict({"root": {"key": "root", "label": "全部", "children": {}}})

    def test_children_must_contain_dicts(self):
        with pytest.raises(ValueError):
            CatalogTree.from_dict({"root": {"key": "root", "label": "全部", "children": ["bad"]}})


class TestCatalogNode:
    """测试 CatalogNode 基本功能"""

    def test_is_leaf_true(self):
        node = CatalogNode("leaf", "叶子")
        assert node.is_leaf

    def test_is_leaf_false(self):
        child = CatalogNode("child", "子节点")
        node = CatalogNode("parent", "父节点", [child])
        assert not node.is_leaf

    def test_find_child_found(self):
        child = CatalogNode("child", "子节点")
        parent = CatalogNode("parent", "父节点", [child])
        found = parent.find_child("child")
        assert found is not None
        assert found.key == "child"

    def test_find_child_not_found(self):
        parent = CatalogNode("parent", "父节点", [])
        found = parent.find_child("nonexistent")
        assert found is None
