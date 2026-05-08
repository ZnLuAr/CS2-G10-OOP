"""历史与报表 Handler

负责交易历史查询、价格统计、排行榜等功能。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.errors import InvalidInputError
from src.ui.handlers.base import BaseHandler
from src.ui.menus import show_report_menu
from src.ui.prompts import prompt_choice
from src.ui.utils import print_paginated
from src.ui.utils import print_paginated

if TYPE_CHECKING:
    from src.app import App
    from src.ui.cli import OperationStack

__all__ = ["ReportHandler"]


class ReportHandler(BaseHandler):
    """历史与报表 Handler"""

    def __init__(self, app: App, op_stack: OperationStack | None = None):
        super().__init__(app, op_stack)

    def run_menu(self) -> None:
        """运行历史与报表菜单循环"""
        while True:
            try:
                menu_text = show_report_menu()
                print(menu_text)
                choice = prompt_choice(
                    "请输入选项",
                    {"1", "2", "3", "4", "5", "6", "b", "B"}
                )

                if choice.lower() == "b":
                    break

                self._dispatch(choice)

            except Exception as e:
                self._handle_exception(e)

    def _dispatch(self, choice: str) -> None:
        """分发菜单选择"""
        actions = {
            "1": self.show_player_transactions,
            "2": self.show_item_transactions,
            "3": self.show_price_stats,
            "4": self.show_top_gold,
            "5": self.show_top_volume,
            "6": self.show_snapshot,
        }
        action = actions.get(choice)
        if action:
            action()

    def show_player_transactions(self) -> None:
        """显示玩家成交历史"""
        pid = input("请输入玩家 ID：").strip()
        player = self.app.player_service.get_by_id(pid)
        txns = self.app.transaction_service.by_player(pid)
        print(f"\n玩家 {player.name} 的成交记录（共 {len(txns)} 条）：")
        print("-" * 90)
        if not txns:
            print("  该玩家暂无成交记录")
            self._pause()
            return

        def _format_player_txn(t) -> str:
            role = "买" if t.buyer_id == pid else "卖"
            other = t.seller_id if t.buyer_id == pid else t.buyer_id
            item_name = self._get_item_display_name(t.item_id)
            return (
                f"  {t.completed_at} [{role}] {item_name}({t.item_id}) "
                f"x{t.count} @ {t.price} = {t.total} → {other}"
            )

        print_paginated(txns, formatter=_format_player_txn, limit=20, unit="条")

    def show_item_transactions(self) -> None:
        """显示物品成交历史（支持按 item_id / 分类）"""
        mode = prompt_choice("查询方式 (1=item_id, 2=类型/分类)", {"1", "2"})
        if mode == "1":
            item_id = input("请输入 item_id：").strip()
            item = self.app.item_service.get_by_id(item_id)
            txns = self.app.transaction_service.by_item(item_id)
            title = f"物品成交历史：{item.name} ({item_id})"
        else:
            category = input("请输入类型/分类（如 weapon / weapon.sword / misc）：").strip()
            txns = self.app.transaction_service.by_category(category)
            title = f"分类成交历史：{category}"

        print(f"\n{title}（共 {len(txns)} 条）：")
        print("-" * 100)
        if not txns:
            print("  该物品/类型暂无成交记录")
            self._pause()
            return

        print_paginated(
            txns,
            formatter=lambda t: (
                f"  {t.completed_at} {self._get_item_display_name(t.item_id)}({t.item_id}) "
                f"买家={t.buyer_id} 卖家={t.seller_id} x{t.count} @ {t.price} = {t.total}"
            ),
            limit=20,
            unit="条"
        )

    def show_price_stats(self) -> None:
        """显示价格统计（支持按 item_id / 分类）"""
        mode = prompt_choice("统计方式 (1=item_id, 2=类型/分类)", {"1", "2"})
        try:
            if mode == "1":
                item_id = input("请输入 item_id：").strip()
                item = self.app.item_service.get_by_id(item_id)
                stats = self.app.transaction_service.price_stats(item_id)
                label = f"{item.name} ({item_id})"
            else:
                category = input("请输入类型/分类（如 weapon / weapon.sword / misc）：").strip()
                stats = self.app.transaction_service.price_stats_by_category(category)
                label = category
        except InvalidInputError:
            print("\n该物品/类型暂无成交数据")
            self._pause()
            return

        print(f"\n价格统计：{label}")
        print("-" * 40)
        print(f"  成交次数：{stats['count']}")
        print(f"  最低成交价：{stats['min']}")
        print(f"  最高成交价：{stats['max']}")
        print(f"  平均成交价：{stats['avg']:.2f}")
        self._pause()

    def show_top_gold(self) -> None:
        """富豪榜"""
        players = self.app.transaction_service.top_by_gold(10)
        print("\n嘉豪榜 Top 10：")
        print("-" * 40)
        print(f"{'排名':<6} {'玩家':<15} {'金币':>10}")
        print("-" * 40)
        for i, p in enumerate(players, 1):
            print(f"{i:<6} {p.name:<15} {p.gold:>10}")
        self._pause()

    def show_top_volume(self) -> None:
        """交易额榜"""
        ranked = self.app.transaction_service.top_by_volume(10)
        print("\n交易额榜 Top 10：")
        print("-" * 44)
        print(f"{'排名':<6} {'玩家':<15} {'成交额':>12}")
        print("-" * 44)
        if not ranked:
            print("  暂无交易额数据")
            self._pause()
            return
        for i, (player, volume) in enumerate(ranked, 1):
            print(f"{i:<6} {player.name:<15} {volume:>12}")
        self._pause()

    def show_snapshot(self) -> None:
        """系统数据快照"""
        snap = self.app.transaction_service.snapshot()

        print(f"\n{'='*40}")
        print("           系统数据快照")
        print(f"{'='*40}")
        print(f"  总玩家数：{snap['players']}")
        print(f"  总物品数：{snap['items']}")
        print(f"  活跃挂单：{snap['active_listings']}")
        print(f"  累计交易额：{snap['total_volume']}")
        print(f"{'='*40}")
        self._pause()
