"""自定义异常体系（统一入口）。

完整接口规范见 docs/error-and-log-design.md。

异常树（三层）::

    Exception
    └── TradingSystemError                          [位于 base.py]
        ├── DataError                               [位于 data.py]
        │   ├── DataIntegrityError
        │   ├── PersistenceError
        │   └── SerializationError
        ├── ValidationError                         [位于 validation.py]
        │   ├── InvalidInputError
        │   ├── NotFoundError
        │   │   ├── PlayerNotFoundError
        │   │   ├── ItemNotFoundError
        │   │   └── ListingNotFoundError
        │   └── BusinessRuleError
        │       ├── InventoryFullError
        │       ├── InventoryNotEmptyError
        │       ├── ItemNotEquippableError
        │       ├── ItemBrokenError
        │       └── LevelOrClassRequirementError
        └── TradeError                              [位于 trade.py]
            ├── InsufficientGoldError
            ├── SelfPurchaseError
            ├── ListingNotActiveError
            └── DuplicateListingError

调用约定：
- 服务层只抛、不捕获
- UI 层用 ``except TradingSystemError as e: print(e.message)`` 翻译给用户
- 主循环最外层兜底任意 ``Exception``，程序不崩溃

每个具体异常都暴露：
- ``message``: 面向用户的中文友好消息
- ``context``: 面向开发者的字段 dict（写日志用）

调用方使用方式不变::

    from src.errors import InsufficientGoldError, PlayerNotFoundError
"""

from __future__ import annotations

from .base import TradingSystemError
from .data import (
    DataError,
    DataIntegrityError,
    PersistenceError,
    SerializationError,
)
from .trade import (
    DuplicateListingError,
    InsufficientGoldError,
    ListingNotActiveError,
    SelfPurchaseError,
    TradeError,
)
from .validation import (
    BusinessRuleError,
    InvalidInputError,
    InventoryFullError,
    InventoryNotEmptyError,
    ItemBrokenError,
    ItemNotEquippableError,
    LevelOrClassRequirementError,
    NotFoundError,
    PlayerNotFoundError,
    ItemNotFoundError,
    ListingNotFoundError,
    ValidationError,
)


__all__ = [
    # 基类
    "TradingSystemError",
    # 数据 / 持久化
    "DataError",
    "DataIntegrityError",
    "PersistenceError",
    "SerializationError",
    # 校验
    "ValidationError",
    "InvalidInputError",
    "NotFoundError",
    "PlayerNotFoundError",
    "ItemNotFoundError",
    "ListingNotFoundError",
    "BusinessRuleError",
    "InventoryFullError",
    "InventoryNotEmptyError",
    "ItemNotEquippableError",
    "ItemBrokenError",
    "LevelOrClassRequirementError",
    # 交易
    "TradeError",
    "InsufficientGoldError",
    "SelfPurchaseError",
    "ListingNotActiveError",
    "DuplicateListingError",
]
