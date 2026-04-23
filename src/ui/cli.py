"""命令行交互主循环、菜单、输入校验（功能 ID 6-9）

职责：
- 显示主菜单及各级子菜单（功能 ID 6）
- 数字/字母导航，进入子菜单或返回（功能 ID 7）
- 非法输入处理，抛 InvalidInputError 并重新显示（功能 ID 8）
- 操作撤销栈，支持撤销可逆操作（功能 ID 9）

调用方式：
    from src.app import App
    from src.ui.cli import run_cli
    App(ui_runner=run_cli).run()


目前只是粗略地做一下 cli。如果想做得更精美的话可以直接邮箱告诉我（
要不把 tui 也做了？（
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from src.errors import InvalidInputError, TradingSystemError

if TYPE_CHECKING:
    from src.app import App


__all__ = ["run_cli"]




# -----------------------------------------------------------------------------
# 操作撤销栈（功能 ID 9）
# -----------------------------------------------------------------------------

@dataclass
class Operation:
    """可撤销的操作记录"""

    name: str                           # 操作名称（如"撤销挂单 l_001"）
    undo_fn: Callable[[], None]         # 撤销函数
    context: dict = field(default_factory=dict)  # 上下文数据（用于日志）


class OperationStack:
    """自实现 Stack，支持撤销最近 N 步可逆操作

    要求的数据结构演示点：
    - 后进先出（LIFO）语义：pop() 取最近 push 的操作
    - 容量上限与淘汰策略：FIFO 淘汰最旧操作
    """

    def __init__(self, max_size: int = 20) -> None:
        self._stack: list[Operation] = []
        self._max_size = max_size

    def push(self, op: Operation) -> None:
        """压栈，超限时淘汰最早的操作（FIFO 淘汰）"""
        if len(self._stack) >= self._max_size:
            self._stack.pop(0)
        self._stack.append(op)

    def pop(self) -> Operation | None:
        """弹栈，空栈返回 None"""
        return self._stack.pop() if self._stack else None

    def can_undo(self) -> bool:
        """检查是否有可撤销的操作"""
        return len(self._stack) > 0

    def __len__(self) -> int:
        return len(self._stack)




# -----------------------------------------------------------------------------
# CLI 主类
# -----------------------------------------------------------------------------

class TradingCLI:
    """交易系统的命令行界面"""

    def __init__(self, app: App) -> None:
        self.app = app
        self.repo = app.repo
        self.op_stack = OperationStack(max_size=20)


    # -------------------------------------------------------------------------
    # 入口
    # -------------------------------------------------------------------------

    def run(self) -> None:
        """主菜单循环，直到用户选择退出"""
        while True:
            try:
                self._clear_screen()
                choice = self._show_main_menu()

                if choice == "6" or choice.lower() == "q":
                    print("\n ……系统关闭…… \n\n")
                    break
                if choice == "0":
                    self._handle_undo()
                    continue

                self._handle_main_choice(choice)

            except InvalidInputError as e:
                print(f"\n[输入错误] {e.message}")
                self._pause()
            except TradingSystemError as e:
                print(f"\n[业务错误] {e.message}")
                self._pause()
            except Exception as e:
                # 进程级兜底任何未预期异常，都不应该导致崩溃
                print(f"\n[系统错误] {type(e).__name__}: {e}")
                self._pause()


    # -------------------------------------------------------------------------
    # 菜单显示
    # -------------------------------------------------------------------------

    def _show_main_menu(self) -> str:
        """显示主菜单并返回用户选择"""
        print("\n" + "=" * 40)
        print("           主  菜  单")
        print("=" * 40)
        print("  1. 玩家管理")
        print("  2. 物品管理")
        print("  3. 背包管理")
        print("  4. 交易市场")
        print("  5. 历史与报表")
        print("  6. 保存并退出")
        print("-" * 40)
        if self.op_stack.can_undo():
            print(f"  0. 撤销上一步 ({len(self.op_stack)} 步可撤销)")
        print("=" * 40)

        return self._prompt_choice(
            "请输入选项",
            valid_choices={"1", "2", "3", "4", "5", "6", "q", "Q"}
            | ({"0"} if self.op_stack.can_undo() else set())
        )


    def _show_player_menu(self) -> str:
        """玩家管理子菜单"""
        print("\n" + "=" * 40)
        print("         玩家管理")
        print("=" * 40)
        print("  1. 创建玩家")
        print("  2. 玩家列表")
        print("  3. 玩家详情")
        print("  4. 按 ID 查询")
        print("  5. 按名字搜索")
        print("  6. 修改玩家名")
        print("  7. 删除玩家")
        print("  8. 金币充值（调试）")
        print("-" * 40)
        print("  b. 返回主菜单")
        print("=" * 40)

        return self._prompt_choice(
            "请输入选项",
            valid_choices={"1", "2", "3", "4", "5", "6", "7", "8", "b", "B"}
        )


    def _show_item_menu(self) -> str:
        """物品管理子菜单"""
        print("\n" + "=" * 40)
        print("         物品管理")
        print("=" * 40)
        print("  1. 物品列表")
        print("  2. 物品详情")
        print("  3. 按 ID 查询")
        print("  4. 按分类浏览")
        print("-" * 40)
        print("  b. 返回主菜单")
        print("=" * 40)

        return self._prompt_choice(
            "请输入选项",
            valid_choices={"1", "2", "3", "4", "b", "B"}
        )


    def _show_inventory_menu(self) -> str:
        """背包管理子菜单"""
        print("\n" + "=" * 40)
        print("         背包管理")
        print("=" * 40)
        print("  1. 查看背包")
        print("  2. 按稀有度排序")
        print("  3. 移除物品")
        print("  4. 添加物品")
        print("  5. 容量信息")
        print("-" * 40)
        print("  b. 返回主菜单")
        print("=" * 40)

        return self._prompt_choice(
            "请输入选项",
            valid_choices={"1", "2", "3", "4", "5", "b", "B"}
        )


    def _show_market_menu(self) -> str:
        """交易市场子菜单"""
        print("\n" + "=" * 40)
        print("         交易市场")
        print("=" * 40)
        print("  1. 挂单上架")
        print("  2. 撤销挂单")
        print("  3. 浏览全部挂单")
        print("  4. 按价格区间查询")
        print("  5. 按分类筛选")
        print("  6. 挂单排序")
        print("  7. 购买物品")
        print("-" * 40)
        print("  b. 返回主菜单")
        print("=" * 40)

        return self._prompt_choice(
            "请输入选项",
            valid_choices={"1", "2", "3", "4", "5", "6", "7", "b", "B"}
        )


    def _show_report_menu(self) -> str:
        """历史与报表子菜单"""
        print("\n" + "=" * 40)
        print("        历史与报表")
        print("=" * 40)
        print("  1. 玩家成交历史")
        print("  2. 物品成交历史")
        print("  3. 价格统计")
        print("  4. 嘉豪榜")
        print("  5. 交易额榜")
        print("  6. 系统数据快照")
        print("-" * 40)
        print("  b. 返回主菜单")
        print("=" * 40)

        return self._prompt_choice(
            "请输入选项",
            valid_choices={"1", "2", "3", "4", "5", "6", "b", "B"}
        )


    # -------------------------------------------------------------------------
    # 菜单处理
    # -------------------------------------------------------------------------

    def _handle_main_choice(self, choice: str) -> None:
        """根据主菜单选择进入对应子菜单"""
        while True:
            try:
                if choice == "1":
                    sub_choice = self._show_player_menu()
                    if sub_choice.lower() == "b":
                        break
                    self._handle_player_choice(sub_choice)
                elif choice == "2":
                    sub_choice = self._show_item_menu()
                    if sub_choice.lower() == "b":
                        break
                    self._handle_item_choice(sub_choice)
                elif choice == "3":
                    sub_choice = self._show_inventory_menu()
                    if sub_choice.lower() == "b":
                        break
                    self._handle_inventory_choice(sub_choice)
                elif choice == "4":
                    sub_choice = self._show_market_menu()
                    if sub_choice.lower() == "b":
                        break
                    self._handle_market_choice(sub_choice)
                elif choice == "5":
                    sub_choice = self._show_report_menu()
                    if sub_choice.lower() == "b":
                        break
                    self._handle_report_choice(sub_choice)
                else:
                    # 输入已校验，理论上是不会走到这里的，但是防御性编程😋
                    raise InvalidInputError(field="choice", value=choice)
            except InvalidInputError as e:
                print(f"\n[输入错误] {e.message}")
                self._pause()
            except TradingSystemError as e:
                print(f"\n[业务错误] {e.message}")
                self._pause()
            except Exception as e:
                print(f"\n[系统错误] {type(e).__name__}: {e}")
                self._pause()


    def _handle_player_choice(self, choice: str) -> None:
        """玩家管理子菜单选择界面"""
        if choice == "1":
            print("\n[创建玩家] 功能待 PlayerService 实现")
        elif choice == "2":
            self._show_player_list()
        elif choice == "3":
            self._show_player_detail()
        elif choice == "4":
            self._query_player_by_id()
        elif choice == "5":
            self._search_player_by_name()
        elif choice == "6":
            print("\n[修改玩家] 功能待 PlayerService 实现")
        elif choice == "7":
            print("\n[删除玩家] 功能待 PlayerService 实现")
        elif choice == "8":
            self._add_gold_debug()
        self._pause()


    def _handle_item_choice(self, choice: str) -> None:
        """物品管理子菜单选择界面"""
        if choice == "1":
            self._show_item_list()
        elif choice == "2":
            self._show_item_detail()
        elif choice == "3":
            self._query_item_by_id()
        elif choice == "4":
            print("\n[按分类浏览] 功能待 CatalogTree 实现")
        self._pause()


    def _handle_inventory_choice(self, choice: str) -> None:
        """处理背包管理子菜单选择"""
        if choice == "1":
            self._show_inventory()
        elif choice == "2":
            print("\n[按稀有度排序] 功能待 Inventory 实现")
        elif choice == "3":
            print("\n[移除物品] 功能待 Inventory 实现")
        elif choice == "4":
            print("\n[添加物品] 功能待 Inventory 实现")
        elif choice == "5":
            print("\n[容量信息] 功能待 Inventory 实现")
        self._pause()


    def _handle_market_choice(self, choice: str) -> None:
        """处理交易市场子菜单选择"""
        if choice == "1":
            print("\n[挂单上架] 功能待 MarketService 实现")
        elif choice == "2":
            self._cancel_listing()
        elif choice == "3":
            self._show_active_listings()
        elif choice == "4":
            self._query_by_price_range()
        elif choice == "5":
            print("\n[按分类筛选] 功能待 MarketService 实现")
        elif choice == "6":
            self._sort_listings()
        elif choice == "7":
            print("\n[购买物品] 功能待 MarketService 实现")
        self._pause()


    def _handle_report_choice(self, choice: str) -> None:
        """处理历史与报表子菜单选择"""
        if choice == "1":
            self._show_player_transactions()
        elif choice == "2":
            self._show_item_transactions()
        elif choice == "3":
            self._show_price_stats()
        elif choice == "4":
            self._show_top_gold()
        elif choice == "5":
            self._show_top_volume()
        elif choice == "6":
            self._show_system_snapshot()
        self._pause()


    def _handle_undo(self) -> None:
        """撤销上一步操作"""
        op = self.op_stack.pop()
        if op is None:
            print("\n[提示] 没有可撤销的操作")
            self._pause()
            return

        try:
            op.undo_fn()
            print(f"\n[撤销成功] 已撤销：{op.name}")
        except Exception as e:
            print(f"\n[撤销失败] {type(e).__name__}: {e}")
        self._pause()


    # -------------------------------------------------------------------------
    # 功能实现
    # -------------------------------------------------------------------------

    def _show_player_list(self) -> None:
        """显示玩家列表"""
        players = self.app.player_service.list_all()
        print(f"\n共有 {len(players)} 名玩家：")
        print("-" * 50)
        print(f"{'ID':<10} {'名字':<12} {'金币':>8} {'等级':>4}")
        print("-" * 50)
        for p in players:
            print(f"{p.player_id:<10} {p.name:<12} {p.gold:>8} {p.level:>4}")


    def _show_player_detail(self) -> None:
        """显示玩家详情"""
        pid = input("请输入玩家 ID：").strip()
        player = self.repo.players.get(pid)
        if not player:
            print(f"[提示] 玩家 {pid} 不存在")
            return

        print(f"\n{'='*40}")
        print(f"玩家：{player.name} ({player.player_id})")
        print(f"{'='*40}")
        print(f"  金币：{player.gold}")
        print(f"  等级：{player.level}")
        print(f"  职业：{player.klass}")
        print(f"  背包：{len(player.inventory)} 件物品")
        if player.inventory:
            for slot in player.inventory:
                print(f"    - {slot.get('item_id', 'unknown')} x{slot.get('count', 1)}")
        print(f"{'='*40}")


    def _query_player_by_id(self) -> None:
        """按 ID 查询玩家"""
        pid = input("请输入玩家 ID：").strip()
        try:
            player = self.app.player_service.get_by_id(pid)
            print(f"\n找到玩家：{player.name}，金币 {player.gold}，等级 {player.level}")
        except TradingSystemError as e:
            print(f"[提示] {e.message}")


    def _search_player_by_name(self) -> None:
        """按名字模糊查询玩家"""
        keyword = input("请输入名字关键词：").strip().lower()
        matches = self.app.player_service.search_by_name(keyword)
        print(f"\n找到 {len(matches)} 名匹配的玩家：")
        for p in matches:
            print(f"  {p.player_id}: {p.name} (金币 {p.gold})")


    def _add_gold_debug(self) -> None:
        """金币充值（调试功能）"""
        pid = input("请输入玩家 ID：").strip()
        amount_str = input("请输入充值金额：").strip()
        try:
            amount = int(amount_str)
        except ValueError:
            raise InvalidInputError(field="amount", value=amount_str)

        self.app.player_service.add_gold(pid, amount)
        player = self.app.player_service.get_by_id(pid)
        print(f"[成功] 已为 {player.name} 充值 {amount} 金币，当前 {player.gold}")


    def _show_item_list(self) -> None:
        """显示物品列表"""
        items = self.app.item_service.list_all()
        print(f"\n共有 {len(items)} 件物品：")
        print("-" * 50)
        print(f"{'ID':<10} {'分类':<20} {'稀有度':<8}")
        print("-" * 50)
        for item in items:
            cat = item.get('category', 'unknown')
            rarity = item.get('rarity', 'unknown')
            print(f"{item['item_id']:<10} {cat:<20} {rarity:<8}")


    def _show_item_detail(self) -> None:
        """显示物品详情"""
        iid = input("请输入物品 ID：").strip()
        item = self.repo.items.get(iid)
        if not item:
            print(f"[提示] 物品 {iid} 不存在")
            return

        print(f"\n{'='*40}")
        print(f"物品：{item.get('name', 'Unknown')} ({iid})")
        print(f"{'='*40}")
        for k, v in sorted(item.items()):
            if k != 'item_id':
                print(f"  {k}: {v}")
        print(f"{'='*40}")


    def _query_item_by_id(self) -> None:
        """按 ID 查询物品"""
        iid = input("请输入物品 ID：").strip()
        try:
            item = self.app.item_service.get_by_id(iid)
            name = item.get('name', 'Unknown')
            cat = item.get('category', 'unknown')
            print(f"\n找到物品：{name} (分类：{cat})")
        except TradingSystemError as e:
            print(f"[提示] {e.message}")


    def _show_inventory(self) -> None:
        """查看玩家背包"""
        pid = input("请输入玩家 ID：").strip()
        player = self.repo.players.get(pid)
        if not player:
            print(f"[提示] 玩家 {pid} 不存在")
            return

        print(f"\n玩家 {player.name} 的背包：")
        print("-" * 40)
        if not player.inventory:
            print("  （空）")
        else:
            for i, slot in enumerate(player.inventory, 1):
                iid = slot.get('item_id', 'unknown')
                item = self.repo.items.get(iid, {})
                name = item.get('name', iid)
                print(f"  {i}. {name} x{slot.get('count', 1)}")


    def _show_active_listings(self) -> None:
        """显示活跃挂单"""
        active = self.app.market_service.list_active()
        print(f"\n共有 {len(active)} 个活跃挂单：")
        print("-" * 60)
        print(f"{'挂单ID':<10} {'卖家':<10} {'物品':<10} {'数量':>4} {'单价':>8}")
        print("-" * 60)
        for l in active[:20]:
            seller = self.repo.players.get(l.seller_id, None)
            seller_name = seller.name if seller else l.seller_id[:8]
            item = self.repo.items.get(l.item_id, {})
            item_name = item.get('name', l.item_id[:8])
            print(f"{l.listing_id:<10} {seller_name:<10} {item_name:<10} {l.count:>4} {l.price:>8}")
        if len(active) > 20:
            print(f"  ... 还有 {len(active)-20} 个挂单未显示")


    def _cancel_listing(self) -> None:
        """撤销挂单（支持撤销）"""
        lid = input("请输入要撤销的挂单 ID：").strip()
        listing = self.repo.listings.get(lid)
        if not listing:
            print(f"[提示] 挂单 {lid} 不存在")
            return
        if listing.status != "active":
            print(f"[提示] 挂单 {lid} 不是活跃状态，无法撤销")
            return

        confirm = input(f"确认撤销挂单 {lid}？此操作可撤销 (y/n)：").strip().lower()
        if confirm != "y":
            print("已取消")
            return

        old_status = listing.status
        listing.status = "cancelled"
        self.app.persistence.save_market(self.repo)

        def undo():
            listing.status = old_status
            self.app.persistence.save_market(self.repo)

        self.op_stack.push(Operation(
            name=f"撤销挂单 {lid}",
            undo_fn=undo,
            context={"listing_id": lid}
        ))
        print(f"[成功] 已撤销挂单 {lid}")


    def _query_by_price_range(self) -> None:
        """按价格区间查询挂单"""
        try:
            min_p = int(input("最低价格：").strip() or "0")
            max_p = int(input("最高价格：").strip() or "999999")
        except ValueError:
            raise InvalidInputError(field="price", value="non-numeric")

        matches = self.app.market_service.query_by_price_range(min_p, max_p)
        print(f"\n价格区间 [{min_p}, {max_p}] 内有 {len(matches)} 个挂单：")
        for l in sorted(matches, key=lambda x: x.price)[:10]:
            item = self.repo.items.get(l.item_id, {})
            name = item.get('name', l.item_id[:8])
            print(f"  {l.listing_id}: {name} x{l.count} @ {l.price}")
        if len(matches) > 10:
            print(f"  ... 还有 {len(matches)-10} 个")


    def _sort_listings(self) -> None:
        """排序展示挂单"""
        sort_by = input("排序方式 (1=价格升序, 2=价格降序, 3=时间升序, 4=时间降序)：").strip()

        if sort_by == "1":
            sorted_list = self.app.market_service.list_active(sort_by="price", desc=False)
        elif sort_by == "2":
            sorted_list = self.app.market_service.list_active(sort_by="price", desc=True)
        elif sort_by == "3":
            sorted_list = self.app.market_service.list_active(sort_by="created_at", desc=False)
        elif sort_by == "4":
            sorted_list = self.app.market_service.list_active(sort_by="created_at", desc=True)
        else:
            raise InvalidInputError(field="sort_by", value=sort_by)

        print(f"\n排序后前 10 个挂单：")
        for l in sorted_list[:10]:
            item = self.repo.items.get(l.item_id, {})
            name = item.get('name', l.item_id[:8])
            print(f"  {l.listing_id}: {name} @ {l.price}")


    def _show_player_transactions(self) -> None:
        """显示玩家成交历史"""
        pid = input("请输入玩家 ID：").strip()
        player = self.app.player_service.get_by_id(pid)
        txns = self.app.transaction_service.by_player(pid)
        print(f"\n玩家 {player.name} 的成交记录（共 {len(txns)} 条）：")
        print("-" * 90)
        if not txns:
            print("  该玩家暂无成交记录")
            return
        shown = txns[:20]
        for t in shown:
            role = "买" if t.buyer_id == pid else "卖"
            other = t.seller_id if t.buyer_id == pid else t.buyer_id
            item = self.repo.items.get(t.item_id, {})
            item_name = item.get("name", t.item_id)
            print(
                f"  {t.completed_at} [{role}] {item_name}({t.item_id}) "
                f"x{t.count} @ {t.price} = {t.total} → {other}"
            )
        if len(txns) > len(shown):
            print(f"  ... 还有 {len(txns) - len(shown)} 条未显示")


    def _show_item_transactions(self) -> None:
        """显示物品成交历史（支持按 item_id / 分类）"""
        mode = self._prompt_choice("查询方式 (1=item_id, 2=类型/分类)", {"1", "2"})
        if mode == "1":
            item_id = input("请输入 item_id：").strip()
            item = self.app.item_service.get_by_id(item_id)
            txns = self.app.transaction_service.by_item(item_id)
            title = f"物品成交历史：{item.get('name', item_id)} ({item_id})"
        else:
            category = input("请输入类型/分类（如 weapon / weapon.sword / misc）：").strip()
            txns = self.app.transaction_service.by_category(category)
            title = f"分类成交历史：{category}"

        print(f"\n{title}（共 {len(txns)} 条）：")
        print("-" * 100)
        if not txns:
            print("  该物品/类型暂无成交记录")
            return
        shown = txns[:20]
        for t in shown:
            item = self.repo.items.get(t.item_id, {})
            item_name = item.get("name", t.item_id)
            print(
                f"  {t.completed_at} {item_name}({t.item_id}) "
                f"买家={t.buyer_id} 卖家={t.seller_id} x{t.count} @ {t.price} = {t.total}"
            )
        if len(txns) > len(shown):
            print(f"  ... 还有 {len(txns) - len(shown)} 条未显示")


    def _show_price_stats(self) -> None:
        """显示价格统计（支持按 item_id / 分类）"""
        mode = self._prompt_choice("统计方式 (1=item_id, 2=类型/分类)", {"1", "2"})
        try:
            if mode == "1":
                item_id = input("请输入 item_id：").strip()
                item = self.app.item_service.get_by_id(item_id)
                stats = self.app.transaction_service.price_stats(item_id)
                label = f"{item.get('name', item_id)} ({item_id})"
            else:
                category = input("请输入类型/分类（如 weapon / weapon.sword / misc）：").strip()
                stats = self.app.transaction_service.price_stats_by_category(category)
                label = category
        except InvalidInputError:
            print("\n该物品/类型暂无成交数据")
            return

        print(f"\n价格统计：{label}")
        print("-" * 40)
        print(f"  成交次数：{stats['count']}")
        print(f"  最低成交价：{stats['min']}")
        print(f"  最高成交价：{stats['max']}")
        print(f"  平均成交价：{stats['avg']:.2f}")


    def _show_top_gold(self) -> None:
        """富豪榜"""
        players = self.app.transaction_service.top_by_gold(10)
        print("\n嘉豪榜 Top 10：")
        print("-" * 40)
        print(f"{'排名':<6} {'玩家':<15} {'金币':>10}")
        print("-" * 40)
        for i, p in enumerate(players, 1):
            print(f"{i:<6} {p.name:<15} {p.gold:>10}")


    def _show_top_volume(self) -> None:
        """交易额榜"""
        ranked = self.app.transaction_service.top_by_volume(10)
        print("\n交易额榜 Top 10：")
        print("-" * 44)
        print(f"{'排名':<6} {'玩家':<15} {'成交额':>12}")
        print("-" * 44)
        if not ranked:
            print("  暂无交易额数据")
            return
        for i, (player, volume) in enumerate(ranked, 1):
            print(f"{i:<6} {player.name:<15} {volume:>12}")


    def _show_system_snapshot(self) -> None:
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


    # -------------------------------------------------------------------------
    # 工具方法
    # -------------------------------------------------------------------------

    def _prompt_choice(self, prompt: str, valid_choices: set[str]) -> str:
        """提示用户输入并校验合法性"""
        user_input = input(f"{prompt}：").strip()
        if user_input not in valid_choices:
            raise InvalidInputError(field="choice", value=user_input)
        return user_input


    def _pause(self) -> None:
        """暂停等待用户按键"""
        try:
            input("\n按回车继续...")
        except EOFError:
            pass


    def _clear_screen(self) -> None:
        """清屏（跨平台）"""
        try:
            os.system("cls" if sys.platform == "win32" else "clear")
        except Exception:
            pass




# -----------------------------------------------------------------------------
# 入口函数
# -----------------------------------------------------------------------------

def run_cli(app: App) -> None:
    """CLI 入口，由 App.ui_runner 调用"""
    cli = TradingCLI(app)
    cli.run()
