from __future__ import annotations

import pytest

from src.errors import (
    BusinessRuleError,
    InsufficientGoldError,
    InvalidInputError,
    InventoryNotEmptyError,
    PlayerNotFoundError,
)
from src.services.persistence import Persistence
from src.services.player_service import PlayerService


@pytest.fixture
def service(tmp_path):
    persistence = Persistence(data_dir=str(tmp_path / "data"))
    persistence.seed_if_empty()
    repo = persistence.load_all()
    return PlayerService(repo, persistence)


def test_get_by_id_returns_player(service):
    pid = next(iter(service.repo.players))
    assert service.get_by_id(pid).player_id == pid


def test_get_by_id_missing_raises(service):
    with pytest.raises(PlayerNotFoundError):
        service.get_by_id("p_999999")


def test_search_by_name(service):
    player = next(iter(service.repo.players.values()))
    matches = service.search_by_name(player.name[:2])
    assert any(p.player_id == player.player_id for p in matches)


def test_list_all_sort_by_gold(service):
    players = service.list_all(sort_by="gold", desc=True)
    assert players[0].gold >= players[-1].gold


def test_add_gold(service):
    pid = next(iter(service.repo.players))
    before = service.get_by_id(pid).gold
    service.add_gold(pid, 123)
    assert service.get_by_id(pid).gold == before + 123


def test_add_gold_invalid_amount(service):
    pid = next(iter(service.repo.players))
    with pytest.raises(InvalidInputError):
        service.add_gold(pid, 0)


def test_spend_gold(service):
    pid = next(iter(service.repo.players))
    player = service.get_by_id(pid)
    amount = min(10, player.gold)
    service.spend_gold(pid, amount)
    assert service.get_by_id(pid).gold == player.gold


def test_spend_gold_insufficient(service):
    pid = next(iter(service.repo.players))
    player = service.get_by_id(pid)
    with pytest.raises(InsufficientGoldError):
        service.spend_gold(pid, player.gold + 999)


def test_create_player(service):
    player = service.create_player(name="Tester", gold=10)
    assert player.player_id in service.repo.players
    assert service.repo.players[player.player_id].name == "Tester"


def test_delete_blocked_by_inventory(service):
    pid = next(pid for pid, p in service.repo.players.items() if p.inventory)
    with pytest.raises(InventoryNotEmptyError):
        service.delete(pid)


def test_delete_blocked_by_active_listing(service):
    pid = next(iter(service.repo.listings.values())).seller_id
    service.repo.players[pid].inventory.clear()
    with pytest.raises(BusinessRuleError):
        service.delete(pid)
