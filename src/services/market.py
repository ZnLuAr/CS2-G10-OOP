"""市场交易服务"""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Callable

from src.errors import (
    BusinessRuleError,
    DuplicateListingError,
    InsufficientGoldError,
    InvalidInputError,
    ItemBrokenError,
    ItemNotEquippableError,
    ItemNotFoundError,
    ListingNotActiveError,
    ListingNotFoundError,
    PlayerNotFoundError,
    SelfPurchaseError,
    TradingSystemError,
)
from src.models import (
    Durable,
    Equippable,
    Listing,
    STATUS_ACTIVE,
    STATUS_CANCELLED,
    STATUS_SOLD,
    Transaction,
)
from src.services.inventory import Inventory, InventorySlot
from src.services.logger import log
from src.services.persistence import Persistence, Repository
from src.structures import PriceBST, Queue

__all__ = ["MarketService"]




class MarketService:
    def __init__(self,
                 repo: Repository,
                 persistence: Persistence,
                 player_service,
                 transaction_service) -> None:
        self.repo = repo
        self.persistence = persistence
        self.player_service = player_service
        self.transaction_service = transaction_service


    def create_listing(self, seller_id: str, item_id: str,
                       count: int, price: int) -> Listing:
        self._validate_positive_int("count", count)
        self._validate_positive_int("price", price)

        seller = self._get_player(seller_id)
        item = self._get_item(item_id)
        if not item.stackable and count != 1:
            raise InvalidInputError(field="count", value=count)

        inventory = self._build_inventory(seller_id, seller.inventory)
        source_slot = inventory.find(item_id)
        if source_slot is None:
            raise ItemNotFoundError(item_id=item_id)

        instance_state = self._slot_instance_state(source_slot)
        self._ensure_item_can_be_listed(item, instance_state)
        if not item.stackable:
            self._ensure_no_duplicate_nonstackable_listing(seller_id, item_id, instance_state)

        seller_inventory_before = self._copy_inventory_data(seller.inventory)
        inventory.remove_by_state(item_id, instance_state, count=count)

        listing = Listing(
            listing_id=self.persistence.next_listing_id(),
            seller_id=seller_id,
            item_id=item_id,
            count=count,
            price=price,
            status=STATUS_ACTIVE,
            created_at=self._utc_now(),
            closed_at=None,
            instance_state=instance_state,
        )

        seller.inventory = inventory.to_inventory_data()
        self.repo.listings[listing.listing_id] = listing

        def rollback() -> None:
            seller.inventory = seller_inventory_before
            self.repo.listings.pop(listing.listing_id, None)

        self._save_or_rollback(rollback, self.persistence.save_players, self.persistence.save_market)
        log.info(
            "market",
            "listing_created",
            listing_id=listing.listing_id,
            seller_id=seller_id,
            item_id=item_id,
            count=count,
            price=price,
        )
        return listing


    def cancel_listing(self, listing_id: str, requester_id: str) -> None:
        listing = self.get_listing(listing_id)
        self._ensure_active(listing)
        if listing.seller_id != requester_id:
            raise BusinessRuleError(
                message="只能撤销自己的挂单",
                listing_id=listing_id,
                requester_id=requester_id,
                seller_id=listing.seller_id,
            )

        seller = self._get_player(listing.seller_id)
        item = self._get_item(listing.item_id)
        inventory = self._build_inventory(seller.player_id, seller.inventory)
        inventory.add(item, count=listing.count, instance_state=listing.instance_state)

        seller_inventory_before = self._copy_inventory_data(seller.inventory)
        old_status = listing.status
        old_closed_at = listing.closed_at

        seller.inventory = inventory.to_inventory_data()
        listing.status = STATUS_CANCELLED
        listing.closed_at = self._utc_now()

        def rollback() -> None:
            seller.inventory = seller_inventory_before
            listing.status = old_status
            listing.closed_at = old_closed_at

        self._save_or_rollback(rollback, self.persistence.save_players, self.persistence.save_market)
        log.info("market", "listing_cancelled", listing_id=listing_id, requester_id=requester_id)


    def list_active(self, sort_by: str = "created_at",
                    desc: bool = False) -> list[Listing]:
        listings = [l for l in self.repo.listings.values() if l.status == STATUS_ACTIVE]
        if sort_by == "created_at":
            key = lambda l: l.created_at
        elif sort_by == "price":
            key = lambda l: l.price
        else:
            raise InvalidInputError(field="sort_by", value=sort_by)
        return sorted(listings, key=key, reverse=desc)


    def query_by_price_range(self, min_price: int,
                             max_price: int) -> list[Listing]:
        if not isinstance(min_price, int) or isinstance(min_price, bool) or min_price < 0:
            raise InvalidInputError(field="min_price", value=min_price)
        if not isinstance(max_price, int) or isinstance(max_price, bool) or max_price < 0:
            raise InvalidInputError(field="max_price", value=max_price)
        if min_price > max_price:
            raise InvalidInputError(field="price_range", value=(min_price, max_price))
        tree = PriceBST()
        for listing in self.repo.listings.values():
            if listing.status == STATUS_ACTIVE:
                tree.insert(listing.price, listing)
        return tree.range_query(min_price, max_price)


    def query_by_category(self, category_prefix: str) -> list[Listing]:
        if not isinstance(category_prefix, str) or not category_prefix.strip():
            raise InvalidInputError(field="category_prefix", value=category_prefix)
        category_prefix = category_prefix.strip()
        if self.repo.catalog.find_by_path(category_prefix) is None:
            raise InvalidInputError(field="category_prefix", value=category_prefix)

        item_ids = {
            item_id for item_id, item in self.repo.items.items()
            if self._category_matches(item.category, category_prefix)
        }
        return [
            l for l in self.repo.listings.values()
            if l.status == STATUS_ACTIVE and l.item_id in item_ids
        ]


    def query_by_seller(self, seller_id: str) -> list[Listing]:
        self._get_player(seller_id)
        return [
            l for l in self.repo.listings.values()
            if l.status == STATUS_ACTIVE and l.seller_id == seller_id
        ]


    def get_listing(self, listing_id: str) -> Listing:
        listing = self.repo.listings.get(listing_id)
        if listing is None:
            raise ListingNotFoundError(listing_id=listing_id)
        return listing


    def buy(self, listing_id: str, buyer_id: str) -> Transaction:
        listing = self.get_listing(listing_id)
        self._ensure_active(listing)
        buyer = self._get_player(buyer_id)
        seller = self._get_player(listing.seller_id)
        if buyer_id == listing.seller_id:
            log.warn("market", "self_purchase_blocked", listing_id=listing_id, buyer_id=buyer_id)
            raise SelfPurchaseError(player_id=buyer_id, listing_id=listing_id)

        item = self._get_item(listing.item_id)
        total = listing.count * listing.price
        if buyer.gold < total:
            log.warn(
                "market",
                "insufficient_gold",
                listing_id=listing_id,
                buyer_id=buyer_id,
                required=total,
                available=buyer.gold,
            )
            raise InsufficientGoldError(required=total, available=buyer.gold, listing_id=listing_id)

        buyer_inventory = self._build_inventory(buyer_id, buyer.inventory)
        buyer_inventory.add(item, count=listing.count, instance_state=listing.instance_state)

        buyer_gold_before = buyer.gold
        seller_gold_before = seller.gold
        buyer_inventory_before = self._copy_inventory_data(buyer.inventory)
        old_status = listing.status
        old_closed_at = listing.closed_at
        transactions_len = len(self.repo.transactions)

        completed_at = self._utc_now()
        transaction = Transaction(
            transaction_id=self.persistence.next_transaction_id(),
            listing_id=listing.listing_id,
            buyer_id=buyer_id,
            seller_id=listing.seller_id,
            item_id=listing.item_id,
            count=listing.count,
            price=listing.price,
            total=total,
            completed_at=completed_at,
        )

        buyer.gold -= total
        seller.gold += total
        buyer.inventory = buyer_inventory.to_inventory_data()
        listing.status = STATUS_SOLD
        listing.closed_at = completed_at
        self.repo.transactions.append(transaction)

        def rollback() -> None:
            buyer.gold = buyer_gold_before
            seller.gold = seller_gold_before
            buyer.inventory = buyer_inventory_before
            listing.status = old_status
            listing.closed_at = old_closed_at
            del self.repo.transactions[transactions_len:]

        self._save_or_rollback(
            rollback,
            self.persistence.save_players,
            self.persistence.save_market,
            self.persistence.save_transactions,
        )
        log.info(
            "market",
            "buy_completed",
            transaction_id=transaction.transaction_id,
            listing_id=listing_id,
            buyer_id=buyer_id,
            seller_id=listing.seller_id,
            total=total,
        )
        return transaction


    def settle_pending(self, orders: list[tuple[str, str]]) -> list[Transaction]:
        queue = Queue()
        for order in orders:
            queue.enqueue(order)

        transactions: list[Transaction] = []
        while not queue.is_empty():
            listing_id, buyer_id = queue.dequeue()
            try:
                transactions.append(self.buy(listing_id, buyer_id))
            except TradingSystemError as e:
                log.warn(
                    "market",
                    "pending_settlement_failed",
                    listing_id=listing_id,
                    buyer_id=buyer_id,
                    error=type(e).__name__,
                    message=e.message,
                )
        return transactions


    @staticmethod
    def _utc_now() -> str:
        return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


    @staticmethod
    def _validate_positive_int(field: str, value: int) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise InvalidInputError(field=field, value=value)


    def _get_player(self, player_id: str):
        player = self.repo.players.get(player_id)
        if player is None:
            raise PlayerNotFoundError(player_id=player_id)
        return player


    def _get_item(self, item_id: str):
        item = self.repo.items.get(item_id)
        if item is None:
            raise ItemNotFoundError(item_id=item_id)
        return item


    def _build_inventory(self, player_id: str, data: list[dict]) -> Inventory:
        return Inventory.from_inventory_data(
            owner_id=player_id,
            data=data,
            item_lookup=lambda iid: self.repo.items[iid],
        )


    @staticmethod
    def _copy_inventory_data(data: list[dict]) -> list[dict]:
        return deepcopy(data)


    @staticmethod
    def _slot_instance_state(slot: InventorySlot) -> dict | None:
        return deepcopy(slot.instance_state) if slot.instance_state else None


    @staticmethod
    def _category_matches(item_category: str, category_prefix: str) -> bool:
        return item_category == category_prefix or item_category.startswith(f"{category_prefix}.")


    def _ensure_active(self, listing: Listing) -> None:
        if listing.status != STATUS_ACTIVE:
            raise ListingNotActiveError(listing_id=listing.listing_id, status=listing.status)


    def _ensure_item_can_be_listed(self, item, instance_state: dict | None) -> None:
        state = instance_state or {}
        if isinstance(item, Durable):
            durability = state.get("durability", item.durability)
            if durability == 0:
                raise ItemBrokenError(item_id=item.item_id)
        if isinstance(item, Equippable):
            equipped = state.get("equipped", item.equipped)
            if equipped:
                raise ItemNotEquippableError(item_id=item.item_id, reason="已穿戴，需先脱下")


    def _ensure_no_duplicate_nonstackable_listing(
        self,
        seller_id: str,
        item_id: str,
        instance_state: dict | None,
    ) -> None:
        target_state = instance_state or {}
        for listing in self.repo.listings.values():
            listing_state = listing.instance_state or {}
            if (
                listing.status == STATUS_ACTIVE
                and listing.seller_id == seller_id
                and listing.item_id == item_id
                and listing_state == target_state
            ):
                raise DuplicateListingError(item_id=item_id, listing_id=listing.listing_id)


    def _save_or_rollback(self, rollback: Callable[[], None], *save_methods) -> None:
        try:
            for save in save_methods:
                save(self.repo)
        except Exception:
            rollback()
            raise
