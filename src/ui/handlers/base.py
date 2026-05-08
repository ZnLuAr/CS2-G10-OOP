"""
Handler 基类

提供所有功能域 Handler 的通用功能和接口。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.errors import BusinessRuleError, InvalidInputError, TradingSystemError
from src.ui.utils import clear_screen, pause

if TYPE_CHECKING:
    from src.app import App
    from src.ui.cli import OperationStack

__all__ = ["BaseHandler"]




class BaseHandler(ABC):
    """Handler 基类，提供通用功能"""

    def __init__(self, app: App, op_stack: OperationStack | None = None):
        """初始化 Handler

        Args:
            app: 应用实例
            op_stack: 操作撤销栈（可选）
        """
        self.app = app
        self.repo = app.repo
        self.persistence = app.persistence
        self.op_stack = op_stack


    @abstractmethod
    def run_menu(self) -> None:
        """
        运行子菜单循环

        子类必须实现此方法，提供菜单显示和选项处理逻辑。
        """
        pass


    def _pause(self) -> None:
        """等待用户按键"""
        pause()


    def _clear_screen(self) -> None:
        """清屏（跨平台）"""
        clear_screen()

    def _get_item_display_name(self, item_id: str) -> str:
        """获取物品显示名称，不存在时返回 item_id"""
        item = self.repo.items.get(item_id)
        return item.name if item else item_id

    def _get_player_or_none(self, pid: str):
        """获取玩家对象，不存在时返回 None 并显示提示"""
        player = self.repo.players.get(pid)
        if player is None:
            print(f"[提示] 玩家 {pid} 不存在")
            self._pause()
        return player

    def _handle_exception(self, e: Exception) -> None:
        """统一异常处理"""
        if isinstance(e, (SystemExit, KeyboardInterrupt)):
            raise
        if isinstance(e, InvalidInputError):
            print(f"\n[输入错误] {e.message}")
        elif isinstance(e, BusinessRuleError):
            print(f"\n[业务错误] {e.message}")
        elif isinstance(e, TradingSystemError):
            print(f"\n[错误] {e.message}")
        else:
            print(f"\n[系统错误] {type(e).__name__}: {e}")
        self._pause()
