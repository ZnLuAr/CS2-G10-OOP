"""命令行交互主循环、菜单、输入校验（功能 ID 6-9）

职责：
- 显示主菜单及各级子菜单（功能 ID 6）
- 数字/字母导航，进入子菜单或返回（功能 ID 7）
- 非法输入处理，抛 InvalidInputError 并重新显示（功能 ID 8）
- 操作撤销栈，支持撤销可逆操作（功能 ID 9）

调用方式：
    from src.app import App
    from src.ui.cli import run_cli
    App(ui_runner=run_cli).run()
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from src.errors import InvalidInputError, TradingSystemError
from src.ui.handlers import (
    DataHandler,
    InventoryHandler,
    ItemHandler,
    MarketHandler,
    PlayerHandler,
    ReportHandler,
)
from src.ui.utils import clear_screen, pause
from src.ui.menus import show_main_menu
from src.ui.operations import OperationStack
from src.ui.prompts import prompt_choice

if TYPE_CHECKING:
    from src.app import App


__all__ = ["run_cli"]


# -----------------------------------------------------------------------------
# CLI 主类
# -----------------------------------------------------------------------------

class TradingCLI:
    """交易系统的命令行界面（路由器）"""

    def __init__(self, app: App) -> None:
        self.app = app
        self.repo = app.repo
        self.persistence = app.persistence
        self.op_stack = OperationStack(max_size=20)

        # 初始化所有 Handler
        self.player_handler = PlayerHandler(app, self.op_stack)
        self.item_handler = ItemHandler(app, self.op_stack)
        self.inventory_handler = InventoryHandler(app, self.op_stack)
        self.market_handler = MarketHandler(app, self.op_stack)
        self.report_handler = ReportHandler(app, self.op_stack)
        self.data_handler = DataHandler(app, self.op_stack)

    def run(self) -> None:
        """主菜单循环，直到用户选择退出"""
        while True:
            try:
                self._clear_screen()
                menu_text = show_main_menu(
                    can_undo=self.op_stack.can_undo(),
                    undo_count=len(self.op_stack)
                )
                print(menu_text)
                choice = prompt_choice(
                    "请输入选项",
                    {"1", "2", "3", "4", "5", "6", "7", "0", "q", "Q"}
                )

                if choice == "7" or choice.lower() == "q":
                    print("\n系统已退出\n")
                    break

                if choice == "0":
                    self._handle_undo()
                    continue

                self._handle_main_choice(choice)

            except InvalidInputError as e:
                print(f"\n[输入错误] {e.message}")
                self._pause()
            except TradingSystemError as e:
                print(f"\n[业务错误] {e.message}")
                self._pause()
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                print(f"\n[系统错误] {type(e).__name__}: {e}")
                self._pause()

    def _handle_main_choice(self, choice: str) -> None:
        """根据主菜单选择委托给对应 Handler"""
        handlers = {
            "1": self.player_handler,
            "2": self.item_handler,
            "3": self.inventory_handler,
            "4": self.market_handler,
            "5": self.report_handler,
            "6": self.data_handler,
        }
        handler = handlers.get(choice)
        if handler:
            handler.run_menu()
        else:
            raise InvalidInputError(field="choice", value=choice)

    def _handle_undo(self) -> None:
        """撤销上一步操作"""
        op = self.op_stack.pop()
        if op is None:
            print("\n[提示] 没有可撤销的操作")
            self._pause()
            return

        try:
            op.undo_fn()
            print(f"\n[成功] 已撤销：{op.name}")
        except Exception as e:
            print(f"\n[撤销失败] {type(e).__name__}: {e}")
        self._pause()

    def _pause(self) -> None:
        """暂停等待用户按键"""
        pause()

    def _clear_screen(self) -> None:
        """清屏（跨平台）"""
        clear_screen()


# -----------------------------------------------------------------------------
# 入口函数
# -----------------------------------------------------------------------------

def run_cli(app: App) -> None:
    """CLI 入口，由 App.ui_runner 调用"""
    cli = TradingCLI(app)
    cli.run()
