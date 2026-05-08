"""
玩家管理 Handler

负责玩家的创建、查询、修改、删除等功能。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.errors import InvalidInputError
from src.ui.formatters import format_player_table
from src.ui.handlers.base import BaseHandler
from src.ui.menus import show_player_menu
from src.ui.prompts import prompt_choice, prompt_confirm, prompt_int, prompt_optional_int, prompt_string

if TYPE_CHECKING:
    from src.app import App
    from src.ui.cli import OperationStack

__all__ = ["PlayerHandler"]




class PlayerHandler(BaseHandler):
    """玩家管理 Handler"""

    def __init__(self, app: App, op_stack: OperationStack | None = None):
        super().__init__(app, op_stack)
        # 初始化背包服务（用于玩家详情页显示）
        from src.services.player_inventory_service import PlayerInventoryService
        self.inventory_service = PlayerInventoryService(self.repo, self.persistence)


    def run_menu(self) -> None:
        """运行玩家管理菜单循环"""
        while True:
            try:
                menu_text = show_player_menu()
                print(menu_text)
                choice = prompt_choice(
                    "请输入选项",
                    {"1", "2", "3", "4", "5", "6", "7", "8", "b", "B"}
                )

                if choice.lower() == "b":
                    break

                self._dispatch(choice)

            except Exception as e:
                self._handle_exception(e)


    def _dispatch(self, choice: str) -> None:
        """分发菜单选择"""
        actions = {
            "1": self.create,
            "2": self.show_list,
            "3": self.show_detail,
            "4": self.query_by_id,
            "5": self.search_by_name,
            "6": self.rename,
            "7": self.delete,
            "8": self.add_gold_debug,
        }
        action = actions.get(choice)
        if action:
            action()


    def show_list(self) -> None:
        """显示玩家列表（功能 ID 12：支持按金币/名字排序）"""
        print("\n排序方式：1=ID（默认） 2=名字 3=金币升序 4=金币降序")
        sort_choice = input("请选择（直接回车=默认）：").strip() or "1"

        sort_map = {
            "1": ("id", False),
            "2": ("name", False),
            "3": ("gold", False),
            "4": ("gold", True),
        }
        sort_by, desc = sort_map.get(sort_choice, ("id", False))

        players = self.app.player_service.list_all(sort_by=sort_by, desc=desc)
        table = format_player_table(players)
        print(table)
        self._pause()


    def show_detail(self) -> None:
        """显示玩家详情"""
        pid = input("请输入玩家 ID：").strip()
        player = self._get_player_or_none(pid)
        if player is None:
            return

        print(f"\n{'='*60}")
        print(f"玩家详情：{player.name} ({player.player_id})")
        print(f"{'='*60}")
        print(f"  金币：{player.gold}")
        print(f"  等级：{player.level}")
        print(f"  职业：{player.klass}")

        # 背包内容（通过服务层获取格式化数据）
        slots = self.inventory_service.get_slots(pid)
        print(f"\n  背包：{len(slots)} 件物品")
        if slots:
            for slot in slots:
                item_name = slot.get_display_name()
                print(f"    - {item_name} x{slot.count}")

        # 活跃挂单（通过服务层查询）
        active_listings = self.app.market_service.query_by_seller(pid)
        print(f"\n  活跃挂单：{len(active_listings)} 条")
        if active_listings:
            for lst in active_listings[:5]:  # 最多显示 5 条
                item_name = self._get_item_display_name(lst.item_id)
                print(f"    - {lst.listing_id}: {item_name} x{lst.count} @ {lst.price}金币")

        # 历史成交（通过服务层查询，已按 completed_at 倒序）
        transactions = self.app.transaction_service.by_player(pid)
        print(f"\n  历史成交：{len(transactions)} 笔")
        if transactions:
            recent = transactions[:5]
            for tx in recent:
                role = "买入" if tx.buyer_id == pid else "卖出"
                item_name = self._get_item_display_name(tx.item_id)
                print(f"    - [{role}] {item_name} x{tx.count} @ {tx.price}金币")

        print(f"{'='*60}")
        self._pause()


    def query_by_id(self) -> None:
        """按 ID 查询玩家"""
        pid = input("请输入玩家 ID：").strip()
        player = self.app.player_service.get_by_id(pid)
        print(f"\n找到玩家：{player.name}，金币 {player.gold}，等级 {player.level}")
        self._pause()


    def search_by_name(self) -> None:
        """按名字模糊查询玩家"""
        keyword = input("请输入名字关键词：").strip().lower()
        matches = self.app.player_service.search_by_name(keyword)
        print(f"\n找到 {len(matches)} 名匹配的玩家：")
        for p in matches:
            print(f"  {p.player_id}: {p.name} (金币 {p.gold})")
        self._pause()


    def create(self) -> None:
        """创建玩家（功能 ID 10）"""
        print("\n" + "=" * 40)
        print("         创建玩家")
        print("=" * 40)

        name = prompt_string("玩家昵称", min_len=1, max_len=20)
        gold = prompt_optional_int("初始金币", default=0)
        level = prompt_optional_int("初始等级", default=1)

        print("\n职业选择：")
        print("  1. warrior (战士)")
        print("  2. archer (弓箭手)")
        print("  3. mage (法师)")
        print("  4. summon (召唤师)")
        print("  5. none (无职业)")
        klass_choice = input("请选择职业（默认5）：").strip() or "5"
        if klass_choice not in {"1", "2", "3", "4", "5"}:
            raise InvalidInputError(field="klass", value=klass_choice)

        klass_map = {"1": "warrior", "2": "archer", "3": "mage", "4": "summon", "5": "none"}
        klass = klass_map[klass_choice]

        player = self.app.player_service.create_player(name, gold=gold, level=level, klass=klass)
        print(f"\n[成功] 已创建玩家：")
        print(f"  ID: {player.player_id}")
        print(f"  昵称: {player.name}")
        print(f"  金币: {player.gold}")
        print(f"  等级: {player.level}")
        print(f"  职业: {player.klass}")
        self._pause()


    def rename(self) -> None:
        """修改玩家昵称（功能 ID 15）"""
        print("\n" + "=" * 40)
        print("         修改玩家昵称")
        print("=" * 40)

        pid = input("请输入玩家 ID：").strip()
        player = self.app.player_service.get_by_id(pid)

        print(f"\n当前玩家信息：")
        print(f"  ID: {player.player_id}")
        print(f"  昵称: {player.name}")
        print(f"  金币: {player.gold}")

        new_name = input("\n请输入新昵称（1-20字符）：").strip()

        if not prompt_confirm(f"确认将 '{player.name}' 改为 '{new_name}'？"):
            print("[已取消]")
            self._pause()
            return

        self.app.player_service.rename(pid, new_name)
        print(f"\n[成功] 已将玩家昵称改为：{new_name}")
        self._pause()


    def delete(self) -> None:
        """删除玩家（功能 ID 16）"""
        print("\n" + "=" * 40)
        print("         删除玩家")
        print("=" * 40)

        pid = input("请输入玩家 ID：").strip()
        player = self.app.player_service.get_by_id(pid)

        print(f"\n玩家信息：")
        print(f"  ID: {player.player_id}")
        print(f"  昵称: {player.name}")
        print(f"  金币: {player.gold}")
        print(f"  背包物品数: {len(player.inventory)}")

        # 检查是否有活跃挂单（通过服务层查询）
        active_listings = self.app.market_service.query_by_seller(pid)
        if active_listings:
            print(f"  活跃挂单数: {len(active_listings)}")

        print("\n" + "!" * 40)
        print("  警告：删除操作不可恢复！")
        print("  要求：背包必须为空，无活跃挂单")
        print("!" * 40)

        confirm = input("\n确认删除该玩家？(yes/no): ").strip().lower()
        if confirm != 'yes':
            print("[已取消]")
            self._pause()
            return

        self.app.player_service.delete(pid)
        print(f"\n[成功] 已删除玩家：{player.name}")
        self._pause()


    def add_gold_debug(self) -> None:
        """金币充值（调试功能）"""
        pid = input("请输入玩家 ID：").strip()
        amount = prompt_int("充值金额")

        self.app.player_service.add_gold(pid, amount)
        player = self.app.player_service.get_by_id(pid)
        print(f"[成功] 已为 {player.name} 充值 {amount} 金币，当前 {player.gold}")
        self._pause()
