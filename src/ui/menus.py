"""
菜单显示模块

提供统一的菜单构建和显示功能。所有函数返回菜单文本字符串。
"""

from __future__ import annotations

__all__ = [
    "MenuBuilder",
    "show_main_menu",
    "show_player_menu",
    "show_item_menu",
    "show_inventory_menu",
    "show_market_menu",
    "show_report_menu",
    "show_data_menu",
]




class MenuBuilder:
    """菜单构建器，用于统一菜单格式"""

    def __init__(self, title: str, width: int = 40):
        self.title = title
        self.width = width
        self.options: list[tuple[str, str]] = []


    def add_option(self, key: str, label: str) -> MenuBuilder:
        """
        添加菜单选项

        Args:
            key: 选项键（如 "1", "b"）
            label: 选项标签

        Returns:
            self（支持链式调用）
        """
        self.options.append((key, label))
        return self


    def add_separator(self) -> MenuBuilder:
        """
        添加分隔线

        Returns:
            self（支持链式调用）
        """
        self.options.append(("", ""))
        return self


    def build(self) -> str:
        """
        生成菜单文本

        Returns:
            格式化后的菜单字符串
        """
        lines = [
            "\n" + "=" * self.width,
            self.title.center(self.width),
            "=" * self.width,
        ]

        for key, label in self.options:
            if key == "" and label == "":
                lines.append("-" * self.width)
            else:
                lines.append(f"  {key}. {label}")

        lines.append("=" * self.width)
        return "\n".join(lines)




def show_main_menu(can_undo: bool = False, undo_count: int = 0) -> str:
    """
    显示主菜单

    Args:
        can_undo: 是否可以撤销
        undo_count: 可撤销步数

    Returns:
        菜单文本
    """
    builder = MenuBuilder("主  菜  单")
    builder.add_option("1", "玩家管理")
    builder.add_option("2", "物品管理")
    builder.add_option("3", "背包管理")
    builder.add_option("4", "交易市场")
    builder.add_option("5", "历史与报表")
    builder.add_option("6", "数据管理")
    builder.add_option("7", "退出")
    builder.add_separator()

    if can_undo:
        builder.add_option("0", f"撤销上一步 ({undo_count} 步可撤销)")

    return builder.build()




def show_player_menu() -> str:
    """
    显示玩家管理菜单

    Returns:
        菜单文本
    """
    builder = MenuBuilder("玩家管理")
    builder.add_option("1", "创建玩家")
    builder.add_option("2", "玩家列表")
    builder.add_option("3", "玩家详情")
    builder.add_option("4", "按 ID 查询")
    builder.add_option("5", "按名字搜索")
    builder.add_option("6", "修改玩家名")
    builder.add_option("7", "删除玩家")
    builder.add_option("8", "金币充值（调试）")
    builder.add_separator()
    builder.add_option("b", "返回主菜单")
    return builder.build()




def show_item_menu() -> str:
    """
    显示物品管理菜单

    Returns:
        菜单文本
    """
    builder = MenuBuilder("物品管理")
    builder.add_option("1", "物品列表")
    builder.add_option("2", "物品详情")
    builder.add_option("3", "按 ID 查询")
    builder.add_option("4", "按分类浏览")
    builder.add_option("5", "创建物品（管理员）")
    builder.add_option("6", "删除物品（管理员）")
    builder.add_separator()
    builder.add_option("b", "返回主菜单")
    return builder.build()




def show_inventory_menu() -> str:
    """
    显示背包管理菜单

    Returns:
        菜单文本
    """
    builder = MenuBuilder("背包管理")
    builder.add_option("1", "查看背包")
    builder.add_option("2", "查看背包（按稀有度排序）")
    builder.add_option("3", "移除物品")
    builder.add_option("4", "添加物品（调试）")
    builder.add_option("5", "背包容量信息")
    builder.add_separator()
    builder.add_option("b", "返回主菜单")
    return builder.build()




def show_market_menu() -> str:
    """
    显示交易市场菜单

    Returns:
        菜单文本
    """
    builder = MenuBuilder("交易市场")
    builder.add_option("1", "挂单上架")
    builder.add_option("2", "撤销挂单")
    builder.add_option("3", "浏览全部挂单")
    builder.add_option("4", "按价格区间查询")
    builder.add_option("5", "按分类筛选")
    builder.add_option("6", "按卖家筛选")
    builder.add_option("7", "挂单详情")
    builder.add_option("8", "挂单排序")
    builder.add_option("9", "购买物品")
    builder.add_option("10", "批量结算挂单（管理员）")
    builder.add_separator()
    builder.add_option("b", "返回主菜单")
    return builder.build()




def show_report_menu() -> str:
    """
    显示历史与报表菜单

    Returns:
        菜单文本
    """
    builder = MenuBuilder("历史与报表")
    builder.add_option("1", "玩家交易历史")
    builder.add_option("2", "物品交易历史")
    builder.add_option("3", "价格统计")
    builder.add_option("4", "金币排行榜")
    builder.add_option("5", "交易量排行榜")
    builder.add_option("6", "系统数据快照")
    builder.add_separator()
    builder.add_option("b", "返回主菜单")
    return builder.build()




def show_data_menu() -> str:
    """
    显示数据管理菜单

    Returns:
        菜单文本
    """
    builder = MenuBuilder("数据管理")
    builder.add_option("1", "立即保存所有数据")
    builder.add_option("2", "查看数据统计")
    builder.add_option("3", "重置所有数据（危险操作）")
    builder.add_separator()
    builder.add_option("b", "返回主菜单")
    return builder.build()
