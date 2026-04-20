"""交易领域异常。

详见 docs/error-and-log-design.md §2。
"""

from __future__ import annotations

from .base import TradingSystemError

__all__ = [
    "TradeError",
    "InsufficientGoldError",
    "SelfPurchaseError",
    "ListingNotActiveError",
    "DuplicateListingError",
]


class TradeError(TradingSystemError):
    default_message = "交易失败"


class InsufficientGoldError(TradeError):
    default_message = "金币不足，交易无法完成"

    def __init__(self, required: int, available: int, **context):
        super().__init__(
            message=f"金币不足：需要 {required}，当前 {available}",
            required=required,
            available=available,
            **context,
        )


class SelfPurchaseError(TradeError):
    default_message = "不能购买自己的挂单"

    def __init__(self, player_id: str, **context):
        super().__init__(
            message=f"玩家 {player_id} 不能购买自己的挂单",
            player_id=player_id,
            **context,
        )


class ListingNotActiveError(TradeError):
    default_message = "挂单已失效"

    def __init__(self, listing_id: str, status: str, **context):
        super().__init__(
            message=f"挂单 {listing_id} 当前状态为 {status}，无法交易",
            listing_id=listing_id,
            status=status,
            **context,
        )


class DuplicateListingError(TradeError):
    default_message = "同一物品已在挂单中"

    def __init__(self, item_id: str, **context):
        super().__init__(
            message=f"物品 {item_id} 已存在活跃挂单，不能重复上架",
            item_id=item_id,
            **context,
        )
