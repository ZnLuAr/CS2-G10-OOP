"""
物品管理 Handler

负责物品的查询、浏览、创建、删除等功能。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.errors import BusinessRuleError, InvalidInputError, TradingSystemError
from src.ui.formatters import format_item_table
from src.ui.handlers.base import BaseHandler
from src.ui.menus import show_item_menu
from src.ui.prompts import prompt_choice, prompt_confirm, prompt_float, prompt_int, prompt_optional_int
from src.ui.utils import print_paginated
from src.ui.utils import print_paginated

if TYPE_CHECKING:
    from src.app import App
    from src.ui.cli import OperationStack

__all__ = ["ItemHandler"]




class ItemHandler(BaseHandler):
    """物品管理 Handler"""

    def __init__(self, app: App, op_stack: OperationStack | None = None):
        super().__init__(app, op_stack)


    def run_menu(self) -> None:
        """运行物品管理菜单循环"""
        while True:
            try:
                menu_text = show_item_menu()
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
            "1": self.show_list,
            "2": self.show_detail,
            "3": self.query_by_id,
            "4": self.browse_by_category,
            "5": self.create,
            "6": self.delete,
        }
        action = actions.get(choice)
        if action:
            action()


    def show_list(self) -> None:
        """显示物品列表"""
        items = self.app.item_service.list_all()
        table = format_item_table(items)
        print(table)
        self._pause()


    def show_detail(self) -> None:
        """显示物品详情"""
        iid = input("请输入物品 ID：").strip()
        item = self.app.item_service.get_by_id(iid)

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
        self._pause()


    def query_by_id(self) -> None:
        """按 ID 查询物品"""
        iid = input("请输入物品 ID：").strip()
        item = self.app.item_service.get_by_id(iid)
        print(f"\n找到物品：{item.name} (分类：{item.category})")
        self._pause()


    def browse_by_category(self) -> None:
        """按 CatalogTree 分类浏览物品"""
        root = self.app.item_service.browse_catalog("root")
        print("\n分类目录：")
        self._print_catalog_node(root)

        category = input("请输入分类路径（如 weapon / weapon.sword / misc，留空=root）：").strip() or "root"
        items = self.app.item_service.items_in_category(category)

        print(f"\n分类 {category} 下共有 {len(items)} 件物品：")
        print("-" * 60)
        if not items:
            print("  暂无物品")
            self._pause()
            return
        print_paginated(
            items,
            formatter=lambda item: f"  {item.item_id:<10} {item.name:<16} {item.category:<20} {item.rarity}",
            limit=20,
            unit="件"
        )


    def create(self) -> None:
        """创建物品（管理员）"""
        name = input("物品名称：").strip()
        category = input("分类（如 weapon.sword / misc）：").strip()
        rarity = input("稀有度（common/uncommon/rare/epic/legendary）：").strip()
        base_value = prompt_int("基础价值", min_val=0)
        description = input("描述（可留空）：").strip()

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
        self._pause()


    def delete(self) -> None:
        """删除物品（管理员）"""
        item_id = input("请输入要删除的物品 ID：").strip()
        item = self.app.item_service.get_by_id(item_id)

        print(f"\n待删除物品：{item.describe()}")
        if not prompt_confirm(f"确认删除 {item.name} ({item.item_id})？此操作不可撤销"):
            print("已取消")
            self._pause()
            return

        self.app.item_service.delete_item(item_id)
        print(f"[成功] 已删除物品 {item_id}")
        self._pause()


    def _print_catalog_node(self, node, depth: int = 0, path: str = "") -> None:
        """递归打印分类树节点"""
        current_path = node.key if node.key != "root" else "root"
        if path and node.key != "root":
            current_path = f"{path}.{node.key}" if path != "root" else node.key
        indent = "  " * depth
        suffix = f" ({current_path})" if node.key != "root" else ""
        print(f"{indent}- {node.label}{suffix}")
        for child in node.children:
            self._print_catalog_node(child, depth + 1, current_path)


    def _prompt_item_stats(self, category: str) -> dict:
        """根据分类提示物品属性"""
        if category.startswith("weapon."):
            return {
                "attack": prompt_int("攻击"),
                "attack_speed": prompt_float("攻速"),
                "durability_max": prompt_int("最大耐久"),
                "durability": prompt_optional_int("当前耐久", None),
                "equipped": False,
                "slot": "weapon",
                "level_req": prompt_optional_int("等级要求", 0),
                "class_req": self._prompt_class_req(),
            }
        if category.startswith("tool."):
            return {
                "efficiency": prompt_float("效率"),
                "tier": prompt_int("工具等级"),
                "durability_max": prompt_int("最大耐久"),
                "durability": prompt_optional_int("当前耐久", None),
                "level_req": prompt_optional_int("等级要求", 0),
                "class_req": self._prompt_class_req(),
            }
        if category.startswith("armor."):
            slot = category.split(".", 1)[1]
            return {
                "defense": prompt_int("防御"),
                "magic_resist": prompt_int("魔抗"),
                "durability_max": prompt_int("最大耐久"),
                "durability": prompt_optional_int("当前耐久", None),
                "equipped": False,
                "slot": slot,
                "level_req": prompt_optional_int("等级要求", 0),
                "class_req": self._prompt_class_req(),
            }
        if category == "consumable.potion":
            return {
                "effect": input("效果：").strip(),
                "power": prompt_int("效果强度"),
                "duration": prompt_optional_int("持续时间", 0),
                "stack_size_max": prompt_int("最大堆叠"),
                "count": prompt_optional_int("默认数量", 1),
            }
        if category == "consumable.food":
            stats = self._prompt_consumable_stats()
            stats["nutrition"] = prompt_optional_int("营养值", 0)
            return stats
        if category == "consumable.magic":
            stats = self._prompt_consumable_stats()
            stats["mana_cost"] = prompt_optional_int("魔力消耗", 0)
            return stats
        if category == "consumable.material":
            return {
                "effect": input("效果（默认 none）：").strip() or "none",
                "power": prompt_optional_int("效果强度", 0),
                "duration": prompt_optional_int("持续时间", 0),
                "stack_size_max": prompt_int("最大堆叠"),
                "count": prompt_optional_int("默认数量", 1),
            }
        if category == "misc":
            return {
                "stack_size_max": prompt_int("最大堆叠"),
                "count": prompt_optional_int("默认数量", 1),
            }
        return {}


    def _prompt_consumable_stats(self) -> dict:
        """提示消耗品通用属性"""
        return {
            "effect": input("效果：").strip(),
            "power": prompt_int("效果强度"),
            "duration": prompt_optional_int("持续时间", 0),
            "stack_size_max": prompt_int("最大堆叠"),
            "count": prompt_optional_int("默认数量", 1),
        }


    def _prompt_class_req(self) -> list[str]:
        """提示职业需求"""
        raw = input("职业要求（逗号分隔，可留空）：").strip()
        if not raw:
            return []
        return [part.strip() for part in raw.split(",") if part.strip()]
