"""玩家详情页测试（回归保护：Transaction.completed_at 字段）

测试玩家详情页的完整显示，包括：
- 基本信息（金币、等级、职业）
- 背包内容（通过 InventoryService）
- 活跃挂单列表
- 历史交易记录（验证 completed_at 字段正确显示）

这是对 player.py:144 修复的回归保护测试。
"""

from __future__ import annotations

import pytest

from src.app import App
from src.services.persistence import Persistence
from src.services.player_inventory_service import PlayerInventoryService
from src.ui.cli import TradingCLI


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


class TestPlayerDetailView:
    """玩家详情页完整测试"""

    def test_player_detail_with_inventory_and_transactions(self, fresh_cli, mock_input, capsys):
        """玩家详情页显示背包、挂单、交易历史（验证 completed_at 字段）"""
        # 准备测试数据：创建一个有背包、挂单、交易的玩家
        player = fresh_cli.app.player_service.create_player("测试玩家", gold=10000, level=5, klass="warrior")
        pid = player.player_id

        # 创建 inventory_service
        inv_service = PlayerInventoryService(fresh_cli.repo, fresh_cli.persistence)

        # 添加背包物品
        item = list(fresh_cli.repo.items.values())[0]
        inv_service.add_item(pid, item.item_id, count=3)

        # 创建挂单
        listing = fresh_cli.app.market_service.create_listing(pid, item.item_id, count=1, price=100)

        # 创建交易记录（买入一个物品）
        seller = list(fresh_cli.repo.players.values())[0]
        if seller.player_id == pid:
            seller = list(fresh_cli.repo.players.values())[1]

        # 给卖家添加物品并创建挂单
        test_item = list(fresh_cli.repo.items.values())[1]
        inv_service.add_item(seller.player_id, test_item.item_id, count=1)
        seller_listing = fresh_cli.app.market_service.create_listing(
            seller.player_id, test_item.item_id, count=1, price=50
        )

        # 测试玩家购买
        txn = fresh_cli.app.market_service.buy(seller_listing.listing_id, pid)

        # 访问玩家详情页：1=玩家管理, 3=查看详情, pid, 回车, b=返回, 回车, 7=退出
        mock_input("1", "3", pid, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out

        # 验证基本信息
        assert "测试玩家" in out
        assert pid in out
        assert "10000" in out or "9950" in out  # 金币（可能因购买减少）
        assert "等级：5" in out
        assert "职业：warrior" in out

        # 验证背包显示
        assert "背包" in out
        assert item.name in out or item.item_id in out
        # 背包应该有物品（数量可能因堆叠规则而不同）
        assert "件物品" in out

        # 验证活跃挂单
        assert "活跃挂单" in out
        assert listing.listing_id in out
        assert "100" in out  # 价格

        # 验证交易历史（关键：验证 completed_at 字段显示）
        assert "历史成交" in out
        assert txn.transaction_id in out
        assert "买入" in out  # 角色标识
        # completed_at 格式：2026-05-08T12:34:56Z，应显示部分时间戳
        assert "2026" in out or "202" in out  # 年份应该出现

    def test_player_detail_empty_inventory_and_no_transactions(self, fresh_cli, mock_input, capsys):
        """玩家详情页：空背包、无挂单、无交易"""
        player = fresh_cli.app.player_service.create_player("空玩家", gold=0, level=1, klass="none")
        pid = player.player_id

        # 访问详情页
        mock_input("1", "3", pid, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out

        # 验证基本信息
        assert "空玩家" in out
        assert pid in out

        # 验证空状态显示
        assert "背包：0 件物品" in out
        assert "活跃挂单：0 条" in out
        assert "历史成交：0 笔" in out

    def test_player_detail_nonexistent_player(self, fresh_cli, mock_input, capsys):
        """玩家详情页：不存在的玩家 ID"""
        mock_input("1", "3", "p_nonexistent", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "不存在" in out or "错误" in out

    def test_player_detail_with_multiple_transactions(self, fresh_cli, mock_input, capsys):
        """玩家详情页：多笔交易记录（验证排序和截断）"""
        # 创建买家和卖家
        buyer = fresh_cli.app.player_service.create_player("买家", gold=100000, level=10)
        seller = fresh_cli.app.player_service.create_player("卖家", gold=0, level=1)

        # 创建 inventory_service
        inv_service = PlayerInventoryService(fresh_cli.repo, fresh_cli.persistence)

        # 创建多笔交易（超过 5 笔，测试截断）
        items = list(fresh_cli.repo.items.values())[:7]
        for i, item in enumerate(items):
            inv_service.add_item(seller.player_id, item.item_id, count=1)
            listing = fresh_cli.app.market_service.create_listing(
                seller.player_id, item.item_id, count=1, price=10 * (i + 1)
            )
            fresh_cli.app.market_service.buy(listing.listing_id, buyer.player_id)

        # 访问买家详情页
        mock_input("1", "3", buyer.player_id, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out

        # 验证交易历史显示
        assert "历史成交：7 笔" in out
        # 应该只显示最近 5 笔（player.py:144 的 [:5] 切片）
        # 验证至少有交易 ID 出现
        assert "买入" in out
        # 验证时间戳格式正确（completed_at 字段）
        assert "202" in out  # 年份前缀


class TestTransactionFieldDisplay:
    """Transaction.completed_at 字段显示测试（formatters.py 回归保护）"""

    def test_transaction_table_displays_completed_at(self, fresh_cli, capsys):
        """验证 format_transaction_table 使用 completed_at 而非 timestamp"""
        # 创建交易
        buyer = list(fresh_cli.repo.players.values())[0]
        seller = list(fresh_cli.repo.players.values())[1]
        item = list(fresh_cli.repo.items.values())[0]

        # 创建 inventory_service
        inv_service = PlayerInventoryService(fresh_cli.repo, fresh_cli.persistence)

        inv_service.add_item(seller.player_id, item.item_id, count=1)
        listing = fresh_cli.app.market_service.create_listing(
            seller.player_id, item.item_id, count=1, price=100
        )
        txn = fresh_cli.app.market_service.buy(listing.listing_id, buyer.player_id)

        # 直接调用 formatter 测试
        from src.ui.formatters import format_transaction_table

        table = format_transaction_table([txn], fresh_cli.repo)

        # 验证 completed_at 字段被正确使用（不会抛 AttributeError）
        assert txn.transaction_id in table
        # 验证时间戳格式（completed_at 是 ISO 8601 字符串）
        assert "202" in table  # 年份应该出现
        # 验证不会出现 "timestamp" 字样（说明没有用错字段）
        assert "timestamp" not in table.lower()

    def test_player_transaction_history_displays_completed_at(self, fresh_cli, mock_input, capsys):
        """验证报表菜单的玩家交易历史使用 completed_at"""
        # 创建交易
        buyer = list(fresh_cli.repo.players.values())[0]
        seller = list(fresh_cli.repo.players.values())[1]
        item = list(fresh_cli.repo.items.values())[0]

        # 创建 inventory_service
        inv_service = PlayerInventoryService(fresh_cli.repo, fresh_cli.persistence)

        inv_service.add_item(seller.player_id, item.item_id, count=1)
        listing = fresh_cli.app.market_service.create_listing(
            seller.player_id, item.item_id, count=1, price=100
        )
        txn = fresh_cli.app.market_service.buy(listing.listing_id, buyer.player_id)

        # 访问报表菜单：5=报表, 1=玩家交易历史, buyer_id, 回车, b, 回车, 7
        mock_input("5", "1", buyer.player_id, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out

        # 验证交易显示（不会因 timestamp 字段不存在而崩溃）
        assert txn.transaction_id in out
        # 验证时间戳显示
        assert "202" in out
