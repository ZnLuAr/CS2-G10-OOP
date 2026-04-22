"""玩家服务"""

from __future__ import annotations

from datetime import UTC, datetime

from src.errors import (
    BusinessRuleError,
    InsufficientGoldError,
    InvalidInputError,
    InventoryNotEmptyError,
    PlayerNotFoundError,
)
from src.models import Player
from src.services.logger import log
from src.services.persistence import Persistence, Repository

__all__ = ["PlayerService"]


_VALID_CLASSES = {"warrior", "archer", "mage", "summon", "none"}




class PlayerService:
    def __init__(self, repo: Repository, persistence: Persistence) -> None:
        self.repo = repo
        self.persistence = persistence

    def create_player(self, name: str, gold: int = 0,
                      level: int = 1, klass: str = "none") -> Player:
        self._validate_name(name)
        if gold < 0:
            raise InvalidInputError(field="gold", value=gold)
        if level < 1:
            raise InvalidInputError(field="level", value=level)
        if klass not in _VALID_CLASSES:
            raise InvalidInputError(field="klass", value=klass)

        player = Player(
            player_id=self.persistence.next_player_id(),
            name=name.strip(),
            gold=gold,
            level=level,
            klass=klass,
            inventory=[],
            created_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        self.repo.players[player.player_id] = player
        self.persistence.save_players(self.repo)
        log.info("player", "created", player_id=player.player_id, name=player.name)
        return player

    def get_by_id(self, player_id: str) -> Player:
        player = self.repo.players.get(player_id)
        if player is None:
            raise PlayerNotFoundError(player_id=player_id)
        return player

    def search_by_name(self, keyword: str) -> list[Player]:
        needle = keyword.strip().lower()
        if not needle:
            return []
        return [p for p in self.repo.players.values() if needle in p.name.lower()]

    def list_all(self, sort_by: str = "id", desc: bool = False) -> list[Player]:
        players = list(self.repo.players.values())
        if sort_by == "id":
            key = lambda p: p.player_id
        elif sort_by == "name":
            key = lambda p: p.name.lower()
        elif sort_by == "gold":
            key = lambda p: p.gold
        else:
            raise InvalidInputError(field="sort_by", value=sort_by)
        return sorted(players, key=key, reverse=desc)

    def rename(self, player_id: str, new_name: str) -> None:
        player = self.get_by_id(player_id)
        self._validate_name(new_name)
        player.name = new_name.strip()
        self.persistence.save_players(self.repo)
        log.info("player", "renamed", player_id=player_id, new_name=player.name)

    def add_gold(self, player_id: str, amount: int) -> None:
        player = self.get_by_id(player_id)
        if amount <= 0:
            raise InvalidInputError(field="amount", value=amount)
        player.gold += amount
        self.persistence.save_players(self.repo)
        log.info("player", "gold_added", player_id=player_id, amount=amount)

    def spend_gold(self, player_id: str, amount: int) -> None:
        player = self.get_by_id(player_id)
        if amount <= 0:
            raise InvalidInputError(field="amount", value=amount)
        if player.gold < amount:
            raise InsufficientGoldError(required=amount, available=player.gold)
        player.gold -= amount
        self.persistence.save_players(self.repo)
        log.info("player", "gold_spent", player_id=player_id, amount=amount)

    def delete(self, player_id: str) -> None:
        player = self.get_by_id(player_id)
        if player.inventory:
            raise InventoryNotEmptyError(player_id=player_id)
        if any(l.seller_id == player_id and l.status == "active"
               for l in self.repo.listings.values()):
            raise BusinessRuleError(message=f"玩家 {player_id} 仍有活跃挂单，无法删除",
                                    player_id=player_id)
        del self.repo.players[player_id]
        self.persistence.save_players(self.repo)
        log.info("player", "deleted", player_id=player_id)

    @staticmethod
    def _validate_name(name: str) -> None:
        clean = name.strip()
        if not (1 <= len(clean) <= 20):
            raise InvalidInputError(field="name", value=name)
