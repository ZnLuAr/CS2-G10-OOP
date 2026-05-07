import pytest

from src.structures.hash_map import HashMap, hash_map


# ============================================================================
# HashMap 新 API 测试
# ============================================================================

class TestHashMap:
    def test_put_and_get(self):
        hm = HashMap()
        hm.put("k1", "v1")
        assert hm.get("k1") == "v1"

    def test_get_nonexistent_returns_default(self):
        hm = HashMap()
        assert hm.get("missing") is None
        assert hm.get("missing", "default") == "default"

    def test_put_updates_existing_key(self):
        hm = HashMap()
        hm.put("k1", "v1")
        hm.put("k1", "v2")
        assert hm.get("k1") == "v2"

    def test_remove_existing_key(self):
        hm = HashMap()
        hm.put("k1", "v1")
        assert hm.remove("k1") is True
        assert hm.get("k1") is None

    def test_remove_nonexistent_key(self):
        hm = HashMap()
        assert hm.remove("missing") is False

    def test_pop_existing_key(self):
        hm = HashMap()
        hm.put("k1", "v1")
        assert hm.pop("k1") == "v1"
        assert hm.get("k1") is None

    def test_pop_nonexistent_key(self):
        hm = HashMap()
        assert hm.pop("missing") is None
        assert hm.pop("missing", "default") == "default"

    def test_clear(self):
        hm = HashMap()
        hm.put("k1", "v1")
        hm.put("k2", "v2")
        hm.clear()
        assert len(hm) == 0
        assert hm.get("k1") is None

    def test_keys(self):
        hm = HashMap()
        hm.put("k1", "v1")
        hm.put("k2", "v2")
        keys = hm.keys()
        assert set(keys) == {"k1", "k2"}

    def test_values(self):
        hm = HashMap()
        hm.put("k1", "v1")
        hm.put("k2", "v2")
        values = hm.values()
        assert set(values) == {"v1", "v2"}

    def test_items(self):
        hm = HashMap()
        hm.put("k1", "v1")
        hm.put("k2", "v2")
        items = hm.items()
        assert set(items) == {("k1", "v1"), ("k2", "v2")}

    def test_to_dict(self):
        hm = HashMap()
        hm.put("k1", "v1")
        hm.put("k2", "v2")
        d = hm.to_dict()
        assert d == {"k1": "v1", "k2": "v2"}

    def test_setitem_getitem(self):
        hm = HashMap()
        hm["k1"] = "v1"
        assert hm["k1"] == "v1"

    def test_getitem_missing_raises_keyerror(self):
        hm = HashMap()
        with pytest.raises(KeyError):
            _ = hm["missing"]

    def test_delitem(self):
        hm = HashMap()
        hm["k1"] = "v1"
        del hm["k1"]
        assert hm.get("k1") is None

    def test_delitem_missing_raises_keyerror(self):
        hm = HashMap()
        with pytest.raises(KeyError):
            del hm["missing"]

    def test_contains(self):
        hm = HashMap()
        hm["k1"] = "v1"
        assert "k1" in hm
        assert "missing" not in hm

    def test_len(self):
        hm = HashMap()
        assert len(hm) == 0
        hm["k1"] = "v1"
        assert len(hm) == 1
        hm["k2"] = "v2"
        assert len(hm) == 2
        del hm["k1"]
        assert len(hm) == 1

    def test_iter(self):
        hm = HashMap()
        hm["k1"] = "v1"
        hm["k2"] = "v2"
        keys = list(hm)
        assert set(keys) == {"k1", "k2"}

    def test_resize_on_load_factor(self):
        hm = HashMap(capacity=4)
        for i in range(10):
            hm[f"k{i}"] = f"v{i}"
        # 应该触发扩容，所有键仍可访问
        for i in range(10):
            assert hm[f"k{i}"] == f"v{i}"

    def test_invalid_capacity_raises(self):
        with pytest.raises(ValueError):
            HashMap(capacity=0)
        with pytest.raises(ValueError):
            HashMap(capacity=-1)


# ============================================================================
# 兼容旧 hash_map API 测试
# ============================================================================

class TestLegacyHashMap:
    def test_put_and_get_username(self):
        mapping = hash_map()
        mapping.put("p_001", "alice")
        assert mapping.get_username("p_001") == "alice"

    def test_put_updates_existing_value(self):
        mapping = hash_map()
        mapping.put("p_001", "alice")
        mapping.put("p_001", "alice_new")
        assert mapping.get_username("p_001") == "alice_new"

    def test_remove_deletes_existing_key(self):
        mapping = hash_map()
        mapping.put("p_001", "alice")
        assert mapping.remove("p_001") is True
        assert mapping.get_username("p_001") is None

    def test_remove_missing_key_returns_false(self):
        mapping = hash_map()
        assert mapping.remove("missing") is False
