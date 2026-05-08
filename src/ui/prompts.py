"""
输入校验工具模块

提供统一的用户输入校验函数，所有函数在输入无效时抛出 InvalidInputError。
"""

from __future__ import annotations

from src.errors import InvalidInputError

__all__ = [
    "prompt_choice",
    "prompt_int",
    "prompt_optional_int",
    "prompt_float",
    "prompt_string",
    "prompt_confirm",
]




def prompt_choice(prompt: str, valid_choices: set[str]) -> str:
    """
    提示用户输入并校验是否在有效选项中

    Args:
        prompt: 提示文本
        valid_choices: 有效选项集合

    Returns:
        用户输入的有效选项

    Raises:
        InvalidInputError: 输入不在有效选项中
    """
    user_input = input(f"{prompt}：").strip()
    if user_input not in valid_choices:
        raise InvalidInputError(field="choice", value=user_input)
    return user_input




def prompt_int(label: str, min_val: int | None = None, max_val: int | None = None) -> int:
    """
    提示用户输入整数

    Args:
        label: 输入标签
        min_val: 最小值（可选）
        max_val: 最大值（可选）

    Returns:
        用户输入的整数

    Raises:
        InvalidInputError: 输入不是有效整数或超出范围
    """
    raw = input(f"{label}：").strip()
    try:
        value = int(raw)
        if min_val is not None and value < min_val:
            raise InvalidInputError(field=label, value=f"{raw} (必须 >= {min_val})")
        if max_val is not None and value > max_val:
            raise InvalidInputError(field=label, value=f"{raw} (必须 <= {max_val})")
        return value
    except ValueError:
        raise InvalidInputError(field=label, value=raw)




def prompt_optional_int(label: str, default: int | None = None, min_val: int | None = None) -> int | None:
    """
    提示用户输入可选整数

    Args:
        label: 输入标签
        default: 默认值（留空时返回）
        min_val: 最小值（可选）

    Returns:
        用户输入的整数或默认值

    Raises:
        InvalidInputError: 输入不是有效整数或低于最小值
    """
    raw = input(f"{label}（可留空）：").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise InvalidInputError(field=label, value=raw)
    if min_val is not None and value < min_val:
        raise InvalidInputError(field=label, value=f"{raw} (必须 >= {min_val})")
    return value




def prompt_float(label: str, min_val: float | None = None) -> float:
    """
    提示用户输入浮点数

    Args:
        label: 输入标签
        min_val: 最小值（可选）

    Returns:
        用户输入的浮点数

    Raises:
        InvalidInputError: 输入不是有效浮点数或小于最小值
    """
    raw = input(f"{label}：").strip()
    try:
        value = float(raw)
        if min_val is not None and value < min_val:
            raise InvalidInputError(field=label, value=f"{raw} (必须 >= {min_val})")
        return value
    except ValueError:
        raise InvalidInputError(field=label, value=raw)




def prompt_string(label: str, min_len: int = 1, max_len: int = 100) -> str:
    """
    提示用户输入字符串

    Args:
        label: 输入标签
        min_len: 最小长度
        max_len: 最大长度

    Returns:
        用户输入的字符串

    Raises:
        InvalidInputError: 输入长度不在范围内
    """
    raw = input(f"{label}：").strip()
    if len(raw) < min_len:
        raise InvalidInputError(field=label, value=f"'{raw}' (长度必须 >= {min_len})")
    if len(raw) > max_len:
        raise InvalidInputError(field=label, value=f"'{raw[:20]}...' (长度必须 <= {max_len})")
    return raw




def prompt_confirm(message: str, default: bool = False) -> bool:
    """
    提示用户确认操作

    Args:
        message: 确认消息
        default: 默认值（留空时返回）

    Returns:
        True 表示确认，False 表示取消
    """
    suffix = " (Y/n)" if default else " (y/N)"
    raw = input(f"{message}{suffix}：").strip().lower()

    if not raw:
        return default

    return raw in ("y", "yes", "是")
