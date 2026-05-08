"""测试 prompts 模块"""

import pytest

from src.errors import InvalidInputError
from src.ui.prompts import (
    prompt_choice,
    prompt_confirm,
    prompt_float,
    prompt_int,
    prompt_optional_int,
    prompt_string,
)


def test_prompt_choice_valid(monkeypatch):
    """测试有效选择"""
    monkeypatch.setattr("builtins.input", lambda _: "1")
    result = prompt_choice("请选择", {"1", "2", "3"})
    assert result == "1"


def test_prompt_choice_invalid(monkeypatch):
    """测试无效选择"""
    monkeypatch.setattr("builtins.input", lambda _: "9")
    with pytest.raises(InvalidInputError):
        prompt_choice("请选择", {"1", "2", "3"})


def test_prompt_int_valid(monkeypatch):
    """测试有效整数输入"""
    monkeypatch.setattr("builtins.input", lambda _: "42")
    result = prompt_int("请输入数字")
    assert result == 42


def test_prompt_int_invalid(monkeypatch):
    """测试无效整数输入"""
    monkeypatch.setattr("builtins.input", lambda _: "abc")
    with pytest.raises(InvalidInputError):
        prompt_int("请输入数字")


def test_prompt_int_with_min_val(monkeypatch):
    """测试最小值校验"""
    monkeypatch.setattr("builtins.input", lambda _: "5")
    with pytest.raises(InvalidInputError):
        prompt_int("请输入数字", min_val=10)


def test_prompt_int_with_max_val(monkeypatch):
    """测试最大值校验"""
    monkeypatch.setattr("builtins.input", lambda _: "100")
    with pytest.raises(InvalidInputError):
        prompt_int("请输入数字", max_val=50)


def test_prompt_optional_int_with_value(monkeypatch):
    """测试可选整数输入（有值）"""
    monkeypatch.setattr("builtins.input", lambda _: "42")
    result = prompt_optional_int("请输入数字", default=10)
    assert result == 42


def test_prompt_optional_int_empty(monkeypatch):
    """测试可选整数输入（空值）"""
    monkeypatch.setattr("builtins.input", lambda _: "")
    result = prompt_optional_int("请输入数字", default=10)
    assert result == 10


def test_prompt_float_valid(monkeypatch):
    """测试有效浮点数输入"""
    monkeypatch.setattr("builtins.input", lambda _: "3.14")
    result = prompt_float("请输入数字")
    assert result == 3.14


def test_prompt_float_invalid(monkeypatch):
    """测试无效浮点数输入"""
    monkeypatch.setattr("builtins.input", lambda _: "abc")
    with pytest.raises(InvalidInputError):
        prompt_float("请输入数字")


def test_prompt_string_valid(monkeypatch):
    """测试有效字符串输入"""
    monkeypatch.setattr("builtins.input", lambda _: "hello")
    result = prompt_string("请输入文本", min_len=1, max_len=10)
    assert result == "hello"


def test_prompt_string_too_short(monkeypatch):
    """测试字符串过短"""
    monkeypatch.setattr("builtins.input", lambda _: "")
    with pytest.raises(InvalidInputError):
        prompt_string("请输入文本", min_len=1)


def test_prompt_string_too_long(monkeypatch):
    """测试字符串过长"""
    monkeypatch.setattr("builtins.input", lambda _: "a" * 100)
    with pytest.raises(InvalidInputError):
        prompt_string("请输入文本", max_len=10)


def test_prompt_confirm_yes(monkeypatch):
    """测试确认输入（是）"""
    monkeypatch.setattr("builtins.input", lambda _: "y")
    result = prompt_confirm("确认吗")
    assert result is True


def test_prompt_confirm_no(monkeypatch):
    """测试确认输入（否）"""
    monkeypatch.setattr("builtins.input", lambda _: "n")
    result = prompt_confirm("确认吗")
    assert result is False


def test_prompt_confirm_default(monkeypatch):
    """测试确认输入（默认值）"""
    monkeypatch.setattr("builtins.input", lambda _: "")
    result = prompt_confirm("确认吗", default=True)
    assert result is True
