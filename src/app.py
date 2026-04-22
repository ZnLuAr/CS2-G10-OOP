"""应用生命周期编排（功能 ID 4-5）

职责：
- 启动横幅（程序名 / 版本 / 数据规模）
- 调用 ``Persistence`` 触发首次种子 → 加载
- 注册 ``atexit`` 钩子保证退出时落盘
- 调用 UI runner（默认 ``run_cli``，可注入用于测试）
- 进程级兜底：未预期 Exception 写堆栈、保存数据后退出

调用方式（main.py）::

    from src.app import App
    App().run()
"""

from __future__ import annotations

import atexit
import sys
import traceback
from typing import Callable

from src.errors import TradingSystemError
from src.services import ItemService, MarketService, PlayerService, TransactionService
from src.services.persistence import Persistence, Repository

__all__ = ["App", "VERSION", "PROGRAM_NAME"]


PROGRAM_NAME = "游戏装备交易系统"
VERSION = "0.1.0"


UIRunner = Callable[["App"], None]


def _default_ui_runner(app: "App") -> None:
    """默认 UI runner——调用 CLI 主菜单"""
    # 延迟导入避免循环依赖
    from src.ui.cli import run_cli
    run_cli(app)


class App:
    """应用对象，负责整个进程的生命周期

    属性:
        persistence: 持久化服务
        repo:        加载后填充的内存仓库
        ui_runner:   UI 入口回调，便于测试时注入
    """

    def __init__(self,
                 persistence: Persistence | None = None,
                 ui_runner: UIRunner | None = None) -> None:
        self.persistence = persistence or Persistence()
        self.ui_runner = ui_runner or _default_ui_runner
        self.repo: Repository | None = None
        self.player_service: PlayerService | None = None
        self.item_service: ItemService | None = None
        self.transaction_service: TransactionService | None = None
        self.market_service: MarketService | None = None
        self._save_registered = False


    # ------------------------------------------------------------------
    # 生命周期
    # ------------------------------------------------------------------

    def bootstrap(self) -> Repository:
        """种子（如需）+ 加载 + 注册退出钩子，返回填充好的 Repository"""
        seeded = self.persistence.seed_if_empty()
        self.repo = self.persistence.load_all()
        self.player_service = PlayerService(self.repo, self.persistence)
        self.transaction_service = TransactionService(self.repo, self.persistence)
        self.item_service = ItemService(self.repo, self.persistence)
        self.market_service = MarketService(
            self.repo,
            self.persistence,
            player_service=self.player_service,
            transaction_service=self.transaction_service,
        )
        self._register_save_on_exit()
        if seeded:
            print("[首次启动] 已生成初始数据集")
        return self.repo

    def show_banner(self) -> None:
        """打印程序名 / 版本 / 当前数据规模（功能 ID 5）"""
        assert self.repo is not None, "调用 show_banner 前必须先 bootstrap()"
        print(f"\n=== {PROGRAM_NAME} v{VERSION} ===")
        print(f"     ようこそ、剣と魔法の世界へ（大噓    \n\n")
        print(f"  玩家: {len(self.repo.players)}"
              f"  物品: {len(self.repo.items)}"
              f"  活跃挂单: {sum(1 for l in self.repo.listings.values() if l.status == 'active')}"
              f"  历史交易: {len(self.repo.transactions)}")

    def shutdown(self) -> None:
        """高雅不堪地关机，保存全部数据（功能 ID 4）"""
        if self.repo is None:
            return
        try:
            self.persistence.save_all(self.repo)
        except Exception as e:                   # noqa: BLE001 - 兜底
            # 退出阶段不能再向上抛——尽力而为，打印错误
            print(f"[ERROR] 退出时保存数据失败：{type(e).__name__}: {e}",
                  file=sys.stderr)


    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------

    def run(self) -> int:
        """启动应用、返回进程退出码（0 = 正常）"""
        try:
            self.bootstrap()
            self.show_banner()
            self.ui_runner(self)
        except KeyboardInterrupt:
            print("\n收到中断信号，正在保存并退出...")
            return 0
        except TradingSystemError as e:
            # 启动期被服务层抛出的可预期错误（例如数据完整性失败）
            print(f"[启动失败] {e.message}", file=sys.stderr)
            return 2
        except Exception as e:                   # noqa: BLE001 - 进程级兜底
            print(f"[FATAL] 未预期异常：{type(e).__name__}: {e}",
                  file=sys.stderr)
            traceback.print_exc()
            return 1
        return 0


    # ------------------------------------------------------------------
    # 内部
    # ------------------------------------------------------------------

    def _register_save_on_exit(self) -> None:
        if self._save_registered:
            return
        atexit.register(self.shutdown)
        self._save_registered = True
