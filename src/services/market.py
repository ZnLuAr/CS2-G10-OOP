"""市场查询服务"""

from __future__ import annotations

from src.errors import (
    BusinessRuleError,
    InvalidInputError,
    ListingNotFoundError,
)
from src.models import Listing
from src.services.logger import log
from src.services.persistence import Persistence, Repository

__all__ = ["MarketService"]




class MarketService:
    def __init__(self,
                 repo: Repository,
                 persistence: Persistence,
                 player_service=None,
                 transaction_service=None) -> None:
        self.repo = repo
        self.persistence = persistence
        self.player_service = player_service
        self.transaction_service = transaction_service

    def create_listing(self, seller_id: str, item_id: str,
                       count: int, price: int) -> Listing:
        raise NotImplementedError("待 Inventory 与交易事务逻辑落地后实现")

    def cancel_listing(self, listing_id: str, requester_id: str) -> None:
        listing = self.get_listing(listing_id)
        if listing.status != "active":
            raise BusinessRuleError(message=f"挂单 {listing_id} 当前不可撤销", listing_id=listing_id)
        if listing.seller_id != requester_id:
            raise BusinessRuleError(message="只能撤销自己的挂单",
                                    listing_id=listing_id, requester_id=requester_id)
        listing.status = "cancelled"
        self.persistence.save_market(self.repo)
        log.info("market", "listing_cancelled", listing_id=listing_id, requester_id=requester_id)

    def list_active(self, sort_by: str = "created_at",
                    desc: bool = False) -> list[Listing]:
        listings = [l for l in self.repo.listings.values() if l.status == "active"]
        if sort_by == "created_at":
            key = lambda l: l.created_at
        elif sort_by == "price":
            key = lambda l: l.price
        else:
            raise InvalidInputError(field="sort_by", value=sort_by)
        return sorted(listings, key=key, reverse=desc)

    def query_by_price_range(self, min_price: int,
                             max_price: int) -> list[Listing]:
        return [
            l for l in self.repo.listings.values()
            if l.status == "active" and min_price <= l.price <= max_price
        ]

    def query_by_category(self, category_prefix: str) -> list[Listing]:
        item_ids = {
            item_id for item_id, item in self.repo.items.items()
            if item.get("category", "").startswith(category_prefix)
        }
        return [
            l for l in self.repo.listings.values()
            if l.status == "active" and l.item_id in item_ids
        ]

    def query_by_seller(self, seller_id: str) -> list[Listing]:
        return [
            l for l in self.repo.listings.values()
            if l.status == "active" and l.seller_id == seller_id
        ]

    def get_listing(self, listing_id: str) -> Listing:
        listing = self.repo.listings.get(listing_id)
        if listing is None:
            raise ListingNotFoundError(listing_id=listing_id)
        return listing

    def buy(self, listing_id: str, buyer_id: str):
        raise NotImplementedError("待交易事务与回滚逻辑落地后实现")

    def settle_pending(self, listing_ids: list[str]):
        raise NotImplementedError("待 Queue 与批量结算逻辑落地后实现")
