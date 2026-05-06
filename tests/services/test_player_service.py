from __future__ import annotations

import pytest

from src.errors import (
    BusinessRuleError,
    InsufficientGoldError,
    InvalidInputError,
    InventoryNotEmptyError,
    PlayerNotFoundError,
)
from src.models import Listing, Player, STATUS_ACTIVE, STATUS_CANCELLED, STATUS_SOLD
from src.services.persistence import Repository
from src.services.player_service import PlayerService


class RecordingPersistence:
    def __init__(self):
        self.saved: list[str] = []
        self._player_counter = 100

    def next_player_id(self) -> str:
        self._player_counter += 1
        return f"p_{self._player_counter:03d}"

    def save_players(self, repo: Repository) -> None:
        self.saved.append("players")


@pytest.fixture
def repo():
    repo = Repository()
    repo.players = {
        "p_001": Player("p_001", "Alice", 100, 2, "warrior", []),
        "p_002": Player("p_002", "Bob", 300, 4, "mage", [
            {"item_id": "i_potion", "count": 2},
        ]),
        "p_003": Player("p_003", "Carol", 200, 3, "archer", []),
    }
    repo.listings = {
        "l_active": Listing("l_active", "p_001", "i_sword", 1, 50, STATUS_ACTIVE),
        "l_sold": Listing("l_sold", "p_003", "i_potion", 1, 10, STATUS_SOLD),
        "l_cancelled": Listing("l_cancelled", "p_003", "i_potion", 1, 11, STATUS_CANCELLED),
    }
    return repo


@pytest.fixture
def persistence():
    return RecordingPersistence()


@pytest.fixture
def service(repo, persistence):
    return PlayerService(repo, persistence)


def test_create_player_success_trims_name_and_persists(service, repo, persistence):
    player = service.create_player(name="  Tester  ", gold=10, level=2, klass="mage")

    assert player.player_id == "p_101"
    assert repo.players[player.player_id] is player
    assert player.name == "Tester"
    assert player.gold == 10
    assert player.level == 2
    assert player.klass == "mage"
    assert player.inventory == []
    assert player.created_at
    assert persistence.saved == ["players"]


@pytest.mark.parametrize("name", ["", "   ", "x" * 21])
def test_create_player_invalid_name_raises_without_save(service, repo, persistence, name):
    before = dict(repo.players)

    with pytest.raises(InvalidInputError):
        service.create_player(name=name)

    assert repo.players == before
    assert persistence.saved == []


@pytest.mark.parametrize(
    ("gold", "level", "klass"),
    [(-1, 1, "none"), (True, 1, "none"), (0, 0, "none"), (0, True, "none"), (0, 1, "bad")],
)
def test_create_player_invalid_fields_raise_without_save(service, repo, persistence, gold, level, klass):
    before = dict(repo.players)

    with pytest.raises(InvalidInputError):
        service.create_player(name="Tester", gold=gold, level=level, klass=klass)

    assert repo.players == before
    assert persistence.saved == []


def test_get_by_id_returns_player(service):
    assert service.get_by_id("p_001").name == "Alice"


def test_get_by_id_missing_raises(service):
    with pytest.raises(PlayerNotFoundError):
        service.get_by_id("p_999999")


def test_search_by_name_is_case_insensitive_and_empty_returns_empty(service):
    assert [p.player_id for p in service.search_by_name("ali")] == ["p_001"]
    assert [p.player_id for p in service.search_by_name("BO")] == ["p_002"]
    assert service.search_by_name("   ") == []


def test_list_all_sorting(service):
    assert [p.player_id for p in service.list_all(sort_by="id")] == ["p_001", "p_002", "p_003"]
    assert [p.name for p in service.list_all(sort_by="name")] == ["Alice", "Bob", "Carol"]
    assert [p.player_id for p in service.list_all(sort_by="gold", desc=True)] == ["p_002", "p_003", "p_001"]


def test_list_all_invalid_sort_raises(service):
    with pytest.raises(InvalidInputError):
        service.list_all(sort_by="level")


def test_rename_success_changes_only_name_and_persists(service, repo, persistence):
    player = repo.players["p_001"]

    service.rename("p_001", "  Alicia  ")

    assert player.player_id == "p_001"
    assert player.name == "Alicia"
    assert player.gold == 100
    assert persistence.saved == ["players"]


def test_rename_missing_or_invalid_raises_without_save(service, repo, persistence):
    before_name = repo.players["p_001"].name

    with pytest.raises(PlayerNotFoundError):
        service.rename("p_missing", "New")
    with pytest.raises(InvalidInputError):
        service.rename("p_001", "")

    assert repo.players["p_001"].name == before_name
    assert persistence.saved == []


def test_add_gold_success_and_validation(service, repo, persistence):
    service.add_gold("p_001", 123)

    assert repo.players["p_001"].gold == 223
    assert persistence.saved == ["players"]

    with pytest.raises(InvalidInputError):
        service.add_gold("p_001", 0)
    with pytest.raises(InvalidInputError):
        service.add_gold("p_001", -1)
    with pytest.raises(InvalidInputError):
        service.add_gold("p_001", True)
    with pytest.raises(PlayerNotFoundError):
        service.add_gold("p_missing", 1)


def test_spend_gold_success_and_validation(service, repo, persistence):
    service.spend_gold("p_001", 40)

    assert repo.players["p_001"].gold == 60
    assert persistence.saved == ["players"]

    with pytest.raises(InvalidInputError):
        service.spend_gold("p_001", 0)
    with pytest.raises(InvalidInputError):
        service.spend_gold("p_001", -1)
    with pytest.raises(InvalidInputError):
        service.spend_gold("p_001", True)
    with pytest.raises(PlayerNotFoundError):
        service.spend_gold("p_missing", 1)


def test_spend_gold_insufficient_does_not_mutate_or_save(service, repo, persistence):
    before = repo.players["p_001"].gold

    with pytest.raises(InsufficientGoldError):
        service.spend_gold("p_001", before + 1)

    assert repo.players["p_001"].gold == before
    assert persistence.saved == []


def test_delete_success_allows_only_inactive_listings(service, repo, persistence):
    service.delete("p_003")

    assert "p_003" not in repo.players
    assert persistence.saved == ["players"]


def test_delete_missing_raises(service):
    with pytest.raises(PlayerNotFoundError):
        service.delete("p_missing")


def test_delete_blocked_by_inventory(service, repo, persistence):
    before = dict(repo.players)

    with pytest.raises(InventoryNotEmptyError):
        service.delete("p_002")

    assert repo.players == before
    assert persistence.saved == []


def test_delete_blocked_by_active_listing(service, repo, persistence):
    before = dict(repo.players)

    with pytest.raises(BusinessRuleError):
        service.delete("p_001")

    assert repo.players == before
    assert persistence.saved == []
