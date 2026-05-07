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

"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

from src.errors import BusinessRuleError, InvalidInputError, TradingSystemError
from src.structures import Stack

if TYPE_CHECKING:
    from src.app import App
    from src.models import Player

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


# OperationStack 现在直接使用 structures.Stack
OperationStack = Stack


# -----------------------------------------------------------------------------
# CLI 主类
# -----------------------------------------------------------------------------




class TradingCLI:
    """交易系统的命令行界面"""

    _DETAIL_LIST_LIMIT = 10

    def __init__(self, app: App) -> None:
        self.app = app
        self.repo = app.repo
        self.persistence = app.persistence
        self.op_stack: Stack = Stack(max_size=20)

        from src.services.player_inventory_service import PlayerInventoryService
        self.inventory_service = PlayerInventoryService(self.repo, self.persistence)


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
        if not self.op_stack.is_empty():
            print(f"  0. 撤销上一步 ({len(self.op_stack)} 步可撤销)")
        print("=" * 40)
        return self._prompt_choice(
            "请输入选项",
            valid_choices={"1", "2", "3", "4", "5", "6", "q", "Q"}
            | ({"0"} if not self.op_stack.is_empty() else set())
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
        print("  5. 创建物品（管理员）")
        print("  6. 删除物品（管理员）")
        print("-" * 40)
        print("  b. 返回主菜单")
        print("=" * 40)
        return self._prompt_choice(
            "请输入选项",
            valid_choices={"1", "2", "3", "4", "5", "6", "b", "B"}
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
        print("  6. 按卖家筛选")
        print("  7. 挂单详情")
        print("  8. 挂单排序")
        print("  9. 购买物品")
        print("  10. 批量结算挂单（管理员）")
        print("-" * 40)
        print("  b. 返回主菜单")
        print("=" * 40)
        return self._prompt_choice(
            "请输入选项",
            valid_choices={"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "b", "B"}
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
            self._create_player()
        elif choice == "2":
            self._show_player_list()
        elif choice == "3":
            self._show_player_detail()
        elif choice == "4":
            self._query_player_by_id()
        elif choice == "5":
            self._search_player_by_name()
        elif choice == "6":
            self._rename_player()
        elif choice == "7":
            self._delete_player()
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
            self._browse_items_by_category()
        elif choice == "5":
            self._create_item()
        elif choice == "6":
            self._delete_item()
        self._pause()


    def _handle_inventory_choice(self, choice: str) -> None:
        """处理背包管理子菜单选择"""
        if choice == "1":
            self._show_inventory()
        elif choice == "2":
            self._show_inventory_sorted()
        elif choice == "3":
            self._remove_item_from_inventory()
        elif choice == "4":
            self._add_item_to_inventory()
        elif choice == "5":
            self._show_inventory_capacity()
        self._pause()


    def _show_inventory_sorted(self) -> None:
        """按稀有度排序查看背包"""
        pid = input("请输入玩家 ID：").strip()
        try:
            sorted_slots = self.inventory_service.get_sorted_view(pid, key="rarity")
            player = self.repo.players.get(pid)
            if player is None:
                print(f"[提示] 玩家 {pid} 不存在")
                return
        except Exception as e:
            print(f"[提示] {getattr(e, 'message', str(e))}")
            return
        print(f"\n玩家 {player.name} 的背包（按稀有度排序）：")
        print("-" * 40)
        if not sorted_slots:
            print("  （空）")
        else:
            for i, slot in enumerate(sorted_slots, 1):
                print(f"  {i}. {slot.get_display_name()} [{slot.get_rarity()}] x{slot.count}")
        print(f"-" * 40)
        info = self.inventory_service.get_capacity_info(pid)
        print(f"  已用槽位：{info['used']} / {info['capacity']}")


    def _remove_item_from_inventory(self) -> None:
        """从背包移除物品"""
        pid = input("请输入玩家 ID：").strip()
        item_id = input("请输入要移除的物品 ID：").strip()
        count_str = input("请输入移除数量（默认 1）：").strip()
        count = int(count_str) if count_str.isdigit() else 1
        try:
            self.inventory_service.remove_item(pid, item_id, count)
            print(f"[成功] 已从背包移除 {count} 个 {item_id}")
        except Exception as e:
            print(f"[提示] {getattr(e, 'message', str(e))}")


    def _add_item_to_inventory(self) -> None:
        """向背包添加物品（管理员调试用）"""
        pid = input("请输入玩家 ID：").strip()
        item_id = input("请输入要添加的物品 ID：").strip()
        count_str = input("请输入添加数量（默认 1）：").strip()
        count = int(count_str) if count_str.isdigit() else 1
        try:
            self.inventory_service.add_item(pid, item_id, count)
            item = self.repo.items.get(item_id)
            item_name = item.name if item else item_id
            print(f"[成功] 已向背包添加 {count} 个 {item_name}")
        except Exception as e:
            print(f"[提示] {getattr(e, 'message', str(e))}")


    def _show_inventory_capacity(self) -> None:
        """显示背包容量信息"""
        pid = input("请输入玩家 ID：").strip()
        try:
            info = self.inventory_service.get_capacity_info(pid)
            player = self.repo.players.get(pid)
            if player is None:
                print(f"[提示] 玩家 {pid} 不存在")
                return
        except Exception as e:
            print(f"[提示] {getattr(e, 'message', str(e))}")
            return
        print(f"\n玩家 {player.name} 的背包容量：")
        print(f"  总容量：{info['capacity']}")
        print(f"  已用槽位：{info['used']}")
        print(f"  剩余槽位：{info['remaining']}")
        print(f"  状态：{'已满' if info['is_full'] else '可用'}")


    def _handle_market_choice(self, choice: str) -> None:
        """处理交易市场子菜单选择"""
        if choice == "1":
            self._create_listing()
        elif choice == "2":
            self._cancel_listing()
        elif choice == "3":
            self._show_active_listings()
        elif choice == "4":
            self._query_by_price_range()
        elif choice == "5":
            self._filter_listings_by_category()
        elif choice == "6":
            self._filter_listings_by_seller()
        elif choice == "7":
            self._show_listing_detail()
        elif choice == "8":
            self._sort_listings()
        elif choice == "9":
            self._buy_listing()
        elif choice == "10":
            self._settle_pending_listings()
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


    def _create_player(self) -> None:
        """创建玩家"""
        name = input("玩家名：").strip()
        gold = self._prompt_int_with_default("初始金币", 0)
        level = self._prompt_int_with_default("初始等级", 1)
        klass = input("职业（warrior/archer/mage/summon/none，默认 none）：").strip() or "none"
        try:
            player = self.app.player_service.create_player(name, gold=gold, level=level, klass=klass)
        except TradingSystemError as e:
            print(f"[提示] {e.message}")
            return
        print(f"[成功] 已创建玩家：{player.name} ({player.player_id})，金币 {player.gold}，等级 {player.level}，职业 {player.klass}")


    def _show_player_list(self) -> None:
        """显示玩家列表"""
        sort_choice = input("排序方式（1=ID, 2=名字, 3=金币降序, 4=金币升序，默认 1）：").strip() or "1"
        if sort_choice == "1":
            players = self.app.player_service.list_all(sort_by="id")
        elif sort_choice == "2":
            players = self.app.player_service.list_all(sort_by="name")
        elif sort_choice == "3":
            players = self.app.player_service.list_all(sort_by="gold", desc=True)
        elif sort_choice == "4":
            players = self.app.player_service.list_all(sort_by="gold")
        else:
            raise InvalidInputError(field="sort_by", value=sort_choice)
        print(f"\n共有 {len(players)} 名玩家：")
        print("-" * 66)
        print(f"{'ID':<10} {'名字':<12} {'金币':>8} {'等级':>4} {'背包数量':>8}")
        print("-" * 66)
        for p in players:
            inventory_count = len(p.inventory)
            print(f"{p.player_id:<10} {p.name:<12} {p.gold:>8} {p.level:>4} {inventory_count:>8}")


    def _show_player_detail(self) -> None:
        """显示玩家详情（聚合基本信息、背包、挂单、交易）"""
        pid = input("请输入玩家 ID：").strip()
        try:
            player = self.app.player_service.get_by_id(pid)
        except TradingSystemError as e:
            print(f"[提示] {e.message}")
            return
        print(f"\n{'='*60}")
        print(f"玩家：{player.name} ({player.player_id})")
        print(f"{'='*60}")
        self._print_player_basic_info(player)
        self._print_player_inventory(pid)
        self._print_player_listings(pid)
        self._print_player_transactions(player.player_id)
        print(f"{'='*60}")


    def _print_player_basic_info(self, player: "Player") -> None:
        print(f"  金币：{player.gold}")
        print(f"  等级：{player.level}")
        print(f"  职业：{player.klass}")
        print(f"  创建时间：{player.created_at or '-'}")


    def _print_player_inventory(self, pid: str) -> None:
        print("\n背包内容：")
        try:
            slots = self.inventory_service.get_slots(pid)
        except TradingSystemError as e:
            print(f"  [提示] {e.message}")
            slots = []
        if not slots:
            print("  （空）")
        else:
            for slot in slots:
                print(f"  - {slot.get_display_name()} [{slot.get_rarity()}] x{slot.count}")


    def _print_player_listings(self, pid: str) -> None:
        listings = self.app.market_service.query_by_seller(pid)
        print(f"\n活跃挂单：{len(listings)} 个")
        if not listings:
            print("  （无）")
        else:
            for listing in listings[:self._DETAIL_LIST_LIMIT]:
                item_name = self._resolve_item_name(listing.item_id)
                print(f"  - {listing.listing_id}: {item_name} x{listing.count} @ {listing.price}")
            if len(listings) > self._DETAIL_LIST_LIMIT:
                print(f"  ... 还有 {len(listings) - self._DETAIL_LIST_LIMIT} 个")


    def _print_player_transactions(self, player_id: str) -> None:
        txns = self.app.transaction_service.by_player(player_id)
        print(f"\n历史成交：{len(txns)} 条")
        if not txns:
            print("  （无）")
        else:
            for txn in txns[:self._DETAIL_LIST_LIMIT]:
                role = "买" if txn.buyer_id == player_id else "卖"
                item_name = self._resolve_item_name(txn.item_id)
                print(f"  - {txn.completed_at} [{role}] {item_name} x{txn.count} @ {txn.price} = {txn.total}")
            if len(txns) > self._DETAIL_LIST_LIMIT:
                print(f"  ... 还有 {len(txns) - self._DETAIL_LIST_LIMIT} 条")

    def _resolve_item_name(self, item_id: str) -> str:
        try:
            item = self.app.item_service.get_by_id(item_id)
            return item.name
        except TradingSystemError:
            return item_id


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


    def _rename_player(self) -> None:
        """修改玩家名"""
        pid = input("请输入玩家 ID：").strip()
        new_name = input("请输入新名字：").strip()
        try:
            old_name = self.app.player_service.get_by_id(pid).name
            self.app.player_service.rename(pid, new_name)
            player = self.app.player_service.get_by_id(pid)
        except TradingSystemError as e:
            print(f"[提示] {e.message}")
            return
        print(f"[成功] 已将玩家 {pid} 从 {old_name} 改名为 {player.name}")


    def _delete_player(self) -> None:
        """删除玩家"""
        pid = input("请输入要删除的玩家 ID：").strip()
        try:
            player = self.app.player_service.get_by_id(pid)
        except TradingSystemError as e:
            print(f"[提示] {e.message}")
            return
        confirm = input(f"确认删除玩家 {player.name} ({player.player_id})？此操作不可撤销 (y/n)：").strip().lower()
        if confirm != "y":
            print("已取消")
            return
        try:
            self.app.player_service.delete(pid)
        except TradingSystemError as e:
            print(f"[提示] {e.message}")
            return
        print(f"[成功] 已删除玩家 {player.name} ({player.player_id})")


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
        print("-" * 62)
        print(f"{'ID':<10} {'分类':<20} {'稀有度':<8} {'基础价值':>8}")
        print("-" * 62)
        for item in items:
            cat = item.category
            rarity = item.rarity
            print(f"{item.item_id:<10} {cat:<20} {rarity:<8} {item.base_value:>8}")


    def _show_item_detail(self) -> None:
        """显示物品详情"""
        iid = input("请输入物品 ID：").strip()
        try:
            item = self.app.item_service.get_by_id(iid)
        except Exception:
            print(f"[提示] 物品 {iid} 不存在")
            return
        print(f"\n{'='*40}")
        print(f"物品：{item.name} ({iid})")
        print(f"{'='*40}")
        print(f"  分类：{item.category}")
        print(f"  稀有度：{item.rarity}")
        print(f"  基础价值：{item.base_value}")
        if item.description:
            print(f"  描述：{item.description}")
        print(f"  {item.describe()}")
        print(f"{'='*40}")


    def _query_item_by_id(self) -> None:
        """按 ID 查询物品"""
        iid = input("请输入物品 ID：").strip()
        try:
            item = self.app.item_service.get_by_id(iid)
            print(f"\n找到物品：{item.name} (分类：{item.category})")
        except TradingSystemError as e:
            print(f"[提示] {e.message}")


    def _browse_items_by_category(self) -> None:
        """按 CatalogTree 分类浏览物品"""
        root = self.app.item_service.browse_catalog("root")
        print("\n分类目录：")
        self._print_catalog_node(root)
        category = input("请输入分类路径（如 weapon / weapon.sword / misc，留空=root）：").strip() or "root"
        try:
            items = self.app.item_service.items_in_category(category)
        except TradingSystemError as e:
            print(f"[提示] {e.message}")
            return
        print(f"\n分类 {category} 下共有 {len(items)} 件物品：")
        print("-" * 60)
        if not items:
            print("  暂无物品")
            return
        for item in items[:20]:
            print(f"  {item.item_id:<10} {item.name:<16} {item.category:<20} {item.rarity}")
        if len(items) > 20:
            print(f"  ... 还有 {len(items) - 20} 件未显示")


    def _create_item(self) -> None:
        """创建物品（管理员）"""
        name = input("物品名称：").strip()
        category = input("分类（如 weapon.sword / misc）：").strip()
        rarity = input("稀有度（common/uncommon/rare/epic/legendary）：").strip()
        base_value_str = input("基础价值：").strip()
        description = input("描述（可留空）：").strip()
        try:
            base_value = int(base_value_str)
        except ValueError:
            raise InvalidInputError(field="base_value", value=base_value_str)
        stats = self._prompt_item_stats(category)
        payload = {
            "name": name,
            "category": category,
            "rarity": rarity,
            "base_value": base_value,
            "description": description,
            "stats": stats,
        }
        item = self.app.item_service.create_item(payload)
        print(f"[成功] 已创建物品：{item.name} ({item.item_id})")


    def _delete_item(self) -> None:
        """删除物品（管理员）"""
        item_id = input("请输入要删除的物品 ID：").strip()
        try:
            item = self.app.item_service.get_by_id(item_id)
        except TradingSystemError as e:
            print(f"[提示] {e.message}")
            return
        print(f"\n待删除物品：{item.describe()}")
        confirm = input(f"确认删除 {item.name} ({item.item_id})？此操作不可撤销 (y/n)：").strip().lower()
        if confirm != "y":
            print("已取消")
            return
        try:
            self.app.item_service.delete_item(item_id)
            print(f"[成功] 已删除物品 {item_id}")
        except BusinessRuleError as e:
            print(f"[业务错误] {e.message}")
        except TradingSystemError as e:
            print(f"[提示] {e.message}")


    def _print_catalog_node(self, node, depth: int = 0, path: str = "") -> None:
        current_path = node.key if node.key != "root" else "root"
        if path and node.key != "root":
            current_path = f"{path}.{node.key}" if path != "root" else node.key
        indent = "  " * depth
        suffix = f" ({current_path})" if node.key != "root" else ""
        print(f"{indent}- {node.label}{suffix}")
        for child in node.children:
            self._print_catalog_node(child, depth + 1, current_path)


    def _prompt_item_stats(self, category: str) -> dict:
        if category.startswith("weapon."):
            return {
                "attack": self._prompt_int("攻击"),
                "attack_speed": self._prompt_float("攻速"),
                "durability_max": self._prompt_int("最大耐久"),
                "durability": self._prompt_optional_int("当前耐久", None),
                "equipped": False,
                "slot": "weapon",
                "level_req": self._prompt_optional_int("等级要求", 0),
                "class_req": self._prompt_class_req(),
            }
        if category.startswith("tool."):
            return {
                "efficiency": self._prompt_float("效率"),
                "tier": self._prompt_int("工具等级"),
                "durability_max": self._prompt_int("最大耐久"),
                "durability": self._prompt_optional_int("当前耐久", None),
                "level_req": self._prompt_optional_int("等级要求", 0),
                "class_req": self._prompt_class_req(),
            }
        if category.startswith("armor."):
            slot = category.split(".", 1)[1]
            return {
                "defense": self._prompt_int("防御"),
                "magic_resist": self._prompt_int("魔抗"),
                "durability_max": self._prompt_int("最大耐久"),
                "durability": self._prompt_optional_int("当前耐久", None),
                "equipped": False,
                "slot": slot,
                "level_req": self._prompt_optional_int("等级要求", 0),
                "class_req": self._prompt_class_req(),
            }
        if category == "consumable.potion":
            return {
                "effect": input("效果：").strip(),
                "power": self._prompt_int("效果强度"),
                "duration": self._prompt_optional_int("持续时间", 0),
                "stack_size_max": self._prompt_int("最大堆叠"),
                "count": self._prompt_optional_int("默认数量", 1),
            }
        if category == "consumable.food":
            stats = self._prompt_consumable_stats()
            stats["nutrition"] = self._prompt_optional_int("营养值", 0)
            return stats
        if category == "consumable.magic":
            stats = self._prompt_consumable_stats()
            stats["mana_cost"] = self._prompt_optional_int("魔力消耗", 0)
            return stats
        if category == "consumable.material":
            return {
                "effect": input("效果（默认 none）：").strip() or "none",
                "power": self._prompt_optional_int("效果强度", 0),
                "duration": self._prompt_optional_int("持续时间", 0),
                "stack_size_max": self._prompt_int("最大堆叠"),
                "count": self._prompt_optional_int("默认数量", 1),
            }
        if category == "misc":
            return {
                "stack_size_max": self._prompt_int("最大堆叠"),
                "count": self._prompt_optional_int("默认数量", 1),
            }
        return {}


    def _prompt_consumable_stats(self) -> dict:
        return {
            "effect": input("效果：").strip(),
            "power": self._prompt_int("效果强度"),
            "duration": self._prompt_optional_int("持续时间", 0),
            "stack_size_max": self._prompt_int("最大堆叠"),
            "count": self._prompt_optional_int("默认数量", 1),
        }


    def _prompt_class_req(self) -> list[str]:
        raw = input("职业要求（逗号分隔，可留空）：").strip()
        if not raw:
            return []
        return [part.strip() for part in raw.split(",") if part.strip()]


    def _prompt_int(self, label: str) -> int:
        raw = input(f"{label}：").strip()
        try:
            return int(raw)
        except ValueError:
            raise InvalidInputError(field=label, value=raw)


    def _prompt_int_with_default(self, label: str, default: int) -> int:
        raw = input(f"{label}（默认 {default}）：").strip()
        if not raw:
            return default
        try:
            return int(raw)
        except ValueError:
            raise InvalidInputError(field=label, value=raw)


    def _prompt_optional_int(self, label: str, default: int | None) -> int | None:
        raw = input(f"{label}（可留空）：").strip()
        if not raw:
            return default
        try:
            return int(raw)
        except ValueError:
            raise InvalidInputError(field=label, value=raw)


    def _prompt_float(self, label: str) -> float:
        raw = input(f"{label}：").strip()
        try:
            return float(raw)
        except ValueError:
            raise InvalidInputError(field=label, value=raw)


    def _show_inventory(self) -> None:
        """查看玩家背包（使用 Inventory 双向链表顺序）"""
        pid = input("请输入玩家 ID：").strip()
        try:
            slots = self.inventory_service.get_slots(pid)
        except Exception as e:
            print(f"[提示] {getattr(e, 'message', str(e))}")
            return
        player = self.repo.players.get(pid)
        print(f"\n玩家 {player.name} 的背包：")
        print("-" * 40)
        if not slots:
            print("  （空）")
        else:
            for i, slot in enumerate(slots, 1):
                print(f"  {i}. {slot.get_display_name()} [{slot.get_rarity()}] x{slot.count}")
        print(f"-" * 40)
        info = self.inventory_service.get_capacity_info(pid)
        print(f"  已用槽位：{info['used']} / {info['capacity']}")


    def _show_active_listings(self) -> None:
        """显示活跃挂单"""
        active = self.app.market_service.list_active()
        print(f"\n共有 {len(active)} 个活跃挂单：")
        print("-" * 60)
        print(f"{'挂单ID':<10} {'卖家':<10} {'物品':<10} {'数量':>4} {'单价':>8}")
        print("-" * 60)
        for l in active[:20]:
            seller = self.repo.players.get(l.seller_id)
            seller_name = seller.name if seller else l.seller_id[:8]
            item = self.repo.items.get(l.item_id)
            item_name = item.name if item else l.item_id[:8]
            print(f"{l.listing_id:<10} {seller_name:<10} {item_name:<10} {l.count:>4} {l.price:>8}")
        if len(active) > 20:
            print(f"  ... 还有 {len(active)-20} 个挂单未显示")


    def _create_listing(self) -> None:
        """创建市场挂单"""
        seller_id = input("卖家玩家 ID：").strip()
        item_id = input("物品 ID：").strip()
        count = self._prompt_int("出售数量")
        price = self._prompt_int("单价")
        try:
            listing = self.app.market_service.create_listing(seller_id, item_id, count, price)
        except TradingSystemError as e:
            print(f"[提示] {e.message}")
            return
        item = self.repo.items.get(listing.item_id)
        item_name = item.name if item else listing.item_id
        print(
            f"[成功] 已创建挂单 {listing.listing_id}："
            f"{item_name} x{listing.count} @ {listing.price}"
        )


    def _cancel_listing(self) -> None:
        """撤销挂单"""
        lid = input("请输入要撤销的挂单 ID：").strip()
        requester_id = input("卖家玩家 ID：").strip()
        try:
            listing = self.app.market_service.get_listing(lid)
        except TradingSystemError as e:
            print(f"[提示] {e.message}")
            return
        item = self.repo.items.get(listing.item_id)
        item_name = item.name if item else listing.item_id
        confirm = input(
            f"确认撤销挂单 {lid}（{item_name} x{listing.count}）？(y/n)："
        ).strip().lower()
        if confirm != "y":
            print("已取消")
            return

        # 记录撤销前快照，用于撤销操作
        seller = self.app.player_service.get_by_id(listing.seller_id)
        old_status = listing.status
        old_closed_at = listing.closed_at
        old_inventory = [dict(slot) for slot in seller.inventory]

        try:
            self.app.market_service.cancel_listing(lid, requester_id)
        except TradingSystemError as e:
            print(f"[提示] {e.message}")
            return

        # 成功取消后压栈
        def undo_cancel():
            listing.status = old_status
            listing.closed_at = old_closed_at
            seller.inventory = old_inventory
            self.persistence.save_players(self.repo)
            self.persistence.save_market(self.repo)

        self.op_stack.push(Operation(
            name=f"撤销挂单 {lid}",
            undo_fn=undo_cancel,
            context={"listing_id": lid, "seller_id": requester_id}
        ))

        print(f"[成功] 已撤销挂单 {lid}，物品已退回卖家背包")


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
            item = self.repo.items.get(l.item_id)
            name = item.name if item else l.item_id[:8]
            print(f"  {l.listing_id}: {name} x{l.count} @ {l.price}")
        if len(matches) > 10:
            print(f"  ... 还有 {len(matches)-10} 个")


    def _filter_listings_by_category(self) -> None:
        """按物品分类筛选挂单"""
        category = input("分类路径（如 weapon.sword / misc）：").strip()
        try:
            matches = self.app.market_service.query_by_category(category)
        except TradingSystemError as e:
            print(f"[提示] {e.message}")
            return
        print(f"\n分类 {category} 下有 {len(matches)} 个活跃挂单：")
        for l in matches[:10]:
            item = self.repo.items.get(l.item_id)
            name = item.name if item else l.item_id[:8]
            print(f"  {l.listing_id}: {name} x{l.count} @ {l.price}")
        if len(matches) > 10:
            print(f"  ... 还有 {len(matches)-10} 个")


    def _filter_listings_by_seller(self) -> None:
        """按卖家筛选挂单"""
        seller_id = input("卖家玩家 ID：").strip()
        try:
            matches = self.app.market_service.query_by_seller(seller_id)
        except TradingSystemError as e:
            print(f"[提示] {e.message}")
            return
        seller = self.repo.players[seller_id]
        print(f"\n卖家 {seller.name} ({seller_id}) 有 {len(matches)} 个活跃挂单：")
        for l in matches[:10]:
            item = self.repo.items.get(l.item_id)
            name = item.name if item else l.item_id[:8]
            print(f"  {l.listing_id}: {name} x{l.count} @ {l.price}")
        if len(matches) > 10:
            print(f"  ... 还有 {len(matches)-10} 个")


    def _show_listing_detail(self) -> None:
        """显示单条挂单详情"""
        listing_id = input("请输入挂单 ID：").strip()
        try:
            listing = self.app.market_service.get_listing(listing_id)
            seller = self.app.player_service.get_by_id(listing.seller_id)
        except TradingSystemError as e:
            print(f"[提示] {e.message}")
            return
        item = self.repo.items.get(listing.item_id)
        item_name = item.name if item else listing.item_id
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


    def _buy_listing(self) -> None:
        """购买市场挂单"""
        lid = input("请输入要购买的挂单 ID：").strip()
        buyer_id = input("买家玩家 ID：").strip()
        try:
            listing = self.app.market_service.get_listing(lid)
            buyer = self.app.player_service.get_by_id(buyer_id)
            seller = self.app.player_service.get_by_id(listing.seller_id)
        except TradingSystemError as e:
            print(f"[提示] {e.message}")
            return
        item = self.repo.items.get(listing.item_id)
        item_name = item.name if item else listing.item_id
        total = listing.count * listing.price
        print("\n请确认交易：")
        print(f"  买家：{buyer.name} ({buyer.player_id})")
        print(f"  卖家：{seller.name} ({seller.player_id})")
        print(f"  物品：{item_name} ({listing.item_id}) x{listing.count}")
        print(f"  单价：{listing.price}")
        print(f"  总价：{total}")
        confirm = input("确认购买？(y/n)：").strip().lower()
        if confirm != "y":
            print("已取消")
            return
        try:
            txn = self.app.market_service.buy(lid, buyer_id)
        except TradingSystemError as e:
            print(f"[提示] {e.message}")
            return
        print(f"[成功] 交易完成，交易记录：{txn.transaction_id}")


    def _settle_pending_listings(self) -> None:
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
            return
        txns = self.app.market_service.settle_pending(orders)
        print(f"[完成] 成功结算 {len(txns)} / {len(orders)} 条订单")
        for txn in txns:
            print(f"  {txn.transaction_id}: {txn.listing_id} -> {txn.buyer_id}, total={txn.total}")


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
            item = self.repo.items.get(l.item_id)
            name = item.name if item else l.item_id[:8]
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
            item = self.repo.items.get(t.item_id)
            item_name = item.name if item else t.item_id
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
            title = f"物品成交历史：{item.name} ({item_id})"
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
            item = self.repo.items.get(t.item_id)
            item_name = item.name if item else t.item_id
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
                label = f"{item.name} ({item_id})"
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
