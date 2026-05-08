"""背包管理 Handler

负责背包查看、物品添加/移除、容量管理等功能。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.errors import BusinessRuleError, TradingSystemError
from src.ui.handlers.base import BaseHandler
from src.ui.menus import show_inventory_menu
from src.ui.prompts import prompt_choice, prompt_optional_int

if TYPE_CHECKING:
    from src.app import App
    from src.ui.cli import OperationStack

__all__ = ["InventoryHandler"]


class InventoryHandler(BaseHandler):
    """背包管理 Handler"""

    def __init__(self, app: App, op_stack: OperationStack | None = None):
        super().__init__(app, op_stack)
        # 初始化背包服务
        from src.services.player_inventory_service import PlayerInventoryService
        self.inventory_service = PlayerInventoryService(self.repo, self.persistence)

    def run_menu(self) -> None:
        """运行背包管理菜单循环"""
        while True:
            try:
                menu_text = show_inventory_menu()
                print(menu_text)
                choice = prompt_choice(
                    "请输入选项",
                    {"1", "2", "3", "4", "5", "b", "B"}
                )

                if choice.lower() == "b":
                    break

                self._dispatch(choice)

            except Exception as e:
                self._handle_exception(e)

    def _dispatch(self, choice: str) -> None:
        """分发菜单选择"""
        actions = {
            "1": self.show_inventory,
            "2": self.show_sorted,
            "3": self.remove_item,
            "4": self.add_item,
            "5": self.show_capacity,
        }
        action = actions.get(choice)
        if action:
            action()

    def show_inventory(self) -> None:
        """查看玩家背包（使用 Inventory 双向链表顺序）"""
        pid = input("请输入玩家 ID：").strip()

        slots = self.inventory_service.get_slots(pid)

        player = self._get_player_or_none(pid)
        if player is None:
            return
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
        self._pause()

    def show_sorted(self) -> None:
        """按稀有度排序查看背包"""
        pid = input("请输入玩家 ID：").strip()

        sorted_slots = self.inventory_service.get_sorted_view(pid, key="rarity")
        player = self._get_player_or_none(pid)
        if player is None:
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
        self._pause()

    def remove_item(self) -> None:
        """从背包移除物品"""
        pid = input("请输入玩家 ID：").strip()
        item_id = input("请输入要移除的物品 ID：").strip()
        count = prompt_optional_int("移除数量", default=1, min_val=1)

        self.inventory_service.remove_item(pid, item_id, count)
        print(f"[成功] 已从背包移除 {count} 个 {item_id}")
        self._pause()

    def add_item(self) -> None:
        """向背包添加物品（管理员调试用）"""
        pid = input("请输入玩家 ID：").strip()
        item_id = input("请输入要添加的物品 ID：").strip()
        count = prompt_optional_int("添加数量", default=1, min_val=1)

        self.inventory_service.add_item(pid, item_id, count)
        item_name = self._get_item_display_name(item_id)
        print(f"[成功] 已向背包添加 {count} 个 {item_name}")
        self._pause()

    def show_capacity(self) -> None:
        """显示背包容量信息"""
        pid = input("请输入玩家 ID：").strip()

        info = self.inventory_service.get_capacity_info(pid)
        player = self._get_player_or_none(pid)
        if player is None:
            return

        print(f"\n玩家 {player.name} 的背包容量：")
        print(f"  总容量：{info['capacity']}")
        print(f"  已用槽位：{info['used']}")
        print(f"  剩余槽位：{info['remaining']}")
        print(f"  状态：{'已满' if info['is_full'] else '可用'}")
        self._pause()
