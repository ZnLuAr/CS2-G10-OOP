from __future__ import annotations

import pytest

from src.errors import InventoryFullError, ItemNotFoundError
from src.models import Player
from src.services.persistence import Repository
from src.services.player_inventory_service import PlayerInventoryService


class RecordingPersistence:
    def __init__(self) -> None:
        self.save_players_calls = 0

    def save_players(self, repo: Repository) -> None:
        self.save_players_calls += 1


def make_player(player_id: str, inventory: list[dict] | None = None) -> Player:
    return Player(
        player_id=player_id,
        name=player_id,
        gold=100,
        level=1,
        klass="warrior",
        inventory=list(inventory or []),
        created_at="2026-05-05T00:00:00Z",
    )


def make_item(item_id: str, stackable: bool = True) -> dict:
    return {
        "item_id": item_id,
        "name": item_id,
        "rarity": "common",
        "stackable": stackable,
        "stack_size_max": 10 if stackable else 1,
    }


def make_service(repo: Repository) -> tuple[PlayerInventoryService, RecordingPersistence]:
    persistence = RecordingPersistence()
    return PlayerInventoryService(repo, persistence), persistence


def test_build_inventory_skips_missing_item_records() -> None:
    repo = Repository(
        players={
            "p_001": make_player(
                "p_001",
                [
                    {"item_id": "i_exists", "count": 2},
                    {"item_id": "i_missing", "count": 1},
                ],
            )
        },
        items={"i_exists": make_item("i_exists")},
    )
    service, _ = make_service(repo)

    slots = service.get_slots("p_001")

    assert len(slots) == 1
    assert slots[0]._item_id() == "i_exists"
    assert slots[0].count == 2


def test_transfer_item_updates_both_players_with_single_save() -> None:
    repo = Repository(
        players={
            "p_from": make_player("p_from", [{"item_id": "i_001", "count": 3}]),
            "p_to": make_player("p_to"),
        },
        items={"i_001": make_item("i_001")},
    )
    service, persistence = make_service(repo)

    service.transfer_item("p_from", "p_to", "i_001", count=2)

    assert repo.players["p_from"].inventory == [{"item_id": "i_001", "count": 1}]
    assert repo.players["p_to"].inventory == [{"item_id": "i_001", "count": 2}]
    assert persistence.save_players_calls == 1


def test_transfer_item_does_not_persist_partial_update_when_receiver_full() -> None:
    full_inventory = [{"item_id": f"i_full_{i}", "count": 1} for i in range(50)]
    items = {slot["item_id"]: make_item(slot["item_id"], stackable=False) for slot in full_inventory}
    items["i_target"] = make_item("i_target", stackable=False)
    repo = Repository(
        players={
            "p_from": make_player("p_from", [{"item_id": "i_target", "count": 1}]),
            "p_to": make_player("p_to", full_inventory),
        },
        items=items,
    )
    service, persistence = make_service(repo)

    with pytest.raises(InventoryFullError):
        service.transfer_item("p_from", "p_to", "i_target", count=1)

    assert repo.players["p_from"].inventory == [{"item_id": "i_target", "count": 1}]
    assert repo.players["p_to"].inventory == full_inventory
    assert persistence.save_players_calls == 0


def test_transfer_item_leaves_state_unchanged_when_receiver_full() -> None:
    full_inventory = [{"item_id": f"i_full_{i}", "count": 1} for i in range(50)]
    items = {slot["item_id"]: make_item(slot["item_id"], stackable=False) for slot in full_inventory}
    items["i_target"] = make_item("i_target", stackable=False)
    repo = Repository(
        players={
            "p_from": make_player("p_from", [{"item_id": "i_target", "count": 1, "instance_state": {"enchant": "fire"}}]),
            "p_to": make_player("p_to", full_inventory),
        },
        items=items,
    )
    service, persistence = make_service(repo)

    with pytest.raises(InventoryFullError):
        service.transfer_item("p_from", "p_to", "i_target", count=1)

    assert repo.players["p_from"].inventory == [{"item_id": "i_target", "count": 1, "instance_state": {"enchant": "fire"}}]
    assert repo.players["p_to"].inventory == full_inventory
    assert persistence.save_players_calls == 0


def test_transfer_item_preserves_instance_state() -> None:
    """转账时 instance_state 不应丢失"""
    repo = Repository(
        players={
            "p_from": make_player("p_from", [{"item_id": "i_001", "count": 1, "instance_state": {"enchant": "fire", "level": 5}}]),
            "p_to": make_player("p_to"),
        },
        items={"i_001": make_item("i_001")},
    )
    service, persistence = make_service(repo)

    service.transfer_item("p_from", "p_to", "i_001", count=1)

    # 卖家背包为空
    assert repo.players["p_from"].inventory == []
    # 买家背包保留 instance_state
    assert repo.players["p_to"].inventory == [{"item_id": "i_001", "count": 1, "instance_state": {"enchant": "fire", "level": 5}}]
    assert persistence.save_players_calls == 1


def test_transfer_item_preserves_instance_state_across_multiple_slots() -> None:
    """从多个槽位转移时，应使用第一个匹配槽位的 instance_state"""
    # 卖家有两个相同 item_id 不同 state 的槽位
    repo = Repository(
        players={
            "p_from": make_player("p_from", [
                {"item_id": "i_001", "count": 2, "instance_state": {"enchant": "fire"}},
                {"item_id": "i_001", "count": 3, "instance_state": {"enchant": "ice"}},
            ]),
            "p_to": make_player("p_to"),
        },
        items={"i_001": make_item("i_001", stackable=True)},
    )
    service, persistence = make_service(repo)

    # 转移 2 个物品（应该取第一个槽位的 state）
    service.transfer_item("p_from", "p_to", "i_001", count=2)

    # 卖家剩下第二个槽位（ice）
    assert len(repo.players["p_from"].inventory) == 1
    assert repo.players["p_from"].inventory[0]["instance_state"] == {"enchant": "ice"}
    # 买家获得 fire state（第一个槽位的 state）
    assert len(repo.players["p_to"].inventory) == 1
    assert repo.players["p_to"].inventory[0]["instance_state"] == {"enchant": "fire"}
    assert repo.players["p_to"].inventory[0]["count"] == 2


def test_remove_item_by_state_via_service() -> None:
    """通过 PlayerInventoryService 精确移除特定状态的物品"""
    repo = Repository(
        players={
            "p_001": make_player("p_001", [
                {"item_id": "i_001", "count": 3, "instance_state": {"enchant": "fire", "level": 5}},
                {"item_id": "i_001", "count": 2, "instance_state": {"enchant": "ice", "level": 3}},
            ]),
        },
        items={"i_001": make_item("i_001")},
    )
    service, persistence = make_service(repo)

    # 只移除 fire 状态的 2 个
    service.remove_item_by_state("p_001", "i_001", {"enchant": "fire", "level": 5}, count=2)

    # fire 槽位剩 1 个，ice 槽位不变
    player_inv = repo.players["p_001"].inventory
    assert len(player_inv) == 2
    fire_slot = next(s for s in player_inv if s.get("instance_state") == {"enchant": "fire", "level": 5})
    ice_slot = next(s for s in player_inv if s.get("instance_state") == {"enchant": "ice", "level": 3})
    assert fire_slot["count"] == 1
    assert ice_slot["count"] == 2
    assert persistence.save_players_calls == 1


def test_remove_item_by_state_not_found_raises() -> None:
    """通过 PlayerInventoryService 找不到匹配状态时应抛 ItemNotFoundError"""
    repo = Repository(
        players={
            "p_001": make_player("p_001", [
                {"item_id": "i_001", "count": 3, "instance_state": {"enchant": "fire"}},
            ]),
        },
        items={"i_001": make_item("i_001")},
    )
    service, _ = make_service(repo)

    with pytest.raises(ItemNotFoundError):
        service.remove_item_by_state("p_001", "i_001", {"enchant": "nonexistent"}, count=1)
