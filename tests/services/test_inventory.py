"""Inventory 服务测试

覆盖槽位管理、堆叠逻辑、移除原子性、排序、序列化/反序列化等边界场景。
"""

from __future__ import annotations

import pytest

from src.errors import InvalidInputError, InventoryFullError, ItemNotFoundError
from src.models import Item
from src.services.inventory import Inventory, InventorySlot


# ========== Fixtures ==========

class FakeItem:
    """测试用的假物品对象"""

    def __init__(
        self,
        item_id: str,
        name: str = "",
        rarity: str = "common",
        stackable: bool = False,
        stack_size_max: int = 1
    ):
        self.item_id = item_id
        self.name = name or f"Item-{item_id}"
        self.rarity = rarity
        self.stackable = stackable
        self.stack_size_max = stack_size_max


def make_stackable(item_id: str, max_stack: int = 10) -> FakeItem:
    """创建可堆叠物品"""
    return FakeItem(item_id, stackable=True, stack_size_max=max_stack)


def make_unstackable(item_id: str) -> FakeItem:
    """创建不可堆叠物品"""
    return FakeItem(item_id, stackable=False, stack_size_max=1)


@pytest.fixture
def inventory():
    """默认容量背包"""
    return Inventory(owner_id="p_001")


@pytest.fixture
def small_inventory():
    """小容量背包（方便测试满容量场景）"""
    return Inventory(owner_id="p_002", capacity=3)


# ========== 基本添加/查询测试 ==========

class TestAddAndQuery:
    """测试添加物品和基础查询"""

    def test_add_single_unstackable(self, inventory):
        """添加单个不可堆叠物品，占用一个槽位"""
        item = make_unstackable("i_001")
        inventory.add(item, count=1)

        assert inventory.used() == 1
        slot = inventory.find("i_001")
        assert slot is not None
        assert slot.count == 1

    def test_add_multiple_unstackable(self, inventory):
        """添加多个不可堆叠物品，每个占用独立槽位"""
        inventory.add(make_unstackable("i_001"), count=1)
        inventory.add(make_unstackable("i_002"), count=1)
        inventory.add(make_unstackable("i_003"), count=1)

        assert inventory.used() == 3
        assert inventory.find("i_001").count == 1
        assert inventory.find("i_002").count == 1
        assert inventory.find("i_003").count == 1

    def test_add_stackable_merges_existing_slot(self, inventory):
        """添加可堆叠物品，合并到已有槽位"""
        item = make_stackable("i_001", max_stack=10)
        inventory.add(item, count=3)
        inventory.add(item, count=4)

        # 应该只占用 1 个槽位，count = 7
        assert inventory.used() == 1
        assert inventory.find("i_001").count == 7

    def test_add_stackable_overflows_to_new_slot(self, inventory):
        """可堆叠物品超过上限时，溢出部分新建槽位"""
        item = make_stackable("i_001", max_stack=5)
        inventory.add(item, count=7)

        # 7 > 5，应该占用 2 个槽位（5 + 2）
        assert inventory.used() == 2

    def test_add_stackable_multiple_slots(self, inventory):
        """大量可堆叠物品填充多个槽位"""
        item = make_stackable("i_001", max_stack=5)
        inventory.add(item, count=12)

        # 12 = 5 + 5 + 2，应该占用 3 个槽位
        assert inventory.used() == 3


    def test_real_item_object_stackable_merges_existing_slot(self, inventory):
        data = {
            "item_id": "i_potion",
            "name": "真实药水",
            "category": "consumable.potion",
            "rarity": "common",
            "base_value": 10,
            "stats": {"effect": "heal", "power": 20, "duration": 0, "stack_size_max": 10, "count": 1},
        }
        item = Item.from_dict(data)

        inventory.add(item, count=3)
        inventory.add(item, count=4)

        assert item.stackable is True
        assert inventory.used() == 1
        assert inventory.find("i_potion").count == 7

    def test_real_weapon_object_is_not_stackable(self, inventory):
        data = {
            "item_id": "i_sword",
            "name": "真实剑",
            "category": "weapon.sword",
            "rarity": "common",
            "base_value": 100,
            "stats": {"attack": 10, "attack_speed": 1.0, "durability_max": 50},
        }
        item = Item.from_dict(data)

        inventory.add(item, count=2)

        assert item.stackable is False
        assert inventory.used() == 2
        assert [slot.count for slot in inventory.slots()] == [1, 1]

    def test_add_count_zero_raises(self, inventory):
        """count=0 应该抛 InvalidInputError"""
        item = make_stackable("i_001")
        with pytest.raises(InvalidInputError) as exc:
            inventory.add(item, count=0)
        assert exc.value.context["field"] == "count"
        assert exc.value.context["value"] == 0

    def test_add_count_negative_raises(self, inventory):
        """count=-1 应该抛 InvalidInputError"""
        item = make_stackable("i_001")
        with pytest.raises(InvalidInputError) as exc:
            inventory.add(item, count=-1)
        assert exc.value.context["value"] == -1


# ========== 满容量测试 ==========

class TestCapacity:
    """测试容量边界"""

    def test_inventory_full_error(self, small_inventory):
        """背包满时继续添加应抛 InventoryFullError"""
        # capacity = 3，添加 3 个不可堆叠物品填满
        small_inventory.add(make_unstackable("i_001"), count=1)
        small_inventory.add(make_unstackable("i_002"), count=1)
        small_inventory.add(make_unstackable("i_003"), count=1)

        assert small_inventory.is_full()

        # 第 4 个应该失败
        with pytest.raises(InventoryFullError) as exc:
            small_inventory.add(make_unstackable("i_004"), count=1)
        assert exc.value.context["capacity"] == 3

    def test_stackable_can_still_add_when_full(self, small_inventory):
        """槽位满但可堆叠物品可以合堆叠时，应该成功"""
        item = make_stackable("i_001", max_stack=10)
        # 先添加占满槽位
        small_inventory.add(item, count=3)  # 每个槽位 1 个（不可堆叠时）

        # 但 i_001 是可堆叠的，且当前槽位还有空间
        # 实际上上面创建的是 3 个槽位各 1 个，但 stack_size_max=10
        # 再次添加应该能合入
        small_inventory.add(item, count=5)
        assert small_inventory.find("i_001").count == 8


# ========== 移除测试（重点是原子性） ==========

class TestRemove:
    """测试移除物品，重点是原子性"""

    def test_remove_part_of_stack(self, inventory):
        """移除部分堆叠"""
        item = make_stackable("i_001", max_stack=10)
        inventory.add(item, count=8)
        inventory.remove("i_001", count=3)

        assert inventory.find("i_001").count == 5

    def test_remove_entire_slot(self, inventory):
        """移除整个槽位"""
        inventory.add(make_stackable("i_001", max_stack=5), count=3)
        inventory.remove("i_001", count=3)

        assert inventory.find("i_001") is None
        assert inventory.used() == 0

    def test_remove_nonexistent_raises(self, inventory):
        """移除不存在的物品应抛 ItemNotFoundError"""
        with pytest.raises(ItemNotFoundError) as exc:
            inventory.remove("i_nonexistent", count=1)
        assert exc.value.context["item_id"] == "i_nonexistent"

    def test_remove_more_than_owned_does_not_mutate_inventory(self, inventory):
        """数量不足时移除，不应修改背包状态（原子性）"""
        # 这是 review 中强调的关键测试
        item = make_stackable("i_001", max_stack=10)
        inventory.add(item, count=2)

        with pytest.raises(InvalidInputError) as exc:
            inventory.remove("i_001", count=5)

        # 验证背包未被修改
        assert inventory.find("i_001").count == 2
        assert inventory.used() == 1

    def test_remove_count_zero_raises(self, inventory):
        """remove count=0 应抛 InvalidInputError"""
        inventory.add(make_stackable("i_001"), count=1)

        with pytest.raises(InvalidInputError) as exc:
            inventory.remove("i_001", count=0)

        # 验证背包未被修改
        assert inventory.find("i_001").count == 1

    def test_remove_count_negative_raises(self, inventory):
        """remove count=-1 应抛 InvalidInputError"""
        inventory.add(make_stackable("i_001"), count=1)

        with pytest.raises(InvalidInputError) as exc:
            inventory.remove("i_001", count=-1)

        # 验证背包未被修改
        assert inventory.find("i_001").count == 1

    def test_remove_across_multiple_slots(self, inventory):
        """从多个槽位中移除（分散存储时）"""
        item = make_stackable("i_001", max_stack=5)
        # 创建 3 个槽位：5 + 5 + 2 = 12
        inventory.add(item, count=12)
        assert inventory.used() == 3

        # 移除 7 个：槽位1被删除，槽位2剩 3 (5-2)，槽位3剩 2
        inventory.remove("i_001", count=7)

        # 验证剩余总数 = 5 (槽位2:3 + 槽位3:2)
        assert inventory.used() == 2  # 剩 2 个槽位
        total = sum(s.count for s in inventory.slots() if s._item_id() == "i_001")
        assert total == 5  # 12 - 7 = 5


# ========== 按状态精确移除测试 ==========

class TestRemoveByState:
    """测试按 instance_state 精确移除物品"""

    def test_remove_by_state_removes_exact_match(self, inventory):
        """精确匹配 item_id + state 的槽位"""
        item = make_stackable("i_001", max_stack=10)
        inventory.add(item, count=3, instance_state={"enchant": "fire"})
        inventory.add(item, count=2, instance_state={"enchant": "ice"})

        # 只移除 fire 状态的 1 个
        inventory.remove_by_state("i_001", {"enchant": "fire"}, count=1)

        # fire 槽位剩 2 个，ice 槽位仍为 2 个
        fire_slot = inventory.find_by_state("i_001", {"enchant": "fire"})
        ice_slot = inventory.find_by_state("i_001", {"enchant": "ice"})
        assert fire_slot.count == 2
        assert ice_slot.count == 2

    def test_remove_by_state_entire_slot(self, inventory):
        """精确移除整个槽位"""
        item = make_stackable("i_001", max_stack=10)
        inventory.add(item, count=3, instance_state={"enchant": "fire"})
        inventory.add(item, count=2, instance_state={"enchant": "ice"})

        # 移除全部 fire 状态物品
        inventory.remove_by_state("i_001", {"enchant": "fire"}, count=3)

        # fire 槽位被删除，ice 槽位保留
        assert inventory.find_by_state("i_001", {"enchant": "fire"}) is None
        assert inventory.find_by_state("i_001", {"enchant": "ice"}) is not None
        assert inventory.used() == 1

    def test_remove_by_state_not_found_raises(self, inventory):
        """找不到匹配 item_id + state 的槽位时抛 ItemNotFoundError"""
        item = make_stackable("i_001", max_stack=10)
        inventory.add(item, count=3, instance_state={"enchant": "fire"})

        with pytest.raises(ItemNotFoundError):
            inventory.remove_by_state("i_001", {"enchant": "nonexistent"}, count=1)

    def test_remove_by_state_insufficient_count_raises(self, inventory):
        """数量不足时不应修改背包状态"""
        item = make_stackable("i_001", max_stack=10)
        inventory.add(item, count=2, instance_state={"enchant": "fire"})

        with pytest.raises(InvalidInputError):
            inventory.remove_by_state("i_001", {"enchant": "fire"}, count=5)

        # 背包未被修改
        slot = inventory.find_by_state("i_001", {"enchant": "fire"})
        assert slot.count == 2

    def test_remove_by_state_count_zero_raises(self, inventory):
        """count=0 应抛 InvalidInputError"""
        item = make_stackable("i_001", max_stack=10)
        inventory.add(item, count=2, instance_state={"enchant": "fire"})

        with pytest.raises(InvalidInputError):
            inventory.remove_by_state("i_001", {"enchant": "fire"}, count=0)

    def test_remove_by_state_none_state(self, inventory):
        """移除无 instance_state 的物品"""
        item = make_stackable("i_001", max_stack=10)
        inventory.add(item, count=3)  # 无 instance_state
        inventory.add(item, count=2, instance_state={"enchant": "fire"})

        # 用 None 移除无状态的物品
        inventory.remove_by_state("i_001", None, count=2)

        no_state_slot = inventory.find_by_state("i_001", None)
        fire_slot = inventory.find_by_state("i_001", {"enchant": "fire"})
        assert no_state_slot.count == 1
        assert fire_slot.count == 2


# ========== 排序测试 ==========

class TestSortedView:
    """测试排序展示（不改变内部顺序）"""

    def test_sorted_view_by_rarity(self, inventory):
        """按稀有度排序"""
        inventory.add(FakeItem("i_001", rarity="common"), count=1)
        inventory.add(FakeItem("i_002", rarity="epic"), count=1)
        inventory.add(FakeItem("i_003", rarity="rare"), count=1)

        sorted_slots = inventory.sorted_view(key="rarity")
        rarities = [slot.item.rarity for slot in sorted_slots]

        # common (0) < uncommon (1) < rare (2) < epic (3) < legendary (4)
        assert rarities == ["common", "rare", "epic"]

    def test_sorted_view_does_not_mutate_original_order(self, inventory):
        """排序不应改变原始链表顺序"""
        inventory.add(FakeItem("i_001", rarity="epic"), count=1)   # 槽位 1
        inventory.add(FakeItem("i_002", rarity="common"), count=1)  # 槽位 2
        inventory.add(FakeItem("i_003", rarity="rare"), count=1)    # 槽位 3

        # 执行排序（但不保存结果）
        _ = inventory.sorted_view(key="rarity")

        # 原始顺序应该保持不变（epic -> common -> rare）
        original_order = [slot.item.rarity for slot in inventory.slots()]
        assert original_order == ["epic", "common", "rare"]

    def test_sorted_view_unknown_rarity(self, inventory):
        """未知稀有度排最后"""
        inventory.add(FakeItem("i_001", rarity="unknown"), count=1)
        inventory.add(FakeItem("i_002", rarity="common"), count=1)

        sorted_slots = inventory.sorted_view(key="rarity")
        rarities = [slot.item.rarity for slot in sorted_slots]

        assert rarities == ["common", "unknown"]

    def test_sorted_view_invalid_key_raises(self, inventory):
        """不支持的排序键应抛 InvalidInputError"""
        with pytest.raises(InvalidInputError) as exc:
            inventory.sorted_view(key="price")
        assert exc.value.context["field"] == "key"


# ========== 序列化/反序列化测试 ==========

class TestSerialization:
    """测试与 Player.inventory 的双向转换"""

    def test_to_inventory_data_format(self, inventory):
        """to_inventory_data 返回 list[dict] 格式"""
        # 使用可堆叠物品添加 3 个到同一槽位
        inventory.add(FakeItem("i_001", rarity="common", stackable=True, stack_size_max=10), count=3)
        inventory.add(FakeItem("i_002", rarity="rare", stackable=False), count=1, instance_state={"enchant": "fire"})

        data = inventory.to_inventory_data()

        assert isinstance(data, list)
        assert len(data) == 2
        # 查找对应 item_id 的数据
        item1_data = next(d for d in data if d["item_id"] == "i_001")
        item2_data = next(d for d in data if d["item_id"] == "i_002")
        assert item1_data["count"] == 3
        assert item2_data["count"] == 1
        assert item2_data["instance_state"] == {"enchant": "fire"}

    def test_from_inventory_data_restores_inventory(self):
        """从 Player.inventory 数据恢复"""
        # 模拟持久化数据
        saved_data = [
            {"item_id": "i_001", "count": 5},
            {"item_id": "i_002", "count": 2, "instance_state": {"durability": 80}},
        ]

        # 模拟 repo.items 查找
        items_db = {
            "i_001": FakeItem("i_001", rarity="common"),
            "i_002": FakeItem("i_002", rarity="rare"),
        }

        inv = Inventory.from_inventory_data(
            owner_id="p_003",
            data=saved_data,
            item_lookup=lambda item_id: items_db[item_id]
        )

        assert inv.owner_id == "p_003"
        assert inv.used() == 2
        assert inv.find("i_001").count == 5
        assert inv.find("i_002").count == 2
        assert inv.find("i_002").instance_state == {"durability": 80}

    def test_round_trip_preserves_data(self):
        """序列化 -> 反序列化 保持数据一致"""
        # 构造原始背包
        original = Inventory(owner_id="p_004")
        original.add(FakeItem("i_001", rarity="common"), count=3)
        original.add(
            FakeItem("i_002", rarity="epic", stackable=True, stack_size_max=5),
            count=7,
            instance_state={"enchant": "ice"}
        )

        # 序列化
        data = original.to_inventory_data()

        # 反序列化
        items_db = {
            "i_001": FakeItem("i_001", rarity="common"),
            "i_002": FakeItem("i_002", rarity="epic", stackable=True, stack_size_max=5),
        }
        restored = Inventory.from_inventory_data(
            owner_id="p_004",
            data=data,
            item_lookup=lambda item_id: items_db[item_id]
        )

        # 验证一致性
        assert restored.owner_id == original.owner_id
        assert restored.to_inventory_data() == data

    def test_from_inventory_data_skips_missing_items(self):
        """反序列化时物品不存在则跳过（数据完整性问题已在 persistence 层处理）"""
        saved_data = [
            {"item_id": "i_exists", "count": 3},
            {"item_id": "i_missing", "count": 2},
        ]

        items_db = {"i_exists": FakeItem("i_exists")}

        inv = Inventory.from_inventory_data(
            owner_id="p_005",
            data=saved_data,
            item_lookup=lambda item_id: items_db[item_id]  # 会抛 KeyError
        )

        assert inv.find("i_exists") is not None
        assert inv.find("i_missing") is None


# ========== instance_state 测试 ==========

class TestInstanceState:
    """测试 instance_state 的正确处理（复制、比较）"""

    def test_instance_state_is_copied_not_shared(self):
        """添加时复制 instance_state，避免引用共享"""
        shared_state = {"enchant": "fire", "level": 3}
        item = make_stackable("i_001", max_stack=5)

        inv = Inventory(owner_id="p_001")
        inv.add(item, count=1, instance_state=shared_state)

        # 修改原始 dict
        shared_state["level"] = 99

        # 槽位中的状态不应受影响
        slot = inv.find("i_001")
        assert slot.instance_state["level"] == 3

    def test_merge_considers_instance_state(self):
        """只有 instance_state 相同才可合并"""
        item = make_stackable("i_001", max_stack=10)

        inv = Inventory(owner_id="p_001")
        inv.add(item, count=3, instance_state={"enchant": "fire"})
        # 不同 state，应该新建槽位
        inv.add(item, count=2, instance_state={"enchant": "ice"})

        # 应该占用 2 个槽位
        assert inv.used() == 2

        # 相同 state 可以再合并
        inv.add(item, count=2, instance_state={"enchant": "fire"})
        # fire 槽位变成 3+2=5，ice 槽位还是 2
        slots = [s for s in inv.slots()]
        assert len(slots) == 2

    def test_slot_to_dict_copies_instance_state(self):
        """to_dict 时复制 instance_state"""
        slot = InventorySlot(
            make_unstackable("i_001"),
            count=1,
            instance_state={"a": 1}
        )

        data1 = slot.to_dict()
        data2 = slot.to_dict()

        # 多次调用返回的 state 应该是独立副本
        data1["instance_state"]["a"] = 999
        assert data2["instance_state"]["a"] == 1


# ========== Dict 物品支持测试 ==========

class TestDictItemSupport:
    """测试 Inventory 支持 dict 格式的物品（用于早期阶段 persistence 层未完全对接时）"""

    def test_add_dict_item(self, inventory):
        """可以添加 dict 格式的物品"""
        item_dict = {
            "item_id": "i_001",
            "name": "Test Item",
            "rarity": "common",
            "stackable": True,
            "stack_size_max": 5
        }
        inventory.add(item_dict, count=3)

        assert inventory.find("i_001").count == 3

    def test_mixed_object_and_dict(self, inventory):
        """可以在同一背包中混合对象和 dict 物品"""
        obj_item = FakeItem("i_001", stackable=True, stack_size_max=10)
        dict_item = {
            "item_id": "i_002",
            "name": "Dict Item",
            "rarity": "rare",
            "stackable": False,
            "stack_size_max": 1
        }

        inventory.add(obj_item, count=2)
        inventory.add(dict_item, count=1)

        assert inventory.used() == 2
        assert inventory.find("i_001") is not None
        assert inventory.find("i_002") is not None

    def test_missing_dict_item_id_is_not_silently_serialized(self):
        """dict 物品缺少 item_id 时不应静默序列化为 None"""
        slot = InventorySlot({"name": "Broken Item"}, count=1)

        with pytest.raises(KeyError):
            slot.to_dict()

    def test_missing_object_item_id_is_not_silently_serialized(self):
        """对象物品缺少 item_id 时不应静默序列化为 None"""
        class BrokenItem:
            name = "Broken Item"

        slot = InventorySlot(BrokenItem(), count=1)

        with pytest.raises(AttributeError):
            slot.to_dict()

    def test_stack_size_max_zero_raises(self, inventory):
        """stack_size_max = 0 时应抛 InvalidInputError"""
        item = {"item_id": "i_zero", "name": "Zero Stack", "stackable": True, "stack_size_max": 0}

        with pytest.raises(InvalidInputError) as exc:
            inventory.add(item, count=1)

        assert exc.value.context["field"] == "stack_size_max"
        assert exc.value.context["value"] == 0
        assert inventory.find("i_zero") is None

    def test_stack_size_max_negative_raises(self, inventory):
        """stack_size_max < 0 时应抛 InvalidInputError"""
        item = {"item_id": "i_neg", "name": "Negative Stack", "stackable": True, "stack_size_max": -1}

        with pytest.raises(InvalidInputError) as exc:
            inventory.add(item, count=1)

        assert exc.value.context["field"] == "stack_size_max"
        assert exc.value.context["value"] == -1
        assert inventory.find("i_neg") is None

    def test_stack_size_max_non_int_raises(self, inventory):
        """stack_size_max 非 int 时应抛 InvalidInputError"""
        item = {"item_id": "i_str", "name": "String Stack", "stackable": True, "stack_size_max": "5"}

        with pytest.raises(InvalidInputError) as exc:
            inventory.add(item, count=1)

        assert exc.value.context["field"] == "stack_size_max"
        assert exc.value.context["value"] == "5"
        assert inventory.find("i_str") is None
