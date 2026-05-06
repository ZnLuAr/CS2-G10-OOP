from __future__ import annotations

import pytest

from src.errors import BusinessRuleError, InvalidInputError, ItemNotFoundError, SerializationError
from src.models import Item
from src.services.item_service import ItemService
from src.services.persistence import Persistence


@pytest.fixture
def service(tmp_path):
    persistence = Persistence(data_dir=str(tmp_path / "data"))
    persistence.seed_if_empty()
    repo = persistence.load_all()
    return ItemService(repo, persistence)


# ========== 查询测试 ==========

def test_get_by_id(service):
    iid = next(iter(service.repo.items))
    item = service.get_by_id(iid)
    assert isinstance(item, Item)
    assert item.item_id == iid


def test_get_by_id_missing_raises(service):
    with pytest.raises(ItemNotFoundError):
        service.get_by_id("i_999999")


def test_list_all(service):
    items = service.list_all()
    assert len(items) == len(service.repo.items)
    assert all(isinstance(item, Item) for item in items)


def test_list_all_by_category_prefix(service):
    items = service.list_all("weapon")
    assert all(item.category.startswith("weapon") for item in items)


def test_browse_catalog_root(service):
    root = service.browse_catalog("root")
    assert root.key == "root"


def test_browse_catalog_missing_raises(service):
    with pytest.raises(InvalidInputError):
        service.browse_catalog("nope")


def test_items_in_category(service):
    items = service.items_in_category("weapon")
    assert all(item.category.startswith("weapon") for item in items)


# ========== 创建测试 ==========

def test_create_item_success(service):
    payload = {
        "name": "测试剑",
        "category": "weapon.sword",
        "rarity": "common",
        "base_value": 100,
        "stats": {"attack": 10, "attack_speed": 1.0, "durability_max": 50},
        "description": "测试用剑",
    }
    item = service.create_item(payload)
    assert isinstance(item, Item)
    assert item.name == "测试剑"
    assert item.category == "weapon.sword"
    assert item.item_id.startswith("i_")


def test_create_item_missing_name_raises(service):
    with pytest.raises(InvalidInputError) as exc:
        service.create_item({"category": "weapon.sword", "rarity": "common", "base_value": 100, "stats": {}})
    assert exc.value.context["field"] == "name"


def test_create_item_invalid_category_raises(service):
    payload = {
        "name": "测试物品",
        "category": "invalid.category",
        "rarity": "common",
        "base_value": 100,
        "stats": {},
    }
    with pytest.raises(InvalidInputError) as exc:
        service.create_item(payload)
    assert exc.value.context["field"] == "category"


def test_create_item_invalid_rarity_raises(service):
    payload = {
        "name": "测试物品",
        "category": "weapon.sword",
        "rarity": "invalid",
        "base_value": 100,
        "stats": {},
    }
    with pytest.raises(InvalidInputError) as exc:
        service.create_item(payload)
    assert exc.value.context["field"] == "rarity"


def test_create_item_negative_base_value_raises(service):
    payload = {
        "name": "测试物品",
        "category": "weapon.sword",
        "rarity": "common",
        "base_value": -1,
        "stats": {},
    }
    with pytest.raises(InvalidInputError) as exc:
        service.create_item(payload)
    assert exc.value.context["field"] == "base_value"


def test_create_item_non_leaf_category_raises_invalid_input(service):
    before_items = dict(service.repo.items)
    payload = {
        "name": "非叶子分类",
        "category": "weapon",
        "rarity": "common",
        "base_value": 100,
        "stats": {"attack": 10, "attack_speed": 1.0, "durability_max": 50},
    }

    with pytest.raises(InvalidInputError) as exc:
        service.create_item(payload)

    assert exc.value.context["field"] == "category"
    assert service.repo.items == before_items


def test_create_item_bad_stats_raise_serialization_error_without_mutating(service):
    before_items = dict(service.repo.items)
    payload = {
        "name": "坏 stats",
        "category": "weapon.sword",
        "rarity": "common",
        "base_value": 100,
        "stats": {"attack": 10},
    }

    with pytest.raises(SerializationError):
        service.create_item(payload)

    assert service.repo.items == before_items


def test_items_in_category_invalid_category_raises(service):
    with pytest.raises(InvalidInputError) as exc:
        service.items_in_category("invalid.category")
    assert exc.value.context["field"] == "category"


def test_create_item_success_persists_once(tmp_path):
    class RecordingPersistence(Persistence):
        def __init__(self, data_dir: str) -> None:
            super().__init__(data_dir=data_dir)
            self.save_items_calls = 0

        def save_items(self, repo):
            self.save_items_calls += 1

    persistence = RecordingPersistence(data_dir=str(tmp_path / "data"))
    persistence.seed_if_empty()
    repo = persistence.load_all()
    service = ItemService(repo, persistence)

    item = service.create_item({
        "name": "持久化测试",
        "category": "misc",
        "rarity": "common",
        "base_value": 1,
        "stats": {"stack_size_max": 99, "count": 1},
    })

    assert item.item_id in repo.items
    assert persistence.save_items_calls == 1


# ========== 删除测试 ==========

def test_delete_item_success(service):
    # 创建一个未被引用的物品然后删除
    item = service.create_item({
        "name": "待删除",
        "category": "misc",
        "rarity": "common",
        "base_value": 1,
        "stats": {"stack_size_max": 99, "count": 1},
    })
    item_id = item.item_id
    service.delete_item(item_id)
    assert item_id not in service.repo.items


def test_delete_item_not_found_raises(service):
    with pytest.raises(ItemNotFoundError):
        service.delete_item("i_999999")


def test_delete_item_with_inventory_reference_raises(service):
    # 找到一个被玩家持有且没有被活跃挂单引用的物品
    active_listing_item_ids = {
        listing.item_id for listing in service.repo.listings.values()
        if listing.status == "active"
    }
    target_item_id = None
    for player in service.repo.players.values():
        for slot in player.inventory:
            iid = slot.get("item_id")
            if iid and iid not in active_listing_item_ids:
                target_item_id = iid
                break
        if target_item_id:
            break

    if target_item_id is None:
        pytest.skip("No player-only item found for test")

    with pytest.raises(BusinessRuleError) as exc:
        service.delete_item(target_item_id)
    assert "player" in exc.value.context["reason"]


def test_delete_item_with_active_listing_raises(service):
    # 找一个被挂单引用的物品
    for item_id in service.repo.items:
        for listing in service.repo.listings.values():
            if listing.item_id == item_id and listing.status == "active":
                with pytest.raises(BusinessRuleError) as exc:
                    service.delete_item(item_id)
                assert "listing" in exc.value.context["reason"]
                return
    pytest.skip("No active listing found for test")
