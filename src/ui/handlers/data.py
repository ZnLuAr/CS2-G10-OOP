"""
数据管理 Handler

负责数据保存、统计、重置等功能。
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import TYPE_CHECKING

from src.errors import TradingSystemError
from src.ui.handlers.base import BaseHandler
from src.ui.menus import show_data_menu
from src.ui.prompts import prompt_choice

if TYPE_CHECKING:
    from src.app import App
    from src.ui.cli import OperationStack

__all__ = ["DataHandler"]




class DataHandler(BaseHandler):
    """数据管理 Handler"""

    def __init__(self, app: App, op_stack: OperationStack | None = None):
        super().__init__(app, op_stack)


    def run_menu(self) -> None:
        """运行数据管理菜单循环"""
        while True:
            try:
                menu_text = show_data_menu()
                print(menu_text)
                choice = prompt_choice("请输入选项", {"1", "2", "3", "b", "B"})

                if choice.lower() == "b":
                    break

                self._dispatch(choice)

            except Exception as e:
                self._handle_exception(e)


    def _dispatch(self, choice: str) -> None:
        """分发菜单选择"""
        actions = {
            "1": self.save_all,
            "2": self.show_stats,
            "3": self.reset_all,
        }
        action = actions.get(choice)
        if action:
            action()


    def save_all(self) -> None:
        """立即保存所有数据到 JSON 文件（功能 ID 49）"""
        try:
            self.persistence.save_all(self.repo)
            print("\n[成功] 所有数据已保存到 data/ 目录")
            print("  - players.json")
            print("  - items.json")
            print("  - market.json")
            print("  - transactions.json")
            print("  - catalog.json")
            self._pause()
        except TradingSystemError as e:
            print(f"\n[错误] 保存失败：{e.message}")
            self._pause()


    def show_stats(self) -> None:
        """显示数据文件统计信息"""
        print("\n" + "=" * 60)
        print("          数据统计")
        print("=" * 60)

        data_dir = self.persistence.data_dir
        print(f"\n数据目录：{os.path.abspath(data_dir)}")

        print("\n文件信息：")
        files = ["players.json", "items.json", "market.json",
                 "transactions.json", "catalog.json"]
        for filename in files:
            path = os.path.join(data_dir, filename)
            if os.path.exists(path):
                size = os.path.getsize(path)
                mtime = os.path.getmtime(path)
                mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"  {filename:<22} {size:>8} bytes  最后修改：{mtime_str}")
            else:
                print(f"  {filename:<22} [不存在]")

        backup_dir = os.path.join(data_dir, "backup")
        if os.path.exists(backup_dir):
            backup_count = len([f for f in os.listdir(backup_dir) if f.endswith(".bak")])
            print(f"\n备份文件：{backup_count} 个")

        print("\n数据量统计：")
        print(f"  玩家数：{len(self.repo.players)}")
        print(f"  物品数：{len(self.repo.items)}")
        print(f"  挂单数：{len(self.repo.listings)}")
        print(f"  交易数：{len(self.repo.transactions)}")
        print("=" * 60)
        self._pause()


    def reset_all(self) -> None:
        """重置所有数据（功能 ID 53）"""
        print("\n" + "!" * 60)
        print("  警告：此操作将删除所有数据文件，无法恢复！")
        print("!" * 60)
        print("\n当前数据：")
        print(f"  - 玩家数：{len(self.repo.players)}")
        print(f"  - 物品数：{len(self.repo.items)}")
        print(f"  - 挂单数：{len(self.repo.listings)}")
        print(f"  - 交易数：{len(self.repo.transactions)}")

        confirm1 = input("\n确认要删除所有数据吗？(yes/no): ").strip().lower()
        if confirm1 != "yes":
            print("[已取消]")
            self._pause()
            return

        print("\n请输入 RESET 以最终确认：")
        confirm2 = input("> ").strip()
        if confirm2 != "RESET":
            print("[已取消]")
            self._pause()
            return

        try:
            self.persistence.reset()
            print("\n[成功] 数据已重置")
            print("程序将退出，请重新启动以生成新的种子数据")
            # 关键：通知 App 跳过 atexit 钩子里的 save_all，
            # 否则 shutdown 会把刚删除的 JSON 文件再写回去。
            self.app._skip_save_on_exit = True
            # 使用 SystemExit 而不是直接 sys.exit(0)，让主循环有机会清理
            raise SystemExit(0)
        except TradingSystemError as e:
            print(f"\n[错误] 重置失败：{e.message}")
            self._pause()
