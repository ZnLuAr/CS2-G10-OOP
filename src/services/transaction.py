"""交易记录与报表服务"""

from __future__ import annotations

from collections import defaultdict

from src.errors import InvalidInputError
from src.models import Player, Transaction
from src.services.logger import log
from src.services.persistence import Persistence, Repository

__all__ = ["TransactionService"]




class TransactionService:
    def __init__(self, repo: Repository, persistence: Persistence) -> None:
        self.repo = repo
        self.persistence = persistence

    def append(self, txn: Transaction) -> None:
        self.repo.transactions.append(txn)
        self.persistence.save_transactions(self.repo)
        log.info("transaction", "appended", transaction_id=txn.transaction_id)

    def by_player(self, player_id: str, role: str = "both") -> list[Transaction]:
        if role not in {"buyer", "seller", "both"}:
            raise InvalidInputError(field="role", value=role)

        txns = []
        for txn in self.repo.transactions:
            if role == "buyer" and txn.buyer_id == player_id:
                txns.append(txn)
            elif role == "seller" and txn.seller_id == player_id:
                txns.append(txn)
            elif role == "both" and (txn.buyer_id == player_id or txn.seller_id == player_id):
                txns.append(txn)
        return sorted(txns, key=lambda t: t.completed_at, reverse=True)

    def by_item(self, item_id: str) -> list[Transaction]:
        txns = [t for t in self.repo.transactions if t.item_id == item_id]
        return sorted(txns, key=lambda t: t.completed_at, reverse=True)

    def price_stats(self, item_id: str) -> dict:
        txns = self.by_item(item_id)
        if not txns:
            raise InvalidInputError(field="item_id", value=item_id, reason="no transactions")
        prices = [t.price for t in txns]
        return {
            "min": min(prices),
            "max": max(prices),
            "avg": sum(prices) / len(prices),
            "count": len(prices),
        }

    def top_by_gold(self, n: int = 10) -> list[Player]:
        return sorted(self.repo.players.values(), key=lambda p: p.gold, reverse=True)[:n]

    def top_by_volume(self, n: int = 10) -> list[tuple[Player, int]]:
        volume: dict[str, int] = defaultdict(int)
        for txn in self.repo.transactions:
            volume[txn.buyer_id] += txn.total
            volume[txn.seller_id] += txn.total

        ranked = [
            (player, volume[player.player_id])
            for player in self.repo.players.values()
            if player.player_id in volume
        ]
        ranked.sort(key=lambda pair: pair[1], reverse=True)
        return ranked[:n]

    def snapshot(self) -> dict:
        return {
            "players": len(self.repo.players),
            "items": len(self.repo.items),
            "active_listings": sum(1 for l in self.repo.listings.values() if l.status == "active"),
            "total_volume": sum(t.total for t in self.repo.transactions),
        }
