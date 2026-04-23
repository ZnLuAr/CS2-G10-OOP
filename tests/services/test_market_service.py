from __future__ import annotations

import pytest

from src.errors import BusinessRuleError, ListingNotFoundError
from src.services.market import MarketService
from src.services.persistence import Persistence
from src.services.player_service import PlayerService
from src.services.transaction import TransactionService


@pytest.fixture
def service(tmp_path):
    persistence = Persistence(data_dir=str(tmp_path / "data"))
    persistence.seed_if_empty()
    repo = persistence.load_all()
    player_service = PlayerService(repo, persistence)
    transaction_service = TransactionService(repo, persistence)
    return MarketService(repo, persistence, player_service, transaction_service)


def test_list_active(service):
    active = service.list_active()
    assert all(l.status == "active" for l in active)


def test_query_by_price_range(service):
    result = service.query_by_price_range(0, 10_000)
    assert all(l.status == "active" for l in result)


def test_query_by_seller(service):
    listing = next(iter(service.repo.listings.values()))
    result = service.query_by_seller(listing.seller_id)
    assert all(l.seller_id == listing.seller_id for l in result)


def test_get_listing(service):
    listing = next(iter(service.repo.listings.values()))
    assert service.get_listing(listing.listing_id).listing_id == listing.listing_id


def test_get_listing_missing_raises(service):
    with pytest.raises(ListingNotFoundError):
        service.get_listing("l_999999")


def test_cancel_listing(service):
    listing = next(l for l in service.repo.listings.values() if l.status == "active")
    service.cancel_listing(listing.listing_id, listing.seller_id)
    assert service.get_listing(listing.listing_id).status == "cancelled"


def test_cancel_listing_wrong_user_raises(service):
    listing = next(l for l in service.repo.listings.values() if l.status == "active")
    with pytest.raises(BusinessRuleError):
        service.cancel_listing(listing.listing_id, "p_999999")


def test_buy_not_implemented(service):
    with pytest.raises(NotImplementedError):
        service.buy("l_001", "p_001")
