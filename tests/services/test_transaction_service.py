from __future__ import annotations

import pytest

from src.errors import InvalidInputError
from src.models import Transaction
from src.services.persistence import Persistence
from src.services.transaction import TransactionService


@pytest.fixture
def service(tmp_path):
    persistence = Persistence(data_dir=str(tmp_path / "data"))
    persistence.seed_if_empty()
    repo = persistence.load_all()
    service = TransactionService(repo, persistence)
    sample = Transaction(
        transaction_id="t_900001",
        listing_id="l_001",
        buyer_id="p_001",
        seller_id="p_002",
        item_id="i_001",
        count=1,
        price=100,
        total=100,
        completed_at="2026-04-21T00:00:00Z",
    )
    service.append(sample)
    return service


def test_by_player_returns_transactions(service):
    result = service.by_player("p_001", role="buyer")
    assert result
    assert all(t.buyer_id == "p_001" for t in result)


def test_by_item_returns_transactions(service):
    result = service.by_item("i_001")
    assert result
    assert all(t.item_id == "i_001" for t in result)


def test_by_category_returns_transactions(service):
    category = service.repo.items["i_001"]["category"].split(".")[0]
    result = service.by_category(category)
    assert result
    assert all(service.repo.items[t.item_id]["category"].startswith(category) for t in result)


def test_price_stats(service):
    stats = service.price_stats("i_001")
    assert stats["count"] >= 1
    assert stats["min"] <= stats["max"]


def test_price_stats_by_category(service):
    category = service.repo.items["i_001"]["category"].split(".")[0]
    stats = service.price_stats_by_category(category)
    assert stats["count"] >= 1
    assert stats["min"] <= stats["max"]


def test_price_stats_empty_raises(service):
    with pytest.raises(InvalidInputError):
        service.price_stats("i_999999")


def test_price_stats_by_category_empty_raises(service):
    with pytest.raises(InvalidInputError):
        service.price_stats_by_category("unknown.category")


def test_top_by_gold(service):
    players = service.top_by_gold(5)
    assert len(players) <= 5
    if len(players) >= 2:
        assert players[0].gold >= players[1].gold


def test_top_by_volume(service):
    ranked = service.top_by_volume(5)
    assert len(ranked) <= 5
    if len(ranked) >= 2:
        assert ranked[0][1] >= ranked[1][1]


def test_snapshot(service):
    snap = service.snapshot()
    assert snap["players"] == len(service.repo.players)
    assert snap["items"] == len(service.repo.items)


def test_append(service):
    before = len(service.repo.transactions)
    txn = Transaction(
        transaction_id="t_999999",
        listing_id="l_001",
        buyer_id="p_001",
        seller_id="p_002",
        item_id="i_001",
        count=1,
        price=100,
        total=100,
        completed_at="2026-04-21T00:00:00Z",
    )
    service.append(txn)
    assert len(service.repo.transactions) == before + 1
