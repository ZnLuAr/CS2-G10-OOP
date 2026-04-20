"""数据 / 持久化相关异常。

详见 docs/error-and-log-design.md §2。
"""

from __future__ import annotations

from .base import TradingSystemError

__all__ = [
    "DataError",
    "DataIntegrityError",
    "PersistenceError",
    "SerializationError",
]


class DataError(TradingSystemError):
    default_message = "数据子系统异常"


class DataIntegrityError(DataError):
    default_message = "数据完整性错误"

    def __init__(self, entity: str, ref_id: str, **context):
        super().__init__(
            message=f"数据完整性错误：{entity} 引用了不存在的 {ref_id}",
            entity=entity,
            ref_id=ref_id,
            **context,
        )


class PersistenceError(DataError):
    default_message = "数据文件读写失败"

    def __init__(self, path: str, op: str, **context):
        super().__init__(
            message=f"数据文件 {op} 失败：{path}",
            path=path,
            op=op,
            **context,
        )


class SerializationError(DataError):
    default_message = "数据序列化失败"

    def __init__(self, entity: str, raw: object = None, **context):
        super().__init__(
            message=f"无法解析 {entity} 数据",
            entity=entity,
            raw=raw,
            **context,
        )
