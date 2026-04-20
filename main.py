"""JC1503 OOP Group Project — CS 2 Group 10
游戏装备交易系统。

程序入口——所有生命周期编排都在 src/app.py::App 里，
本文件只负责把控制权交出去并退出。
"""

import sys

from src.app import App




def main() -> int:
    return App().run()


if __name__ == "__main__":
    sys.exit(main())
