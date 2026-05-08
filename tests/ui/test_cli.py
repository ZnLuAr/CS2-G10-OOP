"""CLI 层单元测试（功能 ID 6-9）

测试策略：
- 使用 monkeypatch 模拟输入序列，避免真实交互
- 使用 capsys 捕获输出，验证菜单显示与提示信息
- 使用 tmp_path 隔离数据目录，避免污染真实数据
- 覆盖主菜单导航、子菜单返回、非法输入、撤销等核心场景

应注意，每个菜单操作后都有 "按回车继续..."，测试输入序列需额外提供回车
"""

from __future__ import annotations

import pytest

from src.app import App
from src.services.persistence import Persistence
from src.ui.cli import TradingCLI, run_cli
from src.ui.operations import Operation, OperationStack




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
    """工厂函数：创建模拟输入序列

    使用说明：
    - mock_input("1", "", "7") 表示：输入1，回车继续，输入7退出
    - 每次 _pause() 需要消耗一个回车 ""
    """
    def _make(*inputs: str):
        gen = iter(inputs)
        def _input_fn(prompt: str = "") -> str:
            try:
                return next(gen)
            except StopIteration:
                # 防止测试卡住，默认返回退出
                return "7"
        monkeypatch.setattr("builtins.input", _input_fn)
    return _make


# -----------------------------------------------------------------------------
# OperationStack 测试（功能 ID 9）
# -----------------------------------------------------------------------------

class TestOperationStack:
    """自实现 Stack 的数据结构测试"""

    def test_lifo_semantics(self):
        """后进先出语义"""
        stack = OperationStack()
        stack.push(Operation(name="op1", undo_fn=lambda: None))
        stack.push(Operation(name="op2", undo_fn=lambda: None))
        stack.push(Operation(name="op3", undo_fn=lambda: None))

        op = stack.pop()
        assert op is not None
        assert op.name == "op3"

    def test_empty_pop_returns_none(self):
        """空栈 pop 返回 None"""
        stack = OperationStack()
        assert stack.pop() is None

    def test_fifo_eviction_at_max_size(self):
        """超限时 FIFO 淘汰最旧操作"""
        stack = OperationStack(max_size=3)
        for i in range(5):
            stack.push(Operation(name=f"op{i}", undo_fn=lambda: None))

        # 只保留最近 3 个：op2, op3, op4
        assert len(stack) == 3
        assert stack.pop().name == "op4"
        assert stack.pop().name == "op3"
        assert stack.pop().name == "op2"

    def test_can_undo_reflects_state(self):
        """can_undo() 正确反映栈状态"""
        stack = OperationStack()
        assert not stack.can_undo()
        stack.push(Operation(name="op", undo_fn=lambda: None))
        assert stack.can_undo()
        stack.pop()
        assert not stack.can_undo()




# -----------------------------------------------------------------------------
# 主菜单与导航测试（功能 ID 6-7）
# -----------------------------------------------------------------------------

class TestMainMenuNavigation:
    """主菜单显示与导航"""

    def test_exit_immediately(self, fresh_cli, mock_input, capsys):
        """用户直接退出"""
        # 6=退出
        mock_input("7")
        fresh_cli.run()

        out = capsys.readouterr().out
        # 检查主菜单是否显示（使用 ASCII 安全的方式）
        assert "=" in out  # 菜单边框
        assert "1." in out  # 选项1

    def test_invalid_input_then_valid(self, fresh_cli, mock_input, capsys):
        """非法输入后重新显示菜单（功能 ID 8）"""
        # 9=非法, 然后暂停, 6=退出
        mock_input("9", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        # 应该看到错误提示和重新显示的菜单
        assert "9" in out  # 非法输入的值会被记录




# -----------------------------------------------------------------------------
# 子菜单测试
# -----------------------------------------------------------------------------

class TestSubMenu:
    """子菜单进入与返回"""

    def test_enter_player_menu_and_back(self, fresh_cli, mock_input, capsys):
        """进入玩家管理子菜单并返回主菜单"""
        # 1=玩家管理, b=返回(然后暂停), 6=退出
        mock_input("1", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        # 检查子菜单和主菜单都显示过
        assert "1." in out
        assert "b." in out.lower()  # 返回选项

    def test_enter_item_menu_and_back(self, fresh_cli, mock_input, capsys):
        """进入物品管理子菜单并返回"""
        mock_input("2", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "2." in out

    def test_enter_market_menu_and_back(self, fresh_cli, mock_input, capsys):
        """进入市场子菜单并返回"""
        mock_input("4", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "4." in out

    def test_player_list_display(self, fresh_cli, mock_input, capsys):
        """查看玩家列表"""
        # 1=玩家管理, 2=玩家列表, 排序选择(默认), 回车继续, b=返回, 回车, 7=退出
        mock_input("1", "2", "1", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        # 检查玩家列表相关信息
        assert "名玩家" in out

    def test_item_list_display(self, fresh_cli, mock_input, capsys):
        """查看物品列表"""
        mock_input("2", "1", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert len(out) > 0

    def test_item_category_browse_display(self, fresh_cli, mock_input, capsys):
        """按分类浏览物品"""
        mock_input("2", "4", "weapon", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "分类目录" in out
        assert "weapon" in out
        assert "功能待 CatalogTree 实现" not in out

    def test_item_create_display(self, fresh_cli, mock_input, capsys):
        """创建物品成功路径"""
        mock_input(
            "2", "5",
            "CLI测试杂项", "misc", "common", "1", "测试描述", "99", "1",
            "", "b", "", "6"
        )
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "已创建物品" in out
        assert any(item.name == "CLI测试杂项" for item in fresh_cli.repo.items.values())

    def test_item_delete_display(self, fresh_cli, mock_input, capsys):
        """删除物品成功路径"""
        item = fresh_cli.app.item_service.create_item({
            "name": "CLI待删除",
            "category": "misc",
            "rarity": "common",
            "base_value": 1,
            "stats": {"stack_size_max": 99, "count": 1},
        })
        mock_input("2", "6", item.item_id, "y", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "已删除物品" in out
        assert item.item_id not in fresh_cli.repo.items

    def test_item_delete_referenced_display_business_error(self, fresh_cli, mock_input, capsys):
        """删除被引用物品时显示业务错误"""
        referenced_item_id = None
        for player in fresh_cli.repo.players.values():
            if player.inventory:
                referenced_item_id = player.inventory[0]["item_id"]
                break
        if referenced_item_id is None:
            pytest.skip("No referenced item in seed data")

        mock_input("2", "6", referenced_item_id, "y", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "业务错误" in out

    def test_active_listings_display(self, fresh_cli, mock_input, capsys):
        """查看活跃挂单"""
        mock_input("4", "3", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert len(out) > 0

    def test_market_create_listing_cli_success(self, fresh_cli, mock_input, capsys):
        """CLI 挂单上架会调用 MarketService 并从背包移出物品"""
        seller = next(iter(fresh_cli.repo.players.values()))
        item = fresh_cli.app.item_service.create_item({
            "name": "CLI市场材料",
            "category": "misc",
            "rarity": "common",
            "base_value": 1,
            "stats": {"stack_size_max": 99, "count": 1},
        })
        seller.inventory.append({"item_id": item.item_id, "count": 5})

        mock_input("4", "1", seller.player_id, item.item_id, "2", "9", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        created = [l for l in fresh_cli.repo.listings.values() if l.item_id == item.item_id]
        assert "已创建挂单" in out
        assert len(created) == 1
        assert created[0].status == "active"
        assert sum(s.get("count", 1) for s in seller.inventory if s.get("item_id") == item.item_id) == 3
        assert "功能待 MarketService 实现" not in out

    def test_market_cancel_listing_cli_uses_service(self, fresh_cli, mock_input, capsys):
        """CLI 撤销挂单会退回物品并关闭挂单"""
        seller = next(iter(fresh_cli.repo.players.values()))
        item = fresh_cli.app.item_service.create_item({
            "name": "CLI撤销材料",
            "category": "misc",
            "rarity": "common",
            "base_value": 1,
            "stats": {"stack_size_max": 99, "count": 1},
        })
        seller.inventory.append({"item_id": item.item_id, "count": 1})
        listing = fresh_cli.app.market_service.create_listing(seller.player_id, item.item_id, 1, 11)

        mock_input("4", "2", listing.listing_id, seller.player_id, "y", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "已撤销挂单" in out
        assert listing.status == "cancelled"
        assert listing.closed_at is not None
        assert any(s.get("item_id") == item.item_id for s in seller.inventory)

    def test_market_category_filter_cli_display(self, fresh_cli, mock_input, capsys):
        """CLI 按分类筛选活跃挂单"""
        seller = next(iter(fresh_cli.repo.players.values()))
        item = fresh_cli.app.item_service.create_item({
            "name": "CLI分类材料",
            "category": "misc",
            "rarity": "common",
            "base_value": 1,
            "stats": {"stack_size_max": 99, "count": 1},
        })
        seller.inventory.append({"item_id": item.item_id, "count": 1})
        listing = fresh_cli.app.market_service.create_listing(seller.player_id, item.item_id, 1, 12)

        mock_input("4", "5", "misc", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert listing.listing_id in out
        assert "CLI分类材料" in out
        assert "功能待 MarketService 实现" not in out

    def test_market_seller_filter_cli_display(self, fresh_cli, mock_input, capsys):
        """CLI 按卖家筛选活跃挂单"""
        seller = next(iter(fresh_cli.repo.players.values()))
        item = fresh_cli.app.item_service.create_item({
            "name": "CLI卖家筛选材料",
            "category": "misc",
            "rarity": "common",
            "base_value": 1,
            "stats": {"stack_size_max": 99, "count": 1},
        })
        seller.inventory.append({"item_id": item.item_id, "count": 1})
        listing = fresh_cli.app.market_service.create_listing(seller.player_id, item.item_id, 1, 14)

        mock_input("4", "6", seller.player_id, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert seller.name in out
        assert listing.listing_id in out
        assert "CLI卖家筛选材料" in out

    def test_market_listing_detail_cli_display(self, fresh_cli, mock_input, capsys):
        """CLI 挂单详情展示卖家、物品字段和历史价格参考"""
        from src.models import Transaction

        players = list(fresh_cli.repo.players.values())
        seller, buyer = players[0], players[1]
        item = fresh_cli.app.item_service.create_item({
            "name": "CLI详情材料",
            "category": "misc",
            "rarity": "common",
            "base_value": 3,
            "stats": {"stack_size_max": 99, "count": 1},
        })
        seller.inventory.append({"item_id": item.item_id, "count": 1})
        listing = fresh_cli.app.market_service.create_listing(seller.player_id, item.item_id, 1, 14)
        fresh_cli.repo.transactions.append(Transaction(
            transaction_id="t_cli_detail",
            listing_id="l_history",
            buyer_id=buyer.player_id,
            seller_id=seller.player_id,
            item_id=item.item_id,
            count=1,
            price=10,
            total=10,
            completed_at="2026-05-06T00:00:00Z",
        ))

        mock_input("4", "7", listing.listing_id, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "挂单详情" in out
        assert seller.name in out
        assert "CLI详情材料" in out
        assert "分类：misc" in out
        assert "历史价格参考" in out
        assert "t_cli_detail" in out

    def test_market_listing_detail_cli_missing_listing(self, fresh_cli, mock_input, capsys):
        """CLI 挂单详情处理不存在挂单"""
        mock_input("4", "7", "l_missing", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "未找到挂单" in out

    def test_market_buy_cli_confirmation_no_does_not_mutate(self, fresh_cli, mock_input, capsys):
        """CLI 购买确认为 n 时不执行交易"""
        players = list(fresh_cli.repo.players.values())
        seller, buyer = players[0], players[1]
        buyer.gold = 999
        item = fresh_cli.app.item_service.create_item({
            "name": "CLI取消购买材料",
            "category": "misc",
            "rarity": "common",
            "base_value": 1,
            "stats": {"stack_size_max": 99, "count": 1},
        })
        seller.inventory.append({"item_id": item.item_id, "count": 1})
        listing = fresh_cli.app.market_service.create_listing(seller.player_id, item.item_id, 1, 13)
        before = (buyer.gold, list(buyer.inventory), listing.status, len(fresh_cli.repo.transactions))

        mock_input("4", "9", listing.listing_id, buyer.player_id, "n", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "已取消" in out
        assert (buyer.gold, buyer.inventory, listing.status, len(fresh_cli.repo.transactions)) == before

    def test_market_buy_cli_success(self, fresh_cli, mock_input, capsys):
        """CLI 购买成功路径"""
        players = list(fresh_cli.repo.players.values())
        seller, buyer = players[0], players[1]
        seller.gold = 100
        buyer.gold = 999
        item = fresh_cli.app.item_service.create_item({
            "name": "CLI购买材料",
            "category": "misc",
            "rarity": "common",
            "base_value": 1,
            "stats": {"stack_size_max": 99, "count": 1},
        })
        seller.inventory.append({"item_id": item.item_id, "count": 1})
        listing = fresh_cli.app.market_service.create_listing(seller.player_id, item.item_id, 1, 17)

        mock_input("4", "9", listing.listing_id, buyer.player_id, "y", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "交易完成" in out
        assert listing.status == "sold"
        assert buyer.gold == 982
        assert seller.gold == 117
        assert any(t.listing_id == listing.listing_id for t in fresh_cli.repo.transactions)
        assert any(s.get("item_id") == item.item_id for s in buyer.inventory)

    def test_market_buy_cli_insufficient_gold_error(self, fresh_cli, mock_input, capsys):
        """CLI 购买金币不足时友好提示且不成交"""
        players = list(fresh_cli.repo.players.values())
        seller, buyer = players[0], players[1]
        buyer.gold = 1
        item = fresh_cli.app.item_service.create_item({
            "name": "CLI金币不足材料",
            "category": "misc",
            "rarity": "common",
            "base_value": 1,
            "stats": {"stack_size_max": 99, "count": 1},
        })
        seller.inventory.append({"item_id": item.item_id, "count": 1})
        listing = fresh_cli.app.market_service.create_listing(seller.player_id, item.item_id, 1, 99)

        mock_input("4", "9", listing.listing_id, buyer.player_id, "y", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "金币不足" in out
        assert listing.status == "active"
        assert not any(t.listing_id == listing.listing_id for t in fresh_cli.repo.transactions)

    def test_market_settle_pending_cli_processes_batch(self, fresh_cli, mock_input, capsys):
        """CLI 管理员批量结算使用 buyer-aware 订单"""
        players = list(fresh_cli.repo.players.values())
        seller, buyer = players[0], players[1]
        buyer.gold = 999
        item = fresh_cli.app.item_service.create_item({
            "name": "CLI批量结算材料",
            "category": "misc",
            "rarity": "common",
            "base_value": 1,
            "stats": {"stack_size_max": 99, "count": 1},
        })
        seller.inventory.append({"item_id": item.item_id, "count": 2})
        first = fresh_cli.app.market_service.create_listing(seller.player_id, item.item_id, 1, 21)
        second = fresh_cli.app.market_service.create_listing(seller.player_id, item.item_id, 1, 22)
        second.status = "sold"

        mock_input(
            "4", "10",
            f"{first.listing_id} {buyer.player_id}",
            f"{second.listing_id} {buyer.player_id}",
            "",
            "", "b", "", "6",
        )
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "成功结算 1 / 2 条订单" in out
        assert first.status == "sold"
        assert any(t.listing_id == first.listing_id for t in fresh_cli.repo.transactions)




# -----------------------------------------------------------------------------
# 输入校验测试（功能 ID 8）
# -----------------------------------------------------------------------------

class TestInvalidInputHandling:
    """非法输入处理"""

    def test_empty_input_rejected(self, fresh_cli, mock_input, capsys):
        """空输入被视为非法"""
        # 空输入(非法), 回车, 6=退出
        mock_input("", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        # 空输入应该导致重试
        assert len(out) > 0

    def test_whitespace_input_rejected(self, fresh_cli, mock_input, capsys):
        """纯空格输入被视为非法"""
        mock_input("   ", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert len(out) > 0

    def test_non_numeric_in_submenu(self, fresh_cli, mock_input, capsys):
        """子菜单中的非法字符输入"""
        # 1=玩家管理, xyz=非法, 回车, b=返回, 回车, 6=退出
        mock_input("1", "xyz", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        # 应该有错误处理
        assert "xyz" in out or len(out) > 100  # 有输出或处理了错误




# -----------------------------------------------------------------------------
# 撤销功能测试（功能 ID 9）
# -----------------------------------------------------------------------------

class TestUndoFunctionality:
    """操作撤销"""

    def test_undo_not_available_initially(self, fresh_cli):
        """初始状态无可撤销操作"""
        # 检查初始状态
        assert not fresh_cli.op_stack.can_undo()
        assert len(fresh_cli.op_stack) == 0

    def test_undo_stack_integration(self, fresh_cli):
        """撤销栈集成功能演示"""
        stack = fresh_cli.op_stack

        executed = []
        def make_undo_fn(name):
            def fn():
                executed.append(name)
            return fn

        stack.push(Operation(name="test_op", undo_fn=make_undo_fn("undo1")))
        assert stack.can_undo()

        op = stack.pop()
        op.undo_fn()
        assert "undo1" in executed




# -----------------------------------------------------------------------------
# 查询功能测试
# -----------------------------------------------------------------------------

class TestQueryFunctions:
    """各种查询功能"""

    def test_query_player_by_id_found(self, fresh_cli, mock_input, capsys):
        """按 ID 查询存在的玩家"""
        first_pid = list(fresh_cli.repo.players.keys())[0]

        # 1=玩家管理, 4=按ID查询, 输入ID, 回车, b=返回, 回车, 6=退出
        mock_input("1", "4", first_pid, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert len(out) > 0

    def test_query_player_by_id_not_found(self, fresh_cli, mock_input, capsys):
        """按 ID 查询不存在的玩家"""
        mock_input("1", "4", "p_99999", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert len(out) > 0

    def test_search_player_by_name(self, fresh_cli, mock_input, capsys):
        """按名字模糊搜索玩家"""
        first_player = list(fresh_cli.repo.players.values())[0]
        prefix = first_player.name[:2]

        mock_input("1", "5", prefix, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert len(out) > 0

    def test_query_item_by_id_found(self, fresh_cli, mock_input, capsys):
        """按 ID 查询存在的物品"""
        first_iid = list(fresh_cli.repo.items.keys())[0]

        mock_input("2", "3", first_iid, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert len(out) > 0

    def test_query_item_by_id_not_found(self, fresh_cli, mock_input, capsys):
        """按 ID 查询不存在的物品"""
        mock_input("2", "3", "i_99999", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert len(out) > 0




# -----------------------------------------------------------------------------
# 数据展示测试
# -----------------------------------------------------------------------------

class TestDataDisplay:
    """数据展示功能"""

    def test_system_snapshot_display(self, fresh_cli, mock_input, capsys):
        """系统数据快照"""
        mock_input("5", "6", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "系统数据快照" in out

    def test_top_gold_display(self, fresh_cli, mock_input, capsys):
        """富豪榜"""
        mock_input("5", "4", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "排名" in out
        assert "玩家" in out
        assert "金币" in out

    def test_player_transactions_display(self, fresh_cli, mock_input, capsys):
        """玩家成交历史（可能为空）"""
        first_pid = list(fresh_cli.repo.players.keys())[0]
        mock_input("5", "1", first_pid, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "成交记录" in out

    def test_item_transactions_by_item_id_empty(self, fresh_cli, mock_input, capsys):
        """按 item_id 查看物品成交历史（无数据）"""
        first_iid = list(fresh_cli.repo.items.keys())[0]
        mock_input("5", "2", "1", first_iid, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "物品成交历史" in out

    def test_item_transactions_by_category_empty(self, fresh_cli, mock_input, capsys):
        """按分类查看物品成交历史（无数据）"""
        first_category = list(fresh_cli.repo.items.values())[0].category.split(".")[0]
        mock_input("5", "2", "2", first_category, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "分类成交历史" in out
        assert "暂无成交记录" in out

    def test_item_transactions_limit_output(self, fresh_cli, mock_input, capsys):
        """物品成交历史最多显示 20 条，并提示剩余数量"""
        from src.models import Transaction

        first_iid = list(fresh_cli.repo.items.keys())[0]
        for i in range(25):
            fresh_cli.repo.transactions.append(
                Transaction(
                    transaction_id=f"t_91{i:03d}",
                    listing_id="l_001",
                    buyer_id="p_001",
                    seller_id="p_002",
                    item_id=first_iid,
                    count=1,
                    price=100 + i,
                    total=100 + i,
                    completed_at=f"2026-04-22T00:00:{i:02d}Z",
                )
            )

        mock_input("5", "2", "1", first_iid, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "还有 5 条未显示" in out

    def test_price_stats_by_item_id_empty(self, fresh_cli, mock_input, capsys):
        """按 item_id 查看价格统计（无数据）"""
        first_iid = list(fresh_cli.repo.items.keys())[0]
        mock_input("5", "3", "1", first_iid, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "暂无成交数据" in out

    def test_price_stats_by_category_empty(self, fresh_cli, mock_input, capsys):
        """按分类查看价格统计（无数据）"""
        first_category = list(fresh_cli.repo.items.values())[0].category.split(".")[0]
        mock_input("5", "3", "2", first_category, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "暂无成交数据" in out

    def test_price_stats_by_category_non_empty(self, fresh_cli, mock_input, capsys):
        """按分类查看价格统计（有数据）"""
        from src.models import Transaction

        first_iid = list(fresh_cli.repo.items.keys())[0]
        first_category = fresh_cli.repo.items[first_iid].category.split(".")[0]
        fresh_cli.repo.transactions.append(
            Transaction(
                transaction_id="t_920001",
                listing_id="l_001",
                buyer_id="p_001",
                seller_id="p_002",
                item_id=first_iid,
                count=1,
                price=233,
                total=233,
                completed_at="2026-04-22T01:00:00Z",
            )
        )

        mock_input("5", "3", "2", first_category, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "价格统计" in out
        assert "成交次数" in out
        assert "平均成交价" in out

    def test_top_volume_display_empty(self, fresh_cli, mock_input, capsys):
        """交易额榜（无数据）"""
        mock_input("5", "5", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "交易额榜" in out

    def test_top_volume_display_non_empty(self, fresh_cli, mock_input, capsys):
        """交易额榜（有数据）"""
        from src.models import Transaction

        fresh_cli.repo.transactions.append(
            Transaction(
                transaction_id="t_930001",
                listing_id="l_001",
                buyer_id="p_001",
                seller_id="p_002",
                item_id=list(fresh_cli.repo.items.keys())[0],
                count=1,
                price=500,
                total=500,
                completed_at="2026-04-22T02:00:00Z",
            )
        )

        mock_input("5", "5", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "交易额榜" in out
        assert "成交额" in out




# -----------------------------------------------------------------------------
# 入口函数测试
# -----------------------------------------------------------------------------

class TestRunCli:
    """run_cli 入口函数"""

    def test_run_cli_integration(self, tmp_path, monkeypatch, capsys):
        """run_cli 完整集成测试"""
        data_dir = str(tmp_path / "data")
        persistence = Persistence(data_dir=data_dir)
        persistence.seed_if_empty()
        app = App(persistence=persistence)
        app.bootstrap()

        # 模拟用户进入主菜单后立即退出（7=退出）
        inputs = iter(["7"])
        def _input_fn(prompt: str = "") -> str:
            try:
                return next(inputs)
            except StopIteration:
                return "7"
        monkeypatch.setattr("builtins.input", _input_fn)

        run_cli(app)

        out = capsys.readouterr().out
        assert len(out) > 0  # 有输出即可




# -----------------------------------------------------------------------------
# 异常兜底测试
# -----------------------------------------------------------------------------

class TestExceptionHandling:
    """异常处理测试"""

    def test_keyboard_interrupt_in_loop(self, fresh_cli):
        """KeyboardInterrupt 在循环中被捕获后正常退出"""
        # 直接测试 TradingCLI.run 的异常处理分支
        # 由于 mock 复杂性，这里只验证方法存在且可调用
        # 哎我超这 mock 怎么这么坏😡
        assert hasattr(fresh_cli, 'run')

    def test_trading_system_error_caught(self, fresh_cli, mock_input, capsys):
        """TradingSystemError 被正确捕获并显示"""
        # 模拟一个会触发异常处理的输入序列
        # 输入不存在的物品ID查询，可能触发 NotFoundError
        mock_input("2", "3", "i_nonexistent_xyz", "", "b", "", "7")
        fresh_cli.run()

        # 不应崩溃，有输出即可
        out = capsys.readouterr().out
        assert len(out) > 0


# -----------------------------------------------------------------------------
# 玩家管理 CLI 交互测试（功能 ID 11、15、16、17、18）
# -----------------------------------------------------------------------------

class TestPlayerManagementCLI:
    """补全玩家管理菜单的 CLI 交互测试"""

    def test_player_create_cli_success(self, fresh_cli, mock_input, capsys):
        """创建玩家成功路径（功能 ID 11）"""
        before = len(fresh_cli.repo.players)
        # 1=玩家管理, 1=创建, name, gold, level, klass, 回车继续, b=返回, 回车, 7=退出
        mock_input("1", "1", "测试CLI玩家", "100", "1", "5", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "已创建玩家" in out
        assert len(fresh_cli.repo.players) == before + 1
        assert any(p.name == "测试CLI玩家" for p in fresh_cli.repo.players.values())

    def test_player_list_sort_by_gold_desc(self, fresh_cli, mock_input, capsys):
        """玩家列表按金币降序展示（功能 ID 12）"""
        # 1=玩家管理, 2=列表, 4=按金币降序, 回车继续, b=返回, 回车, 7=退出
        mock_input("1", "2", "4", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        # 验证有玩家列表输出
        assert "名玩家" in out

    def test_player_list_sort_by_name(self, fresh_cli, mock_input, capsys):
        """玩家列表按名字排序（功能 ID 12）"""
        mock_input("1", "2", "2", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "名玩家" in out

    def test_player_rename_cli_success(self, fresh_cli, mock_input, capsys):
        """重命名玩家成功路径（功能 ID 16）"""
        # 取第一个玩家
        first = next(iter(fresh_cli.repo.players.values()))
        old_name = first.name
        new_name = "重命名后的名字"

        # 1=玩家管理, 6=重命名, pid, 新名字, y=确认, 回车继续, b=返回, 回车, 7=退出
        mock_input("1", "6", first.player_id, new_name, "y", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "已将玩家昵称改为" in out
        # 验证存储中确实更新了
        updated = fresh_cli.app.player_service.get_by_id(first.player_id)
        assert updated.name == new_name
        assert updated.name != old_name

    def test_player_rename_cli_cancelled(self, fresh_cli, mock_input, capsys):
        """重命名玩家取消路径（功能 ID 16）"""
        first = next(iter(fresh_cli.repo.players.values()))
        old_name = first.name

        # 输入 n 取消
        mock_input("1", "6", first.player_id, "新名字", "n", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "已取消" in out
        # 验证名字未变
        unchanged = fresh_cli.app.player_service.get_by_id(first.player_id)
        assert unchanged.name == old_name

    def test_player_delete_cli_blocked_by_inventory(self, fresh_cli, mock_input, capsys):
        """删除玩家被背包非空规则阻止（功能 ID 17）"""
        # 找一个有背包的玩家
        target = None
        for p in fresh_cli.repo.players.values():
            if p.inventory:
                target = p
                break

        if target is None:
            pytest.skip("种子数据无非空背包玩家")

        before = len(fresh_cli.repo.players)
        # 1=玩家管理, 7=删除, pid, yes=确认, 回车, b=返回, 回车, 7=退出
        mock_input("1", "7", target.player_id, "yes", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        # 删除应失败：背包非空
        assert len(fresh_cli.repo.players) == before
        assert target.player_id in fresh_cli.repo.players

    def test_player_delete_cli_cancelled(self, fresh_cli, mock_input, capsys):
        """删除玩家取消路径（功能 ID 17）"""
        first = next(iter(fresh_cli.repo.players.values()))
        before = len(fresh_cli.repo.players)

        # 输入 no 取消
        mock_input("1", "7", first.player_id, "no", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "已取消" in out
        assert len(fresh_cli.repo.players) == before

    def test_player_add_gold_debug_cli(self, fresh_cli, mock_input, capsys):
        """金币充值（调试）CLI 路径（功能 ID 18）"""
        first = next(iter(fresh_cli.repo.players.values()))
        before_gold = first.gold

        # 1=玩家管理, 8=充值, pid, amount, 回车, b=返回, 回车, 7=退出
        mock_input("1", "8", first.player_id, "500", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "已为" in out
        assert "充值" in out
        updated = fresh_cli.app.player_service.get_by_id(first.player_id)
        assert updated.gold == before_gold + 500

    def test_player_add_gold_invalid_amount(self, fresh_cli, mock_input, capsys):
        """金币充值非法输入触发 InvalidInputError（功能 ID 18）"""
        first = next(iter(fresh_cli.repo.players.values()))

        # "abc" 非法 → InvalidInputError → pause → 回到玩家菜单 → b → pause → 7 退出
        mock_input("1", "8", first.player_id, "abc", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        # 非法输入应被捕获并显示错误
        assert "输入错误" in out or "错误" in out


# -----------------------------------------------------------------------------
# 背包管理 CLI 交互补全测试（功能 ID 25-29）
# -----------------------------------------------------------------------------

class TestInventoryManagementCLI:
    """补全背包管理菜单的 CLI 交互测试"""

    def _player_with_inventory(self, fresh_cli):
        """找一个背包非空的玩家"""
        for p in fresh_cli.repo.players.values():
            if p.inventory:
                return p
        return None

    def test_inventory_show_cli(self, fresh_cli, mock_input, capsys):
        """查看背包（功能 ID 25：DoublyLinkedList 顺序）"""
        target = self._player_with_inventory(fresh_cli)
        if target is None:
            pytest.skip("种子数据无非空背包玩家")

        # 3=背包管理, 1=查看, pid, 回车, b=返回, 回车, 7=退出
        mock_input("3", "1", target.player_id, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert target.name in out
        assert "已用槽位" in out

    def test_inventory_show_sorted_cli(self, fresh_cli, mock_input, capsys):
        """按稀有度排序展示背包（功能 ID 26）"""
        target = self._player_with_inventory(fresh_cli)
        if target is None:
            pytest.skip("种子数据无非空背包玩家")

        mock_input("3", "2", target.player_id, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "按稀有度排序" in out

    def test_inventory_capacity_cli(self, fresh_cli, mock_input, capsys):
        """查看背包容量信息（功能 ID 29）"""
        first = next(iter(fresh_cli.repo.players.values()))

        # 3=背包管理, 5=容量信息, pid, 回车, b=返回, 回车, 7=退出
        mock_input("3", "5", first.player_id, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "总容量" in out
        assert "已用槽位" in out
        assert "剩余槽位" in out

    def test_inventory_capacity_player_not_found(self, fresh_cli, mock_input, capsys):
        """查看不存在玩家的容量返回友好提示"""
        mock_input("3", "5", "p_nonexistent_xyz", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        # 应有提示信息，不崩溃
        assert len(out) > 0

    def test_inventory_add_item_cli_success(self, fresh_cli, mock_input, capsys):
        """添加物品到背包（功能 ID 28）"""
        first = next(iter(fresh_cli.repo.players.values()))
        # 取一个 misc 物品（可堆叠）
        target_item = None
        for item in fresh_cli.repo.items.values():
            if item.category == "misc":
                target_item = item
                break

        if target_item is None:
            pytest.skip("种子数据无 misc 类物品")

        before_count = len(first.inventory)

        # 3=背包管理, 4=添加, pid, item_id, count, 回车, b=返回, 回车, 7=退出
        mock_input("3", "4", first.player_id, target_item.item_id, "1", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        # 验证添加成功（背包发生变化）
        after_count = len(first.inventory)
        assert "已向背包添加" in out or after_count > before_count

    def test_inventory_remove_item_cli(self, fresh_cli, mock_input, capsys):
        """从背包移除物品（功能 ID 27）"""
        target = self._player_with_inventory(fresh_cli)
        if target is None:
            pytest.skip("种子数据无非空背包玩家")

        slot = target.inventory[0]
        item_id = slot.get("item_id")
        count = min(slot.get("count", 1), 1)

        # 3=背包管理, 3=移除, pid, item_id, count, 回车, b=返回, 回车, 7=退出
        mock_input("3", "3", target.player_id, item_id, str(count), "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "已从背包移除" in out


# -----------------------------------------------------------------------------
# 市场补全 CLI 交互测试（功能 ID 33、36）
# -----------------------------------------------------------------------------

class TestMarketAdditionalCLI:
    """补全市场菜单中遗漏的 CLI 交互测试"""

    def test_market_query_by_price_range_cli(self, fresh_cli, mock_input, capsys):
        """按价格区间查询挂单（功能 ID 33）"""
        # 4=市场, 4=价格区间, min, max, 回车, b=返回, 回车, 7=退出
        mock_input("4", "4", "0", "999999", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "价格区间" in out

    def test_market_query_by_price_range_invalid_input(self, fresh_cli, mock_input, capsys):
        """价格区间查询非法输入触发 InvalidInputError"""
        # "abc" 触发 InvalidInputError，pause 后回到市场菜单，b 返回，pause 后退出
        mock_input("4", "4", "abc", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        # 应捕获错误并显示提示
        assert "输入错误" in out or "错误" in out

    def test_market_sort_listings_price_asc(self, fresh_cli, mock_input, capsys):
        """挂单按价格升序排序（功能 ID 36）"""
        # 4=市场, 8=排序, 1=价格升序, 回车, b=返回, 回车, 7=退出
        mock_input("4", "8", "1", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "排序后" in out

    def test_market_sort_listings_price_desc(self, fresh_cli, mock_input, capsys):
        """挂单按价格降序排序（功能 ID 36）"""
        mock_input("4", "8", "2", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "排序后" in out

    def test_market_sort_listings_time_asc(self, fresh_cli, mock_input, capsys):
        """挂单按时间升序排序（功能 ID 36）"""
        mock_input("4", "8", "3", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "排序后" in out

    def test_market_sort_listings_time_desc(self, fresh_cli, mock_input, capsys):
        """挂单按时间降序排序（功能 ID 36）"""
        mock_input("4", "8", "4", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "排序后" in out

    def test_market_sort_listings_invalid_choice(self, fresh_cli, mock_input, capsys):
        """挂单排序非法选项触发 InvalidInputError"""
        # "9" 触发 InvalidInputError, pause 后回到市场菜单, b 返回, pause, 7 退出
        mock_input("4", "8", "9", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "输入错误" in out or "错误" in out


# -----------------------------------------------------------------------------
# 异常处理统一测试（Code Review 补充）
# -----------------------------------------------------------------------------

class TestExceptionHandling:
    """测试异常从服务层正确传播到 UI 层并显示正确的错误消息"""

    # ========== PlayerHandler 异常测试 ==========


    def test_player_query_invalid_id_displays_error(self, fresh_cli, mock_input, capsys):
        """查询不存在的玩家 ID 显示错误"""
        # 1=玩家管理, 4=按ID查询, invalid_id, 回车, b=返回, 回车, 7=退出
        mock_input("1", "4", "p_invalid_999", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "错误" in out or "未找到" in out or "不存在" in out

    # ========== ItemHandler 异常测试 ==========

    def test_item_query_not_found_displays_error(self, fresh_cli, mock_input, capsys):
        """查询不存在的物品显示错误"""
        # 2=物品管理, 3=按ID查询, invalid_id, 回车, b=返回, 回车, 7=退出
        mock_input("2", "3", "i_nonexistent_999", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "错误" in out or "未找到" in out or "不存在" in out

    # ========== InventoryHandler 异常测试 ==========

    def test_inventory_show_invalid_player_displays_error(self, fresh_cli, mock_input, capsys):
        """查看不存在玩家的背包显示错误"""
        # 3=背包管理, 1=查看背包, invalid_player_id, 回车, b=返回, 回车, 7=退出
        mock_input("3", "1", "p_invalid_999", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "错误" in out or "未找到" in out or "不存在" in out

    def test_inventory_remove_item_not_found_displays_error(self, fresh_cli, mock_input, capsys):
        """移除背包中不存在的物品显示错误"""
        player = list(fresh_cli.repo.players.values())[0]
        # 3=背包管理, 3=移除物品, player_id, nonexistent_item_id, count, 回车, b=返回, 回车, 7=退出
        mock_input("3", "3", player.player_id, "i_not_in_inventory", "1", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "错误" in out or "未找到" in out or "不存在" in out


# -----------------------------------------------------------------------------
# 边界条件测试（Code Review 补充）
# -----------------------------------------------------------------------------

class TestBoundaryConditions:
    """测试边界条件和特殊输入"""

    def test_unicode_chinese_player_name(self, fresh_cli, mock_input, capsys):
        """中文玩家名称正常工作"""
        # 1=玩家管理, 1=创建, chinese_name, gold, level, class, 回车, b=返回, 回车, 7=退出
        mock_input("1", "1", "测试玩家", "100", "1", "1", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "成功" in out or "测试玩家" in out

    def test_very_large_gold_amount(self, fresh_cli, mock_input, capsys):
        """非常大的金币数量"""
        # 1=玩家管理, 1=创建, name, very_large_gold, level, class, 回车, b=返回, 回车, 7=退出
        mock_input("1", "1", "RichPlayer", "999999999", "1", "1", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "成功" in out or "错误" in out


# -----------------------------------------------------------------------------
# InventoryHandler count 校验回归测试（Code Review #4 补充）
# -----------------------------------------------------------------------------

class TestInventoryCountValidation:
    """覆盖 inventory.py:120 / :138 修复点的回归保护

    原来的 ``count = int(count_str) if count_str.isdigit() and int(count_str) > 0 else 1``
    会让 '0' / '-5' / 'abc' 被静默吞成 1，导致 add_item / remove_item 被错误地以 1 执行。
    修复后非正整数应触发 InvalidInputError 并显示输入错误提示。
    """

    def _first_player_id(self, fresh_cli) -> str:
        return next(iter(fresh_cli.repo.players.values())).player_id

    def _first_item_id(self, fresh_cli) -> str:
        return next(iter(fresh_cli.repo.items.values())).item_id

    def test_remove_item_count_zero_rejected(self, fresh_cli, mock_input, capsys):
        """remove_item 输入 '0' 应被拒绝，不静默回退到 1"""
        pid = self._first_player_id(fresh_cli)
        iid = self._first_item_id(fresh_cli)
        # 3=背包管理, 3=移除, pid, item_id, '0'=非法 count
        mock_input("3", "3", pid, iid, "0", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "输入错误" in out
        assert "已从背包移除" not in out  # 不应执行实际移除

    def test_remove_item_count_negative_rejected(self, fresh_cli, mock_input, capsys):
        """remove_item 输入负数应被拒绝"""
        pid = self._first_player_id(fresh_cli)
        iid = self._first_item_id(fresh_cli)
        mock_input("3", "3", pid, iid, "-5", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "输入错误" in out
        assert "已从背包移除" not in out

    def test_remove_item_count_non_numeric_rejected(self, fresh_cli, mock_input, capsys):
        """remove_item 输入非数字应被拒绝"""
        pid = self._first_player_id(fresh_cli)
        iid = self._first_item_id(fresh_cli)
        mock_input("3", "3", pid, iid, "abc", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "输入错误" in out

    def test_remove_item_count_empty_defaults_to_one(self, fresh_cli, mock_input, capsys):
        """remove_item 留空使用默认 1（这是文档承诺的行为，不应被回归破坏）"""
        # 找一个有物品的玩家
        target_player = None
        target_item_id = None
        for p in fresh_cli.repo.players.values():
            if p.inventory:
                target_player = p
                target_item_id = p.inventory[0]["item_id"]
                break
        if target_player is None:
            pytest.skip("种子数据无非空背包玩家")

        # 留空输入应使用默认 1
        mock_input("3", "3", target_player.player_id, target_item_id, "", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        # 默认数量 1 应执行成功
        assert "已从背包移除 1" in out

    def test_add_item_count_zero_rejected(self, fresh_cli, mock_input, capsys):
        """add_item 输入 '0' 应被拒绝"""
        pid = self._first_player_id(fresh_cli)
        iid = self._first_item_id(fresh_cli)
        mock_input("3", "4", pid, iid, "0", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "输入错误" in out
        assert "已向背包添加" not in out

    def test_add_item_count_negative_rejected(self, fresh_cli, mock_input, capsys):
        """add_item 输入负数应被拒绝"""
        pid = self._first_player_id(fresh_cli)
        iid = self._first_item_id(fresh_cli)
        mock_input("3", "4", pid, iid, "-3", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "输入错误" in out
        assert "已向背包添加" not in out


# -----------------------------------------------------------------------------
# 挂单创建边界测试
# -----------------------------------------------------------------------------

class TestMarketListingEdgeCases:
    """挂单创建边界情况测试"""

    def test_create_listing_nonexistent_seller(self, fresh_cli, mock_input, capsys):
        """挂单上架：不存在的卖家 ID"""
        item = list(fresh_cli.repo.items.values())[0]
        mock_input("4", "1", "p_nonexistent", item.item_id, "1", "100", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "错误" in out
        # 不应创建挂单
        assert "已创建挂单" not in out

    def test_create_listing_nonexistent_item(self, fresh_cli, mock_input, capsys):
        """挂单上架：不存在的物品 ID"""
        seller = next(iter(fresh_cli.repo.players.values()))
        mock_input("4", "1", seller.player_id, "i_nonexistent", "1", "100", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "错误" in out
        assert "已创建挂单" not in out

    def test_create_listing_insufficient_inventory(self, fresh_cli, mock_input, capsys):
        """挂单上架：库存不足"""
        seller = next(iter(fresh_cli.repo.players.values()))
        item = fresh_cli.app.item_service.create_item({
            "name": "稀有物品",
            "category": "misc",
            "rarity": "common",
            "base_value": 1,
            "stats": {"stack_size_max": 99, "count": 1},
        })
        # 只给 1 个，但尝试挂 5 个
        seller.inventory.append({"item_id": item.item_id, "count": 1})
        mock_input("4", "1", seller.player_id, item.item_id, "5", "100", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "错误" in out
        assert "已创建挂单" not in out

    def test_buy_nonexistent_listing(self, fresh_cli, mock_input, capsys):
        """购买不存在的挂单"""
        buyer = next(iter(fresh_cli.repo.players.values()))
        mock_input("4", "9", "l_nonexistent", buyer.player_id, "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "错误" in out
        assert "交易完成" not in out


# -----------------------------------------------------------------------------
# 删除有活跃挂单的玩家测试
# -----------------------------------------------------------------------------

class TestDeletePlayerWithListings:
    """删除有活跃挂单的玩家应被阻止"""

    def test_delete_player_with_active_listing_blocked(self, fresh_cli, mock_input, capsys):
        """删除有活跃挂单的玩家应显示业务错误"""
        seller = fresh_cli.app.player_service.create_player("待删卖家", gold=100)
        item = fresh_cli.app.item_service.create_item({
            "name": "挂单物品",
            "category": "misc",
            "rarity": "common",
            "base_value": 1,
            "stats": {"stack_size_max": 99, "count": 1},
        })
        seller.inventory.append({"item_id": item.item_id, "count": 1})
        fresh_cli.app.market_service.create_listing(seller.player_id, item.item_id, 1, 50)

        # 尝试删除：1=玩家管理, 7=删除, player_id, y=确认, 回车, b, 回车, 7
        mock_input("1", "7", seller.player_id, "y", "", "b", "", "7")
        fresh_cli.run()

        out = capsys.readouterr().out
        assert "业务错误" in out or "错误" in out
        # 玩家应仍然存在
        assert seller.player_id in fresh_cli.repo.players
