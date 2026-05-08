"""数据管理菜单测试（功能 ID 49-53）

测试数据管理子菜单的各项功能：
- 立即保存所有数据
- 查看数据统计
- 重置所有数据（危险操作）
"""

from __future__ import annotations

import sys

import pytest

from src.app import App
from src.services.persistence import Persistence
from src.ui.cli import TradingCLI


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def fresh_cli(tmp_path):
    """提供已 bootstrap 的 CLI 实例（使用临时数据目录）"""
    data_dir = str(tmp_path / "data")
    persistence = Persistence(data_dir=data_dir)
    persistence.seed_if_empty()
    app = App(persistence=persistence)
    app.bootstrap()
    return TradingCLI(app)


@pytest.fixture
def mock_input(monkeypatch):
    """工厂函数：创建模拟输入序列"""
    def _make(*inputs: str):
        gen = iter(inputs)
        def _input_fn(prompt: str = "") -> str:
            try:
                return next(gen)
            except StopIteration:
                return "7"  # 默认退出
        monkeypatch.setattr("builtins.input", _input_fn)
    return _make


# -----------------------------------------------------------------------------
# 数据管理菜单测试
# -----------------------------------------------------------------------------

class TestDataMenu:
    """数据管理菜单功能测试"""

    def test_data_menu_save_all(self, fresh_cli, mock_input, capsys):
        """验证立即保存菜单功能（功能 ID 49）"""
        # 6=数据管理, 1=立即保存, 回车, b=返回, 回车, 7=退出
        mock_input("6", "1", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "所有数据已保存" in out
        assert "players.json" in out
        assert "items.json" in out

    def test_data_menu_show_stats(self, fresh_cli, mock_input, capsys):
        """验证数据统计显示（功能 ID 49）"""
        # 6=数据管理, 2=查看数据统计, 回车, b=返回, 回车, 7=退出
        mock_input("6", "2", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "数据统计" in out
        assert "players.json" in out
        assert "数据目录" in out
        assert "玩家数" in out
        assert "物品数" in out

    def test_data_menu_reset_cancel_first_confirm(self, fresh_cli, mock_input, capsys):
        """验证重置第一次确认取消（功能 ID 53）"""
        # 6=数据管理, 3=重置, no=取消, 回车, b=返回, 回车, 7=退出
        mock_input("6", "3", "no", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "已取消" in out

    def test_data_menu_reset_cancel_second_confirm(self, fresh_cli, mock_input, capsys):
        """验证重置第二次确认取消（功能 ID 53）"""
        # 6=数据管理, 3=重置, yes=第一次确认, wrong=第二次输入错误, 回车, b=返回, 回车, 7=退出
        mock_input("6", "3", "yes", "wrong", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "已取消" in out

    def test_data_menu_reset_exits_program(self, fresh_cli, mock_input, monkeypatch, capsys):
        """验证重置后退出程序（功能 ID 53）"""
        # 6=数据管理, 3=重置, yes=第一次确认, RESET=第二次确认
        mock_input("6", "3", "yes", "RESET")

        with pytest.raises(SystemExit) as exc_info:
            fresh_cli.run()

        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "数据已重置" in out

    def test_data_menu_reset_files_actually_deleted(self, fresh_cli, mock_input, tmp_path):
        """重置后业务 JSON 文件应在磁盘上真的被删除（功能 ID 53）

        回归保护：避免重新引入"reset 后 atexit 把数据写回"的 bug。
        """
        import os
        data_dir = fresh_cli.persistence.data_dir
        business_files = ["players.json", "items.json", "market.json",
                          "transactions.json", "catalog.json"]

        # 重置前：所有业务文件都存在
        for fname in business_files:
            assert os.path.exists(os.path.join(data_dir, fname)), \
                f"前置条件失败：{fname} 应在重置前存在"

        mock_input("6", "3", "yes", "RESET")
        with pytest.raises(SystemExit):
            fresh_cli.run()

        # 重置后：业务文件应全部消失
        for fname in business_files:
            assert not os.path.exists(os.path.join(data_dir, fname)), \
                f"{fname} 在重置后仍然存在 —— atexit 可能错误地将其写回"

    def test_data_menu_reset_atexit_does_not_rewrite_files(self, fresh_cli, mock_input):
        """重置后即便手动触发 App.shutdown()（模拟 atexit 钩子），文件也不应被写回。

        关键回归测试：原 bug 表现为
            - persistence.reset() 删掉了文件
            - 但 atexit 注册的 shutdown 又调用 save_all 把它们全部写回
        修复方式是 App._skip_save_on_exit 标志位由 DataHandler.reset_all() 设置。
        本测试在 SystemExit 抛出后显式调用 shutdown()，验证标志位生效。
        """
        import os
        data_dir = fresh_cli.persistence.data_dir
        business_files = ["players.json", "items.json", "market.json",
                          "transactions.json", "catalog.json"]

        mock_input("6", "3", "yes", "RESET")
        with pytest.raises(SystemExit):
            fresh_cli.run()

        # 模拟 atexit 钩子触发
        fresh_cli.app.shutdown()

        # 文件应保持已删除状态
        for fname in business_files:
            assert not os.path.exists(os.path.join(data_dir, fname)), \
                f"shutdown() 把 {fname} 写回来了，_skip_save_on_exit 标志位未生效"

        # 验证标志位确实被设置
        assert fresh_cli.app._skip_save_on_exit is True

    def test_data_menu_back_to_main(self, fresh_cli, mock_input, capsys):
        """验证数据管理菜单返回主菜单"""
        # 6=数据管理, b=返回, 回车, 7=退出
        mock_input("6", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        # 应该看到主菜单
        assert "主  菜  单" in out or "主菜单" in out
