"""数据持久化服务（功能 ID 1-3 + 53）。

职责：
- 加载 / 保存 data/*.json
- 维护各实体的 ID 自增计数器
- 加载时做外键完整性校验
- 首次运行检测：data/ 下无业务文件则触发种子生成

约定：
- ``Repository.players / listings / transactions`` 已使用真实模型类
  （Player / Listing / Transaction 的 dataclass）
- ``Repository.items / catalog`` 暂以 dict 承载，等 JIAFENG / XINGZHOU
  的 Item 多态层与 CatalogTree 落地后切换
- 详见 docs/services-interface.md §4
"""

from __future__ import annotations

import json
import os
import re
import shutil
from dataclasses import dataclass, field
from typing import Any, Iterable

from src.errors import (
    DataIntegrityError,
    PersistenceError,
    SerializationError,
)
from src.models import Listing, Player, Transaction
from src.services import seed as _seed


__all__ = ["Persistence", "Repository"]




# ---------------------------------------------------------------------------
# Repository（内存数据中枢）
# ---------------------------------------------------------------------------

@dataclass
class Repository:
    """加载后所有内存数据通过单一对象传递，详见 services-interface.md §4.2。"""

    players: dict[str, Player] = field(default_factory=dict)
    items: dict[str, dict] = field(default_factory=dict)              # 待 Item 模型落地
    listings: dict[str, Listing] = field(default_factory=dict)
    transactions: list[Transaction] = field(default_factory=list)
    catalog: dict[str, Any] = field(default_factory=dict)             # 待 CatalogTree 落地




# ---------------------------------------------------------------------------
# Persistence （持久化）
# ---------------------------------------------------------------------------

_BUSINESS_FILES = ("players.json", "items.json", "market.json",
                   "transactions.json", "catalog.json")
_ID_PATTERN = re.compile(r"^([a-z]+)_(\d+)$")


class Persistence:
    """加载 / 保存全部 JSON 数据，并维护 ID 自增计数器。

    单例风格使用：启动时构造一次，挂在 ``App`` 上。
    """

    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = data_dir
        self.backup_dir = os.path.join(data_dir, "backup")
        # ID 计数器；load_all 时会刷新到当前最大值
        self._counters: dict[str, int] = {"p": 0, "i": 0, "l": 0, "t": 0}


    # =====================================================================
    # 路径工具
    # =====================================================================

    def _path(self, filename: str) -> str:
        return os.path.join(self.data_dir, filename)

    def _has_any_business_file(self) -> bool:
        return any(os.path.exists(self._path(f)) for f in _BUSINESS_FILES)


    # =====================================================================
    # 首次运行：种子
    # =====================================================================

    def seed_if_empty(self) -> bool:
        """若 data/ 下无业务文件则生成种子数据集。# persists

        Returns: 是否触发了种子生成（True = 触发）
        """
        if self._has_any_business_file():
            return False
        os.makedirs(self.data_dir, exist_ok=True)
        seed = _seed.generate_seed()
        self._write_json(self._path("catalog.json"), seed["catalog"])
        self._write_json(self._path("items.json"), {"items": seed["items"]})
        self._write_json(self._path("players.json"), {"players": seed["players"]})
        self._write_json(self._path("market.json"), {"listings": seed["listings"]})
        self._write_json(self._path("transactions.json"),
                         {"transactions": seed["transactions"]})
        return True


    # =====================================================================
    # 加载
    # =====================================================================

    def load_all(self) -> Repository:
        """从 data/*.json 加载全部数据。# mutates self（刷新 ID 计数器）

        Raises:
            PersistenceError: 文件读取失败
            SerializationError: JSON 反序列化失败
            DataIntegrityError: 外键完整性校验失败
        """
        repo = Repository()

        catalog_raw = self._read_json(self._path("catalog.json"),
                                      default={"root": {}})
        repo.catalog = catalog_raw if isinstance(catalog_raw, dict) else {}

        # Item 暂保留 dict
        repo.items = self._index_dicts(
            self._read_list(self._path("items.json"), key="items"),
            id_field="item_id",
            entity="Item",
        )

        # Player / Listing / Transaction 反序列化为模型类
        repo.players = self._index_models(
            self._read_list(self._path("players.json"), key="players"),
            from_dict=Player.from_dict,
            id_attr="player_id",
            entity="Player",
        )
        repo.listings = self._index_models(
            self._read_list(self._path("market.json"), key="listings"),
            from_dict=Listing.from_dict,
            id_attr="listing_id",
            entity="Listing",
        )
        repo.transactions = [
            self._build_model(rec, Transaction.from_dict, "Transaction")
            for rec in self._read_list(self._path("transactions.json"),
                                       key="transactions")
        ]

        self._refresh_counters(repo)
        self._validate_integrity(repo)
        return repo


    # =====================================================================
    # 保存
    # =====================================================================

    def save_players(self, repo: Repository) -> None:  # persists
        self._write_with_backup(
            self._path("players.json"),
            {"players": [p.to_dict() for p in repo.players.values()]},
        )

    def save_items(self, repo: Repository) -> None:  # persists
        self._write_with_backup(self._path("items.json"),
                                {"items": list(repo.items.values())})

    def save_market(self, repo: Repository) -> None:  # persists
        self._write_with_backup(
            self._path("market.json"),
            {"listings": [l.to_dict() for l in repo.listings.values()]},
        )

    def save_transactions(self, repo: Repository) -> None:  # persists
        self._write_with_backup(
            self._path("transactions.json"),
            {"transactions": [t.to_dict() for t in repo.transactions]},
        )

    def save_catalog(self, repo: Repository) -> None:  # persists
        self._write_with_backup(self._path("catalog.json"), repo.catalog)

    def save_all(self, repo: Repository) -> None:  # persists
        self.save_catalog(repo)
        self.save_items(repo)
        self.save_players(repo)
        self.save_market(repo)
        self.save_transactions(repo)


    # =====================================================================
    # ID 分配
    # =====================================================================

    def next_player_id(self) -> str:
        return self._next("p", width=3)

    def next_item_id(self) -> str:
        return self._next("i", width=3)

    def next_listing_id(self) -> str:
        return self._next("l", width=3)

    def next_transaction_id(self) -> str:
        return self._next("t", width=3)

    def _next(self, prefix: str, width: int) -> str:
        self._counters[prefix] += 1
        return f"{prefix}_{self._counters[prefix]:0{width}d}"


    # =====================================================================
    # 备份 / 重置
    # =====================================================================

    def backup_before_save(self, path: str) -> None:
        """保存前将旧文件备份为 data/backup/<name>.bak（功能 ID 51）。"""
        if not os.path.exists(path):
            return
        os.makedirs(self.backup_dir, exist_ok=True)
        bak = os.path.join(self.backup_dir, os.path.basename(path) + ".bak")
        try:
            shutil.copy2(path, bak)
        except OSError as e:
            raise PersistenceError(path=bak, op="backup") from e

    def reset(self) -> None:
        """删除全部业务 JSON 文件（功能 ID 53）。"""
        for fname in _BUSINESS_FILES:
            p = self._path(fname)
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError as e:
                    raise PersistenceError(path=p, op="delete") from e


    # =====================================================================
    # 内部辅助 - I/O
    # =====================================================================

    def _read_json(self, path: str, default: Any) -> Any:
        if not os.path.exists(path):
            return default
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except OSError as e:
            raise PersistenceError(path=path, op="read") from e
        except json.JSONDecodeError as e:
            raise SerializationError(entity=os.path.basename(path),
                                     raw=str(e)) from e

    def _read_list(self, path: str, key: str) -> list[dict]:
        data = self._read_json(path, default={key: []})
        if not isinstance(data, dict) or key not in data:
            raise SerializationError(entity=key, raw=f"缺少顶层键 {key!r}")
        items = data[key]
        if not isinstance(items, list):
            raise SerializationError(
                entity=key,
                raw=f"{key!r} 应为 list，实际为 {type(items).__name__}",
            )
        return items

    def _write_json(self, path: str, payload: Any) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except OSError as e:
            raise PersistenceError(path=path, op="write") from e

    def _write_with_backup(self, path: str, payload: Any) -> None:
        self.backup_before_save(path)
        self._write_json(path, payload)


    # =====================================================================
    # 内部辅助 - 反序列化
    # =====================================================================

    @staticmethod
    def _index_dicts(records: Iterable[dict], id_field: str,
                     entity: str) -> dict[str, dict]:
        result: dict[str, dict] = {}
        for rec in records:
            if not isinstance(rec, dict) or id_field not in rec:
                raise SerializationError(entity=entity, raw=rec)
            result[rec[id_field]] = rec
        return result

    @staticmethod
    def _build_model(rec: dict, from_dict, entity: str):
        if not isinstance(rec, dict):
            raise SerializationError(entity=entity, raw=rec)
        try:
            return from_dict(rec)
        except (KeyError, TypeError, ValueError) as e:
            raise SerializationError(entity=entity, raw=rec) from e

    @classmethod
    def _index_models(cls, records: Iterable[dict], from_dict,
                      id_attr: str, entity: str) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for rec in records:
            obj = cls._build_model(rec, from_dict, entity)
            result[getattr(obj, id_attr)] = obj
        return result


    # =====================================================================
    # 内部辅助 - ID 计数器
    # =====================================================================

    def _refresh_counters(self, repo: Repository) -> None:
        self._counters["p"] = self._max_id(repo.players.keys())
        self._counters["i"] = self._max_id(repo.items.keys())
        self._counters["l"] = self._max_id(repo.listings.keys())
        self._counters["t"] = self._max_id(t.transaction_id
                                           for t in repo.transactions)

    @staticmethod
    def _max_id(ids: Iterable[str]) -> int:
        max_n = 0
        for x in ids:
            m = _ID_PATTERN.match(x or "")
            if m:
                max_n = max(max_n, int(m.group(2)))
        return max_n


    # =====================================================================
    # 完整性校验（功能 ID 3）
    # =====================================================================

    def _validate_integrity(self, repo: Repository) -> None:
        """加载时校验外键完整性。

        硬错误（直接抛 DataIntegrityError）：
        - 玩家背包引用了不存在的物品
        - 挂单引用了不存在的卖家 / 物品
        - 交易引用了不存在的玩家 / 物品

        软警告（打印不抛）：
        - 交易引用了不存在的挂单（挂单可能已被清理，历史仍要保留）
        """
        item_ids = set(repo.items.keys())
        player_ids = set(repo.players.keys())
        listing_ids = set(repo.listings.keys())

        for pid, p in repo.players.items():
            for slot in p.inventory:
                if slot.get("item_id") not in item_ids:
                    raise DataIntegrityError(
                        entity=f"Player[{pid}].inventory",
                        ref_id=str(slot.get("item_id")),
                    )

        for lid, listing in repo.listings.items():
            if listing.seller_id not in player_ids:
                raise DataIntegrityError(
                    entity=f"Listing[{lid}].seller_id",
                    ref_id=listing.seller_id,
                )
            if listing.item_id not in item_ids:
                raise DataIntegrityError(
                    entity=f"Listing[{lid}].item_id",
                    ref_id=listing.item_id,
                )

        for txn in repo.transactions:
            tid = txn.transaction_id
            if txn.buyer_id not in player_ids:
                raise DataIntegrityError(
                    entity=f"Transaction[{tid}].buyer_id",
                    ref_id=txn.buyer_id,
                )
            if txn.seller_id not in player_ids:
                raise DataIntegrityError(
                    entity=f"Transaction[{tid}].seller_id",
                    ref_id=txn.seller_id,
                )
            if txn.item_id not in item_ids:
                raise DataIntegrityError(
                    entity=f"Transaction[{tid}].item_id",
                    ref_id=txn.item_id,
                )
            if txn.listing_id not in listing_ids:
                # 软警告：暂以 print 替代日志，等 logger 落地后改为 log.warn
                print(f"[WARN] transaction {tid} references "
                      f"unknown listing {txn.listing_id!r}")
