"""Player 数据模型（字段容器 + JSON 互转）。

字段定义见 docs/data-design.md §3。
本类目前只承载字段；业务方法（add_gold / spend_gold / 删除前校验等）
留待 ``services/player_service.py`` 的负责人实现。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from typing import Any, Dict, List

from errors import PlayerNotFoundError

from services.persistence import Persistence

from services.persistence import Repository

from src.structures.hash_map import hash_map

from src.errors import InsufficientGoldError, InvalidInputError

__all__ = ["Player"]


@dataclass
class Player:
    player_id: str
    name: str
    gold: int
    level: int
    klass: str                              # JSON 字段名为 'class'，Python 关键字回避
    inventory: list[dict] = field(default_factory=list)  # 暂为 dict 列表，等 InventorySlot 落地
    created_at: str = ""

    def add_gold(self, amount: int) -> None:
        if amount < 0:
            raise InvalidInputError("The number of gold(beryl) can not be negative")
        else:
            self.gold += amount

    def spend_gold(self, amount: int) -> None:
        if amount < 0:
            raise InvalidInputError("The number of gold(beryl) can not be negative")
        else:
            if self.gold < amount:
                raise InsufficientGoldError
            else:
                self.gold -= amount

    def rename_player(self, new_name: str) -> None:
        if not (1 <= len(new_name) <= 20):
            raise InvalidInputError("The player name can only contain 1 to 20 characters")
        self.name = new_name



    @classmethod
    def from_dict(cls, d: dict) -> "Player":
        return cls(
            player_id=d["player_id"],
            name=d["name"],
            gold=d["gold"],
            level=d["level"],
            klass=d["class"],
            inventory=list(d.get("inventory", [])),
            created_at=d.get("created_at", ""),
        )

    def to_dict(self) -> dict:
        return {
            "player_id": self.player_id,
            "name": self.name,
            "gold": self.gold,
            "level": self.level,
            "class": self.klass,
            "inventory": list(self.inventory),
            "created_at": self.created_at,
        }

class PlayerService:
    def __init__(self, repo: 'Repository', persistence: 'Persistence') -> None:
        self._repo = repo
        self._persistence = persistence


        self._players_hash = hash_map()

    def creat(self, name: str, initial_gold: int = 0,
              level: int = 1, klass: str = 'none') -> None:
        if not (1 <= len(name) <= 20):
            raise InvalidInputError("The player name can only contain 1 to 20 characters")
        if initial_gold < 0:
            raise InvalidInputError("The initial gold can not be negative")

        new_id = self._persistence.next_player_id()

        player = Player(
            player_id=new_id,
            name=name,
            gold=initial_gold,
            level=level,
            klass=klass,
        )
        self._repo.players[new_id] = player
        self._persistence.save_players(self._repo)
        return player

    def get_player(self, player_id: str) -> Player:
        if player_id not in self._repo.players:
            raise PlayerNotFoundError(player_id)

        return self._repo.players[player_id]

    def get_player_by_name(self, key: str) -> Player:   #Fuzzy search by player name
        key_lower = key.lower()
        for p in self._repo.players.values():
            if key_lower in p.name.lower():
                return p
        return None

    def list_all(self, sort_by: str) -> list[Player]:
        players = list(self._repo.players.values())
        if sort_by == 'gold':
            players.sort(key=lambda p: p.gold, reverse=True)
        elif sort_by == 'name':
            players.sort(key=lambda p: p.name, reverse=True)
        else:
            players.sort(key=lambda p: p.id, reverse=True)

        return players

    def get_details(self, player_id: str) -> Dict[str, Any]:
        player = self.get_player(player_id)
        active_listings = [
            l for l in self._repo.listings.values()
            if l.seller_id == player_id and l.status == "active"
        ]

        transactions = [
            t for t in self._repo.transactions
            if t.buyer_id == player_id or t.seller_id == player_id
        ]
        transactions.sort(key=lambda t: t.completed_at, reverse=True)

        return {
            "basic": player.to_dict(),
            "inventory": player.inventory,
            "active_listings": [l.to_dict() for l in active_listings],
            "transactions": [t.to_dict() for t in transactions[:10]],
        }

    def rename_player(self, player_id: str, new_name: str) -> None:
        player = self.get_player(player_id)
        player.rename_player(new_name)
        self._persistence.save_players(self._repo)

    def remove_player(self, player_id: str) -> None:
        player = self.get_player(player_id)
        active_listings = [l for l in self._repo.listings.values() if l.status == "active"]
        if player.inventory:
            raise ValueError()

        if active_listings:
            raise ValueError()

        del self._repo.players[player_id]
        self._persistence.save_players(self._repo)

    def add_gold(self, player_id:str, amount: int) -> None:
        player = self.get_player(player_id)
        player.add_gold(amount)
        self._persistence.save_players(self._repo)

    def spend_gold(self, player_id: str, amount: int) -> None:
        player = self.get_player(player_id)
        player.spend_gold(amount)
        self._persistence.save_players(self._repo)



