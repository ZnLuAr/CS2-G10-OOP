"""市场交易 Handler

负责挂单管理、交易执行、价格查询等功能。
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from src.errors import BusinessRuleError, TradingSystemError
from src.ui.formatters import format_listing_table
from src.ui.handlers.base import BaseHandler
from src.ui.menus import show_market_menu
from src.ui.operations import Operation
from src.ui.prompts import prompt_choice, prompt_confirm, prompt_int, prompt_optional_int
from src.ui.utils import print_paginated

if TYPE_CHECKING:
    from src.app import App
    from src.ui.cli import OperationStack

__all__ = ["MarketHandler"]


class MarketHandler(BaseHandler):
    """市场交易 Handler"""

    def __init__(self, app: App, op_stack: OperationStack | None = None):
        super().__init__(app, op_stack)

    def run_menu(self) -> None:
        """运行市场交易菜单循环"""
        while True:
            try:
                menu_text = show_market_menu()
                print(menu_text)
                choice = prompt_choice(
                    "请输入选项",
                    {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "b", "B"}
                )

                if choice.lower() == "b":
                    break

                self._dispatch(choice)

            except Exception as e:
                self._handle_exception(e)

    def _dispatch(self, choice: str) -> None:
        """分发菜单选择（编号与原 CLI 保持一致）"""
        actions = {
            "1": self.create_listing,
            "2": self.cancel_listing,
            "3": self.show_active_listings,
            "4": self.query_by_price_range,
            "5": self.filter_by_category,
            "6": self.filter_by_seller,
            "7": self.show_detail,
            "8": self.sort_listings,
            "9": self.buy,
            "10": self.settle_pending,
        }
        action = actions.get(choice)
        if action:
            action()

    def show_active_listings(self) -> None:
        """显示活跃挂单"""
        active = self.app.market_service.list_active()
        table = format_listing_table(active, self.repo)
        print(table)
        self._pause()

    def create_listing(self) -> None:
        """创建市场挂单"""
        seller_id = input("卖家玩家 ID：").strip()
        item_id = input("物品 ID：").strip()
        count = prompt_int("出售数量", min_val=1)
        price = prompt_int("单价", min_val=1)

        listing = self.app.market_service.create_listing(seller_id, item_id, count, price)
        item_name = self._get_item_display_name(listing.item_id)
        print(
            f"[成功] 已创建挂单 {listing.listing_id}："
            f"{item_name} x{listing.count} @ {listing.price}"
        )
        self._pause()

    def cancel_listing(self) -> None:
        """撤销挂单"""
        lid = input("请输入要撤销的挂单 ID：").strip()
        requester_id = input("卖家玩家 ID：").strip()
        listing = self.app.market_service.get_listing(lid)

        item_name = self._get_item_display_name(listing.item_id)
        if not prompt_confirm(f"确认撤销挂单 {lid}（{item_name} x{listing.count}）？"):
            print("已取消")
            self._pause()
            return

        # 保存撤销前的状态
        old_status = listing.status
        old_closed_at = listing.closed_at
        seller = self.repo.players.get(listing.seller_id)
        # Player.inventory 是 list[dict]，需要深拷贝避免引用共享
        old_inventory = copy.deepcopy(seller.inventory) if seller else []

        self.app.market_service.cancel_listing(lid, requester_id)

        # 成功后压栈撤销操作
        def undo():
            """恢复挂单状态和卖家背包"""
            listing.status = old_status
            listing.closed_at = old_closed_at
            if seller:
                seller.inventory = old_inventory
            self.persistence.save_market(self.repo)
            self.persistence.save_players(self.repo)

        self.op_stack.push(Operation(name=f"撤销挂单 {lid}", undo_fn=undo))
        print(f"[成功] 已撤销挂单 {lid}，物品已退回卖家背包")
        self._pause()

    def query_by_price_range(self) -> None:
        """按价格区间查询挂单"""
        min_p = prompt_optional_int("最低价格", default=0)
        max_p = prompt_optional_int("最高价格", default=999999)

        matches = self.app.market_service.query_by_price_range(min_p, max_p)
        print(f"\n价格区间 [{min_p}, {max_p}] 内有 {len(matches)} 个挂单：")

        sorted_matches = sorted(matches, key=lambda x: x.price)
        print_paginated(
            sorted_matches,
            formatter=lambda l: f"  {l.listing_id}: {self._get_item_display_name(l.item_id)} x{l.count} @ {l.price}",
            limit=10,
            unit="个"
        )

    def filter_by_category(self) -> None:
        """按物品分类筛选挂单"""
        category = input("分类路径（如 weapon.sword / misc）：").strip()
        matches = self.app.market_service.query_by_category(category)
        print(f"\n分类 {category} 下有 {len(matches)} 个活跃挂单：")

        print_paginated(
            matches,
            formatter=lambda l: f"  {l.listing_id}: {self._get_item_display_name(l.item_id)} x{l.count} @ {l.price}",
            limit=10,
            unit="个"
        )

    def filter_by_seller(self) -> None:
        """按卖家筛选挂单"""
        seller_id = input("卖家玩家 ID：").strip()
        matches = self.app.market_service.query_by_seller(seller_id)

        seller = self.repo.players.get(seller_id)
        seller_name = seller.name if seller else seller_id
        print(f"\n卖家 {seller_name} ({seller_id}) 有 {len(matches)} 个活跃挂单：")

        print_paginated(
            matches,
            formatter=lambda l: f"  {l.listing_id}: {self._get_item_display_name(l.item_id)} x{l.count} @ {l.price}",
            limit=10,
            unit="个"
        )

    def show_detail(self) -> None:
        """显示单条挂单详情"""
        listing_id = input("请输入挂单 ID：").strip()
        listing = self.app.market_service.get_listing(listing_id)
        seller = self.app.player_service.get_by_id(listing.seller_id)
        item = self.repo.items.get(listing.item_id)
        item_name = self._get_item_display_name(listing.item_id)
        total = listing.count * listing.price
        print("\n挂单详情")
        print("-" * 60)
        print(f"挂单 ID：{listing.listing_id}")
        print(f"状态：{listing.status}")
        print(f"卖家：{seller.name} ({seller.player_id})")
        print(f"物品：{item_name} ({listing.item_id})")
        if item is not None:
            print(f"分类：{item.category}")
            print(f"稀有度：{item.rarity}")
            print(f"基础价值：{item.base_value}")
            print(f"物品描述：{item.describe()}")
        print(f"数量：{listing.count}")
        print(f"单价：{listing.price}")
        print(f"总价：{total}")
        print(f"上架时间：{listing.created_at}")
        print(f"关闭时间：{listing.closed_at or '-'}")
        print(f"实例状态：{listing.instance_state or '-'}")

        history = self.app.transaction_service.by_item(listing.item_id)
        if not history:
            print("历史价格参考：暂无成交记录")
            self._pause()
            return

        stats = self.app.transaction_service.price_stats(listing.item_id)
        print(
            f"历史价格参考：最低 {stats['min']} / 最高 {stats['max']} / "
            f"平均 {stats['avg']:.2f} / 共 {stats['count']} 笔"
        )
        print("最近成交：")
        for txn in history[:5]:
            print(
                f"  {txn.completed_at}: {txn.transaction_id} "
                f"x{txn.count} @ {txn.price} = {txn.total}"
            )
        self._pause()

    def buy(self) -> None:
        """购买市场挂单"""
        lid = input("请输入要购买的挂单 ID：").strip()
        buyer_id = input("买家玩家 ID：").strip()
        listing = self.app.market_service.get_listing(lid)
        buyer = self.app.player_service.get_by_id(buyer_id)
        seller = self.app.player_service.get_by_id(listing.seller_id)

        item_name = self._get_item_display_name(listing.item_id)
        total = listing.count * listing.price
        print("\n请确认交易：")
        print(f"  买家：{buyer.name} ({buyer.player_id})")
        print(f"  卖家：{seller.name} ({seller.player_id})")
        print(f"  物品：{item_name} ({listing.item_id}) x{listing.count}")
        print(f"  单价：{listing.price}")
        print(f"  总价：{total}")
        if not prompt_confirm("确认购买？"):
            print("已取消")
            self._pause()
            return

        txn = self.app.market_service.buy(lid, buyer_id)
        print(f"[成功] 交易完成，交易记录：{txn.transaction_id}")
        self._pause()

    def settle_pending(self) -> None:
        """批量结算挂单（管理员）"""
        print("请输入待结算订单，每行格式：listing_id buyer_id；空行结束。")
        orders: list[tuple[str, str]] = []
        while True:
            line = input("订单：").strip()
            if not line:
                break
            parts = line.split()
            if len(parts) != 2:
                print("[提示] 格式应为：listing_id buyer_id")
                continue
            orders.append((parts[0], parts[1]))

        if not orders:
            print("未输入待结算订单")
            self._pause()
            return

        txns = self.app.market_service.settle_pending(orders)
        print(f"[完成] 成功结算 {len(txns)} / {len(orders)} 条订单")
        for txn in txns:
            print(f"  {txn.transaction_id}: {txn.listing_id} -> {txn.buyer_id}, total={txn.total}")
        self._pause()

    def sort_listings(self) -> None:
        """排序展示挂单"""
        sort_by = prompt_choice(
            "排序方式 (1=价格升序, 2=价格降序, 3=时间升序, 4=时间降序)",
            {"1", "2", "3", "4"}
        )

        if sort_by == "1":
            sorted_list = self.app.market_service.list_active(sort_by="price", desc=False)
        elif sort_by == "2":
            sorted_list = self.app.market_service.list_active(sort_by="price", desc=True)
        elif sort_by == "3":
            sorted_list = self.app.market_service.list_active(sort_by="created_at", desc=False)
        else:
            sorted_list = self.app.market_service.list_active(sort_by="created_at", desc=True)

        print(f"\n排序后挂单：")
        print_paginated(
            sorted_list,
            formatter=lambda l: f"  {l.listing_id}: {self._get_item_display_name(l.item_id)} @ {l.price}",
            limit=10,
            unit="个"
        )
