"""UI 通用工具函数

提供跨 CLI 和 Handler 使用的通用 UI 辅助功能。
"""

from __future__ import annotations

import os
import sys
from typing import Callable, TypeVar


T = TypeVar("T")


def pause() -> None:
    """等待用户按键继续

    捕获 EOFError 以支持测试环境和管道输入。
    """
    try:
        input("\n按回车键继续...")
    except EOFError:
        pass


def clear_screen() -> None:
    """清屏（跨平台）

    Windows 使用 cls，Unix/Linux/Mac 使用 clear。
    捕获异常以避免在不支持的环境中崩溃。
    """
    try:
        os.system("cls" if sys.platform == "win32" else "clear")
    except Exception:
        pass


def print_paginated(
    items: list[T],
    formatter: Callable[[T], str],
    limit: int = 10,
    unit: str = "个",
    auto_pause: bool = True,
) -> None:
    """分页显示列表，超出部分显示溢出提示

    Args:
        items: 要显示的列表
        formatter: 格式化函数，接受单个 item 返回显示字符串
        limit: 显示数量限制
        unit: 溢出提示的单位（"个"、"条"、"件"等）
        auto_pause: 是否自动调用 pause()
    """
    shown = items[:limit]
    for item in shown:
        print(formatter(item))

    if len(items) > limit:
        print(f"  ... 还有 {len(items) - limit} {unit}未显示")

    if auto_pause:
        pause()
