from __future__ import annotations

import pytest

from src.errors import InventoryFullError
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
