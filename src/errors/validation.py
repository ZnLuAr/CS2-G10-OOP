"""校验类异常：输入非法、目标不存在、违反业务规则。

详见 docs/error-and-log-design.md §2。
"""

from __future__ import annotations

from .base import TradingSystemError

__all__ = [
    "ValidationError",
    "InvalidInputError",
    # NotFound 系列
    "NotFoundError",
    "PlayerNotFoundError",
    "ItemNotFoundError",
    "ListingNotFoundError",
    # BusinessRule 系列
    "BusinessRuleError",
    "InventoryFullError",
    "InventoryNotEmptyError",
    "ItemNotEquippableError",
    "ItemBrokenError",
    "LevelOrClassRequirementError",
]


class ValidationError(TradingSystemError):
    default_message = "校验失败"


class InvalidInputError(ValidationError):
    default_message = "输入非法"

    def __init__(self, field: str, value: object, **context):
        super().__init__(
            message=f"字段 {field} 的值非法：{value!r}",
            field=field,
            value=value,
            **context,
        )


# --- NotFound 系列 -----------------------------------------------------------

class NotFoundError(ValidationError):
    default_message = "目标不存在"


class PlayerNotFoundError(NotFoundError):
    default_message = "玩家不存在"

    def __init__(self, player_id: str, **context):
        super().__init__(
            message=f"未找到玩家：{player_id}",
            player_id=player_id,
            **context,
        )


class ItemNotFoundError(NotFoundError):
    default_message = "物品不存在"

    def __init__(self, item_id: str, **context):
        super().__init__(
            message=f"未找到物品：{item_id}",
            item_id=item_id,
            **context,
        )


class ListingNotFoundError(NotFoundError):
    default_message = "挂单不存在"

    def __init__(self, listing_id: str, **context):
        super().__init__(
            message=f"未找到挂单:{listing_id}",
            listing_id=listing_id,
            **context,
        )


# --- BusinessRule 系列 -------------------------------------------------------

class BusinessRuleError(ValidationError):
    default_message = "违反业务规则"


class InventoryFullError(BusinessRuleError):
    default_message = "背包已满"

    def __init__(self, player_id: str, capacity: int, **context):
        super().__init__(
            message=f"背包已满（{capacity} 格），无法继续放入物品",
            player_id=player_id,
            capacity=capacity,
            **context,
        )


class InventoryNotEmptyError(BusinessRuleError):
    default_message = "背包非空，无法删除玩家"

    def __init__(self, player_id: str, **context):
        super().__init__(
            message=f"玩家 {player_id} 的背包仍有物品，无法删除",
            player_id=player_id,
            **context,
        )


class ItemNotEquippableError(BusinessRuleError):
    default_message = "物品不可穿戴"

    def __init__(self, item_id: str, reason: str, **context):
        super().__init__(
            message=f"物品 {item_id} 不可穿戴：{reason}",
            item_id=item_id,
            reason=reason,
            **context,
        )


class ItemBrokenError(BusinessRuleError):
    default_message = "物品已损坏"

    def __init__(self, item_id: str, **context):
        super().__init__(
            message=f"物品 {item_id} 耐久为 0，已损坏",
            item_id=item_id,
            **context,
        )


class LevelOrClassRequirementError(BusinessRuleError):
    default_message = "玩家等级 / 职业不满足要求"

    def __init__(self, item_id: str,
                 level_req: int | None = None,
                 class_req: list[str] | None = None,
                 **context):
        parts = []
        if level_req is not None:
            parts.append(f"等级 ≥ {level_req}")
        if class_req:
            parts.append(f"职业 ∈ {class_req}")
        suffix = "（" + "，".join(parts) + "）" if parts else ""
        super().__init__(
            message=f"使用物品 {item_id} 需要{suffix}",
            item_id=item_id,
            level_req=level_req,
            class_req=class_req,
            **context,
        )
