"""
格式化工具模块

提供统一的表格、列表、详情页格式化函数。所有函数返回字符串而不是直接打印。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from src.models import Player, Item, Listing, Transaction
    from src.services.persistence import Repository


__all__ = [
    "format_header",
    "format_separator",
    "format_player_table",
    "format_item_table",
    "format_listing_table",
    "format_transaction_table",
    "paginate",
]

T = TypeVar("T")

# 字符串截断长度常量
_MAX_ITEM_NAME_LEN = 18
_MAX_ITEM_ID_LEN = 13
_MAX_CATEGORY_LEN = 18
_MAX_RARITY_LEN = 10
_MAX_LISTING_ID_LEN = 8




def format_header(title: str, width: int = 60, char: str = "=") -> str:
    """
    格式化标题头

    Args:
        title: 标题文本
        width: 总宽度
        char: 边框字符

    Returns:
        格式化后的标题字符串
    """
    lines = [
        "\n" + char * width,
        title.center(width),
        char * width,
    ]
    return "\n".join(lines)




def format_separator(width: int = 60, char: str = "-") -> str:
    """
    格式化分隔线

    Args:
        width: 宽度
        char: 分隔字符

    Returns:
        分隔线字符串
    """
    return char * width




def format_player_table(players: list[Player]) -> str:
    """
    格式化玩家列表为表格

    Args:
        players: 玩家列表

    Returns:
        格式化后的表格字符串
    """
    lines = [f"\n共有 {len(players)} 名玩家："]
    lines.append("-" * 50)
    lines.append(f"{'ID':<10} {'名字':<12} {'金币':>8} {'等级':>4} {'背包数量':>8}")
    lines.append("-" * 50)
    for p in players:
        inv_count = len(p.inventory) if p.inventory else 0
        lines.append(f"{p.player_id:<10} {p.name:<12} {p.gold:>8} {p.level:>4} {inv_count:>8}")
    return "\n".join(lines)




def format_item_table(items: list[Item]) -> str:
    """
    格式化物品列表为表格

    Args:
        items: 物品列表

    Returns:
        格式化后的表格字符串
    """
    lines = [f"\n共有 {len(items)} 件物品："]
    lines.append("-" * 80)
    lines.append(f"{'ID':<12} {'名称':<20} {'分类':<18} {'稀有度':<10} {'基础价值':>8}")
    lines.append("-" * 80)
    for item in items:
        cat = item.category
        rarity = item.rarity
        name = item.name[:_MAX_ITEM_NAME_LEN] if len(item.name) > _MAX_ITEM_NAME_LEN else item.name
        lines.append(f"{item.item_id:<12} {name:<20} {cat:<18} {rarity:<10} {item.base_value:>8}")
    return "\n".join(lines)




def format_listing_table(listings: list[Listing], repo: Repository) -> str:
    """
    格式化挂单列表为表格

    Args:
        listings: 挂单列表
        repo: 数据仓库（用于查找卖家和物品名称）

    Returns:
        格式化后的表格字符串
    """
    lines = [f"\n共有 {len(listings)} 个活跃挂单："]
    lines.append("-" * 60)
    lines.append(f"{'挂单ID':<10} {'卖家':<10} {'物品':<10} {'数量':>4} {'单价':>8}")
    lines.append("-" * 60)

    shown, pagination_msg = paginate(listings, page_size=20)

    for listing in shown:
        seller = repo.players.get(listing.seller_id)
        seller_name = seller.name if seller else listing.seller_id[:_MAX_LISTING_ID_LEN]
        item = repo.items.get(listing.item_id)
        item_name = item.name if item else listing.item_id[:_MAX_LISTING_ID_LEN]
        lines.append(f"{listing.listing_id:<10} {seller_name:<10} {item_name:<10} {listing.count:>4} {listing.price:>8}")

    if pagination_msg:
        lines.append(pagination_msg)

    return "\n".join(lines)




def format_transaction_table(transactions: list[Transaction], repo: Repository, role: str | None = None) -> str:
    """
    格式化交易历史为表格

    Args:
        transactions: 交易列表
        repo: 数据仓库
        role: 角色标识（"buyer" 或 "seller"），用于显示角色列

    Returns:
        格式化后的表格字符串
    """
    lines = [f"\n共有 {len(transactions)} 条交易记录："]
    lines.append("-" * 80)

    if role:
        lines.append(f"{'交易ID':<12} {'物品':<15} {'数量':>4} {'单价':>8} {'总价':>10} {'角色':<6} {'时间':<16}")
    else:
        lines.append(f"{'交易ID':<12} {'买家':<10} {'卖家':<10} {'物品':<12} {'数量':>4} {'单价':>8} {'时间':<16}")

    lines.append("-" * 80)

    shown, pagination_msg = paginate(transactions, page_size=20)

    for tx in shown:
        item = repo.items.get(tx.item_id)
        item_name = item.name[:_MAX_ITEM_NAME_LEN] if item else tx.item_id[:_MAX_ITEM_ID_LEN]

        if role:
            role_label = "买入" if role == "buyer" else "卖出"
            total = tx.count * tx.price
            time_str = tx.completed_at[:16] if tx.completed_at else "-"
            lines.append(f"{tx.transaction_id:<12} {item_name:<15} {tx.count:>4} {tx.price:>8} {total:>10} {role_label:<6} {time_str:<16}")
        else:
            buyer = repo.players.get(tx.buyer_id)
            buyer_name = buyer.name[:_MAX_LISTING_ID_LEN] if buyer else tx.buyer_id[:_MAX_LISTING_ID_LEN]
            seller = repo.players.get(tx.seller_id)
            seller_name = seller.name[:_MAX_LISTING_ID_LEN] if seller else tx.seller_id[:_MAX_LISTING_ID_LEN]
            time_str = tx.completed_at[:16] if tx.completed_at else "-"
            lines.append(f"{tx.transaction_id:<12} {buyer_name:<10} {seller_name:<10} {item_name:<12} {tx.count:>4} {tx.price:>8} {time_str:<16}")

    if pagination_msg:
        lines.append(pagination_msg)

    return "\n".join(lines)


def paginate(items: list[T], page_size: int = 20) -> tuple[list[T], str]:
    """
    分页显示列表

    Args:
        items: 待分页的列表
        page_size: 每页显示数量

    Returns:
        (显示的项, 分页提示消息)
    """
    if len(items) <= page_size:
        return items, ""

    shown = items[:page_size]
    remaining = len(items) - page_size
    msg = f"  ... 还有 {remaining} 条未显示"
    return shown, msg
