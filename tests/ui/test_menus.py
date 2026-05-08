"""测试 menus 模块"""

from src.ui.menus import (
    MenuBuilder,
    show_data_menu,
    show_inventory_menu,
    show_item_menu,
    show_main_menu,
    show_market_menu,
    show_player_menu,
    show_report_menu,
)


def test_menu_builder_basic():
    """测试菜单构建器基本功能"""
    builder = MenuBuilder("测试菜单")
    builder.add_option("1", "选项一")
    builder.add_option("2", "选项二")
    result = builder.build()

    assert "测试菜单" in result
    assert "1. 选项一" in result
    assert "2. 选项二" in result
    assert "=" * 40 in result


def test_menu_builder_with_separator():
    """测试菜单构建器分隔线"""
    builder = MenuBuilder("测试菜单")
    builder.add_option("1", "选项一")
    builder.add_separator()
    builder.add_option("b", "返回")
    result = builder.build()

    assert "-" * 40 in result


def test_show_main_menu_without_undo():
    """测试主菜单（无撤销）"""
    result = show_main_menu(can_undo=False)
    assert "主  菜  单" in result
    assert "1. 玩家管理" in result
    assert "7. 退出" in result
    assert "撤销" not in result


def test_show_main_menu_with_undo():
    """测试主菜单（有撤销）"""
    result = show_main_menu(can_undo=True, undo_count=3)
    assert "主  菜  单" in result
    assert "0. 撤销上一步 (3 步可撤销)" in result


def test_show_player_menu():
    """测试玩家管理菜单"""
    result = show_player_menu()
    assert "玩家管理" in result
    assert "1. 创建玩家" in result
    assert "b. 返回主菜单" in result


def test_show_item_menu():
    """测试物品管理菜单"""
    result = show_item_menu()
    assert "物品管理" in result
    assert "1. 物品列表" in result
    assert "b. 返回主菜单" in result


def test_show_inventory_menu():
    """测试背包管理菜单"""
    result = show_inventory_menu()
    assert "背包管理" in result
    assert "1. 查看背包" in result
    assert "b. 返回主菜单" in result


def test_show_market_menu():
    """测试交易市场菜单"""
    result = show_market_menu()
    assert "交易市场" in result
    assert "1. 挂单上架" in result
    assert "b. 返回主菜单" in result


def test_show_report_menu():
    """测试历史与报表菜单"""
    result = show_report_menu()
    assert "历史与报表" in result
    assert "1. 玩家交易历史" in result
    assert "b. 返回主菜单" in result


def test_show_data_menu():
    """测试数据管理菜单"""
    result = show_data_menu()
    assert "数据管理" in result
    assert "1. 立即保存所有数据" in result
    assert "b. 返回主菜单" in result
