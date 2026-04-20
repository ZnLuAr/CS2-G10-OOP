"""异常根基类。

所有自定义异常都继承自 ``TradingSystemError``。
完整接口规范见 docs/error-and-log-design.md §3。
"""

from __future__ import annotations

__all__ = ["TradingSystemError"]


class TradingSystemError(Exception):
    """项目所有自定义异常的根基类。

    Attributes:
        message: 面向用户的友好消息（中文，可直接打印给最终用户）
        context: 面向开发者的上下文 dict（写日志用，不展示给用户）
    """

    default_message: str = "系统出现异常"

    def __init__(self, message: str | None = None, **context):
        self.message = message or self.default_message
        self.context = context
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        ctx = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
        return f"{type(self).__name__}({self.message!r}{', ' + ctx if ctx else ''})"
