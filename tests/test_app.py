"""App 生命周期测试。

验证 docs/功能列表.csv 的：
- ID 1 首次运行触发种子（透传 Persistence）
- ID 2 加载（bootstrap 后 repo 已填充）
- ID 4 优雅退出（正常 / Ctrl+C / 未预期异常 都会触发保存）
- ID 5 启动横幅（含程序名 / 版本 / 数据规模）
"""

from __future__ import annotations

import io

import pytest

from src.app import App, PROGRAM_NAME, VERSION
from src.errors import DataIntegrityError
from src.services.persistence import Persistence




@pytest.fixture
def app(tmp_path):
    return App(persistence=Persistence(data_dir=str(tmp_path / "data")))


# ---------------------------------------------------------------------------
# bootstrap
# ---------------------------------------------------------------------------

class TestBootstrap:
    def test_first_run_seeds_and_loads(self, app):
        repo = app.bootstrap()
        assert repo is not None
        assert len(repo.players) > 0
        assert len(repo.items) > 0

    def test_second_run_does_not_re_seed(self, app, tmp_path):
        app.bootstrap()
        # 重新构造 App，使用同一 data_dir，应当直接加载现有数据
        app2 = App(persistence=Persistence(data_dir=str(tmp_path / "data")))
        repo2 = app2.bootstrap()
        assert len(repo2.players) > 0


# ---------------------------------------------------------------------------
# 启动横幅
# ---------------------------------------------------------------------------

class TestBanner:
    def test_banner_includes_name_version_and_counts(self, app, capsys):
        app.bootstrap()
        app.show_banner()
        out = capsys.readouterr().out
        assert PROGRAM_NAME in out
        assert VERSION in out
        assert "玩家" in out and "物品" in out and "挂单" in out


# ---------------------------------------------------------------------------
# shutdown / atexit
# ---------------------------------------------------------------------------

class TestShutdown:
    def test_shutdown_is_idempotent(self, app):
        app.bootstrap()
        app.shutdown()
        app.shutdown()  # 再来一次不应抛

    def test_shutdown_writes_files(self, app, tmp_path):
        app.bootstrap()
        # 删掉文件后 shutdown 应重新写出来
        import os
        target = os.path.join(str(tmp_path / "data"), "players.json")
        os.remove(target)
        app.shutdown()
        assert os.path.exists(target)

    def test_shutdown_without_bootstrap_is_noop(self, app):
        # 未 bootstrap 直接退出不应抛
        app.shutdown()

    def test_shutdown_skips_save_when_flag_set(self, app, tmp_path):
        """_skip_save_on_exit 为 True 时 shutdown 不应再保存数据。

        回归保护：避免重新引入"reset 后 atexit 把已删数据写回"的 bug。
        """
        import os
        app.bootstrap()
        data_dir = str(tmp_path / "data")

        # 模拟 DataHandler.reset_all 的语义：先 reset，再设置标志位
        app.persistence.reset()
        app._skip_save_on_exit = True

        # 此时 shutdown 不应把文件写回
        app.shutdown()

        for fname in ["players.json", "items.json", "market.json",
                      "transactions.json", "catalog.json"]:
            assert not os.path.exists(os.path.join(data_dir, fname)), \
                f"{fname} 在标志位置 True 时仍被 shutdown 写回"

    def test_shutdown_default_still_saves(self, app, tmp_path):
        """正常退出（标志位为 False）时 shutdown 仍应保存数据，向后兼容。"""
        import os
        app.bootstrap()
        data_dir = str(tmp_path / "data")
        target = os.path.join(data_dir, "players.json")
        os.remove(target)

        # 默认情况下 _skip_save_on_exit 应为 False
        assert app._skip_save_on_exit is False
        app.shutdown()

        # 文件应被重新写出
        assert os.path.exists(target)


# ---------------------------------------------------------------------------
# run() 主流程：UI runner 注入
# ---------------------------------------------------------------------------

class TestRun:
    def test_normal_run_returns_zero(self, app):
        called = []

        def fake_ui(a):
            called.append(a)
        app.ui_runner = fake_ui
        assert app.run() == 0
        assert called == [app]

    def test_keyboard_interrupt_returns_zero(self, app):
        def interrupt(a):
            raise KeyboardInterrupt
        app.ui_runner = interrupt
        assert app.run() == 0
        # 数据文件应已落盘（bootstrap 已触发种子；shutdown 确保保存）
        assert app.repo is not None

    def test_unexpected_exception_caught_returns_one(self, app, capsys):
        def boom(a):
            raise RuntimeError("UI 炸了")
        app.ui_runner = boom
        assert app.run() == 1
        err = capsys.readouterr().err
        assert "FATAL" in err and "RuntimeError" in err

    def test_trading_system_error_during_bootstrap_returns_two(self, tmp_path):
        # 构造一个已损坏的 data 目录，让 load_all 抛 DataIntegrityError
        import json
        import os
        d = str(tmp_path / "data")
        os.makedirs(d)
        # 最小的 catalog / items / market / transactions
        with open(os.path.join(d, "catalog.json"), "w", encoding="utf-8") as f:
            f.write('{"root": {}}')
        with open(os.path.join(d, "items.json"), "w", encoding="utf-8") as f:
            json.dump({"items": []}, f)
        with open(os.path.join(d, "transactions.json"), "w", encoding="utf-8") as f:
            json.dump({"transactions": []}, f)
        # 玩家背包引用了不存在的 item_id
        with open(os.path.join(d, "players.json"), "w", encoding="utf-8") as f:
            json.dump({"players": [{
                "player_id": "p_001", "name": "X", "gold": 0, "level": 1,
                "class": "none",
                "inventory": [{"item_id": "i_999", "count": 1}],
                "created_at": "2026-04-20T00:00:00Z",
            }]}, f)
        with open(os.path.join(d, "market.json"), "w", encoding="utf-8") as f:
            json.dump({"listings": []}, f)

        app = App(persistence=Persistence(data_dir=d))
        assert app.run() == 2
