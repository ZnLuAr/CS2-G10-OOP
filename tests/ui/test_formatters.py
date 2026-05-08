"""测试 formatters 模块"""

from src.models import Player, Item, Listing
from src.services.persistence import Repository
from src.ui.formatters import (
    format_header,
    format_item_table,
    format_player_table,
    format_separator,
    paginate,
)


def test_format_header():
    """测试标题格式化"""
    result = format_header("测试标题", width=40, char="=")
    assert "测试标题" in result
    assert "=" * 40 in result


def test_format_separator():
    """测试分隔线格式化"""
    result = format_separator(width=50, char="-")
    assert result == "-" * 50


def test_format_player_table():
    """测试玩家表格格式化"""
    players = [
        Player(player_id="p_001", name="Alice", gold=1000, level=5, klass="warrior"),
        Player(player_id="p_002", name="Bob", gold=500, level=3, klass="mage"),
    ]
    result = format_player_table(players)
    assert "共有 2 名玩家" in result
    assert "Alice" in result
    assert "Bob" in result
    assert "1000" in result


def test_format_item_table():
    """测试物品表格格式化"""
    from src.models import Weapon

    items = [
        Weapon(
            item_id="i_001",
            name="长剑",
            sub_category="sword",
            rarity="common",
            base_value=100,
            attack=50,
            attack_speed=1.0,
            durability_max=100,
        ),
        Weapon(
            item_id="i_002",
            name="魔法杖",
            sub_category="staff",
            rarity="rare",
            base_value=500,
            attack=80,
            attack_speed=0.8,
            durability_max=100,
        ),
    ]
    result = format_item_table(items)
    assert "共有 2 件物品" in result
    assert "长剑" in result
    assert "魔法杖" in result
    assert "common" in result
    assert "rare" in result


def test_paginate_within_limit():
    """测试分页（未超限）"""
    items = list(range(10))
    shown, msg = paginate(items, page_size=20)
    assert len(shown) == 10
    assert msg == ""


def test_paginate_exceeds_limit():
    """测试分页（超限）"""
    items = list(range(30))
    shown, msg = paginate(items, page_size=20)
    assert len(shown) == 20
    assert "还有 10 条未显示" in msg
