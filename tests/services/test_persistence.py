"""Persistence 单元测试。

覆盖 docs/功能列表.csv 的：
- ID 1 首次运行初始化（seed）
- ID 2 数据加载 / 保存往返
- ID 3 数据完整性校验
- ID 49-53 持久化相关
"""

from __future__ import annotations

import json
import os

import pytest

from src.errors import (
    DataIntegrityError,
    PersistenceError,
    SerializationError,
)
from src.models import Listing, Player, Transaction
from src.services.persistence import Persistence, Repository




# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def data_dir(tmp_path):
    return str(tmp_path / "data")


@pytest.fixture
def fresh_persistence(data_dir):
    p = Persistence(data_dir=data_dir)
    p.seed_if_empty()
    return p




# ---------------------------------------------------------------------------
# 1. 首次运行 → 种子
# ---------------------------------------------------------------------------

class TestSeedIfEmpty:
    def test_first_run_creates_all_business_files(self, data_dir):
        p = Persistence(data_dir=data_dir)
        assert p.seed_if_empty() is True
        for name in ("players.json", "items.json", "market.json",
                     "transactions.json", "catalog.json"):
            assert os.path.exists(os.path.join(data_dir, name))

    def test_idempotent_when_files_exist(self, data_dir):
        p = Persistence(data_dir=data_dir)
        p.seed_if_empty()
        # 第二次调用不应覆盖
        assert p.seed_if_empty() is False

    def test_seed_meets_minimum_size(self, fresh_persistence):
        repo = fresh_persistence.load_all()
        assert len(repo.players) >= 10
        assert len(repo.items) >= 50
        assert len(repo.listings) >= 20




# ---------------------------------------------------------------------------
# 2. 加载 → 模型类型正确
# ---------------------------------------------------------------------------

class TestLoadAll:
    def test_returns_repository(self, fresh_persistence):
        repo = fresh_persistence.load_all()
        assert isinstance(repo, Repository)

    def test_players_are_player_instances(self, fresh_persistence):
        repo = fresh_persistence.load_all()
        for p in repo.players.values():
            assert isinstance(p, Player)
            assert p.player_id.startswith("p_")
            assert isinstance(p.gold, int)

    def test_listings_are_listing_instances(self, fresh_persistence):
        repo = fresh_persistence.load_all()
        for l in repo.listings.values():
            assert isinstance(l, Listing)

    def test_items_remain_dicts_pending_model(self, fresh_persistence):
        # Item 模型未实现，Persistence 暂保留 dict
        repo = fresh_persistence.load_all()
        for it in repo.items.values():
            assert isinstance(it, dict)
            assert "item_id" in it and "category" in it




# ---------------------------------------------------------------------------
# 3. 保存 → 加载 等价（往返）
# ---------------------------------------------------------------------------

class TestRoundTrip:
    def test_save_then_load_preserves_players(self, fresh_persistence):
        repo1 = fresh_persistence.load_all()
        fresh_persistence.save_all(repo1)
        repo2 = fresh_persistence.load_all()
        assert set(repo1.players.keys()) == set(repo2.players.keys())
        for pid in repo1.players:
            assert repo1.players[pid].to_dict() == repo2.players[pid].to_dict()

    def test_save_then_load_preserves_listings(self, fresh_persistence):
        repo1 = fresh_persistence.load_all()
        fresh_persistence.save_all(repo1)
        repo2 = fresh_persistence.load_all()
        for lid in repo1.listings:
            assert repo1.listings[lid].to_dict() == repo2.listings[lid].to_dict()




# ---------------------------------------------------------------------------
# 4. ID 自增
# ---------------------------------------------------------------------------

class TestIdCounters:
    def test_counters_initialized_to_max_existing(self, fresh_persistence):
        repo = fresh_persistence.load_all()
        max_p = max(int(pid.split("_")[1]) for pid in repo.players)
        next_pid = fresh_persistence.next_player_id()
        assert int(next_pid.split("_")[1]) == max_p + 1

    def test_consecutive_calls_increment(self, fresh_persistence):
        fresh_persistence.load_all()
        a = fresh_persistence.next_item_id()
        b = fresh_persistence.next_item_id()
        assert int(b.split("_")[1]) == int(a.split("_")[1]) + 1

    def test_each_entity_has_independent_counter(self, fresh_persistence):
        fresh_persistence.load_all()
        # 不同前缀互不干扰
        assert fresh_persistence.next_transaction_id().startswith("t_")
        assert fresh_persistence.next_player_id().startswith("p_")




# ---------------------------------------------------------------------------
# 5. 完整性校验
# ---------------------------------------------------------------------------

class TestIntegrityCheck:
    def _corrupt(self, path: str, mutator):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        mutator(data)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def test_inventory_references_unknown_item(self, fresh_persistence, data_dir):
        # 把第一个玩家的背包塞个不存在的 item_id
        def mutator(d):
            d["players"][0]["inventory"].append({"item_id": "i_999999", "count": 1})
        self._corrupt(os.path.join(data_dir, "players.json"), mutator)
        with pytest.raises(DataIntegrityError) as exc:
            fresh_persistence.load_all()
        assert exc.value.context["ref_id"] == "i_999999"

    def test_listing_references_unknown_seller(self, fresh_persistence, data_dir):
        def mutator(d):
            d["listings"][0]["seller_id"] = "p_999999"
        self._corrupt(os.path.join(data_dir, "market.json"), mutator)
        with pytest.raises(DataIntegrityError):
            fresh_persistence.load_all()

    def test_listing_references_unknown_item(self, fresh_persistence, data_dir):
        def mutator(d):
            d["listings"][0]["item_id"] = "i_999999"
        self._corrupt(os.path.join(data_dir, "market.json"), mutator)
        with pytest.raises(DataIntegrityError):
            fresh_persistence.load_all()

    def test_transaction_references_unknown_listing_only_warns(self, fresh_persistence, data_dir, capsys):
        def mutator(d):
            d["transactions"].append({
                "transaction_id": "t_900001",
                "listing_id": "l_999999",
                "buyer_id": "p_001",
                "seller_id": "p_002",
                "item_id": "i_001",
                "count": 1,
                "price": 100,
                "total": 100,
                "completed_at": "2026-04-22T00:00:00Z",
            })
        self._corrupt(os.path.join(data_dir, "transactions.json"), mutator)
        repo = fresh_persistence.load_all()
        assert repo is not None
        err = capsys.readouterr().err
        assert "txn_references_missing_listing" in err


# ---------------------------------------------------------------------------
# 6. 错误路径
# ---------------------------------------------------------------------------

class TestErrorPaths:
    def test_malformed_json_raises_serialization_error(self, data_dir):
        os.makedirs(data_dir, exist_ok=True)
        # 写一个合法的最小 catalog 与其它文件，但把 players.json 写成坏 JSON
        for name in ("catalog.json", "items.json", "market.json",
                     "transactions.json"):
            with open(os.path.join(data_dir, name), "w", encoding="utf-8") as f:
                if name == "catalog.json":
                    f.write('{"root": {}}')
                else:
                    key = {"items.json": "items", "market.json": "listings",
                           "transactions.json": "transactions"}[name]
                    f.write(json.dumps({key: []}))
        with open(os.path.join(data_dir, "players.json"), "w", encoding="utf-8") as f:
            f.write("{ this is not json")

        p = Persistence(data_dir=data_dir)
        with pytest.raises(SerializationError):
            p.load_all()

    def test_missing_top_level_key_raises_serialization_error(self, data_dir):
        os.makedirs(data_dir, exist_ok=True)
        with open(os.path.join(data_dir, "players.json"), "w", encoding="utf-8") as f:
            json.dump({"wrong_key": []}, f)
        p = Persistence(data_dir=data_dir)
        with pytest.raises(SerializationError):
            p.load_all()




# ---------------------------------------------------------------------------
# 7. 备份与重置
# ---------------------------------------------------------------------------

class TestBackupAndReset:
    def test_backup_created_on_save(self, fresh_persistence, data_dir):
        repo = fresh_persistence.load_all()
        fresh_persistence.save_players(repo)  # 第一次：原文件存在 → 应产生备份
        bak = os.path.join(data_dir, "backup", "players.json.bak")
        assert os.path.exists(bak)

    def test_reset_removes_business_files(self, fresh_persistence, data_dir):
        fresh_persistence.reset()
        for name in ("players.json", "items.json", "market.json",
                     "transactions.json", "catalog.json"):
            assert not os.path.exists(os.path.join(data_dir, name))
