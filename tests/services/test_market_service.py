from __future__ import annotations

import pytest

from src.errors import (
    BusinessRuleError,
    DuplicateListingError,
    InsufficientGoldError,
    InvalidInputError,
    InventoryFullError,
    ItemBrokenError,
    ItemNotEquippableError,
    ItemNotFoundError,
    ListingNotActiveError,
    ListingNotFoundError,
    PlayerNotFoundError,
    SelfPurchaseError,
)
from src.models import Item, Listing, Player, STATUS_ACTIVE, STATUS_CANCELLED, STATUS_SOLD
from src.services.market import MarketService
from src.services.persistence import Repository
from src.services.player_service import PlayerService
from src.services.transaction import TransactionService
from src.structures import CatalogTree


class RecordingPersistence:
    def __init__(self):
        self.saved: list[str] = []
        self.fail_on: str | None = None
        self._listing_counter = 100
        self._transaction_counter = 100

    def next_listing_id(self) -> str:
        self._listing_counter += 1
        return f"l_{self._listing_counter:03d}"

    def next_transaction_id(self) -> str:
        self._transaction_counter += 1
        return f"t_{self._transaction_counter:03d}"

    def save_players(self, repo: Repository) -> None:
        self._save("players")

    def save_market(self, repo: Repository) -> None:
        self._save("market")

    def save_transactions(self, repo: Repository) -> None:
        self._save("transactions")

    def _save(self, name: str) -> None:
        self.saved.append(name)
        if self.fail_on == name:
            raise RuntimeError(f"failed saving {name}")


@pytest.fixture
def sword():
    return Item.from_dict({
        "item_id": "i_sword",
        "name": "测试剑",
        "category": "weapon.sword",
        "rarity": "rare",
        "base_value": 100,
        "stats": {
            "attack": 12,
            "attack_speed": 1.2,
            "durability": 8,
            "durability_max": 10,
            "equipped": False,
            "slot": "weapon",
        },
    })


@pytest.fixture
def potion():
    return Item.from_dict({
        "item_id": "i_potion",
        "name": "测试药水",
        "category": "consumable.potion",
        "rarity": "common",
        "base_value": 5,
        "stats": {
            "effect": "heal",
            "power": 10,
            "duration": 0,
            "stack_size_max": 20,
            "count": 1,
        },
    })


@pytest.fixture
def repo(sword, potion):
    repo = Repository()
    repo.catalog = CatalogTree.from_dict({
        "root": {
            "key": "root",
            "label": "全部",
            "children": [
                {
                    "key": "weapon",
                    "label": "武器",
                    "children": [{"key": "sword", "label": "剑", "children": []}],
                },
                {
                    "key": "consumable",
                    "label": "消耗品",
                    "children": [{"key": "potion", "label": "药水", "children": []}],
                },
                {"key": "misc", "label": "杂项", "children": []},
            ],
        }
    })
    repo.items = {sword.item_id: sword, potion.item_id: potion}
    repo.players = {
        "p_seller": Player("p_seller", "卖家", 100, 1, "warrior", [
            {"item_id": "i_sword", "count": 1, "instance_state": {"durability": 8, "equipped": False}},
            {"item_id": "i_potion", "count": 10},
        ]),
        "p_buyer": Player("p_buyer", "买家", 500, 1, "mage", []),
    }
    repo.listings = {
        "l_active": Listing(
            listing_id="l_active",
            seller_id="p_seller",
            item_id="i_sword",
            count=1,
            price=120,
            status=STATUS_ACTIVE,
            created_at="2026-05-06T00:00:00Z",
            instance_state={"durability": 8, "equipped": False},
        ),
        "l_sold": Listing(
            listing_id="l_sold",
            seller_id="p_seller",
            item_id="i_potion",
            count=1,
            price=8,
            status=STATUS_SOLD,
            created_at="2026-05-06T00:00:00Z",
            closed_at="2026-05-06T00:10:00Z",
        ),
    }
    return repo


@pytest.fixture
def persistence():
    return RecordingPersistence()


@pytest.fixture
def make_service():
    def _make(repo: Repository, persistence: RecordingPersistence) -> MarketService:
        player_service = PlayerService(repo, persistence)
        transaction_service = TransactionService(repo, persistence)
        return MarketService(repo, persistence, player_service, transaction_service)
    return _make


@pytest.fixture
def service(repo, persistence, make_service):
    return make_service(repo, persistence)


def inventory_count(player: Player, item_id: str) -> int:
    return sum(slot.get("count", 1) for slot in player.inventory if slot.get("item_id") == item_id)


def test_list_active(service):
    active = service.list_active()
    assert active
    assert all(l.status == STATUS_ACTIVE for l in active)


def test_query_by_price_range_active_only(service):
    result = service.query_by_price_range(0, 10_000)
    assert {l.listing_id for l in result} == {"l_active"}


def test_query_by_price_range_uses_bst_in_price_order(service, repo):
    repo.listings["l_low"] = Listing(
        listing_id="l_low",
        seller_id="p_seller",
        item_id="i_potion",
        count=1,
        price=5,
        status=STATUS_ACTIVE,
    )
    repo.listings["l_same"] = Listing(
        listing_id="l_same",
        seller_id="p_seller",
        item_id="i_potion",
        count=1,
        price=120,
        status=STATUS_ACTIVE,
    )

    assert [l.listing_id for l in service.query_by_price_range(5, 120)] == [
        "l_low",
        "l_active",
        "l_same",
    ]


def test_query_by_price_range_invalid_range_raises(service):
    with pytest.raises(InvalidInputError):
        service.query_by_price_range(100, 1)


@pytest.mark.parametrize(
    ("min_price", "max_price"),
    [(-1, 10), (1, -10), (False, 10), (1, True), ("1", 10), (1, "10")],
)
def test_query_by_price_range_invalid_input_types_raise(service, min_price, max_price):
    with pytest.raises(InvalidInputError):
        service.query_by_price_range(min_price, max_price)


def test_query_by_category_uses_catalog_and_active_listings(service):
    result = service.query_by_category("weapon")
    assert [l.listing_id for l in result] == ["l_active"]


def test_query_by_category_invalid_category_raises(service):
    with pytest.raises(InvalidInputError):
        service.query_by_category("weapon.nope")


@pytest.mark.parametrize("category", ["", "   ", 123])
def test_query_by_category_invalid_input_raises(service, category):
    with pytest.raises(InvalidInputError):
        service.query_by_category(category)


def test_query_by_seller_validates_player(service):
    assert [l.listing_id for l in service.query_by_seller("p_seller")] == ["l_active"]
    with pytest.raises(PlayerNotFoundError):
        service.query_by_seller("p_missing")


def test_get_listing(service):
    assert service.get_listing("l_active").listing_id == "l_active"


def test_get_listing_missing_raises(service):
    with pytest.raises(ListingNotFoundError):
        service.get_listing("l_999999")


def test_create_listing_success_removes_item_and_persists(service, repo, persistence):
    repo.listings.clear()
    seller = repo.players["p_seller"]

    listing = service.create_listing("p_seller", "i_sword", 1, 150)

    assert listing.status == STATUS_ACTIVE
    assert listing.seller_id == "p_seller"
    assert listing.item_id == "i_sword"
    assert listing.instance_state == {"durability": 8, "equipped": False}
    assert listing.listing_id in repo.listings
    assert inventory_count(seller, "i_sword") == 0
    assert persistence.saved == ["players", "market"]


def test_create_listing_stackable_partial_count(service, repo):
    repo.listings.clear()
    seller = repo.players["p_seller"]

    listing = service.create_listing("p_seller", "i_potion", 3, 7)

    assert listing.count == 3
    assert inventory_count(seller, "i_potion") == 7


def test_create_listing_removes_matching_instance_state_only(service, repo):
    repo.listings.clear()
    seller = repo.players["p_seller"]
    seller.inventory = [
        {"item_id": "i_sword", "count": 1, "instance_state": {"durability": 8, "equipped": False}},
        {"item_id": "i_sword", "count": 1, "instance_state": {"durability": 3, "equipped": False}},
    ]

    listing = service.create_listing("p_seller", "i_sword", 1, 100)

    assert listing.instance_state == {"durability": 8, "equipped": False}
    assert seller.inventory == [
        {"item_id": "i_sword", "count": 1, "instance_state": {"durability": 3, "equipped": False}}
    ]


@pytest.mark.parametrize(("count", "price"), [(0, 10), (-1, 10), (True, 10), ("1", 10), (1, 0)])
def test_create_listing_invalid_inputs_do_not_mutate(service, repo, persistence, count, price):
    before_inventory = list(repo.players["p_seller"].inventory)
    before_listings = dict(repo.listings)

    with pytest.raises(InvalidInputError):
        service.create_listing("p_seller", "i_sword", count, price)

    assert repo.players["p_seller"].inventory == before_inventory
    assert repo.listings == before_listings
    assert persistence.saved == []


def test_create_listing_missing_seller_raises(service):
    with pytest.raises(PlayerNotFoundError):
        service.create_listing("p_missing", "i_sword", 1, 50)


def test_create_listing_missing_item_raises(service):
    with pytest.raises(ItemNotFoundError):
        service.create_listing("p_seller", "i_missing", 1, 50)


def test_create_listing_item_not_in_inventory_raises(service):
    with pytest.raises(ItemNotFoundError):
        service.create_listing("p_buyer", "i_sword", 1, 50)


def test_create_listing_insufficient_stackable_count_raises_without_mutation(service, repo, persistence):
    before_inventory = list(repo.players["p_seller"].inventory)
    before_listings = dict(repo.listings)

    with pytest.raises(InvalidInputError):
        service.create_listing("p_seller", "i_potion", 11, 5)

    assert repo.players["p_seller"].inventory == before_inventory
    assert repo.listings == before_listings
    assert persistence.saved == []


def test_create_listing_broken_item_raises(repo, persistence, make_service):
    repo.players["p_seller"].inventory = [
        {"item_id": "i_sword", "count": 1, "instance_state": {"durability": 0, "equipped": False}}
    ]
    service = make_service(repo, persistence)

    with pytest.raises(ItemBrokenError):
        service.create_listing("p_seller", "i_sword", 1, 50)
    assert persistence.saved == []


def test_create_listing_equipped_item_raises(repo, persistence, make_service):
    repo.players["p_seller"].inventory = [
        {"item_id": "i_sword", "count": 1, "instance_state": {"durability": 8, "equipped": True}}
    ]
    service = make_service(repo, persistence)

    with pytest.raises(ItemNotEquippableError):
        service.create_listing("p_seller", "i_sword", 1, 50)
    assert persistence.saved == []


def test_create_listing_duplicate_nonstackable_raises(service):
    with pytest.raises(DuplicateListingError):
        service.create_listing("p_seller", "i_sword", 1, 50)


def test_cancel_listing_success_returns_item_and_closes(service, repo, persistence):
    listing = repo.listings["l_active"]
    seller = repo.players["p_seller"]
    seller.inventory = []

    service.cancel_listing("l_active", "p_seller")

    assert listing.status == STATUS_CANCELLED
    assert listing.closed_at is not None
    assert seller.inventory == [
        {"item_id": "i_sword", "count": 1, "instance_state": {"durability": 8, "equipped": False}}
    ]
    assert persistence.saved == ["players", "market"]


def test_cancel_listing_missing_listing_raises(service):
    with pytest.raises(ListingNotFoundError):
        service.cancel_listing("l_missing", "p_seller")


def test_cancel_listing_missing_seller_raises_without_mutation(service, repo, persistence):
    listing = repo.listings["l_active"]
    del repo.players["p_seller"]

    with pytest.raises(PlayerNotFoundError):
        service.cancel_listing("l_active", "p_seller")

    assert listing.status == STATUS_ACTIVE
    assert listing.closed_at is None
    assert persistence.saved == []


def test_cancel_listing_missing_item_raises_without_mutation(service, repo, persistence):
    listing = repo.listings["l_active"]
    del repo.items["i_sword"]

    with pytest.raises(ItemNotFoundError):
        service.cancel_listing("l_active", "p_seller")

    assert listing.status == STATUS_ACTIVE
    assert listing.closed_at is None
    assert persistence.saved == []


def test_cancel_listing_wrong_user_raises_without_mutation(service, repo, persistence):
    listing = repo.listings["l_active"]
    before = (listing.status, listing.closed_at, list(repo.players["p_seller"].inventory))

    with pytest.raises(BusinessRuleError):
        service.cancel_listing("l_active", "p_buyer")

    assert (listing.status, listing.closed_at, repo.players["p_seller"].inventory) == before
    assert persistence.saved == []


def test_cancel_listing_inactive_raises_without_mutation(service, repo, persistence):
    listing = repo.listings["l_sold"]

    with pytest.raises(ListingNotActiveError):
        service.cancel_listing("l_sold", "p_seller")

    assert listing.status == STATUS_SOLD
    assert listing.closed_at == "2026-05-06T00:10:00Z"
    assert persistence.saved == []


def test_cancel_listing_inventory_full_keeps_listing_active(repo, persistence, make_service):
    repo.players["p_seller"].inventory = [
        {"item_id": "i_sword", "count": 1, "instance_state": {"slot": i}}
        for i in range(50)
    ]
    service = make_service(repo, persistence)
    listing = repo.listings["l_active"]

    with pytest.raises(InventoryFullError):
        service.cancel_listing("l_active", "p_seller")

    assert listing.status == STATUS_ACTIVE
    assert listing.closed_at is None
    assert len(repo.players["p_seller"].inventory) == 50
    assert persistence.saved == []


def test_buy_success_updates_gold_inventory_listing_and_transaction(service, repo, persistence):
    seller = repo.players["p_seller"]
    buyer = repo.players["p_buyer"]
    buyer_gold = buyer.gold
    seller_gold = seller.gold

    txn = service.buy("l_active", "p_buyer")

    assert buyer.gold == buyer_gold - 120
    assert seller.gold == seller_gold + 120
    assert buyer.inventory == [
        {"item_id": "i_sword", "count": 1, "instance_state": {"durability": 8, "equipped": False}}
    ]
    assert repo.listings["l_active"].status == STATUS_SOLD
    assert repo.listings["l_active"].closed_at is not None
    assert repo.transactions == [txn]
    assert txn.listing_id == "l_active"
    assert txn.buyer_id == "p_buyer"
    assert txn.seller_id == "p_seller"
    assert txn.item_id == "i_sword"
    assert txn.count == 1
    assert txn.price == 120
    assert txn.total == 120
    assert persistence.saved == ["players", "market", "transactions"]


def test_buy_missing_listing_raises(service):
    with pytest.raises(ListingNotFoundError):
        service.buy("l_missing", "p_buyer")


def test_buy_missing_item_raises_without_mutation(service, repo, persistence):
    del repo.items["i_sword"]
    before = (
        repo.players["p_buyer"].gold,
        repo.players["p_seller"].gold,
        list(repo.players["p_buyer"].inventory),
        repo.listings["l_active"].status,
        len(repo.transactions),
    )

    with pytest.raises(ItemNotFoundError):
        service.buy("l_active", "p_buyer")

    assert (
        repo.players["p_buyer"].gold,
        repo.players["p_seller"].gold,
        repo.players["p_buyer"].inventory,
        repo.listings["l_active"].status,
        len(repo.transactions),
    ) == before
    assert persistence.saved == []


def test_buy_insufficient_gold_rolls_back(service, repo, persistence):
    repo.players["p_buyer"].gold = 10
    before = (
        repo.players["p_buyer"].gold,
        repo.players["p_seller"].gold,
        list(repo.players["p_buyer"].inventory),
        repo.listings["l_active"].status,
        len(repo.transactions),
    )

    with pytest.raises(InsufficientGoldError):
        service.buy("l_active", "p_buyer")

    assert (
        repo.players["p_buyer"].gold,
        repo.players["p_seller"].gold,
        repo.players["p_buyer"].inventory,
        repo.listings["l_active"].status,
        len(repo.transactions),
    ) == before
    assert persistence.saved == []


def test_buy_self_purchase_rolls_back(service, repo, persistence):
    with pytest.raises(SelfPurchaseError):
        service.buy("l_active", "p_seller")

    assert repo.listings["l_active"].status == STATUS_ACTIVE
    assert repo.transactions == []
    assert persistence.saved == []


def test_buy_inactive_listing_raises(service, repo, persistence):
    with pytest.raises(ListingNotActiveError):
        service.buy("l_sold", "p_buyer")

    assert repo.transactions == []
    assert persistence.saved == []


def test_buy_buyer_inventory_full_rolls_back(repo, persistence, make_service):
    repo.players["p_buyer"].inventory = [
        {"item_id": "i_sword", "count": 1, "instance_state": {"slot": i}}
        for i in range(50)
    ]
    service = make_service(repo, persistence)
    before_gold = repo.players["p_buyer"].gold

    with pytest.raises(InventoryFullError):
        service.buy("l_active", "p_buyer")

    assert repo.players["p_buyer"].gold == before_gold
    assert repo.listings["l_active"].status == STATUS_ACTIVE
    assert len(repo.transactions) == 0
    assert persistence.saved == []


def test_buy_missing_buyer_raises(service):
    with pytest.raises(PlayerNotFoundError):
        service.buy("l_active", "p_missing")


@pytest.mark.parametrize("fail_on", ["players", "market", "transactions"])
def test_buy_persistence_failure_rolls_back_memory(repo, persistence, make_service, fail_on):
    persistence.fail_on = fail_on
    service = make_service(repo, persistence)
    buyer = repo.players["p_buyer"]
    seller = repo.players["p_seller"]
    before = (
        buyer.gold,
        seller.gold,
        list(buyer.inventory),
        repo.listings["l_active"].status,
        repo.listings["l_active"].closed_at,
        len(repo.transactions),
    )

    with pytest.raises(RuntimeError):
        service.buy("l_active", "p_buyer")

    assert (
        buyer.gold,
        seller.gold,
        buyer.inventory,
        repo.listings["l_active"].status,
        repo.listings["l_active"].closed_at,
        len(repo.transactions),
    ) == before


def test_create_listing_persistence_failure_rolls_back_memory(repo, persistence, make_service):
    persistence.fail_on = "market"
    repo.listings.clear()
    seller = repo.players["p_seller"]
    before_inventory = list(seller.inventory)
    service = make_service(repo, persistence)

    with pytest.raises(RuntimeError):
        service.create_listing("p_seller", "i_sword", 1, 100)

    assert seller.inventory == before_inventory
    assert repo.listings == {}


def test_cancel_listing_persistence_failure_rolls_back_memory(repo, persistence, make_service):
    persistence.fail_on = "market"
    seller = repo.players["p_seller"]
    seller.inventory = []
    listing = repo.listings["l_active"]
    before = (list(seller.inventory), listing.status, listing.closed_at)
    service = make_service(repo, persistence)

    with pytest.raises(RuntimeError):
        service.cancel_listing("l_active", "p_seller")

    assert (seller.inventory, listing.status, listing.closed_at) == before


def test_settle_pending_processes_fifo_and_continues_after_failure(service, repo, persistence):
    repo.listings["l_second"] = Listing(
        listing_id="l_second",
        seller_id="p_seller",
        item_id="i_potion",
        count=2,
        price=5,
        status=STATUS_ACTIVE,
    )

    result = service.settle_pending([
        ("l_active", "p_buyer"),
        ("l_sold", "p_buyer"),
        ("l_second", "p_buyer"),
    ])

    assert [txn.listing_id for txn in result] == ["l_active", "l_second"]
    assert [txn.listing_id for txn in repo.transactions] == ["l_active", "l_second"]
    assert repo.listings["l_active"].status == STATUS_SOLD
    assert repo.listings["l_sold"].status == STATUS_SOLD
    assert repo.listings["l_second"].status == STATUS_SOLD
    assert repo.players["p_buyer"].gold == 370
    assert persistence.saved == [
        "players", "market", "transactions",
        "players", "market", "transactions",
    ]
